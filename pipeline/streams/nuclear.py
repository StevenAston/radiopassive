"""Nuclear stream script (Task 2.1). Contract: docs/NUCLEAR_SPEC.md (v1.2, including section 13).

Usage: ``python -m pipeline.streams.nuclear [--root PATH] [--write]``

The script is a pure function of the files under ``data/``. It never decays anything:
decay, ingrowth, radon exhalation, seepage, the accident toggle and the removal of a destroyed
unit's in-core inventory belong to the Phase 3 engine.
"""

from __future__ import annotations

import argparse
import csv
import logging
import math
import re
import sys
import tempfile
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pipeline.lib import LibError
from pipeline.lib.bounds import Bounds, product, sum_correlated, sum_independent
from pipeline.lib.factors import apply, master_unit, result_unit, select
from pipeline.lib.io import read_table
from pipeline.lib.rows import make_row, write_master

STREAM = "nuclear"
WORLD_ACTIVITY = "XWL"  # world aggregate / default region in activity and factor tables
WORLD_ROW = "XXX"  # SCHEMA §3 / V10: master rows use XXX for global data
FIRST_YEAR_MAIN = 1950
LAST_YEAR = 2025
TYPES = ("pwr", "bwr", "phwr", "gcr", "lwgr", "fbr")
EVENT_TYPE = {"E002": "pwr", "E004": "lwgr", "E013": "bwr"}  # NUCLEAR_SPEC 7.1
CLOSURE_TOLERANCE = 1e-5  # NUCLEAR_SPEC 2.1 / 13.1: stored values carry six significant digits
EVENT_TOLERANCE = 1e-4  # NUCLEAR_SPEC 7.4, 7.6
PAIR_TOLERANCE = 1e-9  # NUCLEAR_SPEC 5.0

REPROCESSED = "nuc_reprocessed_gwa"
SEA_DUMPED = "nuc_sea_dumped_tbq"
ACTIVITY_FILES = ("uranium.csv", "electricity_generation.csv", "nuclear.csv", "nuclear_cycle.csv")
USED_SERIES = frozenset(
    {"u_production", "phi_civil", "elec_gen_nuclear", REPROCESSED, SEA_DUMPED}
    | {f"nuc_gen_{t}" for t in TYPES}
    | {f"nuc_cap_{t}" for t in TYPES}
)

LOG_KINDS = (
    "no_factor",
    "no_driver",
    "no_family",
    "negative_residual",
    "predecessor_dropped",
    "event_not_modelled",
    "no_inventory",
    "release_exceeds_inventory",
    "lib_warning",
)
CAUSE_ORDER = (
    "zero_central_factor",
    "exact_zero",
    "clipped_difference",
    "floor_dominance",
    "inherited_flag",
)
BASIS_ORDER = ("interpolated", "extrapolated")
LOG_COLUMNS = ("kind", "year", "country", "group", "detail")
REST_OF_WORLD_NOTE = "rest of world (world aggregate minus listed countries)"
CIVIL_SHARE_FLAG = "; civil share undocumented (D64)"

MAIN_OUTPUT = Path("data") / "streams" / "nuclear.csv"
PRE1950_OUTPUT = Path("data") / "streams_pre1950" / "nuclear.csv"
LOG_OUTPUT = Path("research") / "nuclear" / "build_log.csv"

# Registry columns that are match keys: an empty cell is "" everywhere (NUCLEAR_SPEC 13.8).
_KEY_COLUMNS = ("substream", "driver_series", "group", "tier", "route", "residue_type")


@dataclass(frozen=True)
class _UFamily:
    """One uranium front-end row family (NUCLEAR_SPEC 4.3)."""

    name: str
    stage: str
    tier: str
    route: str
    residue: str
    driver: str  # "" when the selection does not pass driver_series
    tonnage: str  # "conv", "isl" or "all"
    label: str
    text: str


_U_FAMILIES = (
    _UFamily("F1", "u_mining_conv", "liberated", "air_ventilation", "", "u_production", "conv",
             "u_mining_conv/liberated/air_ventilation",
             "mine radon (process radon, conventional tonnage)"),
    _UFamily("F2", "u_mining_isl", "liberated", "air_process_vent", "", "u_production", "isl",
             "u_mining_isl/liberated/air_process_vent",
             "ISL wellfield radon (ISL tonnage)"),
    _UFamily("F3", "u_milling", "liberated", "air_process_vent", "", "", "all",
             "u_milling/liberated/air_process_vent",
             "mill radon (all civil tonnage)"),
    _UFamily("F4", "u_milling", "liberated", "air_dust", "", "", "all",
             "u_milling/liberated/air_dust",
             "mill dust (all civil tonnage)"),
    _UFamily("F5", "u_milling", "sealed_fuel_cycle", "", "", "", "all",
             "u_milling/sealed_fuel_cycle",
             "uranium product entering the sealed fuel cycle (all civil tonnage)"),
    _UFamily("F6", "u_milling", "impounded", "", "u_tailings", "", "conv",
             "u_milling/impounded",
             "impounded mill tailings (conventional tonnage only)"),
)
_MEMO_TIER = "memo_earth_moved"
_MEMO_REGION = "USA"
_MEMO_LABEL = "u_mining_conv/memo_earth_moved"


@dataclass(frozen=True)
class BuildResult:
    rows: list[dict]
    rows_pre1950: list[dict]
    log: list[dict]


# --------------------------------------------------------------------------------------
# bounds helpers
# --------------------------------------------------------------------------------------
def _independent_difference(a: Bounds, b: Bounds) -> tuple[Bounds, float]:
    """Independent difference $a-b$ (NUCLEAR_SPEC 3.4); also returns the raw central difference."""
    raw = a.central - b.central
    c = max(raw, 0.0)
    low_raw = c - math.hypot(a.central - a.low, b.high - b.central)
    high = c + math.hypot(a.high - a.central, b.central - b.low)
    low = max(low_raw, 0.0)
    return Bounds(low, c, max(high, c), nd_floored=low_raw < 0.0), raw


