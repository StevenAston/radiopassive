"""Spec-blind tests for pipeline.lib.factors (LIB_SPEC section 3)."""
from __future__ import annotations

import math

import pytest

from pipeline.lib import LibError
from pipeline.lib.bounds import Bounds
from pipeline.lib.factors import apply, result_unit, select


def frow(factor_id="coal:0001", **over):
    row = {
        "factor_id": factor_id,
        "description": "test factor",
        "stream": "coal",
        "stage": "coal_mining",
        "driver_series": "coal_production",
        "group": "Ra226+",
        "tier": "reisolated",
        "route": None,
        "residue_type": None,
        "region": "CHN",
        "year_from": 1990,
        "year_to": 2020,
        "value_low": 5.0,
        "value_central": 10.0,
        "value_high": 20.0,
        "unit": "Bq/t",
        "below_detection": False,
        "basis": "compiled",
        "source_ids": ["S0003"],
        "notes": None,
    }
    row.update(over)
    return row


# ------------------------------------------------------------------ select

def test_select_single_match_returns_row():
    r = frow()
    assert select([r], year=2000, region="CHN") == r


def test_select_year_window_inclusive():
    r = frow()
    assert select([r], year=1990, region="CHN") == r
    assert select([r], year=2020, region="CHN") == r


@pytest.mark.parametrize("year", [1989, 2021])
def test_select_year_outside_window_raises(year):
    with pytest.raises(LibError):
        select([frow()], year=year, region="CHN")


def test_select_no_rows_raises():
    with pytest.raises(LibError):
        select([], year=2000, region="CHN")


def test_select_wrong_region_raises():
    with pytest.raises(LibError):
        select([frow(region="USA")], year=2000, region="CHN")


def test_select_xwl_fallback():
    r = frow(region="XWL")
    assert select([r], year=2000, region="CHN") == r


def test_select_exact_region_beats_xwl():
    exact = frow("coal:0001", region="CHN")
    world = frow("coal:0002", region="XWL")
    assert select([world, exact], year=2000, region="CHN") == exact
    assert select([exact, world], year=2000, region="CHN") == exact


def test_select_xwl_used_when_exact_row_outside_year_window():
    exact = frow("coal:0001", region="CHN", year_from=1950, year_to=1960)
    world = frow("coal:0002", region="XWL")
    assert select([exact, world], year=2000, region="CHN") == world


def test_select_ambiguous_exact_rows_raise():
    a = frow("coal:0001")
    b = frow("coal:0002")
    with pytest.raises(LibError):
        select([a, b], year=2000, region="CHN")


def test_select_ambiguous_xwl_rows_raise():
    a = frow("coal:0001", region="XWL")
    b = frow("coal:0002", region="XWL")
    with pytest.raises(LibError):
        select([a, b], year=2000, region="CHN")


def test_select_ambiguity_among_exact_even_with_xwl_present():
    rows = [frow("coal:0001"), frow("coal:0002"), frow("coal:0003", region="XWL")]
    with pytest.raises(LibError):
        select(rows, year=2000, region="CHN")


def test_select_equality_filters_disambiguate():
    a = frow("coal:0001", stage="coal_mining")
    b = frow("coal:0002", stage="combustion_power")
    assert select([a, b], year=2000, region="CHN", stage="combustion_power") == b


@pytest.mark.parametrize(
    "key,va,vb",
    [
        ("stream", "coal", "oil_gas"),
        ("stage", "s1", "s2"),
        ("group", "Ra226+", "Th232+"),
        ("tier", "impounded", "reisolated"),
        ("route", "stack", "air_ventilation"),
        ("residue_type", "coal_fly_ash", "coal_bottom_ash"),
        ("driver_series", "ds1", "ds2"),
        ("commodity", "copper", "iron"),
        ("component", "own_residue", "embedded_fuel"),
        ("allocation_variant", "default", "bound_main"),
    ],
)
def test_select_each_listed_filter_column(key, va, vb):
    a = frow("coal:0001", **{key: va})
    b = frow("coal:0002", **{key: vb})
    assert select([a, b], year=2000, region="CHN", **{key: vb}) == b
    assert select([a, b], year=2000, region="CHN", **{key: va}) == a


