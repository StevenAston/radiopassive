"""Spec-blind validator tests for gzipped stream outputs (D72, LIB_SPEC 11.6 / 11.8 F, SCHEMA v2.5).

Written from docs/LIB_SPEC.md section 11 and docs/SCHEMA.md only. The gzip fixtures are built with the
standard library (never with pipeline.lib), as the validator must not depend on the library.

Mapping to LIB_SPEC 11.8 F
--------------------------
F1  TestSameIssuesAsPlain          (default discovery and explicit master_files)
F2  TestSameIssuesAsPlain, TestIssueNames
F3  TestCorruptGzip
F4  TestBothFormsPresent           (F04 once per pair, row None, file = the .csv.gz; explicit list: no F04)
F5  TestCrossFile
F6  TestPre1950
F7  TestCli

Ambiguities noted (not asserted beyond the stated reading)
----------------------------------------------------------
A1. (Settled by LIB_SPEC 11.11 item 2: F03 exactly.) Formerly open: a zero-byte .gz file; LIB_SPEC said only "not a valid gzip stream" is F03. Python's gzip reads a
    zero-byte file as empty content, so the code could be F01 (no header) or F03. Only "a file-level
    issue (F01/F02/F03) and no row issues" is asserted.
A2. Whether F04 is reported when the .csv and .csv.gz of a pair are in *different* directories: not
    applicable (discovery is data/streams only).
"""
from __future__ import annotations

import csv
import gzip
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from pipeline.validate import validate

TESTS_DIR = Path(__file__).resolve().parent
FIXTURES = TESTS_DIR / "fixtures"
REAL_ROOT = TESTS_DIR.parents[1]


# ------------------------------------------------------------------------------------------ helpers
def _read_fixture():
    with open(FIXTURES / "valid_rows.csv", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return list(reader.fieldnames), list(reader)


HEADER, VALID_ROWS = _read_fixture()


def vrow(n, **changes):
    row = dict(VALID_ROWS[n - 1])
    row.update({k: str(v) for k, v in changes.items()})
    return row


def csv_bytes(rows) -> bytes:
    import io

    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, fieldnames=HEADER, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue().encode("utf-8")


def gz(data: bytes) -> bytes:
    return gzip.compress(data, 9, mtime=0)


def put(root: Path, rel: str, rows=None, *, raw: bytes | None = None, compress: bool | None = None) -> str:
    """Write a master file under root. Compression follows the suffix unless `compress` says otherwise."""
    p = Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    data = raw if raw is not None else csv_bytes(rows)
    if compress is None:
        compress = rel.endswith(".gz")
    p.write_bytes(gz(data) if compress else data)
    return rel


def describe(issues):
    return "\n".join(f"  {i.file}:{i.row}: {i.rule} {i.message}" for i in issues) or "  (no issues)"


def key(issues, rename=None):
    out = []
    for i in issues:
        f = i.file
        if rename:
            f = rename.get(f, f)
        out.append((f, i.row, i.rule))
    return out


def run_cli(args, cwd):
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(REAL_ROOT), env.get("PYTHONPATH")]))
    return subprocess.run(
        [sys.executable, "-m", "pipeline.validate", *[str(a) for a in args]],
        cwd=str(cwd), env=env, capture_output=True, text=True, timeout=180, check=False,
    )


BAD_ROWS = [vrow(1), vrow(2), vrow(7, unit="Bq"), vrow(10, value_low="9e30")]  # R02 and R03 style problems


