"""Other-energy stream script (Task 2.5). Contract: docs/OTHER_SPEC.md (v1.1, sections 13 and X).

Usage: ``python -m pipeline.streams.other [--root PATH] [--write]``

Geothermal radon and scale, peat (plants, other use, household), wood and charcoal memo rows and the
fallout Cs-137 re-release/memo rows. The script is a pure function of the files under ``data/``. It
never decays anything: decay, ingrowth, radon exhalation, seepage and the memo series belong to the
Phase 3 engine. Hydro and construction have no rows (spec section 7) and are guarded.
"""

from __future__ import annotations

import argparse
import csv
import logging
import math
import re
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pipeline.lib import LibError
from pipeline.lib.bounds import Bounds, product, sum_correlated, sum_independent
from pipeline.lib.factors import apply, master_unit, select
from pipeline.lib.io import read_table
from pipeline.lib.rows import make_row
from pipeline.streams._outputs import diff_mode_preflight, finish

STREAM = "other"
WORLD_ACTIVITY = "XWL"  # world aggregate / default region in activity and factor tables
WORLD_ROW = "XXX"  # SCHEMA §3 / V10: master rows use XXX for global data
FIRST_YEAR_MAIN = 1950
FIRST_YEAR = 1800
LAST_YEAR = 2025
TOLERANCE = 1e-5  # OTHER_SPEC 3.5 / D68: stored values carry six significant digits

GEO, BP, DOM = "geothermal", "biomass_peat", "biomass_domestic"
GEO_SERIES = "elec_gen_geothermal"
PEAT_SERIES = ("peat_power_heat_t", "peat_household_t", "peat_supply_t")
WOOD_SERIES = ("wood_fuel_t", "household_fuelwood_m3", "charcoal_production_t")
ACTIVITY_FILES = ("electricity_generation.csv", "biomass.csv", "peat.csv")
USED_SERIES = frozenset({GEO_SERIES, *PEAT_SERIES, *WOOD_SERIES})
COUNTRY_LIST_SERIES = frozenset(
    {
        GEO_SERIES,
        "peat_power_heat_t",
        "peat_household_t",
        "peat_supply_t",
        "wood_fuel_t",
        "charcoal_production_t",
    }
)

