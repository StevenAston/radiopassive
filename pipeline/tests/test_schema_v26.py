"""Spec-blind tests for SCHEMA v2.6 (D74): `commodity_factors.csv` gains `factor_id` and `ore_type`
(4.7), the optional table `commodity_fuel_inputs.csv` (4.13), `vocab.json` gains `cast_iron`,
`tio2_pigment`, `ore_types` and `fuel_input_fuels` (5.5), and the new rule behaviour of F01, T01-T05
and V13 for those tables.

Two groups:

* Fixture tests (`tmp_root` trees, written here from SCHEMA 4.7 / 6 alone). The tmp_root vocab.json
  is patched in-test with the v2.6 vocabulary so the tests do not depend on the data/ migration.
* Real-data tests (class `TestAppliedData`): premises about data/ once build/d74_staging/ has been
  applied. They are skipped, with a stated reason, while data/reference/commodity_factors.csv is
  absent or lacks the `factor_id` column. After that, a failure whose message starts with
  `PREMISE BROKEN` means the applied data contradicts the v2.6 schema.

SCHEMA 4.13 (commodity_fuel_inputs) is now specified: key (commodity, fuel, region, year_from),
unit coupled to fuel (MWh/t iff electricity), stream_ref equal to fuel_input_fuels[fuel], no T05.
"""
from __future__ import annotations

import copy
import csv
import json
import re
import shutil
from pathlib import Path

import pytest

from pipeline.validate import validate

FIXTURES = Path(__file__).resolve().parent / "fixtures"
REAL_ROOT = Path(__file__).resolve().parents[2]
CF = "data/reference/commodity_factors.csv"
FI = "data/reference/commodity_fuel_inputs.csv"

CF_HEADER = ["factor_id", "commodity", "component", "group", "tier", "route", "residue_type", "region",
             "ore_type", "year_from", "year_to", "allocation_variant", "allocation_rule", "value_low",
             "value_central", "value_high", "unit", "below_detection", "basis", "source_ids", "notes"]
FI_HEADER = ["commodity", "fuel", "stream_ref", "region", "year_from", "year_to", "value_low",
             "value_central", "value_high", "unit", "basis", "source_ids", "notes"]

ORE_TYPES = {
    "copper": ["porphyry_stratiform", "iocg_olympic_dam", "iocg_high_u", "cu_co_stratiform", "all"],
    "ree_oxide": ["ree_bayan_obo", "ree_ionic_clay", "ree_monazite", "ree_mt_weld"],
}
FUEL_INPUT_FUELS = {"coal": "coal", "coke": "coal", "petroleum_coke": "oil_gas",
                    "natural_gas": "oil_gas", "fuel_oil": "oil_gas", "electricity": ""}


# --------------------------------------------------------------------------- helpers
def desc(issues):
    return "\n".join(f"  {i.file}:{i.row}: {i.rule} {i.message}" for i in issues) or "  (no issues)"


def rules(issues, file=None):
    return {i.rule for i in issues if file is None or i.file == file}


def has(issues, rule, row, file):
    return any(i.rule == rule and i.row == row and i.file == file for i in issues)


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        r = csv.DictReader(fh)
        return list(r.fieldnames), list(r)


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=header, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def cf_row(fid, **over):
    row = {"factor_id": fid, "commodity": "copper", "component": "own_residue", "group": "Ra226+",
           "tier": "impounded", "route": "", "residue_type": "metal_tailings", "region": "XWL",
           "ore_type": "porphyry_stratiform", "year_from": "1990", "year_to": "2020",
           "allocation_variant": "default", "allocation_rule": "alloc:value", "value_low": "1.0e3",
           "value_central": "2.0e3", "value_high": "4.0e3", "unit": "Bq/t", "below_detection": "false",
           "basis": "compiled", "source_ids": "S0003", "notes": ""}
    row.update(over)
    return row


