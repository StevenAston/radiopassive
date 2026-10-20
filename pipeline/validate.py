"""Radiopassive data validator.

Implements the contract in docs/SCHEMA.md §6: checks master-format CSVs and the
reference tables (sources, events, nuclides, groups) against the schema, the
controlled vocabularies and the cross-row rules, and reports every problem as
an ``Issue`` with a rule code from SCHEMA §6.3.

Usage:
    python -m pipeline.validate [--root DIR] [FILE ...]
    pixi run validate

Only the standard library and ``jsonschema`` are used. Everything runs in a
single process.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

from jsonschema import Draft7Validator

# --------------------------------------------------------------------------
# Column specifications (SCHEMA §3, §4)
# --------------------------------------------------------------------------

MASTER_COLUMNS = [
    "year", "stream", "substream", "stage", "country", "group", "tier",
    "quantity", "unit", "value_low", "value_central", "value_high",
    "below_detection", "basis", "source_ids", "allocation_variant",
    "allocation_rule", "embedded_fuel", "technology", "event_id", "notes",
]
SOURCES_COLUMNS = [
    "source_id", "short_cite", "full_citation", "url", "doi", "year", "type",
    "rank", "access", "licence", "notes",
]
EVENTS_COLUMNS = [
    "event_id", "name", "date_start", "date_end", "country", "location", "lat",
    "lon", "stream", "stage", "event_type", "is_accident", "from_tier",
    "to_tier", "mass_t", "activity_central_bq", "inclusion", "military",
    "source_ids", "notes",
]
NUCLIDES_COLUMNS = [
    "nuclide", "half_life_value", "half_life_unit", "half_life_a",
    "lambda_per_a", "decay_modes", "daughters", "branching", "e_alpha_mev",
    "e_recoil_mev", "e_beta_mev", "e_photon_mev", "e_electron_mev",
    "e_total_mev", "source_ids", "notes",
]
GROUPS_COLUMNS = [
    "group", "head", "members", "member_weights", "multiplier",
    "e_per_head_decay_mev", "chain", "role", "multiplier_scope",
    "parent_group", "parent_branching", "notes",
]

# Unique key of a master row (SCHEMA §3).
KEY_COLUMNS = [
    "year", "stream", "substream", "stage", "country", "group", "tier",
    "quantity", "allocation_variant", "embedded_fuel", "technology", "event_id",
]
ALLOCATION_VARIANTS = {"default", "bound_main", "bound_radio"}
URANIUM_STAGES = {"u_mining_conv", "u_mining_isl", "u_milling"}
TRANSFER_QUANTITIES = {"transfer_out", "transfer_in"}

NULLABLE_MASTER = {"technology", "event_id", "notes"}
INT_MASTER = {"year"}
FLOAT_MASTER = {"value_low", "value_central", "value_high"}
BOOL_MASTER = {"below_detection", "embedded_fuel"}
LIST_MASTER = {"source_ids"}

REL_TOL_BALANCE = 1e-6
REL_TOL_REFERENCE = 1e-6
BRANCHING_TOL = 1e-4

# --------------------------------------------------------------------------
# Data structures
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Issue:
    """One validation problem (SCHEMA §6.1)."""

    file: str
    row: int | None
    rule: str
    message: str


class _CoercionError(ValueError):
    """A cell could not be converted to its type."""


@dataclass
class _Table:
    """A CSV read from disk: its display name, header and data rows."""

    name: str
    header: list[str]
    rows: list[list[str]]
    ok: bool  # False if the file could not be read or its header is wrong


@dataclass
class _Reference:
    """Everything the master checks look up."""

    vocab: dict
    countries: dict[str, tuple[int | None, int | None]]
    group_scope: dict[str, str]
    source_ids: set[str]
    events: dict[str, dict]
    master_validator: Draft7Validator
    sources_validator: Draft7Validator
    events_validator: Draft7Validator


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------


def _display_name(path: Path, root: Path) -> str:
    """Path relative to root with POSIX separators, else absolute POSIX."""
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _rel_close(a: float, b: float, tol: float) -> bool:
    """True if a and b agree within relative tolerance tol."""
    scale = max(abs(a), abs(b))
    if scale == 0.0:
        return True
    return abs(a - b) <= tol * scale


def _to_int(text: str) -> int:
    text = text.strip()
    try:
        return int(text)
    except ValueError as exc:
        raise _CoercionError(f"not an integer: {text!r}") from exc


def _to_float(text: str) -> float:
    text = text.strip()
    try:
        value = float(text)
    except ValueError as exc:
        raise _CoercionError(f"not a number: {text!r}") from exc
    if math.isnan(value) or math.isinf(value):
        raise _CoercionError(f"not a finite number: {text!r}")
    return value


def _to_bool(text: str) -> bool:
    text = text.strip()
    if text == "true":
        return True
    if text == "false":
        return False
    raise _CoercionError(f"not 'true' or 'false': {text!r}")


def _to_list(text: str) -> list[str]:
    text = text.strip()
    if not text:
        raise _CoercionError("empty list")
    return text.split(";")


def _float_list(text: str) -> list[float]:
    return [_to_float(part) for part in _to_list(text)]


def _forbidden_columns(header: list[str], tokens: Iterable[str]) -> list[str]:
    """Column names containing a forbidden token as a whole '_' word."""
    forbidden = {t.lower() for t in tokens}
    return [
        name for name in header
        if any(part in forbidden for part in name.strip().lower().split("_"))
    ]


def _schema_messages(validator: Draft7Validator, instance: dict) -> list[str]:
    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.path))
    messages = []
    for error in errors:
        where = ".".join(str(p) for p in error.path) or "(row)"
        messages.append(f"{where}: {error.message}")
    return messages


# --------------------------------------------------------------------------
# Reading files
# --------------------------------------------------------------------------


def _read_csv(path: Path, root: Path, expected: list[str] | None,
              forbidden_tokens: Iterable[str], issues: list[Issue]) -> _Table:
    """Read a CSV, reporting F01/F02/F03. Rows are padded/truncated to the header."""
    name = _display_name(path, root)
    try:
        with open(path, encoding="utf-8", newline="") as handle:
            records = list(csv.reader(handle, strict=True))
    except (UnicodeDecodeError, csv.Error) as exc:
        issues.append(Issue(name, None, "F03", f"cannot read as UTF-8 CSV: {exc}"))
        return _Table(name, [], [], ok=False)

    if not records:
        issues.append(Issue(name, None, "F01", "file is empty (no header row)"))
        return _Table(name, [], [], ok=False)

    header = [h.strip() for h in records[0]]
    if header and header[0].startswith("﻿"):
        header[0] = header[0].lstrip("﻿")
    ok = True

    bad = _forbidden_columns(header, forbidden_tokens)
    if bad:
        issues.append(Issue(name, None, "F02",
                            f"forbidden column name(s): {', '.join(bad)}"))
        ok = False

    if expected is not None and header != expected:
        missing = [c for c in expected if c not in header]
        extra = [c for c in header if c not in expected]
        detail = []
        if missing:
            detail.append(f"missing {missing}")
        if extra:
            detail.append(f"unexpected {extra}")
        if not missing and not extra:
            detail.append("columns out of order")
        issues.append(Issue(name, None, "F01",
                            "header does not match specification: " + "; ".join(detail)))
        ok = False

    rows = [r for r in records[1:] if any(cell.strip() for cell in r)]
    width = len(header)
    rows = [(r + [""] * width)[:width] for r in rows]
    return _Table(name, header, rows, ok=ok)


def _as_dicts(table: _Table) -> list[dict[str, str]]:
    return [dict(zip(table.header, row)) for row in table.rows]


def _require(path: Path) -> Path:
    if not path.is_file():
        raise FileNotFoundError(f"required reference file not found: {path}")
    return path


# --------------------------------------------------------------------------
# Reference tables: sources, events, nuclides, groups
# --------------------------------------------------------------------------


def _check_sources(table: _Table, vocab: dict, validator: Draft7Validator,
                   issues: list[Issue]) -> set[str]:
    """S01/S02. Returns every source_id seen (valid or not) for lookups."""
    seen: set[str] = set()
    if not table.ok:
        return seen
    banned = [d.lower() for d in vocab.get("banned_domains", [])]
    for index, raw in enumerate(_as_dicts(table), start=1):
        sid = raw["source_id"].strip()
        problems: list[str] = []
        record: dict = {}
        for key, value in raw.items():
            value = value.strip()
            if key in ("year", "rank"):
                try:
                    record[key] = _to_int(value)
                except _CoercionError as exc:
                    problems.append(f"{key}: {exc}")
            elif key in ("url", "doi", "notes"):
                record[key] = value or None
            else:
                record[key] = value
        if not problems:
            problems.extend(_schema_messages(validator, record))
        if sid in seen:
            problems.append(f"duplicate source_id {sid!r}")
        if problems:
            issues.append(Issue(table.name, index, "S01", "; ".join(problems)))
        if sid:
            seen.add(sid)

        url = raw["url"].strip()
        if url:
            host = (urlparse(url).hostname or "").lower()
            for domain in banned:
                if host == domain or host.endswith("." + domain):
                    issues.append(Issue(table.name, index, "S02",
                                        f"url on banned domain {domain!r}: {url}"))
                    break
    return seen


def _check_events(table: _Table | None, vocab: dict, validator: Draft7Validator,
                  countries: dict, source_ids: set[str],
                  issues: list[Issue]) -> dict[str, dict]:
    """E01/E02. Returns events by ID (coerced where possible) for lookups."""
    events: dict[str, dict] = {}
    if table is None or not table.ok:
        return events
    stages = vocab["stages"]
    for index, raw in enumerate(_as_dicts(table), start=1):
        problems: list[str] = []
        record: dict = {}
        for key, value in raw.items():
            value = value.strip()
            try:
                if key in ("lat", "lon", "mass_t", "activity_central_bq"):
                    record[key] = _to_float(value) if value else None
                elif key in ("is_accident", "military"):
                    record[key] = _to_bool(value)
                elif key == "source_ids":
                    record[key] = _to_list(value)
                elif key in ("date_end", "location", "notes"):
                    record[key] = value or None
                else:
                    record[key] = value
            except _CoercionError as exc:
                problems.append(f"{key}: {exc}")
                record[key] = None
        if not problems:
            problems.extend(_schema_messages(validator, record))
        eid = raw["event_id"].strip()
        if eid in events:
            problems.append(f"duplicate event_id {eid!r}")
        if problems:
            issues.append(Issue(table.name, index, "E01", "; ".join(problems)))

        membership: list[str] = []
        stream, stage = record.get("stream"), record.get("stage")
        if stream in stages and stage not in stages[stream]:
            membership.append(f"stage {stage!r} not allowed for stream {stream!r}")
        country = record.get("country")
        if country and country not in countries:
            membership.append(f"unknown country {country!r}")
        for sid in record.get("source_ids") or []:
            if sid not in source_ids:
                membership.append(f"unknown source {sid!r}")
        if membership:
            issues.append(Issue(table.name, index, "E02", "; ".join(membership)))

        if eid and eid not in events:
            events[eid] = record
    return events


def _check_nuclides(table: _Table, issues: list[Issue]) -> set[str]:
    """N01/N02/N03. Returns the nuclide names."""
    names: set[str] = set()
    if not table.ok:
        return names
    components = ["e_alpha_mev", "e_recoil_mev", "e_beta_mev",
                  "e_photon_mev", "e_electron_mev"]
    for index, raw in enumerate(_as_dicts(table), start=1):
        names.add(raw["nuclide"].strip())

        try:
            daughters = _to_list(raw["daughters"])
            branching = _float_list(raw["branching"])
            if len(daughters) != len(branching):
                issues.append(Issue(table.name, index, "N01",
                                    f"{len(daughters)} daughters but {len(branching)} branching values"))
            elif abs(sum(branching) - 1.0) > BRANCHING_TOL:
                issues.append(Issue(table.name, index, "N01",
                                    f"branching sums to {sum(branching):.6g}, not 1"))
        except _CoercionError as exc:
            issues.append(Issue(table.name, index, "N01", f"daughters/branching: {exc}"))

        try:
            parts = [_to_float(raw[c]) for c in components]
            total = _to_float(raw["e_total_mev"])
            if not _rel_close(sum(parts), total, REL_TOL_REFERENCE):
                issues.append(Issue(table.name, index, "N02",
                                    f"e_total_mev {total:.6g} != sum of components {sum(parts):.6g}"))
        except _CoercionError as exc:
            issues.append(Issue(table.name, index, "N02", f"energies: {exc}"))

        try:
            half_life = _to_float(raw["half_life_a"])
            lam = _to_float(raw["lambda_per_a"])
            expected = math.log(2) / half_life if half_life > 0 else math.inf
            if not _rel_close(lam, expected, REL_TOL_REFERENCE):
                issues.append(Issue(table.name, index, "N03",
                                    f"lambda_per_a {lam:.6g} != ln2/half_life_a {expected:.6g}"))
        except _CoercionError as exc:
            issues.append(Issue(table.name, index, "N03", f"half-life/lambda: {exc}"))
    return names


def _check_groups(table: _Table, nuclides: set[str],
                  issues: list[Issue]) -> dict[str, str]:
    """G01/G02/G03. Returns {group: multiplier_scope}."""
    scope: dict[str, str] = {}
    if not table.ok:
        return scope
    for index, raw in enumerate(_as_dicts(table), start=1):
        group = raw["group"].strip()
        scope[group] = raw["multiplier_scope"].strip()

        head = raw["head"].strip()
        try:
            members = _to_list(raw["members"])
        except _CoercionError:
            members = []
        unknown = [n for n in [head, *members] if n and n not in nuclides]
        if not head or not members or unknown:
            detail = f"unknown nuclide(s): {sorted(set(unknown))}" if unknown else "missing head or members"
            issues.append(Issue(table.name, index, "G01", detail))

        try:
            weights = _float_list(raw["member_weights"])
            multiplier = _to_float(raw["multiplier"])
            if len(weights) != len(members):
                issues.append(Issue(table.name, index, "G02",
                                    f"{len(members)} members but {len(weights)} weights"))
            elif not _rel_close(sum(weights), multiplier, REL_TOL_REFERENCE):
                issues.append(Issue(table.name, index, "G02",
                                    f"multiplier {multiplier:.6g} != sum of member_weights {sum(weights):.6g}"))
        except _CoercionError as exc:
            issues.append(Issue(table.name, index, "G02", f"weights/multiplier: {exc}"))

        role = raw["role"].strip()
        if (scope[group] == "flow_only") != (role == "released_gas"):
            issues.append(Issue(table.name, index, "G03",
                                f"multiplier_scope {scope[group]!r} inconsistent with role {role!r}"))
    return scope


# --------------------------------------------------------------------------
# Master files
# --------------------------------------------------------------------------


@dataclass
class _MasterRow:
    file: str
    row: int
    raw: dict[str, str]
    record: dict
    coerced: bool  # False if any cell failed coercion (R01)


def _coerce_master(raw: dict[str, str]) -> tuple[dict, list[str]]:
    record: dict = {}
    problems: list[str] = []
    for key in MASTER_COLUMNS:
        value = raw[key].strip()
        if key in NULLABLE_MASTER:
            record[key] = value or None
            continue
        if not value and key not in LIST_MASTER:
            problems.append(f"{key}: empty required cell")
            record[key] = None
            continue
        try:
            if key in INT_MASTER:
                record[key] = _to_int(value)
            elif key in FLOAT_MASTER:
                record[key] = _to_float(value)
            elif key in BOOL_MASTER:
                record[key] = _to_bool(value)
            elif key in LIST_MASTER:
                record[key] = _to_list(value)
            else:
                record[key] = value
        except _CoercionError as exc:
            problems.append(f"{key}: {exc}")
            record[key] = None
    return record, problems


def _check_master_row(mrow: _MasterRow, ref: _Reference,
                      issues: list[Issue]) -> None:
    """Row-level (R*) and vocabulary (V*) checks for one master row."""
    rec, vocab = mrow.record, ref.vocab

    if mrow.coerced:
        messages = _schema_messages(ref.master_validator, rec)
        if messages:
            issues.append(Issue(mrow.file, mrow.row, "R02", "; ".join(messages)))
        low, central, high = rec["value_low"], rec["value_central"], rec["value_high"]
        if not (low <= central <= high):
            issues.append(Issue(mrow.file, mrow.row, "R03",
                                f"bounds not ordered: low={low:g}, central={central:g}, high={high:g}"))

    stream, stage, tier = rec.get("stream"), rec.get("stage"), rec.get("tier")
    stream_ok = stream in vocab["substreams"]
    if stream_ok:
        substream = rec.get("substream")
        if substream is not None and substream not in vocab["substreams"][stream]:
            issues.append(Issue(mrow.file, mrow.row, "V01",
                                f"substream {substream!r} not allowed for stream {stream!r}"))
        stage_ok = stage is not None and stage in vocab["stages"][stream]
        if stage is not None and not stage_ok:
            issues.append(Issue(mrow.file, mrow.row, "V02",
                                f"stage {stage!r} not allowed for stream {stream!r}"))
        if (stage_ok and tier in vocab["tiers"]
                and rec.get("quantity") not in TRANSFER_QUANTITIES
                and tier not in vocab["stage_tiers"][stage]):
            issues.append(Issue(mrow.file, mrow.row, "V03",
                                f"tier {tier!r} not allowed for stage {stage!r}"))

    group = rec.get("group")
    if group is not None and group not in ref.group_scope:
        issues.append(Issue(mrow.file, mrow.row, "V04", f"unknown group {group!r}"))

    country = rec.get("country")
    if country is not None:
        if country not in ref.countries:
            issues.append(Issue(mrow.file, mrow.row, "V05", f"unknown country {country!r}"))
        elif rec.get("year") is not None:
            start, end = ref.countries[country]
            year = rec["year"]
            if (start is not None and year < start) or (end is not None and year > end):
                issues.append(Issue(mrow.file, mrow.row, "V06",
                                    f"country {country!r} valid {start}-{end}, used in {year}"))

    unknown_sources = [s for s in rec.get("source_ids") or [] if s not in ref.source_ids]
    if unknown_sources:
        issues.append(Issue(mrow.file, mrow.row, "V07", f"unknown source(s) {unknown_sources}"))

    event_id = rec.get("event_id")
    if event_id is not None and event_id not in ref.events:
        issues.append(Issue(mrow.file, mrow.row, "V08", f"unknown event {event_id!r}"))

    if (group in ref.group_scope and ref.group_scope[group] == "flow_only"
            and rec.get("quantity") is not None and rec["quantity"] != "flow"):
        issues.append(Issue(mrow.file, mrow.row, "V09",
                            f"flow-only group {group!r} used with quantity {rec['quantity']!r}"))


def _check_cross_rows(rows: list[_MasterRow], ref: _Reference,
                      issues: list[Issue]) -> None:
    """Cross-row rules X01-X05 over all master rows together."""
    # X01: duplicate unique key, reported on the later occurrence.
    first_seen: dict[tuple, _MasterRow] = {}
    for mrow in rows:
        key = tuple(mrow.raw[c].strip() for c in KEY_COLUMNS)
        if key in first_seen:
            earlier = first_seen[key]
            issues.append(Issue(mrow.file, mrow.row, "X01",
                                f"duplicate key; first at {earlier.file}:{earlier.row}"))
        else:
            first_seen[key] = mrow

    # X02: transfers balance per (event_id, year, group, allocation_variant).
    balances: dict[tuple, dict] = {}
    for mrow in rows:
        quantity = mrow.raw["quantity"].strip()
        event_id = mrow.raw["event_id"].strip()
        if quantity not in TRANSFER_QUANTITIES or not event_id:
            continue
        key = (event_id, mrow.raw["year"].strip(), mrow.raw["group"].strip(),
               mrow.raw["allocation_variant"].strip())
        entry = balances.setdefault(key, {
            "file": mrow.file, "skip": False,
            "transfer_out": [0.0, 0.0, 0.0], "transfer_in": [0.0, 0.0, 0.0],
        })
        if not mrow.coerced:
            entry["skip"] = True
            continue
        values = (mrow.record["value_low"], mrow.record["value_central"],
                  mrow.record["value_high"])
        for i, value in enumerate(values):
            entry[quantity][i] += value
    for (event_id, year, group, variant), entry in balances.items():
        if entry["skip"]:
            continue
        out, into = entry["transfer_out"], entry["transfer_in"]
        if not all(_rel_close(o, n, REL_TOL_BALANCE) for o, n in zip(out, into)):
            issues.append(Issue(entry["file"], None, "X02",
                                f"transfers unbalanced for event {event_id} {year} {group} ({variant}): "
                                f"out={out[1]:g}, in={into[1]:g} (central)"))

    # X03: allocation completeness.
    variant_index = KEY_COLUMNS.index("allocation_variant")
    by_key: dict[tuple, list[_MasterRow]] = {}
    for mrow in rows:
        if not mrow.coerced:
            continue
        key = tuple(mrow.raw[c].strip() for i, c in enumerate(KEY_COLUMNS) if i != variant_index)
        by_key.setdefault(key, []).append(mrow)
    for members in by_key.values():
        variants = {m.raw["allocation_variant"].strip() for m in members}
        if variants - {"default"} and not ALLOCATION_VARIANTS <= variants:
            first = members[0]
            missing = sorted(ALLOCATION_VARIANTS - variants)
            issues.append(Issue(first.file, first.row, "X03",
                                f"allocation variants incomplete; missing {missing}"))

    # X04: civil rule on uranium mining and milling.
    for mrow in rows:
        if not mrow.coerced:
            continue
        rec = mrow.record
        if rec["stream"] == "nuclear" and rec["stage"] in URANIUM_STAGES:
            parts = (rec["allocation_rule"] or "").split(";")
            if not any(p.startswith("civil:") for p in parts):
                issues.append(Issue(mrow.file, mrow.row, "X04",
                                    f"uranium stage {rec['stage']!r} without a civil: allocation rule"))

    # X05: transfer tiers must match the event's from/to tiers.
    for mrow in rows:
        quantity = mrow.raw["quantity"].strip()
        event_id = mrow.raw["event_id"].strip()
        if quantity not in TRANSFER_QUANTITIES or event_id not in ref.events:
            continue
        event = ref.events[event_id]
        expected = event.get("from_tier") if quantity == "transfer_out" else event.get("to_tier")
        tier = mrow.raw["tier"].strip()
        if expected is not None and tier != expected:
            issues.append(Issue(mrow.file, mrow.row, "X05",
                                f"{quantity} tier {tier!r} does not match event {event_id} "
                                f"{'from' if quantity == 'transfer_out' else 'to'}_tier {expected!r}"))


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------


def _load_countries(path: Path) -> dict[str, tuple[int | None, int | None]]:
    countries: dict[str, tuple[int | None, int | None]] = {}
    with open(path, encoding="utf-8", newline="") as handle:
        for raw in csv.DictReader(handle):
            code = (raw.get("code") or "").strip()
            if not code:
                continue
            start = (raw.get("valid_from") or "").strip()
            end = (raw.get("valid_to") or "").strip()
            countries[code] = (int(start) if start else None, int(end) if end else None)
    return countries


def _resolve_master_files(root: Path,
                          master_files: Iterable[str | os.PathLike] | None) -> list[Path]:
    if master_files is None:
        return sorted((root / "data" / "streams").glob("*.csv"))
    resolved = []
    for item in master_files:
        path = Path(item)
        resolved.append(path if path.is_absolute() else root / path)
    return resolved


def _sort_key(issue: Issue) -> tuple:
    return (issue.file, -1 if issue.row is None else issue.row, issue.rule)


def validate(root: str | os.PathLike,
             master_files: Iterable[str | os.PathLike] | None = None) -> list[Issue]:
    """Validate a project root (SCHEMA §6.1). Returns [] when everything is valid."""
    root = Path(root)
    ref_dir = root / "data" / "reference"
    schema_dir = root / "schema"

    vocab = json.loads(_require(ref_dir / "vocab.json").read_text(encoding="utf-8"))
    countries = _load_countries(_require(ref_dir / "countries.csv"))
    nuclides_path = _require(ref_dir / "nuclides.csv")
    groups_path = _require(ref_dir / "groups.csv")
    sources_path = _require(root / "data" / "sources.csv")
    validators = {
        name: Draft7Validator(json.loads(_require(schema_dir / f"{name}.json")
                                         .read_text(encoding="utf-8")))
        for name in ("master", "sources", "events")
    }
    events_path = root / "data" / "events.csv"
    tokens = vocab.get("forbidden_column_tokens", ["dose", "sv", "sievert", "rem"])

    issues: list[Issue] = []

    sources_table = _read_csv(sources_path, root, SOURCES_COLUMNS, tokens, issues)
    source_ids = _check_sources(sources_table, vocab, validators["sources"], issues)

    events_table = (_read_csv(events_path, root, EVENTS_COLUMNS, tokens, issues)
                    if events_path.is_file() else None)
    events = _check_events(events_table, vocab, validators["events"], countries,
                           source_ids, issues)

    nuclides_table = _read_csv(nuclides_path, root, NUCLIDES_COLUMNS, tokens, issues)
    nuclide_names = _check_nuclides(nuclides_table, issues)

    groups_table = _read_csv(groups_path, root, GROUPS_COLUMNS, tokens, issues)
    group_scope = _check_groups(groups_table, nuclide_names, issues)

    ref = _Reference(vocab, countries, group_scope, source_ids, events,
                     validators["master"], validators["sources"], validators["events"])

    master_rows: list[_MasterRow] = []
    for path in _resolve_master_files(root, master_files):
        if not path.is_file():
            issues.append(Issue(_display_name(path, root), None, "F03", "file not found"))
            continue
        table = _read_csv(path, root, MASTER_COLUMNS, tokens, issues)
        if not table.ok:
            continue
        for index, raw in enumerate(_as_dicts(table), start=1):
            record, problems = _coerce_master(raw)
            mrow = _MasterRow(table.name, index, raw, record, coerced=not problems)
            if problems:
                issues.append(Issue(table.name, index, "R01", "; ".join(problems)))
            _check_master_row(mrow, ref, issues)
            master_rows.append(mrow)

    _check_cross_rows(master_rows, ref, issues)
    return sorted(issues, key=_sort_key)


# --------------------------------------------------------------------------
# Command line
# --------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m pipeline.validate",
        description="Validate Radiopassive data files (docs/SCHEMA.md §6).")
    parser.add_argument("--root", default=".", help="project root (default: current directory)")
    parser.add_argument("files", nargs="*", help="master-format CSVs (default: data/streams/*.csv)")
    args = parser.parse_args(argv)

    try:
        issues = validate(args.root, args.files or None)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    for issue in issues:
        row = "-" if issue.row is None else str(issue.row)
        print(f"{issue.file}:{row}: {issue.rule} {issue.message}")
    files = len({i.file for i in issues})
    if issues:
        print(f"{len(issues)} issue(s) in {files} file(s)")
        return 1
    print("OK: no issues")
    return 0


if __name__ == "__main__":
    sys.exit(main())
