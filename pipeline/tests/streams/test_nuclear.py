"""Spec-blind tests for the nuclear stream script (Task 2.1, docs/NUCLEAR_SPEC.md v1.2 section 9 (a)-(j)).

Written from docs/NUCLEAR_SPEC.md (v1.2), docs/COAL_SPEC.md (sections 11-12, conventions inherited),
docs/LIB_SPEC.md (v1.4), docs/SCHEMA.md (3, 4.9, 5), docs/DECISIONS.md, data/factors/nuclear.csv,
data/events.csv and the activity files. pipeline/streams/nuclear.py was not read (it does not exist
yet). All expected values come from the independent arithmetic in nuclear_oracle.py (pandas plus the
standard library; no pipeline.lib); the factor and activity numbers are read from the files, never
hard-coded. Registry premises are asserted first, with the text "PREMISE BROKEN" in the message.

Mapping to NUCLEAR_SPEC section 9
---------------------------------
(a) Schema               TestSchema, TestRowConventions
(b) Candidates/coverage  TestRowsAgainstOracle (every family, every row), TestCoverage, TestMemoCoverage
(c) Conservation/events  TestTransferBalance, TestEventTotals, TestRemainder, TestTMI2, TestChurchRock,
                         TestNoDoubleCounting, TestMemoRows, TestTonnagePartition, TestMillBalance
(d) Determinism          TestDeterminism
(e) Benchmarks           TestBenchmarks, TestIndependentBenchmarks
(f) Hand-computed        TestHandComputed
(g) Fixture tests        TestMini* (miniature trees in tmp_path)
(h) Pre-1950 file        TestPre1950
(i) Premise assertions   TestPremises
(j) CLI                  TestCli
plus TestFlagsAndNotes (3.3), TestYearsAndEdges (2025, era edges), TestLog (8), TestStderr (3.7).

SPEC AMBIGUITIES / DEFECTS (the tests avoid asserting anything beyond a defensible reading)
--------------------------------------------------------------------------------------------
A1  Empty registry cells: section 3.2 says `None`, LIB_SPEC 10.3 says read_table gives "". Not tested.
A2  UZB 2000-25: the ISL share has central 1, so the complement 1-s has central 0 (high > 0) and the
    tonnage product hits the zero-central rule. Section 3.3 says "no zero_central_factor exists in the
    registry today", but the complement is such an input. The tests accept `zero_central_factor` or
    `floor_dominance` for those rows (oracle: zero_central_factor).
A3  Log entries have no series, stage or route field (section 8). no_factor / no_driver entries are
    identified by (kind, country, group, year range). The "absent series gives one aggregated no_driver"
    test is differential (entries without the series minus entries with it equals 1).
A4  F3-F5 use T_all = P x phi, which has no ISL share, but section 4.3 is silent on whether the ISL share
    factor is listed in factor_ids / source_ids of those rows. Required: the family factor is the LAST
    factor id; F1, F2, F6 and F7 must start with the ISL factor (section 4.4 says so for F7).
A5  E002 Kr88+ / Xe133m have no inventory (I = 0), so the raw central difference is negative; section 7.3
    says release_exceeds_inventory is logged "whenever a central raw difference is negative" but 9(c)3a
    names only no_inventory. Not asserted either way for groups without inventory.
A6  Accident factor_ids: which rows carry the capacity / inventory ids is only specified for the
    inventory-derived rows (damaged-core transfer_in, transfer_out). Liberated transfer_in rows are
    required to contain their release factor id and nothing more is asserted.
A7  below_detection on accident transfer_out and liberated transfer_in rows is only checked for
    consistency (flag implies low = 0); remainder rows are checked exactly (clipped_difference).
A8  Benchmark route of C14 and I131 (section 9(e)) is not stated; the air route (air_stack) is used.
A9  Section 6.4 says factor year_from is 1950 or 1956; in the registry it is 1950 everywhere except the
    single GCR family S35/air_stack (2010). Section 6.1's "windows tile 1950-2025" is true for PWR/BWR only.
A10 Whether a zero-driver year (no row, no log entry) breaks a contiguous no_factor run is not stated;
    run boundaries are therefore only checked for fully populated country series.
A11 Fields of no_family, event_not_modelled and negative_residual entries are not fully specified
    (country, group). The tests look for the reactor type / event id / magnitude anywhere in the entry.
A12 The CLI "prints counts by kind": the format is unspecified; only the kind names are looked for.
A13 Section 5.0 says the script asserts 1e-9 on pair balance and the validator 1e-6: both are met by the
    correlated sum, tests use 1e-6.
A14 Section 2.1 closure tolerance is relative 1e-5 (A2 resolution); the registry premise test measures the
    actual maximum (about 4e-6).
"""
from __future__ import annotations

import csv
import importlib
import itertools
import json
import math
import os
import re
import shutil
import subprocess
import sys
import warnings
from collections import Counter, defaultdict
from pathlib import Path
from typing import ClassVar

import pandas as pd
import pytest
from nuclear_oracle import (
    EVENT_TYPE,
    GWA_TWH,
    B,
    Oracle,
    comp,
    prod,
    remainder,
    scale,
    sum_correlated,
    sum_independent,
)

# pipeline/tests/streams/test_nuclear.py -> streams -> tests -> pipeline -> repository root
ROOT = Path(__file__).resolve().parents[3]

REL = 1e-7          # value comparison against the oracle (in-memory floats)
BAL = 1e-6          # transfer balance (SCHEMA 3.3 rule 1)
RUN_RE = re.compile(r"^(\d{4})-(\d{4}) \((\d+) years?\)")
TYPES = ["pwr", "bwr", "phwr", "gcr", "lwgr", "fbr"]
NOBLE = ["Ar41", "Kr85", "Kr85m", "Kr87", "Kr88+", "Xe133", "Xe135", "Xe138+"]
SEA_GROUPS_N = 13
LOG_KINDS = {"no_factor", "no_driver", "no_family", "negative_residual", "predecessor_dropped",
             "event_not_modelled", "no_inventory", "release_exceeds_inventory", "lib_warning"}


def premise(cond, msg):
    assert cond, f"PREMISE BROKEN: {msg}"


# --------------------------------------------------------------------------------------------
# generic helpers
# --------------------------------------------------------------------------------------------
def _blank(v) -> bool:
    return v is None or v == ""


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
    return (int(r["year"]), r["substream"], r["stage"], r["country"], r["group"], r["tier"], r["quantity"],
            r["route"] or "", r["residue_type"] or "", r["event_id"] or "")


def describe(r: dict) -> str:
    keys = ("year", "substream", "stage", "country", "group", "tier", "quantity", "route", "residue_type", "event_id")
    return ", ".join(f"{k}={r.get(k)!r}" for k in keys)


def vals(r: dict) -> tuple[float, float, float]:
    return float(r["value_low"]), float(r["value_central"]), float(r["value_high"])


def notes_parts(n) -> dict:
    """Parse the notes suffixes of NUCLEAR_SPEC 3.3: civil-share flag, driver basis, below_detection cause."""
    n = n or ""
    out = {"civil_flag": "; civil share undocumented (D64)" in n, "basis": None, "cause": None, "order_ok": True,
           "text": n}
    m = re.search(r"; driver basis: ([a-z+]+)", n)
    if m:
        out["basis"] = set(m.group(1).split("+"))
    m2 = re.search(r"; below_detection cause: ([a-z_+]+)\s*$", n)
    if m2:
        out["cause"] = m2.group(1).split("+")
    pos = []
    if out["civil_flag"]:
        pos.append(n.index("; civil share undocumented (D64)"))
    if m:
        pos.append(m.start())
    if m2:
        pos.append(m2.start())
    out["order_ok"] = pos == sorted(pos)
    return out


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

    def total(self, year: int, **kw) -> float:
        return sum(float(r["value_central"]) for r in self.find(year, **kw))


def log_entries(log: list[dict], kind: str, **kw) -> list[dict]:
    return [e for e in log if e.get("kind") == kind and all(e.get(k) == v for k, v in kw.items())]


def run_of(e: dict):
    m = RUN_RE.match(str(e.get("detail", "")))
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def assert_bounds(row: dict, exp: B, *, label: str = "", rel: float = REL, flag: bool | None = True):
    got = vals(row)
    want = (exp.low, exp.central, exp.high)
    for name, g, w in zip(("low", "central", "high"), got, want):
        assert close(g, w, rel), (f"{label} [{describe(row)}]: value_{name} = {g!r}, hand-computed {w!r} "
                                  f"(row {got}, expected {want})")
    if flag is not None:
        assert as_bool(row["below_detection"]) == exp.nd, (
            f"{label} [{describe(row)}]: below_detection = {row['below_detection']!r}, expected {exp.nd}")


# --------------------------------------------------------------------------------------------
# module-scoped fixtures
# --------------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def nuclear_mod():
    try:
        return importlib.import_module("pipeline.streams.nuclear")
    except ImportError as exc:  # expected until the code-writer is done
        pytest.fail(f"cannot import pipeline.streams.nuclear (NUCLEAR_SPEC 1): {type(exc).__name__}: {exc}")


@pytest.fixture(scope="module")
def result(nuclear_mod):
    assert hasattr(nuclear_mod, "build"), "pipeline.streams.nuclear must expose build(root) (NUCLEAR_SPEC 1)"
    res = nuclear_mod.build(ROOT)
    for attr in ("rows", "rows_pre1950", "log"):
        assert hasattr(res, attr), f"BuildResult has no attribute {attr!r} (NUCLEAR_SPEC 1)"
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
    d = tmp_path_factory.mktemp("nuclear_written")
    main, pre = d / "nuclear.csv", d / "nuclear_pre1950.csv"
    write_master(list(result.rows), main)
    write_master(list(result.rows_pre1950), pre)
    return main, pre


def _copy_tree(dst: Path) -> Path:
    shutil.copytree(ROOT / "data", dst / "data", ignore=shutil.ignore_patterns("streams", "streams_pre1950"))
    shutil.copytree(ROOT / "schema", dst / "schema")
    (dst / "data" / "streams").mkdir()
    (dst / "data" / "streams_pre1950").mkdir()
    (dst / "research" / "nuclear").mkdir(parents=True)
    return dst


def _factor(oracle: Oracle, fid: str) -> dict:
    for f in oracle.factors:
        if f["factor_id"] == fid:
            return f
    raise KeyError(fid)


# --------------------------------------------------------------------------------------------
# row-by-row comparison with the oracle (the engine of (b), (c)4/4b and (f))
# --------------------------------------------------------------------------------------------
def compare_row(er, r: dict) -> list[str]:
    msgs: list[str] = []
    if r["stream"] != "nuclear":
        msgs.append(f"stream={r['stream']!r}")
    if r["basis"] != "modelled":
        msgs.append(f"basis={r['basis']!r}, expected 'modelled' (3.1)")
    if r["allocation_variant"] != "default":
        msgs.append(f"allocation_variant={r['allocation_variant']!r}")
    if as_bool(r["embedded_fuel"]):
        msgs.append("embedded_fuel true")
    for col in ("product", "technology"):
        if not _blank(r[col]):
            msgs.append(f"{col}={r[col]!r}, expected empty")
    if r["unit"] != er.unit:
        msgs.append(f"unit={r['unit']!r}, expected {er.unit!r}")
    got, want = vals(r), (er.b.low, er.b.central, er.b.high)
    for name, g, w in zip(("low", "central", "high"), got, want):
        if not close(g, w, REL):
            msgs.append(f"value_{name}={g!r}, oracle {w!r}")
    flagged = as_bool(r["below_detection"])
    if flagged and got[0] != 0:
        msgs.append(f"below_detection true with value_low={got[0]!r}")
    if er.nd_policy == "exact" and flagged != er.b.nd:
        msgs.append(f"below_detection={flagged}, oracle {er.b.nd}")
    if ids(r["allocation_rule"]) != [er.rule]:
        msgs.append(f"allocation_rule={r['allocation_rule']!r}, expected {er.rule!r}")
    fid = ids(r["factor_ids"])
    if er.ids_exact:
        if fid != er.factor_ids:
            msgs.append(f"factor_ids={fid}, expected {er.factor_ids}")
    elif er.tag in ("F3", "F4", "F5"):
        if not fid or fid[-1] != er.factor_ids[-1]:
            msgs.append(f"factor_ids={fid}, last must be {er.factor_ids[-1]}")
    elif er.tag in ("acc_dmg", "acc_out"):
        inv = er.extra.get("inv_ids", [])
        if fid[:len(inv)] != inv or not set(er.factor_ids) <= set(fid):
            msgs.append(f"factor_ids={fid}, expected to start with {inv} and contain {er.factor_ids}")
    else:  # acc_rel
        if er.factor_ids[0] not in fid:
            msgs.append(f"factor_ids={fid}, must contain {er.factor_ids[0]}")
    src = ids(r["source_ids"])
    if src != sorted(src):
        msgs.append(f"source_ids not sorted: {src}")
    if not (er.src_req <= set(src) <= er.src_req | er.src_opt):
        msgs.append(f"source_ids={src}: missing {sorted(er.src_req - set(src))}, "
                    f"unexpected {sorted(set(src) - er.src_req - er.src_opt)}")
    # notes: rule text, civil flag, driver basis, cause (3.3)
    n = notes_parts(r["notes"])
    if not n["text"].strip():
        msgs.append("notes empty (rule text expected)")
    if n["civil_flag"] != bool(er.flag_note):
        msgs.append(f"civil-share flag present={n['civil_flag']}, expected {bool(er.flag_note)}")
    if (n["basis"] or set()) != er.basis:
        msgs.append(f"driver basis {n['basis']}, expected {sorted(er.basis) or None}")
    if not n["order_ok"]:
        msgs.append(f"notes suffix order wrong: {n['text'][-160:]!r}")
    if flagged:
        if not n["cause"]:
            msgs.append("flagged row has no '; below_detection cause:' suffix")
        elif er.nd_policy == "exact":
            want_c = list(er.b.causes)
            alt = [c for c in want_c if c != "zero_central_factor"]
            if "zero_central_factor" in want_c and "floor_dominance" not in alt:  # A2
                alt = alt + ["floor_dominance"]
            alt = [c for c in ("zero_central_factor", "exact_zero", "clipped_difference", "floor_dominance",
                               "inherited_flag") if c in alt]
            if n["cause"] != want_c and not (alt and n["cause"] == alt and "zero_central_factor" in want_c):
                msgs.append(f"cause {n['cause']}, oracle {want_c}")
    elif n["cause"] is not None:
        msgs.append(f"unflagged row carries a cause suffix {n['cause']}")
    if er.extra.get("rest") and "rest of world (world aggregate minus listed countries)" not in n["text"]:
        msgs.append("rest-of-world row without the required notes text")
    if not er.extra.get("rest") and er.tag in ("F1", "F2", "F3", "F4", "F5", "F6", "F7") \
            and "rest of world (world aggregate minus listed countries)" in n["text"]:
        msgs.append("non-residual row carries the rest-of-world notes text")
    return msgs


def compare_all(exp: dict, rows_obj: Rows, label: str) -> dict[str, list[str]]:
    """tag -> problem messages; the tag 'unexpected' collects rows that the oracle does not expect."""
    problems: dict[str, list[str]] = defaultdict(list)
    for k, er in exp.items():
        got = rows_obj.by_key.get(k)
        if not got:
            problems[er.tag].append(f"MISSING row {dict(zip(('year','substream','stage','country','group','tier','quantity','route','residue','event'), k))}")
            continue
        if len(got) > 1:
            problems[er.tag].append(f"DUPLICATE ({len(got)}) rows for {k}")
            continue
        for m in compare_row(er, got[0]):
            problems[er.tag].append(f"{k}: {m}")
    for k, lst in rows_obj.by_key.items():
        if k not in exp:
            problems["unexpected"].append(f"{label}: unexpected row {describe(lst[0])}")
    return problems


@pytest.fixture(scope="module")
def comparison(rows, expected):
    return compare_all(expected.rows, rows, "master")


@pytest.fixture(scope="module")
def comparison_pre(pre_rows, expected):
    return compare_all(expected.pre, pre_rows, "pre1950")


def show(msgs: list[str], n: int = 6) -> str:
    return f"{len(msgs)} problem(s); first {min(n, len(msgs))}:\n  " + "\n  ".join(msgs[:n])


