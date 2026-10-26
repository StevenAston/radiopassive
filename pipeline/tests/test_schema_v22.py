"""Spec-blind tests for the SCHEMA v2.2 additions (D36, D43-D48).

Written from docs/SCHEMA.md (v2.2 change-log row, sections 2, 3.2, 5.1, 5.3, 5.7, 6.3),
docs/DECISIONS.md (D36, D43-D48) and docs/METHODS.md (5.2, 6.3) only. validate.py
and pipeline/lib/ were not read.

Mapping to the v2.2 change-log row
----------------------------------
* tier `memo_biosphere`        -> TestMemoBiosphere
* route `air_rerelease`        -> TestAirRerelease
* substream / residue type     -> TestBiomassDomestic
* D36 stage-tier additions     -> TestStageTierAdditions
* unchanged opening_stock rule -> TestOpeningStockMemoTiers

Spec gaps (assertions weakened accordingly)
-------------------------------------------
G1. Memo tier at a disallowed stage: V03 is stated (SCHEMA 5.3, 6.3), asserted.
G2. Memo tier with a stock quantity: SCHEMA 3 / 6.3 name "memo flows" as an R02
    conditional, so R02 is asserted.
G3. Memo tier with a route: the spec says route is empty unless tier = liberated
    (R02 "route by tier"), asserted as R02.
G4. air_rerelease at the wrong stage/group/quantity: D48 says "schema conditional"
    (R02); asserted as R02 being present (other codes may accompany it).
G5. Whether `memo_biosphere` is allowed at `biomass_peat` for BOTH substreams is
    stated by D43/D44/D45 and SCHEMA 5.1; whether `dispersed`/`impounded` rows may
    carry any particular residue type is not stated, so `biomass_domestic_ash` is
    used (D45).
G6. Whether memo_biosphere rows may carry a residue_type is unstated; these tests
    leave it empty (the residue_type rule lists impounded/reisolated/dispersed only).
"""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from pipeline.validate import validate
from tests.test_validate import (
    append_copy, assert_clean, assert_has, assert_only, corrupt, describe,
    rules_of, vrow, write_master,
)

STORE_QUANTITIES = ["standing_inventory", "opening_stock"]


def biomass_row(**changes):
    """A memo_biosphere K40 flow at other/biomass_peat, built from valid fixture row 10."""
    base = dict(
        stream="other", substream="biomass_peat", stage="biomass_peat", product="",
        residue_type="", country="FIN", group="K40", tier="memo_biosphere",
        quantity="flow", unit="Bq/a", year="2005", route="", event_id="",
        technology="biomass", source_ids="S0001", allocation_rule="none",
    )
    base.update({k: str(v) for k, v in changes.items()})
    return vrow(10, **base)


def liberated_cs(**changes):
    """A liberated Cs137+ re-release flow at other/biomass_peat."""
    base = dict(tier="liberated", group="Cs137+", route="air_rerelease")
    base.update(changes)
    return biomass_row(**base)


def run(tmp_root, rows):
    rel = write_master(tmp_root, "v22.csv", rows)
    return validate(tmp_root, [rel])


def assert_rejected_with(issues, rule, row=1, file="data/streams/v22.csv"):
    assert issues, "expected the row to be rejected, got no issues"
    assert_has(issues, rule, row, file)


# --------------------------------------------------------------------------- memo_biosphere

