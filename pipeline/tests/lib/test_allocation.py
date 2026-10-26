"""Spec-blind tests for pipeline.lib.allocation (LIB_SPEC section 2, METHODS 10)."""
from __future__ import annotations

import random

import pytest

from pipeline.lib import LibError
from pipeline.lib.allocation import attribution_share, shares, split, variant_token
from pipeline.lib.bounds import Bounds

# Olympic-Dam-like illustrative split.  (quantity_t, unit_value)
PRODUCTS = {
    "cu": (100.0, 8000.0),   # q*v = 800 000
    "u": (10.0, 50000.0),    # q*v = 500 000
    "au": (1.0, 100000.0),   # q*v = 100 000
}


# ------------------------------------------------------------------ shares

def test_shares_value_hand_case():
    # total = 800 000 + 500 000 + 100 000 = 1 400 000
    # cu 4/7 = 0.571429 ; u 5/14 = 0.357143 ; au 1/14 = 0.071429
    s = shares(PRODUCTS, "alloc:value")
    assert set(s) == {"cu", "u", "au"}
    assert s["cu"] == pytest.approx(4 / 7, rel=1e-12)
    assert s["u"] == pytest.approx(5 / 14, rel=1e-12)
    assert s["au"] == pytest.approx(1 / 14, rel=1e-12)


def test_shares_mass_hand_case():
    # total = 111 t ; 100/111, 10/111, 1/111
    s = shares(PRODUCTS, "alloc:mass")
    assert s["cu"] == pytest.approx(100 / 111, rel=1e-12)
    assert s["u"] == pytest.approx(10 / 111, rel=1e-12)
    assert s["au"] == pytest.approx(1 / 111, rel=1e-12)


def test_shares_mass_ignores_missing_unit_value():
    s = shares({"a": (3.0, None), "b": (1.0, None)}, "alloc:mass")
    assert s["a"] == pytest.approx(0.75)
    assert s["b"] == pytest.approx(0.25)


def test_shares_main():
    assert shares(PRODUCTS, "alloc:main", main="cu") == {"cu": 1.0, "u": 0.0, "au": 0.0}


def test_shares_radio():
    assert shares(PRODUCTS, "alloc:radio", radio="u") == {"cu": 0.0, "u": 1.0, "au": 0.0}


def test_shares_main_does_not_need_unit_values():
    s = shares({"a": (1.0, None), "b": (2.0, None)}, "alloc:main", main="a")
    assert s == {"a": 1.0, "b": 0.0}


def test_shares_value_zero_value_product_gets_zero_share():
    s = shares({"a": (5.0, 10.0), "b": (5.0, 0.0)}, "alloc:value")
    assert s["a"] == pytest.approx(1.0)
    assert s["b"] == 0.0


def test_shares_single_product_gets_everything():
    assert shares({"only": (2.0, 3.0)}, "alloc:value")["only"] == pytest.approx(1.0)


def test_shares_denominator_zero_value_raises():
    with pytest.raises(LibError):
        shares({"a": (5.0, 0.0), "b": (2.0, 0.0)}, "alloc:value")


def test_shares_denominator_zero_mass_raises():
    with pytest.raises(LibError):
        shares({"a": (0.0, 1.0), "b": (0.0, 2.0)}, "alloc:mass")


def test_shares_empty_products_raises():
    with pytest.raises(LibError):
        shares({}, "alloc:mass")


def test_shares_negative_quantity_raises():
    with pytest.raises(LibError):
        shares({"a": (-1.0, 5.0), "b": (2.0, 5.0)}, "alloc:value")
    with pytest.raises(LibError):
        shares({"a": (-1.0, 5.0), "b": (2.0, 5.0)}, "alloc:mass")


def test_shares_negative_value_raises_for_alloc_value():
    with pytest.raises(LibError):
        shares({"a": (1.0, -5.0), "b": (2.0, 5.0)}, "alloc:value")


def test_shares_negative_value_raises_even_for_mass():
    with pytest.raises(LibError):
        shares({"a": (1.0, -5.0), "b": (2.0, 5.0)}, "alloc:mass")


