"""Spec-blind tests for SCHEMA v2.3: residue_seepage_by_group.csv (section 4.12, D56) and
the pre-1950 stream files (section 3.2, D57).

Written from docs/SCHEMA.md (sections 2, 4.10, 4.12, 6.1, 6.3-6.5), docs/DECISIONS.md (D56, D57)
and the data files only. validate.py and schema/*.json were not read.

Rule-code assumptions (SCHEMA 6.3 does not list the new table in its T-code rows, so the
existing reference-table convention is applied; see the ambiguity list in the task report)
-----------------------------------------------------------------------------------------
A1. Row fails the table's JSON schema (type, range [0, 1], required cell empty, basis not in
    the enum, coercion failure)                                      -> T01
A2. Duplicate (residue_type, group)                                  -> T02 (on the later row)
A3. low <= central <= high violated                                  -> T03
A4. residue_type not in residue_types.csv, group not in groups.csv,
    a source id not in sources.csv                                   -> T04
A5. Header mismatch / extra or missing column / dose-token column    -> F01 / F02 (file level, "every table")
A6. The file is optional: absent means no issue and no exception (SCHEMA 2: "yes (when present)").
A7. Pre-1950 stream files are not validated: they never produce an issue.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from pipeline.validate import validate

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests.test_validate import (
    append_copy,
    assert_clean,
    assert_has,
    assert_only,
    corrupt,
    describe,
    read_csv,
    rules_of,
    vrow,
    write_csv,
    write_master,
)

REL = "data/reference/residue_seepage_by_group.csv"
COLUMNS = ["residue_type", "group", "seepage_low", "seepage_central", "seepage_high",
           "basis", "source_ids", "notes"]


def _issues_for(root, rel=REL):
    return [i for i in validate(root, []) if i.file == rel]


def _rows(root):
    return read_csv(Path(root) / REL)[1]


def _index_of(root, residue_type, group):
    for n, r in enumerate(_rows(root), 1):
        if r["residue_type"] == residue_type and r["group"] == group:
            return n
    raise AssertionError(f"{residue_type}/{group} not in the real table")


# --------------------------------------------------------------------------- the real tree

def test_real_file_has_the_documented_header():
    header, rows = read_csv(Path(__file__).resolve().parents[2] / REL)
    assert header == COLUMNS
    assert rows, "the released table should not be empty"


def test_real_tree_validates_clean_with_default_master_files(project_root):
    assert_clean(validate(project_root))


def test_real_tree_validates_clean_with_no_master_files(project_root):
    assert_clean(validate(project_root, []))


def test_unmodified_copy_in_temp_tree_is_clean(tmp_root):
    assert (tmp_root / REL).exists()
    assert_clean(validate(tmp_root, []))


# --------------------------------------------------------------------------- optional file

def test_absent_file_is_not_an_error(tmp_root):
    (tmp_root / REL).unlink()
    assert_clean(validate(tmp_root, []))


def test_header_only_file_is_valid(tmp_root):
    write_csv(tmp_root / REL, COLUMNS, [])
    assert_clean(validate(tmp_root, []))


# --------------------------------------------------------------------------- valid variations

def test_boundary_values_zero_and_one_and_equal_bounds_are_valid(tmp_root):
    corrupt(tmp_root, REL, 1, seepage_low="0", seepage_central="0", seepage_high="0")
    corrupt(tmp_root, REL, 2, seepage_low="1", seepage_central="1", seepage_high="1")
    corrupt(tmp_root, REL, 3, seepage_low="0", seepage_central="0.5", seepage_high="1")
    assert_clean(validate(tmp_root, []))


def test_exponent_notation_is_accepted(tmp_root):
    corrupt(tmp_root, REL, 1, seepage_low="1E-6", seepage_central="2.5e-06", seepage_high="3e-5")
    assert_clean(validate(tmp_root, []))


def test_empty_notes_are_valid(tmp_root):
    corrupt(tmp_root, REL, 1, notes="")
    assert_clean(validate(tmp_root, []))


def test_same_group_for_a_different_residue_type_is_not_a_duplicate(tmp_root):
    have = {(r["residue_type"], r["group"]) for r in _rows(tmp_root)}
    other = next(r["residue_type"] for r in _rows_of(tmp_root, "data/reference/residue_types.csv")
                 if (r["residue_type"], "K40") not in have)
    n = append_copy(tmp_root, REL, 1, residue_type=other, group="K40")
    keys = [(r["residue_type"], r["group"]) for r in _rows(tmp_root)]
    assert keys.count((other, "K40")) == 1, "test set-up: key must be new"
    assert_clean(validate(tmp_root, []))
    assert n == len(keys)


def test_residue_type_without_a_filled_seepage_set_may_have_rows(tmp_root):
    """SCHEMA 4.12: 'the validator does not require one for the other residue types'."""
    rt = _rows_of(tmp_root, "data/reference/residue_types.csv")
    empty = [r["residue_type"] for r in rt if not r["seepage_per_a_central"]]
    assert empty, "test set-up: the real table has residue types with an empty seepage set"
    append_copy(tmp_root, REL, 1, residue_type=empty[0], group="K40")
    assert_clean(validate(tmp_root, []))


def _rows_of(root, rel):
    return read_csv(Path(root) / rel)[1]


def test_residue_type_may_have_no_rows_fallback_to_residue_type_triple(tmp_root):
    """Absence of a row means 'same as the residue-type triple', not an error."""
    write_csv(tmp_root / REL, COLUMNS, [r for r in _rows(tmp_root) if r["residue_type"] != "coal_fly_ash"])
    assert_clean(validate(tmp_root, []))


def test_every_released_row_group_is_a_head_code_in_groups(tmp_root):
    heads = {r["group"] for r in _rows_of(tmp_root, "data/reference/groups.csv")}
    assert {r["group"] for r in _rows(tmp_root)} <= heads


# --------------------------------------------------------------------------- T04 references

def test_t04_unknown_residue_type(tmp_root):
    corrupt(tmp_root, REL, 2, residue_type="no_such_residue")
    assert_only(validate(tmp_root, []), "T04", rows=[2], file=REL)


def test_t04_unknown_group(tmp_root):
    corrupt(tmp_root, REL, 2, group="Zz999")
    assert_only(validate(tmp_root, []), "T04", rows=[2], file=REL)


def test_t04_group_must_be_a_head_code_not_a_nuclide_name(tmp_root):
    """'U-238' is a nuclide (the head of U238+), not a group code."""
    corrupt(tmp_root, REL, 2, group="U-238")
    assert_only(validate(tmp_root, []), "T04", rows=[2], file=REL)


@pytest.mark.parametrize("ids", ["S0099", "S0955;S0099", "S0099;S0955"])
def test_t04_unresolved_source_id(tmp_root, ids):
    corrupt(tmp_root, REL, 1, source_ids=ids)
    assert_only(validate(tmp_root, []), "T04", rows=[1], file=REL)


def test_t04_reports_each_bad_row(tmp_root):
    corrupt(tmp_root, REL, 1, group="Zz999")
    corrupt(tmp_root, REL, 3, residue_type="no_such_residue")
    assert_only(validate(tmp_root, []), "T04", rows=[1, 3], file=REL)


# --------------------------------------------------------------------------- T02 duplicates

def test_t02_duplicate_key_reported_on_the_later_row_only(tmp_root):
    later = append_copy(tmp_root, REL, 1)
    assert_only(validate(tmp_root, []), "T02", rows=[later], file=REL)


def test_t02_duplicate_key_ignores_values_basis_sources_and_notes(tmp_root):
    later = append_copy(tmp_root, REL, 1, seepage_low="0.1", seepage_central="0.2", seepage_high="0.3",
                        source_ids="S0954", notes="another derivation")
    assert_only(validate(tmp_root, []), "T02", rows=[later], file=REL)


def test_t02_duplicate_of_a_non_adjacent_row(tmp_root):
    n_rows = len(_rows(tmp_root))
    later = append_copy(tmp_root, REL, 5)
    assert later == n_rows + 1
    assert_only(validate(tmp_root, []), "T02", rows=[later], file=REL)


# --------------------------------------------------------------------------- T03 ordering

@pytest.mark.parametrize("low, central, high", [
    ("0.5", "0.1", "0.9"),      # low > central
    ("0.1", "0.9", "0.5"),      # central > high
    ("0.9", "0.5", "0.1"),      # reversed
    ("0.2", "0.1", "0.1"),
    ("1e-3", "1e-4", "1e-5"),
], ids=["low-gt-central", "central-gt-high", "reversed", "low-gt-both", "exponent-reversed"])
def test_t03_bounds_out_of_order(tmp_root, low, central, high):
    corrupt(tmp_root, REL, 2, seepage_low=low, seepage_central=central, seepage_high=high)
    assert_only(validate(tmp_root, []), "T03", rows=[2], file=REL)


# --------------------------------------------------------------------------- T01 schema

@pytest.mark.parametrize("changes", [
    {"seepage_high": "1.5"},
    {"seepage_low": "-0.1"},
    {"seepage_low": "-1e-9"},
    {"seepage_central": "2"},
    {"seepage_low": "1.0000001", "seepage_central": "1.0000002", "seepage_high": "1.0000003"},
], ids=["high-above-1", "low-negative", "low-slightly-negative", "central-above-1", "all-just-above-1"])
def test_t01_values_outside_0_1(tmp_root, changes):
    corrupt(tmp_root, REL, 1, **changes)
    assert "T01" in rules_of(_issues_for(tmp_root)), describe(validate(tmp_root, []))
    assert {i.row for i in _issues_for(tmp_root)} == {1}
    assert rules_of(validate(tmp_root, [])) <= {"T01", "T03"}


@pytest.mark.parametrize("col", ["seepage_low", "seepage_central", "seepage_high"])
@pytest.mark.parametrize("bad", ["", "n/a", "nan", "inf", "abc"], ids=["empty", "text", "nan", "inf", "word"])
def test_t01_each_value_is_required_and_numeric(tmp_root, col, bad):
    corrupt(tmp_root, REL, 1, **{col: bad})
    assert_has(validate(tmp_root, []), "T01", 1, REL)
    assert {i.row for i in _issues_for(tmp_root)} == {1}


def test_t01_all_three_values_empty_is_not_allowed(tmp_root):
    """Unlike the 4.10 sets, an all-empty triple is not 'not yet set': all three are required."""
    corrupt(tmp_root, REL, 1, seepage_low="", seepage_central="", seepage_high="")
    assert_has(validate(tmp_root, []), "T01", 1, REL)


@pytest.mark.parametrize("col", ["residue_type", "group", "basis", "source_ids"])
def test_t01_required_text_cells_may_not_be_empty(tmp_root, col):
    corrupt(tmp_root, REL, 1, **{col: ""})
    assert_has(validate(tmp_root, []), "T01", 1, REL)
    assert {i.row for i in _issues_for(tmp_root)} == {1}


def test_t01_basis_not_in_enum(tmp_root):
    corrupt(tmp_root, REL, 1, basis="guess")
    assert_only(validate(tmp_root, []), "T01", rows=[1], file=REL)


def test_basis_values_other_than_modelled_are_accepted(tmp_root):
    """'as master': 'modelled' is merely the first-release value."""
    corrupt(tmp_root, REL, 1, basis="compiled")
    assert_clean(validate(tmp_root, []))


# --------------------------------------------------------------------------- F01 / F02

def test_f01_missing_column(tmp_root):
    rows = _rows(tmp_root)
    write_csv(tmp_root / REL, [c for c in COLUMNS if c != "notes"], rows)
    issues = _issues_for(tmp_root)
    assert rules_of(issues) == {"F01"}, describe(issues)
    assert all(i.row is None for i in issues)
    assert rules_of(validate(tmp_root, [])) == {"F01"}


def test_f01_columns_out_of_order(tmp_root):
    rows = _rows(tmp_root)
    hdr = COLUMNS[:]
    hdr[2], hdr[4] = hdr[4], hdr[2]
    write_csv(tmp_root / REL, hdr, rows)
    assert rules_of(_issues_for(tmp_root)) == {"F01"}


def test_f01_wrong_column_name(tmp_root):
    rows = [dict(r, seepage_per_a_low=r["seepage_low"]) for r in _rows(tmp_root)]
    hdr = ["seepage_per_a_low" if c == "seepage_low" else c for c in COLUMNS]
    write_csv(tmp_root / REL, hdr, rows)
    assert rules_of(_issues_for(tmp_root)) == {"F01"}


def test_f01_f02_dose_token_column(tmp_root):
    rows = [dict(r, collective_dose="0") for r in _rows(tmp_root)]
    write_csv(tmp_root / REL, COLUMNS + ["collective_dose"], rows)
    issues = _issues_for(tmp_root)
    assert rules_of(issues) == {"F01", "F02"}, describe(issues)
    assert all(i.row is None for i in issues)


def test_f01_file_rows_are_not_validated(tmp_root):
    """SCHEMA 6.5: a file with F01 has its data rows skipped."""
    rows = _rows(tmp_root)
    rows[0]["group"] = "Zz999"
    write_csv(tmp_root / REL, COLUMNS + ["extra"], rows)
    assert rules_of(_issues_for(tmp_root)) == {"F01"}


def test_f03_not_utf8(tmp_root):
    (tmp_root / REL).write_bytes(b"residue_type,group\n\xff\xfe\x00bad\n")
    assert "F03" in rules_of(_issues_for(tmp_root)), describe(validate(tmp_root, []))


# --------------------------------------------------------------------------- multi-fault rows

def test_issues_are_sorted_by_file_then_row(tmp_root):
    corrupt(tmp_root, REL, 3, group="Zz999")
    corrupt(tmp_root, REL, 1, group="Zz999")
    issues = validate(tmp_root, [])
    assert issues == sorted(issues, key=lambda i: (i.file, -1 if i.row is None else i.row, i.rule))


def test_ordering_and_reference_faults_are_both_reported_on_one_row(tmp_root):
    corrupt(tmp_root, REL, 1, seepage_low="0.9", seepage_central="0.1", seepage_high="0.5", group="Zz999")
    issues = _issues_for(tmp_root)
    assert {"T03", "T04"} <= rules_of(issues), describe(issues)


# --------------------------------------------------------------------------- pre-1950 stream files (D57)

def test_real_pre1950_files_cause_no_issues(project_root):
    assert list((project_root / "data" / "streams_pre1950").glob("*.csv*")), "test set-up: real file exists"
    assert_clean(validate(project_root, []))


def test_pre1950_file_with_master_columns_and_1800_years_is_not_validated(tmp_root):
    d = tmp_root / "data" / "streams_pre1950"
    d.mkdir()
    # a pre-1950 flow row: year outside the master schema's 1950-2025 range
    row = vrow(1, year="1800", quantity="flow", unit="Bq/a", tier="liberated", route="air_stack",
               stage="coal_mining", stream="coal", substream="all", residue_type="")
    write_csv(d / "coal.csv", list(row.keys()), [row])
    assert_clean(validate(tmp_root, []))


def test_pre1950_file_with_garbage_content_causes_no_issues(tmp_root):
    d = tmp_root / "data" / "streams_pre1950"
    d.mkdir()
    (d / "coal.csv").write_text("not,the,master,header\n1,2,3\nS9999,,,\xff\n", encoding="utf-8", errors="replace")
    (d / "other.csv").write_bytes(b"\xff\xfe\x00 not utf-8")
    assert_clean(validate(tmp_root, []))


def test_pre1950_files_are_not_picked_up_as_default_master_files(tmp_root):
    """Default masters are data/streams/*.csv only; a bad pre-1950 file must not appear in the issues."""
    d = tmp_root / "data" / "streams_pre1950"
    d.mkdir()
    row = vrow(1, year="1800", unit="wrong unit", group="Zz999", source_ids="S0099")
    write_csv(d / "coal.csv", list(row.keys()), [row])
    issues = validate(tmp_root)
    assert not [i for i in issues if "streams_pre1950" in i.file], describe(issues)
    assert_clean(issues)


def test_pre1950_files_are_not_counted_in_cross_row_rules(tmp_root):
    """A row in streams_pre1950 duplicating a data/streams row (X01 key) must not raise X01."""
    row = vrow(1)
    write_master(tmp_root, "coal.csv", [row])
    d = tmp_root / "data" / "streams_pre1950"
    d.mkdir()
    write_csv(d / "coal.csv", list(row.keys()), [row, row])
    assert_clean(validate(tmp_root))


def test_master_schema_still_rejects_1800_in_data_streams(tmp_root):
    """Contrast case (D14): the master schema's year range is 1950-2025, which is why D57 files sit outside it."""
    rel = write_master(tmp_root, "coal.csv", [vrow(1, year="1800")])
    assert_has(validate(tmp_root), "R02", 1, rel)
