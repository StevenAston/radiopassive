"""Spec-blind tests for the coal stream script (Task 2.2, docs/COAL_SPEC.md section 9 (a)-(h)).

Written from docs/COAL_SPEC.md, docs/LIB_SPEC.md (v1.2), docs/METHODS.md (3, 5.2, 6.3, 10, 11),
docs/SCHEMA.md (3, 4.9, 5), schema/master.json, data/factors/coal.csv, data/activity/coal.csv,
data/reference/vocab.json and research/coal/factors_notes.md. Neither pipeline/streams nor
pipeline/lib was read. All expected values come from the independent arithmetic in
coal_oracle.py (pandas plus the standard library; no pipeline.lib).

Mapping to COAL_SPEC section 9
------------------------------
(a) Schema            TestSchema
(b) Candidate groups  TestCandidateGroups
(c) Conservation      TestConservation
(d) Determinism       TestDeterminism (build twice, write_master, CLI)
(e) Benchmarks        TestBenchmarks
(f) Hand-computed     TestHandComputed2005 / TestCapCasesPre1950
(g) Fixture tests     TestMiniTree*
(h) Pre-1950 file     TestPre1950
plus TestRowConventions (section 3 and section 4/5/6 row shapes) and TestLog (section 8).

SPEC AMBIGUITIES / CONTRADICTIONS (tests avoid asserting anything beyond a defensible reading)
------------------------------------------------------------------------------------------------
A1. COUNTRY CODE OF WORLD-AGGREGATE ROWS. COAL_SPEC 4.1, 5 and 6 put country `XWL` on the
    rest-of-world mining rows and on every combustion row, but SCHEMA 3 / validator rule V10 forbid
    `XWL` in the master table (global data without a country breakdown go in `XXX`).
    Row selection here accepts either code (WORLD_CODES); the schema test (a) is strict, so it
    fails if the script emits `XWL`.
A2. BOUND-WISE CONSERVATION (9(c)). With the independent difference of section 7 the fly-ash
    residue is F - S, and S + (F - S) = F can hold for the central value only: the lower and upper
    bounds of an independent difference are not F.low - S.high and so on. Only the central
    identity is tested.
A3. F_g + B_g (sections 5.2 and 5.4) does not say whether the two terms are combined as independent
    or fully correlated, and the same holds for the sum of the listed countries in the
    rest-of-world residual (4.1). Stack and stack-radon rows are therefore tested on their central
    value only; the rest-of-world row accepts either convention for its bounds. The cap cases are
    chosen so that the tested bounds are capped under both conventions.
A4. FLAG OF A CLIPPED DIFFERENCE. Section 7 clips a low bound to 0 but does not say whether the
    resulting Bounds is flagged `nd_floored`. Rows that are a bare difference (household ash,
    industrial ash) are therefore not checked for `below_detection` when their low bound is 0.
A5. MINIATURE TREE "TWO GROUPS" (9(g)). Section 3 fixes the eleven groups and says a failed
    required `select` raises LibError, so a two-group factor file cannot work. The miniature trees
    here keep the full real factor registry (copied) and shrink the activity file (five years, two
    listed countries plus XWL).
A6. BENCHMARK "Mine radon (China, scaled to power coal)" (9(e)) does not give the scaling. It is
    computed here as (China mine-radon row / China production, Bq per tonne) x power-station coal
    (coal_ash_power_t / 0.12) per GW.a. The electricity denominator is NOT ambiguous:
    data/activity/electricity_generation.csv holds `elec_gen_coal` for XWL (2010: 8458 TWh,
    2020: 9437 TWh), so the eta = 0.35 fallback is not used.
A7. ZERO-CENTRAL RESIDUE ROWS. The spec writes a row for each tier and residue stream and only
    suppresses the rest-of-world row at exactly zero. Where a zero-central row is written the tests
    check its values; they do not demand that it exists, except for the reisolated bottom-ash rows
    required by (b).
A9-A22: see the v1.2 ambiguity list in the module docstring of the section "COAL_SPEC v1.2 (section 12)"
    below (search for "V1.2 AMBIGUITIES").
A8. `cap_applied` log "bound" is not a named key (section 8 lists kind, year, country, group,
    detail). The bound is looked for in the detail text ("low", "central", "high").
"""
from __future__ import annotations

import csv
import importlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd
import pytest
from coal_oracle import (
    B,
    Oracle,
    bound_min,
    cdiff,
    cdiff_cause,
    diff,
    prod,
    scale,
    sum_correlated,
    sum_independent,
)

# pipeline/tests/streams/test_coal.py -> streams -> tests -> pipeline -> repository root
ROOT = Path(__file__).resolve().parents[3]

WORLD_CODES = ("XWL", "XXX")  # see A1
LOG_KINDS = {"no_factor", "no_driver", "negative_residual", "negative_nonpower_coal",
             "no_power_ash", "cap_applied", "predecessor_dropped", "lib_warning"}
G11 = ["U238+", "U234", "Th230", "Ra226+", "Pb210+", "Po210", "U235+", "Th232", "Ra228+", "Th228+", "K40"]
RESIDUE_TIERS = ["impounded", "reisolated", "dispersed"]
REL = 1e-6

# UNSCEAR 2016 Annex B (S0001), TBq per GW.a, as quoted in COAL_SPEC 9(e).
UNSCEAR = {
    "ra226_ash": (0.060, None),
    "pb210_stack": (1.4e-3, 9.3e-5),
    "ra226_stack": (7e-4, 4.7e-5),
    "rn222_burning": (0.07, None),
    "mine_radon_china_power": (2.8, None),
}


# --------------------------------------------------------------------------------------------
# generic helpers
# --------------------------------------------------------------------------------------------
def _blank(v) -> bool:
    return v is None or v == ""


def ids(v) -> list[str]:
    """Normalise a list-like cell (list, ';'-joined string, None) to a list of strings."""
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


def describe(r: dict) -> str:
    keys = ("year", "substream", "stage", "country", "group", "tier", "residue_type", "route")
    return ", ".join(f"{k}={r.get(k)!r}" for k in keys)


def assert_bounds(row: dict, exp: B, *, flag: bool | None = True, label: str = "", rel: float = REL) -> None:
    """Row value_low / central / high must equal `exp`; below_detection must equal exp.nd unless flag is None."""
    got = (float(row["value_low"]), float(row["value_central"]), float(row["value_high"]))
    want = (exp.low, exp.central, exp.high)
    for name, g, w in zip(("low", "central", "high"), got, want):
        assert close(g, w, rel), (
            f"{label} [{describe(row)}]: value_{name} = {g!r}, hand-computed {w!r} "
            f"(row {got}, expected {want})")
    if flag is not None:
        assert as_bool(row["below_detection"]) == exp.nd, (
            f"{label} [{describe(row)}]: below_detection = {row['below_detection']!r}, expected {exp.nd}")


class Rows:
    """Small query helper over a list of master-row dicts."""

    def __init__(self, rows: list[dict]):
        self.rows = rows
        self.by_year: dict[int, list[dict]] = defaultdict(list)
        for r in rows:
            self.by_year[int(r["year"])].append(r)

    def find(self, year: int | None = None, world: bool | None = None, **kw) -> list[dict]:
        pool = self.rows if year is None else self.by_year.get(year, [])
        out = []
        for r in pool:
            if world is True and r["country"] not in WORLD_CODES:
                continue
            if world is False and r["country"] in WORLD_CODES:
                continue
            ok = True
            for k, v in kw.items():
                rv = r[k]
                if v is None or v == "":
                    if not _blank(rv):
                        ok = False
                        break
                elif rv != v:
                    ok = False
                    break
            if ok:
                out.append(r)
        return out

    def one(self, year: int, world: bool | None = None, **kw) -> dict:
        m = self.find(year, world, **kw)
        assert len(m) == 1, f"expected exactly one row for year={year}, world={world}, {kw}; found {len(m)}"
        return m[0]


def log_entries(log: list[dict], kind: str, **kw) -> list[dict]:
    out = []
    for e in log:
        if e.get("kind") != kind:
            continue
        if all(e.get(k) == v for k, v in kw.items()):
            out.append(e)
    return out


# --------------------------------------------------------------------------------------------
# module-scoped fixtures
# --------------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def coal_mod():
    try:
        return importlib.import_module("pipeline.streams.coal")
    except ImportError as exc:  # expected until the code-writer is done
        pytest.fail(f"cannot import pipeline.streams.coal (COAL_SPEC 1): {type(exc).__name__}: {exc}")


@pytest.fixture(scope="module")
def result(coal_mod):
    assert hasattr(coal_mod, "build"), "pipeline.streams.coal must expose build(root) (COAL_SPEC 1)"
    res = coal_mod.build(ROOT)
    for attr in ("rows", "rows_pre1950", "log"):
        assert hasattr(res, attr), f"BuildResult has no attribute {attr!r} (COAL_SPEC 1)"
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
def write_master():
    return importlib.import_module("pipeline.lib.rows").write_master


@pytest.fixture(scope="module")
def written(result, write_master, tmp_path_factory):
    """Both outputs written with write_master (COAL_SPEC 1)."""
    d = tmp_path_factory.mktemp("coal_written")
    main = d / "coal.csv"
    pre = d / "coal_pre1950.csv"
    write_master(list(result.rows), main)
    write_master(list(result.rows_pre1950), pre)
    return main, pre


def _copy_tree(dst: Path) -> Path:
    """Copy data/ and schema/ (without any existing stream outputs) into dst."""
    shutil.copytree(ROOT / "data", dst / "data",
                    ignore=shutil.ignore_patterns("streams", "streams_pre1950"))
    shutil.copytree(ROOT / "schema", dst / "schema")
    (dst / "data" / "streams").mkdir()
    (dst / "data" / "streams_pre1950").mkdir()
    (dst / "research" / "coal").mkdir(parents=True)
    return dst


# --------------------------------------------------------------------------------------------
# section 3 and 4-6: row conventions
# --------------------------------------------------------------------------------------------
class TestRowConventions:
    def test_rows_are_nonempty_and_dicts(self, rows, pre_rows):
        assert rows.rows, "build().rows is empty"
        assert pre_rows.rows, "build().rows_pre1950 is empty"
        assert all(isinstance(r, dict) for r in rows.rows[:50])

    def test_master_columns_present(self, rows):
        expected = ["year", "stream", "substream", "stage", "product", "residue_type", "country", "group",
                    "tier", "quantity", "unit", "value_low", "value_central", "value_high",
                    "below_detection", "basis", "source_ids", "factor_ids", "allocation_variant",
                    "allocation_rule", "embedded_fuel", "technology", "route", "event_id", "notes"]
        bad = [r for r in rows.rows if list(r.keys()) != expected]
        assert not bad, f"{len(bad)} rows do not have exactly the 25 master columns in order; first: {bad[0]}"

    @pytest.mark.parametrize("which", ["rows", "pre"])
    def test_constant_columns(self, which, rows, pre_rows):
        data = (rows if which == "rows" else pre_rows).rows
        problems = []
        for r in data:
            if r["stream"] != "coal":
                problems.append(("stream", r))
            if r["quantity"] != "flow":
                problems.append(("quantity", r))
            if r["unit"] != "Bq/a":
                problems.append(("unit", r))
            if r["basis"] != "modelled":
                problems.append(("basis", r))
            if r["allocation_variant"] != "default":
                problems.append(("allocation_variant", r))
            if ids(r["allocation_rule"]) != ["none"]:
                problems.append(("allocation_rule", r))
            if as_bool(r["embedded_fuel"]):
                problems.append(("embedded_fuel", r))
            for col in ("product", "technology", "event_id"):
                if not _blank(r[col]):
                    problems.append((col, r))
        assert not problems, f"{len(problems)} convention violations (COAL_SPEC 3); first: {problems[0][0]} in {problems[0][1]}"

    @pytest.mark.parametrize("which", ["rows", "pre"])
    def test_ids_present_and_sorted(self, which, rows, pre_rows):
        data = (rows if which == "rows" else pre_rows).rows
        for r in data:
            f, s = ids(r["factor_ids"]), ids(r["source_ids"])
            assert f, f"factor_ids empty on a modelled row: {describe(r)}"
            assert s, f"source_ids empty: {describe(r)}"
            assert all(x.startswith("coal:") for x in f), f"unexpected factor id in {f}: {describe(r)}"
            assert s == sorted(s), f"source_ids not sorted {s}: {describe(r)}"

    @pytest.mark.parametrize("which", ["rows", "pre"])
    def test_bounds_ordered_and_flag_consistent(self, which, rows, pre_rows):
        data = (rows if which == "rows" else pre_rows).rows
        for r in data:
            lo, c, hi = float(r["value_low"]), float(r["value_central"]), float(r["value_high"])
            assert 0 <= lo <= c <= hi, f"bounds out of order ({lo}, {c}, {hi}): {describe(r)}"
            if as_bool(r["below_detection"]):
                assert lo == 0, f"below_detection true but value_low = {lo}: {describe(r)}"

    @pytest.mark.parametrize("which", ["rows", "pre"])
    def test_stage_substream_tier_route_residue_shapes(self, which, rows, pre_rows):
        """COAL_SPEC 4-6 and SCHEMA 5.3: only the stage/tier/route/residue combinations the spec writes."""
        data = (rows if which == "rows" else pre_rows).rows
        substream = {"coal_mining": "all", "combustion_power": "power", "combustion_nonpower": "non_power"}
        allowed = {
            ("coal_mining", "liberated", "air_ventilation", None),
            ("coal_mining", "liberated", "water_mine_drainage", None),
            ("coal_mining", "impounded", None, "coal_mine_water_sludge"),
            ("combustion_power", "liberated", "air_stack", None),
            ("combustion_nonpower", "liberated", "air_stack", None),
            ("combustion_nonpower", "dispersed", None, "coal_domestic_ash"),
            ("combustion_nonpower", "impounded", None, "coal_bottom_ash"),
        }
        for t in RESIDUE_TIERS:
            allowed.add(("combustion_power", t, None, "coal_fly_ash"))
            allowed.add(("combustion_power", t, None, "coal_bottom_ash"))
        for r in data:
            assert r["stage"] in substream, f"unexpected stage: {describe(r)}"
            assert r["substream"] == substream[r["stage"]], f"wrong substream: {describe(r)}"
            key = (r["stage"], r["tier"], None if _blank(r["route"]) else r["route"],
                   None if _blank(r["residue_type"]) else r["residue_type"])
            assert key in allowed, f"stage/tier/route/residue combination not in COAL_SPEC 4-6: {describe(r)}"

    @pytest.mark.parametrize("which", ["rows", "pre"])
    def test_groups_per_stage(self, which, rows, pre_rows):
        data = (rows if which == "rows" else pre_rows).rows
        by_stage = defaultdict(set)
        for r in data:
            by_stage[(r["stage"], r["tier"] == "liberated")].add(r["group"])
        mining = by_stage[("coal_mining", True)] | by_stage[("coal_mining", False)]
        assert mining <= {"Rn222+", "Ra226+", "Ra228+"}, f"unexpected mining groups {mining}"
        for stage in ("combustion_power", "combustion_nonpower"):
            allg = by_stage[(stage, True)] | by_stage[(stage, False)]
            assert allg <= set(G11) | {"Rn222+", "Rn220+"}, f"unexpected groups at {stage}: {allg}"

    def test_years_within_ranges(self, rows, pre_rows):
        ys = {int(r["year"]) for r in rows.rows}
        assert min(ys) >= 1950 and max(ys) <= 2025, f"rows years {min(ys)}-{max(ys)} outside 1950-2025"
        assert 1950 in ys and 2024 in ys
        yp = {int(r["year"]) for r in pre_rows.rows}
        assert min(yp) >= 1800 and max(yp) <= 1949, f"pre-1950 years {min(yp)}-{max(yp)} outside 1800-1949"

    def test_no_usa_route_shares_in_world_rows(self, rows):
        # D73: coal:0074-0079 retired, coal:0080-0094 live; all are USA-only shares.
        usa = {f"coal:{n:04d}" for n in range(74, 95)}
        bad = [r for r in rows.rows if usa & set(ids(r["factor_ids"]))]
        assert not bad, f"USA-only share factors (coal:0074-0094) used on {len(bad)} rows; first: {describe(bad[0])}"

    def test_unapplied_factors_not_used(self, rows):
        banned = {"coal:0067", "coal:0072", "coal:0073"}
        bad = [r for r in rows.rows if banned & set(ids(r["factor_ids"]))]
        assert not bad, f"coal:0067/0072/0073 must not be applied (COAL_SPEC 6); first: {describe(bad[0])}"


