"""Spec-blind tests for the `wind_solar` stream script (Task 2.4, docs/WIND_SOLAR_SPEC.md v1.0 FINAL, D74).

Written from docs/WIND_SOLAR_SPEC.md, docs/LIB_SPEC.md (v1.5, v1.6), docs/SCHEMA.md v2.6, docs/DECISIONS.md,
docs/OIL_GAS_SPEC.md and docs/OTHER_SPEC.md conventions, and the staged data of build/d74_staging/ (applied into
data/ before these tests run). pipeline/streams/*.py, pipeline/lib and pipeline/validate.py were not read. Expected
values come from wind_solar_oracle.py (pandas plus the standard library; no pipeline.*) and from the hand
arithmetic of TestHandComputed. Every factor, intensity and share is read from the files; premises are asserted
first ("PREMISE BROKEN").

The whole module is skipped, with a reason, when the D74 data are not applied (WIND_SOLAR_SPEC section 12): the
check is the existence of data/activity/material_intensity.csv, data/activity/wind_solar_shares.csv,
data/factors/wind_solar.csv and a data/reference/commodity_factors.csv with the columns factor_id and ore_type.
For local development an alternative root can be given with the environment variable WIND_SOLAR_TEST_ROOT.

Mapping to WIND_SOLAR_SPEC section 9
------------------------------------
(a) Schema              TestSchema, TestRowConventions, TestStagesTechnologies
(b) Coverage            TestRowsAgainstOracle, TestCoverage (incl. the 0.1 % report)
(c) Conservation        TestClassShares (1), TestReeRoutes (2), TestAllocation (3), TestOdIdentity (4),
                        TestMerge (5), TestNoDoubleCount (6) + TestEmbeddedFuel, TestOdMerge
(d) Determinism         TestDeterminism, TestNegligibility
(e) Benchmarks          TestBenchmarks (B1-B4; documented misses as runtime xfail)
(f) Hand-computed       TestHandComputed (16 cases)
(g) Fixtures            TestMini* (miniature trees in tmp_path)
(h) Pre-1950 file       TestPre1950
(i) Premises            TestPremises
(j) CLI                 TestCli
plus TestNotesAndFlags (3.3), TestLog (8), TestPlaceholders, TestEventsNotTransferred, TestPre2001Pv.

SPEC v1.1 (13.9-13.20) and the earlier test round
------------------------------------------------
The S1-S11 questions of the first round are settled by WIND_SOLAR_SPEC v1.1: REE windows from 1982 (no `no_factor`),
B1 corrected (pass rule: <= ore bound, >= 1/10 of it, within x3 of the inventory range), steel route share from pig
iron over steel for 1950-69, stepwise arithmetic per class then sum_correlated, log formats of 13.14, source_ids and
driver basis from the rows behind computed contributions (13.20), shares at central as exact scalars (13.19), the walk
1950-2025, and phi = 1 from 1991 for the contingent OD identity. Rows, values, flags, notes, source_ids, driver basis
and log entries are therefore compared exactly with the oracle; there are no alternative readings.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import importlib
import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
import pytest
from wind_solar_oracle import (
    CHARGE_RADIO,
    CHARGE_MAIN,
    FAMILY_CODE,
    JOINT,
    VARIANTS,
    VAR_RULE,
    WORLD_SERIES,
    B,
    Oracle,
    is_zero_b,
    parse_notes,
    prod,
    scale,
    sum_correlated,
)

# pipeline/tests/streams/test_wind_solar.py -> streams -> tests -> pipeline -> repository root
ROOT = Path(os.environ.get("WIND_SOLAR_TEST_ROOT") or Path(__file__).resolve().parents[3])

REL = 1e-7  # in-memory values against the oracle
WRITTEN = 1e-5  # six significant digits in written files (D68)
RUN_RE = re.compile(r"^(\d{4})-(\d{4}) \((\d+) years?\)")
GZ_HEADER = bytes.fromhex("1f8b08000000000002ff")
LOG_KINDS = {
    "no_factor",
    "no_driver",
    "no_family",
    "lib_warning",
    "no_intensity",
    "no_footprint",
    "placeholder_share",
    "attribution",
    "od_military_remainder",
}
MASTER_COLS = [
    "year", "stream", "substream", "stage", "product", "residue_type", "country", "group", "tier", "quantity",
    "unit", "value_low", "value_central", "value_high", "below_detection", "basis", "source_ids", "factor_ids",
    "allocation_variant", "allocation_rule", "embedded_fuel", "technology", "route", "event_id", "notes",
]
COMMODITIES = {
    "copper", "aluminium", "steel", "cast_iron", "cement", "ree_oxide", "zinc", "tin", "silver", "silicon_mg",
    "glass", "glass_fibre", "tio2_pigment",
}
ORE_TYPES_COPPER = {"porphyry_stratiform", "iocg_olympic_dam", "iocg_high_u", "cu_co_stratiform", "all"}
ORE_TYPES_REE = {"ree_bayan_obo", "ree_ionic_clay", "ree_monazite", "ree_mt_weld"}
JOINT_COMMODITY_FAMILIES = set(JOINT)
NINE_EVENTS = {"E006", "E007", "E012", "E014", "E017", "E018", "E019", "E020", "E021"}
BF_PREMISE_TOL = 0.15


# --------------------------------------------------------------------------------------------
# module gate: the D74 data must be applied (spec 12)
# --------------------------------------------------------------------------------------------
def _applied(root: Path) -> tuple[bool, str]:
    need = [
        "data/activity/material_intensity.csv",
        "data/activity/wind_solar_shares.csv",
        "data/factors/wind_solar.csv",
        "data/reference/commodity_factors.csv",
    ]
    missing = [n for n in need if not (root / n).is_file()]
    if missing:
        return False, (
            "the D74 staged data are not applied into data/ (WIND_SOLAR_SPEC 12, build/d74_staging/APPLY.md); "
            f"missing: {missing}"
        )
    try:
        with open(root / "data/reference/commodity_factors.csv", newline="", encoding="utf-8") as fh:
            head = next(csv.reader(fh))
    except Exception as exc:  # pragma: no cover
        return False, f"cannot read data/reference/commodity_factors.csv: {exc}"
    if "factor_id" not in head or "ore_type" not in head:
        return False, "data/reference/commodity_factors.csv lacks factor_id/ore_type (schema v2.6 not applied)"
    return True, ""


_APPLIED, _WHY = _applied(ROOT)
pytestmark = pytest.mark.skipif(not _APPLIED, reason=_WHY or "D74 data not applied")


def premise(cond, msg):
    assert cond, f"PREMISE BROKEN: {msg}"


# --------------------------------------------------------------------------------------------
# generic helpers
# --------------------------------------------------------------------------------------------
def _blank(v) -> bool:
    return v is None or v == "" or (isinstance(v, float) and math.isnan(v))


def ids(v) -> list[str]:
    if _blank(v):
        return []
    if isinstance(v, (list, tuple)):
        return [str(x) for x in v]
    return str(v).split(";")


def as_bool(v) -> bool:
    if isinstance(v, str):
        return v.strip().lower() == "true"
    return bool(v)


def close(a: float, b: float, rel: float = REL) -> bool:
    if a == 0 and b == 0:
        return True
    return math.isclose(a, b, rel_tol=rel, abs_tol=0.0)


def vals(r: dict) -> tuple[float, float, float]:
    return float(r["value_low"]), float(r["value_central"]), float(r["value_high"])


def rkey(r: dict) -> tuple:
    return (
        int(r["year"]), r["substream"], r["product"], r["residue_type"] or "", r["country"], r["group"],
        r["tier"], r["route"] or "", r["allocation_variant"],
    )


def describe(r: dict) -> str:
    return ", ".join(
        f"{k}={r.get(k)!r}"
        for k in ("year", "substream", "product", "country", "group", "tier", "residue_type", "route", "allocation_variant")
    )


def show(msgs: list[str], n: int = 6) -> str:
    return f"{len(msgs)} problem(s); first {min(n, len(msgs))}:\n  " + "\n  ".join(msgs[:n])


class Rows:
    def __init__(self, rows: list[dict]):
        self.rows = rows
        self.by_year: dict[int, list[dict]] = defaultdict(list)
        self.by_key: dict[tuple, list[dict]] = defaultdict(list)
        for r in rows:
            self.by_year[int(r["year"])].append(r)
            self.by_key[rkey(r)].append(r)

    def find(self, year: int | None = None, **kw) -> list[dict]:
        pool = self.rows if year is None else self.by_year.get(year, [])
        out = []
        for r in pool:
            ok = True
            for k, v in kw.items():
                rv = r[k]
                if v is None or v == "":
                    if not _blank(rv):
                        ok = False
                        break
                elif isinstance(v, (set, frozenset, list, tuple)):
                    if rv not in v:
                        ok = False
                        break
                elif rv != v:
                    ok = False
                    break
            if ok:
                out.append(r)
        return out

    def one(self, year: int, **kw) -> dict:
        m = self.find(year, **kw)
        assert len(m) == 1, f"expected exactly one row for year={year}, {kw}; found {len(m)}"
        return m[0]


def log_entries(log: list[dict], kind: str, **kw) -> list[dict]:
    return [e for e in log if e.get("kind") == kind and all(e.get(k) == v for k, v in kw.items())]


def run_of(e: dict):
    m = RUN_RE.match(str(e.get("detail", "")))
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def entry_years(e: dict) -> set[int]:
    m = run_of(e)
    if m:
        return set(range(m[0], m[1] + 1))
    return {e["year"]} if isinstance(e.get("year"), int) else set()


def names_in(e: dict, name: str) -> bool:
    return name in str(e.get("group", "")) or name in str(e.get("detail", ""))


def lib_error():
    from pipeline.lib import LibError

    return LibError


def _env():
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    return env


# --------------------------------------------------------------------------------------------
# independent data access (hand arithmetic; deliberately not the oracle)
# --------------------------------------------------------------------------------------------
class Data:
    """Central values (and bounds) of the activity files and the registry, straight from the CSVs."""

    CLS = {  # class -> (substream, capacity series, share series, complement)
        "wind_on_nopm": ("wind", "cap_add_wind_onshore", "wind_pm_share_onshore", True),
        "wind_on_pm": ("wind", "cap_add_wind_onshore", "wind_pm_share_onshore", False),
        "wind_off_nopm": ("wind", "cap_add_wind_offshore", "wind_pm_share_offshore", True),
        "wind_off_pm": ("wind", "cap_add_wind_offshore", "wind_pm_share_offshore", False),
        "pv_utility": ("solar", "cap_add_solar_pv", "pv_utility_share", False),
        "pv_rooftop": ("solar", "cap_add_solar_pv", "pv_utility_share", True),
    }

    def __init__(self, root: Path):
        self.root = root
        self.rows: dict[tuple, dict] = {}
        for f in ("capacity_additions", "material_intensity", "wind_solar_shares", "commodity_production", "uranium"):
            p = root / "data" / "activity" / f"{f}.csv"
            if not p.exists():
                continue
            df = pd.read_csv(p, dtype=str, keep_default_na=False)
            for r in df.itertuples(index=False):
                if f == "capacity_additions" and r.country != "XWL":
                    continue  # the file note: use XWL, never the country rows (spec 2.1 group C)
                self.rows[(r.series, r.country, int(r.year))] = dict(
                    low=float(r.value_low), c=float(r.value_central), high=float(r.value_high), basis=r.basis,
                    unit=r.unit, notes=r.notes, src=r.source_ids,
                )
        fp = root / "data" / "reference" / "commodity_factors.csv"
        self.cf = pd.read_csv(fp, dtype=str, keep_default_na=False)
        for c in ("value_low", "value_central", "value_high"):
            self.cf[c] = self.cf[c].astype(float)
        self.cf["year_from"] = self.cf["year_from"].astype(int)
        self.cf["year_to"] = self.cf["year_to"].astype(int)

    def a(self, series, y, country="XWL") -> float:
        return self.rows[(series, country, y)]["c"]

    def has(self, series, y, country="XWL") -> bool:
        return (series, country, y) in self.rows

    def fac(self, commodity, group, tier, y, ore="", region="XWL", residue="", route="") -> dict:
        d = self.cf
        m = d[
            (d.commodity == commodity) & (d.ore_type == ore) & (d.region == region) & (d.group == group)
            & (d.tier == tier) & (d.residue_type == residue) & (d.route == route)
            & (d.allocation_variant == "default") & (d.year_from <= y) & (d.year_to >= y)
        ]
        assert len(m) == 1, f"registry lookup {commodity}/{ore}/{region}/{group}/{tier}/{residue}/{route}@{y}: {len(m)} rows"
        r = m.iloc[0]
        return dict(fid=r.factor_id, low=r.value_low, c=r.value_central, high=r.value_high)

    def tonnes_c(self, y: int, sub: str, c: str) -> float:
        tot = 0.0
        for k, (s, capser, shser, cmpl) in self.CLS.items():
            if s != sub or not self.has(capser, y) or not self.has(shser, y) or not self.has(f"mi_{k}_{c}", y):
                continue
            pi = self.a(shser, y)
            pi = 1.0 - pi if cmpl else pi
            tot += self.a(capser, y) * pi * self.a(f"mi_{k}_{c}", y)
        return tot

    def class_tonnes_c(self, y: int, k: str, c: str) -> float:
        s, capser, shser, cmpl = self.CLS[k]
        pi = self.a(shser, y)
        pi = 1.0 - pi if cmpl else pi
        return self.a(capser, y) * pi * self.a(f"mi_{k}_{c}", y)

    def od_share(self, y: int) -> float:
        if not self.has("prod_copper_od", y, "AUS"):
            return 0.0
        return self.a("prod_copper_od", y, "AUS") / self.a("prod_copper", y)


@pytest.fixture(scope="module")
def data() -> Data:
    return Data(ROOT)


# --------------------------------------------------------------------------------------------
# module-scoped fixtures
# --------------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def ws_mod():
    try:
        return importlib.import_module("pipeline.streams.wind_solar")
    except ImportError as exc:  # expected until the code-writer is done
        pytest.fail(f"cannot import pipeline.streams.wind_solar (WIND_SOLAR_SPEC 1): {type(exc).__name__}: {exc}")


@pytest.fixture(scope="module")
def result(ws_mod):
    assert hasattr(ws_mod, "build"), "pipeline.streams.wind_solar must expose build(root) (WIND_SOLAR_SPEC 1)"
    res = ws_mod.build(ROOT)
    for attr in ("rows", "rows_pre1950", "log"):
        assert hasattr(res, attr), f"BuildResult has no attribute {attr!r} (WIND_SOLAR_SPEC 1)"
    return res


@pytest.fixture(scope="module")
def rows(result) -> Rows:
    return Rows(list(result.rows))


@pytest.fixture(scope="module")
def log(result) -> list[dict]:
    return list(result.log)


@pytest.fixture(scope="module")
def oracle() -> Oracle:
    return Oracle(ROOT)


@pytest.fixture(scope="module")
def expected(oracle):
    return oracle.expected()


@pytest.fixture(scope="module")
def write_master():
    return importlib.import_module("pipeline.lib.rows").write_master


@pytest.fixture(scope="module")
def written(result, write_master, tmp_path_factory):
    d = tmp_path_factory.mktemp("ws_written")
    main, pre = d / "wind_solar.csv", d / "wind_solar_pre1950.csv"
    write_master(list(result.rows), main)
    write_master(list(result.rows_pre1950), pre)
    return main, pre


def _copy_tree(dst: Path) -> Path:
    shutil.copytree(ROOT / "data", dst / "data", ignore=shutil.ignore_patterns("streams", "streams_pre1950"))
    shutil.copytree(ROOT / "schema", dst / "schema")
    (dst / "data" / "streams").mkdir()
    (dst / "data" / "streams_pre1950").mkdir()
    (dst / "research" / "wind_solar").mkdir(parents=True)
    return dst


# --------------------------------------------------------------------------------------------
# row-by-row comparison with the oracle
# --------------------------------------------------------------------------------------------
def _same_b(r: tuple, b: B, rel: float) -> bool:
    return all(close(g, w, rel) for g, w in zip(r, (b.low, b.central, b.high)))


def compare_row(O: Oracle, er, r: dict, rel: float = REL) -> list[str]:
    msgs: list[str] = []
    y, sub, c, rs, country, g, t, rt, v = er.key
    for col, want in (
        ("stream", "wind_solar"),
        ("stage", "commodity_supply"),
        ("quantity", "flow"),
        ("unit", "Bq/a"),
        ("basis", "modelled"),
        ("technology", sub),
        ("substream", sub),
        ("product", c),
        ("country", country),
    ):
        if r[col] != want:
            msgs.append(f"{col}={r[col]!r}, expected {want!r}")
    if as_bool(r["embedded_fuel"]):
        msgs.append("embedded_fuel true (D74(d))")
    if not _blank(r["event_id"]):
        msgs.append(f"event_id={r['event_id']!r}, expected empty (Q18)")
    rule = ids(r["allocation_rule"])
    if er.joint:
        ok = ("alloc:value" in rule) if v == "default" else rule == [VAR_RULE[v]]
        if not ok:
            msgs.append(f"allocation_rule={rule}, expected {VAR_RULE[v]} for variant {v}")
    elif rule != ["none"]:
        msgs.append(f"allocation_rule={rule}, expected ['none'] (single-product family)")
    got = vals(r)
    flagged = as_bool(r["below_detection"])
    match = er.b
    if not _same_b(got, match, rel) or flagged != match.nd:
        msgs.append(f"values {got!r} flag={flagged} differ from the oracle ({match.low!r}, {match.central!r}, {match.high!r}, nd={match.nd})")
    fid = ids(r["factor_ids"])
    if fid != er.fids:
        msgs.append(f"factor_ids={fid}, expected (registry order, 3.5) {er.fids}")
    src = ids(r["source_ids"])
    if src != sorted(er.src):
        msgs.append(f"source_ids={src}, expected (13.20, sorted union) {sorted(er.src)}")
    msgs += check_notes(er, r, match)
    return msgs


def check_notes(er, r: dict, match: B) -> list[str]:
    msgs: list[str] = []
    notes = r["notes"] or ""
    p = parse_notes(notes)
    head = p["head"]
    code = FAMILY_CODE.get(er.commodity)
    if not head or not head[0].startswith(f"{code}: "):
        msgs.append(f"notes should start with the family code {code!r}: {notes[:80]!r} (3.6)")
        return msgs
    if er.commodity == "copper":
        for o in er.ore_types:
            if o not in notes:
                msgs.append(f"notes do not name ore type {o!r} (3.2, 3.6)")
    if er.commodity == "ree_oxide":
        for o in er.ore_types:
            if o[len("ree_") :] not in notes and o not in notes:
                msgs.append(f"notes do not name the REE route {o!r} (3.6)")
    if er.joint and f"D6 {er.variant}, commodity {er.commodity}" not in notes:
        msgs.append(f"notes lack the fragment 'D6 {er.variant}, commodity {er.commodity}' (3.6)")
    if p.get("late_free_text"):
        msgs.append(f"free text after a suffix: {p['late_free_text']} (3.3 order)")
    names = [n for n, _ in p["suffix"]]
    order = ["driver", "share", "alloc", "cause"]
    if names != sorted(names, key=order.index):
        msgs.append(f"suffix order {names}, expected driver, share, allocation, cause (3.3)")
    if len(names) != len(set(names)):
        msgs.append(f"repeated suffix in {names}")
    sd = dict(p["suffix"])
    words = set(sd["driver"].split("+")) if "driver" in sd else set()
    if words != er.basis:
        msgs.append(f"driver basis {sorted(words)}, expected {sorted(er.basis)} (capacity and intensity rows behind computed contributions, 13.20)")
    if "driver" in sd and sd["driver"] != "+".join(w for w in ("interpolated", "extrapolated") if w in words):
        msgs.append(f"driver basis words not in the order interpolated+extrapolated: {sd['driver']!r}")
    if ("share" in sd) != er.share_ph:
        msgs.append(f"'; share basis: placeholder' present={('share' in sd)}, expected {er.share_ph}")
    if ("alloc" in sd) != er.alloc_ph:
        msgs.append(f"'; allocation basis: placeholder' present={('alloc' in sd)}, expected {er.alloc_ph} (default joint rows with a placeholder D6 share only, 3.3)")
    if match.nd:
        if "cause" not in sd:
            msgs.append("flagged row without '; below_detection cause: ...' last")
        elif sd["cause"].split("+") != list(match.causes):
            msgs.append(f"cause {sd['cause']!r}, oracle {list(match.causes)}")
    elif "cause" in sd:
        msgs.append("cause text on an unflagged row")
    return msgs


def compare_all(O: Oracle, exp: dict, rows_obj: Rows, label: str = "master", rel: float = REL) -> dict[str, list[str]]:
    problems: dict[str, list[str]] = defaultdict(list)
    for k, er in exp.items():
        got = rows_obj.by_key.get(k)
        tag = er.family
        if not got:
            problems[tag].append(f"MISSING row {k}")
            continue
        if len(got) > 1:
            problems[tag].append(f"DUPLICATE ({len(got)}) rows for {k}")
            continue
        for m in compare_row(O, er, got[0], rel):
            problems[tag].append(f"{k}: {m}")
    for k, lst in rows_obj.by_key.items():
        if k not in exp:
            problems["unexpected"].append(f"{label}: unexpected row {describe(lst[0])}")
    return problems


@pytest.fixture(scope="module")
def comparison(oracle, rows, expected):
    return compare_all(oracle, expected.rows, rows)


# --------------------------------------------------------------------------------------------
# (i) premises
# --------------------------------------------------------------------------------------------
GROUP_S_PLACEHOLDER = {
    "wind_pm_share_onshore", "wind_pm_share_offshore", "pv_utility_share", "steel_bf_route_share",
    "ree_route_share_bayan_obo", "ree_route_share_ionic_clay", "ree_route_share_monazite",
    "ree_route_share_mt_weld", "ree_charge_factor", "d6_value_share_copper_porphyry",
    "d6_value_share_copper_iocg_ph_cp", "d6_value_share_copper_cu_co", "d6_value_share_ree_bayan_obo",
    "d6_value_share_ree_monazite", "d6_value_share_zinc", "d6_value_share_silver", "od_value_share_u",
}
CLASS_SHARE_SERIES = {
    "cu_class_share_porphyry_stratiform", "cu_class_share_iocg_high_u", "cu_class_share_cu_co_stratiform",
}


def class_share_sum_problems(D: Data) -> list[str]:
    """Spec 2.1: the three copper class shares plus the OD share sum to 1 at central, 1e-6, every year."""
    bad = []
    years = sorted(y for (s, c, y) in D.rows if s == "cu_class_share_porphyry_stratiform")
    for y in years:
        parts = [D.rows.get((s, "XWL", y)) for s in sorted(CLASS_SHARE_SERIES)]
        if any(p is None for p in parts):
            bad.append(f"{y}: a class share is missing")
            continue
        tot = sum(p["c"] for p in parts) + D.od_share(y)
        if abs(tot - 1.0) > 1e-6:
            bad.append(f"{y}: class shares + OD share = {tot!r}")
    return bad


class TestPremises:
    def test_registry_columns_and_ids(self, data):
        cf = data.cf
        premise({"factor_id", "ore_type"} <= set(cf.columns), "commodity_factors.csv needs factor_id and ore_type (v2.6)")
        premise(cf.columns[0] == "factor_id", "factor_id is the first column (Q2)")
        premise(cf.factor_id.str.fullmatch(r"commodity:\d{4}").all(), "factor ids are commodity:NNNN")
        premise(cf.factor_id.is_unique, "factor ids are unique")
        for p in sorted((ROOT / "data" / "factors").glob("*.csv")):
            other = pd.read_csv(p, dtype=str, keep_default_na=False)
            if "factor_id" in other.columns and len(other):
                clash = set(other.factor_id) & set(cf.factor_id)
                premise(not clash, f"factor ids unique across factor files; {p.name} clashes on {sorted(clash)[:3]}")

    def test_registry_ore_types_exactly(self, data):
        cf = data.cf
        got = set(cf.ore_type)
        want = ORE_TYPES_COPPER | ORE_TYPES_REE | {""}
        premise(got == want, f"ore types in the registry are exactly {sorted(want)}; got {sorted(got)}")
        premise(set(cf[cf.commodity == "copper"].ore_type) == ORE_TYPES_COPPER, "copper ore types")
        premise(set(cf[cf.commodity == "ree_oxide"].ore_type) == ORE_TYPES_REE, "REE ore types")
        premise(set(cf[~cf.commodity.isin(["copper", "ree_oxide"])].ore_type) == {""}, "other commodities have no ore type")
        premise(set(cf.commodity) == COMMODITIES, f"registry commodities {sorted(set(cf.commodity))}")

    def test_no_embedded_fuel_or_other_component(self, data):
        premise(set(data.cf.component) == {"own_residue"}, "component is own_residue only (D74(d))")

    def test_region_cells_single_code_and_countries(self, data):
        premise(not data.cf.region.str.contains(";").any(), "no region cell holds ';' (Q14)")
        want = {
            ("copper", "iocg_olympic_dam"): "AUS", ("copper", "iocg_high_u"): "AUS", ("copper", "cu_co_stratiform"): "COD",
            ("copper", "porphyry_stratiform"): "XWL", ("copper", "all"): "XWL", ("ree_oxide", "ree_bayan_obo"): "CHN",
            ("ree_oxide", "ree_ionic_clay"): "CHN", ("ree_oxide", "ree_monazite"): "XWL", ("ree_oxide", "ree_mt_weld"): "MYS",
        }
        for (c, o), reg in want.items():
            got = set(data.cf[(data.cf.commodity == c) & (data.cf.ore_type == o)].region)
            premise(got == {reg}, f"{c}/{o} region {got}, expected {reg} (spec 2.3)")

    def test_od_and_ph_cp_rows_staged_as_specified(self, data):
        cf = data.cf
        od = cf[cf.ore_type == "iocg_olympic_dam"]
        premise(od.year_from.min() == 1988 and od.year_to.max() == 2025, "OD factor rows 1988-2025 (Q1)")
        premise(set(od.tier) == {"impounded"} and set(od.residue_type) == {"metal_tailings"}, "OD rows impounded metal_tailings")
        ph = cf[cf.ore_type == "iocg_high_u"]
        premise(ph.year_from.min() == 2009 and ph.year_to.max() == 2025, "PH/CP rows 2009-2025 (Q1)")
        odg, phg = set(od.group), set(ph.group)
        premise(odg == phg, f"OD and PH/CP rows carry the same groups so that the master keys collide: {odg ^ phg}")

    def test_residue_types_have_engine_parameters(self, data):
        rt = pd.read_csv(ROOT / "data" / "reference" / "residue_types.csv", dtype=str, keep_default_na=False)
        used = {x for x in data.cf.residue_type if x}
        for res in sorted(used):
            row = rt[rt.residue_type == res]
            premise(len(row) == 1, f"residue type {res} exists in residue_types.csv")
            r = row.iloc[0]
            for col in (
                "epsilon_rn222_low", "epsilon_rn222_central", "epsilon_rn222_high", "epsilon_rn220_low",
                "epsilon_rn220_central", "epsilon_rn220_high", "seepage_per_a_low", "seepage_per_a_central",
                "seepage_per_a_high",
            ):
                premise(r[col] != "", f"{res}.{col} is filled (Appendix A applied, Q14)")
        mt = rt[rt.residue_type == "metal_tailings"].iloc[0]
        u = rt[rt.residue_type == "u_tailings"].iloc[0]
        for sfx in ("low", "central", "high"):
            premise(
                float(mt[f"epsilon_rn222_{sfx}"]) == float(u[f"epsilon_rn222_{sfx}"]),
                f"metal_tailings epsilon222 {sfx} equals u_tailings (Q8, D62)",
            )

    def test_shares_are_exact_and_in_range(self, data):
        for (s, c, y), r in data.rows.items():
            if s in GROUP_S_PLACEHOLDER | CLASS_SHARE_SERIES:
                premise(r["low"] == r["c"] == r["high"], f"{s} {c} {y} has low=central=high (S11)")
                if s != "ree_charge_factor":
                    premise(0.0 <= r["c"] <= 1.0, f"{s} {c} {y} in [0, 1]")
        wu = [r["c"] for (s, c, y), r in data.rows.items() if s == "od_value_share_u"]
        premise(wu and all(0 <= x <= 1 for x in wu), "w_U in [0, 1] (spec 2.1 group D)")

    def test_placeholder_rows_carry_placeholder_notes(self, data):
        for (s, c, y), r in data.rows.items():
            if s in GROUP_S_PLACEHOLDER:
                premise(r["notes"].startswith("PLACEHOLDER"), f"{s} {y}: placeholder rows start their notes with PLACEHOLDER")
                premise(r["basis"] == "modelled", f"{s} {y}: placeholder basis is modelled")
            if s in CLASS_SHARE_SERIES:
                premise(not r["notes"].startswith("PLACEHOLDER"), f"{s} {y}: class shares are not placeholders")

    def test_class_shares_sum_to_one(self, data):
        bad = class_share_sum_problems(data)
        premise(not bad, "copper class shares + OD share = 1 at central: " + "; ".join(bad[:4]))

    def test_ree_route_shares_sum_to_one(self, data):
        for y in range(1982, 2026):
            tot = sum(data.a(f"ree_route_share_{r}", y) for r in ("bayan_obo", "ionic_clay", "monazite", "mt_weld"))
            premise(abs(tot - 1.0) < 1e-9, f"REE route shares sum to 1 in {y}: {tot!r}")

    def test_charge_factor_between_rule_bounds(self, data):
        for y in range(1982, 2026):
            ch = data.a("ree_charge_factor", y)
            premise(CHARGE_MAIN <= ch <= CHARGE_RADIO, f"charge factor {ch} in [{CHARGE_MAIN}, {CHARGE_RADIO}] (spec 6.2)")

    def test_od_series_not_above_national(self, data):
        for y in range(1988, 2026):
            if data.has("prod_copper_od", y, "AUS") and data.has("prod_copper", y, "AUS"):
                premise(data.a("prod_copper_od", y, "AUS") <= data.a("prod_copper", y, "AUS"), f"prod_copper_od <= prod_copper AUS in {y}")
            if data.has("u_production_od", y, "AUS") and data.has("u_production", y, "AUS"):
                premise(data.a("u_production_od", y, "AUS") <= data.a("u_production", y, "AUS"), f"u_production_od <= u_production AUS in {y}")
        premise(data.has("u_production_od", 2023, "AUS"), "u_production_od exists (uranium.csv, D74(a))")
        premise(data.rows[("prod_copper_od", "AUS", 2023)]["unit"] == "t", "prod_copper_od is in t")

    def test_bf_share_near_pig_iron_ratio(self, data):
        bad = []
        for y in range(1950, 2026):
            if data.has("prod_pig_iron", y) and data.has("prod_steel", y):
                d = abs(data.a("steel_bf_route_share", y) - data.a("prod_pig_iron", y) / data.a("prod_steel", y))
                if d > BF_PREMISE_TOL:
                    bad.append((y, round(d, 3)))
        premise(not bad, f"steel_bf_route_share within +-{BF_PREMISE_TOL} of prod_pig_iron/prod_steel (v1.1 13.11 sets 1950-69 from the ratio): {bad[:6]}")

    def test_ree_route_windows_start_in_1982(self, data):
        cf = data.cf
        for ore in ("ree_bayan_obo", "ree_ionic_clay", "ree_monazite"):
            premise(cf[cf.ore_type == ore].year_from.min() <= 1982, f"{ore} registry rows start in 1982 or earlier (13.9)")

    def test_capacity_and_intensity_units(self, data):
        for (s, c, y), r in data.rows.items():
            if s.startswith("cap_add_wind") or s.startswith("cap_add_solar_pv"):
                premise(r["unit"] == "GW" and c == "XWL", f"{s} is XWL GW")
            if s.startswith("mi_"):
                premise(r["unit"] == "t/GW" and c == "XWL", f"{s} is XWL t/GW")

    def test_intensity_series_cover_their_class_years(self, data):
        series = sorted({s for (s, c, y) in data.rows if s.startswith("mi_")})
        for s in series:
            ys = {y for (s2, c, y) in data.rows if s2 == s}
            lo = 1982 if "wind_on_" in s else 2001
            premise(ys == set(range(lo, 2026)), f"{s} has one row per year {lo}-2025 (spec 2.1 group I)")

    def test_rooftop_rule_concrete_zero_steel_half(self, data):
        for y in range(2001, 2026):
            premise(data.rows[("mi_pv_rooftop_cement", "XWL", y)]["c"] == 0, f"rooftop cement is 0 in {y} (Q12)")
            u = data.a("mi_pv_utility_steel", y)
            r = data.a("mi_pv_rooftop_steel", y)
            premise(math.isclose(r, 0.5 * u, rel_tol=1e-9), f"rooftop steel = 0.5 x utility in {y} (Q12): {r} vs {u}")

    def test_registry_file_is_header_only(self):
        df = pd.read_csv(ROOT / "data" / "factors" / "wind_solar.csv", dtype=str, keep_default_na=False)
        premise(len(df) == 0, f"data/factors/wind_solar.csv holds no value rows in v0.1 (spec 2.2); has {len(df)}")

    def test_events_wind_solar_rows_are_the_nine(self):
        ev = pd.read_csv(ROOT / "data" / "events.csv", dtype=str, keep_default_na=False)
        got = set(ev[ev.stream == "wind_solar"].event_id)
        premise(got == NINE_EVENTS, f"wind_solar events are exactly {sorted(NINE_EVENTS)}; got {sorted(got)} (Q18)")

    def test_implied_od_epsilon_inside_metal_tailings_triple(self):
        rt = pd.read_csv(ROOT / "data" / "reference" / "residue_types.csv", dtype=str, keep_default_na=False)
        mt = rt[rt.residue_type == "metal_tailings"].iloc[0]
        lo, hi = float(mt["epsilon_rn222_low"]), float(mt["epsilon_rn222_high"])
        premise(lo <= 0.004 <= hi, f"implied OD effective epsilon 0.004 lies in the metal_tailings triple [{lo}, {hi}] (B4)")

    def test_cu_co_notes_state_cobalt_hydroxide_uranium_not_counted(self, data):
        cf = data.cf
        txt = " ".join(cf[cf.ore_type == "cu_co_stratiform"].notes).lower()
        premise("cobalt hydroxide" in txt, "CU-C registry notes mention the uranium leaving in cobalt hydroxide (spec 7.2)")

    def test_fuel_inputs_file_is_reference_only(self):
        p = ROOT / "data" / "reference" / "commodity_fuel_inputs.csv"
        premise(p.is_file(), "data/reference/commodity_fuel_inputs.csv exists (D74(d))")
        df = pd.read_csv(p, dtype=str, keep_default_na=False)
        premise(len(df) == 5, f"commodity_fuel_inputs.csv has five rows (spec 7.1); has {len(df)}")


# --------------------------------------------------------------------------------------------
# (a) schema, row conventions, stages and technologies
# --------------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def issues(written):
    from pipeline.validate import validate

    root = _copy_tree(Path(written[0]).parent / "validation_root")
    shutil.copy(written[0], root / "data" / "streams" / "wind_solar.csv")
    found = validate(root, master_files=["data/streams/wind_solar.csv"])
    return [i for i in found if i.file == "data/streams/wind_solar.csv"]


class TestSchema:
    def test_validator_accepts_wind_solar_csv(self, issues):
        shown = "\n".join(f"  row {i.row}: {i.rule} {i.message}" for i in issues[:15])
        assert not issues, (
            f"wind_solar rows have {len(issues)} validator issues (rules {sorted({i.rule for i in issues})}):\n{shown}"
        )

    @pytest.mark.parametrize("rule", ["V03", "V07", "V09", "V11", "V12", "V13", "R02", "X01", "X02", "X03", "X05", "T04"])
    def test_no_rule_violations(self, issues, rule):
        hits = [i for i in issues if i.rule == rule]
        assert not hits, f"{len(hits)} {rule} issues, first: row {hits[0].row} {hits[0].message}"

    def test_committed_file_passes_the_validator(self):
        from pipeline.validate import validate

        committed = ROOT / "data" / "streams" / "wind_solar.csv.gz"
        assert committed.is_file(), "data/streams/wind_solar.csv.gz is not committed (WIND_SOLAR_SPEC 1; run --write)"
        found = [i for i in validate(ROOT, master_files=["data/streams/wind_solar.csv.gz"]) if "wind_solar" in str(i.file)]
        shown = "\n".join(f"  row {i.row}: {i.rule} {i.message}" for i in found[:10])
        assert not found, f"committed wind_solar.csv.gz has {len(found)} issues:\n{shown}"


class TestRowConventions:
    def test_rows_exist_and_have_the_master_columns(self, rows):
        assert rows.rows, "build() returned no rows"
        for r in rows.rows[:50]:
            assert set(r) == set(MASTER_COLS), f"row columns differ: {sorted(set(r) ^ set(MASTER_COLS))}"

    def test_years_from_the_first_capacity_year(self, rows):
        ys = sorted(rows.by_year)
        assert ys[0] >= 1982 and ys[-1] <= 2025, f"row years {ys[0]}-{ys[-1]}; spec 1: 1982-2025"
        assert 1982 in rows.by_year or 1989 in rows.by_year, "no rows in the first capacity years"

    def test_fixed_columns(self, rows):
        bad = []
        for r in rows.rows:
            if r["stream"] != "wind_solar" or r["stage"] != "commodity_supply":
                bad.append(f"stream/stage {r['stream']}/{r['stage']}")
            if r["quantity"] != "flow" or r["unit"] != "Bq/a" or r["basis"] != "modelled":
                bad.append(f"{describe(r)}: quantity/unit/basis {r['quantity']}/{r['unit']}/{r['basis']}")
            if as_bool(r["embedded_fuel"]):
                bad.append(f"embedded_fuel true: {describe(r)}")
            if not _blank(r["event_id"]):
                bad.append(f"event_id set: {describe(r)}")
            if r["technology"] != r["substream"]:
                bad.append(f"technology {r['technology']!r} != substream {r['substream']!r}: {describe(r)}")
        assert not bad, show(bad)

    def test_products_are_vocabulary_commodities(self, rows):
        voc = json.load(open(ROOT / "data" / "reference" / "vocab.json"))["commodities"]
        got = {r["product"] for r in rows.rows}
        assert got <= set(voc), f"products not in vocab.json commodities: {sorted(got - set(voc))}"
        assert got <= COMMODITIES, f"unexpected products: {sorted(got - COMMODITIES)}"
        assert "cobalt" not in got, "no row for cobalt (D74(b), 9(c)6)"

    def test_country_is_the_residue_location(self, rows):
        got = {r["country"] for r in rows.rows}
        assert got <= {"XXX", "AUS", "COD", "CHN", "MYS"}, f"countries {sorted(got)}; spec 3.1 allows XXX AUS COD CHN MYS (never XWL)"
        for r in rows.rows:
            if r["product"] == "copper" and r["residue_type"] == "metal_tailings":
                assert r["country"] in {"XXX", "AUS", "COD"}, describe(r)

    def test_tier_residue_route_rules(self, rows):
        bad = []
        for r in rows.rows:
            t = r["tier"]
            if t not in {"impounded", "dispersed", "liberated"}:
                bad.append(f"tier {t}: {describe(r)}")
            if t in {"impounded", "dispersed"} and (_blank(r["residue_type"]) or not _blank(r["route"])):
                bad.append(f"residue/route wrong for {t}: {describe(r)}")
            if t == "liberated" and (not _blank(r["residue_type"]) or _blank(r["route"])):
                bad.append(f"residue/route wrong for liberated: {describe(r)}")
            if r["group"] == "Rn222+" and t != "liberated":
                bad.append(f"Rn222+ outside liberated (V09): {describe(r)}")
        assert not bad, show(bad)

    def test_value_order_and_flag(self, rows):
        bad = []
        for r in rows.rows:
            lo, c, hi = vals(r)
            if not (0 <= lo <= c <= hi):
                bad.append(f"order {lo}, {c}, {hi}: {describe(r)}")
            if as_bool(r["below_detection"]) and lo != 0:
                bad.append(f"flagged with low > 0: {describe(r)}")
        assert not bad, show(bad)

    def test_factor_ids_resolve_and_match_the_row(self, rows, data):
        reg = {r.factor_id: r for r in data.cf.itertuples(index=False)}
        bad = []
        for r in rows.rows:
            fids = ids(r["factor_ids"])
            if not fids:
                bad.append(f"no factor_ids: {describe(r)}")
            for f in fids:
                if f not in reg:
                    bad.append(f"factor id {f} not in the registry: {describe(r)}")
                    continue
                g = reg[f]
                y = int(r["year"])
                if not (g.year_from <= y <= g.year_to):
                    bad.append(f"{f} window {g.year_from}-{g.year_to} excludes {y}")
                if g.commodity != r["product"] or g.group != r["group"] or g.tier != r["tier"]:
                    bad.append(f"{f} is {g.commodity}/{g.group}/{g.tier}, row {describe(r)}")
        assert not bad, show(bad)

    def test_source_ids_resolve(self, rows):
        src = pd.read_csv(ROOT / "data" / "sources.csv", dtype=str, keep_default_na=False)
        known = set(src.source_id)
        bad = {s for r in rows.rows for s in ids(r["source_ids"]) if s not in known}
        assert not bad, f"source_ids not in sources.csv: {sorted(bad)[:8]}"

    def test_unique_keys(self, rows):
        dup = [k for k, v in rows.by_key.items() if len(v) > 1]
        assert not dup, f"{len(dup)} duplicate master keys, first {dup[:2]}"

    def test_allocation_completeness_x03(self, rows):
        by = defaultdict(set)
        for r in rows.rows:
            k = rkey(r)[:-1]
            by[k].add(r["allocation_variant"])
        bad = [k for k, v in by.items() if v not in ({"default"}, set(VARIANTS))]
        assert not bad, f"{len(bad)} keys with a partial variant set (X03), first {bad[:2]}"
        for r in rows.rows:
            rule = ids(r["allocation_rule"])
            if r["allocation_variant"] == "default":
                assert rule in (["none"], ["alloc:value"]) or "alloc:value" in rule, describe(r)
            else:
                assert rule == [VAR_RULE[r["allocation_variant"]]], f"{describe(r)}: rule {rule}"


class TestStagesTechnologies:
    def test_only_commodity_supply_and_both_substreams(self, rows):
        assert {r["stage"] for r in rows.rows} == {"commodity_supply"}
        assert {r["substream"] for r in rows.rows} == {"wind", "solar"}
        assert not rows.find(stage="end_of_life"), "end_of_life has no rows (spec 7.3)"

    def test_substream_commodities_follow_the_intensity_files(self, rows, data):
        allowed = defaultdict(set)
        for (s, c, y) in data.rows:
            if s.startswith("mi_"):
                for k, (sub, *_rest) in Data.CLS.items():
                    if s.startswith(f"mi_{k}_"):
                        allowed[sub].add(s[len(f"mi_{k}_") :])
        bad = [describe(r) for r in rows.rows if r["product"] not in allowed[r["substream"]]]
        assert not bad, show(bad)

    def test_ree_is_wind_only_and_solar_ree_absent(self, rows):
        assert not rows.find(substream="solar", product="ree_oxide"), "solar REE is reported as 0 / no rows (spec 5.2)"
        assert rows.find(substream="wind", product="ree_oxide"), "no wind REE rows"


# --------------------------------------------------------------------------------------------
# (b) coverage and the row-by-row oracle comparison
# --------------------------------------------------------------------------------------------
class TestRowsAgainstOracle:
    def test_row_count_matches_the_oracle(self, rows, expected):
        assert len(rows.rows) == len(expected.rows), (
            f"build() has {len(rows.rows)} rows, the oracle expects {len(expected.rows)} "
            "(every family x registry combination x variant x year with a driver)"
        )

    @pytest.mark.parametrize("fam", sorted(set(FAMILY_CODE.values())))
    def test_family_rows_equal_oracle(self, comparison, fam):
        bad = comparison.get(fam, [])
        assert not bad, f"family {fam}: " + show(bad)

    def test_no_unexpected_rows(self, comparison):
        bad = comparison.get("unexpected", [])
        assert not bad, show(bad)

    def test_wind_rows_absent_in_zero_capacity_years(self, rows, data):
        zero = [
            y for y in range(1982, 2026)
            if all(
                (not data.has(s, y)) or data.rows[(s, "XWL", y)]["high"] == 0
                for s in ("cap_add_wind_onshore", "cap_add_wind_offshore")
            )
        ]
        assert zero, "premise: some year has exactly zero wind capacity (1988 today)"
        bad = [y for y in zero if rows.find(y, substream="wind")]
        assert not bad, f"wind rows exist in years whose capacity driver is exactly 0/0/0: {bad} (13.3)"


class TestCoverage:
    def test_committed_log_has_no_no_factor(self, log, expected):
        assert not expected.log["no_factor"], f"premise: registry windows cover every computed contribution (13.9); oracle gaps {sorted(expected.log['no_factor'])[:3]}"
        assert not log_entries(log, "no_factor"), f"committed log has no_factor entries (9(b)): {log_entries(log, 'no_factor')[:2]}"

    def test_every_registry_combination_is_present_each_driver_year(self, rows, expected):
        """For each (family, year, substream) with a driver, every registry (group, tier, route, residue) combination exists."""
        have = defaultdict(set)
        for r in rows.rows:
            have[(int(r["year"]), r["substream"], r["product"], r["country"])].add(
                (r["group"], r["tier"], r["route"] or "", r["residue_type"] or "")
            )
        want = defaultdict(set)
        for k in expected.rows:
            y, sub, c, rs, cty, g, t, rt, v = k
            want[(y, sub, c, cty)].add((g, t, rt, rs))
        bad = [f"{k}: missing {sorted(w - have.get(k, set()))[:2]}" for k, w in want.items() if w - have.get(k, set())]
        assert not bad, show(bad)

    def test_methods_43_candidates_appear_in_2020(self, rows):
        groups = {r["group"] for r in rows.by_year.get(2020, [])}
        need = {"U238+", "U234", "Th230", "Ra226+", "U235+", "Th232", "Ra228+", "Th228+", "Pb210+", "Po210", "Rn222+"}
        assert need <= groups, f"METHODS 4.3 candidates missing from the 2020 rows: {sorted(need - groups)}"

    def test_report_commodities_under_0p1_percent_in_every_decade(self, rows, record_property):
        """Q16 report: lists every commodity under 0.1 % of the stream in every decade (default and single-product rows)."""
        tot = defaultdict(float)
        by = defaultdict(float)
        for r in rows.rows:
            if r["allocation_variant"] != "default":
                continue
            d = int(r["year"]) // 10 * 10
            v = float(r["value_central"])
            tot[d] += v
            by[(d, r["product"])] += v
        assert tot, "no default rows"
        decades = sorted(tot)
        prods = sorted({p for (_, p) in by})
        under = [p for p in prods if all(by.get((d, p), 0.0) < 1e-3 * tot[d] for d in decades)]
        report = {p: {d: by.get((d, p), 0.0) / tot[d] for d in decades} for p in prods}
        record_property("commodities_under_0.1pct_in_every_decade", ",".join(under))
        print("\nQ16 report, commodities under 0.1 % in every decade:", under)
        for d in decades:
            print(f"  {d}s total {tot[d]:.3e} Bq/a; " + ", ".join(f"{p} {report[p][d]:.2%}" for p in prods if report[p][d] > 0))
        assert abs(sum(report[p][decades[-1]] for p in prods) - 1.0) < 1e-9


# --------------------------------------------------------------------------------------------
# (c) conservation and identities, from the rows and the files
# --------------------------------------------------------------------------------------------
def row_c(rows: Rows, y, sub, c, cty, g, tier, residue="", route="", v="default") -> dict:
    return rows.one(
        y, substream=sub, product=c, country=cty, group=g, tier=tier, residue_type=residue, route=route,
        allocation_variant=v,
    )


def cu_groups(D: Data, ore: str, region: str) -> list:
    d = D.cf[(D.cf.commodity == "copper") & (D.cf.ore_type == ore) & (D.cf.region == region)]
    return sorted(set(d.group))


YEARS = [2001, 2005, 2010, 2019, 2020, 2023, 2025]


class TestClassShares:
    def test_shares_sum_to_one(self, data):
        bad = class_share_sum_problems(data)
        assert not bad, show(bad)

    @pytest.mark.parametrize("sub", ["wind", "solar"])
    @pytest.mark.parametrize("y", YEARS)
    def test_porphyry_family_rows_are_tonnes_times_share_times_factor_times_d6(self, rows, data, sub, y):
        M = data.tonnes_c(y, sub, "copper")
        s = data.a("cu_class_share_porphyry_stratiform", y)
        d6 = data.a("d6_value_share_copper_porphyry", y)
        for g in cu_groups(data, "porphyry_stratiform", "XWL"):
            F = data.fac("copper", g, "impounded", y, ore="porphyry_stratiform", residue="metal_tailings")["c"]
            for v, share in (("default", d6), ("bound_main", 1.0), ("bound_radio", 0.0)):
                r = row_c(rows, y, sub, "copper", "XXX", g, "impounded", "metal_tailings", "", v)
                want = M * s * F * share
                assert close(float(r["value_central"]), want, 1e-7), f"{sub} {y} {g} {v}: {r['value_central']} vs M*s*F*share = {want}"

    @pytest.mark.parametrize("y", YEARS)
    def test_cu_co_family_rows(self, rows, data, y):
        M = data.tonnes_c(y, "wind", "copper")
        s = data.a("cu_class_share_cu_co_stratiform", y)
        d6 = data.a("d6_value_share_copper_cu_co", y, "COD")
        for g in cu_groups(data, "cu_co_stratiform", "COD"):
            F = data.fac("copper", g, "impounded", y, ore="cu_co_stratiform", region="COD", residue="metal_tailings")["c"]
            r = row_c(rows, y, "wind", "copper", "COD", g, "impounded", "metal_tailings", "", "default")
            assert close(float(r["value_central"]), M * s * F * d6, 1e-7), f"CU-C {g} {y}"

    @pytest.mark.parametrize("y", YEARS)
    def test_smelter_family_uses_the_whole_copper_tonnage(self, rows, data, y):
        M = data.tonnes_c(y, "solar", "copper")
        d6 = data.a("d6_value_share_copper_porphyry", y)
        F = data.fac("copper", "Ra226+", "impounded", y, ore="all", residue="smelter_slag")["c"]
        r = row_c(rows, y, "solar", "copper", "XXX", "Ra226+", "impounded", "smelter_slag", "", "default")
        assert close(float(r["value_central"]), M * F * d6, 1e-7), "CU-SM applies to the whole copper tonnage with the porphyry D6 share (5.1)"
        for g in ("Pb210+", "Po210"):
            Fs = data.fac("copper", g, "liberated", y, ore="all", route="air_stack")["c"]
            rr = row_c(rows, y, "solar", "copper", "XXX", g, "liberated", "", "air_stack", "default")
            assert close(float(rr["value_central"]), M * Fs * d6, 1e-7)


class TestReeRoutes:
    ROUTES = {
        "ree_bayan_obo": ("CHN", True), "ree_ionic_clay": ("CHN", False),
        "ree_monazite": ("XWL", True), "ree_mt_weld": ("MYS", False),
    }

    @pytest.mark.parametrize("y", [2005, 2012, 2015, 2020, 2025])
    def test_route_rows_apply_route_share_and_charge_factor_once(self, rows, data, y):
        M = data.tonnes_c(y, "wind", "ree_oxide")
        ch = data.a("ree_charge_factor", y)
        checked = 0
        for ore, (region, joint) in self.ROUTES.items():
            share = data.a(f"ree_route_share_{ore[4:]}", y)
            d = data.cf[(data.cf.ore_type == ore) & (data.cf.year_from <= y) & (data.cf.year_to >= y)]
            for r0 in d.itertuples(index=False):
                F = r0.value_central
                cty = "XXX" if region == "XWL" else region
                got = rows.find(
                    y, substream="wind", product="ree_oxide", country=cty, group=r0.group, tier=r0.tier,
                    residue_type=r0.residue_type, route=r0.route, allocation_variant="default",
                )
                if share == 0:
                    assert not got, f"{ore} {r0.group} {y}: route share 0 gives no rows (13.3)"
                    continue
                assert len(got) == 1, f"{ore} {r0.group} {r0.tier} {y}: {len(got)} rows"
                d6 = data.a(f"d6_value_share_{ore}", y, region) if joint else 1.0
                want = M * share * ch * F * d6
                assert close(float(got[0]["value_central"]), want, 1e-7), (
                    f"{ore} {r0.group} {y}: {got[0]['value_central']} vs M*route*charge*F*D6 = {want} (charge applied once, 6.2)"
                )
                checked += 1
        assert checked, f"nothing checked in {y}"

    @pytest.mark.parametrize("y", [2015, 2020])
    def test_charge_variants_default_main_radio(self, rows, data, y):
        M = data.tonnes_c(y, "wind", "ree_oxide")
        ch = data.a("ree_charge_factor", y)
        share = data.a("ree_route_share_bayan_obo", y)
        d6 = data.a("d6_value_share_ree_bayan_obo", y, "CHN")
        F = data.fac("ree_oxide", "Th232", "impounded", y, ore="ree_bayan_obo", region="CHN", residue="ree_tailings")["c"]
        base = M * share * F
        r = {v: row_c(rows, y, "wind", "ree_oxide", "CHN", "Th232", "impounded", "ree_tailings", "", v) for v in VARIANTS}
        assert close(float(r["default"]["value_central"]), base * ch * d6, 1e-7), "default = D6 share x charge factor (0.70 x 2.5)"
        assert vals(r["bound_main"]) == (0.0, 0.0, 0.0) and not as_bool(r["bound_main"]["below_detection"]), "bound_main = 0 x 1: structural zero"
        assert close(float(r["bound_radio"]["value_central"]), base * CHARGE_RADIO * 1.0, 1e-7), "bound_radio = 1 x 5.9 (6.2)"


class TestAllocation:
    def _keys(self, rows: Rows):
        keys = defaultdict(dict)
        for r in rows.rows:
            keys[rkey(r)[:-1]][r["allocation_variant"]] = r
        return {k: v for k, v in keys.items() if len(v) == 3}

    def test_joint_keys_have_all_three_variants(self, rows):
        joint_products = {"copper", "zinc", "silver"}
        part = [k for k, vs in self._keys(rows).items() if k[2] in joint_products]
        assert part, "no joint keys found"
        # every copper, zinc and silver key must be complete
        cnt = Counter()
        for r in rows.rows:
            if r["product"] in joint_products:
                cnt[rkey(r)[:-1]] += 1
        bad = [k for k, n in cnt.items() if n != 3]
        assert not bad, f"{len(bad)} copper/zinc/silver keys without three variants, first {bad[:2]}"

    def test_main_product_commodities_bound_radio_is_exact_zero_and_main_is_whole(self, rows, data):
        """Cu and Zn are the main product of their pools (Q3): bound_radio = 0, bound_main = whole value, default in between."""
        bad = []
        for k, vs in self._keys(rows).items():
            y, sub, c, rs, cty, g, t, rt = k
            if c not in ("copper", "zinc"):
                continue
            main, rad, dflt = vs["bound_main"], vs["bound_radio"], vs["default"]
            if vals(rad) != (0.0, 0.0, 0.0) or as_bool(rad["below_detection"]) or "below_detection" in (rad["notes"] or ""):
                bad.append(f"{k}: bound_radio is not an unflagged structural zero")
            if not (float(dflt["value_central"]) <= float(main["value_central"]) * (1 + 1e-12)):
                bad.append(f"{k}: default above the whole value")
            if float(main["value_central"]) == float(rad["value_central"]) and float(main["value_central"]) != 0:
                bad.append(f"{k}: bound_main equals bound_radio")
        assert not bad, show(bad)

    def test_radio_product_commodities_bound_main_is_exact_zero_and_radio_is_whole(self, rows):
        """REE (Bayan Obo, monazite) and silver are the radioactivity-bearing product: bound_main = 0, bound_radio = the whole value."""
        bad = []
        n = 0
        for k, vs in self._keys(rows).items():
            y, sub, c, rs, cty, g, t, rt = k
            if c not in ("ree_oxide", "silver"):
                continue
            n += 1
            main, rad = vs["bound_main"], vs["bound_radio"]
            if vals(main) != (0.0, 0.0, 0.0) or as_bool(main["below_detection"]) or "below_detection" in (main["notes"] or ""):
                bad.append(f"{k}: bound_main is not an unflagged structural zero")
            if float(rad["value_central"]) <= 0:
                bad.append(f"{k}: bound_radio is not positive")
        assert n, "no REE/silver joint keys"
        assert not bad, show(bad)

    @pytest.mark.parametrize("y", [2010, 2020])
    def test_default_equals_whole_value_times_the_share_series(self, rows, data, y):
        for sub, c, ser, cty, g, tier, rs, scale_by in (
            ("wind", "zinc", "d6_value_share_zinc", "XXX", "U238+", "impounded", "metal_tailings", None),
            ("solar", "silver", "d6_value_share_silver", "XXX", "U238+", "impounded", "metal_tailings", None),
        ):
            share = data.a(ser, y)
            vs = {v: row_c(rows, y, sub, c, cty, g, tier, rs, "", v) for v in VARIANTS}
            whole = max(float(vs["bound_main"]["value_central"]), float(vs["bound_radio"]["value_central"]))
            assert whole > 0
            assert close(float(vs["default"]["value_central"]), whole * share, 1e-7), f"{c} {y}: default != whole x {ser}"
            for b in range(3):
                assert close(vals(vs["default"])[b], whole_b(vs, b) * share, 1e-7), f"{c} {y}: bound {b} of default"

    def test_rest_of_joint_products_have_no_rows(self, rows):
        """Spec 6.1: the other products of the mine are not stream-4 products and get no rows."""
        assert not {r["product"] for r in rows.rows} & {"gold", "molybdenum", "lead", "uranium", "cobalt", "niobium", "iron"}


def whole_b(vs, b):
    return max(vals(vs["bound_main"])[b], vals(vs["bound_radio"])[b])


class TestOdMerge:
    """CU-OD and CU-A share the AUS master key: merged after the D6 split, variant by variant (3.2, 6.3)."""

    def _parts(self, data, y, sub, g):
        M = data.tonnes_c(y, sub, "copper")
        s_od = data.od_share(y)
        s_ph = data.a("cu_class_share_iocg_high_u", y)
        out = {}
        w = data.a("od_value_share_u", y, "AUS") if data.has("od_value_share_u", y, "AUS") else None
        if s_od > 0:
            F = data.fac("copper", g, "impounded", y, ore="iocg_olympic_dam", region="AUS", residue="metal_tailings")
            out["od"] = (M * s_od * F["c"], F["fid"], 1.0 - w)
        if s_ph > 0:
            F = data.fac("copper", g, "impounded", y, ore="iocg_high_u", region="AUS", residue="metal_tailings")
            out["ph"] = (M * s_ph * F["c"], F["fid"], data.a("d6_value_share_copper_iocg_ph_cp", y, "AUS"))
        return out

    @pytest.mark.parametrize("sub", ["wind", "solar"])
    @pytest.mark.parametrize("y", [1990, 2005, 2009, 2015, 2019, 2023, 2025])
    def test_merged_rows_are_the_sum_of_the_two_ledgers(self, rows, data, sub, y):
        if sub == "solar" and y < 2001:
            pytest.skip("no PV before 2001 (Q9)")
        for g in ("Ra226+", "Th232", "U238+"):
            parts = self._parts(data, y, sub, g)
            assert parts, f"no OD or PH/CP part in {y}"
            want = {
                "default": sum(p[0] * p[2] for p in parts.values()),
                "bound_main": sum(p[0] for p in parts.values()),
                "bound_radio": 0.0,
            }
            for v in VARIANTS:
                r = row_c(rows, y, sub, "copper", "AUS", g, "impounded", "metal_tailings", "", v)
                assert close(float(r["value_central"]), want[v], 1e-7), f"{sub} {y} {g} {v}: {r['value_central']} vs {want[v]}"
                got_ids = ids(r["factor_ids"])
                want_ids = [p[1] for p in sorted(parts.values(), key=lambda p: p[1])]
                assert got_ids == want_ids, f"factor_ids {got_ids}, expected both factors in registry order {want_ids}"
                for o, name in (("od", "iocg_olympic_dam"), ("ph", "iocg_high_u")):
                    assert (o in parts) == (name in (r["notes"] or "")), f"notes {r['notes']!r} must name exactly the ore types present: {sorted(parts)}"
            assert vals(row_c(rows, y, sub, "copper", "AUS", g, "impounded", "metal_tailings", "", "bound_radio")) == (0.0, 0.0, 0.0)


class TestMerge:
    """(c)5 and 4.2 steps 4-6: the factor is applied per class, then the classes are summed with sum_correlated (13.12)."""

    @pytest.mark.parametrize("sub,c", [("wind", "aluminium"), ("wind", "steel"), ("solar", "aluminium"), ("solar", "steel")])
    @pytest.mark.parametrize("y", [2010, 2020])
    def test_class_merge(self, rows, data, sub, c, y):
        if c == "aluminium":
            g, tier, rs, rt = "Ra226+", "dispersed", "red_mud", ""
            extra = ()
        else:
            g, tier, rs, rt = "Po210", "liberated", "", "air_stack"
            extra = (b_of(data, "steel_bf_route_share", y),)
        F = fb(data.fac(c, g, tier, y, residue=rs, route=rt))
        parts = class_terms(data, y, sub, c, extra, F)
        assert len(parts) >= 2, f"{sub} {c} {y}: needs several classes to be a merge test"
        want = sum_correlated(parts)
        r = row_c(rows, y, sub, c, "XXX", g, tier, rs, rt, "default")
        assert_row_is_one_of(r, [want], label=f"{sub} {c} {y} merge")


class TestNoDoubleCount:
    def test_no_embedded_fuel_no_bottom_ash_no_end_of_life(self, rows):
        assert not [r for r in rows.rows if as_bool(r["embedded_fuel"])]
        assert not [r for r in rows.rows if r["residue_type"] == "coal_bottom_ash"]
        assert not rows.find(stage="end_of_life")

    def test_no_exhalation_seepage_or_transfer_routes(self, rows):
        assert {r["route"] for r in rows.rows if r["route"]} == {"air_stack"}, "only the stack route (METHODS 5.2)"
        assert not [r for r in rows.rows if "transfer" in r["tier"] or r["tier"].startswith("memo")]

    def test_cement_rows_are_kiln_stack_only(self, rows):
        for r in rows.find(product="cement"):
            assert r["tier"] == "liberated" and r["route"] == "air_stack" and _blank(r["residue_type"]), describe(r)

    def test_no_uranium_product_or_u_stage_rows(self, rows):
        assert not [r for r in rows.rows if r["product"] == "uranium" or str(r["stage"]).startswith("u_")]

    def test_only_commodity_factor_ids(self, rows):
        bad = {f for r in rows.rows for f in ids(r["factor_ids"]) if not f.startswith("commodity:")}
        assert not bad, f"factor ids from other registries: {sorted(bad)[:5]}"

    def test_superseded_ore_types_are_not_in_use(self, rows, data):
        reg = {r.factor_id: r for r in data.cf.itertuples(index=False)}
        used = {reg[f].ore_type for r in rows.rows for f in ids(r["factor_ids"]) if f in reg}
        assert used <= ORE_TYPES_COPPER | ORE_TYPES_REE | {""}, f"ore types used by rows: {sorted(used)}"
        assert "superseded" not in " ".join(data.cf.basis.astype(str)).lower(), "a superseded row was applied into data/ (spec 12 R1)"

    def test_steel_stack_rows_use_the_bf_share_not_the_gross_tonnage(self, rows, data):
        y = 2020
        for sub in ("wind", "solar"):
            M = data.tonnes_c(y, sub, "steel")
            bf = data.a("steel_bf_route_share", y)
            F = data.fac("steel", "Po210", "liberated", y, route="air_stack")["c"]
            r = row_c(rows, y, sub, "steel", "XXX", "Po210", "liberated", "", "air_stack", "default")
            assert close(float(r["value_central"]), M * bf * F, 1e-7)


class TestEmbeddedFuel:
    def test_fuel_inputs_reference_file_never_leaks_into_rows(self, rows):
        assert not [r for r in rows.rows if as_bool(r["embedded_fuel"])]
        assert not [r for r in rows.rows if any(f.startswith("coal:") or f.startswith("oil_gas:") for f in ids(r["factor_ids"]))]

    def test_fuel_inputs_values_are_reference_only(self):
        df = pd.read_csv(ROOT / "data" / "reference" / "commodity_fuel_inputs.csv", dtype=str, keep_default_na=False)
        assert set(zip(df.commodity, df.fuel)) == {
            ("steel", "coal"), ("cement", "coal"), ("silicon_mg", "coal"), ("aluminium", "electricity"), ("silicon_mg", "electricity"),
        }


@pytest.fixture(scope="module")
def f8():
    rows = TestOdIdentity._nuclear_f8()
    if not rows:
        pytest.skip("contingent: NUCLEAR_SPEC 14 (F8 Olympic Dam nuclear ledger) is not built in data/streams/nuclear.csv.gz")
    return rows


class TestOdIdentity:
    """(c)4: F8 of the nuclear stream plus the copper ledger plus the military remainder equal the OD pool, 1988-2025.
    Contingent on NUCLEAR_SPEC 14: skipped with a reason while data/streams/nuclear.csv.gz carries no F8 row."""

    @staticmethod
    def _nuclear_f8():
        p = ROOT / "data" / "streams" / "nuclear.csv.gz"
        if not p.exists():
            return None
        with gzip.open(p, "rt", newline="", encoding="utf-8") as fh:
            rows = [r for r in csv.DictReader(fh) if str(r.get("notes", "")).startswith("F8")]
        return rows or None

    @staticmethod
    def _a(data, y, v):
        return {"default": data.a("od_value_share_u", y, "AUS"), "bound_main": 0.0, "bound_radio": 1.0}[v]

    def test_one_f8_row_per_year_group_variant(self, f8, data):
        groups = sorted(set(data.cf[data.cf.ore_type == "iocg_olympic_dam"].group))
        assert len(groups) == 10, f"premise: ten OD groups, got {groups}"
        cnt = Counter((int(r["year"]), r["group"], r["allocation_variant"]) for r in f8)
        want = {(y, g, v) for y in range(1988, 2026) for g in groups for v in VARIANTS}
        assert set(cnt) == want, f"F8 keys differ: missing {sorted(want - set(cnt))[:3]}, extra {sorted(set(cnt) - want)[:3]}"
        assert len(f8) == 38 * 10 * 3 == 1140 and set(cnt.values()) == {1}, f"{len(f8)} F8 rows, duplicates {[k for k, n in cnt.items() if n > 1][:3]}"

    def test_f8_row_conventions(self, f8, data):
        bad = []
        for r in f8:
            y, g = int(r["year"]), r["group"]
            fid = data.fac("copper", g, "impounded", y, ore="iocg_olympic_dam", region="AUS", residue="metal_tailings")["fid"]
            if (r["country"], r["stage"], r["tier"], r["residue_type"], r["quantity"], r["unit"]) != ("AUS", "u_milling", "impounded", "metal_tailings", "flow", "Bq/a"):
                bad.append(f"{y} {g}: {r['country']}/{r['stage']}/{r['tier']}/{r['residue_type']}")
            if ids(r["factor_ids"]) != [fid]:
                bad.append(f"{y} {g}: factor_ids {r['factor_ids']} != CU-OD factor {fid}")
        assert not bad, show(bad)

    def test_pool_identity_with_military_remainder_1988_2025(self, f8, data):
        bad = []
        for r in f8:
            y, v, g = int(r["year"]), r["allocation_variant"], r["group"]
            P = data.a("prod_copper_od", y, "AUS") * data.fac("copper", g, "impounded", y, ore="iocg_olympic_dam", region="AUS", residue="metal_tailings")["c"]
            a = self._a(data, y, v)
            phi = data.a("phi_civil", y)
            total = float(r["value_central"]) + (1 - a) * P + a * (1 - phi) * P
            if not close(total, P, 1e-5):
                bad.append(f"{y} {g} {v}: F8 {r['value_central']} + copper {(1 - a) * P:.6g} + military {a * (1 - phi) * P:.6g} != pool {P:.6g}")
        assert not bad, show(bad)

    def test_nuclear_log_military_remainder_entries(self, f8, data):
        p = ROOT / "research" / "nuclear" / "build_log.csv"
        assert p.is_file(), "research/nuclear/build_log.csv missing"
        with open(p, newline="", encoding="utf-8") as fh:
            ents = [e for e in csv.DictReader(fh) if e.get("kind") == "od_military_remainder"]
        want = {}
        for y in range(1988, 2026):
            phi = data.a("phi_civil", y)
            for v in ("default", "bound_radio"):  # bound_main has a_v = 0: no remainder
                x = self._a(data, y, v) * (1 - phi)
                if x > 0:
                    want[(y, v)] = x
        got = {}
        for e in ents:
            m = re.match(r"^(default|bound_main|bound_radio)\b[^=]*=\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", e["detail"])
            assert m, f"od_military_remainder detail should start with the variant and a_v*(1-phi): {e}"
            assert e["country"] == "AUS", e
            got[(int(e["year"]), m.group(1))] = float(m.group(2))
        assert set(got) == set(want), f"od_military_remainder (year, variant) differ: missing {sorted(set(want) - set(got))[:3]}, extra {sorted(set(got) - set(want))[:3]}"
        for k, x in want.items():
            assert close(got[k], x, 1e-3), f"{k}: logged a_v*(1-phi) {got[k]} vs {x}"


# --------------------------------------------------------------------------------------------
# (d) determinism, negligibility, events, pre-2001 PV
# --------------------------------------------------------------------------------------------
class TestDeterminism:
    def test_two_in_process_builds_are_identical(self, ws_mod, result):
        again = ws_mod.build(ROOT)
        assert json.dumps(list(again.rows), sort_keys=True, default=str) == json.dumps(list(result.rows), sort_keys=True, default=str)
        assert json.dumps(list(again.log), sort_keys=True, default=str) == json.dumps(list(result.log), sort_keys=True, default=str)

    def test_written_rows_in_schema_key_order(self, written):
        cols = [
            "year", "stream", "substream", "stage", "product", "residue_type", "country", "group", "tier", "quantity",
            "allocation_variant", "embedded_fuel", "technology", "route", "event_id",
        ]
        with open(written[0], newline="", encoding="utf-8") as fh:
            data = list(csv.DictReader(fh))
        assert data

        def key(r):
            return tuple((int(r[c]),) if c == "year" else ((0, "") if r[c] == "" else (1, r[c])) for c in cols)

        keys = [key(r) for r in data]
        assert keys == sorted(keys), "rows are not in SCHEMA 3 unique-key order"
        assert len(keys) == len(set(keys))

    def test_second_build_in_a_fresh_process_is_byte_identical_and_silent(self, written, log):
        code = (
            "import sys, hashlib, json\n"
            "from pathlib import Path\n"
            "from pipeline.streams.wind_solar import build\n"
            "from pipeline.lib.rows import write_master\n"
            "r = build(Path(sys.argv[1]))\n"
            "d = Path(sys.argv[2]); write_master(list(r.rows), d / 'm.csv'); write_master(list(r.rows_pre1950), d / 'p.csv')\n"
            "h = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()\n"
            "print(json.dumps({'m': h(d / 'm.csv'), 'p': h(d / 'p.csv'), 'log': json.loads(json.dumps(r.log, default=str))}))\n"
        )
        out = Path(written[0]).parent / "second"
        out.mkdir(exist_ok=True)
        p = subprocess.run(
            [sys.executable, "-W", "default", "-c", code, str(ROOT), str(out)],
            cwd=str(ROOT), env=_env(), capture_output=True, text=True, timeout=3000, check=False,
        )
        assert p.returncode == 0, p.stderr[-1500:]
        assert p.stderr == "", f"build() wrote {len(p.stderr)} bytes to stderr (inherited 3.7): {p.stderr[:600]!r}"
        got = json.loads(p.stdout.strip().splitlines()[-1])
        h = lambda q: hashlib.sha256(Path(q).read_bytes()).hexdigest()
        assert got["m"] == h(written[0]), "master bytes differ between builds"
        assert got["p"] == h(written[1]), "pre-1950 bytes differ between builds"
        assert got["log"] == json.loads(json.dumps(log, default=str)), "log differs (or is ordered differently) between builds"


class TestNegligibility:
    def test_no_end_of_life_and_no_thin_film_rows(self, rows):
        """Spec 7.3 and 9(d): end_of_life and thin film are negligible; the statement itself has no checkable place (S8)."""
        assert not rows.find(stage="end_of_life")
        assert not {r["product"] for r in rows.rows} & {"tellurium", "cadmium", "indium", "gallium", "selenium"}

    def test_csp_has_no_rows(self, rows, data):
        # capacity_additions has CSP capacity but no CSP intensity: nothing can be attributed (no_intensity)
        assert not [s for (s, c, y) in data.rows if s.startswith("mi_") and "csp" in s]
        assert rows.find(substream="solar"), "PV rows must still exist"


class TestPre2001Pv:
    def test_pre_2001_pv_is_absent(self, rows):
        early = [r for r in rows.find(substream="solar") if int(r["year"]) < 2001]
        assert not early, f"{len(early)} solar rows before 2001 (Q9: PV rows 2001-2025), first {describe(early[0]) if early else ''}"
        assert min(int(r["year"]) for r in rows.find(substream="solar")) >= 2001

    def test_years_before_a_series_first_year_are_silent(self, log):
        """13.13: no_driver only for a missing year inside a series' span; the PV and offshore series start in 2001."""
        bad = [e for e in log_entries(log, "no_driver") if any(1950 <= y <= 2000 for y in entry_years(e)) and re.match(r"cap_add_(solar_pv|wind_offshore)", str(e["detail"]))]
        assert not bad, f"no_driver before the first capacity year: {bad[:2]}"


