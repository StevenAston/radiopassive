"""Spec-blind tests for the Radiopassive data validator (Task 0.2, SCHEMA v2).

Plan done condition: "validate.py accepts 10 hand-written valid example rows and
rejects 10 deliberately invalid rows (wrong unit, missing source, low > high,
unknown nuclide, etc.)."

Written from docs/SCHEMA.md v2 (section 6 is binding), schema/*.json and the real
reference tables only. Only pytest, the standard library and the public API in
SCHEMA.md section 6.1 are used.

Mapping to the done condition
-----------------------------
* fixtures/valid_rows.csv             -> the 10 valid rows (test_valid_rows_*).
* fixtures/invalid/*.csv + cases.json -> the 10 invalid rows (test_invalid_case).
* Everything else extends the same contract: every rule code of section 6.3,
  file-level rules, reference and support tables, cross-file behaviour,
  ordering, the CLI and the real project root.

AMBIGUITIES IN SCHEMA.md v2 (resolved here as noted; tests avoid asserting
anything beyond the stated reading). Several of the v1 ambiguities were settled
by section 6.5 and are now asserted.
------------------------------------------------------------------------
B1. Bound tokens (bound_main without alloc:main, etc.) are both "bound tokens"
    in the R02 list and part of X03 ("a row's rule lacks the token for its
    variant"). Which code, or both, is raised is unclear, so those tests only
    assert that R02 (master) or T01 (commodity_factors) is present.
B2. Same for commodity_factors: T05 is "as X03", T01 covers the bound-token
    schema conditional. A wrong default token is tested as T05 only; a wrong
    bound token only asserts T01.
B3. E03 versus E01 when a value needed by the inclusion test is null (for
    example inclusion=activity with an empty activity_central_bq): the schema
    fails (E01); whether E03 is also raised is unspecified. Not asserted.
B4. Invalid enum members inside to_tiers or an invalid inclusion value fail the
    schema (E01); whether E03 additionally fires is unspecified. Not asserted.
B5. V09 (section 4.2): "may be used only as" flow, transfer_in into liberated,
    transfer_out from sealed_in_core, and standing_inventory. Every other
    quantity/tier combination (opening_stock, transfer_in into another tier,
    transfer_out from another tier) is read as a V09.
B6. Products (section 5.5) for a oil_gas row at the stage `construction` (the
    `oil_gas` rule and the commodity-stage rule both apply) is unspecified.
    Not tested.
B7. T04 for factors lists driver_series, stage-for-stream, region (countries)
    and, through the generic list, source_ids; whether factors.group/tier/
    residue_type are also resolved is not stated. Only the four are tested.
B8. D01 is "reported once per row". Which row column(s) are named in the
    message is unspecified; only the count per row is asserted.
B9. The countries table has no T03/T04 condition (a valid_from > valid_to
    window is unspecified). Only T01 and T02 are tested for countries.
B10. reference_bands T02: "a nuclide may appear only once per class" and the
     `*` default may appear only once per class (read from the Key). Both are
     tested as T02.
B11. Section 6.5 says a file with F01/F02/F03 has its data rows neither
     validated nor used for lookups. Consequences for other tables that look
     the file up (for example V07 floods after a broken sources.csv) are not
     asserted; tests filter issues by file.
B12. Section 6.5: a master file outside the root is reported with its absolute
     POSIX path. Whether symlinks (for example a /tmp that is a link) are
     resolved is unspecified, so the test accepts the resolved or unresolved form.
B13. residue_types parameter sets with `basis` or `source_ids` filled but all
     parameters empty are not covered by section 4.10 ("required if any
     parameter set is filled"). Not tested.
B14. CLI: stdout carries issue lines and the summary; stderr carries errors
     (section 6.2). The exact summary wording is unspecified.
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
    "year", "stream", "substream", "stage", "product", "residue_type", "country", "group", "tier",
    "quantity", "unit", "value_low", "value_central", "value_high", "below_detection", "basis",
    "source_ids", "factor_ids", "allocation_variant", "allocation_rule", "embedded_fuel",
    "technology", "route", "event_id", "notes",
]

ROUTES = [
    "air_stack", "air_ventilation", "air_process_vent", "air_vented_gas", "air_delivered_gas",
    "air_dust", "air_other", "water_liquid_effluent", "water_mine_drainage",
    "water_produced_discharge", "water_spill", "water_other", "sea_disposal_package",
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
HALF = dict(value_low="3.5e16", value_central="4.25e16", value_high="5.0e16")  # half of the E001 Cs137+ release


def vrow(n, **changes):
    """Copy of valid fixture row n (1-based) with cell overrides."""
    row = dict(VALID_ROWS[n - 1])
    row.update({k: str(v) for k, v in changes.items()})
    return row


# Row-number cheat sheet for valid_rows.csv:
#  1 nuclear u_milling dispersed flow (civil:doc)      2 nuclear reactor_operation standing_inventory
#  3 E001 transfer_out                                  4 E001 transfer_in (liberated, route air_other)
#  5 sea_disposal routine transfer_out                  6 sea_disposal routine transfer_in (route)
#  7 coal coal_mining memo_earth_moved, modelled        8 oil_gas production oil, SUN 1980, liberated + route
#  9 wind_solar commodity_supply silicon_mg, embedded   10 other geothermal reisolated

OPENING = dict(stream="coal", substream="power", stage="combustion_power", tier="impounded",
               residue_type="coal_fly_ash", quantity="opening_stock", unit="Bq", country="USA",
               year="1950", technology="", route="", event_id="", embedded_fuel="false",
               product="", allocation_rule="none", basis="compiled", factor_ids="",
               source_ids="S0003")


def kingston_pair(group="Ra226+", in_tier="liberated", **common):
    """Balanced E002 (TVA Kingston, impounded -> liberated) transfer pair as master rows."""
    base = dict(stream="coal", substream="power", stage="combustion_power", country="USA", year=2008,
                group=group, event_id="E002", technology="", source_ids="S0005", product="", **common)
    out = vrow(10, tier="impounded", residue_type="coal_fly_ash", route="", quantity="transfer_out", unit="Bq", **base)
    inn = vrow(10, tier=in_tier, residue_type="", route="water_spill", quantity="transfer_in", unit="Bq", **base)
    return [out, inn]


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


def assert_has(issues, rule, row, file):
    assert any(i.rule == rule and i.row == row and i.file == file for i in issues), (
        f"expected {rule} at {file}:{row}; got:\n{describe(issues)}")


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


def corrupt(root, rel, index, **changes):
    """Overwrite cells of data row `index` (1-based) of a CSV under root."""
    edit_csv(Path(root) / rel, lambda rows: rows[index - 1].update(changes))


def append_copy(root, rel, index, **changes):
    """Append a copy of data row `index`, with overrides, to a CSV under root; return its row number."""
    path = Path(root) / rel
    header, rows = read_csv(path)
    new = dict(rows[index - 1])
    new.update(changes)
    rows.append(new)
    write_csv(path, header, rows)
    return len(rows)


# --------------------------------------------------------------------------- Issue type

def test_issue_is_a_frozen_dataclass_with_the_documented_fields():
    assert dataclasses.is_dataclass(Issue)
    assert [f.name for f in dataclasses.fields(Issue)] == ["file", "row", "rule", "message"]
    issue = Issue("data/streams/coal.csv", 3, "V03", "tier not allowed")
    assert (issue.file, issue.row, issue.rule, issue.message) == ("data/streams/coal.csv", 3, "V03", "tier not allowed")
    with pytest.raises(dataclasses.FrozenInstanceError):
        issue.row = 4  # type: ignore[misc]
    assert Issue("f", None, "X02", "m") == Issue("f", None, "X02", "m")


# --------------------------------------------------------------------------- the 10 valid rows

def test_fixture_has_exactly_ten_valid_rows_in_section_3_column_order():
    assert VALID_HEADER == MASTER_COLUMNS
    assert len(VALID_ROWS) == 10


def test_valid_rows_yield_no_issues(tmp_root):
    rel = write_master(tmp_root, "valid.csv", VALID_ROWS)
    assert_clean(validate(tmp_root, [rel]))


def test_valid_fixture_file_copied_verbatim_yields_no_issues(tmp_root):
    shutil.copy(FIXTURES / "valid_rows.csv", tmp_root / "data" / "streams" / "valid_rows.csv")
    assert_clean(validate(tmp_root, ["data/streams/valid_rows.csv"]))


def test_valid_rows_cover_the_required_features():
    assert {r["stream"] for r in VALID_ROWS} == {"nuclear", "coal", "oil_gas", "wind_solar", "other"}
    assert {r["quantity"] for r in VALID_ROWS} == {"flow", "transfer_out", "transfer_in", "standing_inventory"}
    assert {"reisolated", "dispersed", "memo_earth_moved", "sealed_in_core", "impounded", "liberated"} <= {r["tier"] for r in VALID_ROWS}
    assert any(r["below_detection"] == "true" for r in VALID_ROWS)
    assert any(r["embedded_fuel"] == "true" and r["stream"] == "wind_solar" for r in VALID_ROWS)
    assert any(r["country"] == "SUN" and r["year"] == "1980" for r in VALID_ROWS)
    assert any(r["stage"] == "u_milling" and r["allocation_rule"].startswith("civil:") for r in VALID_ROWS)
    # v2 features
    assert sum(1 for r in VALID_ROWS if r["stage"] == "sea_disposal" and r["event_id"] == "") == 2
    assert any(r["tier"] == "liberated" and r["route"] for r in VALID_ROWS)
    assert any(r["basis"] == "modelled" and r["factor_ids"] for r in VALID_ROWS)
    assert any(r["stream"] == "oil_gas" and r["product"] for r in VALID_ROWS)


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


def test_default_only_keys_are_not_flagged_by_x03(tmp_root):
    rel = write_master(tmp_root, "default_only.csv", [vrow(7), vrow(10)])
    assert_clean(validate(tmp_root, [rel]))


SEALED_DECOM = dict(stage="construction_decom", tier="sealed_fuel_cycle", residue_type="", allocation_rule="none", product="")
COAL_CONSTRUCTION = dict(stage="construction", substream="power", tier="impounded", residue_type="coal_fly_ash",
                         basis="compiled", factor_ids="", product="cement")


@pytest.mark.parametrize(
    "base, changes",
    [
        pytest.param(8, dict(country="CSK", year=1960), id="CSK-in-window"),
        pytest.param(8, dict(country="DDR", year=1970), id="DDR-in-window"),
        pytest.param(8, dict(country="YUG", year=1985), id="YUG-in-window"),
        pytest.param(8, dict(country="DEU", year=1960), id="DEU-pre-1990-no-window"),
        pytest.param(10, dict(country="XXX"), id="XXX-remainder"),
        pytest.param(10, dict(value_low="2e13", value_central="2e13", value_high="2e13"), id="low-eq-central-eq-high"),
        pytest.param(10, dict(value_low="0", value_central="0", value_high="0"), id="all-zero"),
        pytest.param(10, dict(value_low="12000000000000", value_central="30000000000000.5", value_high="6E13"), id="plain-and-exponent-notation"),
        pytest.param(10, dict(year=1950), id="year-lower-bound"),
        pytest.param(10, dict(year=2025), id="year-upper-bound"),
        pytest.param(10, dict(notes='Quoted, with a comma and "quotes"'), id="notes-with-comma"),
        pytest.param(10, dict(technology="gas_power"), id="technology-populated"),
        pytest.param(10, dict(source_ids="S0001;S0002;S0003"), id="three-sources"),
        pytest.param(10, dict(group="Rn222+"), id="flow-only-group-on-flow"),
        pytest.param(10, dict(factor_ids="coal:0001;coal:0002"), id="factor-ids-on-a-non-modelled-row"),
        pytest.param(10, dict(basis="modelled", factor_ids="coal:0002"), id="modelled-with-factor"),
        pytest.param(8, dict(product="gas"), id="product-gas"),
        pytest.param(8, dict(product="ngl"), id="product-ngl"),
        pytest.param(8, dict(product="bitumen"), id="product-bitumen"),
        pytest.param(8, dict(stage="drilling", tier="impounded", residue_type="og_sludge", route=""), id="oil-gas-product-at-drilling"),
        pytest.param(9, dict(product="copper"), id="commodity-copper"),
        pytest.param(9, dict(product="other_commodity"), id="commodity-other"),
        pytest.param(1, SEALED_DECOM, id="sealed-decommissioning-without-product"),
        pytest.param(7, COAL_CONSTRUCTION, id="coal-construction-with-commodity"),
        pytest.param(1, dict(stage="u_mining_isl", tier="impounded", residue_type="isl_pond_residue",
                             allocation_rule="civil:ratio;alloc:value", country="KAZ", year=1999),
                     id="civil-component-among-several-tokens"),
        pytest.param(1, dict(stage="u_mining_conv", tier="impounded", residue_type="u_waste_rock", year=1964,
                             allocation_rule="civil:pre1965", value_low=0, value_central=0, value_high=0),
                     id="civil-pre1965-in-1964-with-zero-high"),
        pytest.param(1, dict(stage="u_mining_conv", tier="impounded", residue_type="u_waste_rock", year=1965,
                             allocation_rule="civil:ratio"), id="civil-ratio-in-1965"),
        pytest.param(1, dict(stage="u_mining_conv", tier="memo_earth_moved", residue_type="", country="AUS", year=1995,
                             allocation_rule="civil:ratio"), id="civil-memo-earth-moved-flow"),
        pytest.param(1, dict(stage="reprocessing", tier="liberated", residue_type="", route="air_stack", country="FRA",
                             year=1990, allocation_rule="civil:throughput"), id="reprocessing-with-civil-throughput"),
        pytest.param(1, dict(stage="reprocessing", tier="sealed_fuel_cycle", residue_type="", country="GBR",
                             year=1990, allocation_rule="civil:doc;civil:throughput"), id="reprocessing-two-civil-tokens"),
        pytest.param(10, OPENING, id="opening-stock-1950"),
        pytest.param(10, dict(OPENING, tier="reisolated"), id="opening-stock-reisolated"),
        pytest.param(10, dict(OPENING, tier="liberated", residue_type="", route="water_spill"), id="opening-stock-liberated"),
    ],
)
def test_other_valid_single_rows(tmp_root, base, changes):
    rel = write_master(tmp_root, "one.csv", [vrow(base, **changes)])
    assert_clean(validate(tmp_root, [rel]))


@pytest.mark.parametrize("route", ROUTES)
def test_every_release_route_is_accepted_on_a_liberated_row(tmp_root, route):
    rel = write_master(tmp_root, "route.csv", [vrow(8, route=route)])
    assert_clean(validate(tmp_root, [rel]))


@pytest.mark.parametrize("tier", ["impounded", "reisolated"])
def test_residue_tiers_accept_a_known_residue_type(tmp_root, tier):
    rel = write_master(tmp_root, "res.csv", [vrow(10, tier=tier)])
    assert_clean(validate(tmp_root, [rel]))


def test_v03_is_not_raised_for_transfer_rows(tmp_root):
    # spent_fuel allows only sealed_fuel_cycle (section 5.3), but transfer rows follow section 3.1 instead.
    rows = [vrow(3, stage="spent_fuel", substream="fuel_cycle"), vrow(4, stage="spent_fuel", substream="fuel_cycle")]
    rel = write_master(tmp_root, "transfers.csv", rows)
    assert_clean(validate(tmp_root, [rel]))


def test_flow_only_groups_in_allowed_forms_are_clean(tmp_root):
    rows = [
        vrow(3, group="Kr88+"),                      # transfer_out from sealed_in_core
        vrow(4, group="Kr88+"),                      # transfer_in into liberated
        vrow(2, group="Xe138+"),                     # standing_inventory
        vrow(10, group="Rn222+"),                    # flow
    ]
    rel = write_master(tmp_root, "gases.csv", rows)
    assert_clean(validate(tmp_root, [rel]))


# --------------------------------------------------------------------------- the 10 invalid cases

CASES = json.loads((INVALID_DIR / "cases.json").read_text(encoding="utf-8"))


def test_manifest_lists_ten_cases_covering_the_required_rules():
    assert len(CASES) == 10
    assert {c["rule"] for c in CASES.values()} >= {
        "R02", "V07", "R03", "V04", "V03", "X01", "X02", "X04", "V06",
    }
    assert {c["rule"] for c in CASES.values()} & {"V11", "V12", "X05"}
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


# --------------------------------------------------------------------------- R01 / R02 / R03

@pytest.mark.parametrize(
    "changes",
    [
        pytest.param(dict(below_detection="yes"), id="bool-yes"),
        pytest.param(dict(embedded_fuel="True"), id="bool-capitalised"),
        pytest.param(dict(below_detection="1"), id="bool-1"),
        pytest.param(dict(year="19x5"), id="year-not-int"),
        pytest.param(dict(year="1986.5"), id="year-not-int-decimal"),
        pytest.param(dict(value_central="abc"), id="float-not-number"),
        pytest.param(dict(value_central="nan"), id="float-nan"),
        pytest.param(dict(value_high="inf"), id="float-infinity"),
        pytest.param(dict(source_ids=""), id="source-ids-empty"),
        pytest.param(dict(basis=""), id="required-cell-empty"),
        pytest.param(dict(country=""), id="required-cell-empty-country"),
        pytest.param(dict(value_low=""), id="required-float-empty"),
        pytest.param(dict(allocation_rule=""), id="allocation-rule-empty"),
    ],
)
def test_r01_uncoercible_cell(tmp_root, changes):
    rel = write_master(tmp_root, "r01.csv", [vrow(7), vrow(10, **changes)])
    issues = validate(tmp_root, [rel])
    assert_has(issues, "R01", 2, rel)
    assert not [i for i in issues if i.row == 1], f"row 1 is valid:\n{describe(issues)}"


@pytest.mark.parametrize("column", ["product", "residue_type", "factor_ids", "technology", "route", "event_id", "notes"])
def test_empty_nullable_master_cells_are_not_r01(tmp_root, column):
    rel = write_master(tmp_root, "nullable.csv", [vrow(8, **{column: ""})])
    assert "R01" not in rules_of(validate(tmp_root, [rel]))


def test_r01_row_skips_r02_and_r03(tmp_root):
    # year is uncoercible AND low > high; only R01 is reported for the row (section 6.5).
    rel = write_master(tmp_root, "r01_skip.csv", [vrow(10, year="19x5", value_low="9e99")])
    assert_only(validate(tmp_root, [rel]), "R01", rows=[1], file=rel)


def test_r01_row_skips_x04(tmp_root):
    rel = write_master(tmp_root, "r01_x04.csv", [vrow(1, year="x", allocation_rule="none")])
    assert_only(validate(tmp_root, [rel]), "R01", rows=[1], file=rel)


def test_r01_row_still_takes_part_in_x01(tmp_root):
    bad = vrow(10, value_central="abc")
    rel = write_master(tmp_root, "r01_x01.csv", [bad, dict(bad)])
    issues = validate(tmp_root, [rel])
    assert rules_of(issues) == {"R01", "X01"}, describe(issues)
    assert_has(issues, "X01", 2, rel)


def test_r01_row_makes_its_whole_x02_balance_key_skipped(tmp_root):
    rows = [vrow(3, value_central="abc"), vrow(4, **HALF)]
    rel = write_master(tmp_root, "r01_x02.csv", rows)
    assert_only(validate(tmp_root, [rel]), "R01", rows=[1], file=rel)


R02_CASES = [
    pytest.param(9, dict(value_low="1e8"), id="below-detection-with-nonzero-low"),
    pytest.param(2, dict(tier="liberated"), id="standing-inventory-outside-sealed-in-core"),
    pytest.param(2, dict(quantity="flow", unit="Bq/a"), id="sealed-in-core-with-flow"),
    pytest.param(2, dict(unit="Bq/a"), id="standing-inventory-unit-bq-per-a"),
    pytest.param(7, dict(embedded_fuel="true"), id="embedded-fuel-outside-wind-solar-or-construction"),
    pytest.param(10, dict(year="2026"), id="year-above-2025"),
    pytest.param(10, dict(year="1949"), id="year-below-1950"),
    pytest.param(10, dict(stream="solar"), id="invalid-stream-skips-v01-v03-v11"),
    pytest.param(10, dict(tier="buried"), id="invalid-tier-skips-v03"),
    pytest.param(10, dict(basis="guess"), id="invalid-basis"),
    pytest.param(10, dict(allocation_rule="civil:xyz"), id="invalid-allocation-token"),
    pytest.param(10, dict(allocation_rule="value"), id="v1-style-token-without-prefix"),
    pytest.param(10, dict(allocation_rule="none;bogus"), id="one-bad-token-in-a-list"),
    pytest.param(10, dict(value_low="-1"), id="negative-value"),
    pytest.param(10, dict(technology="fusion"), id="invalid-technology"),
    pytest.param(10, dict(source_ids="S0001;S0001"), id="duplicate-source-in-list"),
    pytest.param(10, dict(unit="Bq/s"), id="invalid-unit"),
    pytest.param(10, dict(residue_type=""), id="residue-tier-without-residue-type"),
    pytest.param(8, dict(residue_type="og_scale"), id="residue-type-on-liberated-row"),
    pytest.param(7, dict(residue_type="coal_fly_ash"), id="residue-type-on-memo-row"),
    pytest.param(8, dict(route=""), id="liberated-without-route"),
    pytest.param(10, dict(route="air_stack"), id="route-on-non-liberated-row"),
    pytest.param(10, dict(route="air_leak"), id="route-outside-vocabulary"),
    pytest.param(7, dict(factor_ids=""), id="modelled-without-factor-ids"),
    pytest.param(7, dict(quantity="opening_stock", unit="Bq", year="1950"), id="opening-stock-on-memo-tier"),
    pytest.param(10, dict(OPENING, year="1960"), id="opening-stock-outside-1950"),
    pytest.param(2, dict(quantity="opening_stock", unit="Bq", year="1950"), id="opening-stock-in-sealed-in-core"),
    pytest.param(10, dict(OPENING, unit="Bq/a"), id="opening-stock-with-flow-unit"),
    pytest.param(1, dict(allocation_rule="civil:pre1965", year=1970), id="civil-pre1965-after-1964"),
    pytest.param(1, dict(allocation_rule="civil:pre1965", year=1960), id="civil-pre1965-with-nonzero-high"),
    pytest.param(1, dict(allocation_rule="civil:ratio", year=1960), id="civil-ratio-before-1965"),
]


@pytest.mark.parametrize("base, changes", R02_CASES)
def test_r02_schema_failure_is_reported_alone(tmp_root, base, changes):
    rel = write_master(tmp_root, "r02.csv", [vrow(7 if base != 7 else 10), vrow(base, **changes)])
    assert_only(validate(tmp_root, [rel]), "R02", rows=[2], file=rel)


def test_r02_memo_tier_must_be_a_flow(tmp_root):
    # X02/X05 may also fire for the lone transfer; only R02 is asserted.
    rel = write_master(tmp_root, "memo_transfer.csv", [vrow(7, quantity="transfer_out", unit="Bq", event_id="E001")])
    assert_has(validate(tmp_root, [rel]), "R02", 1, rel)


def test_r02_flow_unit_must_be_bq_per_annum_and_stock_unit_bq(tmp_root):
    rel = write_master(tmp_root, "units.csv", [vrow(10, unit="Bq"), vrow(2, unit="Bq/a")])
    assert_only(validate(tmp_root, [rel]), "R02", rows=[1, 2], file=rel)


@pytest.mark.parametrize("variant, rule", [("bound_main", "alloc:value"), ("bound_radio", "alloc:main"), ("bound_main", "none")])
def test_r02_bound_variant_needs_its_own_token(tmp_root, variant, rule):
    # B1: X03 may also fire for the incomplete key; only R02 is asserted.
    rel = write_master(tmp_root, "bound.csv", [vrow(10, allocation_variant=variant, allocation_rule=rule)])
    assert_has(validate(tmp_root, [rel]), "R02", 1, rel)


@pytest.mark.parametrize(
    "changes",
    [
        pytest.param(dict(value_low="9e13"), id="low-above-central"),
        pytest.param(dict(value_central="9e13"), id="central-above-high"),
        pytest.param(dict(value_central="4e12"), id="central-below-low"),
        pytest.param(dict(value_high="5e12"), id="high-below-low-and-central"),
    ],
)
def test_r03_ordering_of_low_central_high(tmp_root, changes):
    rel = write_master(tmp_root, "r03.csv", [vrow(7), vrow(10, **changes)])
    assert_only(validate(tmp_root, [rel]), "R03", rows=[2], file=rel)


# --------------------------------------------------------------------------- V01-V13

VOCAB_CASES = [
    pytest.param("V01", 7, dict(substream="wind"), id="V01-substream-of-another-stream"),
    pytest.param("V01", 10, dict(substream="not_a_substream"), id="V01-unknown-substream"),
    pytest.param("V02", 10, dict(stage="not_a_stage"), id="V02-unknown-stage-only"),
    pytest.param("V02", 10, dict(stage="u_milling", tier="impounded"), id="V02-nuclear-stage-on-other-stream"),
    pytest.param("V03", 10, dict(tier="dispersed"), id="V03-dispersed-at-geothermal"),
    pytest.param("V03", 1, dict(stage="conv_enrich_fab"), id="V03-dispersed-at-conversion"),
    pytest.param("V03", 2, dict(stage="spent_fuel"), id="V03-sealed-in-core-at-spent-fuel"),
    pytest.param("V04", 10, dict(group="Tc98"), id="V04-nuclide-not-a-group"),
    pytest.param("V04", 10, dict(group="Cs137"), id="V04-head-without-plus"),
    pytest.param("V04", 10, dict(group="Zz999"), id="V04-nonsense-group"),
    pytest.param("V05", 10, dict(country="ZZZ"), id="V05-unknown-country"),
    pytest.param("V05", 10, dict(country="CA"), id="V05-two-letter-country"),
    pytest.param("V06", 8, dict(country="SUN", year=1992), id="V06-SUN-after-1991"),
    pytest.param("V06", 8, dict(country="CSK", year=1993), id="V06-CSK-after-1992"),
    pytest.param("V06", 8, dict(country="DDR", year=1991), id="V06-DDR-after-1990"),
    pytest.param("V06", 8, dict(country="YUG", year=2007), id="V06-YUG-after-2006"),
    pytest.param("V07", 10, dict(source_ids="S0001;S0099"), id="V07-one-of-two-unknown"),
    pytest.param("V07", 10, dict(source_ids="S9002"), id="V07-real-id-absent-from-fixture-registry"),
    pytest.param("V08", 10, dict(event_id="E099"), id="V08-unknown-event"),
    pytest.param("V10", 10, dict(country="XWL"), id="V10-world-aggregate-in-master"),
    pytest.param("V11", 8, dict(product=""), id="V11-oil-gas-without-product"),
    pytest.param("V11", 8, dict(product="kerosene"), id="V11-oil-gas-unknown-product"),
    pytest.param("V11", 8, dict(product="copper"), id="V11-oil-gas-with-commodity"),
    pytest.param("V11", 8, dict(stage="drilling", tier="impounded", residue_type="og_sludge", route="", product=""), id="V11-oil-gas-drilling-without-product"),
    pytest.param("V11", 9, dict(product=""), id="V11-commodity-stage-without-product"),
    pytest.param("V11", 9, dict(product="unobtainium"), id="V11-commodity-unknown"),
    pytest.param("V11", 9, dict(product="oil"), id="V11-commodity-stage-with-oil-product"),
    pytest.param("V11", 10, dict(product="copper"), id="V11-product-on-geothermal"),
    pytest.param("V11", 1, dict(product="copper"), id="V11-product-on-uranium-milling"),
    pytest.param("V11", 1, dict(SEALED_DECOM, product="steel"), id="V11-product-on-sealed-tier-at-commodity-stage"),
    pytest.param("V11", 7, dict(COAL_CONSTRUCTION, product=""), id="V11-coal-construction-without-product"),
    pytest.param("V12", 10, dict(residue_type="moon_dust"), id="V12-unknown-residue-type"),
    pytest.param("V13", 7, dict(factor_ids="coal:9999"), id="V13-unknown-factor"),
    pytest.param("V13", 7, dict(factor_ids="coal:0001;coal:9999"), id="V13-one-of-two-unknown"),
    pytest.param("V13", 10, dict(factor_ids="oil_gas:0001"), id="V13-factor-on-a-non-modelled-row"),
]


@pytest.mark.parametrize("rule, base, changes", VOCAB_CASES)
def test_vocabulary_membership_rules_raise_one_code(tmp_root, rule, base, changes):
    filler = vrow(10) if base != 10 else vrow(7)
    rel = write_master(tmp_root, "vocab.csv", [filler, vrow(base, **changes)])
    assert_only(validate(tmp_root, [rel]), rule, rows=[2], file=rel)


def test_v09_flow_only_group_as_transfer_in_to_a_stock_tier(tmp_root):
    # Kr88+ is released_gas / flow_only. transfer_in into sealed_damaged_core (a to_tier of E001) is not allowed.
    rows = [vrow(3, group="Kr88+"), vrow(4, group="Kr88+", tier="sealed_damaged_core", route="")]
    rel = write_master(tmp_root, "v09a.csv", rows)
    assert_only(validate(tmp_root, [rel]), "V09", rows=[2], file=rel)


def test_v09_flow_only_group_as_transfer_out_from_a_non_core_tier(tmp_root):
    rows = kingston_pair(group="Kr88+")  # transfer_out from impounded, transfer_in into liberated
    rel = write_master(tmp_root, "v09b.csv", rows)
    assert_only(validate(tmp_root, [rel]), "V09", rows=[1], file=rel)


@pytest.mark.parametrize("group", ["Rn222+", "Rn220+", "Kr88+", "Xe138+"])
def test_v09_flow_only_group_as_opening_stock(tmp_root, group):
    rel = write_master(tmp_root, "v09c.csv", [vrow(10, **dict(OPENING, group=group))])
    assert_only(validate(tmp_root, [rel]), "V09", rows=[1], file=rel)


def test_v09_not_raised_for_ordinary_groups_in_the_same_forms(tmp_root):
    rows = kingston_pair() + [vrow(10, **OPENING)]
    rel = write_master(tmp_root, "v09d.csv", rows)
    assert_clean(validate(tmp_root, [rel]))


# --------------------------------------------------------------------------- X01-X05

def test_x01_duplicate_key_ignores_values_and_notes(tmp_root):
    rows = [vrow(10), vrow(10, value_central="2e13", value_high="9e13", notes="different")]
    rel = write_master(tmp_root, "dup.csv", rows)
    assert_only(validate(tmp_root, [rel]), "X01", rows=[2], file=rel)


@pytest.mark.parametrize(
    "changes",
    [
        pytest.param(dict(year=2006), id="year"),
        pytest.param(dict(country="IND"), id="country"),
        pytest.param(dict(group="Pb210+"), id="group"),
        pytest.param(dict(tier="impounded"), id="tier"),
        pytest.param(dict(technology="biomass"), id="technology"),
        pytest.param(dict(technology=""), id="technology-null-vs-set"),
        pytest.param(dict(residue_type="biomass_ash", substream="geothermal"), id="residue-type"),
        pytest.param(dict(tier="liberated", residue_type="", route="air_stack"), id="route-and-tier"),
    ],
)
def test_x01_not_raised_when_key_differs(tmp_root, changes):
    rows = [vrow(10), vrow(10, **changes)]
    rel = write_master(tmp_root, "distinct.csv", rows)
    assert_clean(validate(tmp_root, [rel]))


def test_x01_route_and_product_are_part_of_the_key(tmp_root):
    rows = [vrow(8), vrow(8, route="water_spill"), vrow(8, product="gas")]
    rel = write_master(tmp_root, "key_parts.csv", rows)
    assert_clean(validate(tmp_root, [rel]))


def test_x01_allocation_rule_is_not_part_of_the_key(tmp_root):
    rel = write_master(tmp_root, "same_key.csv", [vrow(10), vrow(10, allocation_rule="elec_share")])
    assert_only(validate(tmp_root, [rel]), "X01", rows=[2], file=rel)


def test_x01_across_files_is_reported_on_the_later_file(tmp_root):
    a = write_master(tmp_root, "a.csv", VALID_ROWS)
    b = write_master(tmp_root, "b.csv", VALID_ROWS)
    issues = validate(tmp_root, [a, b])
    assert_only(issues, "X01", rows=range(1, 11), file=b)
    assert len(issues) == 10


def test_x01_later_file_follows_the_order_of_master_files(tmp_root):
    a = write_master(tmp_root, "a.csv", VALID_ROWS)
    b = write_master(tmp_root, "b.csv", VALID_ROWS)
    assert_only(validate(tmp_root, [b, a]), "X01", rows=range(1, 11), file=a)


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


def test_x02_event_key_sums_several_rows_across_countries(tmp_root):
    out_a = vrow(3, country="UKR", value_low="3e16", value_central="4e16", value_high="5e16")
    out_b = vrow(3, country="BLR", value_low="4e16", value_central="4.5e16", value_high="5e16")
    in_row = vrow(4)
    rel = write_master(tmp_root, "sum.csv", [out_a, out_b, in_row])
    assert_clean(validate(tmp_root, [rel]))


def test_x02_event_key_balances_across_to_tiers(tmp_root):
    # E001 may end in liberated or sealed_damaged_core; the two transfer_in rows together balance the transfer_out.
    to_air = vrow(4, value_low="4e16", value_central="5e16", value_high="6e16")
    to_core = vrow(4, tier="sealed_damaged_core", route="", value_low="3e16", value_central="3.5e16", value_high="4e16")
    rel = write_master(tmp_root, "split.csv", [vrow(3), to_air, to_core])
    assert_clean(validate(tmp_root, [rel]))


def test_x02_considers_all_master_files_together(tmp_root):
    a = write_master(tmp_root, "a.csv", [vrow(3), vrow(7)])
    b = write_master(tmp_root, "b.csv", [vrow(4)])
    assert_clean(validate(tmp_root, [a, b]))


def test_x02_across_files_is_reported_against_the_first_file_containing_the_key(tmp_root):
    a = write_master(tmp_root, "a.csv", [vrow(7), vrow(3)])
    b = write_master(tmp_root, "b.csv", [vrow(4, **HALF)])
    issues = validate(tmp_root, [a, b])
    assert_only(issues, "X02", rows=[None], file=a)
    assert len(issues) == 1


def test_x02_missing_counterpart_is_unbalanced(tmp_root):
    rel = write_master(tmp_root, "lonely.csv", [vrow(3)])
    assert_only(validate(tmp_root, [rel]), "X02", rows=[None], file=rel)


def test_x02_routine_pair_balances_on_stage_country_year_group_variant(tmp_root):
    rows = [vrow(5), vrow(6), vrow(5, year=1968), vrow(6, year=1968)]
    rel = write_master(tmp_root, "routine.csv", rows)
    assert_clean(validate(tmp_root, [rel]))


def test_x02_routine_pair_unbalanced(tmp_root):
    rel = write_master(tmp_root, "routine_bad.csv", [vrow(5), vrow(6, **{"value_low": "5e13", "value_central": "1e14", "value_high": "2e14"})])
    assert_only(validate(tmp_root, [rel]), "X02", rows=[None], file=rel)


def test_x02_routine_balance_key_includes_country(tmp_root):
    # Out in GBR, in in FRA: each country key is unbalanced -> two X02 issues, both file-level.
    rel = write_master(tmp_root, "routine_countries.csv", [vrow(5), vrow(6, country="FRA")])
    issues = validate(tmp_root, [rel])
    assert_only(issues, "X02", rows=[None], file=rel)
    assert len(issues) == 2


def test_x02_routine_and_event_keys_are_independent(tmp_root):
    rows = [vrow(3), vrow(4), vrow(5), vrow(6)]
    rel = write_master(tmp_root, "mixed.csv", rows)
    assert_clean(validate(tmp_root, [rel]))


def test_x03_only_non_default_variant_is_flagged_once_on_the_first_row(tmp_root):
    rows = [vrow(10, allocation_variant="bound_main", allocation_rule="alloc:main")]
    rel = write_master(tmp_root, "x03a.csv", rows)
    issues = validate(tmp_root, [rel])
    assert_only(issues, "X03", rows=[1], file=rel)
    assert len(issues) == 1


@pytest.mark.parametrize(
    "order",
    [("default", "bound_main"), ("bound_main", "default"), ("bound_radio", "bound_main"), ("default", "bound_radio")],
)
def test_x03_missing_variant_is_reported_once_per_key_on_its_first_row(tmp_root, order):
    tokens = {"default": "alloc:value", "bound_main": "alloc:main", "bound_radio": "alloc:radio"}
    rows = [vrow(7)] + [vrow(10, allocation_variant=v, allocation_rule=tokens[v]) for v in order]
    rel = write_master(tmp_root, "x03b.csv", rows)
    issues = validate(tmp_root, [rel])
    assert_only(issues, "X03", rows=[2], file=rel)
    assert len(issues) == 1


def _full_variant_rows(default_rule="alloc:value", **common):
    return [
        vrow(10, allocation_variant="default", allocation_rule=default_rule, **common),
        vrow(10, allocation_variant="bound_main", allocation_rule="alloc:main",
             value_low="2e12", value_central="4e12", value_high="7e12", **common),
        vrow(10, allocation_variant="bound_radio", allocation_rule="alloc:radio",
             value_low="5e12", value_central="1e13", value_high="3e13", **common),
    ]


@pytest.mark.parametrize("rule", ["alloc:value", "alloc:mass", "elec_share;alloc:value", "alloc:mass;elec_share"])
def test_x03_complete_variant_set_with_default_token_is_valid(tmp_root, rule):
    rel = write_master(tmp_root, "x03c.csv", _full_variant_rows(rule))
    assert_clean(validate(tmp_root, [rel]))


@pytest.mark.parametrize("rule", ["none", "elec_share", "alloc:main"])
def test_x03_complete_key_whose_default_row_lacks_alloc_value_or_mass(tmp_root, rule):
    rel = write_master(tmp_root, "x03d.csv", _full_variant_rows(rule))
    issues = validate(tmp_root, [rel])
    assert_only(issues, "X03", rows=[1], file=rel)
    assert len(issues) == 1


def test_x04_applies_to_each_civil_rule_stage_including_reprocessing(tmp_root):
    rows = [
        vrow(1, stage="u_mining_conv", tier="impounded", residue_type="u_waste_rock", allocation_rule="none", year=1990),
        vrow(1, stage="u_mining_isl", tier="impounded", residue_type="isl_pond_residue", allocation_rule="alloc:value", year=1991),
        vrow(1, allocation_rule="alloc:mass;elec_share", year=1992),
        vrow(1, stage="reprocessing", tier="sealed_fuel_cycle", residue_type="", allocation_rule="none", year=1993),
    ]
    rel = write_master(tmp_root, "x04.csv", rows)
    assert_only(validate(tmp_root, [rel]), "X04", rows=[1, 2, 3, 4], file=rel)


def test_x04_does_not_apply_to_other_streams_or_stages(tmp_root):
    rows = [vrow(7, allocation_rule="none"),
            vrow(1, stage="conv_enrich_fab", tier="impounded", residue_type="u_process_residue", allocation_rule="none")]
    rel = write_master(tmp_root, "x04b.csv", rows)
    assert_clean(validate(tmp_root, [rel]))


def test_x05_event_transfer_out_must_leave_from_the_event_from_tier(tmp_root):
    rows = [vrow(3, tier="sealed_damaged_core"), vrow(4)]
    rel = write_master(tmp_root, "x05a.csv", rows)
    assert_only(validate(tmp_root, [rel]), "X05", rows=[1], file=rel)


def test_x05_event_transfer_in_must_land_in_a_to_tier(tmp_root):
    rows = [vrow(3), vrow(4, tier="dispersed", route="", residue_type="u_tailings")]
    rel = write_master(tmp_root, "x05b.csv", rows)
    assert_only(validate(tmp_root, [rel]), "X05", rows=[2], file=rel)


def test_x05_every_listed_to_tier_is_accepted(tmp_root):
    rows = [vrow(3), vrow(4, tier="sealed_damaged_core", route="")]
    rel = write_master(tmp_root, "x05c.csv", rows)
    assert_clean(validate(tmp_root, [rel]))


def test_x05_second_event(tmp_root):
    out, inn = kingston_pair()
    rel = write_master(tmp_root, "x05d.csv", [out, inn])
    assert_clean(validate(tmp_root, [rel]))
    bad_in = dict(inn, tier="dispersed", route="", residue_type="coal_fly_ash")
    rel2 = write_master(tmp_root, "x05e.csv", [out, bad_in])
    assert_only(validate(tmp_root, [rel2]), "X05", rows=[2], file=rel2)


def test_x05_routine_transfer_outside_the_routine_stages(tmp_root):
    rows = [vrow(3, event_id=""), vrow(4, event_id="")]  # stage accident is not a routine stage
    rel = write_master(tmp_root, "x05f.csv", rows)
    assert_only(validate(tmp_root, [rel]), "X05", rows=[1, 2], file=rel)


def test_x05_routine_transfer_at_a_non_routine_nuclear_stage(tmp_root):
    rows = [vrow(5, stage="conv_enrich_fab"), vrow(6, stage="conv_enrich_fab")]
    rel = write_master(tmp_root, "x05g.csv", rows)
    assert_only(validate(tmp_root, [rel]), "X05", rows=[1, 2], file=rel)


def test_x05_routine_transfer_with_the_wrong_destination_tier(tmp_root):
    rows = [vrow(5), vrow(6, tier="dispersed", route="", residue_type="u_tailings")]
    rel = write_master(tmp_root, "x05h.csv", rows)
    assert_only(validate(tmp_root, [rel]), "X05", rows=[2], file=rel)


def test_x05_routine_transfer_in_the_reverse_direction(tmp_root):
    rows = [vrow(5, tier="liberated", route="sea_disposal_package"), vrow(6, tier="sealed_fuel_cycle", route="")]
    rel = write_master(tmp_root, "x05i.csv", rows)
    assert_only(validate(tmp_root, [rel]), "X05", rows=[1, 2], file=rel)


def test_routine_reprocessing_transfers_are_valid_with_a_civil_token(tmp_root):
    common = dict(stage="reprocessing", country="FRA", year=1990, allocation_rule="civil:throughput")
    rel = write_master(tmp_root, "reproc.csv", [vrow(5, **common), vrow(6, **common)])
    assert_clean(validate(tmp_root, [rel]))


def test_routine_reprocessing_transfers_need_a_civil_token(tmp_root):
    common = dict(stage="reprocessing", country="FRA", year=1990, allocation_rule="none")
    rel = write_master(tmp_root, "reproc_bad.csv", [vrow(5, **common), vrow(6, **common)])
    assert_only(validate(tmp_root, [rel]), "X04", rows=[1, 2], file=rel)


# --------------------------------------------------------------------------- file-level F01-F03, D01

def _with_extra_column(tmp_root, column, name="extra.csv"):
    header = MASTER_COLUMNS + [column]
    rows = [dict(r, **{column: "1"}) for r in VALID_ROWS]
    return write_master(tmp_root, name, rows, header=header)


def test_f02_and_f01_for_collective_dose_column(tmp_root):
    rel = _with_extra_column(tmp_root, "collective_dose")
    issues = validate(tmp_root, [rel])
    for rule in ("F01", "F02"):
        assert any(i.rule == rule and i.file == rel and i.row is None for i in issues), describe(issues)
    # Section 6.5: the rows of a file with F01/F02 are not validated.
    assert rules_of([i for i in issues if i.file == rel]) == {"F01", "F02"}, describe(issues)


@pytest.mark.parametrize(
    "column, expect_f02",
    [
        ("dose", True),
        ("Dose_Rate", True),
        ("effective-dose", True),
        ("effective dose msv", True),
        ("dose/rate", True),
        ("doses", True),
        ("total_sv", True),
        ("SV", True),
        ("msv", True),
        ("usv_per_h", True),
        ("µsv", True),
        ("mansv", True),
        ("personsv", True),
        ("sievert", True),
        ("rem", True),
        ("mrem", True),
        ("manrem", True),
        ("remarks", False),
        ("svalbard", False),
        ("dosage", False),
        ("random", False),
        ("removal", False),
        ("premium_stream", False),
    ],
)
def test_f02_matches_whole_words_split_on_any_non_alphanumeric_character(tmp_root, column, expect_f02):
    rel = _with_extra_column(tmp_root, column)
    issues = [i for i in validate(tmp_root, [rel]) if i.file == rel]
    rules = rules_of(issues)
    assert "F01" in rules  # any extra column breaks the header
    assert ("F02" in rules) is expect_f02, f"column {column!r}: rules raised {sorted(rules)}"


def test_f01_header_missing_column_or_reordered(tmp_root):
    missing = [c for c in MASTER_COLUMNS if c != "notes"]
    rel = write_master(tmp_root, "missing.csv", VALID_ROWS, header=missing)
    issues = validate(tmp_root, [rel])
    assert_only(issues, "F01", rows=[None], file=rel)

    swapped = list(MASTER_COLUMNS)
    swapped[0], swapped[1] = swapped[1], swapped[0]
    rel = write_master(tmp_root, "swapped.csv", VALID_ROWS, header=swapped)
    assert_only(validate(tmp_root, [rel]), "F01", rows=[None], file=rel)


def test_f01_old_v1_master_header_is_rejected(tmp_root):
    v1 = [c for c in MASTER_COLUMNS if c not in ("product", "residue_type", "factor_ids", "route")]
    rel = write_master(tmp_root, "v1.csv", VALID_ROWS, header=v1)
    assert_only(validate(tmp_root, [rel]), "F01", rows=[None], file=rel)


@pytest.mark.parametrize(
    "rel",
    [
        "data/sources.csv",
        "data/events.csv",
        "data/reference/countries.csv",
        "data/reference/groups.csv",
        "data/reference/nuclides.csv",
        "data/reference/residue_types.csv",
        "data/reference/reference_bands.csv",
        "data/activity/series.csv",
        "data/factors/coal.csv",
    ],
)
def test_f01_and_f02_apply_to_every_table(tmp_root, rel):
    path = tmp_root / rel
    header, rows = read_csv(path)
    write_csv(path, header + ["collective_dose"], [dict(r, collective_dose="0") for r in rows])
    issues = [i for i in validate(tmp_root, []) if i.file == rel]
    assert rules_of(issues) == {"F01", "F02"}, describe(issues)
    assert all(i.row is None for i in issues)


@pytest.mark.parametrize("rel", ["data/baselines.csv", "data/reference/commodity_factors.csv"])
def test_f01_and_f02_apply_to_optional_tables_when_present(tmp_root, install_baselines, install_commodity_factors, rel):
    path = tmp_root / rel
    header, rows = read_csv(path)
    write_csv(path, header + ["dose_rate"], [dict(r, dose_rate="0") for r in rows])
    issues = [i for i in validate(tmp_root, []) if i.file == rel]
    assert rules_of(issues) == {"F01", "F02"}, describe(issues)


def test_f03_file_that_is_not_utf8(tmp_root):
    path = tmp_root / "data" / "streams" / "latin1.csv"
    good = (FIXTURES / "valid_rows.csv").read_bytes()
    path.write_bytes(good + b"caf\xe9 \xff\xfe,,,\n")
    issues = validate(tmp_root, ["data/streams/latin1.csv"])
    assert_only(issues, "F03", rows=[None], file="data/streams/latin1.csv")


def test_f03_for_a_listed_master_file_that_does_not_exist(tmp_root):
    issues = validate(tmp_root, ["data/streams/does_not_exist.csv"])
    assert_only(issues, "F03", rows=[None], file="data/streams/does_not_exist.csv")


def test_f03_for_a_support_table_that_is_not_utf8(tmp_root):
    (tmp_root / "data" / "activity" / "series.csv").write_bytes(b"series,year\n\xff\xfe\x80,1900\n")
    issues = [i for i in validate(tmp_root, []) if i.file == "data/activity/series.csv"]
    assert rules_of(issues) == {"F03"}, describe(issues)


DOSE_VALUE_CASES = [
    pytest.param("data/activity/series.csv", 3, dict(series="dose_rate"), id="activity-series"),
    pytest.param("data/activity/series.csv", 3, dict(unit="mSv/a"), id="activity-unit-msv"),
    pytest.param("data/activity/series.csv", 3, dict(unit="rem"), id="activity-unit-rem"),
    pytest.param("data/activity/series.csv", 3, dict(series="collective_sv_total"), id="activity-series-sv-word"),
    pytest.param("data/events.csv", 1, dict(name="Chernobyl collective dose release"), id="event-name"),
    pytest.param("data/factors/coal.csv", 2, dict(description="Dose conversion factor for fly ash"), id="factor-description"),
    pytest.param("data/factors/coal.csv", 2, dict(unit="Sv/t"), id="factor-unit"),
    pytest.param("data/reference/countries.csv", 1, dict(name="Aruba sievert island"), id="country-name"),
    pytest.param("data/reference/residue_types.csv", 1, dict(description="Rem content of uranium tailings"), id="residue-description"),
]


@pytest.mark.parametrize("rel, index, changes", DOSE_VALUE_CASES)
def test_d01_dose_token_in_a_checked_value_column(tmp_root, rel, index, changes):
    corrupt(tmp_root, rel, index, **changes)
    assert_only(validate(tmp_root, []), "D01", rows=[index], file=rel)


def test_d01_baseline_and_commodity_names(tmp_root, install_baselines):
    corrupt(tmp_root, "data/baselines.csv", 2, name="Collective dose from global fallout")
    assert_only(validate(tmp_root, []), "D01", rows=[2], file="data/baselines.csv")


def test_d01_is_reported_once_per_row(tmp_root):
    corrupt(tmp_root, "data/activity/series.csv", 3, series="dose_rate", unit="mSv/a")
    issues = validate(tmp_root, [])
    assert_only(issues, "D01", rows=[3], file="data/activity/series.csv")
    assert len(issues) == 1


@pytest.mark.parametrize("name", ["Removal of ash from the premium stream", "Svalbard seed vault", "Dosage of nothing at all"])
def test_d01_not_raised_for_look_alike_words(tmp_root, install_baselines, name):
    corrupt(tmp_root, "data/baselines.csv", 2, name=name)
    assert_clean(validate(tmp_root, []))


# --------------------------------------------------------------------------- reference tables: nuclides and groups

def _ref(tmp_root, name):
    return tmp_root / "data" / "reference" / name


def test_reference_tables_and_fixture_registries_are_clean(tmp_root):
    assert_clean(validate(tmp_root, []))


def test_g01_member_missing_from_nuclides(tmp_root):
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
    assert_has(validate(tmp_root, []), "G01", n, "data/reference/groups.csv")


def test_g01_head_must_be_the_first_member(tmp_root):
    path = _ref(tmp_root, "groups.csv")
    _, rows = read_csv(path)
    n = find_index(rows, "group", "Ra228+")  # members Ra-228;Ac-228
    edit_csv(path, lambda rs: rs[n - 1].update(members="Ac-228;Ra-228"))
    assert_only(validate(tmp_root, []), "G01", rows=[n], file="data/reference/groups.csv")


def test_g02_multiplier_must_equal_sum_of_member_weights(tmp_root):
    path = _ref(tmp_root, "groups.csv")
    _, rows = read_csv(path)
    n = find_index(rows, "group", "U238+")
    edit_csv(path, lambda rs: rs[n - 1].update(multiplier="3.5"))
    assert_only(validate(tmp_root, []), "G02", rows=[n], file="data/reference/groups.csv")


def test_g02_members_and_weights_must_have_the_same_length(tmp_root):
    path = _ref(tmp_root, "groups.csv")
    _, rows = read_csv(path)
    n = find_index(rows, "group", "Ra228+")
    edit_csv(path, lambda rs: rs[n - 1].update(member_weights="2", multiplier="2"))  # sum matches, lengths do not
    assert_only(validate(tmp_root, []), "G02", rows=[n], file="data/reference/groups.csv")


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


def test_g04_unknown_chain_enum(tmp_root):
    path = _ref(tmp_root, "groups.csv")
    _, rows = read_csv(path)
    n = find_index(rows, "group", "Th230")
    edit_csv(path, lambda rs: rs[n - 1].update(chain="Th999"))
    assert_only(validate(tmp_root, []), "G04", rows=[n], file="data/reference/groups.csv")


@pytest.mark.parametrize("column, value", [("role", "chainlink"), ("multiplier_scope", "flow")])
def test_g04_unknown_role_or_scope_enum(tmp_root, column, value):
    path = _ref(tmp_root, "groups.csv")
    _, rows = read_csv(path)
    n = find_index(rows, "group", "Th230")
    edit_csv(path, lambda rs: rs[n - 1].update({column: value}))
    assert_has(validate(tmp_root, []), "G04", n, "data/reference/groups.csv")


def test_g04_parent_group_must_exist(tmp_root):
    path = _ref(tmp_root, "groups.csv")
    _, rows = read_csv(path)
    n = find_index(rows, "group", "Th230")
    edit_csv(path, lambda rs: rs[n - 1].update(parent_group="NoSuchGroup"))
    assert_only(validate(tmp_root, []), "G04", rows=[n], file="data/reference/groups.csv")


def test_g04_duplicate_group_is_reported_on_the_later_row(tmp_root):
    path = _ref(tmp_root, "groups.csv")
    _, rows = read_csv(path)
    n = find_index(rows, "group", "H3")
    later = append_copy(tmp_root, "data/reference/groups.csv", n)
    assert_only(validate(tmp_root, []), "G04", rows=[later], file="data/reference/groups.csv")


@pytest.mark.parametrize(
    "gas, parent",
    [
        ("Rn222+", "Th228+"),   # chain group that does not contain Rn-222
        ("Rn222+", "H3"),       # not a chain group
        ("Rn222+", "Rn220+"),   # another released gas, not a chain group
        ("Rn220+", "Ra226+"),   # chain group that does not contain Rn-220
    ],
)
def test_g05_released_gas_parent_must_be_a_chain_group_containing_the_head(tmp_root, gas, parent):
    path = _ref(tmp_root, "groups.csv")
    _, rows = read_csv(path)
    n = find_index(rows, "group", gas)
    edit_csv(path, lambda rs: rs[n - 1].update(parent_group=parent))
    assert_only(validate(tmp_root, []), "G05", rows=[n], file="data/reference/groups.csv")


def test_g05_released_gas_without_a_parent_is_not_checked(tmp_root):
    path = _ref(tmp_root, "groups.csv")
    _, rows = read_csv(path)
    n = find_index(rows, "group", "Rn222+")
    edit_csv(path, lambda rs: rs[n - 1].update(parent_group="", parent_branching=""))
    assert_clean(validate(tmp_root, []))


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


# --------------------------------------------------------------------------- sources and events

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
    corrupt(tmp_root, "data/sources.csv", 3, url=url)
    assert_only(validate(tmp_root, []), "S02", rows=[3], file="data/sources.csv")


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
    corrupt(tmp_root, "data/sources.csv", 3, url=url)
    assert_clean(validate(tmp_root, []))


@pytest.mark.parametrize(
    "column, text",
    [
        ("short_cite", "Wikipedia (2020)"),
        ("short_cite", "per GROKIPEDIA entry"),
        ("full_citation", "Compiled from the Wikipedia article on coal ash, accessed 2026."),
        ("full_citation", "Summary taken from Grokipedia, unpublished."),
    ],
)
def test_s02_banned_term_in_the_citation_text(tmp_root, column, text):
    corrupt(tmp_root, "data/sources.csv", 4, **{column: text})
    assert_only(validate(tmp_root, []), "S02", rows=[4], file="data/sources.csv")


def test_s02_citation_term_check_ignores_other_columns(tmp_root):
    corrupt(tmp_root, "data/sources.csv", 4, notes="Do not cite Wikipedia for this one")
    assert_clean(validate(tmp_root, []))


def test_s01_rank_must_match_type(tmp_root):
    corrupt(tmp_root, "data/sources.csv", 2, rank="5")  # regulator must be rank 1
    assert_only(validate(tmp_root, []), "S01", rows=[2], file="data/sources.csv")


@pytest.mark.parametrize("access", ["paywalled", "inaccessible"])
def test_s01_url_is_required_for_paywalled_or_inaccessible_sources(tmp_root, access):
    corrupt(tmp_root, "data/sources.csv", 4, access=access, url="")
    assert_only(validate(tmp_root, []), "S01", rows=[4], file="data/sources.csv")


def test_s01_url_may_be_empty_for_open_sources(tmp_root):
    corrupt(tmp_root, "data/sources.csv", 4, access="open", url="")
    assert_clean(validate(tmp_root, []))


def test_s01_paywalled_source_with_url_is_valid(tmp_root):
    corrupt(tmp_root, "data/sources.csv", 4, access="inaccessible", url="https://example.org/paper.pdf")
    assert_clean(validate(tmp_root, []))


@pytest.mark.parametrize(
    "changes",
    [
        pytest.param(dict(source_id="S12"), id="bad-id-pattern"),
        pytest.param(dict(year="2101"), id="year-above-2100"),
        pytest.param(dict(year="1700"), id="year-below-1800"),
        pytest.param(dict(year="abcd"), id="year-not-an-integer"),
        pytest.param(dict(type="blog"), id="type-not-in-enum"),
        pytest.param(dict(access="secret"), id="access-not-in-enum"),
        pytest.param(dict(licence="free"), id="licence-not-in-enum"),
        pytest.param(dict(url="ftp://example.org/file"), id="url-not-http"),
        pytest.param(dict(doi="not-a-doi"), id="doi-malformed"),
        pytest.param(dict(short_cite=""), id="short-cite-missing"),
    ],
)
def test_s01_schema_failures(tmp_root, changes):
    corrupt(tmp_root, "data/sources.csv", 4, **changes)
    issues = validate(tmp_root, [])
    assert_has(issues, "S01", 4, "data/sources.csv")


def test_s01_duplicate_source_id_is_reported_on_the_later_row(tmp_root):
    later = append_copy(tmp_root, "data/sources.csv", 1)
    assert_only(validate(tmp_root, []), "S01", rows=[later], file="data/sources.csv")


EVENT_E01_CASES = [
    pytest.param(2, dict(military="true"), id="military-event"),
    pytest.param(1, dict(activity_low_bq="6.0e18"), id="activity-low-above-central"),
    pytest.param(1, dict(activity_high_bq="5.0e18"), id="activity-high-below-central"),
    pytest.param(1, dict(to_tiers="liberated;sealed_in_core"), id="from-tier-among-to-tiers"),
    pytest.param(1, dict(date_start="1986-02-30"), id="date-not-on-the-calendar"),
    pytest.param(2, dict(date_start="2009-02-29"), id="29-february-in-a-common-year"),
    pytest.param(1, dict(date_start="1986-13-01"), id="month-13"),
    pytest.param(1, dict(date_end="1986-04-01"), id="date-end-before-date-start"),
    pytest.param(1, dict(date_start="26/04/1986"), id="date-not-iso"),
    pytest.param(2, dict(is_accident="true"), id="is_accident-disagrees-with-event_type"),
    pytest.param(1, dict(is_accident="false"), id="accident-not-flagged"),
    pytest.param(2, dict(event_id="E2"), id="bad-event-id-pattern"),
    pytest.param(1, dict(lat="95"), id="latitude-out-of-range"),
    pytest.param(1, dict(name="x"), id="name-too-short"),
]


@pytest.mark.parametrize("index, changes", EVENT_E01_CASES)
def test_e01_event_failures_are_reported_alone(tmp_root, index, changes):
    corrupt(tmp_root, "data/events.csv", index, **changes)
    assert_only(validate(tmp_root, []), "E01", rows=[index], file="data/events.csv")


@pytest.mark.parametrize(
    "index, changes",
    [
        pytest.param(1, dict(to_tiers="buried"), id="to-tier-not-in-enum"),
        pytest.param(1, dict(to_tiers=""), id="to-tiers-empty"),
        pytest.param(1, dict(inclusion="importance"), id="inclusion-not-in-enum"),
        pytest.param(1, dict(activity_central_bq=""), id="activity-inclusion-without-activity"),
        pytest.param(2, dict(mass_t=""), id="mass-inclusion-without-mass"),
    ],
)
def test_e01_schema_failures_with_possible_e03_overlap(tmp_root, index, changes):
    corrupt(tmp_root, "data/events.csv", index, **changes)
    assert_has(validate(tmp_root, []), "E01", index, "data/events.csv")


@pytest.mark.parametrize("date", ["2008-02-29", "2008-12-31"])
def test_e01_accepts_real_calendar_dates(tmp_root, date):
    corrupt(tmp_root, "data/events.csv", 2, date_start=date, date_end="")
    assert_clean(validate(tmp_root, []))


def test_e01_date_end_equal_to_date_start_is_valid(tmp_root):
    corrupt(tmp_root, "data/events.csv", 1, date_end="1986-04-26")
    assert_clean(validate(tmp_root, []))


def test_e01_duplicate_event_id_is_reported_on_the_later_row(tmp_root):
    later = append_copy(tmp_root, "data/events.csv", 2)
    assert_only(validate(tmp_root, []), "E01", rows=[later], file="data/events.csv")


@pytest.mark.parametrize(
    "index, changes",
    [
        pytest.param(1, dict(activity_low_bq="1e10", activity_central_bq="5e11", activity_high_bq="8e11"), id="activity-below-1TBq"),
        pytest.param(1, dict(to_tiers="sealed_damaged_core"), id="activity-event-without-liberated-or-dispersed-destination"),
        pytest.param(1, dict(to_tiers="sealed_fuel_cycle;impounded"), id="activity-event-ending-in-sealed-or-impounded-tiers"),
        pytest.param(2, dict(mass_t="5.0e4"), id="mass-below-1e5-t"),
        pytest.param(2, dict(from_tier="reisolated"), id="mass-event-not-from-an-impoundment"),
        pytest.param(2, dict(from_tier="dispersed"), id="mass-event-from-dispersed"),
    ],
)
def test_e03_inclusion_criterion_not_met(tmp_root, index, changes):
    corrupt(tmp_root, "data/events.csv", index, **changes)
    assert_only(validate(tmp_root, []), "E03", rows=[index], file="data/events.csv")


@pytest.mark.parametrize(
    "index, changes",
    [
        pytest.param(1, dict(activity_low_bq="1e12", activity_central_bq="1e12", activity_high_bq="1e12"), id="activity-exactly-1TBq"),
        pytest.param(1, dict(to_tiers="dispersed;sealed_damaged_core"), id="activity-event-ending-in-dispersed"),
        pytest.param(1, dict(to_tiers="sealed_damaged_core;liberated"), id="liberated-in-any-position"),
        pytest.param(2, dict(mass_t="1.0e5"), id="mass-exactly-1e5-t"),
        pytest.param(2, dict(to_tiers="dispersed"), id="mass-event-to-dispersed"),
    ],
)
def test_e03_boundaries_that_meet_the_criterion(tmp_root, index, changes):
    corrupt(tmp_root, "data/events.csv", index, **changes)
    assert_clean(validate(tmp_root, []))


@pytest.mark.parametrize(
    "changes",
    [
        pytest.param(dict(stage="u_milling"), id="stage-not-allowed-for-stream"),
        pytest.param(dict(country="ZZZ"), id="unknown-country"),
        pytest.param(dict(source_ids="S0005;S0099"), id="unknown-source"),
    ],
)
def test_e02_event_vocabulary_membership(tmp_root, changes):
    corrupt(tmp_root, "data/events.csv", 2, **changes)
    assert_only(validate(tmp_root, []), "E02", rows=[2], file="data/events.csv")


# --------------------------------------------------------------------------- support tables: T01-T05

def _fill_residue(**over):
    params = dict(
        epsilon_rn222_low="0.1", epsilon_rn222_central="0.2", epsilon_rn222_high="0.3",
        epsilon_rn220_low="0.05", epsilon_rn220_central="0.1", epsilon_rn220_high="0.2",
        seepage_per_a_low="0.001", seepage_per_a_central="0.002", seepage_per_a_high="0.01",
        basis="compiled", source_ids="S0003",
    )
    params.update(over)
    return params


def test_residue_types_fully_filled_parameter_sets_are_valid(tmp_root):
    corrupt(tmp_root, "data/reference/residue_types.csv", 1, **_fill_residue())
    assert_clean(validate(tmp_root, []))


def test_optional_baselines_and_commodity_factors_are_validated_when_present(tmp_root, install_baselines, install_commodity_factors):
    assert_clean(validate(tmp_root, []))


def test_data_activity_may_be_absent_when_no_factor_needs_a_driver(tmp_root):
    shutil.rmtree(tmp_root / "data" / "activity")
    shutil.rmtree(tmp_root / "data" / "factors")
    assert_clean(validate(tmp_root, []))


T01_CASES = [
    pytest.param("data/reference/countries.csv", 1, dict(code="AB"), id="countries-code-two-letters"),
    pytest.param("data/reference/countries.csv", 1, dict(code="abw"), id="countries-code-lower-case"),
    pytest.param("data/reference/countries.csv", 1, dict(kind="colony"), id="countries-kind-not-in-enum"),
    pytest.param("data/reference/countries.csv", 1, dict(valid_from="1800"), id="countries-window-before-1900"),
    pytest.param("data/reference/countries.csv", 1, dict(valid_to="soon"), id="countries-window-not-an-integer"),
    pytest.param("data/reference/countries.csv", 1, dict(name="X"), id="countries-name-too-short"),
    pytest.param("data/activity/series.csv", 3, dict(year="1799"), id="activity-year-below-1800"),
    pytest.param("data/activity/series.csv", 3, dict(year="2026"), id="activity-year-above-2025"),
    pytest.param("data/activity/series.csv", 3, dict(value_low="-1"), id="activity-negative-value"),
    pytest.param("data/activity/series.csv", 3, dict(series="Coal-Production"), id="activity-series-not-snake-case"),
    pytest.param("data/activity/series.csv", 3, dict(basis="guess"), id="activity-basis-not-in-enum"),
    pytest.param("data/activity/series.csv", 3, dict(unit=""), id="activity-unit-missing"),
    pytest.param("data/activity/series.csv", 3, dict(source_ids=""), id="activity-source-ids-missing"),
    pytest.param("data/activity/series.csv", 3, dict(below_detection="true"), id="activity-below-detection-with-nonzero-low"),
    pytest.param("data/activity/series.csv", 3, dict(below_detection="maybe"), id="activity-bool-not-coercible"),
    pytest.param("data/activity/series.csv", 3, dict(value_central="abc"), id="activity-float-not-coercible"),
    pytest.param("data/factors/coal.csv", 1, dict(factor_id="coal-1"), id="factors-id-pattern"),
    pytest.param("data/factors/coal.csv", 2, dict(tier="buried"), id="factors-tier-not-in-enum"),
    pytest.param("data/factors/coal.csv", 2, dict(unit=""), id="factors-unit-missing"),
    pytest.param("data/factors/coal.csv", 2, dict(route="air_leak"), id="factors-route-not-in-enum"),
    pytest.param("data/factors/coal.csv", 2, dict(year_from="1700"), id="factors-year-from-below-1800"),
    pytest.param("data/reference/residue_types.csv", 1, dict(_fill_residue(epsilon_rn222_high="1.5")), id="residue-epsilon-above-1"),
    pytest.param("data/reference/residue_types.csv", 1, dict(_fill_residue(seepage_per_a_low="-0.1")), id="residue-seepage-negative"),
    pytest.param("data/reference/residue_types.csv", 1, dict(streams="nuclear;mars"), id="residue-stream-not-in-enum"),
    pytest.param("data/reference/residue_types.csv", 1, dict(streams=""), id="residue-streams-missing"),
    pytest.param("data/reference/residue_types.csv", 1, dict(residue_type="Bad-Name"), id="residue-type-not-snake-case"),
    pytest.param("data/reference/residue_types.csv", 1, dict(_fill_residue(basis="guess")), id="residue-basis-not-in-enum"),
    pytest.param("data/reference/reference_bands.csv", 1, dict(rel_low="0.1"), id="bands-rel-low-positive"),
    pytest.param("data/reference/reference_bands.csv", 1, dict(rel_low="-1.5"), id="bands-rel-low-below-minus-1"),
    pytest.param("data/reference/reference_bands.csv", 1, dict(rel_high="-0.1"), id="bands-rel-high-negative"),
    pytest.param("data/reference/reference_bands.csv", 1, dict(band_id="RB1"), id="bands-id-pattern"),
    pytest.param("data/reference/reference_bands.csv", 1, dict(quantity_class="e_gamma"), id="bands-class-not-in-enum"),
    pytest.param("data/reference/reference_bands.csv", 1, dict(rel_low="n/a"), id="bands-float-not-coercible"),
    pytest.param("data/reference/reference_bands.csv", 1, dict(source_ids=""), id="bands-source-ids-missing"),
]


@pytest.mark.parametrize("rel, index, changes", T01_CASES)
def test_t01_row_fails_the_table_schema(tmp_root, rel, index, changes):
    corrupt(tmp_root, rel, index, **changes)
    assert_only(validate(tmp_root, []), "T01", rows=[index], file=rel)


BASELINE_T01 = [
    pytest.param(1, dict(unit="W"), id="stock-with-watts"),
    pytest.param(3, dict(unit="Bq"), id="power-with-becquerel"),
    pytest.param(2, dict(quantity="flow"), id="flow-with-stock-unit"),
    pytest.param(1, dict(baseline_id="B1"), id="id-pattern"),
    pytest.param(1, dict(quantity="flux"), id="quantity-not-in-enum"),
    pytest.param(1, dict(derivation=""), id="derivation-missing"),
    pytest.param(2, dict(year="1700"), id="year-below-1800"),
    pytest.param(1, dict(value_central="-5"), id="negative-value"),
]


@pytest.mark.parametrize("index, changes", BASELINE_T01)
def test_t01_baselines(tmp_root, install_baselines, index, changes):
    corrupt(tmp_root, "data/baselines.csv", index, **changes)
    issues = [i for i in validate(tmp_root, []) if i.file == "data/baselines.csv"]
    assert "T01" in rules_of(issues) and any(i.row == index for i in issues if i.rule == "T01"), describe(issues)


COMMODITY_T01 = [
    pytest.param(1, dict(unit="Bq/kg"), id="unit-not-bq-per-t"),
    pytest.param(4, dict(tier="sealed_in_core"), id="tier-not-in-enum"),
    pytest.param(4, dict(route=""), id="liberated-without-route"),
    pytest.param(5, dict(route="air_dust"), id="route-on-non-liberated-tier"),
    pytest.param(5, dict(residue_type=""), id="residue-tier-without-residue-type"),
    pytest.param(4, dict(residue_type="ree_tailings"), id="residue-type-on-liberated-tier"),
    pytest.param(4, dict(commodity="unobtainium"), id="commodity-not-in-enum"),
    pytest.param(4, dict(component="own_fuel"), id="component-not-in-enum"),
    pytest.param(4, dict(year_from="1700"), id="year-from-below-1800"),
    pytest.param(4, dict(allocation_rule="value"), id="rule-token-without-prefix"),
    pytest.param(4, dict(below_detection="true"), id="below-detection-with-nonzero-low"),
]


@pytest.mark.parametrize("index, changes", COMMODITY_T01)
def test_t01_commodity_factors(tmp_root, install_commodity_factors, index, changes):
    corrupt(tmp_root, "data/reference/commodity_factors.csv", index, **changes)
    assert_only(validate(tmp_root, []), "T01", rows=[index], file="data/reference/commodity_factors.csv")


def test_t01_commodity_bound_row_needs_its_own_token(tmp_root, install_commodity_factors):
    corrupt(tmp_root, "data/reference/commodity_factors.csv", 2, allocation_rule="alloc:value")  # B2
    assert_has(validate(tmp_root, []), "T01", 2, "data/reference/commodity_factors.csv")


def test_t02_duplicate_country_code_is_reported_on_the_later_row(tmp_root):
    later = append_copy(tmp_root, "data/reference/countries.csv", 1)
    assert_only(validate(tmp_root, []), "T02", rows=[later], file="data/reference/countries.csv")


def test_t02_duplicate_activity_key_within_a_file(tmp_root):
    later = append_copy(tmp_root, "data/activity/series.csv", 2, value_central="3.6e9")
    assert_only(validate(tmp_root, []), "T02", rows=[later], file="data/activity/series.csv")


def test_t02_duplicate_activity_key_across_files_is_reported_on_the_later_file(tmp_root):
    header, rows = read_csv(tmp_root / "data" / "activity" / "series.csv")
    write_csv(tmp_root / "data" / "activity" / "zz_more.csv", header, [rows[1]])
    assert_only(validate(tmp_root, []), "T02", rows=[1], file="data/activity/zz_more.csv")


def test_t02_activity_key_differs_by_series_year_and_country(tmp_root):
    header, rows = read_csv(tmp_root / "data" / "activity" / "series.csv")
    variants = [dict(rows[1], year="2016"), dict(rows[1], country="IND"), dict(rows[1], series="coal_imports")]
    write_csv(tmp_root / "data" / "activity" / "zz_more.csv", header, variants)
    assert_clean(validate(tmp_root, []))


def test_t02_duplicate_baseline_id(tmp_root, install_baselines):
    later = append_copy(tmp_root, "data/baselines.csv", 1)
    assert_only(validate(tmp_root, []), "T02", rows=[later], file="data/baselines.csv")


def test_t02_duplicate_commodity_factor_key(tmp_root, install_commodity_factors):
    later = append_copy(tmp_root, "data/reference/commodity_factors.csv", 4, value_central="3.0e6")
    assert_only(validate(tmp_root, []), "T02", rows=[later], file="data/reference/commodity_factors.csv")


def test_t02_duplicate_factor_id_across_files_is_reported_on_the_later_file(tmp_root):
    header, rows = read_csv(tmp_root / "data" / "factors" / "coal.csv")
    write_csv(tmp_root / "data" / "factors" / "zz_other.csv", header, [rows[0]])
    assert_only(validate(tmp_root, []), "T02", rows=[1], file="data/factors/zz_other.csv")


def test_t02_duplicate_residue_type(tmp_root):
    later = append_copy(tmp_root, "data/reference/residue_types.csv", 1)
    assert_only(validate(tmp_root, []), "T02", rows=[later], file="data/reference/residue_types.csv")


def test_t02_duplicate_band_id(tmp_root):
    later = append_copy(tmp_root, "data/reference/reference_bands.csv", 4, quantity_class="e_alpha", applies_to="Ac-227")
    assert_only(validate(tmp_root, []), "T02", rows=[later], file="data/reference/reference_bands.csv")


def test_t02_second_default_band_for_the_same_class(tmp_root):
    later = append_copy(tmp_root, "data/reference/reference_bands.csv", 1, band_id="RB99")  # half_life, '*'
    assert_only(validate(tmp_root, []), "T02", rows=[later], file="data/reference/reference_bands.csv")


def test_t02_nuclide_named_twice_in_the_same_class(tmp_root):
    later = append_copy(tmp_root, "data/reference/reference_bands.csv", 2, band_id="RB99", rel_low="-0.1", rel_high="0.1")
    assert_only(validate(tmp_root, []), "T02", rows=[later], file="data/reference/reference_bands.csv")


def test_t02_same_nuclide_in_different_classes_is_valid(tmp_root):
    append_copy(tmp_root, "data/reference/reference_bands.csv", 2, band_id="RB99", quantity_class="e_alpha")
    assert_clean(validate(tmp_root, []))


T03_CASES = [
    pytest.param("data/activity/series.csv", 3, dict(value_low="9e8"), id="activity-low-above-central"),
    pytest.param("data/activity/series.csv", 3, dict(value_high="1e8"), id="activity-high-below-central"),
    pytest.param("data/factors/coal.csv", 2, dict(year_from="2030", year_to="2020"), id="factors-year-from-after-year-to"),
    pytest.param("data/factors/coal.csv", 2, dict(value_low="9e2"), id="factors-low-above-central"),
    pytest.param("data/reference/residue_types.csv", 1, dict(_fill_residue(epsilon_rn222_low="0.5")), id="residue-epsilon-rn222-unordered"),
    pytest.param("data/reference/residue_types.csv", 1, dict(_fill_residue(seepage_per_a_high="0.0001")), id="residue-seepage-unordered"),
    pytest.param("data/reference/residue_types.csv", 1, dict(epsilon_rn222_central="0.2"), id="residue-partial-set-single-value"),
    pytest.param("data/reference/residue_types.csv", 1, dict(_fill_residue(seepage_per_a_low="", seepage_per_a_central="", seepage_per_a_high="0.01")), id="residue-partial-set-two-empty"),
    pytest.param("data/reference/residue_types.csv", 1, dict(_fill_residue(epsilon_rn220_central="")), id="residue-partial-set-one-empty"),
    pytest.param("data/reference/residue_types.csv", 1, dict(_fill_residue(basis="")), id="residue-filled-without-basis"),
    pytest.param("data/reference/residue_types.csv", 1, dict(_fill_residue(source_ids="")), id="residue-filled-without-source-ids"),
    pytest.param("data/reference/residue_types.csv", 1, dict(_fill_residue(basis="", source_ids="")), id="residue-filled-without-basis-or-source-ids"),
]


@pytest.mark.parametrize("rel, index, changes", T03_CASES)
def test_t03_bounds_out_of_order(tmp_root, rel, index, changes):
    corrupt(tmp_root, rel, index, **changes)
    assert_only(validate(tmp_root, []), "T03", rows=[index], file=rel)


def test_t03_baselines(tmp_root, install_baselines):
    corrupt(tmp_root, "data/baselines.csv", 1, value_low="9e17")
    assert_only(validate(tmp_root, []), "T03", rows=[1], file="data/baselines.csv")


@pytest.mark.parametrize(
    "index, changes",
    [
        pytest.param(4, dict(year_from="2030", year_to="2020"), id="year-from-after-year-to"),
        pytest.param(4, dict(value_central="1e8"), id="central-above-high"),
        pytest.param(4, dict(value_low="9e6"), id="low-above-central"),
    ],
)
def test_t03_commodity_factors(tmp_root, install_commodity_factors, index, changes):
    corrupt(tmp_root, "data/reference/commodity_factors.csv", index, **changes)
    assert_only(validate(tmp_root, []), "T03", rows=[index], file="data/reference/commodity_factors.csv")


def test_t03_year_from_equal_to_year_to_is_valid(tmp_root):
    corrupt(tmp_root, "data/factors/coal.csv", 2, year_from="2000", year_to="2000")
    assert_clean(validate(tmp_root, []))


T04_CASES = [
    pytest.param("data/activity/series.csv", 3, dict(country="ZZZ"), id="activity-country"),
    pytest.param("data/activity/series.csv", 3, dict(source_ids="S0099"), id="activity-source"),
    pytest.param("data/activity/series.csv", 3, dict(source_ids="S0003;S0099"), id="activity-one-source-of-two"),
    pytest.param("data/factors/coal.csv", 1, dict(driver_series="nope_series"), id="factors-driver-series"),
    pytest.param("data/factors/coal.csv", 1, dict(stage="u_milling"), id="factors-stage-not-for-stream"),
    pytest.param("data/factors/coal.csv", 1, dict(region="ZZZ"), id="factors-region"),
    pytest.param("data/factors/coal.csv", 1, dict(source_ids="S0099"), id="factors-source"),
    pytest.param("data/reference/residue_types.csv", 1, dict(_fill_residue(source_ids="S0099")), id="residue-source"),
    pytest.param("data/reference/reference_bands.csv", 1, dict(source_ids="S0099"), id="bands-source"),
    pytest.param("data/reference/reference_bands.csv", 2, dict(applies_to="Zz-999"), id="bands-unknown-nuclide"),
    pytest.param("data/reference/reference_bands.csv", 2, dict(applies_to="At-218;NoSuchGroup"), id="bands-one-unknown-entry"),
]


@pytest.mark.parametrize("rel, index, changes", T04_CASES)
def test_t04_reference_does_not_resolve(tmp_root, rel, index, changes):
    corrupt(tmp_root, rel, index, **changes)
    assert_only(validate(tmp_root, []), "T04", rows=[index], file=rel)


def test_t04_applies_to_may_name_groups_and_the_default_marker(tmp_root):
    corrupt(tmp_root, "data/reference/reference_bands.csv", 2, applies_to="At-218;K40")
    issues = [i for i in validate(tmp_root, []) if i.row == 2]
    assert "T04" not in rules_of(issues), describe(issues)


def test_t04_factor_driver_series_is_looked_up_in_all_activity_files(tmp_root):
    header, _ = read_csv(tmp_root / "data" / "activity" / "series.csv")
    write_csv(tmp_root / "data" / "activity" / "zz_more.csv", header, [dict(
        series="nope_series", year="2000", country="USA", value_low="1", value_central="2", value_high="3",
        unit="t", below_detection="false", basis="compiled", source_ids="S0003", notes="")])
    corrupt(tmp_root, "data/factors/coal.csv", 1, driver_series="nope_series")
    assert_clean(validate(tmp_root, []))


def test_t04_every_factor_with_a_driver_fails_when_activity_files_are_absent(tmp_root):
    shutil.rmtree(tmp_root / "data" / "activity")
    assert_only(validate(tmp_root, []), "T04", rows=[1, 2], file="data/factors/coal.csv")


def test_t04_baselines(tmp_root, install_baselines):
    corrupt(tmp_root, "data/baselines.csv", 1, group="Tc98")
    assert_only(validate(tmp_root, []), "T04", rows=[1], file="data/baselines.csv")
    corrupt(tmp_root, "data/baselines.csv", 1, group="Rn222+", source_ids="S0099")
    assert_only(validate(tmp_root, []), "T04", rows=[1], file="data/baselines.csv")


@pytest.mark.parametrize(
    "changes",
    [
        pytest.param(dict(group="Tc98"), id="unknown-group"),
        pytest.param(dict(residue_type="moon_dust"), id="unknown-residue-type"),
        pytest.param(dict(region="ZZZ"), id="unknown-region"),
        pytest.param(dict(source_ids="S0099"), id="unknown-source"),
    ],
)
def test_t04_commodity_factors(tmp_root, install_commodity_factors, changes):
    corrupt(tmp_root, "data/reference/commodity_factors.csv", 5, **changes)  # row 5 is a default-only key
    assert_only(validate(tmp_root, []), "T04", rows=[5], file="data/reference/commodity_factors.csv")


def test_t04_commodity_factor_region_may_be_xwl(tmp_root, install_commodity_factors):
    # fixture row 1 already uses XWL
    assert_clean(validate(tmp_root, []))


def test_t05_commodity_factors_missing_variant(tmp_root, install_commodity_factors):
    path = tmp_root / "data" / "reference" / "commodity_factors.csv"
    edit_csv(path, lambda rows: rows.pop(2))  # drop bound_radio of the copper key
    assert_only(validate(tmp_root, []), "T05", rows=[1], file="data/reference/commodity_factors.csv")


def test_t05_commodity_factors_only_non_default_variant(tmp_root, install_commodity_factors):
    path = tmp_root / "data" / "reference" / "commodity_factors.csv"
    edit_csv(path, lambda rows: (rows.pop(2), rows.pop(0)))  # leaves bound_main (row 1) and the ree_oxide row
    assert_only(validate(tmp_root, []), "T05", rows=[1], file="data/reference/commodity_factors.csv")


def test_t05_commodity_factors_default_row_lacks_alloc_value_or_mass(tmp_root, install_commodity_factors):
    corrupt(tmp_root, "data/reference/commodity_factors.csv", 1, allocation_rule="none")
    assert_only(validate(tmp_root, []), "T05", rows=[1], file="data/reference/commodity_factors.csv")


def test_t05_commodity_factors_default_only_key_is_normal(tmp_root, install_commodity_factors):
    # fixture row 4 (ree_oxide) is default-only with rule `none`
    assert_clean(validate(tmp_root, []))


def test_t05_commodity_factors_complete_key_with_alloc_mass(tmp_root, install_commodity_factors):
    corrupt(tmp_root, "data/reference/commodity_factors.csv", 1, allocation_rule="alloc:mass")
    assert_clean(validate(tmp_root, []))


# --------------------------------------------------------------------------- API behaviour

REQUIRED_FILES = [
    "data/reference/vocab.json",
    "data/reference/countries.csv",
    "data/reference/nuclides.csv",
    "data/reference/groups.csv",
    "data/reference/residue_types.csv",
    "data/reference/reference_bands.csv",
    "schema/master.json",
    "schema/sources.json",
    "schema/events.json",
    "schema/countries.json",
    "schema/activity.json",
    "schema/baselines.json",
    "schema/commodity_factors.json",
    "schema/factors.json",
    "schema/residue_types.json",
    "schema/reference_bands.json",
    "data/sources.csv",
]


@pytest.mark.parametrize("required", REQUIRED_FILES)
def test_missing_required_file_raises_file_not_found(tmp_root, required):
    (tmp_root / required).unlink()
    with pytest.raises(FileNotFoundError):
        validate(tmp_root, [])


@pytest.mark.parametrize("optional", ["data/events.csv"])
def test_missing_optional_file_is_allowed(tmp_root, optional):
    (tmp_root / optional).unlink()
    assert_clean(validate(tmp_root, []))


def test_missing_events_csv_means_no_events(tmp_root):
    (tmp_root / "data" / "events.csv").unlink()
    rel = write_master(tmp_root, "valid.csv", VALID_ROWS)
    # Unknown event: V08 only; X05 is skipped for those rows (section 6.5).
    assert_only(validate(tmp_root, [rel]), "V08", rows=[3, 4], file=rel)


def test_missing_factor_registry_means_no_factors(tmp_root):
    shutil.rmtree(tmp_root / "data" / "factors")
    rel = write_master(tmp_root, "valid.csv", VALID_ROWS)
    assert_only(validate(tmp_root, [rel]), "V13", rows=[7], file=rel)


def test_default_master_files_are_data_streams_only(tmp_root):
    write_master(tmp_root, "a_valid.csv", [vrow(7)])
    write_master(tmp_root, "b_invalid.csv", [vrow(10), vrow(8, unit="Bq")])
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


def test_default_master_files_are_processed_in_sorted_name_order(tmp_root):
    write_master(tmp_root, "b.csv", VALID_ROWS)
    write_master(tmp_root, "a.csv", VALID_ROWS)
    # "Later" is the later in processing order, i.e. b.csv.
    assert_only(validate(tmp_root), "X01", rows=range(1, 11), file="data/streams/b.csv")


def test_empty_master_files_list_checks_no_master_files(tmp_root):
    write_master(tmp_root, "invalid.csv", [vrow(10, unit="Bq")])
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


def test_master_file_outside_the_root_is_reported_with_its_absolute_posix_path(tmp_root, tmp_path):
    outside = tmp_path / "elsewhere" / "outside.csv"
    outside.parent.mkdir()
    shutil.copy(INVALID_DIR / "01_r02_wrong_unit.csv", outside)
    issues = validate(tmp_root, [outside])
    assert_only(issues, "R02", rows=[2])
    assert {i.file for i in issues} <= {outside.as_posix(), outside.resolve().as_posix()}, describe(issues)  # B12


def test_issues_are_ordered_by_file_then_row_then_rule(tmp_root):
    a = write_master(tmp_root, "a.csv", [
        vrow(10, value_low="9e13"),                       # row 1: R03
        vrow(7, group="Tc98", source_ids="S0099"),        # row 2: V04 and V07
        vrow(3),                                          # row 3: lone transfer -> X02 (row None)
    ])
    b = write_master(tmp_root, "b.csv", [vrow(8, value_low="9e12", value_high="1e11"), vrow(2, unit="Bq/a")])
    issues = validate(tmp_root, [b, a])  # passed out of order on purpose
    assert len(issues) >= 5, describe(issues)
    key = lambda i: (i.file, i.row is not None, i.row if i.row is not None else 0, i.rule)
    assert [key(i) for i in issues] == sorted(key(i) for i in issues), describe(issues)
    assert issues == validate(tmp_root, [b, a]), "output must be stable between calls"
    first_a = [i for i in issues if i.file == a]
    assert first_a[0].row is None and first_a[0].rule == "X02", describe(issues)


def test_file_level_issues_sort_before_row_issues_of_the_same_file(tmp_root):
    corrupt(tmp_root, "data/sources.csv", 2, rank="5")           # S01 row 2
    corrupt(tmp_root, "data/sources.csv", 1, short_cite="Wikipedia 2020")  # S02 row 1
    issues = validate(tmp_root, [])
    assert [(i.row, i.rule) for i in issues] == [(1, "S02"), (2, "S01")], describe(issues)


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
    return subprocess.run(
        [sys.executable, "-m", "pipeline.validate", *[str(a) for a in args]],
        cwd=str(cwd), env=env, capture_output=True, text=True, timeout=180,
    )


def test_cli_exit_0_and_summary_on_valid_file(tmp_root, tmp_path):
    rel = write_master(tmp_root, "valid.csv", VALID_ROWS)
    result = run_cli(["--root", tmp_root, tmp_root / rel], cwd=tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip(), "a summary line is expected on stdout even when there are no issues"
    assert not re.search(r":(\d+|-): [A-Z]\d\d ", result.stdout), result.stdout


def test_cli_exit_1_and_issue_line_on_stdout(tmp_root, tmp_path):
    name = "03_r03_low_above_high.csv"
    shutil.copy(INVALID_DIR / name, tmp_root / "data" / "streams" / name)
    result = run_cli(["--root", tmp_root, tmp_root / "data" / "streams" / name], cwd=tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert re.search(rf"{re.escape(name)}:2: R03\b", result.stdout), result.stdout


def test_cli_prints_dash_for_file_level_issues(tmp_root, tmp_path):
    name = "08_x02_unbalanced_transfers.csv"
    shutil.copy(INVALID_DIR / name, tmp_root / "data" / "streams" / name)
    result = run_cli(["--root", tmp_root, tmp_root / "data" / "streams" / name], cwd=tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert re.search(rf"{re.escape(name)}:-: X02\b", result.stdout), result.stdout


@pytest.mark.parametrize("name", sorted(CASES))
def test_cli_exit_1_for_every_invalid_case(tmp_root, tmp_path, name):
    shutil.copy(INVALID_DIR / name, tmp_root / "data" / "streams" / name)
    result = run_cli(["--root", tmp_root, tmp_root / "data" / "streams" / name], cwd=tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    row = "-" if CASES[name]["row"] is None else str(CASES[name]["row"])
    assert re.search(rf":{row}: {CASES[name]['rule']}\b", result.stdout), result.stdout


def test_cli_relative_file_arguments_are_taken_relative_to_root(tmp_root, tmp_path):
    write_master(tmp_root, "valid.csv", VALID_ROWS)
    result = run_cli(["--root", tmp_root, "data/streams/valid.csv"], cwd=tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr

    name = "03_r03_low_above_high.csv"
    shutil.copy(INVALID_DIR / name, tmp_root / "data" / "streams" / name)
    result = run_cli(["--root", tmp_root, f"data/streams/{name}"], cwd=tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr


def test_cli_exit_1_for_reference_table_problem_without_master_files(tmp_root, tmp_path):
    corrupt(tmp_root, "data/reference/groups.csv", 1, multiplier="3.5")
    result = run_cli(["--root", tmp_root], cwd=tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert re.search(r":1: G02\b", result.stdout), result.stdout


def test_cli_exit_2_on_missing_required_reference_file(tmp_root, tmp_path):
    (_ref(tmp_root, "nuclides.csv")).unlink()
    rel = write_master(tmp_root, "valid.csv", VALID_ROWS)
    result = run_cli(["--root", tmp_root, tmp_root / rel], cwd=tmp_path)
    assert result.returncode == 2, result.stdout + result.stderr
    assert result.stderr.strip(), "errors go to stderr"


@pytest.mark.parametrize("required", ["data/reference/residue_types.csv", "data/reference/reference_bands.csv", "schema/factors.json", "schema/reference_bands.json"])
def test_cli_exit_2_on_missing_new_required_files(tmp_root, tmp_path, required):
    (tmp_root / required).unlink()
    result = run_cli(["--root", tmp_root], cwd=tmp_path)
    assert result.returncode == 2, result.stdout + result.stderr


def test_cli_exit_2_on_usage_error(tmp_root, tmp_path):
    result = run_cli(["--root", tmp_root, "--no-such-option"], cwd=tmp_path)
    assert result.returncode == 2, result.stdout + result.stderr


def test_cli_root_defaults_to_current_directory_and_files_default_to_data_streams(tmp_root):
    write_master(tmp_root, "valid.csv", VALID_ROWS)
    result = run_cli([], cwd=tmp_root)
    assert result.returncode == 0, result.stdout + result.stderr

    write_master(tmp_root, "zz_invalid.csv", [vrow(7, year=2001), vrow(10, unit="Bq", year=2016)])
    result = run_cli([], cwd=tmp_root)
    assert result.returncode == 1, result.stdout + result.stderr
    assert re.search(r"zz_invalid\.csv:2: R02\b", result.stdout), result.stdout


# --------------------------------------------------------------------------- the real project root

def test_real_project_reference_tables_and_sources_validate_cleanly():
    issues = validate(REAL_ROOT, master_files=[])
    assert_clean(issues)
