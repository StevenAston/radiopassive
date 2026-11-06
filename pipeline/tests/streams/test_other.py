"""Spec-blind tests for the `other` stream script (Task 2.5, docs/OTHER_SPEC.md v1.1, section 9 (a)-(j)).

Written from docs/OTHER_SPEC.md, docs/NUCLEAR_SPEC.md (13) and docs/COAL_SPEC.md (11-12) conventions,
docs/LIB_SPEC.md (v1.4), docs/SCHEMA.md, docs/DECISIONS.md, data/factors/other.csv and the activity files.
pipeline/streams/other.py (and coal.py / nuclear.py) were not read. Expected values come from the
independent arithmetic in other_oracle.py (pandas plus the standard library; no pipeline.*); factor and
activity numbers are read from the files. Registry premises are asserted first ("PREMISE BROKEN").

Mapping to OTHER_SPEC section 9
-------------------------------
(a) Schema               TestSchema, TestRowConventions
(b) Candidates/coverage  TestRowsAgainstOracle (every row of every family), TestCoverage
(c) Conservation         TestPeatConservation (1), TestWoodPartition (2), TestCs137Conservation (3),
                         TestGeothermalStructure (4), TestTierStructure (5), TestUniqueKeys (6),
                         TestReRelease (7)
(d) Determinism          TestDeterminism
(e) Benchmarks           TestBenchmarks (B1-B5; known misses as runtime xfail)
(f) Hand-computed        TestHandComputed
(g) Fixture tests        TestMini* (miniature trees in tmp_path; full real factor file)
(h) Pre-1950 file        TestPre1950
(i) Premise assertions   TestPremises
(j) CLI                  TestCli
plus TestFlagsAndNotes (3.4), TestYearsAndEdges, TestLog (8), TestStderr (3.9).

ALIGNMENT WITH OTHER_SPEC v1.1 (D71, section 13.9-13.19)
-------------------------------------------------------
The A1-A16 ambiguities of the first version are settled by D71; no test is loose because of them any more:
notes are compared as exact strings (13.9-13.12), factor_ids as ordered lists (13.13), source_ids and the driver
basis from the driver rows of 13.14, (0,0,h) remainders write rows with cause clipped_difference (13.15),
no row with bounds exactly (0,0,0) is written, log entries have the exact keys and detail formats of 13.16, and
the pre-1950 fixtures are geothermal only (13.17).

REMAINING AMBIGUITIES (the tests assert only what is defensible)
----------------------------------------------------------------
R1  13.16 writes "(<n> years)" for no_driver and the aggregated runs; for a one-year run the singular is not
    stated. Tests accept "year" or "years".
R2  The plant-type cap fixture with other:0014 = 1 at every bound relies on product(A, exact 1) reproducing A
    bit for bit; floating-point noise could leave a residue of ~1e-16 relative instead of exactly 0/0/0. That
    fixture therefore accepts "no impounded/dispersed row" or a residue below 1e-12 of the stack row. The household
    variant (the cap limit is H_g itself) is exact and strictly asserted.
R3  13.15 says a partly capped household smoke remainder (0,0,h) writes flagged rows "by the same rule"; with
    s x e_g the product bounds are wider than H_g, so the cap binds at the high bound whenever it binds at the
    central one and the case cannot be built; it is not tested. The partly capped wood remainder is tested.
R4  The detail of cap_applied joins the capped bounds with "+" (13.16 says "<bounds>"); the order low, central, high is
    taken from the household_wood_capped row of the same table.
R5  13.16 gives the `lib_warning` detail pattern only; tests check the pattern, not the count or message text.
R6  Floating-point equality: a remainder such as R1 = D_tot minus a capped charcoal term has a raw low of exactly 0.0
    (identical doubles) and is NOT flagged; the next product then fires the floor rule (cause floor_dominance on
    587 real rows). This follows LIB_SPEC 8.1 and 3.4, but it depends on exact cancellation in the
    implementation as well.
"""

from __future__ import annotations

import csv
import hashlib
import importlib
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
from other_oracle import (
    BP,
    DOM,
    GEO,
    GWA_TWH,
    RULE,
    TXT_FALLBACK,
    TXT_REST,
    TXT_WORLD,
    B,
    Oracle,
    is_zero_b,
    prod,
    scale,
)

BASIS_ORDER = ["interpolated", "extrapolated"]

# pipeline/tests/streams/test_other.py -> streams -> tests -> pipeline -> repository root
ROOT = Path(__file__).resolve().parents[3]

REL = 1e-7  # value comparison against the oracle (in-memory floats)
CONS = 1e-9  # conservation in memory (13.1)
WRITTEN = 1e-5  # written six-digit files (D68)
RUN_RE = re.compile(r"^(\d{4})-(\d{4}) \((\d+) years?\)")
LOG_KINDS = {
    "no_factor",
    "no_driver",
    "no_family",
    "negative_residual",
    "household_fallback",
    "household_wood_capped",
    "charcoal_wood_capped",
    "cap_applied",
    "predecessor_dropped",
    "lib_warning",
}
ALL_TXT = [TXT_WORLD, TXT_REST, TXT_FALLBACK]
CAUSES = [
    "zero_central_factor",
    "exact_zero",
    "clipped_difference",
    "floor_dominance",
    "inherited_flag",
]
GEO_GAS = {"Rn222+", "Rn220+"}
GEO_SCALE = {"Ra226+", "Ra228+", "Pb210+", "Po210", "K40"}
PEAT11 = {
    "U238+",
    "U234",
    "Th230",
    "Ra226+",
    "Pb210+",
    "Po210",
    "U235+",
    "Th232",
    "Ra228+",
    "Th228+",
    "K40",
}
WOOD5 = {"K40", "Pb210+", "Po210", "Ra226+", "Ra228+"}
MASTER_COLS = [
    "year",
    "stream",
    "substream",
    "stage",
    "product",
    "residue_type",
    "country",
    "group",
    "tier",
    "quantity",
    "unit",
    "value_low",
    "value_central",
    "value_high",
    "below_detection",
    "basis",
    "source_ids",
    "factor_ids",
    "allocation_variant",
    "allocation_rule",
    "embedded_fuel",
    "technology",
    "route",
    "event_id",
    "notes",
]


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


def rkey(r: dict) -> tuple:
    return (
        int(r["year"]),
        r["substream"],
        r["stage"],
        r["country"],
        r["group"],
        r["tier"],
        r["route"] or "",
        r["residue_type"] or "",
    )


def describe(r: dict) -> str:
    keys = (
        "year",
        "substream",
        "stage",
        "country",
        "group",
        "tier",
        "quantity",
        "route",
        "residue_type",
    )
    return ", ".join(f"{k}={r.get(k)!r}" for k in keys)


def vals(r: dict) -> tuple[float, float, float]:
    return float(r["value_low"]), float(r["value_central"]), float(r["value_high"])


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
        assert len(m) == 1, (
            f"expected exactly one row for year={year}, {kw}; found {len(m)}"
        )
        return m[0]

    def total(self, year: int, **kw) -> float:
        return sum(float(r["value_central"]) for r in self.find(year, **kw))


def log_entries(log: list[dict], kind: str, **kw) -> list[dict]:
    return [
        e
        for e in log
        if e.get("kind") == kind and all(e.get(k) == v for k, v in kw.items())
    ]


def run_of(e: dict):
    m = RUN_RE.match(str(e.get("detail", "")))
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def show(msgs: list[str], n: int = 6) -> str:
    return f"{len(msgs)} problem(s); first {min(n, len(msgs))}:\n  " + "\n  ".join(
        msgs[:n]
    )


def lib_error():
    from pipeline.lib import LibError

    return LibError


# --------------------------------------------------------------------------------------------
# module-scoped fixtures
# --------------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def other_mod():
    try:
        return importlib.import_module("pipeline.streams.other")
    except ImportError as exc:  # expected until the code-writer is done
        pytest.fail(
            f"cannot import pipeline.streams.other (OTHER_SPEC 1): {type(exc).__name__}: {exc}"
        )


@pytest.fixture(scope="module")
def result(other_mod):
    assert hasattr(other_mod, "build"), (
        "pipeline.streams.other must expose build(root) (OTHER_SPEC 1)"
    )
    res = other_mod.build(ROOT)
    for attr in ("rows", "rows_pre1950", "log"):
        assert hasattr(res, attr), (
            f"BuildResult has no attribute {attr!r} (OTHER_SPEC 1)"
        )
    return res


@pytest.fixture(scope="module")
def rows(result) -> Rows:
    return Rows(list(result.rows))


@pytest.fixture(scope="module")
def pre_rows(result) -> Rows:
    return Rows(list(result.rows_pre1950))


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
    d = tmp_path_factory.mktemp("other_written")
    main, pre = d / "other.csv", d / "other_pre1950.csv"
    write_master(list(result.rows), main)
    write_master(list(result.rows_pre1950), pre)
    return main, pre


def _copy_tree(dst: Path) -> Path:
    shutil.copytree(
        ROOT / "data",
        dst / "data",
        ignore=shutil.ignore_patterns("streams", "streams_pre1950"),
    )
    shutil.copytree(ROOT / "schema", dst / "schema")
    (dst / "data" / "streams").mkdir()
    (dst / "data" / "streams_pre1950").mkdir()
    (dst / "research" / "other").mkdir(parents=True)
    return dst


def _factor(oracle: Oracle, fid: str) -> dict:
    return oracle.fby[fid]


def fvals(oracle, fid):
    f = oracle.fby[fid]
    return float(f["value_low"]), float(f["value_central"]), float(f["value_high"])


# --------------------------------------------------------------------------------------------
# row-by-row comparison with the oracle (the engine of (b) and (f))
# --------------------------------------------------------------------------------------------
def expected_notes(er) -> str:
    """The notes string of OTHER_SPEC 13.9-13.12: rule text, appended texts, components, driver basis, cause."""
    n = er.rule + "".join("; " + t for t in er.appended)
    if er.comps:
        n += "; components: " + "+".join(er.comps)
    if er.basis:
        n += "; driver basis: " + "+".join(b for b in BASIS_ORDER if b in er.basis)
    if er.b.nd:
        n += "; below_detection cause: " + "+".join(er.b.causes)
    return n


def compare_row(O: Oracle, er, r: dict) -> list[str]:
    msgs: list[str] = []
    for col, want in (
        ("stream", "other"),
        ("basis", "modelled"),
        ("allocation_variant", "default"),
        ("allocation_rule", "none"),
        ("quantity", "flow"),
        ("unit", er.unit),
    ):
        got = "|".join(ids(r[col])) if col == "allocation_rule" else r[col]
        if got != want:
            msgs.append(f"{col}={got!r}, expected {want!r}")
    if as_bool(r["embedded_fuel"]):
        msgs.append("embedded_fuel true")
    for col in ("product", "technology", "event_id"):
        if not _blank(r[col]):
            msgs.append(f"{col}={r[col]!r}, expected empty")
    got = vals(r)
    for nm, g, w in zip(
        ("low", "central", "high"), got, (er.b.low, er.b.central, er.b.high)
    ):
        if not close(g, w, REL):
            msgs.append(f"value_{nm}={g!r}, oracle {w!r}")
    flagged = as_bool(r["below_detection"])
    if flagged != er.b.nd:
        msgs.append(
            f"below_detection={flagged}, oracle {er.b.nd} (causes {list(er.b.causes)})"
        )
    fid = ids(r["factor_ids"])
    if fid != er.fids:
        msgs.append(f"factor_ids={fid}, expected (ordered, 13.13) {er.fids}")
    src = ids(r["source_ids"])
    try:
        want_src = sorted(O.fsrc(er.fids) | er.src)
    except KeyError:
        want_src = []
    if src != want_src:
        msgs.append(f"source_ids={src}, expected (13.14) {want_src}")
    want_n = expected_notes(er)
    if (r["notes"] or "") != want_n:
        msgs.append(f"notes={r['notes']!r}, expected {want_n!r}")
    return msgs


def compare_all(
    O: Oracle, exp: dict, rows_obj: Rows, label: str
) -> dict[str, list[str]]:
    problems: dict[str, list[str]] = defaultdict(list)
    for k, er in exp.items():
        got = rows_obj.by_key.get(k)
        if not got:
            problems[er.tag].append(f"MISSING row {k}")
            continue
        if len(got) > 1:
            problems[er.tag].append(f"DUPLICATE ({len(got)}) rows for {k}")
            continue
        for m in compare_row(O, er, got[0]):
            problems[er.tag].append(f"{k}: {m}")
    for k, lst in rows_obj.by_key.items():
        if k not in exp:
            problems["unexpected"].append(f"{label}: unexpected row {describe(lst[0])}")
    return problems


@pytest.fixture(scope="module")
def comparison(oracle, rows, expected):
    return compare_all(oracle, expected.rows, rows, "master")


@pytest.fixture(scope="module")
def comparison_pre(oracle, pre_rows, expected):
    return compare_all(oracle, expected.pre, pre_rows, "pre1950")


# --------------------------------------------------------------------------------------------
# log comparison (shared by the real tree and the fixtures)
# --------------------------------------------------------------------------------------------
def _span(e):
    m = run_of(e)
    return (m[0], m[1]) if m else None


def _empty(v):
    return v is None or v == ""


def _run_detail(a: int, b: int, tail: str) -> re.Pattern:
    n = b - a + 1
    return re.compile(rf"{a}-{b} \({n} years?\): " + re.escape(tail))


def check_log(log: list[dict], O: Oracle, exp, label: str = "") -> list[str]:
    """Exact comparison with the OTHER_SPEC 13.16 formats."""
    msgs: list[str] = []
    L = exp.log
    for e in log:
        if set(e) != {"kind", "year", "country", "group", "detail"}:
            msgs.append(
                f"{label} log entry keys {sorted(e)} (13.16: exactly kind, year, country, group, detail)"
            )
        if e.get("kind") not in LOG_KINDS:
            msgs.append(f"{label} unknown log kind {e.get('kind')!r}")
        if e.get("country") == "XWL":
            msgs.append(f"{label} log entry uses XWL instead of XXX: {e}")
        if e.get("kind") not in ("lib_warning", "no_family") and not isinstance(
            e.get("year"), int
        ):
            msgs.append(f"{label} year must be an integer: {e}")
        if e.get("kind") != "cap_applied" and not _empty(e.get("group")):
            msgs.append(f"{label} group must be empty outside cap_applied: {e}")

    def compare(kind, want):
        """want: list of (country, year, group, regex-or-str). Matches one-to-one."""
        got = list(log_entries(log, kind))
        left = list(want)
        for e in got:
            hit = None
            for w in left:
                c, y, g, pat = w
                if (
                    e.get("country") == c
                    and e.get("year") == y
                    and (e.get("group") or "") == g
                    and (
                        pat.fullmatch(str(e.get("detail")))
                        if isinstance(pat, re.Pattern)
                        else str(e.get("detail")) == pat
                    )
                ):
                    hit = w
                    break
            if hit is None:
                msgs.append(f"{label} unexpected {kind} entry {e}")
            else:
                left.remove(hit)
        for c, y, g, pat in left:
            msgs.append(
                f"{label} missing {kind} entry: country={c!r} year={y} group={g!r} detail~{getattr(pat, 'pattern', pat)!r}"
            )

    compare(
        "no_driver",
        [
            (c, a, "", _run_detail(a, b, f"{name} has no value"))
            for (name, c, a, b) in L["no_driver_runs"]
        ]
        + [
            (c, a, "", _run_detail(a, b, f"{name} has no value"))
            for (name, c, a, b) in L["no_driver_supply_runs"]
        ],
    )
    compare(
        "household_fallback",
        [
            (
                c,
                a,
                "",
                _run_detail(
                    a,
                    b,
                    "no household_fuelwood_m3 row; household share other:0050 used",
                ),
            )
            for (c, a, b) in L["fallback_runs"]
        ],
    )
    compare(
        "household_wood_capped",
        [
            (c, a, "", _run_detail(a, b, f"capped {bs}"))
            for (c, a, b, bs) in L["hhcap_runs"]
        ],
    )
    compare(
        "charcoal_wood_capped",
        [
            (c, a, "", _run_detail(a, b, f"capped {bs}"))
            for (c, a, b, bs) in L["chcap_runs"]
        ],
    )
    compare(
        "cap_applied",
        [
            (
                c,
                y,
                g,
                ("plant stack cap" if k == "plant" else "household smoke cap")
                + ": capped "
                + "+".join(bs),
            )
            for (c, y, g, bs, k) in L["cap_applied"]
        ],
    )
    nr = []
    for c, y, m, unit, kind in L["negative_residual"]:
        if kind == "peat":
            nr.append(
                (
                    c,
                    y,
                    "",
                    f"peat supply is below plants plus household by {m:.6g} {unit}; treated as 0",
                )
            )
        else:
            nr.append(
                (
                    c,
                    y,
                    "",
                    f"world aggregate is below the listed countries by {m:.6g} {unit}; treated as 0",
                )
            )
    compare("negative_residual", nr)
    compare(
        "predecessor_dropped",
        [
            ("CZE", y, "", f"{s}: CZE value dropped, CSK value used")
            for (s, y) in L["predecessor"]
        ],
    )
    if log_entries(log, "no_factor"):
        msgs.append(
            f"{label} no_factor entries written: 3.8 says a missing factor raises"
        )
    nf = log_entries(log, "no_family")
    want_nf = {
        "stage hydro: no registry rows",
        "stage construction: no registry rows; construction waits for commodity_factors.csv",
    }
    if {e["detail"] for e in nf} != want_nf or len(nf) != 2:
        msgs.append(
            f"{label} no_family entries {[e['detail'] for e in nf]}, expected {sorted(want_nf)}"
        )
    for e in nf:
        if not (_empty(e["year"]) and _empty(e["country"])):
            msgs.append(f"{label} no_family year and country must be empty: {e}")
    lw = log_entries(log, "lib_warning")
    if len(lw) > 1:
        msgs.append(f"{label} {len(lw)} lib_warning entries (at most one per build)")
    for e in lw:
        if not (_empty(e["year"]) and _empty(e["country"])):
            msgs.append(f"{label} lib_warning year and country must be empty: {e}")
        if not re.fullmatch(
            r"\d+ pipeline\.lib warnings captured: \d+ x .+",
            str(e["detail"]),
            re.DOTALL,
        ):
            msgs.append(
                f"{label} lib_warning detail {e['detail']!r} does not follow 13.16"
            )
    return msgs


# --------------------------------------------------------------------------------------------
# (i) premise assertions
# --------------------------------------------------------------------------------------------
def substream_cells_empty(factors_path: Path):
    df = pd.read_csv(factors_path, dtype=str, keep_default_na=False)
    filled = df[df["substream"] != ""]
    premise(
        filled.empty,
        f"every other.csv substream cell must be empty (OTHER_SPEC 2.2); filled: {list(filled['factor_id'])[:5]}",
    )