def test_shares_main_without_main_raises():
    with pytest.raises(LibError):
        shares(PRODUCTS, "alloc:main")


def test_shares_radio_without_radio_raises():
    with pytest.raises(LibError):
        shares(PRODUCTS, "alloc:radio")


def test_shares_main_not_in_products_raises():
    with pytest.raises(LibError):
        shares(PRODUCTS, "alloc:main", main="zinc")


def test_shares_radio_not_in_products_raises():
    with pytest.raises(LibError):
        shares(PRODUCTS, "alloc:radio", radio="zinc")


def test_shares_unknown_variant_raises():
    with pytest.raises(LibError):
        shares(PRODUCTS, "alloc:bogus")


def test_shares_schema_variant_names_are_unknown():
    with pytest.raises(LibError):
        shares(PRODUCTS, "default")


def test_shares_missing_unit_value_for_value_variant_raises_and_names_product():
    with pytest.raises(LibError) as ei:
        shares({"cu": (1.0, 10.0), "mystery": (1.0, None)}, "alloc:value")
    assert "mystery" in str(ei.value)


def test_shares_sweep_sum_to_one_and_nonnegative():
    rng = random.Random(42)
    for _ in range(300):
        n = rng.randint(1, 6)
        prods = {f"p{i}": (rng.uniform(0.1, 1e4), rng.uniform(0.1, 1e5)) for i in range(n)}
        for variant, kw in (
            ("alloc:value", {}),
            ("alloc:mass", {}),
            ("alloc:main", {"main": "p0"}),
            ("alloc:radio", {"radio": f"p{n - 1}"}),
        ):
            s = shares(prods, variant, **kw)
            assert set(s) == set(prods)
            assert abs(sum(s.values()) - 1.0) <= 1e-12, (variant, s)
            assert all(v >= 0.0 for v in s.values()), (variant, s)


# ------------------------------------------------------------------- split

def test_split_hand_case():
    # Bounds (2,4,8) with shares 0.25 / 0.75:
    #   0.25 -> (0.5, 1, 2) ; 0.75 -> (1.5, 3, 6)
    out = split(Bounds(2.0, 4.0, 8.0), {"a": 0.25, "b": 0.75})
    assert set(out) == {"a", "b"}
    assert (out["a"].low, out["a"].central, out["a"].high) == (0.5, 1.0, 2.0)
    assert (out["b"].low, out["b"].central, out["b"].high) == (1.5, 3.0, 6.0)


def test_split_zero_share_gives_zero_bounds():
    out = split(Bounds(2.0, 4.0, 8.0), {"a": 1.0, "b": 0.0})
    assert (out["b"].low, out["b"].central, out["b"].high) == (0.0, 0.0, 0.0)


def test_split_keeps_nd_floored():
    out = split(Bounds(0.0, 1.0, 2.0, nd_floored=True), {"a": 0.5})
    assert out["a"].nd_floored is True


def test_split_negative_share_raises():
    with pytest.raises(LibError):
        split(Bounds(1.0, 2.0, 3.0), {"a": -0.1})


# --------------------------------------------------------- attribution_share

def test_attribution_share_hand_case():
    # sum C*I = 10*300 + 20*100 = 3000 + 2000 = 5000 ; Q = 50 000 -> 0.1
    sigma = attribution_share(
        {"wind": 10.0, "solar": 20.0}, {"wind": 300.0, "solar": 100.0}, 50000.0
    )
    assert sigma == pytest.approx(0.1, rel=1e-12)


def test_attribution_share_missing_intensity_contributes_zero():
    # hydro (5 GW) has no intensity -> 0 ; sum = 3000+2000 = 5000 ; Q=20 000 -> 0.25
    sigma = attribution_share(
        {"wind": 10.0, "solar": 20.0, "hydro": 5.0},
        {"wind": 300.0, "solar": 100.0},
        20000.0,
    )
    assert sigma == pytest.approx(0.25, rel=1e-12)