class TestEventsNotTransferred:
    def test_no_event_ids_no_transfer_rows(self, rows):
        assert not [r for r in rows.rows if not _blank(r["event_id"])], "wind_solar events are markers only (Q18)"
        assert not [r for r in rows.rows if "transfer" in str(r["tier"]) or "transfer" in str(r["stage"])]

    def test_events_file_untouched_and_unneeded(self, ws_mod, tmp_path):
        """build() reads no event: a tree without events.csv builds (also see the mini trees)."""
        root = make_mini(tmp_path, (2020,))
        assert not (root / "data" / "events.csv").exists()
        res = ws_mod.build(root)
        assert res.rows


# --------------------------------------------------------------------------------------------
# (b)/(3.3) notes and flags
# --------------------------------------------------------------------------------------------
class TestNotesAndFlags:
    def test_flagged_rows_carry_a_cause_last(self, rows):
        bad = []
        for r in rows.rows:
            n = r["notes"] or ""
            if as_bool(r["below_detection"]):
                if not re.search(r"; below_detection cause: [a-z_+]+$", n):
                    bad.append(f"{describe(r)}: {n[-80:]!r}")
            elif "below_detection cause" in n:
                bad.append(f"cause text on unflagged row: {describe(r)}")
        assert not bad, show(bad)

    def test_structural_zero_rows_are_unflagged(self, rows):
        zeros = [r for r in rows.rows if vals(r) == (0.0, 0.0, 0.0)]
        assert zeros, "bound rows with a share of 0 must exist as structural zeros"
        for r in zeros:
            assert not as_bool(r["below_detection"]), f"structural zero flagged: {describe(r)}"
            assert r["allocation_variant"] in ("bound_main", "bound_radio"), f"unexpected zero row {describe(r)}"

    def test_family_code_prefixes(self, rows):
        bad = [describe(r) for r in rows.rows if not (r["notes"] or "").startswith(FAMILY_CODE[r["product"]] + ": ")]
        assert not bad, show(bad)

    def test_share_basis_placeholder_on_every_row_with_a_placeholder_share(self, rows):
        miss = [describe(r) for r in rows.rows if "; share basis: placeholder" not in (r["notes"] or "")]
        assert not miss, f"{len(miss)} rows lack '; share basis: placeholder' although every class share is a placeholder: " + show(miss)

    def test_allocation_basis_only_on_default_joint_rows(self, rows):
        for r in rows.rows:
            has = "; allocation basis: placeholder" in (r["notes"] or "")
            joint_default = r["allocation_variant"] == "default" and ids(r["allocation_rule"]) != ["none"]
            if has:
                assert joint_default, describe(r)
            elif joint_default:
                pytest.fail(f"default joint row without allocation basis placeholder (every D6 share is a placeholder): {describe(r)}")


