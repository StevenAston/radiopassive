"""Spec-blind tests for LIB_SPEC section 12 (v1.6, D74): the `ore_type` match key of factors.select,
and read_table reading the `ore_type` column as a string. Items T1-T12 of section 12.1.

T12 (regression) is covered by running the rest of pipeline/tests/lib unchanged; one smoke test
here pins that a substream-keyed call still behaves as in v1.4/v1.5.
"""
from __future__ import annotations

import pytest

from pipeline.lib import LibError
from pipeline.lib import factors as factors_mod
from pipeline.lib.factors import select
from pipeline.lib.io import read_table


def crow(**over):
    row = {
        "factor_id": "commodity:0001", "commodity": "copper", "component": "own_residue",
        "group": "Ra226+", "tier": "impounded", "route": None, "residue_type": "metal_tailings",
        "region": "XWL", "ore_type": "porphyry_stratiform", "year_from": 1950, "year_to": 2025,
        "allocation_variant": "default", "allocation_rule": ["alloc:value"],
        "value_low": 1.0, "value_central": 2.0, "value_high": 3.0, "unit": "Bq/t",
        "below_detection": False, "basis": "compiled", "source_ids": ["S0003"], "notes": None,
    }
    row.update(over)
    return row


KEYS = dict(commodity="copper", component="own_residue", group="Ra226+", tier="impounded",
            residue_type="metal_tailings")


def sel(rows, year=2000, region="XWL", **kw):
    return select(rows, year=year, region=region, **{**KEYS, **kw})


A = crow(factor_id="commodity:0001", ore_type="porphyry_stratiform")
B = crow(factor_id="commodity:0002", ore_type="iocg_high_u")
C = crow(factor_id="commodity:0003", ore_type="")
D = crow(factor_id="commodity:0004", ore_type="all")


# ------------------------------------------------------------------ T1
def test_t1_exact_match_returns_each_row():
    assert sel([A, B], ore_type="porphyry_stratiform") == A
    assert sel([A, B], ore_type="iocg_high_u") == B
    assert sel([B, A], ore_type="iocg_high_u") == B  # order independent


def test_t1_row_is_returned_unchanged_including_factor_id():
    got = sel([A, B], ore_type="iocg_high_u")
    assert got["factor_id"] == "commodity:0002" and got == B


def test_t1_exact_is_not_prefix_or_case_insensitive():
    for bad in ("porphyry", "Porphyry_Stratiform", "porphyry_stratiform ", "iocg"):
        with pytest.raises(LibError, match="^no factor row"):
            sel([A, B], ore_type=bad)


# ------------------------------------------------------------------ T2
def test_t2_empty_call_matches_empty_row():
    assert sel([A, B, C], ore_type="") == C


def test_t2_named_call_never_returns_empty_row():
    assert sel([A, B, C], ore_type="porphyry_stratiform") == A
    with pytest.raises(LibError, match="^no factor row"):
        sel([C], ore_type="porphyry_stratiform")


# ------------------------------------------------------------------ T3
def test_t3_no_wildcard_empty_call_against_named_rows():
    with pytest.raises(LibError) as e:
        sel([A, B], ore_type="")
    assert str(e.value).startswith("no factor row"), str(e.value)


def test_t3_unlisted_ore_type_raises_no_factor_row():
    with pytest.raises(LibError) as e:
        sel([A, B], ore_type="cu_co_stratiform")
    assert str(e.value).startswith("no factor row"), str(e.value)


# ------------------------------------------------------------------ T4
def test_t4_all_is_a_literal():
    assert sel([A, D], ore_type="all") == D
    assert sel([A, D], ore_type="porphyry_stratiform") == A


def test_t4_all_is_not_a_wildcard():
    with pytest.raises(LibError, match="^no factor row"):
        sel([A, B], ore_type="all")
    with pytest.raises(LibError, match="^no factor row"):
        sel([D], ore_type="porphyry_stratiform")


# ------------------------------------------------------------------ T5
def test_t5_omitted_key_with_two_ore_types_is_ambiguous():
    with pytest.raises(LibError) as e:
        sel([A, B])
    assert str(e.value).startswith("ambiguous factor rows"), str(e.value)


def test_t5_omitted_key_with_single_row_returns_it():
    assert sel([A]) == A


def test_t5_omitted_key_returns_row_whatever_its_ore_type():
    assert sel([D]) == D
    assert sel([C]) == C


# ------------------------------------------------------------------ T6
def test_t6_exact_region_beats_xwl_within_same_ore_type():
    e = crow(factor_id="commodity:0010", ore_type="iocg_olympic_dam", region="AUS")
    f = crow(factor_id="commodity:0011", ore_type="iocg_olympic_dam", region="XWL")
    assert sel([e, f], region="AUS", ore_type="iocg_olympic_dam") == e
    assert sel([f, e], region="AUS", ore_type="iocg_olympic_dam") == e
    assert sel([e, f], region="CHN", ore_type="iocg_olympic_dam") == f


def test_t6_ore_type_filters_before_region_precedence():
    g = crow(factor_id="commodity:0012", ore_type="iocg_high_u", region="AUS")
    h = crow(factor_id="commodity:0013", ore_type="porphyry_stratiform", region="XWL")
    assert sel([g, h], region="AUS", ore_type="porphyry_stratiform") == h
    assert sel([h, g], region="AUS", ore_type="porphyry_stratiform") == h
    assert sel([g, h], region="AUS", ore_type="iocg_high_u") == g


# ------------------------------------------------------------------ T7
def test_t7_ambiguity_at_exact_region_level():
    x = crow(factor_id="commodity:0020", ore_type="iocg_high_u", region="AUS")
    y = crow(factor_id="commodity:0021", ore_type="iocg_high_u", region="AUS")
    with pytest.raises(LibError) as e:
        sel([x, y], region="AUS", ore_type="iocg_high_u")
    assert str(e.value).startswith("ambiguous factor rows"), str(e.value)