class TestMemoBiosphere:
    @pytest.mark.parametrize("substream", ["biomass_peat", "biomass_domestic"])
    def test_flow_at_biomass_peat_is_accepted(self, tmp_root, substream):
        assert_clean(run(tmp_root, [biomass_row(substream=substream)]))

    @pytest.mark.parametrize("group", ["K40", "Pb210+", "Po210", "Cs137+"])
    def test_accepted_for_the_natural_and_fallout_groups_of_d43_d44(self, tmp_root, group):
        assert_clean(run(tmp_root, [biomass_row(group=group)]))

    @pytest.mark.parametrize("stream,substream,stage", [
        ("other", "geothermal", "geothermal"),
        ("other", "hydro", "hydro"),
        ("other", "biomass_peat", "construction"),
        ("coal", "power", "combustion_power"),
        ("coal", "non_power", "combustion_nonpower"),
        ("nuclear", "fuel_cycle", "u_milling"),
        ("oil_gas", "conventional", "production"),
    ])
    def test_rejected_at_any_other_stage_v03(self, tmp_root, stream, substream, stage):
        row = biomass_row(stream=stream, substream=substream, stage=stage, product="")
        if stream == "oil_gas":
            row["product"] = "oil"
        if stage == "construction":
            row["product"] = "steel"
        issues = run(tmp_root, [row])
        assert_rejected_with(issues, "V03")

    @pytest.mark.parametrize("quantity,extra", [
        ("standing_inventory", dict(unit="Bq")),
        ("opening_stock", dict(unit="Bq", year="1950")),
    ])
    def test_rejected_with_stock_quantity_r02(self, tmp_root, quantity, extra):
        issues = run(tmp_root, [biomass_row(quantity=quantity, **extra)])
        assert_rejected_with(issues, "R02")

    @pytest.mark.parametrize("quantity", ["transfer_out", "transfer_in"])
    def test_rejected_as_a_transfer_row(self, tmp_root, quantity):
        # Spec: memo tiers are `flow` only (SCHEMA 3, tier column). Rule code for
        # transfers is not stated beyond R02 "memo flows"; assert rejection only.
        issues = run(tmp_root, [biomass_row(quantity=quantity, unit="Bq", event_id="E001")])
        assert issues, "memo_biosphere transfer row was accepted"

    @pytest.mark.parametrize("route", ["air_stack", "air_rerelease", "air_dust"])
    def test_must_carry_no_route_r02(self, tmp_root, route):
        issues = run(tmp_root, [biomass_row(route=route)])
        assert_rejected_with(issues, "R02")

    def test_wrong_unit_for_flow_still_r02(self, tmp_root):
        assert_rejected_with(run(tmp_root, [biomass_row(unit="Bq")]), "R02")


# --------------------------------------------------------------------------- air_rerelease

class TestAirRerelease:
    @pytest.mark.parametrize("substream", ["biomass_peat", "biomass_domestic"])
    def test_liberated_cs137_flow_at_biomass_peat_is_accepted(self, tmp_root, substream):
        assert_clean(run(tmp_root, [liberated_cs(substream=substream)]))

    @pytest.mark.parametrize("stream,substream,stage,product", [
        ("other", "geothermal", "geothermal", ""),
        ("other", "hydro", "hydro", ""),
        ("coal", "power", "combustion_power", ""),
        ("nuclear", "pwr", "reactor_operation", ""),
    ])
    def test_rejected_at_another_stage_r02(self, tmp_root, stream, substream, stage, product):
        row = liberated_cs(stream=stream, substream=substream, stage=stage, product=product,
                           technology="")
        assert_rejected_with(run(tmp_root, [row]), "R02")

    @pytest.mark.parametrize("group", ["K40", "Pb210+", "Po210", "Ra226+", "Sr90+"])
    def test_rejected_with_another_group_r02(self, tmp_root, group):
        assert_rejected_with(run(tmp_root, [liberated_cs(group=group)]), "R02")

    @pytest.mark.parametrize("quantity,extra", [
        ("transfer_in", dict(unit="Bq", event_id="E001")),
        ("transfer_out", dict(unit="Bq", event_id="E001")),
        ("standing_inventory", dict(unit="Bq")),
        ("opening_stock", dict(unit="Bq", year="1950")),
    ])
    def test_rejected_on_a_non_flow_row_r02(self, tmp_root, quantity, extra):
        assert_rejected_with(run(tmp_root, [liberated_cs(quantity=quantity, **extra)]), "R02")

    @pytest.mark.parametrize("tier", ["impounded", "dispersed"])
    def test_rejected_on_a_non_liberated_tier_r02(self, tmp_root, tier):
        row = liberated_cs(tier=tier, residue_type="biomass_domestic_ash")
        assert_rejected_with(run(tmp_root, [row]), "R02")

    def test_is_not_an_accident_route_so_allowed_without_an_event(self, tmp_root):
        # V14 applies to accident routes only; air_rerelease is a routine flow route.
        issues = run(tmp_root, [liberated_cs()])
        assert "V14" not in rules_of(issues), describe(issues)
        assert_clean(issues)

    def test_liberated_flow_without_route_is_still_rejected(self, tmp_root):
        assert_rejected_with(run(tmp_root, [liberated_cs(route="")]), "R02")