# --------------------------------------------------------------------------------------------
# section 3: row conventions
# --------------------------------------------------------------------------------------------
class TestRowConventions:
    """(a) and section 3.1: columns, constants, ordering."""

    def test_rows_are_nonempty_dicts(self, rows, pre_rows):
        assert rows.rows, "build().rows is empty"
        assert pre_rows.rows, "build().rows_pre1950 is empty (the 1946-49 sea-disposal flows, NUCLEAR_SPEC 5.3)"
        assert all(isinstance(r, dict) for r in rows.rows[:50])

    def test_master_columns_present(self, rows):
        expected_cols = ["year", "stream", "substream", "stage", "product", "residue_type", "country", "group",
                         "tier", "quantity", "unit", "value_low", "value_central", "value_high",
                         "below_detection", "basis", "source_ids", "factor_ids", "allocation_variant",
                         "allocation_rule", "embedded_fuel", "technology", "route", "event_id", "notes"]
        bad = [r for r in rows.rows if list(r.keys()) != expected_cols]
        assert not bad, f"{len(bad)} rows do not have exactly the 25 master columns in order; first: {bad[0]}"

    def test_year_ranges(self, rows, pre_rows):
        assert min(int(r["year"]) for r in rows.rows) >= 1950 and max(int(r["year"]) for r in rows.rows) <= 2025
        py = [int(r["year"]) for r in pre_rows.rows]
        assert py and min(py) >= 1800 and max(py) <= 1949

    def test_no_xwl_country(self, rows, pre_rows):
        bad = [r for r in rows.rows + pre_rows.rows if r["country"] == "XWL"]
        assert not bad, f"{len(bad)} rows use country XWL (SCHEMA V10 forbids it; use XXX): {describe(bad[0])}"

    def test_unique_keys(self, rows, pre_rows):
        for name, obj in (("master", rows), ("pre1950", pre_rows)):
            dup = [k for k, v in obj.by_key.items() if len(v) > 1]
            assert not dup, f"{name}: {len(dup)} duplicate unique keys, first {dup[0]}"

    def test_bounds_ordered_and_flag_consistent(self, rows, pre_rows):
        for r in rows.rows + pre_rows.rows:
            lo, c, hi = vals(r)
            assert 0 <= lo <= c <= hi, f"bounds out of order ({lo}, {c}, {hi}): {describe(r)}"
            if as_bool(r["below_detection"]):
                assert lo == 0, f"below_detection true but value_low = {lo}: {describe(r)}"

    def test_ids_present_and_sorted(self, rows, pre_rows):
        for r in rows.rows + pre_rows.rows:
            f, s = ids(r["factor_ids"]), ids(r["source_ids"])
            assert f, f"factor_ids empty: {describe(r)}"
            assert s and s == sorted(s), f"source_ids empty or unsorted {s}: {describe(r)}"
            assert all(x.startswith("nuclear:") for x in f), f"unexpected factor id {f}: {describe(r)}"

    def test_units_by_quantity(self, rows, pre_rows):
        for r in rows.rows + pre_rows.rows:
            want = "Bq/a" if r["quantity"] == "flow" else "Bq"
            assert r["unit"] == want, f"unit {r['unit']!r} for quantity {r['quantity']!r}, expected {want!r} (3.1): {describe(r)}"

    def test_substream_by_stage(self, rows):
        for r in rows.rows:
            st = r["stage"]
            if r["event_id"] and st == "accident":
                assert r["substream"] == EVENT_TYPE[r["event_id"]], describe(r)
            elif st in ("u_mining_conv", "u_mining_isl", "u_milling", "conv_enrich_fab", "reprocessing", "sea_disposal"):
                assert r["substream"] == "fuel_cycle", describe(r)
            else:
                assert r["substream"] in TYPES, describe(r)

    def test_residue_type_only_on_tailings_and_church_rock(self, rows):
        for r in rows.rows:
            if r["residue_type"]:
                assert r["residue_type"] == "u_tailings", describe(r)
                assert r["stage"] == "u_milling" and r["tier"] in ("impounded", "dispersed"), \
                    f"residue_type outside impounded/dispersed tailings rows: {describe(r)}"
            elif r["stage"] == "u_milling" and r["tier"] in ("impounded", "dispersed"):
                pytest.fail(f"impounded/dispersed tailings row without residue_type: {describe(r)}")

    def test_route_only_on_liberated_rows(self, rows, pre_rows):
        for r in rows.rows + pre_rows.rows:
            if r["tier"] == "liberated":
                assert r["route"], f"liberated row without route (3.1): {describe(r)}"
            else:
                assert not r["route"], f"route on a non-liberated row (3.1): {describe(r)}"

    def test_event_id_rules(self, rows):
        for r in rows.rows:
            if r["stage"] == "accident":
                assert r["event_id"], f"accident-stage row without event_id: {describe(r)}"
            if r["event_id"]:
                assert (r["stage"] == "accident") or (r["stage"] == "u_milling" and r["event_id"] == "E003"), \
                    f"event_id outside accident / E003: {describe(r)}"

    def test_transfer_unit_and_quantities_by_stage(self, rows):
        routine = {"conv_enrich_fab", "reprocessing", "sea_disposal"}
        for r in rows.rows:
            if r["stage"] in routine:
                assert r["quantity"] in ("transfer_in", "transfer_out"), \
                    f"plain flow at a routine-transfer stage (V15): {describe(r)}"
            if r["quantity"] == "opening_stock":
                pytest.fail(f"opening_stock row: {describe(r)}")

    def test_country_conventions(self, rows):
        world_stages = {"conv_enrich_fab", "reactor_operation", "spent_fuel"}
        for r in rows.rows:
            if r["stage"] in world_stages:
                assert r["country"] == "XXX", f"world-driver stage must use XXX: {describe(r)}"
        for r in rows.find(stage="accident"):
            assert r["country"] in ("SUN", "JPN", "USA"), describe(r)

    def test_technology_and_product_empty(self, rows, pre_rows):
        for r in rows.rows + pre_rows.rows:
            assert _blank(r["technology"]) and _blank(r["product"]), describe(r)


# --------------------------------------------------------------------------------------------
# (a) schema
# --------------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def issues(written):
    from pipeline.validate import validate

    root = _copy_tree(Path(written[0]).parent / "validation_root")
    shutil.copy(written[0], root / "data" / "streams" / "nuclear.csv")
    found = validate(root, master_files=["data/streams/nuclear.csv"])
    return [i for i in found if i.file == "data/streams/nuclear.csv"]


class TestSchema:
    def test_validator_accepts_nuclear_csv(self, issues):
        shown = "\n".join(f"  row {i.row}: {i.rule} {i.message}" for i in issues[:15])
        assert not issues, (f"data/streams/nuclear.csv has {len(issues)} validator issues "
                            f"(rules {sorted({i.rule for i in issues})}):\n{shown}")

    @pytest.mark.parametrize("rule", ["V03", "V09", "V15", "V10", "V12", "V13", "V14", "X02", "X04", "X05", "R02"])
    def test_no_rule_violations(self, issues, rule):
        hits = [i for i in issues if i.rule == rule]
        assert not hits, f"{len(hits)} {rule} issues, first: row {hits[0].row} {hits[0].message}"

    def test_memo_rows_are_flow_only_never_opening_stock(self, rows):
        memo = rows.find(tier="memo_earth_moved")
        assert memo, "no memo_earth_moved rows (NUCLEAR_SPEC 4.4)"
        assert {r["quantity"] for r in memo} == {"flow"}
        assert {r["stage"] for r in memo} == {"u_mining_conv"}

    def test_civil_tokens_on_production_and_reprocessing(self, rows):
        for r in rows.rows:
            if r["stage"] in ("u_mining_conv", "u_mining_isl", "u_milling", "reprocessing"):
                tok = ids(r["allocation_rule"])
                assert len(tok) == 1 and tok[0].startswith("civil:"), f"no civil token: {describe(r)} {tok}"
                y = int(r["year"])
                if y <= 1964 and r["event_id"] != "E003":
                    assert tok[0] == "civil:pre1965", f"pre-1965 row without civil:pre1965: {describe(r)}"
                if tok[0] == "civil:pre1965":
                    assert y <= 1964 and float(r["value_high"]) == 0, f"civil:pre1965 misuse: {describe(r)}"
                if tok[0] == "civil:ratio":
                    assert y >= 1965, f"civil:ratio before 1965: {describe(r)}"
                if tok[0] == "civil:doc":
                    assert r["event_id"] == "E003", f"civil:doc outside the Church Rock rows: {describe(r)}"
                if r["stage"] == "reprocessing":
                    assert tok[0] == "civil:throughput", describe(r)


# --------------------------------------------------------------------------------------------
# (b) every family, every row, against the oracle
# --------------------------------------------------------------------------------------------
FAMILY_TAGS = ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "enrich", "repro", "sea", "eff", "core", "spent",
               "acc_rel", "acc_dmg", "acc_out", "e003_in", "e003_out"]


class TestRowsAgainstOracle:
    """Row sets and values of every family, recomputed from the files (9(b), 9(c)4, 9(c)4b, 9(f))."""

    @pytest.mark.parametrize("tag", FAMILY_TAGS)
    def test_family_rows_match_oracle(self, comparison, expected, tag):
        n = sum(1 for e in expected.rows.values() if e.tag == tag)
        assert n > 0, f"oracle produced no rows for family {tag}: the registry or activity premise changed"
        msgs = comparison.get(tag, [])
        assert not msgs, f"family {tag} ({n} expected rows): " + show(msgs)

    def test_no_unexpected_rows(self, comparison):
        msgs = comparison.get("unexpected", [])
        assert not msgs, "rows the spec does not allow: " + show(msgs)

    def test_total_row_count(self, rows, expected):
        assert len(rows.rows) == len(expected.rows), f"{len(rows.rows)} rows, oracle expects {len(expected.rows)}"


# --------------------------------------------------------------------------------------------
# (b) candidate nuclides and coverage
# --------------------------------------------------------------------------------------------
class TestCoverage:
    def test_missing_rows_have_log_runs(self, expected, log):
        """A (group, route, year) with a driver and no registry row must sit in a no_factor run (9(b))."""
        runs = defaultdict(list)
        for e in log:
            if e["kind"] == "no_factor":
                r = run_of(e)
                if r:
                    runs[(e["country"], e["group"])].append(r)
        bad = []
        for m in expected.missing:
            if not any(a <= m.year <= b for a, b, _ in runs.get((m.country, m.group), [])):
                bad.append(f"{m.stage}/{m.group}/{m.route or '-'} {m.country} {m.year}")
        assert not bad, f"{len(bad)} missing rows without a covering no_factor run, first: {bad[:6]}"

    def test_no_factor_runs_are_only_real_gaps(self, expected, log):
        gap = {(m.country, m.group, m.year) for m in expected.missing}
        bad = []
        for e in log:
            if e["kind"] != "no_factor":
                continue
            r = run_of(e)
            if not r or r[0] < 1950:
                continue
            for y in range(r[0], r[1] + 1):
                if (e["country"], e["group"], y) not in gap:
                    bad.append((e["country"], e["group"], y))
                    break
        assert not bad, f"no_factor runs covering years without a gap, first {bad[:5]}"

    def test_mining_milling_groups_in_2010(self, rows, oracle):
        reg = {f["group"] for f in oracle.factors}
        found = {r["group"] for r in rows.by_year[2010] if r["stage"] in ("u_mining_conv", "u_mining_isl", "u_milling")}
        for g in ["U238+", "U234", "Th230", "Ra226+", "Pb210+", "Po210", "U235+", "Pa231", "Ac227+", "Rn222+"]:
            if g not in reg:
                warnings.warn(f"METHODS 4.3 group {g} is absent from the registry (reported, not failed)")
                continue
            assert g in found, f"{g} is in the registry but has no 2010 mining/milling row"

    def test_effluent_and_reprocessing_groups_in_2010(self, rows, oracle):
        reg = {f["group"] for f in oracle.factors}
        flows = {r["group"] for r in rows.by_year[2010]
                 if (r["quantity"] == "flow" and r["tier"] == "liberated")
                 or (r["quantity"] == "transfer_in" and r["tier"] == "liberated")}
        want = ["H3", "C14", "I129", "I131", "Cs137+", "Cs134", "Sr90+", "Co60", "Co58", "Mn54", "Ru106+", "Pu239",
                "Pu240", "Am241"] + NOBLE
        for g in want:
            if g not in reg:
                warnings.warn(f"METHODS 4.3 group {g} is absent from the registry (reported, not failed)")
                continue
            assert g in flows, f"{g} is in the registry but has no 2010 liberated flow / transfer_in row"

    @pytest.mark.parametrize("g", ["Sb125+", "Tc99"])
    def test_spent_fuel_and_inventory_groups_in_2010(self, rows, oracle, g):
        if g not in {f["group"] for f in oracle.factors}:
            warnings.warn(f"{g} is absent from the registry (reported, not failed)")
            return
        assert rows.find(2010, stage="spent_fuel", group=g), f"{g}: no 2010 spent-fuel flow"
        assert rows.find(2010, stage="reactor_operation", group=g, quantity="standing_inventory"), \
            f"{g}: no 2010 standing inventory"

    def test_uranium_rows_for_every_producing_country_year(self, rows, oracle):
        """Every producing country-year with a non-zero production gets F1-F6 rows for 2010 groups."""
        for c in oracle.countries("u_production", 2010):
            if oracle.is_zero(oracle.a("u_production", 2010, c)):
                continue
            assert rows.find(2010, stage="u_milling", country=c, group="U238+", tier="sealed_fuel_cycle"), \
                f"no F5 product row for producing country {c} in 2010"

    def test_zero_production_country_years_give_no_rows(self, rows, oracle):
        for (s, y, c) in oracle.act:
            if s == "u_production" and c != "XWL" and y >= 1950 and oracle.is_zero(oracle.a(s, y, c)):
                assert not rows.find(y, country=c, stage="u_milling"), \
                    f"zero-production country-year {c} {y} has rows (4.1)"
                break

    def test_fbr_has_no_in_core_or_spent_fuel_rows(self, rows):
        assert not rows.find(substream="fbr", stage="spent_fuel")
        assert not rows.find(substream="fbr", quantity="standing_inventory")
        assert rows.find(substream="fbr", stage="reactor_operation", quantity="flow"), "fbr effluent flows missing"

    def test_reprocessing_and_sea_per_driver_country(self, rows, oracle):
        for c in oracle.countries("nuc_reprocessed_gwa", 2005):
            if not oracle.is_zero(oracle.a("nuc_reprocessed_gwa", 2005, c)):
                assert rows.find(2005, stage="reprocessing", country=c, quantity="transfer_in"), \
                    f"no reprocessing rows for site country {c} in 2005"
        assert not rows.find(stage="reprocessing", country="XXX") and not rows.find(stage="sea_disposal", country="XXX"), \
            "XXX must not be used at reprocessing or sea_disposal (3.1)"
        for c in oracle.countries("nuc_sea_dumped_tbq", 1967):
            if not oracle.is_zero(oracle.a("nuc_sea_dumped_tbq", 1967, c)):
                assert rows.find(1967, stage="sea_disposal", country=c, quantity="transfer_in"), \
                    f"no sea-disposal rows for dumping country {c} in 1967"

    def test_group_sets_come_from_the_registry(self, rows, oracle):
        """3.2: groups are read from the registry. Orientation counts of section 6 (pwr 18 air / 9 liquid ...)."""
        air = {r["group"] for r in rows.find(2010, substream="pwr", stage="reactor_operation", quantity="flow",
                                              route="air_stack")}
        liq = {r["group"] for r in rows.find(2010, substream="pwr", stage="reactor_operation", quantity="flow",
                                              route="water_liquid_effluent")}
        reg_air = {f["group"] for f in oracle.factors if f["driver_series"] == "nuc_gen_pwr"
                   and f["tier"] == "liberated" and f["route"] == "air_stack"}
        reg_liq = {f["group"] for f in oracle.factors if f["driver_series"] == "nuc_gen_pwr"
                   and f["tier"] == "liberated" and f["route"] == "water_liquid_effluent"}
        assert air == reg_air and liq == reg_liq, "PWR 2010 effluent groups differ from the registry's"


class TestMemoCoverage:
    """9(b) v1.2: the memo family separately."""

    def test_273_rows_usa_1950_1988(self, rows, oracle):
        memo = rows.find(tier="memo_earth_moved")
        groups = {"U238+", "U234", "Th230", "Ra226+", "Pb210+", "Po210", "U235+"}
        years = [y for y in range(1950, 1989) if oracle.has("u_production", y, "USA")
                 and not oracle.is_zero(oracle.a("u_production", y, "USA"))]
        premise(len(years) == 39, "USA u_production is non-zero in every year 1950-1988")
        assert len(memo) == 273, f"{len(memo)} memo rows, expected 39 years x 7 groups = 273"
        assert {r["country"] for r in memo} == {"USA"}
        assert {r["group"] for r in memo} == groups
        assert {int(r["year"]) for r in memo} == set(years)
        assert Counter((int(r["year"]), r["group"]) for r in memo).most_common(1)[0][1] == 1

    def test_no_memo_after_1988_and_no_log_for_other_countries(self, rows, log):
        assert not [r for r in rows.find(tier="memo_earth_moved") if int(r["year"]) > 1988]
        assert not [r for r in rows.rows if r["tier"] == "memo_earth_moved" and r["country"] != "USA"]

    @pytest.mark.parametrize("g", ["U238+", "U234", "Th230", "Ra226+", "Pb210+", "Po210", "U235+"])
    def test_1989_2025_no_factor_runs_logged(self, log, g):
        es = [e for e in log_entries(log, "no_factor", country="USA", group=g) if e["year"] == 1989]
        assert es, f"no aggregated no_factor entry for memo group {g}, USA, from 1989 (4.4)"
        assert any(str(e["detail"]).startswith("1989-2025 (37 years)") for e in es), \
            f"{g}: no entry with detail '1989-2025 (37 years)': {[e['detail'] for e in es]}"

    def test_other_countries_logged_nothing_for_memo(self, log):
        """A non-USA country-year gives neither a row nor a log entry for the memo family."""
        # no entry for a producing country other than USA that names the memo run 1989-2025
        bad = [e for e in log_entries(log, "no_factor", group="Ra226+")
               if e["country"] not in ("USA", "XXX") and str(e["detail"]).startswith("1989-2025")]
        assert not bad, f"no_factor memo-style runs for non-USA countries: {bad[:2]}"


# --------------------------------------------------------------------------------------------
# section 3.3: flag causes and driver basis in notes
# --------------------------------------------------------------------------------------------
class TestFlagsAndNotes:
    def test_flagged_rows_carry_cause_in_fixed_order(self, rows):
        order = ["zero_central_factor", "exact_zero", "clipped_difference", "floor_dominance", "inherited_flag"]
        n_flag = 0
        for r in rows.rows:
            p = notes_parts(r["notes"])
            if as_bool(r["below_detection"]):
                n_flag += 1
                assert p["cause"], f"flagged row without cause suffix: {describe(r)}: {r['notes']!r}"
                assert all(c in order for c in p["cause"]), f"unknown cause {p['cause']}: {describe(r)}"
                assert p["cause"] == [c for c in order if c in p["cause"]], f"causes out of order {p['cause']}"
                assert str(r["notes"]).rstrip().endswith("; below_detection cause: " + "+".join(p["cause"])), \
                    f"cause must end the notes: {r['notes']!r}"
            else:
                assert p["cause"] is None, f"unflagged row has cause text: {describe(r)}"
        assert n_flag > 0, "no flagged rows at all (KAZ/USA ISL complements must produce floor_dominance)"

    def test_floor_dominance_on_isl_complement_rows(self, rows, oracle):
        """KAZ 2010: ISL share (0.99 central, high 1.0) -> complement low 0 -> F1 low flagged floor_dominance."""
        f = oracle.select(2010, "KAZ", stage="u_mining_isl", group="", tier="", route="", residue_type="", driver_series="")
        premise(float(f["value_high"]) == 1.0 and 0 < float(f["value_central"]) < 1, "KAZ 2010 ISL share high is 1.0, central in (0,1)")
        r = rows.one(2010, stage="u_mining_conv", country="KAZ", group="Rn222+", tier="liberated", quantity="flow")
        assert as_bool(r["below_detection"]) and float(r["value_low"]) == 0
        assert notes_parts(r["notes"])["cause"] == ["floor_dominance"], r["notes"]

    def test_structural_zero_rows_are_unflagged_and_have_no_cause(self, rows):
        r = rows.one(1955, stage="u_mining_isl", country="USA", group="Rn222+", tier="liberated", quantity="flow") \
            if rows.find(1955, stage="u_mining_isl", country="USA") else None
        if r is None:
            pytest.fail("no 1955 USA ISL radon row: structural-zero rows must be written (4.1)")
        assert vals(r) == (0.0, 0.0, 0.0) and not as_bool(r["below_detection"])
        assert notes_parts(r["notes"])["cause"] is None

    def test_pre1965_rows_are_zero_unflagged(self, rows):
        pre = [r for r in rows.rows if r["stage"] in ("u_mining_conv", "u_milling") and int(r["year"]) <= 1964
               and r["country"] != "XXX"]
        assert pre, "no pre-1965 uranium rows"
        for r in pre:
            assert vals(r) == (0.0, 0.0, 0.0), f"pre-1965 row not 0/0/0: {describe(r)}"
            assert not as_bool(r["below_detection"]), f"pre-1965 structural zero is flagged: {describe(r)}"
            assert ids(r["allocation_rule"]) == ["civil:pre1965"]

    def test_driver_basis_suffix_on_2025_uranium_and_reactor_rows(self, rows):
        for r in rows.find(2025, stage="u_milling", group="U238+", tier="sealed_fuel_cycle"):
            assert notes_parts(r["notes"])["basis"] == {"extrapolated"}, f"2025 uranium row lacks the suffix: {describe(r)}"
        for t in TYPES:
            for r in rows.find(2025, substream=t, stage="reactor_operation", quantity="flow")[:3]:
                assert notes_parts(r["notes"])["basis"] == {"extrapolated"}, describe(r)
        for r in rows.find(2024, stage="u_milling", group="U238+", tier="sealed_fuel_cycle"):
            assert notes_parts(r["notes"])["basis"] is None, f"2024 measured driver must carry no suffix: {describe(r)}"
        assert all(r["basis"] == "modelled" for r in rows.rows)

    def test_interpolated_driver_basis_on_us_sea_disposal(self, rows):
        r = rows.find(1960, stage="sea_disposal", country="USA", quantity="transfer_in")
        assert r, "no 1960 US sea-disposal rows"
        for x in r:
            p = notes_parts(x["notes"])
            assert p["basis"] == {"interpolated"} and p["civil_flag"], f"{describe(x)}: {x['notes']!r}"

    def test_civil_share_flag_only_on_us_sea_disposal(self, rows, pre_rows):
        for r in rows.rows + pre_rows.rows:
            flagged = notes_parts(r["notes"])["civil_flag"]
            should = r["stage"] == "sea_disposal" and r["country"] == "USA"
            assert flagged == should, f"civil-share flag mismatch (3.3): {describe(r)}"

    def test_notes_order_everywhere(self, rows, pre_rows):
        for r in rows.rows + pre_rows.rows:
            assert notes_parts(r["notes"])["order_ok"], f"suffix order: {describe(r)}: {r['notes']!r}"


