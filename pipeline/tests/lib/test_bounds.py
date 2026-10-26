"""Spec-blind tests for pipeline.lib.bounds (LIB_SPEC section 1, METHODS 11.1).

Written from docs/LIB_SPEC.md and METHODS 10-11 only.  Every formula has a
hand-computed case; the arithmetic is shown beside each.
"""
from __future__ import annotations

import dataclasses
import math
import random

import pytest

from pipeline.lib import LibError
from pipeline.lib.bounds import (
    Bounds,
    product,
    sum_correlated,
    sum_grouped,
    sum_independent,
)


def approx3(b, low, central, high, rel=1e-9):
    assert b.low == pytest.approx(low, rel=rel, abs=1e-300), f"low: {b}"
    assert b.central == pytest.approx(central, rel=rel), f"central: {b}"
    assert b.high == pytest.approx(high, rel=rel), f"high: {b}"


# ---------------------------------------------------------------- LibError

def test_liberror_is_valueerror_subclass():
    assert issubclass(LibError, ValueError)


# ------------------------------------------------------------ construction

def test_bounds_valid_construction_and_defaults():
    b = Bounds(1.0, 2.0, 3.0)
    assert (b.low, b.central, b.high, b.nd_floored) == (1.0, 2.0, 3.0, False)


def test_bounds_allows_equal_and_zero_values():
    Bounds(0.0, 0.0, 0.0)
    Bounds(2.0, 2.0, 2.0)
    Bounds(0.0, 1.0, 1.0)