# --------------------------------------------------------------------------- biomass_domestic

class TestBiomassDomestic:
    def test_substream_accepted_for_stream_other(self, tmp_root):
        row = biomass_row(substream="biomass_domestic", tier="liberated", group="Cs137+",
                          route="air_rerelease")
        assert_clean(run(tmp_root, [row]))

    @pytest.mark.parametrize("stage", ["coal_mining", "combustion_power", "combustion_nonpower"])
    def test_substream_rejected_for_stream_coal_v01(self, tmp_root, stage):
        row = vrow(1, stream="coal", substream="biomass_domestic", stage=stage, tier="liberated",
                   residue_type="", route="air_stack", group="Ra226+", country="USA",
                   allocation_rule="none", product="", technology="")
        assert_rejected_with(run(tmp_root, [row]), "V01")

    @pytest.mark.parametrize("stream,substream,stage,extra", [
        ("nuclear", "biomass_domestic", "u_milling", dict(allocation_rule="civil:doc")),
        ("wind_solar", "biomass_domestic", "commodity_supply", dict(product="silicon_mg")),
        ("oil_gas", "biomass_domestic", "production", dict(product="oil")),
    ])
    def test_substream_rejected_for_other_streams_v01(self, tmp_root, stream, substream, stage, extra):
        row = vrow(1, stream=stream, substream=substream, stage=stage, tier="impounded",
                   residue_type="u_tailings", group="Ra226+", **extra)
        assert_rejected_with(run(tmp_root, [row]), "V01")

    def test_residue_type_exists_in_the_reference_table(self, tmp_root):
        path = tmp_root / "data" / "reference" / "residue_types.csv"
        with open(path, newline="", encoding="utf-8") as fh:
            codes = {r["residue_type"] for r in csv.DictReader(fh)}
        assert "biomass_domestic_ash" in codes

    @pytest.mark.parametrize("tier", ["impounded", "dispersed"])
    def test_residue_type_is_usable_on_a_domestic_ash_row(self, tmp_root, tier):
        row = biomass_row(substream="biomass_domestic", tier=tier,
                          residue_type="biomass_domestic_ash", group="Cs137+")
        assert_clean(run(tmp_root, [row]))

    def test_unknown_residue_type_still_rejected_v12(self, tmp_root):
        row = biomass_row(substream="biomass_domestic", tier="dispersed",
                          residue_type="biomass_domestic_ashes")
        assert_rejected_with(run(tmp_root, [row]), "V12")


# --------------------------------------------------------------------------- D36