# --------------------------------------------------------------------------------------------
# 2025 rows and era edges
# --------------------------------------------------------------------------------------------
class TestYearsAndEdges:
    def test_2025_rows_exist_for_every_family(self, rows):
        y = rows.by_year[2025]
        stages = {r["stage"] for r in y}
        for st in ("u_mining_conv", "u_mining_isl", "u_milling", "conv_enrich_fab", "reprocessing", "reactor_operation",
                   "spent_fuel"):
            assert st in stages, f"no 2025 rows at stage {st} (A1 carry-forward, 4.5, 6.4)"
        assert any(r["quantity"] == "standing_inventory" for r in y)
        assert not any(r["stage"] == "sea_disposal" for r in y), "sea disposal after 1993 has no factor"

    def test_no_rows_before_driver_start(self, rows, oracle):
        first = {t: min(oracle.years_of(f"nuc_gen_{t}", "XWL")) for t in TYPES}
        for t in TYPES:
            early = [r for r in rows.find(substream=t, stage="reactor_operation", quantity="flow") if int(r["year"]) < first[t]]
            assert not early, f"{t}: effluent rows before the first generation year {first[t]}: {describe(early[0])}"

    @pytest.mark.parametrize("t,fid_old,fid_new", [("pwr", "nuclear:0084", "nuclear:1686"),
                                                    ("bwr", "nuclear:0219", "nuclear:1693")])
    def test_noble_gas_edge_2014_2015(self, rows, oracle, t, fid_old, fid_new):
        old, new = _factor(oracle, fid_old), _factor(oracle, fid_new)
        premise(old["driver_series"] == new["driver_series"] == f"nuc_gen_{t}" and old["group"] == new["group"]
                and old["route"] == new["route"] and int(old["year_to"]) == 2014 and int(new["year_from"]) == 2015,
                f"{fid_old} ends 2014 and {fid_new} starts 2015 for the same {t} family")
        g, route = old["group"], old["route"]
        for y, f in ((2014, old), (2015, new)):
            r = rows.one(y, substream=t, stage="reactor_operation", group=g, route=route, quantity="flow")
            G = scale(oracle.a(f"nuc_gen_{t}", y, "XWL"), 1 / GWA_TWH)
            assert ids(r["factor_ids"]) == [f["factor_id"]], f"{t} {g} {y}: factor_ids {r['factor_ids']}, expected {f['factor_id']}"
            assert_bounds(r, prod(G, oracle.fb(f)), label=f"{t} {g} {y} era edge")
        assert float(old["value_central"]) != float(new["value_central"]), "premise: the 2014/2015 rows differ in central"

    def test_all_other_pwr_bwr_effluents_single_2010_2025_row(self, rows, oracle):
        """Groups not split at 2014/2015 keep the same factor id in 2010 and 2025 (6.1)."""
        split = {"nuclear:1686", "nuclear:1693"}
        same = 0
        for t in ("pwr", "bwr"):
            for r10 in rows.find(2010, substream=t, stage="reactor_operation", quantity="flow", tier="liberated"):
                r25 = rows.find(2025, substream=t, stage="reactor_operation", quantity="flow", group=r10["group"],
                                route=r10["route"])
                if r25 and ids(r25[0]["factor_ids"])[0] not in split and ids(r25[0]["factor_ids"]) == ids(r10["factor_ids"]):
                    same += 1
        assert same > 20, f"only {same} PWR/BWR effluent families keep a single 2010-2025 row; the registry has many"

    @pytest.mark.parametrize("y_old,y_new", [(1949, 1950), (1979, 1980), (1989, 1990), (2009, 2010), (2002, 2003)])
    def test_pwr_effluent_era_steps_not_smoothed(self, rows, oracle, y_old, y_new):
        for y in (y_old, y_new):
            if not oracle.has("nuc_gen_pwr", y, "XWL"):
                return
        for g in ("Xe133", "H3"):
            for route in ("air_stack", "water_liquid_effluent"):
                for y in (y_old, y_new):
                    m = rows.find(y, substream="pwr", stage="reactor_operation", group=g, route=route, quantity="flow")
                    if not m:
                        continue
                    f = oracle.select(y, "XWL", stage="reactor_operation", group=g, tier="liberated", route=route,
                                      driver_series="nuc_gen_pwr")
                    assert ids(m[0]["factor_ids"]) == [f["factor_id"]], \
                        f"pwr {g} {route} {y}: factor {m[0]['factor_ids']} but the registry window gives {f['factor_id']}"

    def test_reprocessing_pu_rows_used_as_given(self, rows, oracle):
        """Pu239 and Pu240 2010 rows: ratio equals the factor ratio (no re-split) for FRA, both routes."""
        for route in ("air_stack", "water_liquid_effluent"):
            f9 = oracle.select(2010, "XWL", stage="reprocessing", group="Pu239", tier="liberated", route=route)
            f0 = oracle.select(2010, "XWL", stage="reprocessing", group="Pu240", tier="liberated", route=route)
            r9 = rows.one(2010, stage="reprocessing", country="FRA", group="Pu239", tier="liberated", route=route,
                          quantity="transfer_in")
            r0 = rows.one(2010, stage="reprocessing", country="FRA", group="Pu240", tier="liberated", route=route,
                          quantity="transfer_in")
            ratio = float(r0["value_central"]) / float(r9["value_central"])
            want = float(f0["value_central"]) / float(f9["value_central"])
            assert close(ratio, want, 1e-9), f"{route}: Pu240/Pu239 = {ratio}, factor ratio {want} (D49 rows used as given)"
            assert 1.55 < ratio < 1.63, f"Pu240/Pu239 ratio {ratio}, expected about 1.59"


# --------------------------------------------------------------------------------------------
# section 8: the log
# --------------------------------------------------------------------------------------------
class TestLog:
    def test_log_shape_and_kinds(self, log):
        assert log, "empty log"
        for e in log:
            assert set(e) >= {"kind", "year", "country", "group", "detail"}, f"log entry keys {sorted(e)}"
            assert e["kind"] in LOG_KINDS, f"unknown log kind {e['kind']!r}"

    def test_aggregated_entries_have_run_detail(self, log):
        for kind in ("no_factor", "no_driver"):
            es = log_entries(log, kind)
            for e in es:
                m = run_of(e)
                assert m, f"{kind} detail not 'first-last (n years)': {e}"
                first, last, n = m
                assert e["year"] == first and n == last - first + 1, f"year/detail inconsistent: {e}"

    def test_no_run_is_split_when_contiguous(self, log):
        """Two entries of the same (kind, country, group) must not abut (they would be one run)."""
        by = defaultdict(list)
        for e in log:
            if e["kind"] in ("no_factor", "no_driver") and run_of(e):
                by[(e["kind"], e["country"], e["group"], str(e["detail"])[str(e["detail"]).find(")") + 1:])].append(run_of(e))
        for k, rs in by.items():
            rs = sorted(rs)
            for (a, b, _), (c, d, _) in itertools.pairwise(rs):
                assert c > b + 1 or c <= b, f"adjacent runs {rs} for {k}: must be one entry"

    def test_world_series_entries_use_xxx_never_xwl(self, log):
        assert not [e for e in log if e["country"] == "XWL"], "log entries must use the output country convention (XXX), not XWL"

    def test_pre1950_walk_logged_as_aggregated_runs(self, log):
        """4.6: the 1800-1949 absence of uranium / reactor / reprocessing factors is visible as aggregated runs."""
        early = [e for e in log if e["kind"] in ("no_factor", "no_driver") and e["year"] != "" and e["year"] is not None
                 and int(e["year"]) < 1950]
        assert early, "no log entries for years before 1950 (4.6 says the omission is visible)"
        assert len(early) < 400, f"{len(early)} pre-1950 entries: per-year entries instead of aggregated runs?"

    def test_i131_reprocessing_air_gap_is_a_run_per_site_country(self, log, oracle):
        for c in ("FRA", "GBR"):
            yrs = [y for y in range(1998, 2003) if oracle.has("nuc_reprocessed_gwa", y, c)
                   and not oracle.is_zero(oracle.a("nuc_reprocessed_gwa", y, c))]
            premise(len(yrs) == 5, f"{c} reprocessing has a non-zero driver in every year 1998-2002")
            es = [e for e in log_entries(log, "no_factor", country=c, group="I131") if e["year"] == 1998]
            assert any(str(e["detail"]).startswith("1998-2002 (5 years)") for e in es), \
                f"{c}: I131 air gap 1998-2002 not logged as one run: {[e['detail'] for e in log_entries(log, 'no_factor', country=c, group='I131')]}"

    def test_no_family_for_fbr(self, log):
        es = log_entries(log, "no_family")
        txt = [json.dumps(e, default=str) for e in es]
        assert any("fbr" in t for t in txt), f"no no_family entries naming fbr: {es}"
        assert len(es) >= 2, f"expected fbr in-core and fbr spent-fuel no_family entries, got {es}"
        assert len({t for t in txt}) == len(txt), "no_family must be logged once per family"

    def test_event_not_modelled_only_tokaimura(self, log):
        es = log_entries(log, "event_not_modelled")
        assert len(es) == 1, f"expected exactly one event_not_modelled (E008), got {es}"
        assert "marker only" in str(es[0]["detail"]), es[0]
        for eid in ("E002", "E003", "E004", "E013"):
            assert eid not in json.dumps(es[0], default=str), f"{eid} must not be reported as not modelled"

    def test_no_inventory_for_tmi_noble_gases(self, log):
        es = log_entries(log, "no_inventory")
        for g in ("Kr88+", "Xe133m"):
            m = [e for e in es if e["group"] == g]
            assert len(m) == 1, f"expected one no_inventory entry for {g}, got {m}"
        assert not [e for e in es if e["group"] in ("Np239", "La140", "Nb95")], "E004 groups all have inventory (7.5)"

    def test_no_release_exceeds_inventory_in_real_data_for_groups_with_inventory(self, log, expected):
        for eid in ("E002", "E004", "E013"):
            for g, v in expected.events[eid]["groups"].items():
                if v["has_inv"] and v["neg"]:
                    assert [e for e in log_entries(log, "release_exceeds_inventory") if e["group"] == g], \
                        f"{eid} {g}: central release exceeds inventory but nothing logged"

    def test_negative_residual_none_in_real_data(self, log, expected):
        assert not expected.negative_residual
        assert not log_entries(log, "negative_residual")

    def test_predecessor_rule_inert_in_real_data(self, log, expected):
        premise(not expected.predecessor_dropped, "CSK and CZE never overlap in u_production")
        assert not log_entries(log, "predecessor_dropped")

    def test_single_lib_warning_entry(self, log):
        w = log_entries(log, "lib_warning")
        assert len(w) == 1, f"expected exactly one lib_warning entry, found {len(w)}"
        assert w[0]["year"] in (None, "") and w[0]["country"] in (None, ""), f"year/country must be empty: {w[0]}"
        m = re.search(r"\d+", str(w[0]["detail"]))
        assert m and int(m.group()) >= 1, f"detail must carry the count: {w[0]['detail']!r}"
        assert re.search(r"[A-Za-z]{4,}", str(w[0]["detail"])), "detail must name the message type"


class TestStderr:
    def test_build_writes_nothing_to_stderr_subprocess(self):
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
        code = ("import sys; from pathlib import Path; from pipeline.streams.nuclear import build; "
                "r = build(Path(sys.argv[1])); print(len(r.rows))")
        p = subprocess.run([sys.executable, "-W", "default", "-c", code, str(ROOT)], cwd=str(ROOT), env=env,
                           capture_output=True, text=True, timeout=1800, check=False)
        assert p.returncode == 0, p.stderr[-1500:]
        assert p.stderr == "", f"build() wrote {len(p.stderr)} bytes to stderr (3.7): {p.stderr[:600]!r}"


# --------------------------------------------------------------------------------------------
# (c) conservation and events
# --------------------------------------------------------------------------------------------
def balance_groups(rows_obj: Rows) -> dict:
    g = defaultdict(lambda: {"in": [], "out": []})
    for r in rows_obj.rows:
        if r["quantity"] == "transfer_in":
            g[(r["stage"], r["country"], int(r["year"]), r["group"], r["allocation_variant"])]["in"].append(r)
        elif r["quantity"] == "transfer_out":
            g[(r["stage"], r["country"], int(r["year"]), r["group"], r["allocation_variant"])]["out"].append(r)
    return g


class TestTransferBalance:
    def test_every_balance_key_balances_at_all_three_bounds(self, rows, expected):
        bad = []
        groups = balance_groups(rows)
        want = {(k[2], k[3], k[0], k[4], "default") for k in expected.rows if k[6] in ("transfer_in", "transfer_out")}
        assert set(groups) == want, f"balance keys differ from the oracle's: {len(groups)} vs {len(want)}"
        for k, v in groups.items():
            if len(v["out"]) != 1 or not v["in"]:
                bad.append(f"{k}: {len(v['out'])} transfer_out, {len(v['in'])} transfer_in")
                continue
            o = vals(v["out"][0])
            s = [sum(vals(r)[i] for r in v["in"]) for i in range(3)]
            for name, a, b in zip(("low", "central", "high"), o, s):
                if not close(a, b, BAL):
                    bad.append(f"{k}: transfer_out {name} {a!r} != sum of transfer_in {b!r}")
        assert not bad, f"{len(bad)} unbalanced keys, first: {bad[:4]}"

    def test_stages_with_transfers(self, rows):
        stages = {r["stage"] for r in rows.rows if r["quantity"] == "transfer_in"}
        assert stages == {"conv_enrich_fab", "reprocessing", "sea_disposal", "accident", "u_milling"}, stages

    def test_two_route_case_u238_2010(self, rows, oracle):
        ins = rows.find(2010, stage="conv_enrich_fab", group="U238+", quantity="transfer_in")
        assert sorted(r["route"] for r in ins) == ["air_stack", "water_liquid_effluent"]
        out = rows.one(2010, stage="conv_enrich_fab", group="U238+", quantity="transfer_out")
        assert out["tier"] == "sealed_fuel_cycle" and _blank(out["route"])
        for i in range(3):
            assert close(vals(out)[i], sum(vals(r)[i] for r in ins), BAL)
        assert len(ids(out["factor_ids"])) == 2, f"transfer_out factor_ids {out['factor_ids']} must list both routes"

    def test_one_route_case_th230_2010(self, rows):
        ins = rows.find(2010, stage="conv_enrich_fab", group="Th230", quantity="transfer_in")
        assert len(ins) == 1 and ins[0]["route"] == "air_stack"
        out = rows.one(2010, stage="conv_enrich_fab", group="Th230", quantity="transfer_out")
        assert vals(out) == pytest.approx(vals(ins[0]), rel=1e-12), "one route: transfer_out equals transfer_in"

    def test_each_site_country_balances_alone(self, rows):
        for st in ("reprocessing", "sea_disposal"):
            countries = {r["country"] for r in rows.find(stage=st)}
            assert len(countries) >= 2, f"{st}: only {countries}"
            for c in countries:
                ins = [r for r in rows.find(2005 if st == "reprocessing" else 1967, stage=st, country=c, group="H3",
                                            quantity="transfer_in")]
                outs = [r for r in rows.find(2005 if st == "reprocessing" else 1967, stage=st, country=c, group="H3",
                                             quantity="transfer_out")]
                if ins:
                    assert len(outs) == 1 and close(vals(outs[0])[1], sum(vals(r)[1] for r in ins), BAL), (st, c)


class TestEventTotals:
    @pytest.mark.parametrize("eid", ["E002", "E004", "E013"])
    def test_release_sum_matches_events_csv(self, rows, oracle, eid):
        want = float(oracle.events[eid]["activity_central_bq"])
        tot = sum(float(r["value_central"]) for r in rows.rows
                  if r["event_id"] == eid and r["quantity"] == "transfer_in" and r["tier"] == "liberated")
        assert abs(tot - want) <= 1e-4 * want, f"{eid}: liberated transfer_in sum {tot:.6e} vs events.csv {want:.6e}"

    def test_church_rock_all_receiving_rows_sum_to_activity(self, rows, oracle):
        want = float(oracle.events["E003"]["activity_central_bq"])
        tot = sum(float(r["value_central"]) for r in rows.rows if r["event_id"] == "E003" and r["quantity"] == "transfer_in")
        assert abs(tot - want) <= 1e-4 * want, f"E003 transfer_in sum {tot:.6e} vs events.csv {want:.6e}"