LOG_KINDS = (
    "no_factor",
    "no_driver",
    "no_family",
    "negative_residual",
    "household_fallback",
    "household_wood_capped",
    "charcoal_wood_capped",
    "cap_applied",
    "predecessor_dropped",
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
BOUND_ORDER = ("low", "central", "high")
LOG_COLUMNS = ("kind", "year", "country", "group", "detail")
COMP_ORDER = {
    BP: ("peat_plant", "peat_other", "wood_plant"),
    DOM: ("peat_household", "wood_household", "charcoal"),
}

RULE = {
    "geo222": "geothermal non-condensable gas radon",
    "geo220": "geothermal thoron: Rn-222 flow times Rn-220 ratio",
    "geoscale": "geothermal scale: mass per GW a times activity per tonne",
    "pstack": "peat plant stack release: escape fraction times enrichment, capped at fly ash",
    "pash": "peat ash route share",
    "hstack": "household peat chimney smoke: smoke fraction times enrichment, capped at ash-borne activity",
    "hash": "household peat ash route share",
    "rerel": "re-release: fallout Cs-137 in fuel emitted to air by combustion (D43)",
    "memocs": "memo: fallout Cs-137 not released, left in ash (D43)",
    "memowood": "memo: natural nuclides in burned wood, biosphere cycling (D44)",
}
TXT_WORLD = "world aggregate (no country series before 1980)"
TXT_REST = "rest of world (world aggregate minus listed countries)"
TXT_FALLBACK = "household share fallback (other:0050)"

MAIN_OUTPUT = Path("data") / "streams" / "other.csv.gz"
PRE1950_OUTPUT = Path("data") / "streams_pre1950" / "other.csv.gz"
LOG_OUTPUT = Path("research") / "other" / "build_log.csv"
MATERIAL_INTENSITY = Path("data") / "activity" / "material_intensity.csv"
_MI_PLANT_PREFIXES = ("mi_geothermal_", "mi_hydro_", "mi_biomass_")

_KEY_COLUMNS = ("driver_series", "group", "tier", "route", "residue_type")
_SELECT_KEYS = ("stage", "group", "tier", "route", "residue_type", "driver_series")


@dataclass(frozen=True)
class BuildResult:
    rows: list[dict]
    rows_pre1950: list[dict]
    log: list[dict]


# --------------------------------------------------------------------------------------
# terms: bounds plus flag causes and provenance
# --------------------------------------------------------------------------------------
_EMPTY: frozenset = frozenset()


class T:
    """A ``Bounds`` with the causes of its flag, the factors applied, driver sources and bases."""

    __slots__ = ("b", "c", "causes", "f", "fb", "s", "w")

    def __init__(
        self,
        b: Bounds,
        causes=_EMPTY,
        f: tuple = (),
        s=_EMPTY,
        w=_EMPTY,
        c=_EMPTY,
        fb: bool = False,
    ) -> None:
        self.b = b
        self.causes = causes if b.nd_floored else _EMPTY
        self.f = f
        self.s = s
        self.w = w
        self.c = c
        self.fb = fb

    def with_meta(self, f=None, s=None, w=None, c=None, fb=None) -> T:
        return T(
            self.b,
            self.causes,
            self.f if f is None else f,
            self.s if s is None else s,
            self.w if w is None else w,
            self.c if c is None else c,
            self.fb if fb is None else fb,
        )


ZERO = T(Bounds.exact(0.0))


def _tzero(t: T) -> bool:
    b = t.b
    return b.low == 0.0 and b.central == 0.0 and b.high == 0.0


def _union(sets: Iterable[frozenset]) -> frozenset:
    out: frozenset = _EMPTY
    for s in sets:
        if s:
            out = out | s
    return out


def _meta(ts: Sequence[T]) -> tuple[tuple, frozenset, frozenset, frozenset, bool]:
    """Provenance of a derived term: zero terms contribute nothing (OTHER_SPEC 13.13-13.14)."""
    nz = [t for t in ts if not _tzero(t)] or list(ts)
    f: list[str] = []
    for t in nz:
        for x in t.f:
            if x not in f:
                f.append(x)
    return (
        tuple(f),
        _union(t.s for t in nz),
        _union(t.w for t in nz),
        _union(t.c for t in nz),
        any(t.fb for t in nz),
    )


def _product_causes(b: Bounds, ts: Sequence[T]) -> frozenset:
    if not b.nd_floored:
        return _EMPTY
    inc = _union(t.causes for t in ts)
    if inc:
        return inc
    if not any(t.b.high == 0.0 for t in ts) and any(t.b.central == 0.0 for t in ts):
        return frozenset({"zero_central_factor"})
    return frozenset({"floor_dominance"})


def _mk(b: Bounds, causes: frozenset, ts: Sequence[T]) -> T:
    f, s, w, c, fb = _meta(ts)
    return T(b, causes, f, s, w, c, fb)


def _tprod(*ts: T) -> T:
    b = product(*(t.b for t in ts))
    return _mk(b, _product_causes(b, ts), ts)


def _tsum(ts: Sequence[T]) -> T:
    """Fully correlated sum of the non-zero terms (OTHER_SPEC 3.5, 3.6)."""
    nz = [t for t in ts if not _tzero(t)]
    if not nz:
        return ZERO
    b = sum_correlated(t.b for t in nz)
    causes = _EMPTY
    if b.nd_floored:
        causes = _union(t.causes for t in nz) or frozenset({"inherited_flag"})
    return _mk(b, causes, nz)


def _independent_difference(a: Bounds, b: Bounds) -> tuple[Bounds, float]:
    """Independent difference $a-b$ (OTHER_SPEC 3.5); also returns the raw central difference."""
    raw = a.central - b.central
    c = max(raw, 0.0)
    low_raw = c - math.hypot(a.central - a.low, b.high - b.central)
    high = max(c + math.hypot(a.high - a.central, b.central - b.low), c)
    low = max(low_raw, 0.0)
    clipped = low_raw < 0.0 or raw < 0.0
    return Bounds(low, c, high, nd_floored=clipped and low == 0.0), raw


def _correlated_difference(a: Bounds, b: Bounds) -> Bounds:
    """Correlated difference (OTHER_SPEC 3.5); the cause is added by ``_tdiff``."""
    return _corr_diff(a, b)[0]


def _corr_diff(a: Bounds, b: Bounds) -> tuple[Bounds, frozenset]:
    craw = a.central - b.central
    lraw = min(a.low - b.low, craw)
    hraw = max(a.high - b.high, craw)
    c, lo, hi = max(craw, 0.0), max(lraw, 0.0), max(hraw, 0.0)
    clipped = lraw < 0.0 or craw < 0.0
    exact_zero = craw == 0.0 and hraw == 0.0 and lraw >= 0.0
    zero_central = craw == 0.0 and hraw > 0.0
    inherited = (a.nd_floored or b.nd_floored) and lo == 0.0
    causes: set[str] = set()
    if (clipped and lo == 0.0) or zero_central:
        causes.add("clipped_difference")
    if exact_zero:
        causes.add("exact_zero")
    nd = lo == 0.0 and (clipped or exact_zero or inherited or zero_central)
    return Bounds(lo, c, hi, nd_floored=nd), frozenset(causes)


def _tdiff(a: T, b: T) -> T:
    """Correlated difference of terms, with the cause bookkeeping of OTHER_SPEC 3.4."""
    bounds, own = _corr_diff(a.b, b.b)
    causes = _EMPTY
    if bounds.nd_floored:
        inherited = (
            _union(t.causes for t in (a, b))
            if (a.b.nd_floored or b.b.nd_floored)
            else _EMPTY
        )
        causes = own | inherited or frozenset({"inherited_flag"})
    return _mk(bounds, causes, (a, b))


def _cap(x: T, limit: T) -> tuple[T, list[str]]:
    """Bound-by-bound cap (OTHER_SPEC 3.5); also returns the bounds the cap changed."""
    xb, lb = x.b, limit.b
    lo, c, hi = min(xb.low, lb.low), min(xb.central, lb.central), min(xb.high, lb.high)
    changed = [
        n
        for n, (xv, lv) in zip(
            BOUND_ORDER,
            ((xb.low, lb.low), (xb.central, lb.central), (xb.high, lb.high)),
            strict=True,
        )
        if xv > lv
    ]
    nd = lo == 0.0 and (xb.nd_floored or lb.nd_floored)
    causes = _EMPTY
    if nd:
        causes = _union((x.causes, limit.causes)) or frozenset({"inherited_flag"})
    return _mk(Bounds(lo, c, hi, nd_floored=nd), causes, (x, limit)), changed


def _complement(row: Mapping[str, Any]) -> Bounds:
    """Conventional complement $1-s$, anti-correlated with $s$ (OTHER_SPEC 3.5)."""
    if row["value_high"] > 1.0:
        raise LibError(
            f"share factor {row['factor_id']!r}: high {row['value_high']!r} is above 1"
        )
    return Bounds(
        1.0 - row["value_high"], 1.0 - row["value_central"], 1.0 - row["value_low"]
    )


# --------------------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------------------
class _Drv:
    """One activity row as a term plus its unit."""

    __slots__ = ("t", "unit")

    def __init__(
        self, bounds: Bounds, sources: tuple[str, ...], basis: str, unit: str
    ) -> None:
        w = frozenset({basis}) if basis in BASIS_ORDER else _EMPTY
        causes = frozenset({"inherited_flag"}) if bounds.nd_floored else _EMPTY
        self.t = T(bounds, causes, (), frozenset(sources), w)
        self.unit = unit


class _LibWarnings(logging.Handler):
    """Counts the lib's warnings by message type so that build() writes nothing to stderr."""

    def __init__(self) -> None:
        super().__init__(logging.WARNING)
        self.counts: Counter[str] = Counter()

    def emit(self, record: logging.LogRecord) -> None:
        self.counts[re.split(r"[:;]", str(record.msg))[0].strip()] += 1


def _runs(years: Iterable[int]) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for y in sorted(set(years)):
        if out and y == out[-1][1] + 1:
            out[-1] = (out[-1][0], y)
        else:
            out.append((y, y))
    return out


def _run_text(first: int, last: int) -> str:
    n = last - first + 1
    return f"{first}-{last} ({n} {'year' if n == 1 else 'years'})"


# --------------------------------------------------------------------------------------
# builder
# --------------------------------------------------------------------------------------
class _Builder:
    def __init__(self, root: Path) -> None:
        self.factors = self._load_factors(root)
        self.fsources: dict[str, list[str]] = {
            f["factor_id"]: list(f["source_ids"] or []) for f in self.factors
        }
        self.index: dict[tuple, list[dict]] = {}
        for f in self.factors:
            self.index.setdefault(tuple(f[k] for k in _SELECT_KEYS), []).append(f)
        self._check_events(root)
        self.act: dict[str, dict[int, dict[str, _Drv]]] = {}
        self._load_activity(root / "data" / "activity")

        self.rows: list[dict] = []
        self.rows_pre1950: list[dict] = []
        self.log: list[dict] = []
        self.pred: set[tuple[str, int]] = set()
        self._cache: dict[tuple, Any] = {}
        # run bookkeeping: (kind, country) -> {year: set(bounds)} / (series, country) -> years
        self.fallback_years: dict[str, set[int]] = {}
        self.cap_years: dict[tuple[str, str], dict[int, set[str]]] = {}
        self.supply_missing: dict[str, set[int]] = {}

        self.geo_scale_groups = sorted(
            {
                f["group"]
                for f in self.factors
                if f["stage"] == GEO
                and f["tier"] == "impounded"
                and f["residue_type"] == "geothermal_scale"
                and f["group"]
            }
        )
        self.peat_groups = sorted(
            {
                f["group"]
                for f in self.factors
                if f["stage"] == BP
                and f["residue_type"] == "peat_ash"
                and f["tier"] == ""
                and f["group"]
                and f["group"] != "Cs137+"
            }
        )
        self.wood_groups = sorted(
            {
                f["group"]
                for f in self.factors
                if f["stage"] == BP and f["tier"] == "memo_biosphere"
            }
        )

    # ---- loading --------------------------------------------------------------------
    @staticmethod
    def _load_factors(root: Path) -> list[dict]:
        factors = read_table(root / "data" / "factors" / "other.csv")
        for f in factors:
            for col in _KEY_COLUMNS:
                if f.get(col) is None:
                    f[col] = ""
            # Hydro and construction rows would be silently ignored by this script (spec 7).
            if f["stage"] in ("hydro", "construction"):
                raise LibError(
                    f"factor {f['factor_id']!r}: stage {f['stage']!r} has registry rows; "
                    "the other-stream spec must be revised first (OTHER_SPEC 7)"
                )
        mi_path = root / MATERIAL_INTENSITY
        if mi_path.is_file():
            for row in read_table(mi_path):
                series = row.get("series") or ""
                if series.startswith(_MI_PLANT_PREFIXES):
                    raise LibError(
                        f"{MATERIAL_INTENSITY}: series {series!r} is an other-stream plant type; "
                        "the other-stream spec must be revised first (OTHER_SPEC 7)"
                    )
        return factors

    @staticmethod
    def _check_events(root: Path) -> None:
        path = root / "data" / "events.csv"
        if not path.is_file():
            return
        for e in read_table(path):
            if e.get("stream") == STREAM:
                raise LibError(
                    f"event {e.get('event_id')!r}: the other stream has no event rules"
                )

    def _load_activity(self, folder: Path) -> None:
        for name in ACTIVITY_FILES:
            path = folder / name
            if not path.is_file():
                continue
            for r in read_table(path):
                series = r["series"]
                if series not in USED_SERIES:
                    continue
                low = r["value_low"]
                bounds = Bounds(
                    low,
                    r["value_central"],
                    r["value_high"],
                    nd_floored=bool(r.get("below_detection")) and low == 0,
                )
                drv = _Drv(
                    bounds,
                    tuple(r["source_ids"] or ()),
                    r.get("basis") or "",
                    r["unit"],
                )
                by_country = self.act.setdefault(series, {}).setdefault(r["year"], {})
                if r["country"] in by_country:
                    raise LibError(
                        f"duplicate activity row: series {series!r}, country "
                        f"{r['country']!r}, year {r['year']}"
                    )
                by_country[r["country"]] = drv

    # ---- plumbing ---------------------------------------------------------------------
    def sel(
        self,
        year: int,
        region: str,
        *,
        stage: str,
        group: str = "",
        tier: str = "",
        route: str = "",
        residue: str = "",
        driver: str = "",
    ) -> dict:
        key = (year, region, stage, group, tier, route, residue, driver)
        hit = self._cache.get(key)
        if hit is None:
            pool = self.index.get((stage, group, tier, route, residue, driver), [])
            try:
                hit = select(
                    pool,
                    year=year,
                    region=region,
                    stage=stage,
                    group=group,
                    tier=tier,
                    route=route,
                    residue_type=residue,
                    driver_series=driver,
                )
            except LibError as exc:
                self._cache[key] = exc
                raise
            self._cache[key] = hit
        elif isinstance(hit, LibError):
            raise LibError(str(hit))
        return hit

    def drv(self, series: str, year: int, country: str) -> _Drv | None:
        return self.act.get(series, {}).get(year, {}).get(country)

    def countries(self, series: str, year: int) -> list[str]:
        """Listed countries with a value; CZE is dropped where CSK has one (spec 3.7)."""
        cs = sorted(
            c for c in self.act.get(series, {}).get(year, {}) if c != WORLD_ACTIVITY
        )
        if "CSK" in cs and "CZE" in cs:
            cs.remove("CZE")
            self.pred.add((series, year))
        return cs

    def note(
        self, kind: str, year: int | str, country: str, group: str, detail: str
    ) -> None:
        self.log.append(
            {
                "kind": kind,
                "year": year,
                "country": country,
                "group": group,
                "detail": detail,
            }
        )

    def negative(
        self, year: int, country: str, magnitude: float, unit: str, peat: bool = False
    ) -> None:
        if peat:
            detail = f"peat supply is below plants plus household by {magnitude:.6g} t; treated as 0"
        else:
            detail = (
                f"world aggregate is below the listed countries by {magnitude:.6g} {unit}; "
                "treated as 0"
            )
        self.note("negative_residual", year, country, "", detail)

    # ---- factor application ----------------------------------------------------------
    @staticmethod
    def fterm(row: Mapping[str, Any], complement: bool = False) -> T:
        if complement:
            return T(_complement(row), _EMPTY, (row["factor_id"],))
        low = row["value_low"]
        b = Bounds(
            low,
            row["value_central"],
            row["value_high"],
            nd_floored=bool(row.get("below_detection")) and low == 0,
        )
        return T(
            b,
            frozenset({"inherited_flag"}) if b.nd_floored else _EMPTY,
            (row["factor_id"],),
        )

    def app(self, x: T, unit: str, row: Mapping[str, Any]) -> T:
        b = apply(x.b, unit, row)
        ts = (x, self.fterm(row))
        return _mk(b, _product_causes(b, ts), ts)

    def share(self, row: Mapping[str, Any]) -> T:
        if row["unit"] != "1":
            raise LibError(
                f"factor {row['factor_id']!r}: unit {row['unit']!r}, expected '1'"
            )
        return self.fterm(row)

    # ---- rows ----------------------------------------------------------------------------
    def emit(
        self,
        year: int,
        substream: str,
        stage: str,
        country: str,
        group: str,
        tier: str,
        t: T,
        rule: str,
        *,
        route: str = "",
        residue: str = "",
        appended: Sequence[str] = (),
        comps: Sequence[str] | None = None,
    ) -> None:
        if _tzero(t):
            return  # spec 13.15: no row with bounds exactly (0, 0, 0)
        notes = RULE[rule]
        for a in appended:
            notes += f"; {a}"
        if comps:
            notes += "; components: " + "+".join(comps)
        basis = "+".join(b for b in BASIS_ORDER if b in t.w)
        if basis:
            notes += f"; driver basis: {basis}"
        if t.b.nd_floored:
            causes = [c for c in CAUSE_ORDER if c in t.causes] or ["inherited_flag"]
            notes += "; below_detection cause: " + "+".join(causes)
        sources = set(t.s)
        for fid in t.f:
            sources.update(self.fsources[fid])
        row = make_row(
            bounds=t.b,
            year=year,
            stream=STREAM,
            substream=substream,
            stage=stage,
            country=country,
            group=group,
            tier=tier,
            quantity="flow",
            unit=master_unit("Bq", "flow"),
            basis="modelled",
            allocation_variant="default",
            embedded_fuel=False,
            route=route or None,
            residue_type=residue or None,
            factor_ids=list(t.f),
            source_ids=sorted(sources),
            notes=notes,
        )
        (self.rows if year >= FIRST_YEAR_MAIN else self.rows_pre1950).append(row)

    # ---- rest-of-world residual -----------------------------------------------------------
    def residual(
        self, series: str, year: int, listed: Sequence[str]
    ) -> tuple[str, Any, float]:
        """("zero" | "neg" | "ok", T or magnitude) for the world row minus the listed countries."""
        world = self.drv(series, year, WORLD_ACTIVITY)
        assert world is not None
        listed_rows = [self.act[series][year][c] for c in listed]
        total = sum_independent(d.t.b for d in listed_rows)
        diff, raw = _independent_difference(world.t.b, total)
        if abs(raw) <= TOLERANCE * world.t.b.central:
            return "zero", None, raw
        if raw < 0:
            return "neg", -raw, raw
        causes = frozenset({"clipped_difference"}) if diff.nd_floored else _EMPTY
        rows = [world, *listed_rows]
        term = T(
            diff, causes, (), _union(d.t.s for d in rows), _union(d.t.w for d in rows)
        )
        return "ok", term, raw

    # ---- geothermal -----------------------------------------------------------------------
    def geothermal(self) -> None:
        by_year = self.act.get(GEO_SERIES, {})
        for y in sorted(by_year):
            listed = self.countries(GEO_SERIES, y)
            units: list[tuple[str, str, T, str, list[str]]] = []
            if listed:
                for c in listed:
                    d = by_year[y][c]
                    if not _tzero(d.t):
                        units.append((c, c, d.t, d.unit, []))
                if WORLD_ACTIVITY in by_year[y]:
                    kind, res, _ = self.residual(GEO_SERIES, y, listed)
                    if kind == "neg":
                        self.negative(y, WORLD_ROW, res, "TWh")
                    elif kind == "ok":
                        units.append(
                            (
                                WORLD_ROW,
                                WORLD_ACTIVITY,
                                res,
                                by_year[y][WORLD_ACTIVITY].unit,
                                [TXT_REST],
                            )
                        )
            elif WORLD_ACTIVITY in by_year[y]:
                d = by_year[y][WORLD_ACTIVITY]
                if not _tzero(d.t):
                    units.append((WORLD_ROW, WORLD_ACTIVITY, d.t, d.unit, [TXT_WORLD]))
            for out_country, region, g, unit, appended in units:
                self.geo_unit(y, out_country, region, g, unit, appended)

    def geo_unit(
        self,
        y: int,
        out_country: str,
        region: str,
        g: T,
        unit: str,
        appended: list[str],
    ) -> None:
        common = {"route": "air_vented_gas", "appended": appended}
        f222 = self.sel(
            y,
            region,
            stage=GEO,
            group="Rn222+",
            tier="liberated",
            route="air_vented_gas",
            driver=GEO_SERIES,
        )
        t222 = self.app(g, unit, f222)
        self.emit(
            y, GEO, GEO, out_country, "Rn222+", "liberated", t222, "geo222", **common
        )
        f220 = self.sel(
            y,
            region,
            stage=GEO,
            group="Rn220+",
            tier="liberated",
            route="air_vented_gas",
            driver=GEO_SERIES,
        )
        if f220["unit"] != "1":
            raise LibError(
                f"factor {f220['factor_id']!r}: Rn-220 ratio unit {f220['unit']!r}, expected '1'"
            )
        self.emit(
            y,
            GEO,
            GEO,
            out_country,
            "Rn220+",
            "liberated",
            _tprod(t222, self.fterm(f220)),
            "geo220",
            **common,
        )
        fm = self.sel(
            y,
            region,
            stage=GEO,
            tier="impounded",
            residue="geothermal_scale",
            driver=GEO_SERIES,
        )
        mass = self.app(g, unit, fm)
        for grp in self.geo_scale_groups:
            fg = self.sel(
                y,
                region,
                stage=GEO,
                group=grp,
                tier="impounded",
                residue="geothermal_scale",
            )
            self.emit(
                y,
                GEO,
                GEO,
                out_country,
                grp,
                "impounded",
                self.app(mass, "t", fg),
                "geoscale",
                residue="geothermal_scale",
                appended=appended,
            )

    # ---- biomass ---------------------------------------------------------------------------
    def biomass(self) -> None:
        years: set[int] = set()
        for s in (*PEAT_SERIES, "wood_fuel_t", "charcoal_production_t"):
            years |= set(self.act.get(s, {}))
        for y in sorted(years):
            peat_countries: set[str] = set()
            for s in PEAT_SERIES:
                peat_countries |= set(self.countries(s, y))
            wood_listed = self.countries("wood_fuel_t", y)
            wood_units: dict[str, tuple[str, T]] = {}
            for c in wood_listed:
                w = self.act["wood_fuel_t"][y][c].t
                if not _tzero(w):
                    wood_units[c] = (c, w)
            charcoal_rest: T | None = None
            if self.drv("wood_fuel_t", y, WORLD_ACTIVITY) is not None:
                kind, res, _ = self.residual("wood_fuel_t", y, wood_listed)
                if kind == "neg":
                    self.negative(y, WORLD_ROW, res, "t")
                elif kind == "ok":
                    wood_units[WORLD_ROW] = (WORLD_ACTIVITY, res)
                    if self.drv("charcoal_production_t", y, WORLD_ACTIVITY) is not None:
                        ch_listed = self.countries("charcoal_production_t", y)
                        ck, cres, _ = self.residual(
                            "charcoal_production_t", y, ch_listed
                        )
                        if ck == "neg":
                            self.negative(y, WORLD_ROW, cres, "t")
                        elif ck == "ok":
                            charcoal_rest = cres
            for c in sorted(peat_countries | set(wood_units)):
                peat = self.peat(y, c) if c in peat_countries else None
                wu = None
                if c in wood_units:
                    region, w = wood_units[c]
                    wu = self.wood_unit(
                        y, c, region, w, charcoal_rest if c == WORLD_ROW else None
                    )
                self.cs_rows(y, c, peat, wu)

    # ---- peat -------------------------------------------------------------------------------
    def peat(self, y: int, c: str) -> dict | None:
        def get(series: str) -> T | None:
            d = self.drv(series, y, c)
            return d.t if d is not None else None

        tpl, thh, ts = (get(s) for s in PEAT_SERIES)
        present = [t for t in (tpl, thh, ts) if t is not None]
        if all(_tzero(t) for t in present):
            return None
        all_s, all_w = _union(t.s for t in present), _union(t.w for t in present)
        ppl = tpl if tpl is not None else ZERO
        phh = thh if thh is not None else ZERO
        poth = ZERO
        if ts is None:
            self.supply_missing.setdefault(c, set()).add(y)
        else:
            sub = sum_independent(t.b for t in (ppl, phh) if not _tzero(t))
            diff, raw = _independent_difference(ts.b, sub)
            if abs(raw) > TOLERANCE * ts.b.central:
                if raw < 0:
                    self.negative(y, c, -raw, "t", peat=True)
                causes = (
                    frozenset({"clipped_difference"}) if diff.nd_floored else _EMPTY
                )
                # The residual reads all three series; the clipped (0, 0, h) term contributes.
                poth = T(diff, causes, (), all_s, all_w, frozenset({"peat_other"}))
        if not _tzero(ppl):
            ppl = ppl.with_meta(c=frozenset({"peat_plant"}))

        out: dict = {"plant": None, "hh": None}
        f_ash = self.sel(y, "XWL", stage=BP, residue="peat_ash")
        d_pl = (
            self.app(ppl, "t", self.sel(y, "XWL", stage=BP, driver="peat_power_heat_t"))
            if not _tzero(ppl)
            else ZERO
        )
        d_oth = (
            self.app(poth, "t", self.sel(y, "XWL", stage=BP, driver="peat_supply_t"))
            if not _tzero(poth)
            else ZERO
        )
        dry = _tsum([d_pl, d_oth])
        if not _tzero(dry):
            f_fly = self.sel(
                y, "XWL", stage=BP, residue="peat_ash", driver="peat_power_heat_t"
            )
            f_p = self.sel(
                y,
                "XWL",
                stage=BP,
                tier="liberated",
                route="air_stack",
                driver="peat_power_heat_t",
            )
            f_imp = self.sel(
                y,
                "XWL",
                stage=BP,
                tier="impounded",
                residue="peat_ash",
                driver="peat_power_heat_t",
            )
            f_dis = self.sel(
                y,
                "XWL",
                stage=BP,
                tier="dispersed",
                residue="peat_ash",
                driver="peat_power_heat_t",
            )
            ash = self.app(dry, "t", f_ash)
            tags = [t for t in COMP_ORDER[BP] if t in ash.c]
            for g in self.peat_groups:
                f_a = self.sel(y, "XWL", stage=BP, group=g, residue="peat_ash")
                f_e = self.sel(
                    y,
                    "XWL",
                    stage=BP,
                    group=g,
                    tier="liberated",
                    route="air_stack",
                    driver="peat_power_heat_t",
                )
                ag = self.app(ash, "t", f_a)
                stack, capped = _cap(
                    _tprod(ag, self.share(f_p), self.share(f_e)),
                    _tprod(ag, self.share(f_fly)),
                )
                if capped:
                    self.note(
                        "cap_applied",
                        y,
                        c,
                        g,
                        "plant stack cap: capped " + "+".join(capped),
                    )
                rg = _tdiff(ag, stack)
                self.emit(
                    y,
                    BP,
                    BP,
                    c,
                    g,
                    "liberated",
                    stack,
                    "pstack",
                    route="air_stack",
                    comps=tags,
                )
                for tier, f_s in (("impounded", f_imp), ("dispersed", f_dis)):
                    self.emit(
                        y,
                        BP,
                        BP,
                        c,
                        g,
                        tier,
                        _tprod(rg, self.share(f_s)),
                        "pash",
                        residue="peat_ash",
                        comps=tags,
                    )
            out["plant"] = {"A": ash}
        if not _tzero(phh):
            phh2 = phh.with_meta(c=frozenset({"peat_household"}))
            f_d = self.sel(y, "XWL", stage=BP, driver="peat_household_t")
            f_s = self.sel(
                y,
                "XWL",
                stage=BP,
                tier="liberated",
                route="air_stack",
                driver="peat_household_t",
            )
            f_imp = self.sel(
                y,
                "XWL",
                stage=BP,
                tier="impounded",
                residue="peat_ash",
                driver="peat_household_t",
            )
            f_dis = self.sel(
                y,
                "XWL",
                stage=BP,
                tier="dispersed",
                residue="peat_ash",
                driver="peat_household_t",
            )
            ash_h = self.app(self.app(phh2, "t", f_d), "t", f_ash)
            for g in self.peat_groups:
                f_a = self.sel(y, "XWL", stage=BP, group=g, residue="peat_ash")
                f_e = self.sel(
                    y,
                    "XWL",
                    stage=BP,
                    group=g,
                    tier="liberated",
                    route="air_stack",
                    driver="peat_power_heat_t",
                )
                hg = self.app(ash_h, "t", f_a)
                smoke, capped = _cap(_tprod(hg, self.share(f_s), self.share(f_e)), hg)
                if capped:
                    self.note(
                        "cap_applied",
                        y,
                        c,
                        g,
                        "household smoke cap: capped " + "+".join(capped),
                    )
                rg = _tdiff(hg, smoke)
                self.emit(
                    y, DOM, BP, c, g, "liberated", smoke, "hstack", route="air_stack"
                )
                for tier, f_sh in (("impounded", f_imp), ("dispersed", f_dis)):
                    self.emit(
                        y,
                        DOM,
                        BP,
                        c,
                        g,
                        tier,
                        _tprod(rg, self.share(f_sh)),
                        "hash",
                        residue="peat_ash",
                    )
            out["hh"] = {"A": ash_h}
        return out

    # ---- wood ---------------------------------------------------------------------------------
    def wood_unit(
        self, y: int, c: str, region: str, w: T, charcoal_rest: T | None
    ) -> dict:
        xxx = c == WORLD_ROW
        f_d = self.sel(y, region, stage=BP, driver="wood_fuel_t")
        f_rho = self.sel(y, region, stage=BP, driver="household_fuelwood_m3")
        f_sh = self.sel(y, region, stage=BP, driver="wood_fuel_m3")
        f_k = self.sel(y, region, stage=BP, driver="charcoal_production_t")
        if xxx:
            ct = charcoal_rest if charcoal_rest is not None else ZERO
            m = None
        else:
            cd = self.drv("charcoal_production_t", y, c)
            ct = cd.t if cd is not None else ZERO
            md = self.drv("household_fuelwood_m3", y, c)
            m = md.t if md is not None else None
            m_unit = md.unit if md is not None else "m3"
        id48, id49, id50, id51 = (f["factor_id"] for f in (f_d, f_rho, f_sh, f_k))
        charcoal = not _tzero(ct)
        base_f = (id48, id51) if charcoal else (id48,)
        base_s = w.s | ct.s if charcoal else w.s
        base_w = w.w | ct.w if charcoal else w.w

        d_tot = self.app(w, "t", f_d)
        d_ch = ZERO
        if charcoal:
            d_ch, capped = _cap(self.app(ct, "t", f_k), d_tot)
            d_ch = d_ch.with_meta(
                f=(id48, id51), s=w.s | ct.s, w=w.w | ct.w, c=frozenset({"charcoal"})
            )
            if capped:
                self.cap_years.setdefault(("charcoal_wood_capped", c), {}).setdefault(
                    y, set()
                ).update(capped)
        r1 = _tdiff(d_tot, d_ch)

        fallback = m is None
        if fallback:
            d_hh = self.app(r1, "t", f_sh)
            path_f, path_s, path_w = base_f + (id50,), base_s, base_w
            d_hh = d_hh.with_meta(
                f=path_f, s=path_s, w=path_w, c=frozenset({"wood_household"}), fb=True
            )
            self.fallback_years.setdefault(c, set()).add(y)
        elif _tzero(m):
            d_hh = ZERO
            path_f, path_s, path_w = base_f, base_s | m.s, base_w | m.w
        else:
            path_f, path_s, path_w = base_f + (id49,), base_s | m.s, base_w | m.w
            d_hh, capped = _cap(self.app(self.app(m, m_unit, f_rho), "t", f_d), r1)
            d_hh = d_hh.with_meta(
                f=path_f, s=path_s, w=path_w, c=frozenset({"wood_household"})
            )
            if capped:
                self.cap_years.setdefault(("household_wood_capped", c), {}).setdefault(
                    y, set()
                ).update(capped)
        d_pl = ZERO
        if not _tzero(r1):
            d_pl = _tdiff(r1, d_hh)
            if not _tzero(d_pl):
                d_pl = d_pl.with_meta(
                    f=path_f,
                    s=path_s,
                    w=path_w,
                    c=frozenset({"wood_plant"}),
                    fb=fallback,
                )

        rest = [TXT_REST] if xxx else []
        with_fb = rest + ([TXT_FALLBACK] if fallback else [])
        d_dom = _tsum([d_hh, d_ch])
        if not _tzero(d_dom):
            order = [id48, id51, id49, id50]
            d_dom = d_dom.with_meta(f=tuple(x for x in order if x in d_dom.f))
        dom_tags = [
            t
            for t in COMP_ORDER[DOM]
            if (t == "wood_household" and not _tzero(d_hh))
            or (t == "charcoal" and not _tzero(d_ch))
        ]
        dom_app = with_fb if (fallback and not _tzero(d_hh)) else rest
        for g in self.wood_groups:
            fm = self.sel(
                y,
                region,
                stage=BP,
                group=g,
                tier="memo_biosphere",
                driver="wood_fuel_t",
            )
            self.emit(
                y,
                BP,
                BP,
                c,
                g,
                "memo_biosphere",
                self.app(d_pl, "t", fm),
                "memowood",
                appended=with_fb,
                comps=["wood_plant"],
            )
            self.emit(
                y,
                DOM,
                BP,
                c,
                g,
                "memo_biosphere",
                self.app(d_dom, "t", fm),
                "memowood",
                appended=dom_app,
                comps=dom_tags,
            )
        return {"xxx": xxx, "region": region, "Dpl": d_pl, "Dhh": d_hh, "Dch": d_ch}

    # ---- fallout Cs-137 -------------------------------------------------------------------------
    def cs_rows(self, y: int, c: str, peat: dict | None, wu: dict | None) -> None:
        if peat is None and wu is None:
            return

        def share(driver: str) -> dict:
            return self.sel(
                y,
                "XWL",
                stage=BP,
                group="Cs137+",
                tier="liberated",
                route="air_rerelease",
                driver=driver,
            )

        s67, s68, s69, s70 = (
            share(d)
            for d in (
                "wood_fuel_t",
                "household_fuelwood_m3",
                "charcoal_production_t",
                "household_charcoal_t",
            )
        )
        released: dict[str, list[T]] = {BP: [], DOM: []}
        unreleased: dict[str, list[T]] = {BP: [], DOM: []}

        def split(sub: str, q: T, row: dict) -> None:
            released[sub].append(self.app(q, "Bq", row))
            unreleased[sub].append(_tprod(q, self.fterm(row, complement=True)))

        if peat is not None:
            conc = self.sel(y, "XWL", stage=BP, group="Cs137+", residue="peat_ash")
            if peat["plant"] is not None:
                split(BP, self.app(peat["plant"]["A"], "t", conc), s67)
            if peat["hh"] is not None:
                split(DOM, self.app(peat["hh"]["A"], "t", conc), s68)
        if wu is not None:
            kappa = self.sel(
                y, wu["region"], stage=BP, group="Cs137+", driver="wood_fuel_t"
            )
            if not _tzero(wu["Dpl"]):
                split(BP, self.app(wu["Dpl"], "t", kappa), s67)
            if not _tzero(wu["Dhh"]):
                split(DOM, self.app(wu["Dhh"], "t", kappa), s68)
            if not _tzero(wu["Dch"]):
                q = self.app(wu["Dch"], "t", kappa)
                released[DOM].append(self.app(q, "Bq", s69))
                released[DOM].append(_tprod(q, self.fterm(s69, True), self.fterm(s70)))
                unreleased[DOM].append(
                    _tprod(q, self.fterm(s69, True), self.fterm(s70, True))
                )
        for sub in (BP, DOM):
            if not released[sub] and not unreleased[sub]:
                continue
            for terms, rule, tier, route in (
                (released[sub], "rerel", "liberated", "air_rerelease"),
                (unreleased[sub], "memocs", "memo_biosphere", ""),
            ):
                total = _tsum(terms)
                tags = [t for t in COMP_ORDER[sub] if t in total.c]
                appended = ([TXT_REST] if wu is not None and wu["xxx"] else []) + (
                    [TXT_FALLBACK] if total.fb else []
                )
                self.emit(
                    y,
                    sub,
                    BP,
                    c,
                    "Cs137+",
                    tier,
                    total,
                    rule,
                    route=route,
                    appended=appended,
                    comps=tags,
                )

    # ---- log -------------------------------------------------------------------------------------
    def log_entries(self) -> list[dict]:
        log = list(self.log)
        for series, labels in (
            (GEO_SERIES, (GEO_SERIES,)),
            ("wood_fuel_t", ("wood_fuel_t",)),
            ("peat_supply_t", PEAT_SERIES),
        ):
            have = {y for s in labels for y, cs in self.act.get(s, {}).items() if cs}
            for a, b in _runs(
                y for y in range(FIRST_YEAR, LAST_YEAR + 1) if y not in have
            ):
                log.append(
                    {
                        "kind": "no_driver",
                        "year": a,
                        "country": WORLD_ROW,
                        "group": "",
                        "detail": f"{_run_text(a, b)}: {series} has no value",
                    }
                )
        for c in sorted(self.supply_missing):
            for a, b in _runs(self.supply_missing[c]):
                log.append(
                    {
                        "kind": "no_driver",
                        "year": a,
                        "country": c,
                        "group": "",
                        "detail": f"{_run_text(a, b)}: peat_supply_t has no value",
                    }
                )
        for c in sorted(self.fallback_years):
            for a, b in _runs(self.fallback_years[c]):
                log.append(
                    {
                        "kind": "household_fallback",
                        "year": a,
                        "country": c,
                        "group": "",
                        "detail": f"{_run_text(a, b)}: no household_fuelwood_m3 row; "
                        "household share other:0050 used",
                    }
                )
        for (kind, c), by_year in sorted(self.cap_years.items()):
            for a, b in _runs(by_year):
                bounds = set().union(*(by_year[y] for y in range(a, b + 1)))
                log.append(
                    {
                        "kind": kind,
                        "year": a,
                        "country": c,
                        "group": "",
                        "detail": f"{_run_text(a, b)}: capped "
                        + "+".join(x for x in BOUND_ORDER if x in bounds),
                    }
                )
        for series, y in sorted(self.pred):
            log.append(
                {
                    "kind": "predecessor_dropped",
                    "year": y,
                    "country": "CZE",
                    "group": "",
                    "detail": f"{series}: CZE value dropped, CSK value used",
                }
            )
        log.append(
            {
                "kind": "no_family",
                "year": "",
                "country": "",
                "group": "",
                "detail": "stage hydro: no registry rows",
            }
        )
        log.append(
            {
                "kind": "no_family",
                "year": "",
                "country": "",
                "group": "",
                "detail": "stage construction: no registry rows; construction deferred (D75)",
            }
        )
        return log


def build(root: Path | str) -> BuildResult:
    """Build the other-energy master rows for 1950-2025, the pre-1950 flow rows and the build log.

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
        b.geothermal()
        b.biomass()
    finally:
        lib_logger.removeHandler(handler)
        lib_logger.propagate, level = saved
        lib_logger.setLevel(level)
    log = b.log_entries()
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
    parser = argparse.ArgumentParser(
        prog="python -m pipeline.streams.other", description=__doc__
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="repository root (default: the checkout containing this file)",
    )
    parser.add_argument(
        "--write", action="store_true", help="overwrite the committed outputs"
    )
    args = parser.parse_args(argv)
    root: Path = args.root

    if not args.write:
        # Ambiguity is decidable before the (slow) build.
        early = diff_mode_preflight(root, (MAIN_OUTPUT, PRE1950_OUTPUT))
        if early is not None:
            return early

    result = build(root)
    counts = Counter(e["kind"] for e in result.log)
    print(
        f"rows 1950-2025: {len(result.rows)}; rows 1800-1949: {len(result.rows_pre1950)}"
    )
    for kind in LOG_KINDS:
        print(f"log {kind}: {counts.get(kind, 0)}")

    targets = ((MAIN_OUTPUT, result.rows), (PRE1950_OUTPUT, result.rows_pre1950))
    return finish(root, targets, result.log, LOG_OUTPUT, write_log, args.write)


if __name__ == "__main__":
    raise SystemExit(main())
