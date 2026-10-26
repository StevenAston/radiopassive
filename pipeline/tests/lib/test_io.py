"""Spec-blind tests for pipeline.lib.io (LIB_SPEC section 5, SCHEMA 6.4 coercion)."""
from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

import pytest

from pipeline.lib import LibError
from pipeline.lib.bounds import Bounds
from pipeline.lib.io import read_table
from pipeline.lib.rows import MASTER_COLUMNS, make_row, write_master

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
HEADER = ",".join(MASTER_COLUMNS)


def write(tmp_path, text, name="t.csv"):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8", newline="\n")
    return p


def master_line(**over):
    v = {
        "year": "1998", "stream": "nuclear", "substream": "fuel_cycle", "stage": "u_milling",
        "product": "", "residue_type": "u_tailings", "country": "CAN", "group": "Ra226+",
        "tier": "dispersed", "quantity": "flow", "unit": "Bq/a", "value_low": "2.0e12",
        "value_central": "4.0e12", "value_high": "8.0e12", "below_detection": "false",
        "basis": "compiled", "source_ids": "S0001;S0004", "factor_ids": "",
        "allocation_variant": "default", "allocation_rule": "civil:doc", "embedded_fuel": "false",
        "technology": "", "route": "", "event_id": "", "notes": "",
    }
    v.update(over)
    return ",".join(v[c] for c in MASTER_COLUMNS)


def test_read_table_header_only_is_empty_list(tmp_path):
    assert read_table(write(tmp_path, HEADER + "\n")) == []


def test_read_table_master_types(tmp_path):
    rows = read_table(write(tmp_path, HEADER + "\n" + master_line() + "\n"))
    assert len(rows) == 1
    r = rows[0]
    assert r["year"] == 1998 and type(r["year"]) is int
    assert r["value_low"] == 2.0e12 and type(r["value_low"]) is float
    assert r["value_central"] == 4.0e12 and r["value_high"] == 8.0e12
    assert r["below_detection"] is False and r["embedded_fuel"] is False
    assert r["stream"] == "nuclear" and r["unit"] == "Bq/a"
    assert r["source_ids"] == ["S0001", "S0004"]


def test_read_table_returns_one_dict_per_row_keyed_by_header(tmp_path):
    text = HEADER + "\n" + master_line() + "\n" + master_line(year="1999") + "\n"
    rows = read_table(write(tmp_path, text))
    assert [r["year"] for r in rows] == [1998, 1999]
    assert list(rows[0]) == list(MASTER_COLUMNS)


def test_read_table_empty_cells_become_none(tmp_path):
    r = read_table(write(tmp_path, HEADER + "\n" + master_line() + "\n"))[0]
    for col in ("product", "factor_ids", "technology", "route", "event_id", "notes"):
        assert r[col] is None, col


def test_read_table_booleans_true(tmp_path):
    r = read_table(write(tmp_path, HEADER + "\n"
                         + master_line(below_detection="true", embedded_fuel="true") + "\n"))[0]
    assert r["below_detection"] is True and r["embedded_fuel"] is True


def test_read_table_exponent_notation_floats(tmp_path):
    r = read_table(write(tmp_path, HEADER + "\n"
                         + master_line(value_low="1.5E-7", value_central="2e3",
                                       value_high="3.25e+4") + "\n"))[0]
    assert r["value_low"] == pytest.approx(1.5e-7)
    assert r["value_central"] == 2000.0
    assert r["value_high"] == 32500.0


def test_read_table_list_split_on_semicolon(tmp_path):
    r = read_table(write(tmp_path, HEADER + "\n"
                         + master_line(factor_ids="coal:0001;coal:0002") + "\n"))[0]
    assert r["factor_ids"] == ["coal:0001", "coal:0002"]
    assert read_table(write(tmp_path, HEADER + "\n" + master_line(source_ids="S0001") + "\n",
                            "one.csv"))[0]["source_ids"] == ["S0001"]


def test_read_table_quoted_fields_with_commas(tmp_path):
    r = read_table(write(tmp_path, HEADER + "\n" + master_line(notes='"a, b"') + "\n"))[0]
    assert r["notes"] == "a, b"