class TestRemainder:
    """9(c)3. I and R come from the oracle's own reading of the registry; the rows are output."""

    @pytest.mark.parametrize("eid", ["E002", "E004", "E013"])
    def test_remainder_identities_every_group(self, rows, expected, eid):
        info = expected.events[eid]
        y, c, t = info["year"], info["country"], info["type"]
        bad = []
        for g, v in info["groups"].items():
            I, R = v["I"], v["R"]
            out = rows.find(y, substream=t, stage="accident", country=c, group=g, quantity="transfer_out", event_id=eid)
            if len(out) != 1:
                bad.append(f"{g}: {len(out)} transfer_out rows")
                continue
            o = vals(out[0])
            lib = rows.find(y, substream=t, stage="accident", country=c, group=g, quantity="transfer_in", tier="liberated", event_id=eid)
            dmg = rows.find(y, substream=t, stage="accident", country=c, group=g, quantity="transfer_in",
                            tier="sealed_damaged_core", event_id=eid)
            Rc = sum(float(r["value_central"]) for r in lib)
            Dc = float(dmg[0]["value_central"]) if dmg else 0.0
            if not close(Rc, R.central, REL):
                bad.append(f"{g}: release central {Rc!r} vs registry {R.central!r}")
            if not close(Dc, max(I.central - R.central, 0.0), REL):
                bad.append(f"{g}: D central {Dc!r} != max(I-R,0) = {max(I.central - R.central, 0.0)!r}")
            if not close(o[1], Rc + Dc, REL):
                bad.append(f"{g}: O central {o[1]!r} != R + D = {Rc + Dc!r}")
            if o[1] < I.central * (1 - 1e-9):
                bad.append(f"{g}: O central {o[1]!r} below inventory {I.central!r}")
            if not close(o[1], max(I.central, R.central), REL):
                bad.append(f"{g}: O central {o[1]!r} != max(I,R)")
            # bound-wise balance
            ins = lib + dmg
            for i, name in enumerate(("low", "central", "high")):
                if not close(o[i], sum(vals(r)[i] for r in ins), BAL):
                    bad.append(f"{g}: transfer_out {name} does not balance")
            if v["has_inv"] and v["D"].central == 0 and v["D"].low == 0 and v["D"].high == 0 and dmg:
                bad.append(f"{g}: exact 0/0/0 damaged-core row must be omitted")
        assert not bad, f"{eid}: {len(bad)} problems, first: {bad[:5]}"

    def test_e004_kr85_has_no_damaged_core_row(self, rows):
        assert rows.find(1986, stage="accident", group="Kr85", tier="sealed_damaged_core", event_id="E004") == []
        assert rows.find(1986, stage="accident", group="Kr85", tier="sealed_in_core", quantity="transfer_out", event_id="E004")

    @pytest.mark.parametrize("g", ["La140", "Nb95"])
    def test_e004_inventory_only_groups_go_wholly_to_damaged_core(self, rows, expected, g):
        v = expected.events["E004"]["groups"][g]
        premise(not v["has_rel"] and v["has_inv"], f"E004 {g} has an inventory row and no release row")
        assert not rows.find(1986, stage="accident", group=g, tier="liberated", event_id="E004")
        out = rows.one(1986, stage="accident", group=g, tier="sealed_in_core", quantity="transfer_out", event_id="E004")
        dmg = rows.one(1986, stage="accident", group=g, tier="sealed_damaged_core", event_id="E004")
        assert vals(out) == pytest.approx(vals(dmg), rel=1e-12), "transfer_out must equal the damaged-core remainder"
        for i, x in enumerate((v["I"].low, v["I"].central, v["I"].high)):
            assert close(vals(dmg)[i], x, REL), f"{g}: damaged-core remainder {vals(dmg)} != inventory"

    def test_e004_np239_has_inventory_and_remainder(self, rows, oracle):
        inv = _factor(oracle, "nuclear:1667")
        rel = _factor(oracle, "nuclear:1648")
        premise(inv["group"] == "Np239" and inv["region"] == "SUN" and inv["tier"] == "sealed_in_core"
                and rel["group"] == "Np239", "nuclear:1667 is the E004 Np239 inventory, nuclear:1648 its release")
        I, R = float(inv["value_central"]), float(rel["value_central"])
        dmg = rows.one(1986, stage="accident", group="Np239", tier="sealed_damaged_core", event_id="E004")
        assert close(float(dmg["value_central"]), I - R, REL), f"Np239 D central {dmg['value_central']} != I - R = {I - R:.6e}"
        assert 5.7e19 < float(dmg["value_central"]) < 5.9e19

    def test_e004_cs137_damaged_remainder(self, rows, oracle):
        inv = oracle.select(1986, "SUN", stage="accident", group="Cs137+", tier="sealed_in_core", route="")
        rel = oracle.select(1986, "SUN", stage="accident", group="Cs137+", tier="liberated", route="air_accident_release")
        dmg = rows.one(1986, stage="accident", group="Cs137+", tier="sealed_damaged_core", event_id="E004")
        want = max(float(inv["value_central"]) - float(rel["value_central"]), 0.0)
        assert close(float(dmg["value_central"]), want, REL)
        assert ids(dmg["factor_ids"])[0] == inv["factor_id"], "E004 damaged-core row must list the inventory factor first"

    @pytest.mark.parametrize("eid,gs", [("E013", ["Cs137+", "I131", "Xe133", "Te132+"]), ("E002", ["Xe133", "Xe135", "I131"])])
    def test_generic_inventory_is_capacity_times_in_core_factor(self, rows, oracle, expected, eid, gs):
        info = expected.events[eid]
        y, c, t = info["year"], info["country"], info["type"]
        cap = oracle.capacity_row(eid)
        premise(cap["unit"] == "GW" and cap["description"].startswith(eid), f"{eid} capacity row has unit GW and starts with the event ID")
        C = oracle.fb(cap)
        for g in gs:
            f = oracle.select(y, "XWL", stage="reactor_operation", group=g, tier="sealed_in_core", route="", driver_series=f"nuc_cap_{t}")
            I = prod(C, oracle.fb(f))
            out = rows.one(y, stage="accident", group=g, tier="sealed_in_core", quantity="transfer_out", event_id=eid)
            rel_rows = oracle.select(y, c, stage="accident", group=g, tier="liberated", route="air_accident_release")
            Rb = oracle.fb(rel_rows)
            assert close(float(out["value_central"]), max(I.central, Rb.central), REL), f"{eid} {g}: O != max(I, R) with I = C x in-core factor"
            fid = ids(out["factor_ids"])
            assert fid[:2] == [cap["factor_id"], f["factor_id"]], f"{eid} {g}: factor_ids {fid} must start with capacity id then in-core id"

    def test_release_exceeds_inventory_logged_for_groups_with_inventory(self, log, expected):
        # real data: central release never exceeds inventory except where I = 0
        for eid, info in expected.events.items():
            if eid == "E003":
                continue
            for g, v in info["groups"].items():
                if v["has_inv"]:
                    assert not v["neg"], f"{eid} {g}: premise: release exceeds inventory in the real data"


class TestTMI2:
    FIVE: ClassVar[set[str]] = {"Xe133", "Kr88+", "Xe135", "Xe133m", "I131"}

    def test_release_rows_exactly_five_groups_all_air(self, rows):
        lib = rows.find(1979, stage="accident", tier="liberated", event_id="E002", quantity="transfer_in")
        assert {r["group"] for r in lib} == self.FIVE, f"E002 releases {sorted(r['group'] for r in lib)}"
        assert {r["route"] for r in lib} == {"air_accident_release"}
        assert not rows.find(1979, stage="accident", group="Kr85", tier="liberated", event_id="E002"), \
            "E002 has no Kr85 release row (7.2); the Kr85 inventory-derived rows are a separate matter"

    def test_noble_gas_centrals_sum_to_events_csv(self, rows, oracle):
        want = float(oracle.events["E002"]["activity_central_bq"])
        ng = sum(float(r["value_central"]) for r in rows.find(1979, stage="accident", tier="liberated", event_id="E002",
                                                              quantity="transfer_in") if r["group"] != "I131")
        assert close(ng, want, 1e-6), f"four noble-gas centrals sum to {ng:.9e}, events.csv central {want:.9e}"
        five = ng + float(rows.one(1979, stage="accident", tier="liberated", event_id="E002", group="I131",
                                   quantity="transfer_in")["value_central"])
        assert abs(five - want) <= 1e-4 * want

    @pytest.mark.parametrize("g", ["Kr88+", "Xe133m"])
    def test_groups_without_inventory(self, rows, g):
        lib = rows.one(1979, stage="accident", group=g, tier="liberated", event_id="E002", quantity="transfer_in")
        out = rows.one(1979, stage="accident", group=g, tier="sealed_in_core", event_id="E002", quantity="transfer_out")
        assert vals(out) == pytest.approx(vals(lib), rel=1e-12), f"{g}: transfer_out must equal the release (I = 0)"
        assert not rows.find(1979, stage="accident", group=g, tier="sealed_damaged_core", event_id="E002")

    def test_event_high_and_bounds_of_noble_rows(self, rows, oracle):
        hi = float(oracle.events["E002"]["activity_high_bq"])
        lo = float(oracle.events["E002"]["activity_low_bq"])
        ng = [r for r in rows.find(1979, stage="accident", tier="liberated", event_id="E002", quantity="transfer_in")
              if r["group"] != "I131"]
        assert close(sum(float(r["value_high"]) for r in ng), hi, 1e-4)
        assert close(sum(float(r["value_low"]) for r in ng), lo, 1e-4)


class TestChurchRock:
    def test_pairs_balance_and_shares(self, rows, oracle):
        e = oracle.events["E003"]
        A = float(e["activity_central_bq"])
        shares = [f for f in oracle.factors if f["description"].startswith("E003") and f["stage"] == "u_milling"]
        premise(len(shares) == 16 and abs(sum(float(f["value_central"]) for f in shares) - 1) < 1e-4,
                "16 E003 share rows summing to 1 +/- 1e-4")
        ins = rows.find(1979, stage="u_milling", event_id="E003", quantity="transfer_in")
        outs = rows.find(1979, stage="u_milling", event_id="E003", quantity="transfer_out")
        assert len(ins) == 16 and len(outs) == 9, f"{len(ins)} transfer_in / {len(outs)} transfer_out rows, expected 16 / 9"
        for f in shares:
            m = [r for r in ins if r["group"] == f["group"] and r["tier"] == f["tier"] and (r["route"] or "") == f["route"]]
            assert len(m) == 1, f"E003 share row {f['factor_id']} has {len(m)} output rows"
            assert close(float(m[0]["value_central"]), A * float(f["value_central"]), REL), f"{f['factor_id']}: central != A x share"
            assert ids(m[0]["factor_ids"]) == [f["factor_id"]]
        for o in outs:
            mine = [r for r in ins if r["group"] == o["group"]]
            for i in range(3):
                assert close(vals(o)[i], sum(vals(r)[i] for r in mine), BAL), f"{o['group']}: pair does not balance"
            assert o["tier"] == "impounded" and o["residue_type"] == "u_tailings" and _blank(o["route"])

    def test_row_constants(self, rows):
        for r in rows.rows:
            if r["event_id"] == "E003":
                assert r["stage"] == "u_milling" and r["country"] == "USA" and ids(r["allocation_rule"]) == ["civil:doc"], describe(r)
                assert r["substream"] == "fuel_cycle"
                if r["tier"] == "liberated":
                    assert r["route"] == "water_spill" and _blank(r["residue_type"]), describe(r)
                if r["tier"] == "dispersed":
                    assert _blank(r["route"]) and r["residue_type"] == "u_tailings", describe(r)

    def test_th230_pair_hand_computed(self, rows, oracle):
        e = oracle.events["E003"]
        A = B(float(e["activity_low_bq"]), float(e["activity_central_bq"]), float(e["activity_high_bq"]))
        f = oracle.select(1979, "USA", stage="u_milling", group="Th230", tier="liberated", route="water_spill",
                          residue_type="u_tailings", driver_series="")
        r = rows.one(1979, stage="u_milling", group="Th230", tier="liberated", event_id="E003", quantity="transfer_in")
        assert_bounds(r, prod(A, oracle.fb(f)), label="E003 Th230 liberated")
        assert ids(r["factor_ids"]) == [f["factor_id"]]
        assert set(ids(r["source_ids"])) >= set(f["source_ids"].split(";")) | set(e["source_ids"].split(";"))


class TestNoDoubleCounting:
    def test_no_flow_at_accident_and_event_ids(self, rows):
        assert not rows.find(stage="accident", quantity="flow")
        for r in rows.find(stage="accident"):
            assert r["event_id"], describe(r)
        for r in rows.rows:
            if r["event_id"]:
                assert r["stage"] == "accident" or (r["stage"] == "u_milling" and r["event_id"] == "E003"), describe(r)

    def test_event_group_route_tier_unique(self, rows):
        c = Counter((r["event_id"], r["group"], r["route"] or "", r["quantity"], r["tier"]) for r in rows.rows if r["event_id"])
        dup = [k for k, v in c.items() if v > 1]
        assert not dup, f"duplicate (event, group, route, quantity, tier): {dup[:3]}"

    def test_2011_reactor_effluents_are_driver_times_factor(self, rows, oracle):
        """No accident adjustment in an accident year (7.4 item 2)."""
        n = 0
        for r in rows.find(2011, stage="reactor_operation", quantity="flow"):
            t = r["substream"]
            f = oracle.select(2011, "XWL", stage="reactor_operation", group=r["group"], tier="liberated", route=r["route"],
                              driver_series=f"nuc_gen_{t}")
            G = scale(oracle.a(f"nuc_gen_{t}", 2011, "XWL"), 1 / GWA_TWH)
            assert_bounds(r, prod(G, oracle.fb(f)), label="2011 effluent")
            n += 1
        want = sum(1 for t in TYPES for (g, route) in oracle.family(stage="reactor_operation", tier="liberated", driver_series=f"nuc_gen_{t}")
                   if oracle.try_select(2011, "XWL", stage="reactor_operation", group=g, tier="liberated", route=route,
                                        driver_series=f"nuc_gen_{t}") is not None)
        assert n == want, f"{n} reactor effluent rows in 2011, registry gives {want}"

    def test_in_core_baseline_continues_after_accident(self, rows):
        """7.4 item 3 / METHODS 5.4: the destroyed unit's in-core rows are not reduced by the script."""
        for t, years in (("pwr", (1979, 1980)), ("lwgr", (1986, 1987)), ("bwr", (2011, 2012))):
            for y in years:
                assert rows.find(y, substream=t, stage="reactor_operation", quantity="standing_inventory", group="Cs137+"), \
                    f"{t} {y}: in-core baseline row missing"


class TestMemoRows:
    def test_memo_rows_recomputed(self, rows, oracle):
        for y in (1950, 1960, 1964, 1965, 1975, 1988):
            P = oracle.a("u_production", y, "USA")
            s_row = oracle.select(y, "USA", stage="u_mining_isl", group="", tier="", route="", residue_type="", driver_series="")
            phi = oracle.a("phi_civil", y, "XWL")
            Tconv = prod(P, comp(oracle.fb(s_row)), phi)
            for g in ("Ra226+", "U238+"):
                f = oracle.select(y, "USA", stage="u_mining_conv", group=g, tier="memo_earth_moved", route="",
                                  residue_type="", driver_series="u_production")
                r = rows.one(y, stage="u_mining_conv", country="USA", group=g, tier="memo_earth_moved", quantity="flow")
                assert_bounds(r, prod(Tconv, oracle.fb(f)), label=f"memo {g} {y}")
                assert ids(r["factor_ids"]) == [s_row["factor_id"], f["factor_id"]]
                assert ids(r["allocation_rule"]) == (["civil:pre1965"] if y <= 1964 else ["civil:ratio"])
                if y <= 1964:
                    assert vals(r) == (0.0, 0.0, 0.0) and float(r["value_high"]) == 0

    def test_memo_rows_not_in_tier_totals(self, rows):
        tiers = Counter(r["tier"] for r in rows.find(stage="u_mining_conv"))
        assert tiers["memo_earth_moved"] == 273 and set(tiers) == {"liberated", "memo_earth_moved"}, tiers

    def test_ra226_1975_value(self, rows, oracle):
        """The spec's own example: Ra226+, USA, 1975, civil:ratio."""
        r = rows.one(1975, stage="u_mining_conv", country="USA", group="Ra226+", tier="memo_earth_moved")
        f = oracle.select(1975, "USA", stage="u_mining_conv", group="Ra226+", tier="memo_earth_moved", route="",
                          residue_type="", driver_series="u_production")
        premise(float(f["value_central"]) > 1e9, "Ra226+ memo central of the order 1e10 Bq per t U")
        assert ids(r["allocation_rule"]) == ["civil:ratio"] and float(r["value_central"]) > 0


class TestTonnagePartition:
    def test_conv_plus_isl_equals_all(self, rows, oracle):
        n = 0
        for r3 in rows.rows:
            if not (r3["stage"] == "u_milling" and r3["group"] == "Rn222+" and r3["tier"] == "liberated"):
                continue
            y, c = int(r3["year"]), r3["country"]
            if y < 1965 or float(r3["value_central"]) == 0:
                continue
            region = "XWL" if c == "XXX" else c
            f3 = oracle.select(y, region, stage="u_milling", group="Rn222+", tier="liberated", route="air_process_vent")
            f1 = oracle.select(y, region, stage="u_mining_conv", group="Rn222+", tier="liberated", route="air_ventilation", driver_series="u_production")
            f2 = oracle.select(y, region, stage="u_mining_isl", group="Rn222+", tier="liberated", route="air_process_vent", driver_series="u_production")
            r1 = rows.find(y, stage="u_mining_conv", country=c, group="Rn222+", tier="liberated")
            r2 = rows.find(y, stage="u_mining_isl", country=c, group="Rn222+", tier="liberated")
            assert r1 and r2, f"{c} {y}: F1 or F2 row missing"
            Tall = float(r3["value_central"]) / float(f3["value_central"])
            Tconv = float(r1[0]["value_central"]) / float(f1["value_central"])
            Tisl = float(r2[0]["value_central"]) / float(f2["value_central"])
            assert math.isclose(Tconv + Tisl, Tall, rel_tol=1e-9), f"{c} {y}: Tconv {Tconv} + Tisl {Tisl} != Tall {Tall}"
            n += 1
        assert n > 1000, f"only {n} country-years checked"


class TestMillBalance:
    def test_tailings_to_product_ratio(self, rows, oracle):
        f12, f21 = _factor(oracle, "nuclear:0012"), _factor(oracle, "nuclear:0021")
        premise(f12["group"] == f21["group"] == "U238+" and f12["tier"] == "sealed_fuel_cycle" and f21["tier"] == "impounded",
                "nuclear:0012 / 0021 are the U238+ product and tailings factors")
        ratio = float(f21["value_central"]) / float(f12["value_central"])
        premise(abs(ratio - 0.05 / 0.95) < 1e-3, f"tailings/product factor ratio {ratio} is R:(1-R) with R = 0.95, i.e. 0.0526")
        n = 0
        for r5 in rows.rows:
            if not (r5["stage"] == "u_milling" and r5["group"] == "U238+" and r5["tier"] == "sealed_fuel_cycle"):
                continue
            y, c = int(r5["year"]), r5["country"]
            if y < 1965 or float(r5["value_central"]) == 0 or y % 5:
                continue
            r6 = rows.find(y, stage="u_milling", country=c, group="U238+", tier="impounded", quantity="flow")
            assert r6, f"{c} {y}: no tailings row"
            region = "XWL" if c == "XXX" else c
            s = oracle.fb(oracle.select(y, region, stage="u_mining_isl", group="", tier="", route="", residue_type="", driver_series=""))
            want = ratio * (1 - s.central)
            got = float(r6[0]["value_central"]) / float(r5["value_central"])
            assert close(got, want, 1e-6), f"{c} {y}: tailings/product {got} != 0.0526 x (1 - s) = {want}"
            n += 1
        assert n > 100


# --------------------------------------------------------------------------------------------
# (f) hand-computed cases (recomputed in the test from the files)
# --------------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def O(oracle):
    return oracle


