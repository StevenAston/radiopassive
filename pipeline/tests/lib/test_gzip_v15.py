"""Spec-blind tests for the v1.5 gzip additions to pipeline.lib (D72; LIB_SPEC 11.3, 11.4, 11.8 A-D, H).

Written from docs/LIB_SPEC.md section 11 (and the v1.4 rules it keeps) only. Nothing here hard-codes a
compressed digest or a compressed length (LIB_SPEC 11.8); only the header bytes (11.1) and decompressed
content are asserted.

Mapping to LIB_SPEC 11.8
------------------------
A  Round trip           TestRoundTrip
B  Determinism          TestDeterminism, TestGzipBytes
C  Reading either form  TestReadBytes, TestReadTableGz, TestCorruptGz, TestFirstDifference
D  Both forms present   TestResolveStreamFile  (D2 and D3 are CLI items: streams/test_cli_gz.py)
H  Performance          TestPerformance (skipped when the committed `other` stream is absent)

Also covered: legacy plain form unchanged, write_master leaves no partial or stray output.
The "unchanged committed file is not rewritten" rule (11.5.3) belongs to the stream CLIs and is tested
in pipeline/tests/streams/test_cli_gz.py.

Ambiguities noted (the tests avoid asserting beyond the stated reading)
-----------------------------------------------------------------------
A1. gzip_bytes of bytearray / memoryview: the spec says "non-bytes argument raises LibError"; only str,
    None, int and list are tested.
A2. first_difference with a lone CR inside a cell: the spec says "lines, keeping the \\n". The test reads
    that as splitting on LF only.
A3. resolve_stream_file on a directory that does not exist: unspecified, not tested.
A4. read_bytes/read_table on a zero-byte .gz: spec C3 says LibError; asserted.
A5. The module is named test_gzip_v15.py (caller's instruction); LIB_SPEC 11.8 says test_io_gz.py.
"""
from __future__ import annotations

import gzip
import importlib
import os
import time
from pathlib import Path

import pytest

from pipeline.lib import LibError
from pipeline.lib.rows import MASTER_COLUMNS, write_master

REAL_ROOT = Path(__file__).resolve().parents[3]
GZ_HEADER = bytes.fromhex("1f8b0800000000000" "2ff")  # 1f 8b 08 00 | 00 00 00 00 | 02 ff


def io_fn(name):
    """Fetch pipeline.lib.io.<name>, failing informatively if the v1.5 function is missing."""
    mod = importlib.import_module("pipeline.lib.io")
    if not hasattr(mod, name):
        pytest.fail(f"pipeline.lib.io.{name} is missing (LIB_SPEC 11.4 requires it)", pytrace=False)
    return getattr(mod, name)


def full_row(**over):
    r = {c: None for c in MASTER_COLUMNS}
    r.update(
        year=1998, stream="nuclear", substream="fuel_cycle", stage="u_milling",
        country="CAN", group="Ra226+", tier="dispersed", quantity="flow",
        unit="Bq/a", value_low=1.0, value_central=2.0, value_high=3.0,
        below_detection=False, basis="compiled", source_ids="S0001",
        allocation_variant="default", allocation_rule="none", embedded_fuel=False,
    )
    r.update(over)
    return r


def rich_rows():
    """Floats, None cells, lists, booleans, non-ASCII text, quoting, several years."""
    return [
        full_row(year=1990, value_low=0.0, value_central=1 / 3, value_high=1234567.0),
        full_row(year=1991, value_low=1.5e-7, value_central=4.0e12, value_high=8.0e12,
                 below_detection=True, notes="café, naïve µ 東京"),
        full_row(year=1992, source_ids=["S0001", "S0004"], factor_ids=["coal:0001", "coal:0002"],
                 embedded_fuel=True, notes='quote " and, comma'),
        full_row(year=1993, product=None, technology=None, route=None, event_id=None, notes=None),
    ]


