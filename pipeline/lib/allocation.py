"""D6 allocation of multi-product outputs (METHODS §10; LIB_SPEC §2)."""

from __future__ import annotations

import math
from collections.abc import Mapping

from . import LibError
from .bounds import Bounds

VARIANTS = ("alloc:value", "alloc:mass", "alloc:main", "alloc:radio")
# Tolerance for floating-point overshoot when demand equals production.
_SIGMA_TOL = 1e-12


def _finite_nonneg(name: str, x: float) -> None:
    if not isinstance(x, (int, float)) or not math.isfinite(x) or x < 0:
        raise LibError(f"{name} must be a finite number >= 0, got {x!r}")


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
    if variant not in VARIANTS:
        raise LibError(f"unknown allocation variant {variant!r}")
    for name, (qty, val) in products.items():
        _finite_nonneg(f"quantity of {name!r}", qty)
        if val is not None:
            _finite_nonneg(f"unit_value of {name!r}", val)

    if variant in ("alloc:main", "alloc:radio"):
        chosen = main if variant == "alloc:main" else radio
        arg = "main" if variant == "alloc:main" else "radio"
        if chosen is None:
            raise LibError(f"{variant} requires the {arg}= product name")
        if chosen not in products:
            raise LibError(f"{arg} product {chosen!r} is not in products")
        return {p: (1.0 if p == chosen else 0.0) for p in products}

    if variant == "alloc:value":
        weights = {}
        for name, (qty, val) in products.items():
            if val is None:
                raise LibError(f"alloc:value needs a unit_value for {name!r}")
            weights[name] = qty * val
    else:
        weights = {name: qty for name, (qty, _) in products.items()}
    total = math.fsum(weights.values())
    if total <= 0:
        raise LibError(f"{variant}: denominator is 0")
    return {p: w / total for p, w in weights.items()}


def split(bounds: Bounds, shares: Mapping[str, float]) -> dict[str, Bounds]:
    """Apply each (exact) share to ``bounds`` (LIB_SPEC §2.2)."""
    return {p: bounds.scale(s) for p, s in shares.items()}


def attribution_share(
    cap_added: Mapping[str, float], intensity: Mapping[str, float], production: float
) -> float:
    """Share of a commodity's world production demanded by new capacity (METHODS §10.2).

    $\\sigma_c=\\sum_t C_t I_{t,c}/Q_c$ with C in GW, I in t/GW, Q in t.
    """
    if not isinstance(production, (int, float)) or not math.isfinite(production) or production <= 0:
        raise LibError(f"production must be a finite number > 0, got {production!r}")
    terms = []
    for tech, cap in cap_added.items():
        _finite_nonneg(f"cap_added[{tech!r}]", cap)
        if tech in intensity:
            _finite_nonneg(f"intensity[{tech!r}]", intensity[tech])
            terms.append(cap * intensity[tech])
    sigma = math.fsum(terms) / production
    if sigma > 1 + _SIGMA_TOL:
        raise LibError(f"attribution share {sigma:.6g} > 1: demand exceeds world production")
    return min(sigma, 1.0)


def variant_token(allocation_variant: str, default_token: str = "alloc:value") -> str:
    """Map a master ``allocation_variant`` to an ``alloc:*`` token (LIB_SPEC §7.3)."""
    mapping = {"default": default_token, "bound_main": "alloc:main", "bound_radio": "alloc:radio"}
    if allocation_variant not in mapping:
        raise LibError(f"unknown allocation_variant {allocation_variant!r}")
    return mapping[allocation_variant]