class TestHandComputed:

    def _isl(self, O, y, c):
        return O.select(y, c, stage="u_mining_isl", group="", tier="", route="", residue_type="", driver_series="")

    def test_f1_kaz_2010_own_isl_share(self, rows, O):
        P, phi = O.a("u_production", 2010, "KAZ"), O.a("phi_civil", 2010, "XWL")
        s_row = self._isl(O, 2010, "KAZ")
        premise(s_row["region"] == "KAZ" and float(s_row["value_central"]) > 0.9, "KAZ has its own ISL row, central above 0.9 in 2010")
        f = O.select(2010, "XWL", stage="u_mining_conv", group="Rn222+", tier="liberated", route="air_ventilation", driver_series="u_production")
        r = rows.one(2010, stage="u_mining_conv", country="KAZ", group="Rn222+", tier="liberated", quantity="flow")
        exp = prod(prod(P, comp(O.fb(s_row)), phi), O.fb(f))
        assert_bounds(r, exp, label="F1 KAZ 2010")
        assert ids(r["factor_ids"]) == [s_row["factor_id"], f["factor_id"]]
        assert as_bool(r["below_detection"]) and notes_parts(r["notes"])["cause"] == ["floor_dominance"]
        assert r["route"] == "air_ventilation" and ids(r["allocation_rule"]) == ["civil:ratio"] and r["unit"] == "Bq/a"

    def test_f1_can_2010_uses_xwl_default(self, rows, O):
        s_row = self._isl(O, 2010, "CAN")
        assert s_row["factor_id"] == "nuclear:1701", f"CAN 2010 ISL default should be nuclear:1701, registry gives {s_row['factor_id']}"
        P, phi = O.a("u_production", 2010, "CAN"), O.a("phi_civil", 2010, "XWL")
        f = O.select(2010, "XWL", stage="u_mining_conv", group="Rn222+", tier="liberated", route="air_ventilation", driver_series="u_production")
        r = rows.one(2010, stage="u_mining_conv", country="CAN", group="Rn222+", tier="liberated", quantity="flow")
        assert_bounds(r, prod(prod(P, comp(O.fb(s_row)), phi), O.fb(f)), label="F1 CAN 2010")
        assert ids(r["factor_ids"])[0] == "nuclear:1701"

    def test_aus_2020_takes_1702_known_understated_default(self, rows, O):
        r = rows.one(2020, stage="u_mining_conv", country="AUS", group="Rn222+", tier="liberated", quantity="flow")
        assert ids(r["factor_ids"])[0] == "nuclear:1702", f"AUS 2020 must take the XWL 2020-25 default 1702, got {r['factor_ids']}"
        r2 = rows.one(2020, stage="u_mining_isl", country="AUS", group="Rn222+", tier="liberated", quantity="flow")
        assert ids(r2["factor_ids"])[0] == "nuclear:1702"
        P, phi = O.a("u_production", 2020, "AUS"), O.a("phi_civil", 2020, "XWL")
        f = O.select(2020, "XWL", stage="u_mining_conv", group="Rn222+", tier="liberated", route="air_ventilation", driver_series="u_production")
        assert_bounds(r, prod(prod(P, comp(O.fb(_factor(O, "nuclear:1702"))), phi), O.fb(f)), label="F1 AUS 2020")

    def test_pre1965_zero_row_and_1965_ratio_row(self, rows, O):
        for y, rule in ((1960, "civil:pre1965"), (1965, "civil:ratio")):
            r = rows.one(y, stage="u_mining_conv", country="CAN", group="Rn222+", tier="liberated", quantity="flow")
            assert ids(r["allocation_rule"]) == [rule]
            if y == 1960:
                assert vals(r) == (0.0, 0.0, 0.0) and float(r["value_high"]) == 0 and not as_bool(r["below_detection"])
            else:
                P, phi = O.a("u_production", 1965, "CAN"), O.a("phi_civil", 1965, "XWL")
                premise(0 < phi.central < 1, "phi_civil(1965) is in (0, 1)")
                f = O.select(1965, "XWL", stage="u_mining_conv", group="Rn222+", tier="liberated", route="air_ventilation", driver_series="u_production")
                s = O.fb(self._isl(O, 1965, "CAN"))
                assert_bounds(r, prod(prod(P, comp(s), phi), O.fb(f)), label="F1 CAN 1965")
                assert float(r["value_high"]) > 0

    def test_rest_of_world_2020_residual(self, rows, O):
        listed = O.countries("u_production", 2020)
        from nuclear_oracle import diff
        R, _raw = diff(O.a("u_production", 2020, "XWL"), sum_independent([O.a("u_production", 2020, c) for c in listed]))
        assert 130.5 < R.central < 131.5, f"2020 residual {R.central}, spec says 131 t U"
        phi = O.a("phi_civil", 2020, "XWL")
        f = O.select(2020, "XWL", stage="u_milling", group="U238+", tier="sealed_fuel_cycle", route="")
        r = rows.one(2020, stage="u_milling", country="XXX", group="U238+", tier="sealed_fuel_cycle", quantity="flow")
        assert_bounds(r, prod(prod(R, phi), O.fb(f)), label="rest of world F5 2020")
        assert "rest of world (world aggregate minus listed countries)" in r["notes"]
        assert as_bool(r["below_detection"]) and notes_parts(r["notes"])["cause"] == ["clipped_difference"], r["notes"]
        s = O.fb(self._isl(O, 2020, "XWL"))
        f6 = O.select(2020, "XWL", stage="u_milling", group="Th230", tier="impounded", route="", residue_type="u_tailings")
        r6 = rows.one(2020, stage="u_milling", country="XXX", group="Th230", tier="impounded", quantity="flow")
        assert_bounds(r6, prod(prod(R, comp(s), phi), O.fb(f6)), label="rest of world F6 2020")
        assert ids(r6["factor_ids"])[0] == "nuclear:1702", "the rest-of-world row uses the XWL default ISL share"

    def test_f6_tailings_conventional_only_and_f5_all(self, rows, O):
        P, phi = O.a("u_production", 2010, "CAN"), O.a("phi_civil", 2010, "XWL")
        s = O.fb(self._isl(O, 2010, "CAN"))
        f6 = O.select(2010, "XWL", stage="u_milling", group="Th230", tier="impounded", route="", residue_type="u_tailings")
        r6 = rows.one(2010, stage="u_milling", country="CAN", group="Th230", tier="impounded", quantity="flow")
        assert_bounds(r6, prod(prod(P, comp(s), phi), O.fb(f6)), label="F6 CAN 2010")
        assert r6["residue_type"] == "u_tailings" and _blank(r6["route"])
        f5 = O.select(2010, "XWL", stage="u_milling", group="U238+", tier="sealed_fuel_cycle", route="")
        r5 = rows.one(2010, stage="u_milling", country="CAN", group="U238+", tier="sealed_fuel_cycle", quantity="flow")
        assert_bounds(r5, prod(prod(P, phi), O.fb(f5)), label="F5 CAN 2010")
        assert ids(r5["factor_ids"])[-1] == f5["factor_id"]
        assert _blank(r5["residue_type"]) and _blank(r5["route"])

    def test_f3_f4_mill_rows_use_all_civil_tonnage(self, rows, O):
        P, phi = O.a("u_production", 2010, "CAN"), O.a("phi_civil", 2010, "XWL")
        for g, route, tier in (("Rn222+", "air_process_vent", "liberated"), ("U238+", "air_dust", "liberated")):
            f = O.select(2010, "XWL", stage="u_milling", group=g, tier=tier, route=route)
            r = rows.one(2010, stage="u_milling", country="CAN", group=g, tier=tier, quantity="flow", route=route)
            assert_bounds(r, prod(prod(P, phi), O.fb(f)), label=f"F3/F4 {g}")

    def test_conv_enrich_fab_pair_u238_2010(self, rows, O):
        G = scale(O.a("elec_gen_nuclear", 2010, "XWL"), 1 / GWA_TWH)
        tot = []
        for route in ("air_stack", "water_liquid_effluent"):
            f = O.select(2010, "XWL", stage="conv_enrich_fab", group="U238+", tier="liberated", route=route, driver_series="elec_gen_nuclear")
            exp = prod(G, O.fb(f))
            r = rows.one(2010, stage="conv_enrich_fab", group="U238+", route=route, quantity="transfer_in")
            assert_bounds(r, exp, label=f"conv_enrich_fab U238+ {route}")
            assert r["country"] == "XXX" and r["substream"] == "fuel_cycle" and r["unit"] == "Bq" and ids(r["allocation_rule"]) == ["none"]
            tot.append(exp)
        out = rows.one(2010, stage="conv_enrich_fab", group="U238+", quantity="transfer_out")
        assert_bounds(out, sum_correlated(tot), label="transfer_out = correlated sum")

    def test_pwr_noble_gas_twh_to_gwa(self, rows, O):
        f = O.select(2010, "XWL", stage="reactor_operation", group="Xe133", tier="liberated", route="air_stack", driver_series="nuc_gen_pwr")
        G_twh = O.a("nuc_gen_pwr", 2010, "XWL")
        r = rows.one(2010, substream="pwr", stage="reactor_operation", group="Xe133", route="air_stack", quantity="flow")
        want = G_twh.central / GWA_TWH * float(f["value_central"])
        assert close(float(r["value_central"]), want, 1e-9), f"central {r['value_central']} != G/8.766 x factor = {want}"
        assert r["unit"] == "Bq/a" and r["country"] == "XXX"

    def test_standing_inventory_row(self, rows, O):
        f = O.select(2010, "XWL", stage="reactor_operation", group="Cs137+", tier="sealed_in_core", route="", driver_series="nuc_cap_pwr")
        premise(f["unit"] == "Bq/GW", "PWR in-core factor unit Bq/GW")
        C = O.a("nuc_cap_pwr", 2010, "XWL")
        r = rows.one(2010, substream="pwr", stage="reactor_operation", group="Cs137+", tier="sealed_in_core", quantity="standing_inventory")
        assert_bounds(r, prod(C, O.fb(f)), label="PWR Cs137+ standing inventory")
        assert r["unit"] == "Bq" and _blank(r["route"])

    def test_spent_fuel_row(self, rows, O):
        f = O.select(2010, "XWL", stage="spent_fuel", group="Cs137+", tier="sealed_fuel_cycle", route="", driver_series="nuc_gen_pwr")
        G = scale(O.a("nuc_gen_pwr", 2010, "XWL"), 1 / GWA_TWH)
        r = rows.one(2010, substream="pwr", stage="spent_fuel", group="Cs137+", tier="sealed_fuel_cycle", quantity="flow")
        assert_bounds(r, prod(G, O.fb(f)), label="PWR spent fuel Cs137+")
        assert r["unit"] == "Bq/a"

    def test_reprocessing_fra_2010_pair_and_country_code(self, rows, O):
        Gb = O.a("nuc_reprocessed_gwa", 2010, "FRA")
        for g in ("Pu239", "Pu240"):
            tot = []
            for route in ("air_stack", "water_liquid_effluent"):
                f = O.select(2010, "XWL", stage="reprocessing", group=g, tier="liberated", route=route)
                r = rows.one(2010, stage="reprocessing", country="FRA", group=g, route=route, quantity="transfer_in")
                exp = prod(Gb, O.fb(f))
                assert_bounds(r, exp, label=f"FRA reprocessing {g} {route}")
                assert ids(r["allocation_rule"]) == ["civil:throughput"] and r["substream"] == "fuel_cycle"
                tot.append(exp)
            out = rows.one(2010, stage="reprocessing", country="FRA", group=g, quantity="transfer_out")
            assert_bounds(out, sum_correlated(tot), label=f"FRA {g} transfer_out")
        assert not rows.find(2010, stage="reprocessing", country="XXX")

    def test_sea_disposal_bel_1970_and_us_flag(self, rows, O):
        # NUCLEAR_SPEC 9(f) names BEL 1970, but the BEL driver is 0/0/0 in 1970 (no rows, 4.1/5.3): 1971 is used.
        premise(O.is_zero(O.a("nuc_sea_dumped_tbq", 1970, "BEL")) and not O.is_zero(O.a("nuc_sea_dumped_tbq", 1971, "BEL")),
                "BEL sea-disposal driver is zero in 1970 and non-zero in 1971")
        assert not rows.find(1970, stage="sea_disposal", country="BEL"), "a zero driver gives no rows"
        D = scale(O.a("nuc_sea_dumped_tbq", 1971, "BEL"), 1e12)
        f = O.select(1971, "XWL", stage="sea_disposal", group="H3", tier="liberated", route="sea_disposal_package")
        r = rows.one(1971, stage="sea_disposal", country="BEL", group="H3", quantity="transfer_in")
        assert_bounds(r, prod(D, O.fb(f)), label="BEL 1970 H3 sea disposal")
        assert r["route"] == "sea_disposal_package" and ids(r["allocation_rule"]) == ["none"]
        assert not notes_parts(r["notes"])["civil_flag"]
        out = rows.one(1971, stage="sea_disposal", country="BEL", group="H3", quantity="transfer_out")
        assert vals(out) == pytest.approx(vals(r), rel=1e-12)
        us = rows.one(1960, stage="sea_disposal", country="USA", group="H3", quantity="transfer_in")
        assert "; civil share undocumented (D64)" in us["notes"]
        Du = scale(O.a("nuc_sea_dumped_tbq", 1960, "USA"), 1e12)
        fu = O.select(1960, "XWL", stage="sea_disposal", group="H3", tier="liberated", route="sea_disposal_package")
        assert_bounds(us, prod(Du, O.fb(fu)), label="USA 1960 H3 sea disposal")

    def test_pre1950_sea_flow_row(self, pre_rows, O):
        D = scale(O.a("nuc_sea_dumped_tbq", 1947, "USA"), 1e12)
        f = O.select(1947, "XWL", stage="sea_disposal", group="H3", tier="liberated", route="sea_disposal_package")
        r = pre_rows.one(1947, stage="sea_disposal", country="USA", group="H3", quantity="flow", tier="liberated")
        assert_bounds(r, prod(D, O.fb(f)), label="USA 1947 H3 sea flow")
        assert r["route"] == "sea_disposal_package" and r["unit"] == "Bq/a" and "civil share undocumented" in r["notes"]

    def test_e004_retained_group_cs137(self, rows, O):
        inv = O.fb(O.select(1986, "SUN", stage="accident", group="Cs137+", tier="sealed_in_core", route=""))
        rel = O.fb(O.select(1986, "SUN", stage="accident", group="Cs137+", tier="liberated", route="air_accident_release"))
        D, _ = remainder(inv, rel)
        dmg = rows.one(1986, stage="accident", group="Cs137+", tier="sealed_damaged_core", event_id="E004")
        assert_bounds(dmg, D, label="E004 Cs137+ damaged core", flag=None)
        out = rows.one(1986, stage="accident", group="Cs137+", tier="sealed_in_core", quantity="transfer_out", event_id="E004")
        assert close(float(out["value_central"]), max(inv.central, rel.central), REL)
        assert out["substream"] == "lwgr" and out["country"] == "SUN"

    def test_e013_generic_inventory_cs137(self, rows, O):
        cap = O.capacity_row("E013")
        f = O.select(2011, "XWL", stage="reactor_operation", group="Cs137+", tier="sealed_in_core", route="", driver_series="nuc_cap_bwr")
        I = prod(O.fb(cap), O.fb(f))
        R = sum_correlated([O.fb(x) for x in O.factors if x["stage"] == "accident" and x["region"] == "JPN"
                            and x["group"] == "Cs137+" and x["tier"] == "liberated"])
        D, _ = remainder(I, R)
        dmg = rows.one(2011, stage="accident", group="Cs137+", tier="sealed_damaged_core", event_id="E013")
        assert_bounds(dmg, D, label="E013 Cs137+ damaged core", flag=None)
        assert rows.one(2011, stage="accident", group="Cs137+", tier="sealed_in_core", quantity="transfer_out", event_id="E013")["substream"] == "bwr"
        assert len(rows.find(2011, stage="accident", group="Cs137+", tier="liberated", event_id="E013")) == 2, "air and water release rows"


# --------------------------------------------------------------------------------------------
# (h) pre-1950 file
# --------------------------------------------------------------------------------------------
class TestPre1950:
    def test_rows_match_oracle(self, comparison_pre, expected):
        assert expected.pre, "oracle expects pre-1950 sea-disposal flows"
        assert not comparison_pre, "pre-1950 rows differ from the oracle: " + show([m for v in comparison_pre.values() for m in v])

    def test_shape(self, pre_rows):
        assert {r["stage"] for r in pre_rows.rows} == {"sea_disposal"}
        assert {r["quantity"] for r in pre_rows.rows} == {"flow"}
        assert {r["tier"] for r in pre_rows.rows} == {"liberated"}
        assert {r["route"] for r in pre_rows.rows} == {"sea_disposal_package"}
        assert {int(r["year"]) for r in pre_rows.rows} == {1946, 1947, 1948, 1949}
        assert not [r for r in pre_rows.rows if r["tier"].startswith("memo")]
        assert {r["country"] for r in pre_rows.rows} == {"USA", "GBR"}
        assert len(pre_rows.rows) == 13 * 5, "USA 1946-49 and GBR 1949, 13 groups each"

    def test_each_row_passes_master_schema_with_relaxed_years(self, written):
        from jsonschema import Draft7Validator

        from pipeline.lib.io import read_table

        schema = json.loads((ROOT / "schema" / "master.json").read_text(encoding="utf-8"))
        schema["properties"]["year"]["minimum"] = 1800
        schema["properties"]["year"]["maximum"] = 1949
        v = Draft7Validator(schema)
        recs = read_table(written[1])
        assert recs
        for rec in recs:
            if isinstance(rec["allocation_rule"], list):  # the validator hands the schema the joined text
                rec["allocation_rule"] = ";".join(rec["allocation_rule"])
            errs = list(v.iter_errors(rec))
            assert not errs, f"pre-1950 row {rec['year']} {rec['group']} fails master.json: {errs[0].message}"

    def test_header_only_without_sea_series(self, nuclear_mod, tmp_path):
        root = make_mini(tmp_path, mini_act(sea=False))
        res = nuclear_mod.build(root)
        assert list(res.rows_pre1950) == [], "no nuc_sea_dumped_tbq: the pre-1950 file must be empty"