def test_attribution_share_extra_intensity_ignored():
    sigma = attribution_share({"wind": 10.0}, {"wind": 300.0, "gas": 1e6}, 6000.0)
    assert sigma == pytest.approx(0.5)


def test_attribution_share_empty_capacity_is_zero():
    assert attribution_share({}, {"wind": 300.0}, 1000.0) == 0.0


def test_attribution_share_exactly_one_allowed():
    assert attribution_share({"wind": 10.0}, {"wind": 300.0}, 3000.0) == pytest.approx(1.0)


def test_attribution_share_above_one_raises():
    with pytest.raises(LibError):
        attribution_share({"wind": 10.0}, {"wind": 300.0}, 2999.0)  # 3000/2999 > 1


@pytest.mark.parametrize("q", [0.0, -5.0])
def test_attribution_share_nonpositive_production_raises(q):
    with pytest.raises(LibError):
        attribution_share({"wind": 1.0}, {"wind": 1.0}, q)


# ----------------------------------------------------------- variant_token

def test_variant_token_mapping():
    assert variant_token("default") == "alloc:value"
    assert variant_token("bound_main") == "alloc:main"
    assert variant_token("bound_radio") == "alloc:radio"


def test_variant_token_default_token_override():
    assert variant_token("default", default_token="alloc:mass") == "alloc:mass"
    assert variant_token("default", default_token="alloc:value") == "alloc:value"
    # default_token only affects `default`
    assert variant_token("bound_main", default_token="alloc:mass") == "alloc:main"


@pytest.mark.parametrize("bad", ["alloc:value", "bound_x", "", "DEFAULT"])
def test_variant_token_unknown_raises(bad):
    with pytest.raises(LibError):
        variant_token(bad)


def test_variant_token_output_is_accepted_by_shares():
    s = shares(PRODUCTS, variant_token("bound_main"), main="cu")
    assert s["cu"] == 1.0
    s = shares(PRODUCTS, variant_token("default"))
    assert s["cu"] == pytest.approx(4 / 7)


# ======================================================================
# v1.2 additions (LIB_SPEC section 8.6)
# ======================================================================

# ------------------------------------------------------- shares: types

@pytest.mark.parametrize("bad", [
    None, 5, "cu", [("cu", (1.0, 2.0))], [1.0, 2.0],
])
def test_shares_non_mapping_products_raises_liberror(bad):
    with pytest.raises(LibError):
        shares(bad, "alloc:mass")


@pytest.mark.parametrize("bad", [None, 5, 1.5, ["alloc:value"], b"alloc:value"])
def test_shares_non_string_variant_raises_liberror(bad):
    with pytest.raises(LibError):
        shares(PRODUCTS, bad)


@pytest.mark.parametrize("entry", [
    ("1.0", 2.0), (None, 2.0), (True, 2.0), ([1.0], 2.0),
])
def test_shares_bad_quantity_type_raises_liberror(entry):
    with pytest.raises(LibError):
        shares({"a": entry, "b": (1.0, 2.0)}, "alloc:mass")


@pytest.mark.parametrize("value", ["2.0", True, [2.0]])
def test_shares_bad_unit_value_type_raises_liberror(value):
    with pytest.raises(LibError):
        shares({"a": (1.0, value), "b": (1.0, 2.0)}, "alloc:value")


@pytest.mark.parametrize("entry", [1.0, "ab", None, (1.0,), (1.0, 2.0, 3.0)])
def test_shares_entry_not_a_pair_raises_liberror(entry):
    with pytest.raises(LibError):
        shares({"a": entry, "b": (1.0, 2.0)}, "alloc:mass")


@pytest.mark.parametrize("bad", [float("nan"), float("inf")])
def test_shares_non_finite_quantity_raises_liberror(bad):
    with pytest.raises(LibError):
        shares({"a": (bad, 1.0), "b": (1.0, 1.0)}, "alloc:mass")


# ------------------------------------------------ shares: overflow

def test_shares_mass_total_overflow_raises_liberror():
    with pytest.raises(LibError):
        shares({"a": (1.7e308, 1.0), "b": (1.7e308, 1.0)}, "alloc:mass")


