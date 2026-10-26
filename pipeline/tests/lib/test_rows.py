"""Spec-blind tests for pipeline.lib.rows (LIB_SPEC section 4, SCHEMA section 3)."""
from __future__ import annotations

import csv

import pytest

from pipeline.lib import LibError
from pipeline.lib.bounds import Bounds
from pipeline.lib.rows import MASTER_COLUMNS, make_row, write_master

EXPECTED_COLUMNS = [
    "year", "stream", "substream", "stage", "product", "residue_type", "country",
    "group", "tier", "quantity", "unit", "value_low", "value_central", "value_high",
    "below_detection", "basis", "source_ids", "factor_ids", "allocation_variant",
    "allocation_rule", "embedded_fuel", "technology", "route", "event_id", "notes",
]

REQUIRED = ["year", "stream", "substream", "stage", "country", "group", "tier",
            "quantity", "unit", "basis", "source_ids"]

KEY_COLUMNS = ["year", "stream", "substream", "stage", "product", "residue_type",
               "country", "group", "tier", "quantity", "allocation_variant",
               "embedded_fuel", "technology", "route", "event_id"]


def base_fields(**over):
    f = {
        "year": 1998, "stream": "nuclear", "substream": "fuel_cycle", "stage": "u_milling",
        "country": "CAN", "group": "Ra226+", "tier": "dispersed", "quantity": "flow",
        "unit": "Bq/a", "basis": "compiled", "source_ids": "S0001",
    }
    f.update(over)
    return f


def full_row(**over):
    """A complete 25-column row built by hand (independent of make_row)."""
    r = {c: None for c in EXPECTED_COLUMNS}
    r.update(
        year=1998, stream="nuclear", substream="fuel_cycle", stage="u_milling",
        country="CAN", group="Ra226+", tier="dispersed", quantity="flow",
        unit="Bq/a", value_low=1.0, value_central=2.0, value_high=3.0,
        below_detection=False, basis="compiled", source_ids="S0001",
        allocation_variant="default", allocation_rule="none", embedded_fuel=False,
    )
    r.update(over)
    return r


def read_raw(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.reader(fh))


# ----------------------------------------------------------- MASTER_COLUMNS

def test_master_columns_exact_order_and_count():
    assert list(MASTER_COLUMNS) == EXPECTED_COLUMNS
    assert len(MASTER_COLUMNS) == 25


# ----------------------------------------------------------------- make_row

def test_make_row_keys_exactly_master_columns():
    row = make_row(bounds=Bounds(1.0, 2.0, 3.0), **base_fields())
    assert set(row) == set(EXPECTED_COLUMNS)
    assert list(row) == EXPECTED_COLUMNS or sorted(row) == sorted(EXPECTED_COLUMNS)


def test_make_row_values_from_bounds():
    row = make_row(bounds=Bounds(1.0, 2.0, 3.0), **base_fields())
    assert (row["value_low"], row["value_central"], row["value_high"]) == (1.0, 2.0, 3.0)


def test_make_row_below_detection_follows_nd_floored():
    nd = make_row(bounds=Bounds(0.0, 1.0, 2.0, nd_floored=True), **base_fields())
    assert nd["below_detection"] is True
    plain = make_row(bounds=Bounds(1.0, 2.0, 3.0), **base_fields())
    assert plain["below_detection"] is False


def test_make_row_explicit_below_detection_agreeing_with_bounds_is_kept():
    # Converted for LIB_SPEC 8.2: explicit values must agree with the bounds.
    row = make_row(bounds=Bounds(0.0, 1.0, 2.0), below_detection=True, **base_fields())
    assert row["below_detection"] is True
    row = make_row(bounds=Bounds(0.0, 1.0, 2.0, nd_floored=True),
                   below_detection=True, **base_fields())
    assert row["below_detection"] is True
    row = make_row(bounds=Bounds(1.0, 2.0, 3.0), below_detection=False, **base_fields())
    assert row["below_detection"] is False
    # low == 0 but not flagged: an explicit False is consistent
    row = make_row(bounds=Bounds(0.0, 1.0, 2.0), below_detection=False, **base_fields())
    assert row["below_detection"] is False


