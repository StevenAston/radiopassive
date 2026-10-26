"""Factor-registry lookup and application (SCHEMA §4.7, §4.9; METHODS §11.1; LIB_SPEC §3)."""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from typing import Any

from . import LibError
from .bounds import Bounds, product

logger = logging.getLogger(__name__)

WORLD_REGION = "XWL"
GWA_TWH = 8.766  # 1 GW·a in TWh, a = 365.25 d (exact)


def select(factors: Iterable[Mapping[str, Any]], *, year: int, region: str, **match: Any) -> dict:
    """Pick the single factor row valid for ``year`` and ``region``.

    An exact-region row beats an ``XWL`` row. Raises ``LibError`` when nothing
    matches or the registry is ambiguous at the winning precedence level.
    """
    exact: list[Mapping[str, Any]] = []
    world: list[Mapping[str, Any]] = []
    for row in factors:
        yf, yt = row.get("year_from"), row.get("year_to")
        if yf is None or yt is None or not (yf <= year <= yt):
            continue
        if any(row.get(k) != v for k, v in match.items()):
            continue
        if row.get("region") == region:
            exact.append(row)
        elif row.get("region") == WORLD_REGION:
            world.append(row)
    winners = exact or world
    desc = f"year={year}, region={region!r}, match={match!r}"
    if not winners:
        raise LibError(f"no factor row for {desc}")
    if len(winners) > 1:
        ids = [w.get("factor_id") for w in winners]
        raise LibError(f"ambiguous factor rows for {desc}: {ids!r}")
    return dict(winners[0])


def _driver_conversion(driver_unit: str, per_unit: str) -> float:
    """Multiplier taking a driver in ``driver_unit`` to ``per_unit``."""
    if driver_unit == per_unit:
        return 1.0
    if driver_unit == "TWh" and per_unit == "GWa":
        return 1.0 / GWA_TWH
    if driver_unit == "GWa" and per_unit == "TWh":
        return GWA_TWH
    raise LibError(f"unit mismatch: driver in {driver_unit!r}, factor per {per_unit!r}")


def _parse_unit(unit: str) -> tuple[str, str | None]:
    """Return (kind, per_unit): kind is 'Bq', 'Bq/a' or '1'."""
    unit = (unit or "").strip()
    if unit == "1":
        return "1", None
    if unit.startswith("Bq/a per "):
        return "Bq/a", unit[len("Bq/a per ") :].strip()
    if unit.startswith("Bq/"):
        return "Bq", unit[len("Bq/") :].strip()
    raise LibError(f"unsupported factor unit {unit!r}")


def result_unit(driver_unit: str, factor_unit: str) -> str:
    """Unit of ``apply``'s result (LIB_SPEC §3.2, §7.9); raises on a mismatch."""
    kind, per = _parse_unit(factor_unit)
    if kind == "1":
        return driver_unit
    _driver_conversion(driver_unit, per)
    return kind


def apply(driver_value: Bounds, driver_unit: str, factor_row: Mapping[str, Any]) -> Bounds:
    """Multiply a driver by a factor (LIB_SPEC §3.2).

    Factor units: ``Bq/<u>`` (result Bq), ``Bq/a per <u>`` (Bq/a), or ``1``
    (result in the driver's unit). Only TWh <-> GWa is converted.
    """
    kind, per = _parse_unit(factor_row.get("unit"))
    conv = 1.0 if kind == "1" else _driver_conversion(driver_unit, per)
    try:
        # The row's own bounds are kept for non-detects (LIB_SPEC §7.6).
        factor = Bounds(
            factor_row["value_low"],
            factor_row["value_central"],
            factor_row["value_high"],
            nd_floored=bool(factor_row.get("below_detection")),
        )
    except (KeyError, TypeError) as exc:
        raise LibError(
            f"factor row {factor_row.get('factor_id')!r} lacks usable value_low/central/high: {exc}"
        ) from exc
    driver = driver_value if conv == 1.0 else driver_value.scale(conv)
    return product(driver, factor)
