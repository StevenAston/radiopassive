"""Spec-blind tests for LIB_SPEC section 9 (v1.3): mass factors 't/<driver_unit>'."""
from __future__ import annotations

import pytest

from pipeline.lib import LibError
from pipeline.lib.bounds import Bounds, product
from pipeline.lib.factors import apply, master_unit, result_unit


def frow(**over):
    row = {
        "factor_id": "geo:0001", "description": "mass factor", "stream": "geothermal",
        "stage": "drilling", "driver_series": "geo_gwa", "group": "Ra226+",
        "tier": "reisolated", "route": None, "residue_type": None, "region": "XWL",
        "year_from": 1990, "year_to": 2020,
        "value_low": 1.0, "value_central": 10.0, "value_high": 100.0,
        "unit": "t/GWa", "below_detection": False, "basis": "compiled",
        "source_ids": ["S0003"], "notes": None,
    }
    row.update(over)
    return row


def same(a: Bounds, b: Bounds, rel=1e-12):
    assert a.low == pytest.approx(b.low, rel=rel, abs=1e-300)
    assert a.central == pytest.approx(b.central, rel=rel)
    assert a.high == pytest.approx(b.high, rel=rel)
    assert a.nd_floored == b.nd_floored


FAC = Bounds(1.0, 10.0, 100.0)


# ------------------------------------------------------------- apply: values

def test_t_per_gwa_with_gwa_driver_exact_driver():
    out = apply(Bounds.exact(70.0), "GWa", frow())
    assert out.central == pytest.approx(700.0)
    assert out.low == pytest.approx(70.0)
    assert out.high == pytest.approx(7000.0)


def test_t_per_gwa_with_gwa_driver_matches_product():
    d = Bounds(60.0, 70.0, 85.0)
    same(apply(d, "GWa", frow()), product(d, FAC))


def test_t_per_gwa_with_twh_driver_converts_exactly():
    # 8.766 TWh = 1 GWa exactly -> central 10 t
    out = apply(Bounds.exact(8.766), "TWh", frow())
    assert out.central == pytest.approx(10.0, rel=1e-12)
    assert out.low == pytest.approx(1.0, rel=1e-12)
    assert out.high == pytest.approx(100.0, rel=1e-12)


def test_t_per_gwa_with_twh_driver_matches_product_on_converted_driver():
    d = Bounds(500.0, 613.62, 700.0)
    same(apply(d, "TWh", frow()), product(d.scale(1 / 8.766), FAC), rel=1e-10)


def test_t_per_twh_with_gwa_driver_converts():
    # 2 GWa = 17.532 TWh ; factor 3 t/TWh -> 52.596 t
    fac = frow(unit="t/TWh", value_low=3.0, value_central=3.0, value_high=3.0)
    out = apply(Bounds.exact(2.0), "GWa", fac)
    assert out.central == pytest.approx(2 * 8.766 * 3.0, rel=1e-12)


def test_t_per_m3_with_m3_driver():
    fac = frow(unit="t/m3", value_low=0.4, value_central=0.5, value_high=0.7)
    d = Bounds(90.0, 100.0, 120.0)
    out = apply(d, "m3", fac)
    same(out, product(d, Bounds(0.4, 0.5, 0.7)))
    assert out.central == pytest.approx(50.0)


def test_unit_string_surrounding_whitespace_tolerated():
    out = apply(Bounds.exact(2.0), "GWa", frow(unit="  t/GWa "))
    assert out.central == pytest.approx(20.0)


# -------------------------------------------------------------- result_unit

@pytest.mark.parametrize("driver,factor", [
    ("GWa", "t/GWa"), ("TWh", "t/GWa"), ("GWa", "t/TWh"), ("m3", "t/m3"),
])
def test_result_unit_is_tonnes(driver, factor):
    assert result_unit(driver, factor) == "t"