# ------------------------------------------------------------------------------------------ F1, F2
class TestSameIssuesAsPlain:
    def test_valid_gz_is_clean_by_default_discovery(self, tmp_root):
        put(tmp_root, "data/streams/x.csv.gz", VALID_ROWS)
        issues = validate(tmp_root)
        assert issues == [], f"a valid gzipped stream must validate clean:\n{describe(issues)}"

    def test_valid_gz_is_clean_with_explicit_list(self, tmp_root):
        rel = put(tmp_root, "data/streams/x.csv.gz", VALID_ROWS)
        issues = validate(tmp_root, [rel])
        assert issues == [], describe(issues)

    @pytest.mark.parametrize("explicit", [False, True], ids=["default-discovery", "explicit-list"])
    def test_invalid_gz_gives_same_issues_as_plain_apart_from_file_name(self, tmp_root, explicit):
        put(tmp_root, "data/streams/x.csv", BAD_ROWS)
        plain = validate(tmp_root, ["data/streams/x.csv"] if explicit else None)
        assert plain, "set-up: the invalid rows should produce issues in plain form"
        (tmp_root / "data" / "streams" / "x.csv").unlink()

        put(tmp_root, "data/streams/x.csv.gz", BAD_ROWS)
        gzipped = validate(tmp_root, ["data/streams/x.csv.gz"] if explicit else None)
        assert key(gzipped) == key(plain, {"data/streams/x.csv": "data/streams/x.csv.gz"}), (
            f"plain:\n{describe(plain)}\ngz:\n{describe(gzipped)}")

    def test_invalid_rows_keep_gz_suffix_in_file_names(self, tmp_root):
        put(tmp_root, "data/streams/x.csv.gz", BAD_ROWS)
        issues = validate(tmp_root)
        assert issues
        assert {i.file for i in issues} == {"data/streams/x.csv.gz"}, describe(issues)


# ------------------------------------------------------------------------------------------ F3
class TestCorruptGzip:
    def _only_file_level(self, issues, rel, codes=("F03",)):
        mine = [i for i in issues if i.file == rel]
        assert mine, f"expected a file-level issue for {rel}:\n{describe(issues)}"
        assert {i.rule for i in mine} <= set(codes), describe(issues)
        assert all(i.row is None for i in mine), describe(issues)
        return mine

    def test_plain_text_named_gz_is_f03(self, tmp_root):
        rel = put(tmp_root, "data/streams/x.csv.gz", raw=csv_bytes(VALID_ROWS), compress=False)
        mine = self._only_file_level(validate(tmp_root), rel)
        assert {i.rule for i in mine} == {"F03"}

    def test_truncated_gz_is_f03_and_rows_not_validated(self, tmp_root):
        rel = "data/streams/x.csv.gz"
        good = gz(csv_bytes(BAD_ROWS))
        (tmp_root / rel).write_bytes(good[:-10])
        issues = validate(tmp_root)
        mine = self._only_file_level(issues, rel)
        assert {i.rule for i in mine} == {"F03"}
        assert all(i.file == rel for i in issues), "no issue may come from rows of the unreadable file"

    def test_corrupt_crc_is_f03(self, tmp_root):
        rel = "data/streams/x.csv.gz"
        good = bytearray(gz(csv_bytes(VALID_ROWS)))
        good[-8] ^= 0xFF  # CRC32 field
        (tmp_root / rel).write_bytes(bytes(good))
        mine = self._only_file_level(validate(tmp_root), rel)
        assert {i.rule for i in mine} == {"F03"}

    def test_random_bytes_are_f03(self, tmp_root):
        rel = "data/streams/x.csv.gz"
        (tmp_root / rel).write_bytes(b"\x1f\x8b\x08\x00garbage-garbage-garbage")
        mine = self._only_file_level(validate(tmp_root), rel)
        assert {i.rule for i in mine} == {"F03"}

    def test_gz_of_non_utf8_is_f03(self, tmp_root):
        rel = put(tmp_root, "data/streams/x.csv.gz", raw=b"year,stream\n\xff\xfe\xfa,coal\n")
        mine = self._only_file_level(validate(tmp_root), rel, codes=("F01", "F02", "F03"))
        assert "F03" in {i.rule for i in mine}, describe(mine)

    def test_zero_byte_gz_is_f03_exactly(self, tmp_root):  # LIB_SPEC 11.11 item 2
        rel = "data/streams/x.csv.gz"
        (tmp_root / rel).write_bytes(b"")
        mine = self._only_file_level(validate(tmp_root), rel)
        assert [(i.rule, i.row) for i in mine] == [("F03", None)], describe(mine)

    def test_corrupt_gz_does_not_stop_other_files_being_validated(self, tmp_root):
        (tmp_root / "data/streams/a.csv.gz").write_bytes(b"not gzip")
        put(tmp_root, "data/streams/b.csv", [vrow(7, unit="Bq")])
        issues = validate(tmp_root)
        assert any(i.rule == "F03" and i.file == "data/streams/a.csv.gz" for i in issues), describe(issues)
        assert any(i.file == "data/streams/b.csv" and i.rule == "R02" for i in issues), describe(issues)


