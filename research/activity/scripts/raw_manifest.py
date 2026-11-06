"""Manifest of the git-ignored raw inputs (D72; docs/DATA_ARCHIVE.md section 4).

Pins the exact bytes of every ignored, untracked file under
``research/activity/raw`` and ``import`` as ``path,size,sha256,fetched`` rows,
so a commit names the raw files it was built from.

    python research/activity/scripts/raw_manifest.py write [--root DIR] [--manifest PATH] [--include DIR ...] [--date YYYY-MM-DD]
    python research/activity/scripts/raw_manifest.py check [--root DIR] [--manifest PATH] [--include DIR ...]

Exit codes: 0 success / no differences, 1 differences (check only), 2 usage
error, not a git work tree, or a missing or malformed manifest.

Standard library plus the ``git`` executable only; no network, and it never
runs zpaqfranz.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HEADER = ["path", "size", "sha256", "fetched"]
DEFAULT_MANIFEST = "research/activity/raw/MANIFEST.csv"
DEFAULT_INCLUDES = ("research/activity/raw", "import")
_SHA_RE = re.compile(r"[0-9a-f]{64}")
_CHUNK = 1 << 20


class UsageError(Exception):
    """Reported on stderr with exit code 2."""


def _git(root: Path, *args: str) -> bytes:
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, check=False
        )
    except FileNotFoundError as exc:
        raise UsageError("git executable not found") from exc
    except OSError as exc:
        raise UsageError(f"cannot run git: {exc}") from exc
    if proc.returncode != 0:
        detail = proc.stderr.decode("utf-8", "replace").strip()
        raise UsageError(f"git {' '.join(args)} failed: {detail}")
    return proc.stdout


def _split_z(raw: bytes) -> list[str]:
    try:
        return [p.decode("utf-8") for p in raw.split(b"\0") if p]
    except UnicodeDecodeError as exc:
        raise UsageError(f"file name is not valid UTF-8: {exc}") from exc


def _manifest_rel(root: Path, manifest: Path) -> str | None:
    try:
        return manifest.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return None


def _list_files(root: Path, includes: list[str], skip: set[str], flags: list[str]) -> list[str]:
    out = _git(root, "ls-files", "--others", *flags, "--exclude-standard", "-z", "--", *includes)
    return sorted(p for p in set(_split_z(out)) if p not in skip)


def _hash(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with open(path, "rb") as handle:
        while chunk := handle.read(_CHUNK):
            size += len(chunk)
            digest.update(chunk)
    return size, digest.hexdigest()


def _scan(root: Path, includes: list[str], skip: set[str]) -> dict[str, tuple[int, str]]:
    found: dict[str, tuple[int, str]] = {}
    for rel in _list_files(root, includes, skip, ["--ignored"]):
        full = root / rel
        if full.is_symlink():
            print(f"skipped symlink {rel}", file=sys.stderr)
            continue
        if not full.is_file():
            continue  # vanished between listing and hashing
        found[rel] = _hash(full)
    return found


def _read_manifest(path: Path) -> dict[str, tuple[int, str, str]]:
    """Parse and validate the manifest; raises UsageError naming the line."""
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise UsageError(f"cannot read manifest {path}: {exc}") from exc
    if b"\r" in raw:
        raise UsageError(f"{path}: CR found; the manifest must use LF line endings")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UsageError(f"{path}: not valid UTF-8: {exc}") from exc
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    if not lines:
        raise UsageError(f"{path}:1: empty manifest (no header)")
    rows: dict[str, tuple[int, str, str]] = {}
    previous: str | None = None
    try:
        parsed = list(csv.reader(lines, strict=True))
    except csv.Error as exc:
        raise UsageError(f"{path}: malformed CSV: {exc}") from exc
    if len(parsed) != len(lines):
        raise UsageError(f"{path}: a row spans several lines")
    if parsed[0] != HEADER:
        raise UsageError(f"{path}:1: header must be {','.join(HEADER)}")
    for lineno, cells in enumerate(parsed[1:], start=2):
        where = f"{path}:{lineno}"
        if len(cells) != len(HEADER):
            raise UsageError(f"{where}: expected {len(HEADER)} fields, got {len(cells)}")
        name, size_text, digest, fetched = cells
        if not name:
            raise UsageError(f"{where}: empty path")
        if not re.fullmatch(r"[0-9]+", size_text):
            raise UsageError(f"{where}: size must be a non-negative decimal integer")
        if not _SHA_RE.fullmatch(digest):
            raise UsageError(f"{where}: sha256 must be 64 lowercase hex characters")
        try:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", fetched):
                raise ValueError
            dt.date.fromisoformat(fetched)
        except ValueError as exc:
            raise UsageError(f"{where}: fetched must be a YYYY-MM-DD date") from exc
        if name in rows:
            raise UsageError(f"{where}: duplicate path {name}")
        if previous is not None and name < previous:
            raise UsageError(f"{where}: rows are not sorted by path")
        previous = name
        rows[name] = (int(size_text), digest, fetched)
    return rows


def _differences(
    current: dict[str, tuple[int, str]], recorded: dict[str, tuple[int, str, str]]
) -> list[tuple[str, str]]:
    diffs = []
    for name in sorted(set(current) | set(recorded)):
        if name not in recorded:
            diffs.append(("added", name))
        elif name not in current:
            diffs.append(("missing", name))
        elif current[name] != recorded[name][:2]:
            diffs.append(("changed", name))
    return diffs


def _context(args: argparse.Namespace) -> tuple[Path, Path, list[str], set[str]]:
    root = Path(args.root)
    if not root.is_dir():
        raise UsageError(f"--root {root} is not a directory")
    inside = _git(root, "rev-parse", "--is-inside-work-tree").strip()
    if inside != b"true":
        raise UsageError(f"{root} is not a git work tree")
    manifest = Path(args.manifest) if args.manifest else root / DEFAULT_MANIFEST
    includes = [i.strip("/\\").replace("\\", "/") for i in (args.include or DEFAULT_INCLUDES)]
    skip = {DEFAULT_MANIFEST}
    own = _manifest_rel(root, manifest)
    if own:
        skip.add(own)
    return root, manifest, includes, skip


def _cmd_check(args: argparse.Namespace) -> int:
    root, manifest, includes, skip = _context(args)
    if not manifest.is_file():
        raise UsageError(f"manifest not found: {manifest}")
    recorded = _read_manifest(manifest)
    current = _scan(root, includes, skip)
    for rel in _list_files(root, includes, skip, []):
        # --others without --ignored lists untracked files that are not ignored.
        print(f"untracked-not-ignored {rel}", file=sys.stderr)
    diffs = _differences(current, recorded)
    for kind, name in diffs:
        print(f"{kind} {name}")
    if diffs:
        counts = {k: sum(1 for kind, _ in diffs if kind == k) for k in ("added", "changed", "missing")}
        print(f"check: {counts['added']} added, {counts['changed']} changed, {counts['missing']} missing")
        return 1
    print(f"check: OK ({len(current)} files)")
    return 0


def _cmd_write(args: argparse.Namespace) -> int:
    root, manifest, includes, skip = _context(args)
    if args.date is not None:
        try:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.date):
                raise ValueError
            dt.date.fromisoformat(args.date)
        except ValueError as exc:
            raise UsageError("--date must be YYYY-MM-DD") from exc
    today = args.date or dt.datetime.now(dt.timezone.utc).date().isoformat()
    recorded = _read_manifest(manifest) if manifest.exists() else {}
    current = _scan(root, includes, skip)

    rows = []
    for name in sorted(current):
        size, digest = current[name]
        old = recorded.get(name)
        # Only the hash recorded in the existing manifest counts (DATA_ARCHIVE 4.2).
        fetched = old[2] if old is not None and old[1] == digest else today
        rows.append([name, str(size), digest, fetched])

    manifest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=manifest.parent, prefix=".manifest-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(HEADER)
            writer.writerows(rows)
        os.replace(tmp_name, manifest)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    for kind, name in _differences(current, recorded):
        print(f"{kind} {name}")
    print(f"{len(rows)} files, {sum(s for s, _ in current.values())} bytes")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="raw_manifest.py", description=__doc__.split("\n\n")[0])
    parser.add_argument("command", choices=("write", "check"))
    parser.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parents[3]),
        help="git work tree (default: the repository containing this script)",
    )
    parser.add_argument("--manifest", help=f"manifest path (default: <root>/{DEFAULT_MANIFEST})")
    parser.add_argument(
        "--include",
        action="append",
        metavar="DIR",
        help="repo-relative directory; repeatable (default: research/activity/raw and import)",
    )
    parser.add_argument("--date", help="override today's UTC date (write only), YYYY-MM-DD")
    args = parser.parse_args(argv)
    if args.command == "check" and args.date is not None:
        parser.error("--date applies to write only")
    try:
        return _cmd_check(args) if args.command == "check" else _cmd_write(args)
    except UsageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