# --------------------------------------------------------------------------------------------
# (8) log
# --------------------------------------------------------------------------------------------
def check_runs(log, kind, want: dict, ident) -> list[str]:
    """Exact comparison of aggregated run entries (13.14): one entry per run, year = first year, detail '<series>: a-b (n years)'.
    ident(key) -> (country, group, series-or-detail-prefix)."""
    from wind_solar_oracle import runs

    exp = set()
    for k, ys in want.items():
        country, group, name = ident(k)
        for a, b in runs(ys):
            exp.add((a, country, group, f"{name}: {a}-{b} ({b - a + 1} years)"))
    got = set()
    msgs = []
    for e in log_entries(log, kind):
        got.add((e["year"], e["country"], e["group"], re.sub(r"\((\d+) years?\)", r"(\1 years)", str(e["detail"]))))
    for x in sorted(exp - got)[:4]:
        msgs.append(f"{kind}: missing entry {x}")
    for x in sorted(got - exp)[:4]:
        msgs.append(f"{kind}: unexpected entry {x}")
    return msgs


class TestLog:
    def test_entry_shape(self, log):
        assert log, "the log is empty (attribution entries are always written)"
        for e in log:
            assert set(e) == {"kind", "year", "country", "group", "detail"}, f"log keys {sorted(e)}"
            assert e["kind"] in LOG_KINDS, f"unknown log kind {e['kind']!r}"
            assert e["country"] != "XWL", f"log uses XWL instead of XXX: {e}"
            if e["kind"] == "lib_warning":
                assert e["year"] in ("", None) and e["country"] in ("", None), f"lib_warning year/country must be empty: {e}"

    def test_no_family_absent_in_the_committed_tree(self, log):
        assert not log_entries(log, "no_family"), f"no_family entries: {log_entries(log, 'no_family')[:2]}"

    def test_no_footprint_absent_in_the_committed_tree(self, log):
        assert not log_entries(log, "no_footprint"), "every intensity commodity has a registry family (S7)"

    def test_no_driver_entries_exact(self, log, expected):
        problems = check_runs(log, "no_driver", expected.log["no_driver"], lambda k: (("XXX" if k[1] == "XWL" else k[1]), "", k[0]))
        assert not problems, show(problems)

    def test_no_intensity_for_csp(self, log, expected):
        assert expected.log["no_intensity"], "premise: CSP capacity exists"
        problems = check_runs(log, "no_intensity", expected.log["no_intensity"], lambda k: ("XXX", "", k[0]))
        assert not problems, show(problems)

    def test_attribution_exact(self, log, expected):
        att = expected.log["attribution"]
        ents = log_entries(log, "attribution")
        pat = re.compile(r"^([a-z0-9_]+): max sigma ([-+0-9.eE]+) in (\d{4})$")
        got = {}
        for e in ents:
            m = pat.match(str(e["detail"]))
            assert m, f"attribution detail must be '<commodity>: max sigma <value> in <year>' (13.14): {e}"
            assert e["country"] == "XXX" and e["group"] == "" and e["year"] % 10 == 0, f"attribution fields: {e}"
            got[(m.group(1), e["year"])] = (float(m.group(2)), int(m.group(3)))
        assert set(got) == set(att), f"attribution (commodity, decade) {sorted(set(got) ^ set(att))[:4]}"
        for k, (sig, yr) in att.items():
            assert close(got[k][0], sig, 1e-3), f"{k}: sigma {got[k][0]} vs {sig:.6g}"
            assert got[k][1] == yr, f"{k}: year of the maximum {got[k][1]} vs {yr}"

    def test_sigma_never_above_one_in_the_data(self, expected):
        assert not expected.errors, f"the data give sigma > 1 or a share above 1 (the build must raise): {expected.errors[:2]}"
        assert max(expected.sigma.values()) <= 1.0