def test_read_table_factor_fixture_types(tmp_path):
    p = tmp_path / "factors.csv"
    shutil.copy(FIXTURES / "factors_coal.csv", p)
    rows = read_table(p)
    assert len(rows) == 2
    f = rows[0]
    assert f["factor_id"] == "coal:0001"
    assert f["year_from"] == 1950 and f["year_to"] == 2025
    assert type(f["year_from"]) is int
    assert f["value_low"] == 2.0e3 and f["value_central"] == 4.0e3 and f["value_high"] == 8.0e3
    assert f["unit"] == "Bq/t"
    assert f["below_detection"] is False
    assert f["source_ids"] == ["S0003"]
    assert f["route"] is None and f["residue_type"] is None and f["notes"] is None
    assert f["region"] == "USA"
    assert rows[1]["residue_type"] == "coal_fly_ash"


def test_read_table_valid_rows_fixture_loads(tmp_path):
    p = tmp_path / "valid.csv"
    shutil.copy(FIXTURES / "valid_rows.csv", p)
    rows = read_table(p)
    assert len(rows) == 10
    assert all(isinstance(r["year"], int) for r in rows)
    assert all(isinstance(r["source_ids"], list) and r["source_ids"] for r in rows)


def test_read_table_utf8_content(tmp_path):
    r = read_table(write(tmp_path, HEADER + "\n" + master_line(notes="café µ") + "\n"))[0]
    assert r["notes"] == "café µ"


def test_write_then_read_round_trip(tmp_path):
    row = make_row(
        bounds=Bounds(2.0e12, 4.0e12, 8.0e12), year=1998, stream="nuclear",
        substream="fuel_cycle", stage="u_milling", country="CAN", group="Ra226+",
        tier="dispersed", quantity="flow", unit="Bq/a", basis="compiled",
        source_ids=["S0001", "S0004"], residue_type="u_tailings",
        allocation_rule="civil:doc",
    )
    p = tmp_path / "m.csv"
    write_master([row], p)
    back = read_table(p)[0]
    assert back["year"] == 1998
    assert back["value_low"] == 2.0e12 and back["value_high"] == 8.0e12
    assert back["source_ids"] == ["S0001", "S0004"]
    assert back["below_detection"] is False and back["embedded_fuel"] is False
    assert back["product"] is None
    assert back["allocation_variant"] == "default"


@pytest.mark.parametrize("col,bad", [
    ("year", "19x8"), ("year", "1998.5"), ("value_low", "abc"),
    ("value_central", "nan"), ("value_high", "inf"),
    ("below_detection", "True"), ("below_detection", "yes"),
    ("embedded_fuel", "1"),
])
def test_read_table_coercion_failure_raises(tmp_path, col, bad):
    p = write(tmp_path, HEADER + "\n" + master_line(**{col: bad}) + "\n")
    with pytest.raises(LibError):
        read_table(p)


def test_read_table_empty_required_master_cell_raises(tmp_path):
    with pytest.raises(LibError):
        read_table(write(tmp_path, HEADER + "\n" + master_line(year="") + "\n"))


def test_read_table_error_names_file_line_and_column(tmp_path):
    p = write(tmp_path, HEADER + "\n" + master_line(value_low="abc") + "\n", "named.csv")
    with pytest.raises(LibError) as ei:
        read_table(p)
    msg = str(ei.value)
    assert "named.csv" in msg and "value_low" in msg


def test_read_table_write_master_round_trip_byte_stable(tmp_path):
    text = (HEADER + "\n"
            + master_line(factor_ids="coal:0001;coal:0002") + "\n"
            + master_line(year="1999", product="copper", notes='"a, b"',
                          below_detection="true", value_low="0",
                          allocation_rule="civil:doc;alloc:value") + "\n")
    src = write(tmp_path, text, "src.csv")
    rows = read_table(src)
    assert isinstance(rows[0]["factor_ids"], list)
    assert isinstance(rows[0]["source_ids"], list)
    out1, out2 = tmp_path / "o1.csv", tmp_path / "o2.csv"
    write_master(rows, out1)
    write_master(read_table(out1), out2)
    assert out1.read_bytes() == out2.read_bytes()
    assert read_table(out1) == rows
    assert isinstance(rows[0]["allocation_rule"], list)


# ======================================================================
# v1.2 additions (LIB_SPEC section 8.4)
# ======================================================================