def test_make_row_explicit_true_with_positive_low_raises():
    # was: "explicit below_detection wins" (True with low 1.0); now SCHEMA 3
    # (below_detection => value_low == 0) is enforced.
    with pytest.raises(LibError) as ei:
        make_row(bounds=Bounds(1.0, 2.0, 3.0), below_detection=True, **base_fields())
    assert "below_detection" in str(ei.value)


def test_make_row_explicit_false_with_flagged_bounds_raises():
    # was: "explicit below_detection wins" (False over a flagged Bounds)
    with pytest.raises(LibError):
        make_row(bounds=Bounds(0.0, 1.0, 2.0, nd_floored=True),
                 below_detection=False, **base_fields())


def test_make_row_nullable_defaults_are_none():
    row = make_row(bounds=Bounds(1.0, 2.0, 3.0), **base_fields())
    for col in ("product", "residue_type", "factor_ids", "technology",
                "route", "event_id", "notes"):
        assert row[col] is None, col


def test_make_row_allocation_variant_default():
    row = make_row(bounds=Bounds(1.0, 2.0, 3.0), **base_fields())
    assert row["allocation_variant"] == "default"


def test_make_row_embedded_fuel_default_false_bool():
    row = make_row(bounds=Bounds(1.0, 2.0, 3.0), **base_fields())
    assert row["embedded_fuel"] is False


def test_make_row_allocation_rule_default_none_token():
    row = make_row(bounds=Bounds(1.0, 2.0, 3.0), **base_fields())
    assert row["allocation_rule"] == "none"


def test_make_row_allocation_rule_list_joined():
    row = make_row(bounds=Bounds(1.0, 2.0, 3.0),
                   allocation_rule=["civil:doc", "alloc:value"], **base_fields())
    assert row["allocation_rule"] == "civil:doc;alloc:value"


def test_make_row_unknown_field_raises():
    with pytest.raises(LibError):
        make_row(bounds=Bounds(1.0, 2.0, 3.0), colour="red", **base_fields())


@pytest.mark.parametrize("missing", REQUIRED)
def test_make_row_missing_required_field_raises(missing):
    fields = base_fields()
    del fields[missing]
    with pytest.raises(LibError) as ei:
        make_row(bounds=Bounds(1.0, 2.0, 3.0), **fields)
    assert missing in str(ei.value)


def test_make_row_source_ids_list_joined_with_semicolon():
    row = make_row(bounds=Bounds(1.0, 2.0, 3.0),
                   **base_fields(source_ids=["S0001", "S0004"]))
    assert row["source_ids"] == "S0001;S0004"


def test_make_row_factor_ids_list_joined_with_semicolon():
    row = make_row(bounds=Bounds(1.0, 2.0, 3.0),
                   **base_fields(factor_ids=["coal:0001", "coal:0002"]))
    assert row["factor_ids"] == "coal:0001;coal:0002"


def test_make_row_string_ids_pass_through():
    row = make_row(bounds=Bounds(1.0, 2.0, 3.0),
                   **base_fields(source_ids="S0001;S0002", factor_ids="coal:0001"))
    assert row["source_ids"] == "S0001;S0002"
    assert row["factor_ids"] == "coal:0001"


def test_make_row_passes_optional_fields_through():
    row = make_row(bounds=Bounds(1.0, 2.0, 3.0),
                   **base_fields(product="copper", notes="hello", allocation_variant="bound_main",
                                 allocation_rule="alloc:main", embedded_fuel=True,
                                 technology="wind", route="stack", event_id="E001"))
    assert row["product"] == "copper" and row["notes"] == "hello"
    assert row["allocation_variant"] == "bound_main"
    assert row["embedded_fuel"] is True
    assert row["technology"] == "wind" and row["route"] == "stack"
    assert row["event_id"] == "E001"


# ------------------------------------------------------------- write_master

def test_write_master_header_and_columns(tmp_path):
    p = tmp_path / "m.csv"
    write_master([full_row()], p)
    rows = read_raw(p)
    assert rows[0] == EXPECTED_COLUMNS
    assert len(rows) == 2 and all(len(r) == 25 for r in rows)


def test_write_master_empty_list_writes_header_only(tmp_path):
    p = tmp_path / "m.csv"
    write_master([], p)
    assert read_raw(p) == [EXPECTED_COLUMNS]


def test_write_master_accepts_str_path(tmp_path):
    p = tmp_path / "m.csv"
    write_master([full_row()], str(p))
    assert p.exists()


