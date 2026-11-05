"""Spec-blind tests for the oil and gas stream script (Task 2.3, docs/OIL_GAS_SPEC.md v1.1 section 9 (a)-(j)).

Written from docs/OIL_GAS_SPEC.md (v1.1, sections 1-12), docs/NUCLEAR_SPEC.md (13), docs/COAL_SPEC.md
(11-12), docs/LIB_SPEC.md (v1.4), docs/SCHEMA.md (v2.4b), docs/DECISIONS.md, data/factors/oil_gas.csv,
data/activity/oil_gas*.csv and data/reference/*. pipeline/streams/oil_gas.py was not read (it does not
exist yet). All expected values come from the independent arithmetic in oil_gas_oracle.py (pandas plus the
standard library; no pipeline.lib); the factor and activity numbers are read from the files, never
hard-coded. Registry and data premises are asserted first, with the text "PREMISE BROKEN" in the message.

Mapping to OIL_GAS_SPEC section 9
---------------------------------
(a) Schema               TestSchema, TestRowConventions
(b) Candidates/coverage  TestRowsAgainstOracle (every family, every row), TestCoverage
(c) Conservation         TestWaterTierSplit, TestSolids, TestMerge, TestAllocation, TestRestOfWorld,
                         TestNoDoubleCounting
(d) Determinism          TestDeterminism
(e) Benchmarks           TestBenchmarks (B1-B7) with runtime xfail for the documented known misses
(f) Hand-computed        TestHandComputed (plain central-value arithmetic, no oracle)
(g) Fixture tests        TestMini* (miniature trees in tmp_path, full real factor file, shrunk activity files)
(h) Pre-1950 file        TestPre1950
(i) Premise assertions   TestPremises
(j) CLI                  TestCli
plus TestFlagsAndNotes (3.3), TestLog (8), TestStderr (3.7), TestMainRadio (4.4, 4.5), TestEpsilonState (7.4).

SPEC AMBIGUITIES / DEFECTS (the tests avoid asserting anything beyond a defensible reading)
--------------------------------------------------------------------------------------------
A1  (resolved, D71 C4) Stepwise nesting per 5.2: A = product(apply(V, C), share), W = product(A, f), S = product(A, sigma) ...
    The oracle follows it exactly, including the zero-central rule on intermediates.
A2  (resolved, D71 C2) A year before the first unit-value year logs no_unit_value; a gap inside the series raises.
A3  (resolved, D71 C3) The D54 cap is a guard only; no forced-cap fixture. The tests assert it never fires on the registry.
A4  (resolved, D71 C7) Solids contributions list C, share, sigma, pi, phi, R or A; T is not included. factor_ids are
    compared as exact lists (merged rows: union in contribution order).
A5  Log entries carry no series field. no_driver and no_factor runs are identified by (kind, country, group)
    and by the union of the years they cover; differential fixtures are used where one series is removed.
A6  Section 6.1 says a negative residual central "becomes 0"; section 3.4 says an exactly zero residual gives
    no rows. Coal 12.7 says no row. The tests require no rest-of-world row and one negative_residual entry.
A7  B5 and 9(c)5 state a relative 1e-6 identity for flaring, but the 1e-5 tolerance of 3.4 lets the country
    rows differ from the XWL row by up to 1e-5 (2020: 2.6e-6). The identity is tested at 1e-6 where a
    residual row is written or the XWL row is used, at 1e-5 where the tolerance dropped the residual.
A8  The CLI "one line per log kind": the line format is `log <kind>: <count>`; a kind with a zero count may
    or may not be printed. The tests check every kind present in the log and accept absent zero lines.
A9  Section 8 does not say which country/group the lib_warning entry carries beyond "year and country
    empty"; the tests accept None or "" and require a count and a message type in the detail.
A10 `_radio_product(geography, year, quantities, values)`: the argument types are not given. The test passes
    {product: q} and {product: unit value} dicts and expects a product name.
A11 Whether the run of a no_driver entry restarts at 1950 (separate pre-1950 walk) or spans 1900-2025 is
    not stated; coverage tests use the union of covered years per country.
A12 Section 3.3 expects the oil-sands ore rows "after the last measured year" to be extrapolated; in the
    file 2017-2025 are measured and only 1967-71 are extrapolated. The tests read the basis from the file.
A13 The XWL unit_value_gas series is basis extrapolated in every year, so every default joint row carries
    "; allocation basis: extrapolated" (plus modelled where a quantity row is modelled). Read from the file.
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
from collections import Counter, defaultdict
from pathlib import Path
from typing import ClassVar

import pandas as pd
import pytest
from oil_gas_oracle import (
    ALLOC_BASIS_WORDS,
    PRODUCTS,
    REST_GAS,
    REST_WATER,
    TOL,
    WORLD_FLARE,
    Oracle,
    cdiff,
    diff,
    sum_independent,
)

# pipeline/tests/streams/test_oil_gas.py -> streams -> tests -> pipeline -> repository root
ROOT = Path(__file__).resolve().parents[3]

REL = 1e-7          # value comparison against the oracle (in-memory floats)
RUN_RE = re.compile(r"^(\d{4})-(\d{4}) \((\d+) years?\)")
LOG_KINDS = {"no_factor", "no_driver", "no_unit_value", "no_family", "negative_residual", "cap_applied",
             "lib_warning"}
CODES = ["PW", "AB", "DR", "GD", "GN", "GV", "GP", "OR", "FL", "OS"]
JOINT = {"PW", "AB", "DR"}
WATER_TIERS = ("reisolated", "impounded", "liberated", "dispersed")
SUBSTREAMS = ("conventional", "unconventional")


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
    return (int(r["year"]), r["substream"], r["stage"], r["country"], r["group"], r["tier"], r["route"] or "",
            r["residue_type"] or "", r["product"] or "", r["allocation_variant"])


def describe(r: dict) -> str:
    keys = ("year", "substream", "stage", "country", "group", "tier", "route", "residue_type", "product",
            "allocation_variant")
    return ", ".join(f"{k}={r.get(k)!r}" for k in keys)


def vals(r: dict) -> tuple[float, float, float]:
    return float(r["value_low"]), float(r["value_central"]), float(r["value_high"])


NOTE_DRV = re.compile(r"; driver basis: ([a-z+]+)")
NOTE_ALLOC = re.compile(r"; allocation basis: ([a-z+]+)")
NOTE_CAUSE = re.compile(r"; below_detection cause: ([a-z_+]+)\s*$")


def notes_parts(n) -> dict:
    n = n or ""
    out = {"text": n, "drv": None, "alloc": None, "cause": None, "alloc_raw": None, "drv_raw": None}
    pos = []
    m = NOTE_DRV.search(n)
    if m:
        out["drv"], out["drv_raw"] = set(m.group(1).split("+")), m.group(1)
        pos.append(m.start())
    m = NOTE_ALLOC.search(n)
    if m:
        out["alloc"], out["alloc_raw"] = set(m.group(1).split("+")), m.group(1)
        pos.append(m.start())
    m = NOTE_CAUSE.search(n)
    if m:
        out["cause"] = m.group(1).split("+")
        pos.append(m.start())
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


def covered(entries: list[dict]) -> set[int]:
    out: set[int] = set()
    for e in entries:
        r = run_of(e)
        if r:
            out |= set(range(r[0], r[1] + 1))
    return out


def lib_error():
    from pipeline.lib import LibError
    return LibError


# --------------------------------------------------------------------------------------------
# module-scoped fixtures
# --------------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def og_mod():
    try:
        return importlib.import_module("pipeline.streams.oil_gas")
    except ImportError as exc:  # expected until the code-writer is done
        pytest.fail(f"cannot import pipeline.streams.oil_gas (OIL_GAS_SPEC 1): {type(exc).__name__}: {exc}")


@pytest.fixture(scope="module")
def result(og_mod):
    assert hasattr(og_mod, "build"), "pipeline.streams.oil_gas must expose build(root) (OIL_GAS_SPEC 1)"
    res = og_mod.build(ROOT)
    for attr in ("rows", "rows_pre1950", "log"):
        assert hasattr(res, attr), f"BuildResult has no attribute {attr!r} (OIL_GAS_SPEC 1)"
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
    d = tmp_path_factory.mktemp("og_written")
    main, pre = d / "oil_gas.csv", d / "oil_gas_pre1950.csv"
    write_master(list(result.rows), main)
    write_master(list(result.rows_pre1950), pre)
    return main, pre


def _copy_tree(dst: Path) -> Path:
    shutil.copytree(ROOT / "data", dst / "data", ignore=shutil.ignore_patterns("streams", "streams_pre1950"))
    shutil.copytree(ROOT / "schema", dst / "schema")
    (dst / "data" / "streams").mkdir()
    (dst / "data" / "streams_pre1950").mkdir()
    (dst / "research" / "oil_gas").mkdir(parents=True)
    return dst


def fx(oracle: Oracle, fid: str) -> dict:
    return oracle.fid[fid]


def fc(oracle: Oracle, fid: str) -> tuple[float, float, float]:
    f = oracle.fid[fid]
    return float(f["value_low"]), float(f["value_central"]), float(f["value_high"])


# --------------------------------------------------------------------------------------------
# row-by-row comparison with the oracle (the engine of (b), (c) and (f))
# --------------------------------------------------------------------------------------------
def compare_row(er, r: dict) -> list[str]:
    msgs: list[str] = []
    if r["stream"] != "oil_gas":
        msgs.append(f"stream={r['stream']!r}")
    if r["basis"] != "modelled":
        msgs.append(f"basis={r['basis']!r}, expected 'modelled' (3.1)")
    if r["quantity"] != "flow" or r["unit"] != "Bq/a":
        msgs.append(f"quantity/unit = {r['quantity']!r}/{r['unit']!r}, expected flow/Bq/a (3.1)")
    if as_bool(r["embedded_fuel"]):
        msgs.append("embedded_fuel true")
    for col in ("technology", "event_id"):
        if not _blank(r[col]):
            msgs.append(f"{col}={r[col]!r}, expected empty")
    if r["product"] != er.product or r["allocation_variant"] != er.variant:
        msgs.append(f"product/variant = {r['product']!r}/{r['allocation_variant']!r}")
    if ids(r["allocation_rule"]) != [er.rule]:
        msgs.append(f"allocation_rule={r['allocation_rule']!r}, expected {er.rule!r}")
    got = vals(r)
    want = (er.b.low, er.b.central, er.b.high)
    if not close(got[0], want[0]):
        msgs.append(f"value_low={got[0]!r}, oracle {want[0]!r}")
    if not close(got[1], want[1]):
        msgs.append(f"value_central={got[1]!r}, oracle {want[1]!r}")
    if not close(got[2], want[2]):
        msgs.append(f"value_high={got[2]!r}, oracle {want[2]!r}")
    flagged = as_bool(r["below_detection"])
    if flagged != er.b.nd:
        msgs.append(f"below_detection={flagged}, oracle {er.b.nd}")
    fid = ids(r["factor_ids"])
    if len(set(fid)) != len(fid):
        msgs.append(f"factor_ids has duplicates: {fid}")
    if fid != er.factor_ids:
        msgs.append(f"factor_ids={fid}, expected {er.factor_ids} (3.9, D71 C7)")
    src = ids(r["source_ids"])
    if src != sorted(src):
        msgs.append(f"source_ids not sorted: {src}")
    if not (er.src_req <= set(src) <= er.src_req | er.src_opt):
        msgs.append(f"source_ids={src}: missing {sorted(er.src_req - set(src))}, "
                    f"unexpected {sorted(set(src) - er.src_req - er.src_opt)}")
    n = notes_parts(r["notes"])
    if not n["text"].startswith(er.code + ":"):
        msgs.append(f"notes do not start with {er.code + ':'!r}: {n['text'][:60]!r}")
    for frag in er.fragments:
        if frag not in n["text"]:
            msgs.append(f"notes lack the fragment {frag!r}")
    if not er.fragments:
        for bad in (REST_GAS, REST_WATER, WORLD_FLARE):
            if bad in n["text"]:
                msgs.append(f"notes carry {bad!r} on a row that is not a rest-of-world / world-aggregate row")
    if er.code in JOINT and f"D6 {er.variant}, product {er.product}" not in n["text"]:
        msgs.append(f"notes lack 'D6 {er.variant}, product {er.product}'")
    if not n["order_ok"]:
        msgs.append(f"notes suffix order wrong: {n['text'][-170:]!r}")
    if (n["drv"] or set()) != er.driver_basis:
        msgs.append(f"driver basis {n['drv']}, expected {sorted(er.driver_basis) or None}")
    want_alloc = (er.alloc_basis or set()) if er.variant == "default" and er.code in JOINT else set()
    if (n["alloc"] or set()) != want_alloc:
        msgs.append(f"allocation basis {n['alloc']}, expected {sorted(want_alloc) or None}")
    if n["alloc_raw"] and n["alloc_raw"] != "+".join(sorted(n["alloc"])):
        msgs.append(f"allocation basis not alphabetical: {n['alloc_raw']}")
    if n["drv_raw"] and n["drv_raw"] != "+".join(sorted(n["drv"])):
        msgs.append(f"driver basis not alphabetical: {n['drv_raw']}")
    if flagged:
        if n["cause"] != list(er.b.causes):
            msgs.append(f"cause {n['cause']}, oracle {list(er.b.causes)}")
    elif n["cause"] is not None:
        msgs.append(f"unflagged row carries a cause suffix {n['cause']}")
    return msgs


def compare_all(exp: dict, rows_obj: Rows, label: str) -> dict[str, list[str]]:
    problems: dict[str, list[str]] = defaultdict(list)
    for k, er in exp.items():
        got = rows_obj.by_key.get(k)
        if not got:
            problems[er.tag].append(f"MISSING row {dict(zip(('year','substream','stage','country','group','tier','route','residue','product','variant'), k))}")
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


def show(msgs: list[str], n: int = 6) -> str:
    return f"{len(msgs)} problem(s); first {min(n, len(msgs))}:\n  " + "\n  ".join(msgs[:n])


@pytest.fixture(scope="module")
def comparison(rows, expected):
    return compare_all(expected.rows, rows, "master")


@pytest.fixture(scope="module")
def comparison_pre(pre_rows, expected):
    return compare_all(expected.pre, pre_rows, "pre1950")


# --------------------------------------------------------------------------------------------
# section 3: row conventions
# --------------------------------------------------------------------------------------------
class TestRowConventions:
    """(a) and section 3.1: columns, constants, ordering."""

    def test_rows_are_nonempty_dicts(self, rows, pre_rows):
        assert rows.rows, "build().rows is empty"
        assert pre_rows.rows, "build().rows_pre1950 is empty (gas and oil radon from 1900, OIL_GAS_SPEC 3.8)"
        assert all(isinstance(r, dict) for r in rows.rows[:50])

    def test_master_columns_present(self, rows):
        cols = ["year", "stream", "substream", "stage", "product", "residue_type", "country", "group", "tier",
                "quantity", "unit", "value_low", "value_central", "value_high", "below_detection", "basis",
                "source_ids", "factor_ids", "allocation_variant", "allocation_rule", "embedded_fuel", "technology",
                "route", "event_id", "notes"]
        bad = [r for r in rows.rows if list(r.keys()) != cols]
        assert not bad, f"{len(bad)} rows do not have exactly the 25 master columns in order; first: {bad[0]}"

    def test_year_ranges(self, rows, pre_rows):
        assert min(int(r["year"]) for r in rows.rows) >= 1950 and max(int(r["year"]) for r in rows.rows) <= 2025
        py = [int(r["year"]) for r in pre_rows.rows]
        assert py and min(py) >= 1900 and max(py) <= 1949

    def test_stream_basis_flow_unit(self, rows, pre_rows):
        for r in rows.rows + pre_rows.rows:
            assert r["stream"] == "oil_gas" and r["basis"] == "modelled", describe(r)
            assert r["quantity"] == "flow" and r["unit"] == "Bq/a", f"quantity/unit {r['quantity']}/{r['unit']}: {describe(r)}"

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
            assert all(x.startswith("oil_gas:") for x in f), f"unexpected factor id {f}: {describe(r)}"

    def test_product_required_and_in_vocabulary(self, rows, pre_rows):
        for r in rows.rows + pre_rows.rows:
            assert r["product"] in ("oil", "gas", "ngl", "bitumen"), f"product {r['product']!r} (V11): {describe(r)}"
            assert (r["product"] == "bitumen") == (r["stage"] == "oil_sands_mining"), describe(r)

    def test_substream_by_family(self, rows, pre_rows):
        for r in rows.rows + pre_rows.rows:
            st = r["stage"]
            if st == "oil_sands_mining":
                want = {"oil_sands"}
            elif st == "processing_transport" or (st == "production" and r["group"] == "Rn222+"):
                want = {"all"}
            else:
                want = {"conventional", "unconventional"}
            assert r["substream"] in want, f"substream {r['substream']!r} not in {want}: {describe(r)}"

    def test_residue_type_iff_impounded_reisolated_dispersed(self, rows, pre_rows):
        for r in rows.rows + pre_rows.rows:
            has = not _blank(r["residue_type"])
            assert has == (r["tier"] in ("impounded", "reisolated", "dispersed")), f"residue_type rule (R02): {describe(r)}"

    def test_route_iff_liberated(self, rows, pre_rows):
        for r in rows.rows + pre_rows.rows:
            assert (not _blank(r["route"])) == (r["tier"] == "liberated"), f"route rule (R02): {describe(r)}"

    def test_event_technology_embedded_fuel(self, rows, pre_rows):
        for r in rows.rows + pre_rows.rows:
            assert _blank(r["event_id"]) and _blank(r["technology"]) and not as_bool(r["embedded_fuel"]), describe(r)

    def test_no_transfers_memo_opening_stock_or_unregistered_routes(self, rows, pre_rows):
        for r in rows.rows + pre_rows.rows:
            assert not r["tier"].startswith("memo"), f"memo tier: {describe(r)}"
            assert r["quantity"] == "flow", f"quantity {r['quantity']}: {describe(r)}"
        routes = {r["route"] for r in rows.rows + pre_rows.rows if r["route"]}
        assert routes <= {"air_delivered_gas", "air_vented_gas", "air_stack", "water_produced_discharge"}, \
            f"routes outside the registry's: {sorted(routes)}"

    def test_rn222_only_liberated_flow(self, rows, pre_rows):
        for r in rows.rows + pre_rows.rows:
            if r["group"] == "Rn222+":
                assert r["tier"] == "liberated" and r["quantity"] == "flow", f"V09: {describe(r)}"

    def test_country_conventions(self, rows, pre_rows):
        for r in rows.rows:
            if r["stage"] == "drilling":
                assert r["country"] == "USA", describe(r)
            elif r["stage"] == "oil_sands_mining":
                assert r["country"] == "CAN", describe(r)
            elif r["stage"] in ("production", "abandonment_scrap") and r["group"] != "Rn222+":
                assert r["country"] in ("USA", "XXX"), f"water-borne rows exist for USA and XXX only: {describe(r)}"
        assert not [r for r in pre_rows.rows if r["stage"] not in ("processing_transport",)], \
            "pre-1950 file may hold processing_transport rows only (3.8)"

    def test_allocation_tokens_by_variant(self, rows):
        tok = {"default": "alloc:value", "bound_main": "alloc:main", "bound_radio": "alloc:radio"}
        for r in rows.rows:
            t = ids(r["allocation_rule"])
            if r["product"] == "bitumen" or r["stage"] == "processing_transport" or (
                    r["stage"] == "production" and r["group"] == "Rn222+"):
                assert r["allocation_variant"] == "default" and t == ["none"], f"single-driver row: {describe(r)} {t}"
            else:
                assert t == [tok[r["allocation_variant"]]], f"{describe(r)} rule {t}"


# --------------------------------------------------------------------------------------------
# (a) schema
# --------------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def issues(written):
    from pipeline.validate import validate

    root = _copy_tree(Path(written[0]).parent / "validation_root")
    shutil.copy(written[0], root / "data" / "streams" / "oil_gas.csv")
    found = validate(root, master_files=["data/streams/oil_gas.csv"])
    return [i for i in found if i.file == "data/streams/oil_gas.csv"]


class TestSchema:
    def test_validator_accepts_oil_gas_csv(self, issues):
        shown = "\n".join(f"  row {i.row}: {i.rule} {i.message}" for i in issues[:15])
        assert not issues, (f"data/streams/oil_gas.csv has {len(issues)} validator issues "
                            f"(rules {sorted({i.rule for i in issues})}):\n{shown}")

    @pytest.mark.parametrize("rule", ["V03", "V07", "V09", "V10", "V11", "V12", "V13", "V15", "X01", "X02", "X03",
                                      "X05", "R02"])
    def test_no_rule_violations(self, issues, rule):
        hits = [i for i in issues if i.rule == rule]
        assert not hits, f"{len(hits)} {rule} issues, first: row {hits[0].row} {hits[0].message}"

    def test_vocabulary_has_all_under_oil_gas(self):
        v = json.loads((ROOT / "data" / "reference" / "vocab.json").read_text(encoding="utf-8"))
        premise("all" in v["substreams"]["oil_gas"], "vocab.json substreams.oil_gas lacks 'all' (schema v2.4b, D70)")


# --------------------------------------------------------------------------------------------
# (b) every family, every row, against the oracle
# --------------------------------------------------------------------------------------------
class TestRowsAgainstOracle:
    """Row sets and values of every family, recomputed from the files (9(b), 9(c)3/4, 9(f))."""

    def test_oracle_has_no_missing_factor_lookup(self, expected):
        premise(not expected.missing, f"the oracle could not select a factor: {expected.missing[:2]}")

    @pytest.mark.parametrize("tag", CODES)
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

    def test_oracle_expects_every_stage(self, expected):
        stages = {k[2] for k in expected.rows}
        premise(stages == {"production", "processing_transport", "abandonment_scrap", "drilling", "oil_sands_mining"},
                f"stages in the oracle: {stages}")


class TestCoverage:
    """9(b): candidate nuclides, the nine rows per joint key, geographies."""

    def test_nine_rows_per_joint_key(self, rows):
        groups = defaultdict(set)
        for r in rows.rows:
            if r["stage"] in ("production", "abandonment_scrap", "drilling") and r["group"] != "Rn222+":
                k = (int(r["year"]), r["substream"], r["stage"], r["country"], r["group"], r["tier"], r["route"] or "",
                     r["residue_type"] or "")
                groups[k].add((r["product"], r["allocation_variant"]))
        full = {(p, v) for p in PRODUCTS for v in ("default", "bound_main", "bound_radio")}
        bad = [k for k, s in groups.items() if s != full]
        assert groups and not bad, f"{len(bad)} joint keys without all nine (product, variant) rows, first {bad[:1]}"

    def test_methods_4_3_groups_in_2010(self, rows):
        for g in ("Ra226+", "Ra228+", "Pb210+", "K40", "Rn222+"):
            assert rows.find(2010, group=g, stage=("production", "processing_transport")), f"{g} absent from 2010 flows"

    def test_th228_and_po210_only_in_cuttings_and_oil_sands(self, rows):
        for g in ("Th228+", "Po210"):
            stages = {r["stage"] for r in rows.rows if r["group"] == g}
            assert stages <= {"drilling", "oil_sands_mining"}, \
                f"{g} appears at {sorted(stages)}: engine ingrowth must not be booked as a row (9(b))"
        assert any(r["stage"] == "drilling" for r in rows.rows if r["group"] == "Po210")
        assert any(r["stage"] == "oil_sands_mining" for r in rows.rows if r["group"] == "Th228+")

    def test_geographies_by_family(self, rows):
        for sub in SUBSTREAMS:
            for geo in ("USA", "XXX"):
                yrs = {int(r["year"]) for r in rows.rows if r["stage"] == "production" and r["substream"] == sub
                       and r["country"] == geo and r["group"] != "Rn222+"}
                assert yrs == set(range(1950, 2026)), f"{sub}/{geo} production years incomplete: {sorted(set(range(1950, 2026)) - yrs)[:5]}"
        dr = {(r["substream"], int(r["year"])) for r in rows.rows if r["stage"] == "drilling"}
        assert {y for s, y in dr if s == "conventional"} == set(range(1950, 2026)), "vertical drilling 1950-2025"
        assert {y for s, y in dr if s == "unconventional"} == set(range(1980, 2026)), "horizontal drilling 1980-2025"
        os_ = {int(r["year"]) for r in rows.rows if r["stage"] == "oil_sands_mining"}
        assert os_ == set(range(1967, 2026)), "oil sands 1967-2025"

    def test_group_sets(self, rows):
        assert {r["group"] for r in rows.rows if r["stage"] == "drilling"} == {
            "U238+", "U234", "Th230", "U235+", "Ra226+", "Pb210+", "Po210", "Th232", "Ra228+", "Th228+", "K40"}
        assert {r["group"] for r in rows.rows if r["stage"] == "oil_sands_mining"} == {"Th232", "Ra228+", "Th228+"}
        assert {r["group"] for r in rows.rows if r["stage"] == "abandonment_scrap"} == {"Ra226+", "Ra228+", "Pb210+"}
        assert {r["group"] for r in rows.rows if r["stage"] == "production" and r["group"] != "Rn222+"} == {
            "Ra226+", "Ra228+", "K40", "Pb210+"}

    def test_k40_has_no_solids_rows(self, rows):
        assert not rows.find(stage="abandonment_scrap", group="K40")
        assert not [r for r in rows.rows if r["stage"] == "production" and r["group"] == "K40" and r["residue_type"] == "og_scale"]

    def test_no_pre1950_in_main_and_no_post1949_in_pre(self, rows, pre_rows):
        assert all(int(r["year"]) >= 1950 for r in rows.rows)
        assert all(int(r["year"]) <= 1949 for r in pre_rows.rows)


# --------------------------------------------------------------------------------------------
# (c) conservation
# --------------------------------------------------------------------------------------------
def sums_by(rows_obj: Rows, pred, keyf):
    """Sum low/central/high over rows that pass pred, grouped by keyf."""
    out: dict = defaultdict(lambda: [0.0, 0.0, 0.0])
    for r in rows_obj.rows:
        if pred(r):
            s = out[keyf(r)]
            lo, c, hi = vals(r)
            s[0] += lo
            s[1] += c
            s[2] += hi
    return out


class TestWaterTierSplit:
    def test_k40_tier_rows_sum_to_water_activity(self, rows, expected):
        """K-40 has no solids, so the four merged tier rows are the pure water tiers (summed over products)."""
        s = sums_by(rows, lambda r: r["stage"] == "production" and r["group"] == "K40" and r["allocation_variant"] == "default",
                    lambda r: (r["country"], int(r["year"]), r["substream"]))
        n = 0
        for (geo, y, sub), (lo, c, hi) in s.items():
            A = expected.parts.get((geo, y, sub, "A", "K40"))
            assert A is not None, f"oracle has no water activity for {geo} {y} {sub}"
            assert math.isclose(c, A.central, rel_tol=1e-3), \
                f"{geo} {y} {sub} K40: four tier rows sum to {c:.6g}, water activity {A.central:.6g} (9(c)1)"
            n += 1
        assert n == 2 * 76 * 2, f"expected 304 geography-year-substream sets, found {n}"

    def test_no_tier_row_exceeds_activity_at_any_bound(self, rows, expected):
        for r in rows.rows:
            if r["stage"] == "production" and r["group"] == "K40":
                A = expected.parts[(r["country"], int(r["year"]), r["substream"], "A", "K40")]
                lo, c, hi = vals(r)
                assert lo <= A.low * (1 + 1e-9) + 1e-30 and c <= A.central * (1 + 1e-9) + 1e-30 and hi <= A.high * (1 + 1e-9) + 1e-30, \
                    f"tier row above the water activity: {describe(r)}"

    def test_oracle_water_shares_close_to_one(self, expected):
        bad = []
        by = defaultdict(float)
        for k, v in expected.parts.items():
            if len(k) == 6 and k[3] == "W":
                by[(k[0], k[1], k[2], k[4])] += v.central
        for (geo, y, sub, g), tot in by.items():
            A = expected.parts[(geo, y, sub, "A", g)].central
            if A > 0 and not math.isclose(tot, A, rel_tol=1e-3):
                bad.append((geo, y, sub, g, tot / A))
        assert not bad, f"{len(bad)} water tier sets do not sum to the activity within 1e-3: {bad[:3]}"

    def test_cap_not_expected_to_fire_on_the_registry(self, log):
        assert not log_entries(log, "cap_applied"), "cap_applied entries on the real registry (3.4: not expected)"


class TestSolids:
    def test_scale_removed_plus_retained_equals_formed(self, expected):
        n = 0
        for k, S in expected.parts.items():
            if len(k) == 6 and k[3] == "S" and k[5] == "og_scale":
                geo, y, sub, _, g, r = k
                rem, ret = expected.parts[(geo, y, sub, "Srem", g, r)], expected.parts[(geo, y, sub, "Sret", g, r)]
                assert math.isclose(rem.central + ret.central, S.central, rel_tol=1e-9), (geo, y, sub, g)
                n += 1
        assert n == 2 * 76 * 2 * 3

    def test_pb210_solids_are_pi_times_ra226_solids(self, expected, oracle):
        for res, pid in (("og_scale", "oil_gas:0051"), ("og_sludge", "oil_gas:0052")):
            premise(fx(oracle, pid)["residue_type"] == res and fx(oracle, pid)["group"] == "Pb210+", f"{pid} is the {res} Pb-210 ratio")
            pi = fc(oracle, pid)[1]
            for geo in ("USA", "XXX"):
                for y in (1950, 1975, 2010, 2025):
                    for sub in SUBSTREAMS:
                        pb = expected.parts[(geo, y, sub, "S", "Pb210+", res)].central
                        ra = expected.parts[(geo, y, sub, "S", "Ra226+", res)].central
                        assert math.isclose(pb, pi * ra, rel_tol=1e-9, abs_tol=0), (geo, y, sub, res)

    def test_sludge_tiers_sum_to_sludge_formed(self, expected):
        by = defaultdict(float)
        for k, v in expected.parts.items():
            if len(k) == 7 and k[3] == "X" and k[5] == "og_sludge":
                by[(k[0], k[1], k[2], k[4])] += v.central
        assert by
        for (geo, y, sub, g), tot in by.items():
            S = expected.parts[(geo, y, sub, "S", g, "og_sludge")].central
            assert S == 0 or math.isclose(tot, S, rel_tol=1e-3), (geo, y, sub, g, tot / S)

    def test_scale_removed_tiers_sum_to_removed_scale(self, expected):
        by = defaultdict(float)
        for k, v in expected.parts.items():
            if len(k) == 7 and k[3] == "X" and k[5] == "og_scale":
                by[(k[0], k[1], k[2], k[4])] += v.central
        for (geo, y, sub, g), tot in by.items():
            rem = expected.parts[(geo, y, sub, "Srem", g, "og_scale")].central
            assert rem == 0 or math.isclose(tot, rem, rel_tol=1e-3), (geo, y, sub, g, tot / rem)

    def test_abandonment_rows_equal_retained_scale(self, rows, expected):
        s = sums_by(rows, lambda r: r["stage"] == "abandonment_scrap" and r["allocation_variant"] == "default",
                    lambda r: (r["country"], int(r["year"]), r["substream"], r["group"]))
        assert s
        for (geo, y, sub, g), (lo, c, hi) in s.items():
            ret = expected.parts[(geo, y, sub, "Sret", g, "og_scale")]
            assert c == ret.central == 0 or math.isclose(c, ret.central, rel_tol=1e-3), \
                f"abandonment rows {geo} {y} {sub} {g}: {c:.6g} vs retained scale {ret.central:.6g}"

    def test_sludge_only_and_scale_only_keys_equal_their_contribution(self, rows, expected):
        """dispersed/og_sludge and impounded/og_scale hold exactly one contribution each (5.5)."""
        for key, part in (("dispersed", "og_sludge"), ("impounded", "og_scale")):
            s = sums_by(rows, lambda r, key=key, part=part: r["stage"] == "production" and r["tier"] == key
                        and r["residue_type"] == part and r["allocation_variant"] == "default",
                        lambda r: (r["country"], int(r["year"]), r["substream"], r["group"]))
            assert s
            for (geo, y, sub, g), (lo, c, hi) in s.items():
                X = expected.parts[(geo, y, sub, "X", g, part, key)]
                assert (c == 0 and X.central == 0) or math.isclose(c, X.central, rel_tol=1e-7), (geo, y, sub, g, key, part)


class TestMerge:
    def test_liberated_ra226_usa_2010_is_water_plus_removed_solids(self, rows, expected):
        y, geo, sub, g = 2010, "USA", "conventional", "Ra226+"
        P = expected.parts
        parts = [P[(geo, y, sub, "W", g, "liberated")], P[(geo, y, sub, "X", g, "og_scale", "liberated")],
                 P[(geo, y, sub, "X", g, "og_sludge", "liberated")]]
        lo, c, hi = (sum(p.low for p in parts), sum(p.central for p in parts), sum(p.high for p in parts))
        got = [rows.one(y, stage="production", substream=sub, country=geo, group=g, tier="liberated", product=p,
                        allocation_variant="default") for p in PRODUCTS]
        for name, idx, want in (("low", 0, lo), ("central", 1, c), ("high", 2, hi)):
            assert math.isclose(sum(vals(r)[idx] for r in got), want, rel_tol=1e-7), f"merged liberated row {name}"
        fid = ids(got[0]["factor_ids"])
        assert len(fid) == len(set(fid)) and {"oil_gas:0002", "oil_gas:0012"} <= set(fid)

    def test_merged_row_is_larger_than_the_water_term(self, rows, expected):
        """5.5: the solids are additive to the water, never subtracted."""
        for geo in ("USA", "XXX"):
            for y in (1960, 1990, 2010, 2020):
                for tier in ("liberated", "impounded"):
                    for sub in SUBSTREAMS:
                        tot = sum(float(r["value_central"]) for r in rows.find(
                            y, stage="production", substream=sub, country=geo, group="Ra226+", tier=tier,
                            allocation_variant="default") if tier == "liberated" or r["residue_type"] == "og_sludge")
                        W = expected.parts[(geo, y, sub, "W", "Ra226+", tier)]
                        assert tot >= W.central * (1 - 1e-9), (geo, y, sub, tier)

    def test_k40_liberated_has_no_solids_and_three_factors(self, rows):
        r = rows.one(2010, stage="production", substream="conventional", country="USA", group="K40", tier="liberated",
                     product="oil", allocation_variant="default")
        assert len(ids(r["factor_ids"])) == 3, f"K-40 liberated: concentration, share, tier-fate only: {r['factor_ids']}"

    def test_pb210_impounded_sludge_row_includes_solids(self, rows, expected):
        y, geo, sub = 2010, "XXX", "conventional"
        P = expected.parts
        want = P[(geo, y, sub, "W", "Pb210+", "impounded")].central + P[(geo, y, sub, "X", "Pb210+", "og_sludge", "impounded")].central
        got = sum(float(r["value_central"]) for r in rows.find(
            y, stage="production", substream=sub, country=geo, group="Pb210+", tier="impounded", residue_type="og_sludge",
            allocation_variant="default"))
        assert math.isclose(got, want, rel_tol=1e-7), f"Pb-210 impounded sludge row {got:.6g} vs pit water + removed sludge {want:.6g}"


class TestAllocation:
    def test_variants_split_the_same_unallocated_value(self, rows):
        grp = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0, 0.0]))
        for r in rows.rows:
            if r["stage"] in ("production", "abandonment_scrap", "drilling") and r["group"] != "Rn222+":
                k = (int(r["year"]), r["substream"], r["stage"], r["country"], r["group"], r["tier"], r["residue_type"] or "",
                     r["route"] or "")
                s = grp[k][r["allocation_variant"]]
                lo, c, hi = vals(r)
                s[0] += lo
                s[1] += c
                s[2] += hi
        assert grp
        for k, byv in grp.items():
            base = byv["default"]
            for v in ("bound_main", "bound_radio"):
                for i, nm in enumerate(("low", "central", "high")):
                    assert math.isclose(byv[v][i], base[i], rel_tol=1e-5, abs_tol=0), f"{k}: {v} {nm} sum {byv[v][i]} != default {base[i]}"

    def test_default_shares_equal_value_shares_from_the_files(self, rows, oracle):
        n = 0
        for geo in ("USA", "XXX"):
            for y in (1950, 1990, 2010, 2020, 2025):
                al = oracle.alloc(geo, y)
                for g in ("Ra226+", "K40"):
                    rs = {p: rows.one(y, stage="production", substream="conventional", country=geo, group=g, tier="reisolated",
                                      product=p, allocation_variant="default") for p in PRODUCTS}
                    tot = sum(float(r["value_central"]) for r in rs.values())
                    for p in PRODUCTS:
                        assert math.isclose(float(rs[p]["value_central"]) / tot, al["shares"]["default"][p], rel_tol=1e-9), \
                            f"{geo} {y} {g} {p} share"
                    n += 1
        assert n == 20

    def test_bound_variants_have_exactly_one_nonzero_product(self, rows, oracle):
        for geo in ("USA", "XXX"):
            for y in (1950, 1990, 2010, 2020, 2025):
                al = oracle.alloc(geo, y)
                for variant, want in (("bound_main", al["main"]), ("bound_radio", al["radio"])):
                    nz = [p for p in PRODUCTS if float(rows.one(
                        y, stage="production", substream="conventional", country=geo, group="K40", tier="reisolated",
                        product=p, allocation_variant=variant)["value_central"]) > 0]
                    assert nz == [want], f"{geo} {y} {variant}: non-zero products {nz}, expected {[want]}"

    def test_structural_zero_rows_are_exact_zero_unflagged_without_cause(self, rows):
        n = 0
        for r in rows.rows:
            if r["allocation_variant"] != "default" and float(r["value_central"]) == 0 and r["stage"] != "processing_transport":
                lo, c, hi = vals(r)
                if (lo, c, hi) == (0.0, 0.0, 0.0) and not as_bool(r["below_detection"]):
                    assert "below_detection cause" not in (r["notes"] or ""), f"cause text on a structural zero: {describe(r)}"
                    n += 1
        assert n > 0
        # bound rows with a zero value but a non-zero high must not exist: a zero share is exactly zero
        bad = [r for r in rows.rows if r["allocation_variant"] != "default" and float(r["value_central"]) == 0
               and float(r["value_high"]) > 0 and not as_bool(r["below_detection"])]
        assert not bad

    def test_nine_rows_share_factor_and_source_ids(self, rows):
        seen = defaultdict(set)
        for r in rows.rows:
            if r["stage"] in ("production", "abandonment_scrap", "drilling") and r["group"] != "Rn222+":
                k = (int(r["year"]), r["substream"], r["stage"], r["country"], r["group"], r["tier"], r["residue_type"] or "",
                     r["route"] or "")
                seen[k].add((r["factor_ids"], r["source_ids"]))
        bad = [k for k, s in seen.items() if len(s) != 1]
        assert not bad, f"{len(bad)} joint keys whose nine rows differ in factor_ids or source_ids, first {bad[:1]} (3.9)"

    def test_default_rows_carry_value_token_bound_rows_their_own(self, rows):
        for r in rows.rows[:: max(1, len(rows.rows) // 5000)]:
            if r["stage"] in ("production", "abandonment_scrap", "drilling") and r["group"] != "Rn222+":
                want = {"default": "alloc:value", "bound_main": "alloc:main", "bound_radio": "alloc:radio"}[r["allocation_variant"]]
                assert ids(r["allocation_rule"]) == [want], describe(r)


def _family_of(r: dict):
    st, g, rt, pr = r["stage"], r["group"], r["route"], r["product"]
    if st == "processing_transport":
        if g == "Pb210+":
            return "GP"
        if rt == "air_delivered_gas":
            return "GN" if pr == "ngl" else "GD"
        if rt == "air_vented_gas":
            return "GV"
        if rt == "air_stack":
            return "OR"
    if st == "production" and g == "Rn222+":
        return "FL"
    return None


class TestRestOfWorld:
    SERIES: ClassVar[dict] = {"GD": ("gas_production_m3", "oil_gas:0074"), "GN": ("gas_production_m3", "oil_gas:0110"),
              "GV": ("gas_production_m3", "oil_gas:0075"), "GP": ("gas_production_m3", "oil_gas:0076"),
              "OR": ("oil_production_t", "oil_gas:0077"), "FL": ("gas_flared_m3", "oil_gas:0111")}

    @pytest.mark.parametrize("code", ["GD", "GN", "GV", "GP", "OR", "FL"])
    def test_countries_plus_residual_equal_world_times_factor(self, rows, pre_rows, oracle, code):
        series, fid = self.SERIES[code]
        f = fc(oracle, fid)[1]
        tot = defaultdict(float)
        has_xxx = defaultdict(bool)
        for obj in (rows, pre_rows):
            for r in obj.rows:
                if _family_of(r) == code:
                    y = int(r["year"])
                    tot[y] += float(r["value_central"])
                    has_xxx[y] |= r["country"] == "XXX"
        assert tot, f"no {code} rows"
        for y, t in tot.items():
            xwl = oracle.a(series, y, "XWL").b.central
            tol = 1e-6 if (has_xxx[y] and code != "FL") or (code == "FL" and y < 2012) else 1e-5      # A7
            assert math.isclose(t / f, xwl, rel_tol=tol), \
                f"{code} {y}: countries + residual = {t / f:.8g} m3 (or t), world aggregate {xwl:.8g} (9(c)5)"

    def test_xxx_gas_rows_are_clipped_difference_flagged_where_the_low_clips(self, rows, oracle):
        flagged = 0
        for y in (1990, 2010, 2020):
            xw = oracle.a("gas_production_m3", y, "XWL").b
            listed = [oracle.a("gas_production_m3", y, c).b for c in oracle.countries("gas_production_m3", y)]
            R, _ = diff(xw, sum_independent(listed))
            r = rows.one(y, stage="processing_transport", country="XXX", group="Rn222+", route="air_delivered_gas", product="gas")
            assert as_bool(r["below_detection"]) == R.nd, f"{y}: XXX gas row flag vs oracle residual flag {R.nd}"
            if R.nd:
                assert notes_parts(r["notes"])["cause"] == ["clipped_difference"]
                assert REST_GAS in r["notes"]
                flagged += 1
        premise(flagged >= 1, "no year among 1990, 2010, 2020 has a clipped gas residual (spec 6.1 expects them)")


class TestNoDoubleCounting:
    def test_gn_is_driven_by_gas_not_ngl(self, rows, oracle):
        r0 = fc(oracle, "oil_gas:0110")[1] / fc(oracle, "oil_gas:0074")[1]
        n = 0
        for r in rows.rows:
            if _family_of(r) == "GN" and int(r["year"]) % 7 == 0:
                gd = rows.one(int(r["year"]), stage="processing_transport", country=r["country"], group="Rn222+",
                              route="air_delivered_gas", product="gas")
                assert math.isclose(float(r["value_central"]) / float(gd["value_central"]), r0, rel_tol=1e-9), describe(r)
                n += 1
        assert n > 20

    def test_gd_and_gn_differ_only_by_product(self, rows):
        a = rows.one(2010, stage="processing_transport", country="USA", group="Rn222+", route="air_delivered_gas", product="gas")
        b = rows.one(2010, stage="processing_transport", country="USA", group="Rn222+", route="air_delivered_gas", product="ngl")
        assert a["substream"] == b["substream"] == "all" and ids(a["factor_ids"]) == ["oil_gas:0074"] and ids(b["factor_ids"]) == ["oil_gas:0110"]
        assert b["residue_type"] in (None, ""), "NGL radon is liberated: residue_type is only a registry key device (2.3)"

    def test_no_row_cites_retired_flaring_factors(self, rows, pre_rows):
        for obj in (rows, pre_rows):
            for r in obj.rows:
                assert not ({"oil_gas:0071", "oil_gas:0072", "oil_gas:0073"} & set(ids(r["factor_ids"]))), \
                    f"retired factor cited (D70): {describe(r)}"

    def test_flaring_comes_from_exactly_one_source_per_year(self, rows):
        by = defaultdict(list)
        for r in rows.rows:
            if _family_of(r) == "FL":
                by[int(r["year"])].append(r)
        assert set(by) == set(range(1950, 2026)), "flaring rows every year 1950-2025"
        for y, lst in by.items():
            world = [r for r in lst if WORLD_FLARE in (r["notes"] or "")]
            if y < 2012:
                assert len(lst) == 1 and len(world) == 1 and lst[0]["country"] == "XXX", f"{y}: expected one XXX world row"
            else:
                assert not world, f"{y}: world aggregate row alongside country rows (the world would be counted twice)"
                assert all(r["country"] != "XXX" or REST_GAS in r["notes"] for r in lst)
                assert len(lst) >= 50

    def test_flaring_is_oil_product_at_production_stage(self, rows):
        for r in rows.rows:
            if _family_of(r) == "FL":
                assert r["product"] == "oil" and r["substream"] == "all" and r["route"] == "air_stack" and r["tier"] == "liberated"
                assert ids(r["factor_ids"]) == ["oil_gas:0111"], describe(r)

    def test_plate_out_has_no_ngl_row(self, rows):
        assert not [r for r in rows.rows if r["group"] == "Pb210+" and r["stage"] == "processing_transport" and r["product"] != "gas"]

    def test_no_exhalation_seepage_rows(self, rows):
        assert not [r for r in rows.rows if "exhal" in (r["route"] or "") or "seep" in (r["route"] or "")]


# --------------------------------------------------------------------------------------------
# (d) determinism and stderr
# --------------------------------------------------------------------------------------------
class TestDeterminism:
    def test_two_builds_write_identical_bytes_and_log(self, og_mod, result, written, write_master, tmp_path):
        second = og_mod.build(ROOT)
        m2, p2 = tmp_path / "o2.csv", tmp_path / "p2.csv"
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
        assert keys == sorted(keys), "rows are not in SCHEMA 3 key order"
        assert len(set(keys)) == len(keys)


class TestStderr:
    def test_build_writes_nothing_to_stderr_subprocess(self):
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
        code = ("import sys; from pathlib import Path; from pipeline.streams.oil_gas import build; "
                "r = build(Path(sys.argv[1])); print(len(r.rows))")
        p = subprocess.run([sys.executable, "-W", "default", "-c", code, str(ROOT)], cwd=str(ROOT), env=env,
                           capture_output=True, text=True, timeout=1800, check=False)
        assert p.returncode == 0, p.stderr[-1500:]
        assert p.stderr == "", f"build() wrote {len(p.stderr)} bytes to stderr (3.7): {p.stderr[:600]!r}"


# --------------------------------------------------------------------------------------------
# section 3.3: flags, causes, driver basis, allocation basis, suffix order
# --------------------------------------------------------------------------------------------
class TestFlagsAndNotes:
    def test_every_note_has_family_prefix_and_clean_suffix_grammar(self, rows, pre_rows):
        order = ["zero_central_factor", "exact_zero", "clipped_difference", "floor_dominance", "inherited_flag"]
        prefixes = tuple(c + ":" for c in CODES)
        for r in rows.rows + pre_rows.rows:
            n = notes_parts(r["notes"])
            assert n["text"].startswith(prefixes), f"notes without a family code: {n['text'][:50]!r} ({describe(r)})"
            assert n["order_ok"], f"suffix order (rule text, driver basis, allocation basis, cause): {n['text'][-170:]!r}"
            if n["cause"] is not None:
                assert as_bool(r["below_detection"]), f"cause text on an unflagged row: {describe(r)}"
                assert n["cause"] == [c for c in order if c in n["cause"]], f"cause order {n['cause']}"
            elif as_bool(r["below_detection"]):
                pytest.fail(f"flagged row without '; below_detection cause:': {describe(r)}")
            if n["alloc"] is not None:
                assert r["allocation_variant"] == "default" and r["stage"] in ("production", "abandonment_scrap", "drilling"), \
                    f"allocation basis on a row that does not take one: {describe(r)}"
                assert n["alloc"] <= set(ALLOC_BASIS_WORDS)

    def test_xwl_unconventional_water_rows_before_2006_are_zero_central_flagged(self, rows, oracle):
        f16 = fc(oracle, "oil_gas:0016")
        premise(f16[1] == 0 and f16[2] > 0, "registry 0016 (XWL unconventional share 1950-2005) has central 0, high > 0")
        for y in (1950, 1960, 2005):
            for p in PRODUCTS:
                r = rows.one(y, stage="production", substream="unconventional", country="XXX", group="Ra226+",
                             tier="reisolated", product=p, allocation_variant="default")
                if float(r["value_high"]) == 0:
                    continue
                assert float(r["value_central"]) == 0 and float(r["value_low"]) == 0 and as_bool(r["below_detection"]), describe(r)
                assert "zero_central_factor" in notes_parts(r["notes"])["cause"], r["notes"]
                assert float(r["value_high"]) > 0

    def test_usa_unconventional_water_rows_before_2006_are_floor_dominance_flagged(self, rows, oracle):
        f11 = fc(oracle, "oil_gas:0011")
        premise(f11[0] == 0 and f11[1] > 0, "registry 0011 (USA unconventional share 1950-2005) has low 0, central > 0")
        r = rows.one(1960, stage="production", substream="unconventional", country="USA", group="Ra226+", tier="reisolated",
                     product="oil", allocation_variant="default")
        assert float(r["value_central"]) > 0 and float(r["value_low"]) == 0 and as_bool(r["below_detection"]), describe(r)
        assert notes_parts(r["notes"])["cause"] == ["floor_dominance"], r["notes"]

    def test_structural_zero_is_not_flagged_whatever_the_unallocated_flag(self, rows):
        r = rows.one(1960, stage="production", substream="unconventional", country="XXX", group="Ra226+", tier="reisolated",
                     product="gas", allocation_variant="bound_main")
        assert vals(r) == (0.0, 0.0, 0.0) and not as_bool(r["below_detection"]) and "cause" not in r["notes"], describe(r)

    def test_driver_basis_suffix_follows_the_file(self, rows, oracle):
        # horizontal wells 1980-1990 interpolated, oil sands 1967-71 extrapolated, rest silent
        for y in (1980, 1985, 1990, 1991, 2010):
            b = oracle.a("us_wells_drilled_horizontal", y, "USA").basis
            r = rows.find(y, stage="drilling", substream="unconventional", group="U238+", product="oil", allocation_variant="default")[0]
            want = {b} if b in ("interpolated", "extrapolated") else None
            assert notes_parts(r["notes"])["drv"] == want, f"{y}: horizontal driver basis {b!r}, notes {r['notes']!r}"
        for y in (1967, 1971, 1972, 2020):
            b = oracle.a("oil_sands_ore_processed_t", y, "CAN").basis
            r = rows.one(y, stage="oil_sands_mining", group="Th232")
            assert notes_parts(r["notes"])["drv"] == ({b} if b in ("interpolated", "extrapolated") else None), (y, b, r["notes"])
            assert r["basis"] == "modelled"

    def test_allocation_basis_only_on_default_joint_rows(self, rows, oracle):
        r = rows.one(2025, stage="production", substream="conventional", country="XXX", group="K40", tier="reisolated",
                     product="oil", allocation_variant="default")
        want = oracle.alloc("XXX", 2025)["basis"]
        premise("extrapolated" in want, "unit_value_gas XWL is extrapolated in 2025 (A13)")
        assert notes_parts(r["notes"])["alloc"] == want, f"allocation basis {r['notes']!r}, expected {sorted(want)}"
        b = rows.one(2025, stage="production", substream="conventional", country="XXX", group="K40", tier="reisolated",
                     product="oil", allocation_variant="bound_main")
        assert notes_parts(b["notes"])["alloc"] is None
        g = rows.one(2025, stage="processing_transport", country="USA", group="Rn222+", route="air_delivered_gas", product="gas")
        assert notes_parts(g["notes"])["alloc"] is None

    def test_driver_basis_of_2025_rows_is_read_from_the_file(self, rows, oracle):
        """2025 water, gas and flaring drivers: the suffix appears exactly when a driver row is interpolated or extrapolated."""
        for series in ("produced_water_m3", "gas_production_m3", "gas_flared_m3", "oil_sands_ore_processed_t"):
            for c in ("USA", "XWL", "CAN"):
                a = oracle.a(series, 2025, c)
                if a is not None:
                    print(f"2025 {series}/{c}: basis {a.basis}")
        r = rows.one(2025, stage="production", substream="conventional", country="USA", group="K40", tier="reisolated",
                     product="oil", allocation_variant="default")
        want = {x for x in (oracle.a("produced_water_m3", 2025, "USA").basis,) if x in ("interpolated", "extrapolated")}
        assert (notes_parts(r["notes"])["drv"] or set()) == want


# --------------------------------------------------------------------------------------------
# section 4.4 and 4.5: main and radio products
# --------------------------------------------------------------------------------------------
class TestMainRadio:
    def test_premise_main_oil_radio_gas_everywhere(self, oracle):
        bad = []
        for geo in ("USA", "XXX"):
            for y in range(1950, 2026):
                al = oracle.alloc(geo, y)
                if (al["main"], al["radio"]) != ("oil", "gas"):
                    bad.append((geo, y, al["main"], al["radio"]))
        # D71 C1: R3 follows the data. Only USA 1993-94 and 1997-2006 differ (main gas, radio oil); XXX never does.
        premise(not [x for x in bad if x[0] == "XXX"], f"XXX has oil/gas in every year (C1); differs in {bad[:4]}")
        premise({y for g, y, _m, _r in bad if g == "USA"} == {1993, 1994, *range(1997, 2007)},
                f"USA main = gas, radio = oil exactly in 1993-94 and 1997-2006 (C1); found {sorted(y for _g, y, _m, _r in bad)}")

    def test_usa_2003_main_gas_radio_oil_follows_the_data_rule(self, rows, oracle):
        al = oracle.alloc("USA", 2003)
        premise((al["main"], al["radio"]) == ("gas", "oil"), "USA 2003 has gas ahead of oil by value (D71 C1)")
        kw = {"stage": "production", "substream": "conventional", "country": "USA", "group": "K40", "tier": "reisolated"}
        nz = lambda v: [p for p in PRODUCTS if float(rows.one(2003, product=p, allocation_variant=v, **kw)["value_central"]) > 0]
        assert nz("bound_main") == ["gas"] and nz("bound_radio") == ["oil"], (nz("bound_main"), nz("bound_radio"))

    def test_bound_main_all_to_oil_bound_radio_all_to_gas_and_they_differ(self, rows):
        for geo in ("USA", "XXX"):
            for y in (1950, 1990, 2010, 2020, 2025):
                kw = {"stage": "production", "substream": "conventional", "country": geo, "group": "Ra226+", "tier": "reisolated"}
                val = {(p, v): float(rows.one(y, product=p, allocation_variant=v, **kw)["value_central"])
                       for p in PRODUCTS for v in ("default", "bound_main", "bound_radio")}
                tot = sum(val[(p, "default")] for p in PRODUCTS)
                assert val[("oil", "bound_main")] == pytest.approx(tot) and val[("gas", "bound_main")] == 0 == val[("ngl", "bound_main")]
                assert val[("gas", "bound_radio")] == pytest.approx(tot) and val[("oil", "bound_radio")] == 0 == val[("ngl", "bound_radio")]
                assert val[("oil", "bound_main")] != val[("oil", "bound_radio")] and val[("gas", "bound_main")] != val[("gas", "bound_radio")]
                assert 0 < val[("gas", "default")] < tot, "the toggle must bracket the default for gas (0 / 17-35 % / 100 %)"

    def test_radio_product_helper_when_present(self, og_mod):
        f = getattr(og_mod, "_radio_product", None)
        if f is None:
            pytest.fail("pipeline.streams.oil_gas._radio_product is named in OIL_GAS_SPEC 4.5 but is missing")
        q = {"oil": 100.0, "gas": 300.0, "ngl": 20.0}
        v = {"oil": 10.0, "gas": 2.0, "ngl": 20.0}      # values 1000 / 600 / 400
        assert f("USA", 2010, q, v) == "gas"
        v2 = {"oil": 10.0, "gas": 0.5, "ngl": 20.0}      # 1000 / 150 / 400: NGL outranks gas
        assert f("USA", 2010, q, v2) == "ngl"
        v3 = {"oil": 1.0, "gas": 2.0, "ngl": 20.0}       # 100 / 600 / 400: gas is main, so the radio product is NGL...
        assert f("USA", 2010, q, v3) == "ngl"
        v4 = {"oil": 4.0, "gas": 5.0, "ngl": 1.0}        # 400 / 1500 / 20: gas is main, oil second
        assert f("USA", 2010, q, v4) == "oil"

    def test_correlated_difference_helper_when_present(self, og_mod):
        from pipeline.lib.bounds import Bounds
        f = getattr(og_mod, "_correlated_difference", None)
        if f is None:
            pytest.fail("pipeline.streams.oil_gas._correlated_difference is named in OIL_GAS_SPEC 3.4 but is missing")
        a, b = Bounds(8.0, 10.0, 13.0), Bounds(1.0, 2.0, 4.0)
        r = f(a, b)
        assert (r.low, r.central, r.high) == (pytest.approx(min(8.0 - 1.0, 8.0)), pytest.approx(8.0), pytest.approx(max(13.0 - 4.0, 8.0)))
        assert not r.nd_floored
        c = f(Bounds(1.0, 5.0, 9.0), Bounds(2.0, 4.0, 6.0))      # raw low -1: clipped to 0, flag set
        assert c.low == 0 and c.nd_floored and c.central == pytest.approx(1.0) and c.high == pytest.approx(3.0)
        d = f(Bounds(1.0, 3.0, 5.0), Bounds(2.0, 4.0, 6.0))      # negative central: set to 0
        assert d.central == 0 and d.low == 0


# --------------------------------------------------------------------------------------------
# 8: log
# --------------------------------------------------------------------------------------------
class TestLog:
    def test_entry_shape_and_kinds(self, log):
        assert log, "the committed build has at least no_driver, no_unit_value and lib_warning entries"
        for e in log:
            assert {"kind", "year", "country", "group", "detail"} <= set(e), f"log entry keys: {sorted(e)}"
            assert e["kind"] in LOG_KINDS, f"unknown log kind {e['kind']!r}"

    def test_no_factor_no_family_and_cap_absent_on_the_committed_build(self, log):
        for k in ("no_factor", "no_family", "cap_applied"):
            assert not log_entries(log, k), f"{k} entries in the committed log (9(b)): {log_entries(log, k)[:2]}"

    def test_runs_are_well_formed(self, log):
        for e in log:
            if e["kind"] in ("no_factor", "no_driver", "no_unit_value"):
                run = run_of(e)
                assert run, f"detail must start 'first-last (n years)': {e}"
                assert run[1] - run[0] + 1 == run[2], f"run length: {e['detail']}"
                assert e["year"] == run[0], f"year must be the first year of the run: {e}"

    def test_no_unit_value_is_the_1949_vertical_well_row_only(self, log, expected):
        es = log_entries(log, "no_unit_value")
        assert len(es) == 1, f"expected one aggregated no_unit_value entry, got {es}"
        assert es[0]["year"] == 1949 and str(es[0]["detail"]).startswith("1949-1949 (1 year"), es[0]
        assert expected.no_unit_value == [("drilling", 1949)]

    def test_pre1950_no_driver_runs_cover_water_flaring_oil_sands(self, log):
        nd = log_entries(log, "no_driver")
        assert covered([e for e in nd if e["country"] == "CAN"]) == set(range(1900, 1967)), \
            "oil sands (CAN) has no driver 1900-1966"
        assert covered([e for e in nd if e["country"] == "XXX"]) >= set(range(1900, 1950)), \
            "produced water and flaring (XXX) have no driver before 1950"
        assert covered([e for e in nd if e["country"] == "USA"]) >= set(range(1900, 1950)), "USA produced water 1900-1949"
        assert covered([e for e in nd if e["country"] == "USA"]) <= set(range(1900, 1980)), \
            "USA no_driver years run to 1979 at most (horizontal wells start 1980)"

    def test_no_driver_entries_leave_the_driver_years_alone(self, log):
        us = covered([e for e in log_entries(log, "no_driver") if e["country"] == "USA"])
        assert not us & set(range(1980, 2026)), "USA has drivers 1980-2025 for every series"

    def test_negative_residual_matches_the_oracle(self, log, expected):
        got = Counter(e["year"] for e in log_entries(log, "negative_residual"))
        want = Counter(y for y, _lab, _m in expected.neg)
        assert got == want, f"negative_residual entries per year {dict(got)}, oracle {dict(want)}"

    def test_single_lib_warning_with_count_and_type(self, log):
        w = log_entries(log, "lib_warning")
        assert len(w) == 1, f"exactly one lib_warning entry per build (3.7), got {len(w)}"
        assert w[0]["year"] in (None, "", 0) and w[0]["country"] in (None, ""), f"year and country empty (A9): {w[0]}"
        m = re.search(r"\d+", str(w[0]["detail"]))
        assert m and int(m.group()) >= 1, f"detail must carry the count: {w[0]['detail']!r}"
        assert re.search(r"[A-Za-z]{4,}", str(w[0]["detail"])), "detail must name the message type"


# --------------------------------------------------------------------------------------------
# (e) benchmarks (D51): two years, 2010 and 2020, x/x_ref within a factor of 3
# --------------------------------------------------------------------------------------------
GWA_TWH = 8.766


def check(name, x, ref, known_miss=False, reason=""):
    ratio = x / ref if ref else float("inf")
    ok = 1 / 3 <= ratio <= 3
    print(f"[benchmark] {name}: stream {x:.5g}, reference {ref:.5g}, ratio {ratio:.3g}")
    if not ok and known_miss:
        pytest.xfail(f"documented known miss (OIL_GAS_SPEC 9(e)): {name}: stream {x:.4g}, reference {ref:.4g}, "
                     f"ratio {ratio:.3g}. {reason}")
    assert ok, f"{name}: stream {x:.4g}, reference {ref:.4g}, ratio {ratio:.3g} outside a factor of 3"


@pytest.fixture(scope="module")
def elec():
    df = pd.read_csv(ROOT / "data" / "activity" / "electricity_generation.csv", dtype=str, keep_default_na=False)
    df = df[df.country == "XWL"]
    return {(r["series"], int(r["year"])): float(r["value_central"]) for r in df.to_dict("records")}


@pytest.fixture(scope="module")
def unscear():
    df = pd.read_csv(ROOT / "research" / "unscear_extraction.csv", dtype=str, keep_default_na=False)
    out = {}
    for r in df.to_dict("records"):
        try:
            out[r["item_id"]] = float(r["value"])
        except ValueError:
            pass
    return out


def tbq_rows(rows_obj, y, code):
    return sum(float(r["value_central"]) for r in rows_obj.by_year.get(y, []) if _family_of(r) == code) / 1e12


class TestBenchmarks:
    @pytest.mark.parametrize("year", [2010, 2020])
    def test_b1_gas_radon_per_gwa_within_3_of_at_least_one_reference(self, rows, oracle, elec, unscear, year):
        share = oracle.a("gas_power_share", year, "XWL").b.central
        gwa = elec[("elec_gen_gas", year)] / GWA_TWH
        x = tbq_rows(rows, year, "GD") * share / gwa
        refs = {"Johnson 1973 direct": 1.38, "bottom-up chain": 0.42, "Dixon 2001": 0.50}
        ratios = {k: x / v for k, v in refs.items()}
        print(f"[benchmark] B1 {year}: stream {x:.4g} TBq/GW.a; ratios {ratios}")
        assert any(1 / 3 <= r <= 3 for r in ratios.values()), f"B1 {year}: {x:.4g} TBq/GW.a is outside x3 of every reference {refs}"
        assert 0.05 <= x <= 8.7, f"B1 {year}: {x:.4g} outside the Gesell 1975 range 0.05-8.7 TBq/GW.a"

    @pytest.mark.parametrize("year", [2010, 2020])
    def test_b1_annex_b_is_reported_not_required(self, rows, oracle, elec, unscear, year):
        share = oracle.a("gas_power_share", year, "XWL").b.central
        x = tbq_rows(rows, year, "GD") * share / (elec[("elec_gen_gas", year)] / GWA_TWH)
        print(f"[reported] B1 {year} vs Annex B U0240 {unscear['U0240']}: ratio {x / unscear['U0240']:.3g} (near-circular)")

    @pytest.mark.parametrize("year", [2010, 2020])
    def test_b2_oil_radon_per_gwa_within_3_of_each(self, rows, oracle, elec, unscear, year):
        share = oracle.a("oil_power_share", year, "XWL").b.central
        gwa = elec[("elec_gen_oil", year)] / GWA_TWH
        x = tbq_rows(rows, year, "OR") * share / gwa
        check(f"B2 {year} vs Annex B U0241", x, unscear["U0241"])
        check(f"B2 {year} vs Bell et al. mean 0.7 Bq/kg", x, 0.0017)

    def _b3(self, oracle, expected):
        y = 1990
        V = oracle.a("produced_water_m3", y, "USA").b.central
        u = fc(oracle, oracle.select(y, "USA", stage="production", substream="", group="", tier="", route="", residue_type="",
                                      driver_series="produced_water_unconv_share")["factor_id"])[1]
        sig = {r: fc(oracle, oracle.select(y, "XWL", stage="production", substream="", group="Ra226+", tier="", route="",
                                            residue_type=r)["factor_id"])[1] for r in ("og_scale", "og_sludge")}
        out = {}
        for g in ("Ra226+", "Ra228+"):
            cc = fc(oracle, oracle.select(y, "USA", stage="production", substream="conventional", group=g, tier="", route="",
                                           residue_type="")["factor_id"])[1]
            cu = fc(oracle, oracle.select(y, "USA", stage="production", substream="unconventional", group=g, tier="", route="",
                                           residue_type="")["factor_id"])[1]
            out[g] = V * ((1 - u) * cc + u * cu) * (sig["og_scale"] + sig["og_sludge"]) / 1e12
        return out

    def test_b3_us_solids_radium_about_1990(self, oracle, expected, rows):
        out = self._b3(oracle, expected)
        parts = sum(expected.parts[("USA", 1990, s, "S", g, r)].central for s in SUBSTREAMS for g in ("Ra226+", "Ra228+")
                    for r in ("og_scale", "og_sludge")) / 1e12
        assert math.isclose(parts, out["Ra226+"] + out["Ra228+"], rel_tol=1e-9), "9(c)2 identity: formula vs components"
        ret = sum(float(r["value_central"]) for r in rows.find(1990, stage="abandonment_scrap", country="USA", group="Ra226+",
                                                                 allocation_variant="default"))
        sret = sum(expected.parts[("USA", 1990, s, "Sret", "Ra226+", "og_scale")].central for s in SUBSTREAMS)
        assert math.isclose(ret, sret, rel_tol=1e-3), "rows tie to the components through the abandonment rows"
        total = out["Ra226+"] + out["Ra228+"]
        r1, r2 = total / 3.22, total / 1.07
        print(f"[benchmark] B3 1990: Ra-226 {out['Ra226+']:.3g}, Ra-228 {out['Ra228+']:.3g}, total {total:.3g} TBq/a; ratios {r1:.3g}, {r2:.3g}")
        assert any(1 / 3 <= r <= 3 for r in (r1, r2)), f"B3: total {total:.3g} TBq/a outside x3 of both EPA 1991 (3.22) and EPA 1993 (1.07)"

    def test_b3_known_miss_ra228_to_ra226_ratio_in_solids(self, oracle, expected):
        out = self._b3(oracle, expected)
        ratio = out["Ra228+"] / out["Ra226+"]
        check("B3 Ra-228:Ra-226 in US solids vs EPA 1991 (0.35)", ratio, 0.35, known_miss=True,
              reason="papers_round3 O3: the stream carries the water ratio; EPA's solids ratio is an assumption")

    @pytest.mark.parametrize("year", [2010, 2020])
    def test_b4_rest_of_world_effective_radium_concentration(self, expected, oracle, year):
        tot = sum(expected.parts[("XXX", year, s, "A", "Ra226+")].central for s in SUBSTREAMS)
        V = cdiff(oracle.a("produced_water_m3", year, "XWL").b, oracle.a("produced_water_m3", year, "USA").b)[0].central
        conc = tot / (V * 1000.0)       # Bq per litre
        print(f"[benchmark] B4 {year}: ROW effective Ra-226 {conc:.3g} Bq/L")
        assert 3.5 <= conc <= 10.0, f"B4 {year}: {conc:.3g} Bq/L outside the Norway (3.5) to RP 135 (10) range"

    @pytest.mark.parametrize("year", [2010, 2020])
    def test_b4_liberated_radium_between_ospar_and_100_times(self, rows, expected, year):
        water = sum(expected.parts[("XXX", year, s, "W", "Ra226+", "liberated")].central for s in SUBSTREAMS) / 1e12
        merged = sum(float(r["value_central"]) for r in rows.find(
            year, stage="production", country="XXX", group="Ra226+", tier="liberated", allocation_variant="default")) / 1e12
        print(f"[benchmark] B4 {year}: ROW liberated Ra-226 water term {water:.3g} TBq/a (merged row {merged:.3g})")
        assert 0.73 <= water <= 100 * 1.1, f"B4 {year}: liberated water Ra-226 {water:.3g} TBq/a outside [0.73, 110]"
        assert merged >= water * (1 - 1e-9)

    @pytest.mark.parametrize("year", [2010, 2020])
    def test_b5_flaring_identity_and_series(self, rows, oracle, year):
        f = fc(oracle, "oil_gas:0111")[1]
        x = sum(float(r["value_central"]) for r in rows.by_year[year] if _family_of(r) == "FL") / f
        xwl = oracle.a("gas_flared_m3", year, "XWL").b.central
        assert math.isclose(x, xwl, rel_tol=1e-6 if year < 2012 else 1e-5), f"B5 {year}: rows/factor {x:.8g} vs series {xwl:.8g} (A7)"
        bcm = xwl / 1e9
        if year == 2010:
            assert 132.3 / 1.1 < bcm < 132.3 * 1.1 and 1 / 1.1 <= bcm / 134.0 <= 1.1, f"2010 flared volume {bcm:.2f} bcm vs 134 (World Bank)"
            eia = oracle.a("gas_flared_reported_m3", 2010, "XWL").b.central / 1e9
            assert 1 / 1.1 <= bcm / eia <= 1.1, f"2010 flared volume {bcm:.2f} bcm vs EIA-reported {eia:.2f} bcm"
        else:
            assert 1 / 1.1 <= bcm / 149.5 <= 1.1, f"2020 flared volume {bcm:.2f} bcm vs GGFR 149.5"

    def test_b6_oil_sands_2024_inside_the_aer_range(self, rows):
        t = sum(float(r["value_central"]) for r in rows.find(2024, stage="oil_sands_mining", group="Th232")) / 1e12
        print(f"[benchmark] B6 2024: Th-232 {t:.3g} TBq/a")
        assert 2.2 <= t <= 20.6, f"B6: {t:.3g} TBq/a outside the AER-based range 2.2-20.6 TBq/a (consistency check, not independent)"

    def test_b7_drilling_is_reported_only(self, rows):
        dr = sum(float(r["value_central"]) for r in rows.find(2010, stage="drilling", group="Ra226+", allocation_variant="default")) / 1e12
        w = sum(float(r["value_central"]) for r in rows.find(2010, stage="production", country="USA", group="Ra226+",
                                                               tier=("reisolated",), allocation_variant="default")) / 1e12
        print(f"[reported] B7 2010: cuttings Ra-226 {dr:.3g} TBq/a; USA re-isolated water Ra-226 {w:.3g} TBq/a")
        assert dr > 0 and w > 0


# --------------------------------------------------------------------------------------------
# (f) hand-computed cases: plain central-value arithmetic from the files, no oracle structure
# --------------------------------------------------------------------------------------------
class TestHandComputed:
    def _ct(self, oracle, series, y, c):
        return oracle.a(series, y, c).b.central

    def _need(self, oracle, y, region, fid, **kw):
        sel = oracle.select(y, region, **kw)["factor_id"]
        premise(sel == fid, f"the registry row selected for {kw} in {y}/{region} is {sel}, the hand case uses {fid}")
        return fc(oracle, fid)[1]

    def _row_sum(self, rows, y, **kw):
        return sum(float(r["value_central"]) for r in rows.find(y, allocation_variant="default", **kw))

    def test_usa_2010_conventional_ra226_liberated_water_term(self, oracle, expected):
        y = 2010
        u = self._need(oracle, y, "USA", "oil_gas:0012", stage="production", substream="", group="", tier="", route="",
                       residue_type="", driver_series="produced_water_unconv_share")
        c = self._need(oracle, y, "USA", "oil_gas:0002", stage="production", substream="conventional", group="Ra226+", tier="", route="", residue_type="")
        f = self._need(oracle, y, "USA", "oil_gas:0033", stage="production", substream="", group="", tier="liberated",
                       route="water_produced_discharge", residue_type="", driver_series="produced_water_m3")
        hand = self._ct(oracle, "produced_water_m3", y, "USA") * (1 - u) * c * f
        assert math.isclose(expected.parts[("USA", y, "conventional", "W", "Ra226+", "liberated")].central, hand, rel_tol=1e-12)

    def test_usa_2010_merged_liberated_and_impounded_sludge_rows(self, rows, oracle):
        y = 2010
        V = self._ct(oracle, "produced_water_m3", y, "USA")
        u, c = fc(oracle, "oil_gas:0012")[1], fc(oracle, "oil_gas:0002")[1]
        A = V * (1 - u) * c
        f_lib, f_imp = fc(oracle, "oil_gas:0033")[1], fc(oracle, "oil_gas:0032")[1]
        s_scale, s_sludge = fc(oracle, "oil_gas:0047")[1], fc(oracle, "oil_gas:0048")[1]
        phi = fc(oracle, "oil_gas:0078")[1]
        rho_sc_lib, rho_sl_lib, rho_sl_imp = (fc(oracle, i)[1] for i in ("oil_gas:0061", "oil_gas:0070", "oil_gas:0068"))
        lib = A * (f_lib + s_scale * (1 - phi) * rho_sc_lib + s_sludge * rho_sl_lib)
        imp = A * (f_imp + s_sludge * rho_sl_imp)
        got_lib = self._row_sum(rows, y, stage="production", substream="conventional", country="USA", group="Ra226+", tier="liberated")
        got_imp = self._row_sum(rows, y, stage="production", substream="conventional", country="USA", group="Ra226+",
                                tier="impounded", residue_type="og_sludge")
        assert math.isclose(got_lib, lib, rel_tol=1e-9), f"merged liberated row {got_lib:.6g}, hand {lib:.6g}"
        assert math.isclose(got_imp, imp, rel_tol=1e-9), f"merged impounded sludge row {got_imp:.6g}, hand {imp:.6g}"

    def test_xxx_2010_unconventional_ra228_reisolated(self, rows, oracle):
        y = 2010
        V = self._ct(oracle, "produced_water_m3", y, "XWL") - self._ct(oracle, "produced_water_m3", y, "USA")
        u, c, f = fc(oracle, "oil_gas:0017")[1], fc(oracle, "oil_gas:0006")[1], fc(oracle, "oil_gas:0043")[1]
        got = self._row_sum(rows, y, stage="production", substream="unconventional", country="XXX", group="Ra228+", tier="reisolated")
        assert math.isclose(got, V * u * c * f, rel_tol=1e-9)

    def test_xxx_1960_unconventional_central_zero_flagged(self, rows):
        r = rows.one(1960, stage="production", substream="unconventional", country="XXX", group="Ra228+", tier="liberated",
                     product="oil", allocation_variant="default")
        assert vals(r)[:2] == (0.0, 0.0) and vals(r)[2] > 0 and as_bool(r["below_detection"])
        assert "zero_central_factor" in notes_parts(r["notes"])["cause"]

    def test_usa_1960_unconventional_floor_dominance(self, rows, oracle):
        y = 1960
        V = self._ct(oracle, "produced_water_m3", y, "USA")
        u, c, f = fc(oracle, "oil_gas:0011")[1], fc(oracle, "oil_gas:0003")[1], fc(oracle, "oil_gas:0019")[1]
        got = self._row_sum(rows, y, stage="production", substream="unconventional", country="USA", group="Ra226+", tier="reisolated")
        assert math.isclose(got, V * u * c * f, rel_tol=1e-9)
        r = rows.one(y, stage="production", substream="unconventional", country="USA", group="Ra226+", tier="reisolated",
                     product="oil", allocation_variant="default")
        assert as_bool(r["below_detection"]) and notes_parts(r["notes"])["cause"] == ["floor_dominance"]

    def test_pb210_solids_row_is_005_of_ra226_solids(self, rows, oracle):
        pi = fc(oracle, "oil_gas:0051")[1]
        for y in (1955, 1970, 1990, 2010):
            a = self._row_sum(rows, y, stage="abandonment_scrap", substream="conventional", country="USA", group="Ra226+", tier="impounded")
            b = self._row_sum(rows, y, stage="abandonment_scrap", substream="conventional", country="USA", group="Pb210+", tier="impounded")
            assert math.isclose(b, pi * a, rel_tol=1e-9), f"{y}: Pb-210 retained scale {b:.6g} vs pi x Ra-226 {pi * a:.6g}"

    @pytest.mark.parametrize("y,imp,disp", [(1955, "oil_gas:0079", "oil_gas:0080"), (1970, "oil_gas:0081", "oil_gas:0082"),
                                            (1990, "oil_gas:0083", "oil_gas:0084")])
    def test_abandonment_rows_by_creation_era(self, rows, oracle, y, imp, disp):
        V = self._ct(oracle, "produced_water_m3", y, "USA")
        u = fc(oracle, oracle.select(y, "USA", stage="production", substream="", group="", tier="", route="", residue_type="",
                                      driver_series="produced_water_unconv_share")["factor_id"])[1]
        c = fc(oracle, oracle.select(y, "USA", stage="production", substream="conventional", group="Ra226+", tier="", route="", residue_type="")["factor_id"])[1]
        s = fc(oracle, "oil_gas:0047")[1]
        phi = fc(oracle, "oil_gas:0078")[1]
        ret = V * (1 - u) * c * s * phi
        a = self._row_sum(rows, y, stage="abandonment_scrap", substream="conventional", country="USA", group="Ra226+", tier="impounded")
        b = self._row_sum(rows, y, stage="abandonment_scrap", substream="conventional", country="USA", group="Ra226+", tier="dispersed")
        assert math.isclose(a, ret * fc(oracle, imp)[1], rel_tol=1e-9) and math.isclose(b, ret * fc(oracle, disp)[1], rel_tol=1e-9)
        assert rows.one(y, stage="abandonment_scrap", substream="conventional", country="USA", group="Ra226+", tier="dispersed",
                        product="oil", allocation_variant="default")["residue_type"] == "og_scaled_scrap"

    @pytest.mark.parametrize("geo", ["USA", "XXX"])
    def test_nine_allocation_rows_2010(self, rows, oracle, geo):
        y = 2010
        if geo == "USA":
            q = {p: self._ct(oracle, s, y, "USA") for p, s in (("oil", "oil_production_m3"), ("gas", "gas_production_m3"), ("ngl", "ngl_production_m3"))}
            v = {"oil": self._ct(oracle, "unit_value_oil_usd_per_m3", y, "USA"), "gas": self._ct(oracle, "unit_value_gas_usd_per_m3", y, "USA"),
                 "ngl": self._ct(oracle, "unit_value_ngl_usd_per_m3", y, "XWL")}
        else:
            q = {p: self._ct(oracle, s, y, "XWL") - self._ct(oracle, s, y, "USA") for p, s in (
                ("oil", "oil_production_m3"), ("gas", "gas_production_m3"), ("ngl", "ngl_production_m3"))}
            v = {"oil": self._ct(oracle, "unit_value_oil_usd_per_m3", y, "XWL"), "gas": self._ct(oracle, "unit_value_gas_usd_per_m3", y, "XWL"),
                 "ngl": self._ct(oracle, "unit_value_ngl_usd_per_m3", y, "XWL")}
        val = {p: q[p] * v[p] for p in PRODUCTS}
        tot = sum(val.values())
        kw = {"stage": "production", "substream": "conventional", "country": geo, "group": "K40", "tier": "reisolated"}
        rs = {(p, vv): rows.one(y, product=p, allocation_variant=vv, **kw) for p in PRODUCTS for vv in ("default", "bound_main", "bound_radio")}
        unall = sum(float(rs[(p, "default")]["value_central"]) for p in PRODUCTS)
        for p in PRODUCTS:
            assert math.isclose(float(rs[(p, "default")]["value_central"]), unall * val[p] / tot, rel_tol=1e-9), (geo, p)
        order = sorted(PRODUCTS, key=lambda p: (-val[p], PRODUCTS.index(p)))
        assert [float(rs[(p, "bound_main")]["value_central"]) > 0 for p in PRODUCTS] == [p == order[0] for p in PRODUCTS]
        assert [float(rs[(p, "bound_radio")]["value_central"]) > 0 for p in PRODUCTS] == [p == order[1] for p in PRODUCTS]
        for p in PRODUCTS:
            for vv, tok in (("default", "alloc:value"), ("bound_main", "alloc:main"), ("bound_radio", "alloc:radio")):
                assert ids(rs[(p, vv)]["allocation_rule"]) == [tok]
            assert all(not rs[(p, vv)]["technology"] for vv in ("default", "bound_main", "bound_radio"))

    def test_gas_family_usa_2010(self, rows, oracle):
        y = 2010
        P = self._ct(oracle, "gas_production_m3", y, "USA")
        for fam, fid, kw in (("GD", "oil_gas:0074", {"route": "air_delivered_gas", "product": "gas", "group": "Rn222+"}),
                             ("GN", "oil_gas:0110", {"route": "air_delivered_gas", "product": "ngl", "group": "Rn222+"}),
                             ("GV", "oil_gas:0075", {"route": "air_vented_gas", "product": "gas", "group": "Rn222+"}),
                             ("GP", "oil_gas:0076", {"product": "gas", "group": "Pb210+", "tier": "impounded", "residue_type": "og_processing_residue"})):
            r = rows.one(y, stage="processing_transport", country="USA", substream="all", **kw)
            assert math.isclose(float(r["value_central"]), P * fc(oracle, fid)[1], rel_tol=1e-12), fam
            assert ids(r["factor_ids"]) == [fid] and r["allocation_variant"] == "default" and ids(r["allocation_rule"]) == ["none"]

    def test_rest_of_world_gd_row_2010(self, rows, oracle):
        y = 2010
        res = self._ct(oracle, "gas_production_m3", y, "XWL") - sum(self._ct(oracle, "gas_production_m3", y, c)
                                                                     for c in oracle.countries("gas_production_m3", y))
        r = rows.one(y, stage="processing_transport", country="XXX", group="Rn222+", route="air_delivered_gas", product="gas")
        assert math.isclose(float(r["value_central"]), res * fc(oracle, "oil_gas:0074")[1], rel_tol=1e-9)
        assert as_bool(r["below_detection"]) and notes_parts(r["notes"])["cause"] == ["clipped_difference"] and REST_GAS in r["notes"]

    def test_oil_radon_usa_2010(self, rows, oracle):
        r = rows.one(2010, stage="processing_transport", country="USA", group="Rn222+", route="air_stack", product="oil")
        assert math.isclose(float(r["value_central"]), self._ct(oracle, "oil_production_t", 2010, "USA") * fc(oracle, "oil_gas:0077")[1], rel_tol=1e-12)
        assert r["substream"] == "all" and r["tier"] == "liberated"

    def test_flaring_2011_world_row_and_2012_country_row(self, rows, oracle):
        f = fc(oracle, "oil_gas:0111")[1]
        r = rows.one(2011, stage="production", group="Rn222+", route="air_stack")
        assert r["country"] == "XXX" and WORLD_FLARE in r["notes"] and r["product"] == "oil" and r["substream"] == "all"
        assert math.isclose(float(r["value_central"]), self._ct(oracle, "gas_flared_m3", 2011, "XWL") * f, rel_tol=1e-12)
        c = rows.one(2012, stage="production", group="Rn222+", route="air_stack", country="RUS")
        assert math.isclose(float(c["value_central"]), self._ct(oracle, "gas_flared_m3", 2012, "RUS") * f, rel_tol=1e-12)
        assert not rows.find(2012, stage="production", group="Rn222+", route="air_stack", country="XXX"), \
            "2012 world and listed countries agree to 7e-7: the residual is within the 1e-5 tolerance (3.4)"

    def test_drilling_vertical_and_horizontal_u238_2010_share_the_same_allocation(self, rows, oracle):
        y = 2010
        v = rows.one(y, stage="drilling", substream="conventional", group="U238+", product="oil", allocation_variant="default")
        h = rows.one(y, stage="drilling", substream="unconventional", group="U238+", product="oil", allocation_variant="default")
        nv = self._ct(oracle, "us_wells_drilled_vertical", y, "USA") * fc(oracle, "oil_gas:0088")[1]
        nh = self._ct(oracle, "us_wells_drilled_horizontal", y, "USA") * fc(oracle, "oil_gas:0099")[1]
        sh = oracle.alloc("USA", y)["shares"]["default"]["oil"]
        assert math.isclose(float(v["value_central"]), nv * sh, rel_tol=1e-9) and math.isclose(float(h["value_central"]), nh * sh, rel_tol=1e-9)
        assert v["country"] == h["country"] == "USA" and v["residue_type"] == "og_drill_cuttings" and v["tier"] == "impounded"

    def test_oil_sands_2024(self, rows, oracle):
        r = rows.one(2024, stage="oil_sands_mining", group="Th232")
        assert math.isclose(float(r["value_central"]), self._ct(oracle, "oil_sands_ore_processed_t", 2024, "CAN") * fc(oracle, "oil_gas:0085")[1], rel_tol=1e-12)
        assert (r["substream"], r["product"], r["country"], r["residue_type"], r["allocation_variant"]) == (
            "oil_sands", "bitumen", "CAN", "oil_sands_tailings", "default")

    def test_horizontal_drilling_starts_in_1980(self, rows):
        assert not rows.find(1979, stage="drilling", substream="unconventional")
        assert rows.find(1980, stage="drilling", substream="unconventional")

    def test_1949_vertical_drilling_omitted_and_logged(self, rows, pre_rows, log):
        assert not rows.find(1949) and not pre_rows.find(1949, stage="drilling"), "1949 drilling is omitted (3.8)"
        assert len(log_entries(log, "no_unit_value")) == 1


# --------------------------------------------------------------------------------------------
# (h) pre-1950 file
# --------------------------------------------------------------------------------------------
class TestPre1950:
    def test_rows_match_oracle(self, comparison_pre, expected):
        assert expected.pre, "oracle expects pre-1950 gas and oil radon rows"
        assert not comparison_pre, "pre-1950 rows differ from the oracle: " + show([m for v in comparison_pre.values() for m in v])

    def test_shape(self, pre_rows):
        assert {_family_of(r) for r in pre_rows.rows} == {"GD", "GN", "GV", "GP", "OR"}
        assert {r["quantity"] for r in pre_rows.rows} == {"flow"}
        yrs = {int(r["year"]) for r in pre_rows.rows}
        assert min(yrs) == 1900 and max(yrs) == 1949
        assert not [r for r in pre_rows.rows if r["tier"].startswith("memo")]
        assert {r["allocation_variant"] for r in pre_rows.rows} == {"default"}
        assert {r["product"] for r in pre_rows.rows} <= {"gas", "ngl", "oil"}

    def test_values_are_driver_times_factor(self, pre_rows, oracle):
        for y in (1900, 1930, 1949):
            P = oracle.a("gas_production_m3", y, "USA").b.central
            r = pre_rows.one(y, stage="processing_transport", country="USA", group="Rn222+", route="air_delivered_gas", product="gas")
            assert math.isclose(float(r["value_central"]), P * fc(oracle, "oil_gas:0074")[1], rel_tol=1e-12)
            o = oracle.a("oil_production_t", y, "USA").b.central
            r = pre_rows.one(y, stage="processing_transport", country="USA", group="Rn222+", route="air_stack", product="oil")
            assert math.isclose(float(r["value_central"]), o * fc(oracle, "oil_gas:0077")[1], rel_tol=1e-12)

    def test_no_joint_family_or_flaring_row(self, pre_rows):
        assert not [r for r in pre_rows.rows if r["stage"] in ("production", "abandonment_scrap", "drilling", "oil_sands_mining")]

    def test_each_row_passes_master_schema_with_relaxed_years(self, written):
        from jsonschema import Draft7Validator

        from pipeline.lib.io import read_table

        schema = json.loads((ROOT / "schema" / "master.json").read_text(encoding="utf-8"))
        schema["properties"]["year"]["minimum"] = 1900
        schema["properties"]["year"]["maximum"] = 1949
        v = Draft7Validator(schema)
        recs = read_table(written[1])
        assert recs
        for rec in recs:
            if isinstance(rec["allocation_rule"], list):
                rec["allocation_rule"] = ";".join(rec["allocation_rule"])
            errs = list(v.iter_errors(rec))
            assert not errs, f"pre-1950 row {rec['year']} {rec['group']} fails master.json: {errs[0].message}"


# --------------------------------------------------------------------------------------------
# (i) premise assertions
# --------------------------------------------------------------------------------------------
GROUPS4 = ("Ra226+", "Ra228+", "K40", "Pb210+")


def _calls(oracle: Oracle):
    base = {"stage": "production", "substream": "", "group": "", "tier": "", "route": "", "residue_type": ""}
    out = []

    def add(name, kw, regions, y0, y1, strict=False):
        out.append((name, kw, regions, y0, y1, strict))

    for g in GROUPS4:
        add(f"C conv {g}", {**base, "substream": "conventional", "group": g}, ("USA", "XWL"), 1950, 2025)
        add(f"C' unc {g}", {**base, "substream": "unconventional", "group": g}, ("USA", "XWL"), 1950, 2025)
    add("U", {**base, "driver_series": "produced_water_unconv_share"}, ("USA", "XWL"), 1950, 2025, True)
    for t, route, res in (("reisolated", "", "og_produced_water"), ("impounded", "", "og_sludge"),
                          ("liberated", "water_produced_discharge", ""), ("dispersed", "", "og_produced_water")):
        add(f"T {t}", {**base, "tier": t, "route": route, "residue_type": res, "driver_series": "produced_water_m3"},
            ("USA", "XWL"), 1950, 2025, True)
    for g in ("Ra226+", "Ra228+"):
        for r in ("og_scale", "og_sludge"):
            add(f"Sigma {g} {r}", {**base, "group": g, "residue_type": r}, ("XWL",), 1950, 2025)
    for r in ("og_scale", "og_sludge"):
        add(f"Pi {r}", {**base, "group": "Pb210+", "residue_type": r}, ("XWL",), 1950, 2025)
        for t, route in (("impounded", ""), ("dispersed", ""), ("liberated", "water_produced_discharge")):
            add(f"R {r} {t}", {**base, "tier": t, "route": route, "residue_type": r, "driver_series": ""}, ("XWL",), 1950, 2025)
    ab = {"stage": "abandonment_scrap", "substream": "", "group": "", "tier": "", "route": "", "residue_type": ""}
    add("Phi", {**ab, "residue_type": "og_scale", "driver_series": ""}, ("XWL",), 1950, 2025)
    add("A imp", {**ab, "tier": "impounded", "residue_type": "og_scale"}, ("XWL",), 1950, 2025)
    add("A disp", {**ab, "tier": "dispersed", "residue_type": "og_scaled_scrap"}, ("XWL",), 1950, 2025)
    pt = {"stage": "processing_transport", "substream": "all", "group": "Rn222+", "tier": "liberated", "route": "air_delivered_gas", "residue_type": ""}
    add("GD", pt, ("USA", "XWL"), 1900, 2025)
    add("GN", {**pt, "residue_type": "og_processing_residue"}, ("USA", "XWL"), 1900, 2025)
    add("GV", {**pt, "route": "air_vented_gas"}, ("USA", "XWL"), 1900, 2025)
    add("GP", {**pt, "group": "Pb210+", "tier": "impounded", "route": "", "residue_type": "og_processing_residue"}, ("USA", "XWL"), 1900, 2025)
    add("OR", {**pt, "route": "air_stack"}, ("USA", "XWL"), 1900, 2025)
    add("FL", {"stage": "production", "substream": "all", "group": "Rn222+", "tier": "liberated", "route": "air_stack", "residue_type": "",
                   "driver_series": "gas_flared_m3"}, ("XWL",), 1950, 2025)
    for g in ("Th232", "Ra228+", "Th228+"):
        add(f"OS {g}", {"stage": "oil_sands_mining", "substream": "", "group": g, "tier": "impounded", "route": "", "residue_type": "oil_sands_tailings"},
            ("CAN",), 1967, 2025, True)
    dg = lambda sub: oracle.groups_of(stage="drilling", substream=sub)
    for sub, y0 in (("conventional", 1949), ("unconventional", 1980)):
        for g in dg(sub):
            add(f"D {sub} {g}", {"stage": "drilling", "substream": sub, "group": g, "tier": "impounded", "route": "", "residue_type": "og_drill_cuttings"},
                ("USA",), y0, 2025, True)
    return out


class TestPremises:
    def test_factor_file_columns_and_ids(self, oracle):
        with open(ROOT / "data" / "factors" / "oil_gas.csv", newline="", encoding="utf-8") as fh:
            header = next(csv.reader(fh))
        premise("stage" in header and "substream" in header and header.index("substream") == header.index("stage") + 1,
                "the registry carries a 'substream' column directly after 'stage'")
        want = [f"oil_gas:{i:04d}" for i in range(1, 112)]
        premise(list(oracle.fid) == want, "the registry holds exactly the ids oil_gas:0001-0111")

    def test_substream_cells(self, oracle):
        rng = lambda a, b: {f"oil_gas:{i:04d}" for i in range(a, b + 1)}
        conv = {f"oil_gas:{i:04d}" for i in (1, 2, 4, 5, 7, 9)} | rng(88, 98)
        unc = {f"oil_gas:{i:04d}" for i in (3, 6, 8, 10)} | rng(99, 109)
        allx = rng(74, 77) | {"oil_gas:0110", "oil_gas:0111"}
        for fid, f in oracle.fid.items():
            want = "conventional" if fid in conv else "unconventional" if fid in unc else "all" if fid in allx else ""
            premise(f["substream"] == want, f"{fid} substream is {f['substream']!r}, the spec expects {want!r}")

    def test_vocab_substream_all(self):
        v = json.loads((ROOT / "data" / "reference" / "vocab.json").read_text(encoding="utf-8"))
        premise("all" in v["substreams"]["oil_gas"], "vocab.json substreams.oil_gas has 'all'")

    def test_every_section_2_3_call_returns_exactly_one_row_in_its_window(self, oracle):
        bad = []
        for name, kw, regions, y0, y1, strict in _calls(oracle):
            for region in regions:
                for y in range(y0, y1 + 1):
                    try:
                        f = oracle.select(y, region, **kw)
                    except LookupError as exc:
                        bad.append(f"{name} {region} {y}: {exc}")
                        break
                    if strict and f["region"] != region:
                        bad.append(f"{name} {region} {y}: fell back to {f['region']}")
                        break
        premise(not bad, f"{len(bad)} registry windows do not tile: {bad[:3]}")

    def test_family_group_counts(self, oracle):
        premise(len(oracle.groups_of(stage="drilling", substream="conventional")) == 11, "11 vertical drilling groups")
        premise(len(oracle.groups_of(stage="drilling", substream="unconventional")) == 11, "11 horizontal drilling groups")
        premise(set(oracle.groups_of(stage="production", substream="conventional")) == set(GROUPS4), "four water groups (conventional)")
        premise(set(oracle.groups_of(stage="production", substream="unconventional")) == set(GROUPS4), "four water groups (unconventional)")

    def test_fate_shares_sum_to_one(self, oracle):
        base = {"stage": "production", "substream": "", "group": "", "route": "", "residue_type": ""}
        bad = []
        for region in ("USA", "XWL"):
            for y in range(1950, 2026):
                s = 0.0
                for t, route, res in (("reisolated", "", "og_produced_water"), ("impounded", "", "og_sludge"),
                                      ("liberated", "water_produced_discharge", ""), ("dispersed", "", "og_produced_water")):
                    s += fc(oracle, oracle.select(y, region, **{**base, "tier": t, "route": route, "residue_type": res,
                                                                  "driver_series": "produced_water_m3"})["factor_id"])[1]
                if abs(s - 1) > 1e-3:
                    bad.append(("water", region, y, s))
        for r in ("og_scale", "og_sludge"):
            for y in range(1950, 2026):
                s = sum(fc(oracle, oracle.select(y, "XWL", **{**base, "tier": t, "route": route, "residue_type": r,
                                                              "driver_series": ""})["factor_id"])[1]
                        for t, route in (("impounded", ""), ("dispersed", ""), ("liberated", "water_produced_discharge")))
                if abs(s - 1) > 1e-3:
                    bad.append((r, y, s))
        for y in range(1950, 2026):
            s = sum(fc(oracle, oracle.select(y, "XWL", stage="abandonment_scrap", substream="", group="", tier=t, route="",
                                             residue_type=r)["factor_id"])[1] for t, r in (("impounded", "og_scale"), ("dispersed", "og_scaled_scrap")))
            if abs(s - 1) > 1e-3:
                bad.append(("retained", y, s))
        premise(not bad, f"fate shares must sum to 1 within 1e-3: {bad[:3]}")

    def test_specific_registry_values(self, oracle):
        f16, f14, f78 = fc(oracle, "oil_gas:0016"), fc(oracle, "oil_gas:0014"), fc(oracle, "oil_gas:0078")
        premise(f16[1] == 0 and math.isclose(f16[2], 0.01), "0016 has central 0 and high 0.01")
        sh = oracle.a("produced_water_unconv_share", 2017, "USA") or oracle.a("produced_water_unconv_share", 2017, "XWL")
        premise(sh is not None and math.isclose(f14[1], sh.b.central), "0014 central equals the 2017 produced_water_unconv_share value")
        premise(math.isclose(f78[1], 0.9), "0078 central is 0.9")
        for fid, grp, res in (("0047", "Ra226+", "og_scale"), ("0048", "Ra226+", "og_sludge"), ("0049", "Ra228+", "og_scale"),
                              ("0050", "Ra228+", "og_sludge"), ("0051", "Pb210+", "og_scale"), ("0052", "Pb210+", "og_sludge")):
            f = oracle.fid[f"oil_gas:{fid}"]
            premise((f["group"], f["residue_type"], f["unit"], f["region"]) == (grp, res, "1", "XWL"), f"{fid} is the {grp} {res} solids factor (unit 1, XWL)")
        f74, f110 = oracle.fid["oil_gas:0074"], oracle.fid["oil_gas:0110"]
        premise(f110["residue_type"] == "og_processing_residue" and all(
            f74[k] == f110[k] for k in ("stage", "group", "tier", "route", "driver_series")), "0110 differs from 0074 only by the key-device residue type")

    def test_driver_series_columns(self, oracle):
        for fid, f in oracle.fid.items():
            premise(f["driver_series"] != "us_wells_drilled_total", f"{fid} uses the retired us_wells_drilled_total")
        for i in range(88, 99):
            premise(oracle.fid[f"oil_gas:{i:04d}"]["driver_series"] == "us_wells_drilled_vertical", f"{i} driver")
        for i in range(99, 110):
            premise(oracle.fid[f"oil_gas:{i:04d}"]["driver_series"] == "us_wells_drilled_horizontal", f"{i} driver")
        for i in (85, 86, 87):
            premise(oracle.fid[f"oil_gas:{i:04d}"]["driver_series"] == "oil_sands_ore_processed_t", f"{i} driver")
        premise({f["region"] for f in oracle.factors} <= {"XWL", "USA", "CAN"}, "registry regions are XWL, USA, CAN only")

    def test_flaring_row_and_retired_rows(self, oracle):
        f = oracle.fid["oil_gas:0111"]
        premise((f["driver_series"], f["unit"], f["substream"], f["group"], f["tier"], f["route"], f["stage"]) == (
            "gas_flared_m3", "Bq/m3", "all", "Rn222+", "liberated", "air_stack", "production"), "0111 is the flaring factor")
        premise(fc(oracle, "oil_gas:0111") == (150.0, 800.0, 1400.0), "0111 is 150/800/1,400")
        for i in (71, 72, 73):
            f = oracle.fid[f"oil_gas:{i:04d}"]
            premise("RETIRED (D70)" in f["notes"], f"{i} must carry 'RETIRED (D70)' in its notes")
            premise(f["driver_series"] == "oil_production_t" and f["substream"] == "", f"{i} keeps the per-tonne driver and an empty substream")

    def test_radon_budget_closes(self, oracle):
        wellhead = fc(oracle, "oil_gas:0111")[1]
        d, n, v = (fc(oracle, i)[1] for i in ("oil_gas:0074", "oil_gas:0110", "oil_gas:0075"))
        premise(d + n + v < wellhead, f"delivered + NGL + vented = {d + n + v} must stay below the wellhead {wellhead}")
        pb = fc(oracle, "oil_gas:0076")[1]
        want = (wellhead - d - n - v) * 4.715e-4 * 0.8       # 4.715e-4 and 0.8: constants of 6.2, not registry factors
        premise(math.isclose(pb, want, rel_tol=1e-3), f"0076 central {pb} must equal the closed budget {want} (6.2, D70)")
        premise(math.isclose(wellhead - d - n - v, 284.0, rel_tol=1e-9), "the plated-out Rn-222 is 284 Bq/m3 at the time of writing")

    def test_residue_types_and_events(self, oracle):
        rt = pd.read_csv(ROOT / "data" / "reference" / "residue_types.csv", dtype=str, keep_default_na=False)
        have = set(rt["residue_type"])
        for t in ("og_scale", "og_sludge", "og_produced_water", "og_scaled_scrap", "og_drill_cuttings", "og_processing_residue",
                  "oil_sands_tailings"):
            premise(t in have, f"residue type {t} exists in residue_types.csv")
        ev = pd.read_csv(ROOT / "data" / "events.csv", dtype=str, keep_default_na=False)
        premise(not (ev["stream"] == "oil_gas").any(), "events.csv has no oil_gas event (D32): a later event needs a stream change")

    def test_activity_premises(self, oracle):
        pw = "produced_water_m3"
        for y in range(1950, 2026):
            x, u = oracle.a(pw, y, "XWL").b, oracle.a(pw, y, "USA").b
            premise(x.low >= u.low and x.central >= u.central and x.high >= u.high, f"XWL water >= USA at all bounds in {y}")
            for s in ("oil_production_m3", "gas_production_m3", "ngl_production_m3"):
                premise(oracle.a(s, y, "XWL").b.central > oracle.a(s, y, "USA").b.central, f"{s}: XWL > USA in {y}")
            for s, cs in (("unit_value_oil_usd_per_m3", ("USA", "XWL")), ("unit_value_gas_usd_per_m3", ("USA", "XWL")),
                          ("unit_value_ngl_usd_per_m3", ("XWL",))):
                for c in cs:
                    premise(oracle.a(s, y, c) is not None, f"{s} has a {c} value in {y}")
        for s in ("oil_production_t", "gas_production_m3", "gas_flared_m3"):
            for y in oracle.years(s):
                xw = oracle.a(s, y, "XWL")
                lst = [oracle.a(s, y, c).b.central for c in oracle.countries(s, y)]
                if xw is None or not lst:
                    continue
                premise(xw.b.central - sum(lst) >= -TOL * xw.b.central, f"{s} {y}: world aggregate below the listed sum by more than 1e-5")
        fl_years_with_countries = {y for y in oracle.years("gas_flared_m3") if oracle.countries("gas_flared_m3", y)}
        premise(fl_years_with_countries == set(range(2012, 2026)), "gas_flared_m3 has country rows 2012-2025 only")
        premise(all(oracle.a("gas_flared_m3", y, "XWL") is not None for y in range(1950, 2026)), "gas_flared_m3 XWL 1950-2025")

    def test_predecessor_pairs_do_not_overlap(self, oracle):
        for s in ("gas_production_m3", "oil_production_t"):
            for succ in ("RUS", "KAZ", "AZE", "TKM", "UZB", "UKR"):
                both = [y for y in oracle.years(s) if (oracle.a(s, y, "SUN") and oracle.a(s, y, succ)
                                                      and oracle.a(s, y, "SUN").b.central > 0 and oracle.a(s, y, succ).b.central > 0)]
                premise(not both, f"{s}: SUN and {succ} are both non-zero in {both[:3]}")

    def test_duplicate_free_activity(self, oracle):
        assert oracle.act       # the oracle raises on a duplicate key while loading


class TestEpsilonState:
    """7.4: the residue parameters the engine needs; the script does not use them."""

    def _rt(self):
        return pd.read_csv(ROOT / "data" / "reference" / "residue_types.csv", dtype=str, keep_default_na=False).set_index("residue_type")

    def test_epsilon_222_filled_for_the_og_types(self):
        rt = self._rt()
        for t in ("og_scale", "og_sludge", "og_produced_water", "og_scaled_scrap", "og_drill_cuttings", "oil_sands_tailings"):
            for s in ("low", "central", "high"):
                premise(rt.loc[t, f"epsilon_rn222_{s}"] != "", f"epsilon_rn222_{s} of {t} is empty (7.4/D70 fill it)")
        premise([rt.loc["og_scale", f"epsilon_rn222_{s}"] for s in ("low", "central", "high")] == ["0.037", "0.088", "0.14"], "og_scale eps222")
        premise([rt.loc["og_sludge", f"epsilon_rn222_{s}"] for s in ("low", "central", "high")] == ["0.05", "0.15", "0.25"], "og_sludge eps222")

    def test_processing_residue_has_explicit_zero_for_both_radons(self):
        rt = self._rt()
        for k in ("rn222", "rn220"):
            vals_ = [rt.loc["og_processing_residue", f"epsilon_{k}_{s}"] for s in ("low", "central", "high")]
            premise(all(v != "" and float(v) == 0 for v in vals_), f"og_processing_residue epsilon_{k} must be an explicit 0/0/0, got {vals_}")

    def test_eps220_of_scale_and_sludge_is_filled_by_d71(self):
        rt = self._rt()
        want = {"og_scale": (1.8e-5, 3.6e-4, 3.9e-3), "og_sludge": (2.5e-5, 6.1e-4, 5e-3)}
        for t, w in want.items():
            got = tuple(float(rt.loc[t, f"epsilon_rn220_{s}"]) if rt.loc[t, f"epsilon_rn220_{s}"] != "" else None
                        for s in ("low", "central", "high"))
            premise(None not in got and all(math.isclose(g, x, rel_tol=1e-6) for g, x in zip(got, w)),
                    f"epsilon_rn220 of {t} is {got}, D71 writes {w}")

    def test_og_scaled_scrap_carries_the_scale_values(self):
        rt = self._rt()
        for k in ("epsilon_rn222_central",):
            premise(rt.loc["og_scaled_scrap", k] == rt.loc["og_scale", k], "og_scaled_scrap eps222 equals og_scale (7.4)")
        premise(rt.loc["og_scaled_scrap", "epsilon_rn220_central"] != "", "og_scaled_scrap eps220 is filled")

    def test_build_does_not_read_the_residue_types(self, og_mod, tmp_path, mini_base):
        root = make_mini(tmp_path, mini_act(), name="noref", reference=False)
        assert not (root / "data" / "reference").exists()
        res = og_mod.build(root)
        assert [vals(r) for r in res.rows] == [vals(r) for r in mini_base[1].rows], "the script must not read residue_types.csv (2.2)"


# --------------------------------------------------------------------------------------------
# (j) CLI
# --------------------------------------------------------------------------------------------
class TestCli:
    @staticmethod
    def _run(root, *extra):
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
        cmd = [sys.executable, "-m", "pipeline.streams.oil_gas", "--root", str(root)]
        return subprocess.run(cmd + list(extra), cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=1800, check=False)

    def test_cli_write_diff_and_log(self, og_mod, write_master, tmp_path):
        root = make_mini(tmp_path, mini_act(), name="cli_root")
        w = self._run(root, "--write")
        assert w.returncode == 0, f"--write exited {w.returncode}\nstdout: {w.stdout[-800:]}\nstderr: {w.stderr[-1500:]}"
        main = root / "data" / "streams" / "oil_gas.csv"
        pre = root / "data" / "streams_pre1950" / "oil_gas.csv"
        logf = root / "research" / "oil_gas" / "build_log.csv"
        assert main.is_file() and pre.is_file() and logf.is_file(), "--write must write all three files (OIL_GAS_SPEC 1)"
        res = og_mod.build(root)
        m2, p2 = tmp_path / "m2.csv", tmp_path / "p2.csv"
        write_master(list(res.rows), m2)
        write_master(list(res.rows_pre1950), p2)
        assert main.read_bytes() == m2.read_bytes(), "CLI master output differs from build() + write_master"
        assert pre.read_bytes() == p2.read_bytes(), "CLI pre-1950 output differs"
        counts = Counter(e["kind"] for e in res.log)
        printed = {m.group(1): int(m.group(2)) for m in re.finditer(r"^log (\w+): (\d+)\s*$", w.stdout + w.stderr, re.MULTILINE)}
        for kind, n in counts.items():
            assert printed.get(kind) == n, f"CLI must print 'log {kind}: {n}' (1, A8); printed {printed}"
        assert self._run(root).returncode == 0, "identical files must give exit 0"

        good = logf.read_bytes()
        logf.write_bytes(good + b"no_factor,1900,XXX,,tampered\n")
        assert self._run(root).returncode != 0, "a differing build_log.csv alone must give a non-zero exit"
        assert logf.read_bytes() != good, "the diff run must not overwrite the log"
        logf.write_bytes(good)
        t = pre.read_bytes()
        pre.write_bytes(t.replace(b"oil_gas,", b"oil_gaz,", 1))
        assert pre.read_bytes() != t
        assert self._run(root).returncode != 0, "a differing pre-1950 file must give a non-zero exit"
        pre.write_bytes(t)
        text = main.read_bytes()
        tampered = text.replace(b"oil_gas,", b"oil_gaz,", 1)
        assert tampered != text
        main.write_bytes(tampered)
        assert self._run(root).returncode != 0, "a differing master file must give a non-zero exit"
        assert main.read_bytes() == tampered, "the diff run must not overwrite files"
        main.write_bytes(text)
        assert self._run(root).returncode == 0
        logf.unlink()
        assert self._run(root).returncode != 0, "a missing committed build_log.csv must count as a difference"

    def test_cli_second_write_is_byte_identical(self, tmp_path):
        root = make_mini(tmp_path, mini_act(), name="cli_twice")
        files = [root / "data" / "streams" / "oil_gas.csv", root / "data" / "streams_pre1950" / "oil_gas.csv",
                 root / "research" / "oil_gas" / "build_log.csv"]
        first = None
        for _ in range(2):
            p = self._run(root, "--write")
            assert p.returncode == 0, p.stderr[-1000:]
            cur = [f.read_bytes() for f in files]
            if first is None:
                first = cur
            else:
                assert cur == first, "two --write runs differ (determinism, 9(d))"

    def test_committed_tree_cli_matches_when_files_exist(self):
        """Informational: the committed outputs (when present) must equal a fresh build; skipped until they exist."""
        if not (ROOT / "data" / "streams" / "oil_gas.csv").exists():
            pytest.skip("data/streams/oil_gas.csv is not committed yet")
        p = self._run(ROOT)
        assert p.returncode == 0, f"committed oil_gas outputs differ from a fresh build:\n{p.stdout[-600:]}{p.stderr[-600:]}"


# --------------------------------------------------------------------------------------------
# (g) fixture tests on miniature trees
# --------------------------------------------------------------------------------------------
ACT_COLUMNS = ["series", "year", "country", "value_low", "value_central", "value_high", "unit", "below_detection", "basis",
               "source_ids", "notes"]
MINI_YEARS = list(range(1948, 1953)) + list(range(2008, 2015)) + [2025]
MINI_POST = [y for y in MINI_YEARS if y >= 1950]
MINI_FLARE_WORLD = [y for y in MINI_POST if y < 2012]
MINI_FLARE_CTRY = [y for y in MINI_POST if y >= 2012]
UNIT_FOR = {"produced_water_m3": "m3", "gas_production_m3": "m3", "oil_production_t": "t", "oil_production_m3": "m3",
            "ngl_production_m3": "m3", "unit_value_oil_usd_per_m3": "USD/m3", "unit_value_gas_usd_per_m3": "USD/m3",
            "unit_value_ngl_usd_per_m3": "USD/m3", "gas_flared_m3": "m3", "oil_sands_ore_processed_t": "t",
            "us_wells_drilled_vertical": "1", "us_wells_drilled_horizontal": "1"}


def _a(series, y, c, central, band=0.1, basis="modelled", src="S0801"):
    return {"series": series, "year": y, "country": c, "value_low": central * (1 - band), "value_central": central,
            "value_high": central * (1 + band), "unit": UNIT_FOR[series], "below_detection": "false", "basis": basis,
            "source_ids": src, "notes": ""}


def mini_act():
    """Two activity files (file name -> rows). Gas and oil: three countries plus an XWL aggregate 5 % above their sum."""
    og, dr = [], []
    for y in MINI_YEARS:
        for c, g, o in (("USA", 7e11, 3.0e8), ("RUS", 6e11, 4.0e8), ("QAT", 1.5e11, 3.0e7)):
            og.append(_a("gas_production_m3", y, c, g, src="S0802"))
            og.append(_a("oil_production_t", y, c, o, src="S0803"))
        og.append(_a("gas_production_m3", y, "XWL", 1.52e12, band=0.05, src="S0802"))
        og.append(_a("oil_production_t", y, "XWL", 7.6e8, band=0.05, src="S0803"))
        og.append(_a("oil_production_m3", y, "USA", 3.6e8, src="S0804"))
        og.append(_a("oil_production_m3", y, "XWL", 9.0e8, band=0.05, src="S0804"))
        dr.append(_a("ngl_production_m3", y, "USA", 4e7, src="S0805"))
        dr.append(_a("ngl_production_m3", y, "XWL", 1.5e8, band=0.05, src="S0805"))
        dr.append(_a("us_wells_drilled_vertical", y, "USA", 20000.0, src="S0806"))
    for y in MINI_POST:
        og.append(_a("produced_water_m3", y, "USA", 3.0e9, src="S0807"))
        og.append(_a("produced_water_m3", y, "XWL", 1.2e10, band=0.1, src="S0807"))
        dr.append(_a("unit_value_oil_usd_per_m3", y, "USA", 400.0, src="S0808", basis="compiled"))
        dr.append(_a("unit_value_oil_usd_per_m3", y, "XWL", 380.0, src="S0808", basis="compiled"))
        dr.append(_a("unit_value_gas_usd_per_m3", y, "USA", 0.12, src="S0809", basis="compiled"))
        dr.append(_a("unit_value_gas_usd_per_m3", y, "XWL", 0.10, band=0.5, src="S0809", basis="extrapolated"))
        dr.append(_a("unit_value_ngl_usd_per_m3", y, "XWL", 200.0, band=0.3, src="S0810", basis="modelled"))
    for y in MINI_FLARE_WORLD:
        dr.append(_a("gas_flared_m3", y, "XWL", 1.3e11, band=0.3, src="S0811"))
    for y in MINI_FLARE_CTRY:
        dr.append(_a("gas_flared_m3", y, "RUS", 2.0e10, src="S0811", basis="compiled"))
        dr.append(_a("gas_flared_m3", y, "QAT", 1.0e10, src="S0811", basis="compiled"))
        dr.append(_a("gas_flared_m3", y, "XWL", 3.0e10, band=0.02, src="S0811", basis="compiled"))
    for y in [y for y in MINI_POST if y >= 2010]:
        dr.append(_a("us_wells_drilled_horizontal", y, "USA", 10000.0, src="S0806"))
        dr.append(_a("oil_sands_ore_processed_t", y, "CAN", 8.0e8, src="S0812"))
    return {"oil_gas.csv": og, "oil_gas_drivers.csv": dr}


def make_mini(tmp_path: Path, act: dict, factor_edit=None, name="mini", reference=True) -> Path:
    root = tmp_path / name
    (root / "data" / "activity").mkdir(parents=True)
    (root / "data" / "factors").mkdir(parents=True)
    (root / "data" / "streams").mkdir()
    (root / "data" / "streams_pre1950").mkdir()
    (root / "research" / "oil_gas").mkdir(parents=True)
    if reference:
        shutil.copytree(ROOT / "data" / "reference", root / "data" / "reference")
    shutil.copy(ROOT / "data" / "sources.csv", root / "data" / "sources.csv")
    shutil.copy(ROOT / "data" / "events.csv", root / "data" / "events.csv")
    for fname, rws in act.items():
        if rws is None:
            continue
        with open(root / "data" / "activity" / fname, "w", newline="\n", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=ACT_COLUMNS)
            w.writeheader()
            w.writerows(rws)
    fac = pd.read_csv(ROOT / "data" / "factors" / "oil_gas.csv", dtype=str, keep_default_na=False)
    recs = fac.to_dict("records")
    if factor_edit:
        recs = factor_edit(recs)
    with open(root / "data" / "factors" / "oil_gas.csv", "w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(fac.columns))
        w.writeheader()
        w.writerows(recs)
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


def scale_series(act, series, k, countries=None):
    for fn in act:
        for r in act[fn]:
            if r["series"] == series and (countries is None or r["country"] in countries):
                for c in ("value_low", "value_central", "value_high"):
                    r[c] *= k


def drop_rows(act, pred):
    for fn in act:
        act[fn] = [r for r in act[fn] if not pred(r)]


def set_rows(act, pred, **changes):
    n = 0
    for fn in act:
        for r in act[fn]:
            if pred(r):
                r.update(changes)
                n += 1
    assert n, "fixture edit matched no row"


@pytest.fixture(scope="module")
def mini_base(og_mod, tmp_path_factory):
    tmp = tmp_path_factory.mktemp("mini_base")
    return build_mini(og_mod, tmp)


def mini_problems(root, res, label="mini"):
    exp = Oracle(root).expected()
    main = compare_all(exp.rows, Rows(list(res.rows)), label)
    pre = compare_all(exp.pre, Rows(list(res.rows_pre1950)), label + " pre")
    return exp, [m for v in main.values() for m in v] + [m for v in pre.values() for m in v]


class TestMiniBase:
    def test_mini_tree_matches_oracle(self, mini_base):
        root, res, _rws, _lg = mini_base
        exp, flat = mini_problems(root, res)
        assert exp.rows and exp.pre
        assert not flat, "mini tree differs from the oracle: " + show(flat)

    def test_zero_flaring_residual_gives_no_rows(self, mini_base):
        _, _, rws, lg = mini_base
        assert not rws.find(2012, stage="production", country="XXX", group="Rn222+")
        assert not log_entries(lg, "negative_residual")

    def test_1949_vertical_drilling_logs_no_unit_value(self, mini_base):
        _, res, _rws, lg = mini_base
        es = log_entries(lg, "no_unit_value")
        assert len(es) == 1 and es[0]["year"] == 1949 and str(es[0]["detail"]).startswith("1949-1949 (1 year"), es
        assert not [r for r in list(res.rows) + list(res.rows_pre1950) if int(r["year"]) == 1949 and r["stage"] == "drilling"]

    def test_horizontal_wells_only_where_the_driver_exists(self, mini_base):
        _, _, rws, _ = mini_base
        assert not rws.find(2008, stage="drilling", substream="unconventional")
        assert rws.find(2010, stage="drilling", substream="unconventional")
        assert rws.find(2008, stage="drilling", substream="conventional")

    def test_stderr_in_process(self, og_mod, tmp_path, capfd):
        build_mini(og_mod, tmp_path)
        assert capfd.readouterr().err == ""

    def test_at_most_one_lib_warning(self, mini_base):
        assert len(log_entries(mini_base[3], "lib_warning")) <= 1

    def test_merge_gives_one_row_per_colliding_key(self, mini_base, write_master, tmp_path):
        write_master(list(mini_base[1].rows), tmp_path / "x.csv")      # write_master raises on a duplicate key (X01)
        keys = Counter(rkey(r) for r in mini_base[1].rows)
        assert max(keys.values()) == 1

    def test_driver_basis_suffix(self, og_mod, tmp_path):
        act = mini_act()
        set_rows(act, lambda r: r["series"] == "produced_water_m3" and r["country"] == "USA" and r["year"] == 2025, basis="extrapolated")
        set_rows(act, lambda r: r["series"] == "us_wells_drilled_vertical" and r["year"] == 2013, basis="interpolated")
        set_rows(act, lambda r: r["series"] == "oil_sands_ore_processed_t" and r["year"] == 2014, basis="extrapolated")
        set_rows(act, lambda r: r["series"] == "gas_production_m3" and r["country"] == "RUS" and r["year"] == 2014, basis="interpolated")
        set_rows(act, lambda r: r["series"] == "gas_production_m3" and r["country"] == "XWL" and r["year"] == 2013, basis="extrapolated")
        root, res, rws, _ = build_mini(og_mod, tmp_path, act)
        _exp, flat = mini_problems(root, res)
        assert not flat, show(flat)
        usa25 = rws.one(2025, stage="production", substream="conventional", country="USA", group="K40", tier="reisolated",
                        product="oil", allocation_variant="default")
        assert notes_parts(usa25["notes"])["drv"] == {"extrapolated"} and usa25["basis"] == "modelled"
        xxx25 = rws.one(2025, stage="production", substream="conventional", country="XXX", group="K40", tier="reisolated",
                        product="oil", allocation_variant="default")
        assert notes_parts(xxx25["notes"])["drv"] == {"extrapolated"}, "XXX water uses the USA row too: both rows count"
        dr = rws.one(2013, stage="drilling", substream="conventional", group="U238+", product="oil", allocation_variant="default")
        assert notes_parts(dr["notes"])["drv"] == {"interpolated"}
        os_ = rws.one(2014, stage="oil_sands_mining", group="Th232")
        assert notes_parts(os_["notes"])["drv"] == {"extrapolated"}
        rus = rws.one(2014, stage="processing_transport", country="RUS", group="Rn222+", route="air_delivered_gas", product="gas")
        assert notes_parts(rus["notes"])["drv"] == {"interpolated"}
        xxx = rws.one(2013, stage="processing_transport", country="XXX", group="Rn222+", route="air_delivered_gas", product="gas")
        assert notes_parts(xxx["notes"])["drv"] == {"extrapolated"}, "a rest-of-world residual counts the aggregate and the listed rows"
        both = rws.one(2014, stage="processing_transport", country="XXX", group="Rn222+", route="air_delivered_gas", product="gas")
        assert notes_parts(both["notes"])["drv"] == {"interpolated"}


class TestMiniResiduals:
    def test_negative_gas_residual_logged_and_no_rows(self, og_mod, tmp_path):
        act = mini_act()
        set_rows(act, lambda r: r["series"] == "gas_production_m3" and r["country"] == "XWL" and r["year"] == 2010,
                 value_low=1.3e12, value_central=1.4e12, value_high=1.5e12)
        root, res, rws, lg = build_mini(og_mod, tmp_path, act)
        es = log_entries(lg, "negative_residual", year=2010)
        assert len(es) == 1, f"one negative_residual entry for gas 2010 (the oil aggregate is fine), got {es}"
        nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?(?:[eE][+-]?\d+)?", str(es[0]["detail"]))]
        assert any(abs(n - 5.0e10) <= 1e-2 * 5.0e10 for n in nums), f"detail must carry the magnitude 5e10 m3: {es[0]['detail']!r}"
        assert not rws.find(2010, stage="processing_transport", country="XXX", route="air_delivered_gas")
        assert rws.find(2010, stage="processing_transport", country="XXX", route="air_stack"), "oil residual unaffected"
        assert len(log_entries(lg, "negative_residual")) == 1
        _, flat = mini_problems(root, res)
        assert not flat, show(flat)

    def test_negative_quantity_difference_in_allocation(self, og_mod, tmp_path):
        act = mini_act()
        set_rows(act, lambda r: r["series"] == "ngl_production_m3" and r["country"] == "XWL" and r["year"] == 2011,
                 value_low=3e7, value_central=3.5e7, value_high=4e7)
        root, res, rws, lg = build_mini(og_mod, tmp_path, act)
        es = log_entries(lg, "negative_residual", year=2011)
        assert len(es) == 1, f"one negative_residual entry for the NGL quantity difference of 2011, got {es}"
        nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?(?:[eE][+-]?\d+)?", str(es[0]["detail"]))]
        assert any(abs(n - 5e6) <= 1e-2 * 5e6 for n in nums), es[0]["detail"]
        r = rws.one(2011, stage="production", substream="conventional", country="XXX", group="K40", tier="reisolated",
                    product="ngl", allocation_variant="default")
        assert vals(r) == (0.0, 0.0, 0.0) and not as_bool(r["below_detection"]), "NGL share is a structural zero"
        _, flat = mini_problems(root, res)
        assert not flat, show(flat)

    @pytest.mark.parametrize("rel,written_", [(5e-6, False), (-5e-6, False), (9e-6, False), (5e-5, True), (1e-3, True)])
    def test_flaring_residual_tolerance(self, og_mod, tmp_path, rel, written_):
        act = mini_act()
        set_rows(act, lambda r: r["series"] == "gas_flared_m3" and r["country"] == "XWL" and r["year"] == 2012,
                 value_low=3e10 * (1 + rel) * 0.98, value_central=3e10 * (1 + rel), value_high=3e10 * (1 + rel) * 1.02)
        root, res, rws, lg = build_mini(og_mod, tmp_path, act)
        xxx = rws.find(2012, stage="production", country="XXX", group="Rn222+", route="air_stack")
        assert bool(xxx) == written_, f"relative residual {rel}: rest-of-world flaring row present = {bool(xxx)}"
        assert not log_entries(lg, "negative_residual"), "a residual within the 1e-5 tolerance is zero, not a negative residual"
        if xxx:
            assert REST_GAS in xxx[0]["notes"]
        _, flat = mini_problems(root, res)
        assert not flat, show(flat)

    def test_flaring_with_country_rows_and_world_row_writes_countries_and_residual_only(self, mini_base):
        _, _, rws, _ = mini_base
        r = rws.find(2013, stage="production", group="Rn222+", route="air_stack")
        assert {x["country"] for x in r} == {"RUS", "QAT"}, f"2013: country rows only, got {[x['country'] for x in r]}"
        w = rws.find(2011, stage="production", group="Rn222+", route="air_stack")
        assert [x["country"] for x in w] == ["XXX"] and WORLD_FLARE in w[0]["notes"]

    def test_zero_production_country_year_is_silent(self, og_mod, tmp_path):
        act = mini_act()
        set_rows(act, lambda r: r["series"] == "oil_production_t" and r["country"] == "QAT" and r["year"] == 2010,
                 value_low=0, value_central=0, value_high=0)
        _, _, rws, lg = build_mini(og_mod, tmp_path, act)
        assert not rws.find(2010, country="QAT", route="air_stack")
        assert not [e for e in lg if e["country"] == "QAT"], "zero production is not a missing driver"

    def test_absent_country_year_is_silent(self, og_mod, tmp_path):
        act = mini_act()
        drop_rows(act, lambda r: r["series"] == "gas_production_m3" and r["country"] == "QAT" and r["year"] == 2010)
        root, res, rws, lg = build_mini(og_mod, tmp_path, act)
        assert not rws.find(2010, country="QAT", route="air_delivered_gas")
        assert not [e for e in lg if e["country"] == "QAT"], "a country with no row is not a missing driver (8)"
        _, flat = mini_problems(root, res)
        assert not flat, show(flat)


class TestMiniMissingAndAbsent:
    def test_missing_driver_years_are_aggregated_runs(self, og_mod, tmp_path, mini_base):
        act = mini_act()
        drop_rows(act, lambda r: r["series"] == "produced_water_m3" and r["year"] in (2010, 2011))
        drop_rows(act, lambda r: r["series"] == "produced_water_m3" and r["year"] == 2013)
        _, _, rws, lg = build_mini(og_mod, tmp_path, act)
        assert not rws.find(2010, stage="production", group="K40") and not rws.find(2011, stage="abandonment_scrap")
        assert rws.find(2012, stage="production", group="K40")
        runs = {(e["country"], str(e["detail"])[:19]) for e in log_entries(lg, "no_driver") if e["year"] in (2010, 2013)}
        assert ("USA", "2010-2011 (2 years)") in runs and ("XXX", "2010-2011 (2 years)") in runs, runs
        assert any(d.startswith("2013-2013 (1 year") for _c, d in runs), runs
        base_runs = [e for e in log_entries(mini_base[3], "no_driver") if e["year"] in (2010, 2013)]
        assert not base_runs

    def test_absent_series_gives_one_aggregated_no_driver_and_no_rows(self, og_mod, tmp_path):
        act = mini_act()
        drop_rows(act, lambda r: r["series"] == "oil_sands_ore_processed_t")
        _, _res, rws, lg = build_mini(og_mod, tmp_path, act, name="absent_os")
        assert not rws.find(stage="oil_sands_mining")
        es = [e for e in log_entries(lg, "no_driver") if e["country"] == "CAN"]
        assert len(es) == 1, f"an absent oil_sands_ore_processed_t must give exactly one aggregated no_driver entry (8): {es}"

    def test_absent_horizontal_series_removes_only_unconventional_drilling(self, og_mod, tmp_path, mini_base):
        act = mini_act()
        drop_rows(act, lambda r: r["series"] == "us_wells_drilled_horizontal")
        _, _res, rws, _lg = build_mini(og_mod, tmp_path, act, name="absent_hz")
        assert not rws.find(stage="drilling", substream="unconventional") and rws.find(stage="drilling", substream="conventional")
        assert len(mini_base[2].rows) > len(rws.rows)

    def test_absent_flaring_series_gives_no_flaring_rows(self, og_mod, tmp_path):
        act = mini_act()
        drop_rows(act, lambda r: r["series"] == "gas_flared_m3")
        _, _res, rws, lg = build_mini(og_mod, tmp_path, act, name="absent_fl")
        assert not [r for r in rws.rows if _family_of(r) == "FL"]
        assert [e for e in log_entries(lg, "no_driver") if e["country"] == "XXX"]

    def test_pre_1950_walk_has_no_joint_rows(self, mini_base):
        _, res, _, _ = mini_base
        assert {_family_of(r) for r in res.rows_pre1950} == {"GD", "GN", "GV", "GP", "OR"}
        assert {int(r["year"]) for r in res.rows_pre1950} == {1948, 1949}


class TestMiniErrors:
    def test_duplicate_activity_rows_in_one_file_raise(self, og_mod, tmp_path):
        act = mini_act()
        act["oil_gas.csv"].append(dict(next(r for r in act["oil_gas.csv"] if r["series"] == "gas_production_m3"
                                          and r["country"] == "RUS" and r["year"] == 2010)))
        with pytest.raises(lib_error()) as ei:
            build_mini(og_mod, tmp_path, act)
        msg = str(ei.value)
        assert "gas_production_m3" in msg and "2010" in msg and "RUS" in msg, f"message must name the key: {msg}"

    def test_duplicate_activity_rows_across_the_two_files_raise(self, og_mod, tmp_path):
        act = mini_act()
        act["oil_gas_drivers.csv"].append(dict(next(r for r in act["oil_gas.csv"] if r["series"] == "gas_production_m3"
                                                  and r["country"] == "RUS" and r["year"] == 2010)))
        with pytest.raises(lib_error()) as ei:
            build_mini(og_mod, tmp_path, act)
        assert "RUS" in str(ei.value) and "2010" in str(ei.value)

    def test_ambiguous_registry_row_propagates(self, og_mod, tmp_path):
        def dup(recs):
            c = dict(next(x for x in recs if x["factor_id"] == "oil_gas:0074"))
            c["factor_id"] = "oil_gas:9999"
            return recs + [c]
        with pytest.raises(lib_error(), match="ambiguous factor rows"):
            build_mini(og_mod, tmp_path, factor_edit=dup)

    def test_registry_window_gap_logs_no_factor(self, og_mod, tmp_path):
        _root, _res, rws, lg = build_mini(og_mod, tmp_path, factor_edit=edit_factor("oil_gas:0074", year_to=2012))
        assert rws.find(2012, country="RUS", route="air_delivered_gas", product="gas")
        assert not rws.find(2013, country="RUS", route="air_delivered_gas", product="gas")
        assert rws.find(2013, country="RUS", route="air_delivered_gas", product="ngl"), "other families are unaffected"
        es = [e for e in log_entries(lg, "no_factor") if e["country"] == "RUS" and e["group"] == "Rn222+"]
        assert covered(es) == {2013, 2014, 2025} and len(es) == 2, [e["detail"] for e in es]

    def test_share_with_high_above_one_raises(self, og_mod, tmp_path):
        with pytest.raises(lib_error()):
            build_mini(og_mod, tmp_path, factor_edit=edit_factor("oil_gas:0012", value_high=1.5))

    @pytest.mark.parametrize("fid", ["oil_gas:0033", "oil_gas:0043", "oil_gas:0047", "oil_gas:0061", "oil_gas:0083",
                                     "oil_gas:0017", "oil_gas:0078"])
    def test_any_share_with_high_1_5_raises(self, og_mod, tmp_path, fid):
        """3.4: a share with high above 1 raises, whichever family uses it (not only where a complement is taken)."""
        with pytest.raises(lib_error()):
            build_mini(og_mod, tmp_path, factor_edit=edit_factor(fid, value_high=1.5), name="hi15")

    def test_unit_one_factor_with_another_unit_raises(self, og_mod, tmp_path):
        with pytest.raises(lib_error()):
            build_mini(og_mod, tmp_path, factor_edit=edit_factor("oil_gas:0012", unit="Bq/m3"))

    def test_driver_series_mismatch_on_oil_sands_raises_and_empty_cell_is_accepted(self, og_mod, tmp_path, mini_base):
        with pytest.raises(lib_error(), match=re.compile("driver mismatch", re.IGNORECASE)):
            build_mini(og_mod, tmp_path, factor_edit=edit_factor("oil_gas:0085", driver_series="oil_sands_ore_t"), name="mm")

        def blank(recs):
            for r in recs:
                if r["factor_id"] in ("oil_gas:0085", "oil_gas:0086", "oil_gas:0087"):
                    r["driver_series"] = ""
            return recs
        _, _, rws, _ = build_mini(og_mod, tmp_path, factor_edit=blank, name="blank")
        assert [vals(r) for r in rws.find(stage="oil_sands_mining")] == [vals(r) for r in mini_base[2].find(stage="oil_sands_mining")]

    def test_missing_unit_value_year_inside_the_series_raises(self, og_mod, tmp_path):
        """4.2 and 9(g): a product with q > 0 and no unit value raises LibError (before the series starts, 1949, it logs instead: C2)."""
        act = mini_act()
        drop_rows(act, lambda r: r["series"] == "unit_value_gas_usd_per_m3" and r["year"] == 2011)
        with pytest.raises(lib_error()):
            build_mini(og_mod, tmp_path, act)



class TestMiniMainRadio:
    def test_ngl_outranking_gas_gives_radio_ngl(self, og_mod, tmp_path):
        act = mini_act()
        scale_series(act, "unit_value_gas_usd_per_m3", 0.05)
        root, res, rws, _ = build_mini(og_mod, tmp_path, act)
        for geo in ("USA", "XXX"):
            al = Oracle(root).alloc(geo, 2010)
            premise((al["main"], al["radio"]) == ("oil", "ngl"), f"{geo}: the fixture must rank oil > ngl > gas, got {al['main']}/{al['radio']}")
            kw = {"stage": "production", "substream": "conventional", "country": geo, "group": "K40", "tier": "reisolated"}
            nz = lambda v, kw=kw: [p for p in PRODUCTS if float(rws.one(2010, product=p, allocation_variant=v, **kw)["value_central"]) > 0]
            assert nz("bound_main") == ["oil"] and nz("bound_radio") == ["ngl"], (geo, nz("bound_main"), nz("bound_radio"))
        _, flat = mini_problems(root, res)
        assert not flat, show(flat)

    def test_gas_as_main_gives_radio_oil_and_still_three_variants(self, og_mod, tmp_path):
        act = mini_act()
        scale_series(act, "unit_value_gas_usd_per_m3", 100.0)
        root, res, rws, _ = build_mini(og_mod, tmp_path, act)
        for geo in ("USA", "XXX"):
            al = Oracle(root).alloc(geo, 2010)
            premise((al["main"], al["radio"]) == ("gas", "oil"), f"{geo}: the fixture must rank gas > oil, got {al['main']}/{al['radio']}")
            kw = {"stage": "production", "substream": "conventional", "country": geo, "group": "K40", "tier": "reisolated"}
            nz = lambda v, kw=kw: [p for p in PRODUCTS if float(rws.one(2010, product=p, allocation_variant=v, **kw)["value_central"]) > 0]
            assert nz("bound_main") == ["gas"] and nz("bound_radio") == ["oil"]
            assert len([r for r in rws.find(2010, **kw)]) == 9
        _, flat = mini_problems(root, res)
        assert not flat, show(flat)


def _set_central(act, series, country, central, band=0.1):
    set_rows(act, lambda r: r["series"] == series and r["country"] == country,
             value_low=central * (1 - band), value_central=central, value_high=central * (1 + band))


class TestMiniTiesAndCauses:
    """Tie-break order of main and radio (4.4, 4.5) and cause order (3.3)."""

    CASES: ClassVar[dict] = {
        # (oil q, oil v, gas q, gas v, ngl q, ngl v) -> value oil / gas / ngl
        "all_equal": ((1e8, 2.0), (2e8, 1.0), (4e7, 5.0), "oil", "gas"),          # 2e8 / 2e8 / 2e8
        "oil_gas_tie_ngl_low": ((1e8, 2.0), (2e8, 1.0), (4e7, 1.0), "oil", "gas"),  # 2e8 / 2e8 / 4e7
        "gas_top_oil_ngl_tie": ((1e8, 2.0), (2e8, 2.0), (4e7, 5.0), "gas", "oil"),  # 2e8 / 4e8 / 2e8
    }

    @pytest.mark.parametrize("case", list(CASES))
    def test_exact_value_ties_follow_the_order_oil_gas_ngl(self, og_mod, tmp_path, case):
        (qo, vo), (qg, vg), (qn, vn), main, radio = self.CASES[case]
        act = mini_act()
        _set_central(act, "oil_production_m3", "USA", qo)
        _set_central(act, "gas_production_m3", "USA", qg)
        _set_central(act, "ngl_production_m3", "USA", qn)
        _set_central(act, "unit_value_oil_usd_per_m3", "USA", vo)
        _set_central(act, "unit_value_gas_usd_per_m3", "USA", vg)
        _set_central(act, "unit_value_ngl_usd_per_m3", "XWL", vn)
        root, res, rws, _ = build_mini(og_mod, tmp_path, act, name=f"tie_{case}")
        val = {"oil": qo * vo, "gas": qg * vg, "ngl": qn * vn}
        premise(sorted(val.values())[-2] == max(val.values()) or case == "gas_top_oil_ngl_tie",
                f"the {case} fixture must contain an exact tie for the top value: {val}")
        premise(val["oil"] == val["ngl"] if case == "gas_top_oil_ngl_tie" else val["oil"] == val["gas"], f"exact tie in {case}")
        al = Oracle(root).alloc("USA", 2010)
        assert (al["main"], al["radio"]) == (main, radio), f"oracle reading of the spec tie order: {al['main']}/{al['radio']}"
        kw = {"stage": "production", "substream": "conventional", "country": "USA", "group": "K40", "tier": "reisolated"}
        nz = lambda v: [p for p in PRODUCTS if float(rws.one(2010, product=p, allocation_variant=v, **kw)["value_central"]) > 0]
        assert nz("bound_main") == [main], f"{case}: main on a tie must be {main} (4.4, ties oil, gas, ngl); got {nz('bound_main')}"
        assert nz("bound_radio") == [radio], f"{case}: radio on a tie must be {radio} (4.5); got {nz('bound_radio')}"
        _, flat = mini_problems(root, res)
        assert not flat, show(flat)

    def test_causes_are_written_in_the_fixed_order(self, og_mod, tmp_path):
        """XWL water low below the USA low gives a clipped rest-of-world volume; in 1951 the XWL unconventional share has
        central 0 as well, so zero_central_factor and clipped_difference both apply (order: zero_central_factor first)."""
        act = mini_act()
        set_rows(act, lambda r: r["series"] == "produced_water_m3" and r["country"] == "XWL", value_low=1e8)
        root, res, rws, _ = build_mini(og_mod, tmp_path, act, name="causes")
        r = rws.one(1951, stage="production", substream="unconventional", country="XXX", group="Ra226+", tier="reisolated",
                    product="oil", allocation_variant="default")
        assert as_bool(r["below_detection"])
        assert notes_parts(r["notes"])["cause"] == ["zero_central_factor", "clipped_difference"], r["notes"]
        c = rws.one(2010, stage="production", substream="conventional", country="XXX", group="Ra226+", tier="reisolated",
                    product="oil", allocation_variant="default")
        assert as_bool(c["below_detection"]) and "clipped_difference" in notes_parts(c["notes"])["cause"], c["notes"]
        order = ["zero_central_factor", "exact_zero", "clipped_difference", "floor_dominance", "inherited_flag"]
        for x in res.rows:
            cs = notes_parts(x["notes"])["cause"]
            if cs:
                assert cs == [k for k in order if k in cs], f"cause order: {cs}"
        _, flat = mini_problems(root, res)
        assert not flat, show(flat)
