"""Spec-blind tests for research/activity/scripts/raw_manifest.py (D72, docs/DATA_ARCHIVE.md section 4 and 6).

Every test builds a throwaway git repository in tmp_path (`git init`, a .gitignore, committed files) and runs
the script as a subprocess with `--root <repo>`. Skipped when `git` is not on PATH. No network, nothing outside
tmp_path. There is deliberately no __init__.py in this directory: the pipeline/tests tree is collected by
rootdir path, and a package called `research` here would shadow the top-level research/ directory.

Mapping to DATA_ARCHIVE section 6
---------------------------------
A  TestFileSet            B  TestContent            C  TestDeterminismAndFetched
D  TestCheck              E  TestSafety             (+ TestOptions for --manifest and usage errors)

Ambiguities noted (not asserted beyond the stated reading)
----------------------------------------------------------
A1. `write` prints "one line per added, changed or removed path (format as in `check`)". For a removed file
    the check kind would be `missing`; the tests only require the path to appear on stdout.
A2. Exit code for `write` when nothing changed: 0 (spec: "Exit 0").
A3. "bad row" in check/write: tests treat a wrong field count, a non-integer size, a sha256 that is not 64
    lowercase hex characters, and a `fetched` that is not YYYY-MM-DD as malformed. DATA_ARCHIVE 4.1 states
    these formats; 4.2 does not list each one as an exit-2 cause.
A4. What `write` prints for the summary when there are zero files (`0 files, 0 bytes`) is assumed from the
    stated format `N files, M bytes`.
A5. A missing include directory with `write`: the manifest is written with the header only (inferred).
A6. Whether `untracked-not-ignored` lines are also printed by `write`: unspecified, not tested.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "research" / "activity" / "scripts" / "raw_manifest.py"
HEADER = "path,size,sha256,fetched"
RAW = "research/activity/raw"
MANIFEST = f"{RAW}/MANIFEST.csv"

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git is not on PATH (DATA_ARCHIVE 6)")

ABC_SHA = "edeaaff3f1774ad2888673770c6d64097e391bc362d7d6fb34982ddf0efd18cb"  # sha256(b"abc\n")
EMPTY_SHA = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

GITIGNORE = "*.zip\n*.json\n*.csv\nimport/*.pdf\nfao/\n"
RAW_GITIGNORE = "*.txt\n"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class Repo:
    def __init__(self, root: Path):
        self.root = root
        self.env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull,
                        GIT_CONFIG_NOSYSTEM="1", PYTHONIOENCODING="utf-8")

    # -- git
    def git(self, *args):
        r = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid",
                            "-c", "commit.gpgsign=false", "-C", str(self.root), *args],
                           env=self.env, capture_output=True, text=True, check=False)
        assert r.returncode == 0, f"git {' '.join(args)} failed: {r.stderr}"
        return r

    # -- files
    def put(self, rel: str, data: bytes | str = b"", mtime: int | None = None) -> Path:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data.encode("utf-8") if isinstance(data, str) else data)
        if mtime is not None:
            os.utime(p, (mtime, mtime))
        return p

    def rm(self, rel: str):
        (self.root / rel).unlink()

    # -- script
    def run(self, command, *args, root: Path | None = None):
        cmd = [sys.executable, str(SCRIPT), command, "--root", str(root or self.root), *map(str, args)]
        r = subprocess.run(cmd, cwd=str(self.root.parent), env=self.env, capture_output=True, timeout=300, check=False)
        r.out = r.stdout.decode("utf-8", "replace")
        r.err = r.stderr.decode("utf-8", "replace")
        return r

    def write(self, *args, date="2026-01-01"):
        r = self.run("write", *(["--date", date] if date else []), *args)
        assert r.returncode == 0, f"write exited {r.returncode}\nstdout: {r.out}\nstderr: {r.err}"
        return r

    @property
    def manifest_path(self) -> Path:
        return self.root / MANIFEST

    def manifest_bytes(self) -> bytes:
        return self.manifest_path.read_bytes()

    def rows(self):
        text = self.manifest_bytes().decode("utf-8")
        rows = list(csv.reader(io.StringIO(text, newline="")))
        assert rows and rows[0] == HEADER.split(","), f"unexpected header: {rows[:1]}"
        return rows[1:]

    def by_path(self):
        return {r[0]: r for r in self.rows()}

    def paths(self):
        return [r[0] for r in self.rows()]


@pytest.fixture
def repo(tmp_path):
    if not SCRIPT.is_file():
        pytest.fail(f"{SCRIPT.relative_to(ROOT)} does not exist yet (DATA_ARCHIVE 4.2)", pytrace=False)
    root = tmp_path / "repo"
    root.mkdir()
    r = Repo(root)
    r.git("init", "-q")
    r.put(".gitignore", GITIGNORE)
    r.put(f"{RAW}/.gitignore", RAW_GITIGNORE)
    r.put("README.md", "tracked\n")
    r.git("add", ".gitignore", f"{RAW}/.gitignore", "README.md")
    r.git("commit", "-q", "-m", "init")
    return r


def standard_files(repo: Repo):
    """Ignored, untracked files in both default roots (plus decoys)."""
    repo.put(f"{RAW}/INTL.txt", b"intl\n")           # ignored by the nested .gitignore
    repo.put(f"{RAW}/data.json", b'{"a": 1}\n')       # *.json
    repo.put(f"{RAW}/fao/x/a.csv", b"x,y\n1,2\n")     # ignored subdirectory
    repo.put("import/doc.pdf", b"%PDF-1.4 fake\n")    # import/*.pdf
    return [f"{RAW}/INTL.txt", f"{RAW}/data.json", f"{RAW}/fao/x/a.csv", "import/doc.pdf"]


# ------------------------------------------------------------------------------------------ A
class TestFileSet:
    def test_ignored_untracked_files_are_listed_including_ignored_subdirectories(self, repo):
        want = standard_files(repo)
        repo.write()
        assert sorted(repo.paths()) == sorted(want)

    def test_tracked_file_matching_ignore_pattern_is_not_listed(self, repo):
        standard_files(repo)
        repo.put(f"{RAW}/forced.json", b"{}\n")
        repo.put(f"{RAW}/forced.txt", b"t\n")
        repo.git("add", "-f", f"{RAW}/forced.json", f"{RAW}/forced.txt")
        repo.git("commit", "-q", "-m", "force-add")
        repo.write()
        assert f"{RAW}/forced.json" not in repo.paths()
        assert f"{RAW}/forced.txt" not in repo.paths()
        assert f"{RAW}/data.json" in repo.paths()

    def test_untracked_not_ignored_files_are_not_listed_and_check_mentions_them_on_stderr_only(self, repo):
        standard_files(repo)
        repo.put(f"{RAW}/notes.md", "n\n")
        repo.put("import/readme.md", "r\n")
        repo.write()
        assert f"{RAW}/notes.md" not in repo.paths() and "import/readme.md" not in repo.paths()
        r = repo.run("check")
        assert r.returncode == 0, f"unaffected exit code expected; got {r.returncode}\n{r.out}{r.err}"
        err_lines = r.err.splitlines()
        assert f"untracked-not-ignored {RAW}/notes.md" in err_lines, r.err
        assert "untracked-not-ignored import/readme.md" in err_lines, r.err
        assert "untracked-not-ignored" not in r.out, "the information goes to stderr only"
        assert not any(l.startswith("untracked-not-ignored") and f"{RAW}/data.json" in l for l in err_lines), (
            "ignored files must not be reported as untracked-not-ignored")

    def test_files_outside_roots_manifest_and_gitignore_are_not_listed(self, repo):
        standard_files(repo)
        repo.put("data/outside.zip", b"zz")          # ignored, but outside the include roots
        repo.put("elsewhere/deep/thing.json", b"{}")
        repo.write()
        paths = repo.paths()
        assert not any(p.startswith(("data/", "elsewhere/")) for p in paths), paths
        assert MANIFEST not in paths, "the manifest must not list itself (it is untracked and ignored here)"
        assert not any(p.endswith(".gitignore") for p in paths)

    def test_manifest_still_excluded_when_untracked_and_rewritten(self, repo):
        standard_files(repo)
        repo.write()
        repo.write(date="2026-02-02")
        assert MANIFEST not in repo.paths()

    def test_include_replaces_the_default_roots(self, repo):
        standard_files(repo)
        repo.put("data/outside.zip", b"zz")
        repo.write("--include", "import")
        assert repo.paths() == ["import/doc.pdf"]
        repo.write("--include", "data")
        assert repo.paths() == ["data/outside.zip"]

    def test_include_can_be_repeated(self, repo):
        standard_files(repo)
        repo.put("data/outside.zip", b"zz")
        repo.write("--include", "import", "--include", "data")
        assert sorted(repo.paths()) == ["data/outside.zip", "import/doc.pdf"]

    def test_missing_included_directory_is_not_an_error(self, repo):
        standard_files(repo)
        r = repo.write("--include", "no/such/dir", "--include", "import")
        assert repo.paths() == ["import/doc.pdf"]
        r = repo.run("check", "--include", "no/such/dir", "--include", "import")
        assert r.returncode == 0, r.out + r.err

    def test_only_missing_directories_gives_header_only_manifest(self, repo):  # ambiguity A5
        repo.write("--include", "nothing/here")
        assert repo.manifest_bytes() == (HEADER + "\n").encode()

    @pytest.mark.parametrize("command", ["write", "check"])
    def test_non_git_root_is_exit_2(self, repo, tmp_path, command):
        plain = tmp_path / "not_a_repo"
        plain.mkdir()
        (plain / "import").mkdir()
        r = repo.run(command, root=plain)
        assert r.returncode == 2, f"rc={r.returncode}\n{r.out}{r.err}"
        assert not (plain / MANIFEST).exists(), "nothing may be written for a non-git root"

    def test_nonexistent_root_is_exit_2(self, repo, tmp_path):
        r = repo.run("check", root=tmp_path / "gone")
        assert r.returncode == 2


# ------------------------------------------------------------------------------------------ B
class TestContent:
    def test_header_is_exact(self, repo):
        standard_files(repo)
        repo.write()
        first = repo.manifest_bytes().split(b"\n", 1)[0]
        assert first == HEADER.encode()

    def test_header_only_when_there_are_no_files(self, repo):
        repo.write()
        assert repo.manifest_bytes() == (HEADER + "\n").encode()

    def test_size_and_sha256_match_the_files(self, repo):
        standard_files(repo)
        repo.write()
        for rel, row in repo.by_path().items():
            data = (repo.root / rel).read_bytes()
            assert row[1] == str(len(data)) == str(os.path.getsize(repo.root / rel)), rel
            assert row[2] == sha(data), rel
            assert re.fullmatch(r"[0-9a-f]{64}", row[2])

    def test_known_digests(self, repo):
        repo.put(f"{RAW}/abc.json", b"abc\n")
        repo.put(f"{RAW}/empty.json", b"")
        repo.write()
        rows = repo.by_path()
        assert rows[f"{RAW}/abc.json"][1:3] == ["4", ABC_SHA]
        assert rows[f"{RAW}/empty.json"][1:3] == ["0", EMPTY_SHA]

    def test_paths_are_repo_relative_posix(self, repo):
        standard_files(repo)
        repo.write()
        for p in repo.paths():
            assert "\\" not in p and not p.startswith(("/", "./")) and ":" not in p[:3], p

    def test_rows_are_in_code_point_order(self, repo):
        repo.put(f"{RAW}/a.csv", b"1")
        repo.put(f"{RAW}/B.csv", b"2")
        repo.put(f"{RAW}/fao/x.csv", b"3")
        repo.write()
        paths = repo.paths()
        assert paths == [f"{RAW}/B.csv", f"{RAW}/a.csv", f"{RAW}/fao/x.csv"], paths
        assert paths == sorted(paths)

    def test_code_point_order_beyond_ascii(self, repo):
        repo.put("import/zeta.pdf", b"1")
        repo.put("import/école.pdf", b"2")
        repo.put("import/Zed.pdf", b"3")
        repo.write()
        assert repo.paths() == sorted(repo.paths()) == ["import/Zed.pdf", "import/zeta.pdf", "import/école.pdf"]

    def test_lf_no_bom_utf8_with_non_ascii_name(self, repo):
        name = "import/café 東京.pdf"
        repo.put(name, b"x")
        repo.put("import/with space.pdf", b"y")
        repo.write()
        raw = repo.manifest_bytes()
        assert b"\r" not in raw and not raw.startswith(b"\xef\xbb\xbf")
        text = raw.decode("utf-8")
        assert raw.endswith(b"\n")
        assert name in repo.paths()
        assert "import/with space.pdf" in repo.paths()
        assert not text.startswith("﻿")

    def test_crlf_file_hashes_raw_bytes(self, repo):
        data = b"line1\r\nline2\r\n"
        repo.put(f"{RAW}/crlf.json", data)
        repo.write()
        row = repo.by_path()[f"{RAW}/crlf.json"]
        assert row[1] == "14" and row[2] == sha(data), "no newline conversion may happen before hashing"

    def test_binary_file_large_enough_to_need_several_chunks(self, repo):
        data = os.urandom(3 * 1024 * 1024 + 17)
        repo.put(f"{RAW}/big.zip", data)
        repo.write()
        row = repo.by_path()[f"{RAW}/big.zip"]
        assert row[1] == str(len(data)) and row[2] == sha(data)

    def test_row_shape(self, repo):
        standard_files(repo)
        repo.write(date="2026-03-04")
        for row in repo.rows():
            assert len(row) == 4
            assert re.fullmatch(r"\d+", row[1])
            assert row[3] == "2026-03-04"

    def test_summary_line_counts_files_and_bytes(self, repo):
        repo.put(f"{RAW}/a.json", b"12345")
        repo.put(f"{RAW}/b.json", b"123")
        r = repo.write()
        assert "2 files, 8 bytes" in r.out.splitlines(), r.out


# ------------------------------------------------------------------------------------------ C
class TestDeterminismAndFetched:
    def test_two_writes_with_different_dates_are_byte_identical(self, repo):
        standard_files(repo)
        repo.write(date="2026-01-01")
        first = repo.manifest_bytes()
        repo.write(date="2030-12-31")
        assert repo.manifest_bytes() == first

    def test_first_write_without_date_uses_todays_utc_date(self, repo):
        standard_files(repo)
        before = dt.datetime.now(dt.timezone.utc).date()
        repo.write(date=None)
        after = dt.datetime.now(dt.timezone.utc).date()
        got = {r[3] for r in repo.rows()}
        assert len(got) == 1 and dt.date.fromisoformat(got.pop()) in {before, after}

    def test_changed_file_gets_new_date_and_others_keep_theirs(self, repo):
        standard_files(repo)
        repo.write(date="2026-01-01")
        repo.put(f"{RAW}/data.json", b'{"a": 2}\n')
        repo.write(date="2026-02-02")
        rows = repo.by_path()
        assert rows[f"{RAW}/data.json"][3] == "2026-02-02"
        for p in (f"{RAW}/INTL.txt", f"{RAW}/fao/x/a.csv", "import/doc.pdf"):
            assert rows[p][3] == "2026-01-01", p

    def test_new_file_gets_the_new_date(self, repo):
        standard_files(repo)
        repo.write(date="2026-01-01")
        repo.put(f"{RAW}/new.zip", b"n")
        repo.write(date="2026-02-02")
        rows = repo.by_path()
        assert rows[f"{RAW}/new.zip"][3] == "2026-02-02" and rows["import/doc.pdf"][3] == "2026-01-01"

    def test_change_and_change_back_gets_the_current_date(self, repo):
        original = b'{"v": 1}\n'
        repo.put(f"{RAW}/data.json", original)
        repo.put(f"{RAW}/stable.json", b"s")
        repo.write(date="2026-01-01")
        repo.put(f"{RAW}/data.json", b'{"v": 2}\n')
        repo.write(date="2026-02-02")
        repo.put(f"{RAW}/data.json", original)
        repo.write(date="2026-03-03")
        rows = repo.by_path()
        assert rows[f"{RAW}/data.json"][3] == "2026-03-03", "only the hash in the existing manifest counts"
        assert rows[f"{RAW}/stable.json"][3] == "2026-01-01"

    def test_same_size_different_content_counts_as_changed(self, repo):
        repo.put(f"{RAW}/data.json", b"aaaa")
        repo.write(date="2026-01-01")
        repo.put(f"{RAW}/data.json", b"aaab")
        repo.write(date="2026-02-02")
        assert repo.by_path()[f"{RAW}/data.json"][3] == "2026-02-02"

    def test_touching_without_changing_content_keeps_fetched(self, repo):
        repo.put(f"{RAW}/data.json", b"same")
        repo.write(date="2026-01-01")
        os.utime(repo.root / f"{RAW}/data.json", (1_000_000_000, 1_000_000_000))
        repo.write(date="2026-02-02")
        assert repo.by_path()[f"{RAW}/data.json"][3] == "2026-01-01"

    def test_deleted_file_row_disappears(self, repo):
        standard_files(repo)
        repo.write()
        repo.rm("import/doc.pdf")
        r = repo.write(date="2026-02-02")
        assert "import/doc.pdf" not in repo.paths()
        assert "import/doc.pdf" in r.out, "write must print a line for the removed path"
        assert len(repo.rows()) == 3

    def test_write_prints_a_line_for_added_and_changed_paths(self, repo):
        standard_files(repo)
        r = repo.write()
        for p in standard_files(repo):
            assert p in r.out, f"added path {p} not printed:\n{r.out}"
        repo.put(f"{RAW}/data.json", b"changed")
        r = repo.write(date="2026-02-02")
        assert f"{RAW}/data.json" in r.out
        assert "import/doc.pdf" not in r.out, "unchanged paths are not printed"

    def test_creation_order_and_mtimes_do_not_matter(self, tmp_path):
        if not SCRIPT.is_file():
            pytest.fail(f"{SCRIPT.relative_to(ROOT)} does not exist yet (DATA_ARCHIVE 4.2)", pytrace=False)
        files = {f"{RAW}/a.json": b"1", f"{RAW}/b.zip": b"22", "import/c.pdf": b"333", f"{RAW}/fao/d.csv": b"4444"}
        outs = []
        for n, order in enumerate([list(files), list(reversed(files))]):
            root = tmp_path / f"r{n}"
            root.mkdir()
            r = Repo(root)
            r.git("init", "-q")
            r.put(".gitignore", GITIGNORE)
            r.git("add", ".gitignore")
            r.git("commit", "-q", "-m", "i")
            for i, rel in enumerate(order):
                r.put(rel, files[rel], mtime=1_000_000_000 + (i * 1_000_003 if n else -i * 977))
            r.write(date="2026-01-01")
            outs.append(r.manifest_bytes())
        assert outs[0] == outs[1]

    def test_write_is_atomic_leaves_no_temporary_files(self, repo):
        standard_files(repo)
        before = set(os.listdir(repo.root / RAW))
        repo.write()
        after = set(os.listdir(repo.root / RAW))
        assert after - before == {"MANIFEST.csv"}, f"stray files: {after - before}"


# ------------------------------------------------------------------------------------------ D
class TestCheck:
    @pytest.fixture
    def clean(self, repo):
        standard_files(repo)
        repo.write()
        return repo

    def test_clean_tree_exit_0_and_ok_line(self, clean):
        r = clean.run("check")
        assert r.returncode == 0, r.out + r.err
        assert "check: OK (4 files)" in r.out.splitlines(), r.out

    def test_new_ignored_file_is_added_exit_1(self, clean):
        clean.put(f"{RAW}/new.zip", b"n")
        r = clean.run("check")
        assert r.returncode == 1
        assert f"added {RAW}/new.zip" in r.out.splitlines(), r.out
        assert "check: 1 added, 0 changed, 0 missing" in r.out.splitlines(), r.out

    def test_modified_byte_same_size_is_changed(self, clean):
        p = clean.root / f"{RAW}/data.json"
        data = bytearray(p.read_bytes())
        data[2] ^= 0x01
        p.write_bytes(bytes(data))
        r = clean.run("check")
        assert r.returncode == 1
        assert f"changed {RAW}/data.json" in r.out.splitlines(), r.out

    def test_size_change_is_changed(self, clean):
        clean.put("import/doc.pdf", b"longer than before, definitely")
        r = clean.run("check")
        assert r.returncode == 1 and "changed import/doc.pdf" in r.out.splitlines()

    def test_deleted_file_is_missing(self, clean):
        clean.rm("import/doc.pdf")
        r = clean.run("check")
        assert r.returncode == 1
        assert "missing import/doc.pdf" in r.out.splitlines(), r.out
        assert "check: 0 added, 0 changed, 1 missing" in r.out.splitlines(), r.out

    def test_several_differences_sorted_by_path_one_line_each_with_counts(self, clean):
        clean.put(f"{RAW}/zz_new.zip", b"1")       # added
        clean.put(f"{RAW}/aa_new.zip", b"2")       # added
        clean.put(f"{RAW}/data.json", b"altered")  # changed
        clean.rm("import/doc.pdf")                 # missing
        r = clean.run("check")
        assert r.returncode == 1
        lines = [l for l in r.out.splitlines() if re.match(r"(added|changed|missing) ", l)]
        assert lines == [
            "missing import/doc.pdf",
            f"added {RAW}/aa_new.zip",
            f"changed {RAW}/data.json",
            f"added {RAW}/zz_new.zip",
        ], r.out
        assert "check: 2 added, 1 changed, 1 missing" in r.out.splitlines(), r.out

    def test_changed_fetched_value_alone_is_exit_0(self, clean):
        text = clean.manifest_bytes().decode().replace("2026-01-01", "1999-09-09")
        clean.manifest_path.write_bytes(text.encode())
        r = clean.run("check")
        assert r.returncode == 0, r.out + r.err

    def test_check_never_modifies_the_manifest(self, clean):
        clean.put(f"{RAW}/new.zip", b"n")
        clean.rm("import/doc.pdf")
        os.utime(clean.manifest_path, (1_000_000_000, 1_000_000_000))
        before = (clean.manifest_bytes(), clean.manifest_path.stat().st_mtime_ns)
        listing = sorted(os.listdir(clean.root / RAW))
        clean.run("check")
        assert (clean.manifest_bytes(), clean.manifest_path.stat().st_mtime_ns) == before
        assert sorted(os.listdir(clean.root / RAW)) == listing

    def test_check_with_custom_manifest_path(self, clean, tmp_path):
        alt = tmp_path / "alt_manifest.csv"
        shutil.move(str(clean.manifest_path), alt)  # so the default location holds no manifest
        r = clean.run("check", "--manifest", alt)
        assert r.returncode == 0, r.out + r.err
        r = clean.run("check", "--manifest", tmp_path / "does_not_exist.csv")
        assert r.returncode == 2


GOOD_ROW = f"{RAW}/data.json,5,{ABC_SHA},2026-01-01"
BAD_MANIFESTS = {
    "wrong-header": "path,size,sha,fetched\n",
    "header-order": "path,sha256,size,fetched\n",
    "empty-file": "",
    "short-row": f"{HEADER}\n{RAW}/data.json,5,{ABC_SHA}\n",
    "long-row": f"{HEADER}\n{RAW}/data.json,5,{ABC_SHA},2026-01-01,extra\n",
    "non-integer-size": f"{HEADER}\n{RAW}/data.json,five,{ABC_SHA},2026-01-01\n",
    "short-sha": f"{HEADER}\n{RAW}/data.json,5,abc123,2026-01-01\n",
    "uppercase-sha": f"{HEADER}\n{RAW}/data.json,5,{ABC_SHA.upper()},2026-01-01\n",
    "bad-date": f"{HEADER}\n{RAW}/data.json,5,{ABC_SHA},01/01/2026\n",
    "duplicate-path": f"{HEADER}\n{GOOD_ROW}\n{GOOD_ROW}\n",
    "out-of-order": f"{HEADER}\nimport/b.pdf,5,{ABC_SHA},2026-01-01\nimport/a.pdf,5,{ABC_SHA},2026-01-01\n",
    "not-utf8": b"\xff\xfe\x00garbage\n",
    "crlf-header": f"{HEADER}\r\n",
}


class TestCheckExit2:
    def test_missing_manifest_is_exit_2(self, repo):
        standard_files(repo)
        r = repo.run("check")
        assert r.returncode == 2, f"rc={r.returncode}\n{r.out}{r.err}"
        assert not repo.manifest_path.exists(), "check must not create the manifest"

    @pytest.mark.parametrize("name", sorted(BAD_MANIFESTS))
    def test_malformed_manifest_is_exit_2(self, repo, name):
        standard_files(repo)
        data = BAD_MANIFESTS[name]
        repo.put(MANIFEST, data)
        before = repo.manifest_bytes()
        r = repo.run("check")
        if name == "crlf-header":  # ambiguity: strictly the format requires LF; a CR makes the header differ
            assert r.returncode == 2, f"CRLF line endings are outside the format; rc={r.returncode}"
        else:
            assert r.returncode == 2, f"rc={r.returncode}\n{r.out}{r.err}"
        assert repo.manifest_bytes() == before


# ------------------------------------------------------------------------------------------ E
class TestSafety:
    @pytest.mark.parametrize("name", sorted(BAD_MANIFESTS))
    def test_write_over_malformed_manifest_exits_2_and_leaves_it_unchanged(self, repo, name):
        standard_files(repo)
        repo.put(MANIFEST, BAD_MANIFESTS[name])
        before = repo.manifest_bytes()
        r = repo.run("write", "--date", "2026-01-01")
        assert r.returncode == 2, f"rc={r.returncode}\n{r.out}{r.err}"
        assert repo.manifest_bytes() == before, "an unreadable manifest must never be silently replaced"
        assert sorted(os.listdir(repo.root / RAW)).count("MANIFEST.csv") == 1

    def test_deleting_the_bad_manifest_lets_write_start_over(self, repo):
        standard_files(repo)
        repo.put(MANIFEST, BAD_MANIFESTS["wrong-header"])
        repo.rm(MANIFEST)
        repo.write()
        assert len(repo.rows()) == 4

    def test_symlink_is_skipped_with_stderr_note(self, repo):
        standard_files(repo)
        link = repo.root / f"{RAW}/link.json"
        try:
            os.symlink(repo.root / f"{RAW}/data.json", link)
        except (OSError, NotImplementedError, AttributeError):
            pytest.skip("symlinks cannot be created here")
        r = repo.write()
        assert f"{RAW}/link.json" not in repo.paths()
        assert f"skipped symlink {RAW}/link.json" in r.err.splitlines(), r.err

    def test_symlink_to_a_directory_is_skipped_too(self, repo):
        standard_files(repo)
        link = repo.root / "import" / "dirlink.pdf"
        try:
            os.symlink(repo.root / "import", link, target_is_directory=True)
        except (OSError, NotImplementedError, AttributeError):
            pytest.skip("symlinks cannot be created here")
        repo.write()
        assert not any("dirlink" in p for p in repo.paths())

    def test_script_makes_no_network_calls_and_runs_zpaq_never(self, repo):
        """No zpaqfranz binary is needed (4.2): run with an empty PATH apart from git's directory."""
        standard_files(repo)
        git_dir = str(Path(shutil.which("git")).parent)
        env = dict(repo.env, PATH=git_dir)
        r = subprocess.run([sys.executable, str(SCRIPT), "write", "--root", str(repo.root), "--date", "2026-01-01"],
                           env=env, capture_output=True, timeout=120, check=False)
        assert r.returncode == 0, r.stderr.decode(errors="replace")


