"""Low / central / high arithmetic (METHODS §11.1; LIB_SPEC §1).

Independent multiplicative terms combine in log space (quadrature on the log
ratios); independent sums combine in quadrature on the absolute deviations;
fully correlated sums add linearly.
"""

from __future__ import annotations

import logging
import math
from collections.abc import Hashable, Iterable, Sequence
from dataclasses import dataclass

from . import LibError

logger = logging.getLogger(__name__)

# A zero low bound is replaced by this fraction of the central value when
# forming log ratios (METHODS §11.1 "floor").
FLOOR_FRACTION = 1e-3


@dataclass(frozen=True)
class Bounds:
    """A non-negative quantity with ``low <= central <= high`` (METHODS §11.1).

    ``nd_floored`` records that a "not detected" floor dominated the low side.
    """

    low: float
    central: float
    high: float
    nd_floored: bool = False

    def __post_init__(self) -> None:
        values = (self.low, self.central, self.high)
        if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in values):
            raise LibError(f"Bounds values must be finite numbers, got {values!r}")
        if not (0 <= self.low <= self.central <= self.high):
            raise LibError(f"Bounds require 0 <= low <= central <= high, got {values!r}")

    @classmethod
    def exact(cls, x: float) -> Bounds:
        """A quantity with no uncertainty."""
        return cls(x, x, x)

    @classmethod
    def not_detected(cls, dl: float) -> Bounds:
        """A non-detect: low 0, central half the detection limit, high the limit."""
        return cls(0.0, dl / 2, dl, nd_floored=True)

    def scale(self, k: float) -> Bounds:
        """Multiply all three values by a constant ``k >= 0``."""
        if not (isinstance(k, (int, float)) and math.isfinite(k)) or k < 0:
            raise LibError(f"scale factor must be a finite number >= 0, got {k!r}")
        return Bounds(self.low * k, self.central * k, self.high * k, self.nd_floored)


def _make(low: float, central: float, high: float, nd: bool) -> Bounds:
    """Build a Bounds, absorbing last-bit rounding so that the ordering holds."""
    low = min(max(low, 0.0), central)
    high = max(high, central)
    return Bounds(low, central, high, nd)


def product(*terms: Bounds) -> Bounds:
    """Combine independent multiplicative terms (METHODS §11.1; LIB_SPEC §1.2)."""
    if not terms:
        raise LibError("product() needs at least one term")
    nd = any(t.nd_floored for t in terms)

    high_prod = 1.0
    for t in terms:
        high_prod *= t.high
    if any(t.high == 0 for t in terms):
        # An exactly-zero term (LIB_SPEC §7.7) makes the product exactly zero.
        return Bounds(0.0, 0.0, 0.0, nd_floored=nd)
    if any(t.central == 0 for t in terms):
        # A zero central carries no log scale; keep a conservative upper bound.
        logger.warning("zero central value in product; result (0, 0, %.6g)", high_prod)
        return Bounds(0.0, 0.0, high_prod, nd_floored=True)

    central = 1.0
    for t in terms:
        central *= t.central

    sum_high = 0.0
    sum_low = 0.0
    sum_floored = 0.0
    for t in terms:
        sum_high += math.log(t.high / t.central) ** 2
        if t.low > 0:
            sum_low += math.log(t.central / t.low) ** 2
        else:
            contribution = math.log(1.0 / FLOOR_FRACTION) ** 2
            sum_low += contribution
            sum_floored += contribution

    high = central * math.exp(math.sqrt(sum_high))
    if sum_floored > 0 and sum_floored > sum_low / 2:
        low = 0.0
        nd = True
        logger.warning(
            "floor dominance applied: floored terms contribute %.3g of %.3g to the "
            "low-side log variance; low set to 0 (central %.6g)",
            sum_floored,
            sum_low,
            central,
        )
    else:
        low = central / math.exp(math.sqrt(sum_low))
    return _make(low, central, high, nd)


def sum_independent(terms: Iterable[Bounds]) -> Bounds:
    """Sum independent terms, deviations in quadrature (LIB_SPEC §1.3)."""
    terms = list(terms)
    if not terms:
        return Bounds.exact(0.0)
    central = math.fsum(t.central for t in terms)
    up = math.sqrt(math.fsum((t.high - t.central) ** 2 for t in terms))
    down = math.sqrt(math.fsum((t.central - t.low) ** 2 for t in terms))
    return _make(central - down, central, central + up, any(t.nd_floored for t in terms))


def sum_correlated(terms: Iterable[Bounds]) -> Bounds:
    """Sum fully correlated terms, deviations add linearly (LIB_SPEC §1.3)."""
    terms = list(terms)
    if not terms:
        return Bounds.exact(0.0)
    return _make(
        math.fsum(t.low for t in terms),
        math.fsum(t.central for t in terms),
        math.fsum(t.high for t in terms),
        any(t.nd_floored for t in terms),
    )


def sum_grouped(terms: Sequence[Bounds], keys: Sequence[Hashable]) -> Bounds:
    """Correlated within a key (e.g. ``factor_id``), independent across keys."""
    terms = list(terms)
    keys = list(keys)
    if len(terms) != len(keys):
        raise LibError(f"sum_grouped: {len(terms)} terms but {len(keys)} keys")
    groups: dict[Hashable, list[Bounds]] = {}
    for term, key in zip(terms, keys, strict=True):
        groups.setdefault(key, []).append(term)
    return sum_independent([sum_correlated(g) for g in groups.values()])