def triple(first_id, **over):
    """default / bound_main / bound_radio rows for one key (consecutive factor ids)."""
    n = int(first_id.split(":")[1])
    out = []
    for k, (variant, token, scale) in enumerate([("default", "alloc:value", 1.0),
                                                 ("bound_main", "alloc:main", 2.0),
                                                 ("bound_radio", "alloc:radio", 0.1)]):
        out.append(cf_row(f"commodity:{n + k:04d}", allocation_variant=variant, allocation_rule=token,
                          value_low=f"{1e3 * scale:.6g}", value_central=f"{2e3 * scale:.6g}",
                          value_high=f"{4e3 * scale:.6g}", **over))
    return out


BASE_ROWS = (
    triple("commodity:0001", ore_type="porphyry_stratiform")
    + triple("commodity:0004", ore_type="iocg_olympic_dam", region="AUS", year_from="1988", year_to="2025")
    + [cf_row("commodity:0007", commodity="ree_oxide", group="Th228+", tier="liberated", route="air_dust",
              residue_type="", ore_type="ree_bayan_obo", region="CHN", year_from="2000", year_to="2020",
              allocation_rule="none", value_low="1e6", value_central="2e6", value_high="5e6"),
       cf_row("commodity:0008", commodity="zinc", ore_type="", allocation_rule="none")]
)


def fi_row(**over):
    row = {"commodity": "steel", "fuel": "coal", "stream_ref": "coal", "region": "XWL", "year_from": "1950",
           "year_to": "2025", "value_low": "0.6", "value_central": "0.8", "value_high": "1",
           "unit": "t/t", "basis": "compiled", "source_ids": "S0003", "notes": ""}
    row.update(over)
    return row


@pytest.fixture
def v26_root(tmp_root: Path) -> Path:
    """tmp_root with the v2.6 vocabulary, a valid v2.6 commodity_factors.csv and no fuel-input table."""
    vp = tmp_root / "data" / "reference" / "vocab.json"
    vocab = json.loads(vp.read_text(encoding="utf-8"))
    for c in ("cast_iron", "tio2_pigment"):
        if c not in vocab["commodities"]:
            vocab["commodities"].append(c)
        prod = vocab.get("products", {}).get("commodity")
        if isinstance(prod, list) and c not in prod:
            prod.append(c)
    vocab["commodity_components"] = ["own_residue"]
    if isinstance(vocab.get("products", {}).get("commodity"), list):
        vocab["products"]["commodity"] = list(vocab["commodities"])
    vocab["ore_types"] = copy.deepcopy(ORE_TYPES)
    vocab["fuel_input_fuels"] = dict(FUEL_INPUT_FUELS)
    vp.write_text(json.dumps(vocab, indent=2, ensure_ascii=False), encoding="utf-8")
    write_csv(tmp_root / CF, CF_HEADER, copy.deepcopy(BASE_ROWS))
    return tmp_root


def edit(root, rel, mutate, header=None):
    h, rows = read_csv(root / rel)
    mutate(rows)
    write_csv(root / rel, header or h, rows)
    return rows


def install_fuel(root, rows=None):
    write_csv(root / FI, FI_HEADER, rows if rows is not None else [fi_row()])


# --------------------------------------------------------------------------- baseline
def test_baseline_v26_fixture_is_clean(v26_root):
    issues = validate(v26_root, [])
    assert issues == [], "valid v2.6 commodity_factors.csv must be clean:\n" + desc(issues)


def test_same_key_with_different_ore_type_is_not_a_duplicate(v26_root):
    """ore_type is part of the key (4.7): two ore types sharing every other key cell are legal."""
    extra = triple("commodity:0010", ore_type="iocg_high_u", region="AUS", year_from="1988", year_to="2025")
    edit(v26_root, CF, lambda rows: rows.extend(extra))
    issues = validate(v26_root, [])
    assert issues == [], "ore_type must distinguish keys:\n" + desc(issues)