def test_select_filter_matching_nothing_raises():
    with pytest.raises(LibError):
        select([frow(stage="coal_mining")], year=2000, region="CHN", stage="nope")


def test_select_none_row_value_matches_only_none_filter():
    plain = frow("coal:0001", route=None)
    routed = frow("coal:0002", route="stack")
    assert select([plain, routed], year=2000, region="CHN", route=None) == plain
    # a non-None filter never matches a None row
    assert select([plain, routed], year=2000, region="CHN", route="stack") == routed
    with pytest.raises(LibError):
        select([plain], year=2000, region="CHN", route="stack")


def test_select_omitted_filter_does_not_constrain():
    plain = frow("coal:0001", route=None)
    routed = frow("coal:0002", route="stack")
    with pytest.raises(LibError):  # both qualify -> ambiguous
        select([plain, routed], year=2000, region="CHN")


def test_select_accepts_generator():
    r = frow()
    assert select((x for x in [r]), year=2000, region="CHN") == r


def test_select_error_message_is_informative():
    with pytest.raises(LibError) as ei:
        select([], year=2000, region="CHN")
    assert str(ei.value)


# ------------------------------------------------------------------- apply
E_ = math.exp


def _approx(b, low, c, high, rel=1e-9):
    assert b.low == pytest.approx(low, rel=rel, abs=1e-300)
    assert b.central == pytest.approx(c, rel=rel)
    assert b.high == pytest.approx(high, rel=rel)


def test_apply_bq_per_driver_unit_hand_case():
    # driver exact 4 t ; factor (e^-1, 1, e^2)*10 Bq/t via ratios 1 and 2:
    # central 4*10 = 40 ; high 40 e^2 ; low 40 e^-1 (exact driver adds 0).
    fac = frow(unit="Bq/t", value_low=10 * E_(-1), value_central=10.0, value_high=10 * E_(2))
    out = apply(Bounds.exact(4.0), "t", fac)
    _approx(out, 40 * E_(-1), 40.0, 40 * E_(2))


def test_apply_bq_per_a_per_driver_unit():
    fac = frow(unit="Bq/a per t", value_low=10.0, value_central=10.0, value_high=10.0)
    _approx(apply(Bounds.exact(3.0), "t", fac), 30.0, 30.0, 30.0)


def test_apply_dimensionless_factor():
    fac = frow(unit="1", value_low=0.5, value_central=0.5, value_high=0.5)
    _approx(apply(Bounds(1.0, 2.0, 4.0), "t", fac), 0.5, 1.0, 2.0)


def test_apply_equals_product_of_driver_and_factor():
    # driver (2,3,4) x factor (8,10,12): central 30
    # high: sqrt(ln(4/3)^2 + ln(12/10)^2) = sqrt(0.08276+0.03324)=0.34059 -> 30 e^0.34059
    # low : sqrt(ln(3/2)^2 + ln(10/8)^2) = sqrt(0.16440+0.04979)=0.46281 -> 30 e^-0.46281
    d = Bounds(2.0, 3.0, 4.0)
    fac = frow(unit="Bq/t", value_low=8.0, value_central=10.0, value_high=12.0)
    out = apply(d, "t", fac)
    _approx(out, 30 * math.exp(-0.4628120551436434), 30.0, 30 * math.exp(0.34059084673831574))


def test_apply_twh_driver_with_gwa_factor():
    # 1 GWa = 8.766 TWh -> driver 3 TWh = 3/8.766 GWa = 0.342231 GWa
    # central = 0.342231 * 10 Bq/GWa = 3.42231 ; ratios unchanged by the scaling:
    # high ln = 0.34059 -> 4.81101 ; low ln = 0.46281 -> 2.15438
    d = Bounds(2.0, 3.0, 4.0)
    fac = frow(unit="Bq/GWa", value_low=8.0, value_central=10.0, value_high=12.0)
    _approx(apply(d, "TWh", fac), 2.1543837602083182, 3.4223134839151266, 4.8110128150129965)