# --------------------------------------------------------------------------------------------
# (d) determinism
# --------------------------------------------------------------------------------------------
class TestDeterminism:
    def test_two_builds_write_identical_bytes_and_log(self, nuclear_mod, result, written, write_master, tmp_path):
        second = nuclear_mod.build(ROOT)
        m2, p2 = tmp_path / "n2.csv", tmp_path / "p2.csv"
        write_master(list(second.rows), m2)
        write_master(list(second.rows_pre1950), p2)
        assert Path(written[0]).read_bytes() == m2.read_bytes(), "master bytes differ between builds"
        assert Path(written[1]).read_bytes() == p2.read_bytes(), "pre-1950 bytes differ between builds"
        assert list(second.log) == list(result.log), "log differs (or is ordered differently) between builds"

    @pytest.mark.parametrize("idx", [0, 1])
    def test_written_rows_are_in_schema_key_order(self, written, idx):
        with open(written[idx], newline="", encoding="utf-8") as fh:
            data = list(csv.DictReader(fh))
        assert data
        cols = ["year", "stream", "substream", "stage", "product", "residue_type", "country", "group", "tier",
                "quantity", "allocation_variant", "embedded_fuel", "technology", "route", "event_id"]

        def key(r):
            return tuple((int(r[c]),) if c == "year" else ((0, "") if r[c] == "" else (1, r[c])) for c in cols)

        keys = [key(r) for r in data]
        assert keys == sorted(keys), "rows are not in SCHEMA 3 unique-key order"
        assert len(keys) == len(set(keys))


# --------------------------------------------------------------------------------------------
# (i) premise assertions (registry and data premises the tests rely on)
# --------------------------------------------------------------------------------------------
class TestPremises:
    def test_isl_default_and_mill_rows(self, oracle):
        f2 = _factor(oracle, "nuclear:0002")
        premise(f2["unit"] == "Bq/t" and abs(float(f2["value_central"]) - 3e11) < 1e6
                and int(f2["year_from"]) <= 2010 <= int(f2["year_to"]), "nuclear:0002 is 3e11 Bq/t, valid in 2010")
        for fid, stage in (("nuclear:0003", "u_mining_isl"), ("nuclear:0004", "u_milling")):
            premise(_factor(oracle, fid)["stage"] == stage, f"{fid} present at stage {stage}")

    def test_sea_disposal_shares(self, oracle):
        sh = [f for f in oracle.factors if f["stage"] == "sea_disposal"]
        premise(len(sh) == SEA_GROUPS_N, f"13 sea-disposal share rows, found {len(sh)}")
        premise(abs(sum(float(f["value_central"]) for f in sh) - 1) < 1e-3, "13 sea-disposal central shares sum to 1 +/- 1e-3")
        premise(all(int(f["year_from"]) <= 1946 and int(f["year_to"]) >= 1993 for f in sh), "sea-disposal shares valid 1946-1993")
        premise(all(f["unit"] == "1" and f["route"] == "sea_disposal_package" and f["region"] == "XWL" for f in sh),
                "sea-disposal shares are unit 1, route sea_disposal_package, region XWL")

    def test_kr85_reprocessing_factor(self, oracle):
        f = _factor(oracle, "nuclear:1565")
        premise(f["unit"] == "Bq/GWa" and f["group"] == "Kr85" and f["stage"] == "reprocessing", "nuclear:1565 is reprocessing Kr85 Bq/GWa")
        v = float(f["value_central"])
        premise(abs(v - 4.734e15) / 4.734e15 < 1e-3, f"nuclear:1565 = 4.734e15 Bq/GW.a, found {v}")
        premise(abs(v - 1.5e8 * 3.156e7) / v < 1e-3, "nuclear:1565 equals 1.5e8 Bq/s x 3.156e7 s")

    def test_pu_ratio(self, oracle):
        for route in ("air_stack", "water_liquid_effluent"):
            f9 = oracle.select(2010, "XWL", stage="reprocessing", group="Pu239", tier="liberated", route=route)
            f0 = oracle.select(2010, "XWL", stage="reprocessing", group="Pu240", tier="liberated", route=route)
            r = float(f0["value_central"]) / float(f9["value_central"])
            premise(abs(r - 1.59) <= 0.01, f"Pu240/Pu239 central ratio of the 2003-25 {route} rows is 1.59 +/- 0.01, found {r}")
            premise(int(f9["year_from"]) == 2003 and int(f9["year_to"]) == 2025, "Pu rows valid 2003-2025")

    def test_event_release_sums(self, oracle, expected):
        for eid in ("E002", "E004", "E013"):
            rel = [f for f in oracle.factors if f["stage"] == "accident" and f["tier"] == "liberated"
                   and f["region"] == oracle.events[eid]["country"]
                   and int(f["year_from"]) <= int(oracle.events[eid]["date_start"][:4]) <= int(f["year_to"])]
            s = sum(float(f["value_central"]) for f in rel)
            want = float(oracle.events[eid]["activity_central_bq"])
            premise(abs(s - want) <= 1e-4 * want, f"{eid}: registry release sum {s:.6e} vs events.csv {want:.6e} within 1e-4")
        premise(len({f["group"] for f in expected.events["E002"]["release_rows"]}) == 5, "E002 has five release groups")

    def test_e002_high(self, oracle):
        premise(float(oracle.events["E002"]["activity_high_bq"]) == 4.81e17, "events.csv E002 high is 4.81e17 Bq")

    def test_pwr_bwr_effluent_windows_tile(self, oracle):
        fam = defaultdict(list)
        for f in oracle.factors:
            if f["stage"] == "reactor_operation" and f["tier"] == "liberated" and f["driver_series"] in ("nuc_gen_pwr", "nuc_gen_bwr"):
                fam[(f["driver_series"], f["group"], f["route"])].append((int(f["year_from"]), int(f["year_to"]), f["factor_id"]))
        premise(len(fam) > 30, "PWR/BWR effluent families found")
        for k, w in fam.items():
            w.sort()
            premise(w[0][0] == 1950 and w[-1][1] == 2025, f"{k} windows span 1950-2025: {w}")
            for a, b in itertools.pairwise(w):
                premise(b[0] == a[1] + 1, f"{k}: windows {a} and {b} leave a gap or overlap")

    def test_isl_windows_tile(self, oracle):
        fam = defaultdict(list)
        for f in oracle.factors:
            if f["stage"] == "u_mining_isl" and f["group"] == "":
                fam[f["region"]].append((int(f["year_from"]), int(f["year_to"]), f["factor_id"]))
        premise(set(fam) == {"XWL", "KAZ", "UZB", "USA"}, f"ISL share regions {sorted(fam)}")
        for k, w in fam.items():
            w.sort()
            premise(w[0][0] == 1950 and w[-1][1] == 2025, f"ISL {k} spans 1950-2025")
            for a, b in itertools.pairwise(w):
                premise(b[0] == a[1] + 1, f"ISL {k}: {a} / {b} gap or overlap")
        premise([x[2] for x in sorted(fam["XWL"])] == ["nuclear:0024", "nuclear:0025", "nuclear:0026", "nuclear:1701", "nuclear:1702"],
                "XWL ISL default rows are 0024, 0025, 0026, 1701, 1702")

    def test_memo_rows(self, oracle):
        memo = [f for f in oracle.factors if f["tier"] == "memo_earth_moved"]
        premise(len(memo) == 21, f"21 memo rows, found {len(memo)}")
        premise(all(f["region"] == "USA" and f["unit"] == "Bq/t" and f["stage"] == "u_mining_conv" for f in memo), "memo rows are USA, Bq/t, u_mining_conv")
        premise({(int(f["year_from"]), int(f["year_to"])) for f in memo} == {(1950, 1968), (1969, 1978), (1979, 1988)}, "memo eras")
        premise(not any(f["factor_id"] == "nuclear:1706" for f in oracle.factors), "nuclear:1706 does not exist (D67)")
        premise({f["factor_id"] for f in memo} == {f"nuclear:{i}" for i in range(1707, 1728)}, "memo rows are nuclear:1707-1727")

    def test_no_registry_below_detection_and_substream_empty(self, oracle):
        premise(not [f for f in oracle.factors if f["below_detection"].lower() == "true"], "no registry row has below_detection true")
        premise(all(f["substream"] == "" for f in oracle.factors), "every nuclear registry substream cell is empty (2.2)")

    def test_capacity_rows(self, oracle):
        rows_ = [f for f in oracle.factors if f["stage"] == "accident" and f["group"] == "" and f["tier"] == ""]
        premise({f["factor_id"] for f in rows_} == {"nuclear:1668", "nuclear:1669"}, "capacity rows are nuclear:1668 and 1669")
        premise(all(f["unit"] == "GW" and f["year_from"] == f["year_to"] and f["driver_series"] == "" for f in rows_), "capacity rows: unit GW, one year")
        premise(len({(f["region"], f["year_from"]) for f in rows_}) == len(rows_), "one capacity row per (country, year)")
        for eid in ("E002", "E013"):
            c = oracle.capacity_row(eid)
            premise(c["description"].startswith(eid), f"capacity row for {eid} starts with the event ID")

    def test_e003_shares(self, oracle):
        sh = [f for f in oracle.factors if f["description"].startswith("E003") and f["stage"] == "u_milling"]
        premise(len(sh) == 16, f"16 E003 share rows, found {len(sh)}")
        premise(abs(sum(float(f["value_central"]) for f in sh) - 1) <= 1e-4, "E003 central shares sum to 1 +/- 1e-4")
        premise(all(f["unit"] == "1" and f["region"] == "USA" and f["year_from"] == f["year_to"] == "1979" for f in sh), "E003 rows: unit 1, USA, 1979")
        premise({f["factor_id"] for f in sh} == {f"nuclear:{i}" for i in range(1670, 1686)}, "E003 rows are nuclear:1670-1685")

    def test_e004_np239_inventory(self, oracle):
        f = _factor(oracle, "nuclear:1667")
        premise(f["group"] == "Np239" and f["tier"] == "sealed_in_core" and f["region"] == "SUN" and f["year_from"] == "1986",
                "E004 Np239 inventory row nuclear:1667")
        premise(abs(float(f["value_central"]) - 5.81e19) / 5.81e19 < 1e-3 and abs(float(f["value_low"]) - 2.7e19) / 2.7e19 < 1e-3, "Np239 58,100 PBq central, 27,000 PBq low")

    def test_closure_of_country_series(self, oracle):
        for s in ("nuc_reprocessed_gwa", "nuc_sea_dumped_tbq"):
            worst = 0.0
            for y in sorted({k[1] for k in oracle.act if k[0] == s}):
                tot = sum(oracle.a(s, y, c).central for c in oracle.countries(s, y))
                w = oracle.a(s, y, "XWL").central
                if w > 0 or tot > 0:
                    worst = max(worst, abs(tot - w) / max(w, tot))
            premise(worst < 1e-5, f"{s}: XWL equals the sum of the country rows within 1e-5 relative (worst {worst:.2e})")

    def test_series_units_and_driver_series_cells(self, oracle):
        premise(oracle.arow("nuc_reprocessed_gwa", 2010, "FRA")["unit"] == "GWa", "nuc_reprocessed_gwa unit GWa")
        premise(oracle.arow("nuc_sea_dumped_tbq", 1967, "BEL")["unit"] == "TBq", "nuc_sea_dumped_tbq unit TBq")
        premise(oracle.arow("u_production", 2010, "CAN")["unit"] == "t", "u_production unit t")
        for f in oracle.factors:
            if f["stage"] in ("reprocessing", "sea_disposal"):
                premise(f["driver_series"] in ("", "nuc_reprocessed_gwa", "nuc_sea_dumped_tbq"), f"{f['factor_id']} driver_series {f['driver_series']!r}")

    def test_predecessor_states_do_not_overlap(self, oracle):
        premise(not [y for y in range(1945, 2026) if oracle.has("u_production", y, "CSK") and oracle.has("u_production", y, "CZE")],
                "CSK and CZE u_production never overlap")

    def test_uranium_residual_years(self, oracle, expected):
        ex = expected.rows
        premise(any(k[3] == "XXX" and k[0] == 2020 for k in ex) and any(k[3] == "XXX" and k[0] == 2024 for k in ex),
                "rest-of-world residual rows exist in 2020 and 2024")

    def test_residue_type_u_tailings_exists(self):
        df = pd.read_csv(ROOT / "data" / "reference" / "residue_types.csv", dtype=str, keep_default_na=False)
        premise("u_tailings" in set(df.iloc[:, 0]), "residue type u_tailings exists")

    def test_no_zero_central_with_positive_high_among_factors(self, oracle):
        bad = [f["factor_id"] for f in oracle.factors if float(f["value_central"]) == 0 and float(f["value_high"]) > 0]
        premise(not bad, f"no zero-central factor with positive high (3.3): {bad[:5]}")

    def test_accident_events_match_catalogue_shape(self, oracle):
        for eid in ("E002", "E004", "E013"):
            e = oracle.events[eid]
            premise(e["is_accident"] == "true" and e["from_tier"] == "sealed_in_core"
                    and {"liberated", "sealed_damaged_core"} <= set(e["to_tiers"].split(";")), f"{eid} accident event shape")
        e = oracle.events["E003"]
        premise(e["is_accident"] == "false" and e["from_tier"] == "impounded" and e["stage"] == "u_milling"
                and {"liberated", "dispersed"} <= set(e["to_tiers"].split(";")), "E003 impoundment shape")
        premise(oracle.events["E008"]["stage"] == "accident", "E008 is an accident-stage marker")
        premise(not [f for f in oracle.factors if f["stage"] == "accident" and f["region"] == "JPN" and f["year_from"] == "1999"], "E008 has no registry rows")


# --------------------------------------------------------------------------------------------
# (e) benchmarks
# --------------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def unscear():
    df = pd.read_csv(ROOT / "research" / "unscear_extraction.csv", dtype=str, keep_default_na=False)
    return {r["item_id"]: r for r in df.to_dict("records")}


def U(unscear, item, nuclide=None):
    r = unscear[item]
    if nuclide:
        premise(r["nuclide_or_group"] == nuclide, f"extraction row {item} is {nuclide}, found {r['nuclide_or_group']}")
    return float(r["value"])


def check(name, x, ref, known_miss=False, reason=""):
    ratio = x / ref if ref else float("inf")
    ok = 1 / 3 <= ratio <= 3
    if not ok and known_miss:
        pytest.xfail(f"documented known miss (NUCLEAR_SPEC 9(e)): {name}: stream {x:.4g}, reference {ref:.4g}, ratio {ratio:.3g}. {reason}")
    assert ok, f"{name}: stream {x:.4g} TBq/GW.a vs reference {ref:.4g}, ratio {ratio:.3g} outside [1/3, 3]"


def Wy(O, y):
    return O.a("elec_gen_nuclear", y, "XWL").central / GWA_TWH


def Wt(O, t, y):
    return O.a(f"nuc_gen_{t}", y, "XWL").central / GWA_TWH


def tbq(rows, y, **kw):
    return rows.total(y, **kw) / 1e12


def conv_tonnage(O, y):
    tot = 0.0
    phi = O.a("phi_civil", y, "XWL").central
    listed = [c for c in O.countries("u_production", y) if not (c == "CZE" and O.has("u_production", y, "CSK"))]
    for c in listed:
        s = O.fb(O.select(y, c, stage="u_mining_isl", group="", tier="", route="", residue_type="", driver_series="")).central
        tot += O.a("u_production", y, c).central * (1 - s) * phi
    res = O.a("u_production", y, "XWL").central - sum(O.a("u_production", y, c).central for c in listed)
    if res > 0:
        s = O.fb(O.select(y, "XWL", stage="u_mining_isl", group="", tier="", route="", residue_type="", driver_series="")).central
        tot += res * (1 - s) * phi
    return tot


YEARS = [2010, 2020]
ANNEX = {  # type -> (noble, H3 air, H3 liquid, C14, I131) extraction ids; GCR / AGR are separate columns
    "pwr": ("U0034", "U0036", "U0045", "U0040", "U0038"),
    "bwr": ("U0049", "U0051", "U0060", "U0055", "U0053"),
    "phwr": ("U0064", "U0066", "U0075", "U0070", "U0068"),
    "lwgr": ("U0079", "U0081", "U0090", "U0085", "U0083"),
    "fbr": ("U0125", "U0127", "U0136", "U0131", "U0129"),
}
GCR_IDS = ("U0110", "U0112", "U0121", "U0115", "U0114")
AGR_IDS = ("U0094", "U0096", "U0106", "U0100", "U0098")
LABELS = ("noble gases", "H3 air", "H3 liquid", "C14", "I131")
KNOWN_MISSES = {("pwr", "noble gases", 2020): "ratio about 0.26 after the D65 N1-N3 revisions",
                ("pwr", "I131", 2010): "I-131 air 1e-5 vs 8e-5 TBq per GW.a (N10)",
                ("pwr", "I131", 2020): "I-131 air 1e-5 vs 8e-5 TBq per GW.a (N10)"}


def stream_quantities(rows, t, y):
    kw = {"substream": t, "stage": "reactor_operation", "quantity": "flow", "tier": "liberated"}
    return (sum(rows.total(y, group=g, route="air_stack", **kw) for g in NOBLE) / 1e12,
            tbq(rows, y, group="H3", route="air_stack", **kw),
            tbq(rows, y, group="H3", route="water_liquid_effluent", **kw),
            tbq(rows, y, group="C14", route="air_stack", **kw),
            tbq(rows, y, group="I131", route="air_stack", **kw))


