"""Spec-blind tests for the Radiopassive data validator (Task 0.2).

Plan done condition: "validate.py accepts 10 hand-written valid example rows and
rejects 10 deliberately invalid rows (wrong unit, missing source, low > high,
unknown nuclide, etc.)."

Written from docs/SCHEMA.md (section 6 is binding), schema/*.json and the real
reference tables only. Only pytest, the standard library and the public API in
SCHEMA.md section 6.1 are used.

Mapping to the done condition
-----------------------------
* fixtures/valid_rows.csv          -> the 10 valid rows (test_valid_rows_*).
* fixtures/invalid/*.csv + cases.json -> the 10 invalid rows (test_invalid_case).
* Everything else extends the same contract: other rule codes, file-level
  rules, reference tables, cross-file behaviour, ordering, CLI.

AMBIGUITIES IN SCHEMA.md SECTION 6 (resolved here as noted; tests avoid
asserting anything beyond the stated reading)
------------------------------------------------------------------------
A1. Issue.file for a master file that lies OUTSIDE the root is undefined. Tests
    only pass master files located inside the temporary root (relative path,
    absolute str or absolute Path) and expect "data/streams/<name>".
A2. "The later file" for a cross-file X01 is read as "later in the order of
    master_files". Tests pass an explicit list.
A3. Which row carries a duplicate-source_id S01 / duplicate-event_id E01 (first
    or later occurrence) is unspecified. Tests accept either.
A4. Whether other rules still run on a row that raised R01 (and whether R02 is
    also reported) is unspecified. R01 tests assert R01 at the row only.
A5. Whether data rows are still validated after a file-level F01/F02/F03 issue
    is unspecified. File-level tests assert the F-codes (row None) only.
A6. Inclusivity of valid_from/valid_to in countries.csv is not stated. Tests
    use years clearly inside or clearly outside the window, never the bounds.
A7. CLI: whether FILE arguments are relative to the cwd or to --root, whether
    issue lines go to stdout or stderr, and whether the printed file is
    root-relative or as given, is unspecified. CLI tests pass absolute FILE
    paths, read stdout+stderr together, and match only ":<row>: <RULE>".
A8. An unknown event_id (V08) or a missing events.csv: whether X05 is skipped is
    implied ("tier does not match its event") but not stated. The no-events.csv
    test expects exactly V08 on the transfer rows.
A9. Behaviour of V03 and V01/V02 when stage or stream is unknown: V02 is raised
    for an unknown stage, but whether V03 is also raised is unspecified, so no
    test asserts either way beyond the stated "invalid stream/tier skips V01-V03 /
    V03" notes.
A10. S02 "banned domain": the host is taken to be the test; a banned name that
    appears only in the URL path, or as a suffix of a longer label
    ("notwikipedia.org"), is read as NOT banned.
A11. X03 on a single master file with only non-default variants: reported once
    per key on the key's first row (stated). Which row number that is when the
    key's rows are in several files is unspecified; tests keep each key in one
    file.
A12. A header-only master file is read as valid (no rows, no issues).
A13. SCHEMA section 4.2 says the flow_only rule applies to "a stock tier", while
    section 6.3 (V09) says any quantity other than flow. Section 6.3 is binding
    and is what V09 tests encode.
A14. Row ordering inside the "by file, then row, then rule" ordering: file-level
    (row None) first; files compared as root-relative POSIX strings.
"""
from __future__ import annotations

import csv
import dataclasses
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from pipeline.validate import Issue, validate

TESTS_DIR = Path(__file__).resolve().parent
FIXTURES = TESTS_DIR / "fixtures"
INVALID_DIR = FIXTURES / "invalid"
REAL_ROOT = TESTS_DIR.parents[1]

MASTER_COLUMNS = [
    "year", "stream", "substream", "stage", "country", "group", "tier", "quantity", "unit",
    "value_low", "value_central", "value_high", "below_detection", "basis", "source_ids",
    "allocation_variant", "allocation_rule", "embedded_fuel", "technology", "event_id", "notes",
]


# --------------------------------------------------------------------------- helpers

def read_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return list(reader.fieldnames), list(reader)


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=header, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


VALID_HEADER, VALID_ROWS = read_csv(FIXTURES / "valid_rows.csv")


HALF = dict(value_low="3.5e16", value_central="4.25e16", value_high="5.0e16")  # half of E001 Cs137+ release


def vrow(n, **changes):
    """Copy of valid fixture row n (1-based) with cell overrides."""
    row = dict(VALID_ROWS[n - 1])
    row.update({k: str(v) for k, v in changes.items()})
    return row


def write_master(root, name, rows, header=None):
    """Write a master file into <root>/data/streams/<name>; return the root-relative POSIX path."""
    rel = f"data/streams/{name}"
    write_csv(Path(root) / rel, header or MASTER_COLUMNS, rows)
    return rel


def describe(issues):
    return "\n".join(f"  {i.file}:{i.row}: {i.rule} {i.message}" for i in issues) or "  (no issues)"


def rules_of(issues):
    return {i.rule for i in issues}


def assert_clean(issues):
    assert issues == [], f"expected no issues, got:\n{describe(issues)}"


def assert_only(issues, rule, rows=None, file=None):
    """Exactly one rule code appears; optionally at the given rows and in the given file."""
    assert issues, f"expected {rule}, got no issues"
    assert rules_of(issues) == {rule}, f"expected only {rule}, got:\n{describe(issues)}"
    if rows is not None:
        assert {i.row for i in issues} == set(rows), f"{rule} on wrong rows:\n{describe(issues)}"
    if file is not None:
        assert {i.file for i in issues} == {file}, f"{rule} in wrong file:\n{describe(issues)}"
    assert all(isinstance(i.message, str) and i.message for i in issues)


def edit_csv(path, mutate):
    header, rows = read_csv(path)
    mutate(rows)
    write_csv(path, header, rows)
    return header, rows


def find_index(rows, column, value):
    """1-based data-row number of the row whose column equals value."""
    for n, row in enumerate(rows, 1):
        if row[column] == value:
            return n
    raise AssertionError(f"{column}={value!r} not found")


# --------------------------------------------------------------------------- Issue type