class TestPlaceholders:
    def test_placeholder_share_entries(self, log, expected, data):
        assert expected.log["placeholder_share"], "premise: placeholder series are used"

        def country(series):  # 13.14: the series country, XWL written as XXX
            cs = {c for (s, c, y) in data.rows if s == series}
            assert len(cs) == 1, f"{series} has several countries {cs}"
            c = cs.pop()
            return "XXX" if c == "XWL" else c

        problems = check_runs(log, "placeholder_share", expected.log["placeholder_share"], lambda k: (country(k), "", k))
        assert not problems, show(problems)

    def test_class_shares_are_not_logged_as_placeholders(self, log):
        for e in log_entries(log, "placeholder_share"):
            assert "cu_class_share" not in f"{e['group']} {e['detail']}", f"class shares are not placeholders: {e}"

    def test_placeholder_notes_come_only_from_the_prefix(self, ws_mod, tmp_path):
        """13.5: the script does not know placeholders except by the PLACEHOLDER prefix."""

        def strip(df):
            m = df.notes.str.startswith("PLACEHOLDER")
            df.loc[m, "notes"] = "supplied value"
            return df

        root = make_mini(tmp_path, (2020,), edits={"wind_solar_shares.csv": strip})
        res = ws_mod.build(root)
        assert res.rows
        assert not [r for r in res.rows if "placeholder" in (r["notes"] or "").lower()], "no placeholder text once the rows are supplied"
        assert not log_entries(res.log, "placeholder_share")


