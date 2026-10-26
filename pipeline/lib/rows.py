"""Master-table rows: construction and deterministic writing (SCHEMA §3; LIB_SPEC §4)."""

from __future__ import annotations

import csv
import logging
import math
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
_STRING_FIELDS = (
    "stream",
    "substream",
    "stage",
    "country",
    "group",
    "tier",
    "unit",
    "basis",
    "quantity",
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
    if not isinstance(bounds, Bounds):
        raise LibError(f"bounds must be a Bounds, got {bounds!r}")
    unknown = sorted((set(fields) - set(MASTER_COLUMNS)) | (set(fields) & set(_BOUND_FIELDS)))
    if unknown:
        raise LibError(f"unknown or bounds-derived field(s): {unknown}")
    missing = [f for f in REQUIRED_FIELDS if fields.get(f) is None]
    if missing:
        raise LibError(f"missing or None required field(s): {missing}")
    for f in _STRING_FIELDS:
        if not isinstance(fields[f], str):
            raise LibError(f"{f} must be a str, got {fields[f]!r}")
    if fields.get("embedded_fuel") is not None and not isinstance(fields["embedded_fuel"], bool):
        raise LibError(f"embedded_fuel must be a bool, got {fields['embedded_fuel']!r}")
    for f in ("source_ids", "factor_ids"):
        value = fields.get(f)
        if isinstance(value, (list, tuple)):
            for item in value:
                if not isinstance(item, str) or not item.strip():
                    raise LibError(f"{f} items must be non-blank strings, got {item!r}")
    year = fields["year"]
    if not isinstance(year, int) or isinstance(year, bool):
        raise LibError(f"year must be an int, got {year!r}")
    if fields["source_ids"] == [] or (
        isinstance(fields["source_ids"], str) and not fields["source_ids"].strip()
    ):
        raise LibError("source_ids must not be empty")

    row: dict = {c: _DEFAULTS.get(c) for c in MASTER_COLUMNS}
    row.update(fields)
    # An explicit None means "use the default" for these three columns.
    for k, default in _DEFAULTS.items():
        if row[k] is None:
            row[k] = default
    for k in _LIST_FIELDS:
        row[k] = _join(row[k])
    row["value_low"], row["value_central"], row["value_high"] = (
        bounds.low,
        bounds.central,
        bounds.high,
    )

    explicit = fields.get("below_detection")
    if explicit is None:
        row["below_detection"] = bounds.nd_floored
    else:
        if not isinstance(explicit, bool):
            raise LibError(f"below_detection must be a bool or None, got {explicit!r}")
        # SCHEMA §3: below_detection implies value_low == 0 (LIB_SPEC §8.2).
        if explicit and bounds.low > 0:
            raise LibError(f"below_detection=True requires value_low == 0, got {bounds.low!r}")
        if not explicit and bounds.nd_floored:
            raise LibError("below_detection=False contradicts bounds with nd_floored=True")
        row["below_detection"] = explicit
    return row


def _sort_key(row: Mapping[str, Any]) -> tuple:
    # None sorts first within each column, explicitly rather than as "falsy first".
    return tuple((0,) if row[c] is None else (1, row[c]) for c in KEY_COLUMNS)


def _cell(column: str, value: Any) -> str:
    if value is None:
        return ""
    if column in _BOUND_FIELDS:
        if isinstance(value, bool):
            raise LibError(f"column {column}: expected a number, got {value!r}")
        try:
            value = float(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise LibError(f"column {column}: expected a number, got {value!r}") from exc
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        if not math.isfinite(value):
            raise LibError(f"column {column}: value must be finite, got {value!r}")
        # + 0.0 turns -0.0 into 0.0 so "-0" is never written.
        return format(value + 0.0, ".6g")
    return str(_join(value))


def write_master(rows: Iterable[Mapping[str, Any]], path: str | os.PathLike) -> None:
    """Write rows sorted by the SCHEMA §3 unique key; byte-identical across runs."""
    try:
        rows = list(rows)
    except TypeError as exc:
        raise LibError(f"rows must be an iterable of mappings, got {rows!r}") from exc
    expected = set(MASTER_COLUMNS)
    for i, r in enumerate(rows):
        if not isinstance(r, Mapping):
            raise LibError(f"row {i}: expected a mapping, got {r!r}")
        extra = sorted(set(r) - expected)
        absent = sorted(expected - set(r))
        if extra or absent:
            raise LibError(f"row {i}: unknown column(s) {extra}, missing column(s) {absent}")
    seen: set[tuple] = set()
    for r in rows:
        key = tuple(r[c] for c in KEY_COLUMNS)
        try:
            duplicate = key in seen
        except TypeError as exc:
            raise LibError(f"unhashable value in key columns: {key!r}") from exc
        if duplicate:
            raise LibError(f"duplicate master key: {dict(zip(KEY_COLUMNS, key, strict=True))}")
        seen.add(key)
    try:
        ordered = sorted(rows, key=_sort_key)
    except TypeError as exc:
        raise LibError(f"cannot order rows (mixed types in a key column): {exc}") from exc
    # Format everything before opening the file so a bad cell leaves no partial output.
    body = [[_cell(c, r[c]) for c in MASTER_COLUMNS] for r in ordered]
    if isinstance(path, bool) or not isinstance(path, (str, os.PathLike)):
        # open() would treat an int as a file descriptor.
        raise LibError(f"path must be a str or os.PathLike, got {path!r}")
    try:
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(MASTER_COLUMNS)
            writer.writerows(body)
    except (OSError, TypeError, ValueError) as exc:
        raise LibError(f"cannot write {path!r}: {exc}") from exc