def test_issue_is_a_frozen_dataclass_with_the_documented_fields():
    assert dataclasses.is_dataclass(Issue)
    assert [f.name for f in dataclasses.fields(Issue)] == ["file", "row", "rule", "message"]
    issue = Issue("data/streams/coal.csv", 3, "V03", "tier not allowed")
    assert (issue.file, issue.row, issue.rule, issue.message) == ("data/streams/coal.csv", 3, "V03", "tier not allowed")
    with pytest.raises(dataclasses.FrozenInstanceError):
        issue.row = 4  # type: ignore[misc]
    assert Issue("f", None, "X02", "m") == Issue("f", None, "X02", "m")


# --------------------------------------------------------------------------- valid rows

def test_fixture_has_exactly_ten_valid_rows_in_section_3_column_order():
    assert VALID_HEADER == MASTER_COLUMNS
    assert len(VALID_ROWS) == 10


def test_valid_rows_yield_no_issues(tmp_root):
    rel = write_master(tmp_root, "valid.csv", VALID_ROWS)
    assert_clean(validate(tmp_root, [rel]))


def test_valid_fixture_file_copied_verbatim_yields_no_issues(tmp_root):
    shutil.copy(FIXTURES / "valid_rows.csv", tmp_root / "data" / "streams" / "valid_rows.csv")
    assert_clean(validate(tmp_root, ["data/streams/valid_rows.csv"]))


def test_valid_rows_cover_all_five_streams_and_required_features():
    streams = {r["stream"] for r in VALID_ROWS}
    assert streams == {"nuclear", "coal", "oil_gas", "wind_solar", "other"}
    assert {r["quantity"] for r in VALID_ROWS} == {"flow", "transfer_out", "transfer_in", "standing_inventory"}
    assert {"reisolated", "dispersed", "memo_earth_moved", "sealed_in_core"} <= {r["tier"] for r in VALID_ROWS}
    assert any(r["below_detection"] == "true" for r in VALID_ROWS)
    assert any(r["embedded_fuel"] == "true" and r["stream"] == "wind_solar" for r in VALID_ROWS)
    assert any(r["country"] == "SUN" and r["year"] == "1980" for r in VALID_ROWS)
    assert any(r["stage"] == "u_milling" and r["allocation_rule"].startswith("civil:") for r in VALID_ROWS)


def test_valid_rows_accept_str_path_pathlike_absolute_and_generator(tmp_root):
    rel = write_master(tmp_root, "valid.csv", VALID_ROWS)
    absolute = tmp_root / rel
    assert_clean(validate(str(tmp_root), [rel]))
    assert_clean(validate(tmp_root, [Path(rel)]))
    assert_clean(validate(tmp_root, [absolute]))
    assert_clean(validate(tmp_root, [str(absolute)]))
    assert_clean(validate(tmp_root, (p for p in [rel])))


def test_header_only_master_file_is_valid(tmp_root):
    rel = write_master(tmp_root, "empty.csv", [])
    assert_clean(validate(tmp_root, [rel]))


@pytest.mark.parametrize(
    "changes",
    [
        pytest.param(dict(country="CSK", year=1960), id="CSK-in-window"),
        pytest.param(dict(country="DDR", year=1970), id="DDR-in-window"),
        pytest.param(dict(country="YUG", year=1985), id="YUG-in-window"),
        pytest.param(dict(country="DEU", year=1960), id="DEU-pre-1990-no-window"),
        pytest.param(dict(country="XWL"), id="XWL-aggregate"),
        pytest.param(dict(country="XXX"), id="XXX-remainder"),
        pytest.param(dict(value_low="2e13", value_central="2e13", value_high="2e13"), id="low-eq-central-eq-high"),
        pytest.param(dict(value_low="0", value_central="0", value_high="0"), id="all-zero"),
        pytest.param(dict(value_low="12000000000000", value_central="30000000000000.5", value_high="6E13"), id="plain-and-exponent-notation"),
        pytest.param(dict(year=1950), id="year-lower-bound"),
        pytest.param(dict(year=2025), id="year-upper-bound"),
        pytest.param(dict(notes='Quoted, with a comma and "quotes"'), id="notes-with-comma"),
        pytest.param(dict(technology="gas_power"), id="technology-populated"),
        pytest.param(dict(source_ids="S0001;S0002;S0003"), id="three-sources"),
        pytest.param(dict(group="Rn222+", quantity="flow"), id="flow-only-group-on-flow"),
        pytest.param(
            dict(stream="nuclear", substream="fuel_cycle", stage="u_mining_isl", tier="impounded",
                 allocation_rule="value;civil:ratio", country="KAZ", year=1999),
            id="civil-component-among-several-rules"),
        pytest.param(
            dict(stream="nuclear", substream="fuel_cycle", stage="u_mining_conv", tier="memo_earth_moved",
                 allocation_rule="civil:pre1965", country="AUS", year=1960),
            id="civil-pre1965-memo-earth-moved"),
    ],
)
def test_other_valid_single_rows(tmp_root, changes):
    rel = write_master(tmp_root, "one.csv", [vrow(5, **changes)])
    assert_clean(validate(tmp_root, [rel]))


def test_v03_is_not_raised_for_transfer_rows(tmp_root):
    # liberated is not an allowed tier at spent_fuel (section 5.3) but transfer rows are exempt from V03.
    rows = [
        vrow(3, stage="spent_fuel", substream="fuel_cycle"),
        vrow(4, stage="spent_fuel", substream="fuel_cycle"),
    ]
    rel = write_master(tmp_root, "transfers.csv", rows)
    assert_clean(validate(tmp_root, [rel]))


def test_default_only_keys_are_not_flagged_by_x03(tmp_root):
    rel = write_master(tmp_root, "default_only.csv", [vrow(5), vrow(9)])
    assert_clean(validate(tmp_root, [rel]))


# --------------------------------------------------------------------------- the 10 invalid cases

CASES = json.loads((INVALID_DIR / "cases.json").read_text(encoding="utf-8"))


def test_manifest_lists_ten_cases_covering_the_required_rules():
    assert len(CASES) == 10
    assert {c["rule"] for c in CASES.values()} >= {
        "R02", "V07", "R03", "V04", "V03", "V02", "X01", "X02", "X04", "V06",
    }
    for name, case in CASES.items():
        assert (INVALID_DIR / name).is_file(), name
        assert set(case) == {"rule", "row", "description"}