EVENTS_HEADER = (
    "event_id,name,date_start,date_end,country,location,lat,lon,stream,stage,"
    "event_type,is_accident,from_tier,to_tiers,mass_t,activity_low_bq,"
    "activity_central_bq,activity_high_bq,inclusion,military,source_ids,notes"
)
COUNTRIES_HEADER = "code,name,kind,valid_from,valid_to,notes"
SOURCES_HEADER = ("source_id,short_cite,full_citation,url,doi,year,type,rank,access,"
                  "licence,notes")
BANDS_HEADER = "band_id,quantity_class,applies_to,rel_low,rel_high,basis,source_ids,notes"
RESIDUE_HEADER = (
    "residue_type,description,streams,epsilon_rn222_low,epsilon_rn222_central,"
    "epsilon_rn222_high,epsilon_rn220_low,epsilon_rn220_central,epsilon_rn220_high,"
    "seepage_per_a_low,seepage_per_a_central,seepage_per_a_high,basis,source_ids,notes"
)


# ------------------------------------------------------------- events

def test_read_table_events_types(tmp_path):
    text = (
        EVENTS_HEADER + "\n"
        "E001,Test accident,1986-04-26,1986-05-06,UKR,Site,51.389,30.099,nuclear,"
        "accident,accident,true,sealed_in_core,liberated;sealed_damaged_core,,4.0e18,"
        "5.3e18,7.0e18,activity,false,S0001,\n"
        "E002,Test spill,2008-12-22,,USA,Somewhere,35.9,-84.51,coal,combustion_power,"
        "impoundment_failure,false,impounded,liberated,4.1e6,,,,mass,false,S0005;S0006,note\n"
    )
    a, b = read_table(write(tmp_path, text, "events.csv"))
    assert type(a["lat"]) is float and a["lat"] == 51.389
    assert type(a["lon"]) is float and a["lon"] == 30.099
    assert a["is_accident"] is True and a["military"] is False
    assert a["to_tiers"] == ["liberated", "sealed_damaged_core"]
    assert a["activity_low_bq"] == 4.0e18 and type(a["activity_low_bq"]) is float
    assert a["activity_central_bq"] == 5.3e18 and a["activity_high_bq"] == 7.0e18
    assert a["mass_t"] is None
    assert a["source_ids"] == ["S0001"]
    assert a["date_start"] == "1986-04-26" and a["event_id"] == "E001"
    assert a["notes"] is None
    assert b["lon"] == -84.51
    assert b["is_accident"] is False
    assert b["to_tiers"] == ["liberated"]
    assert type(b["mass_t"]) is float and b["mass_t"] == 4.1e6
    assert b["activity_central_bq"] is None
    assert b["date_end"] is None
    assert b["source_ids"] == ["S0005", "S0006"]


def test_read_table_events_fixture(tmp_path):
    p = tmp_path / "events.csv"
    shutil.copy(FIXTURES / "events.csv", p)
    rows = read_table(p)
    assert rows[0]["is_accident"] is True and rows[0]["to_tiers"][0] == "liberated"
    assert rows[1]["mass_t"] == 4.1e6


@pytest.mark.parametrize("col,bad", [
    ("lat", "north"), ("lon", "nan"), ("mass_t", "1,5"),
    ("activity_high_bq", "inf"), ("is_accident", "True"), ("military", "no"),
])
def test_read_table_events_coercion_failure_raises(tmp_path, col, bad):
    vals = {
        "event_id": "E001", "name": "n", "date_start": "1986-04-26", "date_end": "", "country": "UKR",
        "location": "", "lat": "1.0", "lon": "2.0", "stream": "nuclear", "stage": "accident",
        "event_type": "accident", "is_accident": "true", "from_tier": "sealed_in_core",
        "to_tiers": "liberated", "mass_t": "", "activity_low_bq": "", "activity_central_bq": "",
        "activity_high_bq": "", "inclusion": "activity", "military": "false", "source_ids": "S0001",
        "notes": "",
    }
    vals[col] = bad
    line = ",".join(vals[c] for c in EVENTS_HEADER.split(","))
    with pytest.raises(LibError):
        read_table(write(tmp_path, EVENTS_HEADER + "\n" + line + "\n", "events.csv"))


# ---------------------------------------------------------- countries