def master_bytes(rows, tmp_path, name="ref.csv"):
    p = tmp_path / name
    write_master(rows, p)
    return p.read_bytes()


def big_content(n=400):
    header = ",".join(MASTER_COLUMNS) + "\n"
    return (header + "".join(f"{1900 + i % 120},row{i},filler,{'x' * 40}\n" for i in range(n))).encode()


# ---------------------------------------------------------------------------------------------- A
class TestRoundTrip:
    @pytest.mark.parametrize("rows_factory", [list, lambda: [full_row()], rich_rows],
                             ids=["empty-list", "single-row", "rich"])
    def test_gz_round_trip_equals_plain_round_trip(self, tmp_path, rows_factory):
        read_table = io_fn("read_table")
        plain, gz = tmp_path / "p.csv", tmp_path / "p.csv.gz"
        write_master(rows_factory(), plain)
        write_master(rows_factory(), gz)
        assert gz.is_file(), "write_master to a .csv.gz path must create that file"
        assert read_table(gz) == read_table(plain)

    def test_header_only_output_round_trips_to_empty_list(self, tmp_path):
        gz = tmp_path / "h.csv.gz"
        write_master([], gz)
        assert io_fn("read_table")(gz) == []
        assert gzip.decompress(gz.read_bytes()) == (",".join(MASTER_COLUMNS) + "\n").encode()

    @pytest.mark.parametrize("rows_factory", [list, lambda: [full_row()], rich_rows],
                             ids=["empty-list", "single-row", "rich"])
    def test_decompressed_content_equals_plain_bytes(self, tmp_path, rows_factory):
        plain, gz = tmp_path / "p.csv", tmp_path / "p.csv.gz"
        write_master(rows_factory(), plain)
        write_master(rows_factory(), gz)
        assert gzip.decompress(gz.read_bytes()) == plain.read_bytes()

    def test_decompressed_content_is_lf_utf8_without_bom(self, tmp_path):
        gz = tmp_path / "p.csv.gz"
        write_master(rich_rows(), gz)
        content = gzip.decompress(gz.read_bytes())
        assert b"\r" not in content, "CR found inside the gzip content (LF only, SCHEMA 1)"
        assert not content.startswith(b"\xef\xbb\xbf"), "BOM found inside the gzip content"
        text = content.decode("utf-8")  # raises if not valid UTF-8
        assert "café" in text and "東京" in text
        assert content.endswith(b"\n")

    def test_plain_output_matches_hand_written_bytes(self, tmp_path):
        """Plain output is unchanged from v1.4 (A4)."""
        header = ("year,stream,substream,stage,product,residue_type,country,group,tier,quantity,unit,"
                  "value_low,value_central,value_high,below_detection,basis,source_ids,factor_ids,"
                  "allocation_variant,allocation_rule,embedded_fuel,technology,route,event_id,notes\n")
        line = "1998,nuclear,fuel_cycle,u_milling,,,CAN,Ra226+,dispersed,flow,Bq/a,1,2,3,false,compiled,S0001,,default,none,false,,,,\n"
        p = tmp_path / "plain.csv"
        write_master([full_row()], p)
        assert p.read_bytes() == (header + line).encode("utf-8")

    def test_plain_and_gz_paths_accept_str(self, tmp_path):
        write_master([full_row()], str(tmp_path / "s.csv.gz"))
        assert (tmp_path / "s.csv.gz").is_file()

    def test_gz_write_leaves_no_stray_files(self, tmp_path):
        d = tmp_path / "out"
        d.mkdir()
        write_master(rich_rows(), d / "x.csv.gz")
        assert sorted(p.name for p in d.iterdir()) == ["x.csv.gz"]

    def test_bad_input_creates_no_gz_file(self, tmp_path):
        """Formatting (and so validation) happens before the file is opened; covers compression too."""
        gz = tmp_path / "bad.csv.gz"
        with pytest.raises(LibError):
            write_master([full_row(), full_row()], gz)  # duplicate unique key
        assert not gz.exists(), "a failed write_master must not leave a partial .gz"

    def test_bad_input_leaves_existing_gz_untouched(self, tmp_path):
        gz = tmp_path / "keep.csv.gz"
        write_master([full_row()], gz)
        before = gz.read_bytes()
        with pytest.raises(LibError):
            write_master([full_row(), full_row()], gz)
        assert gz.read_bytes() == before