# --------------------------------------------------------------------------- F01
@pytest.mark.parametrize("label,transform", [
    ("v2.5 header (no factor_id, no ore_type)", lambda h: [c for c in h if c not in ("factor_id", "ore_type")]),
    ("factor_id missing", lambda h: [c for c in h if c != "factor_id"]),
    ("ore_type missing", lambda h: [c for c in h if c != "ore_type"]),
    ("factor_id not first", lambda h: [c for c in h if c != "factor_id"][:1] + ["factor_id"] + [c for c in h if c != "factor_id"][1:]),
    ("ore_type at the end", lambda h: [c for c in h if c != "ore_type"] + ["ore_type"]),
    ("ore_type before region", lambda h: [c for c in h if c != "ore_type"][:7] + ["ore_type", "region"] + [c for c in h if c not in ("ore_type", "region")][7:]),
])
def test_f01_header_must_be_the_v26_header_in_order(v26_root, label, transform):
    assert not any(i.rule == "F01" for i in validate(v26_root, [])), "the exact v2.6 header must not raise F01"
    rows = read_csv(v26_root / CF)[1]
    write_csv(v26_root / CF, transform(CF_HEADER), rows)
    issues = validate(v26_root, [])
    assert any(i.rule == "F01" and i.file == CF for i in issues), f"{label}: expected F01 on {CF}:\n" + desc(issues)


# --------------------------------------------------------------------------- T01
@pytest.mark.parametrize("bad", ["", "commodity:1", "commodity:00012", "coal:0001", "commodity-0001",
                                 "Commodity:0001", "commodity:00a1", "0001", "commodity:0001 ", "xcommodity:0001"])
def test_t01_malformed_factor_id(v26_root, bad):  # pattern is exactly ^commodity:[0-9]{4}$
    edit(v26_root, CF, lambda rows: rows[7].update(factor_id=bad))  # zinc row, row number 8
    issues = validate(v26_root, [])
    assert has(issues, "T01", 8, CF), f"factor_id {bad!r} should be T01 at row 8:\n" + desc(issues)


@pytest.mark.parametrize("bad", ["embedded_fuel", "fuel", "OWN_RESIDUE", ""])
def test_t01_component_only_own_residue(v26_root, bad):
    edit(v26_root, CF, lambda rows: rows[7].update(component=bad))
    issues = validate(v26_root, [])
    assert has(issues, "T01", 8, CF), f"component {bad!r} should be T01:\n" + desc(issues)


def test_t01_ore_type_on_commodity_without_entry(v26_root):
    edit(v26_root, CF, lambda rows: rows[7].update(ore_type="all"))  # zinc has no ore_types entry
    issues = validate(v26_root, [])
    assert has(issues, "T01", 8, CF), "ore_type on zinc must be T01:\n" + desc(issues)


@pytest.mark.parametrize("row_index", [1, 7])  # copper porphyry row; ree row
def test_t01_empty_ore_type_on_commodity_with_entry(v26_root, row_index):
    edit(v26_root, CF, lambda rows: rows[row_index - 1].update(ore_type=""))
    issues = validate(v26_root, [])
    assert has(issues, "T01", row_index, CF), "empty ore_type on copper/ree_oxide must be T01:\n" + desc(issues)


@pytest.mark.parametrize("region", ["AUS;CHN", "CHN;MMR", "XWL;AUS"])
def test_t01_region_with_semicolon(v26_root, region):
    edit(v26_root, CF, lambda rows: rows[7].update(region=region))
    issues = validate(v26_root, [])
    assert has(issues, "T01", 8, CF), f"region {region!r} must be T01:\n" + desc(issues)


# --------------------------------------------------------------------------- T02
def test_t02_duplicate_key_including_ore_type(v26_root):
    def dup(rows):
        new = dict(rows[7]); new["factor_id"] = "commodity:0099"; new["value_central"] = "1.5e3"
        rows.append(new)
    edit(v26_root, CF, dup)
    issues = validate(v26_root, [])
    assert has(issues, "T02", 9, CF), "duplicate key must be T02 on the later row:\n" + desc(issues)


def test_t02_duplicate_factor_id_within_file_is_independent_of_key(v26_root):
    edit(v26_root, CF, lambda rows: rows[7].update(factor_id="commodity:0001"))
    issues = validate(v26_root, [])
    assert has(issues, "T02", 8, CF), "factor_id duplicate must be T02 on the later row:\n" + desc(issues)