# --------------------------------------------------------------------------------------------
# (a) schema
# --------------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def issues(written):
    from pipeline.validate import validate

    root = _copy_tree(Path(written[0]).parent / "validation_root")
    shutil.copy(written[0], root / "data" / "streams" / "coal.csv")
    found = validate(root, master_files=["data/streams/coal.csv"])
    return [i for i in found if i.file == "data/streams/coal.csv"]


class TestSchema:
    def test_validator_accepts_coal_csv(self, issues):
        shown = "\n".join(f"  row {i.row}: {i.rule} {i.message}" for i in issues[:15])
        assert not issues, (f"data/streams/coal.csv has {len(issues)} validator issues "
                            f"(rules {sorted({i.rule for i in issues})}):\n{shown}")

    @pytest.mark.parametrize("rule", ["V03", "V09", "V15", "V14", "V12", "V13", "V07", "V04", "V05", "V06"])
    def test_no_stage_tier_route_violations(self, issues, rule):
        hits = [i for i in issues if i.rule == rule]
        assert not hits, f"{len(hits)} {rule} issues, first: row {hits[0].row} {hits[0].message}"

    def test_no_xwl_country_in_master_rows(self, issues, rows):
        """SCHEMA 3 / V10: XWL is not allowed in master rows (see A1)."""
        hits = [i for i in issues if i.rule == "V10"]
        assert not hits and not any(r["country"] == "XWL" for r in rows.rows), (
            f"{len(hits)} rows use country XWL, which SCHEMA 3 forbids (use XXX); "
            "COAL_SPEC 4.1/5/6 say XWL, so the spec contradicts the schema (A1)")


# --------------------------------------------------------------------------------------------
# (b) candidate nuclides
# --------------------------------------------------------------------------------------------
class TestCandidateGroups:
    def test_every_group_in_every_ash_tier_every_year(self, rows):
        missing = []
        for y in range(1950, 2026):
            have = {(r["group"], r["tier"]) for r in rows.find(y, stage="combustion_power", residue_type="coal_bottom_ash")}
            for g in G11:
                for t in RESIDUE_TIERS:
                    if (g, t) not in have:
                        missing.append((y, g, t))
        assert not missing, f"{len(missing)} missing (year, group, tier) bottom-ash rows; first: {missing[:5]}"

    def test_every_group_has_stack_release_every_year(self, rows):
        missing = []
        for y in range(1950, 2026):
            have = {r["group"] for r in rows.find(y, stage="combustion_power", tier="liberated", route="air_stack")}
            for g in G11 + ["Rn222+", "Rn220+"]:
                if g not in have:
                    missing.append((y, g))
        assert not missing, f"{len(missing)} missing stack rows (year, group); first: {missing[:5]}"

    def test_eleven_groups_exist_in_flyash_tiers(self, rows):
        for y in (1950, 1975, 2000, 2024, 2025):
            have = {r["group"] for r in rows.find(y, stage="combustion_power", residue_type="coal_fly_ash")}
            assert set(G11) <= have, f"{y}: groups missing from fly-ash rows: {set(G11) - have}"


# --------------------------------------------------------------------------------------------
# (c) conservation
# --------------------------------------------------------------------------------------------
class TestConservation:
    def test_flyash_stack_plus_residue_equals_flyash_activity_central(self, rows, oracle):
        """Central value only (A2)."""
        bad = []
        for y in range(1950, 2026):
            for g in G11:
                F, _ = oracle.F(y, g)
                stack = rows.one(y, world=True, stage="combustion_power", group=g, tier="liberated", route="air_stack")
                resid = sum(float(r["value_central"]) for r in
                            rows.find(y, stage="combustion_power", group=g, residue_type="coal_fly_ash"))
                s = float(stack["value_central"])
                if not close(s + resid, F.central, 1e-6):
                    bad.append((y, g, s, resid, F.central))
                if s > F.central * (1 + 1e-9):
                    bad.append((y, g, "stack exceeds fly-ash activity", s, F.central))
        assert not bad, f"{len(bad)} conservation failures (year, group, stack, residue, F); first: {bad[:3]}"

    def test_tier_shares_sum_back_to_the_residue(self, rows, oracle):
        bad = []
        for y in range(1950, 2026):
            for g in G11:
                stack = rows.one(y, world=True, stage="combustion_power", group=g, tier="liberated", route="air_stack")
                F, _ = oracle.F(y, g)
                Bk, _ = oracle.Bk(y, g)
                fly_resid = F.central - float(stack["value_central"])
                tot_fly = sum(float(r["value_central"]) for r in
                              rows.find(y, stage="combustion_power", group=g, residue_type="coal_fly_ash"))
                tot_bot = sum(float(r["value_central"]) for r in
                              rows.find(y, stage="combustion_power", group=g, residue_type="coal_bottom_ash"))
                if abs(tot_fly - fly_resid) > 1e-9 * F.central:
                    bad.append((y, g, "fly", tot_fly, fly_resid))
                if abs(tot_bot - Bk.central) > 1e-9 * Bk.central:
                    bad.append((y, g, "bottom", tot_bot, Bk.central))
        assert not bad, f"{len(bad)} tier-sum failures (rel 1e-9); first: {bad[:3]}"

    def test_bottom_ash_activity_uses_difference_of_ash_series(self, rows, oracle):
        for y in (1950, 1999, 2020):
            tot, fly, _ = oracle.ash(y)
            _, f = oracle.Bk(y, "Ra226+")
            expected = (tot.central - fly.central) * float(f["value_central"])
            got = sum(float(r["value_central"]) for r in
                      rows.find(y, stage="combustion_power", group="Ra226+", residue_type="coal_bottom_ash"))
            assert close(got, expected, 1e-9), f"{y}: bottom-ash Ra-226 tiers sum to {got}, expected {expected}"

    def test_nonpower_activity_is_partitioned(self, rows, oracle):
        """Smoke + household ash = household activity H and industrial ash = N - H (central, section 6)."""
        for y in (1950, 1980, 2005, 2020):
            for g in ("Ra226+", "Pb210+", "K40"):
                N, _ = oracle.N(y, g)
                total = sum(float(r["value_central"]) for r in
                            rows.find(y, stage="combustion_nonpower", group=g))
                assert close(total, N.central, 1e-9), (
                    f"{y} {g}: non-power rows sum to {total}, expected N = {N.central}")


