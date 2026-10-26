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


def is_number(x: object) -> bool:
    """True for a finite real number that is not a bool (LIB_SPEC §8.6)."""
    if not isinstance(x, (int, float)) or isinstance(x, bool):
        return False
    try:
        return math.isfinite(x)
    except OverflowError:  # an int too large for a float (LIB_SPEC §8.8.1)
        return False


@dataclass(frozen=True)
class Bounds:
    """A non-negative quantity with ``low <= central <= high`` (METHODS §11.1).

    ``nd_floored`` means the low bound is zero because of a non-detect or the
    floor rule (LIB_SPEC §8.1), so it can only be true when ``low == 0``.
    """

    low: float
    central: float
    high: float
    nd_floored: bool = False

    def __post_init__(self) -> None:
        values = (self.low, self.central, self.high)
        if not all(is_number(v) for v in values):
            raise LibError(f"Bounds values must be finite numbers (not bool), got {values!r}")
        if not (0 <= self.low <= self.central <= self.high):
            raise LibError(f"Bounds require 0 <= low <= central <= high, got {values!r}")
        if not isinstance(self.nd_floored, bool):
            raise LibError(f"nd_floored must be a bool, got {self.nd_floored!r}")
        if self.nd_floored and self.low != 0:
            raise LibError(f"nd_floored requires low == 0, got low={self.low!r}")
        # Adding 0.0 turns -0.0 into 0.0 and leaves every other value unchanged.
        for name, v in zip(("low", "central", "high"), values, strict=True):
            object.__setattr__(self, name, v + 0.0)

    @classmethod
    def exact(cls, x: float) -> Bounds:
        """A quantity with no uncertainty."""
        return cls(x, x, x)

    @classmethod
    def not_detected(cls, dl: float) -> Bounds:
        """A non-detect: low 0, central half the detection limit, high the limit."""
        if not is_number(dl):
            raise LibError(f"detection limit must be a finite number, got {dl!r}")
        return cls(0.0, dl / 2, dl, nd_floored=True)

    def scale(self, k: float) -> Bounds:
        """Multiply all three values by a constant ``k >= 0``."""
        if not is_number(k) or k < 0:
            raise LibError(f"scale factor must be a finite number >= 0, got {k!r}")
        return Bounds(self.low * k, self.central * k, self.high * k, self.nd_floored)


def _terms(terms: object, what: str) -> list[Bounds]:
    """Materialise an iterable of ``Bounds``, raising ``LibError`` otherwise."""
    try:
        items = list(terms)  # type: ignore[call-overload]
    except TypeError as exc:
        raise LibError(f"{what}: expected an iterable of Bounds, got {terms!r}") from exc
    for t in items:
        if not isinstance(t, Bounds):
            raise LibError(f"{what}: expected Bounds, got {t!r}")
    return items


def _finish(low: float, central: float, high: float, flag_cause: bool, what: str) -> Bounds:
    """Build the result, absorbing last-bit rounding and applying LIB_SPEC §8.1."""
    if not all(math.isfinite(v) for v in (low, central, high)):
        raise LibError(f"{what}: result is not finite (overflow)")
    low = min(max(low, 0.0), central)
    high = max(high, central)
    return Bounds(low, central, high, nd_floored=flag_cause and low == 0)


def product(*terms: Bounds) -> Bounds:
    """Combine independent multiplicative terms (METHODS §11.1; LIB_SPEC §1.2)."""
    if not terms:
        raise LibError("product() needs at least one term")
    terms = tuple(_terms(terms, "product"))
    flagged = any(t.nd_floored for t in terms)

    if any(t.high == 0 for t in terms):
        # An exactly-zero term (LIB_SPEC §7.7) makes the product exactly zero.
        return Bounds(0.0, 0.0, 0.0, nd_floored=flagged)
    if any(t.central == 0 for t in terms):
        # A zero central carries no log scale; keep a conservative upper bound.
        high_prod = 1.0
        for t in terms:
            high_prod *= t.high
        logger.warning("zero central value in product; result (0, 0, %.6g)", high_prod)
        return _finish(0.0, 0.0, high_prod, True, "product")

    central = 1.0
    for t in terms:
        central *= t.central
    if central == 0.0:
        raise LibError("product: central value underflows to 0")

    sum_high = 0.0
    sum_low = 0.0
    sum_floored = 0.0
    for t in terms:
        # Differences of logs, not logs of ratios, so extreme magnitudes cannot overflow.
        sum_high += (math.log(t.high) - math.log(t.central)) ** 2
        if t.low > 0:
            sum_low += (math.log(t.central) - math.log(t.low)) ** 2
        else:
            contribution = math.log(1.0 / FLOOR_FRACTION) ** 2
            sum_low += contribution
            sum_floored += contribution

    try:
        high = central * math.exp(math.sqrt(sum_high))
    except OverflowError as exc:
        raise LibError("product: high bound overflows") from exc
    cause = flagged
    if sum_floored > 0 and sum_floored > sum_low / 2:
        low = 0.0
        cause = True
        logger.warning(
            "floor dominance applied: floored terms contribute %.3g of %.3g to the "
            "low-side log variance; low set to 0 (central %.6g)",
            sum_floored,
            sum_low,
            central,
        )
    else:
        low = central * math.exp(-math.sqrt(sum_low))
    return _finish(low, central, high, cause, "product")


def sum_independent(terms: Iterable[Bounds]) -> Bounds:
    """Sum independent terms, deviations in quadrature (LIB_SPEC §1.3)."""
    items = _terms(terms, "sum_independent")
    if not items:
        return Bounds.exact(0.0)
    try:
        central = math.fsum(t.central for t in items)
        up = math.hypot(*(t.high - t.central for t in items))
        down = math.hypot(*(t.central - t.low for t in items))
        return _finish(
            central - down,
            central,
            central + up,
            any(t.nd_floored for t in items),
            "sum_independent",
        )
    except OverflowError as exc:
        raise LibError("sum_independent: result overflows") from exc


def sum_correlated(terms: Iterable[Bounds]) -> Bounds:
    """Sum fully correlated terms, deviations add linearly (LIB_SPEC §1.3)."""
    items = _terms(terms, "sum_correlated")
    if not items:
        return Bounds.exact(0.0)
    try:
        return _finish(
            math.fsum(t.low for t in items),
            math.fsum(t.central for t in items),
            math.fsum(t.high for t in items),
            any(t.nd_floored for t in items),
            "sum_correlated",
        )
    except OverflowError as exc:
        raise LibError("sum_correlated: result overflows") from exc


def sum_grouped(terms: Sequence[Bounds], keys: Sequence[Hashable]) -> Bounds:
    """Correlated within a key (e.g. ``factor_id``), independent across keys."""
    items = _terms(terms, "sum_grouped")
    try:
        key_list = list(keys)
    except TypeError as exc:
        raise LibError(f"sum_grouped: keys must be an iterable, got {keys!r}") from exc
    if len(items) != len(key_list):
        raise LibError(f"sum_grouped: {len(items)} terms but {len(key_list)} keys")
    groups: dict[Hashable, list[Bounds]] = {}
    for term, key in zip(items, key_list, strict=True):
        try:
            groups.setdefault(key, []).append(term)
        except TypeError as exc:
            raise LibError(f"sum_grouped: unhashable key {key!r}") from exc
    out = sum_independent([sum_correlated(g) for g in groups.values()])
    # Judge the flag on the original terms: an intermediate group may have lost it.
    flag = out.low == 0 and any(t.nd_floored for t in items)
    return Bounds(out.low, out.central, out.high, nd_floored=flag)