# --------------------------------------------------------------------------------------------
# (e) benchmarks (components, not the stream total; D51, Q13). Known misses are runtime xfails.
# --------------------------------------------------------------------------------------------
def check(name, x, ref, known_miss=False, reason="", unit="Bq"):
    ratio = x / ref if ref else float("inf")
    ok = 1 / 3 <= ratio <= 3
    if not ok and known_miss:
        pytest.xfail(f"documented known miss (WIND_SOLAR_SPEC 9(e)): {name}: stream {x:.4g}, reference {ref:.4g}, ratio {ratio:.3g}. {reason}")
    assert ok, f"{name}: component {x:.4g} {unit} vs reference {ref:.4g}, ratio {ratio:.3g} outside [1/3, 3]"
    return ratio


class TestBenchmarks:
    def test_structural_known_miss_no_stream_level_benchmark(self):
        pytest.xfail("documented structural known miss (Q13): UNSCEAR 2016 Annex B gives no Bq factors for wind or solar; no stream-level estimate exists")

    def test_b1_bayan_obo_thorium_tailings_to_2006(self, data):
        """B1: RE-BO Th232 tailings factor x cumulative Bayan Obo REO to 2006 against S0405 (S2: reference corrected by 1000)."""
        tot = 0.0
        years = []
        for y in range(1958, 2007):
            if data.has("prod_ree_oxide", y, "CHN") and data.has("ree_route_share_bayan_obo", y):
                try:
                    F = data.fac("ree_oxide", "Th232", "impounded", y, ore="ree_bayan_obo", region="CHN", residue="ree_tailings")["c"]
                except AssertionError:
                    continue
                tot += data.a("prod_ree_oxide", y, "CHN") * data.a("ree_route_share_bayan_obo", y) * F
                years.append(y)
        assert tot > 0, "no Bayan Obo cumulative could be formed"
        # independent bound: ore mined to the end of 2006, 276 Mt at 0.032 % ThO2 (1.14 Bq/g Th-232)
        ore_upper = 276e6 * 1.14e6  # Bq (t x Bq/t); the spec prints 3.1e17, a x1000 slip (S2)
        tail_lo, tail_hi = 149e6 * 1.0e6, 149e6 * 1.6e6  # S0405: 149 Mt at 1.0-1.6 Bq/g
        assert tot <= ore_upper, f"B1: cumulative stream {tot:.3g} Bq exceeds the ore upper bound {ore_upper:.3g} (data {years[0]}-{years[-1]})"
        assert tot >= ore_upper / 10, f"B1: stream {tot:.3g} Bq below one tenth of the ore bound {ore_upper:.3g} (v1.1 pass rule)"
        assert tail_lo / 3 <= tot <= tail_hi * 3, f"B1: stream {tot:.3g} Bq not within x3 of the S0405 inventory {tail_lo:.3g}-{tail_hi:.3g} (v1.1 pass rule)"

    def test_b2_steel_stack_pb210_po210_1999(self, data):
        y = 1999
        bf = data.a("steel_bf_route_share", y)
        t = data.a("prod_steel", y, "GBR")
        pb = t * bf * data.fac("steel", "Pb210+", "liberated", y, route="air_stack")["c"]
        po = t * bf * data.fac("steel", "Po210", "liberated", y, route="air_stack")["c"]
        check("B2 Po-210 (NRPB-W48 1.35e11 Bq/a)", po, 1.35e11, unit="Bq/a")
        check(
            "B2 Pb-210 (NRPB-W48 2.1e10 Bq/a)", pb, 2.1e10, known_miss=True, unit="Bq/a",
            reason="A ratio above 3 is a documented miss because Po-210 passes (4.0e9 vs 3.96e10 contradiction, commodity_notes 3.2)",
        )

    def test_b3_aluminium_red_mud_ra226_2017(self, data):
        y = 2017
        q = data.a("prod_aluminium", y)
        x = q * (data.fac("aluminium", "Ra226+", "impounded", y, residue="red_mud")["c"] + data.fac("aluminium", "Ra226+", "dispersed", y, residue="red_mud")["c"])
        lo, hi = 1.5e13, 7.5e13  # S0436: about 150 Mt/a red mud at 100-500 Bq/kg
        assert lo <= x <= hi, f"B3: red-mud Ra-226 {x:.4g} Bq/a outside the range {lo:.3g}-{hi:.3g}"

    def test_b4_od_radon_effective_epsilon_inside_triple(self):
        rt = pd.read_csv(ROOT / "data" / "reference" / "residue_types.csv", dtype=str, keep_default_na=False)
        mt = rt[rt.residue_type == "metal_tailings"].iloc[0]
        lo, hi = float(mt["epsilon_rn222_low"]), float(mt["epsilon_rn222_high"])
        assert lo <= 0.004 <= hi, f"B4: implied OD effective epsilon 0.004 outside the metal_tailings epsilon222 triple [{lo}, {hi}] (deferred to Phase 3 otherwise)"

    def test_stream_rows_reproduce_the_b2_component(self, rows, data):
        """The stream's ST stack Po-210 rows are the factor x tonnage the benchmark uses (link between B2 and the rows)."""
        y = 2020
        r = row_c(rows, y, "wind", "steel", "XXX", "Po210", "liberated", "", "air_stack", "default")
        want = data.tonnes_c(y, "wind", "steel") * data.a("steel_bf_route_share", y) * data.fac("steel", "Po210", "liberated", y, route="air_stack")["c"]
        assert close(float(r["value_central"]), want, 1e-7)