def test_read_table_countries_types(tmp_path):
    text = (COUNTRIES_HEADER + "\n"
            "SUN,Soviet Union,iso3166_3_former,1950,1991,dissolved\n"
            "USA,United States,iso3166_1,,,\n")
    sun, usa = read_table(write(tmp_path, text, "countries.csv"))
    assert sun["valid_from"] == 1950 and type(sun["valid_from"]) is int
    assert sun["valid_to"] == 1991 and type(sun["valid_to"]) is int
    assert sun["code"] == "SUN" and sun["notes"] == "dissolved"
    assert usa["valid_from"] is None and usa["valid_to"] is None and usa["notes"] is None


def test_read_table_countries_non_integer_year_raises(tmp_path):
    text = COUNTRIES_HEADER + "\nSUN,Soviet Union,iso3166_3_former,1950.5,1991,\n"
    with pytest.raises(LibError):
        read_table(write(tmp_path, text, "countries.csv"))


# ------------------------------------------------------------ sources

def test_read_table_sources_types(tmp_path):
    text = (SOURCES_HEADER + "\n"
            'S0001,UNSCEAR 2016,"Long, quoted citation",https://example.org/a,,2017,'
            "compilation,2,open,open,\n")
    r = read_table(write(tmp_path, text, "sources.csv"))[0]
    assert r["year"] == 2017 and type(r["year"]) is int
    assert r["rank"] == 2 and type(r["rank"]) is int
    assert r["full_citation"] == "Long, quoted citation"
    assert r["doi"] is None and r["notes"] is None
    assert r["source_id"] == "S0001"


def test_read_table_sources_fixture(tmp_path):
    p = tmp_path / "sources.csv"
    shutil.copy(FIXTURES / "sources.csv", p)
    rows = read_table(p)
    assert rows[0]["year"] == 2017 and rows[0]["rank"] == 2
    assert rows[1]["rank"] == 1 and rows[1]["year"] == 2012


def test_read_table_sources_non_integer_rank_raises(tmp_path):
    text = (SOURCES_HEADER + "\n"
            "S0001,a,b,,,2017,compilation,two,open,open,\n")
    with pytest.raises(LibError):
        read_table(write(tmp_path, text, "sources.csv"))


# ---------------------------------------------------- reference bands

def test_read_table_reference_bands_types(tmp_path):
    text = (BANDS_HEADER + "\n"
            "RB01,half_life,*,-0.1,0.1,compiled,S0001,\n"
            "RB02,e_alpha,U238;Th232,-0.02,0.05,compiled,S0001;S0002,note\n")
    a, b = read_table(write(tmp_path, text, "bands.csv"))
    assert a["applies_to"] == ["*"]
    assert a["rel_low"] == -0.1 and type(a["rel_low"]) is float
    assert a["rel_high"] == 0.1 and type(a["rel_high"]) is float
    assert a["source_ids"] == ["S0001"] and a["notes"] is None
    assert b["applies_to"] == ["U238", "Th232"]
    assert b["rel_low"] == -0.02 and b["rel_high"] == 0.05
    assert b["source_ids"] == ["S0001", "S0002"]


def test_read_table_reference_bands_bad_float_raises(tmp_path):
    text = BANDS_HEADER + "\nRB01,half_life,*,minus,0.1,compiled,S0001,\n"
    with pytest.raises(LibError):
        read_table(write(tmp_path, text, "bands.csv"))


# ------------------------------------------------------ residue types

def test_read_table_residue_types_types(tmp_path):
    text = (RESIDUE_HEADER + "\n"
            "u_tailings,Uranium tailings,nuclear;coal,0.1,0.2,0.4,0.01,0.02,0.04,"
            "1e-5,2e-5,4e-5,modelled,S0001;S0002,\n"
            "coal_fly_ash,Fly ash,coal,,,,,,,,,,,,\n")
    a, b = read_table(write(tmp_path, text, "residue_types.csv"))
    assert a["streams"] == ["nuclear", "coal"]
    for col, want in [("epsilon_rn222_low", 0.1), ("epsilon_rn222_central", 0.2),
                      ("epsilon_rn222_high", 0.4), ("epsilon_rn220_low", 0.01),
                      ("epsilon_rn220_central", 0.02), ("epsilon_rn220_high", 0.04),
                      ("seepage_per_a_low", 1e-5), ("seepage_per_a_central", 2e-5),
                      ("seepage_per_a_high", 4e-5)]:
        assert a[col] == pytest.approx(want), col
        assert type(a[col]) is float, col
    assert a["source_ids"] == ["S0001", "S0002"]
    assert b["streams"] == ["coal"]
    assert b["epsilon_rn222_low"] is None and b["seepage_per_a_high"] is None
    assert b["basis"] is None and b["source_ids"] is None