def test_t02_factor_id_clash_with_another_factor_file(v26_root):
    p = v26_root / "data" / "factors" / "coal.csv"
    h, rows = read_csv(p)
    rows[0]["factor_id"] = "commodity:0008"
    write_csv(p, h, rows)
    issues = validate(v26_root, [])
    assert has(issues, "T02", 8, CF), "factor_id shared with data/factors/*.csv must flag the commodity_factors row:\n" + desc(issues)


# --------------------------------------------------------------------------- T03
@pytest.mark.parametrize("changes", [
    {"value_low": "9e3"},                      # low > central
    {"value_high": "1e2"},                     # high < central
    {"year_from": "2021", "year_to": "2020"},  # window reversed
])
def test_t03_bounds_and_window(v26_root, changes):
    edit(v26_root, CF, lambda rows: rows[7].update(changes))
    issues = validate(v26_root, [])
    assert has(issues, "T03", 8, CF), f"{changes} must be T03 at row 8:\n" + desc(issues)


# --------------------------------------------------------------------------- T04
@pytest.mark.parametrize("row_index,ore", [
    (1, "ree_bayan_obo"),      # ree type on copper
    (7, "iocg_olympic_dam"),   # copper type on ree_oxide
    (1, "iocg_olympic_damX"),  # not in any list
    (1, "ALL"),                # case matters
])
def test_t04_ore_type_not_in_vocab_for_commodity(v26_root, row_index, ore):
    edit(v26_root, CF, lambda rows: rows[row_index - 1].update(ore_type=ore))
    issues = validate(v26_root, [])
    assert has(issues, "T04", row_index, CF), f"ore_type {ore!r} must be T04 at row {row_index}:\n" + desc(issues)


@pytest.mark.parametrize("changes", [
    {"commodity": "unobtainium", "ore_type": ""},
    {"group": "Zz999+"},
    {"residue_type": "no_such_residue"},
    {"region": "ZZZ"},
    {"source_ids": "S9998"},
])
def test_t04_existing_references_still_checked(v26_root, changes):
    edit(v26_root, CF, lambda rows: rows[7].update(changes))
    issues = validate(v26_root, [])
    assert has(issues, "T04", 8, CF), f"{changes} must be T04 at row 8:\n" + desc(issues)


def test_t04_new_commodities_resolve(v26_root):
    rows = [cf_row("commodity:0020", commodity="cast_iron", ore_type="", allocation_rule="none"),
            cf_row("commodity:0021", commodity="tio2_pigment", ore_type="", allocation_rule="none")]
    edit(v26_root, CF, lambda r: r.extend(rows))
    issues = validate(v26_root, [])
    assert issues == [], "cast_iron and tio2_pigment are v2.6 commodities:\n" + desc(issues)


# --------------------------------------------------------------------------- T05
def test_t05_allocation_completeness_is_per_ore_type(v26_root):
    """Dropping bound_radio for the OD key (rows 4-6): one T05, on the key's first row (4), none for porphyry."""
    edit(v26_root, CF, lambda rows: rows.pop(5))
    t05 = [i for i in validate(v26_root, []) if i.rule == "T05"]
    assert [(i.file, i.row) for i in t05] == [(CF, 4)], "T05 once per key, on its first row:\n" + desc(t05)


def test_t05_default_only_key_is_complete(v26_root):
    assert validate(v26_root, []) == [], "baseline (incl. default-only zinc and ree keys) must be clean"


def test_t05_bound_without_default_for_ore_type(v26_root):
    edit(v26_root, CF, lambda rows: rows.pop(3))  # OD default removed; bound_main is now the key's first row (4)
    t05 = [i for i in validate(v26_root, []) if i.rule == "T05"]
    assert [(i.file, i.row) for i in t05] == [(CF, 4)], desc(t05)