@pytest.mark.parametrize("name", sorted(CASES))
def test_invalid_case(tmp_root, name):
    case = CASES[name]
    shutil.copy(INVALID_DIR / name, tmp_root / "data" / "streams" / name)
    rel = f"data/streams/{name}"

    issues = validate(tmp_root, [rel])

    hits = [i for i in issues if i.rule == case["rule"]]
    assert hits, f"{name}: expected rule {case['rule']} ({case['description']}); got:\n{describe(issues)}"
    assert {i.file for i in hits} == {rel}, f"{name}: wrong file:\n{describe(issues)}"
    assert case["row"] in {i.row for i in hits}, (
        f"{name}: {case['rule']} expected at row {case['row']}; got rows {[i.row for i in hits]}")
    others = rules_of(issues) - {case["rule"]}
    assert not others, f"{name}: each case must break exactly one rule, but also raised {sorted(others)}:\n{describe(issues)}"
    assert all(i.message for i in issues)


# --------------------------------------------------------------------------- row-level rules R01 / R02 / R03

@pytest.mark.parametrize(
    "changes",
    [
        pytest.param(dict(below_detection="yes"), id="bool-yes"),
        pytest.param(dict(embedded_fuel="True"), id="bool-capitalised"),
        pytest.param(dict(below_detection="1"), id="bool-1"),
        pytest.param(dict(year="19x5"), id="year-not-int"),
        pytest.param(dict(year="1986.5"), id="year-not-int-decimal"),
        pytest.param(dict(value_central="abc"), id="float-not-number"),
        pytest.param(dict(source_ids=""), id="source-ids-empty"),
        pytest.param(dict(basis=""), id="required-cell-empty"),
        pytest.param(dict(country=""), id="required-cell-empty-country"),
        pytest.param(dict(value_low=""), id="required-float-empty"),
    ],
)
def test_r01_uncoercible_cell(tmp_root, changes):
    rel = write_master(tmp_root, "r01.csv", [vrow(5), vrow(9, **changes)])
    issues = validate(tmp_root, [rel])
    assert any(i.rule == "R01" and i.row == 2 and i.file == rel for i in issues), describe(issues)
    assert not [i for i in issues if i.row == 1], f"row 1 is valid:\n{describe(issues)}"


@pytest.mark.parametrize(
    "base, changes",
    [
        pytest.param(6, dict(value_low="1e8"), id="below-detection-with-nonzero-low"),
        pytest.param(2, dict(tier="liberated"), id="standing-inventory-outside-sealed-in-core"),
        pytest.param(2, dict(quantity="flow", unit="Bq/a"), id="sealed-in-core-with-flow"),
        pytest.param(2, dict(unit="Bq/a"), id="standing-inventory-unit-bq-per-a"),
        pytest.param(5, dict(embedded_fuel="true"), id="embedded-fuel-outside-wind-solar-or-construction"),
        pytest.param(5, dict(year="2026"), id="year-above-2025"),
        pytest.param(5, dict(year="1949"), id="year-below-1950"),
        pytest.param(5, dict(stream="solar"), id="invalid-stream-skips-v01-v03"),
        pytest.param(5, dict(tier="buried"), id="invalid-tier-skips-v03"),
        pytest.param(5, dict(basis="guess"), id="invalid-basis"),
        pytest.param(5, dict(allocation_rule="civil:xyz"), id="invalid-allocation-rule"),
        pytest.param(5, dict(value_low="-1"), id="negative-value"),
        pytest.param(5, dict(technology="fusion"), id="invalid-technology"),
        pytest.param(5, dict(source_ids="S0001;S0001"), id="duplicate-source-in-list"),
        pytest.param(5, dict(unit="Bq/s"), id="invalid-unit"),
    ],
)
def test_r02_schema_failure_is_reported_alone(tmp_root, base, changes):
    rel = write_master(tmp_root, "r02.csv", [vrow(9), vrow(base, **changes)])
    assert_only(validate(tmp_root, [rel]), "R02", rows=[2], file=rel)


def test_r02_flow_unit_must_be_bq_per_annum_and_stock_unit_bq(tmp_root):
    rel = write_master(tmp_root, "units.csv", [vrow(5, unit="Bq"), vrow(2, unit="Bq/a")])
    assert_only(validate(tmp_root, [rel]), "R02", rows=[1, 2], file=rel)


def test_r02_transfer_row_without_event_id(tmp_root):
    rel = write_master(tmp_root, "no_event.csv", [vrow(3, event_id="")])
    issues = validate(tmp_root, [rel])
    assert any(i.rule == "R02" and i.row == 1 for i in issues), describe(issues)


@pytest.mark.parametrize(
    "changes",
    [
        pytest.param(dict(value_low="9e13"), id="low-above-central"),
        pytest.param(dict(value_central="9e13"), id="central-above-high"),
        pytest.param(dict(value_central="5e12"), id="central-below-low"),
        pytest.param(dict(value_high="5e12"), id="high-below-low-and-central"),
    ],
)
def test_r03_ordering_of_low_central_high(tmp_root, changes):
    rel = write_master(tmp_root, "r03.csv", [vrow(9), vrow(5, **changes)])
    assert_only(validate(tmp_root, [rel]), "R03", rows=[2], file=rel)


# --------------------------------------------------------------------------- vocabulary membership V01-V09

@pytest.mark.parametrize(
    "rule, changes",
    [
        pytest.param("V01", dict(substream="wind"), id="V01-substream-of-another-stream"),
        pytest.param("V01", dict(substream="not_a_substream"), id="V01-unknown-substream"),
        pytest.param("V02", dict(stage="reactor_operation", tier="liberated"), id="V02-nuclear-stage-on-coal"),
        pytest.param("V03", dict(tier="memo_earth_moved"), id="V03-memo-at-non-mining-stage"),
        pytest.param("V03", dict(tier="sealed_fuel_cycle"), id="V03-sealed-tier-at-combustion"),
        pytest.param("V04", dict(group="Tc98"), id="V04-nuclide-not-a-group"),
        pytest.param("V04", dict(group="Cs137"), id="V04-head-without-plus"),
        pytest.param("V04", dict(group="Zz999"), id="V04-nonsense-group"),
        pytest.param("V05", dict(country="ZZZ"), id="V05-unknown-country"),
        pytest.param("V05", dict(country="CA"), id="V05-two-letter-country"),
        pytest.param("V06", dict(country="SUN", year=1992), id="V06-SUN-after-1991"),
        pytest.param("V06", dict(country="CSK", year=1993), id="V06-CSK-after-1992"),
        pytest.param("V06", dict(country="DDR", year=1991), id="V06-DDR-after-1990"),
        pytest.param("V06", dict(country="YUG", year=2007), id="V06-YUG-after-2006"),
        pytest.param("V07", dict(source_ids="S0001;S0099"), id="V07-one-of-two-unknown"),
        pytest.param("V07", dict(source_ids="S9001"), id="V07-real-id-absent-from-fixture-registry"),
        pytest.param("V08", dict(event_id="E099"), id="V08-unknown-event"),
    ],
)
def test_vocabulary_membership_rules_raise_one_code(tmp_root, rule, changes):
    rel = write_master(tmp_root, "vocab.csv", [vrow(9), vrow(5, **changes)])
    assert_only(validate(tmp_root, [rel]), rule, rows=[2], file=rel)