# --------------------------------------------------------------------------------------------
# (f) hand-computed cases (each recomputed from the files, not from the oracle)
# --------------------------------------------------------------------------------------------
def b_of(D: Data, series, y, country="XWL") -> B:
    r = D.rows[(series, country, y)]
    return B(r["low"], r["c"], r["high"])


def first_row(D: Data, commodity, y, ore=""):
    d = D.cf[(D.cf.commodity == commodity) & (D.cf.ore_type == ore) & (D.cf.year_from <= y) & (D.cf.year_to >= y)]
    assert len(d), f"registry has no {commodity} row in {y}"
    return d.iloc[0]


def class_terms(D: Data, y, sub, c, pre=(), F=None):
    """Per-class contribution bounds prod(cap, pi, I, *pre, F) (spec 4.1-4.2)."""
    out = []
    for k, (s, capser, shser, cmpl) in Data.CLS.items():
        if s != sub or not D.has(f"mi_{k}_{c}", y) or not D.has(capser, y):
            continue
        pi = b_of(D, shser, y)
        if cmpl:
            pi = B(1 - pi.high, 1 - pi.central, 1 - pi.low)
        terms = [b_of(D, capser, y), pi, b_of(D, f"mi_{k}_{c}", y), *pre]
        if F is not None:
            terms.append(F)
        out.append(prod(*terms))
    return out


def fb(Fr) -> B:
    return B(Fr["low"], Fr["c"], Fr["high"])


def both_orders(D, y, sub, c, pre, F, share=1.0):
    """Stepwise per class (4.2 steps 3-5), then sum_correlated (step 6): one reading (13.12)."""
    return [sum_correlated([scale(t, share) for t in class_terms(D, y, sub, c, pre, F)])]


def assert_row_is_one_of(r: dict, cands: list[B], rel=1e-6, label=""):
    got = vals(r)
    assert any(all(close(g, w, rel) for g, w in zip(got, (b.low, b.central, b.high))) for b in cands), (
        f"{label}: row {got} matches none of {[(b.low, b.central, b.high) for b in cands]}"
    )


class TestHandComputed:
    Y = 2020

    def test_01_cu_b_ra226_all_three_variants(self, rows, data):
        y = self.Y
        s = b_of(data, "cu_class_share_porphyry_stratiform", y)
        F = fb(data.fac("copper", "Ra226+", "impounded", y, ore="porphyry_stratiform", residue="metal_tailings"))
        d6 = data.a("d6_value_share_copper_porphyry", y)
        pre = (B(s.central, s.central, s.central),)
        for v, share in (("default", d6), ("bound_main", 1.0), ("bound_radio", 0.0)):
            r = row_c(rows, y, "wind", "copper", "XXX", "Ra226+", "impounded", "metal_tailings", "", v)
            assert_row_is_one_of(r, both_orders(data, y, "wind", "copper", pre, F, share), label=f"CU-B Ra226+ {v}")

    def test_02_cu_od_2023_default_with_wu(self, rows, data):
        y = 2023
        w = data.a("od_value_share_u", y, "AUS")
        assert 0 < w < 1
        M = data.tonnes_c(y, "solar", "copper")
        Fo = data.fac("copper", "Ra226+", "impounded", y, ore="iocg_olympic_dam", region="AUS", residue="metal_tailings")
        Fp = data.fac("copper", "Ra226+", "impounded", y, ore="iocg_high_u", region="AUS", residue="metal_tailings")
        od = M * data.od_share(y) * Fo["c"]
        ph = M * data.a("cu_class_share_iocg_high_u", y) * Fp["c"]
        d6 = data.a("d6_value_share_copper_iocg_ph_cp", y, "AUS")
        r = row_c(rows, y, "solar", "copper", "AUS", "Ra226+", "impounded", "metal_tailings", "", "default")
        assert close(float(r["value_central"]), od * (1 - w) + ph * d6, 1e-7), "OD (1 - w_U) + PH/CP D6 share"
        assert ids(r["factor_ids"]) == sorted([Fo["fid"], Fp["fid"]])
        # the nuclear ledger of the same pool is w_U x the whole OD pool: ledgers sum to the pool
        pool = data.a("prod_copper_od", y, "AUS") * Fo["c"]
        assert close(pool * w + pool * (1 - w), pool)

    def test_03_cu_c_cod(self, rows, data):
        y = self.Y
        M = data.tonnes_c(y, "solar", "copper")
        F = data.fac("copper", "Ra226+", "impounded", y, ore="cu_co_stratiform", region="COD", residue="metal_tailings")["c"]
        r = row_c(rows, y, "solar", "copper", "COD", "Ra226+", "impounded", "metal_tailings", "", "default")
        want = M * data.a("cu_class_share_cu_co_stratiform", y) * F * data.a("d6_value_share_copper_cu_co", y, "COD")
        assert close(float(r["value_central"]), want, 1e-7)
        assert vals(row_c(rows, y, "solar", "copper", "COD", "Ra226+", "impounded", "metal_tailings", "", "bound_radio")) == (0.0, 0.0, 0.0), "Co is the radio product (D74(b))"

    def test_04_cu_sm_slag_dispersed(self, rows, data):
        y = self.Y
        M = data.tonnes_c(y, "wind", "copper")
        F = data.fac("copper", "Ra226+", "dispersed", y, ore="all", residue="smelter_slag")["c"]
        r = row_c(rows, y, "wind", "copper", "XXX", "Ra226+", "dispersed", "smelter_slag", "", "default")
        assert close(float(r["value_central"]), M * F * data.a("d6_value_share_copper_porphyry", y), 1e-7)

    def test_05_re_bo_th232_2015(self, rows, data):
        y = 2015
        F = fb(data.fac("ree_oxide", "Th232", "impounded", y, ore="ree_bayan_obo", region="CHN", residue="ree_tailings"))
        share = data.a("ree_route_share_bayan_obo", y)
        ch = data.a("ree_charge_factor", y)
        d6 = data.a("d6_value_share_ree_bayan_obo", y, "CHN")
        ex = lambda x: B(x, x, x)
        for v, c_, sh in (("default", ch, d6), ("bound_main", CHARGE_MAIN, 0.0), ("bound_radio", CHARGE_RADIO, 1.0)):
            r = row_c(rows, y, "wind", "ree_oxide", "CHN", "Th232", "impounded", "ree_tailings", "", v)
            assert_row_is_one_of(r, both_orders(data, y, "wind", "ree_oxide", (ex(share), ex(c_)), F, sh), label=f"RE-BO {v}")

    def test_06_re_mw_2012_present_2011_absent(self, rows):
        assert rows.find(2012, substream="wind", product="ree_oxide", country="MYS"), "RE-MW rows must exist in 2012 (route share and factor window start)"
        assert not rows.find(2011, substream="wind", product="ree_oxide", country="MYS"), "no RE-MW row in 2011 (route share 0, window starts 2012)"

    def test_07_st_stack_po210_bf_share(self, rows, data):
        y = self.Y
        bf = data.a("steel_bf_route_share", y)
        F = fb(data.fac("steel", "Po210", "liberated", y, route="air_stack"))
        r = row_c(rows, y, "solar", "steel", "XXX", "Po210", "liberated", "", "air_stack", "default")
        assert_row_is_one_of(r, both_orders(data, y, "solar", "steel", (B(bf, bf, bf),), F), label="ST Po210")

    def test_08_al_red_mud_dispersed(self, rows, data):
        y = self.Y
        F = data.fac("aluminium", "Ra226+", "dispersed", y, residue="red_mud")["c"]
        r = row_c(rows, y, "wind", "aluminium", "XXX", "Ra226+", "dispersed", "red_mud", "", "default")
        assert close(float(r["value_central"]), data.tonnes_c(y, "wind", "aluminium") * F, 1e-7)
        assert ids(r["allocation_rule"]) == ["none"] and r["allocation_variant"] == "default"

    def test_09_ce_rn222_stack(self, rows, data):
        y = self.Y
        F = data.fac("cement", "Rn222+", "liberated", y, route="air_stack")["c"]
        r = row_c(rows, y, "wind", "cement", "XXX", "Rn222+", "liberated", "", "air_stack", "default")
        assert close(float(r["value_central"]), data.tonnes_c(y, "wind", "cement") * F, 1e-7)

    def test_10_ag_silver_joint_radio(self, rows, data):
        y = self.Y
        M = data.tonnes_c(y, "solar", "silver")
        F = data.fac("silver", "Ra226+", "impounded", y, residue="metal_tailings")["c"]
        share = data.a("d6_value_share_silver", y)
        vs = {v: row_c(rows, y, "solar", "silver", "XXX", "Ra226+", "impounded", "metal_tailings", "", v) for v in VARIANTS}
        assert close(float(vs["bound_radio"]["value_central"]), M * F, 1e-7), "silver is the radio product: bound_radio = whole"
        assert vals(vs["bound_main"]) == (0.0, 0.0, 0.0)
        assert close(float(vs["default"]["value_central"]), M * F * share, 1e-7)

    def test_11_wind_row_merging_several_classes(self, rows, data):
        y = self.Y
        r0 = first_row(data, "tin", y)
        F = fb(data.fac("tin", r0.group, r0.tier, y, residue=r0.residue_type, route=r0.route))
        parts = class_terms(data, y, "wind", "tin", (), F)
        assert len([p for p in parts if p.central > 0]) >= 3, "premise: at least three wind classes contribute tin in 2020"
        r = row_c(rows, y, "wind", "tin", "XXX", r0.group, r0.tier, r0.residue_type, r0.route, "default")
        assert_row_is_one_of(r, both_orders(data, y, "wind", "tin", (), F), label="wind tin merge")

    def test_12_pv_rooftop_aluminium(self, rows, data):
        y = self.Y
        cap = data.a("cap_add_solar_pv", y)
        u = data.a("pv_utility_share", y)
        Mu = cap * u * data.a("mi_pv_utility_aluminium", y)
        Mr = cap * (1 - u) * data.a("mi_pv_rooftop_aluminium", y)
        assert Mr > 0
        F = data.fac("aluminium", "Ra226+", "impounded", y, residue="red_mud")["c"]
        r = row_c(rows, y, "solar", "aluminium", "XXX", "Ra226+", "impounded", "red_mud", "", "default")
        assert close(float(r["value_central"]), (Mu + Mr) * F, 1e-7)

    def test_13_placeholder_flagged_notes(self, rows):
        y = self.Y
        d = row_c(rows, y, "wind", "copper", "XXX", "Ra226+", "impounded", "metal_tailings", "", "default")
        main = row_c(rows, y, "wind", "copper", "XXX", "Ra226+", "impounded", "metal_tailings", "", "bound_main")
        assert d["notes"].startswith("CU: porphyry_stratiform")
        assert "D6 default, commodity copper" in d["notes"]
        assert d["notes"].endswith("; share basis: placeholder; allocation basis: placeholder"), d["notes"]
        assert main["notes"].endswith("; share basis: placeholder") and "allocation basis" not in main["notes"], main["notes"]

    def test_14_zn_joint_main(self, rows, data):
        y = self.Y
        M = data.tonnes_c(y, "wind", "zinc")
        F = data.fac("zinc", "U238+", "impounded", y, residue="metal_tailings")["c"]
        vs = {v: row_c(rows, y, "wind", "zinc", "XXX", "U238+", "impounded", "metal_tailings", "", v) for v in VARIANTS}
        assert close(float(vs["bound_main"]["value_central"]), M * F, 1e-7)
        assert vals(vs["bound_radio"]) == (0.0, 0.0, 0.0), "lead is the second product by value (Q3): zinc gets 0 under bound_radio"
        assert close(float(vs["default"]["value_central"]), M * F * data.a("d6_value_share_zinc", y), 1e-7)

    def test_15_gl_and_gf_stack_rows(self, rows, data):
        y = self.Y
        for sub, c in (("solar", "glass"), ("wind", "glass_fibre")):
            r0 = first_row(data, c, y)
            F = data.fac(c, r0.group, r0.tier, y, route=r0.route)["c"]
            r = row_c(rows, y, sub, c, "XXX", r0.group, r0.tier, "", r0.route, "default")
            assert close(float(r["value_central"]), data.tonnes_c(y, sub, c) * F, 1e-7)

    def test_16_cast_iron_and_pv_before_2001(self, rows, data):
        y = self.Y
        r0 = first_row(data, "cast_iron", y)
        F = data.fac("cast_iron", r0.group, r0.tier, y, residue=r0.residue_type)["c"]
        r = row_c(rows, y, "wind", "cast_iron", "XXX", r0.group, r0.tier, r0.residue_type, "", "default")
        assert close(float(r["value_central"]), data.tonnes_c(y, "wind", "cast_iron") * F, 1e-7)
        assert not rows.find(2000, substream="solar"), "pre-2001 PV absent"


