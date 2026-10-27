"""Coal stream script (Task 2.2). Contract: docs/COAL_SPEC.md (v1.2 overrides v1.1, which overrides v1).

Usage: ``python -m pipeline.streams.coal [--root PATH] [--write]``

The script is a pure function of the files under ``data/``. It never decays anything:
decay, ingrowth, radon exhalation and seepage belong to the Phase 3 engine.
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

STREAM = "coal"
WORLD_ACTIVITY = "XWL"  # country code of the world aggregate in activity and factor tables
WORLD_ROW = "XXX"  # SCHEMA §3 / V10: master rows use XXX for global data (COAL_SPEC 11.1)
FIRST_YEAR_MAIN = 1950
POWER_COAL_ASH_YIELD = 0.12

# COAL_SPEC §3: the 11 head-nuclide groups carried by ash and coal content.
GROUPS = (
    "U238+",
    "U234",
    "Th230",
    "Ra226+",
    "Pb210+",
    "Po210",
    "U235+",
    "Th232",
    "Ra228+",
    "Th228+",
    "K40",
)
RESIDUE_TIERS = ("impounded", "reisolated", "dispersed")
LOG_KINDS = (
    "no_factor",
    "no_driver",
    "negative_residual",
    "negative_nonpower_coal",
    "no_power_ash",
    "cap_applied",
    "predecessor_dropped",
    "lib_warning",
)
# COAL_SPEC 12.5: these kinds are written once per contiguous year run.
RUN_KINDS = ("no_driver", "no_power_ash")
# COAL_SPEC 12.3: fixed order of the flag causes in the notes suffix.
CAUSE_ORDER = ("zero_central_factor", "clipped_difference", "floor_dominance", "inherited_flag")
BASIS_ORDER = ("interpolated", "extrapolated")
LOG_COLUMNS = ("kind", "year", "country", "group", "detail")
REST_OF_WORLD_NOTE = "rest of world (world aggregate minus listed countries)"

MAIN_OUTPUT = Path("data") / "streams" / "coal.csv"
PRE1950_OUTPUT = Path("data") / "streams_pre1950" / "coal.csv"
LOG_OUTPUT = Path("research") / "coal" / "build_log.csv"


@dataclass(frozen=True)
class BuildResult:
    rows: list[dict]
    rows_pre1950: list[dict]
    log: list[dict]


# --------------------------------------------------------------------------------------
# bounds helpers
# --------------------------------------------------------------------------------------
def _independent_difference(a: Bounds, b: Bounds) -> tuple[Bounds, float]:
    """Independent difference $a-b$ (COAL_SPEC §7, §11.4).

    Returns the clipped result and the raw (possibly negative) central difference so that
    callers can log a negative result. A clipped low bound sets ``nd_floored``.
    """
    raw = a.central - b.central
    c = max(raw, 0.0)
    low_raw = c - math.hypot(a.central - a.low, b.high - b.central)
    high = c + math.hypot(a.high - a.central, b.central - b.low)
    low = max(low_raw, 0.0)
    return Bounds(low, c, max(high, c), nd_floored=low_raw < 0.0), raw


def _correlated_difference(a: Bounds, b: Bounds) -> Bounds:
    """Correlated difference $a-b$ for quantities sharing their driver (COAL_SPEC §12.1, §12.15).

    low and high are the differences of the bounds, clamped around the central (not sorted),
    then clipped to $\\ge 0$. A clipped low or a zero central (including a negative one set
    to zero) sets ``nd_floored``.
    """
    raw = a.central - b.central
    c = max(raw, 0.0)
    low_raw = min(a.low - b.low, c)
    high = max(a.high - b.high, c)
    low = max(low_raw, 0.0)
    return Bounds(low, c, high, nd_floored=c == 0.0 or low_raw < 0.0)


def _cap(raw: Bounds, ceiling: Bounds) -> tuple[Bounds, list[str]]:
    """Bound-wise minimum of ``raw`` and ``ceiling`` (D54); also names the bounds changed."""
    pairs = (
        ("low", raw.low, ceiling.low),
        ("central", raw.central, ceiling.central),
        ("high", raw.high, ceiling.high),
    )
    changed = [name for name, r, c in pairs if r > c]
    low, central, high = (min(r, c) for _, r, c in pairs)
    flagged = low == 0.0 and (raw.nd_floored or ceiling.nd_floored)
    return Bounds(low, central, high, nd_floored=flagged), changed


def _factor_bounds(factor: Mapping[str, Any]) -> Bounds:
    """A dimensionless factor row as ``Bounds`` (used for unit-1 fractions and shares)."""
    low = factor["value_low"]
    return Bounds(
        low,
        factor["value_central"],
        factor["value_high"],
        nd_floored=bool(factor.get("below_detection")) and low == 0,
    )


# --------------------------------------------------------------------------------------
# bounds with flag causes (COAL_SPEC §12.3)
# --------------------------------------------------------------------------------------
@dataclass(frozen=True)
class _Q:
    """``Bounds`` plus the causes of its ``nd_floored`` flag, tracked from our own inputs.

    The causes only describe an active flag, so they are dropped when the flag is not set.
    """

    b: Bounds
    causes: frozenset[str] = frozenset()

    def scale(self, k: float) -> _Q:
        return _Q(self.b.scale(k), self.causes)


def _q_finish(b: Bounds, inputs: Iterable[_Q], extra: Iterable[str] = ()) -> _Q:
    if not b.nd_floored:
        return _Q(b)
    causes = set(extra)
    for q in inputs:
        causes |= q.causes
    if not causes:
        # Flagged with no earlier cause: the lib's zero-low floor rule fired in this operation.
        causes.add("floor_dominance")
    return _Q(b, frozenset(causes))


def _fq(factor: Mapping[str, Any]) -> _Q:
    """A unit-1 factor row as a ``_Q``; a zero central is the cause of any flag it brings."""
    b = _factor_bounds(factor)
    zero = b.central == 0 and b.high > 0
    return _Q(b, frozenset({"zero_central_factor"}) if zero else frozenset())


def _qproduct(*terms: _Q) -> _Q:
    return _q_finish(product(*(t.b for t in terms)), terms)


def _qapply(driver: _Q, unit: str, factor: Mapping[str, Any]) -> _Q:
    f = _fq(factor)
    return _q_finish(apply(driver.b, unit, factor), (driver, f))


def _qsum_correlated(terms: Sequence[_Q]) -> _Q:
    return _q_finish(sum_correlated(t.b for t in terms), terms)


def _qsum_independent(terms: Sequence[_Q]) -> _Q:
    return _q_finish(sum_independent(t.b for t in terms), terms)


def _qdiff_independent(a: _Q, b: _Q) -> tuple[_Q, float]:
    out, raw = _independent_difference(a.b, b.b)
    return _q_finish(out, (a, b), ("clipped_difference",)), raw


def _qdiff_correlated(a: _Q, b: _Q) -> _Q:
    return _q_finish(_correlated_difference(a.b, b.b), (a, b), ("clipped_difference",))


def _merge(*groups: Iterable[str]) -> list[str]:
    """Order-preserving de-duplication of id lists."""
    seen: dict[str, None] = {}
    for group in groups:
        for item in group:
            seen.setdefault(item, None)
    return list(seen)


def _sources(factors: Iterable[Mapping[str, Any]], drivers: Iterable[_Driver]) -> list[str]:
    ids: set[str] = set()
    for f in factors:
        ids.update(f["source_ids"] or [])
    for d in drivers:
        ids.update(d.sources)
    return sorted(ids)


def _no_factor(exc: LibError) -> bool:
    """Only a missing factor row is tolerated; ambiguity and other errors propagate (§12.6)."""
    return str(exc).startswith("no factor row")


@dataclass(frozen=True)
class _Driver:
    bounds: Bounds
    sources: tuple[str, ...]
    basis: str = ""

    @property
    def q(self) -> _Q:
        # A flagged activity row passes its flag on (COAL_SPEC 12.3, inherited_flag).
        return _Q(self.bounds, frozenset({"inherited_flag"}) if self.bounds.nd_floored else frozenset())


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
        self.factors = read_table(root / "data" / "factors" / "coal.csv")
        self.series: dict[tuple[str, str], dict[int, _Driver]] = {}
        for r in read_table(root / "data" / "activity" / "coal.csv"):
            low = r["value_low"]
            bounds = Bounds(
                low,
                r["value_central"],
                r["value_high"],
                nd_floored=bool(r.get("below_detection")) and low == 0,
            )
            driver = _Driver(bounds, tuple(r["source_ids"] or ()), r.get("basis") or "")
            by_year = self.series.setdefault((r["series"], r["country"]), {})
            if r["year"] in by_year:
                raise LibError(
                    f"duplicate activity row: series {r['series']!r}, country "
                    f"{r['country']!r}, year {r['year']}"
                )
            by_year[r["year"]] = driver
        self.rows: list[dict] = []
        self.rows_pre1950: list[dict] = []
        self.log: list[dict] = []
        # (kind, label, country, year) events that are written as contiguous runs (12.5).
        self.runs: list[tuple[str, str, str, int]] = []
        self._cache: dict[tuple, dict] = {}

    # ---- plumbing ----------------------------------------------------------------
    def sel(self, year: int, region: str, **match: Any) -> dict:
        key = (year, region, tuple(sorted(match.items())))
        hit = self._cache.get(key)
        if hit is None:
            hit = self._cache[key] = select(self.factors, year=year, region=region, **match)
        return hit

    def driver(self, series: str, country: str, year: int) -> _Driver | None:
        return self.series.get((series, country), {}).get(year)

    def note(self, kind: str, year: int, country: str, group: str, detail: str) -> None:
        self.log.append(
            {"kind": kind, "year": year, "country": country, "group": group, "detail": detail}
        )

    def note_run(self, kind: str, year: int, country: str, label: str) -> None:
        self.runs.append((kind, label, WORLD_ROW if country == WORLD_ACTIVITY else country, year))

    def run_entries(self) -> list[dict]:
        grouped: dict[tuple[str, str, str], list[int]] = {}
        for kind, label, country, year in self.runs:
            grouped.setdefault((kind, label, country), []).append(year)
        out = []
        for (kind, label, country), years in sorted(grouped.items()):
            years = sorted(set(years))
            start = years[0]
            for i, y in enumerate(years):
                last = i + 1 == len(years)
                if last or years[i + 1] != y + 1:
                    n = y - start + 1
                    word = "year" if n == 1 else "years"
                    detail = f"{start}-{y} ({n} {word}): {label}"
                    out.append(
                        {"kind": kind, "year": start, "country": country, "group": "", "detail": detail}
                    )
                    if not last:
                        start = years[i + 1]
        return out

    def emit(
        self,
        year: int,
        q: _Q,
        *,
        drivers: Sequence[_Driver],
        notes: str,
        **fields: Any,
    ) -> None:
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
            quantity="flow",
            basis="modelled",
            allocation_variant="default",
            allocation_rule="none",
            embedded_fuel=False,
            notes=notes,
            **fields,
        )
        (self.rows if year >= FIRST_YEAR_MAIN else self.rows_pre1950).append(row)

    @staticmethod
    def flow_unit(driver_unit: str, factor: Mapping[str, Any]) -> str:
        return master_unit(result_unit(driver_unit, factor["unit"]), "flow")

    def capped(self, year: int, group: str, raw: _Q, ceiling: _Q, where: str) -> _Q:
        out, changed = _cap(raw.b, ceiling.b)
        for name in changed:
            self.note(
                "cap_applied",
                year,
                WORLD_ROW,
                group,
                f"{where}: bound={name}; {getattr(raw.b, name):.6g} reduced to "
                f"{getattr(ceiling.b, name):.6g} (D54 release cap)",
            )
        return _q_finish(out, (raw, ceiling))

    # ---- driver bookkeeping ---------------------------------------------------------
    def years(self) -> list[int]:
        wanted = {"coal_production_t", "coal_consumption_t", "coal_ash_power_t", "coal_fly_ash_t"}
        return sorted({y for (s, _), by in self.series.items() if s in wanted for y in by})

    def log_missing_mining_drivers(self, year: int) -> None:
        for (series, country), by in sorted(self.series.items()):
            if series != "coal_production_t" or year in by:
                continue
            # A country is expected from its first year on; the world aggregate always.
            if country == WORLD_ACTIVITY or year >= min(by):
                self.note_run("no_driver", year, country, "coal_production_t has no value")

    # ---- coal_mining ----------------------------------------------------------------
    def listed_countries(self, year: int) -> list[str]:
        present = {
            c
            for (s, c), by in self.series.items()
            if s == "coal_production_t" and c != WORLD_ACTIVITY and year in by
        }
        if {"CSK", "CZE"} <= present:
            # CSK is the whole-country series; using both double counts (COAL_SPEC 12.2).
            present.discard("CZE")
            self.note(
                "predecessor_dropped",
                year,
                "CZE",
                "",
                "CZE production dropped because CSK (whole-country series) is present",
            )
        return sorted(present)

    def mining(self, year: int) -> None:
        self.log_missing_mining_drivers(year)
        listed = self.listed_countries(year)
        for c in listed:
            drv = self.driver("coal_production_t", c, year)
            fac = self.sel(
                year,
                c,
                stage="coal_mining",
                group="Rn222+",
                tier="liberated",
                route="air_ventilation",
                residue_type=None,
            )
            self.emit(
                year,
                _qapply(drv.q, "t", fac),
                drivers=[drv],
                substream="all",
                stage="coal_mining",
                country=c,
                group="Rn222+",
                tier="liberated",
                route="air_ventilation",
                unit=self.flow_unit("t", fac),
                factor_ids=[fac["factor_id"]],
                source_ids=_sources([fac], [drv]),
                notes="mine radon; country factor if present, else world default",
            )
            if c == "POL":
                self.mine_water(year, drv)
        self.rest_of_world(year, listed)

    def mine_water(self, year: int, drv: _Driver) -> None:
        for group in ("Ra226+", "Ra228+"):
            try:
                rel = self.sel(
                    year,
                    "POL",
                    stage="coal_mining",
                    group=group,
                    tier="liberated",
                    route="water_mine_drainage",
                    residue_type=None,
                )
            except LibError as exc:
                if not _no_factor(exc):
                    raise
                self.note("no_factor", year, "POL", group, f"mine-water release: {exc}")
                continue
            released = _qapply(drv.q, "t", rel)
            unit = self.flow_unit("t", rel)
            self.emit(
                year,
                released,
                drivers=[drv],
                substream="all",
                stage="coal_mining",
                country="POL",
                group=group,
                tier="liberated",
                route="water_mine_drainage",
                unit=unit,
                factor_ids=[rel["factor_id"]],
                source_ids=_sources([rel], [drv]),
                notes="mine-water radium released to rivers",
            )
            try:
                ret = self.sel(
                    year,
                    "POL",
                    stage="coal_mining",
                    group=group,
                    tier="impounded",
                    route=None,
                    residue_type="coal_mine_water_sludge",
                )
            except LibError as exc:
                if not _no_factor(exc):
                    raise
                self.note("no_factor", year, "POL", group, f"mine-water retention: {exc}")
                continue
            # Retained = released * r / (1 - r), applied bound by bound (COAL_SPEC 4.2).
            r = _factor_bounds(ret)
            ratio = Bounds(
                r.low / (1.0 - r.low), r.central / (1.0 - r.central), r.high / (1.0 - r.high)
            )
            self.emit(
                year,
                _qproduct(released, _Q(ratio)),
                drivers=[drv],
                substream="all",
                stage="coal_mining",
                country="POL",
                group=group,
                tier="impounded",
                residue_type="coal_mine_water_sludge",
                unit=unit,
                factor_ids=[rel["factor_id"], ret["factor_id"]],
                source_ids=_sources([rel, ret], [drv]),
                notes="mine-water radium retained underground as sludge",
            )

    def rest_of_world(self, year: int, listed: Sequence[str]) -> None:
        world = self.driver("coal_production_t", WORLD_ACTIVITY, year)
        if world is None:
            return  # already logged as no_driver
        parts = [self.driver("coal_production_t", c, year) for c in listed]
        total = _qsum_independent([p.q for p in parts])
        residual, raw = _qdiff_independent(world.q, total)
        if raw < 0:
            self.note(
                "negative_residual",
                year,
                WORLD_ROW,
                "",
                f"world aggregate is below the listed countries by {-raw:.6g} t; treated as 0",
            )
            return
        if raw == 0:
            return
        fac = self.sel(
            year,
            WORLD_ACTIVITY,
            stage="coal_mining",
            group="Rn222+",
            tier="liberated",
            route="air_ventilation",
            residue_type=None,
        )
        self.emit(
            year,
            _qapply(residual, "t", fac),
            drivers=[world, *parts],
            substream="all",
            stage="coal_mining",
            country=WORLD_ROW,
            group="Rn222+",
            tier="liberated",
            route="air_ventilation",
            unit=self.flow_unit("t", fac),
            factor_ids=[fac["factor_id"]],
            source_ids=_sources([fac], [world, *parts]),
            notes=REST_OF_WORLD_NOTE,
        )

    # ---- combustion_power -----------------------------------------------------------
    def concentration(self, year: int, group: str, residue: str) -> dict:
        return self.sel(
            year,
            WORLD_ACTIVITY,
            stage="combustion_power",
            group=group,
            residue_type=residue,
            tier=None,
            route=None,
        )

    def power(self, year: int) -> None:
        tot = self.driver("coal_ash_power_t", WORLD_ACTIVITY, year)
        fly = self.driver("coal_fly_ash_t", WORLD_ACTIVITY, year)
        missing = [
            name for name, d in (("coal_ash_power_t", tot), ("coal_fly_ash_t", fly)) if d is None
        ]
        if missing:
            self.note_run("no_driver", year, WORLD_ACTIVITY, f"no value for {', '.join(missing)}")
            return
        # Bottom ash and total ash come from one activity builder: correlated (COAL_SPEC 12.1).
        bottom = _qdiff_correlated(tot.q, fly.q)
        base = self.sel(
            year,
            WORLD_ACTIVITY,
            stage="combustion_power",
            tier="liberated",
            route="air_stack",
            group=None,
        )
        shares = {
            t: self.sel(
                year,
                WORLD_ACTIVITY,
                stage="combustion_power",
                tier=t,
                group=None,
                residue_type=None,
                route=None,
            )
            for t in RESIDUE_TIERS
        }
        drivers = [tot, fly]
        parts: dict[str, tuple[_Q, _Q, dict, dict]] = {}
        for g in GROUPS:
            f_fac = self.concentration(year, g, "coal_fly_ash")
            b_fac = self.concentration(year, g, "coal_bottom_ash")
            parts[g] = (
                _qapply(fly.q, "t", f_fac),
                _qapply(bottom, "t", b_fac),
                f_fac,
                b_fac,
            )
        for g in GROUPS:
            F, B, f_fac, b_fac = parts[g]
            enrich = self.sel(
                year,
                WORLD_ACTIVITY,
                stage="combustion_power",
                tier="liberated",
                route="air_stack",
                group=g,
            )
            unit = self.flow_unit("t", f_fac)
            # F and B share one concentration uncertainty: fully correlated (COAL_SPEC 11.3).
            both = _qsum_correlated([F, B])
            stack = self.capped(
                year,
                g,
                _qproduct(_fq(base), _fq(enrich), both),
                F,
                "combustion_power stack release",
            )
            stack_ids = [f_fac["factor_id"], b_fac["factor_id"], base["factor_id"], enrich["factor_id"]]
            stack_factors = [f_fac, b_fac, base, enrich]
            self.emit(
                year,
                stack,
                drivers=drivers,
                substream="power",
                stage="combustion_power",
                country=WORLD_ROW,
                group=g,
                tier="liberated",
                route="air_stack",
                unit=unit,
                factor_ids=stack_ids,
                source_ids=_sources(stack_factors, drivers),
                notes="stack release, capped at fly-ash activity",
            )
            # S is a fraction of F + B, so it moves with F: correlated (COAL_SPEC 12.1).
            fly_residue = _qdiff_correlated(F, stack)
            residues = (
                ("coal_fly_ash", fly_residue, stack_ids, stack_factors, "fly ash after stack release"),
                ("coal_bottom_ash", B, [b_fac["factor_id"]], [b_fac], "bottom ash route share"),
            )
            for residue_type, amount, ids, facs, text in residues:
                for tier in RESIDUE_TIERS:
                    share = shares[tier]
                    self.emit(
                        year,
                        _qproduct(amount, _fq(share)),
                        drivers=drivers,
                        substream="power",
                        stage="combustion_power",
                        residue_type=residue_type,
                        country=WORLD_ROW,
                        group=g,
                        tier=tier,
                        unit=unit,
                        factor_ids=_merge(ids, [share["factor_id"]]),
                        source_ids=_sources([*facs, share], drivers),
                        notes=f"ash route share; {text}",
                    )
        # Radon released at the stack, from the Ra-226 and Th-228 ash activity.
        for group, parent in (("Rn222+", "Ra226+"), ("Rn220+", "Th228+")):
            F, B, f_fac, b_fac = parts[parent]
            fac = self.sel(
                year,
                WORLD_ACTIVITY,
                stage="combustion_power",
                tier="liberated",
                route="air_stack",
                group=group,
            )
            self.emit(
                year,
                _qapply(_qsum_correlated([F, B]), "Bq", fac),
                drivers=drivers,
                substream="power",
                stage="combustion_power",
                country=WORLD_ROW,
                group=group,
                tier="liberated",
                route="air_stack",
                unit=self.flow_unit("t", f_fac),
                factor_ids=[f_fac["factor_id"], b_fac["factor_id"], fac["factor_id"]],
                source_ids=_sources([f_fac, b_fac, fac], drivers),
                notes="radon released with the stack gas",
            )

    # ---- combustion_nonpower ---------------------------------------------------------
    def nonpower(self, year: int) -> None:
        cons = self.driver("coal_consumption_t", WORLD_ACTIVITY, year)
        if cons is None:
            self.note_run("no_driver", year, WORLD_ACTIVITY, "no value for coal_consumption_t")
            return
        tot = self.driver("coal_ash_power_t", WORLD_ACTIVITY, year)
        drivers = [cons]
        if tot is None:
            self.note_run("no_power_ash", year, WORLD_ACTIVITY, "no ash series; power coal taken as 0")
            power_coal = _Q(Bounds.exact(0.0))
        else:
            drivers.append(tot)
            power_coal = tot.q.scale(1.0 / POWER_COAL_ASH_YIELD)
        # Different builders: the independent form stays here (COAL_SPEC 12.1).
        coal, raw = _qdiff_independent(cons.q, power_coal)
        if raw < 0:
            self.note(
                "negative_nonpower_coal",
                year,
                WORLD_ROW,
                "",
                f"consumption is below power-station coal by {-raw:.6g} t; treated as 0",
            )
        hh = self.sel(
            year,
            WORLD_ACTIVITY,
            stage="combustion_nonpower",
            tier="dispersed",
            residue_type="coal_domestic_ash",
            group=None,
            route=None,
        )
        smoke = self.sel(
            year,
            WORLD_ACTIVITY,
            stage="combustion_nonpower",
            tier="liberated",
            route="air_stack",
            group=None,
            residue_type=None,
        )
        content: dict[str, tuple[_Q, dict]] = {}
        for g in GROUPS:
            fac = self.sel(
                year,
                WORLD_ACTIVITY,
                stage="combustion_nonpower",
                group=g,
                tier=None,
                route=None,
                residue_type=None,
            )
            content[g] = (_qapply(coal, "t", fac), fac)
        for g in GROUPS:
            N, fac = content[g]
            enrich = self.sel(
                year,
                WORLD_ACTIVITY,
                stage="combustion_power",
                tier="liberated",
                route="air_stack",
                group=g,
            )
            unit = self.flow_unit("t", fac)
            H = _qproduct(N, _fq(hh))
            M = self.capped(
                year,
                g,
                _qproduct(H, _fq(smoke), _fq(enrich)),
                H,
                "combustion_nonpower smoke",
            )
            hh_ids = [fac["factor_id"], hh["factor_id"]]
            smoke_ids = _merge(hh_ids, [smoke["factor_id"], enrich["factor_id"]])
            smoke_facs = [fac, hh, smoke, enrich]
            common = {
                "substream": "non_power",
                "stage": "combustion_nonpower",
                "country": WORLD_ROW,
                "group": g,
                "unit": unit,
                "drivers": drivers,
            }
            self.emit(
                year,
                M,
                tier="liberated",
                route="air_stack",
                factor_ids=smoke_ids,
                source_ids=_sources(smoke_facs, drivers),
                notes="household smoke fraction, capped at household activity",
                **common,
            )
            # H-M and N-H stay independent in v1.2 (COAL_SPEC 12.15): overstated, to be revisited.
            household_ash, _ = _qdiff_independent(H, M)
            self.emit(
                year,
                household_ash,
                tier="dispersed",
                residue_type="coal_domestic_ash",
                factor_ids=smoke_ids,
                source_ids=_sources(smoke_facs, drivers),
                notes="household ash after smoke release",
                **common,
            )
            industrial, _ = _qdiff_independent(N, H)
            self.emit(
                year,
                industrial,
                tier="impounded",
                residue_type="coal_bottom_ash",
                factor_ids=hh_ids,
                source_ids=_sources([fac, hh], drivers),
                notes="industrial ash; no industrial stack-release factor (gap)",
                **common,
            )
        for group, parent in (("Rn222+", "Ra226+"), ("Rn220+", "Th228+")):
            N, fac = content[parent]
            rn = self.sel(
                year,
                WORLD_ACTIVITY,
                stage="combustion_power",
                tier="liberated",
                route="air_stack",
                group=group,
            )
            self.emit(
                year,
                _qapply(N, "Bq", rn),
                drivers=drivers,
                substream="non_power",
                stage="combustion_nonpower",
                country=WORLD_ROW,
                group=group,
                tier="liberated",
                route="air_stack",
                unit=self.flow_unit("t", fac),
                factor_ids=[fac["factor_id"], rn["factor_id"]],
                source_ids=_sources([fac, rn], drivers),
                notes="radon released from non-power coal burning",
            )


def build(root: Path | str) -> BuildResult:
    """Build the coal master rows for 1950-2025, the pre-1950 flow rows and the build log.

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
        for year in b.years():
            b.mining(year)
            b.power(year)
            b.nonpower(year)
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
    parser = argparse.ArgumentParser(prog="python -m pipeline.streams.coal", description=__doc__)
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