def test_v09_flow_only_group_with_transfer_quantities(tmp_root):
    # Kr88+ is a released_gas / flow_only group in groups.csv; a balanced E001 transfer pair is otherwise valid.
    rows = [vrow(3, group="Kr88+"), vrow(4, group="Kr88+")]
    rel = write_master(tmp_root, "v09.csv", rows)
    assert_only(validate(tmp_root, [rel]), "V09", rows=[1, 2], file=rel)


# --------------------------------------------------------------------------- cross-row rules X01-X05

def test_x01_duplicate_key_ignores_values_and_notes(tmp_root):
    rows = [vrow(5), vrow(5, value_central="4e13", value_high="9e13", notes="different")]
    rel = write_master(tmp_root, "dup.csv", rows)
    assert_only(validate(tmp_root, [rel]), "X01", rows=[2], file=rel)


@pytest.mark.parametrize(
    "changes",
    [
        pytest.param(dict(year=2016), id="year"),
        pytest.param(dict(country="IND"), id="country"),
        pytest.param(dict(group="Pb210+"), id="group"),
        pytest.param(dict(tier="liberated"), id="tier"),
        pytest.param(dict(technology="gas_power"), id="technology-different"),
        pytest.param(dict(technology=""), id="technology-null-vs-set"),
    ],
)
def test_x01_not_raised_when_key_differs(tmp_root, changes):
    rows = [vrow(5), vrow(5, **changes)]  # row 5 has technology coal_power
    rel = write_master(tmp_root, "distinct.csv", rows)
    assert_clean(validate(tmp_root, [rel]))


def test_x01_allocation_rule_is_not_part_of_the_key(tmp_root):
    rel = write_master(tmp_root, "same_key.csv", [vrow(5), vrow(5, allocation_rule="value")])
    assert_only(validate(tmp_root, [rel]), "X01", rows=[2], file=rel)


def test_x01_across_files_is_reported_on_the_later_file(tmp_root):
    a = write_master(tmp_root, "a.csv", VALID_ROWS)
    b = write_master(tmp_root, "b.csv", VALID_ROWS)
    issues = validate(tmp_root, [a, b])
    assert_only(issues, "X01", rows=range(1, 11), file=b)
    assert len(issues) == 10


def test_x02_unbalanced_transfer_is_reported_once_with_row_none(tmp_root):
    rows = [vrow(3), vrow(4, **HALF)]
    rel = write_master(tmp_root, "x02.csv", rows)
    issues = validate(tmp_root, [rel])
    assert_only(issues, "X02", rows=[None], file=rel)
    assert len(issues) == 1


@pytest.mark.parametrize(
    "changes, balanced",
    [
        pytest.param(dict(value_central="8.5000000085e16"), True, id="central-within-1e-6"),
        pytest.param(dict(value_low="7.0000000070e16"), True, id="low-within-1e-6"),
        pytest.param(dict(value_high="1.0001e17"), False, id="high-off-by-1e-4"),
        pytest.param(dict(value_low="6.9e16"), False, id="low-off-by-1e-2"),
        pytest.param(dict(value_central="8.5085e16"), False, id="central-off-by-1e-3"),
    ],
)
def test_x02_relative_tolerance_applies_to_low_central_and_high(tmp_root, changes, balanced):
    rel = write_master(tmp_root, "tol.csv", [vrow(3), vrow(4, **changes)])
    issues = validate(tmp_root, [rel])
    if balanced:
        assert_clean(issues)
    else:
        assert_only(issues, "X02", rows=[None], file=rel)


def test_x02_sums_several_rows_per_event_year_group_variant(tmp_root):
    # Two outgoing rows (different countries) balance one incoming row.
    out_a = vrow(3, country="UKR", value_low="3e16", value_central="4e16", value_high="5e16")
    out_b = vrow(3, country="BLR", value_low="4e16", value_central="4.5e16", value_high="5e16")
    in_row = vrow(4, value_low="7e16", value_central="8.5e16", value_high="1.0e17")
    rel = write_master(tmp_root, "sum.csv", [out_a, out_b, in_row])
    assert_clean(validate(tmp_root, [rel]))


def test_x02_considers_all_master_files_together(tmp_root):
    a = write_master(tmp_root, "a.csv", [vrow(3), vrow(5)])
    b = write_master(tmp_root, "b.csv", [vrow(4)])
    assert_clean(validate(tmp_root, [a, b]))


def test_x02_across_files_is_reported_against_the_first_file_containing_the_event(tmp_root):
    a = write_master(tmp_root, "a.csv", [vrow(5), vrow(3)])
    b = write_master(tmp_root, "b.csv", [vrow(4, **HALF)])
    issues = validate(tmp_root, [a, b])
    assert_only(issues, "X02", rows=[None], file=a)
    assert len(issues) == 1


def test_x02_missing_counterpart_is_unbalanced(tmp_root):
    rel = write_master(tmp_root, "lonely.csv", [vrow(3)])
    assert_only(validate(tmp_root, [rel]), "X02", rows=[None], file=rel)


def test_x03_only_non_default_variant_is_flagged_once_on_the_first_row(tmp_root):
    rows = [vrow(5, allocation_variant="bound_main", allocation_rule="value")]
    rel = write_master(tmp_root, "x03a.csv", rows)
    issues = validate(tmp_root, [rel])
    assert_only(issues, "X03", rows=[1], file=rel)
    assert len(issues) == 1