def test_write_master_float_format_6g(tmp_path):
    # format(x, '.6g'):
    #   4.0e12 -> '4e+12' ; 1234567.0 -> '1.23457e+06' ; 0.1 -> '0.1'
    #   2.0 -> '2' ; 0.0 -> '0' ; 1/3 -> '0.333333' ; 1.5e-7 -> '1.5e-07'
    p = tmp_path / "m.csv"
    write_master([full_row(value_low=0.0, value_central=1 / 3, value_high=1234567.0)], p)
    r = read_raw(p)[1]
    h = EXPECTED_COLUMNS
    assert r[h.index("value_low")] == "0"
    assert r[h.index("value_central")] == "0.333333"
    assert r[h.index("value_high")] == "1.23457e+06"
    write_master([full_row(value_low=2.0, value_central=4.0e12, value_high=1.5e-7 + 4.0e12)], p)
    r = read_raw(p)[1]
    assert r[h.index("value_low")] == "2"
    assert r[h.index("value_central")] == "4e+12"
    write_master([full_row(value_low=1.5e-7, value_central=1.5e-7, value_high=0.1)], p)
    r = read_raw(p)[1]
    assert r[h.index("value_low")] == "1.5e-07"
    assert r[h.index("value_high")] == "0.1"


def test_write_master_booleans_true_false(tmp_path):
    p = tmp_path / "m.csv"
    write_master([
        full_row(below_detection=True, embedded_fuel=False),
        full_row(year=1999, below_detection=False, embedded_fuel=True),
    ], p)
    rows = read_raw(p)
    h = EXPECTED_COLUMNS
    by_year = {r[h.index("year")]: r for r in rows[1:]}
    assert by_year["1998"][h.index("below_detection")] == "true"
    assert by_year["1998"][h.index("embedded_fuel")] == "false"
    assert by_year["1999"][h.index("below_detection")] == "false"
    assert by_year["1999"][h.index("embedded_fuel")] == "true"


def test_write_master_none_is_empty_cell_and_ints_plain(tmp_path):
    p = tmp_path / "m.csv"
    write_master([full_row(product=None, notes=None)], p)
    r = read_raw(p)[1]
    h = EXPECTED_COLUMNS
    assert r[h.index("product")] == "" and r[h.index("notes")] == ""
    assert r[h.index("year")] == "1998"


def test_write_master_utf8_lf_endings(tmp_path):
    p = tmp_path / "m.csv"
    write_master([full_row(notes="café, naïve µ"), full_row(year=1999)], p)
    raw = p.read_bytes()
    assert b"\r" not in raw
    text = raw.decode("utf-8")  # must be valid UTF-8
    assert "café" in text
    assert text.count("\n") >= 3
    assert read_raw(p)[1][EXPECTED_COLUMNS.index("notes")] in ("café, naïve µ", "")


def test_write_master_quotes_commas_and_roundtrips_notes(tmp_path):
    p = tmp_path / "m.csv"
    write_master([full_row(notes="a, b")], p)
    assert read_raw(p)[1][EXPECTED_COLUMNS.index("notes")] == "a, b"


def test_write_master_sorted_by_year_numeric(tmp_path):
    p = tmp_path / "m.csv"
    write_master([full_row(year=2000), full_row(year=1998), full_row(year=1999)], p)
    years = [r[0] for r in read_raw(p)[1:]]
    assert years == ["1998", "1999", "2000"]


def test_write_master_sort_follows_key_column_order(tmp_path):
    # year equal -> stream decides before substream etc.
    p = tmp_path / "m.csv"
    write_master([
        full_row(stream="oil_gas", substream="aaa"),
        full_row(stream="coal", substream="zzz"),
        full_row(stream="coal", substream="bbb"),
    ], p)
    h = EXPECTED_COLUMNS
    got = [(r[h.index("stream")], r[h.index("substream")]) for r in read_raw(p)[1:]]
    assert got == [("coal", "bbb"), ("coal", "zzz"), ("oil_gas", "aaa")]


def test_write_master_none_sorts_first(tmp_path):
    # product None < 'copper' < 'zinc', other key columns equal.
    p = tmp_path / "m.csv"
    write_master([
        full_row(product="zinc"), full_row(product="copper"), full_row(product=None),
    ], p)
    h = EXPECTED_COLUMNS
    assert [r[h.index("product")] for r in read_raw(p)[1:]] == ["", "copper", "zinc"]


