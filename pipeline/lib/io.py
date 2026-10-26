"""Reading CSV tables with the validator's coercion (SCHEMA §6.5; LIB_SPEC §5, §8.4)."""

from __future__ import annotations

import csv
import logging
import os

from ..validate import (
    _CONVERTERS,
    MASTER_COLUMNS,
    MASTER_NULLABLE,
    MASTER_TYPES,
    _CoercionError,
)
from . import LibError

logger = logging.getLogger(__name__)

# Typed columns across every table the validator knows, merged by column name.
# The master map is the validator's own; the others mirror the inline maps in
# validate.py (activity, baselines, factors, commodity_factors, events,
# countries, sources, reference_bands, residue_types). A column name has the
# same type in every table that uses it, so a single map is unambiguous.
COLUMN_TYPES: dict[str, str] = {
    **MASTER_TYPES,
    "allocation_rule": "list",  # LIB_SPEC §8.4; the validator keeps it as text
    "year_from": "int",
    "year_to": "int",
    "valid_from": "int",
    "valid_to": "int",
    "rank": "int",
    "lat": "float",
    "lon": "float",
    "mass_t": "float",
    "activity_low_bq": "float",
    "activity_central_bq": "float",
    "activity_high_bq": "float",
    "rel_low": "float",
    "rel_high": "float",
    "is_accident": "bool",
    "military": "bool",
    "to_tiers": "list",
    "applies_to": "list",
    "streams": "list",
}
for _param in ("epsilon_rn222", "epsilon_rn220", "seepage_per_a"):
    for _side in ("low", "central", "high"):
        COLUMN_TYPES[f"{_param}_{_side}"] = "float"


def read_table(path: str | os.PathLike) -> list[dict]:
    """Read a UTF-8 CSV: empty cell -> ``None``, typed columns parsed.

    Cells are whitespace-stripped, as the validator does. Raises ``LibError``
    naming the file, line and column for unreadable files, ragged rows,
    duplicate headers, cells that fail to parse, and (for master tables) empty
    cells in non-nullable columns.
    """
    if not isinstance(path, (str, os.PathLike)):  # open() would accept an int fd
        raise LibError(f"path must be a str or os.PathLike, got {path!r}")
    try:
        name = os.fspath(path)
    except TypeError as exc:
        raise LibError(f"path must be a str or os.PathLike, got {path!r}") from exc
    if not isinstance(name, str):  # bytes paths are not accepted
        raise LibError(f"path must be a str or os.PathLike, got {path!r}")
    try:
        with open(path, encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle, strict=True)
            records: list[tuple[int, list[str]]] = []
            previous_end = 0
            for cells in reader:
                records.append((previous_end + 1, cells))
                previous_end = reader.line_num
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        raise LibError(f"cannot read {name}: {exc}") from exc
    if not records:
        raise LibError(f"{name}: file is empty (no header row)")

    header = [h.strip() for h in records[0][1]]
    for i, col in enumerate(header):
        if col in header[:i]:
            raise LibError(f"{name}:1: duplicate header column {col!r}")
    is_master = header == list(MASTER_COLUMNS)

    out: list[dict] = []
    for lineno, cells in records[1:]:
        if len(cells) <= 1 and not any(c.strip() for c in cells):
            continue  # blank line
        if len(cells) != len(header):
            raise LibError(
                f"{name}:{lineno}: row has {len(cells)} cells, header has {len(header)}"
            )
        row: dict = {}
        for col, raw in zip(header, cells, strict=True):
            text = raw.strip()
            if not text:
                if is_master and col not in MASTER_NULLABLE:
                    raise LibError(
                        f"{name}:{lineno}: column {col}: empty cell in a required column"
                    )
                row[col] = None
                continue
            kind = COLUMN_TYPES.get(col, "str")
            if kind == "str":
                row[col] = text
                continue
            try:
                row[col] = _CONVERTERS[kind](text)
            except _CoercionError as exc:
                raise LibError(f"{name}:{lineno}: column {col}: {exc}") from exc
        out.append(row)
    return out