class TestStageTierAdditions:
    def test_dispersed_now_allowed_at_coal_mining(self, tmp_root):
        row = vrow(7, stream="coal", substream="all", stage="coal_mining", tier="dispersed",
                   residue_type="coal_fly_ash", quantity="flow", unit="Bq/a", route="",
                   basis="compiled", factor_ids="", source_ids="S0001", group="Ra226+",
                   country="USA", allocation_rule="none", product="")
        assert_clean(run(tmp_root, [row]))

    def test_dispersed_at_coal_mining_still_needs_a_residue_type(self, tmp_root):
        row = vrow(7, stream="coal", substream="all", stage="coal_mining", tier="dispersed",
                   residue_type="", quantity="flow", unit="Bq/a", route="", basis="compiled",
                   factor_ids="", source_ids="S0001")
        assert_rejected_with(run(tmp_root, [row]), "R02")

    def test_dispersed_still_rejected_where_not_allowed(self, tmp_root):
        # oil_sands_mining allows impounded, liberated, memo_earth_moved only.
        row = vrow(7, stream="oil_gas", substream="oil_sands", stage="oil_sands_mining",
                   tier="dispersed", residue_type="coal_fly_ash", quantity="flow", unit="Bq/a",
                   product="bitumen", basis="compiled", factor_ids="", source_ids="S0001")
        assert_rejected_with(run(tmp_root, [row]), "V03")

    def _add_fuel_cycle_event(self, tmp_root):
        append_copy(tmp_root, "data/events.csv", 1, event_id="E003", name="Fuel-cycle criticality",
                    stream="nuclear", stage="accident", event_type="accident", is_accident="true",
                    from_tier="sealed_fuel_cycle", to_tiers="liberated",
                    inclusion="activity", military="false")

    def test_event_from_sealed_fuel_cycle_at_accident_is_accepted(self, tmp_root):
        self._add_fuel_cycle_event(tmp_root)
        issues = validate(tmp_root, [])
        assert_clean([i for i in issues if i.file == "data/events.csv"])

    def test_master_transfer_pair_from_sealed_fuel_cycle_at_accident_is_accepted(self, tmp_root):
        self._add_fuel_cycle_event(tmp_root)
        common = dict(event_id="E003", stage="accident", substream="fuel_cycle", country="JPN",
                      year="1999")
        out = vrow(3, tier="sealed_fuel_cycle", **common)
        inn = vrow(4, tier="liberated", **common)
        issues = run(tmp_root, [out, inn])
        assert_clean(issues)

    def test_sealed_fuel_cycle_at_accident_is_not_a_v03_for_a_flow_row(self, tmp_root):
        row = vrow(2, stage="accident", substream="fuel_cycle", tier="sealed_fuel_cycle",
                   quantity="flow", unit="Bq/a", country="JPN", year="1999")
        issues = run(tmp_root, [row])
        assert "V03" not in rules_of(issues), describe(issues)

    def test_transfer_out_tier_must_still_match_the_event(self, tmp_root):
        # E001 (fixture) has from_tier sealed_in_core; a sealed_fuel_cycle transfer_out is X05.
        common = dict(event_id="E001")
        out = vrow(3, tier="sealed_fuel_cycle", **common)
        inn = vrow(4, **common)
        assert "X05" in rules_of(run(tmp_root, [out, inn]))


# --------------------------------------------------------------------------- opening_stock

class TestOpeningStockMemoTiers:
    @pytest.mark.parametrize("tier", ["memo_biosphere", "memo_earth_moved"])
    def test_opening_stock_may_not_use_either_memo_tier(self, tmp_root, tier):
        row = biomass_row(tier=tier, quantity="opening_stock", unit="Bq", year="1950")
        assert_rejected_with(run(tmp_root, [row]), "R02")

    def test_opening_stock_memo_earth_moved_at_a_mining_stage(self, tmp_root):
        row = vrow(7, quantity="opening_stock", unit="Bq", year="1950", basis="compiled",
                   factor_ids="", source_ids="S0001")
        assert_rejected_with(run(tmp_root, [row]), "R02")

    def test_opening_stock_still_accepted_for_an_ordinary_stock_tier(self, tmp_root):
        row = biomass_row(tier="impounded", residue_type="biomass_domestic_ash",
                          substream="biomass_domestic", quantity="opening_stock", unit="Bq",
                          year="1950", group="Pb210+", basis="compiled")
        assert_clean(run(tmp_root, [row]))