def test_bounds_is_frozen():
    b = Bounds(1.0, 2.0, 3.0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        b.low = 0.5  # type: ignore[misc]


def test_bounds_equality_is_exact_dataclass_equality():
    assert Bounds(1.0, 2.0, 3.0) == Bounds(1.0, 2.0, 3.0)
    assert Bounds(1.0, 2.0, 3.0) != Bounds(1.0, 2.0, 3.0, nd_floored=True)


@pytest.mark.parametrize(
    "args",
    [
        (3.0, 2.0, 4.0),   # low > central
        (1.0, 5.0, 4.0),   # central > high
        (-0.1, 1.0, 2.0),  # negative low
        (-2.0, -1.0, -0.5),  # all negative
    ],
    ids=["low>central", "central>high", "negative-low", "all-negative"],
)
def test_bounds_rejects_misordered_or_negative(args):
    with pytest.raises(LibError):
        Bounds(*args)


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
@pytest.mark.parametrize("slot", [0, 1, 2])
def test_bounds_rejects_non_finite(bad, slot):
    vals = [1.0, 2.0, 3.0]
    vals[slot] = bad
    with pytest.raises(LibError):
        Bounds(*vals)


def test_exact():
    b = Bounds.exact(4.5)
    assert (b.low, b.central, b.high, b.nd_floored) == (4.5, 4.5, 4.5, False)


def test_exact_negative_raises():
    with pytest.raises(LibError):
        Bounds.exact(-1.0)


def test_not_detected():
    # dl = 6 -> low 0, central dl/2 = 3, high dl = 6, flagged.
    b = Bounds.not_detected(6.0)
    assert (b.low, b.central, b.high, b.nd_floored) == (0.0, 3.0, 6.0, True)


def test_not_detected_negative_limit_raises():
    with pytest.raises(LibError):
        Bounds.not_detected(-1.0)


def test_scale_multiplies_all_three():
    # 2*3 = 6 ; 4*3 = 12 ; 8*3 = 24
    b = Bounds(2.0, 4.0, 8.0).scale(3.0)
    assert (b.low, b.central, b.high) == (6.0, 12.0, 24.0)


def test_scale_keeps_nd_floored():
    assert Bounds(0.0, 1.0, 2.0, nd_floored=True).scale(2.0).nd_floored is True
    assert Bounds(1.0, 1.0, 2.0).scale(2.0).nd_floored is False


def test_scale_zero_allowed():
    b = Bounds(1.0, 2.0, 3.0).scale(0.0)
    assert (b.low, b.central, b.high) == (0.0, 0.0, 0.0)


def test_scale_negative_raises():
    with pytest.raises(LibError):
        Bounds(1.0, 2.0, 3.0).scale(-0.5)


# ----------------------------------------------------------------- product

def test_product_no_terms_raises():
    with pytest.raises(LibError):
        product()


def test_product_single_term_is_identity():
    b = Bounds(1.0, 2.0, 8.0)
    out = product(b)
    approx3(out, 1.0, 2.0, 8.0)
    assert out.nd_floored is False


def test_product_log_quadrature_hand_case():
    # Term a: c=2, l=2e^-5, h=2e^3  -> ln(h/c)=3, ln(c/l)=5
    # Term b: c=10, l=10e^-12, h=10e^4 -> ln(h/c)=4, ln(c/l)=12
    # central = 2*10 = 20
    # high: ln(xh/xc) = sqrt(3^2 + 4^2) = 5   -> 20 e^5
    # low : ln(xc/xl) = sqrt(5^2 + 12^2) = 13 -> 20 e^-13
    e = math.exp
    a = Bounds(2 * e(-5), 2.0, 2 * e(3))
    b = Bounds(10 * e(-12), 10.0, 10 * e(4))
    out = product(a, b)
    approx3(out, 20 * e(-13), 20.0, 20 * e(5))
    assert out.nd_floored is False


def test_product_three_terms_quadrature():
    # Three terms each with ln ratio 1 on the high side and 2 on the low side:
    # high: sqrt(1+1+1)=sqrt3 ; low: sqrt(4+4+4)=sqrt12 ; centrals 1,1,1 -> 1.
    e = math.exp
    t = Bounds(e(-2), 1.0, e(1))
    out = product(t, t, t)
    approx3(out, e(-math.sqrt(12)), 1.0, e(math.sqrt(3)))


def test_product_exact_terms_contribute_nothing():
    # exact(3) has ln ratios 0, so only a's spread remains; central 2*3=6.
    a = Bounds(1.0, 2.0, 8.0)
    out = product(a, Bounds.exact(3.0))
    approx3(out, 3.0, 6.0, 24.0)


def test_product_zero_central_returns_zero_with_conservative_high():
    # Zero central -> Bounds(0, 0, h), h = 5 * 3 = 15, flagged.
    out = product(Bounds(0.0, 0.0, 5.0), Bounds(1.0, 2.0, 3.0))
    assert out.low == 0.0 and out.central == 0.0
    assert out.high == pytest.approx(15.0)
    assert out.nd_floored is True


def test_product_zero_central_high_uses_every_terms_high():
    out = product(Bounds(1.0, 2.0, 4.0), Bounds(0.0, 0.0, 7.0), Bounds(1.0, 1.0, 2.0))
    # 4 * 7 * 2 = 56
    assert out.high == pytest.approx(56.0)
    assert out.central == 0.0 and out.nd_floored is True


def test_product_single_floored_term_floor_dominates():
    # One term, low=0 -> l* = 1e-3 * c ; floored share of sum = 100% > 50%
    # -> result low = 0, flagged; central/high unchanged.
    out = product(Bounds(0.0, 2.0, 8.0))
    approx3(out, 0.0, 2.0, 8.0)
    assert out.low == 0.0
    assert out.nd_floored is True


def test_product_floor_dominance_hand_case_dominant():
    # a: low=0, c=1 -> ln(c/l*) = ln(1000) = 6.9078, squared = 47.717
    # b: c=1, ln(c/l) = 3 -> squared 9
    # floored share = 47.717 / 56.717 = 0.84 > 0.5 -> low = 0, flagged.
    e = math.exp
    a = Bounds(0.0, 1.0, 2.0)
    b = Bounds(e(-3), 1.0, 2.0)
    out = product(a, b)
    assert out.low == 0.0
    assert out.nd_floored is True
    assert out.central == pytest.approx(1.0)
    # high: sqrt(ln2^2 + ln2^2) = ln2*sqrt2 -> 2^sqrt2 = 2.6651
    assert out.high == pytest.approx(2 ** math.sqrt(2), rel=1e-9)


def test_product_floor_not_dominant_hand_case():
    # a: low=0, c=1 -> squared 47.717 (=(3 ln10)^2)
    # b: c=1, ln(c/l)=10 -> squared 100
    # floored share = 47.717/147.717 = 0.32 <= 0.5 -> low NOT forced to 0:
    # ln(xc/xl) = sqrt(147.717) = 12.1539 -> low = e^-12.1539 = 5.2678e-6
    e = math.exp
    a = Bounds(0.0, 1.0, 2.0)
    b = Bounds(e(-10), 1.0, 2.0)
    out = product(a, b)
    assert out.low == pytest.approx(5.267831916865327e-06, rel=1e-6)
    assert out.low > 0.0
    assert out.nd_floored is False


def test_product_propagates_input_nd_floored():
    nd = Bounds.not_detected(2.0)  # (0, 1, 2) flagged
    out = product(nd, Bounds.exact(5.0))
    assert out.nd_floored is True
    approx3(out, 0.0, 5.0, 10.0)


def test_product_input_flag_with_positive_low_still_flags():
    flagged = Bounds(0.5, 1.0, 2.0, nd_floored=True)
    out = product(flagged, Bounds(1.0, 1.0, 1.0))
    assert out.nd_floored is True
    assert out.low > 0.0  # floor rule not triggered; only the flag propagates


def test_product_not_detected_central_is_half_limit():
    # (0, 1.5, 3) x exact(4): central = 6 ; high = 12 ; low floored -> 0
    out = product(Bounds.not_detected(3.0), Bounds.exact(4.0))
    approx3(out, 0.0, 6.0, 12.0)


# -------------------------------------------------------------------- sums
# Hand data: a = (l=6, c=10, h=13): up 3, down 4
#            b = (l=17, c=20, h=24): up 4, down 3

A = Bounds(6.0, 10.0, 13.0)
B = Bounds(17.0, 20.0, 24.0)


def test_sum_independent_hand_case():
    # central 30 ; up sqrt(3^2+4^2)=5 -> 35 ; down sqrt(4^2+3^2)=5 -> 25
    out = sum_independent([A, B])
    approx3(out, 25.0, 30.0, 35.0)
    assert out.nd_floored is False


def test_sum_independent_accepts_any_iterable():
    approx3(sum_independent(iter([A, B])), 25.0, 30.0, 35.0)


def test_sum_independent_or_of_flags():
    out = sum_independent([A, Bounds(0.0, 1.0, 2.0, nd_floored=True)])
    assert out.nd_floored is True


def test_sum_independent_empty_is_exact_zero():
    assert sum_independent([]) == Bounds.exact(0.0)


def test_sum_independent_single_term_identity():
    approx3(sum_independent([A]), 6.0, 10.0, 13.0)


def test_sum_correlated_hand_case():
    # low 6+17 = 23 ; central 30 ; high 13+24 = 37
    approx3(sum_correlated([A, B]), 23.0, 30.0, 37.0)


def test_sum_correlated_empty_is_exact_zero():
    assert sum_correlated([]) == Bounds.exact(0.0)


def test_sum_grouped_hand_case():
    # Group k1: two copies of E=(l=4, c=10, h=16) (up 6, down 6) summed
    #   linearly: (8, 20, 32) -> up 12, down 12.
    # Group k2: F=(l=14, c=20, h=28) -> up 8, down 6.
    # Combined by quadrature: central 40 ; up sqrt(12^2+8^2)=sqrt208 ;
    #   down sqrt(12^2+6^2)=sqrt180.
    E = Bounds(4.0, 10.0, 16.0)
    F = Bounds(14.0, 20.0, 28.0)
    out = sum_grouped([E, E, F], ["k1", "k1", "k2"])
    approx3(
        out,
        40.0 - math.sqrt(180.0),
        40.0,
        40.0 + math.sqrt(208.0),
    )


def test_sum_grouped_distinct_keys_equals_independent():
    approx3(sum_grouped([A, B], ["x", "y"]), 25.0, 30.0, 35.0)


def test_sum_grouped_single_key_equals_correlated():
    approx3(sum_grouped([A, B], ["x", "x"]), 23.0, 30.0, 37.0)


def test_sum_grouped_length_mismatch_raises():
    with pytest.raises(LibError):
        sum_grouped([A, B], ["only-one"])
    with pytest.raises(LibError):
        sum_grouped([A], ["a", "b"])


def test_sum_grouped_empty_is_exact_zero():
    assert sum_grouped([], []) == Bounds.exact(0.0)


def test_all_sums_or_of_flags():
    # LIB_SPEC 7.1: every combining operation ORs nd_floored.
    flagged = Bounds(0.0, 1.0, 2.0, nd_floored=True)
    assert sum_independent([A, flagged]).nd_floored is True
    assert sum_correlated([A, flagged]).nd_floored is True
    assert sum_grouped([A, flagged], ["a", "b"]).nd_floored is True
    assert sum_grouped([A, flagged], ["a", "a"]).nd_floored is True
    assert sum_independent([A, B]).nd_floored is False
    assert sum_correlated([A, B]).nd_floored is False
    assert sum_grouped([A, B], ["a", "b"]).nd_floored is False


def test_product_exact_zero_term_gives_exact_zero():
    # LIB_SPEC 7.7: a term with high == 0 -> Bounds.exact(0.0) (flag = OR of inputs).
    out = product(Bounds.exact(0.0), Bounds(1.0, 2.0, 3.0))
    assert (out.low, out.central, out.high) == (0.0, 0.0, 0.0)
    assert out.nd_floored is False
    out = product(Bounds(1.0, 2.0, 3.0), Bounds.exact(0.0), Bounds(2.0, 3.0, 4.0))
    assert (out.low, out.central, out.high) == (0.0, 0.0, 0.0)


def test_product_exact_zero_term_flag_follows_or_of_inputs():
    out = product(Bounds.exact(0.0), Bounds(0.0, 1.0, 2.0, nd_floored=True))
    assert (out.low, out.central, out.high) == (0.0, 0.0, 0.0)
    assert out.nd_floored is True


def test_product_exact_zero_beats_zero_central_with_positive_high():
    # exact zero present -> exact(0), not (0, 0, prod h)
    out = product(Bounds(0.0, 0.0, 5.0), Bounds.exact(0.0))
    assert (out.low, out.central, out.high) == (0.0, 0.0, 0.0)


# ------------------------------------------------- 1.4 invariants (sweep)

def _random_bounds(rng: random.Random) -> Bounds:
    c = 10 ** rng.uniform(-3, 3)
    if rng.random() < 0.15:
        low = 0.0
    else:
        low = c * 10 ** (-rng.uniform(0, 1.5))
    if rng.random() < 0.15:
        high = c
    else:
        high = c * 10 ** rng.uniform(0, 1.5)
    return Bounds(low, c, high, nd_floored=rng.random() < 0.1)


def _bounds_list(rng, n):
    return [_random_bounds(rng) for _ in range(n)]


N_SWEEP = 300


def test_sweep_product_ordering_invariant():
    rng = random.Random(20261025)
    for _ in range(N_SWEEP):
        terms = _bounds_list(rng, rng.randint(1, 5))
        out = product(*terms)
        assert out.low <= out.central <= out.high, (terms, out)
        assert out.low >= 0.0


def test_sweep_product_with_exact_equals_scale():
    rng = random.Random(7)
    for _ in range(N_SWEEP):
        a = _random_bounds(rng)
        k = 10 ** rng.uniform(-3, 3)
        got = product(a, Bounds.exact(k))
        want = a.scale(k)
        # flags may legitimately differ (floor rule), so compare values only
        assert got.low == pytest.approx(want.low, rel=1e-9, abs=1e-300), (a, k)
        assert got.central == pytest.approx(want.central, rel=1e-9), (a, k)
        assert got.high == pytest.approx(want.high, rel=1e-9), (a, k)


def test_sweep_product_order_independent():
    rng = random.Random(99)
    for _ in range(N_SWEEP):
        terms = _bounds_list(rng, rng.randint(2, 5))
        shuffled = terms[:]
        rng.shuffle(shuffled)
        a, b = product(*terms), product(*shuffled)
        assert a.low == pytest.approx(b.low, rel=1e-9, abs=1e-300), terms
        assert a.central == pytest.approx(b.central, rel=1e-9), terms
        assert a.high == pytest.approx(b.high, rel=1e-9), terms
        assert a.nd_floored == b.nd_floored, terms


def test_sweep_sum_independent_never_wider_than_linear():
    rng = random.Random(1234)
    for _ in range(N_SWEEP):
        terms = _bounds_list(rng, rng.randint(1, 6))
        out = sum_independent(terms)
        lin_low = sum(t.low for t in terms)
        lin_high = sum(t.high for t in terms)
        tol = 1e-9
        assert out.low <= out.central <= out.high
        assert out.low >= lin_low * (1 - tol) - 1e-12, (terms, out)
        assert out.high <= lin_high * (1 + tol) + 1e-12, (terms, out)
        assert out.central == pytest.approx(sum(t.central for t in terms), rel=1e-9)


def test_sweep_sum_correlated_equals_linear_and_ordered():
    rng = random.Random(5)
    for _ in range(N_SWEEP):
        terms = _bounds_list(rng, rng.randint(1, 6))
        out = sum_correlated(terms)
        assert out.low == pytest.approx(sum(t.low for t in terms), rel=1e-9, abs=1e-12)
        assert out.high == pytest.approx(sum(t.high for t in terms), rel=1e-9)
        assert out.low <= out.central <= out.high


def test_sweep_sum_grouped_between_independent_and_correlated():
    rng = random.Random(31)
    for _ in range(N_SWEEP):
        terms = _bounds_list(rng, rng.randint(1, 6))
        keys = [rng.choice("abc") for _ in terms]
        out = sum_grouped(terms, keys)
        ind = sum_independent(terms)
        cor = sum_correlated(terms)
        tol = 1e-9
        assert out.low <= out.central <= out.high
        assert out.high <= cor.high * (1 + tol) + 1e-12
        assert out.high >= ind.high * (1 - tol) - 1e-12
        assert out.low >= cor.low * (1 - tol) - 1e-12
        assert out.low <= ind.low * (1 + tol) + 1e-12