def _remainder(inv: Bounds, rel: Bounds) -> tuple[Bounds, bool]:
    """Bound-wise damaged-core remainder (NUCLEAR_SPEC 7.3 item 1).

    Returns the remainder and whether the raw central difference was negative.
    """
    raw_c = inv.central - rel.central
    raw_l = inv.low - rel.low
    raw_h = inv.high - rel.high
    central = max(raw_c, 0.0)
    low = min(max(raw_l, 0.0), central)
    high = max(max(raw_h, 0.0), central)
    return Bounds(low, central, high, nd_floored=raw_l < 0.0), raw_c < 0.0


def _row_bounds(row: Mapping[str, Any]) -> Bounds:
    """A factor row as ``Bounds`` (used for shares, event releases and capacities)."""
    low = row["value_low"]
    return Bounds(
        low,
        row["value_central"],
        row["value_high"],
        nd_floored=bool(row.get("below_detection")) and low == 0,
    )


def _isl_complement(share: Bounds, factor_id: str) -> Bounds:
    """Conventional fraction $1-s$, anti-correlated with $s$ (NUCLEAR_SPEC 3.4)."""
    if share.high > 1.0:
        raise LibError(f"ISL share factor {factor_id!r}: high {share.high!r} is above 1")
    return Bounds(1.0 - share.high, 1.0 - share.central, 1.0 - share.low)


def _is_zero(b: Bounds) -> bool:
    return b.low == 0.0 and b.central == 0.0 and b.high == 0.0


# --------------------------------------------------------------------------------------
# bounds with flag causes (NUCLEAR_SPEC 3.3)
# --------------------------------------------------------------------------------------
@dataclass(frozen=True)
class _Q:
    """``Bounds`` plus the causes of its ``nd_floored`` flag, tracked from our own inputs."""

    b: Bounds
    causes: frozenset[str] = frozenset()

    def scale(self, k: float) -> _Q:
        return _Q(self.b.scale(k), self.causes)


def _finish(
    b: Bounds, terms: Iterable[_Q], *, products: bool, extra: Iterable[str] = ()
) -> _Q:
    if not b.nd_floored:
        return _Q(b)
    terms = list(terms)
    causes = set(extra)
    for t in terms:
        causes |= t.causes
    # The lib's zero-central rule: a term with central 0 and a positive high (for example
    # the complement of an ISL share of exactly 1) gives (0, 0, high) and a flag.
    if (
        products
        and not any(t.b.high == 0.0 for t in terms)
        and any(t.b.central == 0.0 for t in terms)
    ):
        causes.add("zero_central_factor")
    if not causes:
        # Flagged with no earlier cause: the lib's zero-low floor rule fired in this operation.
        causes.add("floor_dominance" if products else "inherited_flag")
    return _Q(b, frozenset(causes))


def _fq(row: Mapping[str, Any]) -> _Q:
    b = _row_bounds(row)
    return _Q(b, frozenset({"inherited_flag"}) if b.nd_floored else frozenset())


def _qproduct(*terms: _Q) -> _Q:
    return _finish(product(*(t.b for t in terms)), terms, products=True)


def _qapply(driver: _Q, unit: str, factor: Mapping[str, Any]) -> _Q:
    return _finish(apply(driver.b, unit, factor), (driver, _fq(factor)), products=True)


def _qsum_correlated(terms: Sequence[_Q]) -> _Q:
    return _finish(sum_correlated(t.b for t in terms), terms, products=False)


def _qsum_independent(terms: Sequence[_Q]) -> _Q:
    return _finish(sum_independent(t.b for t in terms), terms, products=False)


def _qdiff_independent(a: _Q, b: _Q) -> tuple[_Q, float]:
    out, raw = _independent_difference(a.b, b.b)
    return _finish(out, (a, b), products=False, extra=("clipped_difference",)), raw


# --------------------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------------------
def _no_factor(exc: LibError) -> bool:
    """Only a missing factor row is tolerated; ambiguity and other errors propagate (3.6)."""
    return str(exc).startswith("no factor row")


def _merge(*groups: Iterable[str]) -> list[str]:
    """Order-preserving de-duplication of id lists."""
    seen: dict[str, None] = {}
    for group in groups:
        for item in group:
            seen.setdefault(item, None)
    return list(seen)


def _sources(
    factors: Iterable[Mapping[str, Any]], drivers: Iterable[_Driver], extra: Iterable[str] = ()
) -> list[str]:
    ids: set[str] = set(extra)
    for f in factors:
        ids.update(f["source_ids"] or [])
    for d in drivers:
        ids.update(d.sources)
    return sorted(ids)


class _Driver:
    """One activity row: bounds, sources, basis and unit."""

    __slots__ = ("basis", "bounds", "q", "sources", "unit")

    def __init__(self, bounds: Bounds, sources: tuple[str, ...], basis: str, unit: str) -> None:
        self.bounds = bounds
        self.sources = sources
        self.basis = basis
        self.unit = unit
        # A flagged activity row passes its flag on (inherited_flag).
        self.q = _Q(bounds, frozenset({"inherited_flag"}) if bounds.nd_floored else frozenset())


class _LibWarnings(logging.Handler):
    """Counts the lib's warnings by message type so that build() writes nothing to stderr."""

    def __init__(self) -> None:
        super().__init__(logging.WARNING)
        self.counts: Counter[str] = Counter()

    def emit(self, record: logging.LogRecord) -> None:
        self.counts[re.split(r"[:;]", str(record.msg))[0].strip()] += 1