# --------------------------------------------------------------------------------------------
# (f) hand-computed rows, 2005
# --------------------------------------------------------------------------------------------
class TestHandComputed2005:
    Y = 2005

    # ---- coal_mining -----------------------------------------------------------------------
    def test_china_mine_radon_uses_china_factor(self, rows, oracle):
        f = oracle.select(self.Y, "CHN", stage="coal_mining", group="Rn222+", route="air_ventilation",
                          tier="liberated")
        assert f["factor_id"] == "coal:0002"
        row = rows.one(self.Y, stage="coal_mining", country="CHN", group="Rn222+")
        assert row["tier"] == "liberated" and row["route"] == "air_ventilation" and row["substream"] == "all"
        assert ids(row["factor_ids"]) == ["coal:0002"]
        assert_bounds(row, prod(oracle.a("coal_production_t", self.Y, "CHN"), oracle.fb(f)), label="CHN radon 2005")
        want = oracle.a_sources("coal_production_t", self.Y, "CHN") | oracle.sources_of(f)
        assert ids(row["source_ids"]) == sorted(want)

    def test_china_before_2000_falls_back_to_world_factor(self, rows, oracle):
        y = 1995
        f = oracle.select(y, "CHN", stage="coal_mining", group="Rn222+", route="air_ventilation", tier="liberated")
        assert f["factor_id"] == "coal:0001"
        row = rows.one(y, stage="coal_mining", country="CHN", group="Rn222+")
        assert ids(row["factor_ids"]) == ["coal:0001"]
        assert_bounds(row, prod(oracle.a("coal_production_t", y, "CHN"), oracle.fb(f)), label="CHN radon 1995")

    def test_china_low_bound_differs_from_world_default_in_2005(self, rows, oracle):
        """China-versus-world: the measured row lifts the low bound (1.9e5 against 1.2e4 Bq/t)."""
        chn = rows.one(self.Y, stage="coal_mining", country="CHN", group="Rn222+")
        world = oracle.select(self.Y, "XWL", stage="coal_mining", group="Rn222+", route="air_ventilation")
        world_b = prod(oracle.a("coal_production_t", self.Y, "CHN"), oracle.fb(world))
        assert float(chn["value_low"]) > 5 * world_b.low
        assert close(float(chn["value_central"]), world_b.central)

    def test_other_country_uses_world_default_radon(self, rows, oracle):
        row = rows.one(self.Y, stage="coal_mining", country="USA", group="Rn222+")
        assert ids(row["factor_ids"]) == ["coal:0001"]
        f = oracle.select(self.Y, "USA", stage="coal_mining", group="Rn222+", route="air_ventilation")
        assert_bounds(row, prod(oracle.a("coal_production_t", self.Y, "USA"), oracle.fb(f)), label="USA radon 2005")

    def test_rest_of_world_residual_row(self, rows, oracle):
        y = self.Y
        xwl = oracle.a("coal_production_t", y, "XWL")
        listed = [oracle.a("coal_production_t", y, c) for c in oracle.listed_countries("coal_production_t", y)]
        f = oracle.select(y, "XWL", stage="coal_mining", group="Rn222+", route="air_ventilation")
        row = rows.one(y, world=True, stage="coal_mining", group="Rn222+")
        assert row["tier"] == "liberated" and row["route"] == "air_ventilation"
        assert "rest of world (world aggregate minus listed countries)" in str(row["notes"])
        assert ids(row["factor_ids"]) == ["coal:0001"]
        residual_central = xwl.central - sum(c.central for c in listed)
        assert residual_central > 0
        assert close(float(row["value_central"]), residual_central * float(f["value_central"]), 1e-9)
        # bounds: the sum of the listed countries is not specified (A3); accept either convention
        variants = [prod(diff(xwl, s), oracle.fb(f)) for s in (sum_independent(listed), sum_correlated(listed))]
        got = (float(row["value_low"]), float(row["value_central"]), float(row["value_high"]))
        matches = [all(close(g, w) for g, w in zip(got, (v.low, v.central, v.high))) for v in variants]
        assert any(matches), f"rest-of-world bounds {got} match neither convention {variants}"
        want_flag = next(v.nd for v, m in zip(variants, matches) if m)
        assert as_bool(row["below_detection"]) == want_flag

    def test_listed_countries_have_no_xwl_double_count(self, rows, oracle):
        """Exactly one mine-radon row per listed country with a driver, plus one rest-of-world row."""
        y = self.Y
        radon = rows.find(y, stage="coal_mining", group="Rn222+")
        countries = [r["country"] for r in radon]
        assert len(countries) == len(set(countries)), "duplicate mine-radon countries"
        listed = set(oracle.listed_countries("coal_production_t", y))
        assert listed <= set(countries), f"missing listed countries: {listed - set(countries)}"
        assert len(set(countries) - listed) == 1, "expected one rest-of-world row"

    @pytest.mark.parametrize("group,rel_id,ret_id", [("Ra226+", "coal:0003", "coal:0005"),
                                                     ("Ra228+", "coal:0004", "coal:0006")])
    def test_poland_mine_water_released_and_retained(self, rows, oracle, group, rel_id, ret_id):
        y = self.Y
        frel = oracle.select(y, "POL", stage="coal_mining", group=group, route="water_mine_drainage")
        fret = oracle.select(y, "POL", stage="coal_mining", group=group, residue_type="coal_mine_water_sludge")
        assert frel["factor_id"] == rel_id and fret["factor_id"] == ret_id
        P = oracle.a("coal_production_t", y, "POL")
        released = prod(P, oracle.fb(frel))
        r = oracle.fb(fret)
        ratio = B(r.low / (1 - r.low), r.central / (1 - r.central), r.high / (1 - r.high))

        rel_row = rows.one(y, country="POL", stage="coal_mining", group=group, tier="liberated")
        assert rel_row["route"] == "water_mine_drainage" and _blank(rel_row["residue_type"])
        assert ids(rel_row["factor_ids"]) == [rel_id]
        assert_bounds(rel_row, released, label=f"POL {group} released")

        ret_row = rows.one(y, country="POL", stage="coal_mining", group=group, tier="impounded")
        assert ret_row["residue_type"] == "coal_mine_water_sludge" and _blank(ret_row["route"])
        assert ids(ret_row["factor_ids"]) == [rel_id, ret_id], "release factor then retention factor"
        assert_bounds(ret_row, prod(released, ratio), label=f"POL {group} retained")
        assert close(float(ret_row["value_central"]), float(rel_row["value_central"]) * r.central / (1 - r.central), 1e-9)
        want = oracle.a_sources("coal_production_t", y, "POL") | oracle.sources_of(frel, fret)
        assert ids(ret_row["source_ids"]) == sorted(want)

    def test_poland_only_for_mine_water(self, rows):
        y = self.Y
        water = rows.find(y, stage="coal_mining", route="water_mine_drainage")
        sludge = rows.find(y, stage="coal_mining", residue_type="coal_mine_water_sludge")
        assert {r["country"] for r in water + sludge} == {"POL"}
        assert len(water) == 2 and len(sludge) == 2

    # ---- combustion_power residues -----------------------------------------------------------
    def test_bottom_ash_impounded_ra226(self, rows, oracle):
        y, g = self.Y, "Ra226+"
        Bk, f = oracle.Bk(y, g)
        sh = oracle.share(y, "impounded")
        assert f["factor_id"] == "coal:0014" and sh["factor_id"] == "coal:0043"
        row = rows.one(y, world=True, stage="combustion_power", group=g, tier="impounded", residue_type="coal_bottom_ash")
        assert row["substream"] == "power" and _blank(row["route"])
        assert ids(row["factor_ids"]) == ["coal:0014", "coal:0043"]
        assert_bounds(row, prod(Bk, oracle.fb(sh)), label="bottom ash Ra-226 impounded")
        tot_src = oracle.a_sources("coal_ash_power_t", y, "XWL") | oracle.a_sources("coal_fly_ash_t", y, "XWL")
        assert set(ids(row["source_ids"])) == tot_src | oracle.sources_of(f, sh)
        assert ids(row["source_ids"]) == sorted(ids(row["source_ids"]))

    def test_bottom_ash_reisolated_zero_central_row_is_flagged(self, rows, oracle):
        y, g = self.Y, "Ra226+"
        Bk, _ = oracle.Bk(y, g)
        sh = oracle.share(y, "reisolated")
        assert float(sh["value_central"]) == 0 and float(sh["value_high"]) > 0
        row = rows.one(y, world=True, stage="combustion_power", group=g, tier="reisolated", residue_type="coal_bottom_ash")
        exp = prod(Bk, oracle.fb(sh))
        assert exp.nd and exp.central == 0 and exp.low == 0
        assert_bounds(row, exp, label="bottom ash reisolated (zero central)")
        assert float(row["value_central"]) == 0 and float(row["value_low"]) == 0
        assert as_bool(row["below_detection"]) is True
        assert close(float(row["value_high"]), Bk.high * 0.062)
        assert ids(row["factor_ids"]) == ["coal:0014", "coal:0044"]

    def test_bottom_ash_dispersed_pb210(self, rows, oracle):
        y, g = self.Y, "Pb210+"
        Bk, f = oracle.Bk(y, g)
        sh = oracle.share(y, "dispersed")
        assert f["factor_id"] == "coal:0016" and sh["factor_id"] == "coal:0045"
        row = rows.one(y, world=True, stage="combustion_power", group=g, tier="dispersed", residue_type="coal_bottom_ash")
        assert_bounds(row, prod(Bk, oracle.fb(sh)), label="bottom ash Pb-210 dispersed")

    def test_bottom_ash_rows_use_the_correlated_difference(self, rows, oracle):
        """COAL_SPEC 12.1: A_bot = A_tot - A_fly is a correlated difference (low = l_tot - l_fly)."""
        tot, fly, bot = oracle.ash(self.Y)
        assert bot.low == pytest.approx(tot.low - fly.low), "oracle premise"
        for g in ("Ra226+", "Pb210+", "K40"):
            Bk, _f = oracle.Bk(self.Y, g)
            for tier in ("impounded", "reisolated", "dispersed"):
                sh = oracle.share(self.Y, tier)
                r = rows.one(self.Y, world=True, stage="combustion_power", group=g, tier=tier,
                             residue_type="coal_bottom_ash")
                assert_bounds(r, prod(Bk, oracle.fb(sh)), label=f"bottom ash {g} {tier} (correlated A_bot)")

    def test_stack_and_fly_residue_central_values_pb210(self, rows, oracle):
        y, g = self.Y, "Pb210+"
        F, _ = oracle.F(y, g)
        Bk, _ = oracle.Bk(y, g)
        p = float(oracle.base_fraction(y)["value_central"])
        e = float(oracle.enrichment(y, g)["value_central"])
        S = min(p * e * (F.central + Bk.central), F.central)
        stack = rows.one(y, world=True, stage="combustion_power", group=g, tier="liberated", route="air_stack")
        assert close(float(stack["value_central"]), S, 1e-9)
        assert set(ids(stack["factor_ids"])) >= {oracle.base_fraction(y)["factor_id"],
                                                 oracle.enrichment(y, g)["factor_id"],
                                                 oracle.conc(y, g, "coal_fly_ash")["factor_id"],
                                                 oracle.conc(y, g, "coal_bottom_ash")["factor_id"]}
        fly = rows.one(y, world=True, stage="combustion_power", group=g, tier="impounded", residue_type="coal_fly_ash")
        share = float(oracle.share(y, "impounded")["value_central"])
        assert close(float(fly["value_central"]), (F.central - S) * share, 1e-9)
        assert ids(fly["factor_ids"])[0] == oracle.conc(y, g, "coal_fly_ash")["factor_id"]
        assert oracle.share(y, "impounded")["factor_id"] in ids(fly["factor_ids"])

    def test_stack_radon_central_values(self, rows, oracle):
        y = self.Y
        for group, parent, fid in (("Rn222+", "Ra226+", "coal:0065"), ("Rn220+", "Th228+", "coal:0066")):
            F, _ = oracle.F(y, parent)
            Bk, _ = oracle.Bk(y, parent)
            f = oracle.radon_factor(y, group)
            assert f["factor_id"] == fid
            row = rows.one(y, world=True, stage="combustion_power", group=group)
            assert row["tier"] == "liberated" and row["route"] == "air_stack"
            assert close(float(row["value_central"]), (F.central + Bk.central) * float(f["value_central"]), 1e-9)
            assert fid in ids(row["factor_ids"])

    # ---- combustion_nonpower -----------------------------------------------------------------
    def test_nonpower_coal_is_consumption_minus_power_coal(self, oracle):
        cnp, negative = oracle.nonpower_coal(self.Y)
        assert not negative and cnp.central > 0

    def test_nonpower_smoke_pb210(self, rows, oracle):
        y, g = self.Y, "Pb210+"
        N, f = oracle.N(y, g)
        hs, ss = oracle.household_share(y), oracle.smoke_fraction(y)
        assert hs["factor_id"] == "coal:0069" and ss["factor_id"] == "coal:0071"
        e = oracle.enrichment(y, g)
        H = prod(N, oracle.fb(hs))
        M = bound_min(prod(H, oracle.fb(ss), oracle.fb(e)), H)
        row = rows.one(y, world=True, stage="combustion_nonpower", group=g, tier="liberated")
        assert row["route"] == "air_stack" and row["substream"] == "non_power" and _blank(row["residue_type"])
        assert_bounds(row, M, flag=None, label="non-power smoke Pb-210")
        assert {f["factor_id"], "coal:0069", "coal:0071", e["factor_id"]} <= set(ids(row["factor_ids"]))
        assert ids(row["factor_ids"])[:2] == [f["factor_id"], "coal:0069"], "content factor, then household share"

    def test_nonpower_household_ash_ra226(self, rows, oracle):
        y, g = self.Y, "Ra226+"
        N, _ = oracle.N(y, g)
        H = prod(N, oracle.fb(oracle.household_share(y)))
        M = bound_min(prod(H, oracle.fb(oracle.smoke_fraction(y)), oracle.fb(oracle.enrichment(y, g))), H)
        exp = diff(H, M)
        row = rows.one(y, world=True, stage="combustion_nonpower", group=g, tier="dispersed")
        assert row["residue_type"] == "coal_domestic_ash" and _blank(row["route"])
        assert_bounds(row, exp, flag=None if exp.low == 0 else False, label="household ash Ra-226")

    def test_nonpower_industrial_ash_u238(self, rows, oracle):
        y, g = self.Y, "U238+"
        N, _ = oracle.N(y, g)
        H = prod(N, oracle.fb(oracle.household_share(y)))
        exp = diff(N, H)
        row = rows.one(y, world=True, stage="combustion_nonpower", group=g, tier="impounded")
        assert row["residue_type"] == "coal_bottom_ash" and _blank(row["route"])
        assert_bounds(row, exp, flag=None if exp.low == 0 else False, label="industrial ash U-238")

    @pytest.mark.parametrize("group,parent,fid", [("Rn222+", "Ra226+", "coal:0065"), ("Rn220+", "Th228+", "coal:0066")])
    def test_nonpower_radon(self, rows, oracle, group, parent, fid):
        y = self.Y
        N, nf = oracle.N(y, parent)
        f = oracle.radon_factor(y, group)
        row = rows.one(y, world=True, stage="combustion_nonpower", group=group)
        assert row["tier"] == "liberated" and row["route"] == "air_stack"
        assert ids(row["factor_ids"]) == [nf["factor_id"], fid]
        assert_bounds(row, prod(N, oracle.fb(f)), label=f"non-power {group}")

    def test_nonpower_households_use_xwl_shares_not_usa(self, rows):
        row = rows.one(self.Y, world=True, stage="combustion_nonpower", group="U238+", tier="dispersed")
        assert "coal:0069" in ids(row["factor_ids"])


# --------------------------------------------------------------------------------------------
# (f) cap cases, 1938 (D54; re-anchored from 1960 by D59, when the 1950-69 base fractions fell below the cap)
# --------------------------------------------------------------------------------------------
class TestCapCasesPre1950:
    """Cap cases anchored on 1938. The premise tests derive the binding pattern from the oracle (factor file),
    so a later factor revision fails them loudly instead of silently voiding the cap tests."""
    Y = 1938
    PARTIAL = "Ra226+"   # high bound capped, central not, under both F+B conventions

    def test_premise_holds_for_both_sum_conventions(self, oracle):
        """Po-210 low, central and high are capped whichever way F+B is summed; PARTIAL only at the high bound."""
        F, _ = oracle.F(self.Y, "Po210")
        for v in oracle.stack_variants(self.Y, "Po210"):
            assert v.low > F.low and v.central > F.central and v.high > F.high, (
                f"PREMISE BROKEN (factor file changed?): Po-210 {self.Y} uncapped stack {v} no longer exceeds F {F} at all "
                f"bounds; re-anchor TestCapCasesPre1950.Y on a year where the cap binds")
        Fp, _ = oracle.F(self.Y, self.PARTIAL)
        for v in oracle.stack_variants(self.Y, self.PARTIAL):
            assert v.high > Fp.high and v.central < Fp.central, (
                f"PREMISE BROKEN (factor file changed?): {self.PARTIAL} {self.Y} should be capped at high only; stack {v}, F {Fp}")

    def test_po210_stack_is_capped_at_fly_ash_activity(self, pre_rows, oracle):
        y, g = self.Y, "Po210"
        F, _ = oracle.F(y, g)
        row = pre_rows.one(y, world=True, stage="combustion_power", group=g, tier="liberated", route="air_stack")
        assert close(float(row["value_central"]), F.central, 1e-9), "central must be capped to F"
        assert close(float(row["value_high"]), F.high, 1e-9), "high must be capped to F"
        assert 0 < float(row["value_low"]) <= F.low * (1 + 1e-9)
        assert not as_bool(row["below_detection"])

    def test_po210_fly_residue_has_zero_central(self, pre_rows, oracle):
        """With S = F at the centre the fly-ash residue F - S has central 0 (section 7: zero, not negative)."""
        rs = pre_rows.find(self.Y, world=True, stage="combustion_power", group="Po210", residue_type="coal_fly_ash")
        assert rs, "no Po-210 fly-ash residue rows found"
        for r in rs:
            assert float(r["value_central"]) == 0, f"expected zero-central residue: {describe(r)}"
            if r["tier"] != "reisolated":
                assert as_bool(r["below_detection"]) and float(r["value_low"]) == 0, describe(r)
            # COAL_SPEC 12.16: S = F at all three bounds is a true zero, not a clipped difference
            want = ["zero_central_factor", "exact_zero"] if r["tier"] == "reisolated" else ["exact_zero"]
            assert causes_of(r) == want, f"{describe(r)}: notes {r['notes']!r}, expected causes {want}"

    def test_partial_cap_high_bound_capped_centre_not(self, pre_rows, oracle):
        y, g = self.Y, self.PARTIAL
        F, _ = oracle.F(y, g)
        Bk, _ = oracle.Bk(y, g)
        for v in oracle.stack_variants(y, g):
            assert v.high > F.high and v.central < F.central, "premise of the partial-cap case"
        p = float(oracle.base_fraction(y)["value_central"])
        e = float(oracle.enrichment(y, g)["value_central"])
        row = pre_rows.one(y, world=True, stage="combustion_power", group=g, tier="liberated", route="air_stack")
        assert close(float(row["value_central"]), p * e * (F.central + Bk.central), 1e-9)
        assert close(float(row["value_high"]), F.high, 1e-9)

    def test_cap_applied_is_logged_per_bound(self, log):
        po = [e for e in log_entries(log, "cap_applied", year=self.Y, group="Po210")]
        text = " ".join(str(e.get("detail", "")).lower() for e in po)
        assert len(po) >= 2 and "central" in text and "high" in text, (
            f"Po-210 {self.Y}: expected cap_applied entries for at least the central and high bounds, got {po}")
        pb = log_entries(log, "cap_applied", year=self.Y, group=self.PARTIAL)
        assert pb and "high" in " ".join(str(e.get("detail", "")).lower() for e in pb), (
            f"{self.PARTIAL} {self.Y}: expected a cap_applied entry naming the high bound, got {pb}")
        assert "central" not in " ".join(str(e.get("detail", "")).lower() for e in pb)

    def test_no_cap_logged_where_stack_is_far_below_fly_ash(self, log):
        assert not log_entries(log, "cap_applied", year=2005, group="Ra226+")


# --------------------------------------------------------------------------------------------
# (e) benchmarks (D51)
# --------------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def electricity():
    e = pd.read_csv(ROOT / "data" / "activity" / "electricity_generation.csv", dtype=str, keep_default_na=False)
    e = e[(e["series"] == "elec_gen_coal") & (e["country"] == "XWL")]
    return {int(r["year"]): float(r["value_central"]) for r in e.to_dict("records")}


def _sum(rows: Rows, y: int, **kw) -> float:
    return sum(float(r["value_central"]) for r in rows.find(y, **kw))


@pytest.fixture(scope="module")
def table(rows, oracle, electricity):
    out = {}
    for y in (2010, 2020):
        twh = electricity[y]
        gwa = twh / 8.766
        tb = 1e12 * gwa
        ra_ash = _sum(rows, y, stage="combustion_power", group="Ra226+") - _sum(
            rows, y, stage="combustion_power", group="Ra226+", tier="liberated")
        chn = rows.one(y, stage="coal_mining", country="CHN", group="Rn222+")
        per_t = float(chn["value_central"]) / oracle.a("coal_production_t", y, "CHN").central
        power_coal = oracle.a("coal_ash_power_t", y, "XWL").central / 0.12
        out[y] = {
            "gwa": gwa,
            "ra226_ash": ra_ash / tb,
            "pb210_stack": _sum(rows, y, stage="combustion_power", group="Pb210+", tier="liberated",
                                     route="air_stack") / tb,
            "ra226_stack": _sum(rows, y, stage="combustion_power", group="Ra226+", tier="liberated",
                                     route="air_stack") / tb,
            "rn222_burning": _sum(rows, y, stage="combustion_power", group="Rn222+", tier="liberated",
                                       route="air_stack") / tb,
            "mine_radon_china_power": per_t * power_coal / tb,
        }
    return out



class TestBenchmarks:
    def test_denominator_series_exists(self, electricity):
        """A6: elec_gen_coal / XWL is present, so the eta = 0.35 fallback is not needed."""
        for y in (2010, 2020):
            assert y in electricity and electricity[y] > 5000, f"no usable coal electricity for {y}"

    @pytest.mark.parametrize("year", [2010, 2020])
    @pytest.mark.parametrize("name", list(UNSCEAR))
    def test_within_factor_three_of_unscear(self, table, year, name):
        older, modern = UNSCEAR[name]
        x = table[year][name]
        ok = older / 3 <= x <= older * 3
        if modern is not None:
            ok = ok or (modern <= x <= older)
        assert ok, (f"{name} {year}: output gives {x:.3e} TBq per GW.a (denominator {table[year]['gwa']:.1f} GW.a = "
                    f"elec_gen_coal / 8.766); UNSCEAR 2016 Annex B quotes {older}"
                    + (f" (older) / {modern} (modern)" if modern else "") + "; allowed within a factor of 3")


