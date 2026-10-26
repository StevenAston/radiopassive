"""D6 allocation of multi-product outputs (METHODS §10; LIB_SPEC §2)."""

from __future__ import annotations

import math
from collections.abc import Mapping

from . import LibError
from .bounds import Bounds, is_number

VARIANTS = ("alloc:value", "alloc:mass", "alloc:main", "alloc:radio")
# Tolerance for floating-point overshoot when demand equals production.
_SIGMA_TOL = 1e-12
_SHARE_TOL = 1e-12


def _finite_nonneg(name: str, x: object) -> None:
    if not is_number(x) or x < 0:  # type: ignore[operator]
        raise LibError(f"{name} must be a finite number >= 0 (not bool), got {x!r}")


def _mapping(name: str, x: object) -> Mapping:
    if not isinstance(x, Mapping):
        raise LibError(f"{name} must be a mapping, got {x!r}")
    return x


def shares(
    products: Mapping[str, tuple[float, float | None]],
    variant: str,
    *,
    main: str | None = None,
    radio: str | None = None,
) -> dict[str, float]:
    """Share of the multi-product output attributed to each product (METHODS §10.1).

    ``products`` maps name to ``(quantity_t, unit_value)``; ``unit_value`` is
    only needed for ``alloc:value``. Shares are >= 0 and sum to 1.
    """
    _mapping("products", products)
    if not isinstance(variant, str):
        raise LibError(f"allocation variant must be a string, got {variant!r}")
    if variant not in VARIANTS:
        raise LibError(f"unknown allocation variant {variant!r}")
    entries: dict[str, tuple[float, float | None]] = {}
    for name, entry in products.items():
        if not isinstance(entry, (tuple, list)) or len(entry) != 2:
            raise LibError(f"product {name!r} must be a (quantity, unit_value) pair, got {entry!r}")
        qty, val = entry
        _finite_nonneg(f"quantity of {name!r}", qty)
        if val is not None:
            _finite_nonneg(f"unit_value of {name!r}", val)
        entries[name] = (qty, val)

    for arg, named in (("main", main), ("radio", radio)):
        if named is not None and not isinstance(named, str):
            raise LibError(f"{arg} must be a string or None, got {named!r}")

    if variant in ("alloc:main", "alloc:radio"):
        chosen = main if variant == "alloc:main" else radio
        arg = "main" if variant == "alloc:main" else "radio"
        if chosen is None:
            raise LibError(f"{variant} requires the {arg}= product name")
        if chosen not in entries:
            raise LibError(f"{arg} product {chosen!r} is not in products")
        return {p: (1.0 if p == chosen else 0.0) for p in entries}

    weights: dict[str, float] = {}
    for name, (qty, val) in entries.items():
        if variant == "alloc:value":
            if val is None:
                raise LibError(f"alloc:value needs a unit_value for {name!r}")
            weights[name] = qty * val
        else:
            weights[name] = qty
    try:
        total = math.fsum(weights.values())
    except OverflowError as exc:
        raise LibError(f"{variant}: total overflows") from exc
    if not all(math.isfinite(w) for w in weights.values()) or not math.isfinite(total):
        raise LibError(f"{variant}: weights or total overflow")
    if total <= 0:
        raise LibError(f"{variant}: denominator is 0")
    return {p: w / total for p, w in weights.items()}


def split(bounds: Bounds, shares: Mapping[str, float]) -> dict[str, Bounds]:
    """Apply each (exact) share to ``bounds`` (LIB_SPEC §2.2, §8.6)."""
    if not isinstance(bounds, Bounds):
        raise LibError(f"bounds must be a Bounds, got {bounds!r}")
    _mapping("shares", shares)
    checked: dict[str, float] = {}
    for p, s in shares.items():
        if not is_number(s) or not (0 <= s <= 1 + _SHARE_TOL):
            raise LibError(f"share of {p!r} must be a number in [0, 1], got {s!r}")
        # Rounding overshoot within tolerance is clamped so no output exceeds the input.
        checked[p] = min(s, 1.0)
    return {p: bounds.scale(s) for p, s in checked.items()}


def attribution_share(
    cap_added: Mapping[str, float], intensity: Mapping[str, float], production: float
) -> float:
    """Share of a commodity's world production demanded by new capacity (METHODS §10.2).

    $\\sigma_c=\\sum_t C_t I_{t,c}/Q_c$ with C in GW, I in t/GW, Q in t.
    """
    _mapping("cap_added", cap_added)
    _mapping("intensity", intensity)
    if not is_number(production) or production <= 0:
        raise LibError(f"production must be a finite number > 0 (not bool), got {production!r}")
    for tech, value in intensity.items():
        _finite_nonneg(f"intensity[{tech!r}]", value)
    terms = []
    for tech, cap in cap_added.items():
        _finite_nonneg(f"cap_added[{tech!r}]", cap)
        if tech in intensity:
            terms.append(cap * intensity[tech])
    try:
        sigma = math.fsum(terms) / production
    except OverflowError as exc:
        raise LibError("attribution share overflows") from exc
    if not math.isfinite(sigma):
        raise LibError("attribution share overflows")
    if sigma > 1 + _SIGMA_TOL:
        raise LibError(f"attribution share {sigma:.6g} > 1: demand exceeds world production")
    return min(sigma, 1.0)


def variant_token(allocation_variant: str, default_token: str = "alloc:value") -> str:
    """Map a master ``allocation_variant`` to an ``alloc:*`` token (LIB_SPEC §7.3)."""
    if not isinstance(allocation_variant, str):
        raise LibError(f"allocation_variant must be a string, got {allocation_variant!r}")
    mapping = {"default": default_token, "bound_main": "alloc:main", "bound_radio": "alloc:radio"}
    if allocation_variant not in mapping:
        raise LibError(f"unknown allocation_variant {allocation_variant!r}")
    return mapping[allocation_variant]
