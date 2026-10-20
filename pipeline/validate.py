"""Radiopassive data validator (schema v2).

Implements the contract in docs/SCHEMA.md §6: checks master-format CSVs and
every reference and support table against its JSON schema, the controlled
vocabularies and the cross-row rules, and reports every problem as an
``Issue`` with a rule code from SCHEMA §6.3.

Usage:
    python -m pipeline.validate [--root DIR] [FILE ...]
    pixi run validate

Only the standard library and ``jsonschema`` are used. Everything runs in a
single process.
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import math
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable
from urllib.parse import urlparse

from jsonschema import Draft7Validator

# --------------------------------------------------------------------------
# Column specifications (SCHEMA §3, §4)
# --------------------------------------------------------------------------

MASTER_COLUMNS = [
    "year", "stream", "substream", "stage", "product", "residue_type",
    "country", "group", "tier", "quantity", "unit", "value_low",
    "value_central", "value_high", "below_detection", "basis", "source_ids",
    "factor_ids", "allocation_variant", "allocation_rule", "embedded_fuel",
    "technology", "route", "event_id", "notes",
]
SOURCES_COLUMNS = [
    "source_id", "short_cite", "full_citation", "url", "doi", "year", "type",
    "rank", "access", "licence", "notes",
]
EVENTS_COLUMNS = [
    "event_id", "name", "date_start", "date_end", "country", "location", "lat",
    "lon", "stream", "stage", "event_type", "is_accident", "from_tier",
    "to_tiers", "mass_t", "activity_low_bq", "activity_central_bq",
    "activity_high_bq", "inclusion", "military", "source_ids", "notes",
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
    "year", "stream", "substream", "stage", "product", "residue_type",
    "country", "group", "tier", "quantity", "allocation_variant",
    "embedded_fuel", "technology", "route", "event_id",
]
ALLOCATION_VARIANTS = ("default", "bound_main", "bound_radio")
VARIANT_TOKENS = {
    "default": ("alloc:value", "alloc:mass"),
    "bound_main": ("alloc:main",),
    "bound_radio": ("alloc:radio",),
}
TRANSFER_QUANTITIES = {"transfer_out", "transfer_in"}

MASTER_NULLABLE = {"product", "residue_type", "factor_ids", "technology",
                   "route", "event_id", "notes"}
MASTER_TYPES = {
    "year": "int", "value_low": "float", "value_central": "float",
    "value_high": "float", "below_detection": "bool", "embedded_fuel": "bool",
    "source_ids": "list", "factor_ids": "list",
}

REL_TOL_BALANCE = 1e-6
REL_TOL_REFERENCE = 1e-6
BRANCHING_TOL = 1e-4
GROUP_ENUMS = {
    "chain": {"U238", "U235", "Th232", "K40", "artificial"},
    "role": {"chain", "released_gas", "artificial"},
    "multiplier_scope": {"stock_and_flow", "flow_only"},
}

SCHEMA_NAMES = ("master", "sources", "events", "countries", "activity",
                "baselines", "commodity_factors", "factors", "residue_types",
                "reference_bands")

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
    ok: bool  # False if unreadable or its header is wrong / forbidden

    def dicts(self) -> list[dict[str, str]]:
        return [dict(zip(self.header, row)) for row in self.rows]


@dataclass
class _Context:
    """Everything loaded so far, for lookups by later checks."""

    root: Path
    vocab: dict
    validators: dict[str, Draft7Validator]
    issues: list[Issue]
    countries: dict[str, tuple[int | None, int | None]] = field(default_factory=dict)
    source_ids: set[str] = field(default_factory=set)
    nuclides: set[str] = field(default_factory=set)
    groups: dict[str, dict[str, str]] = field(default_factory=dict)
    residue_types: set[str] = field(default_factory=set)
    activity_series: set[str] = field(default_factory=set)
    factor_ids: set[str] = field(default_factory=set)
    events: dict[str, dict] = field(default_factory=dict)

    def add(self, file: str, row: int | None, rule: str, message: str) -> None:
        self.issues.append(Issue(file, row, rule, message))


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------

_WORD_SPLIT = re.compile(r"[^0-9a-zµμ]+")


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


def _words(text: str) -> set[str]:
    """Lower-cased whole words, split on every non-alphanumeric character."""
    return {w for w in _WORD_SPLIT.split(text.lower()) if w}


def _to_int(text: str) -> int:
    text = text.strip()
    if not re.fullmatch(r"[+-]?[0-9]+", text):
        raise _CoercionError(f"not an integer: {text!r}")
    return int(text)


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


_CONVERTERS: dict[str, Callable[[str], object]] = {
    "int": _to_int, "float": _to_float, "bool": _to_bool, "list": _to_list,
}


def _coerce(raw: dict[str, str], types: dict[str, str]) -> tuple[dict, list[str]]:
    """Coerce a support-table row: empty → None; typed columns converted."""
    record: dict = {}
    problems: list[str] = []
    for key, value in raw.items():
        value = value.strip()
        if not value:
            record[key] = None
            continue
        kind = types.get(key, "str")
        if kind == "str":
            record[key] = value
            continue
        try:
            record[key] = _CONVERTERS[kind](value)
        except _CoercionError as exc:
            problems.append(f"{key}: {exc}")
            record[key] = None
    return record, problems


def _schema_messages(validator: Draft7Validator, instance: dict) -> list[str]:
    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.path))
    messages = []
    for error in errors:
        where = ".".join(str(p) for p in error.path) or "(row)"
        messages.append(f"{where}: {error.message}")
    return messages


def _bounds_ok(record: dict, low: str, central: str, high: str) -> bool | None:
    """None if any value is missing; else whether low ≤ central ≤ high."""
    values = (record.get(low), record.get(central), record.get(high))
    if any(v is None for v in values):
        return None
    return values[0] <= values[1] <= values[2]


# --------------------------------------------------------------------------
# Reading files
# --------------------------------------------------------------------------


def _read_csv(ctx: _Context, path: Path, expected: list[str] | None) -> _Table:
    """Read a CSV, reporting F01/F02/F03 and D01. Rows are padded/truncated."""
    name = _display_name(path, ctx.root)
    try:
        with open(path, encoding="utf-8", newline="") as handle:
            records = list(csv.reader(handle, strict=True))
    except (UnicodeDecodeError, csv.Error) as exc:
        ctx.add(name, None, "F03", f"cannot read as UTF-8 CSV: {exc}")
        return _Table(name, [], [], ok=False)

    if not records:
        ctx.add(name, None, "F01", "file is empty (no header row)")
        return _Table(name, [], [], ok=False)

    header = [h.strip() for h in records[0]]
    if header and header[0].startswith("﻿"):
        header[0] = header[0].lstrip("﻿")
    ok = True

    tokens = set(ctx.vocab.get("forbidden_column_tokens", ctx.vocab.get("dose_tokens", [])))
    bad = [h for h in header if _words(h) & tokens]
    if bad:
        ctx.add(name, None, "F02", f"forbidden column name(s): {', '.join(bad)}")
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
        ctx.add(name, None, "F01", "header does not match specification: " + "; ".join(detail))
        ok = False

    rows = [r for r in records[1:] if any(cell.strip() for cell in r)]
    width = len(header)
    rows = [(r + [""] * width)[:width] for r in rows]
    table = _Table(name, header, rows, ok=ok)
    if ok:
        _check_dose_values(ctx, table)
    return table


def _check_dose_values(ctx: _Context, table: _Table) -> None:
    """D01: dose tokens in the values of the checked columns."""
    tokens = set(ctx.vocab.get("dose_tokens", []))
    columns = [c for c in ctx.vocab.get("value_checked_columns", []) if c in table.header]
    if not columns or not tokens:
        return
    for index, raw in enumerate(table.dicts(), start=1):
        hits = [f"{c}={raw[c].strip()!r}" for c in columns if _words(raw[c]) & tokens]
        if hits:
            ctx.add(table.name, index, "D01", f"dose quantity in value(s): {', '.join(hits)}")


def _require(path: Path) -> Path:
    if not path.is_file():
        raise FileNotFoundError(f"required file not found: {path}")
    return path


# --------------------------------------------------------------------------
# Generic support tables (T01–T05)
# --------------------------------------------------------------------------


@dataclass
class _Spec:
    schema: str
    columns: list[str]
    types: dict[str, str]
    key: Callable[[dict], list[tuple]]          # one or more key tuples per row
    bounds: list[tuple[str, str, str]] = field(default_factory=list)
    year_window: tuple[str, str] | None = None


def _value_bounds() -> list[tuple[str, str, str]]:
    return [("value_low", "value_central", "value_high")]


def _check_table(ctx: _Context, spec: _Spec, paths: list[Path],
                 extra: Callable[[_Context, str, int, dict], None] | None = None) -> list[tuple[str, int, dict]]:
    """Run T01–T03 (and the table's own T04 checks via ``extra``) over files."""
    validator = ctx.validators[spec.schema]
    seen: dict[tuple, tuple[str, int]] = {}
    rows: list[tuple[str, int, dict]] = []
    for path in paths:
        table = _read_csv(ctx, path, spec.columns)
        if not table.ok:
            continue
        for index, raw in enumerate(table.dicts(), start=1):
            record, problems = _coerce(raw, spec.types)
            if problems:
                ctx.add(table.name, index, "T01", "; ".join(problems))
            else:
                messages = _schema_messages(validator, record)
                if messages:
                    ctx.add(table.name, index, "T01", "; ".join(messages))

            for key in spec.key(record):
                if key in seen:
                    first = seen[key]
                    ctx.add(table.name, index, "T02",
                            f"duplicate key {key}; first at {first[0]}:{first[1]}")
                else:
                    seen[key] = (table.name, index)

            disorder = [f"{lo} ≤ {c} ≤ {hi}" for lo, c, hi in spec.bounds
                        if _bounds_ok(record, lo, c, hi) is False]
            if spec.year_window:
                a, b = spec.year_window
                if record.get(a) is not None and record.get(b) is not None and record[a] > record[b]:
                    disorder.append(f"{a} ≤ {b}")
            if disorder:
                ctx.add(table.name, index, "T03", "bounds out of order: " + "; ".join(disorder))

            if extra is not None:
                extra(ctx, table.name, index, record)
            rows.append((table.name, index, record))
    return rows


def _t04(ctx: _Context, name: str, index: int, record: dict, *,
         sources: bool = True, country: str | None = None, group: str | None = None,
         residue: bool = False, driver: bool = False, stage: bool = False) -> None:
    """Shared reference-resolution checks for the support tables."""
    unresolved: list[str] = []
    if sources:
        unresolved += [f"source {s!r}" for s in record.get("source_ids") or []
                       if s not in ctx.source_ids]
    if country and record.get(country) and record[country] not in ctx.countries:
        unresolved.append(f"{country} {record[country]!r}")
    if group and record.get(group) and record[group] not in ctx.groups:
        unresolved.append(f"group {record[group]!r}")
    if residue and record.get("residue_type") and record["residue_type"] not in ctx.residue_types:
        unresolved.append(f"residue_type {record['residue_type']!r}")
    if driver and record.get("driver_series") and record["driver_series"] not in ctx.activity_series:
        unresolved.append(f"driver_series {record['driver_series']!r}")
    if stage and record.get("stream") in ctx.vocab["stages"] and record.get("stage") \
            and record["stage"] not in ctx.vocab["stages"][record["stream"]]:
        unresolved.append(f"stage {record['stage']!r} for stream {record['stream']!r}")
    if unresolved:
        ctx.add(name, index, "T04", "unresolved reference(s): " + ", ".join(unresolved))


def _check_countries(ctx: _Context, path: Path) -> None:
    spec = _Spec("countries", ["code", "name", "kind", "valid_from", "valid_to", "notes"],
                 {"valid_from": "int", "valid_to": "int"},
                 key=lambda r: [(r.get("code"),)] if r.get("code") else [],
                 year_window=("valid_from", "valid_to"))
    for _, _, record in _check_table(ctx, spec, [path]):
        if record.get("code"):
            ctx.countries[record["code"]] = (record.get("valid_from"), record.get("valid_to"))


def _check_residue_types(ctx: _Context, path: Path) -> None:
    params = ("epsilon_rn222", "epsilon_rn220", "seepage_per_a")
    columns = ["residue_type", "description", "streams"]
    for p in params:
        columns += [f"{p}_low", f"{p}_central", f"{p}_high"]
    columns += ["basis", "source_ids", "notes"]
    types = {c: "float" for c in columns if c.startswith(params)}
    types.update({"streams": "list", "source_ids": "list"})
    spec = _Spec("residue_types", columns, types,
                 key=lambda r: [(r.get("residue_type"),)] if r.get("residue_type") else [])

    def extra(ctx: _Context, name: str, index: int, record: dict) -> None:
        problems = []
        filled_any = False
        for p in params:
            values = [record.get(f"{p}_{s}") for s in ("low", "central", "high")]
            present = [v is not None for v in values]
            if any(present) and not all(present):
                problems.append(f"{p}: parameter set partly filled")
            elif all(present):
                filled_any = True
                if not values[0] <= values[1] <= values[2]:
                    problems.append(f"{p}: low ≤ central ≤ high fails")
        if filled_any and (not record.get("basis") or not record.get("source_ids")):
            problems.append("parameters filled without basis and source_ids")
        if problems:
            ctx.add(name, index, "T03", "; ".join(problems))
        _t04(ctx, name, index, record)

    for _, _, record in _check_table(ctx, spec, [path], extra):
        if record.get("residue_type"):
            ctx.residue_types.add(record["residue_type"])


def _check_reference_bands(ctx: _Context, path: Path) -> None:
    columns = ["band_id", "quantity_class", "applies_to", "rel_low", "rel_high",
               "basis", "source_ids", "notes"]
    spec = _Spec("reference_bands", columns,
                 {"applies_to": "list", "rel_low": "float", "rel_high": "float", "source_ids": "list"},
                 key=lambda r: ([("id", r["band_id"])] if r.get("band_id") else [])
                 + [("applies", r.get("quantity_class"), a) for a in r.get("applies_to") or []])

    def extra(ctx: _Context, name: str, index: int, record: dict) -> None:
        _t04(ctx, name, index, record)
        unknown = [a for a in record.get("applies_to") or []
                   if a != "*" and a not in ctx.nuclides and a not in ctx.groups]
        if unknown:
            ctx.add(name, index, "T04", f"applies_to not a nuclide or group: {unknown}")

    _check_table(ctx, spec, [path], extra)


def _check_activity(ctx: _Context, paths: list[Path]) -> None:
    columns = ["series", "year", "country", "value_low", "value_central", "value_high",
               "unit", "below_detection", "basis", "source_ids", "notes"]
    spec = _Spec("activity", columns,
                 {"year": "int", "value_low": "float", "value_central": "float",
                  "value_high": "float", "below_detection": "bool", "source_ids": "list"},
                 key=lambda r: [(r.get("series"), r.get("year"), r.get("country"))],
                 bounds=_value_bounds())
    rows = _check_table(ctx, spec, paths,
                        lambda c, n, i, r: _t04(c, n, i, r, country="country"))
    ctx.activity_series.update(r["series"] for _, _, r in rows if r.get("series"))


def _check_factors(ctx: _Context, paths: list[Path]) -> None:
    columns = ["factor_id", "description", "stream", "stage", "driver_series", "group",
               "tier", "route", "residue_type", "region", "year_from", "year_to",
               "value_low", "value_central", "value_high", "unit", "below_detection",
               "basis", "source_ids", "notes"]
    spec = _Spec("factors", columns,
                 {"year_from": "int", "year_to": "int", "value_low": "float",
                  "value_central": "float", "value_high": "float",
                  "below_detection": "bool", "source_ids": "list"},
                 key=lambda r: [(r.get("factor_id"),)] if r.get("factor_id") else [],
                 bounds=_value_bounds(), year_window=("year_from", "year_to"))
    rows = _check_table(ctx, spec, paths,
                        lambda c, n, i, r: _t04(c, n, i, r, country="region", group="group",
                                                residue=True, driver=True, stage=True))
    ctx.factor_ids.update(r["factor_id"] for _, _, r in rows if r.get("factor_id"))


def _check_commodity_factors(ctx: _Context, path: Path) -> None:
    columns = ["commodity", "component", "group", "tier", "route", "residue_type", "region",
               "year_from", "year_to", "allocation_variant", "allocation_rule",
               "value_low", "value_central", "value_high", "unit", "below_detection",
               "basis", "source_ids", "notes"]
    key_cols = ["commodity", "component", "group", "tier", "route", "residue_type",
                "region", "year_from", "allocation_variant"]
    spec = _Spec("commodity_factors", columns,
                 {"year_from": "int", "year_to": "int", "value_low": "float",
                  "value_central": "float", "value_high": "float",
                  "below_detection": "bool", "source_ids": "list"},
                 key=lambda r: [tuple(r.get(c) for c in key_cols)],
                 bounds=_value_bounds(), year_window=("year_from", "year_to"))
    rows = _check_table(ctx, spec, [path],
                        lambda c, n, i, r: _t04(c, n, i, r, country="region", group="group",
                                                residue=True))
    # T05: allocation completeness, as X03.
    by_key: dict[tuple, list[tuple[str, int, dict]]] = {}
    for item in rows:
        record = item[2]
        k = tuple(record.get(c) for c in key_cols if c != "allocation_variant")
        by_key.setdefault(k, []).append(item)
    for members in by_key.values():
        message = _allocation_problem([(m[2].get("allocation_variant"),
                                        (m[2].get("allocation_rule") or "").split(";"))
                                       for m in members])
        if message:
            ctx.add(members[0][0], members[0][1], "T05", message)


def _check_baselines(ctx: _Context, path: Path) -> None:
    columns = ["baseline_id", "name", "quantity", "group", "year", "value_low",
               "value_central", "value_high", "unit", "basis", "derivation",
               "source_ids", "notes"]
    spec = _Spec("baselines", columns,
                 {"year": "int", "value_low": "float", "value_central": "float",
                  "value_high": "float", "source_ids": "list"},
                 key=lambda r: [(r.get("baseline_id"),)] if r.get("baseline_id") else [],
                 bounds=_value_bounds())
    _check_table(ctx, spec, [path], lambda c, n, i, r: _t04(c, n, i, r, group="group"))


def _allocation_problem(members: list[tuple[str | None, list[str]]]) -> str | None:
    """Shared X03/T05 logic over (variant, rule tokens) of one key's rows."""
    variants = {v for v, _ in members if v}
    if not (variants - {"default"}):
        return None
    missing = [v for v in ALLOCATION_VARIANTS if v not in variants]
    if missing:
        return f"allocation variants incomplete; missing {missing}"
    wrong = [v for v, tokens in members if v in VARIANT_TOKENS
             and not any(t in tokens for t in VARIANT_TOKENS[v])]
    if wrong:
        return f"allocation rule lacks the token for variant(s) {sorted(set(wrong))}"
    return None


# --------------------------------------------------------------------------
# Sources, events, nuclides, groups
# --------------------------------------------------------------------------


def _check_sources(ctx: _Context, path: Path) -> None:
    """S01/S02."""
    table = _read_csv(ctx, path, SOURCES_COLUMNS)
    if not table.ok:
        return
    banned_domains = [d.lower() for d in ctx.vocab.get("banned_domains", [])]
    banned_terms = [t.lower() for t in ctx.vocab.get("banned_citation_terms", [])]
    for index, raw in enumerate(table.dicts(), start=1):
        record, problems = _coerce(raw, {"year": "int", "rank": "int"})
        if not problems:
            problems.extend(_schema_messages(ctx.validators["sources"], record))
        sid = raw["source_id"].strip()
        if sid and sid in ctx.source_ids:
            problems.append(f"duplicate source_id {sid!r}")
        if problems:
            ctx.add(table.name, index, "S01", "; ".join(problems))
        if sid:
            ctx.source_ids.add(sid)

        banned: list[str] = []
        url = raw["url"].strip()
        if url:
            host = (urlparse(url).hostname or "").lower()
            banned += [f"url on banned domain {d!r}" for d in banned_domains
                       if host == d or host.endswith("." + d)]
        citation = (raw["short_cite"] + " " + raw["full_citation"]).lower()
        banned += [f"citation names banned source {t!r}" for t in banned_terms if t in citation]
        if banned:
            ctx.add(table.name, index, "S02", "; ".join(banned))


def _real_date(text: str | None) -> bool:
    if text is None:
        return True
    try:
        _dt.date.fromisoformat(text)
        return True
    except ValueError:
        return False


def _check_events(ctx: _Context, path: Path) -> None:
    """E01/E02/E03."""
    table = _read_csv(ctx, path, EVENTS_COLUMNS)
    if not table.ok:
        return
    stages = ctx.vocab["stages"]
    inclusion = ctx.vocab.get("event_inclusion", {})
    types = {"lat": "float", "lon": "float", "mass_t": "float",
             "activity_low_bq": "float", "activity_central_bq": "float",
             "activity_high_bq": "float", "is_accident": "bool", "military": "bool",
             "source_ids": "list", "to_tiers": "list"}
    for index, raw in enumerate(table.dicts(), start=1):
        record, problems = _coerce(raw, types)
        if not problems:
            problems.extend(_schema_messages(ctx.validators["events"], record))
        for key in ("date_start", "date_end"):
            if record.get(key) and not _real_date(record[key]):
                problems.append(f"{key}: not a real calendar date {record[key]!r}")
        if (record.get("date_end") and record.get("date_start")
                and _real_date(record["date_start"]) and _real_date(record["date_end"])
                and record["date_end"] < record["date_start"]):
            problems.append("date_end before date_start")
        if _bounds_ok(record, "activity_low_bq", "activity_central_bq", "activity_high_bq") is False:
            problems.append("activity low ≤ central ≤ high fails")
        if record.get("from_tier") and record.get("from_tier") in (record.get("to_tiers") or []):
            problems.append("from_tier also listed in to_tiers")
        eid = raw["event_id"].strip()
        if eid and eid in ctx.events:
            problems.append(f"duplicate event_id {eid!r}")
        if problems:
            ctx.add(table.name, index, "E01", "; ".join(problems))

        membership: list[str] = []
        stream, stage = record.get("stream"), record.get("stage")
        if stream in stages and stage and stage not in stages[stream]:
            membership.append(f"stage {stage!r} not allowed for stream {stream!r}")
        if record.get("country") and record["country"] not in ctx.countries:
            membership.append(f"unknown country {record['country']!r}")
        membership += [f"unknown source {s!r}" for s in record.get("source_ids") or []
                       if s not in ctx.source_ids]
        if membership:
            ctx.add(table.name, index, "E02", "; ".join(membership))

        crit = record.get("inclusion")
        failed: list[str] = []
        if crit == "activity":
            central = record.get("activity_central_bq")
            if central is not None and central < inclusion.get("activity_bq_min", 1e12):
                failed.append(f"activity {central:g} Bq below threshold")
            if not set(record.get("to_tiers") or []) & {"liberated", "dispersed"}:
                failed.append("activity criterion needs a destination in liberated or dispersed")
        elif crit == "mass":
            mass = record.get("mass_t")
            if mass is not None and mass < inclusion.get("mass_t_min", 1e5):
                failed.append(f"mass {mass:g} t below threshold")
            if record.get("from_tier") != "impounded":
                failed.append("mass criterion needs from_tier impounded")
        if failed:
            ctx.add(table.name, index, "E03", "; ".join(failed))

        if eid and eid not in ctx.events:
            ctx.events[eid] = record


def _check_nuclides(ctx: _Context, path: Path) -> None:
    """N01/N02/N03."""
    table = _read_csv(ctx, path, NUCLIDES_COLUMNS)
    if not table.ok:
        return
    components = ["e_alpha_mev", "e_recoil_mev", "e_beta_mev", "e_photon_mev", "e_electron_mev"]
    for index, raw in enumerate(table.dicts(), start=1):
        ctx.nuclides.add(raw["nuclide"].strip())
        try:
            daughters = _to_list(raw["daughters"])
            branching = _float_list(raw["branching"])
            if len(daughters) != len(branching):
                ctx.add(table.name, index, "N01",
                        f"{len(daughters)} daughters but {len(branching)} branching values")
            elif abs(sum(branching) - 1.0) > BRANCHING_TOL:
                ctx.add(table.name, index, "N01", f"branching sums to {sum(branching):.6g}, not 1")
        except _CoercionError as exc:
            ctx.add(table.name, index, "N01", f"daughters/branching: {exc}")
        try:
            parts = [_to_float(raw[c]) for c in components]
            total = _to_float(raw["e_total_mev"])
            if not _rel_close(sum(parts), total, REL_TOL_REFERENCE):
                ctx.add(table.name, index, "N02",
                        f"e_total_mev {total:.6g} != sum of components {sum(parts):.6g}")
        except _CoercionError as exc:
            ctx.add(table.name, index, "N02", f"energies: {exc}")
        try:
            half_life = _to_float(raw["half_life_a"])
            lam = _to_float(raw["lambda_per_a"])
            expected = math.log(2) / half_life if half_life > 0 else math.inf
            if not _rel_close(lam, expected, REL_TOL_REFERENCE):
                ctx.add(table.name, index, "N03",
                        f"lambda_per_a {lam:.6g} != ln2/half_life_a {expected:.6g}")
        except _CoercionError as exc:
            ctx.add(table.name, index, "N03", f"half-life/lambda: {exc}")


def _check_groups(ctx: _Context, path: Path) -> None:
    """G01–G05."""
    table = _read_csv(ctx, path, GROUPS_COLUMNS)
    if not table.ok:
        return
    rows = table.dicts()
    names = {r["group"].strip() for r in rows if r["group"].strip()}
    seen: set[str] = set()
    for index, raw in enumerate(rows, start=1):
        group = raw["group"].strip()
        head = raw["head"].strip()
        try:
            members = _to_list(raw["members"])
        except _CoercionError:
            members = []

        unknown = [n for n in [head, *members] if n and n not in ctx.nuclides]
        g01 = []
        if not head or not members:
            g01.append("missing head or members")
        elif members[0] != head:
            g01.append(f"head {head!r} is not the first member")
        if unknown:
            g01.append(f"unknown nuclide(s): {sorted(set(unknown))}")
        if g01:
            ctx.add(table.name, index, "G01", "; ".join(g01))

        try:
            weights = _float_list(raw["member_weights"])
            multiplier = _to_float(raw["multiplier"])
            if len(weights) != len(members):
                ctx.add(table.name, index, "G02", f"{len(members)} members but {len(weights)} weights")
            elif not _rel_close(sum(weights), multiplier, REL_TOL_REFERENCE):
                ctx.add(table.name, index, "G02",
                        f"multiplier {multiplier:.6g} != sum of member_weights {sum(weights):.6g}")
        except _CoercionError as exc:
            ctx.add(table.name, index, "G02", f"weights/multiplier: {exc}")

        role, scope = raw["role"].strip(), raw["multiplier_scope"].strip()
        if (scope == "flow_only") != (role == "released_gas"):
            ctx.add(table.name, index, "G03",
                    f"multiplier_scope {scope!r} inconsistent with role {role!r}")

        g04 = [f"{col} {raw[col].strip()!r} not allowed" for col, allowed in GROUP_ENUMS.items()
               if raw[col].strip() not in allowed]
        parent = raw["parent_group"].strip()
        if parent and parent not in names:
            g04.append(f"parent_group {parent!r} not a group")
        if group in seen:
            g04.append(f"duplicate group {group!r}")
        if g04:
            ctx.add(table.name, index, "G04", "; ".join(g04))
        seen.add(group)

        if group and group not in ctx.groups:
            ctx.groups[group] = {k: v.strip() for k, v in raw.items()}

    for index, raw in enumerate(rows, start=1):
        if raw["role"].strip() != "released_gas" or not raw["parent_group"].strip():
            continue
        parent = ctx.groups.get(raw["parent_group"].strip())
        head = raw["head"].strip()
        parent_members = (parent or {}).get("members", "").split(";")
        if parent is None or parent.get("role") != "chain" or head not in parent_members:
            ctx.add(table.name, index, "G05",
                    f"released-gas group's parent {raw['parent_group'].strip()!r} "
                    f"is not a chain group containing {head!r}")


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

    def text(self, column: str) -> str:
        return self.raw[column].strip()


def _coerce_master(raw: dict[str, str]) -> tuple[dict, list[str]]:
    record: dict = {}
    problems: list[str] = []
    for key in MASTER_COLUMNS:
        value = raw[key].strip()
        if not value:
            if key in MASTER_NULLABLE:
                record[key] = None
            else:
                problems.append(f"{key}: empty required cell")
                record[key] = None
            continue
        kind = MASTER_TYPES.get(key, "str")
        try:
            record[key] = _CONVERTERS[kind](value) if kind != "str" else value
        except _CoercionError as exc:
            problems.append(f"{key}: {exc}")
            record[key] = None
    return record, problems


def _product_rule(vocab: dict, stream: str | None, stage: str | None) -> str | None:
    rules = vocab.get("product_rules", {})
    if stream in rules.get("by_stream", {}):
        return rules["by_stream"][stream]
    if stage in rules.get("by_stage", {}):
        return rules["by_stage"][stage]
    return None


def _flow_only_allowed(quantity: str | None, tier: str | None) -> bool:
    return (quantity in ("flow", "standing_inventory")
            or (quantity == "transfer_in" and tier == "liberated")
            or (quantity == "transfer_out" and tier == "sealed_in_core"))


def _check_master_row(ctx: _Context, mrow: _MasterRow) -> None:
    """Row-level (R*) and vocabulary (V*) checks for one master row."""
    rec, vocab = mrow.record, ctx.vocab
    add = lambda rule, msg: ctx.add(mrow.file, mrow.row, rule, msg)  # noqa: E731

    if mrow.coerced:
        messages = _schema_messages(ctx.validators["master"], rec)
        if messages:
            add("R02", "; ".join(messages))
        if _bounds_ok(rec, "value_low", "value_central", "value_high") is False:
            add("R03", f"bounds not ordered: low={rec['value_low']:g}, "
                       f"central={rec['value_central']:g}, high={rec['value_high']:g}")

    stream, stage, tier = rec.get("stream"), rec.get("stage"), rec.get("tier")
    quantity = rec.get("quantity")
    if stream in vocab["substreams"]:
        substream = rec.get("substream")
        if substream is not None and substream not in vocab["substreams"][stream]:
            add("V01", f"substream {substream!r} not allowed for stream {stream!r}")
        stage_ok = stage is not None and stage in vocab["stages"][stream]
        if stage is not None and not stage_ok:
            add("V02", f"stage {stage!r} not allowed for stream {stream!r}")
        if (stage_ok and tier in vocab["tiers"] and quantity not in TRANSFER_QUANTITIES
                and tier not in vocab["stage_tiers"][stage]):
            add("V03", f"tier {tier!r} not allowed for stage {stage!r}")
        if stage_ok:
            _check_product(ctx, mrow)

    group = rec.get("group")
    if group is not None and group not in ctx.groups:
        add("V04", f"unknown group {group!r}")

    country = rec.get("country")
    if country is not None:
        if country not in ctx.countries:
            add("V05", f"unknown country {country!r}")
        elif rec.get("year") is not None:
            start, end = ctx.countries[country]
            if (start is not None and rec["year"] < start) or (end is not None and rec["year"] > end):
                add("V06", f"country {country!r} valid {start}-{end}, used in {rec['year']}")
        if country == "XWL":
            add("V10", "XWL not allowed in the master table; use country rows plus XXX")

    unknown_sources = [s for s in rec.get("source_ids") or [] if s not in ctx.source_ids]
    if unknown_sources:
        add("V07", f"unknown source(s) {unknown_sources}")

    event_id = rec.get("event_id")
    if event_id is not None and event_id not in ctx.events:
        add("V08", f"unknown event {event_id!r}")

    if (group in ctx.groups and ctx.groups[group].get("multiplier_scope") == "flow_only"
            and quantity is not None and not _flow_only_allowed(quantity, tier)):
        add("V09", f"flow-only group {group!r} used with quantity {quantity!r} in tier {tier!r}")

    residue = rec.get("residue_type")
    if residue is not None and residue not in ctx.residue_types:
        add("V12", f"unknown residue_type {residue!r}")

    unknown_factors = [f for f in rec.get("factor_ids") or [] if f not in ctx.factor_ids]
    if unknown_factors:
        add("V13", f"unknown factor(s) {unknown_factors}")


def _check_product(ctx: _Context, mrow: _MasterRow) -> None:
    """V11: product rules (SCHEMA §5.5). Called only when stream and stage are valid."""
    rec = mrow.record
    product = rec.get("product")
    rule = _product_rule(ctx.vocab, rec.get("stream"), rec.get("stage"))
    tier = rec.get("tier") or ""
    problem = None
    if rule == "commodity" and tier.startswith("sealed"):
        if product is not None:
            problem = f"product {product!r} not allowed on a Sealed-tier row"
    elif rule is not None:
        allowed = ctx.vocab["products"][rule]
        if product is None:
            problem = f"product required ({rule})"
        elif product not in allowed:
            problem = f"product {product!r} not in the {rule} vocabulary"
    elif product is not None:
        problem = f"product {product!r} not allowed at stage {rec.get('stage')!r}"
    if problem:
        ctx.add(mrow.file, mrow.row, "V11", problem)


def _balance_key(mrow: _MasterRow) -> tuple:
    event_id = mrow.text("event_id")
    if event_id:
        return ("event", event_id, mrow.text("year"), mrow.text("group"),
                mrow.text("allocation_variant"))
    return ("routine", mrow.text("stage"), mrow.text("country"), mrow.text("year"),
            mrow.text("group"), mrow.text("allocation_variant"))


def _check_cross_rows(ctx: _Context, rows: list[_MasterRow]) -> None:
    """Cross-row rules X01–X05 over all master rows together."""
    vocab = ctx.vocab

    # X01: duplicate unique key, reported on the later occurrence.
    first_seen: dict[tuple, _MasterRow] = {}
    for mrow in rows:
        key = tuple(mrow.text(c) for c in KEY_COLUMNS)
        if key in first_seen:
            earlier = first_seen[key]
            ctx.add(mrow.file, mrow.row, "X01", f"duplicate key; first at {earlier.file}:{earlier.row}")
        else:
            first_seen[key] = mrow

    # X02: transfers balance.
    balances: dict[tuple, dict] = {}
    for mrow in rows:
        quantity = mrow.text("quantity")
        if quantity not in TRANSFER_QUANTITIES:
            continue
        entry = balances.setdefault(_balance_key(mrow), {
            "file": mrow.file, "skip": False,
            "transfer_out": [0.0, 0.0, 0.0], "transfer_in": [0.0, 0.0, 0.0]})
        if not mrow.coerced:
            entry["skip"] = True
            continue
        for i, col in enumerate(("value_low", "value_central", "value_high")):
            entry[quantity][i] += mrow.record[col]
    for key, entry in balances.items():
        if entry["skip"]:
            continue
        out, into = entry["transfer_out"], entry["transfer_in"]
        if not all(_rel_close(o, n, REL_TOL_BALANCE) for o, n in zip(out, into)):
            label = " ".join(str(k) for k in key)
            ctx.add(entry["file"], None, "X02",
                    f"transfers unbalanced for {label}: out={out[1]:g}, in={into[1]:g} (central)")

    # X03: allocation completeness and token coupling.
    variant_index = KEY_COLUMNS.index("allocation_variant")
    by_key: dict[tuple, list[_MasterRow]] = {}
    for mrow in rows:
        if not mrow.coerced:
            continue
        key = tuple(mrow.text(c) for i, c in enumerate(KEY_COLUMNS) if i != variant_index)
        by_key.setdefault(key, []).append(mrow)
    for members in by_key.values():
        message = _allocation_problem([(m.text("allocation_variant"),
                                        m.text("allocation_rule").split(";")) for m in members])
        if message:
            ctx.add(members[0].file, members[0].row, "X03", message)

    # X04: civil rule on uranium mining, milling and reprocessing.
    civil_stages = set(vocab.get("civil_rule_stages", []))
    for mrow in rows:
        if not mrow.coerced:
            continue
        if mrow.record["stream"] == "nuclear" and mrow.record["stage"] in civil_stages:
            tokens = mrow.text("allocation_rule").split(";")
            if not any(t.startswith("civil:") for t in tokens):
                ctx.add(mrow.file, mrow.row, "X04",
                        f"stage {mrow.record['stage']!r} without a civil: allocation token")

    # X05: transfers must be legitimate.
    routine = vocab.get("routine_transfers", {})
    for mrow in rows:
        quantity = mrow.text("quantity")
        if quantity not in TRANSFER_QUANTITIES:
            continue
        tier, event_id, stage = mrow.text("tier"), mrow.text("event_id"), mrow.text("stage")
        if event_id:
            if event_id not in ctx.events:
                continue  # V08 already reported
            event = ctx.events[event_id]
            if quantity == "transfer_out" and event.get("from_tier") is not None \
                    and tier != event["from_tier"]:
                ctx.add(mrow.file, mrow.row, "X05",
                        f"transfer_out tier {tier!r} is not event {event_id} from_tier {event['from_tier']!r}")
            if quantity == "transfer_in" and event.get("to_tiers") is not None \
                    and tier not in event["to_tiers"]:
                ctx.add(mrow.file, mrow.row, "X05",
                        f"transfer_in tier {tier!r} not in event {event_id} to_tiers {event['to_tiers']}")
        else:
            pair = routine.get(stage)
            expected = None if pair is None else (pair["from"] if quantity == "transfer_out" else pair["to"])
            if pair is None:
                ctx.add(mrow.file, mrow.row, "X05",
                        f"transfer without event_id at non-routine stage {stage!r}")
            elif tier != expected:
                ctx.add(mrow.file, mrow.row, "X05",
                        f"routine {quantity} at {stage!r} must use tier {expected!r}, not {tier!r}")


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------


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
    ref = root / "data" / "reference"
    data = root / "data"

    vocab = json.loads(_require(ref / "vocab.json").read_text(encoding="utf-8"))
    required = {
        "countries": _require(ref / "countries.csv"),
        "nuclides": _require(ref / "nuclides.csv"),
        "groups": _require(ref / "groups.csv"),
        "residue_types": _require(ref / "residue_types.csv"),
        "reference_bands": _require(ref / "reference_bands.csv"),
        "sources": _require(data / "sources.csv"),
    }
    validators = {
        name: Draft7Validator(json.loads(_require(root / "schema" / f"{name}.json")
                                         .read_text(encoding="utf-8")))
        for name in SCHEMA_NAMES
    }
    ctx = _Context(root, vocab, validators, [])

    # Order matters: each table may look up those checked before it.
    _check_countries(ctx, required["countries"])
    _check_sources(ctx, required["sources"])
    _check_nuclides(ctx, required["nuclides"])
    _check_groups(ctx, required["groups"])
    _check_residue_types(ctx, required["residue_types"])
    _check_reference_bands(ctx, required["reference_bands"])
    _check_activity(ctx, sorted((data / "activity").glob("*.csv")))
    _check_factors(ctx, sorted((data / "factors").glob("*.csv")))
    if (ref / "commodity_factors.csv").is_file():
        _check_commodity_factors(ctx, ref / "commodity_factors.csv")
    if (data / "baselines.csv").is_file():
        _check_baselines(ctx, data / "baselines.csv")
    if (data / "events.csv").is_file():
        _check_events(ctx, data / "events.csv")

    master_rows: list[_MasterRow] = []
    for path in _resolve_master_files(root, master_files):
        if not path.is_file():
            ctx.add(_display_name(path, root), None, "F03", "file not found")
            continue
        table = _read_csv(ctx, path, MASTER_COLUMNS)
        if not table.ok:
            continue
        for index, raw in enumerate(table.dicts(), start=1):
            record, problems = _coerce_master(raw)
            mrow = _MasterRow(table.name, index, raw, record, coerced=not problems)
            if problems:
                ctx.add(table.name, index, "R01", "; ".join(problems))
            _check_master_row(ctx, mrow)
            master_rows.append(mrow)

    _check_cross_rows(ctx, master_rows)
    return sorted(ctx.issues, key=_sort_key)


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
    if issues:
        print(f"{len(issues)} issue(s) in {len({i.file for i in issues})} file(s)")
        return 1
    print("OK: no issues")
    return 0


if __name__ == "__main__":
    sys.exit(main())