# ---------------------------------------------------------------------------------------------- B
class TestDeterminism:
    def test_two_writes_are_byte_identical(self, tmp_path):
        a, b = tmp_path / "a.csv.gz", tmp_path / "b.csv.gz"
        write_master(rich_rows(), a)
        write_master(rich_rows(), b)
        assert a.read_bytes() == b.read_bytes()

    def test_file_name_and_directory_do_not_matter(self, tmp_path):
        (tmp_path / "sub").mkdir()
        a, b = tmp_path / "a.csv.gz", tmp_path / "sub" / "coal.csv.gz"
        write_master(rich_rows(), a)
        write_master(rich_rows(), b)
        assert a.read_bytes() == b.read_bytes(), "the gzip header must not embed the file name"

    def test_rewriting_same_path_is_identical(self, tmp_path):
        a = tmp_path / "a.csv.gz"
        write_master(rich_rows(), a)
        first = a.read_bytes()
        write_master(rich_rows(), a)
        assert a.read_bytes() == first

    @pytest.mark.parametrize("fake_now", [0.0, 2e9], ids=["epoch", "2033"])
    def test_clock_independent(self, tmp_path, monkeypatch, fake_now):
        ref = tmp_path / "ref.csv.gz"
        write_master(rich_rows(), ref)
        monkeypatch.setattr(time, "time", lambda: fake_now)
        out = tmp_path / "out.csv.gz"
        write_master(rich_rows(), out)
        assert out.read_bytes() == ref.read_bytes(), "output depends on time.time()"
        assert out.read_bytes()[4:8] == b"\x00\x00\x00\x00", "MTIME bytes must be zero"

    def test_header_bytes_exact(self, tmp_path):
        a = tmp_path / "a.csv.gz"
        write_master(rich_rows(), a)
        head = a.read_bytes()[:10]
        assert head == GZ_HEADER, f"gzip header {head.hex(' ')} != {GZ_HEADER.hex(' ')}"

    def test_flg_has_no_fname_fcomment_or_fextra(self, tmp_path):
        a = tmp_path / "some_long_name.csv.gz"
        write_master(rich_rows(), a)
        flg = a.read_bytes()[3]
        assert flg & 0b00011100 == 0, f"FLG={flg:#04x} has FEXTRA/FNAME/FCOMMENT set"

    def test_file_mtime_does_not_change_content(self, tmp_path):
        a, b = tmp_path / "a.csv.gz", tmp_path / "b.csv.gz"
        write_master(rich_rows(), a)
        os.utime(tmp_path, (1, 1))
        write_master(rich_rows(), b)
        assert a.read_bytes() == b.read_bytes()


class TestGzipBytes:
    @pytest.mark.parametrize("data", [b"", b"a", b"x,y\n1,2\n" * 1000, bytes(range(256)) * 50],
                             ids=["empty", "one-byte", "csv", "binary"])
    def test_round_trip_and_reference_equality(self, data):
        gzip_bytes = io_fn("gzip_bytes")
        out = gzip_bytes(data)
        assert isinstance(out, bytes)
        assert gzip.decompress(out) == data
        assert out == gzip.compress(data, 9, mtime=0), "gzip_bytes must equal gzip.compress(x, 9, mtime=0)"
        assert out[:10] == GZ_HEADER

    def test_gzip_level_constant_is_nine(self):
        assert io_fn("GZIP_LEVEL") == 9

    def test_clock_independent(self, monkeypatch):
        gzip_bytes = io_fn("gzip_bytes")
        monkeypatch.setattr(time, "time", lambda: 0.0)
        a = gzip_bytes(b"abc" * 100)
        monkeypatch.setattr(time, "time", lambda: 2e9)
        b = gzip_bytes(b"abc" * 100)
        assert a == b and a[4:8] == b"\x00" * 4

    @pytest.mark.parametrize("bad", ["text", None, 5, ["a"]], ids=["str", "None", "int", "list"])
    def test_non_bytes_raises_liberror(self, bad):
        with pytest.raises(LibError):
            io_fn("gzip_bytes")(bad)


