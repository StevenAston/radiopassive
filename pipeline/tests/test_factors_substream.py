"""Spec-blind validator tests for SCHEMA v2.4 (D63): `substream` column in factor files (4.9).

Ambiguities (assertions deliberately accept the documented alternatives):
A1. Invalid substream value for the stream: SCHEMA 6 gives no explicit code. V01 is the master-row
    code "substream not allowed for stream"; T04 is "reference does not resolve" for factors;
    T01 is schema failure. SCHEMA says membership is NOT a JSON-schema matter, so T01 is unlikely.
    Resolved (orchestrator, 2026-10-27): SCHEMA §6 now lists substream under T04 for the factor
    registry, so the test requires exactly T04.
A2. Header problems (missing column, wrong position) are F01 per 6.1 ("exactly the specified
    columns, in order"); F01 stops row validation for that file.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from pipeline.validate import validate

FIXTURES = Path(__file__).resolve().parent / "fixtures"
REAL_ROOT = Path(__file__).resolve().parents[2]
REL = "data/factors/coal.csv"


def _fixture():
    with open(FIXTURES / "factors_coal.csv", newline="", encoding="utf-8") as fh:
        r = csv.DictReader(fh)
        return list(r.fieldnames), list(r)


def _write(root, header, rows, rel=REL):
    with open(Path(root) / rel, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=header, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def install(root, substreams=("", ""), position="after_stage", drop=False):
    """Install fixture coal factors with a substream column (v2.4 layout by default)."""
    header, rows = _fixture()
    # The shared fixture gained the v2.4 column (orchestrator, 2026-10-27); start from the
    # pre-v2.4 layout so each test controls the column's presence and position itself.
    header = [h for h in header if h != "substream"]
    for row in rows:
        row.pop("substream", None)
    for row, s in zip(rows, substreams):
        row["substream"] = s
    base = list(header)
    if not drop:
        if position == "after_stage":
            base.insert(base.index("stage") + 1, "substream")
        elif position == "end":
            base.append("substream")
        elif position == "before_stage":
            base.insert(base.index("stage"), "substream")
        elif position == "after_stream":  # i.e. before stage, directly after stream
            base.insert(base.index("stream") + 1, "substream")
    _write(root, base, rows)


def desc(issues):
    return "\n".join(f"  {i.file}:{i.row}: {i.rule} {i.message}" for i in issues) or "  (none)"


def in_factors(issues):
    return [i for i in issues if i.file == REL]


# ------------------------------------------------------------------ header rule (F01)
def test_valid_header_with_substream_after_stage_is_clean(tmp_root):
    install(tmp_root)
    assert validate(tmp_root, []) == [], desc(validate(tmp_root, []))


def test_header_without_substream_is_f01(tmp_root):
    install(tmp_root, drop=True)
    issues = in_factors(validate(tmp_root, []))
    assert any(i.rule == "F01" for i in issues), "missing substream column must be F01:\n" + desc(issues)


@pytest.mark.parametrize("position", ["end", "after_stream"])
def test_substream_in_wrong_position_is_f01(tmp_root, position):
    install(tmp_root, position=position)
    issues = in_factors(validate(tmp_root, []))
    assert any(i.rule == "F01" for i in issues), f"substream at {position} must be F01:\n" + desc(issues)


def test_f01_file_rows_not_validated(tmp_root):
    # A bad substream value in a file whose header is wrong must not add row-level issues.
    install(tmp_root, substreams=("not_a_substream", ""), position="end")
    issues = in_factors(validate(tmp_root, []))
    assert {i.rule for i in issues} == {"F01"}, desc(issues)


# ------------------------------------------------------------------ values
@pytest.mark.parametrize("value", ["power", "non_power", "all"])
def test_valid_coal_substream_values_are_clean(tmp_root, value):
    install(tmp_root, substreams=(value, value))
    assert validate(tmp_root, []) == [], desc(validate(tmp_root, []))


def test_empty_substream_value_is_ok(tmp_root):
    install(tmp_root, substreams=("", "power"))
    assert validate(tmp_root, []) == [], desc(validate(tmp_root, []))


@pytest.mark.parametrize("bad", ["conventional", "pwr", "nonsense", "Power"])
def test_substream_not_in_vocab_for_stream(tmp_root, bad):
    # 'conventional' and 'pwr' exist in vocab, but for other streams (oil_gas / nuclear), not coal.
    install(tmp_root, substreams=("power", bad))
    issues = validate(tmp_root, [])
    hit = [i for i in in_factors(issues) if i.row == 2]
    assert hit, f"expected an issue on factors row 2:\n{desc(issues)}"
    assert {i.rule for i in hit} == {"T04"}, desc(issues)  # SCHEMA §6 (v2.4): T04
    assert not any(i.rule == "F01" for i in issues), desc(issues)
    assert not [i for i in in_factors(issues) if i.row == 1], "row 1 is valid:\n" + desc(issues)


def test_vocab_is_per_stream_not_global(tmp_root):
    vocab = json.loads((tmp_root / "data" / "reference" / "vocab.json").read_text())
    assert "power" in vocab["substreams"]["coal"] and "power" not in vocab["substreams"]["nuclear"]


# ------------------------------------------------------------------ real tree (eventual state)
def test_real_tree_validates_once_real_factor_files_have_substream():
    """Eventual state: every data/factors/*.csv carries `substream` directly after `stage`."""
    for f in sorted((REAL_ROOT / "data" / "factors").glob("*.csv")):
        header = next(csv.reader(open(f, newline="", encoding="utf-8")))
        assert header[header.index("stage") + 1] == "substream", f"{f.name}: substream column missing/misplaced"
    issues = validate(REAL_ROOT, [])
    assert [i for i in issues if i.file.startswith("data/factors")] == [], desc(issues)
