"""Spec-blind CLI tests for gzipped stream outputs (D72; LIB_SPEC 11.5, 11.8 D2/D3 and E), all four streams.

Each stream CLI is run as `python -m pipeline.streams.<stream> --root <tmp tree>` on a mini tree in tmp_path
(data/ and schema/ copied from the repository without any stream outputs, as the per-stream suites do).

Runtime control: a full stream build costs about 3 s (coal), 4 s (nuclear), 6 s (oil_gas) and 14 s (other) per
CLI run, in either mode. Each scenario below is therefore a module-scoped fixture that runs the CLI once or
twice and keeps the results; several tests then assert on the one result. Per stream: 1 template `--write`,
1 clean diff, 1 tampered diff, 1 corrupt/missing diff, 2 for recompressed (diff, write), 2 for legacy
(diff, write), 2 for both-forms (diff, write): 10 runs.

Mapping to LIB_SPEC 11.8
------------------------
D2  TestBothFormsPresent.test_diff_exits_2*        D3  TestBothFormsPresent.test_write_*
E1  TestWriteAndCleanDiff                          E2/E3  TestTamperedContent (main and pre-1950 together)
E4  TestRecompressedCopy                           E5  TestLegacyPlain
E6  TestMissingAndCorrupt                          E7  not repeated here (build-log behaviour is unchanged
    and is covered by the per-stream suites)

Ambiguities noted
-----------------
A1. The exact wording of the legacy, missing and unreadable messages is only partly fixed by LIB_SPEC 11.5.2
    ("legacy plain form, run --write to migrate", "missing", "unreadable: <reason>"). Tests match on the
    key words "legacy", "missing", "unreadable" (case-insensitive) and on `first difference at line N`.
A2. Whether both-forms exit 2 happens before or after the (expensive) build is not specified; the tests do
    not care.
A3. The "(unchanged)" / "(removed legacy <stream>.csv)" flags are specified for the `written:` line;
    tests look for them anywhere in stdout+stderr.
"""
from __future__ import annotations

import gzip
import hashlib
import importlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
STREAMS = ["coal", "nuclear", "oil_gas", "other"]
GZ_HEADER = bytes.fromhex("1f8b08000000000002ff")
TAMPER_LINE = 3


# ------------------------------------------------------------------------------------------ helpers
def _env():
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    return env


def run_cli(stream, root, *extra):
    return subprocess.run(
        [sys.executable, "-m", f"pipeline.streams.{stream}", "--root", str(root), *extra],
        cwd=str(ROOT), env=_env(), capture_output=True, text=True, timeout=1800, check=False,
    )


def out_of(p):
    return (p.stdout + p.stderr).replace("\\", "/")


def paths(root: Path, stream: str):
    return {
        "main": root / "data" / "streams" / f"{stream}.csv.gz",
        "pre": root / "data" / "streams_pre1950" / f"{stream}.csv.gz",
        "main_plain": root / "data" / "streams" / f"{stream}.csv",
        "pre_plain": root / "data" / "streams_pre1950" / f"{stream}.csv",
        "log": root / "research" / stream / "build_log.csv",
    }


def snapshot(root: Path, stream: str):
    """name -> (sha256, mtime_ns) of everything the CLI could touch."""
    snap = {}
    for d in (root / "data" / "streams", root / "data" / "streams_pre1950", root / "research" / stream):
        if d.is_dir():
            for p in sorted(d.iterdir()):
                st = p.stat()
                snap[p.relative_to(root).as_posix()] = (hashlib.sha256(p.read_bytes()).hexdigest(), st.st_mtime_ns)
    return snap


def make_tree(dst: Path, stream: str, link_from: Path | None = None) -> Path:
    """data/ and schema/ without stream outputs, plus empty output directories (as the stream suites do)."""
    src = link_from or ROOT

    def copy(s, d, **kw):
        if link_from is not None:
            try:
                os.link(s, d)
                return d
            except OSError:
                pass
        return shutil.copy2(s, d)

    shutil.copytree(src / "data", dst / "data", copy_function=copy,
                    ignore=shutil.ignore_patterns("streams", "streams_pre1950"))
    shutil.copytree(src / "schema", dst / "schema", copy_function=copy)
    (dst / "data" / "streams").mkdir()
    (dst / "data" / "streams_pre1950").mkdir()
    (dst / "research" / stream).mkdir(parents=True)
    return dst


def clone(template: Path, dst: Path, stream: str) -> Path:
    """Clone a written template: inputs hard-linked (never modified), outputs really copied."""
    make_tree(dst, stream, link_from=template)
    for rel in (f"data/streams/{stream}.csv.gz", f"data/streams_pre1950/{stream}.csv.gz",
                f"research/{stream}/build_log.csv"):
        shutil.copy2(template / rel, dst / rel)
    return dst