class TestBenchmarks:
    @pytest.mark.parametrize("y", YEARS)
    def test_isl_mill_radon_and_dust(self, rows, oracle, unscear, y):
        W = Wy(oracle, y)
        flows = {"quantity": "flow", "tier": "liberated"}
        check("F2 ISL radon", tbq(rows, y, stage="u_mining_isl", group="Rn222+", **flows) / W, U(unscear, "U0022"))
        check("F3 mill radon", tbq(rows, y, stage="u_milling", group="Rn222+", route="air_process_vent", **flows) / W, U(unscear, "U0023"))
        for g, item in (("U238+", "U0030"), ("U234", "U0029"), ("Th230", "U0031"), ("Ra226+", "U0028"),
                        ("Pb210+", "U0027"), ("Po210", "U0026")):
            check(f"F4 mill dust {g}", tbq(rows, y, stage="u_milling", group=g, route="air_dust", **flows) / W, U(unscear, item))

    @pytest.mark.parametrize("y", YEARS)
    def test_f1_per_tonne_conventionally_mined(self, rows, oracle, unscear, y):
        """Decided (D64): the pass/fail test is per tonne conventionally mined."""
        per_t = U(unscear, "U0021", "Rn-222 -> Rn222+") / U(unscear, "U0032")
        f1 = tbq(rows, y, stage="u_mining_conv", group="Rn222+", tier="liberated", quantity="flow")
        check("F1 mine radon per t U mined conventionally", f1 / conv_tonnage(oracle, y), per_t)

    def test_f1_plain_per_gwa_2010_passes_2020_is_documented_miss(self, rows, oracle, unscear):
        ref = U(unscear, "U0021")
        r10 = tbq(rows, 2010, stage="u_mining_conv", group="Rn222+", tier="liberated", quantity="flow") / Wy(oracle, 2010) / ref
        r20 = tbq(rows, 2020, stage="u_mining_conv", group="Rn222+", tier="liberated", quantity="flow") / Wy(oracle, 2020) / ref
        print(f"F1 plain per-GW.a ratios to Annex B: 2010 {r10:.3f}, 2020 {r20:.3f}")
        assert 1 / 3 <= r10 <= 3, f"F1 2010 plain per-GW.a ratio {r10:.3f} outside a factor of 3"
        if not 1 / 3 <= r20 <= 3:
            pytest.xfail(f"documented known miss: F1 2020 plain per-GW.a ratio {r20:.3f} (UNSCEAR assumes 220 t U/GW.a, all conventional)")

    @pytest.mark.parametrize("y", YEARS)
    @pytest.mark.parametrize("t", list(ANNEX))
    @pytest.mark.parametrize("qi", range(5))
    def test_reactor_effluents_against_annex_b(self, rows, oracle, unscear, t, qi, y):
        ref = U(unscear, ANNEX[t][qi])
        nuclide = unscear[ANNEX[t][qi]]["nuclide_or_group"]
        premise(nuclide in ("UNMAPPED:noble_gases_mixed", "H3", "C14", "I131"), f"extraction row {ANNEX[t][qi]} is {nuclide}")
        x = stream_quantities(rows, t, y)[qi] / Wt(oracle, t, y)
        label = LABELS[qi]
        check(f"{t} {label} {y}", x, ref, known_miss=(t, label, y) in KNOWN_MISSES, reason=KNOWN_MISSES.get((t, label, y), ""))

    @pytest.mark.parametrize("y", YEARS)
    @pytest.mark.parametrize("qi", range(5))
    def test_gcr_against_weighted_gcr_agr_mean(self, rows, oracle, unscear, qi, y):
        gcr, agr = U(unscear, GCR_IDS[qi]), U(unscear, AGR_IDS[qi])
        if y == 2010:
            w1, w2 = U(unscear, "U0016"), U(unscear, "U0015")
            ref = (w1 * gcr + w2 * agr) / (w1 + w2)
        else:
            ref = agr
        x = stream_quantities(rows, "gcr", y)[qi] / Wt(oracle, "gcr", y)
        check(f"gcr {LABELS[qi]} {y}", x, ref)

    @pytest.mark.parametrize("y", YEARS)
    def test_reprocessing_unit_chain_per_site_country(self, rows, oracle, unscear, y):
        conv = 3.15576e7 / 1e12
        refs = {("Kr85", "air_stack"): U(unscear, "U0143") * conv, ("H3", "air_stack"): U(unscear, "U0140") * conv,
                ("H3", "water_liquid_effluent"): U(unscear, "U0150") * conv, ("C14", "air_stack"): U(unscear, "U0141") * conv}
        pu_ref = U(unscear, "U0149") * conv
        n = 0
        for c in oracle.countries("nuc_reprocessed_gwa", y):
            G = oracle.a("nuc_reprocessed_gwa", y, c).central
            if G == 0:
                continue
            for (g, route), ref in refs.items():
                x = tbq(rows, y, stage="reprocessing", country=c, group=g, route=route, quantity="transfer_in") / G
                check(f"reprocessing {c} {g} {route} {y}", x, ref)
            pu = sum(tbq(rows, y, stage="reprocessing", country=c, group=g, route="air_stack", quantity="transfer_in") for g in ("Pu239", "Pu240")) / G
            check(f"reprocessing {c} Pu239+240 air {y}", pu, pu_ref)
            n += 1
        assert n >= 2, "expected at least FRA and GBR reprocessing in 2010 and 2020"


class TestIndependentBenchmarks:
    """Second, independent estimates (9(e) table): within a factor of 3 of at least one independent value.

    Excluded by design (no independent value, 9(e) table): mine / ISL / mill radon and dust; BWR noble gases against
    0.18 TBq per reactor-year (the independent value lies below the row-sum low); PHWR / LWGR / GCR / FBR effluents;
    in-core PWR / PHWR / GCR; spent-fuel arisings; conversion / enrichment / fabrication."""

    @pytest.mark.parametrize("y", YEARS)
    @pytest.mark.parametrize("t,ref", [("pwr", 1.2), ("bwr", 1.4)])
    def test_reactor_h3_air(self, rows, oracle, t, ref, y):
        """US 2021 medians (NUREG/CR-2907 v27, S0121) per reactor-year; a US reactor-year is taken as 1 GW.a."""
        check(f"{t} H3 air {y} vs S0121", stream_quantities(rows, t, y)[1] / Wt(oracle, t, y), ref)

    @pytest.mark.parametrize("y", YEARS)
    def test_pwr_h3_liquid(self, rows, oracle, y):
        check(f"pwr H3 liquid {y} vs S0121", stream_quantities(rows, "pwr", y)[2] / Wt(oracle, "pwr", y), 19.9)

    @pytest.mark.parametrize("y", YEARS)
    @pytest.mark.parametrize("t,ref", [("pwr", 0.34), ("bwr", 0.57)])
    def test_reactor_c14_required_pass(self, rows, oracle, t, ref, y):
        check(f"{t} C14 {y} vs S0121", stream_quantities(rows, t, y)[3] / Wt(oracle, t, y), ref)

    @pytest.mark.parametrize("y", YEARS)
    def test_ospar_nuclear_power_plant_h3_liquid_regional_lower_bound(self, rows, y):
        o = pd.read_csv(ROOT / "research" / "nuclear" / "ospar_liquid_discharges_1989_2023.csv", dtype=str)
        v = float(o[(o.year == str(y)) & (o.sub_sector == "nuclear_power_plants") & (o.quantity == "tritium")].value_tbq_per_a.iloc[0])
        tot = tbq(rows, y, stage="reactor_operation", group="H3", route="water_liquid_effluent", quantity="flow", tier="liberated")
        assert v <= tot <= 10 * v, f"global reactor H3 liquid {tot:.4g} TBq/a must lie in [{v}, {10 * v}] (OSPAR NPP, {y})"

    @pytest.mark.parametrize("y", YEARS)
    def test_ospar_reprocessing_h3_liquid(self, rows, oracle, y):
        o = pd.read_csv(ROOT / "research" / "nuclear" / "ospar_liquid_discharges_1989_2023.csv", dtype=str)
        v = float(o[(o.year == str(y)) & (o.sub_sector == "reprocessing") & (o.quantity == "tritium")].value_tbq_per_a.iloc[0])
        gwa = sum(oracle.a("nuc_reprocessed_gwa", y, c).central for c in ("FRA", "GBR") if oracle.has("nuc_reprocessed_gwa", y, c))
        premise(gwa > 30, f"FRA + GBR reprocessed throughput in {y} is {gwa:.1f} GW.a (OSPAR implies about 52 and 57)")
        x = sum(tbq(rows, y, stage="reprocessing", country=c, group="H3", route="water_liquid_effluent", quantity="transfer_in")
                for c in ("FRA", "GBR"))
        ratio = x / v
        assert 1 / 3 <= ratio <= 3, f"reprocessing H3 liquid FRA+GBR {x:.4g} TBq/a vs OSPAR {v} TBq/a (ratio {ratio:.3g})"

    @pytest.mark.parametrize("y", YEARS)
    def test_bwr_in_core_cs137_i131_vs_fukushima(self, rows, oracle, y):
        C = oracle.a("nuc_cap_bwr", y, "XWL").central
        for g, ref in (("Cs137+", 345.0), ("I131", 2960.0)):
            x = rows.one(y, substream="bwr", stage="reactor_operation", group=g, tier="sealed_in_core", quantity="standing_inventory")
            check(f"bwr in-core {g} {y} (PBq per GW)", float(x["value_central"]) / 1e15 / C, ref)

    @pytest.mark.parametrize("y", YEARS)
    def test_lwgr_in_core_vs_unscear_2000_annex_j(self, rows, oracle, y):
        C = oracle.a("nuc_cap_lwgr", y, "XWL").central
        for g, ref in (("Cs137+", 260.0), ("Sr90+", 220.0), ("I131", 3200.0)):
            x = rows.one(y, substream="lwgr", stage="reactor_operation", group=g, tier="sealed_in_core", quantity="standing_inventory")
            check(f"lwgr in-core {g} {y} (PBq per GW)", float(x["value_central"]) / 1e15 / C, ref)

    def test_sea_disposal_closure_with_series_total(self, rows, pre_rows, oracle):
        series_total_tbq = sum(oracle.a("nuc_sea_dumped_tbq", y, c).central for (s, y, c) in oracle.act
                               if s == "nuc_sea_dumped_tbq" and c != "XWL" and 1946 <= y <= 1993)
        premise(44000 < series_total_tbq < 45500, f"series total 1946-93 is about 44,602 TBq, found {series_total_tbq:.0f}")
        stream = sum(float(r["value_central"]) for r in rows.rows if r["stage"] == "sea_disposal" and r["quantity"] == "transfer_in" and r["tier"] == "liberated")
        stream += sum(float(r["value_central"]) for r in pre_rows.rows if r["stage"] == "sea_disposal" and r["tier"] == "liberated")
        assert abs(stream / 1e12 - series_total_tbq) <= 2e-3 * series_total_tbq, \
            f"stream sea-disposal liberated sum {stream / 1e12:.1f} TBq vs series total {series_total_tbq:.1f} TBq"


# --------------------------------------------------------------------------------------------
# (j) CLI
# --------------------------------------------------------------------------------------------
class TestCli:
    def test_cli_write_diff_and_log(self, written, tmp_path):
        root = _copy_tree(tmp_path / "cli_root")
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
        cmd = [sys.executable, "-m", "pipeline.streams.nuclear", "--root", str(root)]

        def run(*extra):
            return subprocess.run(cmd + list(extra), cwd=str(ROOT), env=env, capture_output=True, text=True,
                                  timeout=1800, check=False)

        w = run("--write")
        assert w.returncode == 0, f"--write exited {w.returncode}\nstdout: {w.stdout[-800:]}\nstderr: {w.stderr[-1500:]}"
        main = root / "data" / "streams" / "nuclear.csv"
        pre = root / "data" / "streams_pre1950" / "nuclear.csv"
        logf = root / "research" / "nuclear" / "build_log.csv"
        assert main.is_file() and pre.is_file() and logf.is_file(), "--write must write all three files (NUCLEAR_SPEC 1)"
        assert main.read_bytes() == Path(written[0]).read_bytes(), "CLI master output differs from build() + write_master"
        assert pre.read_bytes() == Path(written[1]).read_bytes(), "CLI pre-1950 output differs"
        assert "no_factor" in (w.stdout + w.stderr), "the CLI prints counts by kind (8)"
        assert run().returncode == 0, "identical files must give exit 0"

        good = logf.read_bytes()
        logf.write_bytes(good + b"no_factor,1900,XXX,,tampered\n")
        assert run().returncode != 0, "a differing build_log.csv alone must give a non-zero exit"
        assert logf.read_bytes() != good, "the diff run must not overwrite the log"
        logf.write_bytes(good)

        t = pre.read_bytes()
        pre.write_bytes(t.replace(b"nuclear,fuel_cycle", b"nuclear,fuel_cyc1", 1))
        assert run().returncode != 0, "a differing pre-1950 file must give a non-zero exit"
        pre.write_bytes(t)

        text = main.read_bytes()
        tampered = text.replace(b"nuclear,fuel_cycle", b"nuclear,fuel_cyc1", 1)
        main.write_bytes(tampered)
        assert run().returncode != 0, "a differing master file must give a non-zero exit"
        assert main.read_bytes() == tampered, "the diff run must not overwrite files"
        main.write_bytes(text)
        assert run().returncode == 0

        logf.unlink()
        assert run().returncode != 0, "a missing committed build_log.csv must count as a difference"

    def test_cli_second_write_is_byte_identical(self, tmp_path):
        root = _copy_tree(tmp_path / "cli_twice")
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
        cmd = [sys.executable, "-m", "pipeline.streams.nuclear", "--root", str(root), "--write"]
        files = [root / "data" / "streams" / "nuclear.csv", root / "data" / "streams_pre1950" / "nuclear.csv",
                 root / "research" / "nuclear" / "build_log.csv"]
        first = None
        for _ in range(2):
            p = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=1800, check=False)
            assert p.returncode == 0, p.stderr[-1000:]
            cur = [f.read_bytes() for f in files]
            if first is None:
                first = cur
            else:
                assert cur == first, "two --write runs differ (determinism, 9(d))"


# --------------------------------------------------------------------------------------------
# (g) fixture tests on miniature trees
# --------------------------------------------------------------------------------------------
ACT_COLUMNS = ["series", "year", "country", "value_low", "value_central", "value_high", "unit",
               "below_detection", "basis", "source_ids", "notes"]
DENSE = list(range(1990, 2013))
URANIUM_YEARS = [1960, 1965] + DENSE


def _a(series, y, c, central, unit, band=0.1, basis="compiled", src="S0113"):
    return {"series": series, "year": y, "country": c, "value_low": central * (1 - band), "value_central": central,
            "value_high": central * (1 + band), "unit": unit, "below_detection": "false", "basis": basis,
            "source_ids": src, "notes": ""}


def mini_act(*, sea=True, repro=True, xwl_prod=None, gen_pwr_skip=(), extra_uranium=()):
    """Four activity files (file name -> rows). XWL production equals the sum of the three listed countries unless overridden."""
    xwl_prod = xwl_prod or {}
    ur, el, nu, cy = [], [], [], []
    for y in URANIUM_YEARS:
        ur.append(_a("phi_civil", y, "XWL", 0.5 if y == 1965 else (0.0 if y == 1960 else 0.9), "1", band=0.0 if y == 1960 else 0.1))
        for c, v in (("CAN", 4000.0), ("KAZ", 5000.0), ("UZB", 1000.0)):
            ur.append(_a("u_production", y, c, v, "t"))
        ur.append(_a("u_production", y, "XWL", xwl_prod.get(y, 10000.0), "t", band=0.02))
    ur += list(extra_uranium)
    for y in DENSE:
        el.append(_a("elec_gen_nuclear", y, "XWL", 2500.0, "TWh", band=0.02))
        if y not in gen_pwr_skip:
            nu.append(_a("nuc_gen_pwr", y, "XWL", 1500.0, "TWh", band=0.02))
        nu.append(_a("nuc_cap_pwr", y, "XWL", 200.0, "GW", band=0.02))
        nu.append(_a("nuc_gen_bwr", y, "XWL", 600.0, "TWh", band=0.02))
        nu.append(_a("nuc_cap_bwr", y, "XWL", 90.0, "GW", band=0.02))
        if repro:
            cy.append(_a("nuc_reprocessed_gwa", y, "FRA", 30.0, "GWa", band=0.05))
            cy.append(_a("nuc_reprocessed_gwa", y, "XWL", 30.0, "GWa", band=0.05))
    if sea:
        for y, c, v in ((1947, "USA", 2.0), (1965, "BEL", 5.0), (1965, "USA", 3.0)):
            cy.append(_a("nuc_sea_dumped_tbq", y, c, v, "TBq", band=0.2, basis="interpolated" if c == "USA" else "compiled"))
        for y in (1947, 1965):
            tot = sum(r["value_central"] for r in cy if r["series"] == "nuc_sea_dumped_tbq" and r["year"] == y)
            cy.append(_a("nuc_sea_dumped_tbq", y, "XWL", tot, "TBq", band=0.2))
    return {"uranium.csv": ur, "electricity_generation.csv": el, "nuclear.csv": nu, "nuclear_cycle.csv": cy}


def make_mini(tmp_path: Path, act: dict, factor_edit=None, event_edit=None, name="mini") -> Path:
    root = tmp_path / name
    (root / "data" / "activity").mkdir(parents=True)
    (root / "data" / "factors").mkdir(parents=True)
    shutil.copytree(ROOT / "data" / "reference", root / "data" / "reference")
    shutil.copy(ROOT / "data" / "sources.csv", root / "data" / "sources.csv")
    for fname, rws in act.items():
        if rws is None:
            continue
        with open(root / "data" / "activity" / fname, "w", newline="\n", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=ACT_COLUMNS)
            w.writeheader()
            w.writerows(rws)
    fac = pd.read_csv(ROOT / "data" / "factors" / "nuclear.csv", dtype=str, keep_default_na=False)
    recs = fac.to_dict("records")
    if factor_edit:
        recs = factor_edit(recs)
    with open(root / "data" / "factors" / "nuclear.csv", "w", newline="\n", encoding="utf-8") as fh:
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
    return root


def build_mini(mod, tmp_path, act=None, **kw):
    root = make_mini(tmp_path, act if act is not None else mini_act(), **kw)
    res = mod.build(root)
    return root, res, Rows(list(res.rows)), list(res.log)


def edit_factor(fid, **changes):
    def fn(recs):
        for r in recs:
            if r["factor_id"] == fid:
                r.update({k: str(v) for k, v in changes.items()})
        return recs
    return fn


def edit_event(eid, **changes):
    def fn(recs):
        for r in recs:
            if r["event_id"] == eid:
                r.update({k: str(v) for k, v in changes.items()})
        return recs
    return fn


def lib_error():
    from pipeline.lib import LibError
    return LibError


@pytest.fixture(scope="module")
def mini_base(nuclear_mod, tmp_path_factory):
    tmp = tmp_path_factory.mktemp("mini_base")
    root, res, rws, lg = build_mini(nuclear_mod, tmp)
    return root, res, rws, lg