# --------------------------------------------------------------------------------------------
# (h) pre-1950 file
# --------------------------------------------------------------------------------------------
class TestPre1950:
    def test_build_has_no_pre_1950_rows(self, result):
        assert list(result.rows_pre1950) == [], "no wind or solar capacity before 1950: rows_pre1950 is empty (no D31 opening stock)"

    def test_all_rows_inside_the_years_of_the_build(self, result):
        assert all(1950 <= int(r["year"]) <= 2025 for r in result.rows)

    def test_committed_pre_1950_file_is_header_only(self):
        p = ROOT / "data" / "streams_pre1950" / "wind_solar.csv.gz"
        assert p.is_file(), "data/streams_pre1950/wind_solar.csv.gz is not committed (spec 1)"
        raw = p.read_bytes()
        assert raw[:2] == b"\x1f\x8b", "not gzip"
        text = gzip.decompress(raw).decode("utf-8")
        lines = [ln for ln in text.split("\n") if ln]
        assert len(lines) == 1, f"header only expected, got {len(lines)} lines"
        assert set(lines[0].split(",")) == set(MASTER_COLS), "header is not the master column set"


# --------------------------------------------------------------------------------------------
# miniature trees (g)
# --------------------------------------------------------------------------------------------
CAP_SERIES = {
    "cap_add_wind_onshore", "cap_add_wind_offshore", "cap_add_solar_pv", "cap_add_solar_csp", "pv_share_thin_film",
}
PROD_SERIES = set(WORLD_SERIES.values()) | {"prod_copper_od", "prod_pig_iron", "prod_steel"}


def make_mini(tmp_path: Path, years=(2019, 2020, 2023), edits=None, registry_edit=None, name="mini", extra_files=None) -> Path:
    """A tree with only what build() may read (spec 1): data/activity/{capacity_additions, material_intensity,
    wind_solar_shares, commodity_production}.csv, data/factors/wind_solar.csv, data/reference/commodity_factors.csv."""
    root = tmp_path / name
    (root / "data" / "activity").mkdir(parents=True)
    (root / "data" / "factors").mkdir(parents=True)
    (root / "data" / "reference").mkdir(parents=True)
    (root / "data" / "streams").mkdir()
    (root / "data" / "streams_pre1950").mkdir()
    (root / "research" / "wind_solar").mkdir(parents=True)
    edits = edits or {}
    ys = set(years)
    src = ROOT / "data" / "activity"
    for fname in ("capacity_additions", "material_intensity", "wind_solar_shares", "commodity_production"):
        df = pd.read_csv(src / f"{fname}.csv", dtype=str, keep_default_na=False)
        df = df[df.year.astype(int).isin(ys)]
        if fname == "capacity_additions":
            df = df[(df.country == "XWL") & df.series.isin(CAP_SERIES)]
        if fname == "commodity_production":
            df = df[df.series.isin(PROD_SERIES)]
        df = df.reset_index(drop=True)
        fn = edits.get(f"{fname}.csv")
        if fn:
            df = fn(df)
        df.to_csv(root / "data" / "activity" / f"{fname}.csv", index=False, lineterminator="\n")
    shutil.copy(ROOT / "data" / "factors" / "wind_solar.csv", root / "data" / "factors" / "wind_solar.csv")
    reg = pd.read_csv(ROOT / "data" / "reference" / "commodity_factors.csv", dtype=str, keep_default_na=False)
    if registry_edit:
        reg = registry_edit(reg)
    reg.to_csv(root / "data" / "reference" / "commodity_factors.csv", index=False, lineterminator="\n")
    for rel, text in (extra_files or {}).items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return root


def build_mini(mod, tmp_path, **kw):
    root = make_mini(tmp_path, **kw)
    res = mod.build(root)
    return root, res, Rows(list(res.rows)), list(res.log)


def all_problems(O: Oracle, rws: Rows, label="mini") -> list[str]:
    comp = compare_all(O, O.expected().rows, rws, label)
    return [m for v in comp.values() for m in v]


def drop_series(name):
    return lambda df: df[df.series != name].reset_index(drop=True)


def drop_rows(**cond):
    def fn(df):
        m = pd.Series(True, index=df.index)
        for k, v in cond.items():
            m &= df[k] == v
        return df[~m].reset_index(drop=True)

    return fn


@pytest.fixture(scope="module")
def mini_base(ws_mod, tmp_path_factory):
    tmp = tmp_path_factory.mktemp("mini_base")
    root, res, rws, lg = build_mini(ws_mod, tmp)
    O = Oracle(root)
    return root, res, rws, lg, O


class TestMiniBase:
    def test_rows_equal_oracle(self, mini_base):
        root, res, rws, lg, O = mini_base
        bad = all_problems(O, rws)
        assert not bad, show(bad)
        assert rws.rows

    def test_build_does_not_need_other_reference_files_or_events(self, mini_base):
        root = mini_base[0]
        assert sorted(p.name for p in (root / "data" / "reference").iterdir()) == ["commodity_factors.csv"]
        assert not (root / "data" / "events.csv").exists()

    def test_build_is_repeatable(self, ws_mod, mini_base):
        root, res = mini_base[0], mini_base[1]
        again = ws_mod.build(root)
        assert json.dumps(list(again.rows), sort_keys=True, default=str) == json.dumps(list(res.rows), sort_keys=True, default=str)

    def test_no_no_driver_inside_the_mini_years_except_unavailable_series(self, mini_base):
        lg = mini_base[3]
        for e in log_entries(lg, "no_driver"):
            assert not (entry_years(e) & {2019, 2020, 2023}), f"no_driver for a year with all drivers: {e}"

    def test_fuel_inputs_and_residue_files_are_never_read(self, ws_mod, tmp_path, mini_base):
        junk = {
            "data/reference/commodity_fuel_inputs.csv": "this,is,not,a,table\n\x00\x01",
            "data/reference/residue_types.csv": "garbage\n",
            "data/reference/groups.csv": "garbage\n",
            "data/events.csv": "garbage\n",
        }
        root, res, rws, lg = build_mini(ws_mod, tmp_path, name="junk", extra_files=junk)
        assert json.dumps(list(res.rows), sort_keys=True, default=str) == json.dumps(list(mini_base[1].rows), sort_keys=True, default=str)


class TestMiniErrors:
    def test_share_with_high_above_one_raises(self, ws_mod, tmp_path):
        def f(df):
            m = df.series == "pv_utility_share"
            df.loc[m, "value_high"] = "1.2"
            return df

        root = make_mini(tmp_path, edits={"wind_solar_shares.csv": f})
        with pytest.raises(lib_error()):
            ws_mod.build(root)

    def test_charge_factor_high_above_one_is_exempt(self, ws_mod, tmp_path):
        def f(df):
            m = df.series == "ree_charge_factor"
            df.loc[m, "value_low"] = "2.0"
            df.loc[m, "value_high"] = "3.0"
            return df

        root, res, rws, lg = build_mini(ws_mod, tmp_path, edits={"wind_solar_shares.csv": f})
        assert rws.find(substream="wind", product="ree_oxide"), "charge factor with high 3 must not raise"
        bad = all_problems(Oracle(root), rws)
        assert not bad, show(bad)

    def test_world_attribution_above_one_raises(self, ws_mod, tmp_path):
        def f(df):
            m = df.series == "cap_add_wind_onshore"
            for c in ("value_low", "value_central", "value_high"):
                df.loc[m, c] = (df.loc[m, c].astype(float) * 1e7).astype(str)
            return df

        root = make_mini(tmp_path, edits={"capacity_additions.csv": f})
        with pytest.raises(lib_error()):
            ws_mod.build(root)

    @pytest.mark.parametrize("fname,series", [
        ("capacity_additions.csv", "cap_add_solar_pv"),
        ("material_intensity.csv", "mi_wind_on_pm_copper"),
        ("wind_solar_shares.csv", "wind_pm_share_onshore"),
        ("commodity_production.csv", "prod_copper"),
    ])
    def test_duplicate_activity_rows_raise_naming_the_key(self, ws_mod, tmp_path, fname, series):
        def f(df):
            row = df[(df.series == series) & (df.year == "2020")].iloc[[0]]
            return pd.concat([df, row], ignore_index=True)

        root = make_mini(tmp_path, edits={fname: f})
        with pytest.raises(lib_error()) as ei:
            ws_mod.build(root)
        msg = str(ei.value)
        assert series in msg and "2020" in msg, f"the error should name the duplicate key (series and year): {msg!r}"

    def test_ambiguous_registry_rows_propagate(self, ws_mod, tmp_path):
        def f(df):
            row = df[(df.commodity == "steel") & (df.group == "Po210") & (df.tier == "liberated")].iloc[[0]].copy()
            row["factor_id"] = "commodity:9999"
            return pd.concat([df, row], ignore_index=True)

        root = make_mini(tmp_path, registry_edit=f)
        with pytest.raises(lib_error()) as ei:
            ws_mod.build(root)
        assert "ambiguous" in str(ei.value).lower(), f"expected an 'ambiguous factor rows' error, got {ei.value!r}"

    def test_ore_type_blank_does_not_match_an_ore_type_row(self, ws_mod, tmp_path, mini_base):
        """LIB v1.6 exact equality: a steel lookup with ore_type='' must ignore an extra steel row carrying an ore type."""

        def f(df):
            row = df[(df.commodity == "steel") & (df.group == "Po210") & (df.tier == "liberated")].iloc[[0]].copy()
            row["factor_id"] = "commodity:9999"
            row["ore_type"] = "iocg_high_u"
            row["value_central"] = "1"
            return pd.concat([df, row], ignore_index=True)

        root, res, rws, lg = build_mini(ws_mod, tmp_path, registry_edit=f)
        base = mini_base[2]
        got = sorted(vals(r) for r in rws.find(product="steel", group="Po210"))
        want = sorted(vals(r) for r in base.find(product="steel", group="Po210"))
        assert got == want, "an extra row with another ore_type changed the steel result: ore_type is not an exact-equality key"

    def test_class_shares_not_summing_to_one_fail_the_premise(self, tmp_path):
        def f(df):
            m = df.series == "cu_class_share_porphyry_stratiform"
            for c in ("value_low", "value_central", "value_high"):
                df.loc[m, c] = (df.loc[m, c].astype(float) * 0.9).astype(str)
            return df

        root = make_mini(tmp_path, edits={"wind_solar_shares.csv": f})
        assert class_share_sum_problems(Data(root)), "the class-share premise must detect shares that do not sum to 1"


class TestMiniDrivers:
    def test_absent_share_series_gives_no_driver_not_a_raise(self, ws_mod, tmp_path):
        root, res, rws, lg = build_mini(ws_mod, tmp_path, edits={"wind_solar_shares.csv": drop_series("wind_pm_share_onshore")})
        O = Oracle(root)
        exp = O.expected()
        assert exp.log["no_driver"][("wind_pm_share_onshore", "XWL")], "premise: the absent series is needed in the mini years"
        problems = check_runs(lg, "no_driver", exp.log["no_driver"], lambda k: (("XXX" if k[1] == "XWL" else k[1]), "", k[0]))
        assert not problems, show(problems)
        bad = all_problems(O, rws)
        assert not bad, show(bad)

    def test_missing_od_series_gives_no_cu_od_rows_and_no_driver(self, ws_mod, tmp_path, mini_base):
        root, res, rws, lg = build_mini(ws_mod, tmp_path, edits={"commodity_production.csv": drop_series("prod_copper_od")})
        aus = rws.find(2020, substream="wind", product="copper", country="AUS", group="Ra226+", allocation_variant="default")
        assert len(aus) == 1 and not any("iocg_olympic_dam" in (r["notes"] or "") for r in aus), "only PH/CP remains at AUS"
        O = Oracle(root)
        exp = O.expected()
        assert ("prod_copper_od", "AUS") in exp.log["no_driver"]
        problems = check_runs(lg, "no_driver", exp.log["no_driver"], lambda k: (("XXX" if k[1] == "XWL" else k[1]), "", k[0]))
        assert not problems, show(problems)
        bad = all_problems(O, rws)
        assert not bad, show(bad)

    def test_csp_only_capacity_logs_no_intensity(self, ws_mod, tmp_path):
        def f(df):
            return df[df.series == "cap_add_solar_csp"].reset_index(drop=True)

        root, res, rws, lg = build_mini(ws_mod, tmp_path, edits={"capacity_additions.csv": f})
        assert not rws.rows, "CSP has no intensity: no rows"
        exp = Oracle(root).expected()
        problems = check_runs(lg, "no_intensity", exp.log["no_intensity"], lambda k: ("XXX", "", k[0]))
        assert not problems and exp.log["no_intensity"], show(problems or ["no no_intensity expected"])

    def test_commodity_without_registry_rows_logs_no_footprint_once(self, ws_mod, tmp_path):
        root, res, rws, lg = build_mini(ws_mod, tmp_path, registry_edit=drop_rows(commodity="tin"))
        assert not rws.find(product="tin")
        ents = [e for e in log_entries(lg, "no_footprint") if str(e["detail"]).startswith("tin (mi_")]
        assert ents and all(e["year"] == "" and e["country"] == "" and e["group"] == "" for e in ents), f"no_footprint fields are empty except detail (13.14): {ents}"
        assert len(ents) == 1, f"no_footprint for tin must be logged once per build, got {len(ents)}"

    def test_family_without_registry_rows_logs_no_family(self, ws_mod, tmp_path):
        root, res, rws, lg = build_mini(ws_mod, tmp_path, registry_edit=drop_rows(ore_type="iocg_olympic_dam"))
        assert log_entries(lg, "no_family"), "a family (CU-OD) with no registry rows is logged no_family"
        assert not [r for r in rws.find(product="copper", country="AUS") if "iocg_olympic_dam" in (r["notes"] or "")]

    def test_registry_window_gap_logs_no_factor_and_does_not_raise(self, ws_mod, tmp_path):
        def f(df):
            m = (df.commodity == "steel") & (df.group == "Po210") & (df.tier == "liberated")
            df.loc[m, "year_to"] = "2019"
            return df

        root, res, rws, lg = build_mini(ws_mod, tmp_path, registry_edit=f)
        assert not rws.find(2020, product="steel", group="Po210", tier="liberated")
        assert rws.find(2019, product="steel", group="Po210", tier="liberated")
        ents = [e for e in log_entries(lg, "no_factor") if e["group"] == "Po210"]
        want = {(2020, "XXX", "Po210", "steel/-/liberated/air_stack: 2020-2020 (1 years)"), (2023, "XXX", "Po210", "steel/-/liberated/air_stack: 2023-2023 (1 years)")}
        assert {(e["year"], e["country"], e["group"], re.sub(r"\((\d+) years?\)", r"(\1 years)", e["detail"])) for e in ents} == want, f"no_factor entries {ents} (13.14 format)"
        bad = all_problems(Oracle(root), rws)
        assert not bad, show(bad)

    def test_zero_capacity_year_gives_no_rows(self, ws_mod, tmp_path):
        def f(df):
            m = df.series.isin(["cap_add_wind_onshore", "cap_add_wind_offshore"]) & (df.year == "2020")
            for c in ("value_low", "value_central", "value_high"):
                df.loc[m, c] = "0"
            return df

        root, res, rws, lg = build_mini(ws_mod, tmp_path, edits={"capacity_additions.csv": f})
        assert not rws.find(2020, substream="wind"), "an exactly zero capacity driver gives no rows (13.3)"
        assert rws.find(2019, substream="wind") and rws.find(2020, substream="solar")
        assert not [e for e in log_entries(lg, "no_driver") if 2020 in entry_years(e)], "a 0/0/0 year logs nothing (13.3)"

    def test_oracle_agreement_when_pm_share_changes(self, ws_mod, tmp_path):
        def f(df):
            m = df.series == "wind_pm_share_onshore"
            for c in ("value_low", "value_central", "value_high"):
                df.loc[m, c] = "0.4"
            return df

        root, res, rws, lg = build_mini(ws_mod, tmp_path, edits={"wind_solar_shares.csv": f})
        bad = all_problems(Oracle(root), rws)
        assert not bad, show(bad)