def test_shares_value_product_overflow_raises_liberror():
    with pytest.raises(LibError):
        shares({"a": (1e200, 1e200), "b": (1.0, 1.0)}, "alloc:value")


def test_shares_value_total_overflow_raises_liberror():
    with pytest.raises(LibError):
        shares({"a": (1e308, 1.5), "b": (1e308, 1.5)}, "alloc:value")


# ------------------------------------------------------ split: shares

def test_split_share_just_above_one_within_tolerance_is_accepted():
    out = split(Bounds(2.0, 4.0, 8.0), {"a": 1.0 + 1e-13})
    assert out["a"].central == pytest.approx(4.0, rel=1e-9)


@pytest.mark.parametrize("bad", [1.0 + 1e-9, 1.5, 2.0, 1e6])
def test_split_share_above_one_raises(bad):
    with pytest.raises(LibError):
        split(Bounds(1.0, 2.0, 3.0), {"a": bad})


@pytest.mark.parametrize("bad", [-1e-9, -1.0, float("nan"), float("inf")])
def test_split_share_out_of_range_or_non_finite_raises(bad):
    with pytest.raises(LibError):
        split(Bounds(1.0, 2.0, 3.0), {"a": bad})


def test_split_one_bad_share_among_good_ones_raises():
    with pytest.raises(LibError):
        split(Bounds(1.0, 2.0, 3.0), {"a": 0.5, "b": 1.2})


@pytest.mark.parametrize("bad", [True, "0.5", None])
def test_split_share_wrong_type_raises_liberror(bad):
    with pytest.raises(LibError):
        split(Bounds(1.0, 2.0, 3.0), {"a": bad})


@pytest.mark.parametrize("bad", [(1.0, 2.0, 3.0), 5, None, "b"])
def test_split_non_bounds_raises_liberror(bad):
    with pytest.raises(LibError):
        split(bad, {"a": 0.5})


@pytest.mark.parametrize("bad", [None, 5, [0.5], "a"])
def test_split_non_mapping_shares_raises_liberror(bad):
    with pytest.raises(LibError):
        split(Bounds(1.0, 2.0, 3.0), bad)


# ------------------------------------------- attribution_share: clamp

def test_attribution_share_rounding_overshoot_is_clamped_to_exactly_one():
    # 0.1 + 0.2 = 0.30000000000000004 > 0.3, so the raw ratio is 1 + 2e-16.
    sigma = attribution_share({"a": 0.1, "b": 0.2}, {"a": 1.0, "b": 1.0}, 0.3)
    assert sigma == 1.0


def test_attribution_share_overshoot_within_tolerance_clamped():
    # raw ratio = 1 + 5e-13 <= 1 + 1e-12 -> exactly 1.0
    sigma = attribution_share({"a": 1.0}, {"a": 1.0 + 5e-13}, 1.0)
    assert sigma == 1.0


def test_attribution_share_overshoot_beyond_tolerance_raises():
    # raw ratio = 1 + 1e-11 > 1 + 1e-12
    with pytest.raises(LibError):
        attribution_share({"a": 1.0}, {"a": 1.0 + 1e-11}, 1.0)


def test_attribution_share_below_one_is_not_altered():
    assert attribution_share({"a": 1.0}, {"a": 0.5}, 1.0) == 0.5


# ------------------------------------------- attribution_share: types

@pytest.mark.parametrize("bad", [None, 5, [("a", 1.0)], "a"])
def test_attribution_share_non_mapping_capacity_raises_liberror(bad):
    with pytest.raises(LibError):
        attribution_share(bad, {"a": 1.0}, 10.0)


@pytest.mark.parametrize("bad", [None, 5, [("a", 1.0)], "a"])
def test_attribution_share_non_mapping_intensity_raises_liberror(bad):
    with pytest.raises(LibError):
        attribution_share({"a": 1.0}, bad, 10.0)


@pytest.mark.parametrize("bad", [True, "10", None, [10.0], float("nan")])
def test_attribution_share_bad_production_raises_liberror(bad):
    with pytest.raises(LibError):
        attribution_share({"a": 1.0}, {"a": 1.0}, bad)


