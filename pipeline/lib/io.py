"""Reading CSV tables with the validator's coercion (SCHEMA §6.5; LIB_SPEC §5)."""

from __future__ import annotations

import csv
import logging
import os

from ..validate import _CONVERTERS, MASTER_COLUMNS, MASTER_NULLABLE, _CoercionError
from . import LibError

logger = logging.getLogger(__name__)

# Typed columns across master, activity, factor and commodity-factor tables
# (the validator's per-table type maps, merged by column name).
COLUMN_TYPES: dict[str, str] = {
    "year": "int",
    "year_from": "int",
    "year_to": "int",
    "value_low": "float",
    "value_central": "float",
    "value_high": "float",
    "below_detection": "bool",
    "embedded_fuel": "bool",
    "source_ids": "list",
    "factor_ids": "list",
}


def read_table(path: str | os.PathLike) -> list[dict]:
    """Read a UTF-8 CSV: empty cell -> ``None``, typed columns parsed.

    Raises ``LibError`` naming the file, row and column for unreadable files or
    cells that fail to parse.
    """
    try:
        with open(path, encoding="utf-8-sig", newline="") as handle:
            records = list(csv.reader(handle, strict=True))
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        raise LibError(f"cannot read {os.fspath(path)}: {exc}") from exc
    if not records:
        raise LibError(f"{os.fspath(path)}: file is empty (no header row)")
    header = [h.strip() for h in records[0]]
    is_master = header == MASTER_COLUMNS
    out: list[dict] = []
    for lineno, cells in enumerate(records[1:], start=2):
        if not any(c.strip() for c in cells):
            continue
        cells = (cells + [""] * len(header))[: len(header)]
        row: dict = {}
        for col, raw in zip(header, cells, strict=True):
            text = raw.strip()
            if not text:
                if is_master and col not in MASTER_NULLABLE:
                    raise LibError(
                        f"{os.fspath(path)}:{lineno}: column {col}: empty cell in a required column"
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
                raise LibError(f"{os.fspath(path)}:{lineno}: column {col}: {exc}") from exc
        out.append(row)
    return out
