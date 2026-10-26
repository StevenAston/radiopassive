"""Spec-blind tests for pipeline.lib.io (LIB_SPEC section 5, SCHEMA 6.4 coercion)."""
from __future__ import annotations

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
    v = dict(
        year="1998", stream="nuclear", substream="fuel_cycle", stage="u_milling",
        product="", residue_type="u_tailings", country="CAN", group="Ra226+",
        tier="dispersed", quantity="flow", unit="Bq/a", value_low="2.0e12",
        value_central="4.0e12", value_high="8.0e12", below_detection="false",
        basis="compiled", source_ids="S0001;S0004", factor_ids="",
        allocation_variant="default", allocation_rule="civil:doc", embedded_fuel="false",
        technology="", route="", event_id="", notes="",
    )
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