# --------------------------------------------------------------------------------------
# builder
# --------------------------------------------------------------------------------------
class _Builder:
    def __init__(self, root: Path) -> None:
        self.factors = self._load_factors(root / "data" / "factors" / "nuclear.csv")
        self.index: dict[tuple[str, str], list[dict]] = {}
        for f in self.factors:
            self.index.setdefault((f["stage"], f["group"]), []).append(f)
        self.events = [
            e
            for e in read_table(root / "data" / "events.csv")
            if e["stream"] == STREAM
        ]
        self.series: dict[tuple[str, str], dict[int, _Driver]] = {}
        self._load_activity(root / "data" / "activity")
        self.present = {s for s, _ in self.series}

        self.rows: list[dict] = []
        self.rows_pre1950: list[dict] = []
        self.log: list[dict] = []
        # (kind, label, country, group) -> years, written as contiguous runs (NUCLEAR_SPEC 8)
        self.runs: dict[tuple[str, str, str, str], set[int]] = {}
        self._cache: dict[tuple, Any] = {}
        self._units: dict[tuple[str, str], tuple[str, str]] = {}

        self.u_groups = {
            fam.name: self._groups(
                stage=fam.stage, tier=fam.tier, route=fam.route, residue_type=fam.residue,
                **({"driver_series": fam.driver} if fam.driver else {}),
            )
            for fam in _U_FAMILIES
        }
        self.memo_groups = self._groups(stage="u_mining_conv", tier=_MEMO_TIER)
        self.core_groups = {
            t: self._groups(
                stage="reactor_operation", tier="sealed_in_core", driver_series=f"nuc_cap_{t}"
            )
            for t in TYPES
        }

    # ---- loading --------------------------------------------------------------------
    @staticmethod
    def _load_factors(path: Path) -> list[dict]:
        factors = read_table(path)
        for f in factors:
            for col in _KEY_COLUMNS:
                if f.get(col) is None:
                    f[col] = ""
            if f["substream"] != "":
                # Nuclear keeps the reactor type in driver_series (NUCLEAR_SPEC 2.2); a filled
                # cell would be silently ignored because select is called without the key.
                raise LibError(
                    f"factor {f['factor_id']!r}: substream {f['substream']!r} must be empty "
                    "in the nuclear registry"
                )
        for f in factors:
            expected = {"reprocessing": REPROCESSED, "sea_disposal": SEA_DUMPED}.get(f["stage"])
            if expected and f["driver_series"] not in ("", expected):
                raise LibError(
                    f"driver mismatch: factor {f['factor_id']!r} at stage {f['stage']!r} names "
                    f"driver_series {f['driver_series']!r}, the script uses {expected!r}"
                )
        return factors

    def _load_activity(self, folder: Path) -> None:
        for name in ACTIVITY_FILES:
            path = folder / name
            if not path.is_file():
                continue
            for r in read_table(path):
                if r["series"] not in USED_SERIES:
                    continue
                low = r["value_low"]
                bounds = Bounds(
                    low,
                    r["value_central"],
                    r["value_high"],
                    nd_floored=bool(r.get("below_detection")) and low == 0,
                )
                driver = _Driver(
                    bounds, tuple(r["source_ids"] or ()), r.get("basis") or "", r["unit"]
                )
                by_year = self.series.setdefault((r["series"], r["country"]), {})
                if r["year"] in by_year:
                    raise LibError(
                        f"duplicate activity row: series {r['series']!r}, country "
                        f"{r['country']!r}, year {r['year']}"
                    )
                by_year[r["year"]] = driver

    def _groups(self, **match: str) -> list[str]:
        return sorted(
            {f["group"] for f in self.factors if all(f[k] == v for k, v in match.items())}
        )

    def _family(self, **match: str) -> list[tuple[str, str]]:
        """Distinct (group, route) pairs over all years and regions (NUCLEAR_SPEC 3.2)."""
        return sorted(
            {(f["group"], f["route"]) for f in self.factors if all(f[k] == v for k, v in match.items())}
        )

    # ---- plumbing ---------------------------------------------------------------------
    def sel(self, year: int, region: str, **match: Any) -> dict:
        key = (year, region, tuple(match.items()))
        hit = self._cache.get(key)
        if hit is None:
            pool = self.index.get((match["stage"], match["group"]), [])
            try:
                hit = select(pool, year=year, region=region, **match)
            except LibError as exc:
                self._cache[key] = exc
                raise
            self._cache[key] = hit
        elif isinstance(hit, LibError):
            raise LibError(str(hit))
        return hit

    def driver(self, series: str, country: str, year: int) -> _Driver | None:
        return self.series.get((series, country), {}).get(year)

    def note(self, kind: str, year: int | str, country: str, group: str, detail: str) -> None:
        self.log.append(
            {"kind": kind, "year": year, "country": country, "group": group, "detail": detail}
        )

    def note_run(self, kind: str, year: int, country: str, group: str, label: str) -> None:
        country = WORLD_ROW if country == WORLD_ACTIVITY else country
        self.runs.setdefault((kind, label, country, group), set()).add(year)

    def run_entries(self) -> list[dict]:
        out = []
        for (kind, label, country, group), years_set in sorted(self.runs.items()):
            years = sorted(years_set)
            start = years[0]
            for i, y in enumerate(years):
                last = i + 1 == len(years)
                if last or years[i + 1] != y + 1:
                    n = y - start + 1
                    word = "year" if n == 1 else "years"
                    out.append(
                        {
                            "kind": kind,
                            "year": start,
                            "country": country,
                            "group": group,
                            "detail": f"{start}-{y} ({n} {word}): {label}",
                        }
                    )
                    if not last:
                        start = years[i + 1]
        return out

    def units(self, driver_unit: str, factor: Mapping[str, Any]) -> tuple[str, str]:
        """(flow unit, stock unit) of ``apply(driver, driver_unit, factor)``."""
        key = (driver_unit, factor["unit"])
        hit = self._units.get(key)
        if hit is None:
            res = result_unit(driver_unit, factor["unit"])
            hit = self._units[key] = (master_unit(res, "flow"), master_unit(res, "stock"))
        return hit

    def emit(
        self,
        year: int,
        q: _Q,
        *,
        drivers: Sequence[_Driver],
        text: str,
        flag_note: str = "",
        **fields: Any,
    ) -> None:
        notes = text + flag_note
        bases = {d.basis for d in drivers}
        basis = "+".join(b for b in BASIS_ORDER if b in bases)
        if basis:
            notes += f"; driver basis: {basis}"
        if q.b.nd_floored:
            causes = [c for c in CAUSE_ORDER if c in q.causes] or ["floor_dominance"]
            notes += "; below_detection cause: " + "+".join(causes)
        row = make_row(
            bounds=q.b,
            year=year,
            stream=STREAM,
            basis="modelled",
            allocation_variant="default",
            embedded_fuel=False,
            notes=notes,
            **fields,
        )
        (self.rows if year >= FIRST_YEAR_MAIN else self.rows_pre1950).append(row)

    def flow(
        self,
        year: int,
        q: _Q,
        factor: Mapping[str, Any],
        driver_unit: str,
        *,
        drivers: Sequence[_Driver],
        text: str,
        **fields: Any,
    ) -> None:
        self.emit(
            year,
            q,
            drivers=drivers,
            text=text,
            quantity="flow",
            unit=self.units(driver_unit, factor)[0],
            **fields,
        )

    def pair(
        self,
        stage: str,
        country: str,
        year: int,
        group: str,
        items: Sequence[tuple[str, _Q, dict]],
        driver_unit: str,
        *,
        rule: str,
        drivers: Sequence[_Driver],
        text: str,
        flag_note: str = "",
    ) -> None:
        """Routine transfer: one ``transfer_in`` per route, one ``transfer_out`` (NUCLEAR_SPEC 5.0)."""
        common = {
            "substream": "fuel_cycle",
            "stage": stage,
            "country": country,
            "group": group,
            "allocation_rule": rule,
        }
        for route, q, f in items:
            self.emit(
                year,
                q,
                drivers=drivers,
                text=text,
                flag_note=flag_note,
                quantity="transfer_in",
                unit=self.units(driver_unit, f)[1],
                tier="liberated",
                route=route,
                factor_ids=[f["factor_id"]],
                source_ids=_sources([f], drivers),
                **common,
            )
        total = _qsum_correlated([q for _, q, _ in items])
        for i, name in enumerate(("low", "central", "high")):
            want = math.fsum(getattr(q.b, name) for _, q, _ in items)
            got = getattr(total.b, name)
            if abs(got - want) > PAIR_TOLERANCE * max(abs(want), abs(got), 1e-300):
                raise LibError(
                    f"{stage} {country} {year} {group}: transfer_out {name} does not balance"
                )
        factors = [f for _, _, f in items]
        self.emit(
            year,
            total,
            drivers=drivers,
            text=text,
            flag_note=flag_note,
            quantity="transfer_out",
            unit=self.units(driver_unit, factors[0])[1],
            tier="sealed_fuel_cycle",
            factor_ids=_merge(f["factor_id"] for f in factors),
            source_ids=_sources(factors, drivers),
            **common,
        )

    # ---- uranium front end ---------------------------------------------------------------
    def listed_countries(self, year: int) -> list[str]:
        present = sorted(
            c for (s, c), by in self.series.items()
            if s == "u_production" and c != WORLD_ACTIVITY and year in by
        )
        if "CSK" in present and "CZE" in present:
            # CSK is the whole-country series; using both double counts (NUCLEAR_SPEC 3.5).
            present.remove("CZE")
            self.note(
                "predecessor_dropped", year, "CZE", "",
                "CZE production dropped because CSK (whole-country series) is present",
            )
        return present

    def uranium(self) -> None:
        early = {
            y for (s, _), by in self.series.items() if s in ("u_production", "phi_civil") for y in by
        }
        years = sorted({y for y in early if y < FIRST_YEAR_MAIN} | set(range(FIRST_YEAR_MAIN, LAST_YEAR + 1)))
        for year in years:
            main = year >= FIRST_YEAR_MAIN
            phi = self.driver("phi_civil", WORLD_ACTIVITY, year)
            if phi is None:
                if main:
                    self.note_run("no_driver", year, WORLD_ROW, "", "phi_civil has no value")
                continue
            has_p = any(
                s == "u_production" and year in by for (s, _), by in self.series.items()
            )
            if not has_p:
                if main:
                    self.note_run("no_driver", year, WORLD_ROW, "", "u_production has no value")
                continue
            listed = self.listed_countries(year)
            parts = [self.series[("u_production", c)][year] for c in listed]
            for c, p in zip(listed, parts, strict=True):
                if p.unit != "t":
                    raise LibError(f"u_production {c} {year}: unit {p.unit!r}, expected 't'")
                if _is_zero(p.bounds):
                    continue
                self.uranium_country(year, c, c, p.q, p.unit, [p], phi, rest=False)
            world = self.driver("u_production", WORLD_ACTIVITY, year)
            if world is None:
                continue
            total = _qsum_independent([p.q for p in parts]) if parts else _Q(Bounds.exact(0.0))
            residual, raw = _qdiff_independent(world.q, total)
            if raw < 0:
                self.note(
                    "negative_residual", year, WORLD_ROW, "",
                    f"world aggregate is below the listed countries by {-raw:.6g} t; treated as 0",
                )
            elif residual.b.central > 0:
                self.uranium_country(
                    year, WORLD_ROW, WORLD_ACTIVITY, residual, world.unit, [world, *parts], phi,
                    rest=True,
                )

    def uranium_country(
        self,
        year: int,
        out_country: str,
        region: str,
        prod_q: _Q,
        unit: str,
        drivers: list[_Driver],
        phi: _Driver,
        *,
        rest: bool,
    ) -> None:
        all_drivers = [phi, *drivers]
        rule = "civil:pre1965" if year <= 1964 else "civil:ratio"
        text_tail = f"; {REST_OF_WORLD_NOTE}" if rest else ""

        # The ISL share is mandatory (NUCLEAR_SPEC 3.6); before 1950 no share row exists and the
        # absent factors are logged family by family instead (NUCLEAR_SPEC 4.6).
        s_row: dict | None
        try:
            s_row = self.sel(
                year, region, stage="u_mining_isl", group="", tier="", route="",
                residue_type="", driver_series="",
            )
        except LibError as exc:
            if not _no_factor(exc) or year >= FIRST_YEAR_MAIN:
                raise
            s_row = None
        tonnage: dict[str, _Q | None] = {"all": _qproduct(prod_q, phi.q), "isl": None, "conv": None}
        if s_row is not None:
            if s_row["unit"] != "1":
                raise LibError(f"ISL share factor {s_row['factor_id']!r}: unit {s_row['unit']!r}")
            share = _row_bounds(s_row)
            comp = _isl_complement(share, s_row["factor_id"])
            tonnage["isl"] = _qproduct(prod_q, _fq(s_row), phi.q)
            tonnage["conv"] = _qproduct(prod_q, _Q(comp), phi.q)

        for fam in _U_FAMILIES:
            uses_isl = fam.tonnage != "all"
            for g in self.u_groups[fam.name]:
                match: dict[str, str] = {
                    "stage": fam.stage, "group": g, "tier": fam.tier, "route": fam.route,
                }
                if fam.residue:
                    match["residue_type"] = fam.residue
                if fam.driver:
                    match["driver_series"] = fam.driver
                try:
                    f = self.sel(year, region, **match)
                except LibError as exc:
                    if not _no_factor(exc):
                        raise
                    self.note_run("no_factor", year, out_country, g, f"{fam.label}: no factor row")
                    continue
                t = tonnage[fam.tonnage]
                if t is None:
                    raise LibError(
                        f"factor {f['factor_id']!r} is valid in {year} but no ISL share row is"
                    )
                factors = ([s_row] if uses_isl else []) + [f]
                self.flow(
                    year, _qapply(t, unit, f), f, unit,
                    drivers=all_drivers,
                    text=fam.text + text_tail,
                    substream="fuel_cycle",
                    stage=fam.stage,
                    country=out_country,
                    group=g,
                    tier=fam.tier,
                    route=fam.route or None,
                    residue_type=fam.residue or None,
                    allocation_rule=rule,
                    factor_ids=[x["factor_id"] for x in factors],
                    source_ids=_sources(factors, all_drivers),
                )

        # Overburden memo series: USA only, from the conventional civil tonnage (NUCLEAR_SPEC 4.4).
        conv = tonnage["conv"]
        if out_country == _MEMO_REGION and year >= FIRST_YEAR_MAIN and conv is not None:
            for g in self.memo_groups:
                try:
                    f = self.sel(
                        year, _MEMO_REGION, stage="u_mining_conv", group=g, tier=_MEMO_TIER,
                        route="", residue_type="", driver_series="u_production",
                    )
                except LibError as exc:
                    if not _no_factor(exc):
                        raise
                    self.note_run("no_factor", year, out_country, g, f"{_MEMO_LABEL}: no factor row")
                    continue
                assert s_row is not None
                self.flow(
                    year, _qapply(conv, unit, f), f, unit,
                    drivers=all_drivers,
                    text="below-threshold overburden and waste rock moved (memo, outside tier totals)",
                    substream="fuel_cycle",
                    stage="u_mining_conv",
                    country=out_country,
                    group=g,
                    tier=_MEMO_TIER,
                    allocation_rule=rule,
                    factor_ids=[s_row["factor_id"], f["factor_id"]],
                    source_ids=_sources([s_row, f], all_drivers),
                )

    # ---- conv_enrich_fab ----------------------------------------------------------------
    def enrichment(self) -> None:
        series = "elec_gen_nuclear"
        fam = self._family(stage="conv_enrich_fab", tier="liberated")
        for year in range(FIRST_YEAR_MAIN, LAST_YEAR + 1):
            drv = self.driver(series, WORLD_ACTIVITY, year)
            if drv is None:
                self.note_run("no_driver", year, WORLD_ROW, "", f"{series} has no value")
                continue
            if _is_zero(drv.bounds):
                continue
            by_group: dict[str, list[tuple[str, _Q, dict]]] = {}
            for g, route in fam:
                try:
                    f = self.sel(
                        year, WORLD_ACTIVITY, stage="conv_enrich_fab", group=g, tier="liberated",
                        route=route, driver_series=series,
                    )
                except LibError as exc:
                    if not _no_factor(exc):
                        raise
                    self.note_run(
                        "no_factor", year, WORLD_ROW, g, f"conv_enrich_fab/liberated/{route}: no factor row"
                    )
                    continue
                by_group.setdefault(g, []).append((route, _qapply(drv.q, drv.unit, f), f))
            for g, items in by_group.items():
                self.pair(
                    "conv_enrich_fab", WORLD_ROW, year, g, items, drv.unit,
                    rule="none", drivers=[drv],
                    text="conversion, enrichment and fabrication release per GW a of nuclear electricity",
                )

    # ---- reprocessing and sea disposal ------------------------------------------------
    def check_closure(self, series: str) -> None:
        """XWL equals the sum of the country rows within 1e-5 relative (NUCLEAR_SPEC 2.1)."""
        by_year: dict[int, list[float]] = {}
        for (s, c), by in sorted(self.series.items()):
            if s != series or c == WORLD_ACTIVITY:
                continue
            for y, d in by.items():
                by_year.setdefault(y, []).append(d.bounds.central)
        for y, world in sorted(self.series.get((series, WORLD_ACTIVITY), {}).items()):
            tot = math.fsum(by_year.get(y, ()))
            w = world.bounds.central
            if abs(tot - w) > CLOSURE_TOLERANCE * max(abs(tot), abs(w)):
                raise LibError(
                    f"{series} {y}: XWL central {w!r} differs from the sum of the country rows "
                    f"{tot!r} by more than {CLOSURE_TOLERANCE:g} relative"
                )

    def country_stage(self, stage: str, series: str) -> None:
        if series not in self.present:
            for year in range(FIRST_YEAR_MAIN, LAST_YEAR + 1):
                self.note_run("no_driver", year, "", "", f"{series} is absent from data/activity")
            return
        self.check_closure(series)
        sea = stage == "sea_disposal"
        fam = self._family(stage=stage, tier="liberated")
        countries = sorted(c for (s, c) in self.series if s == series and c != WORLD_ACTIVITY)
        for c in countries:
            for year, drv in sorted(self.series[(series, c)].items()):
                if sea:
                    if drv.unit == "TBq":
                        q = drv.q.scale(1e12)
                    elif drv.unit == "Bq":
                        q = drv.q
                    else:
                        raise LibError(
                            f"{series} {c} {year}: unit {drv.unit!r}, expected 'TBq' or 'Bq'"
                        )
                    unit = "Bq"
                else:
                    q, unit = drv.q, drv.unit
                if _is_zero(drv.bounds):
                    continue
                by_group: dict[str, list[tuple[str, _Q, dict]]] = {}
                for g, route in fam:
                    try:
                        f = self.sel(
                            year, WORLD_ACTIVITY, stage=stage, group=g, tier="liberated", route=route
                        )
                    except LibError as exc:
                        if not _no_factor(exc):
                            raise
                        self.note_run(
                            "no_factor", year, c, g, f"{stage}/liberated/{route}: no factor row"
                        )
                        continue
                    by_group.setdefault(g, []).append((route, _qapply(q, unit, f), f))
                flag = CIVIL_SHARE_FLAG if sea and c == "USA" else ""
                for g, items in by_group.items():
                    if sea and year < FIRST_YEAR_MAIN:
                        # Pre-1950 file: the liberated half only, as flows (NUCLEAR_SPEC 5.3).
                        for route, qq, f in items:
                            self.flow(
                                year, qq, f, unit,
                                drivers=[drv],
                                text="civil sea disposal, liberated half (pre-1950 file)",
                                flag_note=flag,
                                substream="fuel_cycle",
                                stage=stage,
                                country=c,
                                group=g,
                                tier="liberated",
                                route=route,
                                allocation_rule="none",
                                factor_ids=[f["factor_id"]],
                                source_ids=_sources([f], [drv]),
                            )
                    elif year >= FIRST_YEAR_MAIN:
                        self.pair(
                            stage, c, year, g, items, unit,
                            rule="none" if sea else "civil:throughput",
                            drivers=[drv],
                            text=(
                                "sea disposal of packaged waste, share of dumped activity"
                                if sea
                                else "reprocessing release per GW a reprocessed at the site country"
                            ),
                            flag_note=flag,
                        )

    # ---- reactors ----------------------------------------------------------------------
    def reactors(self) -> None:
        for t in TYPES:
            gen, cap = f"nuc_gen_{t}", f"nuc_cap_{t}"
            effluents = self._family(stage="reactor_operation", tier="liberated", driver_series=gen)
            spent = self._groups(stage="spent_fuel", tier="sealed_fuel_cycle", driver_series=gen)
            core = self.core_groups[t]
            for family, present in (("effluent", effluents), ("in_core", core), ("spent_fuel", spent)):
                if not present:
                    self.note(
                        "no_family", "", WORLD_ROW, "", f"{t}: no registry rows for {family} family"
                    )
            for year in range(FIRST_YEAR_MAIN, LAST_YEAR + 1):
                drv = self.driver(gen, WORLD_ACTIVITY, year)
                if drv is None:
                    self.note_run("no_driver", year, WORLD_ROW, "", f"{gen} has no value")
                elif not _is_zero(drv.bounds):
                    self.reactor_flows(t, year, drv, gen, effluents, spent)
                cdrv = self.driver(cap, WORLD_ACTIVITY, year)
                if cdrv is None:
                    self.note_run("no_driver", year, WORLD_ROW, "", f"{cap} has no value")
                elif not _is_zero(cdrv.bounds):
                    self.reactor_core(t, year, cdrv, cap, core)

    def reactor_flows(
        self, t: str, year: int, drv: _Driver, gen: str,
        effluents: Sequence[tuple[str, str]], spent: Sequence[str],
    ) -> None:
        common = {"substream": t, "country": WORLD_ROW, "allocation_rule": "none"}
        for g, route in effluents:
            try:
                f = self.sel(
                    year, WORLD_ACTIVITY, stage="reactor_operation", group=g, tier="liberated",
                    route=route, driver_series=gen,
                )
            except LibError as exc:
                if not _no_factor(exc):
                    raise
                self.note_run(
                    "no_factor", year, WORLD_ROW, g,
                    f"{t} reactor_operation/liberated/{route}: no factor row",
                )
                continue
            self.flow(
                year, _qapply(drv.q, drv.unit, f), f, drv.unit,
                drivers=[drv], text=f"{t} reactor effluent per GW a of generation",
                stage="reactor_operation", group=g, tier="liberated", route=route,
                factor_ids=[f["factor_id"]], source_ids=_sources([f], [drv]), **common,
            )
        for g in spent:
            try:
                f = self.sel(
                    year, WORLD_ACTIVITY, stage="spent_fuel", group=g, tier="sealed_fuel_cycle",
                    route="", driver_series=gen,
                )
            except LibError as exc:
                if not _no_factor(exc):
                    raise
                self.note_run(
                    "no_factor", year, WORLD_ROW, g, f"{t} spent_fuel/sealed_fuel_cycle: no factor row"
                )
                continue
            self.flow(
                year, _qapply(drv.q, drv.unit, f), f, drv.unit,
                drivers=[drv], text=f"{t} spent-fuel arisings per GW a of generation",
                stage="spent_fuel", group=g, tier="sealed_fuel_cycle",
                factor_ids=[f["factor_id"]], source_ids=_sources([f], [drv]), **common,
            )

    def reactor_core(
        self, t: str, year: int, drv: _Driver, cap: str, core: Sequence[str]
    ) -> None:
        for g in core:
            try:
                f = self.sel(
                    year, WORLD_ACTIVITY, stage="reactor_operation", group=g,
                    tier="sealed_in_core", route="", driver_series=cap,
                )
            except LibError as exc:
                if not _no_factor(exc):
                    raise
                self.note_run(
                    "no_factor", year, WORLD_ROW, g,
                    f"{t} reactor_operation/sealed_in_core: no factor row",
                )
                continue
            self.emit(
                year, _qapply(drv.q, drv.unit, f),
                drivers=[drv], text=f"{t} standing in-core inventory (no-accident baseline)",
                quantity="standing_inventory", unit=self.units(drv.unit, f)[1],
                substream=t, stage="reactor_operation", country=WORLD_ROW, group=g,
                tier="sealed_in_core", allocation_rule="none",
                factor_ids=[f["factor_id"]], source_ids=_sources([f], [drv]),
            )

    # ---- events -----------------------------------------------------------------------------
    def window_rows(self, year: int, region: str, **match: str) -> list[dict]:
        return [
            f for f in self.factors
            if f["region"] == region
            and f["year_from"] <= year <= f["year_to"]
            and all(f[k] == v for k, v in match.items())
        ]

    def event_pass(self) -> None:
        for e in sorted(self.events, key=lambda r: r["event_id"]):
            year = int(str(e["date_start"])[:4])
            country = e["country"]
            if e["stage"] == "accident" and self.window_rows(
                year, country, stage="accident", tier="liberated"
            ):
                self.accident(e, year)
            elif (
                e["stage"] == "u_milling"
                and e["event_type"] == "impoundment_failure"
                and [
                    f for f in self.window_rows(year, country, stage="u_milling")
                    if str(f["description"]).startswith(e["event_id"])
                ]
            ):
                self.impoundment(e, year)
            else:
                self.note(
                    "event_not_modelled", year, country, "",
                    f"{e['event_id']}: marker only (no registry rows)",
                )

    @staticmethod
    def check_shape(e: Mapping[str, Any], *, accident: bool) -> None:
        eid = e["event_id"]
        tiers = set(e["to_tiers"] or ())
        if accident:
            ok = (
                e["is_accident"] is True
                and e["from_tier"] == "sealed_in_core"
                and {"liberated", "sealed_damaged_core"} <= tiers
            )
            want = "is_accident true, from_tier sealed_in_core, to_tiers with liberated and sealed_damaged_core"
        else:
            ok = (
                e["is_accident"] is False
                and e["from_tier"] == "impounded"
                and {"liberated", "dispersed"} <= tiers
            )
            want = "is_accident false, from_tier impounded, to_tiers with liberated and dispersed"
        if not ok:
            raise LibError(f"event {eid}: expected {want}")

    @staticmethod
    def bq_bounds(row: Mapping[str, Any]) -> Bounds:
        if row["unit"] != "Bq":
            raise LibError(f"factor {row['factor_id']!r}: unit {row['unit']!r}, expected 'Bq'")
        return _row_bounds(row)

    def accident(self, e: dict, year: int) -> None:
        eid, country = e["event_id"], e["country"]
        etype = EVENT_TYPE.get(eid)
        if etype is None:
            raise LibError(f"accident event {eid} has no reactor type in the script table")
        self.check_shape(e, accident=True)
        ev_src = list(e["source_ids"] or ())

        releases: dict[str, list[tuple[str, dict, Bounds]]] = {}
        pairs = sorted({
            (f["group"], f["route"])
            for f in self.window_rows(year, country, stage="accident", tier="liberated")
        })
        for g, route in pairs:
            f = self.sel(year, country, stage="accident", group=g, tier="liberated", route=route)
            releases.setdefault(g, []).append((route, f, self.bq_bounds(f)))

        # Required sum (choice 10): the registry release rows agree with events.csv on the central.
        total = math.fsum(b.central for rows in releases.values() for _, _, b in rows)
        want = float(e["activity_central_bq"])
        if abs(total - want) > EVENT_TOLERANCE * want:
            raise LibError(
                f"event {eid}: registry release central sum {total:.6e} Bq differs from "
                f"events.csv {want:.6e} Bq by more than {EVENT_TOLERANCE:g} relative"
            )

        inventory: dict[str, tuple[Bounds, list[dict]]] = {}
        inv_pairs = sorted({
            f["group"]
            for f in self.window_rows(year, country, stage="accident", tier="sealed_in_core")
        })
        if inv_pairs:
            for g in inv_pairs:
                f = self.sel(
                    year, country, stage="accident", group=g, tier="sealed_in_core", route=""
                )
                inventory[g] = (self.bq_bounds(f), [f])
        else:
            cap = self.sel(
                year, country, stage="accident", group="", tier="", route="",
                residue_type="", driver_series="",
            )
            if cap["unit"] != "GW":
                raise LibError(f"capacity factor {cap['factor_id']!r}: unit {cap['unit']!r}, expected 'GW'")
            if not str(cap["description"]).startswith(eid):
                raise LibError(
                    f"capacity factor {cap['factor_id']!r}: description must begin with {eid!r}"
                )
            cq = _Q(_row_bounds(cap))
            for g in self.core_groups[etype]:
                try:
                    f = self.sel(
                        year, WORLD_ACTIVITY, stage="reactor_operation", group=g,
                        tier="sealed_in_core", route="", driver_series=f"nuc_cap_{etype}",
                    )
                except LibError as exc:
                    if not _no_factor(exc):
                        raise
                    continue
                inventory[g] = (_qapply(cq, "GW", f).b, [cap, f])

        common = {
            "substream": etype, "stage": "accident", "country": country, "event_id": eid,
            "allocation_rule": "none", "quantity": "transfer_in",
        }
        zero = Bounds.exact(0.0)
        for g in sorted(set(inventory) | set(releases)):
            rels = releases.get(g, [])
            rel = (
                _qsum_correlated([_Q(b) for _, _, b in rels]).b if rels else zero
            )
            has_inv = g in inventory
            inv, inv_factors = inventory[g] if has_inv else (zero, [])
            if rels and not has_inv:
                self.note(
                    "no_inventory", year, country, g,
                    f"{eid}: release row without an inventory row; inventory taken as 0",
                )
            dmg, negative = _remainder(inv, rel)
            if has_inv and inv.central > 0 and negative:
                self.note(
                    "release_exceeds_inventory", year, country, g,
                    f"{eid}: central release exceeds inventory by "
                    f"{rel.central - inv.central:.6g} Bq",
                )
            if not has_inv:
                dmg = zero  # no inventory: nothing remains in the damaged core
            out_low = rel.low + dmg.low
            out_flag = out_low == 0.0 and (rel.nd_floored or dmg.nd_floored)
            out = Bounds(out_low, rel.central + dmg.central, rel.high + dmg.high, nd_floored=out_flag)
            out_causes = frozenset(
                ({"clipped_difference"} if dmg.nd_floored else set())
                | ({"inherited_flag"} if rel.nd_floored else set())
            )

            for route, f, b in rels:
                self.emit(
                    year, _Q(b), drivers=[], text=f"{eid} release to the environment",
                    unit="Bq", tier="liberated", route=route, group=g,
                    factor_ids=[f["factor_id"]], source_ids=_sources([f], [], ev_src), **common,
                )
            all_factors = [*inv_factors, *(f for _, f, _ in rels)]
            ids = _merge(f["factor_id"] for f in all_factors)
            srcs = _sources(all_factors, [], ev_src)
            if has_inv and not _is_zero(dmg):
                self.emit(
                    year, _Q(dmg, frozenset({"clipped_difference"}) if dmg.nd_floored else frozenset()),
                    drivers=[], text=f"{eid} inventory remaining in the damaged core",
                    unit="Bq", tier="sealed_damaged_core", group=g,
                    factor_ids=ids, source_ids=srcs, **common,
                )
            common_out = {**common, "quantity": "transfer_out"}
            self.emit(
                year, _Q(out, out_causes if out.nd_floored else frozenset()),
                drivers=[], text=f"{eid} removed from the in-core inventory",
                unit="Bq", tier="sealed_in_core", group=g,
                factor_ids=ids, source_ids=srcs, **common_out,
            )

    def impoundment(self, e: dict, year: int) -> None:
        eid, country = e["event_id"], e["country"]
        self.check_shape(e, accident=False)
        ev_src = list(e["source_ids"] or ())
        amount = Bounds(e["activity_low_bq"], e["activity_central_bq"], e["activity_high_bq"])
        keys = sorted({
            (f["group"], f["tier"], f["route"], f["residue_type"])
            for f in self.window_rows(year, country, stage="u_milling")
            if str(f["description"]).startswith(eid)
        })
        by_group: dict[str, list[tuple[dict, _Q]]] = {}
        for g, tier, route, residue in keys:
            f = self.sel(
                year, country, stage="u_milling", group=g, tier=tier, route=route,
                residue_type=residue, driver_series="",
            )
            if f["unit"] != "1":
                raise LibError(f"composition factor {f['factor_id']!r}: unit {f['unit']!r}, expected '1'")
            by_group.setdefault(g, []).append((f, _qproduct(_Q(amount), _fq(f))))

        total = math.fsum(q.b.central for items in by_group.values() for _, q in items)
        want = amount.central
        if abs(total - want) > EVENT_TOLERANCE * want:
            raise LibError(
                f"event {eid}: composition shares give {total:.6e} Bq, events.csv has "
                f"{want:.6e} Bq (shares must sum to 1 within {EVENT_TOLERANCE:g})"
            )
        common = {
            "substream": "fuel_cycle", "stage": "u_milling", "country": country,
            "event_id": eid, "allocation_rule": "civil:doc",
        }
        for g, items in by_group.items():
            for f, q in items:
                dispersed = f["tier"] == "dispersed"
                self.emit(
                    year, q, drivers=[], text=f"{eid} impoundment failure, share of event activity",
                    quantity="transfer_in", unit="Bq", tier=f["tier"], group=g,
                    route=f["route"] or None,
                    residue_type="u_tailings" if dispersed else None,
                    factor_ids=[f["factor_id"]], source_ids=_sources([f], [], ev_src), **common,
                )
            self.emit(
                year, _qsum_correlated([q for _, q in items]), drivers=[],
                text=f"{eid} impoundment failure, removed from the impounded tier",
                quantity="transfer_out", unit="Bq", tier="impounded", group=g,
                residue_type="u_tailings",
                factor_ids=[f["factor_id"] for f, _ in items],
                source_ids=_sources([f for f, _ in items], [], ev_src), **common,
            )