# --------------------------------------------------------------------------- V13
def _master_with_factor_ids(root, factor_ids):
    h, rows = read_csv(FIXTURES / "valid_rows.csv")
    idx = next(i for i, r in enumerate(rows) if r["factor_ids"] == "coal:0001")
    rows[idx]["factor_ids"] = factor_ids
    rel = "data/streams/valid.csv"
    write_csv(root / rel, h, rows)
    return rel, idx + 1


def test_v13_resolves_commodity_factor_ids(v26_root):
    rel, _ = _master_with_factor_ids(v26_root, "commodity:0001")
    issues = validate(v26_root, [rel])
    assert "V13" not in rules(issues), "commodity ids join the V13 registry:\n" + desc(issues)


def test_v13_commodity_id_mixed_with_other_stream_ids(v26_root):
    rel, _ = _master_with_factor_ids(v26_root, "coal:0001;commodity:0004")
    assert "V13" not in rules(validate(v26_root, [rel]))


def test_v13_unknown_commodity_id(v26_root):
    ok, _ = _master_with_factor_ids(v26_root, "commodity:0001")
    assert "V13" not in rules(validate(v26_root, [ok])), "a registered commodity id must resolve"
    rel, n = _master_with_factor_ids(v26_root, "commodity:9999")
    issues = validate(v26_root, [rel])
    assert has(issues, "V13", n, rel), "unknown commodity id must be V13:\n" + desc(issues)


def test_v13_commodity_id_unresolvable_without_the_table(v26_root):
    rel, n = _master_with_factor_ids(v26_root, "commodity:0001")
    assert "V13" not in rules(validate(v26_root, [rel])), "resolves while the table is present"
    (v26_root / CF).unlink()
    issues = validate(v26_root, [rel])
    assert has(issues, "V13", n, rel), desc(issues)


# --------------------------------------------------------------------------- commodity_fuel_inputs (4.13)
ALU = dict(commodity="aluminium", fuel="electricity", stream_ref="", unit="MWh/t",
           value_low="14", value_central="14.5", value_high="15")


def test_fuel_inputs_file_is_optional(v26_root):
    assert not (v26_root / FI).exists()
    assert validate(v26_root, []) == []


def test_fuel_inputs_valid_file_is_clean(v26_root):
    install_fuel(v26_root, [fi_row(), fi_row(**ALU),
                            fi_row(fuel="coke", stream_ref="coal"),
                            fi_row(fuel="natural_gas", stream_ref="oil_gas", commodity="cement"),
                            fi_row(fuel="fuel_oil", stream_ref="oil_gas", commodity="cement", year_from="1990")])
    issues = validate(v26_root, [])
    assert issues == [], "valid commodity_fuel_inputs.csv must be clean (no T05, no master cross-check):\n" + desc(issues)


@pytest.mark.parametrize("header", [
    [c for c in FI_HEADER if c != "stream_ref"],
    FI_HEADER[1:] + FI_HEADER[:1],
    FI_HEADER + ["below_detection"],
])
def test_fuel_inputs_header_checked_f01(v26_root, header):
    install_fuel(v26_root)
    assert not any(i.rule == "F01" for i in validate(v26_root, [])), "exact header must not raise F01"
    write_csv(v26_root / FI, header, [fi_row()])
    assert any(i.rule == "F01" and i.file == FI for i in validate(v26_root, [])), "wrong header must be F01"


def test_fuel_inputs_bounds_t03(v26_root):
    install_fuel(v26_root, [fi_row(value_low="2", value_central="1", value_high="3")])
    assert has(validate(v26_root, []), "T03", 1, FI)


def test_fuel_inputs_window_t03(v26_root):
    install_fuel(v26_root, [fi_row(year_from="2025", year_to="1950")])
    assert has(validate(v26_root, []), "T03", 1, FI)


@pytest.mark.parametrize("changes", [
    {"fuel": "peat", "stream_ref": "coal"},   # not a key of fuel_input_fuels
    {"commodity": "unobtainium"},
    {"region": "ZZZ"},
    {"source_ids": "S9998"},
])
def test_fuel_inputs_references_t04(v26_root, changes):
    install_fuel(v26_root, [fi_row(**changes)])
    issues = validate(v26_root, [])
    assert has(issues, "T04", 1, FI), f"{changes} must be T04:\n" + desc(issues)


