"""Spec-blind tests for pipeline.lib.factors (LIB_SPEC section 3)."""
from __future__ import annotations

import math

import pytest

from pipeline.lib import LibError
from pipeline.lib import factors as _factors_module
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


# ======================================================================
# v1.2 additions (LIB_SPEC section 8)
# ======================================================================

# ------------------------------------------------ select: mutation gaps

def test_select_none_region_row_is_not_an_exact_region_match():
    # A row whose region is None is neither the requested region nor XWL.
    nameless = frow("coal:0001", region=None)
    world = frow("coal:0002", region="XWL")
    assert select([nameless, world], year=2000, region="CHN") == world
    assert select([world, nameless], year=2000, region="CHN") == world


def test_select_only_none_region_row_is_no_candidate():
    with pytest.raises(LibError):
        select([frow(region=None)], year=2000, region="CHN")


def test_select_none_region_row_does_not_make_exact_level_ambiguous():
    exact = frow("coal:0001", region="CHN")
    nameless = frow("coal:0002", region=None)
    assert select([exact, nameless], year=2000, region="CHN") == exact


def test_select_returns_a_copy_not_the_input_row():
    r = frow()
    got = select([r], year=2000, region="CHN")
    assert got is not r
    assert got == r


def test_select_result_mutation_does_not_change_input():
    r = frow()
    snapshot = dict(r)
    got = select([r], year=2000, region="CHN")
    got["value_central"] = 999.0
    got["notes"] = "changed"
    del got["unit"]
    assert r == snapshot


def test_select_result_copy_holds_for_xwl_fallback_too():
    r = frow(region="XWL")
    got = select([r], year=2000, region="CHN")
    got["value_low"] = -1.0
    assert r["value_low"] == 5.0


# --------------------------------------------------- select: wrong types

@pytest.mark.parametrize("bad", [5, None, 2.5])
def test_select_non_iterable_factors_raises_liberror(bad):
    with pytest.raises(LibError):
        select(bad, year=2000, region="CHN")


@pytest.mark.parametrize("bad_row", ["row", 5, None, ["a"]])
def test_select_non_mapping_row_raises_liberror(bad_row):
    with pytest.raises(LibError):
        select([frow(), bad_row], year=2000, region="CHN")


@pytest.mark.parametrize("bad_year", ["2000", True, False, None, [2000]])
def test_select_non_int_year_raises_liberror(bad_year):
    with pytest.raises(LibError):
        select([frow()], year=bad_year, region="CHN")


@pytest.mark.parametrize("bad_region", [5, True, ["CHN"], b"CHN"])
def test_select_non_string_region_raises_liberror(bad_region):
    with pytest.raises(LibError):
        select([frow()], year=2000, region=bad_region)


# ------------------------------------------------------ apply: types

def test_apply_non_bounds_driver_raises_liberror():
    for bad in (4.0, "4", None, (1.0, 2.0, 3.0)):
        with pytest.raises(LibError):
            apply(bad, "t", frow())


@pytest.mark.parametrize("bad", [None, 5, True, b"t", ["t"]])
def test_apply_non_string_driver_unit_raises_liberror(bad):
    with pytest.raises(LibError):
        apply(Bounds.exact(1.0), bad, frow())


@pytest.mark.parametrize("bad", [None, 5, "row", [("unit", "Bq/t")]])
def test_apply_non_mapping_factor_row_raises_liberror(bad):
    with pytest.raises(LibError):
        apply(Bounds.exact(1.0), "t", bad)


@pytest.mark.parametrize("bad_unit", [None, 5, True])
def test_apply_non_string_factor_unit_raises_liberror(bad_unit):
    with pytest.raises(LibError):
        apply(Bounds.exact(1.0), "t", frow(unit=bad_unit))


@pytest.mark.parametrize("field", ["value_low", "value_central", "value_high"])
@pytest.mark.parametrize("bad", [None, "5", True])
def test_apply_non_numeric_factor_values_raise_liberror(field, bad):
    with pytest.raises(LibError):
        apply(Bounds.exact(1.0), "t", frow(**{field: bad}))


@pytest.mark.parametrize("bad", ["false", "true", "False", "", 0, 1, 0.0, [], ["x"]])
def test_apply_below_detection_wrong_type_raises_liberror(bad):
    with pytest.raises(LibError):
        apply(Bounds.exact(1.0), "t", frow(below_detection=bad))


def test_apply_below_detection_string_false_is_not_treated_as_false():
    # Regression guard: the string "false" is truthy in Python; it must be
    # rejected, not silently treated as a non-detect.
    with pytest.raises(LibError):
        apply(Bounds.exact(2.0), "t",
              frow(value_low=0.0, value_central=4.0, value_high=10.0, below_detection="false"))


def test_apply_below_detection_none_is_treated_as_false():
    out = apply(Bounds.exact(2.0), "t", frow(below_detection=None))
    assert out.central == pytest.approx(20.0)


def test_apply_below_detection_true_and_false_bools_accepted():
    row_true = frow(value_low=0.0, value_central=4.0, value_high=10.0, below_detection=True)
    row_false = frow(value_low=1.0, value_central=4.0, value_high=10.0, below_detection=False)
    assert apply(Bounds.exact(2.0), "t", row_true).central == pytest.approx(8.0)
    assert apply(Bounds.exact(2.0), "t", row_false).central == pytest.approx(8.0)


# ------------------------------- apply: below_detection carried into flag

