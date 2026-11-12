"""Spec-blind tests for the Olympic Dam amendment of the nuclear stream (docs/NUCLEAR_SPEC.md v1.3 section 14, D74(a)).

Written from NUCLEAR_SPEC section 14 (and the conventions of the rest of that spec), WIND_SOLAR_SPEC
section 6.3 (the two-ledger table), DECISIONS D74, SCHEMA v2.6 and LIB_SPEC v1.6. pipeline/streams/nuclear.py
was not read. Expected values come from nuclear_od_oracle.py (which re-uses the standard-library bounds
arithmetic of nuclear_oracle.py; no pipeline.lib); every factor and activity number is read from the files.

Mapping to the section 14.5 done conditions
-------------------------------------------
(i) premises            TestPremises
(c) carve-out           TestF6Carveout (row-by-row against the oracle; F6 + P_OD x phi = v1.2 F6 against the
                        committed v1.2 stream; negative_residual log)
(c) new identity        TestTwoLedgerClosure (F8 + copper ledger + military remainder = pool; copper ledger
                        computed from the files per WIND_SOLAR_SPEC 6.3, not from stream 4)
(a)/(b) F8 rows         TestF8Rows (row set, columns, values per D6 variant, notes, flags, factor_ids)
(f) hand cases          TestHandCases (AUS 2023 F6 Ra226+; F8 Ra226+ 2023 in all three variants)
F1-F5, F7 unchanged     TestUnchanged (whole-stream text comparison with the v1.2 baseline, except AUS F6)
(g) fixtures            TestMiniFixtures (clip, absent OD series, absent commodity_factors.csv, exact-phi closure)
committed stream        TestCommittedStream

BASELINE
--------
The "current committed output" is a snapshot of data/streams/nuclear.csv.gz and
data/streams_pre1950/nuclear.csv.gz taken before the D74 rebuild: pipeline/tests/streams/baselines/. The live
data/streams files will be overwritten by the rebuild, so the snapshot is the v1.2 reference. Do not refresh it.

SKIP RULE
---------
Every test that needs the D74 inputs skips (premise skip) until build/d74_staging has been applied into data/
(APPLY.md): commodity_factors.csv with the iocg_olympic_dam rows, u_production_od, prod_copper_od and
od_value_share_u. Once applied, a missing implementation fails (import error or missing rows), as intended.

CLARIFICATIONS (NUCLEAR_SPEC 14.2-14.4 as clarified 2026-11-11)
-----------------------------------------------------------------
* No clip occurs with the staged series (OD <= conventional AUS bound by bound). The clip rule is tested on a
  fixture: raw central < 0 -> no F6 rows for the year plus one negative_residual entry (AUS, group "", detail
  "u_production_od: conventional AUS minus OD = <c> t U; no F6 rows"); raw central exactly 0 -> no rows, no log;
  central > 0 with a clipped low -> row written, flagged clipped_difference.
* Military remainder a_v (1 - phi) P_OD per variant; logged per year and variant (default, bound_radio) as
  "<variant>: a_v*(1-phi)=<v>; Ra226+ central <Bq/a>", country AUS, group "".
* B4 (ruled): the source_ids of carved-out F6 rows include the u_production_od row's sources (required).
* Shares are central-only scalars (LIB_SPEC 2.2, WIND_SOLAR S11): F8 default uses the central od_value_share_u even
  when the row has a band (TestMiniFixtures.test_banded_share_uses_central_exactly).
* phi_civil has low < central for every year 1988-2025, so the low/high closure is vacuous on the real data and
  is tested on a fixture with an exact phi.
"""
from __future__ import annotations

import csv
import gzip
import importlib
import math
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
import pytest
from nuclear_od_oracle import RULE, VARIANTS, ODOracle
from nuclear_oracle import B, Oracle, scale

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent / "baselines"
REL = 1e-7
CLOSE = 1e-5
F6_FRAGMENT = "Olympic Dam carved out (D74)"
OD_GROUPS = ["U238+", "U234", "Th230", "U235+", "Ra226+", "Pb210+", "Po210", "Th232", "Ra228+", "Th228+"]
OD_IDS = [f"commodity:{n:04d}" for n in range(87, 97)]
YEARS = list(range(1988, 2026))
F8_KEYCOLS = ("year", "stage", "country", "group", "tier", "quantity", "residue_type", "allocation_variant")


# --------------------------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------------------------
def as_bool(v) -> bool:
    return v.strip().lower() == "true" if isinstance(v, str) else bool(v)


def blank(v) -> bool:
    return v is None or v == ""


def ids(v) -> list[str]:
    if blank(v):
        return []
    return [str(x) for x in (v if isinstance(v, (list, tuple)) else str(v).split(";"))]


def vals(r: dict) -> tuple[float, float, float]:
    return float(r["value_low"]), float(r["value_central"]), float(r["value_high"])


def close(a: float, b: float, rel: float = REL) -> bool:
    return (a == 0 and b == 0) or math.isclose(a, b, rel_tol=rel, abs_tol=0.0)


def desc(r: dict) -> str:
    return ", ".join(f"{k}={r.get(k)!r}" for k in ("year", "stage", "country", "group", "tier", "quantity",
                                                   "residue_type", "allocation_variant"))


def is_f8(r: dict) -> bool:
    return r["stage"] == "u_milling" and r["tier"] == "impounded" and r["residue_type"] == "metal_tailings"


def is_aus_f6(r: dict) -> bool:
    return (r["stage"] == "u_milling" and r["tier"] == "impounded" and r["residue_type"] == "u_tailings"
            and r["country"] == "AUS" and r["quantity"] == "flow" and not r["event_id"])


def cause_of(notes: str):
    i = notes.rfind("; below_detection cause: ")
    return None if i < 0 else notes[i + len("; below_detection cause: "):].strip().split("+")


def driver_basis_of(notes: str) -> set:
    i = notes.find("; driver basis: ")
    if i < 0:
        return set()
    tail = notes[i + len("; driver basis: "):]
    word = tail.split(";")[0].strip()
    return set(word.split("+"))