def gz_lib():
    mod = importlib.import_module("pipeline.lib.io")
    if not hasattr(mod, "gzip_bytes"):
        pytest.fail("pipeline.lib.io.gzip_bytes is missing (LIB_SPEC 11.4)", pytrace=False)
    return mod.gzip_bytes


def tamper(content: bytes, line: int = TAMPER_LINE) -> bytes:
    lines = content.split(b"\n")
    assert len(lines) > line + 1, f"set-up: need more than {line} lines to tamper with"
    first = lines[line - 1]
    lines[line - 1] = (b"8" if first[:1] == b"9" else b"9") + first[1:]
    return b"\n".join(lines)


# ------------------------------------------------------------------------------------------ fixtures
@pytest.fixture(scope="module", params=STREAMS)
def stream(request):
    return request.param


@pytest.fixture(scope="module")
def template(stream, tmp_path_factory):
    """A clean tree after one `--write` with the new code, plus its result."""
    root = make_tree(tmp_path_factory.mktemp(f"{stream}_tpl") / "r", stream)
    proc = run_cli(stream, root, "--write")
    return {"root": root, "proc": proc, "p": paths(root, stream)}


@pytest.fixture(scope="module")
def good(template, stream):
    """Template guard: the other scenarios only make sense if --write worked."""
    p = template["p"]
    if template["proc"].returncode != 0 or not p["main"].is_file() or not p["pre"].is_file():
        pytest.fail(f"set-up: `--write` on a clean tree must exit 0 and create both .csv.gz files; "
                    f"rc={template['proc'].returncode}\n{template['proc'].stderr[-1500:]}", pytrace=False)
    return {
        "root": template["root"],
        "main_content": gzip.decompress(p["main"].read_bytes()),
        "pre_content": gzip.decompress(p["pre"].read_bytes()),
        "main_bytes": p["main"].read_bytes(),
        "pre_bytes": p["pre"].read_bytes(),
    }


@pytest.fixture(scope="module")
def clean_diff(good, stream):
    return run_cli(stream, good["root"])


@pytest.fixture(scope="module")
def tampered(good, stream, tmp_path_factory):
    root = clone(good["root"], tmp_path_factory.mktemp(f"{stream}_tamper") / "r", stream)
    p = paths(root, stream)
    gzip_bytes = gz_lib()
    p["main"].write_bytes(gzip_bytes(tamper(good["main_content"])))
    p["pre"].write_bytes(gzip_bytes(tamper(good["pre_content"])))
    before = snapshot(root, stream)
    proc = run_cli(stream, root)
    after = snapshot(root, stream)
    yield {"root": root, "p": p, "proc": proc, "before": before, "after": after}
    shutil.rmtree(root.parent, ignore_errors=True)


@pytest.fixture(scope="module")
def corrupt_and_missing(good, stream, tmp_path_factory):
    root = clone(good["root"], tmp_path_factory.mktemp(f"{stream}_corrupt") / "r", stream)
    p = paths(root, stream)
    p["main"].write_bytes(good["main_bytes"][:-10])  # truncated gzip
    p["pre"].unlink()                                # missing
    before = snapshot(root, stream)
    proc = run_cli(stream, root)
    after = snapshot(root, stream)
    yield {"root": root, "p": p, "proc": proc, "before": before, "after": after}
    shutil.rmtree(root.parent, ignore_errors=True)


@pytest.fixture(scope="module")
def recompressed(good, stream, tmp_path_factory):
    root = clone(good["root"], tmp_path_factory.mktemp(f"{stream}_recomp") / "r", stream)
    p = paths(root, stream)
    for key, content in (("main", good["main_content"]), ("pre", good["pre_content"])):
        data = gzip.compress(content, 1, mtime=1_700_000_000)  # different level and non-zero MTIME
        p[key].write_bytes(data)
        os.utime(p[key], ns=(1_600_000_000 * 10**9, 1_600_000_000 * 10**9))
    assert p["main"].read_bytes() != good["main_bytes"], "set-up: recompressed bytes must differ"
    before = snapshot(root, stream)
    diff = run_cli(stream, root)
    after_diff = snapshot(root, stream)
    write = run_cli(stream, root, "--write")
    after_write = snapshot(root, stream)
    yield {"root": root, "p": p, "diff": diff, "write": write, "before": before,
           "after_diff": after_diff, "after_write": after_write}
    shutil.rmtree(root.parent, ignore_errors=True)