class TestMiniBase:
    def test_mini_tree_matches_oracle(self, mini_base):
        root, res, rws, _lg = mini_base
        exp = Oracle(root).expected()
        prob = compare_all(exp.rows, rws, "mini")
        flat = [m for v in prob.values() for m in v]
        assert not flat, "mini tree differs from the oracle: " + show(flat)
        prob = compare_all(exp.pre, Rows(list(res.rows_pre1950)), "mini pre")
        assert not [m for v in prob.values() for m in v]

    def test_zero_residual_gives_no_rest_of_world_rows(self, mini_base):
        _, _, rws, lg = mini_base
        assert not rws.find(stage="u_milling", country="XXX"), "XWL equals the listed sum: residual 0 gives no rows (4.2)"
        assert not log_entries(lg, "negative_residual")

    def test_e008_marker_only(self, mini_base):
        _, res, _rws, lg = mini_base
        es = log_entries(lg, "event_not_modelled")
        assert len(es) == 1 and "marker only" in str(es[0]["detail"]), es
        assert not [r for r in res.rows if r["event_id"] == "E008"], "E008 writes no rows (7.1)"

    def test_tbq_driver_scaled_by_1e12(self, mini_base):
        root, _, rws, _ = mini_base
        O = Oracle(root)
        f = O.select(1965, "XWL", stage="sea_disposal", group="H3", tier="liberated", route="sea_disposal_package")
        r = rws.one(1965, stage="sea_disposal", country="BEL", group="H3", quantity="transfer_in")
        assert close(float(r["value_central"]), 5.0 * 1e12 * float(f["value_central"]), 1e-9), \
            f"5 TBq dump gave {r['value_central']}, expected 5e12 x share"
        assert r["unit"] == "Bq"

    def test_pre1950_flow_from_mini(self, mini_base):
        root, res, _, _ = mini_base
        O = Oracle(root)
        pre = Rows(list(res.rows_pre1950))
        f = O.select(1947, "XWL", stage="sea_disposal", group="H3", tier="liberated", route="sea_disposal_package")
        r = pre.one(1947, stage="sea_disposal", country="USA", group="H3", quantity="flow")
        assert close(float(r["value_central"]), 2.0e12 * float(f["value_central"]), 1e-9)

    def test_i131_reprocessing_gap_is_one_no_factor_run(self, mini_base):
        _, _, rws, lg = mini_base
        es = [e for e in log_entries(lg, "no_factor", country="FRA", group="I131") if e["year"] == 1998]
        assert any(str(e["detail"]).startswith("1998-2002 (5 years)") for e in es), [e["detail"] for e in es]
        assert not rws.find(2000, stage="reprocessing", country="FRA", group="I131", route="air_stack")
        assert rws.find(1997, stage="reprocessing", country="FRA", group="I131", route="air_stack")
        assert rws.find(2003, stage="reprocessing", country="FRA", group="I131", route="air_stack")

    def test_uzb_complement_zero_central_rows(self, mini_base):
        """A2: UZB 2010 ISL share has central 1, so the conventional tonnage is (0, 0, h) and flagged."""
        _, _, rws, _ = mini_base
        r = rws.one(2010, stage="u_mining_conv", country="UZB", group="Rn222+", tier="liberated", quantity="flow")
        assert float(r["value_central"]) == 0 and as_bool(r["below_detection"]) and float(r["value_high"]) > 0
        assert notes_parts(r["notes"])["cause"] in (["zero_central_factor"], ["floor_dominance"]), r["notes"]
        isl = rws.one(2010, stage="u_mining_isl", country="UZB", group="Rn222+", tier="liberated", quantity="flow")
        assert float(isl["value_central"]) > 0

    def test_stderr_in_process(self, nuclear_mod, tmp_path, capfd):
        build_mini(nuclear_mod, tmp_path)
        assert capfd.readouterr().err == ""

    def test_at_most_one_lib_warning(self, mini_base):
        assert len(log_entries(mini_base[3], "lib_warning")) <= 1

    def test_driver_basis_suffix_in_mini(self, nuclear_mod, tmp_path):
        act = mini_act()
        for r in act["uranium.csv"]:
            if r["series"] == "u_production" and r["country"] == "CAN" and r["year"] == 2010:
                r["basis"] = "extrapolated"
            if r["series"] == "u_production" and r["country"] == "KAZ" and r["year"] == 2011:
                r["basis"] = "interpolated"
            if r["series"] == "phi_civil" and r["year"] == 2011:
                r["basis"] = "extrapolated"
        _, _, rws, _ = build_mini(nuclear_mod, tmp_path, act)
        assert notes_parts(rws.one(2010, stage="u_milling", country="CAN", group="U238+", tier="sealed_fuel_cycle")["notes"])["basis"] == {"extrapolated"}
        assert notes_parts(rws.one(2010, stage="u_milling", country="KAZ", group="U238+", tier="sealed_fuel_cycle")["notes"])["basis"] is None
        both = notes_parts(rws.one(2011, stage="u_milling", country="KAZ", group="U238+", tier="sealed_fuel_cycle")["notes"])
        assert both["basis"] == {"interpolated", "extrapolated"} and "+" in both["text"].split("driver basis: ")[1].split(";")[0]
        assert rws.one(2011, stage="u_milling", country="KAZ", group="U238+", tier="sealed_fuel_cycle")["basis"] == "modelled"


class TestMiniResiduals:
    def test_negative_residual_logged_and_no_rows(self, nuclear_mod, tmp_path):
        act = mini_act(xwl_prod={2010: 9000.0})
        _, _, rws, lg = build_mini(nuclear_mod, tmp_path, act)
        es = log_entries(lg, "negative_residual", year=2010)
        assert len(es) == 1, f"expected one negative_residual entry for 2010, got {es}"
        nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?(?:[eE][+-]?\d+)?", str(es[0]["detail"]))]
        assert any(abs(n - 1000.0) <= 1e-3 * 1000 for n in nums), f"detail must carry the magnitude 1000: {es[0]['detail']!r}"
        assert not rws.find(2010, stage="u_milling", country="XXX")
        assert len(log_entries(lg, "negative_residual")) == 1

    def test_positive_residual_rows_with_notes_text_and_clipped_cause(self, nuclear_mod, tmp_path):
        act = mini_act(xwl_prod={2010: 10500.0})
        root, _, rws, _lg = build_mini(nuclear_mod, tmp_path, act)
        r = rws.one(2010, stage="u_milling", country="XXX", group="U238+", tier="sealed_fuel_cycle", quantity="flow")
        assert "rest of world (world aggregate minus listed countries)" in r["notes"]
        O = Oracle(root)
        from nuclear_oracle import diff
        R, _ = diff(O.a("u_production", 2010, "XWL"), sum_independent([O.a("u_production", 2010, c) for c in O.countries("u_production", 2010)]))
        assert 499 < R.central < 501
        f = O.select(2010, "XWL", stage="u_milling", group="U238+", tier="sealed_fuel_cycle", route="")
        assert_bounds(r, prod(prod(R, O.a("phi_civil", 2010, "XWL")), O.fb(f)), label="mini rest of world")
        assert as_bool(r["below_detection"]) and notes_parts(r["notes"])["cause"] == ["clipped_difference"]

    def test_csk_cze_predecessor_rule(self, nuclear_mod, tmp_path):
        extra = [_a("u_production", 2010, "CSK", 100.0, "t"), _a("u_production", 2010, "CZE", 50.0, "t")]
        act = mini_act(xwl_prod={2010: 10100.0}, extra_uranium=extra)
        _, _, rws, lg = build_mini(nuclear_mod, tmp_path, act)
        assert not rws.find(2010, stage="u_milling", country="CZE"), "CZE is dropped where CSK has a value (3.5)"
        assert rws.find(2010, stage="u_milling", country="CSK", group="U238+")
        es = log_entries(lg, "predecessor_dropped", country="CZE")
        assert len(es) == 1 and es[0]["year"] == 2010 and "CSK" in str(es[0]["detail"]), es
        assert not rws.find(2010, stage="u_milling", country="XXX"), "residual must exclude CZE: XWL = sum of the rest"
        assert not log_entries(lg, "negative_residual")

    def test_zero_production_country_year_is_silent(self, nuclear_mod, tmp_path):
        act = mini_act()
        for r in act["uranium.csv"]:
            if r["series"] == "u_production" and r["country"] == "CAN" and r["year"] == 2005:
                r.update(value_low=0, value_central=0, value_high=0)
        _, _, rws, lg = build_mini(nuclear_mod, tmp_path, act)
        assert not rws.find(2005, country="CAN", stage="u_milling"), "P = 0/0/0 gives no rows (4.1)"
        assert not [e for e in lg if e["country"] == "CAN" and e["year"] == 2005], "zero production is not a missing driver"

    def test_absent_country_year_is_silent(self, nuclear_mod, tmp_path):
        act = mini_act(xwl_prod={2005: 6000.0})
        act["uranium.csv"] = [r for r in act["uranium.csv"] if not (r["series"] == "u_production" and r["country"] == "CAN" and r["year"] == 2005)]
        _, _, rws, lg = build_mini(nuclear_mod, tmp_path, act)
        assert not rws.find(2005, country="CAN", stage="u_milling")
        assert not [e for e in lg if e["country"] == "CAN" and run_of(e) and run_of(e)[0] <= 2005 <= run_of(e)[1]], \
            "a country that is not producing is not a missing driver (8)"


class TestMiniMissingAndAbsent:
    def test_missing_driver_years_are_aggregated_runs(self, nuclear_mod, tmp_path):
        act = mini_act(gen_pwr_skip=(2000, 2001, 2010))
        _, _, rws, lg = build_mini(nuclear_mod, tmp_path, act)
        assert not rws.find(2000, substream="pwr", stage="reactor_operation", quantity="flow")
        assert rws.find(2002, substream="pwr", stage="reactor_operation", quantity="flow")
        e = [x for x in log_entries(lg, "no_driver", country="XXX") if x["year"] == 2000]
        assert len(e) == 1 and str(e[0]["detail"]).startswith("2000-2001 (2 years)"), e
        e2 = [x for x in log_entries(lg, "no_driver", country="XXX") if x["year"] == 2010]
        assert len(e2) == 1 and str(e2[0]["detail"]).startswith("2010-2010 (1 year") , e2

    @pytest.mark.parametrize("drop", ["nuc_reprocessed_gwa", "nuc_sea_dumped_tbq"])
    def test_absent_country_series_gives_one_no_driver_and_no_rows(self, nuclear_mod, tmp_path, mini_base, drop):
        act = mini_act()
        act["nuclear_cycle.csv"] = [r for r in act["nuclear_cycle.csv"] if r["series"] != drop]
        _, _res, rws, lg = build_mini(nuclear_mod, tmp_path, act, name="absent_rows")
        stage = "reprocessing" if drop == "nuc_reprocessed_gwa" else "sea_disposal"
        assert not rws.find(stage=stage), f"no rows at {stage} without {drop}"
        base_n = len(log_entries(mini_base[3], "no_driver"))
        assert len(log_entries(lg, "no_driver")) - base_n == 1, \
            f"an absent {drop} must add exactly one aggregated no_driver entry (8)"

    def test_missing_cycle_file_does_not_raise(self, nuclear_mod, tmp_path, mini_base):
        act = mini_act()
        act["nuclear_cycle.csv"] = None
        _, res, rws, lg = build_mini(nuclear_mod, tmp_path, act, name="nofile")
        assert not rws.find(stage="reprocessing") and not rws.find(stage="sea_disposal")
        assert len(log_entries(lg, "no_driver")) - len(log_entries(mini_base[3], "no_driver")) == 2
        assert list(res.rows_pre1950) == []


class TestMiniErrors:
    def test_duplicate_activity_rows_raise(self, nuclear_mod, tmp_path):
        act = mini_act()
        dup = next(r for r in act["uranium.csv"] if r["series"] == "u_production" and r["country"] == "CAN" and r["year"] == 2010)
        act["uranium.csv"].append(dict(dup))
        with pytest.raises(lib_error()) as ei:
            build_mini(nuclear_mod, tmp_path, act)
        msg = str(ei.value)
        assert "u_production" in msg and "2010" in msg and "CAN" in msg, f"message must name the key: {msg}"

    def test_ambiguous_registry_row_propagates(self, nuclear_mod, tmp_path):
        def dup(recs):
            r = next(x for x in recs if x["factor_id"] == "nuclear:0002")
            c = dict(r)
            c["factor_id"] = "nuclear:9999"
            return recs + [c]
        with pytest.raises(lib_error(), match="ambiguous factor rows"):
            build_mini(nuclear_mod, tmp_path, factor_edit=dup)

    @pytest.mark.parametrize("series,country,rel,ok", [("nuc_reprocessed_gwa", "FRA", 1e-3, False), ("nuc_reprocessed_gwa", "FRA", 5e-6, True),
                                                       ("nuc_sea_dumped_tbq", "BEL", 1e-3, False), ("nuc_sea_dumped_tbq", "BEL", 5e-6, True)])
    def test_xwl_closure_check(self, nuclear_mod, tmp_path, series, country, rel, ok):
        act = mini_act()
        for r in act["nuclear_cycle.csv"]:
            if r["series"] == series and r["country"] == country and r["year"] == (1965 if series == "nuc_sea_dumped_tbq" else 2005):
                for k in ("value_low", "value_central", "value_high"):
                    r[k] = r[k] * (1 + rel)
        if ok:
            build_mini(nuclear_mod, tmp_path, act)
        else:
            with pytest.raises(lib_error()):
                build_mini(nuclear_mod, tmp_path, act)

    def test_accident_without_capacity_row_raises(self, nuclear_mod, tmp_path):
        with pytest.raises(lib_error(), match="no factor row"):
            build_mini(nuclear_mod, tmp_path, factor_edit=lambda recs: [r for r in recs if r["factor_id"] != "nuclear:1668"])

    def test_two_capacity_rows_raise_ambiguous(self, nuclear_mod, tmp_path):
        def dup(recs):
            c = dict(next(x for x in recs if x["factor_id"] == "nuclear:1669"))
            c["factor_id"] = "nuclear:9998"
            return recs + [c]
        with pytest.raises(lib_error(), match="ambiguous factor rows"):
            build_mini(nuclear_mod, tmp_path, factor_edit=dup)

    @pytest.mark.parametrize("change", [{"unit": "MW"}, {"description": "unit capacity without the event identifier"}])
    def test_bad_capacity_row_raises(self, nuclear_mod, tmp_path, change):
        with pytest.raises(lib_error()):
            build_mini(nuclear_mod, tmp_path, factor_edit=edit_factor("nuclear:1668", **change))

    def test_e003_shares_summing_to_0_9_raise(self, nuclear_mod, tmp_path):
        def scale_shares(recs):
            for r in recs:
                if r["description"].startswith("E003") and r["stage"] == "u_milling":
                    for k in ("value_low", "value_central", "value_high"):
                        r[k] = repr(float(r[k]) * 0.9)
            return recs
        with pytest.raises(lib_error()):
            build_mini(nuclear_mod, tmp_path, factor_edit=scale_shares)

    def test_wrong_driver_unit_raises(self, nuclear_mod, tmp_path):
        act = mini_act()
        for r in act["nuclear_cycle.csv"]:
            if r["series"] == "nuc_sea_dumped_tbq":
                r["unit"] = "GBq"
        with pytest.raises(lib_error()):
            build_mini(nuclear_mod, tmp_path, act)

    def test_bq_driver_unit_is_not_scaled(self, nuclear_mod, tmp_path, mini_base):
        act = mini_act()
        for r in act["nuclear_cycle.csv"]:
            if r["series"] == "nuc_sea_dumped_tbq":
                r["unit"] = "Bq"
                for k in ("value_low", "value_central", "value_high"):
                    r[k] = r[k] * 1e12
        _, _, rws, _ = build_mini(nuclear_mod, tmp_path, act)
        a = rws.one(1965, stage="sea_disposal", country="BEL", group="H3", quantity="transfer_in")
        b = mini_base[2].one(1965, stage="sea_disposal", country="BEL", group="H3", quantity="transfer_in")
        assert close(float(a["value_central"]), float(b["value_central"]), 1e-9)

    def test_driver_series_mismatch_raises(self, nuclear_mod, tmp_path):
        with pytest.raises(lib_error(), match=re.compile("driver mismatch", re.IGNORECASE)):
            build_mini(nuclear_mod, tmp_path, factor_edit=edit_factor("nuclear:1565", driver_series="nuc_sea_dumped_tbq"))

    def test_matching_driver_series_cell_is_accepted(self, nuclear_mod, tmp_path, mini_base):
        def fill(recs):
            for r in recs:
                if r["stage"] == "reprocessing":
                    r["driver_series"] = "nuc_reprocessed_gwa"
                if r["stage"] == "sea_disposal":
                    r["driver_series"] = "nuc_sea_dumped_tbq"
            return recs
        _, _, rws, _ = build_mini(nuclear_mod, tmp_path, factor_edit=fill)
        a = [vals(r) for r in rws.find(stage="reprocessing")]
        b = [vals(r) for r in mini_base[2].find(stage="reprocessing")]
        assert a == b and a, "filling the optional driver_series cells with the right names must change nothing (R7)"

    @pytest.mark.parametrize("eid,mult", [("E004", 1.01), ("E013", 1.001), ("E002", 1.01)])
    def test_event_total_mismatch_raises(self, nuclear_mod, tmp_path, eid, mult):
        ev = {r["event_id"]: r for r in pd.read_csv(ROOT / "data" / "events.csv", dtype=str, keep_default_na=False).to_dict("records")}
        new = repr(float(ev[eid]["activity_central_bq"]) * mult)
        with pytest.raises(lib_error()):
            build_mini(nuclear_mod, tmp_path, event_edit=edit_event(eid, activity_central_bq=new))

    def test_isl_share_high_above_one_raises(self, nuclear_mod, tmp_path):
        with pytest.raises(lib_error()):
            build_mini(nuclear_mod, tmp_path, factor_edit=edit_factor("nuclear:0026", value_high=1.5))

    @pytest.mark.parametrize("eid,changes", [("E004", {"is_accident": "false"}), ("E003", {"is_accident": "true"}),
                                             ("E004", {"from_tier": "liberated"}), ("E003", {"from_tier": "sealed_in_core"})])
    def test_wrong_event_shape_raises(self, nuclear_mod, tmp_path, eid, changes):
        with pytest.raises(lib_error()):
            build_mini(nuclear_mod, tmp_path, event_edit=edit_event(eid, **changes))

    def test_release_above_inventory_logs_and_keeps_pair_balanced(self, nuclear_mod, tmp_path):
        base = pd.read_csv(ROOT / "data" / "factors" / "nuclear.csv", dtype=str, keep_default_na=False)
        inv = base[(base.region == "SUN") & (base.group == "Cs137+") & (base.tier == "sealed_in_core")].iloc[0]
        rel = base[(base.region == "SUN") & (base.group == "Cs137+") & (base.tier == "liberated")].iloc[0]
        premise(float(inv["value_central"]) > 0 and float(rel["value_central"]) > 0, "E004 Cs137+ has inventory and release rows")

        def shrink(recs):
            for r in recs:
                if r["factor_id"] == inv["factor_id"]:
                    for k in ("value_low", "value_central", "value_high"):
                        r[k] = repr(float(r[k]) * 0.1)
            return recs
        root, res, rws, lg = build_mini(nuclear_mod, tmp_path, factor_edit=shrink)
        es = [e for e in log_entries(lg, "release_exceeds_inventory") if e["group"] == "Cs137+"]
        assert len(es) == 1, f"expected one release_exceeds_inventory for Cs137+, got {es}"
        O = Oracle(root)
        exp = O.expected()
        prob = compare_all({k: v for k, v in exp.rows.items() if v.tag.startswith("acc_")},
                           Rows([r for r in res.rows if r["stage"] == "accident"]), "mini accident")
        flat = [m for k, v in prob.items() if k != "unexpected" for m in v]
        assert not flat, show(flat)
        out = rws.one(1986, stage="accident", group="Cs137+", tier="sealed_in_core", quantity="transfer_out", event_id="E004")
        lib = rws.one(1986, stage="accident", group="Cs137+", tier="liberated", quantity="transfer_in", event_id="E004")
        assert close(float(out["value_central"]), float(lib["value_central"]), BAL), "O = R when R exceeds I at the central"
        assert not rws.find(1986, stage="accident", group="Cs137+", tier="sealed_damaged_core") or \
            float(rws.one(1986, stage="accident", group="Cs137+", tier="sealed_damaged_core")["value_central"]) == 0

    def test_missing_phi_civil_gives_no_uranium_rows(self, nuclear_mod, tmp_path):
        act = mini_act()
        act["uranium.csv"] = [r for r in act["uranium.csv"] if r["series"] != "phi_civil"]
        _root, _res, rws, lg = build_mini(nuclear_mod, tmp_path, act)
        # E003 Church Rock is a u_milling event row (§7.6, no activity driver), so it is exempt.
        assert not [r for r in rws.find(stage="u_milling") if not r.get("event_id")], "no phi_civil: no uranium rows"
        assert [e for e in log_entries(lg, "no_driver") if e["country"] in ("XXX", "")], "missing phi_civil must be logged as no_driver"