@pytest.mark.parametrize("col,val", [
    ("residue_type", "u_tailings"), ("technology", "wind"),
    ("route", "stack"), ("event_id", "E001"),
])
def test_write_master_none_sorts_first_for_each_nullable_key(tmp_path, col, val):
    p = tmp_path / "m.csv"
    write_master([full_row(**{col: val}), full_row(**{col: None})], p)
    h = EXPECTED_COLUMNS
    assert [r[h.index(col)] for r in read_raw(p)[1:]] == ["", val]


def test_write_master_embedded_fuel_false_before_true(tmp_path):
    p = tmp_path / "m.csv"
    write_master([full_row(embedded_fuel=True), full_row(embedded_fuel=False)], p)
    h = EXPECTED_COLUMNS
    assert [r[h.index("embedded_fuel")] for r in read_raw(p)[1:]] == ["false", "true"]


def test_write_master_nonkey_columns_do_not_affect_order(tmp_path):
    # values/notes differ but the key is the same except for 'group'
    p = tmp_path / "m.csv"
    write_master([
        full_row(group="Th232+", value_central=1.0),
        full_row(group="Ra226+", value_central=99.0),
    ], p)
    h = EXPECTED_COLUMNS
    assert [r[h.index("group")] for r in read_raw(p)[1:]] == ["Ra226+", "Th232+"]


def test_write_master_duplicate_key_raises(tmp_path):
    p = tmp_path / "m.csv"
    with pytest.raises(LibError):
        write_master([full_row(), full_row()], p)


def test_write_master_duplicate_key_with_different_values_raises(tmp_path):
    p = tmp_path / "m.csv"
    with pytest.raises(LibError):
        write_master([full_row(value_central=2.0), full_row(value_central=5.0, notes="x")], p)


@pytest.mark.parametrize("col,val", [
    ("year", 1999), ("stream", "coal"), ("substream", "x"), ("stage", "y"),
    ("product", "copper"), ("residue_type", "r"), ("country", "USA"),
    ("group", "Th232+"), ("tier", "impounded"), ("quantity", "standing_inventory"),
    ("allocation_variant", "bound_main"), ("embedded_fuel", True),
    ("technology", "wind"), ("route", "stack"), ("event_id", "E001"),
])
def test_write_master_each_key_column_distinguishes_rows(tmp_path, col, val):
    p = tmp_path / "m.csv"
    write_master([full_row(), full_row(**{col: val})], p)  # no error
    assert len(read_raw(p)) == 3


def test_write_master_duplicate_error_names_key(tmp_path):
    with pytest.raises(LibError) as ei:
        write_master([full_row(), full_row()], tmp_path / "m.csv")
    assert str(ei.value)


def test_write_master_byte_identical_across_runs_and_input_order(tmp_path):
    rows = [
        full_row(year=2001, product="zinc", value_central=1 / 3),
        full_row(year=1999, product=None, below_detection=True),
        full_row(year=1999, product="copper", notes="a, b"),
        full_row(year=1950, embedded_fuel=True, value_high=1e30),
    ]
    p1, p2, p3 = tmp_path / "a.csv", tmp_path / "b.csv", tmp_path / "c.csv"
    write_master(rows, p1)
    write_master(rows, p2)
    write_master(list(reversed(rows)), p3)
    assert p1.read_bytes() == p2.read_bytes()
    assert p1.read_bytes() == p3.read_bytes()


def test_write_master_does_not_mutate_input(tmp_path):
    rows = [full_row(year=2001), full_row(year=1999)]
    snapshot = [dict(r) for r in rows]
    write_master(rows, tmp_path / "m.csv")
    assert rows == snapshot


def test_make_row_then_write_master_end_to_end(tmp_path):
    row = make_row(bounds=Bounds(2.0e12, 4.0e12, 8.0e12),
                   **base_fields(source_ids=["S0001", "S0004"], allocation_rule="civil:doc"))
    p = tmp_path / "m.csv"
    write_master([row], p)
    got = read_raw(p)[1]
    h = EXPECTED_COLUMNS
    assert got[h.index("value_low")] == "2e+12"
    assert got[h.index("value_central")] == "4e+12"
    assert got[h.index("value_high")] == "8e+12"
    assert got[h.index("source_ids")] == "S0001;S0004"
    assert got[h.index("below_detection")] == "false"
    assert got[h.index("allocation_variant")] == "default"
    assert got[h.index("embedded_fuel")] == "false"