@pytest.mark.parametrize("bad", [True, "1", None])
def test_attribution_share_bad_capacity_value_raises_liberror(bad):
    with pytest.raises(LibError):
        attribution_share({"a": bad}, {"a": 1.0}, 10.0)


@pytest.mark.parametrize("bad", [True, "1", None])
def test_attribution_share_bad_intensity_value_raises_liberror(bad):
    with pytest.raises(LibError):
        attribution_share({"a": 1.0}, {"a": bad}, 10.0)


def test_attribution_share_overflow_raises_liberror():
    with pytest.raises(LibError):
        attribution_share({"a": 1e308}, {"a": 1e308}, 1.0)


# --------------------------------------------------- variant_token types

@pytest.mark.parametrize("bad", [None, 5, ["default"], b"default"])
def test_variant_token_non_string_raises_liberror(bad):
    with pytest.raises(LibError):
        variant_token(bad)


# ------------------------------------- LIB_SPEC 8.8 (round 2) and gap tests

def test_split_share_just_above_one_within_tolerance_equals_scale_by_one():
    # 8.6: shares in [0, 1 + 1e-12] are accepted; 8.8 gap: result is exactly scale(1.0).
    b = Bounds(1.0, 2.0, 4.0)
    for sh in (1.0 + 5e-13, 1.0 + 1e-12):
        out = split(b, {"a": sh})
        assert out["a"] == b.scale(1.0), (sh, out)
        assert (out["a"].low, out["a"].central, out["a"].high) == (1.0, 2.0, 4.0)


def test_split_share_beyond_tolerance_raises():
    with pytest.raises(LibError):
        split(Bounds(1.0, 2.0, 4.0), {"a": 1.0 + 1e-9})


@pytest.mark.parametrize("products", [
    {"a": (10**400, 1.0)},
    {"a": (1.0, 10**400)},
    {"a": (1.0, 1.0), "b": (10**400, 1.0)},
])
@pytest.mark.parametrize("variant", ["alloc:value", "alloc:mass"])
def test_shares_huge_int_raises_liberror(products, variant):
    # 8.8.1
    with pytest.raises(LibError):
        shares(products, variant)


@pytest.mark.parametrize("args", [
    ({"t": 1.0}, {"t": 1.0}, 10**400),
    ({"t": 10**400}, {"t": 1.0}, 1.0),
    ({"t": 1.0}, {"t": 10**400}, 1.0),
])
def test_attribution_share_huge_int_raises_liberror(args):
    with pytest.raises(LibError):
        attribution_share(*args)


def test_split_huge_int_share_raises_liberror():
    with pytest.raises(LibError):
        split(Bounds(1.0, 2.0, 4.0), {"a": 10**400})


@pytest.mark.parametrize("kw", [
    {"main": 5}, {"main": b"cu"}, {"main": ["cu"]}, {"main": 1.0},
])
def test_shares_alloc_main_non_str_name_raises(kw):
    # 8.8.3
    with pytest.raises(LibError):
        shares(PRODUCTS, "alloc:main", **kw)


@pytest.mark.parametrize("kw", [
    {"radio": 5}, {"radio": b"u"}, {"radio": ["u"]}, {"radio": 1.0},
])
def test_shares_alloc_radio_non_str_name_raises(kw):
    with pytest.raises(LibError):
        shares(PRODUCTS, "alloc:radio", **kw)


def test_shares_non_str_main_raises_even_for_other_variant():
    # 8.8.3: "main and radio must be str (or None), otherwise LibError".
    with pytest.raises(LibError):
        shares(PRODUCTS, "alloc:mass", main=5)
    with pytest.raises(LibError):
        shares(PRODUCTS, "alloc:mass", radio=5)


def test_shares_none_names_still_accepted_for_mass():
    s = shares(PRODUCTS, "alloc:mass", main=None, radio=None)
    assert sum(s.values()) == pytest.approx(1.0, abs=1e-12)
