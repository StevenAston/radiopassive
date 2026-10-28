"""Spec-blind tests for LIB_SPEC section 10 (v1.4): the `substream` match key of factors.select,
and read_table reading the factor-file `substream` column as a string."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from pipeline.lib import LibError
from pipeline.lib.factors import select
from pipeline.lib.io import read_table

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def frow(**over):
    row = {
        "factor_id": "oil_gas:0001", "description": "d", "stream": "oil_gas", "stage": "production",
        "substream": "", "driver_series": "oil_gas_prod", "group": "Ra226+", "tier": None,
        "route": None, "residue_type": None, "region": "CHN", "year_from": 1990, "year_to": 2020,
        "value_low": 1.0, "value_central": 2.0, "value_high": 3.0, "unit": "Bq/m3",
        "below_detection": False, "basis": "compiled", "source_ids": ["S0003"], "notes": None,
    }
    row.update(over)
    return row


def three(region="CHN"):
    conv = frow(factor_id="oil_gas:0001", substream="conventional", region=region)
    unconv = frow(factor_id="oil_gas:0002", substream="unconventional", region=region)
    sands = frow(factor_id="oil_gas:0003", substream="oil_sands", region=region)
    return conv, unconv, sands


# ------------------------------------------------------------------ match
def test_substream_selects_matching_row():
    conv, unconv, sands = three()
    for want in (conv, unconv, sands):
        assert select([conv, unconv, sands], year=2000, region="CHN", substream=want["substream"]) == want


def test_substream_order_independent():
    conv, unconv, sands = three()
    assert select([sands, unconv, conv], year=2000, region="CHN", substream="conventional") == conv


def test_substream_mismatch_raises():
    conv, _, _ = three()
    with pytest.raises(LibError):
        select([conv], year=2000, region="CHN", substream="oil_sands")


def test_substream_is_exact_not_prefix_or_case_insensitive():
    conv, _, _ = three()
    for bad in ("conv", "Conventional", "conventional ", "unconventional"):
        with pytest.raises(LibError):
            select([conv], year=2000, region="CHN", substream=bad)


# ------------------------------------------------------------------ empty cells: no wildcard
def test_empty_row_substream_does_not_match_named_substream():
    generic = frow(substream="")
    with pytest.raises(LibError):
        select([generic], year=2000, region="CHN", substream="conventional")


def test_empty_row_matches_empty_string_call():
    generic = frow(substream="")
    assert select([generic], year=2000, region="CHN", substream="") == generic


def test_empty_string_call_does_not_match_named_row():
    conv, _, _ = three()
    with pytest.raises(LibError):
        select([conv], year=2000, region="CHN", substream="")


def test_empty_string_call_picks_empty_row_among_named():
    conv, unconv, _ = three()
    generic = frow(factor_id="oil_gas:0009", substream="")
    assert select([conv, generic, unconv], year=2000, region="CHN", substream="") == generic


def test_named_call_ignores_empty_row_even_when_named_present():
    conv, _, _ = three()
    generic = frow(factor_id="oil_gas:0009", substream="")
    assert select([generic, conv], year=2000, region="CHN", substream="conventional") == conv


# ------------------------------------------------------------------ calls without substream unaffected
def test_call_without_substream_single_row_any_substream():
    conv, _, _ = three()
    assert select([conv], year=2000, region="CHN") == conv
    generic = frow(substream="")
    assert select([generic], year=2000, region="CHN") == generic


def test_call_without_substream_ambiguous_when_rows_differ_only_by_substream():
    conv, unconv, _ = three()
    with pytest.raises(LibError):
        select([conv, unconv], year=2000, region="CHN")


def test_call_without_substream_still_filters_other_keys():
    conv, unconv, _ = three()
    other = frow(factor_id="oil_gas:0007", substream="conventional", group="Ra228+")
    assert select([other, unconv], year=2000, region="CHN", group="Ra228+") == other


# ------------------------------------------------------------------ precedence and ambiguity
def test_exact_region_beats_xwl_with_substream():
    exact = frow(factor_id="oil_gas:0010", substream="oil_sands", region="CHN")
    world = frow(factor_id="oil_gas:0011", substream="oil_sands", region="XWL")
    assert select([world, exact], year=2000, region="CHN", substream="oil_sands") == exact
    assert select([exact, world], year=2000, region="CHN", substream="oil_sands") == exact


def test_xwl_fallback_with_substream():
    world = frow(substream="oil_sands", region="XWL")
    assert select([world], year=2000, region="CHN", substream="oil_sands") == world


def test_exact_region_with_other_substream_does_not_block_xwl():
    exact_other = frow(factor_id="oil_gas:0010", substream="conventional", region="CHN")
    world = frow(factor_id="oil_gas:0011", substream="oil_sands", region="XWL")
    assert select([exact_other, world], year=2000, region="CHN", substream="oil_sands") == world


def test_ambiguous_exact_rows_same_substream_raise():
    a = frow(factor_id="oil_gas:0010", substream="oil_sands")
    b = frow(factor_id="oil_gas:0011", substream="oil_sands")
    with pytest.raises(LibError):
        select([a, b], year=2000, region="CHN", substream="oil_sands")


def test_ambiguous_xwl_rows_same_substream_raise():
    a = frow(factor_id="oil_gas:0010", substream="oil_sands", region="XWL")
    b = frow(factor_id="oil_gas:0011", substream="oil_sands", region="XWL")
    with pytest.raises(LibError):
        select([a, b], year=2000, region="CHN", substream="oil_sands")


def test_substream_combines_with_other_equality_keys():
    a = frow(factor_id="oil_gas:0010", substream="oil_sands", group="Ra226+")
    b = frow(factor_id="oil_gas:0011", substream="oil_sands", group="Ra228+")
    assert select([a, b], year=2000, region="CHN", substream="oil_sands", group="Ra228+") == b


# ------------------------------------------------------------------ read_table
HEADER = ("factor_id,description,stream,stage,substream,driver_series,group,tier,route,residue_type,"
          "region,year_from,year_to,value_low,value_central,value_high,unit,below_detection,basis,"
          "source_ids,notes")


def line(sub):
    return (f"oil_gas:0001,desc,oil_gas,production,{sub},oil_gas_prod,Ra226+,,,,XWL,1950,2025,"
            "1,2,3,Bq/m3,false,compiled,S0003,")


def test_read_table_substream_empty_cell_is_empty_string(tmp_path):
    p = tmp_path / "f.csv"
    p.write_text(HEADER + "\n" + line("") + "\n", encoding="utf-8")
    r = read_table(p)[0]
    assert r["substream"] == "" and isinstance(r["substream"], str), repr(r["substream"])
    assert r["route"] is None and r["notes"] is None  # other empty cells unchanged


def test_read_table_substream_value_is_string(tmp_path):
    p = tmp_path / "f.csv"
    p.write_text(HEADER + "\n" + line("oil_sands") + "\n" + line("") + "\n", encoding="utf-8")
    rows = read_table(p)
    assert [r["substream"] for r in rows] == ["oil_sands", ""]


def test_read_table_then_select_roundtrip(tmp_path):
    p = tmp_path / "f.csv"
    p.write_text(HEADER + "\n" + line("oil_sands") + "\n" + line("") + "\n", encoding="utf-8")
    rows = read_table(p)
    assert select(rows, year=2000, region="CHN", substream="oil_sands")["substream"] == "oil_sands"
    assert select(rows, year=2000, region="CHN", substream="")["substream"] == ""