def test_read_table_residue_types_bad_float_raises(tmp_path):
    text = (RESIDUE_HEADER + "\n"
            "x,d,coal,0.1,abc,0.4,,,,,,,,,\n")
    with pytest.raises(LibError):
        read_table(write(tmp_path, text, "residue_types.csv"))


# ------------------------------------- baselines, activity, commodity

def test_read_table_baselines_fixture_types(tmp_path):
    p = tmp_path / "baselines.csv"
    shutil.copy(FIXTURES / "baselines.csv", p)
    rows = read_table(p)
    assert rows[0]["year"] is None and rows[0]["group"] == "Rn222+"
    assert rows[0]["value_central"] == 2.0e17 and type(rows[0]["value_central"]) is float
    assert rows[1]["year"] == 2020 and type(rows[1]["year"]) is int
    assert rows[0]["source_ids"] == ["S0001"]


def test_read_table_activity_fixture_types(tmp_path):
    p = tmp_path / "activity.csv"
    shutil.copy(FIXTURES / "activity.csv", p)
    r = read_table(p)[0]
    assert r["year"] == 2000 and type(r["year"]) is int
    assert r["value_central"] == 1.2e9 and r["below_detection"] is False
    assert r["source_ids"] == ["S0003"]


def test_read_table_commodity_factors_fixture_types(tmp_path):
    p = tmp_path / "commodity_factors.csv"
    shutil.copy(FIXTURES / "commodity_factors.csv", p)
    rows = read_table(p)
    r = rows[0]
    assert r["year_from"] == 1990 and r["year_to"] == 2020
    assert r["value_low"] == 1.0e3 and r["value_high"] == 4.0e3
    assert r["below_detection"] is False and r["route"] is None
    assert r["source_ids"] == ["S0003"]


# ------------------------------------------------- width and headers

def test_read_table_short_row_raises_naming_file_and_line(tmp_path):
    lines = [COUNTRIES_HEADER] + [f"C{i:02d},Name,user_assigned,,,"
                                  for i in range(6)] + ["BAD,Short,user_assigned"]
    p = write(tmp_path, "\n".join(lines) + "\n", "widthfile.csv")
    with pytest.raises(LibError) as ei:
        read_table(p)
    msg = str(ei.value)
    assert "widthfile.csv" in msg
    assert "8" in msg  # header is line 1, bad row is line 8


def test_read_table_long_row_raises(tmp_path):
    text = COUNTRIES_HEADER + "\nSUN,Soviet Union,iso3166_3_former,1950,1991,note,extra\n"
    with pytest.raises(LibError) as ei:
        read_table(write(tmp_path, text, "toolong.csv"))
    assert "toolong.csv" in str(ei.value)


def test_read_table_master_row_missing_a_cell_raises(tmp_path):
    line = master_line()
    short = line.rsplit(",", 1)[0]  # drop the last cell
    with pytest.raises(LibError):
        read_table(write(tmp_path, HEADER + "\n" + short + "\n"))


def test_read_table_master_row_with_trailing_comma_raises(tmp_path):
    with pytest.raises(LibError):
        read_table(write(tmp_path, HEADER + "\n" + master_line() + ",\n"))


def test_read_table_duplicate_header_raises_naming_file_and_column(tmp_path):
    text = "code,name,code,valid_from,valid_to,notes\nSUN,x,SUN,1950,1991,\n"
    with pytest.raises(LibError) as ei:
        read_table(write(tmp_path, text, "dupheader.csv"))
    msg = str(ei.value)
    assert "dupheader.csv" in msg and "code" in msg


def test_read_table_duplicate_header_in_header_only_file_raises(tmp_path):
    with pytest.raises(LibError):
        read_table(write(tmp_path, "code,name,code\n", "dup2.csv"))


# ------------------------------------- blank lines and byte-order mark
# LIB_SPEC is silent on both; the instruction for this suite and the
# validator's behaviour (SCHEMA 6.5) are the basis.

def test_read_table_blank_lines_are_skipped(tmp_path):
    text = ("\n".join([HEADER, "", master_line(), "", master_line(year="1999"), "", ""])
            + "\n")
    rows = read_table(write(tmp_path, text))
    assert [r["year"] for r in rows] == [1998, 1999]