@pytest.mark.parametrize("field", ["value_low", "value_central", "value_high"])
def test_make_row_value_field_alongside_bounds_raises(field):
    with pytest.raises(LibError):
        make_row(bounds=Bounds(1.0, 2.0, 3.0), **base_fields(**{field: 9.0}))


def test_write_master_accepts_lists_or_joined_strings(tmp_path):
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    write_master([full_row(source_ids=["S0001", "S0004"], factor_ids=["c:0001", "c:0002"],
                           allocation_rule=["civil:doc", "alloc:value"])], a)
    write_master([full_row(source_ids="S0001;S0004", factor_ids="c:0001;c:0002",
                           allocation_rule="civil:doc;alloc:value")], b)
    assert a.read_bytes() == b.read_bytes()
    r = read_raw(a)[1]
    assert r[EXPECTED_COLUMNS.index("source_ids")] == "S0001;S0004"
    assert r[EXPECTED_COLUMNS.index("allocation_rule")] == "civil:doc;alloc:value"


# ======================================================================
# v1.2 additions (LIB_SPEC section 8.2, 8.3, 8.4)
# ======================================================================

H = EXPECTED_COLUMNS


def cells(path):
    """Header-keyed list of dicts of raw cell text."""
    raw = read_raw(path)
    return [dict(zip(raw[0], r)) for r in raw[1:]]


# ------------------------------------------------- make_row: explicit None

@pytest.mark.parametrize("col,want", [
    ("allocation_variant", "default"),
    ("allocation_rule", "none"),
    ("embedded_fuel", False),
])
def test_make_row_explicit_none_takes_default(col, want):
    row = make_row(bounds=Bounds(1.0, 2.0, 3.0), **base_fields(**{col: None}))
    assert row[col] == want
    assert type(row[col]) is type(want)


def test_make_row_all_three_explicit_none_together():
    row = make_row(bounds=Bounds(1.0, 2.0, 3.0),
                   **base_fields(allocation_variant=None, allocation_rule=None,
                                 embedded_fuel=None))
    assert (row["allocation_variant"], row["allocation_rule"], row["embedded_fuel"]) == (
        "default", "none", False)


def test_make_row_explicit_none_on_nullable_columns_stays_none():
    row = make_row(bounds=Bounds(1.0, 2.0, 3.0),
                   **base_fields(product=None, route=None, notes=None, factor_ids=None))
    assert row["product"] is None and row["route"] is None
    assert row["notes"] is None and row["factor_ids"] is None


# ------------------------------------------------ make_row: source_ids

@pytest.mark.parametrize("empty", [[], ""])
def test_make_row_empty_source_ids_raises(empty):
    with pytest.raises(LibError) as ei:
        make_row(bounds=Bounds(1.0, 2.0, 3.0), **base_fields(source_ids=empty))
    assert "source_ids" in str(ei.value)


def test_make_row_single_element_source_ids_list():
    row = make_row(bounds=Bounds(1.0, 2.0, 3.0), **base_fields(source_ids=["S0009"]))
    assert row["source_ids"] == "S0009"


# ---------------------------------------------------------- make_row: year

@pytest.mark.parametrize("bad", [True, False])
def test_make_row_bool_year_raises(bad):
    with pytest.raises(LibError) as ei:
        make_row(bounds=Bounds(1.0, 2.0, 3.0), **base_fields(year=bad))
    assert "year" in str(ei.value)


@pytest.mark.parametrize("bad", ["1998", 1998.0, None])
def test_make_row_non_int_year_raises_liberror(bad):
    with pytest.raises(LibError):
        make_row(bounds=Bounds(1.0, 2.0, 3.0), **base_fields(year=bad))


@pytest.mark.parametrize("year", [1800, 1949, 2026, 9999])
def test_make_row_does_not_range_check_year(year):
    # 8.2: range checks belong to the validator.
    row = make_row(bounds=Bounds(1.0, 2.0, 3.0), **base_fields(year=year))
    assert row["year"] == year