# --------------------------------------------------------------------------------------------
# (j) CLI and gzip outputs
# --------------------------------------------------------------------------------------------
def run_cli(root, *extra):
    return subprocess.run(
        [sys.executable, "-m", "pipeline.streams.wind_solar", "--root", str(root), *extra],
        cwd=str(ROOT), env=_env(), capture_output=True, text=True, timeout=1800, check=False,
    )


@pytest.fixture(scope="module")
def cli_world(ws_mod, tmp_path_factory, write_master):
    tmp = tmp_path_factory.mktemp("cli")
    root = make_mini(tmp, (2019, 2020), name="cli_root")
    w = run_cli(root, "--write")
    res = ws_mod.build(root)
    write_master(list(res.rows), tmp / "m.csv")
    write_master(list(res.rows_pre1950), tmp / "p.csv")
    return root, w, res, tmp


class TestCli:
    def test_write_exits_zero_and_creates_the_three_files(self, cli_world):
        root, w, res, tmp = cli_world
        assert w.returncode == 0, f"--write exited {w.returncode}\nstdout: {w.stdout[-800:]}\nstderr: {w.stderr[-1500:]}"
        for p in (
            root / "data" / "streams" / "wind_solar.csv.gz",
            root / "data" / "streams_pre1950" / "wind_solar.csv.gz",
            root / "research" / "wind_solar" / "build_log.csv",
        ):
            assert p.is_file(), f"--write must write {p.relative_to(root)} (spec 1)"
        assert not (root / "data" / "streams" / "wind_solar.csv").exists(), "no plain csv beside the gz (D72)"

    def test_outputs_are_deterministic_gzip_with_the_build_content(self, cli_world):
        from pipeline.lib.io import read_bytes

        root, w, res, tmp = cli_world
        main = root / "data" / "streams" / "wind_solar.csv.gz"
        pre = root / "data" / "streams_pre1950" / "wind_solar.csv.gz"
        assert main.read_bytes()[:10] == GZ_HEADER, "gzip header must be the deterministic one of LIB_SPEC 11 (mtime 0, no name)"
        assert read_bytes(main) == (tmp / "m.csv").read_bytes(), "CLI master content differs from build() + write_master"
        assert read_bytes(pre) == (tmp / "p.csv").read_bytes(), "CLI pre-1950 content differs"
        assert len([ln for ln in read_bytes(pre).decode().split("\n") if ln]) == 1, "pre-1950 file is header only"

    def test_log_file_and_cli_lines(self, cli_world):
        root, w, res, tmp = cli_world
        logf = root / "research" / "wind_solar" / "build_log.csv"
        with open(logf, newline="", encoding="utf-8") as fh:
            rd = list(csv.DictReader(fh))
        assert len(rd) == len(res.log), "build_log.csv must hold the full log"
        assert {"kind", "year", "country", "group", "detail"} <= set(rd[0]) if rd else True
        counts = Counter(e["kind"] for e in res.log)
        out = w.stdout + w.stderr
        for kind, n in counts.items():
            assert f"log {kind}: {n}" in out, f"CLI output lacks 'log {kind}: {n}':\n{out[-600:]}"

    def test_diff_mode_exit_codes_and_no_overwrite(self, cli_world):
        from pipeline.lib.io import gzip_bytes, read_bytes

        root, w, res, tmp = cli_world
        assert run_cli(root).returncode == 0, "identical files must give exit 0"
        main = root / "data" / "streams" / "wind_solar.csv.gz"
        pre = root / "data" / "streams_pre1950" / "wind_solar.csv.gz"
        logf = root / "research" / "wind_solar" / "build_log.csv"
        good_log, good_main, good_pre = logf.read_bytes(), main.read_bytes(), pre.read_bytes()
        try:
            logf.write_bytes(good_log + b"no_driver,1900,XXX,,tampered\n")
            assert run_cli(root).returncode != 0, "a differing build_log.csv alone must give a non-zero exit"
            assert logf.read_bytes() != good_log, "the diff run must not overwrite the log"
            logf.write_bytes(good_log)
            tampered = gzip_bytes(read_bytes(main).replace(b"wind_solar,wind", b"wind_solar,wInd", 1))
            main.write_bytes(tampered)
            assert run_cli(root).returncode != 0, "a differing master file must give a non-zero exit"
            assert main.read_bytes() == tampered, "the diff run must not overwrite files"
            main.write_bytes(good_main)
            pre.write_bytes(gzip_bytes(read_bytes(pre) + b"2020,wind_solar\n"))
            assert run_cli(root).returncode != 0, "a differing pre-1950 file must give a non-zero exit"
            pre.write_bytes(good_pre)
            assert run_cli(root).returncode == 0
            logf.unlink()
            assert run_cli(root).returncode != 0, "a missing committed build_log.csv must count as a difference"
        finally:
            logf.write_bytes(good_log)
            main.write_bytes(good_main)
            pre.write_bytes(good_pre)

    def test_recompressed_copy_still_matches(self, cli_world):
        """Diff compares decompressed content (spec 1)."""
        root, w, res, tmp = cli_world
        main = root / "data" / "streams" / "wind_solar.csv.gz"
        good = main.read_bytes()
        try:
            raw = gzip.decompress(good)
            buf = io.BytesIO()
            with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=1, mtime=12345, filename="x") as g:
                g.write(raw)
            main.write_bytes(buf.getvalue())
            assert run_cli(root).returncode == 0, "only the compressed bytes differ: the diff must pass"
        finally:
            main.write_bytes(good)

    def test_second_write_is_byte_identical(self, tmp_path):
        root = make_mini(tmp_path, (2020,), name="cli_twice")
        files = [
            root / "data" / "streams" / "wind_solar.csv.gz",
            root / "data" / "streams_pre1950" / "wind_solar.csv.gz",
            root / "research" / "wind_solar" / "build_log.csv",
        ]
        first = None
        for _ in range(2):
            p = run_cli(root, "--write")
            assert p.returncode == 0, p.stderr[-1000:]
            cur = [f.read_bytes() for f in files]
            if first is None:
                first = cur
            else:
                assert cur == first, "two --write runs differ (determinism, 9(d))"

    def test_cli_output_passes_the_validator_in_gz_form(self, cli_world, tmp_path):
        from pipeline.validate import validate

        root = cli_world[0]
        vroot = _copy_tree(tmp_path / "vroot")
        shutil.copy(root / "data" / "streams" / "wind_solar.csv.gz", vroot / "data" / "streams" / "wind_solar.csv.gz")
        found = [i for i in validate(vroot, master_files=["data/streams/wind_solar.csv.gz"]) if "wind_solar" in str(i.file)]
        assert not found, "\n".join(f"{i.rule} {i.message}" for i in found[:8])

    def test_committed_files_equal_a_fresh_build(self, result, write_master, tmp_path):
        """The three committed files must be current (spec 1, 9(j)): decompressed content equals build() + write_master."""
        from pipeline.lib.io import read_bytes

        main = ROOT / "data" / "streams" / "wind_solar.csv.gz"
        assert main.is_file(), "data/streams/wind_solar.csv.gz is not committed (run python -m pipeline.streams.wind_solar --write)"
        write_master(list(result.rows), tmp_path / "m.csv")
        assert read_bytes(main) == (tmp_path / "m.csv").read_bytes(), "committed master differs from a fresh build"
        assert (ROOT / "research" / "wind_solar" / "build_log.csv").is_file(), "research/wind_solar/build_log.csv is not committed"


# --------------------------------------------------------------------------------------------
# fixtures with non-degenerate shares (low < central < high) and the 1950-2025 walk
# --------------------------------------------------------------------------------------------
def widen(series, lo=0.5, share=True):
    """Make `series` rows non-degenerate: low = lo x central, high halfway to 1 (shares) or 1.2 x central (others)."""

    def fn(df):
        m = df.series.isin(series)
        c = df.loc[m, "value_central"].astype(float)
        df.loc[m, "value_low"] = (c * lo).astype(str)
        df.loc[m, "value_high"] = ((c + (1 - c) * 0.5) if share else c * 1.2).astype(str)
        return df

    return fn


def chain_edits(*fns):
    def fn(df):
        for f in fns:
            df = f(df)
        return df

    return fn


class TestMiniShares:
    PM = ["wind_pm_share_onshore", "wind_pm_share_offshore", "pv_utility_share"]
    CENTRAL_ONLY = [
        "ree_route_share_bayan_obo", "ree_route_share_ionic_clay", "ree_route_share_monazite", "ree_route_share_mt_weld",
        "d6_value_share_copper_porphyry", "d6_value_share_copper_cu_co", "d6_value_share_copper_iocg_ph_cp",
        "d6_value_share_zinc", "d6_value_share_silver", "d6_value_share_ree_bayan_obo", "d6_value_share_ree_monazite",
        "cu_class_share_porphyry_stratiform", "cu_class_share_iocg_high_u", "cu_class_share_cu_co_stratiform", "od_value_share_u",
    ]

    def test_complement_is_anti_correlated(self, ws_mod, tmp_path):
        root, res, rws, lg = build_mini(ws_mod, tmp_path, years=(2020,), edits={"wind_solar_shares.csv": widen(self.PM)})
        D = Data(root)
        for sub, c, g, tier, rs, rt in (("wind", "aluminium", "Ra226+", "dispersed", "red_mud", ""), ("solar", "aluminium", "Ra226+", "dispersed", "red_mud", "")):
            F = fb(D.fac(c, g, tier, 2020, residue=rs, route=rt))
            want = sum_correlated(class_terms(D, 2020, sub, c, (), F))
            lo = D.rows[("pv_utility_share" if sub == "solar" else "wind_pm_share_onshore", "XWL", 2020)]
            assert lo["low"] < lo["c"] < lo["high"], "premise: non-degenerate share"
            r = row_c(rws, 2020, sub, c, "XXX", g, tier, rs, rt, "default")
            assert_row_is_one_of(r, [want], rel=1e-7, label=f"{sub} {c} with anti-correlated complements")
        bad = all_problems(Oracle(root), rws)
        assert not bad, show(bad)

    def test_exact_shares_enter_at_central_only(self, ws_mod, tmp_path):
        root, res, rws, lg = build_mini(
            ws_mod, tmp_path, years=(2020,),
            edits={"wind_solar_shares.csv": chain_edits(widen(self.CENTRAL_ONLY), widen(["ree_charge_factor"], lo=0.8, share=False))},
        )
        D = Data(root)
        y = 2020
        s = D.rows[("cu_class_share_porphyry_stratiform", "XWL", y)]
        assert s["low"] < s["c"] < s["high"], "premise: non-degenerate class share"
        # CU-B: class share and D6 default at central; the row bounds are those of the unshared chain
        F = fb(D.fac("copper", "Ra226+", "impounded", y, ore="porphyry_stratiform", residue="metal_tailings"))
        d6 = D.a("d6_value_share_copper_porphyry", y)
        r = row_c(rws, y, "wind", "copper", "XXX", "Ra226+", "impounded", "metal_tailings", "", "default")
        assert_row_is_one_of(r, both_orders(D, y, "wind", "copper", (B(s["c"], s["c"], s["c"]),), F, d6), rel=1e-7, label="CU-B default")
        # RE-BO: route share and charge factor at central, D6 share at central
        route, ch, d6r = D.a("ree_route_share_bayan_obo", y), D.a("ree_charge_factor", y), D.a("d6_value_share_ree_bayan_obo", y, "CHN")
        Fr = fb(D.fac("ree_oxide", "Th232", "impounded", y, ore="ree_bayan_obo", region="CHN", residue="ree_tailings"))
        r = row_c(rws, y, "wind", "ree_oxide", "CHN", "Th232", "impounded", "ree_tailings", "", "default")
        assert_row_is_one_of(r, both_orders(D, y, "wind", "ree_oxide", (B(route * ch, route * ch, route * ch),), Fr, d6r), rel=1e-7, label="RE-BO default")
        bad = all_problems(Oracle(root), rws)
        assert not bad, show(bad)

    @pytest.mark.parametrize("series", [
        "ree_route_share_bayan_obo", "ree_route_share_monazite", "cu_class_share_porphyry_stratiform",
        "cu_class_share_cu_co_stratiform", "d6_value_share_copper_porphyry", "d6_value_share_zinc", "steel_bf_route_share",
    ])
    def test_share_with_high_above_one_raises_when_not_a_complement(self, ws_mod, tmp_path, series):
        def f(df):
            m = df.series == series
            df.loc[m, "value_high"] = "1.2"
            return df

        root = make_mini(tmp_path, years=(2020,), edits={"wind_solar_shares.csv": f})
        with pytest.raises(lib_error()):
            ws_mod.build(root)

    def test_share_rows_never_feed_the_driver_basis(self, ws_mod, tmp_path):
        def shares(df):
            df["basis"] = "extrapolated"
            return df

        def measured(df):
            df["basis"] = "measured"
            return df

        root, res, rws, lg = build_mini(
            ws_mod, tmp_path, years=(2019, 2020, 2023),
            edits={"wind_solar_shares.csv": shares, "capacity_additions.csv": measured, "material_intensity.csv": measured},
        )
        assert rws.rows
        bad = [describe(r) for r in rws.rows if "driver basis" in (r["notes"] or "")]
        assert not bad, "share rows (extrapolated) must not give a driver basis suffix when capacity and intensity are measured: " + show(bad)
        probs = all_problems(Oracle(root), rws)
        assert not probs, show(probs)

    def test_pre_1950_capacity_rows_produce_no_rows(self, ws_mod, tmp_path):
        def clone(old=2020, news=(1940, 1949)):
            def fn(df):
                add = []
                for n in news:
                    t = df[df.year == str(old)].copy()
                    t["year"] = str(n)
                    add.append(t)
                return pd.concat([df, *add], ignore_index=True)

            return fn

        edits = {f: clone() for f in ("capacity_additions.csv", "material_intensity.csv", "wind_solar_shares.csv", "commodity_production.csv")}
        root, res, rws, lg = build_mini(ws_mod, tmp_path, years=(2020,), edits=edits)
        assert rws.find(2020), "premise: the 2020 rows exist"
        assert not [r for r in res.rows if int(r["year"]) < 1950], "the walk is 1950-2025: no row before 1950 (13.17)"
        assert list(res.rows_pre1950) == [], "pre-1950 rows must stay empty"
        bad = all_problems(Oracle(root), rws)
        assert not bad, show(bad)