def build(root: Path | str) -> BuildResult:
    """Build the nuclear master rows for 1950-2025, the pre-1950 flow rows and the build log.

    Writes nothing to stderr: the lib's warnings are counted into one ``lib_warning`` entry.
    """
    lib_logger = logging.getLogger("pipeline.lib")
    handler = _LibWarnings()
    saved = (lib_logger.propagate, lib_logger.level)
    lib_logger.propagate = False
    lib_logger.setLevel(logging.WARNING)
    lib_logger.addHandler(handler)
    try:
        b = _Builder(Path(root))
        b.uranium()
        b.enrichment()
        b.country_stage("reprocessing", REPROCESSED)
        b.country_stage("sea_disposal", SEA_DUMPED)
        b.reactors()
        b.event_pass()
    finally:
        lib_logger.removeHandler(handler)
        lib_logger.propagate, level = saved
        lib_logger.setLevel(level)
    log = [*b.log, *b.run_entries()]
    if handler.counts:
        total = sum(handler.counts.values())
        kinds = "; ".join(f"{n} x {name}" for name, n in sorted(handler.counts.items()))
        log.append(
            {
                "kind": "lib_warning",
                "year": "",
                "country": "",
                "group": "",
                "detail": f"{total} pipeline.lib warnings captured: {kinds}",
            }
        )
    return BuildResult(rows=b.rows, rows_pre1950=b.rows_pre1950, log=log)