# ------------------------------------------------------------------------------------------ F4
class TestBothFormsPresent:
    def test_default_discovery_gives_exactly_one_f04_and_reads_neither(self, tmp_root):
        put(tmp_root, "data/streams/x.csv", BAD_ROWS)
        put(tmp_root, "data/streams/x.csv.gz", BAD_ROWS)
        issues = validate(tmp_root)
        assert [(i.file, i.row, i.rule) for i in issues] == [("data/streams/x.csv.gz", None, "F04")], (
            "expected exactly one F04 against the .csv.gz and no row issues from either file:\n" + describe(issues))

    def test_f04_message_names_both_files(self, tmp_root):
        put(tmp_root, "data/streams/x.csv", VALID_ROWS)
        put(tmp_root, "data/streams/x.csv.gz", VALID_ROWS)
        (issue,) = validate(tmp_root)
        assert "x.csv.gz" in issue.message and re.search(r"x\.csv(?!\.gz)", issue.message), issue.message

    def test_identical_valid_pair_does_not_raise_x01(self, tmp_root):
        put(tmp_root, "data/streams/x.csv", VALID_ROWS)
        put(tmp_root, "data/streams/x.csv.gz", VALID_ROWS)
        assert {i.rule for i in validate(tmp_root)} == {"F04"}

    def test_one_f04_per_pair(self, tmp_root):
        for s in ("a", "b"):
            put(tmp_root, f"data/streams/{s}.csv", [vrow(7)])
            put(tmp_root, f"data/streams/{s}.csv.gz", [vrow(7)])
        issues = validate(tmp_root)
        assert sorted((i.file, i.rule) for i in issues) == [
            ("data/streams/a.csv.gz", "F04"), ("data/streams/b.csv.gz", "F04")], describe(issues)

    def test_other_single_form_streams_still_validated_beside_a_pair(self, tmp_root):
        put(tmp_root, "data/streams/x.csv", VALID_ROWS)
        put(tmp_root, "data/streams/x.csv.gz", VALID_ROWS)
        put(tmp_root, "data/streams/y.csv.gz", [vrow(7, unit="Bq")])
        issues = validate(tmp_root)
        assert {(i.file, i.rule) for i in issues} == {
            ("data/streams/x.csv.gz", "F04"), ("data/streams/y.csv.gz", "R02")}, describe(issues)

    def test_explicit_list_of_both_gives_no_f04(self, tmp_root):
        put(tmp_root, "data/streams/x.csv", VALID_ROWS)
        put(tmp_root, "data/streams/x.csv.gz", VALID_ROWS)
        issues = validate(tmp_root, ["data/streams/x.csv", "data/streams/x.csv.gz"])
        assert "F04" not in {i.rule for i in issues}, "an explicit list is taken literally (SCHEMA 6.5)"
        # Both files are then read: every key of the second duplicates the first (X01 on the later file).
        assert {i.file for i in issues if i.rule == "X01"} == {"data/streams/x.csv.gz"}, describe(issues)

    def test_explicit_single_form_of_a_pair_gives_no_f04(self, tmp_root):
        put(tmp_root, "data/streams/x.csv", VALID_ROWS)
        put(tmp_root, "data/streams/x.csv.gz", VALID_ROWS)
        assert validate(tmp_root, ["data/streams/x.csv.gz"]) == []