def test_t7_ambiguity_at_xwl_level():
    x = crow(factor_id="commodity:0020", ore_type="all")
    y = crow(factor_id="commodity:0021", ore_type="all")
    with pytest.raises(LibError) as e:
        sel([x, y], region="CHN", ore_type="all")
    assert str(e.value).startswith("ambiguous factor rows"), str(e.value)


def test_t7_ambiguity_not_raised_when_ore_types_differ_and_key_given():
    assert sel([A, B], ore_type="iocg_high_u") == B  # would be ambiguous without the key


# ------------------------------------------------------------------ T8
def test_t8_window_combines_with_ore_type():
    od = crow(factor_id="commodity:0030", ore_type="iocg_olympic_dam", region="AUS",
              year_from=1988, year_to=2025)
    with pytest.raises(LibError, match="^no factor row"):
        sel([od], year=1987, region="AUS", ore_type="iocg_olympic_dam")
    assert sel([od], year=1988, region="AUS", ore_type="iocg_olympic_dam") == od
    assert sel([od], year=2025, region="AUS", ore_type="iocg_olympic_dam") == od
    with pytest.raises(LibError, match="^no factor row"):
        sel([od], year=2026, region="AUS", ore_type="iocg_olympic_dam")


def test_t8_other_ore_type_in_window_does_not_rescue_out_of_window_row():
    od = crow(factor_id="commodity:0030", ore_type="iocg_olympic_dam", region="AUS",
              year_from=1988, year_to=2025)
    ph = crow(factor_id="commodity:0031", ore_type="iocg_high_u", region="AUS",
              year_from=2009, year_to=2018)
    with pytest.raises(LibError, match="^no factor row"):
        sel([od, ph], year=1987, region="AUS", ore_type="iocg_olympic_dam")
    assert sel([od, ph], year=2010, region="AUS", ore_type="iocg_high_u") == ph


# ------------------------------------------------------------------ T9
HEADER = ("factor_id,commodity,component,group,tier,route,residue_type,region,ore_type,year_from,"
          "year_to,allocation_variant,allocation_rule,value_low,value_central,value_high,unit,"
          "below_detection,basis,source_ids,notes")


def line(fid, ore):
    return (f"{fid},copper,own_residue,Ra226+,impounded,,metal_tailings,XWL,{ore},1950,2025,"
            "default,alloc:value,1,2,3,Bq/t,false,compiled,S0003,")


def write(tmp_path, *lines):
    d = tmp_path / "reference"
    d.mkdir()
    p = d / "commodity_factors.csv"
    p.write_text(HEADER + "\n" + "\n".join(lines) + "\n", encoding="utf-8")
    return p


def test_t9_read_table_ore_type_empty_and_padded(tmp_path):
    p = write(tmp_path, line("commodity:0001", ""), line("commodity:0002", "  iocg_high_u  "))
    rows = read_table(p)
    assert rows[0]["ore_type"] == "" and isinstance(rows[0]["ore_type"], str), repr(rows[0]["ore_type"])
    assert rows[0]["ore_type"] is not None
    assert rows[1]["ore_type"] == "iocg_high_u", repr(rows[1]["ore_type"])
    assert rows[0]["route"] is None and rows[0]["notes"] is None  # other empty cells unchanged


def test_t9_read_table_factor_id_is_kept(tmp_path):
    rows = read_table(write(tmp_path, line("commodity:0007", "all")))
    assert rows[0]["factor_id"] == "commodity:0007"


def test_t9_read_table_then_select_roundtrip(tmp_path):
    rows = read_table(write(tmp_path, line("commodity:0001", ""), line("commodity:0002", " all ")))
    assert sel(rows, ore_type="")["factor_id"] == "commodity:0001"
    assert sel(rows, ore_type="all")["factor_id"] == "commodity:0002"
    with pytest.raises(LibError, match="^ambiguous factor rows"):
        sel(rows)


# ------------------------------------------------------------------ T10
def test_t10_row_without_ore_type_key_matches_empty_only():
    r = crow(factor_id="commodity:0040")
    del r["ore_type"]
    assert sel([r], ore_type="") == r
    assert sel([r]) == r
    with pytest.raises(LibError, match="^no factor row"):
        sel([r], ore_type="all")
    with pytest.raises(LibError, match="^no factor row"):
        sel([r], ore_type="porphyry_stratiform")


# ------------------------------------------------------------------ T11
def test_t11_ore_type_in_match_keys():
    assert hasattr(factors_mod, "MATCH_KEYS"), "pipeline.lib.factors.MATCH_KEYS not found"
    assert "ore_type" in factors_mod.MATCH_KEYS
    assert "substream" in factors_mod.MATCH_KEYS  # v1.4 key kept


def test_t11_unknown_key_still_rejected_and_lists_ore_type():
    with pytest.raises(LibError) as e:
        sel([A], oretype="porphyry_stratiform")
    msg = str(e.value)
    assert "unknown match key(s)" in msg, msg
    assert "ore_type" in msg, f"allowed-key list must name ore_type: {msg}"


# ------------------------------------------------------------------ T12 smoke
def test_t12_substream_key_unchanged():
    a = crow(factor_id="commodity:0050", ore_type="", **{"substream": "conventional"})
    b = crow(factor_id="commodity:0051", ore_type="", **{"substream": "oil_sands"})
    assert sel([a, b], substream="oil_sands", ore_type="") == b
    with pytest.raises(LibError, match="^ambiguous factor rows"):
        sel([a, b])