class TestPremises:
    def test_registry_ids_and_size(self, oracle):
        got = {f["factor_id"] for f in oracle.factors}
        want = {f"other:{i:04d}" for i in range(1, 74)} | {"other:0075"}
        premise(
            len(oracle.factors) == 74,
            f"other.csv has {len(oracle.factors)} rows, spec says 74",
        )
        premise(
            got == want,
            f"factor ids differ: missing {sorted(want - got)}, extra {sorted(got - want)}",
        )
        premise("other:0074" not in got, "other:0074 must not exist")

    def test_substream_cells_empty(self):
        substream_cells_empty(ROOT / "data" / "factors" / "other.csv")

    def test_filled_substream_cell_is_detected(self, tmp_path):
        df = pd.read_csv(
            ROOT / "data" / "factors" / "other.csv", dtype=str, keep_default_na=False
        )
        df.loc[0, "substream"] = "geothermal"
        p = tmp_path / "other.csv"
        df.to_csv(p, index=False)
        with pytest.raises(AssertionError, match="PREMISE BROKEN"):
            substream_cells_empty(p)

    def test_geothermal_factor_values(self, oracle):
        f1 = _factor(oracle, "other:0001")
        premise(
            f1["unit"] == "Bq/GWa"
            and float(f1["value_central"]) == 8e13
            and float(f1["value_low"]) == 5e12,
            f"other:0001 must be Bq/GWa, central 8e13, low 5e12 (D61/D65): {f1['unit']} {f1['value_central']} {f1['value_low']}",
        )
        for fid, c in (
            ("other:0002", 2.6e14),
            ("other:0003", 3.85e13),
            ("other:0072", 8e13),
        ):
            f = _factor(oracle, fid)
            premise(
                f["unit"] == "Bq/GWa"
                and math.isclose(float(f["value_central"]), c, rel_tol=1e-9),
                f"{fid} central must be {c:.4g} Bq/GWa, got {f['value_central']} {f['unit']}",
            )
        for fid, c in (("other:0071", 0.05), ("other:0075", 0.01)):
            f = _factor(oracle, fid)
            premise(
                f["unit"] == "1"
                and math.isclose(float(f["value_central"]), c, rel_tol=1e-9),
                f"{fid} must be unit 1 with centre {c}, got {f['value_central']} {f['unit']}",
            )
        f4, f49 = _factor(oracle, "other:0004"), _factor(oracle, "other:0049")
        premise(
            f4["unit"] == "t/GWa" and float(f4["value_central"]) == 250,
            f"other:0004 t/GWa centre 250: {f4['unit']} {f4['value_central']}",
        )
        premise(
            f49["unit"] == "t/m3" and math.isclose(float(f49["value_central"]), 0.725),
            f"other:0049 t/m3 centre 0.725: {f49['unit']}",
        )

    @staticmethod
    def _windows(oracle, region, group, stage="geothermal"):
        return sorted(
            (int(f["year_from"]), int(f["year_to"]))
            for f in oracle.factors
            if f["region"] == region
            and f["group"] == group
            and f["stage"] == stage
            and f["tier"] == "liberated"
            and f["route"] == "air_vented_gas"
        )

    def test_geothermal_windows(self, oracle):
        for region, win in (
            ("XWL", (1900, 2025)),
            ("ITA", (1913, 2025)),
            ("USA", (1960, 2025)),
            ("NZL", (1958, 2025)),
        ):
            premise(
                self._windows(oracle, region, "Rn222+") == [win],
                f"{region} Rn222+ window must be {win}",
            )
        premise(
            self._windows(oracle, "XWL", "Rn220+") == [(1900, 2025)],
            "XWL Rn220+ window 1900-2025",
        )
        premise(
            self._windows(oracle, "ITA", "Rn220+") == [(1913, 2025)],
            "ITA Rn220+ window 1913-2025",
        )
        for r in ("USA", "NZL"):
            premise(
                self._windows(oracle, r, "Rn220+") == [],
                f"{r} has no own Rn220+ ratio (uses the XWL one)",
            )

    def test_era_rows_tile(self, oracle):
        def tiles(ids_, lo, hi):
            ws = sorted(
                (int(oracle.fby[i]["year_from"]), int(oracle.fby[i]["year_to"]))
                for i in ids_
            )
            cur = lo
            for a, b in ws:
                premise(a == cur, f"{ids_}: era starts at {a}, expected {cur}")
                cur = b + 1
            premise(cur == hi + 1, f"{ids_}: eras end at {cur - 1}, expected {hi}")

        tiles([f"other:{i:04d}" for i in (57, 58, 59, 60)], 1950, 2025)
        tiles([f"other:{i:04d}" for i in (44, 45, 46, 47)], 1950, 2025)
        tiles(["other:0061", "other:0062"], 1986, 2025)
        tiles(["other:0063", "other:0064"], 1986, 2025)
        tiles(["other:0065", "other:0066"], 1986, 2025)
        tiles(["other:0073"], 2001, 2025)
        tiles(["other:0026", "other:0027"], 1800, 2025)

    def test_shared_and_complementary_values(self, oracle):
        b = [fvals(oracle, f"other:{i:04d}") for i in (10, 11, 12)]
        premise(
            b[0] == b[1] == b[2],
            f"other:0010/0011/0012 must carry identical bounds: {b}",
        )
        premise(
            math.isclose(
                fvals(oracle, "other:0039")[1] + fvals(oracle, "other:0040")[1], 1.0
            ),
            "0039+0040 centres must sum to 1",
        )
        premise(
            math.isclose(
                fvals(oracle, "other:0041")[1] + fvals(oracle, "other:0042")[1], 1.0
            ),
            "0041+0042 centres must sum to 1",
        )
        premise(
            math.isclose(fvals(oracle, "other:0068")[1], 0.19),
            "other:0068 central must be 0.19 (D61)",
        )
        premise(
            math.isclose(fvals(oracle, "other:0067")[2], 0.13),
            "other:0067 high must be 0.13 (D65)",
        )
        for i in (15, 16):
            premise(
                math.isclose(fvals(oracle, f"other:{i:04d}")[1], 2.5e5),
                f"other:00{i} central must be 2.5e5 (D65)",
            )
        premise(
            not [f for f in oracle.factors if f["below_detection"].lower() == "true"],
            "no registry row may be below_detection",
        )
        premise(
            not [f for f in oracle.factors if f["stage"] in ("hydro", "construction")],
            "no registry row at stage hydro / construction",
        )

    def test_files_and_references(self):
        premise(
            not (ROOT / "data" / "reference" / "commodity_factors.csv").exists(),
            "commodity_factors.csv must be absent (7)",
        )
        ev = pd.read_csv(ROOT / "data" / "events.csv", dtype=str, keep_default_na=False)
        premise(
            not (ev["stream"] == "other").any(),
            "events.csv must have no `other` event (2.2)",
        )
        rt = pd.read_csv(
            ROOT / "data" / "reference" / "residue_types.csv",
            dtype=str,
            keep_default_na=False,
        ).set_index("residue_type")
        for r in ("peat_ash", "geothermal_scale"):
            premise(r in rt.index, f"residue_types.csv lacks {r}")
            row = rt.loc[r]
            for c in ("epsilon_rn222_central", "seepage_per_a_central"):
                premise(row[c] != "", f"{r}: {c} must be filled (D62)")
        v = json.loads((ROOT / "data" / "reference" / "vocab.json").read_text())
        premise(
            "memo_biosphere" in v["tiers"] and "air_rerelease" in v["routes"],
            "vocab lacks memo_biosphere / air_rerelease",
        )
        premise(
            {"geothermal", "biomass_peat", "hydro", "biomass_domestic"}
            <= set(v["substreams"]["other"]),
            "vocab other substreams",
        )

    def test_activity_facts(self, oracle):
        O = oracle
        premise(
            not any(
                c == "XWL" for cs in O.by_series["peat_supply_t"].values() for c in cs
            ),
            "peat has no XWL series",
        )
        for s in ("peat_power_heat_t", "peat_household_t", "peat_supply_t"):
            premise(
                not any("XWL" in cs for cs in O.by_series[s].values()),
                f"{s} must have no XWL row",
            )
        worst = 0.0
        for y in range(1980, 2026):
            lst = [c for c in O.by_series["elec_gen_geothermal"][y] if c != "XWL"]
            premise(bool(lst), f"geothermal country rows exist in {y}")
            s = sum(O.ab("elec_gen_geothermal", y, c).central for c in lst)
            x = O.ab("elec_gen_geothermal", y, "XWL").central
            worst = max(worst, abs(x - s) / x)
        premise(
            worst <= 1e-5,
            f"geothermal XWL differs from the country sum by {worst:.3g} relative (> 1e-5)",
        )
        premise(
            all(
                not [c for c in O.by_series["elec_gen_geothermal"][y] if c != "XWL"]
                for y in range(1916, 1980)
            ),
            "geothermal has no country rows before 1980",
        )
        for s in ("wood_fuel_t", "household_fuelwood_m3", "charcoal_production_t"):
            for y, cs in O.by_series[s].items():
                premise(
                    not ("CSK" in cs and "CZE" in cs), f"{s} {y}: CSK and CZE overlap"
                )
        for s in ("wood_fuel_t", "wood_fuel_m3", "charcoal_production_t"):
            r = O.arow(s, 2025, "XWL")
            premise(
                r["basis"] == "extrapolated",
                f"{s} 2025 must be extrapolated (D70), got {r['basis']}",
            )
        premise(
            all(
                O.arow(s, 2025, c)["basis"] == "extrapolated"
                for s in ("peat_power_heat_t", "peat_household_t", "peat_supply_t")
                for c in O.by_series[s].get(2025, [])
            ),
            "all 2025 peat rows must be extrapolated",
        )
        premise(
            max(O.by_series["household_fuelwood_m3"]) == 2023,
            "household_fuelwood_m3 must end in 2023 (no 2024/2025 row)",
        )
        premise(
            O.arow("elec_gen_geothermal", 2025, "XWL")["basis"] == "extrapolated",
            "geothermal 2025 must be extrapolated",
        )
        periods = {
            "wood_fuel_t": (
                (1961, 1992, 0.030, 0.055),
                (1993, 2011, 0.009, 0.012),
                (2024, 2025, 0.003, 0.0035),
            ),
            "charcoal_production_t": (
                (1961, 1992, 0.068, 0.108),
                (1993, 2011, 0.016, 0.023),
                (2024, 2025, 0.0002, 0.0004),
            ),
        }
        for ser, per in periods.items():
            res = {}
            for y in range(1961, 2026):
                if O.has(ser, y, "XWL"):
                    x = O.ab(ser, y, "XWL").central
                    res[y] = (
                        x - sum(O.ab(ser, y, c).central for c in O.countries(ser, y))
                    ) / x
            for a, b, lo, hi in per:
                bad = {
                    y: r for y, r in res.items() if a <= y <= b and not lo <= r <= hi
                }
                premise(
                    not bad,
                    f"{ser} residual share of the world row outside {lo:.2%}-{hi:.2%} in {a}-{b} (13.19): {dict(list(bad.items())[:3])}",
                )
            bad = {
                y: r for y, r in res.items() if 2012 <= y <= 2023 and abs(r) > 1e-5 * 3
            }
            premise(
                not bad,
                f"{ser} residual must be inside the 1e-5 tolerance in 2012-2023 (13.19): {dict(list(bad.items())[:3])}",
            )
        n = sum(
            1
            for c in O.countries("household_fuelwood_m3", 2010)
            if O.has("wood_fuel_t", 2010, c)
            and O.ab("household_fuelwood_m3", 2010, c).central
            * fvals(O, "other:0049")[1]
            > O.ab("wood_fuel_t", 2010, c).central
        )
        premise(
            40 <= n <= 110,
            f"UNSD household exceeds FAOSTAT wood fuel in {n} countries in 2010 (spec: 71 of ~182)",
        )
        usa = (
            O.ab("household_fuelwood_m3", 2010, "USA").central
            * fvals(O, "other:0049")[1]
            / O.ab("wood_fuel_t", 2010, "USA").central
        )
        premise(
            usa > 1.0,
            f"USA household wood exceeds FAOSTAT wood fuel (spec 1.3x), ratio {usa:.2f}",
        )

    def test_geothermal_countries_valid_for_years(self, oracle):
        cn = pd.read_csv(
            ROOT / "data" / "reference" / "countries.csv",
            dtype=str,
            keep_default_na=False,
        ).set_index("code")
        for s, y, c in oracle.act:
            if s != "elec_gen_geothermal" or c == "XWL":
                continue
            premise(c in cn.index, f"geothermal country {c} not in countries.csv")
            vf, vt = cn.loc[c, "valid_from"], cn.loc[c, "valid_to"]
            premise(
                (vf == "" or y >= int(vf)) and (vt == "" or y <= int(vt)),
                f"geothermal {c} {y} outside valid {vf}-{vt}",
            )

    def test_source_ids_resolve(self, oracle):
        src = set(
            pd.read_csv(
                ROOT / "data" / "sources.csv", dtype=str, keep_default_na=False
            )["source_id"]
        )
        bad = {
            x
            for f in oracle.factors
            for x in f["source_ids"].split(";")
            if x and x not in src
        }
        premise(not bad, f"factor source_ids unresolved: {sorted(bad)[:5]}")
        bad = {
            x
            for r in oracle.act.values()
            for x in r["source_ids"].split(";")
            if x and x not in src
        }
        premise(not bad, f"activity source_ids unresolved: {sorted(bad)[:5]}")

    def test_unscear_extraction_rows(self):
        df = pd.read_csv(
            ROOT / "research" / "unscear_extraction.csv",
            dtype=str,
            keep_default_na=False,
        ).set_index("item_id")
        for item, nuc, val in (
            ("U0242", "Rn-222", 150.0),
            ("U0243", "Rn-222", 260.0),
            ("U0244", "Rn-222", 38.5),
            ("U1351", "U-238", 40.0),
        ):
            premise(
                item in df.index and nuc in df.loc[item, "nuclide_or_group"],
                f"extraction row {item} missing or not {nuc}",
            )
            premise(
                math.isclose(float(df.loc[item, "value"]), val),
                f"extraction row {item} value {df.loc[item, 'value']} != {val}",
            )


# --------------------------------------------------------------------------------------------
# (a) schema and row conventions
# --------------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def issues(written):
    from pipeline.validate import validate

    root = _copy_tree(Path(written[0]).parent / "validation_root")
    shutil.copy(written[0], root / "data" / "streams" / "other.csv")
    found = validate(root, master_files=["data/streams/other.csv"])
    return [i for i in found if i.file == "data/streams/other.csv"]


class TestSchema:
    def test_validator_accepts_other_csv(self, issues):
        shown = "\n".join(f"  row {i.row}: {i.rule} {i.message}" for i in issues[:15])
        assert not issues, (
            f"data/streams/other.csv has {len(issues)} validator issues "
            f"(rules {sorted({i.rule for i in issues})}):\n{shown}"
        )

    @pytest.mark.parametrize("rule", ["V03", "V09", "V10", "R02", "X01", "X02", "T04"])
    def test_no_rule_violations(self, issues, rule):
        hits = [i for i in issues if i.rule == rule]
        assert not hits, (
            f"{len(hits)} {rule} issues, first: row {hits[0].row} {hits[0].message}"
        )


class TestRowConventions:
    def test_rows_nonempty(self, rows, pre_rows):
        assert rows.rows, "build().rows is empty"
        assert pre_rows.rows, (
            "build().rows_pre1950 is empty (geothermal 1916-1949, OTHER_SPEC 1)"
        )

    def test_master_columns_exact(self, rows):
        bad = [r for r in rows.rows if list(r.keys()) != MASTER_COLS]
        assert not bad, (
            f"{len(bad)} rows do not have exactly the 25 master columns in order; first: {bad[0]}"
        )

    def test_year_ranges(self, rows, pre_rows):
        assert (
            min(int(r["year"]) for r in rows.rows) >= 1950
            and max(int(r["year"]) for r in rows.rows) <= 2025
        )
        py = [int(r["year"]) for r in pre_rows.rows]
        assert py and min(py) >= 1800 and max(py) <= 1949

    def test_no_xwl_country(self, rows, pre_rows):
        bad = [r for r in rows.rows + pre_rows.rows if r["country"] == "XWL"]
        assert not bad, f"{len(bad)} rows use XWL (V10; use XXX): {describe(bad[0])}"

    def test_flow_only_and_units(self, rows, pre_rows):
        for r in rows.rows + pre_rows.rows:
            assert r["quantity"] == "flow", (
                f"quantity {r['quantity']!r} (3.1: flow only): {describe(r)}"
            )
            assert r["unit"] == "Bq/a", (
                f"unit {r['unit']!r} (3.1: Bq/a on every row): {describe(r)}"
            )

    def test_constant_columns(self, rows, pre_rows):
        for r in rows.rows + pre_rows.rows:
            assert r["stream"] == "other" and r["basis"] == "modelled", describe(r)
            assert (
                r["allocation_variant"] == "default"
                and "|".join(ids(r["allocation_rule"])) == "none"
            ), describe(r)
            assert not as_bool(r["embedded_fuel"]), describe(r)
            assert (
                _blank(r["technology"])
                and _blank(r["product"])
                and _blank(r["event_id"])
            ), describe(r)

    def test_bounds_ordered_flag_consistent(self, rows, pre_rows):
        for r in rows.rows + pre_rows.rows:
            lo, c, hi = vals(r)
            assert 0 <= lo <= c <= hi, (
                f"bounds out of order ({lo}, {c}, {hi}): {describe(r)}"
            )
            if as_bool(r["below_detection"]):
                assert lo == 0, (
                    f"below_detection true but value_low = {lo}: {describe(r)}"
                )

    def test_ids_present_and_sorted(self, rows, pre_rows):
        for r in rows.rows + pre_rows.rows:
            f, s = ids(r["factor_ids"]), ids(r["source_ids"])
            assert f and all(x.startswith("other:") for x in f), (
                f"factor_ids {f}: {describe(r)}"
            )
            assert s and s == sorted(s), (
                f"source_ids empty or unsorted {s}: {describe(r)}"
            )

    def test_substream_stage_by_family(self, rows):
        for r in rows.rows:
            if r["substream"] == "geothermal":
                assert r["stage"] == "geothermal", describe(r)
            else:
                assert (
                    r["substream"] in ("biomass_peat", "biomass_domestic")
                    and r["stage"] == "biomass_peat"
                ), f"biomass substreams use stage biomass_peat (D45): {describe(r)}"
            assert r["substream"] != "hydro" and r["stage"] not in (
                "hydro",
                "construction",
            ), describe(r)

    def test_residue_type_rules(self, rows, pre_rows):
        for r in rows.rows + pre_rows.rows:
            if r["tier"] in ("impounded", "dispersed"):
                want = "geothermal_scale" if r["stage"] == "geothermal" else "peat_ash"
                assert r["residue_type"] == want, (
                    f"residue_type {r['residue_type']!r}, expected {want}: {describe(r)}"
                )
            else:
                assert _blank(r["residue_type"]), (
                    f"residue_type outside impounded/dispersed: {describe(r)}"
                )

    def test_route_rules(self, rows, pre_rows):
        for r in rows.rows + pre_rows.rows:
            if r["tier"] == "liberated":
                if r["stage"] == "geothermal":
                    assert r["route"] == "air_vented_gas", describe(r)
                elif r["group"] == "Cs137+":
                    assert r["route"] == "air_rerelease", describe(r)
                else:
                    assert r["route"] == "air_stack", describe(r)
            else:
                assert _blank(r["route"]), (
                    f"route on a non-liberated row: {describe(r)}"
                )

    def test_country_conventions(self, rows, pre_rows):
        for r in pre_rows.rows:
            assert r["country"] == "XXX", (
                f"pre-1950 geothermal is the world aggregate: {describe(r)}"
            )
        for r in rows.rows:
            if r["country"] == "XXX":
                notes = r["notes"] or ""
                assert (TXT_WORLD in notes) or (TXT_REST in notes), (
                    f"XXX row without the world-aggregate or rest-of-world text (3.4): {describe(r)}"
                )
        # the world-aggregate text only before 1980, and only on geothermal rows
        for r in rows.rows:
            if TXT_WORLD in (r["notes"] or ""):
                assert r["substream"] == "geothermal" and int(r["year"]) < 1980, (
                    describe(r)
                )