@pytest.mark.parametrize("order", [("default", "bound_main"), ("bound_main", "default"), ("bound_radio", "bound_main")])
def test_x03_missing_variant_is_reported_once_per_key_on_its_first_row(tmp_root, order):
    rows = [vrow(9)] + [vrow(5, allocation_variant=v, allocation_rule="value") for v in order]
    rel = write_master(tmp_root, "x03b.csv", rows)
    issues = validate(tmp_root, [rel])
    assert_only(issues, "X03", rows=[2], file=rel)
    assert len(issues) == 1


def test_x03_complete_variant_set_is_valid(tmp_root):
    rows = [
        vrow(5, allocation_variant="default", allocation_rule="value"),
        vrow(5, allocation_variant="bound_main", allocation_rule="value",
             value_low="2e13", value_central="4e13", value_high="7e13"),
        vrow(5, allocation_variant="bound_radio", allocation_rule="value",
             value_low="5e12", value_central="1e13", value_high="3e13"),
    ]
    rel = write_master(tmp_root, "x03c.csv", rows)
    assert_clean(validate(tmp_root, [rel]))


def test_x04_applies_to_each_uranium_mining_and_milling_stage(tmp_root):
    rows = [
        vrow(1, stage="u_mining_conv", allocation_rule="none", tier="impounded", year=1990),
        vrow(1, stage="u_mining_isl", allocation_rule="value", tier="impounded", year=1991),
        vrow(1, stage="u_milling", allocation_rule="mass;elec_share", tier="impounded", year=1992),
    ]
    rel = write_master(tmp_root, "x04.csv", rows)
    assert_only(validate(tmp_root, [rel]), "X04", rows=[1, 2, 3], file=rel)


def test_x04_does_not_apply_to_other_streams_or_stages(tmp_root):
    rows = [vrow(5, allocation_rule="none"), vrow(1, stage="conv_enrich_fab", tier="impounded", allocation_rule="none")]
    rel = write_master(tmp_root, "x04b.csv", rows)
    assert_clean(validate(tmp_root, [rel]))


def test_x05_transfer_tier_must_match_event_tiers(tmp_root):
    # E001 runs sealed_in_core -> liberated.
    rows = [vrow(3, tier="sealed_damaged_core"), vrow(4)]
    rel = write_master(tmp_root, "x05a.csv", rows)
    assert_only(validate(tmp_root, [rel]), "X05", rows=[1], file=rel)

    rows = [vrow(3), vrow(4, tier="sealed_damaged_core")]
    rel = write_master(tmp_root, "x05b.csv", rows)
    assert_only(validate(tmp_root, [rel]), "X05", rows=[2], file=rel)


def test_x05_transfers_for_the_impoundment_event_match_when_tiers_agree(tmp_root):
    # E002 (TVA Kingston) runs impounded -> liberated at coal combustion_power.
    base = dict(stream="coal", substream="power", stage="combustion_power", country="USA",
                year=2008, group="Ra226+", event_id="E002", technology="", allocation_rule="mass")
    out = vrow(5, quantity="transfer_out", unit="Bq", tier="impounded", **base)
    inn = vrow(5, quantity="transfer_in", unit="Bq", tier="liberated", **base)
    rel = write_master(tmp_root, "kingston.csv", [out, inn])
    assert_clean(validate(tmp_root, [rel]))

    bad = vrow(5, quantity="transfer_in", unit="Bq", tier="dispersed", **base)
    rel2 = write_master(tmp_root, "kingston_bad.csv", [out, bad])
    assert "X05" in rules_of(validate(tmp_root, [rel2]))


# --------------------------------------------------------------------------- file-level rules F01-F03

def _with_extra_column(tmp_root, column, name="extra.csv"):
    header = MASTER_COLUMNS + [column]
    rows = [dict(r, **{column: "1"}) for r in VALID_ROWS]
    return write_master(tmp_root, name, rows, header=header)


def test_f02_and_f01_for_collective_dose_column(tmp_root):
    rel = _with_extra_column(tmp_root, "collective_dose")
    issues = validate(tmp_root, [rel])
    by_rule = {r: [i for i in issues if i.rule == r] for r in ("F01", "F02")}
    assert by_rule["F01"], describe(issues)
    assert by_rule["F02"], describe(issues)
    for i in by_rule["F01"] + by_rule["F02"]:
        assert i.file == rel and i.row is None, describe(issues)


@pytest.mark.parametrize(
    "column, expect_f02",
    [
        ("dose", True),
        ("Dose_Rate", True),
        ("effective_dose_msv", True),
        ("total_sv", True),
        ("SV", True),
        ("sievert", True),
        ("rem", True),
        ("remarks", False),
        ("svalbard", False),
        ("dosage", False),
        ("random", False),
    ],
)
def test_f02_matches_whole_underscore_separated_words_case_insensitively(tmp_root, column, expect_f02):
    rel = _with_extra_column(tmp_root, column)
    rules = rules_of(validate(tmp_root, [rel]))
    assert "F01" in rules  # any extra column breaks the header
    assert ("F02" in rules) is expect_f02, f"column {column!r}: rules raised {sorted(rules)}"


def test_f01_header_missing_column_or_reordered(tmp_root):
    missing = [c for c in MASTER_COLUMNS if c != "notes"]
    rel = write_master(tmp_root, "missing.csv", VALID_ROWS, header=missing)
    issues = validate(tmp_root, [rel])
    assert any(i.rule == "F01" and i.row is None and i.file == rel for i in issues), describe(issues)
    assert "F02" not in rules_of(issues)

    swapped = list(MASTER_COLUMNS)
    swapped[0], swapped[1] = swapped[1], swapped[0]
    rel = write_master(tmp_root, "swapped.csv", VALID_ROWS, header=swapped)
    issues = validate(tmp_root, [rel])
    assert any(i.rule == "F01" and i.row is None and i.file == rel for i in issues), describe(issues)


def test_f01_and_f02_apply_to_non_master_csvs(tmp_root):
    path = tmp_root / "data" / "sources.csv"
    header, rows = read_csv(path)
    write_csv(path, header + ["dose"], [dict(r, dose="0") for r in rows])
    issues = validate(tmp_root, [])
    f = {i.rule for i in issues if i.file == "data/sources.csv"}
    assert {"F01", "F02"} <= f, describe(issues)