@pytest.mark.parametrize("changes", [
    {"value_central": "abc", "value_low": "x", "value_high": "y"},   # coercion failure
    {"value_low": "-1", "value_central": "0.8"},                      # negative
    {"unit": "MWh/t"},                                                # coal with MWh/t
    {"unit": "kg/t"},                                                 # outside the allowed set
    {"fuel": "electricity", "stream_ref": "", "unit": "t/t"},         # electricity with t/t
    {"fuel": "electricity", "stream_ref": "coal", "unit": "MWh/t"},   # electricity with non-empty stream_ref
    {"stream_ref": ""},                                               # coal with empty stream_ref
    {"stream_ref": "oil_gas"},                                        # coal with the wrong stream_ref
    {"fuel": "natural_gas", "stream_ref": "coal"},                    # gas with the wrong stream_ref
    {"source_ids": ""},                                               # empty source_ids
    {"region": "AUS;CHN"},                                            # region list
    {"basis": "guess"},
    {"year_from": "1700"},                                            # outside 1800-2100 (window stays ordered)
    {"year_to": "2101"},
])
def test_fuel_inputs_t01(v26_root, changes):
    install_fuel(v26_root, [fi_row(**changes)])
    issues = validate(v26_root, [])
    assert has(issues, "T01", 1, FI), f"{changes} must be T01 at row 1:\n" + desc(issues)


def test_fuel_inputs_duplicate_key_flags_later_row_t02(v26_root):
    install_fuel(v26_root, [fi_row(), fi_row(**ALU), fi_row(value_central="0.9")])
    issues = [i for i in validate(v26_root, []) if i.rule == "T02"]
    assert [(i.file, i.row) for i in issues] == [(FI, 3)], desc(issues)


def test_fuel_inputs_same_key_different_year_from_is_not_duplicate(v26_root):
    install_fuel(v26_root, [fi_row(year_to="1989"), fi_row(year_from="1990")])
    assert validate(v26_root, []) == []


# --------------------------------------------------------------------------- vocab (fixture of the staged shape)
def test_vocab_components_and_products_in_staged_vocab():
    p = REAL_ROOT / "build" / "d74_staging" / "data" / "reference" / "vocab.json"
    if not p.exists():
        pytest.skip("staging directory no longer present")
    v = json.loads(p.read_text(encoding="utf-8"))
    assert v["commodity_components"] == ["own_residue"], v["commodity_components"]
    assert v["products"]["commodity"] == v["commodities"]


# --------------------------------------------------------------------------- applied data (D74)
def _applied_ready():
    p = REAL_ROOT / CF
    if not p.exists():
        return False, f"{CF} does not exist yet (build/d74_staging/ not applied)"
    with open(p, newline="", encoding="utf-8") as fh:
        head = next(csv.reader(fh), [])
    if "factor_id" not in head:
        return False, f"{CF} lacks the factor_id column (v2.6 data not applied)"
    return True, ""


_READY, _WHY = _applied_ready()
applied = pytest.mark.skipif(not _READY, reason="D74 data not applied: " + _WHY)


def broken(msg):
    pytest.fail("PREMISE BROKEN: " + msg)