def test_apply_below_detection_flag_visible_when_only_the_flag_can_carry_it():
    # Exact-zero driver: product returns exact(0), flagged only if an input
    # was flagged (8.1).  The factor row (0, 4, 10) is a non-detect only if the
    # row says so, so the two cases must differ.
    zero = Bounds.exact(0.0)
    nd_row = frow(value_low=0.0, value_central=4.0, value_high=10.0, below_detection=True)
    plain_row = frow(value_low=0.0, value_central=4.0, value_high=10.0, below_detection=False)
    flagged = apply(zero, "t", nd_row)
    unflagged = apply(zero, "t", plain_row)
    assert (flagged.low, flagged.central, flagged.high) == (0.0, 0.0, 0.0)
    assert flagged.nd_floored is True
    assert (unflagged.low, unflagged.central, unflagged.high) == (0.0, 0.0, 0.0)
    assert unflagged.nd_floored is False


def test_apply_row_low_zero_below_detection_true_gives_flagged_zero_low():
    row = frow(value_low=0.0, value_central=4.0, value_high=10.0, below_detection=True)
    out = apply(Bounds.exact(2.0), "t", row)
    assert out.low == 0.0 and out.nd_floored is True


def test_apply_row_low_zero_below_detection_false_floor_rule_still_flags():
    # Floor rule: single floored term is 100% of the log sum -> low 0, flagged.
    row = frow(value_low=0.0, value_central=4.0, value_high=10.0, below_detection=False)
    out = apply(Bounds.exact(2.0), "t", row)
    assert out.low == 0.0 and out.nd_floored is True


def test_apply_row_low_positive_below_detection_false_is_unflagged():
    row = frow(value_low=2.0, value_central=4.0, value_high=10.0, below_detection=False)
    out = apply(Bounds.exact(2.0), "t", row)
    assert out.low > 0.0 and out.nd_floored is False


def test_apply_row_low_positive_with_below_detection_true_raises():
    # LIB_SPEC 7.6 builds the factor with nd_floored=True from the row's own
    # values; 8.1 makes that an error when low > 0 (row violates SCHEMA 3).
    row = frow(value_low=2.0, value_central=4.0, value_high=10.0, below_detection=True)
    with pytest.raises(LibError):
        apply(Bounds.exact(2.0), "t", row)


# --------------------------------------------------------- master_unit

def master_unit(*args, **kwargs):
    """Late-bound so a missing v1.2 function fails these tests, not collection."""
    fn = getattr(_factors_module, "master_unit", None)
    assert fn is not None, "pipeline.lib.factors.master_unit is not implemented (LIB_SPEC 8.5)"
    return fn(*args, **kwargs)


@pytest.mark.parametrize("unit,kind,want", [
    ("Bq", "flow", "Bq/a"),
    ("Bq/a", "flow", "Bq/a"),
    ("Bq", "stock", "Bq"),
    ("t", "flow", "t"),
    ("t", "stock", "t"),
    ("GWa", "flow", "GWa"),
    ("TWh", "stock", "TWh"),
    ("1", "flow", "1"),
])
def test_master_unit_cases(unit, kind, want):
    assert master_unit(unit, kind) == want


def test_master_unit_stock_with_bq_per_a_raises():
    with pytest.raises(LibError) as ei:
        master_unit("Bq/a", "stock")
    assert str(ei.value)


@pytest.mark.parametrize("kind", ["Flow", "STOCK", "", "flux", "memo", "flow ", None, 1, True])
def test_master_unit_bad_kind_raises(kind):
    with pytest.raises(LibError):
        master_unit("Bq", kind)


@pytest.mark.parametrize("kind", ["Flow", "", None])
def test_master_unit_bad_kind_raises_even_for_passthrough_unit(kind):
    with pytest.raises(LibError):
        master_unit("t", kind)


@pytest.mark.parametrize("bad", [None, 5, True, b"Bq", ["Bq"]])
def test_master_unit_non_string_unit_raises_liberror(bad):
    with pytest.raises(LibError):
        master_unit(bad, "flow")


def test_master_unit_composes_with_result_unit():
    assert master_unit(result_unit("t", "Bq/t"), "flow") == "Bq/a"
    assert master_unit(result_unit("t", "Bq/t"), "stock") == "Bq"
    assert master_unit(result_unit("t", "Bq/a per t"), "flow") == "Bq/a"
    with pytest.raises(LibError):
        master_unit(result_unit("t", "Bq/a per t"), "stock")


@pytest.mark.parametrize("bad", [None, 5, True])
def test_result_unit_non_string_arguments_raise_liberror(bad):
    with pytest.raises(LibError):
        result_unit(bad, "Bq/t")
    with pytest.raises(LibError):
        result_unit("t", bad)


# ------------------------------------- LIB_SPEC 8.8 (round 2) and gap tests

def test_select_unknown_match_key_raises_liberror():
    # 3.1 lists the permitted match keys; an unknown key must not be silently ignored.
    with pytest.raises(LibError):
        select([frow()], year=2000, region="CHN", bogus=None)


def test_select_unknown_match_key_with_value_raises_liberror():
    with pytest.raises(LibError):
        select([frow()], year=2000, region="CHN", bogus="x")


@pytest.mark.parametrize("kind", ["flux", "Flow", "STOCK", "", None, 1, ["flow"]])
@pytest.mark.parametrize("unit", ["Bq", "Bq/a"])
def test_master_unit_invalid_kind_raises_liberror(unit, kind):
    # 8.5: any other kind raises.
    with pytest.raises(LibError):
        _factors_module.master_unit(unit, kind)