# ---------------------------------------------------------------------------------------------- C
class TestReadBytes:
    def test_gz_path_returns_decompressed_content(self, tmp_path):
        p = tmp_path / "x.csv.gz"
        p.write_bytes(io_fn("gzip_bytes")(b"a,b\r\n\xef\xbb\xbf1,2"))
        assert io_fn("read_bytes")(p) == b"a,b\r\n\xef\xbb\xbf1,2"

    def test_plain_path_returns_raw_bytes_unaltered(self, tmp_path):
        p = tmp_path / "x.csv"
        raw = b"\xef\xbb\xbfa,b\r\n1,2"
        p.write_bytes(raw)
        assert io_fn("read_bytes")(p) == raw

    def test_str_path_accepted(self, tmp_path):
        p = tmp_path / "x.csv.gz"
        p.write_bytes(gzip.compress(b"q", 9, mtime=0))
        assert io_fn("read_bytes")(str(p)) == b"q"

    def test_detection_is_by_suffix_only_and_case_sensitive(self, tmp_path):
        comp = gzip.compress(b"payload", 9, mtime=0)
        upper = tmp_path / "x.csv.GZ"
        upper.write_bytes(comp)
        assert io_fn("read_bytes")(upper) == comp, "'.GZ' is not '.gz': read as plain (case-sensitive)"
        disguised = tmp_path / "x.csv"
        disguised.write_bytes(comp)
        assert io_fn("read_bytes")(disguised) == comp, "no content sniffing: a gzip file named .csv is plain"

    def test_bare_gz_suffix_is_gzip(self, tmp_path):
        p = tmp_path / "x.gz"
        p.write_bytes(gzip.compress(b"z", 9, mtime=0))
        assert io_fn("read_bytes")(p) == b"z"

    def test_missing_file_raises_liberror_naming_path(self, tmp_path):
        p = tmp_path / "nope.csv.gz"
        with pytest.raises(LibError) as ei:
            io_fn("read_bytes")(p)
        assert "nope.csv.gz" in str(ei.value)


class TestUppercaseGzSuffix:
    """Suffix detection is case-sensitive (LIB_SPEC 11.3.2)."""

    @pytest.mark.parametrize("name", ["x.csv.GZ", "x.GZ", "x.csv.Gz"])
    def test_read_bytes_treats_uppercase_suffix_as_plain(self, tmp_path, name):
        comp = gzip.compress(b"payload", 9, mtime=0)
        p = tmp_path / name
        p.write_bytes(comp)
        assert io_fn("read_bytes")(p) == comp

    @pytest.mark.parametrize("name", ["x.csv.GZ", "x.GZ"])
    def test_read_table_treats_uppercase_suffix_as_plain_text(self, tmp_path, name):
        read_table = io_fn("read_table")
        header = (",".join(MASTER_COLUMNS) + "\n").encode()
        p = tmp_path / name
        p.write_bytes(header)               # plain CSV content under an upper-case suffix
        assert read_table(p) == []
        q = tmp_path / ("gzipped_" + name)
        q.write_bytes(io_fn("gzip_bytes")(header))   # real gzip under the same suffix is NOT decompressed
        with pytest.raises(LibError):
            read_table(q)

    def test_resolve_stream_file_ignores_uppercase_gz(self, tmp_path):
        resolve = io_fn("resolve_stream_file")
        (tmp_path / "coal.csv.GZ").write_bytes(b"x")
        assert resolve(tmp_path, "coal") is None
        (tmp_path / "coal.csv").write_bytes(b"y")
        assert Path(resolve(tmp_path, "coal")) == tmp_path / "coal.csv", "no both-forms error for .GZ"
        (tmp_path / "coal.csv.gz").write_bytes(b"z")
        with pytest.raises(LibError):
            resolve(tmp_path, "coal")