@pytest.mark.parametrize("driver,factor", [
    ("t", "t/m3"), ("m3", "t/GWa"), ("GWa", "t/m3"), ("t", "t/GWa"),
])
def test_result_unit_mismatch_raises(driver, factor):
    with pytest.raises(LibError):
        result_unit(driver, factor)


@pytest.mark.parametrize("driver,factor", [("t", "t/m3"), ("m3", "t/GWa"), ("t", "t/t")])
def test_apply_mismatch_raises(driver, factor):
    with pytest.raises(LibError):
        apply(Bounds.exact(1.0), driver, frow(unit=factor))


# ------------------------------------------------------ unsupported spellings

BAD = ["t/", "t", "kg/m3", "Mt/a", "t per GWa", "t/   ", "kg/GWa", "Mt/GWa"]


@pytest.mark.parametrize("unit", BAD)
def test_apply_unsupported_mass_spelling_raises(unit):
    with pytest.raises(LibError):
        apply(Bounds.exact(1.0), "GWa", frow(unit=unit))


@pytest.mark.parametrize("unit", BAD)
def test_result_unit_unsupported_mass_spelling_raises(unit):
    for driver in ("GWa", "m3", "t"):
        with pytest.raises(LibError):
            result_unit(driver, unit)


# ------------------------------------------------------ bounds / below_detection

def test_wide_bounds_propagate_via_product_for_mass_and_bq_alike():
    d = Bounds(2.0, 3.0, 4.0)
    mass = apply(d, "GWa", frow(value_low=8.0, value_central=10.0, value_high=12.0))
    bq = apply(d, "GWa", frow(unit="Bq/GWa", value_low=8.0, value_central=10.0, value_high=12.0))
    same(mass, bq)
    same(mass, product(d, Bounds(8.0, 10.0, 12.0)))


def test_below_detection_mass_factor_uses_rows_own_values_and_flags():
    fac = frow(unit="t/m3", below_detection=True, value_low=0.0, value_central=4.0, value_high=10.0)
    out = apply(Bounds.exact(2.0), "m3", fac)
    assert out.nd_floored is True
    assert out.low == 0.0
    assert out.central == pytest.approx(8.0)
    assert out.high == pytest.approx(20.0)


def test_below_detection_mass_matches_bq_behaviour():
    kw = {"below_detection": True, "value_low": 0.0, "value_central": 4.0, "value_high": 10.0}
    d = Bounds(1.0, 2.0, 3.0)
    same(apply(d, "m3", frow(unit="t/m3", **kw)), apply(d, "m3", frow(unit="Bq/m3", **kw)))


def test_below_detection_wrong_type_still_raises_for_mass():
    with pytest.raises(LibError):
        apply(Bounds.exact(1.0), "GWa", frow(below_detection="false"))


# --------------------------------------------------------------- master_unit

@pytest.mark.parametrize("kind", ["flow", "stock"])
def test_master_unit_tonnes_passes_through(kind):
    """LIB_SPEC 9.4 (revised): non-Bq units pass through unchanged, as in v1.2."""
    assert master_unit("t", kind) == "t"


# ---------------------------------------------------------------- regression

def test_regression_bq_per_driver():
    out = apply(Bounds.exact(2.0), "t", frow(unit="Bq/t", value_low=1.0, value_central=2.0, value_high=3.0))
    assert out.central == pytest.approx(4.0)
    assert result_unit("t", "Bq/t") == "Bq"


def test_regression_bq_per_a_per_driver():
    assert result_unit("GWa", "Bq/a per GWa") == "Bq/a"
    assert apply(Bounds.exact(2.0), "GWa", frow(unit="Bq/a per GWa")).central == pytest.approx(20.0)


def test_regression_dimensionless_returns_driver_unit():
    assert result_unit("m3", "1") == "m3"
    assert result_unit("t", "1") == "t"


def test_regression_master_unit_bq():
    assert master_unit("Bq", "flow") == "Bq/a"
    with pytest.raises(LibError):
        master_unit("Bq/a", "stock")
