"""Shared compare/write logic for the stream CLIs (LIB_SPEC §11.5).

The four stream modules differ only in their constants, so the diff and
``--write`` behaviour for ``<stream>.csv.gz`` outputs lives here once.
Gzip output is compared by decompressed content, never by compressed bytes,
because compressed bytes are only stable for one zlib build (LIB_SPEC §11.1).
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from pipeline.lib import LibError
from pipeline.lib.io import first_difference, read_bytes, resolve_stream_file
from pipeline.lib.rows import write_master

Target = tuple[Path, Sequence[Mapping[str, Any]]]


def _plain_sibling(gz: Path) -> Path:
    return gz.with_name(gz.name[: -len(".gz")])


def both_forms_error(root: Path, rels: Iterable[Path]) -> str | None:
    """Message naming both files if any target exists in both forms, else None."""
    for rel in rels:
        gz = root / rel
        plain = _plain_sibling(gz)
        if gz.is_file() and plain.is_file():
            return (
                f"error: both {rel.as_posix()} and {_plain_sibling(rel).as_posix()} exist; "
                "remove the plain file or run with --write"
            )
    return None


def diff_mode_preflight(root: Path, rels: Iterable[Path]) -> int | None:
    """Exit code 2 (after printing the error) when a target is ambiguous."""
    message = both_forms_error(root, rels)
    if message is None:
        return None
    print(message, file=sys.stderr)
    return 2


def finish(
    root: Path,
    targets: Sequence[Target],
    log: Sequence[Mapping[str, Any]],
    log_output: Path,
    write_log: Callable[[Sequence[Mapping[str, Any]], Path], None],
    write: bool,
) -> int:
    """Write (``--write``) or compare the outputs; returns the process exit code."""
    with tempfile.TemporaryDirectory() as scratch:
        fresh: list[tuple[Path, Path]] = []
        for n, (rel, rows) in enumerate(targets):
            path = Path(scratch) / f"{n}.csv.gz"
            write_master(rows, path)
            fresh.append((rel, path))
        fresh_log = Path(scratch) / "log.csv"
        write_log(log, fresh_log)

        if write:
            return _write(root, fresh, log, log_output, write_log)
        return _diff(root, fresh, fresh_log, log_output)


def _write(root, fresh, log, log_output, write_log) -> int:
    notes = []
    for rel, path in fresh:
        target = root / rel
        plain = _plain_sibling(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        content = read_bytes(path)
        unchanged = False
        if target.is_file():
            try:
                unchanged = read_bytes(target) == content
            except LibError:
                unchanged = False  # corrupt: rewrite
        if not unchanged:
            shutil.copyfile(path, target)
        removed = plain.exists()
        if removed:
            plain.unlink()
        flags = []
        if unchanged:
            flags.append("(unchanged)")
        if removed:
            flags.append(f"(removed legacy {plain.name})")
        notes.append(" ".join([rel.as_posix(), *flags]))
    (root / log_output).parent.mkdir(parents=True, exist_ok=True)
    write_log(log, root / log_output)
    print("written: " + ", ".join(notes) + f", {log_output.as_posix()}")
    return 0


def _diff(root, fresh, fresh_log, log_output) -> int:
    differing = []
    for rel, path in fresh:
        committed = root / rel
        name = rel.as_posix()
        try:
            found = resolve_stream_file(committed.parent, committed.name[: -len(".csv.gz")])
        except LibError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        if found is None:
            print(f"{name}: missing", file=sys.stderr)
        elif found != committed:
            print(f"{name}: legacy plain form, run --write to migrate", file=sys.stderr)
        else:
            try:
                line = first_difference(read_bytes(committed), read_bytes(path))
            except LibError as exc:
                print(f"{name}: unreadable: {exc}", file=sys.stderr)
            else:
                if line is None:
                    continue
                print(f"{name}: first difference at line {line}", file=sys.stderr)
        differing.append(name)
    committed_log = root / log_output
    if not committed_log.is_file():
        print(f"{log_output.as_posix()}: missing", file=sys.stderr)
        differing.append(log_output.as_posix())
    elif committed_log.read_bytes() != fresh_log.read_bytes():
        line = first_difference(committed_log.read_bytes(), fresh_log.read_bytes())
        print(f"{log_output.as_posix()}: first difference at line {line}", file=sys.stderr)
        differing.append(log_output.as_posix())
    if differing:
        print("differs from the committed file(s): " + ", ".join(differing), file=sys.stderr)
        return 1
    print("outputs identical to the committed files")
    return 0