@pytest.fixture(scope="module")
def legacy(good, stream, tmp_path_factory):
    """Plain `.csv` with correct content and no `.csv.gz` (a tree committed by the old code)."""
    root = clone(good["root"], tmp_path_factory.mktemp(f"{stream}_legacy") / "r", stream)
    p = paths(root, stream)
    p["main"].unlink()
    p["pre"].unlink()
    p["main_plain"].write_bytes(good["main_content"])
    p["pre_plain"].write_bytes(good["pre_content"])
    before = snapshot(root, stream)
    diff = run_cli(stream, root)
    after_diff = snapshot(root, stream)
    gz_after_diff = [p["main"].exists(), p["pre"].exists()]
    write = run_cli(stream, root, "--write")
    yield {"root": root, "p": p, "diff": diff, "write": write, "before": before, "after_diff": after_diff,
           "gz_after_diff": gz_after_diff}
    shutil.rmtree(root.parent, ignore_errors=True)


@pytest.fixture(scope="module")
def both(good, stream, tmp_path_factory):
    root = clone(good["root"], tmp_path_factory.mktemp(f"{stream}_both") / "r", stream)
    p = paths(root, stream)
    p["main_plain"].write_bytes(good["main_content"])   # the plain sibling beside the .gz
    before = snapshot(root, stream)
    diff = run_cli(stream, root)
    after_diff = snapshot(root, stream)
    write = run_cli(stream, root, "--write")
    yield {"root": root, "p": p, "diff": diff, "write": write, "before": before, "after_diff": after_diff}
    shutil.rmtree(root.parent, ignore_errors=True)


# ------------------------------------------------------------------------------------------ E1 and --write
class TestWriteAndCleanDiff:
    def test_write_exits_0(self, template, stream):
        assert template["proc"].returncode == 0, template["proc"].stderr[-1500:]

    def test_write_creates_csv_gz_files_and_no_plain_files(self, good, template, stream):
        p = template["p"]
        assert p["main"].is_file() and p["pre"].is_file(), "--write must create <stream>.csv.gz in both directories"
        assert not p["main_plain"].exists() and not p["pre_plain"].exists(), "no plain .csv may be written"

    def test_output_is_deterministic_gzip(self, good, template):
        p = template["p"]
        for key in ("main", "pre"):
            data = p[key].read_bytes()
            assert data[:10] == GZ_HEADER, f"{key}: gzip header {data[:10].hex(' ')} != {GZ_HEADER.hex(' ')}"

    def test_content_is_lf_utf8_no_bom_with_header(self, good):
        for content in (good["main_content"], good["pre_content"]):
            assert b"\r" not in content and not content.startswith(b"\xef\xbb\xbf")
            text = content.decode("utf-8")
            assert text.startswith("year,stream,") and text.endswith("\n")

    def test_written_line_names_the_gz_paths(self, template, stream):
        text = out_of(template["proc"])
        assert f"data/streams/{stream}.csv.gz" in text, text[-1200:]
        assert f"data/streams_pre1950/{stream}.csv.gz" in text, text[-1200:]

    def test_build_log_stays_plain(self, template):
        log = template["p"]["log"].read_bytes()
        assert log[:2] != b"\x1f\x8b", "build_log.csv must stay plain CSV"
        log.decode("utf-8")
        assert not template["p"]["log"].with_name("build_log.csv.gz").exists()

    def test_diff_after_write_exits_0(self, clean_diff):
        assert clean_diff.returncode == 0, f"diff on a freshly written tree exited {clean_diff.returncode}\n{clean_diff.stderr[-1500:]}"

    def test_diff_reports_identical(self, clean_diff):
        assert "identical" in out_of(clean_diff).lower()


# ------------------------------------------------------------------------------------------ E2 / E3
class TestTamperedContent:
    def test_exit_code_is_1(self, tampered):
        assert tampered["proc"].returncode == 1, f"rc={tampered['proc'].returncode}\n{tampered['proc'].stderr[-1500:]}"

    def test_main_file_named_with_first_difference_line(self, tampered, stream):
        want = f"data/streams/{stream}.csv.gz: first difference at line {TAMPER_LINE}"
        assert want in out_of(tampered["proc"]), f"missing {want!r} in:\n{tampered['proc'].stderr[-1500:]}"

    def test_pre1950_file_named_with_first_difference_line(self, tampered, stream):
        want = f"data/streams_pre1950/{stream}.csv.gz: first difference at line {TAMPER_LINE}"
        assert want in out_of(tampered["proc"]), f"missing {want!r} in:\n{tampered['proc'].stderr[-1500:]}"

    def test_summary_line_lists_the_differing_files(self, tampered, stream):
        text = out_of(tampered["proc"])
        assert "differs from the committed file" in text
        assert text.count(f"{stream}.csv.gz") >= 2

    def test_diff_mode_writes_nothing(self, tampered):
        assert tampered["after"] == tampered["before"], "diff mode must not write, delete or touch any committed file"