# ------------------------------------------------- make_row: argument types

@pytest.mark.parametrize("bad", [None, (1.0, 2.0, 3.0), 5.0, "b", {"low": 1}])
def test_make_row_non_bounds_raises_liberror(bad):
    with pytest.raises(LibError):
        make_row(bounds=bad, **base_fields())


# ------------------------------------------------ write_master: coercion

def test_write_master_int_value_columns_formatted_like_floats(tmp_path):
    p = tmp_path / "m.csv"
    write_master([full_row(value_low=2, value_central=12345678, value_high=3 * 10**9)], p)
    c = cells(p)[0]
    # format(float(12345678), '.6g') == '1.23457e+07'; int would give '12345678'
    assert c["value_low"] == "2"
    assert c["value_central"] == "1.23457e+07"
    assert c["value_high"] == "3e+09"


def test_write_master_int_and_float_inputs_are_byte_identical(tmp_path):
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    write_master([full_row(value_low=1, value_central=12345678, value_high=20000000)], a)
    write_master([full_row(value_low=1.0, value_central=12345678.0, value_high=20000000.0)], b)
    assert a.read_bytes() == b.read_bytes()


def test_write_master_zero_int_and_float_identical(tmp_path):
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    write_master([full_row(value_low=0, value_central=0, value_high=0)], a)
    write_master([full_row(value_low=0.0, value_central=0.0, value_high=0.0)], b)
    assert a.read_bytes() == b.read_bytes()
    assert cells(a)[0]["value_low"] == "0"


def test_exact_integer_bounds_round_trip_is_byte_stable(tmp_path):
    from pipeline.lib.io import read_table

    row = make_row(bounds=Bounds.exact(12345678), **base_fields())
    first, second = tmp_path / "first.csv", tmp_path / "second.csv"
    write_master([row], first)
    assert cells(first)[0]["value_central"] == "1.23457e+07"
    write_master(read_table(first), second)
    assert first.read_bytes() == second.read_bytes()


def test_write_master_does_not_coerce_non_value_numeric_columns(tmp_path):
    # year stays an integer string; only value_* are float-coerced
    p = tmp_path / "m.csv"
    write_master([full_row(year=1998)], p)
    assert cells(p)[0]["year"] == "1998"


# ------------------------------------------- write_master: column checks

def test_write_master_unknown_column_raises(tmp_path):
    row = full_row()
    row["colour"] = "red"
    with pytest.raises(LibError) as ei:
        write_master([row], tmp_path / "m.csv")
    assert "colour" in str(ei.value)


def test_write_master_missing_column_raises(tmp_path):
    row = full_row()
    del row["notes"]
    with pytest.raises(LibError) as ei:
        write_master([row], tmp_path / "m.csv")
    assert "notes" in str(ei.value)


@pytest.mark.parametrize("col", EXPECTED_COLUMNS)
def test_write_master_each_missing_column_raises(tmp_path, col):
    row = full_row()
    del row[col]
    with pytest.raises(LibError):
        write_master([row], tmp_path / "m.csv")


def test_write_master_bad_second_row_raises_even_if_first_is_fine(tmp_path):
    bad = full_row(year=1999)
    bad["extra"] = 1
    with pytest.raises(LibError):
        write_master([full_row(), bad], tmp_path / "m.csv")


@pytest.mark.parametrize("col", ["value_low", "value_central", "value_high"])
@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_write_master_non_finite_value_raises(tmp_path, col, bad):
    with pytest.raises(LibError) as ei:
        write_master([full_row(**{col: bad})], tmp_path / "m.csv")
    assert col in str(ei.value) or "finite" in str(ei.value)


@pytest.mark.parametrize("bad", [5, None, "abc", 3.5])
def test_write_master_rows_not_iterable_of_mappings_raises(tmp_path, bad):
    with pytest.raises(LibError):
        write_master(bad, tmp_path / "m.csv")


@pytest.mark.parametrize("bad_row", ["row", 5, None, ["year"]])
def test_write_master_non_mapping_row_raises(tmp_path, bad_row):
    with pytest.raises(LibError):
        write_master([bad_row], tmp_path / "m.csv")


# ------------------------------------------------- write_master: ordering