# --------------------------------------------------------------------------------------------
# (d) determinism
# --------------------------------------------------------------------------------------------
class TestDeterminism:
    def test_two_builds_write_identical_bytes(self, coal_mod, written, write_master, tmp_path):
        second = coal_mod.build(ROOT)
        m2, p2 = tmp_path / "coal2.csv", tmp_path / "pre2.csv"
        write_master(list(second.rows), m2)
        write_master(list(second.rows_pre1950), p2)
        assert Path(written[0]).read_bytes() == m2.read_bytes(), "data/streams/coal.csv bytes differ between builds"
        assert Path(written[1]).read_bytes() == p2.read_bytes(), "pre-1950 bytes differ between builds"

    @pytest.mark.parametrize("idx", [0, 1])
    def test_written_rows_are_in_schema_key_order(self, written, idx):
        with open(written[idx], newline="", encoding="utf-8") as fh:
            data = list(csv.DictReader(fh))
        assert data, "empty output file"
        cols = ["year", "stream", "substream", "stage", "product", "residue_type", "country", "group", "tier",
                "quantity", "allocation_variant", "embedded_fuel", "technology", "route", "event_id"]

        def key(r):
            return tuple((int(r[c]),) if c == "year" else ((0, "") if r[c] == "" else (1, r[c])) for c in cols)

        keys = [key(r) for r in data]
        assert keys == sorted(keys), "rows are not in SCHEMA 3 unique-key order"
        assert len(keys) == len(set(keys)), "duplicate unique keys in output"

    def test_cli_write_and_diff(self, written, tmp_path):
        root = _copy_tree(tmp_path / "cli_root")
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
        cmd = [sys.executable, "-m", "pipeline.streams.coal", "--root", str(root)]

        w = subprocess.run(cmd + ["--write"], cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=900, check=False)
        assert w.returncode == 0, f"--write exited {w.returncode}\nstdout: {w.stdout[-800:]}\nstderr: {w.stderr[-1500:]}"
        out_main = root / "data" / "streams" / "coal.csv"
        out_pre = root / "data" / "streams_pre1950" / "coal.csv"
        assert out_main.read_bytes() == Path(written[0]).read_bytes(), "CLI output differs from build() + write_master"
        assert out_pre.read_bytes() == Path(written[1]).read_bytes()
        assert (root / "research" / "coal" / "build_log.csv").is_file(), "--write must write research/coal/build_log.csv"

        d = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=900, check=False)
        assert d.returncode == 0, f"diff run on identical files exited {d.returncode}\n{d.stderr[-800:]}"

        text = out_main.read_text(encoding="utf-8")
        out_main.write_text(text.replace("coal,all", "coal,al1", 1), encoding="utf-8", newline="\n")
        t = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=900, check=False)
        assert t.returncode != 0, "without --write a differing committed file must give a non-zero exit"
        assert out_main.read_text(encoding="utf-8") != text, "the diff run must not overwrite files"


# --------------------------------------------------------------------------------------------
# (h) pre-1950 file
# --------------------------------------------------------------------------------------------
class TestPre1950:
    def test_years_and_quantity(self, pre_rows):
        ys = sorted({int(r["year"]) for r in pre_rows.rows})
        assert ys[0] == 1800 and ys[-1] == 1949, f"pre-1950 rows span {ys[0]}-{ys[-1]}, expected 1800-1949"
        assert all(r["quantity"] == "flow" for r in pre_rows.rows)
        assert not any(str(r["tier"]).startswith("memo_") for r in pre_rows.rows)

    def test_ash_based_rows_begin_in_1900(self, pre_rows):
        power = [int(r["year"]) for r in pre_rows.rows if r["stage"] == "combustion_power"]
        assert power and min(power) == 1900, f"combustion_power rows begin in {min(power) if power else None}, expected 1900"
        assert set(range(1900, 1950)) <= set(power)
        nonpower_early = {int(r["year"]) for r in pre_rows.rows if r["stage"] == "combustion_nonpower" and int(r["year"]) < 1900}
        assert 1800 in nonpower_early and 1890 in nonpower_early, (
            "coal-content rows must start in 1800 (no ash needed); XWL consumption is decadal before 1900")

    def test_pre_1900_nonpower_equals_consumption(self, pre_rows, oracle):
        """No ash series before 1900: power coal is 0, so C_np = C_XWL (section 6.1)."""
        y, g = 1850, "Ra226+"
        assert oracle.has("coal_consumption_t", y, "XWL")
        N, f = oracle.N(y, g)
        assert close(N.central, oracle.a("coal_consumption_t", y, "XWL").central * float(f["value_central"]), 1e-12)
        total = sum(float(r["value_central"]) for r in pre_rows.find(y, stage="combustion_nonpower", group=g))
        assert close(total, N.central, 1e-9)

    def test_same_code_path_as_post_1950(self, rows, pre_rows):
        def shape(rs):
            return {(r["substream"], r["stage"], r["group"], r["tier"], r["route"] or "", r["residue_type"] or "")
                    for r in rs}
        assert shape(pre_rows.find(1949)) == shape(rows.find(1950)), (
            "row shapes differ between 1949 and 1950 (pre-1950 must use the same code path)")

    def test_pre1950_uses_era_factors(self, pre_rows, oracle):
        y = 1930
        p = oracle.base_fraction(y)
        assert p["factor_id"] == "coal:0049"
        row = pre_rows.one(y, world=True, stage="combustion_power", group="Ra226+", tier="liberated", route="air_stack")
        assert p["factor_id"] in ids(row["factor_ids"])
        h = oracle.household_share(1900)
        assert h["factor_id"] == "coal:0068"
        r2 = pre_rows.one(1900, world=True, stage="combustion_nonpower", group="Ra226+", tier="dispersed")
        assert "coal:0068" in ids(r2["factor_ids"])

    def test_written_file_validates_with_relaxed_year_bounds(self, written):
        from jsonschema import Draft7Validator

        schema = json.loads((ROOT / "schema" / "master.json").read_text(encoding="utf-8"))
        schema["properties"]["year"]["minimum"] = 1800
        schema["properties"]["year"]["maximum"] = 1949
        validator = Draft7Validator(schema)
        with open(written[1], newline="", encoding="utf-8") as fh:
            data = list(csv.DictReader(fh))
        assert data
        errors = []
        for i, raw in enumerate(data, start=1):
            rec = {
                "year": int(raw["year"]),
                **{k: raw[k] for k in ("stream", "substream", "stage", "country", "group", "tier", "quantity",
                                        "unit", "basis", "allocation_variant", "allocation_rule")},
                **{k: (raw[k] or None) for k in ("product", "residue_type", "technology", "route", "event_id", "notes")},
                "value_low": float(raw["value_low"]), "value_central": float(raw["value_central"]),
                "value_high": float(raw["value_high"]),
                "below_detection": raw["below_detection"] == "true",
                "embedded_fuel": raw["embedded_fuel"] == "true",
                "source_ids": raw["source_ids"].split(";") if raw["source_ids"] else [],
                "factor_ids": raw["factor_ids"].split(";") if raw["factor_ids"] else None,
            }
            for err in validator.iter_errors(rec):
                errors.append((i, err.message))
                break
            if len(errors) > 5:
                break
        assert not errors, f"pre-1950 rows fail schema/master.json (years relaxed): {errors}"


# --------------------------------------------------------------------------------------------
# section 8: log
# --------------------------------------------------------------------------------------------
class TestLog:
    def test_log_shape(self, log):
        assert isinstance(log, list)
        for e in log[:2000]:
            assert isinstance(e, dict)
            assert {"kind", "year", "country", "group", "detail"} <= set(e), f"log entry lacks required keys: {e}"
            assert e["kind"] in LOG_KINDS, f"unknown log kind {e['kind']!r}"

    def test_negative_residual_logged_exactly_in_years_where_residual_is_negative(self, log, oracle):
        expected = set()
        for y in range(1800, 2026):
            if not oracle.has("coal_production_t", y, "XWL"):
                continue
            listed = [oracle.a("coal_production_t", y, c) for c in oracle.listed_countries("coal_production_t", y)]
            if oracle.a("coal_production_t", y, "XWL").central - sum(c.central for c in listed) < 0:
                expected.add(y)
        # COAL_SPEC 12.2: with CZE dropped where CSK is present, 1991 is no longer negative
        assert 1991 not in expected and expected, "oracle premise: only the early GBR-only years remain negative"
        got = {e["year"] for e in log_entries(log, "negative_residual")}
        assert got == expected, f"negative_residual logged for {sorted(got)}, expected {sorted(expected)}"
        assert all(str(e["detail"]).strip() for e in log_entries(log, "negative_residual")), "detail must give the magnitude"

    def test_no_rest_of_world_row_when_residual_negative(self, rows, pre_rows, oracle):
        # COAL_SPEC 12.2: 1991 is no longer negative; test every year the oracle finds negative.
        negative = []
        for y in range(1800, 2026):
            if not oracle.has("coal_production_t", y, "XWL"):
                continue
            listed = [oracle.a("coal_production_t", y, c) for c in oracle.listed_countries("coal_production_t", y)]
            if oracle.a("coal_production_t", y, "XWL").central - sum(c.central for c in listed) < 0:
                negative.append(y)
        assert negative, "oracle premise: some early years are negative"
        # non-vacuity: the finder does see rest-of-world rows in a positive pre-1950 year
        assert pre_rows.find(1900, world=True, stage="coal_mining"), "expected a rest-of-world row in 1900"
        for y in negative:
            src = rows if y >= 1950 else pre_rows
            assert not src.find(y, world=True, stage="coal_mining"), f"rest-of-world row in negative year {y}"

    def test_no_power_ash_logged_before_1900_only(self, log):
        """COAL_SPEC 12.5: aggregated as one entry per contiguous run (see TestV12LogAggregation)."""
        entries = log_entries(log, "no_power_ash")
        assert entries, "no no_power_ash entry"
        assert 1800 in {e["year"] for e in entries}
        assert all(e["year"] < 1900 for e in entries), (
            f"no_power_ash logged for years >= 1900: {[e['year'] for e in entries if e['year'] >= 1900][:5]}")

    def test_no_factor_logged_for_poland_before_1985(self, log):
        assert log_entries(log, "no_factor", year=1960, country="POL"), "POL has no mine-water factor in 1960"

    def test_no_negative_nonpower_coal_in_real_data(self, log, oracle):
        expected = {y for y in range(1800, 2025) if oracle.has("coal_consumption_t", y, "XWL") and oracle.nonpower_coal(y)[1]}
        got = {e["year"] for e in log_entries(log, "negative_nonpower_coal")}
        assert got == expected


# --------------------------------------------------------------------------------------------
# (g) fixture tests on a miniature tree
# --------------------------------------------------------------------------------------------
ACT_COLUMNS = ["series", "year", "country", "value_low", "value_central", "value_high", "unit",
               "below_detection", "basis", "source_ids", "notes"]
MINI_YEARS = [1960, 2003, 2004, 2005, 2012]


def _act(series: str, year: int, country: str, central: float, band: float = 0.1) -> dict:
    return {"series": series, "year": year, "country": country,
            "value_low": central * (1 - band), "value_central": central, "value_high": central * (1 + band),
            "unit": "TWh" if series.endswith("_twh") else "t", "below_detection": "false", "basis": "measured",
            "source_ids": "S0804", "notes": ""}


def mini_activity(*, xwl_prod: dict | None = None, consumption: dict | None = None) -> list[dict]:
    xwl_prod = {1960: 2.0e8, 2003: 1.5e8, 2004: 1.4e8, 2005: 2.0e8, 2012: 2.0e8, **(xwl_prod or {})}
    consumption = {y: 2.0e8 for y in MINI_YEARS} | (consumption or {})
    out = []
    for y in MINI_YEARS:
        out += [_act("coal_production_t", y, "CHN", 1.0e8), _act("coal_production_t", y, "POL", 5.0e7),
                _act("coal_production_t", y, "XWL", xwl_prod[y]),
                _act("coal_consumption_t", y, "XWL", consumption[y]),
                _act("coal_ash_power_t", y, "XWL", 1.0e7), _act("coal_fly_ash_t", y, "XWL", 8.0e6),
                _act("coal_burn_power_twh", y, "XWL", 5.0e4)]
    return out