@applied
class TestAppliedData:
    @pytest.fixture(scope="class")
    def vocab(self):
        return json.loads((REAL_ROOT / "data/reference/vocab.json").read_text(encoding="utf-8"))

    @pytest.fixture(scope="class")
    def cf(self):
        return read_csv(REAL_ROOT / CF)

    def test_whole_tree_validates_clean(self):
        issues = validate(REAL_ROOT)
        assert issues == [], "PREMISE BROKEN: applied D74 data must validate with no issues (APPLY.md step 3):\n" + desc(issues[:40])

    def test_header_exact(self, cf):
        if cf[0] != CF_HEADER:
            broken(f"commodity_factors.csv header is {cf[0]}, expected {CF_HEADER}")

    def test_factor_ids_well_formed_and_unique(self, cf):
        ids = [r["factor_id"] for r in cf[1]]
        bad = [i for i in ids if not re.fullmatch(r"commodity:\d{4}", i)]
        if bad:
            broken(f"malformed factor_id values {bad[:5]}")
        if len(set(ids)) != len(ids):
            broken("duplicate factor_id in commodity_factors.csv")

    def test_factor_ids_do_not_collide_with_other_factor_files(self, cf):
        mine = {r["factor_id"] for r in cf[1]}
        for p in (REAL_ROOT / "data" / "factors").glob("*.csv*"):
            if p.suffix == ".gz":
                continue
            theirs = {r["factor_id"] for r in read_csv(p)[1]}
            if mine & theirs:
                broken(f"factor ids {sorted(mine & theirs)[:3]} also appear in {p.name}")

    def test_component_is_own_residue_only(self, cf):
        bad = {r["component"] for r in cf[1]} - {"own_residue"}
        if bad:
            broken(f"components other than own_residue: {bad}")

    def test_no_region_lists(self, cf):
        bad = [r["factor_id"] for r in cf[1] if ";" in r["region"]]
        if bad:
            broken(f"region cells with ';' in {bad[:5]}")

    def test_ore_type_required_exactly_for_commodities_with_an_entry(self, cf, vocab):
        ot = vocab.get("ore_types")
        if not isinstance(ot, dict) or not ot:
            broken("vocab.json has no ore_types map")
        for r in cf[1]:
            allowed = ot.get(r["commodity"])
            if allowed is None and r["ore_type"] != "":
                broken(f"{r['factor_id']}: {r['commodity']} has no ore_types entry but ore_type={r['ore_type']!r}")
            if allowed is not None and r["ore_type"] not in allowed:
                broken(f"{r['factor_id']}: ore_type {r['ore_type']!r} not in {allowed}")

    def test_vocab_ore_types_and_commodities(self, vocab):
        if vocab.get("ore_types") != ORE_TYPES:
            broken(f"ore_types is {vocab.get('ore_types')}, SCHEMA 4.7 lists {ORE_TYPES}")
        for c in ("cast_iron", "tio2_pigment"):
            if c not in vocab["commodities"]:
                broken(f"{c} missing from vocab commodities")

    def test_vocab_components_and_products(self, vocab):
        if vocab.get("commodity_components") != ["own_residue"]:
            broken(f"commodity_components is {vocab.get('commodity_components')}, expected ['own_residue']")
        if vocab["products"]["commodity"] != vocab["commodities"]:
            broken("products.commodity must equal commodities")

    def test_vocab_fuel_input_fuels(self, vocab):
        fif = vocab.get("fuel_input_fuels")
        if not isinstance(fif, dict) or not fif:
            broken("vocab.json has no fuel_input_fuels map")
        for fuel, ref in fif.items():
            if ref != "" and ref not in vocab["streams"]:
                broken(f"fuel {fuel} has stream_ref {ref!r}, not a stream or empty")

    def test_every_listed_ore_type_is_used(self, cf, vocab):
        used = {(r["commodity"], r["ore_type"]) for r in cf[1]}
        for com, types in vocab["ore_types"].items():
            for t in types:
                if (com, t) not in used:
                    broken(f"vocab lists ({com}, {t}) but no commodity_factors row uses it")

    def test_no_embedded_fuel_rows_remain(self, cf):
        if any(r["component"] == "embedded_fuel" for r in cf[1]):
            broken("embedded_fuel rows must have moved to commodity_fuel_inputs.csv (D74(d))")

    def test_olympic_dam_rows(self, cf):
        od = [r for r in cf[1] if r["ore_type"] == "iocg_olympic_dam"]
        if not od:
            broken("no iocg_olympic_dam rows")
        for r in od:
            if (r["region"], r["year_from"], r["year_to"]) != ("AUS", "1988", "2025"):
                broken(f"{r['factor_id']}: OD row is {(r['region'], r['year_from'], r['year_to'])}, expected AUS 1988-2025")

    def test_allocation_triples_complete_per_key(self, cf):
        groups = {}
        for r in cf[1]:
            k = tuple(r[c] for c in ("commodity", "component", "ore_type", "group", "tier", "route",
                                      "residue_type", "region", "year_from"))
            groups.setdefault(k, set()).add(r["allocation_variant"])
        for k, v in groups.items():
            if v not in ({"default"}, {"default", "bound_main", "bound_radio"}):
                broken(f"key {k} has variants {sorted(v)}")

    def test_fuel_inputs_table(self, vocab):
        p = REAL_ROOT / FI
        if not p.exists():
            broken(f"{FI} missing")
        h, rows = read_csv(p)
        if h != FI_HEADER:
            broken(f"fuel-input header {h}")
        for r in rows:
            if r["fuel"] not in vocab["fuel_input_fuels"]:
                broken(f"fuel {r['fuel']} not in fuel_input_fuels")
            if r["stream_ref"] != vocab["fuel_input_fuels"][r["fuel"]]:
                broken(f"{r['commodity']}/{r['fuel']}: stream_ref {r['stream_ref']!r} disagrees with vocab")
            want = "MWh/t" if r["fuel"] == "electricity" else "t/t"
            if r["unit"] != want:
                broken(f"{r['commodity']}/{r['fuel']}: unit {r['unit']!r}, expected {want!r}")
            if not (float(r["value_low"]) <= float(r["value_central"]) <= float(r["value_high"])):
                broken(f"{r['commodity']}/{r['fuel']}: bounds out of order")

    def test_select_on_real_data_ore_type_and_precedence(self):
        from pipeline.lib import LibError
        from pipeline.lib.factors import select
        from pipeline.lib.io import read_table
        rows = read_table(REAL_ROOT / CF)
        od = [r for r in rows if r["ore_type"] == "iocg_olympic_dam"]
        if not od:
            broken("no OD rows to select")
        r0 = od[0]
        keys = {k: r0[k] for k in ("commodity", "component", "group", "tier", "route", "residue_type",
                                   "allocation_variant")}
        # With the key given, the OD row is returned for AUS in a covered year.
        got = select(rows, year=2000, region="AUS", ore_type="iocg_olympic_dam", **keys)
        assert got["ore_type"] == "iocg_olympic_dam" and got["region"] == "AUS"

        def cands(region, year):
            same = [r for r in rows if all(r[k] == r0[k] for k in keys)
                    and int(r["year_from"]) <= year <= int(r["year_to"])]
            exact = [r for r in same if r["region"] == region]
            return exact if exact else [r for r in same if r["region"] == "XWL"]

        # Omitting ore_type: ore_type plays no part in precedence (LIB_SPEC 12.2). The outcome
        # is the winning region level: one row -> that row; several -> ambiguous.
        for region, year in [("AUS", 2000), ("CHN", 2000), ("AUS", 1990), ("AUS", 2020)]:
            win = cands(region, year)
            if len(win) == 1:
                assert select(rows, year=year, region=region, **keys)["factor_id"] == win[0]["factor_id"]
            elif len(win) > 1:
                with pytest.raises(LibError, match="^ambiguous factor rows"):
                    select(rows, year=year, region=region, **keys)
            else:
                with pytest.raises(LibError, match="^no factor row"):
                    select(rows, year=year, region=region, **keys)
        # Exact-region OD row beats the XWL copper rows when ore_type is omitted for AUS.
        # A tie at one level: XWL copper rows for a region with no exact row differ only by ore type.
        xwl = [r for r in rows if all(r[k] == r0[k] for k in keys) and r["region"] == "XWL"
               and int(r["year_from"]) <= 2000 <= int(r["year_to"])]
        if len({r["ore_type"] for r in xwl}) > 1:
            with pytest.raises(LibError, match="^ambiguous factor rows"):
                select(rows, year=2000, region="CHN", **keys)
