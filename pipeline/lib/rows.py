"""Master-table rows: construction and deterministic writing (SCHEMA §3; LIB_SPEC §4)."""

from __future__ import annotations

import csv
import logging
import os
from collections.abc import Iterable, Mapping
from typing import Any

from ..validate import KEY_COLUMNS
from ..validate import MASTER_COLUMNS as _VALIDATOR_COLUMNS
from . import LibError
from .bounds import Bounds

logger = logging.getLogger(__name__)

MASTER_COLUMNS: list[str] = list(_VALIDATOR_COLUMNS)
REQUIRED_FIELDS = (
    "year",
    "stream",
    "substream",
    "stage",
    "country",
    "group",
    "tier",
    "quantity",
    "unit",
    "basis",
    "source_ids",
)
_LIST_FIELDS = ("source_ids", "factor_ids", "allocation_rule")
_BOUND_FIELDS = ("value_low", "value_central", "value_high")
_DEFAULTS: dict[str, Any] = {
    "allocation_variant": "default",
    "embedded_fuel": False,
    "allocation_rule": "none",
}


def _join(value: Any) -> Any:
    if isinstance(value, (list, tuple)):
        return ";".join(str(v) for v in value)
    return value


def make_row(*, bounds: Bounds, **fields: Any) -> dict:
    """Build a master row dict with exactly ``MASTER_COLUMNS`` as keys."""
    unknown = sorted((set(fields) - set(MASTER_COLUMNS)) | (set(fields) & set(_BOUND_FIELDS)))
    if unknown:
        raise LibError(f"unknown or bounds-derived field(s): {unknown}")
    missing = [f for f in REQUIRED_FIELDS if fields.get(f) is None]
    if missing:
        raise LibError(f"missing required field(s): {missing}")
    row: dict = {c: _DEFAULTS.get(c) for c in MASTER_COLUMNS}
    row.update({k: v for k, v in fields.items() if v is not None or k in row})
    for k in _LIST_FIELDS:
        row[k] = _join(row[k])
    row["value_low"], row["value_central"], row["value_high"] = (
        bounds.low,
        bounds.central,
        bounds.high,
    )
    if fields.get("below_detection") is None:
        row["below_detection"] = bounds.nd_floored
    for k in ("allocation_variant", "embedded_fuel"):
        if row[k] is None:
            row[k] = _DEFAULTS[k]
    return row


def _sort_key(row: Mapping[str, Any]) -> tuple:
    # None sorts first within each column.
    return tuple((0,) if row.get(c) is None else (1, row[c]) for c in KEY_COLUMNS)


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return format(value, ".6g")
    return str(_join(value))


def write_master(rows: Iterable[Mapping[str, Any]], path: str | os.PathLike) -> None:
    """Write rows sorted by the SCHEMA §3 unique key; byte-identical across runs."""
    rows = list(rows)
    for i, r in enumerate(rows):
        extra = sorted(set(r) - set(MASTER_COLUMNS))
        if extra:
            raise LibError(f"row {i}: unknown column(s) {extra}")
    seen: set[tuple] = set()
    for r in rows:
        key = tuple(r.get(c) for c in KEY_COLUMNS)
        if key in seen:
            raise LibError(f"duplicate master key: {dict(zip(KEY_COLUMNS, key, strict=True))}")
        seen.add(key)
    try:
        ordered = sorted(rows, key=_sort_key)
    except TypeError as exc:
        raise LibError(f"cannot order rows (mixed types in a key column): {exc}") from exc
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(MASTER_COLUMNS)
        for r in ordered:
            writer.writerow([_cell(r.get(c)) for c in MASTER_COLUMNS])