def test_read_table_trailing_blank_lines_only(tmp_path):
    rows = read_table(write(tmp_path, HEADER + "\n" + master_line() + "\n\n\n"))
    assert len(rows) == 1


def test_read_table_utf8_bom_is_tolerated(tmp_path):
    p = tmp_path / "bom.csv"
    p.write_bytes(("\ufeff" + HEADER + "\n" + master_line() + "\n").encode("utf-8"))
    rows = read_table(p)
    assert len(rows) == 1
    assert list(rows[0]) == list(MASTER_COLUMNS)  # first key is 'year', not '\ufeffyear'
    assert rows[0]["year"] == 1998


def test_read_table_utf8_bom_on_non_master_table(tmp_path):
    p = tmp_path / "bomc.csv"
    p.write_bytes(("\ufeff" + COUNTRIES_HEADER + "\nUSA,United States,iso3166_1,,,\n")
                  .encode("utf-8"))
    rows = read_table(p)
    assert rows[0]["code"] == "USA"


# ------------------------------------------------- round trip, int input

def test_round_trip_exact_integer_bounds_byte_stable(tmp_path):
    row = make_row(
        bounds=Bounds.exact(12345678), year=1998, stream="nuclear", substream="fuel_cycle",
        stage="u_milling", country="CAN", group="Ra226+", tier="dispersed",
        quantity="flow", unit="Bq/a", basis="compiled", source_ids=["S0001"],
        residue_type="u_tailings",
    )
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    write_master([row], a)
    back = read_table(a)
    assert back[0]["value_central"] == pytest.approx(12345678, rel=1e-5)
    write_master(back, b)
    assert a.read_bytes() == b.read_bytes()


# ------------------------------------- LIB_SPEC 8.8 (round 2) and gap tests
# Skipped on purpose: "read_table strips whitespace around cells and headers".
# SCHEMA 6.4 and 6.5 say nothing about stripping, so the spec does not support a test.


def test_read_table_empty_file_raises_liberror(tmp_path):
    # 8.8.4: a zero-byte file has no header and is an error (a header-only file is valid).
    p = tmp_path / "empty.csv"
    p.write_bytes(b"")
    with pytest.raises(LibError):
        read_table(p)


@pytest.mark.parametrize("bad", [123, None, 1.5, ["a.csv"], b"a.csv"])
def test_read_table_non_path_raises_liberror(bad):
    with pytest.raises(LibError):
        read_table(bad)


def test_read_table_directory_raises_liberror_naming_path(tmp_path):
    with pytest.raises(LibError) as ei:
        read_table(tmp_path)
    assert str(tmp_path) in str(ei.value)


def test_read_table_missing_file_raises_liberror_naming_path(tmp_path):
    p = tmp_path / "absent.csv"
    with pytest.raises(LibError) as ei:
        read_table(p)
    assert str(p) in str(ei.value)


def test_read_table_accepts_pathlike_and_str(tmp_path):
    p = write(tmp_path, HEADER + "\n" + master_line() + "\n")

    class P(os.PathLike):
        def __fspath__(self):
            return str(p)

    assert read_table(P()) == read_table(str(p)) == read_table(p)


def test_read_table_multiline_quoted_cell_reads_back(tmp_path):
    text = HEADER + "\n" + master_line(notes='"line one\nline two"') + "\n"
    rows = read_table(write(tmp_path, text))
    assert rows[0]["notes"] == "line one\nline two"


def test_read_table_error_after_multiline_cell_reports_sensible_line(tmp_path):
    # Physical lines: 1 header; 2-3 first record (multi-line notes); 4 second record (bad year).
    # Record number would be 3; physical line 4.  Either is sensible; 2 or 1 is not.
    text = (HEADER + "\n" + master_line(notes='"a\nb"') + "\n"
            + master_line(year="abc") + "\n")
    p = write(tmp_path, text)
    with pytest.raises(LibError) as ei:
        read_table(p)
    msg = str(ei.value)
    assert p.name in msg
    nums = {int(n) for n in re.findall(r"\d+", msg.replace(p.name, ""))}
    assert nums & {3, 4}, f"no plausible line number (3 or 4) in: {msg}"
    assert "year" in msg