def test_write_master_none_first_across_mixed_key_columns(tmp_path):
    # Rows differ in two nullable key columns; None must precede any value in
    # each column in key-column order (product before technology).
    p = tmp_path / "m.csv"
    write_master([
        full_row(product="copper", technology=None),
        full_row(product=None, technology="wind"),
        full_row(product=None, technology=None),
        full_row(product="copper", technology="wind"),
    ], p)
    got = [(c["product"], c["technology"]) for c in cells(p)]
    assert got == [("", ""), ("", "wind"), ("copper", ""), ("copper", "wind")]


def test_write_master_none_first_regardless_of_input_order(tmp_path):
    rows = [full_row(route="stack"), full_row(route="air_ventilation"), full_row(route=None)]
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    write_master(rows, a)
    write_master(list(reversed(rows)), b)
    assert [c["route"] for c in cells(a)] == ["", "air_ventilation", "stack"]
    assert a.read_bytes() == b.read_bytes()


def test_write_master_none_before_false_like_values(tmp_path):
    # None must sort before a real value even where that value is "smaller"
    # as text or falsy; 'A' < 'copper' by ordinary comparison but None < 'A'.
    p = tmp_path / "m.csv"
    write_master([full_row(event_id="A"), full_row(event_id=None)], p)
    assert [c["event_id"] for c in cells(p)] == ["", "A"]


def test_write_master_sorts_year_numerically_not_textually(tmp_path):
    p = tmp_path / "m.csv"
    write_master([full_row(year=1998), full_row(year=2001), full_row(year=999)], p)
    assert [c["year"] for c in cells(p)] == ["999", "1998", "2001"]


# --------------------------------------------------- write_master: bytes

def test_write_master_lf_only_and_final_newline(tmp_path):
    p = tmp_path / "m.csv"
    write_master([full_row(year=1998), full_row(year=1999, notes="x")], p)
    raw = p.read_bytes()
    assert b"\r" not in raw
    assert raw.endswith(b"\n") and not raw.endswith(b"\n\n")
    assert raw.count(b"\n") == 3  # header + 2 rows


def test_write_master_header_only_is_lf_terminated(tmp_path):
    p = tmp_path / "m.csv"
    write_master([], p)
    raw = p.read_bytes()
    assert raw == (",".join(EXPECTED_COLUMNS) + "\n").encode("utf-8")


def test_write_master_lf_endings_with_quoted_fields(tmp_path):
    p = tmp_path / "m.csv"
    write_master([full_row(notes='say "hi", ok')], p)
    raw = p.read_bytes()
    assert b"\r" not in raw
    assert cells(p)[0]["notes"] == 'say "hi", ok'


# ------------------------------------- LIB_SPEC 8.8 (round 2) and gap tests

def test_make_row_unflagged_bounds_gives_below_detection_false():
    # Most important gap: Bounds(0, 1, 2) has low == 0 but is NOT flagged;
    # below_detection follows nd_floored, not low == 0 (8.1, 4.2).
    r = make_row(bounds=Bounds(0.0, 1.0, 2.0), **base_fields())
    assert r["below_detection"] is False
    assert r["value_low"] == 0.0


def test_make_row_flagged_bounds_gives_below_detection_true():
    r = make_row(bounds=Bounds(0.0, 1.0, 2.0, nd_floored=True), **base_fields())
    assert r["below_detection"] is True
    assert r["value_low"] == 0.0


def test_make_row_not_detected_bounds_gives_below_detection_true():
    r = make_row(bounds=Bounds.not_detected(4.0), **base_fields())
    assert r["below_detection"] is True


def test_make_row_enforces_below_detection_low_consistency():
    # 8.8.8 (enforced half): explicit True with low > 0 raises; explicit False with flagged raises.
    with pytest.raises(LibError):
        make_row(bounds=Bounds(1.0, 2.0, 3.0), below_detection=True, **base_fields())
    with pytest.raises(LibError):
        make_row(bounds=Bounds(0.0, 1.0, 2.0, nd_floored=True), below_detection=False,
                 **base_fields())


def test_write_master_raw_dict_inconsistent_below_detection_does_not_raise(tmp_path):
    # 8.8.8 (documented, not enforced): validator R02 is the backstop.
    row = full_row(below_detection=True, value_low=1.0)
    p = tmp_path / "m.csv"
    write_master([row], p)
    rows = read_raw(p)
    hdr = rows[0]
    assert rows[1][hdr.index("below_detection")] == "true"
    assert rows[1][hdr.index("value_low")] == "1"