def read_gz(path: Path) -> list[dict]:
    with gzip.open(path, "rt", newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def read_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def full_key(r: dict) -> tuple:
    return (int(r["year"]), r["substream"], r["stage"], r["country"], r["group"], r["tier"], r["quantity"],
            r.get("route") or "", r.get("residue_type") or "", r.get("event_id") or "",
            r.get("allocation_variant") or "")


# --------------------------------------------------------------------------------------------
# applied-data premise skip, build fixtures
# --------------------------------------------------------------------------------------------
def d74_applied(root: Path) -> tuple[bool, str]:
    cf = root / "data" / "reference" / "commodity_factors.csv"
    if not cf.exists():
        return False, "data/reference/commodity_factors.csv not applied (build/d74_staging/APPLY.md)"
    df = pd.read_csv(cf, dtype=str, keep_default_na=False, usecols=lambda c: c in ("ore_type",))
    if "ore_type" not in df.columns or "iocg_olympic_dam" not in set(df["ore_type"]):
        return False, "commodity_factors.csv has no iocg_olympic_dam rows (D74 staging not applied)"
    for fname, series in (("uranium.csv", "u_production_od"), ("commodity_production.csv", "prod_copper_od"),
                          ("wind_solar_shares.csv", "od_value_share_u")):
        p = root / "data" / "activity" / fname
        if not p.exists():
            return False, f"data/activity/{fname} not applied"
        s = pd.read_csv(p, dtype=str, keep_default_na=False, usecols=["series"])
        if series not in set(s["series"]):
            return False, f"series {series} absent from data/activity/{fname} (D74 staging not applied)"
    return True, ""


@pytest.fixture(scope="module")
def applied():
    ok, why = d74_applied(ROOT)
    if not ok:
        pytest.skip(f"PREMISE (contingent test): {why}")


@pytest.fixture(scope="module")
def nuclear_mod(applied):
    try:
        return importlib.import_module("pipeline.streams.nuclear")
    except ImportError as exc:
        pytest.fail(f"cannot import pipeline.streams.nuclear: {type(exc).__name__}: {exc}")


@pytest.fixture(scope="module")
def result(nuclear_mod):
    res = nuclear_mod.build(ROOT)
    for attr in ("rows", "rows_pre1950", "log"):
        assert hasattr(res, attr), f"BuildResult has no attribute {attr!r}"
    return res


@pytest.fixture(scope="module")
def rows(result) -> list[dict]:
    return list(result.rows)


@pytest.fixture(scope="module")
def log(result) -> list[dict]:
    return list(result.log)


@pytest.fixture(scope="module")
def od(applied) -> ODOracle:
    return ODOracle(ROOT)


@pytest.fixture(scope="module")
def f8_rows(rows) -> dict:
    out: dict = defaultdict(list)
    for r in rows:
        if is_f8(r):
            out[(int(r["year"]), r["group"], r["allocation_variant"])].append(r)
    return dict(out)


@pytest.fixture(scope="module")
def aus_f6(rows) -> dict:
    out: dict = defaultdict(list)
    for r in rows:
        if is_aus_f6(r):
            out[(int(r["year"]), r["group"])].append(r)
    return dict(out)


@pytest.fixture(scope="module")
def baseline():
    p = BASE / "nuclear_v12.csv.gz"
    assert p.exists(), f"missing v1.2 baseline snapshot {p}"
    rws = read_gz(p)
    assert not any(is_f8(r) for r in rws), "PREMISE BROKEN: the baseline snapshot already contains F8 rows"
    return rws


# --------------------------------------------------------------------------------------------
# (i) premises
# --------------------------------------------------------------------------------------------
class TestPremises:
    def test_od_factor_rows_cover_every_year_and_group(self, od):
        assert sorted(od.groups) == sorted(OD_GROUPS), \
            f"PREMISE BROKEN: OD groups in the registry {sorted(od.groups)}, section 14.4 lists {sorted(OD_GROUPS)}"
        assert sorted(r["factor_id"] for r in od.cf) == OD_IDS, "OD factor ids must be commodity:0087-0096"
        for y in YEARS:
            for g in OD_GROUPS:
                od.factor(y, g)  # asserts exactly one row
        for r in od.cf:
            assert r["unit"] == "Bq/t" and r["residue_type"] == "metal_tailings" and r["region"] == "AUS"
            assert r["tier"] == "impounded"

    def test_od_series_cover_1988_2025(self, od):
        for name, d in (("u_production_od", od.od_u), ("prod_copper_od", od.q_od), ("od_value_share_u", od.w_u)):
            assert sorted(d) == YEARS, f"PREMISE BROKEN: {name} years {sorted(d)[:3]}...{sorted(d)[-3:]}, expected 1988-2025"

    def test_od_uranium_not_above_aus_total_at_central(self, od):
        for y in YEARS:
            assert od.o.a("u_production_od", y, "AUS").central <= od.o.a("u_production", y, "AUS").central, \
                f"PREMISE BROKEN: u_production_od > u_production AUS in {y}"

    def test_od_uranium_not_above_conventional_aus_bound_by_bound(self, od):
        """14.2 OD series rule: u_production_od <= C_AUS = (P_l(1-s_h), P_c(1-s_c), P_h(1-s_l)) at every bound."""
        for y in YEARS:
            c, d = od.conv_aus(y), od.o.a("u_production_od", y, "AUS")
            assert d.low <= c.low and d.central <= c.central and d.high <= c.high, \
                f"PREMISE BROKEN: u_production_od {y} = ({d.low:.1f}, {d.central:.1f}, {d.high:.1f}) exceeds C_AUS ({c.low:.1f}, {c.central:.1f}, {c.high:.1f})"

    def test_od_copper_not_above_aus_copper_at_central(self, od):
        df = pd.read_csv(ROOT / "data" / "activity" / "commodity_production.csv", dtype=str, keep_default_na=False)
        aus = {int(r["year"]): float(r["value_central"]) for r in df[(df["series"] == "prod_copper")
                                                                    & (df["country"] == "AUS")].to_dict("records")}
        checked = 0
        for y in YEARS:
            if y in aus:
                assert float(od.q_od[y]["value_central"]) <= aus[y], f"PREMISE BROKEN: prod_copper_od > prod_copper AUS in {y}"
                checked += 1
        assert checked > 20

    def test_value_share_in_unit_interval(self, od):
        for y, r in od.w_u.items():
            lo, c, hi = float(r["value_low"]), float(r["value_central"]), float(r["value_high"])
            assert 0.0 <= lo <= c <= hi <= 1.0, f"PREMISE BROKEN: od_value_share_u {y} = ({lo}, {c}, {hi}) outside [0, 1]"

    def test_metal_tailings_residue_type_exists(self, applied):
        rt = pd.read_csv(ROOT / "data" / "reference" / "residue_types.csv", dtype=str, keep_default_na=False)
        assert "metal_tailings" in set(rt.iloc[:, 0]), "PREMISE BROKEN: residue type metal_tailings"

    def test_baseline_snapshot_is_v12(self, baseline):
        n = sum(1 for r in baseline if is_aus_f6(r))
        assert n > 400, f"PREMISE BROKEN: only {n} AUS F6 rows in the v1.2 baseline snapshot"


# --------------------------------------------------------------------------------------------
# (c) carve-out of F6 for AUS
# --------------------------------------------------------------------------------------------
class TestF6Carveout:
    def test_aus_f6_rows_match_oracle(self, od, aus_f6):
        exp = od.f6_aus()
        assert exp, "oracle produced no AUS F6 rows"
        bad = []
        for k, er in exp.items():
            got = aus_f6.get((k[0], k[4]), [])
            if len(got) != 1:
                bad.append(f"{k[0]} {k[4]}: {len(got)} rows, expected 1")
                continue
            r = got[0]
            n = r["notes"]
            for name, g, w in zip(("low", "central", "high"), vals(r), (er.b.low, er.b.central, er.b.high)):
                if not close(g, w):
                    bad.append(f"{k[0]} {k[4]}: value_{name}={g!r}, oracle {w!r}")
            flagged = as_bool(r["below_detection"])
            if er.clipped:  # central > 0 with a clipped low (14.3)
                if flagged != er.b.nd:
                    bad.append(f"{k[0]} {k[4]}: below_detection={flagged}, oracle {er.b.nd} (clipped year)")
                if flagged and "clipped_difference" not in (cause_of(n) or []):
                    bad.append(f"{k[0]} {k[4]}: flagged clipped row lacks cause clipped_difference: {n[-120:]!r}")
            else:
                if flagged:
                    bad.append(f"{k[0]} {k[4]}: flagged but no clipping and no flagged input")
                if cause_of(n) is not None:
                    bad.append(f"{k[0]} {k[4]}: unflagged row carries a cause suffix")
            if (F6_FRAGMENT in n) != er.od_year:
                bad.append(f"{k[0]} {k[4]}: notes fragment present={F6_FRAGMENT in n}, expected {er.od_year}")
            if ids(r["factor_ids"]) != er.factor_ids:
                bad.append(f"{k[0]} {k[4]}: factor_ids {ids(r['factor_ids'])}, expected {er.factor_ids}")
            s = ids(r["source_ids"])
            if s != sorted(s) or not (er.src_req <= set(s) <= er.src_req | er.src_extra_ok):
                bad.append(f"{k[0]} {k[4]}: source_ids {s}, required {sorted(er.src_req)}")
            if r["allocation_rule"] != er.rule or r["allocation_variant"] != "default":
                bad.append(f"{k[0]} {k[4]}: rule/variant {r['allocation_rule']!r}/{r['allocation_variant']!r}")
            if driver_basis_of(n) != er.basis:
                bad.append(f"{k[0]} {k[4]}: driver basis {driver_basis_of(n)}, expected {er.basis}")
            if er.od_year and F6_FRAGMENT in n:
                pos = [n.index(F6_FRAGMENT)]
                for m in ("; driver basis:", "; below_detection cause:"):
                    if m in n:
                        if n.index(m) < pos[0]:
                            bad.append(f"{k[0]} {k[4]}: fragment must precede '{m}' (suffix order, 3.3)")
        unexpected = [kk for kk in aus_f6 if (kk[0], "fuel_cycle", "u_milling", "AUS", kk[1], "impounded", "flow", "",
                                                "u_tailings", "") not in exp]
        assert not bad, f"{len(bad)} problem(s) in AUS F6; first:\n  " + "\n  ".join(bad[:8])
        assert not unexpected, f"unexpected AUS F6 rows: {unexpected[:5]}"

    def test_f6_plus_od_tonnage_equals_v12_f6(self, od, aus_f6, baseline):
        """14.5(c): for AUS, F6 tonnage + P_OD x phi = the v1.2 F6 tonnage at central, relative 1e-5 (six-significant-figure stored values, D68) where no clipping."""
        base = {(int(r["year"]), r["group"]): r for r in baseline if is_aus_f6(r)}
        exp = od.f6_aus()
        n = 0
        bad = []
        for (y, g), rs in aus_f6.items():
            if y not in od.od_u or (y, g) not in base:
                continue
            er = exp[(y, "fuel_cycle", "u_milling", "AUS", g, "impounded", "flow", "", "u_tailings", "")]
            if er.clipped:
                continue
            f = od.o.select(y, "AUS", stage="u_milling", group=g, tier="impounded", route="", residue_type="u_tailings")
            Fc = float(f["value_central"])
            carve = od.o.a("u_production_od", y, "AUS").central * od.o.a("phi_civil", y, "XWL").central * Fc
            new_c = float(rs[0]["value_central"])
            old_c = float(base[(y, g)]["value_central"])
            n += 1
            if not math.isclose(new_c + carve, old_c, rel_tol=1e-5):
                bad.append(f"{y} {g}: new {new_c:.6e} + P_OD phi F {carve:.6e} != v1.2 {old_c:.6e}")
        assert n > 200, f"only {n} year-group cases checked"
        assert not bad, f"{len(bad)} carve-out mismatches; first:\n  " + "\n  ".join(bad[:6])

    def test_f6_before_1988_identical_to_v12_and_same_row_set(self, aus_f6, baseline):
        base = {(int(r["year"]), r["group"]): r for r in baseline if is_aus_f6(r)}
        assert set(aus_f6) == set(base), \
            f"AUS F6 (year, group) set differs from v1.2: +{sorted(set(aus_f6) - set(base))[:4]} -{sorted(set(base) - set(aus_f6))[:4]}"
        for (y, g), r in base.items():
            if y < 1988:
                n = aus_f6[(y, g)][0]
                for col in r:
                    nv = "" if n[col] is None else n[col]
                    if isinstance(nv, bool):
                        nv = "true" if nv else "false"
                    assert str(nv) == str(r[col]) or (col.startswith("value_") and close(float(n[col]), float(r[col]), 1e-5)), \
                        f"AUS F6 {y} {g} column {col}: {nv!r} != v1.2 {r[col]!r} (no OD carve-out before 1988)"

    def test_f6_aus_strictly_reduced_from_1988_when_od_positive(self, od, aus_f6, baseline):
        base = {(int(r["year"]), r["group"]): r for r in baseline if is_aus_f6(r)}
        for y in YEARS:
            g = "Ra226+"
            new, old = float(aus_f6[(y, g)][0]["value_central"]), float(base[(y, g)]["value_central"])
            assert new < old, f"AUS F6 {g} {y}: {new:.4e} not below v1.2 {old:.4e}; OD tonnage not carved out"

    def test_2023_total_reduction_about_1e14_bq_s5(self, aus_f6, baseline):
        """14.5(e): AUS F6 total falls in 2023 by about 1.06e14 Bq (S5 groups, order of magnitude only)."""
        base = {(int(r["year"]), r["group"]): float(r["value_central"]) for r in baseline if is_aus_f6(r)}
        groups = ("Ra226+", "Th230", "Pb210+", "Po210", "U238+", "U234", "U235+")
        drop = sum(base[(2023, g)] - float(aus_f6[(2023, g)][0]["value_central"]) for g in groups)
        assert 2e13 < drop < 5e14, f"2023 AUS F6 reduction {drop:.3e} Bq/a is not of the order 1e14 (spec about 1.06e14)"

    def test_no_clip_with_staged_series(self, od, aus_f6, log):
        od.f6_aus()
        assert not od.no_f6, f"PREMISE BROKEN: staged series clips in {sorted(od.no_f6)} (14.2: no year clips)"
        assert not [e for e in log if e.get("kind") == "negative_residual"], \
            "negative_residual logged although no AUS year clips"
        assert all(not as_bool(r["below_detection"]) for rs in aus_f6.values() for r in rs), \
            "an AUS F6 row is flagged although no year clips"


# --------------------------------------------------------------------------------------------
# F8 rows
# --------------------------------------------------------------------------------------------
def _need_f8(f8_rows):
    assert len(f8_rows) == 1140, f"F8 rows present for {len(f8_rows)} (year, group, variant) keys, expected 1140 (not implemented?)"


class TestF8Rows:
    def test_row_set_is_year_group_variant_complete(self, od, f8_rows):
        exp = od.f8()
        assert len(exp) == 38 * 10 * 3, f"oracle expects {len(exp)} F8 rows, 38 years x 10 groups x 3 variants = 1140"
        missing = [k for k in exp if k not in f8_rows]
        extra = [k for k in f8_rows if k not in exp]
        assert not missing, f"{len(missing)} F8 rows missing, first {missing[:4]}"
        assert not extra, f"{len(extra)} unexpected F8-type rows, first {extra[:4]}"
        dup = [k for k, v in f8_rows.items() if len(v) != 1]
        assert not dup, f"duplicate F8 keys {dup[:4]}"

    def test_group_set_excludes_pa231_and_ac227(self, f8_rows):
        groups = {k[1] for k in f8_rows}
        assert groups == set(OD_GROUPS), f"F8 groups {sorted(groups)}, expected {sorted(OD_GROUPS)} (14.4: Pa231 and Ac227+ absent)"

    def test_values_per_variant_match_oracle(self, od, f8_rows):
        _need_f8(f8_rows)
        bad = []
        for k, er in od.f8().items():
            rs = f8_rows.get(k)
            if not rs:
                continue
            r = rs[0]
            for name, g, w in zip(("low", "central", "high"), vals(r), (er.b.low, er.b.central, er.b.high)):
                if not close(g, w):
                    bad.append(f"{k}: value_{name}={g!r}, oracle {w!r}")
        assert not bad, f"{len(bad)} value mismatches; first:\n  " + "\n  ".join(bad[:8])

    def test_columns_and_constants(self, od, f8_rows):
        _need_f8(f8_rows)
        bad = []
        for k, er in od.f8().items():
            rs = f8_rows.get(k)
            if not rs:
                continue
            r = rs[0]
            want = {"stream": "nuclear", "substream": "fuel_cycle", "stage": "u_milling", "tier": "impounded",
                    "residue_type": "metal_tailings", "country": "AUS", "quantity": "flow", "unit": "Bq/a",
                    "basis": "modelled", "allocation_variant": k[2], "allocation_rule": er.rule}
            for c, w in want.items():
                if r[c] != w:
                    bad.append(f"{k}: {c}={r[c]!r}, expected {w!r}")
            for c in ("product", "technology", "route", "event_id"):
                if not blank(r[c]):
                    bad.append(f"{k}: {c}={r[c]!r}, expected empty")
            if as_bool(r["embedded_fuel"]):
                bad.append(f"{k}: embedded_fuel true")
        assert not bad, f"{len(bad)} column problems; first:\n  " + "\n  ".join(bad[:8])

    def test_allocation_rule_strings_by_variant(self):
        assert RULE == {"default": "civil:ratio;alloc:value", "bound_main": "civil:ratio;alloc:main",
                        "bound_radio": "civil:ratio;alloc:radio"}

    def test_factor_ids_and_source_ids(self, od, f8_rows):
        _need_f8(f8_rows)
        bad = []
        for k, er in od.f8().items():
            rs = f8_rows.get(k)
            if not rs:
                continue
            r = rs[0]
            if ids(r["factor_ids"]) != [er.factor_id]:
                bad.append(f"{k}: factor_ids {ids(r['factor_ids'])}, expected [{er.factor_id!r}]")
            s = ids(r["source_ids"])
            if s != sorted(er.src):
                bad.append(f"{k}: source_ids {s}, expected {sorted(er.src)} (factor's plus the three activity rows')")
        assert not bad, f"{len(bad)} id problems; first:\n  " + "\n  ".join(bad[:6])
        used = {ids(rs[0]["factor_ids"])[0] for rs in f8_rows.values()}
        assert used == set(OD_IDS), f"F8 uses factor ids {sorted(used)}, expected exactly commodity:0087-0096"

    def test_notes_text_flags_and_suffix_order(self, od, f8_rows):
        _need_f8(f8_rows)
        bad = []
        for k, er in od.f8().items():
            rs = f8_rows.get(k)
            if not rs:
                continue
            r = rs[0]
            n = r["notes"]
            head = f"F8: Olympic Dam pool, nuclear ledger (D74), D6 {k[2]}"
            if not n.startswith(head):
                bad.append(f"{k}: notes {n[:90]!r} do not start with {head!r}")
            if driver_basis_of(n) != er.basis:
                bad.append(f"{k}: driver basis {driver_basis_of(n)}, expected {er.basis}")
            flagged = as_bool(r["below_detection"])
            if flagged != er.b.nd:
                bad.append(f"{k}: below_detection={flagged}, oracle {er.b.nd}")
            if not flagged and cause_of(n) is not None:
                bad.append(f"{k}: unflagged row carries a cause suffix")
            if flagged and not cause_of(n):
                bad.append(f"{k}: flagged row without '; below_detection cause:'")
            if "; driver basis:" in n and "; below_detection cause:" in n and n.index("; driver basis:") > n.index("; below_detection cause:"):
                bad.append(f"{k}: suffix order wrong")
            if "civil share undocumented" in n:
                bad.append(f"{k}: civil-share flag does not apply to F8")
        assert not bad, f"{len(bad)} notes problems; first:\n  " + "\n  ".join(bad[:6])

    def test_bound_main_rows_are_structural_zeros(self, f8_rows):
        _need_f8(f8_rows)
        n = 0
        for (y, g, v), rs in f8_rows.items():
            if v == "bound_main":
                r = rs[0]
                assert vals(r) == (0.0, 0.0, 0.0), f"bound_main {y} {g} must be 0/0/0, got {vals(r)}"
                assert not as_bool(r["below_detection"]), f"bound_main {y} {g}: structural zero must be unflagged"
                assert cause_of(r["notes"]) is None, f"bound_main {y} {g}: unflagged zero carries a cause: {r['notes']!r}"
                n += 1
        assert n == 380

    def test_variant_ordering_x03(self, f8_rows):
        """X03: main <= default <= radio at central for every (year, group); radio >= default >= 0 at all bounds' centres."""
        for y in YEARS:
            for g in OD_GROUPS:
                m = float(f8_rows[(y, g, "bound_main")][0]["value_central"])
                d = float(f8_rows[(y, g, "default")][0]["value_central"])
                rd = float(f8_rows[(y, g, "bound_radio")][0]["value_central"])
                assert m <= d <= rd, f"{y} {g}: bound_main {m:.3e}, default {d:.3e}, bound_radio {rd:.3e} not ordered"
                assert d > 0 and rd > 0

    def test_default_is_value_share_of_bound_radio(self, od, f8_rows):
        """default central = w_U x bound_radio central (same phi, same pool) in every year."""
        for y in YEARS:
            w = float(od.w_u[y]["value_central"])
            for g in OD_GROUPS:
                d = float(f8_rows[(y, g, "default")][0]["value_central"])
                rd = float(f8_rows[(y, g, "bound_radio")][0]["value_central"])
                assert close(d, w * rd, 1e-9), f"{y} {g}: default {d:.6e} != w_U {w} x bound_radio {rd:.6e}"

    def test_unique_keys_across_whole_master(self, rows, f8_rows):
        _need_f8(f8_rows)
        c = Counter(full_key(r) for r in rows)
        dup = [k for k, v in c.items() if v > 1]
        assert not dup, f"{len(dup)} duplicate unique keys (variant included), first {dup[:2]}"

    def test_military_remainder_logged_per_year_and_variant(self, od, log):
        es = [e for e in log if e.get("kind") == "od_military_remainder"]
        got = defaultdict(list)
        for e in es:
            got[int(e["year"])].append(e)
            assert e.get("country") == "AUS" and e.get("group") in ("", None), f"country/group of {e}"
        want_years = sorted(y for y in YEARS if od.phi(y).central < 1.0)
        assert want_years, "PREMISE BROKEN: phi < 1 in 1988-90 expected"
        assert sorted(got) == want_years, f"od_military_remainder years {sorted(got)}, expected {want_years}"
        for y in want_years:
            d = sorted(str(e["detail"]).split(":")[0] for e in got[y])
            assert d == ["bound_radio", "default"], f"{y}: variants logged {d}, expected default and bound_radio (never bound_main)"
            for e in got[y]:
                v = str(e["detail"]).split(":")[0]
                m = re.fullmatch(r"(\w+): a_v\*\(1-phi\)=(\S+); Ra226\+ central (\S+)", str(e["detail"]))
                assert m, f"detail format {e['detail']!r}"
                av = od.share(y, v) * (1.0 - od.phi(y).central)
                assert math.isclose(float(m.group(2)), av, rel_tol=1e-5), f"{y} {v}: a_v(1-phi) {m.group(2)} vs {av:.6g}"
                assert math.isclose(float(m.group(3)), od.military(y, "Ra226+", v), rel_tol=1e-5), \
                    f"{y} {v}: Ra226+ central {m.group(3)} vs {od.military(y, 'Ra226+', v):.6g}"


# --------------------------------------------------------------------------------------------
# two-ledger closure
# --------------------------------------------------------------------------------------------
class TestTwoLedgerClosure:
    def test_f8_plus_copper_ledger_plus_military_equals_pool(self, od, f8_rows):
        bad, n, n_all = [], 0, 0
        for y in YEARS:
            phi = od.phi(y)
            equal_phi = phi.low == phi.central == phi.high
            for g in OD_GROUPS:
                P = od.pool(y, g)
                for v in VARIANTS:
                    r = f8_rows[(y, g, v)][0]
                    cu = od.copper_ledger(y, g, v)
                    mil = od.military(y, g, v)
                    tot_c = float(r["value_central"]) + cu.central + mil
                    n += 1
                    if not math.isclose(tot_c, P.central, rel_tol=CLOSE):
                        bad.append(f"{y} {g} {v}: F8 + copper + military = {tot_c:.6e}, pool {P.central:.6e} (central)")
                    if equal_phi:
                        n_all += 1
                        for name, got, cuv, pv in (("low", float(r["value_low"]), cu.low, P.low),
                                                   ("high", float(r["value_high"]), cu.high, P.high)):
                            milb = od.share(y, v) * (1.0 - phi.central) * pv
                            if not math.isclose(got + cuv + milb, pv, rel_tol=CLOSE):
                                bad.append(f"{y} {g} {v}: {name} closure {got + cuv + milb:.6e} != pool {pv:.6e}")
        assert n == 1140
        assert not bad, f"{len(bad)} closure failures; first:\n  " + "\n  ".join(bad[:6])

    def test_ledger_shares_sum_to_one_in_every_variant(self, od):
        for y in YEARS:
            w = float(od.w_u[y]["value_central"])
            assert 0.0 <= w <= 1.0
            assert math.isclose(w + (1 - w), 1.0)
            for g in ("Ra226+",):
                P = od.pool(y, g).central
                assert math.isclose(od.copper_ledger(y, g, "default").central + w * P, P, rel_tol=1e-12)
                assert od.copper_ledger(y, g, "bound_main").central == P
                assert od.copper_ledger(y, g, "bound_radio").central == 0.0

    def test_closure_uses_pool_from_files(self, od):
        """The pool is prod_copper_od x the OD factor (Bq/a), read from the files (not from any stream row)."""
        y, g = 2023, "Ra226+"
        q = float(od.q_od[y]["value_central"])
        f = float(od.factor(y, g)["value_central"])
        assert math.isclose(od.pool(y, g).central, q * f, rel_tol=1e-12)


# --------------------------------------------------------------------------------------------
# (f) hand cases (recomputed from the files)
# --------------------------------------------------------------------------------------------
class TestHandCases:
    def test_aus_2023_f6_ra226(self, od, aus_f6, baseline):
        y, g = 2023, "Ra226+"
        o = od.o
        P = float(o.arow("u_production", y, "AUS")["value_central"])
        s = float(o.select(y, "AUS", stage="u_mining_isl", group="", tier="", route="", residue_type="",
                           driver_series="")["value_central"])
        OD = float(o.arow("u_production_od", y, "AUS")["value_central"])
        phi = float(o.arow("phi_civil", y, "XWL")["value_central"])
        F = float(o.select(y, "AUS", stage="u_milling", group=g, tier="impounded", route="",
                           residue_type="u_tailings")["value_central"])
        want = (P * (1 - s) - OD) * phi * F
        r = aus_f6[(y, g)][0]
        assert math.isclose(float(r["value_central"]), want, rel_tol=1e-9), \
            f"AUS 2023 F6 Ra226+: {r['value_central']} vs ((P(1-s) - P_OD) phi F) = {want:.6e}"
        assert F6_FRAGMENT in r["notes"]
        old = float(next(b for b in baseline if is_aus_f6(b) and b["year"] == "2023" and b["group"] == g)["value_central"])
        assert math.isclose(old - float(r["value_central"]), OD * phi * F, rel_tol=1e-5), \
            "2023 reduction must equal P_OD x phi x F (relative 1e-5 on the six-digit committed value)"
        assert not as_bool(r["below_detection"])

    @pytest.mark.parametrize("variant,share", [("default", None), ("bound_main", 0.0), ("bound_radio", 1.0)])
    def test_f8_2023_ra226(self, od, f8_rows, variant, share):
        y, g = 2023, "Ra226+"
        Q = float(od.q_od[y]["value_central"])
        F = float(od.factor(y, g)["value_central"])
        phi = float(od.o.arow("phi_civil", y, "XWL")["value_central"])
        a = float(od.w_u[y]["value_central"]) if share is None else share
        r = f8_rows[(y, g, variant)][0]
        assert math.isclose(float(r["value_central"]), Q * F * a * phi, rel_tol=1e-9, abs_tol=0.0) or (a == 0 and float(r["value_central"]) == 0), \
            f"F8 Ra226+ 2023 {variant}: {r['value_central']} vs Q F a phi = {Q * F * a * phi:.6e}"
        assert r["allocation_rule"] == RULE[variant]
        assert ids(r["factor_ids"]) == ["commodity:0094"]
        assert r["notes"].startswith(f"F8: Olympic Dam pool, nuclear ledger (D74), D6 {variant}")

    def test_f8_2023_default_s5_total_of_order_3e13(self, od, f8_rows):
        """14.5(e): 2023 default about 3.5e13 Bq S5 [I]; order of magnitude over the S5 groups only."""
        s5 = ("Ra226+", "Th230", "Pb210+", "Po210", "U238+", "U234", "U235+")
        tot = sum(float(f8_rows[(2023, g, "default")][0]["value_central"]) for g in s5)
        assert 5e12 < tot < 2e14, f"2023 default F8 S5 total {tot:.3e} Bq/a, spec about 3.5e13"


# --------------------------------------------------------------------------------------------
# F1-F5, F7 and everything else unchanged
# --------------------------------------------------------------------------------------------
class TestUnchanged:
    @pytest.fixture(scope="class")
    def written(self, result, tmp_path_factory):
        write_master = importlib.import_module("pipeline.lib.rows").write_master
        d = tmp_path_factory.mktemp("od_written")
        main, pre = d / "nuclear.csv", d / "nuclear_pre1950.csv"
        write_master(list(result.rows), main)
        write_master(list(result.rows_pre1950), pre)
        return main, pre

    def test_all_other_rows_identical_to_v12(self, written, baseline):
        new = {full_key(r): r for r in read_csv(written[0])}
        old = {full_key(r): r for r in baseline}
        diffs, missing = [], []
        for k, r in old.items():
            if is_aus_f6(r):
                continue
            n = new.get(k)
            if n is None:
                missing.append(k)
                continue
            if n != r:
                cols = [c for c in r if n.get(c) != r[c]]
                diffs.append(f"{k}: columns {cols}")
        assert not missing, f"{len(missing)} v1.2 rows no longer written (outside AUS F6), first {missing[:3]}"
        assert not diffs, f"{len(diffs)} v1.2 rows changed (outside AUS F6), first:\n  " + "\n  ".join(diffs[:5])

    def test_only_f8_rows_are_new(self, written, baseline):
        new = read_csv(written[0])
        old = {full_key(r) for r in baseline}
        added = [r for r in new if full_key(r) not in old]
        assert len(added) == 1140, f"{len(added)} rows not in v1.2, expected exactly the 1140 F8 rows"
        assert all(is_f8(r) for r in added), f"a non-F8 row is new: {desc(next(r for r in added if not is_f8(r)))}"
        assert len(new) == len(baseline) + 1140

    def test_f1_to_f5_f7_aus_rows_unchanged(self, written, baseline):
        new = {full_key(r): r for r in read_csv(written[0])}
        n = 0
        for r in baseline:
            if r["country"] != "AUS" or r["stage"] not in ("u_mining_conv", "u_mining_isl", "u_milling"):
                continue
            if is_aus_f6(r):
                continue
            assert new[full_key(r)] == r, f"AUS row changed although §14.3 leaves it unchanged: {desc(r)}"
            n += 1
        assert n > 500, f"only {n} AUS F1-F5 rows compared"

    def test_pre1950_unchanged(self, written):
        old = read_gz(BASE / "nuclear_pre1950_v12.csv.gz")
        new = read_csv(written[1])
        assert new == old, "the pre-1950 file must not change (section 14 touches 1988-2025 only)"


# --------------------------------------------------------------------------------------------
# committed stream (after the rebuild)
# --------------------------------------------------------------------------------------------
class TestCommittedStream:
    def test_committed_stream_contains_f8_and_carve_out(self, applied):
        rws = read_gz(ROOT / "data" / "streams" / "nuclear.csv.gz")
        f8 = [r for r in rws if is_f8(r)]
        assert len(f8) == 1140, f"data/streams/nuclear.csv.gz has {len(f8)} F8 rows: the stream was not rebuilt after D74 (expected 1140)"
        assert any(F6_FRAGMENT in r["notes"] for r in rws if is_aus_f6(r)), "committed AUS F6 rows lack the carve-out notes"

    def test_committed_stream_matches_fresh_build(self, applied, result, tmp_path):
        write_master = importlib.import_module("pipeline.lib.rows").write_master
        p = tmp_path / "n.csv"
        write_master(list(result.rows), p)
        new = read_csv(p)
        old = read_gz(ROOT / "data" / "streams" / "nuclear.csv.gz")
        assert len(new) == len(old), f"committed stream has {len(old)} rows, a fresh build gives {len(new)}"
        assert new == old, "committed data/streams/nuclear.csv.gz differs from a fresh build"


# --------------------------------------------------------------------------------------------
# (g) fixtures: miniature trees
# --------------------------------------------------------------------------------------------
ACT_COLUMNS = ["series", "year", "country", "value_low", "value_central", "value_high", "unit",
               "below_detection", "basis", "source_ids", "notes"]
MINI_YEARS = [2005, 2006, 2007]


def _a(series, y, c, central, unit, band=0.1, basis="compiled", src="S0113"):
    return {"series": series, "year": y, "country": c, "value_low": central * (1 - band), "value_central": central,
            "value_high": central * (1 + band), "unit": unit, "below_detection": "false", "basis": basis,
            "source_ids": src, "notes": ""}


def _write(path: Path, rws: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=ACT_COLUMNS)
        w.writeheader()
        w.writerows(rws)


def make_od_mini(tmp_path: Path, *, od_u=None, q=None, phi=None, drop_cf=False, w_band=0.0, name="od_mini") -> Path:
    """AUS-only tree, 2005-2007. od_u / q: year -> central (None entry = absent series)."""
    od_u = {2005: 300.0, 2006: 999.0, 2007: 940.0} if od_u is None else od_u
    q = {y: 50000.0 for y in MINI_YEARS} if q is None else q
    phi = {2005: 1.0, 2006: 1.0, 2007: 0.9} if phi is None else phi
    root = tmp_path / name
    shutil.copytree(ROOT / "data" / "reference", root / "data" / "reference")
    shutil.copy(ROOT / "data" / "sources.csv", root / "data" / "sources.csv")
    if drop_cf:
        (root / "data" / "reference" / "commodity_factors.csv").unlink()
    ur = []
    for y in MINI_YEARS:
        ur.append(_a("phi_civil", y, "XWL", phi[y], "1", band=0.0))
        ur.append(_a("u_production", y, "AUS", 1000.0, "t"))
        ur.append(_a("u_production", y, "XWL", 1000.0, "t", band=0.02))
    ur += [_a("u_production_od", y, "AUS", v, "t", band=0.05 if y == 2007 else 0.1, basis="modelled", src="S0407") for y, v in od_u.items()]
    _write(root / "data" / "activity" / "uranium.csv", ur)
    _write(root / "data" / "activity" / "commodity_production.csv",
           [_a("prod_copper_od", y, "AUS", v, "t", band=0.1, basis="modelled", src="S0407") for y, v in q.items()])
    _write(root / "data" / "activity" / "wind_solar_shares.csv",
           [_a("od_value_share_u", y, "AUS", 0.12, "1", band=w_band, basis="modelled", src="S0407") for y in MINI_YEARS])
    for fname in ("electricity_generation.csv", "nuclear.csv", "nuclear_cycle.csv"):
        _write(root / "data" / "activity" / fname, [])
    (root / "data" / "factors").mkdir(parents=True)
    shutil.copy(ROOT / "data" / "factors" / "nuclear.csv", root / "data" / "factors" / "nuclear.csv")
    shutil.copy(ROOT / "data" / "events.csv", root / "data" / "events.csv")
    return root


def build_od_mini(mod, tmp_path, **kw):
    root = make_od_mini(tmp_path, **kw)
    res = mod.build(root)
    return root, list(res.rows), list(res.log)


def _f6(rows):
    d = defaultdict(list)
    for r in rows:
        if is_aus_f6(r):
            d[(int(r["year"]), r["group"])].append(r)
    return d


def _f8(rows):
    d = defaultdict(list)
    for r in rows:
        if is_f8(r):
            d[(int(r["year"]), r["group"], r["allocation_variant"])].append(r)
    return d


class TestMiniFixtures:
    def test_clip_rule_negative_zero_and_clipped_low(self, nuclear_mod, tmp_path):
        """2005 normal; 2006 raw central < 0 (no rows, one negative_residual); 2007 central > 0 with a clipped low
        (row written, flagged clipped_difference)."""
        root, rows, log = build_od_mini(nuclear_mod, tmp_path)
        odo = ODOracle(root)
        exp = odo.f6_aus()
        assert sorted(odo.no_f6) == [2006] and odo.no_f6[2006] < 0, f"fixture premise: {odo.no_f6}"
        f6 = _f6(rows)
        assert not [k for k in f6 if k[0] == 2006], "2006: raw central < 0 must write no F6 rows (any group)"
        for k, er in exp.items():
            y, g = k[0], k[4]
            got = f6.get((y, g))
            assert got and len(got) == 1, f"mini AUS F6 {y} {g}: {0 if not got else len(got)} rows"
            for name, a, b in zip(("low", "central", "high"), vals(got[0]), (er.b.low, er.b.central, er.b.high)):
                assert close(a, b), f"mini AUS F6 {y} {g} value_{name} {a!r}, oracle {b!r}"
            assert as_bool(got[0]["below_detection"]) == er.b.nd, f"mini AUS F6 {y} {g} flag"
            assert F6_FRAGMENT in got[0]["notes"]
        assert exp[(2007, "fuel_cycle", "u_milling", "AUS", "Ra226+", "impounded", "flow", "", "u_tailings", "")].clipped, \
            "fixture premise: the 2007 OD low (band 5 percent) must clip the correlated-difference low"
        r = f6[(2007, "Ra226+")][0]
        assert float(r["value_central"]) > 0 and float(r["value_low"]) == 0, "2007: central > 0 with clipped low"
        assert as_bool(r["below_detection"]) and "clipped_difference" in (cause_of(r["notes"]) or []), r["notes"]
        assert not as_bool(f6[(2005, "Ra226+")][0]["below_detection"])
        es = [e for e in log if e.get("kind") == "negative_residual"]
        assert len(es) == 1, f"expected exactly one negative_residual entry (per year, not per group): {es}"
        e = es[0]
        assert int(e["year"]) == 2006 and e["country"] == "AUS" and e["group"] in ("", None), e
        m = re.fullmatch(r"u_production_od: conventional AUS minus OD = (\S+) t U; no F6 rows", str(e["detail"]))
        assert m, f"negative_residual detail format: {e['detail']!r}"
        assert math.isclose(float(m.group(1)), odo.no_f6[2006], rel_tol=1e-5), f"{m.group(1)} vs {odo.no_f6[2006]:.6g}"
        # F8 is still written in the year without F6 rows (the pool does not depend on the conventional tonnage)
        assert len(_f8(rows)) == 3 * 10 * 3

    def test_central_exactly_zero_writes_nothing_and_logs_nothing(self, nuclear_mod, tmp_path):
        probe = ODOracle(make_od_mini(tmp_path, name="probe"))
        c0 = probe.conv_aus(2005).central
        root, rows, log = build_od_mini(nuclear_mod, tmp_path, od_u={2005: c0, 2006: 300.0, 2007: 300.0}, name="zero")
        odo = ODOracle(root)
        odo.f6_aus()
        assert odo.no_f6.get(2005) == 0.0, f"fixture premise: raw central {odo.no_f6.get(2005)}"
        assert not [k for k in _f6(rows) if k[0] == 2005], "raw central exactly 0 must write no F6 rows"
        assert [k for k in _f6(rows) if k[0] == 2006], "other years unaffected"
        assert not [e for e in log if e.get("kind") == "negative_residual"], "raw central exactly 0 must not be logged"

    def test_exact_phi_closure_at_low_central_high(self, nuclear_mod, tmp_path):
        root, rows, log = build_od_mini(nuclear_mod, tmp_path)
        odo = ODOracle(root)
        f8 = _f8(rows)
        bad = []
        for y in MINI_YEARS:
            phi = odo.phi(y)
            assert phi.low == phi.central == phi.high
            for g in OD_GROUPS:
                P = odo.pool(y, g)
                for v in VARIANTS:
                    r = f8[(y, g, v)][0]
                    cu = odo.copper_ledger(y, g, v)
                    a = odo.share(y, v)
                    for name, got, cuv, pv in (("low", float(r["value_low"]), cu.low, P.low),
                                               ("central", float(r["value_central"]), cu.central, P.central),
                                               ("high", float(r["value_high"]), cu.high, P.high)):
                        mil = a * (1.0 - phi.central) * pv
                        if not math.isclose(got + cuv + mil, pv, rel_tol=CLOSE):
                            bad.append(f"{y} {g} {v} {name}: {got + cuv + mil:.6e} != {pv:.6e}")
        assert not bad, f"{len(bad)} closure failures; first {bad[:5]}"
        want_years = sorted(y for y in MINI_YEARS if odo.phi(y).central < 1.0)
        got = sorted((int(e["year"]), str(e["detail"]).split(":")[0]) for e in log if e.get("kind") == "od_military_remainder")
        assert want_years == [2007] and got == [(2007, "bound_radio"), (2007, "default")], \
            f"od_military_remainder (year, variant) {got}, expected 2007 default and bound_radio only"

    def test_banded_share_uses_central_exactly(self, nuclear_mod, tmp_path):
        root, rows, _ = build_od_mini(nuclear_mod, tmp_path, w_band=0.5, name="banded")
        odo = ODOracle(root)
        for y in MINI_YEARS:
            r = odo.w_u[y]
            assert float(r["value_low"]) < float(r["value_central"]) < float(r["value_high"]), "fixture premise: banded share"
        f8 = _f8(rows)
        for y in MINI_YEARS:
            w = float(odo.w_u[y]["value_central"])
            phi = odo.phi(y)
            for g in OD_GROUPS:
                P = odo.pool(y, g)
                d, rd = f8[(y, g, "default")][0], f8[(y, g, "bound_radio")][0]
                for name, got, ref in (("low", float(d["value_low"]), P.low * phi.central),
                                       ("central", float(d["value_central"]), P.central * phi.central),
                                       ("high", float(d["value_high"]), P.high * phi.central)):
                    assert math.isclose(got, w * ref, rel_tol=1e-9), \
                        f"{y} {g} default {name}: {got:.6e}, expected central share {w} x {ref:.6e}; the share bounds must not be used"
                assert math.isclose(float(d["value_central"]), w * float(rd["value_central"]), rel_tol=1e-9)
        # the copper ledger identity still closes with the central share
        for y in MINI_YEARS:
            for g in ("Ra226+",):
                r = f8[(y, g, "default")][0]
                P = odo.pool(y, g)
                tot = float(r["value_central"]) + odo.copper_ledger(y, g, "default").central + odo.military(y, g, "default")
                assert math.isclose(tot, P.central, rel_tol=CLOSE)

    def test_f8_values_match_oracle_in_mini(self, nuclear_mod, tmp_path):
        root, rows, _ = build_od_mini(nuclear_mod, tmp_path)
        f8 = _f8(rows)
        for k, er in ODOracle(root).f8().items():
            got = f8.get(k)
            assert got and len(got) == 1, f"mini F8 {k} missing"
            for name, a, b in zip(("low", "central", "high"), vals(got[0]), (er.b.low, er.b.central, er.b.high)):
                assert close(a, b), f"mini F8 {k} value_{name} {a!r}, oracle {b!r}"

    def test_absent_od_series_gives_v12_f6_no_f8_and_no_driver(self, nuclear_mod, tmp_path):
        _, _, base_log = build_od_mini(nuclear_mod, tmp_path, name="with_od")
        root, rows, log = build_od_mini(nuclear_mod, tmp_path, od_u={}, q={}, name="no_od")
        assert not [r for r in rows if is_f8(r)], "F8 rows written although prod_copper_od is absent"
        odo = ODOracle(root)
        assert not odo.od_u
        f6 = _f6(rows)
        for k, er in odo.f6_aus().items():  # no OD series: the oracle gives the v1.2 rule
            got = f6[(k[0], k[4])][0]
            for name, a, b in zip(("low", "central", "high"), vals(got), (er.b.low, er.b.central, er.b.high)):
                assert close(a, b), f"F6 as v1.2 expected without u_production_od: {k[0]} {k[4]} value_{name} {a!r} vs {b!r}"
            assert F6_FRAGMENT not in got["notes"], "no carve-out fragment without u_production_od"
        n_no = sum(1 for e in log if e["kind"] == "no_driver")
        n_with = sum(1 for e in base_log if e["kind"] == "no_driver")
        assert n_no > n_with, f"absent OD series must log no_driver (aggregated): {n_no} entries vs {n_with} with the series"

    def test_absent_commodity_factors_gives_no_family_and_no_f8(self, nuclear_mod, tmp_path):
        _, base_rows, base_log = build_od_mini(nuclear_mod, tmp_path, name="with_cf")
        root, rows, log = build_od_mini(nuclear_mod, tmp_path, drop_cf=True, name="no_cf")
        assert not [r for r in rows if is_f8(r)], "F8 rows written without commodity_factors.csv"
        n_no = len([e for e in log if e["kind"] == "no_family"])
        n_with = len([e for e in base_log if e["kind"] == "no_family"])
        assert n_no == n_with + 1, f"absent commodity_factors.csv must add exactly one no_family entry: {n_no} vs {n_with}"
        # the carve-out of F6 still applies (it needs u_production_od only)
        r = _f6(rows)[(2005, "Ra226+")][0]
        assert F6_FRAGMENT in r["notes"]