# ------------------------------------------------------------------------------------------ E4
class TestRecompressedCopy:
    def test_diff_exits_0_when_only_compressed_bytes_differ(self, recompressed):
        d = recompressed["diff"]
        assert d.returncode == 0, f"comparison must be by decompressed content; rc={d.returncode}\n{d.stderr[-1500:]}"

    def test_diff_leaves_files_untouched(self, recompressed):
        assert recompressed["after_diff"] == recompressed["before"]

    def test_write_exits_0(self, recompressed):
        assert recompressed["write"].returncode == 0, recompressed["write"].stderr[-1500:]

    def test_write_does_not_rewrite_unchanged_content(self, recompressed, stream):
        """Same bytes and same mtime, so a different zlib never churns git (LIB_SPEC 11.5.3)."""
        for rel in (f"data/streams/{stream}.csv.gz", f"data/streams_pre1950/{stream}.csv.gz"):
            assert recompressed["after_write"][rel] == recompressed["before"][rel], f"{rel} was rewritten"

    def test_write_flags_unchanged(self, recompressed):
        assert "(unchanged)" in out_of(recompressed["write"]), out_of(recompressed["write"])[-1200:]


# ------------------------------------------------------------------------------------------ E5
class TestLegacyPlain:
    def test_diff_exits_1_even_though_content_matches(self, legacy):
        d = legacy["diff"]
        assert d.returncode == 1, f"an unmigrated tree must never report identical; rc={d.returncode}\n{d.stderr[-1500:]}"

    def test_diff_reports_legacy_for_both_files(self, legacy, stream):
        text = out_of(legacy["diff"]).lower()
        assert "legacy" in text, text[-1500:]
        assert f"data/streams/{stream}.csv" in text and f"data/streams_pre1950/{stream}.csv" in text

    def test_diff_does_not_migrate(self, legacy):
        assert legacy["after_diff"] == legacy["before"]
        assert legacy["gz_after_diff"] == [False, False], "diff mode must not create the .csv.gz files"

    def test_write_exits_0(self, legacy):
        assert legacy["write"].returncode == 0, legacy["write"].stderr[-1500:]

    def test_write_creates_gz_with_same_content_and_removes_plain(self, legacy, good):
        p = legacy["p"]
        assert p["main"].is_file() and p["pre"].is_file(), "--write must create the .csv.gz files"
        assert not p["main_plain"].exists() and not p["pre_plain"].exists(), "--write must remove the plain files"
        assert gzip.decompress(p["main"].read_bytes()) == good["main_content"]
        assert gzip.decompress(p["pre"].read_bytes()) == good["pre_content"]

    def test_write_reports_removed_legacy(self, legacy):
        assert "removed legacy" in out_of(legacy["write"]).lower(), out_of(legacy["write"])[-1200:]


# ------------------------------------------------------------------------------------------ E6
class TestMissingAndCorrupt:
    def test_exit_code_is_1(self, corrupt_and_missing):
        r = corrupt_and_missing["proc"]
        assert r.returncode == 1, f"rc={r.returncode}\n{r.stderr[-1500:]}"

    def test_missing_pre1950_gz_is_reported_missing(self, corrupt_and_missing, stream):
        text = out_of(corrupt_and_missing["proc"])
        assert f"data/streams_pre1950/{stream}.csv.gz: missing" in text, text[-1500:]

    def test_corrupt_main_gz_is_reported_unreadable(self, corrupt_and_missing, stream):
        text = out_of(corrupt_and_missing["proc"])
        assert f"data/streams/{stream}.csv.gz" in text and "unreadable" in text.lower(), text[-1500:]

    def test_diff_does_not_overwrite_or_create(self, corrupt_and_missing, stream):
        assert corrupt_and_missing["after"] == corrupt_and_missing["before"]
        assert not corrupt_and_missing["p"]["pre"].exists(), "diff mode must not create the missing file"


# ------------------------------------------------------------------------------------------ D2 / D3
class TestBothFormsPresent:
    def test_diff_exits_2(self, both):
        d = both["diff"]
        assert d.returncode == 2, f"both forms present must exit 2; rc={d.returncode}\n{d.stderr[-1500:]}"

    def test_diff_error_names_both_files(self, both, stream):
        text = out_of(both["diff"])
        assert f"{stream}.csv.gz" in text and text.replace(f"{stream}.csv.gz", "").count(f"{stream}.csv") >= 1, text[-1500:]

    def test_diff_leaves_both_files_untouched(self, both):
        assert both["after_diff"] == both["before"]

    def test_write_exits_0(self, both):
        assert both["write"].returncode == 0, both["write"].stderr[-1500:]

    def test_write_leaves_only_the_gz(self, both):
        assert not both["p"]["main_plain"].exists(), "--write must delete the plain sibling"
        assert both["p"]["main"].is_file()

    def test_write_result_equals_a_fresh_build(self, both, good):
        assert gzip.decompress(both["p"]["main"].read_bytes()) == good["main_content"]
        assert gzip.decompress(both["p"]["pre"].read_bytes()) == good["pre_content"]