def test_apply_gwa_driver_with_twh_factor():
    # factor 10 Bq/TWh = 10*8.766 = 87.66 Bq/GWa ; driver 3 GWa -> 262.98
    d = Bounds(2.0, 3.0, 4.0)
    fac = frow(unit="Bq/TWh", value_low=8.0, value_central=10.0, value_high=12.0)
    _approx(apply(d, "GWa", fac), 165.5487856160503, 262.98, 369.6914838569169)


def test_apply_twh_gwa_round_trip_factor_exact():
    # exact driver 8.766 TWh with factor 1 Bq/GWa -> exactly 1 Bq
    fac = frow(unit="Bq/GWa", value_low=1.0, value_central=1.0, value_high=1.0)
    _approx(apply(Bounds.exact(8.766), "TWh", fac), 1.0, 1.0, 1.0, rel=1e-12)


def test_apply_below_detection_uses_rows_own_values():
    # LIB_SPEC 7.6: bounds are the row's own (0, 4, 10) -- NOT rebuilt from
    # value_high as not_detected(10) = (0, 5, 10).  Driver exact 2:
    # central 2*4 = 8 ; high 2*10 = 20 ; low floored -> 0 ; flagged.
    fac = frow(unit="Bq/t", below_detection=True, value_low=0.0, value_central=4.0, value_high=10.0)
    out = apply(Bounds.exact(2.0), "t", fac)
    assert out.nd_floored is True
    assert out.low == 0.0
    assert out.central == pytest.approx(8.0)
    assert out.high == pytest.approx(20.0)


@pytest.mark.parametrize(
    "factor_unit,driver_unit",
    [
        ("Bq/t", "GWa"),
        ("Bq/m3", "t"),
        ("Bq/TWh", "t"),
        ("Bq/GWa", "m3"),
        ("Bq/GWa", "GWh"),   # only TWh<->GWa is convertible
        ("Bq/GWh", "TWh"),
        ("Bq", "t"),
        ("t/GW", "GW"),
        ("Bq/a per t", "m3"),
    ],
)
def test_apply_unit_mismatch_raises(factor_unit, driver_unit):
    fac = frow(unit=factor_unit)
    with pytest.raises(LibError):
        apply(Bounds.exact(1.0), driver_unit, fac)


def test_apply_unit_mismatch_message_mentions_units():
    with pytest.raises(LibError) as ei:
        apply(Bounds.exact(1.0), "m3", frow(unit="Bq/t"))
    msg = str(ei.value)
    assert "Bq/t" in msg or "m3" in msg


# ------------------------------------------------------------- result_unit

@pytest.mark.parametrize(
    "driver,factor,want",
    [
        ("t", "Bq/t", "Bq"),
        ("m3", "Bq/m3", "Bq"),
        ("t", "Bq/a per t", "Bq/a"),
        ("t", "1", "t"),
        ("GWa", "1", "GWa"),
        ("TWh", "Bq/GWa", "Bq"),
        ("GWa", "Bq/TWh", "Bq"),
        ("TWh", "Bq/TWh", "Bq"),
        ("GWa", "Bq/GWa", "Bq"),
        ("TWh", "Bq/a per GWa", "Bq/a"),
        ("GWa", "Bq/a per TWh", "Bq/a"),
    ],
)
def test_result_unit(driver, factor, want):
    assert result_unit(driver, factor) == want


@pytest.mark.parametrize(
    "driver,factor",
    [("GWa", "Bq/t"), ("t", "Bq/m3"), ("t", "Bq/TWh"), ("m3", "Bq/GWa"),
     ("GWh", "Bq/GWa"), ("t", "Bq"), ("m3", "Bq/a per t")],
)
def test_result_unit_mismatch_raises(driver, factor):
    with pytest.raises(LibError):
        result_unit(driver, factor)