# ------------------------------------------------------------------------------------------ F5
class TestCrossFile:
    def test_x01_between_plain_and_gz(self, tmp_root):
        put(tmp_root, "data/streams/a.csv", [vrow(7)])
        put(tmp_root, "data/streams/b.csv.gz", [vrow(7)])
        issues = validate(tmp_root)
        assert [(i.file, i.row, i.rule) for i in issues] == [("data/streams/b.csv.gz", 1, "X01")], describe(issues)

    def test_x01_between_gz_and_plain_follows_sorted_name_order(self, tmp_root):
        put(tmp_root, "data/streams/a.csv.gz", [vrow(7)])
        put(tmp_root, "data/streams/b.csv", [vrow(7)])
        issues = validate(tmp_root)
        assert [(i.file, i.row, i.rule) for i in issues] == [("data/streams/b.csv", 1, "X01")], describe(issues)

    def test_x02_balance_spans_plain_and_gz_files(self, tmp_root):
        # Rows 3 and 4 of the fixture are the two halves of one E001 transfer; split across forms.
        put(tmp_root, "data/streams/a.csv", [vrow(3)])
        put(tmp_root, "data/streams/b.csv.gz", [vrow(4)])
        assert validate(tmp_root) == [], "balance rows in different forms must still be considered together"


# ------------------------------------------------------------------------------------------ F6
class TestPre1950:
    def test_pre1950_gz_is_never_read_even_if_invalid(self, tmp_root):
        d = tmp_root / "data" / "streams_pre1950"
        d.mkdir(parents=True)
        (d / "coal.csv.gz").write_bytes(b"this is not gzip")
        (d / "bad.csv.gz").write_bytes(gz(csv_bytes(BAD_ROWS)))
        put(tmp_root, "data/streams/x.csv.gz", VALID_ROWS)
        assert validate(tmp_root) == []

    def test_pre1950_beside_a_plain_twin_is_not_f04(self, tmp_root):
        d = tmp_root / "data" / "streams_pre1950"
        d.mkdir(parents=True)
        (d / "coal.csv").write_bytes(csv_bytes(BAD_ROWS))
        (d / "coal.csv.gz").write_bytes(gz(csv_bytes(BAD_ROWS)))
        assert validate(tmp_root) == []


# ------------------------------------------------------------------------------------------ F7
class TestCli:
    def test_cli_accepts_gz_file_argument(self, tmp_root, tmp_path):
        rel = put(tmp_root, "data/streams/x.csv.gz", VALID_ROWS)
        r = run_cli(["--root", tmp_root, tmp_root / rel], cwd=tmp_path)
        assert r.returncode == 0, r.stdout + r.stderr

    def test_cli_relative_gz_argument_is_relative_to_root(self, tmp_root, tmp_path):
        put(tmp_root, "data/streams/x.csv.gz", VALID_ROWS)
        r = run_cli(["--root", tmp_root, "data/streams/x.csv.gz"], cwd=tmp_path)
        assert r.returncode == 0, r.stdout + r.stderr

    def test_cli_issue_lines_keep_gz_suffix(self, tmp_root, tmp_path):
        rel = put(tmp_root, "data/streams/x.csv.gz", [vrow(7, unit="Bq")])
        r = run_cli(["--root", tmp_root, rel], cwd=tmp_path)
        assert r.returncode == 1, r.stdout + r.stderr
        assert re.search(r"data/streams/x\.csv\.gz:1: R02\b", r.stdout), r.stdout

    def test_cli_default_discovery_finds_gz(self, tmp_root, tmp_path):
        put(tmp_root, "data/streams/x.csv.gz", [vrow(7, unit="Bq")])
        r = run_cli(["--root", tmp_root], cwd=tmp_path)
        assert r.returncode == 1, r.stdout + r.stderr
        assert re.search(r"x\.csv\.gz:1: R02\b", r.stdout), r.stdout

    def test_cli_f04_line_for_both_forms(self, tmp_root, tmp_path):
        put(tmp_root, "data/streams/x.csv", VALID_ROWS)
        put(tmp_root, "data/streams/x.csv.gz", VALID_ROWS)
        r = run_cli(["--root", tmp_root], cwd=tmp_path)
        assert r.returncode == 1, r.stdout + r.stderr
        assert re.search(r"data/streams/x\.csv\.gz:-: F04\b", r.stdout), r.stdout

    def test_cli_corrupt_gz_is_f03_exit_1(self, tmp_root, tmp_path):
        (tmp_root / "data/streams/x.csv.gz").write_bytes(b"junk")
        r = run_cli(["--root", tmp_root], cwd=tmp_path)
        assert r.returncode == 1, r.stdout + r.stderr
        assert re.search(r"x\.csv\.gz:-: F03\b", r.stdout), r.stdout