def test_f03_file_that_is_not_utf8(tmp_root):
    path = tmp_root / "data" / "streams" / "latin1.csv"
    good = (FIXTURES / "valid_rows.csv").read_bytes()
    path.write_bytes(good + b"1990,coal,power,combustion_power,CHN,Ra226+,liberated,flow,Bq/a,1,2,3,false,modelled,S0001,default,none,false,,,caf\xe9 \xff\xfe\n")
    issues = validate(tmp_root, ["data/streams/latin1.csv"])
    assert any(i.rule == "F03" and i.file == "data/streams/latin1.csv" and i.row is None for i in issues), describe(issues)


# --------------------------------------------------------------------------- reference tables: nuclides, groups, sources, events

def _ref(tmp_root, name):
    return tmp_root / "data" / "reference" / name


def test_reference_tables_and_fixture_registries_are_clean(tmp_root):
    assert_clean(validate(tmp_root, []))


def test_g02_multiplier_must_equal_sum_of_member_weights(tmp_root):
    path = _ref(tmp_root, "groups.csv")
    _, rows = read_csv(path)
    n = find_index(rows, "group", "U238+")
    edit_csv(path, lambda rs: rs[n - 1].update(multiplier="3.5"))
    assert_only(validate(tmp_root, []), "G02", rows=[n], file="data/reference/groups.csv")


def test_g01_member_or_head_missing_from_nuclides(tmp_root):
    path = _ref(tmp_root, "groups.csv")
    _, rows = read_csv(path)
    n = find_index(rows, "group", "Th230")
    edit_csv(path, lambda rs: rs[n - 1].update(members="Th-230;Zz-999", member_weights="1;0.5", multiplier="1.5"))
    assert_only(validate(tmp_root, []), "G01", rows=[n], file="data/reference/groups.csv")


def test_g01_head_missing_from_nuclides(tmp_root):
    path = _ref(tmp_root, "groups.csv")
    _, rows = read_csv(path)
    n = find_index(rows, "group", "Th230")
    edit_csv(path, lambda rs: rs[n - 1].update(head="Zz-999"))
    issues = validate(tmp_root, [])
    assert any(i.rule == "G01" and i.row == n and i.file == "data/reference/groups.csv" for i in issues), describe(issues)


@pytest.mark.parametrize(
    "group, scope",
    [("H3", "flow_only"), ("Rn222+", "stock_and_flow")],
    ids=["flow_only-without-released_gas", "released_gas-without-flow_only"],
)
def test_g03_flow_only_iff_released_gas(tmp_root, group, scope):
    path = _ref(tmp_root, "groups.csv")
    _, rows = read_csv(path)
    n = find_index(rows, "group", group)
    edit_csv(path, lambda rs: rs[n - 1].update(multiplier_scope=scope))
    assert_only(validate(tmp_root, []), "G03", rows=[n], file="data/reference/groups.csv")


def test_n01_branching_must_sum_to_one(tmp_root):
    path = _ref(tmp_root, "nuclides.csv")
    _, rows = read_csv(path)
    n = find_index(rows, "nuclide", "Pa-234m")
    edit_csv(path, lambda rs: rs[n - 1].update(branching="0.5;0.0016"))
    assert_only(validate(tmp_root, []), "N01", rows=[n], file="data/reference/nuclides.csv")


def test_n01_daughters_and_branching_lengths_must_match(tmp_root):
    path = _ref(tmp_root, "nuclides.csv")
    _, rows = read_csv(path)
    n = find_index(rows, "nuclide", "Pa-234m")
    edit_csv(path, lambda rs: rs[n - 1].update(daughters="U-234"))
    assert_only(validate(tmp_root, []), "N01", rows=[n], file="data/reference/nuclides.csv")


def test_n02_total_energy_must_equal_sum_of_components(tmp_root):
    path = _ref(tmp_root, "nuclides.csv")
    _, rows = read_csv(path)
    n = find_index(rows, "nuclide", "Th-234")
    old = float(rows[n - 1]["e_total_mev"])
    edit_csv(path, lambda rs: rs[n - 1].update(e_total_mev=repr(old * 1.01)))
    assert_only(validate(tmp_root, []), "N02", rows=[n], file="data/reference/nuclides.csv")


def test_n03_lambda_must_equal_ln2_over_half_life(tmp_root):
    path = _ref(tmp_root, "nuclides.csv")
    _, rows = read_csv(path)
    n = find_index(rows, "nuclide", "Th-234")
    old = float(rows[n - 1]["lambda_per_a"])
    edit_csv(path, lambda rs: rs[n - 1].update(lambda_per_a=repr(old * 1.01)))
    assert_only(validate(tmp_root, []), "N03", rows=[n], file="data/reference/nuclides.csv")


@pytest.mark.parametrize(
    "url",
    [
        "https://en.wikipedia.org/wiki/Coal_ash",
        "https://wikipedia.org/wiki/Coal_ash",
        "http://de.m.wikipedia.org/wiki/Kohle",
        "https://grokipedia.com/page/Coal_ash",
        "https://www.grokipedia.com/page/Coal_ash",
    ],
)
def test_s02_banned_domains_and_their_subdomains(tmp_root, url):
    path = tmp_root / "data" / "sources.csv"
    _, rows = read_csv(path)
    n = find_index(rows, "source_id", "S0003")
    edit_csv(path, lambda rs: rs[n - 1].update(url=url))
    assert_only(validate(tmp_root, []), "S02", rows=[n], file="data/sources.csv")


@pytest.mark.parametrize(
    "url",
    [
        "https://notwikipedia.org/wiki/Coal_ash",
        "https://wikipedia.org.example.com/page",
        "https://example.org/mirror/wikipedia.org/Coal_ash",
        "https://www.unscear.org/",
    ],
)
def test_s02_not_raised_for_other_hosts(tmp_root, url):
    path = tmp_root / "data" / "sources.csv"
    _, rows = read_csv(path)
    n = find_index(rows, "source_id", "S0003")
    edit_csv(path, lambda rs: rs[n - 1].update(url=url))
    assert_clean(validate(tmp_root, []))


def test_s01_rank_must_match_type(tmp_root):
    path = tmp_root / "data" / "sources.csv"
    _, rows = read_csv(path)
    n = find_index(rows, "source_id", "S0002")  # regulator, rank 1
    edit_csv(path, lambda rs: rs[n - 1].update(rank="5"))
    assert_only(validate(tmp_root, []), "S01", rows=[n], file="data/sources.csv")


