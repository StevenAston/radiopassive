"""Reading CSV tables with the validator's coercion (SCHEMA §6.5; LIB_SPEC §5, §8.4)."""

from __future__ import annotations

import csv
import gzip
import io
import logging
import os
import zlib
from pathlib import Path

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


# Part of the on-disk format (LIB_SPEC §11.4): changing it changes every committed byte.
GZIP_LEVEL = 9


def gzip_bytes(data: bytes) -> bytes:
    """Deterministic gzip: level ``GZIP_LEVEL``, MTIME 0, no file name (LIB_SPEC §11.4).

    One-shot compression, so neither the clock, the path nor write chunking can
    change the output.
    """
    if not isinstance(data, bytes):
        raise LibError(f"gzip_bytes needs bytes, got {type(data).__name__}")
    return gzip.compress(data, compresslevel=GZIP_LEVEL, mtime=0)


def _path_name(path: object) -> str:
    if isinstance(path, bool) or not isinstance(path, (str, os.PathLike)):
        raise LibError(f"path must be a str or os.PathLike, got {path!r}")
    try:
        name = os.fspath(path)
    except TypeError as exc:
        raise LibError(f"path must be a str or os.PathLike, got {path!r}") from exc
    if not isinstance(name, str):  # bytes paths are not accepted
        raise LibError(f"path must be a str or os.PathLike, got {path!r}")
    return name


def read_bytes(path: str | os.PathLike) -> bytes:
    """Return the file's content: decompressed for a ``.gz`` path, raw otherwise."""
    name = _path_name(path)
    try:
        if name.endswith(".gz"):
            with gzip.open(name, "rb") as handle:
                data = handle.read()
            # gzip.open treats an empty file as an empty stream; the spec calls it corrupt.
            if os.path.getsize(name) == 0:
                raise LibError(f"cannot read {name}: empty file is not a gzip stream")
            return data
        with open(name, "rb") as handle:
            return handle.read()
    except (OSError, EOFError, zlib.error) as exc:
        raise LibError(f"cannot read {name}: {exc}") from exc


def first_difference(a: bytes, b: bytes) -> int | None:
    """1-based number of the first differing LF-terminated line (header is 1), or None."""
    if not isinstance(a, bytes) or not isinstance(b, bytes):
        raise LibError("first_difference needs bytes arguments")
    if a == b:
        return None
    la = a.split(b"\n")
    lb = b.split(b"\n")
    # Splitting on LF leaves a final fragment: empty if the data ends in LF, which
    # makes "missing final newline" and "extra lines" fall out as ordinary differences.
    for i in range(min(len(la), len(lb))):
        if la[i] != lb[i]:
            return i + 1
    return min(len(la), len(lb))


def resolve_stream_file(directory: str | os.PathLike, stream: str) -> Path | None:
    """Locate ``<stream>.csv.gz`` or ``<stream>.csv`` in ``directory`` (LIB_SPEC §11.4).

    Returns None when neither exists; raises ``LibError`` when both exist or
    either name is not a regular file.
    """
    _path_name(directory)
    base = Path(directory)
    gz, plain = base / f"{stream}.csv.gz", base / f"{stream}.csv"
    for candidate in (gz, plain):
        if candidate.is_dir():
            raise LibError(f"{candidate} is a directory, expected a file")
    has_gz, has_plain = gz.is_file(), plain.is_file()
    if has_gz and has_plain:
        raise LibError(f"both {gz} and {plain} exist; remove one (run the stream CLI with --write)")
    if has_gz:
        return gz
    if has_plain:
        return plain
    return None


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
        with (
            io.TextIOWrapper(io.BytesIO(read_bytes(name)), encoding="utf-8-sig", newline="")
            if name.endswith(".gz")
            else open(path, encoding="utf-8-sig", newline="")
        ) as handle:
            reader = csv.reader(handle, strict=True)
            records: list[tuple[int, list[str]]] = []
            previous_end = 0
            for cells in reader:
                records.append((previous_end + 1, cells))
                previous_end = reader.line_num
    except (OSError, EOFError, zlib.error, UnicodeDecodeError, csv.Error) as exc:
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
                # Factor-file substream and commodity ore_type are "" when empty so
                # select's exact equality works (LIB_SPEC §10.3, §12.3); never None.
                row[col] = "" if col in ("substream", "ore_type") else None
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