def make_mini(tmp_path: Path, act_rows: list[dict], factor_edit=None) -> Path:
    root = tmp_path / "mini"
    (root / "data" / "activity").mkdir(parents=True)
    (root / "data" / "factors").mkdir(parents=True)
    shutil.copytree(ROOT / "data" / "reference", root / "data" / "reference")
    shutil.copy(ROOT / "data" / "sources.csv", root / "data" / "sources.csv")
    with open(root / "data" / "activity" / "coal.csv", "w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=ACT_COLUMNS)
        w.writeheader()
        w.writerows(act_rows)
    fac = pd.read_csv(ROOT / "data" / "factors" / "coal.csv", dtype=str, keep_default_na=False)
    records = fac.to_dict("records")
    if factor_edit:
        records = factor_edit(records)
    with open(root / "data" / "factors" / "coal.csv", "w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(fac.columns))
        w.writeheader()
        w.writerows(records)
    return root


def _build_mini(coal_mod, tmp_path, act_rows, factor_edit=None):
    root = make_mini(tmp_path, act_rows, factor_edit)
    res = coal_mod.build(root)
    return root, res, Rows(list(res.rows)), list(res.log)


class TestMiniTreeResiduals:
    def test_zero_negative_and_positive_residual(self, coal_mod, tmp_path):
        _, _, rows, log = _build_mini(coal_mod, tmp_path, mini_activity())
        # 2003: 1.5e8 - (1.0e8 + 5.0e7) = 0 exactly -> no row, nothing logged
        assert not rows.find(2003, world=True, stage="coal_mining")
        assert not log_entries(log, "negative_residual", year=2003)
        # 2004: 1.4e8 - 1.5e8 < 0 -> treated as 0, logged with its magnitude, no row
        assert not rows.find(2004, world=True, stage="coal_mining")
        neg = log_entries(log, "negative_residual", year=2004)
        assert len(neg) == 1 and str(neg[0]["detail"]).strip()
        # 2005: 2.0e8 - 1.5e8 = 5.0e7 -> one rest-of-world row
        row = rows.one(2005, world=True, stage="coal_mining", group="Rn222+")
        assert close(float(row["value_central"]), 5.0e7 * 930000, 1e-9)
        assert "rest of world (world aggregate minus listed countries)" in str(row["notes"])
        assert not log_entries(log, "negative_residual", year=2005)
        # listed countries are unaffected
        assert close(float(rows.one(2004, stage="coal_mining", country="CHN", group="Rn222+")["value_central"]),
                     1.0e8 * 930000, 1e-9)

    def test_negative_nonpower_coal(self, coal_mod, tmp_path):
        # 2004: consumption 5e7 t < power coal 1e7 / 0.12 = 8.33e7 t
        _, _, rows, log = _build_mini(coal_mod, tmp_path, mini_activity(consumption={2004: 5.0e7}))
        entries = log_entries(log, "negative_nonpower_coal", year=2004)
        assert len(entries) >= 1, "negative non-power coal must be logged"
        assert not log_entries(log, "negative_nonpower_coal", year=2005)
        assert all(float(r["value_central"]) == 0 for r in rows.find(2004, stage="combustion_nonpower")), (
            "non-power coal below 0 is set to 0, so no non-power row may carry activity")
        assert any(float(r["value_central"]) > 0 for r in rows.find(2005, stage="combustion_nonpower"))

    def test_nonpower_coal_value_in_mini_tree(self, coal_mod, tmp_path):
        root, _, rows, _ = _build_mini(coal_mod, tmp_path, mini_activity())
        o = Oracle(root)
        N, f = o.N(2005, "Ra226+")
        assert close(N.central, (2.0e8 - 1.0e7 / 0.12) * float(f["value_central"]), 1e-12)
        total = sum(float(r["value_central"]) for r in rows.find(2005, stage="combustion_nonpower", group="Ra226+"))
        assert close(total, N.central, 1e-9)


class TestMiniTreeMissing:
    def test_missing_polish_factor(self, coal_mod, tmp_path):
        def edit(records):
            out = []
            for r in records:
                if r["factor_id"] == "coal:0004":
                    continue  # Ra-228 drainage factor absent in every year
                if r["factor_id"] == "coal:0003":
                    r = {**r, "year_from": "2005"}  # Ra-226 only from 2005
                out.append(r)
            return out

        _, _, rows, log = _build_mini(coal_mod, tmp_path, mini_activity(), edit)
        for y in (2003, 2004):
            assert not rows.find(y, country="POL", group="Ra226+"), f"POL Ra-226 rows in {y} despite no factor"
            assert log_entries(log, "no_factor", year=y, country="POL"), f"no_factor not logged for POL {y}"
        assert len(rows.find(2005, country="POL", group="Ra226+", tier="liberated", route="water_mine_drainage")) == 1
        assert len(rows.find(2005, country="POL", group="Ra226+", tier="impounded")) == 1
        for y in (2003, 2004, 2005, 2012):
            assert not rows.find(y, country="POL", group="Ra228+"), f"POL Ra-228 rows in {y} despite no factor"
        assert log_entries(log, "no_factor", year=2005, country="POL"), "missing Ra-228 factor must be logged for 2005"
        # the rest of the build still ran
        assert rows.find(2005, country="POL", group="Rn222+") and rows.find(2005, stage="combustion_power")

    def test_missing_mine_water_only_for_poland(self, coal_mod, tmp_path):
        _, _, rows, _ = _build_mini(coal_mod, tmp_path, mini_activity())
        others = [r for r in rows.rows if r["stage"] == "coal_mining" and r["country"] != "POL"
                  and (r["route"] == "water_mine_drainage" or r["residue_type"] == "coal_mine_water_sludge")]
        assert not others

    def test_missing_driver_year_for_a_country(self, coal_mod, tmp_path):
        act = [a for a in mini_activity() if not (a["series"] == "coal_production_t" and a["country"] == "CHN"
                                                  and a["year"] == 2004)]
        _, _, rows, log = _build_mini(coal_mod, tmp_path, act)
        assert not rows.find(2004, stage="coal_mining", country="CHN")
        assert log_entries(log, "no_driver", year=2004, country="CHN"), "missing CHN 2004 driver must be logged"
        assert rows.find(2003, stage="coal_mining", country="CHN") and rows.find(2005, stage="coal_mining", country="CHN")

    def test_missing_ash_driver_year(self, coal_mod, tmp_path):
        act = [a for a in mini_activity() if not (a["series"] == "coal_fly_ash_t" and a["year"] == 2004)]
        _, _, rows, log = _build_mini(coal_mod, tmp_path, act)
        assert not rows.find(2004, stage="combustion_power"), "no fly-ash driver: no combustion_power rows"
        assert log_entries(log, "no_driver", year=2004), "missing driver year must be logged"
        assert rows.find(2003, stage="combustion_power") and rows.find(2005, stage="combustion_power")


class TestMiniTreeCapAndShares:
    def test_cap_is_logged_and_applied(self, coal_mod, tmp_path):
        Y = TestCapCasesPre1950.Y  # pre-1950: the cap binds at every bound for Po-210 (D59)
        act = mini_activity() + [_act("coal_production_t", Y, "CHN", 1.0e8), _act("coal_production_t", Y, "POL", 5.0e7),
                                 _act("coal_production_t", Y, "XWL", 2.0e8), _act("coal_consumption_t", Y, "XWL", 2.0e8),
                                 _act("coal_ash_power_t", Y, "XWL", 1.0e7), _act("coal_fly_ash_t", Y, "XWL", 8.0e6),
                                 _act("coal_burn_power_twh", Y, "XWL", 5.0e4)]
        root, res, _, log = _build_mini(coal_mod, tmp_path, act)
        pre = Rows(list(res.rows_pre1950))
        o = Oracle(root)
        F, _ = o.F(Y, "Po210")
        for v in o.stack_variants(Y, "Po210"):
            assert v.central > F.central and v.high > F.high, (
                f"PREMISE BROKEN (factor file changed?): Po-210 {Y} mini-tree stack {v} not above F {F}; pick a year where the cap binds")
        stack = pre.one(Y, world=True, stage="combustion_power", group="Po210", tier="liberated", route="air_stack")
        assert close(float(stack["value_central"]), F.central, 1e-9)
        assert close(float(stack["value_high"]), F.high, 1e-9)
        entries = log_entries(log, "cap_applied", year=Y, group="Po210")
        text = " ".join(str(e["detail"]).lower() for e in entries)
        assert len(entries) >= 2 and "central" in text and "high" in text, f"cap log: {entries}"
        assert not log_entries(log, "cap_applied", year=2005, group="Ra226+")
        assert not log_entries(log, "cap_applied", year=2005, group="U238+")

    def test_usa_shares_not_used_for_world_rows(self, coal_mod, tmp_path):
        root, _, rows, _ = _build_mini(coal_mod, tmp_path, mini_activity())
        o = Oracle(root)
        y, g = 2012, "Ra226+"
        Bk, _ = o.Bk(y, g)
        xwl_share = o.share(y, "impounded")
        assert xwl_share["factor_id"] == "coal:0046"
        row = rows.one(y, world=True, stage="combustion_power", group=g, tier="impounded", residue_type="coal_bottom_ash")
        assert close(float(row["value_central"]), Bk.central * 0.468, 1e-9), "XWL share 0.468, not the USA 0.592 (coal:0089)"
        assert "coal:0046" in ids(row["factor_ids"])
        usa = {f"coal:{n:04d}" for n in range(74, 95)}  # D73: retired 0074-0079 and live 0080-0094
        assert not any(usa & set(ids(r["factor_ids"])) for r in rows.rows)

    def test_usa_share_edit_does_not_change_world_rows(self, coal_mod, tmp_path):
        def edit(records):
            # D73: edit every live USA share (coal:0080-0094), which covers all mini-tree years.
            live_usa = {f"coal:{n:04d}" for n in range(80, 95)}
            return [{**r, "value_central": "0.5", "value_low": "0.4", "value_high": "0.6"} if r["factor_id"] in live_usa else r
                    for r in records]
        _, _, base, _ = _build_mini(coal_mod, tmp_path / "a", mini_activity())
        _, _, edited, _ = _build_mini(coal_mod, tmp_path / "b", mini_activity(), edit)
        assert [(r["value_low"], r["value_central"], r["value_high"]) for r in base.rows] == [
            (r["value_low"], r["value_central"], r["value_high"]) for r in edited.rows]


# ============================================================================================
# COAL_SPEC v1.2 (section 12)
# ============================================================================================
"""
V1.2 AMBIGUITIES (tests take the most defensible reading; each is listed in the hand-off report)
------------------------------------------------------------------------------------------------
A9.  12.1 "the three values are then ordered": clamp around the central or sort? They differ only when
     l_a-l_b > c or h_a-h_b < c. Tests assert only 0 <= low <= c <= high there, and use
     unambiguous cases for exact bounds. The signature of `_correlated_difference` is assumed to be
     (a: Bounds, b: Bounds) -> Bounds (a tuple whose first element is the Bounds is also accepted).
A10. 12.1 does not say whether the household-ash (H-M) and industrial-ash (N-H) differences of section 6
     use the independent or the correlated form. Those existing tests are left unchanged (independent).
A11. 12.3: a flagged ACTIVITY input (below_detection true) is read as `inherited_flag`.
A12. 12.3/12.4: the order of the `driver basis` suffix and the `below_detection cause` suffix is not given;
     the cause suffix is required to be last ("ends its notes"), the driver suffix to be present before it.
     When both bases occur the `+` order is not fixed; tests compare sets.
A13. 12.5 `detail` of aggregated entries is `first-last (n years)`; a one-year run is accepted as
     `(1 year)` or `(1 years)`.
A14. 12.5 does not give the country code of an aggregated entry (XWL or XXX); tests do not constrain it
     except where a listed country (CHN, CZE) is the key.
A15. 12.10 "ash per GW.a" is tested within a factor of 3 only (the text calls 0.808 Mt an upper bound but
     the rule given is the factor-3 rule). The era check uses the 1970-89 base fraction (coal:0051)
     with the enrichment and the 2010 F+B central values.
A16. 12.2 does not say whether `predecessor_dropped` carries a group; only kind, year, country and the
     word CSK in the detail are checked.
A17. 12.3 `floor_dominance` versus `inherited_flag` when both could apply: inherited wins (the text says
     floor_dominance means "no other cause").
A18. 12.8 the CLI diff of the pre-1950 file is also expected to give a non-zero exit (section 1, not
     repeated in 12.8).
"""
from pipeline.lib import LibError
from pipeline.lib.bounds import Bounds

CAUSE_ORDER = ["zero_central_factor", "exact_zero", "clipped_difference", "floor_dominance", "inherited_flag"]  # 12.16
CAUSE_RE = re.compile(r"; below_detection cause: ([a-z_]+(?:\+[a-z_]+)*)\s*$")
BASIS_RE = re.compile(r"; driver basis: (interpolated|extrapolated)(?:\+(interpolated|extrapolated))?")
RUN_RE = re.compile(r"^(\d{4})-(\d{4}) \((\d+) years?\)")


def causes_of(row: dict):
    m = CAUSE_RE.search(str(row["notes"] or ""))
    return m.group(1).split("+") if m else None


def basis_set(row: dict) -> set[str]:
    m = BASIS_RE.search(str(row["notes"] or ""))
    return {g for g in m.groups() if g} if m else set()


def edit_act(act: list[dict], *, series=None, country=None, year=None, **fields) -> list[dict]:
    out = []
    for a in act:
        if ((series is None or a["series"] == series) and (country is None or a["country"] == country)
                and (year is None or a["year"] == year)):
            a = {**a, **fields}
        out.append(a)
    return out


def drop_act(act: list[dict], *, series=None, country=None, year=None) -> list[dict]:
    return [a for a in act if not ((series is None or a["series"] == series)
                                   and (country is None or a["country"] == country)
                                   and (year is None or a["year"] == year))]


def band(act, series, year, low, central, high, country="XWL", **extra):
    return edit_act(act, series=series, country=country, year=year,
                    value_low=low, value_central=central, value_high=high, **extra)


@pytest.fixture(scope="module")
def mini_base(coal_mod, tmp_path_factory):
    root = make_mini(tmp_path_factory.mktemp("mini_base"), mini_activity())
    res = coal_mod.build(root)
    return root, Rows(list(res.rows)), list(res.log), Oracle(root)


def _bounds_close(row, exp: B, rel=1e-6):
    got = (float(row["value_low"]), float(row["value_central"]), float(row["value_high"]))
    return all(close(g, w, rel) for g, w in zip(got, (exp.low, exp.central, exp.high)))


# --------------------------------------------------------------------------------------------
# 12.1 correlated difference
# --------------------------------------------------------------------------------------------
@pytest.fixture
def fn(coal_mod):
    f = getattr(coal_mod, "_correlated_difference", None)
    assert f is not None, "pipeline.streams.coal._correlated_difference missing (COAL_SPEC 12.1)"

    def call(a, b):
        r = f(a, b)
        return r[0] if isinstance(r, tuple) else r
    return call


class TestV12CorrelatedDifferenceHelper:
    def test_low_high_are_differences_of_bounds(self, fn):
        r = fn(Bounds(8.0, 10.0, 12.0), Bounds(1.0, 3.0, 4.0))
        assert (r.low, r.central, r.high) == pytest.approx((7.0, 7.0, 8.0)), (
            f"correlated difference of (8,10,12)-(1,3,4) must be (7,7,8); got {r}")
        assert r.nd_floored is False, "a difference whose low is positive is unflagged (COAL_SPEC 11.4)"

    def test_differs_from_independent_difference(self, fn):
        # independent (section 7) would give low = 7 - sqrt(2^2 + 1^2) = 4.76
        r = fn(Bounds(8.0, 10.0, 12.0), Bounds(1.0, 3.0, 4.0))
        assert r.low > 6.9, f"low {r.low} looks like the independent form"

    def test_clipped_low_sets_nd_floored(self, fn):
        r = fn(Bounds(2.0, 10.0, 12.0), Bounds(5.0, 6.0, 7.0))  # l_a - l_b = -3
        assert r.low == 0 and r.central == pytest.approx(4.0) and r.high == pytest.approx(5.0)
        assert r.nd_floored is True, "a clipped low must set nd_floored (COAL_SPEC 12.1, 11.4)"

    def test_low_exactly_zero_is_not_a_clip_but_is_valid(self, fn):
        r = fn(Bounds(5.0, 10.0, 12.0), Bounds(5.0, 6.0, 7.0))
        assert r.low == 0 and r.central == pytest.approx(4.0) and r.high == pytest.approx(5.0)

    def test_negative_central_is_set_to_zero(self, fn):
        r = fn(Bounds(1.0, 2.0, 3.0), Bounds(2.0, 5.0, 6.0))
        assert (r.low, r.central, r.high) == (0.0, 0.0, 0.0)
        assert r.nd_floored is True

    @pytest.mark.parametrize("a,b", [
        ((8, 10, 12), (1, 3, 4)), ((2, 10, 12), (5, 6, 7)), ((9, 10, 11), (7, 9.5, 12)),
        ((1, 2, 3), (2, 5, 6)), ((0, 10, 20), (0, 4, 30)), ((5, 10, 15), (7, 8, 9)),
    ])
    def test_result_is_ordered_and_non_negative(self, fn, a, b):
        r = fn(Bounds(*map(float, a)), Bounds(*map(float, b)))
        assert 0 <= r.low <= r.central <= r.high, f"{a} - {b} gave unordered {r}"


@pytest.fixture(scope="module")
def mini_exactfly(coal_mod, tmp_path_factory):
    """Fly ash exact (no band): the independent and correlated A_bot agree, isolating the F+B and F-S conventions."""
    act = band(mini_activity(), "coal_fly_ash_t", 2005, 8e6, 8e6, 8e6)
    root = make_mini(tmp_path_factory.mktemp("exactfly"), act)
    res = coal_mod.build(root)
    return root, Rows(list(res.rows)), list(res.log), Oracle(root)


class TestV12ConventionsInMiniTree:
    """Mini tree 2005: A_tot = 1e7 (+-10 %), A_fly = 8e6 (+-10 %), CHN/POL/XWL production, consumption 2e8."""

    def test_bottom_ash_uses_correlated_difference(self, mini_base):
        _root, rows, _, o = mini_base
        tot, fly, bot = o.ash(2005)
        assert not close(diff(tot, fly).low, bot.low, 1e-2), "test premise: the two conventions must differ"
        for tier in ("impounded", "dispersed"):
            Bk, _ = o.Bk(2005, "Ra226+")
            r = rows.one(2005, world=True, stage="combustion_power", group="Ra226+", tier=tier,
                         residue_type="coal_bottom_ash")
            assert_bounds(r, prod(Bk, o.fb(o.share(2005, tier))), label=f"A_bot correlated, {tier}")

    def test_fly_ash_residue_uses_correlated_difference(self, mini_exactfly):
        _, rows, _, o = mini_exactfly
        g = "Ra226+"
        F, _ = o.F(2005, g)
        S = o.stack(2005, g)
        assert S.central < F.central and S.high < F.high, "premise: uncapped"
        assert not close(diff(F, S).low, cdiff(F, S).low, 1e-3), "premise: the two conventions must differ"
        for tier in ("impounded", "dispersed"):
            r = rows.one(2005, world=True, stage="combustion_power", group=g, tier=tier, residue_type="coal_fly_ash")
            assert_bounds(r, prod(cdiff(F, S), o.fb(o.share(2005, tier))), label=f"F-S correlated, {tier}")

    def test_rest_of_world_uses_sum_independent_then_independent_difference(self, mini_base):
        _, rows, _, o = mini_base
        xwl = o.a("coal_production_t", 2005, "XWL")
        listed = [o.a("coal_production_t", 2005, c) for c in o.listed_countries("coal_production_t", 2005)]
        f = o.select(2005, "XWL", stage="coal_mining", group="Rn222+", route="air_ventilation")
        exp = prod(diff(xwl, sum_independent(listed)), o.fb(f))
        alts = [prod(diff(xwl, sum_correlated(listed)), o.fb(f)), prod(cdiff(xwl, sum_independent(listed)), o.fb(f))]
        assert not any(close(exp.low, a.low, 1e-3) for a in alts), "premise: conventions must differ"
        row = rows.one(2005, world=True, stage="coal_mining", group="Rn222+")
        assert_bounds(row, exp, label="rest of world (sum_independent, independent difference)")

    def test_nonpower_coal_uses_independent_difference(self, mini_base):
        _, rows, _, o = mini_base
        cons = o.a("coal_consumption_t", 2005, "XWL")
        power = scale(o.a("coal_ash_power_t", 2005, "XWL"), 1 / 0.12)
        N, _ = o.N(2005, "Ra226+")
        assert not close(cdiff(cons, power).low * 20000, N.low, 1e-3), "premise: conventions must differ"
        f = o.radon_factor(2005, "Rn222+")
        r = rows.one(2005, world=True, stage="combustion_nonpower", group="Rn222+")
        assert_bounds(r, prod(N, o.fb(f)), label="C_np independent difference")

    def test_stack_sums_fb_as_correlated(self, mini_exactfly):
        _, rows, _, o = mini_exactfly
        g = "Ra226+"
        exp = o.stack(2005, g)
        alt = o.stack_variants(2005, g)[0]
        assert not close(exp.low, alt.low, 1e-3), "premise: sum_independent and sum_correlated must differ"
        r = rows.one(2005, world=True, stage="combustion_power", group=g, tier="liberated", route="air_stack")
        assert_bounds(r, exp, label="stack with F+B sum_correlated")

    def test_stack_radon_sums_fb_as_correlated(self, mini_exactfly):
        _, rows, _, o = mini_exactfly
        F, _ = o.F(2005, "Ra226+")
        Bk, _ = o.Bk(2005, "Ra226+")
        f = o.fb(o.radon_factor(2005, "Rn222+"))
        exp = prod(sum_correlated([F, Bk]), f)
        assert not close(exp.low, prod(sum_independent([F, Bk]), f).low, 1e-3), "premise"
        r = rows.one(2005, world=True, stage="combustion_power", group="Rn222+")
        assert_bounds(r, exp, label="stack radon with F+B sum_correlated")

    def test_clipped_difference_flags_bottom_ash_rows(self, coal_mod, tmp_path):
        act = band(mini_activity(), "coal_ash_power_t", 2005, 5e6, 1e7, 1.5e7)
        act = band(act, "coal_fly_ash_t", 2005, 7e6, 8e6, 9e6)
        root, _, rows, _ = _build_mini(coal_mod, tmp_path, act)
        o = Oracle(root)
        _tot, _fly, bot = o.ash(2005)
        assert bot.low == 0 and bot.nd and bot.central > 0, "premise: A_bot low is clipped"
        r = rows.one(2005, world=True, stage="combustion_power", group="Ra226+", tier="impounded",
                     residue_type="coal_bottom_ash")
        Bk, _ = o.Bk(2005, "Ra226+")
        assert_bounds(r, prod(Bk, o.fb(o.share(2005, "impounded"))), label="clipped A_bot, impounded")
        assert float(r["value_low"]) == 0 and as_bool(r["below_detection"]), (
            "a clipped difference low must set below_detection (COAL_SPEC 12.1 / 11.4)")
        assert causes_of(r) == ["clipped_difference"], f"notes: {r['notes']!r}"

    def test_unclipped_difference_is_unflagged(self, mini_base):
        _, rows, _, _ = mini_base
        r = rows.one(2005, world=True, stage="combustion_power", group="Ra226+", tier="impounded",
                     residue_type="coal_bottom_ash")
        assert float(r["value_low"]) > 0 and not as_bool(r["below_detection"])
        assert causes_of(r) is None and "below_detection cause" not in str(r["notes"])


# --------------------------------------------------------------------------------------------
# 12.16 exact_zero cause
# --------------------------------------------------------------------------------------------
def _is_zero_row(r: dict) -> bool:
    return (float(r["value_low"]), float(r["value_central"]), float(r["value_high"])) == (0.0, 0.0, 0.0)


class TestV12ExactZeroCause:
    def test_cause_order_is_fixed_with_exact_zero_second(self):
        assert CAUSE_ORDER == ["zero_central_factor", "exact_zero", "clipped_difference",
                               "floor_dominance", "inherited_flag"]

    # ---- helper level -------------------------------------------------------------------
    def test_helper_equal_inputs_give_flagged_zero(self, fn):
        r = fn(Bounds(8.0, 10.0, 12.0), Bounds(8.0, 10.0, 12.0))
        assert (r.low, r.central, r.high) == (0.0, 0.0, 0.0), f"equal inputs must give (0,0,0); got {r}"
        assert r.nd_floored is True, "an exact zero stays flagged (COAL_SPEC 12.16, D52 zero-central rule)"

    # ---- real tree ----------------------------------------------------------------------
    def test_real_tree_every_zero_fly_residue_row_is_exact_zero(self, rows, pre_rows, oracle):
        allrows = rows.rows + pre_rows.rows
        zero_rows = [r for r in allrows if r["stage"] == "combustion_power"
                     and r["residue_type"] == "coal_fly_ash" and r["country"] in WORLD_CODES and _is_zero_row(r)]
        assert zero_rows, "premise: the real tree has exactly-zero fly-ash residue rows (Po-210, Pb-210+, K-40 early years)"
        bad = []
        for r in zero_rows:
            want = ["zero_central_factor", "exact_zero"] if r["tier"] == "reisolated" else ["exact_zero"]
            if not as_bool(r["below_detection"]) or causes_of(r) != want:
                bad.append((describe(r), r["below_detection"], causes_of(r)))
        assert not bad, f"{len(bad)} zero fly residue rows with wrong flag/cause, e.g. {bad[:3]}"

    def test_real_tree_exact_zero_set_matches_oracle(self, rows, pre_rows, oracle):
        """The (year, group) pairs where F - S is an unclipped (0,0,0) are derived from the oracle."""
        expected = set()
        for y in sorted({int(r["year"]) for r in rows.rows + pre_rows.rows if r["stage"] == "combustion_power"}):
            for g in ("Po210", "Pb210+", "K40"):
                try:
                    F, _ = oracle.F(y, g)
                    S = oracle.stack(y, g)
                except (KeyError, LookupError):
                    continue
                if cdiff_cause(F, S) == "exact_zero":
                    expected.add((y, g))
        assert expected, "oracle premise: some (year, group) has F - S = exactly zero"
        got = {(int(r["year"]), r["group"]) for r in rows.rows + pre_rows.rows
               if r["stage"] == "combustion_power" and r["residue_type"] == "coal_fly_ash"
               and r["country"] in WORLD_CODES and r["tier"] == "impounded" and causes_of(r) == ["exact_zero"]}
        assert expected <= got, f"oracle exact-zero (year, group) pairs not labelled exact_zero: {sorted(expected - got)[:8]}"
        wrong = {k for k in got if k not in expected and k[1] in ("Po210", "Pb210+", "K40")}
        assert not wrong, f"rows labelled exact_zero where the oracle sees no exact zero: {sorted(wrong)[:8]}"

    def test_real_tree_no_zero_row_is_labelled_clipped_difference_when_unclipped(self, rows, pre_rows, oracle):
        for r in rows.rows + pre_rows.rows:
            if (r["stage"] == "combustion_power" and r["residue_type"] == "coal_fly_ash"
                    and r["country"] in WORLD_CODES and _is_zero_row(r)):
                assert "clipped_difference" not in (causes_of(r) or []), (
                    f"{describe(r)}: unclipped exact zero wrongly labelled clipped_difference: {r['notes']!r}")

    # ---- mini tree ----------------------------------------------------------------------
    def test_mini_equal_total_and_fly_ash_gives_exact_zero_bottom_ash(self, coal_mod, tmp_path):
        act = band(mini_activity(), "coal_ash_power_t", 2005, 7e6, 8e6, 9e6)
        act = band(act, "coal_fly_ash_t", 2005, 7e6, 8e6, 9e6)
        root, _, rows, _ = _build_mini(coal_mod, tmp_path, act)
        o = Oracle(root)
        _t, _f, bot = o.ash(2005)
        assert (bot.low, bot.central, bot.high) == (0.0, 0.0, 0.0) and bot.nd, "oracle premise"
        assert cdiff_cause(o.a("coal_ash_power_t", 2005, "XWL"), o.a("coal_fly_ash_t", 2005, "XWL")) == "exact_zero"
        for tier, want in (("impounded", ["exact_zero"]), ("dispersed", ["exact_zero"]),
                           ("reisolated", ["zero_central_factor", "exact_zero"])):
            r = rows.one(2005, world=True, stage="combustion_power", group="Ra226+", tier=tier,
                         residue_type="coal_bottom_ash")
            assert _is_zero_row(r), f"{tier}: expected exact (0,0,0), got {describe(r)}"
            assert as_bool(r["below_detection"]), f"{tier}: an exact zero must stay flagged"
            assert causes_of(r) == want, f"{tier}: notes {r['notes']!r}"
            assert str(r["notes"]).endswith("; below_detection cause: " + "+".join(want))

    def test_mini_negative_central_difference_is_clipped_not_exact_zero(self, coal_mod, tmp_path):
        """Total ash below fly ash everywhere: raw bounds are negative, clipped to (0,0,0): clipped_difference."""
        act = band(mini_activity(), "coal_ash_power_t", 2005, 5e6, 6e6, 7e6)
        act = band(act, "coal_fly_ash_t", 2005, 7e6, 8e6, 9e6)
        root, _, rows, _ = _build_mini(coal_mod, tmp_path, act)
        o = Oracle(root)
        assert cdiff_cause(o.a("coal_ash_power_t", 2005, "XWL"), o.a("coal_fly_ash_t", 2005, "XWL")) == "clipped_difference"
        r = rows.one(2005, world=True, stage="combustion_power", group="Ra226+", tier="impounded",
                     residue_type="coal_bottom_ash")
        assert _is_zero_row(r) and as_bool(r["below_detection"])
        assert causes_of(r) == ["clipped_difference"], f"genuinely clipped difference: notes {r['notes']!r}"

    def test_mini_exact_zero_only_on_fly_ash_residue_rows(self, mini_base):
        """COAL_SPEC 12.16: in the baseline mini tree exact zeros arise only where the cap sets S = F."""
        _, rows, _, _ = mini_base
        bad = [r for r in rows.rows if "exact_zero" in (causes_of(r) or [])
               and not (r["stage"] == "combustion_power" and r["residue_type"] == "coal_fly_ash")]
        assert not bad, f"exact_zero outside the fly-ash residue rows: {bad[:2]}"


# --------------------------------------------------------------------------------------------
# 12.2 predecessor and successor states
# --------------------------------------------------------------------------------------------
def _cz_activity():
    act = mini_activity(xwl_prod={1960: 3.0e8, 2003: 3.0e8, 2005: 3.0e8, 2012: 3.0e8})
    for y in (2003, 2005):
        act += [_act("coal_production_t", y, "CSK", 6.0e7), _act("coal_production_t", y, "CZE", 4.0e7)]
    act += [_act("coal_production_t", 2012, "CZE", 4.0e7)]
    for c, v in (("SUN", 2.0e7), ("RUS", 3.0e7), ("YUG", 1.0e7), ("SRB", 1.0e7)):
        act.append(_act("coal_production_t", 2005, c, v))
    return act


class TestV12PredecessorStates:
    def test_mini_cze_dropped_where_csk_present(self, coal_mod, tmp_path):
        _root, _, rows, log = _build_mini(coal_mod, tmp_path, _cz_activity())
        for y in (2003, 2005):
            assert not rows.find(y, stage="coal_mining", country="CZE"), f"CZE mining row in {y} despite CSK"
            assert rows.find(y, stage="coal_mining", country="CSK", group="Rn222+"), f"no CSK row in {y}"
        assert rows.find(2012, stage="coal_mining", country="CZE", group="Rn222+"), "CZE kept where no CSK"
        dropped = log_entries(log, "predecessor_dropped")
        assert sorted(e["year"] for e in dropped) == [2003, 2005], f"predecessor_dropped log: {dropped}"
        assert all(e["country"] == "CZE" and "CSK" in str(e["detail"]) for e in dropped)

    def test_mini_rest_of_world_excludes_cze_when_csk_present(self, coal_mod, tmp_path):
        root, _, rows, _ = _build_mini(coal_mod, tmp_path, _cz_activity())
        o = Oracle(root)
        for y in (2005, 2012):
            xwl = o.a("coal_production_t", y, "XWL")
            lc = o.listed_countries("coal_production_t", y)
            assert ("CZE" in lc) == (y == 2012)
            listed = [o.a("coal_production_t", y, c) for c in lc]
            f = o.select(y, "XWL", stage="coal_mining", group="Rn222+", route="air_ventilation")
            row = rows.one(y, world=True, stage="coal_mining", group="Rn222+")
            assert_bounds(row, prod(diff(xwl, sum_independent(listed)), o.fb(f)), label=f"rest of world {y}")

    def test_mini_sun_yug_have_no_rule(self, coal_mod, tmp_path):
        _, _, rows, log = _build_mini(coal_mod, tmp_path, _cz_activity())
        for c in ("SUN", "RUS", "YUG", "SRB"):
            assert rows.find(2005, stage="coal_mining", country=c, group="Rn222+"), f"{c} row dropped"
        assert {e["country"] for e in log_entries(log, "predecessor_dropped")} == {"CZE"}

    def test_real_cze_dropped_1981_to_1992(self, rows, log, oracle):
        yrs = range(1981, 1993)
        for y in yrs:
            assert oracle.dropped_czech(y), "oracle premise"
            assert not rows.find(y, stage="coal_mining", country="CZE"), f"CZE row in {y}"
            assert rows.find(y, stage="coal_mining", country="CSK", group="Rn222+"), f"CSK row missing {y}"
        assert rows.find(1993, stage="coal_mining", country="CZE", group="Rn222+")
        dropped = log_entries(log, "predecessor_dropped")
        assert sorted(e["year"] for e in dropped) == list(yrs), (
            f"predecessor_dropped years {sorted(e['year'] for e in dropped)}")
        assert all(e["country"] == "CZE" and "CSK" in str(e["detail"]) for e in dropped)

    @pytest.mark.parametrize("y", [1985, 1991])
    def test_real_rest_of_world_excludes_cze(self, rows, oracle, y):
        xwl = oracle.a("coal_production_t", y, "XWL")
        listed = [oracle.a("coal_production_t", y, c) for c in oracle.listed_countries("coal_production_t", y)]
        resid = diff(xwl, sum_independent(listed))
        assert resid.central > 0
        f = oracle.select(y, "XWL", stage="coal_mining", group="Rn222+", route="air_ventilation")
        row = rows.one(y, world=True, stage="coal_mining", group="Rn222+")
        assert_bounds(row, prod(resid, oracle.fb(f)), flag=None, label=f"rest of world {y}")

    def test_real_1991_no_longer_negative(self, log):
        assert not log_entries(log, "negative_residual", year=1991)

    def test_real_sun_and_yug_rows_kept(self, rows):
        assert rows.find(1984, stage="coal_mining", country="SUN", group="Rn222+")
        assert rows.find(1991, stage="coal_mining", country="YUG", group="Rn222+")
        assert rows.find(1985, stage="coal_mining", country="RUS", group="Rn222+")


# --------------------------------------------------------------------------------------------
# 12.3 flag cause in notes
# --------------------------------------------------------------------------------------------
class TestV12FlagCause:
    def test_every_flagged_row_ends_with_ordered_causes_and_no_unflagged_row_has_one(self, rows, pre_rows):
        bad = []
        for r in rows.rows + pre_rows.rows:
            c = causes_of(r)
            if as_bool(r["below_detection"]):
                if not c:
                    bad.append(("flagged without cause suffix", describe(r), r["notes"]))
                    continue
                idx = [CAUSE_ORDER.index(x) if x in CAUSE_ORDER else -1 for x in c]
                if -1 in idx or idx != sorted(set(idx)):
                    bad.append(("causes out of order or unknown", describe(r), c))
            elif "below_detection cause" in str(r["notes"] or ""):
                bad.append(("unflagged with cause text", describe(r), r["notes"]))
            if len(bad) > 5:
                break
        assert not bad, f"flag-cause notes violations: {bad[:3]}"

    def test_zero_central_factor(self, mini_base):
        _, rows, _, _ = mini_base
        for res in ("coal_bottom_ash", "coal_fly_ash"):
            r = rows.one(2005, world=True, stage="combustion_power", group="Ra226+", tier="reisolated", residue_type=res)
            assert as_bool(r["below_detection"])
            assert causes_of(r) == ["zero_central_factor"], f"{res}: notes {r['notes']!r}"
            assert str(r["notes"]).endswith("; below_detection cause: zero_central_factor")

    def test_floor_dominance(self, mini_base):
        _, rows, _, _ = mini_base
        for tier in ("impounded", "reisolated"):  # coal:0046 / 0047 have value_low 0 and central > 0
            r = rows.one(2012, world=True, stage="combustion_power", group="Ra226+", tier=tier,
                         residue_type="coal_bottom_ash")
            assert float(r["value_low"]) == 0 and as_bool(r["below_detection"])
            assert causes_of(r) == ["floor_dominance"], f"{tier}: notes {r['notes']!r}"

    def test_unflagged_row_has_no_cause(self, mini_base):
        _, rows, _, _ = mini_base
        r = rows.one(2012, world=True, stage="combustion_power", group="Ra226+", tier="dispersed",
                     residue_type="coal_bottom_ash")
        assert not as_bool(r["below_detection"]) and causes_of(r) is None

    def test_clipped_and_zero_central_in_fixed_order(self, coal_mod, tmp_path):
        act = band(mini_activity(), "coal_ash_power_t", 2005, 5e6, 1e7, 1.5e7)
        act = band(act, "coal_fly_ash_t", 2005, 7e6, 8e6, 9e6)
        _, _, rows, _ = _build_mini(coal_mod, tmp_path, act)
        r = rows.one(2005, world=True, stage="combustion_power", group="Ra226+", tier="reisolated",
                     residue_type="coal_bottom_ash")
        assert causes_of(r) == ["zero_central_factor", "clipped_difference"], f"notes {r['notes']!r}"

    def test_inherited_flag_from_flagged_activity_input(self, coal_mod, tmp_path):
        act = edit_act(mini_activity(), series="coal_production_t", country="CHN", year=2005,
                       value_low=0.0, below_detection="true")
        _, _, rows, _ = _build_mini(coal_mod, tmp_path, act)
        r = rows.one(2005, stage="coal_mining", country="CHN", group="Rn222+")
        assert as_bool(r["below_detection"]) and float(r["value_low"]) == 0
        assert causes_of(r) == ["inherited_flag"], f"(A11, A17) notes {r['notes']!r}"

    def test_original_rule_text_is_kept_before_the_suffix(self, mini_base):
        _, rows, _, _ = mini_base
        r = rows.one(2005, world=True, stage="combustion_power", group="Ra226+", tier="reisolated",
                     residue_type="coal_bottom_ash")
        assert len(str(r["notes"]).split("; below_detection cause")[0].strip()) > 0


# --------------------------------------------------------------------------------------------
# 12.4 driver basis in notes
# --------------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def basis_built(coal_mod, tmp_path_factory):
    act = mini_activity()
    act = edit_act(act, series="coal_fly_ash_t", year=2005, basis="interpolated")
    act = edit_act(act, series="coal_consumption_t", year=2012, basis="extrapolated")
    for s_ in ("coal_ash_power_t", "coal_fly_ash_t"):
        act = edit_act(act, series=s_, year=2003, basis="interpolated")
    act = edit_act(act, series="coal_consumption_t", year=2003, basis="extrapolated")
    root = make_mini(tmp_path_factory.mktemp("basis"), act)
    return Rows(list(coal_mod.build(root).rows))


class TestV12DriverBasis:
    @pytest.fixture
    def built(self, basis_built):
        return basis_built

    def test_power_rows_get_interpolated_suffix_and_stay_modelled(self, built):
        rs = built.find(2005, stage="combustion_power")
        assert rs
        for r in rs:
            assert basis_set(r) == {"interpolated"}, f"{describe(r)}: notes {r['notes']!r}"
            assert r["basis"] == "modelled"

    def test_nonpower_rows_unaffected_by_fly_ash_basis(self, built):
        for r in built.find(2005, stage="combustion_nonpower"):
            assert basis_set(r) == set(), f"{describe(r)}: notes {r['notes']!r}"

    def test_nonpower_rows_get_extrapolated_suffix(self, built):
        rs = built.find(2012, stage="combustion_nonpower")
        assert rs
        for r in rs:
            assert basis_set(r) == {"extrapolated"}, f"{describe(r)}: notes {r['notes']!r}"
            assert r["basis"] == "modelled"

    def test_both_bases_are_joined_with_plus(self, built):
        for r in built.find(2003, stage="combustion_nonpower"):
            assert basis_set(r) == {"interpolated", "extrapolated"}, f"{describe(r)}: notes {r['notes']!r}"
            assert re.search(r"driver basis: (interpolated\+extrapolated|extrapolated\+interpolated)", r["notes"])

    def test_mining_rows_and_other_years_have_no_suffix(self, built):
        for r in built.find(2005, stage="coal_mining") + built.find(2012, stage="combustion_power"):
            assert "driver basis" not in str(r["notes"]), f"{describe(r)}: notes {r['notes']!r}"

    def test_suffix_precedes_flag_cause_suffix(self, built):
        r = built.one(2005, world=True, stage="combustion_power", group="Ra226+", tier="reisolated",
                      residue_type="coal_bottom_ash")
        assert str(r["notes"]).endswith("; below_detection cause: zero_central_factor")
        assert basis_set(r) == {"interpolated"}

    def test_real_pre1900_nonpower_rows_are_interpolated(self, pre_rows):
        r = pre_rows.one(1851, world=True, stage="combustion_nonpower", group="Ra226+", tier="liberated")
        assert basis_set(r) == {"interpolated"} and r["basis"] == "modelled", r["notes"]

    def test_real_2025_nonpower_rows_are_extrapolated(self, rows):
        rs = rows.find(2025, stage="combustion_nonpower")
        assert rs
        assert all(basis_set(r) == {"extrapolated"} and r["basis"] == "modelled" for r in rs), rs[0]["notes"]

    def test_real_measured_mining_row_has_no_suffix(self, rows):
        assert "driver basis" not in str(rows.one(2005, stage="coal_mining", country="CHN", group="Rn222+")["notes"])


# --------------------------------------------------------------------------------------------
# 12.5 stderr, library warnings, aggregation
# --------------------------------------------------------------------------------------------
class TestV12StderrAndLog:
    def test_build_writes_nothing_to_stderr_subprocess(self):
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
        code = ("import sys; from pathlib import Path; from pipeline.streams.coal import build; "
                "r = build(Path(sys.argv[1])); print(len(r.rows))")
        p = subprocess.run([sys.executable, "-W", "default", "-c", code, str(ROOT)], cwd=str(ROOT), env=env,
                           capture_output=True, text=True, timeout=900, check=False)
        assert p.returncode == 0, p.stderr[-1500:]
        assert p.stderr == "", f"build() wrote {len(p.stderr)} bytes to stderr (COAL_SPEC 12.5): {p.stderr[:600]!r}"

    def test_build_writes_nothing_to_stderr_in_process(self, coal_mod, tmp_path, capfd):
        _build_mini(coal_mod, tmp_path, mini_activity())
        out = capfd.readouterr()
        assert out.err == "", f"stderr not empty: {out.err[:600]!r}"

    def test_single_lib_warning_entry_real(self, log):
        w = log_entries(log, "lib_warning")
        assert len(w) == 1, f"expected exactly one lib_warning entry, found {len(w)}"
        assert w[0]["year"] in (None, "") and w[0]["country"] in (None, ""), f"year/country must be empty: {w[0]}"
        m = re.search(r"\d+", str(w[0]["detail"]))
        assert m and int(m.group()) >= 1, f"detail must carry the count: {w[0]['detail']!r}"
        assert re.search(r"[A-Za-z]{4,}", str(w[0]["detail"])), "detail must name the message type"

    def test_single_lib_warning_entry_mini(self, mini_base):
        assert len(log_entries(mini_base[2], "lib_warning")) == 1

    def test_no_power_ash_is_one_run(self, log):
        e = log_entries(log, "no_power_ash")
        assert len(e) == 1, f"expected a single contiguous no_power_ash run, got {len(e)}: {e[:3]}"
        assert e[0]["year"] == 1800 and str(e[0]["detail"]).startswith("1800-1899 (100 years)"), e[0]

    def test_aggregated_entries_have_run_detail(self, log):
        for kind in ("no_driver", "no_power_ash"):
            es = log_entries(log, kind)
            assert es or kind == "no_driver"
            for e in es:
                m = RUN_RE.match(str(e["detail"]))
                assert m, f"{kind} detail not 'first-last (n years)': {e}"
                first, last, n = map(int, m.groups())
                assert e["year"] == first and n == last - first + 1, e

    def test_world_run_entries_use_xxx(self, log):
        """COAL_SPEC 12.15: aggregated entries for world series carry the output convention XXX."""
        e = log_entries(log, "no_power_ash")
        assert e and all(x["country"] == "XXX" for x in e), e
        assert not [x for x in log if x["kind"] in ("no_driver", "no_power_ash") and x["country"] == "XWL"]

    def test_other_kinds_are_not_aggregated(self, log, oracle):
        neg = log_entries(log, "negative_residual")
        assert len(neg) == 24 and sorted(e["year"] for e in neg) == list(range(1800, 1824))

    def test_mini_contiguous_gap_is_one_entry_and_separate_gap_is_another(self, coal_mod, tmp_path):
        act = drop_act(mini_activity(), series="coal_production_t", country="CHN", year=2003)
        act = drop_act(act, series="coal_production_t", country="CHN", year=2004)
        act = drop_act(act, series="coal_production_t", country="CHN", year=2012)
        _, _, _rows, log = _build_mini(coal_mod, tmp_path, act)
        es = sorted(log_entries(log, "no_driver", country="CHN"), key=lambda e: e["year"])
        assert [e["year"] for e in es] == [2003, 2012], f"no_driver entries: {es}"
        assert str(es[0]["detail"]).startswith("2003-2004 (2 years)"), es[0]
        m = RUN_RE.match(str(es[1]["detail"]))
        assert m and m.group(1) == m.group(2) == "2012" and m.group(3) == "1", es[1]


# --------------------------------------------------------------------------------------------
# 12.6 / 12.7 error handling
# --------------------------------------------------------------------------------------------
class TestV12Errors:
    @pytest.mark.parametrize("fid", ["coal:0003", "coal:0004"])
    def test_ambiguous_factor_rows_propagate(self, coal_mod, tmp_path, fid):
        def edit(records):
            dup = next(r for r in records if r["factor_id"] == fid)
            return records + [{**dup, "factor_id": "coal:0900"}]
        with pytest.raises(LibError) as ei:
            _build_mini(coal_mod, tmp_path, mini_activity(), edit)
        assert "ambiguous" in str(ei.value).lower(), f"unexpected LibError message: {ei.value}"

    def test_missing_factor_is_still_swallowed(self, coal_mod, tmp_path):
        _, _, _rows, log = _build_mini(coal_mod, tmp_path, mini_activity(),
                                      lambda rs: [r for r in rs if r["factor_id"] != "coal:0004"])
        assert log_entries(log, "no_factor", year=2005, country="POL")

    @pytest.mark.parametrize("series,country", [("coal_production_t", "CHN"), ("coal_fly_ash_t", "XWL"),
                                                ("coal_consumption_t", "XWL"), ("coal_production_t", "XWL")])
    def test_duplicate_activity_rows_raise(self, coal_mod, tmp_path, series, country):
        act = mini_activity()
        dup = next(a for a in act if a["series"] == series and a["country"] == country and a["year"] == 2005)
        act.append({**dup, "value_central": dup["value_central"] * 1.01})
        with pytest.raises(LibError) as ei:
            _build_mini(coal_mod, tmp_path, act)
        msg = str(ei.value)
        assert series in msg and country in msg and "2005" in msg, f"LibError must name the key: {msg}"


# --------------------------------------------------------------------------------------------
# 12.8 CLI diff covers the build log
# --------------------------------------------------------------------------------------------
class TestV12Cli:
    def test_cli_log_in_diff_and_write(self, tmp_path):
        root = _copy_tree(tmp_path / "cli_log")
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
        cmd = [sys.executable, "-m", "pipeline.streams.coal", "--root", str(root)]

        def run(*extra):
            return subprocess.run(cmd + list(extra), cwd=str(ROOT), env=env, capture_output=True, text=True,
                                  timeout=900, check=False)

        w = run("--write")
        assert w.returncode == 0, w.stderr[-1000:]
        main = root / "data" / "streams" / "coal.csv"
        pre = root / "data" / "streams_pre1950" / "coal.csv"
        logf = root / "research" / "coal" / "build_log.csv"
        assert main.is_file() and pre.is_file() and logf.is_file(), "--write must write all three files"
        assert run().returncode == 0, "identical files must give exit 0"

        good = logf.read_text(encoding="utf-8")
        logf.write_text(good + "no_factor,1900,XXX,,tampered\n", encoding="utf-8", newline="\n")
        d = run()
        assert d.returncode != 0, "a differing build_log.csv alone must give a non-zero exit (COAL_SPEC 12.8)"
        assert logf.read_text(encoding="utf-8") != good, "the diff run must not overwrite the log"
        logf.write_text(good, encoding="utf-8", newline="\n")

        t = pre.read_text(encoding="utf-8")
        pre.write_text(t.replace("coal,all", "coal,al1", 1), encoding="utf-8", newline="\n")
        assert run().returncode != 0, "a differing pre-1950 file must give a non-zero exit (A18)"
        pre.write_text(t, encoding="utf-8", newline="\n")
        assert run().returncode == 0

        logf.unlink()
        assert run().returncode != 0, "a missing committed build_log.csv must count as a difference"


# --------------------------------------------------------------------------------------------
# 12.9 2025 and pre-1900 rows
# --------------------------------------------------------------------------------------------
class TestV12Years:
    def test_2025_nonpower_rows_exist_and_partition_consumption(self, rows, oracle):
        for g in ("Ra226+", "Pb210+", "K40", "U238+"):
            N, _ = oracle.N(2025, g)
            assert N.central > 0
            total = sum(float(r["value_central"]) for r in rows.find(2025, stage="combustion_nonpower", group=g))
            assert close(total, N.central, 1e-9), f"2025 {g}: non-power rows sum to {total}, expected {N.central}"
        for g in G11:
            assert rows.find(2025, stage="combustion_nonpower", group=g, tier="liberated"), f"no 2025 smoke row {g}"
        assert rows.find(2025, stage="combustion_nonpower", group="Rn222+")

    def test_no_driver_for_world_consumption_in_2025(self, log):
        for e in log_entries(log, "no_driver"):
            m = RUN_RE.match(str(e["detail"]))
            if m and e["country"] in WORLD_CODES + ("XWL",):
                assert not (int(m.group(1)) <= 2025 <= int(m.group(2))), f"2025 still a no_driver year: {e}"

    def test_pre1900_nonpower_rows_every_year(self, pre_rows):
        missing = [y for y in range(1800, 1900)
                   if not pre_rows.find(y, world=True, stage="combustion_nonpower", group="Ra226+", tier="liberated")]
        assert not missing, f"no pre-1900 non-power rows for {missing[:8]} (XWL consumption is annual)"

    def test_pre1900_mining_rows_every_year(self, pre_rows):
        missing = [y for y in range(1801, 1900) if not pre_rows.find(y, stage="coal_mining", group="Rn222+")]
        assert not missing, f"no pre-1900 mining rows for {missing[:8]}"

    def test_no_ash_based_rows_before_1900(self, pre_rows):
        assert not [r for r in pre_rows.rows if r["stage"] == "combustion_power" and int(r["year"]) < 1900]

    def test_pre1900_nonpower_equals_interpolated_consumption(self, pre_rows, oracle):
        N, _ = oracle.N(1855, "Ra226+")
        total = sum(float(r["value_central"]) for r in pre_rows.find(1855, stage="combustion_nonpower", group="Ra226+"))
        assert close(total, N.central, 1e-9)


# --------------------------------------------------------------------------------------------
# 12.10 independent benchmarks
# --------------------------------------------------------------------------------------------
INDEPENDENT = {  # TBq per GW.a, research/coal/benchmarks.md section 4 (COAL_SPEC 12.10)
    "ra226_ash": (0.0528, 0.149),
    "pb210_stack": (5.9e-4, 4.3e-4),
    "ra226_stack": (2.1e-4, None),
    "rn222_burning": (0.0495, 0.071),
}


class TestV12IndependentBenchmarks:
    @pytest.mark.parametrize("year", [2010, 2020])
    @pytest.mark.parametrize("name", list(INDEPENDENT))
    def test_within_factor_three_of_independent(self, table, year, name):
        vals = [v for v in INDEPENDENT[name] if v is not None]
        lo, hi = min(vals), max(vals)
        x = table[year][name]
        assert lo / 3 <= x <= hi * 3, (
            f"{name} {year}: stream {x:.3e} TBq per GW.a vs independent {vals} (UK NRPB / India); "
            f"allowed {lo / 3:.3e} to {hi * 3:.3e}")

    @pytest.mark.parametrize("year", [2010, 2020])
    def test_ra226_stack_era_check(self, rows, oracle, table, year):
        """Stream 1970-89 factors applied to this year's ash activity vs S0972 4.5e-3 (A15)."""
        F, _ = oracle.F(year, "Ra226+")
        Bk, _ = oracle.Bk(year, "Ra226+")
        p = float(oracle.base_fraction(1980)["value_central"])
        assert oracle.base_fraction(1980)["factor_id"] == "coal:0051"
        e = float(oracle.enrichment(1980, "Ra226+")["value_central"])
        S = min(p * e * (F.central + Bk.central), F.central)
        x = S / (1e12 * table[year]["gwa"])
        assert 4.5e-3 / 3 <= x <= 4.5e-3 * 3, f"era-check Ra-226 stack {x:.3e} vs 4.5e-3 TBq per GW.a (S0972)"

    @pytest.mark.parametrize("year", [2010, 2020])
    def test_ash_per_gwa_within_factor_three(self, oracle, table, year):
        mt = oracle.a("coal_ash_power_t", year, "XWL").central / 1e6 / table[year]["gwa"]
        assert 0.808 / 3 <= mt <= 0.808 * 3, f"ash per GW.a {mt:.3f} Mt vs 0.808 Mt (S0977)"


# --------------------------------------------------------------------------------------------
# 12.13 / 12.14 mutation-survivor tests
# --------------------------------------------------------------------------------------------
ERA_P = {1949: "coal:0049", 1950: "coal:0050", 1969: "coal:0050", 1970: "coal:0051",
         1989: "coal:0051", 1990: "coal:0052", 2009: "coal:0052", 2010: "coal:0053"}
ERA_SHARE = {1949: "coal:0040", 1950: "coal:0040", 1969: "coal:0040", 1970: "coal:0040",
             1989: "coal:0040", 1990: "coal:0043", 2009: "coal:0043", 2010: "coal:0046"}
ERA_HOUSE = {1949: ("coal:0068", "coal:0070"), 1950: ("coal:0069", "coal:0071")}


class TestV12EraEdges:
    @pytest.fixture
    def either(self, rows, pre_rows):
        return lambda y: pre_rows if y < 1950 else rows

    @pytest.mark.parametrize("y", sorted(ERA_P))
    def test_base_fraction_factor_and_value(self, either, oracle, y):
        assert oracle.base_fraction(y)["factor_id"] == ERA_P[y], "oracle premise"
        for g in ("Pb210+", "Ra226+"):
            r = either(y).one(y, world=True, stage="combustion_power", group=g, tier="liberated", route="air_stack")
            assert ERA_P[y] in ids(r["factor_ids"]), f"{y} {g}: factor_ids {r['factor_ids']}"
            others = {v for k, v in ERA_P.items() if v != ERA_P[y]}
            assert not (others & set(ids(r["factor_ids"]))), f"{y} {g}: wrong era factor in {r['factor_ids']}"
            F, _ = oracle.F(y, g)
            Bk, _ = oracle.Bk(y, g)
            p = float(oracle.base_fraction(y)["value_central"])
            e = float(oracle.enrichment(y, g)["value_central"])
            assert close(float(r["value_central"]), min(p * e * (F.central + Bk.central), F.central), 1e-9)

    @pytest.mark.parametrize("y", sorted(ERA_SHARE))
    def test_route_share_factor_and_value(self, either, oracle, y):
        sh = oracle.share(y, "impounded")
        want = oracle.share(y, "impounded")["factor_id"]
        assert want == ERA_SHARE[y]
        r = either(y).one(y, world=True, stage="combustion_power", group="Ra226+", tier="impounded",
                          residue_type="coal_bottom_ash")
        Bk, _ = oracle.Bk(y, "Ra226+")
        assert want in ids(r["factor_ids"])
        assert close(float(r["value_central"]), Bk.central * float(sh["value_central"]), 1e-9)

    @pytest.mark.parametrize("y", [1949, 1950])
    def test_household_and_smoke_factors_step_at_1950(self, either, oracle, y):
        hid, sid = ERA_HOUSE[y]
        assert oracle.household_share(y)["factor_id"] == hid and oracle.smoke_fraction(y)["factor_id"] == sid
        r = either(y).one(y, world=True, stage="combustion_nonpower", group="Pb210+", tier="liberated")
        assert hid in ids(r["factor_ids"]) and sid in ids(r["factor_ids"]), r["factor_ids"]
        N, _ = oracle.N(y, "Pb210+")
        H = N.central * float(oracle.household_share(y)["value_central"])
        M = min(float(oracle.smoke_fraction(y)["value_central"]) * float(oracle.enrichment(y, "Pb210+")["value_central"]) * H, H)
        assert close(float(r["value_central"]), M, 1e-9)
        d = either(y).one(y, world=True, stage="combustion_nonpower", group="Pb210+", tier="dispersed")
        assert close(float(d["value_central"]), H - M, 1e-9)


@pytest.fixture(scope="module")
def npcap_built(coal_mod, tmp_path_factory):
    def edit(records):
        return [{**r, "value_low": "0.4", "value_central": "0.5", "value_high": "0.9"}
                if r["factor_id"] == "coal:0071" else r for r in records]
    root = make_mini(tmp_path_factory.mktemp("npcap"), mini_activity(), edit)
    res = coal_mod.build(root)
    return Oracle(root), Rows(list(res.rows)), list(res.log)


class TestV12NonPowerCap:
    @pytest.fixture
    def built(self, npcap_built):
        return npcap_built

    @pytest.mark.parametrize("g", ["Po210", "Pb210+", "Ra226+", "K40"])
    def test_smoke_is_capped_bound_wise_at_household_activity(self, built, g):
        o, rows, _ = built
        y = 2005
        N, _ = o.N(y, g)
        H = prod(N, o.fb(o.household_share(y)))
        raw = prod(H, o.fb(o.smoke_fraction(y)), o.fb(o.enrichment(y, g)))
        M = bound_min(raw, H)
        r = rows.one(y, world=True, stage="combustion_nonpower", group=g, tier="liberated")
        assert_bounds(r, M, flag=None, label=f"non-power smoke {g} (capped)")
        d = rows.one(y, world=True, stage="combustion_nonpower", group=g, tier="dispersed")
        assert close(float(d["value_central"]), H.central - M.central, 1e-9)
        ind = rows.one(y, world=True, stage="combustion_nonpower", group=g, tier="impounded")
        assert close(float(ind["value_central"]), N.central - H.central, 1e-9)

    def test_cap_premises(self, built):
        o, _, _ = built
        y = 2005
        capped = {}
        for g in ("Po210", "Pb210+", "Ra226+", "K40"):
            N, _ = o.N(y, g)
            H = prod(N, o.fb(o.household_share(y)))
            raw = prod(H, o.fb(o.smoke_fraction(y)), o.fb(o.enrichment(y, g)))
            capped[g] = {n for n, a, b in zip(("low", "central", "high"), (raw.low, raw.central, raw.high),
                                              (H.low, H.central, H.high)) if a > b}
        assert "central" in capped["Po210"] and "central" in capped["Pb210+"], f"premise: {capped}"
        assert "central" not in capped["Ra226+"], f"premise: {capped}"

    def test_nonpower_cap_is_logged_per_bound(self, built):
        o, _, log = built
        y = 2005
        for g in ("Po210", "Pb210+", "Ra226+"):
            N, _ = o.N(y, g)
            H = prod(N, o.fb(o.household_share(y)))
            raw = prod(H, o.fb(o.smoke_fraction(y)), o.fb(o.enrichment(y, g)))
            want = {n for n, a, b in zip(("low", "central", "high"), (raw.low, raw.central, raw.high),
                                         (H.low, H.central, H.high)) if a > b}
            text = " ".join(str(e["detail"]).lower() for e in log_entries(log, "cap_applied", year=y, group=g))
            got = {w for w in ("low", "central", "high") if w in text}
            assert got == want, f"{g} {y}: cap_applied names {got}, expected {want}"


class TestV12RadonFactorIds:
    Y = 2005

    @pytest.mark.parametrize("group,parent,fid,other", [("Rn222+", "Ra226+", "coal:0065", "coal:0066"),
                                                         ("Rn220+", "Th228+", "coal:0066", "coal:0065")])
    def test_power_stack_radon_lists_fly_bottom_and_radon_factor(self, rows, oracle, group, parent, fid, other):
        r = rows.one(self.Y, world=True, stage="combustion_power", group=group)
        got = ids(r["factor_ids"])
        want = {oracle.conc(self.Y, parent, "coal_fly_ash")["factor_id"],
                oracle.conc(self.Y, parent, "coal_bottom_ash")["factor_id"], fid}
        assert set(got) == want and len(got) == len(want), f"{group}: factor_ids {got}, expected {sorted(want)}"
        assert got[-1] == fid and other not in got

    @pytest.mark.parametrize("group,parent,fid", [("Rn222+", "Ra226+", "coal:0065"), ("Rn220+", "Th228+", "coal:0066")])
    def test_nonpower_radon_factor_ids_in_order(self, rows, oracle, group, parent, fid):
        r = rows.one(self.Y, world=True, stage="combustion_nonpower", group=group)
        assert ids(r["factor_ids"]) == [oracle.np_factor(self.Y, parent)["factor_id"], fid]

    def test_mining_radon_factor_ids(self, rows):
        assert ids(rows.one(self.Y, stage="coal_mining", country="CHN", group="Rn222+")["factor_ids"]) == ["coal:0002"]
        assert ids(rows.one(self.Y, world=True, stage="coal_mining", group="Rn222+")["factor_ids"]) == ["coal:0001"]