@pytest.mark.parametrize(
    "changes",
    [
        pytest.param(dict(source_id="S12"), id="bad-id-pattern"),
        pytest.param(dict(year="2027"), id="year-in-the-future"),
        pytest.param(dict(type="blog"), id="type-not-in-enum"),
        pytest.param(dict(access="secret"), id="access-not-in-enum"),
        pytest.param(dict(url="ftp://example.org/file"), id="url-not-http"),
        pytest.param(dict(doi="not-a-doi"), id="doi-malformed"),
    ],
)
def test_s01_schema_failures(tmp_root, changes):
    path = tmp_root / "data" / "sources.csv"
    edit_csv(path, lambda rs: rs[3].update(changes))
    issues = validate(tmp_root, [])
    assert any(i.rule == "S01" and i.row == 4 and i.file == "data/sources.csv" for i in issues), describe(issues)


def test_s01_duplicate_source_id(tmp_root):
    path = tmp_root / "data" / "sources.csv"
    edit_csv(path, lambda rs: rs.append(dict(rs[0])))
    issues = validate(tmp_root, [])
    assert_only(issues, "S01", file="data/sources.csv")
    assert {i.row for i in issues} <= {1, 6}  # A3: first or later occurrence


def _event_row(rows, event_id):
    return find_index(rows, "event_id", event_id)


@pytest.mark.parametrize(
    "event_id, changes",
    [
        pytest.param("E002", dict(military="true"), id="military-event"),
        pytest.param("E001", dict(activity_central_bq="5.0e11"), id="activity-below-1TBq"),
        pytest.param("E002", dict(mass_t="5.0e4"), id="mass-below-1e5-t"),
        pytest.param("E002", dict(is_accident="true"), id="is_accident-disagrees-with-event_type"),
        pytest.param("E001", dict(is_accident="false"), id="accident-not-flagged"),
        pytest.param("E001", dict(from_tier="liberated"), id="liberated-to-liberated"),
        pytest.param("E002", dict(event_id="E2"), id="bad-event-id-pattern"),
        pytest.param("E001", dict(date_start="26/04/1986"), id="date-not-iso"),
        pytest.param("E001", dict(lat="95"), id="latitude-out-of-range"),
        pytest.param("E002", dict(inclusion="importance"), id="inclusion-not-in-enum"),
        pytest.param("E001", dict(activity_central_bq=""), id="activity-inclusion-without-activity"),
    ],
)
def test_e01_event_schema_failures(tmp_root, event_id, changes):
    path = tmp_root / "data" / "events.csv"
    _, rows = read_csv(path)
    n = _event_row(rows, event_id)
    edit_csv(path, lambda rs: rs[n - 1].update(changes))
    issues = validate(tmp_root, [])
    assert any(i.rule == "E01" and i.row == n and i.file == "data/events.csv" for i in issues), describe(issues)


def test_e01_duplicate_event_id(tmp_root):
    path = tmp_root / "data" / "events.csv"
    edit_csv(path, lambda rs: rs.append(dict(rs[1])))
    issues = validate(tmp_root, [])
    assert_only(issues, "E01", file="data/events.csv")
    assert {i.row for i in issues} <= {2, 3}  # A3


@pytest.mark.parametrize(
    "changes",
    [
        pytest.param(dict(stage="u_milling"), id="stage-not-allowed-for-stream"),
        pytest.param(dict(country="ZZZ"), id="unknown-country"),
        pytest.param(dict(source_ids="S0005;S0099"), id="unknown-source"),
    ],
)
def test_e02_event_vocabulary_membership(tmp_root, changes):
    path = tmp_root / "data" / "events.csv"
    edit_csv(path, lambda rs: rs[1].update(changes))
    assert_only(validate(tmp_root, []), "E02", rows=[2], file="data/events.csv")


# --------------------------------------------------------------------------- API behaviour

REQUIRED_FILES = [
    "data/reference/vocab.json",
    "data/reference/countries.csv",
    "data/reference/nuclides.csv",
    "data/reference/groups.csv",
    "schema/master.json",
    "schema/sources.json",
    "schema/events.json",
    "data/sources.csv",
]


@pytest.mark.parametrize("required", REQUIRED_FILES)
def test_missing_required_file_raises_file_not_found(tmp_root, required):
    (tmp_root / required).unlink()
    with pytest.raises(FileNotFoundError):
        validate(tmp_root, [])


def test_missing_events_csv_is_allowed_and_means_no_events(tmp_root):
    (tmp_root / "data" / "events.csv").unlink()
    assert_clean(validate(tmp_root, []))
    # With no events, every master row naming an event_id is a V08.
    rel = write_master(tmp_root, "valid.csv", VALID_ROWS)
    issues = validate(tmp_root, [rel])
    assert_only(issues, "V08", rows=[3, 4], file=rel)


def test_default_master_files_are_data_streams_only(tmp_root):
    write_master(tmp_root, "a_valid.csv", [vrow(5)])
    write_master(tmp_root, "b_invalid.csv", [vrow(9), vrow(10, unit="Bq")])
    issues = validate(tmp_root)
    assert_only(issues, "R02", rows=[2], file="data/streams/b_invalid.csv")


def test_default_master_files_exclude_build_master_unless_passed(tmp_root):
    write_master(tmp_root, "valid.csv", VALID_ROWS)
    (tmp_root / "build").mkdir()
    shutil.copy(FIXTURES / "valid_rows.csv", tmp_root / "build" / "master.csv")
    # The merge duplicates every key of the stream file; by default it is not read.
    assert_clean(validate(tmp_root))
    assert_clean(validate(tmp_root, None))
    issues = validate(tmp_root, ["data/streams/valid.csv", "build/master.csv"])
    assert_only(issues, "X01", rows=range(1, 11), file="build/master.csv")


def test_empty_master_files_list_checks_no_master_files(tmp_root):
    write_master(tmp_root, "invalid.csv", [vrow(5, unit="Bq")])
    assert_clean(validate(tmp_root, []))


def test_no_streams_directory_is_not_an_error(tmp_root):
    shutil.rmtree(tmp_root / "data" / "streams")
    assert_clean(validate(tmp_root))