class TestReadTableGz:
    def test_same_result_for_csv_and_csv_gz(self, tmp_path):
        read_table = io_fn("read_table")
        plain, gz = tmp_path / "a.csv", tmp_path / "a.csv.gz"
        write_master(rich_rows(), plain)
        gz.write_bytes(io_fn("gzip_bytes")(plain.read_bytes()))
        assert read_table(gz) == read_table(plain)
        assert read_table(gz)[1]["notes"] == "café, naïve µ 東京"

    def test_utf8_sig_bom_inside_gz_is_tolerated_like_plain(self, tmp_path):
        read_table = io_fn("read_table")
        body = b"\xef\xbb\xbf" + (",".join(MASTER_COLUMNS) + "\n").encode()
        plain, gz = tmp_path / "b.csv", tmp_path / "b.csv.gz"
        plain.write_bytes(body)
        gz.write_bytes(io_fn("gzip_bytes")(body))
        assert read_table(gz) == read_table(plain) == []

    def test_legacy_plain_form_still_readable(self, tmp_path):
        p = tmp_path / "legacy.csv"
        write_master(rich_rows(), p)
        rows = io_fn("read_table")(p)
        assert [r["year"] for r in rows] == [1990, 1991, 1992, 1993]

    def test_same_errors_as_plain_for_bad_cell(self, tmp_path):
        read_table = io_fn("read_table")
        body = (",".join(MASTER_COLUMNS) + "\n" + ",".join(["notayear"] + [""] * (len(MASTER_COLUMNS) - 1)) + "\n").encode()
        plain, gz = tmp_path / "c.csv", tmp_path / "c.csv.gz"
        plain.write_bytes(body)
        gz.write_bytes(io_fn("gzip_bytes")(body))
        with pytest.raises(LibError):
            read_table(plain)
        with pytest.raises(LibError):
            read_table(gz)


def _corrupt_variants(tmp_path):
    good = io_fn("gzip_bytes")(big_content())
    crc = bytearray(good)
    crc[-8] ^= 0xFF
    return {
        "plain-text-named-gz": big_content(),
        "truncated-last-10": good[:-10],
        "bad-crc": bytes(crc),
        "empty-file": b"",
    }


@pytest.mark.parametrize("variant", ["plain-text-named-gz", "truncated-last-10", "bad-crc", "empty-file"])
@pytest.mark.parametrize("reader", ["read_table", "read_bytes"])
class TestCorruptGz:
    def test_raises_liberror_naming_path(self, tmp_path, variant, reader):
        p = tmp_path / f"{variant}.csv.gz"
        p.write_bytes(_corrupt_variants(tmp_path)[variant])
        with pytest.raises(LibError) as ei:
            io_fn(reader)(p)
        assert p.name in str(ei.value) or str(p) in str(ei.value), (
            f"LibError for {variant} must name the path; got: {ei.value}")

    def test_does_not_modify_the_file(self, tmp_path, variant, reader):
        p = tmp_path / f"{variant}.csv.gz"
        p.write_bytes(_corrupt_variants(tmp_path)[variant])
        before = p.read_bytes()
        with pytest.raises(LibError):
            io_fn(reader)(p)
        assert p.read_bytes() == before