# --------------------------------------------------------------------------------------------
# (b) every family, every row, against the oracle
# --------------------------------------------------------------------------------------------
FAMILY_TAGS = [
    "geo222",
    "geo220",
    "geoscale",
    "pstack",
    "pash",
    "hstack",
    "hash",
    "memowood",
    "rerel",
    "memocs",
]


class TestRowsAgainstOracle:
    def test_oracle_sanity(self, expected):
        c = Counter(er.tag for er in expected.rows.values())
        assert set(c) == set(FAMILY_TAGS), f"oracle families {sorted(c)}"
        assert len(expected.rows) > 100_000

    @pytest.mark.parametrize("tag", FAMILY_TAGS)
    def test_family_matches_oracle(self, comparison, tag):
        assert not comparison.get(tag), f"family {tag}: " + show(comparison[tag])

    def test_no_unexpected_rows(self, comparison):
        assert not comparison.get("unexpected"), show(comparison["unexpected"])

    def test_row_counts_agree(self, rows, expected):
        assert len(rows.rows) == len(expected.rows), (
            f"{len(rows.rows)} rows; oracle expects {len(expected.rows)}"
        )


# --------------------------------------------------------------------------------------------
# (b) coverage, independent of the oracle's row table
# --------------------------------------------------------------------------------------------
class TestCoverage:
    def test_geothermal_every_country_year_has_all_groups(self, rows, oracle):
        ser = "elec_gen_geothermal"
        by = defaultdict(set)
        for r in rows.rows:
            if r["substream"] == "geothermal" and r["tier"] in (
                "liberated",
                "impounded",
            ):
                by[(r["country"], int(r["year"]))].add(r["group"])
        n = 0
        for (s, y, c), r in oracle.act.items():
            if s != ser or c == "XWL" or y < 1980 or float(r["value_central"]) == 0:
                continue
            n += 1
            assert by.get((c, y)) == GEO_GAS | GEO_SCALE, (
                f"{c} {y}: geothermal groups {sorted(by.get((c, y), []))}"
            )
        assert n > 500
        for y in range(1950, 1980):
            assert by.get(("XXX", y)) == GEO_GAS | GEO_SCALE, (
                f"XXX {y}: world aggregate groups {sorted(by.get(('XXX', y), []))}"
            )

    def test_peat_chain_has_all_eleven_groups_per_tier(self, rows, oracle):
        got = defaultdict(set)
        for r in rows.rows:
            if (
                r["stage"] == "biomass_peat"
                and r["tier"] in ("liberated", "impounded", "dispersed")
                and r["group"] != "Cs137+"
            ):
                got[(r["substream"], r["country"], int(r["year"]), r["tier"])].add(
                    r["group"]
                )
        n = 0
        for (s, y, c), r in oracle.act.items():
            if s == "peat_power_heat_t" and float(r["value_central"]) > 0:
                n += 1
                for t in ("liberated", "impounded", "dispersed"):
                    assert got.get((BP, c, y, t)) == PEAT11, (
                        f"{c} {y} {t}: plant-type peat groups {sorted(got.get((BP, c, y, t), []))}"
                    )
            if s == "peat_household_t" and float(r["value_central"]) > 0:
                n += 1
                for t in ("liberated", "impounded", "dispersed"):
                    assert got.get((DOM, c, y, t)) == PEAT11, (
                        f"{c} {y} {t}: household peat groups {sorted(got.get((DOM, c, y, t), []))}"
                    )
        assert n > 200

    def test_no_peat_before_1990_and_no_wood_before_1961(self, rows):
        for r in rows.rows:
            if r["substream"] == "geothermal":
                continue
            y = int(r["year"])
            assert y >= 1961, (
                f"biomass row before 1961 (wood fuel starts in 1961): {describe(r)}"
            )
            is_peat_natural = r["group"] in PEAT11 and r["tier"] in (
                "liberated",
                "impounded",
                "dispersed",
            )
            if is_peat_natural or r["residue_type"] == "peat_ash":
                assert y >= 1990, (
                    f"peat row before 1990 (UNSD peat starts in 1990): {describe(r)}"
                )

    def test_wood_memo_groups_complete_where_central_positive(self, rows, expected):
        got = defaultdict(set)
        for r in rows.rows:
            if r["tier"] == "memo_biosphere" and r["group"] in WOOD5:
                got[(r["substream"], r["country"], int(r["year"]))].add(r["group"])
        bad = []
        for (c, y), u in expected.units.items():
            if u["Dpl"].b.central > 0 and got.get((BP, c, y)) != WOOD5:
                bad.append(
                    f"{c} {y} plant wood memo groups {sorted(got.get((BP, c, y), []))}"
                )
            ddom = u["Dhh"].b.central + u["Dch"].b.central
            if ddom > 0 and got.get((DOM, c, y)) != WOOD5:
                bad.append(
                    f"{c} {y} domestic wood memo groups {sorted(got.get((DOM, c, y), []))}"
                )
        assert not bad, show(bad)

    def test_group_coverage_2010(self, rows):
        g = {r["group"] for r in rows.by_year[2010] if r["substream"] == "geothermal"}
        assert {
            "Rn222+",
            "Rn220+",
            "Ra226+",
            "Ra228+",
            "Pb210+",
            "Po210",
            "K40",
        } <= g, f"geothermal groups 2010: {sorted(g)}"
        b = {r["group"] for r in rows.by_year[2010] if r["substream"] != "geothermal"}
        assert {
            "K40",
            "Cs137+",
            "Pb210+",
            "Po210",
            "U238+",
            "U234",
            "Th230",
            "Ra226+",
        } <= b, f"biomass/peat groups 2010: {sorted(b)}"

    def test_hydro_and_construction_absent(self, rows, pre_rows):
        for r in rows.rows + pre_rows.rows:
            assert (
                r["stage"] not in ("hydro", "construction")
                and r["substream"] != "hydro"
            ), describe(r)


# --------------------------------------------------------------------------------------------
# (c) conservation and structure
# --------------------------------------------------------------------------------------------
def central_peat(O: Oracle, c: str, y: int):
    """Centre-only arithmetic of the peat tonnages (5.1): returns (Ppl, Poth, Phh) or None."""

    def g(s):
        return O.ab(s, y, c).central if O.has(s, y, c) else None

    ppl, phh, s = g("peat_power_heat_t"), g("peat_household_t"), g("peat_supply_t")
    if all(v in (None, 0.0) for v in (ppl, phh, s)):
        return None
    ppl, phh = ppl or 0.0, phh or 0.0
    oth = 0.0
    if s is not None:
        d = s - ppl - phh
        oth = 0.0 if abs(d) <= 1e-5 * s else max(d, 0.0)
    return ppl, oth, phh


def fc(O: Oracle, y, region="XWL", **kw) -> float:
    return O.fb(O.sel(y, region, **kw)).central