def test_issue_file_is_root_relative_posix_for_absolute_and_relative_inputs(tmp_root):
    name = "01_r02_wrong_unit.csv"
    shutil.copy(INVALID_DIR / name, tmp_root / "data" / "streams" / name)
    expected = f"data/streams/{name}"
    for arg in (expected, str(tmp_root / expected), tmp_root / expected):
        issues = validate(tmp_root, [arg])
        assert {i.file for i in issues} == {expected}, describe(issues)
        assert all("\\" not in i.file for i in issues)


def test_issues_are_ordered_by_file_then_row_then_rule(tmp_root):
    a = write_master(tmp_root, "a.csv", [
        vrow(5, value_low="9e13"),                       # row 1: R03
        vrow(9, group="Tc98", source_ids="S0099"),      # row 2: V04 and V07
        vrow(3),                                         # row 3: lone transfer -> X02 (row None)
    ])
    b = write_master(tmp_root, "b.csv", [vrow(10, value_low="9e12", value_high="1e11"), vrow(2, unit="Bq/a")])
    issues = validate(tmp_root, [b, a])  # passed out of order on purpose
    assert len(issues) >= 5, describe(issues)
    key = lambda i: (i.file, i.row is not None, i.row if i.row is not None else 0, i.rule)
    assert [key(i) for i in issues] == sorted(key(i) for i in issues), describe(issues)
    assert issues == validate(tmp_root, [b, a]), "output must be stable between calls"
    first_a = [i for i in issues if i.file == a]
    assert first_a[0].row is None and first_a[0].rule == "X02", describe(issues)


def test_validate_does_not_modify_inputs(tmp_root):
    rel = write_master(tmp_root, "valid.csv", VALID_ROWS)
    before = {p: p.read_bytes() for p in tmp_root.rglob("*") if p.is_file()}
    validate(tmp_root, [rel])
    after = {p: p.read_bytes() for p in tmp_root.rglob("*") if p.is_file()}
    assert before == after


# --------------------------------------------------------------------------- command line

def run_cli(args, cwd, extra_env=None):
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(REAL_ROOT), env.get("PYTHONPATH")]))
    if extra_env:
        env.update(extra_env)
    result = subprocess.run(
        [sys.executable, "-m", "pipeline.validate", *[str(a) for a in args]],
        cwd=str(cwd), env=env, capture_output=True, text=True, timeout=180,
    )
    return result, (result.stdout or "") + (result.stderr or "")


def test_cli_exit_0_and_summary_on_valid_file(tmp_root, tmp_path):
    rel = write_master(tmp_root, "valid.csv", VALID_ROWS)
    result, out = run_cli(["--root", tmp_root, tmp_root / rel], cwd=tmp_path)
    assert result.returncode == 0, out
    assert out.strip(), "a summary line is expected even when there are no issues"
    assert not re.search(r":(\d+|-): [A-Z]\d\d ", out), out


def test_cli_exit_1_and_issue_line_format_on_invalid_file(tmp_root, tmp_path):
    name = "03_r03_low_above_high.csv"
    shutil.copy(INVALID_DIR / name, tmp_root / "data" / "streams" / name)
    result, out = run_cli(["--root", tmp_root, tmp_root / "data" / "streams" / name], cwd=tmp_path)
    assert result.returncode == 1, out
    assert re.search(rf"{re.escape(name)}:2: R03\b", out), out


def test_cli_prints_dash_for_file_level_issues(tmp_root, tmp_path):
    name = "08_x02_unbalanced_transfers.csv"
    shutil.copy(INVALID_DIR / name, tmp_root / "data" / "streams" / name)
    result, out = run_cli(["--root", tmp_root, tmp_root / "data" / "streams" / name], cwd=tmp_path)
    assert result.returncode == 1, out
    assert re.search(rf"{re.escape(name)}:-: X02\b", out), out


@pytest.mark.parametrize("name", sorted(CASES))
def test_cli_exit_1_for_every_invalid_case(tmp_root, tmp_path, name):
    shutil.copy(INVALID_DIR / name, tmp_root / "data" / "streams" / name)
    result, out = run_cli(["--root", tmp_root, tmp_root / "data" / "streams" / name], cwd=tmp_path)
    assert result.returncode == 1, out
    row = "-" if CASES[name]["row"] is None else str(CASES[name]["row"])
    assert re.search(rf":{row}: {CASES[name]['rule']}\b", out), out


def test_cli_exit_1_for_reference_table_problem_without_master_files(tmp_root, tmp_path):
    path = _ref(tmp_root, "groups.csv")
    edit_csv(path, lambda rs: rs[0].update(multiplier="3.5"))
    result, out = run_cli(["--root", tmp_root], cwd=tmp_path)
    assert result.returncode == 1, out
    assert re.search(r":1: G02\b", out), out


def test_cli_exit_2_on_missing_required_reference_file(tmp_root, tmp_path):
    (_ref(tmp_root, "nuclides.csv")).unlink()
    rel = write_master(tmp_root, "valid.csv", VALID_ROWS)
    result, out = run_cli(["--root", tmp_root, tmp_root / rel], cwd=tmp_path)
    assert result.returncode == 2, out


def test_cli_exit_2_on_missing_schema_file(tmp_root, tmp_path):
    (tmp_root / "schema" / "master.json").unlink()
    result, out = run_cli(["--root", tmp_root], cwd=tmp_path)
    assert result.returncode == 2, out


def test_cli_exit_2_on_usage_error(tmp_root, tmp_path):
    result, out = run_cli(["--root", tmp_root, "--no-such-option"], cwd=tmp_path)
    assert result.returncode == 2, out


def test_cli_root_defaults_to_current_directory_and_files_default_to_data_streams(tmp_root):
    write_master(tmp_root, "valid.csv", VALID_ROWS)
    result, out = run_cli([], cwd=tmp_root)
    assert result.returncode == 0, out

    write_master(tmp_root, "zz_invalid.csv", [vrow(9, year=2001), vrow(5, unit="Bq", year=2016)])
    result, out = run_cli([], cwd=tmp_root)
    assert result.returncode == 1, out
    assert re.search(r"zz_invalid\.csv:2: R02\b", out), out


# --------------------------------------------------------------------------- the real project root

def test_real_project_reference_tables_and_sources_validate_cleanly():
    issues = validate(REAL_ROOT, master_files=[])
    assert_clean(issues)