class TestOptions:
    def test_custom_manifest_inside_include_dir_lists_neither_itself_nor_the_default(self, repo):
        """DATA_ARCHIVE 7.1: both the manifest in use and the default MANIFEST.csv are self-excluded."""
        standard_files(repo)
        custom = f"{RAW}/custom_manifest.csv"       # ignored by *.csv, untracked, inside an include dir
        repo.put(MANIFEST, "stale default manifest, ignored and untracked\n")
        repo.write("--manifest", repo.root / custom)
        rows = [r[0] for r in csv.reader(io.StringIO((repo.root / custom).read_text("utf-8"), newline=""))][1:]
        assert custom not in rows, "the manifest in use must not list itself"
        assert MANIFEST not in rows, "the default MANIFEST.csv must not be listed either"
        assert sorted(rows) == sorted(standard_files(repo))
        # a second write (custom manifest now exists on disk) stays identical
        first = (repo.root / custom).read_bytes()
        repo.write("--manifest", repo.root / custom, date="2030-01-01")
        assert (repo.root / custom).read_bytes() == first
        r = repo.run("check", "--manifest", repo.root / custom)
        assert r.returncode == 0, r.out + r.err

    def test_default_manifest_is_not_listed_when_a_custom_one_is_used_via_check(self, repo):
        standard_files(repo)
        custom = repo.root / f"{RAW}/custom_manifest.csv"
        repo.write("--manifest", custom)
        repo.put(MANIFEST, "x\n")
        r = repo.run("check", "--manifest", custom)
        assert r.returncode == 0, r.out + r.err
        assert MANIFEST not in r.out

    def test_custom_manifest_path_is_written(self, repo, tmp_path):
        standard_files(repo)
        alt = tmp_path / "alt" / "m.csv"
        alt.parent.mkdir()
        repo.write("--manifest", alt)
        assert alt.is_file() and alt.read_bytes().startswith((HEADER + "\n").encode())
        assert not repo.manifest_path.exists()

    def test_no_subcommand_is_usage_error(self, repo):
        r = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, timeout=60, check=False)
        assert r.returncode == 2

    def test_unknown_subcommand_is_usage_error(self, repo):
        r = subprocess.run([sys.executable, str(SCRIPT), "frobnicate", "--root", str(repo.root)],
                           capture_output=True, timeout=60, check=False)
        assert r.returncode == 2