class TestFirstDifference:
    A = b"head\nl2\nl3\n"

    def test_equal_gives_none(self):
        fd = io_fn("first_difference")
        assert fd(self.A, self.A) is None
        assert fd(b"", b"") is None

    def test_difference_in_header_is_line_1(self):
        assert io_fn("first_difference")(self.A, b"HEAD\nl2\nl3\n") == 1

    @pytest.mark.parametrize("k", [2, 3, 4])
    def test_difference_at_line_k(self, k):
        fd = io_fn("first_difference")
        lines = [b"head\n", b"l2\n", b"l3\n", b"l4\n", b"l5\n"]
        other = list(lines)
        other[k - 1] = b"CHANGED\n"
        assert fd(b"".join(lines), b"".join(other)) == k
        assert fd(b"".join(other), b"".join(lines)) == k

    def test_first_of_several_differences_is_reported(self):
        assert io_fn("first_difference")(b"h\na\nb\nc\n", b"h\nA\nB\nC\n") == 2

    def test_extra_trailing_lines_report_first_extra_line(self):
        fd = io_fn("first_difference")
        assert fd(self.A, self.A + b"l4\nl5\n") == 4
        assert fd(self.A + b"l4\nl5\n", self.A) == 4

    def test_missing_final_newline_is_a_difference_on_that_line(self):
        fd = io_fn("first_difference")
        assert fd(b"head\nl2\nl3", self.A) == 3
        assert fd(self.A, b"head\nl2\nl3") == 3

    def test_empty_versus_nonempty_is_line_1(self):
        fd = io_fn("first_difference")
        assert fd(b"", b"x\n") == 1
        assert fd(b"x\n", b"") == 1

    def test_lone_cr_is_not_a_line_break(self):  # ambiguity A2
        assert io_fn("first_difference")(b"h\na\rb\nc\n", b"h\na\rb\nd\n") == 3

    @pytest.mark.parametrize("a,b", [("text", b"x"), (b"x", "text"), (None, b"x"), (b"x", None), (1, 2)])
    def test_non_bytes_raises_liberror(self, a, b):
        with pytest.raises(LibError):
            io_fn("first_difference")(a, b)

    def test_integer_result_type(self):
        r = io_fn("first_difference")(b"a\n", b"b\n")
        assert type(r) is int


# ---------------------------------------------------------------------------------------------- D
class TestResolveStreamFile:
    def test_only_gz_returns_gz_path(self, tmp_path):
        (tmp_path / "coal.csv.gz").write_bytes(b"x")
        assert Path(io_fn("resolve_stream_file")(tmp_path, "coal")) == tmp_path / "coal.csv.gz"

    def test_only_plain_returns_plain_path(self, tmp_path):
        (tmp_path / "coal.csv").write_bytes(b"x")
        assert Path(io_fn("resolve_stream_file")(tmp_path, "coal")) == tmp_path / "coal.csv"

    def test_neither_returns_none(self, tmp_path):
        (tmp_path / "other.csv").write_bytes(b"x")
        assert io_fn("resolve_stream_file")(tmp_path, "coal") is None

    def test_str_directory_accepted(self, tmp_path):
        (tmp_path / "coal.csv.gz").write_bytes(b"x")
        assert Path(io_fn("resolve_stream_file")(str(tmp_path), "coal")) == tmp_path / "coal.csv.gz"

    def test_both_present_raises_naming_both(self, tmp_path):
        (tmp_path / "coal.csv").write_bytes(b"x")
        (tmp_path / "coal.csv.gz").write_bytes(b"y")
        with pytest.raises(LibError) as ei:
            io_fn("resolve_stream_file")(tmp_path, "coal")
        msg = str(ei.value)
        assert "coal.csv.gz" in msg and "coal.csv" in msg.replace("coal.csv.gz", ""), (
            f"the error must name both files; got: {msg}")

    def test_both_present_leaves_files_untouched(self, tmp_path):
        (tmp_path / "coal.csv").write_bytes(b"x")
        (tmp_path / "coal.csv.gz").write_bytes(b"y")
        with pytest.raises(LibError):
            io_fn("resolve_stream_file")(tmp_path, "coal")
        assert (tmp_path / "coal.csv").read_bytes() == b"x" and (tmp_path / "coal.csv.gz").read_bytes() == b"y"

    @pytest.mark.parametrize("dirname", ["coal.csv", "coal.csv.gz"])
    def test_directory_with_either_name_raises(self, tmp_path, dirname):
        (tmp_path / dirname).mkdir()
        with pytest.raises(LibError):
            io_fn("resolve_stream_file")(tmp_path, "coal")

    def test_directory_beside_a_real_file_still_raises(self, tmp_path):
        (tmp_path / "coal.csv").mkdir()
        (tmp_path / "coal.csv.gz").write_bytes(b"y")
        with pytest.raises(LibError):
            io_fn("resolve_stream_file")(tmp_path, "coal")

    def test_other_streams_in_the_directory_are_ignored(self, tmp_path):
        (tmp_path / "coal.csv").write_bytes(b"x")
        (tmp_path / "nuclear.csv.gz").write_bytes(b"y")
        assert Path(io_fn("resolve_stream_file")(tmp_path, "coal")) == tmp_path / "coal.csv"
        assert Path(io_fn("resolve_stream_file")(tmp_path, "nuclear")) == tmp_path / "nuclear.csv.gz"