# --------------------------------------------------------------------------------------
# command line
# --------------------------------------------------------------------------------------
def write_log(log: Sequence[Mapping[str, Any]], path: Path) -> None:
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(LOG_COLUMNS)
        writer.writerows([[e[c] for c in LOG_COLUMNS] for e in log])


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m pipeline.streams.nuclear", description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="repository root (default: the checkout containing this file)",
    )
    parser.add_argument("--write", action="store_true", help="overwrite the committed outputs")
    args = parser.parse_args(argv)
    root: Path = args.root

    result = build(root)
    counts = Counter(e["kind"] for e in result.log)
    print(f"rows 1950-2025: {len(result.rows)}; rows 1800-1949: {len(result.rows_pre1950)}")
    for kind in LOG_KINDS:
        print(f"log {kind}: {counts.get(kind, 0)}")

    targets = ((MAIN_OUTPUT, result.rows), (PRE1950_OUTPUT, result.rows_pre1950))
    if args.write:
        for rel, rows in targets:
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            write_master(rows, root / rel)
        (root / LOG_OUTPUT).parent.mkdir(parents=True, exist_ok=True)
        write_log(result.log, root / LOG_OUTPUT)
        print("written: " + ", ".join(str(rel) for rel, _ in targets) + f", {LOG_OUTPUT}")
        return 0

    differing = []
    with tempfile.TemporaryDirectory() as scratch:
        fresh_files = []
        for n, (rel, rows) in enumerate(targets):
            fresh = Path(scratch) / f"{n}.csv"
            write_master(rows, fresh)
            fresh_files.append((rel, fresh))
        fresh_log = Path(scratch) / "log.csv"
        write_log(result.log, fresh_log)
        fresh_files.append((LOG_OUTPUT, fresh_log))
        for rel, fresh in fresh_files:
            committed = root / rel
            if not committed.is_file() or committed.read_bytes() != fresh.read_bytes():
                differing.append(str(rel))
    if differing:
        print("differs from the committed file(s): " + ", ".join(differing), file=sys.stderr)
        return 1
    print("outputs identical to the committed files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
