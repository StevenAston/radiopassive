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


MATCH_KEYS = frozenset(
    {
        "stream",
        "stage",
        "group",
        "tier",
        "route",
        "residue_type",
        "driver_series",
        "commodity",
        "component",
        "allocation_variant",
    }
)


def select(factors: Iterable[Mapping[str, Any]], *, year: int, region: str, **match: Any) -> dict:
    """Pick the single factor row valid for ``year`` and ``region``.

    An exact-region row beats an ``XWL`` row. Raises ``LibError`` when nothing
    matches or the registry is ambiguous at the winning precedence level.
    """
    if not isinstance(year, int) or isinstance(year, bool):
        raise LibError(f"year must be an int, got {year!r}")
    if not isinstance(region, str):
        raise LibError(f"region must be a string, got {region!r}")
    # An unknown key would otherwise silently match nothing (or everything).
    unknown = sorted(set(match) - MATCH_KEYS)
    if unknown:
        raise LibError(f"unknown match key(s) {unknown}; allowed: {sorted(MATCH_KEYS)}")
    try:
        rows = list(factors)
    except TypeError as exc:
        raise LibError(f"factors must be an iterable of mappings, got {factors!r}") from exc
    for row in rows:
        if not isinstance(row, Mapping):
            raise LibError(f"factor rows must be mappings, got {row!r}")

    exact: list[Mapping[str, Any]] = []
    world: list[Mapping[str, Any]] = []
    for row in rows:
        yf, yt = row.get("year_from"), row.get("year_to")
        if yf is None or yt is None:
            continue
        if not all(isinstance(v, int) and not isinstance(v, bool) for v in (yf, yt)):
            raise LibError(f"factor {row.get('factor_id')!r}: year_from/year_to must be ints")
        if not (yf <= year <= yt):
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
    if not isinstance(unit, str):
        raise LibError(f"unit must be a string, got {unit!r}")
    unit = unit.strip()
    if unit == "1":
        return "1", None
    if unit.startswith("Bq/a per "):
        return "Bq/a", unit[len("Bq/a per ") :].strip()
    if unit.startswith("Bq/"):
        return "Bq", unit[len("Bq/") :].strip()
    raise LibError(f"unsupported factor unit {unit!r}")


def result_unit(driver_unit: str, factor_unit: str) -> str:
    """Unit of ``apply``'s result (LIB_SPEC §3.2, §7.9); raises on a mismatch."""
    if not isinstance(driver_unit, str):
        raise LibError(f"driver unit must be a string, got {driver_unit!r}")
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
    if not isinstance(driver_value, Bounds):
        raise LibError(f"driver value must be a Bounds, got {driver_value!r}")
    if not isinstance(driver_unit, str):
        raise LibError(f"driver unit must be a string, got {driver_unit!r}")
    if not isinstance(factor_row, Mapping):
        raise LibError(f"factor row must be a mapping, got {factor_row!r}")
    kind, per = _parse_unit(factor_row.get("unit"))
    conv = 1.0 if kind == "1" else _driver_conversion(driver_unit, per)
    name = factor_row.get("factor_id")
    nd = factor_row.get("below_detection")
    if nd is not None and not isinstance(nd, bool):
        raise LibError(f"factor row {name!r}: below_detection must be a bool or None, got {nd!r}")
    try:
        # The row's own bounds are kept for non-detects (LIB_SPEC §7.6); a flag
        # on a row whose low is positive is rejected by Bounds (§8.1).
        factor = Bounds(
            factor_row["value_low"],
            factor_row["value_central"],
            factor_row["value_high"],
            nd_floored=bool(nd),
        )
    except KeyError as exc:
        raise LibError(f"factor row {name!r} lacks {exc}") from exc
    driver = driver_value if conv == 1.0 else driver_value.scale(conv)
    return product(driver, factor)


def master_unit(result_unit: str, kind: str) -> str:
    """Master-table ``unit`` for a result unit (LIB_SPEC §8.5).

    ``kind`` is ``"flow"`` or ``"stock"``; the caller decides, the library never guesses.
    """
    if not isinstance(result_unit, str):
        raise LibError(f"result unit must be a string, got {result_unit!r}")
    if not isinstance(kind, str) or kind not in ("flow", "stock"):
        raise LibError(f"kind must be 'flow' or 'stock', got {kind!r}")
    if kind == "flow" and result_unit == "Bq":
        return "Bq/a"
    if kind == "stock" and result_unit == "Bq/a":
        raise LibError("a stock cannot have unit 'Bq/a'")
    return result_unit