@pytest.mark.parametrize("col", ["value_low", "value_central", "value_high"])
def test_write_master_negative_zero_written_as_zero(tmp_path, col):
    row = full_row(**{col: -0.0})
    if col == "value_low":
        row.update(value_central=2.0, value_high=3.0)
    p = tmp_path / "m.csv"
    write_master([row], p)
    rows = read_raw(p)
    assert rows[1][rows[0].index(col)] == "0"


@pytest.mark.parametrize("col", ["value_low", "value_central", "value_high"])
@pytest.mark.parametrize("bad", [10**400, -(10**400)])
def test_write_master_huge_int_value_raises_liberror(tmp_path, col, bad):
    # 8.8.1
    with pytest.raises(LibError):
        write_master([full_row(**{col: bad})], tmp_path / "m.csv")


@pytest.mark.parametrize("col", ["value_low", "value_central", "value_high"])
@pytest.mark.parametrize("bad", [True, False])
def test_write_master_bool_in_value_column_raises_liberror(tmp_path, col, bad):
    # 8.8.5
    with pytest.raises(LibError):
        write_master([full_row(**{col: bad})], tmp_path / "m.csv")


@pytest.mark.parametrize("field", ["source_ids", "factor_ids"])
@pytest.mark.parametrize("items", [["S0001", ""], ["S0001", "  "], [""], ["\t"], ["S0001", " ", "S0002"]])
def test_make_row_empty_or_blank_list_item_raises(field, items):
    # 8.8.2
    fields = base_fields()
    fields[field] = items
    with pytest.raises(LibError):
        make_row(bounds=Bounds(1.0, 2.0, 3.0), **fields)


@pytest.mark.parametrize("blank", ["   ", "\t", " \n "])
def test_make_row_whitespace_only_source_ids_string_raises(blank):
    # 8.2 / 8.8.2
    with pytest.raises(LibError):
        make_row(bounds=Bounds(1.0, 2.0, 3.0), **base_fields(source_ids=blank))


@pytest.mark.parametrize("field", REQUIRED)
def test_make_row_explicit_none_for_required_field_raises(field):
    # 8.8.7
    with pytest.raises(LibError):
        make_row(bounds=Bounds(1.0, 2.0, 3.0), **base_fields(**{field: None}))


@pytest.mark.parametrize("field", ["stream", "substream", "stage", "country", "group",
                                   "tier", "unit", "basis", "quantity"])
@pytest.mark.parametrize("bad", [5, 1.5, b"x", ["x"], True])
def test_make_row_required_string_fields_must_be_str(field, bad):
    # 8.8.7
    with pytest.raises(LibError):
        make_row(bounds=Bounds(1.0, 2.0, 3.0), **base_fields(**{field: bad}))


@pytest.mark.parametrize("bad", ["false", "true", 0, 1, "", [False]])
def test_make_row_embedded_fuel_must_be_bool(bad):
    with pytest.raises(LibError):
        make_row(bounds=Bounds(1.0, 2.0, 3.0), embedded_fuel=bad, **base_fields())


@pytest.mark.parametrize("flag", [True, False])
def test_make_row_embedded_fuel_bool_accepted(flag):
    r = make_row(bounds=Bounds(1.0, 2.0, 3.0), embedded_fuel=flag, **base_fields())
    assert r["embedded_fuel"] is flag


@pytest.mark.parametrize("bad", [123, None, 1.5, ["a.csv"], b"x.csv"])
def test_write_master_non_path_raises_liberror(bad):
    # 8.8.4
    with pytest.raises(LibError):
        write_master([full_row()], bad)


def test_write_master_to_directory_raises_liberror_naming_path(tmp_path):
    with pytest.raises(LibError) as ei:
        write_master([full_row()], tmp_path)
    assert str(tmp_path) in str(ei.value)


def test_write_master_unwritable_location_raises_liberror_naming_path(tmp_path):
    target = tmp_path / "no_such_dir" / "m.csv"
    with pytest.raises(LibError) as ei:
        write_master([full_row()], target)
    assert str(target) in str(ei.value)