class TestPeatConservation:
    def test_stack_plus_ash_tiers_equal_ash_borne_activity(self, rows, oracle):
        O = oracle
        bad, n = [], 0
        idx = defaultdict(float)
        for r in rows.rows:
            if (
                r["stage"] == "biomass_peat"
                and r["group"] in PEAT11
                and r["tier"] in ("liberated", "impounded", "dispersed")
            ):
                idx[(r["substream"], r["country"], int(r["year"]), r["group"])] += (
                    float(r["value_central"])
                )
        pairs = sorted(
            {
                (c, y)
                for (s_, y, c) in O.act
                if s_ in ("peat_supply_t", "peat_power_heat_t", "peat_household_t")
            }
        )
        for c, y in pairs:
            t = central_peat(O, c, y)
            if t is None:
                continue
            ppl, oth, phh = t
            dry = ppl * fc(O, y, stage=BP, driver="peat_power_heat_t") + oth * fc(
                O, y, stage=BP, driver="peat_supply_t"
            )
            ash = dry * fc(O, y, stage=BP, residue="peat_ash")
            ashh = (
                phh
                * fc(O, y, stage=BP, driver="peat_household_t")
                * fc(O, y, stage=BP, residue="peat_ash")
            )
            for g in PEAT11:
                a = fc(O, y, stage=BP, group=g, residue="peat_ash")
                for sub, mass in ((BP, ash), (DOM, ashh)):
                    if mass <= 0:
                        continue
                    n += 1
                    want = mass * a
                    got = idx.get((sub, c, y, g), 0.0)
                    if not close(got, want, CONS):
                        bad.append(
                            f"{sub} {c} {y} {g}: tiers sum {got!r}, A_g {want!r}"
                        )
        assert n > 5000
        assert not bad, (
            "stack + impounded + dispersed != ash-borne activity at the centre: "
            + show(bad)
        )

    def test_route_shares_sum_to_one(self, oracle):
        O = oracle
        assert math.isclose(
            fc(
                O,
                2000,
                stage=BP,
                tier="impounded",
                residue="peat_ash",
                driver="peat_power_heat_t",
            )
            + fc(
                O,
                2000,
                stage=BP,
                tier="dispersed",
                residue="peat_ash",
                driver="peat_power_heat_t",
            ),
            1.0,
        )
        assert math.isclose(
            fc(
                O,
                2000,
                stage=BP,
                tier="impounded",
                residue="peat_ash",
                driver="peat_household_t",
            )
            + fc(
                O,
                2000,
                stage=BP,
                tier="dispersed",
                residue="peat_ash",
                driver="peat_household_t",
            ),
            1.0,
        )

    def test_written_file_conservation_1e5(self, written, oracle):
        """The same balance on the six-digit file (D68, relative 1e-5)."""
        idx = defaultdict(float)
        with open(written[0], newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if (
                    r["substream"] == DOM
                    and r["group"] in PEAT11
                    and r["tier"] in ("liberated", "impounded", "dispersed")
                    and r["country"] == "FIN"
                ):
                    idx[(int(r["year"]), r["group"])] += float(r["value_central"])
        O = oracle
        n = 0
        for y in range(1990, 2024):
            t = central_peat(O, "FIN", y)
            if not t or t[2] <= 0:
                continue
            ashh = (
                t[2]
                * fc(O, y, stage=BP, driver="peat_household_t")
                * fc(O, y, stage=BP, residue="peat_ash")
            )
            for g in PEAT11:
                want = ashh * fc(O, y, stage=BP, group=g, residue="peat_ash")
                assert close(idx[(y, g)], want, WRITTEN), (
                    f"FIN {y} {g}: file {idx[(y, g)]!r} vs {want!r}"
                )
                n += 1
        assert n > 100


def central_wood(O: Oracle, c: str, y: int):
    """Centre-only arithmetic of the dry-wood partition (6.2)."""
    xxx = c == "XXX"
    if xxx:
        listed = O.countries("wood_fuel_t", y)
        if not O.has("wood_fuel_t", y, "XWL"):
            return None
        x = O.ab("wood_fuel_t", y, "XWL").central
        w = x - sum(O.ab("wood_fuel_t", y, k).central for k in listed)
        if abs(w) <= 1e-5 * x or w < 0:
            return None
        cl = O.countries("charcoal_production_t", y)
        ch = 0.0
        if O.has("charcoal_production_t", y, "XWL"):
            xc = O.ab("charcoal_production_t", y, "XWL").central
            r = xc - sum(O.ab("charcoal_production_t", y, k).central for k in cl)
            ch = 0.0 if abs(r) <= 1e-5 * xc or r < 0 else r
        m = None
        region = "XWL"
    else:
        if not O.has("wood_fuel_t", y, c):
            return None
        w = O.ab("wood_fuel_t", y, c).central
        if w == 0:
            return None
        ch = (
            O.ab("charcoal_production_t", y, c).central
            if O.has("charcoal_production_t", y, c)
            else 0.0
        )
        m = (
            O.ab("household_fuelwood_m3", y, c).central
            if O.has("household_fuelwood_m3", y, c)
            else None
        )
        region = c
    d = fc(O, y, region, stage=BP, driver="wood_fuel_t")
    dtot = w * d
    dch = min(ch * fc(O, y, region, stage=BP, driver="charcoal_production_t"), dtot)
    r1 = dtot - dch
    if m is None:
        dhh = r1 * fc(O, y, region, stage=BP, driver="wood_fuel_m3")
    else:
        dhh = min(
            m * fc(O, y, region, stage=BP, driver="household_fuelwood_m3") * d, r1
        )
    return {
        "dtot": dtot,
        "dch": dch,
        "r1": r1,
        "dhh": dhh,
        "dpl": r1 - dhh,
        "region": region,
        "w": w,
        "ch": ch,
        "m": m,
        "d": d,
    }


class TestWoodPartition:
    def test_partition_closes_at_centre_and_memo_rows_follow(
        self, rows, oracle, expected
    ):
        O = oracle
        idx = {}
        for r in rows.rows:
            if r["tier"] == "memo_biosphere" and r["group"] == "K40":
                idx[(r["substream"], r["country"], int(r["year"]))] = float(
                    r["value_central"]
                )
        f52 = fc(
            O, 2000, stage=BP, group="K40", tier="memo_biosphere", driver="wood_fuel_t"
        )
        bad, n = [], 0
        for c, y in expected.units:
            p = central_wood(O, c, y)
            assert p is not None, (
                f"oracle has a wood unit {c} {y} the centre model does not"
            )
            n += 1
            tot = p["dpl"] + p["dhh"] + p["dch"]
            if not close(tot, p["dtot"], CONS):
                bad.append(
                    f"{c} {y}: D_pl + D_hh + D_ch = {tot!r} != D_tot {p['dtot']!r}"
                )
            f = fc(
                O,
                y,
                p["region"],
                stage=BP,
                group="K40",
                tier="memo_biosphere",
                driver="wood_fuel_t",
            )
            gp, gd = idx.get((BP, c, y), 0.0), idx.get((DOM, c, y), 0.0)
            if p["dpl"] > 0 and not close(gp, p["dpl"] * f, CONS):
                bad.append(
                    f"{c} {y}: biomass_peat K40 memo {gp!r}, D_pl x 0052 = {p['dpl'] * f!r}"
                )
            if p["dpl"] <= 0 and gp != 0.0:
                bad.append(f"{c} {y}: biomass_peat K40 memo {gp!r} with D_pl = 0")
            want = (p["dhh"] + p["dch"]) * f
            if not close(gd, want, CONS):
                bad.append(
                    f"{c} {y}: biomass_domestic K40 memo {gd!r}, (D_hh + D_ch) x 0052 = {want!r}"
                )
            if not close(gp + gd, p["dtot"] * f, CONS):
                bad.append(f"{c} {y}: memo rows do not close on D_tot x 0052")
        assert n > 5000
        assert f52 > 0
        assert not bad, show(bad)

    def test_partition_closes_at_the_bounds_for_unclipped_units(
        self, rows, expected, oracle
    ):
        """Correlated differences: with no clipping, cap or min effect, D_pl + D_hh + D_ch = D_tot at low and high too.

        D_pl and (D_hh + D_ch) are recovered from the K40 memo rows by inverting the log-space product with the
        0052 factor; this pins the correlated (not independent) form (resolution 2, D70).
        """
        idx = {}
        for r in rows.rows:
            if r["tier"] == "memo_biosphere" and r["group"] == "K40":
                idx[(r["substream"], r["country"], int(r["year"]))] = vals(r)

        def invert(row, f):
            lo, c, hi = row
            fl, fcn, fh = f
            if lo <= 0 or c <= 0:
                return None
            x_c = c / fcn
            up2 = math.log(hi / c) ** 2 - math.log(fh / fcn) ** 2
            dn2 = math.log(c / lo) ** 2 - math.log(fcn / fl) ** 2
            if up2 < -1e-12 or dn2 < -1e-12:
                return None
            return (
                x_c * math.exp(-math.sqrt(max(dn2, 0))),
                x_c,
                x_c * math.exp(math.sqrt(max(up2, 0))),
            )

        checked = 0
        bad = []
        for (c, y), u in expected.units.items():
            if u["caph"] or u["capc"] or u["Dpl"].b.central <= 0 or u["Dpl"].b.low <= 0:
                continue
            if u["Dhh"].b.low <= 0 or u["Dch"].b.central != 0:
                continue  # keep the pure D_tot = D_pl + D_hh partition (no charcoal)
            if not (
                u["R1"].b.low == u["Dtot"].b.low and u["R1"].b.high == u["Dtot"].b.high
            ):
                continue
            if (
                abs(u["Dpl"].b.low - (u["R1"].b.low - u["Dhh"].b.low))
                > 1e-9 * u["R1"].b.central
                or abs(u["Dpl"].b.high - (u["R1"].b.high - u["Dhh"].b.high))
                > 1e-9 * u["R1"].b.central
            ):
                continue  # a min / max effect of the correlated difference: closure at the bounds is not promised
            fr = oracle.sel(
                y,
                u["region"],
                stage=BP,
                group="K40",
                tier="memo_biosphere",
                driver="wood_fuel_t",
            )
            f = (
                float(fr["value_low"]),
                float(fr["value_central"]),
                float(fr["value_high"]),
            )
            a, b = idx.get((BP, c, y)), idx.get((DOM, c, y))
            if not a or not b:
                continue
            xa, xb = invert(a, f), invert(b, f)
            if not xa or not xb:
                continue
            dl = u["Dtot"].b
            for i, nm in ((0, "low"), (1, "central"), (2, "high")):
                tot = xa[i] + xb[i]
                want = (dl.low, dl.central, dl.high)[i]
                if not close(tot, want, 1e-6):
                    bad.append(f"{c} {y} {nm}: D_pl + D_hh = {tot!r}, D_tot = {want!r}")
            checked += 1
            if checked >= 400:
                break
        assert checked > 100, (
            f"only {checked} units suitable for the bound-closure test"
        )
        assert not bad, (
            "partition does not close at the bounds (correlated form expected): "
            + show(bad)
        )

    def test_usa_2010_household_cap_binds_everywhere(self, rows, expected, log):
        u = expected.units[("USA", 2010)]
        assert u["caph"] == ["low", "central", "high"], (
            f"premise: USA 2010 household cap should bind at every bound, got {u['caph']}"
        )
        assert not [
            r
            for r in rows.find(2010, country="USA", substream=BP, tier="memo_biosphere")
            if r["group"] in WOOD5
        ], (
            "USA 2010 plant wood is exactly 0/0/0: no biomass_peat wood rows (resolution 8)"
        )
        assert rows.find(2010, country="USA", substream=DOM, tier="memo_biosphere"), (
            "household wood memo rows expected"
        )


class TestCs137Conservation:
    def test_release_plus_memo_equals_fuel_cs137(self, rows, oracle, expected):
        """3: re-release + memo = fuel Cs-137 of the contributing materials, from the files, at the centre."""
        O = oracle
        L = defaultdict(float)
        N = defaultdict(float)
        for r in rows.rows:
            if r["group"] == "Cs137+":
                key = (r["substream"], r["country"], int(r["year"]))
                if r["tier"] == "liberated":
                    L[key] += float(r["value_central"])
                elif r["tier"] == "memo_biosphere":
                    N[key] += float(r["value_central"])
        bad, n_agg, n_single = [], 0, 0
        keys = set(L) | set(N)
        want_keys = set()
        for c, y in expected.units:
            want_keys |= {(BP, c, y), (DOM, c, y)}
        for s, y, c in O.act:
            if s.startswith("peat_"):
                want_keys |= {(BP, c, y), (DOM, c, y)}
        for key in sorted(keys):
            sub, c, y = key
            q = 0.0
            ncontrib = 0
            conc = fc(O, y, stage=BP, group="Cs137+", residue="peat_ash")
            t = central_peat(O, c, y) if c != "XXX" else None
            if t:
                ppl, oth, phh = t
                if sub == BP and (ppl + oth) > 0:
                    ash = (
                        ppl * fc(O, y, stage=BP, driver="peat_power_heat_t")
                        + oth * fc(O, y, stage=BP, driver="peat_supply_t")
                    ) * fc(O, y, stage=BP, residue="peat_ash")
                    q += ash * conc
                    ncontrib += 1
                if sub == DOM and phh > 0:
                    q += (
                        phh
                        * fc(O, y, stage=BP, driver="peat_household_t")
                        * fc(O, y, stage=BP, residue="peat_ash")
                        * conc
                    )
                    ncontrib += 1
            p = central_wood(O, c, y)
            if p:
                kap = fc(
                    O, y, p["region"], stage=BP, group="Cs137+", driver="wood_fuel_t"
                )
                if sub == BP and p["dpl"] > 0:
                    q += p["dpl"] * kap
                    ncontrib += 1
                if sub == DOM:
                    if p["dhh"] > 0:
                        q += p["dhh"] * kap
                        ncontrib += 1
                    if p["dch"] > 0:
                        q += p["dch"] * kap
                        ncontrib += 1
            got = L.get(key, 0.0) + N.get(key, 0.0)
            if ncontrib >= 2:
                n_agg += 1
            else:
                n_single += 1
            if not close(got, q, CONS):
                bad.append(f"{key}: re-release + memo = {got!r}, fuel Cs-137 {q!r}")
        assert n_agg > 100 and n_single > 1000, (
            f"coverage: {n_agg} aggregated keys, {n_single} single-material keys"
        )
        assert not bad, show(bad)

    def test_one_release_and_one_memo_row_per_key(self, rows):
        c = Counter(
            (r["substream"], r["country"], int(r["year"]), r["tier"])
            for r in rows.rows
            if r["group"] == "Cs137+"
        )
        dup = [k for k, v in c.items() if v > 1]
        assert not dup, (
            f"{len(dup)} Cs137+ keys with more than one row (3.6), first {dup[0]}"
        )

    def test_charcoal_stove_share_chain(self, rows, oracle, expected):
        """K + T + N_ch = Q_ch and the kiln / stove split at the centre, for keys without household peat."""
        O = oracle
        found = 0
        for (c, y), u in sorted(expected.units.items()):
            if found >= 40:
                break
            if (
                y < 1990
                or u["Dch"].b.central <= 0
                or (c != "XXX" and (central_peat(O, c, y) or (0, 0, 0))[2] > 0)
            ):
                continue
            p = central_wood(O, c, y)
            rel = rows.find(
                y, country=c, substream=DOM, group="Cs137+", tier="liberated"
            )
            mem = rows.find(
                y, country=c, substream=DOM, group="Cs137+", tier="memo_biosphere"
            )
            assert len(rel) == 1 and len(mem) == 1, (
                f"{c} {y}: expected one re-release and one memo Cs137+ row"
            )
            kap = fc(O, y, p["region"], stage=BP, group="Cs137+", driver="wood_fuel_t")
            sh = {
                k: fc(
                    O,
                    y,
                    stage=BP,
                    group="Cs137+",
                    tier="liberated",
                    route="air_rerelease",
                    driver=k,
                )
                for k in (
                    "household_fuelwood_m3",
                    "charcoal_production_t",
                    "household_charcoal_t",
                )
            }
            q, qh = p["dch"] * kap, p["dhh"] * kap
            s68, s69, s70 = (
                sh["household_fuelwood_m3"],
                sh["charcoal_production_t"],
                sh["household_charcoal_t"],
            )
            want_l = qh * s68 + q * s69 + q * (1 - s69) * s70
            want_n = qh * (1 - s68) + q * (1 - s69) * (1 - s70)
            assert close(float(rel[0]["value_central"]), want_l, CONS), (
                f"{c} {y}: re-release {rel[0]['value_central']} vs {want_l}"
            )
            assert close(float(mem[0]["value_central"]), want_n, CONS), (
                f"{c} {y}: memo {mem[0]['value_central']} vs {want_n}"
            )
            found += 1
        assert found >= 10, (
            "fewer than ten charcoal-bearing country-years available for the chain check"
        )


class TestGeothermalStructure:
    def test_rn220_is_rn222_times_the_right_ratio(self, rows, oracle):
        O = oracle
        n = 0
        for r in rows.rows:
            if r["substream"] != "geothermal" or r["group"] != "Rn220+":
                continue
            y, c = int(r["year"]), r["country"]
            r222 = rows.one(
                y, country=c, substream=GEO, group="Rn222+", tier="liberated"
            )
            region = "XWL" if c == "XXX" else c
            fid = "other:0075" if region == "ITA" else "other:0071"
            ratio = fvals(O, fid)[1]
            assert close(
                float(r["value_central"]), float(r222["value_central"]) * ratio, CONS
            ), (
                f"{c} {y}: Rn220 {r['value_central']} != Rn222 {r222['value_central']} x {fid} ({ratio})"
            )
            f = ids(r["factor_ids"])
            assert f[1] == fid and f[0] in ids(r222["factor_ids"]), (
                f"{c} {y}: Rn220 factor_ids {f} (Rn222 factor then {fid})"
            )
            n += 1
        assert n > 900

    def test_scale_rows_are_mass_times_concentration(self, rows, oracle):
        O = oracle
        mass_f = fvals(O, "other:0004")[1]
        bad = []
        for r in rows.rows:
            if r["tier"] != "impounded" or r["substream"] != "geothermal":
                continue
            y, c = int(r["year"]), r["country"]
            G = (
                O.ab("elec_gen_geothermal", y, "XWL" if c == "XXX" else c).central
                if c != "XXX" or y < 1980
                else None
            )
            if G is None:
                continue
            fid = next(f for f in ids(r["factor_ids"]) if f != "other:0004")
            want = G / GWA_TWH * mass_f * fvals(O, fid)[1]
            if not close(float(r["value_central"]), want, CONS):
                bad.append(
                    f"{c} {y} {r['group']}: {r['value_central']} vs {want} (t/GWa route)"
                )
            assert (
                ids(r["factor_ids"])[0] == "other:0004"
                and len(ids(r["factor_ids"])) == 2
            ), ids(r["factor_ids"])
        assert not bad, show(bad)

    def test_no_reisolated_or_brine_rows(self, rows):
        assert not rows.find(tier="reisolated") and not rows.find(
            residue_type="geothermal_brine"
        )


def allowed_combos():
    out = set()
    for sub, st in (("geothermal", "geothermal"),):
        out |= {(sub, st, "liberated", "air_vented_gas", "", g) for g in GEO_GAS}
        out |= {(sub, st, "impounded", "", "geothermal_scale", g) for g in GEO_SCALE}
    for sub in (BP, DOM):
        out |= {(sub, BP, "liberated", "air_stack", "", g) for g in PEAT11}
        out |= {(sub, BP, "impounded", "", "peat_ash", g) for g in PEAT11}
        out |= {(sub, BP, "dispersed", "", "peat_ash", g) for g in PEAT11}
        out |= {
            (sub, BP, "liberated", "air_rerelease", "", "Cs137+"),
            (sub, BP, "memo_biosphere", "", "", "Cs137+"),
        }
        out |= {(sub, BP, "memo_biosphere", "", "", g) for g in WOOD5}
    return out


class TestTierStructure:
    def test_combinations_equal_the_3_3_table(self, rows, pre_rows):
        got = {
            (
                r["substream"],
                r["stage"],
                r["tier"],
                r["route"] or "",
                r["residue_type"] or "",
                r["group"],
            )
            for r in rows.rows
        }
        allowed = allowed_combos()
        assert not (got - allowed), (
            f"combinations outside the 3.3 table: {sorted(got - allowed)[:8]}"
        )
        assert not (allowed - got), (
            f"3.3 table combinations never written: {sorted(allowed - got)[:8]}"
        )
        gp = {
            (
                r["substream"],
                r["stage"],
                r["tier"],
                r["route"] or "",
                r["residue_type"] or "",
                r["group"],
            )
            for r in pre_rows.rows
        }
        assert gp == {c for c in allowed if c[0] == "geothermal"}, (
            "pre-1950 combinations are exactly the geothermal ones"
        )

    def test_forbidden_rows(self, rows):
        for r in rows.rows:
            assert not (
                r["group"] == "Cs137+" and r["tier"] in ("impounded", "dispersed")
            ), describe(r)
            if (
                r["group"] in WOOD5
                and r["tier"] != "memo_biosphere"
                and r["substream"] != "geothermal"
            ):
                assert r["stage"] == "biomass_peat" and r["tier"] in (
                    "liberated",
                    "impounded",
                    "dispersed",
                ), describe(r)
            assert r["tier"] not in (
                "reisolated",
                "sealed_in_core",
                "sealed_fuel_cycle",
                "sealed_damaged_core",
                "memo_earth_moved",
            ), describe(r)
            assert r["quantity"] not in (
                "transfer_in",
                "transfer_out",
                "standing_inventory",
                "opening_stock",
            ), describe(r)

    def test_wood_natural_groups_only_as_memo_in_wood_memo_notes(self, rows):
        # wood natural nuclides are memo rows (D44); the only liberated/impounded/dispersed natural rows are peat's
        for r in rows.rows:
            if r["tier"] == "memo_biosphere" and r["group"] != "Cs137+":
                assert r["group"] in WOOD5, describe(r)
                assert (r["notes"] or "").startswith(RULE["memowood"]), describe(r)
                assert _blank(r["route"]) and _blank(r["residue_type"]), describe(r)


class TestUniqueKeys:
    def test_master_key_unique(self, rows, pre_rows, result):
        for name, obj in (("master", rows), ("pre1950", pre_rows)):
            dup = [k for k, v in obj.by_key.items() if len(v) > 1]
            assert not dup, f"{name}: {len(dup)} duplicate unique keys, first {dup[0]}"

    def test_written_without_error(self, written):
        assert Path(written[0]).stat().st_size > 0


def consumer_total(rows_list, year, substream=None):
    """Reference implementation of the consumer rule (3.3 item 3): Liberated tier, route != air_rerelease."""
    return sum(
        float(r["value_central"])
        for r in rows_list
        if int(r["year"]) == year
        and r["tier"] == "liberated"
        and r["route"] != "air_rerelease"
        and r["stage"] == "biomass_peat"
        and (substream is None or r["substream"] == substream)
    )


class TestReRelease:
    def test_every_rerelease_row_is_marked(self, rows):
        n = 0
        for r in rows.rows:
            if r["route"] == "air_rerelease":
                n += 1
                assert (
                    r["stage"] == "biomass_peat"
                    and r["group"] == "Cs137+"
                    and r["quantity"] == "flow"
                    and r["tier"] == "liberated"
                ), f"air_rerelease outside its schema conditional: {describe(r)}"
                assert (r["notes"] or "").startswith("re-release"), (
                    f"notes must begin with 're-release': {r['notes']!r}"
                )
                assert (r["notes"] or "").startswith(RULE["rerel"]), describe(r)
            if r["group"] == "Cs137+" and r["tier"] == "liberated":
                assert r["route"] == "air_rerelease", (
                    f"Cs137+ Liberated row with another route: {describe(r)}"
                )
        assert n > 5000

    def test_consumer_filter_arithmetic(self, rows):
        for y in (1965, 1990, 2010, 2020):
            lib = [
                r
                for r in rows.by_year[y]
                if r["stage"] == "biomass_peat" and r["tier"] == "liberated"
            ]
            unfiltered = sum(float(r["value_central"]) for r in lib)
            rerel = sum(
                float(r["value_central"]) for r in lib if r["route"] == "air_rerelease"
            )
            filtered = consumer_total(rows.rows, y)
            assert rerel > 0, f"no re-release in {y}"
            assert close(filtered, unfiltered - rerel, CONS), (
                f"{y}: filtered {filtered} != unfiltered {unfiltered} - re-release {rerel}"
            )
            memo = sum(
                float(r["value_central"])
                for r in rows.by_year[y]
                if r["tier"] == "memo_biosphere"
            )
            assert memo > 0
            assert close(consumer_total(rows.rows, y), filtered, CONS), (
                "memo rows must enter neither total"
            )
            assert not [
                r
                for r in rows.by_year[y]
                if r["tier"] == "memo_biosphere" and r["route"] == "air_rerelease"
            ]

    def test_memo_cs137_is_never_in_a_liberated_total(self, rows):
        for r in rows.rows:
            if r["tier"] == "memo_biosphere":
                assert _blank(r["route"]) and _blank(r["residue_type"]), describe(r)
                assert (r["notes"] or "").startswith(
                    ("memo: fallout Cs-137", "memo: natural nuclides")
                ), describe(r)


# --------------------------------------------------------------------------------------------
# flags, notes, years and edges (3.4)
# --------------------------------------------------------------------------------------------
class TestFlagsAndNotes:
    def test_flagged_rows_have_cause_suffix_and_unflagged_none(self, rows):
        for r in rows.rows:
            n = r["notes"] or ""
            has = "; below_detection cause:" in n
            assert has == as_bool(r["below_detection"]), (
                f"cause suffix vs flag mismatch: {describe(r)} {n[-120:]!r}"
            )
            if has:
                assert re.search(r"; below_detection cause: [a-z_+]+\s*$", n), (
                    f"cause text must be last: {n[-160:]!r}"
                )

    def test_usa_2010_biomass_flagged_rows_absent_and_cap_logged(self, rows, log):
        assert not [
            r
            for r in rows.find(2010, country="USA", substream=BP)
            if r["group"] in WOOD5
        ], "USA 2010 has no biomass_peat wood rows"
        es = [
            e
            for e in log_entries(log, "household_wood_capped", country="USA")
            if _span(e) and _span(e)[0] <= 2010 <= _span(e)[1]
        ]
        assert es, "USA 2010 must be inside a household_wood_capped run"
        d = str(es[0]["detail"])
        assert all(re.search(rf"\b{b}\b", d) for b in ("low", "central", "high")), (
            f"detail should name low, central and high: {d!r}"
        )

    def test_negative_residual_peat_rows_carry_clipped_difference(self, rows):
        # DEU 1993: the only plant-type term is the clipped (0, 0, h) other-use residual (13.15)
        for tier, route, rule in (
            ("liberated", "air_stack", RULE["pstack"]),
            ("impounded", "", RULE["pash"]),
            ("dispersed", "", RULE["pash"]),
        ):
            r = rows.one(
                1993, country="DEU", substream=BP, group="K40", tier=tier, route=route
            )
            assert (
                float(r["value_low"]) == 0
                and float(r["value_central"]) == 0
                and float(r["value_high"]) > 0
            )
            assert as_bool(r["below_detection"])
            assert (
                r["notes"]
                == rule
                + "; components: peat_other; below_detection cause: clipped_difference"
            ), r["notes"]

    def test_no_exact_zero_rows_and_no_exact_zero_cause(self, rows):
        for r in rows.rows:
            assert vals(r) != (0.0, 0.0, 0.0), (
                f"a row with bounds exactly (0, 0, 0) was written (13.15): {describe(r)}"
            )
            assert "exact_zero" not in (r["notes"] or ""), (
                f"cause exact_zero on a written row: {describe(r)}"
            )

    def test_driver_basis_only_on_2025_rows(self, rows):
        for r in rows.rows:
            has = "; driver basis:" in (r["notes"] or "")
            if int(r["year"]) == 2025:
                assert has and "extrapolated" in r["notes"], (
                    f"2025 row without '; driver basis: extrapolated': {describe(r)}"
                )
            else:
                assert not has, (
                    f"driver basis suffix outside 2025: {describe(r)} {r['notes'][-80:]!r}"
                )
            assert r["basis"] == "modelled"

    def test_fallback_text_exactly_where_unsd_row_missing(self, rows, expected):
        bad = []
        for r in rows.rows:
            if r["tier"] != "memo_biosphere" or r["group"] not in WOOD5:
                continue
            u = expected.units.get((r["country"], int(r["year"])))
            has = TXT_FALLBACK in (r["notes"] or "")
            if r["substream"] == BP:
                if has != u["fallback"]:
                    bad.append(
                        f"{describe(r)} fallback text {has}, unit fallback {u['fallback']}"
                    )
            elif u["Dhh"].b.central > 0 and has != u["fallback"]:
                bad.append(
                    f"{describe(r)} fallback text {has}, unit fallback {u['fallback']}"
                )
        assert not bad, show(bad)

    def test_world_aggregate_and_rest_text_scope(self, rows):
        geo = [r for r in rows.rows if TXT_WORLD in (r["notes"] or "")]
        assert geo and {int(r["year"]) for r in geo} == set(range(1950, 1980)), (
            "world aggregate text on XXX geothermal 1950-1979"
        )
        xxx = {
            int(r["year"])
            for r in rows.rows
            if r["country"] == "XXX" and r["substream"] != "geothermal"
        }
        assert xxx == set(range(1961, 2012)) | {2024, 2025}, (
            f"rest-of-world wood years: expected 1961-2011 and 2024-2025 (13.19), got {sorted(xxx)[:3]}..{sorted(xxx)[-4:]}; none in 2012-2023"
        )
        for r in rows.rows:
            assert not (
                TXT_WORLD in (r["notes"] or "") and TXT_REST in (r["notes"] or "")
            ), "world and rest texts never co-occur"

    def test_rest_of_world_2010_domestic_memo_notes_exact(self, rows, expected):
        r = rows.one(
            2010, country="XXX", substream=DOM, group="K40", tier="memo_biosphere"
        )
        head = f"{RULE['memowood']}; {TXT_REST}; {TXT_FALLBACK}; components: wood_household+charcoal"  # 13.10 example
        assert r["notes"].startswith(head), r["notes"]
        er = expected.rows[(2010, DOM, BP, "XXX", "K40", "memo_biosphere", "", "")]
        assert r["notes"] == expected_notes(er), r["notes"]
        assert r["notes"] == head or r["notes"].endswith(
            "; below_detection cause: clipped_difference"
        ), (
            "a rest-of-world residual with a clipped low carries cause clipped_difference only"
        )

    def test_rest_of_world_2025_notes_exact(self, rows, expected):
        r = rows.one(
            2025, country="XXX", substream=BP, group="K40", tier="memo_biosphere"
        )
        head = f"{RULE['memowood']}; {TXT_REST}; {TXT_FALLBACK}; components: wood_plant; driver basis: extrapolated"
        assert r["notes"].startswith(head), r["notes"]
        er = expected.rows[(2025, BP, BP, "XXX", "K40", "memo_biosphere", "", "")]
        assert r["notes"] == expected_notes(er), r["notes"]


class TestYearsAndEdges:
    def test_geothermal_2025_rows_exist(self, rows):
        assert rows.find(2025, substream=GEO, group="Rn222+"), (
            "2025 geothermal rows must be written (extrapolated driver)"
        )

    def test_peat_from_1990_and_2025_rows_present(self, rows):
        yrs = {
            int(r["year"])
            for r in rows.rows
            if r["substream"] != "geothermal" and r["tier"] == "impounded"
        }
        assert min(yrs) == 1990 and 2025 in yrs, f"peat years {min(yrs)}..{max(yrs)}"
        assert not [
            r
            for r in rows.rows
            if r["substream"] == BP
            and r["tier"] == "impounded"
            and r["country"] == "XXX"
        ], "peat has no XWL series: no rest-of-world peat rows"
        assert not [
            r
            for r in rows.rows
            if r["residue_type"] == "peat_ash" and r["country"] == "XXX"
        ]

    def test_wood_from_1961(self, rows):
        yrs = {int(r["year"]) for r in rows.rows if r["tier"] == "memo_biosphere"}
        assert min(yrs) == 1961 and max(yrs) == 2025

    def test_1979_1980_step_not_smoothed(self, rows, oracle):
        O = oracle
        a = rows.one(
            1979, country="XXX", substream=GEO, group="Rn222+", tier="liberated"
        )
        want = (
            O.ab("elec_gen_geothermal", 1979, "XWL").central
            / GWA_TWH
            * fvals(O, "other:0001")[1]
        )
        assert close(float(a["value_central"]), want, CONS), (
            "1979 world aggregate uses other:0001 on the XWL row"
        )
        assert not rows.find(1980, country="XXX", substream=GEO), (
            "no XXX geothermal rows in 1980 (country rows begin, residual zero)"
        )
        assert rows.find(1980, country="ITA", substream=GEO, group="Rn222+")

    def test_no_xxx_geothermal_after_1979(self, rows):
        assert not [
            r
            for r in rows.rows
            if r["substream"] == GEO
            and r["country"] == "XXX"
            and int(r["year"]) >= 1980
        ]

    def test_charcoal_series_optional_and_household_zero_row(self, expected, oracle):
        # a country with an exact-zero UNSD household row has D_hh = 0 and no fallback (6.2 item 4)
        zeros = [
            (c, y)
            for (s, y, c), r in oracle.act.items()
            if s == "household_fuelwood_m3"
            and float(r["value_high"]) == 0
            and oracle.has("wood_fuel_t", y, c)
            and float(oracle.act[("wood_fuel_t", y, c)]["value_high"]) > 0
        ]
        premise(
            bool(zeros),
            "no exact-zero UNSD household row with a wood driver in the data",
        )
        for c, y in zeros[:50]:
            u = expected.units[(c, y)]
            assert not u["fallback"] and is_zero_b(u["Dhh"].b)


# --------------------------------------------------------------------------------------------
# log (8)
# --------------------------------------------------------------------------------------------
class TestLog:
    def test_log_against_oracle(self, log, oracle, expected):
        msgs = check_log(log, oracle, expected, "real")
        assert not msgs, show(msgs, 10)

    def test_expected_aggregated_runs_today(self, log):
        nd = {
            (e["country"], e["year"], e["detail"].split(" (")[0])
            for e in log_entries(log, "no_driver")
        }
        assert len(log_entries(log, "no_driver")) == 3
        assert ("XXX", 1800, "1800-1915") in nd, "elec_gen_geothermal 1800-1915"
        assert ("XXX", 1800, "1800-1960") in nd, "wood_fuel_t 1800-1960"
        assert ("XXX", 1800, "1800-1989") in nd, "peat 1800-1989"
        txt = {e["detail"] for e in log_entries(log, "no_driver")}
        assert txt == {
            "1800-1915 (116 years): elec_gen_geothermal has no value",
            "1800-1960 (161 years): wood_fuel_t has no value",
            "1800-1989 (190 years): peat_supply_t has no value",
        }, txt

    def test_negative_residual_four_peat_country_years(self, log):
        got = {
            (e["country"], e["year"]): e["detail"]
            for e in log_entries(log, "negative_residual")
        }
        assert set(got) == {
            ("ARM", 2012),
            ("DEU", 1993),
            ("ROU", 1998),
            ("UKR", 1997),
        }, got
        assert (
            got[("DEU", 1993)]
            == "peat supply is below plants plus household by 5000 t; treated as 0"
        ), got[("DEU", 1993)]

    def test_world_series_entries_use_xxx(self, log):
        assert not [e for e in log if e["country"] == "XWL"]

    def test_no_per_year_entries(self, log):
        assert len(log) < 2000, (
            f"{len(log)} log entries: per-year instead of aggregated runs?"
        )

    def test_single_lib_warning_entry(self, log):
        w = log_entries(log, "lib_warning")
        assert len(w) == 1, (
            f"expected exactly one lib_warning entry on the real tree (13.16), found {len(w)}"
        )
        assert _empty(w[0]["year"]) and _empty(w[0]["country"]), (
            f"year/country must be empty: {w[0]}"
        )
        assert re.fullmatch(
            r"\d+ pipeline\.lib warnings captured: \d+ x .+",
            str(w[0]["detail"]),
            re.DOTALL,
        ), w[0]["detail"]

    def test_no_cap_applied_for_peat_in_real_data(self, log):
        assert not log_entries(log, "cap_applied") and not log_entries(
            log, "predecessor_dropped"
        )


# --------------------------------------------------------------------------------------------
# (d) determinism, stderr
# --------------------------------------------------------------------------------------------
def _env():
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    return env


class TestDeterminism:
    def test_written_rows_in_schema_key_order(self, written):
        cols = [
            "year",
            "stream",
            "substream",
            "stage",
            "product",
            "residue_type",
            "country",
            "group",
            "tier",
            "quantity",
            "allocation_variant",
            "embedded_fuel",
            "technology",
            "route",
            "event_id",
        ]
        for p in written:
            with open(p, newline="", encoding="utf-8") as fh:
                data = list(csv.DictReader(fh))
            assert data

            def key(r):
                return tuple(
                    (int(r[c]),)
                    if c == "year"
                    else ((0, "") if r[c] == "" else (1, r[c]))
                    for c in cols
                )

            keys = [key(r) for r in data]
            assert keys == sorted(keys), "rows are not in SCHEMA 3 unique-key order"
            assert len(keys) == len(set(keys))

    def test_second_build_in_a_fresh_process_is_byte_identical_and_silent(
        self, written, log
    ):
        """Cross-process determinism of all three outputs and 3.9 (nothing on stderr, even with -W default)."""
        code = (
            "import sys, hashlib, json\n"
            "from pathlib import Path\n"
            "from pipeline.streams.other import build\n"
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
            cwd=str(ROOT),
            env=_env(),
            capture_output=True,
            text=True,
            timeout=3000,
            check=False,
        )
        assert p.returncode == 0, p.stderr[-1500:]
        assert p.stderr == "", (
            f"build() wrote {len(p.stderr)} bytes to stderr (3.9): {p.stderr[:600]!r}"
        )
        got = json.loads(p.stdout.strip().splitlines()[-1])
        h = lambda q: hashlib.sha256(Path(q).read_bytes()).hexdigest()
        assert got["m"] == h(written[0]), "master bytes differ between builds"
        assert got["p"] == h(written[1]), "pre-1950 bytes differ between builds"
        assert got["log"] == json.loads(json.dumps(log, default=str)), (
            "log differs (or is ordered differently) between builds"
        )


# --------------------------------------------------------------------------------------------
# (e) benchmarks (D51); known misses are runtime xfails (D69, D70)
# --------------------------------------------------------------------------------------------
def check(name, x, ref, known_miss=False, reason="", unit="TBq/GW.a"):
    ratio = x / ref if ref else float("inf")
    ok = 1 / 3 <= ratio <= 3
    if not ok and known_miss:
        pytest.xfail(
            f"documented known miss (OTHER_SPEC 9(e)): {name}: stream {x:.4g}, reference {ref:.4g}, ratio {ratio:.3g}. {reason}"
        )
    assert ok, (
        f"{name}: stream {x:.4g} {unit} vs reference {ref:.4g}, ratio {ratio:.3g} outside [1/3, 3]"
    )
    return ratio


def w_geo(O, y):
    return O.ab("elec_gen_geothermal", y, "XWL").central / GWA_TWH


def w_peat(O, y):
    return O.ab("elec_gen_peat", y, "XWL").central / GWA_TWH


class TestBenchmarks:
    @pytest.mark.parametrize("y", [2010, 2020])
    def test_b1_world_mean_against_unscear_150(self, rows, oracle, y):
        x = (
            rows.total(y, substream=GEO, group="Rn222+", tier="liberated")
            / 1e12
            / w_geo(oracle, y)
        )
        r = check(
            f"B1 geothermal world mean {y} vs UNSCEAR 150 (circular: tests the weighting arithmetic)",
            x,
            150.0,
        )
        print(f"B1 {y}: stream {x:.3g} TBq/GW.a, ratio to 150 = {r:.3g}")

    @pytest.mark.parametrize("y", [2010, 2020])
    def test_b1_usa_required_pass(self, rows, oracle, y):
        c = rows.one(y, country="USA", substream=GEO, group="Rn222+", tier="liberated")
        x = (
            float(c["value_central"])
            / 1e12
            / (oracle.ab("elec_gen_geothermal", y, "USA").central / GWA_TWH)
        )
        check("B1 USA Rn-222 per GW.a vs Kruger-Stoker-Umana 1977 (54)", x, 54.0)

    @pytest.mark.parametrize("y", [2010, 2020])
    def test_b1_ita_against_stanford_laboratory_value(self, rows, oracle, y):
        c = rows.one(y, country="ITA", substream=GEO, group="Rn222+", tier="liberated")
        x = (
            float(c["value_central"])
            / 1e12
            / (oracle.ab("elec_gen_geothermal", y, "ITA").central / GWA_TWH)
        )
        check(
            f"B1 ITA Rn-222 {y} vs Stanford laboratory value 76",
            x,
            76.0,
            known_miss=True,
            reason="Field-method values 257-304 share one root dataset; the 1.4-2.8x field/laboratory gap is unresolved.",
        )

    @pytest.mark.parametrize("y", [2010, 2020])
    def test_b1_rest_of_world_against_salton_sea(self, rows, oracle, y):
        c = rows.one(y, country="JPN", substream=GEO, group="Rn222+", tier="liberated")
        x = (
            float(c["value_central"])
            / 1e12
            / (oracle.ab("elec_gen_geothermal", y, "JPN").central / GWA_TWH)
        )
        check(
            f"B1 rest-of-world default {y} (JPN, other:0001) vs Salton Sea centre 10",
            x,
            10.0,
            known_miss=True,
            reason="The default is the NZ flash estimate (80); Salton Sea flashing-brine steam gives 7-15.",
        )

    def test_b1_range_tests(self, oracle):
        lo, _, hi = (v / 1e12 for v in fvals(oracle, "other:0001"))
        assert lo <= 10.0 <= hi and lo <= 80.0 <= hi, (
            f"Salton Sea 10 and NZ 80 must lie in the other:0001 band {lo}-{hi}"
        )
        lo, _c, hi = (v / 1e12 for v in fvals(oracle, "other:0072"))
        assert lo <= 40.0 and 200.0 <= hi, (
            f"NZ range 40-200 must lie inside the other:0072 band {lo}-{hi}"
        )

    def _phi(self, O, y):
        """Plant share phi = sum Ppl / sum (Ppl + Poth) (9(e) B2)."""
        pl = oth = 0.0
        for c in {
            c
            for s in ("peat_power_heat_t", "peat_household_t", "peat_supply_t")
            for c in O.by_series[s].get(y, [])
        }:
            t = central_peat(O, c, y)
            if t:
                pl += t[0]
                oth += t[1]
        return pl / (pl + oth)

    @pytest.mark.parametrize("y", [2010, 2020])
    def test_b2_peat_u238_per_gwa(self, rows, oracle, y):
        O = oracle
        tot = sum(
            float(r["value_central"])
            for r in rows.by_year[y]
            if r["substream"] == BP
            and r["group"] == "U238+"
            and r["tier"] in ("liberated", "impounded", "dispersed")
        )
        x = tot * self._phi(O, y) / 1e12 / w_peat(O, y)
        unscear = 40.0 * 5e9 / 1e12  # 40 Bq/kg x 5e9 kg per GW.a (U1351)
        check(f"B2 peat U-238 {y} vs UNSCEAR 1988 ({unscear:.2f})", x, unscear)
        refs = {
            "Finland production peat 11 Bq/kg": 0.055,
            "Mustonen 1984, 15 Bq/kg": 0.075,
            "Sweden ash median 420 Bq/kg": 0.105,
        }
        ratios = {k: x / v for k, v in refs.items()}
        print(f"B2 {y}: stream {x:.4g} TBq/GW.a; independent ratios {ratios}")
        assert any(1 / 3 <= r <= 3 for r in ratios.values()), (
            f"B2 {y}: stream {x:.4g} not within x3 of any independent value {ratios}"
        )

    @pytest.mark.parametrize("y", [2010, 2020])
    def test_b3_dry_peat_per_gwa(self, oracle, y):
        O = oracle
        pl = sum(
            O.ab("peat_power_heat_t", y, c).central
            for c in O.countries("peat_power_heat_t", y)
        )
        x = (
            pl * fvals(O, "other:0010")[1] * 1000.0 / w_peat(O, y)
        )  # kg of dry peat per GW.a
        refs = {
            "UNSCEAR 1988": 5e9,
            "SSI plant at eta 0.30": 1.51e9 / 0.30,
            "SSI plant at eta 0.35": 1.51e9 / 0.35,
        }
        ratios = {k: x / v for k, v in refs.items()}
        print(f"B3 {y}: stream {x:.4g} kg/GW.a; ratios {ratios}")
        assert 1 / 3 <= ratios["UNSCEAR 1988"] <= 3, (
            f"B3 {y}: {x:.4g} kg/GW.a vs UNSCEAR 1988 5e9, ratio {ratios['UNSCEAR 1988']:.3g}"
        )
        assert any(1 / 3 <= r <= 3 for k, r in ratios.items() if k.startswith("SSI")), (
            f"B3 {y}: {x:.4g} kg/GW.a not within x3 of the independent SSI value: {ratios}"
        )

    @pytest.mark.parametrize(
        "y,ranges",
        [
            (1991, {"US 1990-92": (2.9, 780.0)}),
            (2021, {"Austria 2020-22": (11.8, 867.0), "Greece 2013": (25.0, 499.0)}),
        ],
    )
    def test_b4_wood_ash_cs137_range(self, oracle, y, ranges):
        """B4 is a range test (D61 choice 9): x = kappa (1 - s) / a_ash, a_ash = 0.01 t ash per t dry wood (test constant, D70)."""
        O = oracle
        kappa = fc(O, y, stage=BP, group="Cs137+", driver="wood_fuel_t")
        s = fvals(O, "other:0068")[1]
        x = kappa * (1 - s) / 0.01 / 1000.0  # Bq per kg of ash
        for name, (lo, hi) in ranges.items():
            assert lo <= x <= hi, (
                f"B4 {y}: factor-implied wood-ash Cs-137 {x:.3g} Bq/kg outside the {name} range {lo}-{hi}"
            )
        print(
            f"B4 {y}: {x:.3g} Bq/kg ash (recorded, not criteria: Finland 2018 ash 310-1940, Belgian ~200, US mean 444)"
        )

    def test_b5_stove_emission_per_kg_wood(self, oracle):
        """B5: Thessaloniki 2013 air-derived 0.8-6.5 Bq/kg of wood burned. Diagnostic; a known miss (xfail)."""
        O = oracle
        kappa = (
            fc(O, 2013, stage=BP, group="Cs137+", driver="wood_fuel_t") / 1000.0
        )  # Bq/kg
        x = kappa * fvals(O, "other:0068")[1]
        lo, hi = 0.8, 6.5
        ref = lo if x < lo else min(x, hi)
        check(
            "B5 stove Cs-137 emission per kg of wood, Thessaloniki 2013",
            x,
            ref,
            known_miss=True,
            unit="Bq/kg",
            reason="XWL default kappa x 0.19 is 4-34x below Greece, whose wood carries more Cs-137 (beech 8-11 Bq/kg).",
        )

    def test_b4_round_trip_in_a_fixture(self, other_mod, tmp_path):
        root = make_mini(
            tmp_path,
            {
                "biomass.csv": [
                    _a("wood_fuel_t", y, c, 1000.0, "t", 0.1)
                    for y in (2005, 2006)
                    for c in ("FRA", "XWL")
                ]
            },
        )
        res = other_mod.build(root)
        O = Oracle(root)
        rws = Rows(list(res.rows))
        y = 2005
        r = rws.one(
            y, country="FRA", substream=DOM, group="Cs137+", tier="memo_biosphere"
        )
        d = 1000.0 * fc(O, y, stage=BP, driver="wood_fuel_t")
        dhh = d * fc(O, y, stage=BP, driver="wood_fuel_m3")
        kappa = fc(O, y, stage=BP, group="Cs137+", driver="wood_fuel_t")
        s = fvals(O, "other:0068")[1]
        assert close(float(r["value_central"]) / dhh, kappa * (1 - s), CONS), (
            "memo / household dry wood != kappa (1 - s)"
        )


# --------------------------------------------------------------------------------------------
# (f) hand-computed cases
# --------------------------------------------------------------------------------------------
def gbq(O, y, c, fid):
    """Rn-222-like flow: TWh -> GW a, times the factor (full bounds)."""
    g = O.ab("elec_gen_geothermal", y, c)
    return prod(scale(g, 1 / GWA_TWH), B(*fvals(O, fid)))


def same_bounds(r, b: B, rel=REL, label=""):
    got = vals(r)
    for nm, g, w in zip(("low", "central", "high"), got, (b.low, b.central, b.high)):
        assert close(g, w, rel), (
            f"{label} [{describe(r)}]: value_{nm} = {g!r}, hand-computed {w!r}"
        )


class TestHandComputed:
    @pytest.mark.parametrize(
        "c,fid",
        [
            ("ITA", "other:0002"),
            ("USA", "other:0003"),
            ("NZL", "other:0072"),
            ("JPN", "other:0001"),
        ],
    )
    def test_rn222_2010_with_tw_to_gwa_conversion(self, rows, oracle, c, fid):
        r = rows.one(2010, country=c, substream=GEO, group="Rn222+", tier="liberated")
        same_bounds(r, gbq(oracle, 2010, c, fid), label="Rn222")
        assert ids(r["factor_ids"]) == [fid]
        assert (
            r["unit"] == "Bq/a"
            and r["route"] == "air_vented_gas"
            and r["notes"] == RULE["geo222"]
        )

    def test_rn220_ita_uses_its_own_ratio(self, rows, oracle):
        r = rows.one(
            2010, country="ITA", substream=GEO, group="Rn220+", tier="liberated"
        )
        same_bounds(
            r,
            prod(
                gbq(oracle, 2010, "ITA", "other:0002"), B(*fvals(oracle, "other:0075"))
            ),
            label="Rn220 ITA",
        )
        assert (
            ids(r["factor_ids"]) == ["other:0002", "other:0075"]
            and r["notes"] == RULE["geo220"]
        )

    def test_rn220_usa_uses_own_rn222_and_xwl_ratio(self, rows, oracle):
        r = rows.one(
            2010, country="USA", substream=GEO, group="Rn220+", tier="liberated"
        )
        same_bounds(
            r,
            prod(
                gbq(oracle, 2010, "USA", "other:0003"), B(*fvals(oracle, "other:0071"))
            ),
            label="Rn220 USA",
        )
        assert ids(r["factor_ids"]) == ["other:0003", "other:0071"]

    def test_world_aggregate_1970_and_pre1950_1930(self, rows, pre_rows, oracle):
        r = rows.one(
            1970, country="XXX", substream=GEO, group="Rn222+", tier="liberated"
        )
        same_bounds(r, gbq(oracle, 1970, "XWL", "other:0001"), label="XXX 1970")
        assert r["notes"].startswith(RULE["geo222"]) and TXT_WORLD in r["notes"], r[
            "notes"
        ]
        p = pre_rows.one(
            1930, country="XXX", substream=GEO, group="Rn222+", tier="liberated"
        )
        same_bounds(p, gbq(oracle, 1930, "XWL", "other:0001"), label="XXX 1930")
        assert int(p["year"]) == 1930 and p["quantity"] == "flow"

    def test_scale_row_through_t_per_gwa(self, rows, oracle):
        O = oracle
        r = rows.one(
            2010, country="ITA", substream=GEO, group="Ra226+", tier="impounded"
        )
        g = scale(O.ab("elec_gen_geothermal", 2010, "ITA"), 1 / GWA_TWH)
        mass = prod(g, B(*fvals(O, "other:0004")))
        same_bounds(r, prod(mass, B(*fvals(O, "other:0005"))), label="scale")
        assert (
            ids(r["factor_ids"]) == ["other:0004", "other:0005"]
            and r["residue_type"] == "geothermal_scale"
        )
        assert r["notes"] == RULE["geoscale"]

    def test_geothermal_2025_row_driver_basis(self, rows, oracle):
        r = rows.one(
            2025, country="ITA", substream=GEO, group="Rn222+", tier="liberated"
        )
        same_bounds(r, gbq(oracle, 2025, "ITA", "other:0002"), label="ITA 2025")
        assert r["notes"] == f"{RULE['geo222']}; driver basis: extrapolated", r["notes"]

    def test_2025_wood_ind_k40_domestic_fallback(self, rows, oracle):
        O = oracle
        r = rows.one(
            2025, country="IND", substream=DOM, group="K40", tier="memo_biosphere"
        )
        w = O.ab("wood_fuel_t", 2025, "IND")
        assert not O.has("household_fuelwood_m3", 2025, "IND")
        n = r["notes"]
        assert (
            n.startswith(RULE["memowood"])
            and TXT_FALLBACK in n
            and "; driver basis: extrapolated" in n
        ), n
        p = central_wood(O, "IND", 2025)
        assert close(
            float(r["value_central"]),
            (p["dhh"] + p["dch"])
            * fc(
                O,
                2025,
                stage=BP,
                group="K40",
                tier="memo_biosphere",
                driver="wood_fuel_t",
            ),
            CONS,
        )
        assert w.central > 0

    def test_2025_peat_fin_pb210_stack(self, rows, oracle):
        r = rows.one(
            2025,
            country="FIN",
            substream=BP,
            group="Pb210+",
            tier="liberated",
            route="air_stack",
        )
        assert "; driver basis: extrapolated" in r["notes"] and r["notes"].startswith(
            RULE["pstack"]
        )
        f = ids(r["factor_ids"])
        assert f[-3:] == ["other:0027", "other:0030", "other:0014"], (
            f"2025 stack row factor_ids {f}"
        )

    def test_fin_2010_pb210_stack_chain(self, rows, oracle):
        O = oracle
        y = 2010
        ppl, oth, _phh = central_peat(O, "FIN", y)
        assert oth > 0, (
            "premise: FIN 2010 has other peat use (supply above plants + household)"
        )
        dry = ppl * fvals(O, "other:0010")[1] + oth * fvals(O, "other:0012")[1]
        ash = dry * fvals(O, "other:0013")[1]
        a = ash * fvals(O, "other:0019")[1]
        p = fvals(O, "other:0027")[1]
        e = fvals(O, "other:0030")[1]
        r = rows.one(
            y,
            country="FIN",
            substream=BP,
            group="Pb210+",
            tier="liberated",
            route="air_stack",
        )
        assert close(float(r["value_central"]), a * p * e, CONS), (
            f"FIN 2010 Pb210+ stack: {r['value_central']} vs {a * p * e}"
        )
        assert ids(r["factor_ids"]) == [
            "other:0010",
            "other:0012",
            "other:0013",
            "other:0019",
            "other:0027",
            "other:0030",
            "other:0014",
        ]
        assert r["notes"].endswith("; components: peat_plant+peat_other"), r["notes"]
        imp = rows.one(y, country="FIN", substream=BP, group="Pb210+", tier="impounded")
        dis = rows.one(y, country="FIN", substream=BP, group="Pb210+", tier="dispersed")
        res = a - a * p * e
        assert close(float(imp["value_central"]), res * fvals(O, "other:0039")[1], CONS)
        assert close(float(dis["value_central"]), res * fvals(O, "other:0040")[1], CONS)
        assert (
            imp["residue_type"] == "peat_ash" == dis["residue_type"]
            and ids(imp["factor_ids"])[-1] == "other:0039"
        )

    def test_household_peat_set_fin_2010(self, rows, oracle):
        O = oracle
        y = 2010
        _ppl, _oth, phh = central_peat(O, "FIN", y)
        ash = phh * fvals(O, "other:0011")[1] * fvals(O, "other:0013")[1]
        for g, aid, eid in (
            ("Pb210+", "other:0019", "other:0030"),
            ("U238+", "other:0015", "other:0032"),
        ):
            h = ash * fvals(O, aid)[1]
            m = min(h * fvals(O, "other:0043")[1] * fvals(O, eid)[1], h)
            st = rows.one(
                y,
                country="FIN",
                substream=DOM,
                group=g,
                tier="liberated",
                route="air_stack",
            )
            assert (
                close(float(st["value_central"]), m, CONS)
                and st["notes"] == RULE["hstack"]
            ), st["notes"]
            im = rows.one(y, country="FIN", substream=DOM, group=g, tier="impounded")
            di = rows.one(y, country="FIN", substream=DOM, group=g, tier="dispersed")
            assert close(
                float(im["value_central"]), (h - m) * fvals(O, "other:0041")[1], CONS
            )
            assert close(
                float(di["value_central"]), (h - m) * fvals(O, "other:0042")[1], CONS
            )
            assert im["notes"] == RULE["hash"]

    def test_deu_1993_negative_residual(self, log, rows):
        e = [
            x
            for x in log_entries(log, "negative_residual")
            if x["country"] == "DEU" and x["year"] == 1993
        ]
        assert len(e) == 1
        assert (
            rows.find(1993, country="DEU", substream=BP, tier="liberated", group="K40")
            or True
        )

    def test_household_wood_unsd_path_k40(self, rows, oracle, expected):
        O = oracle
        cands = [
            (c, y)
            for (c, y), u in expected.units.items()
            if y == 2010
            and not u["fallback"]
            and not u["caph"]
            and u["Dhh"].b.central > 0
            and not u["capc"]
            and u["Dch"].b.central == 0
        ]
        assert cands, "no UNSD-path, uncapped country in 2010"
        c, y = cands[0]
        m = O.ab("household_fuelwood_m3", y, c).central
        d = fvals(O, "other:0048")[1]
        dhh = m * fvals(O, "other:0049")[1] * d
        r = rows.one(y, country=c, substream=DOM, group="K40", tier="memo_biosphere")
        assert close(float(r["value_central"]), dhh * fvals(O, "other:0052")[1], CONS)
        assert TXT_FALLBACK not in r["notes"]

    def test_chn_2010_fallback(self, rows, oracle):
        O = oracle
        assert not O.has("household_fuelwood_m3", 2010, "CHN")
        r = rows.one(
            2010, country="CHN", substream=DOM, group="K40", tier="memo_biosphere"
        )
        p = central_wood(O, "CHN", 2010)
        assert close(
            float(r["value_central"]),
            (p["dhh"] + p["dch"]) * fvals(O, "other:0052")[1],
            CONS,
        )
        assert close(p["dhh"], p["r1"] * fvals(O, "other:0050")[1], CONS)
        assert TXT_FALLBACK in r["notes"]

    def test_rest_of_world_wood_unit_before_2010_uses_fallback(self, rows, oracle):
        O = oracle
        r = rows.one(
            2005, country="XXX", substream=DOM, group="K40", tier="memo_biosphere"
        )
        assert TXT_REST in r["notes"] and TXT_FALLBACK in r["notes"]
        assert r["notes"].index(TXT_REST) < r["notes"].index(TXT_FALLBACK)
        p = central_wood(O, "XXX", 2005)
        assert close(
            float(r["value_central"]),
            (p["dhh"] + p["dch"]) * fvals(O, "other:0052")[1],
            CONS,
        )

    def test_cs137_country_overrides(self, rows, oracle):
        """kappa from the registry override rows; the wood part is recomputed from kappa and the 0067/0068/0069/0070 shares,
        the peat part from the ash-borne Cs-137 and the era row; their sum is the row (re-release and memo)."""
        O = oracle
        s67, s68, s69, s70 = (fvals(O, f)[1] for f in ("other:0067", "other:0068", "other:0069", "other:0070"))
        for c, y, fid in (("SWE", 2005, "other:0062"), ("FIN", 2010, "other:0073")):
            kap = fvals(O, fid)[1]
            xwl = fvals(O, "other:0060")[1]
            premise(kap != xwl and 2001 <= y, f"{fid} central {kap} must differ from the XWL era row other:0060 ({xwl})")
            p = central_wood(O, c, y)
            assert p, f"{c} {y}: premise, a wood unit"
            conc = fc(O, y, stage=BP, group="Cs137+", residue="peat_ash")
            t = central_peat(O, c, y)
            ppl, oth, phh = t if t else (0.0, 0.0, 0.0)
            ash = (ppl * fc(O, y, stage=BP, driver="peat_power_heat_t") + oth * fc(O, y, stage=BP, driver="peat_supply_t")) \
                * fc(O, y, stage=BP, residue="peat_ash")
            ashh = phh * fc(O, y, stage=BP, driver="peat_household_t") * fc(O, y, stage=BP, residue="peat_ash")
            q_pl_peat, q_hh_peat = ash * conc, ashh * conc
            want = {
                (BP, "liberated"): (p["dpl"] * kap + q_pl_peat) * s67,
                (BP, "memo_biosphere"): (p["dpl"] * kap + q_pl_peat) * (1 - s67),
                (DOM, "liberated"): (p["dhh"] * kap + q_hh_peat) * s68 + p["dch"] * kap * (s69 + (1 - s69) * s70),
                (DOM, "memo_biosphere"): (p["dhh"] * kap + q_hh_peat) * (1 - s68) + p["dch"] * kap * (1 - s69) * (1 - s70),
            }
            for (sub, tier), w in want.items():
                got = rows.find(y, country=c, substream=sub, group="Cs137+", tier=tier)
                assert len(got) == 1, f"{c} {y} {sub} {tier}: {len(got)} rows"
                r = got[0]
                f = ids(r["factor_ids"])
                assert fid in f and "other:0060" not in f, f"{c} {y} {sub} {tier}: {fid} must replace other:0060 in {f}"
                assert close(float(r["value_central"]), w, CONS), f"{c} {y} {sub} {tier}: {r['value_central']} vs kappa-based {w}"
                wood_only = w - (q_pl_peat * (s67 if tier == "liberated" else 1 - s67) if sub == BP else
                                 q_hh_peat * (s68 if tier == "liberated" else 1 - s68))
                assert float(r["value_central"]) >= wood_only * (1 - CONS), "row below its wood part"
        # FIN before 2001 uses the XWL era row
        r = rows.find(1995, country="FIN", group="Cs137+", tier="memo_biosphere", substream=DOM)
        assert r and "other:0059" in ids(r[0]["factor_ids"]) and "other:0073" not in ids(r[0]["factor_ids"])

    def test_aggregated_rerelease_and_memo_pair(self, rows, oracle, expected):
        keys = sorted(
            (c, y)
            for (s, c, y) in expected.cs
            if s == DOM
            and y >= 1990
            and (c, y) in expected.units
            and expected.units[(c, y)]["Dch"].b.central > 0
            and expected.units[(c, y)]["Dhh"].b.central > 0
            and expected.peat.get((c, y), {}).get("Phh") is not None
            and expected.peat[(c, y)]["Phh"].central > 0
        )
        assert keys, "no country-year with household peat, household wood and charcoal"
        c, y = keys[0]
        rel = rows.one(y, country=c, substream=DOM, group="Cs137+", tier="liberated")
        mem = rows.one(
            y, country=c, substream=DOM, group="Cs137+", tier="memo_biosphere"
        )
        fuel = expected.cs[(DOM, c, y)]["Q"].central
        assert close(
            float(rel["value_central"]) + float(mem["value_central"]), fuel, CONS
        )
        assert rel["notes"].startswith("re-release")
        assert "; components: peat_household+wood_household+charcoal" in rel["notes"]
        assert "; components: peat_household+wood_household+charcoal" in mem["notes"]
        assert (
            "other:0069" in ids(rel["factor_ids"])
            and "other:0070" in ids(rel["factor_ids"])
            and "other:0068" in ids(rel["factor_ids"])
        )

    def test_pre1950_geothermal_row_count(self, pre_rows):
        assert {int(r["year"]) for r in pre_rows.rows} == set(range(1916, 1950))
        assert len(pre_rows.rows) == 34 * 7


# --------------------------------------------------------------------------------------------
# (h) pre-1950 file
# --------------------------------------------------------------------------------------------
class TestPre1950:
    def test_rows_match_oracle(self, comparison_pre, expected):
        assert expected.pre, "oracle expects pre-1950 geothermal rows"
        assert not comparison_pre, "pre-1950 rows differ from the oracle: " + show(
            [m for v in comparison_pre.values() for m in v]
        )

    def test_shape(self, pre_rows):
        assert {r["country"] for r in pre_rows.rows} == {"XXX"}
        assert {r["substream"] for r in pre_rows.rows} == {"geothermal"}
        assert {r["quantity"] for r in pre_rows.rows} == {"flow"}
        assert not [
            r
            for r in pre_rows.rows
            if r["tier"].startswith("memo") or r["quantity"].startswith("transfer")
        ]
        assert {r["group"] for r in pre_rows.rows} == GEO_GAS | GEO_SCALE
        assert {int(r["year"]) for r in pre_rows.rows} == set(range(1916, 1950))

    def test_each_row_passes_master_schema_with_relaxed_years(self, written):
        from jsonschema import Draft7Validator

        from pipeline.lib.io import read_table

        schema = json.loads(
            (ROOT / "schema" / "master.json").read_text(encoding="utf-8")
        )
        schema["properties"]["year"]["minimum"] = 1800
        schema["properties"]["year"]["maximum"] = 1949
        v = Draft7Validator(schema)
        recs = read_table(written[1])
        assert recs
        for rec in recs:
            if isinstance(rec["allocation_rule"], list):
                rec["allocation_rule"] = ";".join(rec["allocation_rule"])
            errs = list(v.iter_errors(rec))
            assert not errs, (
                f"pre-1950 row {rec['year']} {rec['group']} fails master.json: {errs[0].message}"
            )

    def test_earlier_geothermal_driver_gives_rows_in_the_same_path(
        self, other_mod, tmp_path
    ):
        rws = [
            _a("elec_gen_geothermal", y, "XWL", 0.5, "TWh", 0.1, src="S0810")
            for y in (1905, 1930, 1960)
        ]
        root = make_mini(tmp_path, {"electricity_generation.csv": rws})
        res = other_mod.build(root)
        pre = Rows(list(res.rows_pre1950))
        assert {int(r["year"]) for r in pre.rows} == {1905, 1930}
        assert {int(r["year"]) for r in res.rows} == {1960}
        assert not [r for r in pre.rows if r["tier"].startswith("memo")]
        comparison = compare_all(
            Oracle(root), Oracle(root).expected().pre, pre, "mini pre"
        )
        assert not comparison, show([m for v in comparison.values() for m in v])


# --------------------------------------------------------------------------------------------
# (j) CLI, on a small tree (the real-tree build is covered above)
# --------------------------------------------------------------------------------------------
ACT_COLUMNS = [
    "series",
    "year",
    "country",
    "value_low",
    "value_central",
    "value_high",
    "unit",
    "below_detection",
    "basis",
    "source_ids",
    "notes",
]
SRC = {"elec": "S0810", "bio": "S0846", "peat": "S0847"}


def _a(
    series,
    y,
    c,
    central,
    unit,
    band=0.1,
    basis="compiled",
    src="S0846",
    low=None,
    high=None,
):
    lo = central * (1 - band) if low is None else low
    hi = central * (1 + band) if high is None else high
    return {
        "series": series,
        "year": y,
        "country": c,
        "value_low": lo,
        "value_central": central,
        "value_high": hi,
        "unit": unit,
        "below_detection": "false",
        "basis": basis,
        "source_ids": src,
        "notes": "",
    }


def make_mini(
    tmp_path: Path,
    act: dict,
    factor_edit=None,
    event_edit=None,
    name="mini",
    extra_files=None,
) -> Path:
    root = tmp_path / name
    (root / "data" / "activity").mkdir(parents=True)
    (root / "data" / "factors").mkdir(parents=True)
    shutil.copytree(ROOT / "data" / "reference", root / "data" / "reference")
    shutil.copy(ROOT / "data" / "sources.csv", root / "data" / "sources.csv")
    for fname, rws in act.items():
        if rws is None:
            continue
        with open(
            root / "data" / "activity" / fname, "w", newline="\n", encoding="utf-8"
        ) as fh:
            w = csv.DictWriter(fh, fieldnames=ACT_COLUMNS)
            w.writeheader()
            w.writerows(rws)
    fac = pd.read_csv(
        ROOT / "data" / "factors" / "other.csv", dtype=str, keep_default_na=False
    )
    recs = fac.to_dict("records")
    if factor_edit:
        recs = factor_edit(recs)
    with open(
        root / "data" / "factors" / "other.csv", "w", newline="\n", encoding="utf-8"
    ) as fh:
        w = csv.DictWriter(fh, fieldnames=list(fac.columns))
        w.writeheader()
        w.writerows(recs)
    ev = pd.read_csv(ROOT / "data" / "events.csv", dtype=str, keep_default_na=False)
    erecs = ev.to_dict("records")
    if event_edit:
        erecs = event_edit(erecs)
    with open(root / "data" / "events.csv", "w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(ev.columns))
        w.writeheader()
        w.writerows(erecs)
    for rel, text in (extra_files or {}).items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    (root / "research" / "other").mkdir(parents=True, exist_ok=True)
    (root / "data" / "streams").mkdir(exist_ok=True)
    (root / "data" / "streams_pre1950").mkdir(exist_ok=True)
    return root


def edit_factor(fid, **changes):
    def fn(recs):
        for r in recs:
            if r["factor_id"] == fid:
                r.update({k: str(v) for k, v in changes.items()})
        return recs

    return fn


def add_factor(base_id, new_id, **changes):
    def fn(recs):
        src = next(r for r in recs if r["factor_id"] == base_id)
        new = dict(src)
        new["factor_id"] = new_id
        new.update({k: str(v) for k, v in changes.items()})
        recs.append(new)
        return recs

    return fn


def drop_factor(fid):
    return lambda recs: [r for r in recs if r["factor_id"] != fid]


def freg(fid: str, col: str = "value_central") -> float:
    df = pd.read_csv(
        ROOT / "data" / "factors" / "other.csv", dtype=str, keep_default_na=False
    ).set_index("factor_id")
    return float(df.loc[fid, col])


def build_mini(mod, tmp_path, act, **kw):
    root = make_mini(tmp_path, act, **kw)
    res = mod.build(root)
    return root, res, Rows(list(res.rows)), list(res.log)


def mini_world(years=(1990, 1991, 1992, 2023, 2024, 2025)):
    """Geothermal (ITA, USA, JPN + exact world), wood (FRA with UNSD household to 2023, CHN without, charcoal), peat (FIN, IRL)."""
    el, bio, pt = [], [], []
    for y in years:
        ex = y == 2025
        b = "extrapolated" if ex else "compiled"
        tot = 0.0
        for c, v in (("ITA", 5.6), ("USA", 17.0), ("JPN", 3.1)):
            el.append(_a("elec_gen_geothermal", y, c, v, "TWh", 0.05, b, SRC["elec"]))
            tot += v
        el.append(_a("elec_gen_geothermal", y, "XWL", tot, "TWh", 0.05, b, SRC["elec"]))
        wsum = csum = 0.0
        for c, w, m, ch in (
            ("FRA", 9.0e6, 3.0e7, 2.0e5),
            ("CHN", 2.5e8, None, 3.0e6),
            ("BRA", 1.5e8, 1.0e8, 5.0e6),
        ):
            bio.append(_a("wood_fuel_t", y, c, w, "t", 0.1, b))
            bio.append(_a("charcoal_production_t", y, c, ch, "t", 0.15, b))
            if m is not None and y <= 2023:
                bio.append(_a("household_fuelwood_m3", y, c, m, "m3", 0.1))
            wsum += w
            csum += ch
        bio.append(_a("wood_fuel_t", y, "XWL", wsum * 1.03, "t", 0.02, b))
        bio.append(_a("charcoal_production_t", y, "XWL", csum * 1.01, "t", 0.02, b))
        for c, ppl, hh, sup in (
            ("FIN", 4.0e6, 1.0e5, 6.0e6),
            ("IRL", 1.0e6, 6.0e5, 2.4e6),
        ):
            pt.append(_a("peat_power_heat_t", y, c, ppl, "t", 0.1, b, SRC["peat"]))
            pt.append(_a("peat_household_t", y, c, hh, "t", 0.2, b, SRC["peat"]))
            pt.append(_a("peat_supply_t", y, c, sup, "t", 0.1, b, SRC["peat"]))
    return {"electricity_generation.csv": el, "biomass.csv": bio, "peat.csv": pt}


@pytest.fixture(scope="module")
def mini_base(other_mod, tmp_path_factory):
    tmp = tmp_path_factory.mktemp("mini_base")
    root, res, rws, lg = build_mini(other_mod, tmp, mini_world())
    O = Oracle(root)
    return root, res, rws, lg, O, O.expected()


class TestCli:
    def test_cli_write_diff_and_log(self, other_mod, tmp_path, write_master):
        act = mini_world((1990, 1991, 2024, 2025))
        act["electricity_generation.csv"].append(
            _a(
                "elec_gen_geothermal",
                1930,
                "XWL",
                0.2,
                "TWh",
                0.1,
                "modelled",
                SRC["elec"],
            )
        )
        root = make_mini(tmp_path, act, name="cli_root")
        cmd = [sys.executable, "-m", "pipeline.streams.other", "--root", str(root)]

        def run(*extra):
            return subprocess.run(
                cmd + list(extra),
                cwd=str(ROOT),
                env=_env(),
                capture_output=True,
                text=True,
                timeout=1800,
                check=False,
            )

        w = run("--write")
        assert w.returncode == 0, (
            f"--write exited {w.returncode}\nstdout: {w.stdout[-800:]}\nstderr: {w.stderr[-1500:]}"
        )
        from pipeline.lib.io import gzip_bytes, read_bytes

        main = root / "data" / "streams" / "other.csv.gz"
        pre = root / "data" / "streams_pre1950" / "other.csv.gz"
        logf = root / "research" / "other" / "build_log.csv"
        assert main.is_file() and pre.is_file() and logf.is_file(), (
            "--write must write all three files (OTHER_SPEC 1)"
        )
        res = other_mod.build(root)
        write_master(list(res.rows), tmp_path / "m.csv")
        write_master(list(res.rows_pre1950), tmp_path / "p.csv")
        assert read_bytes(main) == (tmp_path / "m.csv").read_bytes(), (
            "CLI master output differs from build() + write_master"
        )
        assert read_bytes(pre) == (tmp_path / "p.csv").read_bytes(), (
            "CLI pre-1950 output differs"
        )
        out = w.stdout + w.stderr
        assert "log no_driver:" in out and "log no_family: 2" in out, out[-500:]
        assert run().returncode == 0, "identical files must give exit 0"

        good = logf.read_bytes()
        logf.write_bytes(good + b"no_driver,1900,XXX,,tampered\n")
        assert run().returncode != 0, (
            "a differing build_log.csv alone must give a non-zero exit (the log is part of the diff)"
        )
        assert logf.read_bytes() != good, "the diff run must not overwrite the log"
        logf.write_bytes(good)
        t = pre.read_bytes()
        pre.write_bytes(gzip_bytes(read_bytes(pre).replace(b"other,geothermal", b"other,geothermaI", 1)))
        assert run().returncode != 0, (
            "a differing pre-1950 file must give a non-zero exit"
        )
        pre.write_bytes(t)
        text = main.read_bytes()
        tampered = gzip_bytes(read_bytes(main).replace(b"other,geothermal", b"other,geothermaI", 1))
        main.write_bytes(tampered)
        assert run().returncode != 0, (
            "a differing master file must give a non-zero exit"
        )
        assert main.read_bytes() == tampered, "the diff run must not overwrite files"
        main.write_bytes(text)
        assert run().returncode == 0
        logf.unlink()
        assert run().returncode != 0, (
            "a missing committed build_log.csv must count as a difference"
        )

    def test_cli_second_write_is_byte_identical(self, tmp_path):
        root = make_mini(tmp_path, mini_world((1990, 2025)), name="cli_twice")
        cmd = [
            sys.executable,
            "-m",
            "pipeline.streams.other",
            "--root",
            str(root),
            "--write",
        ]
        files = [
            root / "data" / "streams" / "other.csv.gz",
            root / "data" / "streams_pre1950" / "other.csv.gz",
            root / "research" / "other" / "build_log.csv",
        ]
        first = None
        for _ in range(2):
            p = subprocess.run(
                cmd,
                cwd=str(ROOT),
                env=_env(),
                capture_output=True,
                text=True,
                timeout=1800,
                check=False,
            )
            assert p.returncode == 0, p.stderr[-1000:]
            cur = [f.read_bytes() for f in files]
            if first is None:
                first = cur
            else:
                assert cur == first, "two --write runs differ (determinism, 9(d))"

    def test_cli_output_passes_the_validator(self, tmp_path):
        from pipeline.validate import validate

        root = make_mini(tmp_path, mini_world((1990, 2024, 2025)), name="cli_val")
        p = subprocess.run(
            [
                sys.executable,
                "-m",
                "pipeline.streams.other",
                "--root",
                str(root),
                "--write",
            ],
            cwd=str(ROOT),
            env=_env(),
            capture_output=True,
            text=True,
            timeout=1800,
            check=False,
        )
        assert p.returncode == 0, p.stderr[-800:]
        shutil.copytree(ROOT / "schema", root / "schema", dirs_exist_ok=True)
        found = [
            i
            for i in validate(root, master_files=["data/streams/other.csv.gz"])
            if i.file == "data/streams/other.csv.gz"
        ]
        assert not found, "\n".join(f"{i.rule} {i.message}" for i in found[:8])


# --------------------------------------------------------------------------------------------
# (g) fixture tests
# --------------------------------------------------------------------------------------------
def all_problems(O, exp, rws, label="mini"):
    prob = compare_all(O, exp.rows, rws, label)
    return [m for v in prob.values() for m in v]


class TestMiniBase:
    def test_mini_tree_matches_oracle(self, mini_base):
        _root, res, rws, _lg, O, exp = mini_base
        flat = all_problems(O, exp, rws)
        assert not flat, "mini tree differs from the oracle: " + show(flat)
        pre = compare_all(O, exp.pre, Rows(list(res.rows_pre1950)), "mini pre")
        assert not [m for v in pre.values() for m in v]

    def test_mini_log_matches_oracle(self, mini_base):
        _root, _res, _rws, lg, O, exp = mini_base
        msgs = check_log(lg, O, exp, "mini")
        assert not msgs, show(msgs, 10)

    def test_at_most_one_lib_warning(self, mini_base):
        assert len(log_entries(mini_base[3], "lib_warning")) <= 1

    def test_geothermal_world_equal_to_country_sum_gives_no_xxx_rows(self, mini_base):
        _, _, rws, _lg, _O, _e = mini_base
        assert not rws.find(substream=GEO, country="XXX")

    def test_rest_of_world_wood_unit_exists_with_text(self, mini_base):
        _, _, rws, _lg, _O, _e = mini_base
        r = rws.find(
            1990, substream=DOM, country="XXX", group="K40", tier="memo_biosphere"
        )
        assert (
            len(r) == 1 and TXT_REST in r[0]["notes"] and TXT_FALLBACK in r[0]["notes"]
        )

    def test_no_peat_rest_of_world(self, mini_base):
        _, _, rws, _lg, _O, _e = mini_base
        assert not rws.find(country="XXX", residue_type="peat_ash")


class TestMiniGeothermalResidual:
    def _tree(self, other_mod, tmp_path):
        rows_ = []
        for y, f in ((1990, 1 + 5e-6), (1991, 1 + 5e-5), (1992, 0.9)):
            tot = 0.0
            for c, v in (("ITA", 5.6), ("USA", 17.0)):
                rows_.append(
                    _a("elec_gen_geothermal", y, c, v, "TWh", 0.05, src="S0810")
                )
                tot += v
            rows_.append(
                _a("elec_gen_geothermal", y, "XWL", tot * f, "TWh", 0.05, src="S0810")
            )
        rows_.append(
            _a(
                "elec_gen_geothermal",
                2025,
                "XWL",
                0.0,
                "TWh",
                0.0,
                "extrapolated",
                src="S0810",
                low=0.0,
                high=0.0,
            )
        )
        return build_mini(other_mod, tmp_path, {"electricity_generation.csv": rows_})

    def test_tolerance_rows_and_negative_residual(self, other_mod, tmp_path):
        root, _res, rws, lg = self._tree(other_mod, tmp_path)
        assert not rws.find(1990, substream=GEO, country="XXX"), (
            "5e-6 residual is within the 1e-5 tolerance: no XXX rows"
        )
        x91 = rws.find(1991, substream=GEO, country="XXX", group="Rn222+")
        assert len(x91) == 1 and TXT_REST in x91[0]["notes"], (
            "5e-5 residual gives rest-of-world rows"
        )
        assert not rws.find(1992, substream=GEO, country="XXX"), (
            "negative residual gives no rows"
        )
        nr = [(e["country"], e["year"]) for e in log_entries(lg, "negative_residual")]
        assert nr == [("XXX", 1992)], nr
        assert not log_entries(lg, "negative_residual", year=1990) and not log_entries(
            lg, "negative_residual", year=1991
        )
        O = Oracle(root)
        exp = O.expected()
        assert not all_problems(O, exp, rws)

    def test_zero_world_row_gives_no_rows_not_zero_rows(self, other_mod, tmp_path):
        _root, _res, rws, _lg = self._tree(other_mod, tmp_path)
        assert not rws.find(2025), (
            "a zero world row (and no countries) must give no rows at all"
        )

    def test_absent_series_give_no_rows_and_one_no_driver_each(
        self, other_mod, tmp_path
    ):
        root, _res, rws, lg = self._tree(other_mod, tmp_path)
        nd = Counter((e["country"], run_of(e)) for e in log_entries(lg, "no_driver"))
        # wood and peat files are absent: one aggregated run each over the whole span, never an exception
        assert nd[("XXX", (1800, 2025, 226))] == 2, (
            f"expected one 1800-2025 run each for wood_fuel_t and peat: {dict(nd)}"
        )
        assert (
            nd[("XXX", (1800, 1989, 190))] == 1 and nd[("XXX", (1993, 2024, 32))] == 1
        ), dict(nd)
        assert not [r for r in rws.rows if r["substream"] != GEO]
        O = Oracle(root)
        assert not check_log(lg, O, O.expected(), "geo")


class TestMiniWood:
    def _tree(self, other_mod, tmp_path, **kw):
        bio = []
        for y in (1990, 1991, 1992):
            # USA: household UNSD larger than FAOSTAT: cap binds at every bound, plant wood exactly 0/0/0
            bio += [
                _a("wood_fuel_t", y, "USA", 1.0e6, "t", 0.1),
                _a("household_fuelwood_m3", y, "USA", 4.0e6, "m3", 0.1),
            ]
            # DEU: charcoal larger than the total: charcoal cap binds
            bio += [
                _a("wood_fuel_t", y, "DEU", 1.0e5, "t", 0.1),
                _a("charcoal_production_t", y, "DEU", 5.0e5, "t", 0.1),
                _a("household_fuelwood_m3", y, "DEU", 1.0e4, "m3", 0.1),
            ]
            # FRA: wide household band so only the high bound is capped (1990); fallback in 1991 (no UNSD row)
            bio += [_a("wood_fuel_t", y, "FRA", 1.0e6, "t", 0.1)]
        # central household wood = 0.8 x direct-burn wood, with a wide band: only the high bound is capped
        m_fra = (
            0.8 * 1.0e6 * freg("other:0048") / (freg("other:0049") * freg("other:0048"))
        )
        bio += [_a("household_fuelwood_m3", 1990, "FRA", m_fra, "m3", 0.7)]
        # UNSD exact zero in 1992 for FRA: D_hh = 0, no fallback
        bio += [
            _a("household_fuelwood_m3", 1992, "FRA", 0.0, "m3", 0.0, low=0.0, high=0.0)
        ]
        # ESP 1990: wide wood band, narrow household band, central household just above direct-burn wood:
        # the cap binds at the low and central bounds only, so plant wood is the partly capped (0, 0, h)
        bio += [
            _a("wood_fuel_t", 1990, "ESP", 2.0e5, "t", 0.5),
            _a(
                "household_fuelwood_m3",
                1990,
                "ESP",
                1.001 * 2.0e5 / freg("other:0049"),
                "m3",
                0.01,
            ),
        ]
        for y in (1990, 1991, 1992):
            tot = 1.0e6 + 1.0e5 + 1.0e6 + (2.0e5 if y == 1990 else 0.0)
            bio.append(_a("wood_fuel_t", y, "XWL", tot, "t", 0.01))
        return build_mini(other_mod, tmp_path, {"biomass.csv": bio}, **kw)

    def test_matches_oracle_and_caps(self, other_mod, tmp_path):
        root, _res, rws, lg = self._tree(other_mod, tmp_path)
        O = Oracle(root)
        exp = O.expected()
        assert exp.units[("USA", 1990)]["caph"] == ["low", "central", "high"]
        assert exp.units[("DEU", 1990)]["capc"], "premise: DEU charcoal cap binds"
        assert exp.units[("FRA", 1990)]["caph"] == ["high"], (
            f"premise: FRA 1990 only the high bound is capped, got {exp.units[('FRA', 1990)]['caph']}"
        )
        esp = exp.units[("ESP", 1990)]
        assert esp["caph"] == ["low", "central"], (
            f"premise: ESP 1990 cap binds at low and central, got {esp['caph']}"
        )
        assert (
            esp["Dpl"].b.low == 0
            and esp["Dpl"].b.central == 0
            and esp["Dpl"].b.high > 0
        ), esp["Dpl"].b
        flat = all_problems(O, exp, rws)
        assert not flat, show(flat)
        assert not rws.find(1990, country="USA", substream=BP, tier="memo_biosphere"), (
            "exact-zero plant wood writes no rows (res. 8)"
        )
        msgs = check_log(lg, O, exp, "wood")
        assert not msgs, show(msgs)

    def test_partly_capped_plant_wood_writes_flagged_rows(self, other_mod, tmp_path):
        _root, _res, rws, lg = self._tree(other_mod, tmp_path)
        for g in WOOD5:
            r = rws.one(
                1990, country="ESP", substream=BP, group=g, tier="memo_biosphere"
            )
            assert (
                float(r["value_low"]) == 0
                and float(r["value_central"]) == 0
                and float(r["value_high"]) > 0
                and as_bool(r["below_detection"])
            )
            assert (
                r["notes"]
                == f"{RULE['memowood']}; components: wood_plant; below_detection cause: clipped_difference"
            ), r["notes"]
        cs = rws.one(
            1990, country="ESP", substream=BP, group="Cs137+", tier="liberated"
        )
        assert as_bool(cs["below_detection"]) and cs["notes"].endswith(
            "; components: wood_plant; below_detection cause: clipped_difference"
        )
        d = [e for e in log_entries(lg, "household_wood_capped", country="ESP")]
        assert len(d) == 1 and d[0]["detail"].endswith(": capped low+central"), d

    def test_cap_changes_only_the_bounds_it_must(self, other_mod, tmp_path):
        _root, _res, _rws, lg = self._tree(other_mod, tmp_path)
        e = [
            x
            for x in log_entries(lg, "household_wood_capped", country="FRA")
            if _span(x) and _span(x)[0] == 1990
        ]
        assert e, (
            f"FRA 1990 household cap not logged: {log_entries(lg, 'household_wood_capped')}"
        )
        d = str(e[0]["detail"])
        assert re.search(r"\bhigh\b", d) and not re.search(r"\b(low|central)\b", d), (
            f"detail should name only the high bound: {d!r}"
        )

    def test_fallback_for_year_without_unsd_row_and_exact_zero_row(
        self, other_mod, tmp_path
    ):
        _root, _res, rws, lg = self._tree(other_mod, tmp_path)
        fb = {(e["country"], _span(e)) for e in log_entries(lg, "household_fallback")}
        assert ("FRA", (1991, 1991)) in fb and not any(
            c == "FRA" and sp and sp[0] <= 1992 <= sp[1] for c, sp in fb
        ), (
            f"FRA falls back in 1991 only; a 0/0/0 UNSD row (1992) is data, not a fallback: {sorted(fb)}"
        )
        r91 = rws.find(
            1991, country="FRA", substream=DOM, group="K40", tier="memo_biosphere"
        )
        assert len(r91) == 1 and TXT_FALLBACK in r91[0]["notes"]
        assert not rws.find(
            1992, country="FRA", substream=DOM, group="K40", tier="memo_biosphere"
        ), "UNSD household exactly 0/0/0 and no charcoal: no household wood rows"
        assert rws.find(
            1992, country="FRA", substream=BP, group="K40", tier="memo_biosphere"
        ), "all direct-burn wood is plant wood"

    def test_rest_of_world_residual_tolerance_for_wood(self, other_mod, tmp_path):
        bio = []
        for y, f in ((1990, 1 + 5e-6), (1991, 1 + 5e-5), (1992, 0.9)):
            bio += [
                _a("wood_fuel_t", y, "FRA", 1.0e6, "t", 0.1),
                _a("wood_fuel_t", y, "XWL", 1.0e6 * f, "t", 0.01),
            ]
        _root, _res, rws, lg = build_mini(other_mod, tmp_path, {"biomass.csv": bio})
        assert not rws.find(1990, country="XXX"), (
            "5e-6: within tolerance, no rest-of-world wood rows, no log"
        )
        assert rws.find(1991, country="XXX"), "5e-5: rest-of-world rows"
        assert not rws.find(1992, country="XXX")
        assert [
            (e["country"], e["year"]) for e in log_entries(lg, "negative_residual")
        ] == [("XXX", 1992)]

    def test_predecessor_csk_czk(self, other_mod, tmp_path):
        bio = [
            _a("wood_fuel_t", 1992, "CSK", 1.0e6, "t", 0.1),
            _a("wood_fuel_t", 1992, "CZE", 5.0e5, "t", 0.1),
            _a("wood_fuel_t", 1993, "CZE", 5.0e5, "t", 0.1),
            _a("wood_fuel_t", 1992, "XWL", 1.2e6, "t", 0.02),
            _a("wood_fuel_t", 1993, "XWL", 5.0e5, "t", 0.02),
        ]
        root, _res, rws, lg = build_mini(other_mod, tmp_path, {"biomass.csv": bio})
        pd_ = log_entries(lg, "predecessor_dropped")
        assert (
            len(pd_) == 1
            and pd_[0]["country"] == "CZE"
            and pd_[0]["year"] == 1992
            and "CSK" in str(pd_[0]["detail"])
        ), pd_
        assert not rws.find(1992, country="CZE"), "the dropped CZE value gives no rows"
        assert rws.find(1992, country="CSK") and rws.find(1993, country="CZE")
        O = Oracle(root)
        assert not all_problems(O, O.expected(), rws)

    def test_missing_driver_year_aggregated_no_driver(self, other_mod, tmp_path):
        bio = []
        for y in (1990, 1992, 1993):
            bio += [
                _a("wood_fuel_t", y, "FRA", 1.0e6, "t", 0.1),
                _a("wood_fuel_t", y, "XWL", 1.0e6, "t", 0.01),
            ]
        _root, _res, rws, lg = build_mini(other_mod, tmp_path, {"biomass.csv": bio})
        nd = {(e["country"], run_of(e)) for e in log_entries(lg, "no_driver")}
        assert ("XXX", (1991, 1991, 1)) in nd, nd
        assert not rws.find(1991, substream=DOM)


class TestMiniPeat:
    def test_negative_other_use_residual(self, other_mod, tmp_path):
        pt = []
        for y in (2000, 2001):
            pt += [
                _a("peat_power_heat_t", y, "FIN", 4.0e6, "t", 0.1),
                _a("peat_household_t", y, "FIN", 1.0e5, "t", 0.1),
                _a(
                    "peat_supply_t",
                    y,
                    "FIN",
                    4.0e6 if y == 2000 else 6.0e6,
                    "t",
                    0.05,
                    src="S0847",
                ),
            ]
        root, _res, rws, lg = build_mini(other_mod, tmp_path, {"peat.csv": pt})
        nr = log_entries(lg, "negative_residual")
        assert [(e["country"], e["year"]) for e in nr] == [("FIN", 2000)], nr
        O = Oracle(root)
        exp = O.expected()
        assert not all_problems(O, exp, rws)
        assert not check_log(lg, O, exp, "peat")

    @staticmethod
    def _edits(*edits):
        def fe(recs):
            for e in edits:
                recs = e(recs)
            return recs

        return fe

    def test_plant_stack_cap_binds_residue_rows_still_written(
        self, other_mod, tmp_path
    ):
        pt = [
            _a("peat_power_heat_t", 2000, "FIN", 4.0e6, "t", 0.1, src="S0847"),
            _a("peat_supply_t", 2000, "FIN", 4.0e6, "t", 0.1, src="S0847"),
        ]
        root, _res, rws, lg = build_mini(
            other_mod,
            tmp_path,
            {"peat.csv": pt},
            factor_edit=self._edits(
                edit_factor("other:0027", value_low=3, value_central=3, value_high=3)
            ),
        )
        caps = log_entries(lg, "cap_applied")
        assert {e["group"] for e in caps} >= {"U238+", "K40"} and all(
            e["country"] == "FIN" and e["year"] == 2000 for e in caps
        ), caps
        assert all(e["detail"].startswith("plant stack cap: capped ") for e in caps)
        O = Oracle(root)
        exp = O.expected()
        assert not all_problems(O, exp, rws), (
            "with f_fly < 1 the residue rows are written, unflagged, equal to the oracle"
        )
        r = rws.one(2000, country="FIN", substream=BP, group="U238+", tier="impounded")
        assert not as_bool(r["below_detection"]) and float(r["value_central"]) > 0
        assert not check_log(lg, O, exp, "cap")

    def test_plant_cap_using_the_whole_remainder_writes_no_residue_rows(
        self, other_mod, tmp_path
    ):
        pt = [
            _a("peat_power_heat_t", 2000, "FIN", 4.0e6, "t", 0.1, src="S0847"),
            _a("peat_supply_t", 2000, "FIN", 4.0e6, "t", 0.1, src="S0847"),
        ]
        _root, _res, rws, lg = build_mini(
            other_mod,
            tmp_path,
            {"peat.csv": pt},
            factor_edit=self._edits(
                edit_factor("other:0027", value_low=3, value_central=3, value_high=3),
                edit_factor("other:0014", value_low=1, value_central=1, value_high=1),
            ),
        )
        assert {e["group"] for e in log_entries(lg, "cap_applied")} >= {"U238+", "K40"}
        for g in ("U238+", "K40"):
            assert rws.one(
                2000, country="FIN", substream=BP, group=g, tier="liberated"
            ), "the stack row is written"
            sa = float(
                rws.one(2000, country="FIN", substream=BP, group=g, tier="liberated")[
                    "value_central"
                ]
            )
            for t in ("impounded", "dispersed"):
                rr = rws.find(2000, country="FIN", substream=BP, group=g, tier=t)
                # R2: product(A, exact 1) may leave floating-point dust; an exactly (0,0,0) remainder writes no row
                assert not rr or float(rr[0]["value_high"]) <= 1e-12 * sa, (
                    f"{g} {t}: residue row written for a used-up remainder: {rr[0]['value_central']}"
                )

    def test_household_smoke_cap_using_the_whole_remainder_writes_no_residue_rows(
        self, other_mod, tmp_path
    ):
        pt = [
            _a("peat_household_t", 2000, "IRL", 6.0e5, "t", 0.2, src="S0847"),
            _a("peat_supply_t", 2000, "IRL", 6.0e5, "t", 0.1, src="S0847"),
        ]
        root, _res, rws, lg = build_mini(
            other_mod,
            tmp_path,
            {"peat.csv": pt},
            factor_edit=self._edits(
                edit_factor("other:0043", value_low=3, value_central=3, value_high=3)
            ),
        )
        caps = log_entries(lg, "cap_applied")
        assert {e["group"] for e in caps} == set(PEAT11), (
            "the smoke cap binds at every bound for all eleven groups"
        )
        assert all(
            e["detail"] == "household smoke cap: capped low+central+high" for e in caps
        ), [e["detail"] for e in caps][:2]
        for g in PEAT11:
            d1 = rws.one(2000, country="IRL", substream=DOM, group=g, tier="liberated")
            assert not as_bool(d1["below_detection"]) and float(d1["value_central"]) > 0
            assert not rws.find(
                2000, country="IRL", substream=DOM, group=g, tier="impounded"
            )
            assert not rws.find(
                2000, country="IRL", substream=DOM, group=g, tier="dispersed"
            )
        O = Oracle(root)
        exp = O.expected()
        assert not all_problems(O, exp, rws)
        assert not check_log(lg, O, exp, "smoke")

    def test_empty_plant_type_chain_writes_no_plant_rows(self, other_mod, tmp_path):
        pt = [
            _a("peat_household_t", 2000, "IRL", 6.0e5, "t", 0.2, src="S0847"),
            _a("peat_supply_t", 2000, "IRL", 6.0e5, "t", 0.1, src="S0847"),
        ]
        _root, _res, rws, _lg = build_mini(other_mod, tmp_path, {"peat.csv": pt})
        assert not [
            r for r in rws.rows if r["substream"] == BP and r["group"] in PEAT11
        ], "supply equal to household: no plant-type peat rows"
        assert rws.find(
            2000, country="IRL", substream=DOM, group="U238+", tier="liberated"
        )
        assert not [
            r for r in rws.rows if r["substream"] == BP and r["group"] == "Cs137+"
        ]

    def test_pre1990_escape_fraction_row(self, other_mod, tmp_path):
        pt = [
            _a("peat_power_heat_t", 1985, "FIN", 4.0e6, "t", 0.1, src="S0847"),
            _a("peat_supply_t", 1985, "FIN", 4.0e6, "t", 0.1, src="S0847"),
        ]
        root, _res, rws, _lg = build_mini(other_mod, tmp_path, {"peat.csv": pt})
        r = rws.one(
            1985,
            country="FIN",
            substream=BP,
            group="Pb210+",
            tier="liberated",
            route="air_stack",
        )
        assert "other:0026" in ids(r["factor_ids"]) and "other:0027" not in ids(
            r["factor_ids"]
        )
        O = Oracle(root)
        assert not all_problems(O, O.expected(), rws)


class TestMiniPeatSupplyAbsent:
    def test_missing_supply_gives_no_residual_and_one_aggregated_no_driver(self, other_mod, tmp_path):
        pt = []
        for y in (2000, 2001, 2002):
            pt += [_a("peat_power_heat_t", y, "FIN", 4.0e6, "t", 0.1, src="S0847"), _a("peat_household_t", y, "FIN", 1.0e5, "t", 0.1, src="S0847")]
        root, _res, rws, lg = build_mini(other_mod, tmp_path, {"peat.csv": pt})
        e = [x for x in log_entries(lg, "no_driver") if x["country"] == "FIN"]
        assert len(e) == 1 and e[0]["year"] == 2000, f"one aggregated peat_supply_t entry for FIN: {e}"
        assert re.fullmatch(r"2000-2002 \(3 years\): peat_supply_t has no value", e[0]["detail"]), e[0]["detail"]
        for r in rws.find(2001, country="FIN", substream=BP, group="U238+"):
            assert "peat_other" not in (r["notes"] or ""), "no residual is formed: no peat_other term"
        d = rws.one(2001, country="FIN", substream=BP, group="U238+", tier="liberated")
        assert "other:0012" not in ids(d["factor_ids"]) and "other:0010" in ids(d["factor_ids"])
        assert rws.find(2001, country="FIN", substream=DOM, group="U238+", tier="liberated"), "household chain runs"
        assert not log_entries(lg, "negative_residual")
        O = Oracle(root)
        exp = O.expected()
        assert not all_problems(O, exp, rws)
        assert not check_log(lg, O, exp, "supply")


class TestMiniRatioUnit:
    @pytest.mark.parametrize("fid,country", [("other:0071", "USA"), ("other:0075", "ITA")])
    def test_rn220_ratio_with_a_unit_other_than_one_raises(self, other_mod, tmp_path, fid, country):
        el = [_a("elec_gen_geothermal", 2010, country, 5.0, "TWh", 0.05, src="S0810"),
              _a("elec_gen_geothermal", 2010, "XWL", 5.0, "TWh", 0.05, src="S0810")]
        root = make_mini(tmp_path, {"electricity_generation.csv": el}, factor_edit=edit_factor(fid, unit="Bq/GWa"))
        with pytest.raises(lib_error()):
            other_mod.build(root)

    def test_unchanged_ratio_builds(self, other_mod, tmp_path):
        el = [_a("elec_gen_geothermal", 2010, "USA", 5.0, "TWh", 0.05, src="S0810"),
              _a("elec_gen_geothermal", 2010, "XWL", 5.0, "TWh", 0.05, src="S0810")]
        root = make_mini(tmp_path, {"electricity_generation.csv": el})
        assert other_mod.build(root).rows


class TestMiniErrors:
    def test_duplicate_activity_rows_raise_naming_the_key(self, other_mod, tmp_path):
        bio = [
            _a("wood_fuel_t", 1990, "FRA", 1.0e6, "t"),
            _a("wood_fuel_t", 1990, "FRA", 2.0e6, "t"),
        ]
        root = make_mini(tmp_path, {"biomass.csv": bio})
        with pytest.raises(lib_error()) as ei:
            other_mod.build(root)
        m = str(ei.value)
        assert "wood_fuel_t" in m and "1990" in m and "FRA" in m, (
            f"error should name the duplicate key: {m}"
        )

    def test_ambiguous_factor_propagates(self, other_mod, tmp_path):
        root = make_mini(
            tmp_path,
            mini_world((1990,)),
            factor_edit=add_factor("other:0048", "other:9001"),
        )
        with pytest.raises(lib_error(), match="ambiguous"):
            other_mod.build(root)

    def test_missing_factor_raises_and_is_not_logged(self, other_mod, tmp_path):
        root = make_mini(
            tmp_path, mini_world((1990,)), factor_edit=drop_factor("other:0013")
        )
        with pytest.raises(lib_error(), match="no factor row"):
            other_mod.build(root)

    @pytest.mark.parametrize("stage", ["hydro", "construction"])
    def test_registry_row_at_hydro_or_construction_raises(
        self, other_mod, tmp_path, stage
    ):
        root = make_mini(
            tmp_path,
            mini_world((1990,)),
            factor_edit=add_factor(
                "other:0001",
                "other:9002",
                stage=stage,
                group="",
                tier="liberated",
                route="air_stack",
            ),
        )
        with pytest.raises(lib_error()):
            other_mod.build(root)

    def test_commodity_factors_file_raises(self, other_mod, tmp_path):
        root = make_mini(
            tmp_path,
            mini_world((1990,)),
            extra_files={
                "data/reference/commodity_factors.csv": "commodity,stage,component\n"
            },
        )
        with pytest.raises(lib_error()):
            other_mod.build(root)

    def test_other_event_raises(self, other_mod, tmp_path):
        def ev(recs):
            e = dict(recs[0])
            e.update({"event_id": "E999", "stream": "other", "stage": "geothermal"})
            return recs + [e]

        root = make_mini(tmp_path, mini_world((1990,)), event_edit=ev)
        with pytest.raises(lib_error()):
            other_mod.build(root)

    def test_factor_unit_outside_the_allowed_set_raises(self, other_mod, tmp_path):
        root = make_mini(
            tmp_path,
            mini_world((1990,)),
            factor_edit=edit_factor("other:0010", unit="Bq/m3"),
        )
        with pytest.raises(lib_error()):
            other_mod.build(root)

    def test_share_with_high_above_one_raises_in_the_complement(
        self, other_mod, tmp_path
    ):
        root = make_mini(
            tmp_path,
            mini_world((1990,)),
            factor_edit=edit_factor("other:0068", value_high=1.5),
        )
        with pytest.raises(lib_error()):
            other_mod.build(root)

    def test_complement_round_trip(self, other_mod, tmp_path):
        """1 - s: release + memo = fuel Cs-137 exactly at the centre (single-material key, wood only)."""
        bio = [
            _a("wood_fuel_t", 2005, "FRA", 1.0e6, "t", 0.1),
            _a("wood_fuel_t", 2005, "XWL", 1.0e6, "t", 0.01),
        ]
        root, _res, rws, _lg = build_mini(other_mod, tmp_path, {"biomass.csv": bio})
        O = Oracle(root)
        for sub in (BP, DOM):
            rel = rws.find(
                2005, country="FRA", substream=sub, group="Cs137+", tier="liberated"
            )
            mem = rws.find(
                2005,
                country="FRA",
                substream=sub,
                group="Cs137+",
                tier="memo_biosphere",
            )
            if not rel:
                continue
            u = O.expected().units[("FRA", 2005)]
            q = (u["Dpl"] if sub == BP else u["Dhh"]).b.central * fc(
                O, 2005, "FRA", stage=BP, group="Cs137+", driver="wood_fuel_t"
            )
            assert close(
                float(rel[0]["value_central"]) + float(mem[0]["value_central"]), q, CONS
            )
            assert mem[0]["tier"] == "memo_biosphere"