# ---------------------------------------------------------------------------------------------- H
def _committed_other():
    d = REAL_ROOT / "data" / "streams"
    for name in ("other.csv.gz", "other.csv"):
        if (d / name).is_file():
            return d / name
    return None


@pytest.fixture(scope="module")
def other_content():
    src = _committed_other()
    if src is None:
        pytest.skip("neither data/streams/other.csv.gz nor other.csv exists: nothing to time (LIB_SPEC 11.8 H)")
    return gzip.decompress(src.read_bytes()) if src.name.endswith(".gz") else src.read_bytes()


@pytest.fixture(scope="module")
def other_pair(other_content, tmp_path_factory):
    d = tmp_path_factory.mktemp("perf_other")
    plain, gz = d / "other.csv", d / "other.csv.gz"
    plain.write_bytes(other_content)
    gz.write_bytes(gzip.compress(other_content, 9, mtime=0))
    return plain, gz


class TestPerformance:
    def test_h1_gzip_bytes_within_5_seconds(self, other_content):
        gzip_bytes = io_fn("gzip_bytes")
        t0 = time.perf_counter()
        out = gzip_bytes(other_content)
        dt = time.perf_counter() - t0
        assert gzip.decompress(out) == other_content
        assert dt <= 5.0, f"gzip_bytes took {dt:.2f} s on {len(other_content)/1e6:.0f} MB (budget 5 s)"

    def test_h2_write_master_gz_within_20_seconds(self, other_pair, tmp_path):
        rows = io_fn("read_table")(other_pair[0])
        out = tmp_path / "other.csv.gz"
        t0 = time.perf_counter()
        write_master(rows, out)
        dt = time.perf_counter() - t0
        assert dt <= 20.0, f"write_master to .csv.gz took {dt:.2f} s (budget 20 s)"
        assert gzip.decompress(out.read_bytes()) == other_pair[0].read_bytes(), (
            "round trip read_table -> write_master must reproduce the committed content byte for byte")

    def test_h3_read_table_gz_close_to_plain(self, other_pair):
        read_table = io_fn("read_table")
        plain, gz = other_pair
        t0 = time.perf_counter()
        a = read_table(plain)
        t_plain = time.perf_counter() - t0
        t0 = time.perf_counter()
        b = read_table(gz)
        t_gz = time.perf_counter() - t0
        assert len(a) == len(b)
        assert t_gz <= 1.5 * t_plain + 2.0, (
            f"read_table(.gz) {t_gz:.2f} s vs plain {t_plain:.2f} s; budget 1.5 x plain + 2 s")
