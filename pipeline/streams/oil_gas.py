"""Oil and gas stream script (Task 2.3). Contract: docs/OIL_GAS_SPEC.md (v1.1, including section 13).

Usage: ``python -m pipeline.streams.oil_gas [--root PATH] [--write]``

The script is a pure function of ``data/activity/`` and ``data/factors/oil_gas.csv``. It never
decays anything: decay, ingrowth, exhalation and seepage belong to the Phase 3 engine, and it
reads neither ``data/reference/`` nor ``data/events.csv`` (no civil oil and gas event, D32).
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
from pipeline.lib.allocation import shares as alloc_shares
from pipeline.lib.allocation import variant_token
from pipeline.lib.bounds import Bounds, product, sum_correlated, sum_independent
from pipeline.lib.factors import apply, master_unit, result_unit, select
from pipeline.lib.io import read_table
from pipeline.lib.rows import make_row, write_master

STREAM = "oil_gas"
WORLD_ACTIVITY = "XWL"  # world aggregate in activity and factor tables
WORLD_ROW = "XXX"  # SCHEMA V10: master rows use XXX for global data
FIRST_YEAR_MAIN = 1950
WALK_YEARS = range(1900, 2026)  # pre-1950 goes through the same code path (OIL_GAS_SPEC 3.8)
RESIDUAL_TOLERANCE = 1e-5  # OIL_GAS_SPEC 3.4: a smaller rest-of-world residual is exactly 0

PRODUCTS = ("oil", "gas", "ngl")
VARIANTS = ("default", "bound_main", "bound_radio")
SUBSTREAMS = ("conventional", "unconventional")
SOLID_RESIDUES = ("og_scale", "og_sludge")
PB210, RA226 = "Pb210+", "Ra226+"

WATER_SERIES = "produced_water_m3"
SHARE_SERIES = "produced_water_unconv_share"
OIL_SANDS_SERIES = "oil_sands_ore_processed_t"
FLARE_SERIES = "gas_flared_m3"
VERTICAL_SERIES = "us_wells_drilled_vertical"
HORIZONTAL_SERIES = "us_wells_drilled_horizontal"
QUANTITY_SERIES = {
    "oil": "oil_production_m3",
    "gas": "gas_production_m3",
    "ngl": "ngl_production_m3",
}
VALUE_SERIES = {
    "oil": "unit_value_oil_usd_per_m3",
    "gas": "unit_value_gas_usd_per_m3",
    "ngl": "unit_value_ngl_usd_per_m3",
}
ACTIVITY_FILES = ("oil_gas.csv", "oil_gas_drivers.csv")
# Series the script reads (OIL_GAS_SPEC 2.1). The benchmark-only series are left to the tests.
USED_SERIES = frozenset(
    {
        WATER_SERIES,
        "gas_production_m3",
        "oil_production_t",
        "oil_production_m3",
        "ngl_production_m3",
        *VALUE_SERIES.values(),
        FLARE_SERIES,
        OIL_SANDS_SERIES,
        VERTICAL_SERIES,
        HORIZONTAL_SERIES,
    }
)

LOG_KINDS = (
    "no_factor",
    "no_driver",
    "no_unit_value",
    "no_family",
    "negative_residual",
    "cap_applied",
    "lib_warning",
)
# OIL_GAS_SPEC 8: these kinds are written once per contiguous year run.
RUN_KINDS = ("no_factor", "no_driver", "no_unit_value")
CAUSE_ORDER = (
    "zero_central_factor",
    "exact_zero",
    "clipped_difference",
    "floor_dominance",
    "inherited_flag",
)
DRIVER_BASIS_WORDS = frozenset({"extrapolated", "interpolated"})
ALLOC_BASIS_WORDS = frozenset({"extrapolated", "interpolated", "modelled"})
LOG_COLUMNS = ("kind", "year", "country", "group", "detail")
KEY_COLUMNS = ("stage", "substream", "driver_series", "group", "tier", "route", "residue_type")

REST_GAS = "rest of world (world aggregate minus listed countries)"
REST_WATER = "rest of world (world aggregate minus USA)"
WORLD_FLARE = "world aggregate (no country split before 2012)"

MAIN_OUTPUT = Path("data") / "streams" / "oil_gas.csv"
PRE1950_OUTPUT = Path("data") / "streams_pre1950" / "oil_gas.csv"
LOG_OUTPUT = Path("research") / "oil_gas" / "build_log.csv"


@dataclass(frozen=True)
class BuildResult:
    rows: list[dict]
    rows_pre1950: list[dict]
    log: list[dict]


# --------------------------------------------------------------------------------------
# bounds helpers
# --------------------------------------------------------------------------------------
def _independent_difference(a: Bounds, b: Bounds) -> tuple[Bounds, float]:
    """Independent difference $a-b$ (OIL_GAS_SPEC 3.4).

    Returns the clipped result and the raw (possibly negative) central difference so that the
    caller can log a negative result. A clipped low bound sets ``nd_floored``.
    """
    raw = a.central - b.central
    c = max(raw, 0.0)
    low_raw = c - math.hypot(a.central - a.low, b.high - b.central)
    high = c + math.hypot(a.high - a.central, b.central - b.low)
    low = max(low_raw, 0.0)
    return Bounds(low, c, max(high, c), nd_floored=low_raw < 0.0 or raw < 0.0), raw


def _correlated_difference(a: Bounds, b: Bounds) -> Bounds:
    """Correlated difference $a-b$ of two quantities that move together (OIL_GAS_SPEC 3.4).

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
    flagged = low == 0.0 and raw.nd_floored
    return Bounds(low, central, high, nd_floored=flagged), changed


def _factor_bounds(factor: Mapping[str, Any]) -> Bounds:
    low = factor["value_low"]
    return Bounds(
        low,
        factor["value_central"],
        factor["value_high"],
        nd_floored=bool(factor.get("below_detection")) and low == 0,
    )


# --------------------------------------------------------------------------------------
# bounds with flag causes (OIL_GAS_SPEC 3.3)
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


def _share_q(factor: Mapping[str, Any]) -> _Q:
    """A unit-1 factor row (a share or ratio) as a ``_Q`` (OIL_GAS_SPEC 3.4).

    The unit must be exactly ``1`` and the high bound at most 1, else ``LibError``. A zero
    central with a positive high is the cause of any flag it brings.
    """
    if factor["unit"] != "1":
        raise LibError(
            f"factor {factor['factor_id']!r}: a share must have unit '1', got {factor['unit']!r}"
        )
    if factor["value_high"] > 1:
        raise LibError(
            f"factor {factor['factor_id']!r}: share with high {factor['value_high']!r} above 1"
        )
    b = _factor_bounds(factor)
    zero = b.central == 0 and b.high > 0
    return _Q(b, frozenset({"zero_central_factor"}) if zero else frozenset())


def _complement_q(s: _Q) -> _Q:
    """$1-s$ of a share, anti-correlated with $s$ (OIL_GAS_SPEC 3.4)."""
    b = Bounds(1.0 - s.b.high, 1.0 - s.b.central, 1.0 - s.b.low)
    zero = b.central == 0 and b.high > 0
    return _Q(b, frozenset({"zero_central_factor"}) if zero else frozenset())


def _qproduct(*terms: _Q) -> _Q:
    return _q_finish(product(*(t.b for t in terms)), terms)


def _qapply(driver: _Q, unit: str, factor: Mapping[str, Any]) -> _Q:
    f_zero = factor["value_central"] == 0 and factor["value_high"] > 0
    f = _Q(_factor_bounds(factor), frozenset({"zero_central_factor"}) if f_zero else frozenset())
    return _q_finish(apply(driver.b, unit, factor), (driver, f))


def _qsum_correlated(terms: Sequence[_Q]) -> _Q:
    return _q_finish(sum_correlated(t.b for t in terms), terms)


def _qsum_independent(terms: Sequence[_Q]) -> _Q:
    return _q_finish(sum_independent(t.b for t in terms), terms)


def _qdiff_independent(a: _Q, b: _Q) -> tuple[_Q, float]:
    out, raw = _independent_difference(a.b, b.b)
    return _q_finish(out, (a, b), ("clipped_difference",)), raw


def _qdiff_correlated(a: _Q, b: _Q) -> tuple[_Q, float]:
    raw_low = a.b.low - b.b.low
    raw_central = a.b.central - b.b.central
    raw_high = a.b.high - b.b.high
    # A positive raw low clamped to the central is not clipping; only a raw low or central
    # below 0 is a clipped difference, and a true zero is flagged as such.
    if raw_low < 0.0 or raw_central < 0.0:
        extra: tuple[str, ...] = ("clipped_difference",)
    elif raw_central == 0.0 and raw_high == 0.0:
        extra = ("exact_zero",)
    else:
        extra = ()
    return _q_finish(_correlated_difference(a.b, b.b), (a, b), extra), raw_central


def _merge(*groups: Iterable[str]) -> list[str]:
    """Order-preserving de-duplication of id lists."""
    seen: dict[str, None] = {}
    for group in groups:
        for item in group:
            seen.setdefault(item, None)
    return list(seen)


def _no_factor(exc: LibError) -> bool:
    """Only a missing factor row is tolerated; ambiguity and other errors propagate (3.6)."""
    return str(exc).startswith("no factor row")


# --------------------------------------------------------------------------------------
# allocation rules (OIL_GAS_SPEC 4.4, 4.5)
# --------------------------------------------------------------------------------------
def _values(quantities: Mapping[str, float], values: Mapping[str, float]) -> dict[str, float]:
    return {p: quantities.get(p, 0.0) * values.get(p, 0.0) for p in PRODUCTS}


def _main_product(quantities: Mapping[str, float], values: Mapping[str, float]) -> str:
    """Largest $q_pv_p$; ties in the order oil, gas, ngl (OIL_GAS_SPEC 4.4)."""
    val = _values(quantities, values)
    return max(PRODUCTS, key=lambda p: (val[p], -PRODUCTS.index(p)))


def _radio_product(
    geography: str,
    year: int,
    quantities: Mapping[str, float],
    values: Mapping[str, float],
) -> str:
    """Rule R3 (D70): the product with the second-largest value $q_pv_p$ (OIL_GAS_SPEC 4.5).

    ``quantities`` is ``{product: q}`` and ``values`` ``{product: unit value}``. The geography
    and year are accepted so that a later rule can depend on them; R3 does not.
    """
    val = _values(quantities, values)
    main = _main_product(quantities, values)
    rest = [p for p in PRODUCTS if p != main]
    return max(rest, key=lambda p: (val[p], -PRODUCTS.index(p)))


@dataclass(frozen=True)
class _Alloc:
    shares: Mapping[str, Mapping[str, float]]  # variant -> product -> share
    basis: str  # `+`-joined allocation-basis words (OIL_GAS_SPEC 3.3), may be empty
    sources: tuple[str, ...]


@dataclass(frozen=True)
class _Driver:
    bounds: Bounds
    sources: tuple[str, ...]
    basis: str = ""

    @property
    def q(self) -> _Q:
        # A flagged activity row passes its flag on (inherited_flag).
        return _Q(self.bounds, frozenset({"inherited_flag"}) if self.bounds.nd_floored else frozenset())


@dataclass
class _Contribution:
    q: _Q
    factors: list[dict]
    unit: str


@dataclass(frozen=True)
class _Single:
    """A single-driver processing_transport row family (OIL_GAS_SPEC 6.2, 6.3)."""

    code: str
    series: str
    driver_unit: str
    product: str
    group: str
    tier: str
    route: str
    select_residue: str  # the registry residue type, a key device on GN
    row_residue: str | None  # the residue type of the master row
    text: str


SINGLES = (
    _Single("GD", "gas_production_m3", "m3", "gas", "Rn222+", "liberated", "air_delivered_gas",
            "", None, "radon in delivered sales gas"),
    _Single("GN", "gas_production_m3", "m3", "ngl", "Rn222+", "liberated", "air_delivered_gas",
            "og_processing_residue", None, "radon diverted with natural gas liquids"),
    _Single("GV", "gas_production_m3", "m3", "gas", "Rn222+", "liberated", "air_vented_gas",
            "", None, "radon in vented gas"),
    _Single("GP", "gas_production_m3", "m3", "gas", "Pb210+", "impounded", "",
            "og_processing_residue", "og_processing_residue", "Pb-210 plate-out in the gas system"),
    _Single("OR", "oil_production_t", "t", "oil", "Rn222+", "liberated", "air_stack",
            "", None, "radon in crude oil"),
)


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
        self.factors = self._load_factors(root / "data" / "factors" / "oil_gas.csv")
        self.by_stage: dict[str, list[dict]] = {}
        for f in self.factors:
            self.by_stage.setdefault(f["stage"], []).append(f)

        self.series: dict[tuple[str, str], dict[int, _Driver]] = {}
        self.countries_by_year: dict[str, dict[int, list[str]]] = {}
        self._load_activity(root / "data" / "activity")
        self.value_first_year = {
            p: min((y for (s, _), by in self.series.items() if s == VALUE_SERIES[p] for y in by), default=None)
            for p in PRODUCTS
        }

        self.rows: list[dict] = []
        self.rows_pre1950: list[dict] = []
        self.log: list[dict] = []
        # (kind, label, country, group) -> years, written as contiguous runs (OIL_GAS_SPEC 8)
        self.runs: dict[tuple[str, str, str, str], set[int]] = {}
        self._cache: dict[tuple, Any] = {}
        self._units: dict[tuple[str, str], str] = {}
        self._alloc_cache: dict[tuple[str, int], _Alloc | None] = {}
        self._residual_cache: dict[tuple[str, int], tuple[_Q, list[_Driver]] | None] = {}
        self._negative_seen: set[tuple[int, str]] = set()

        # Families discovered from the registry (OIL_GAS_SPEC 3.2): never a hard-coded list.
        self.water_groups = {
            s: self._groups(stage="production", substream=s) for s in SUBSTREAMS
        }
        solids = self._groups(
            stage="production", substream="", tier="", route="", driver_series="",
            residue_type="og_scale",
        )
        self.solids_groups = [g for g in solids if g not in ("", PB210)]
        self.pb_groups = [g for g in solids if g == PB210]
        self.fate_keys = sorted(
            {
                (f["tier"], f["route"], f["residue_type"])
                for f in self.by_stage.get("production", [])
                if f["substream"] == "" and f["driver_series"] == WATER_SERIES and f["group"] == ""
            }
        )
        self.removed_keys = {
            r: sorted(
                {
                    (f["tier"], f["route"])
                    for f in self.by_stage.get("production", [])
                    if f["substream"] == "" and f["driver_series"] == "" and f["group"] == ""
                    and f["tier"] != "" and f["residue_type"] == r
                }
            )
            for r in SOLID_RESIDUES
        }
        self.retained_keys = sorted(
            {
                (f["tier"], f["residue_type"])
                for f in self.by_stage.get("abandonment_scrap", [])
                if f["tier"] != ""
            }
        )
        self.drilling_groups = {
            s: self._groups(stage="drilling", substream=s) for s in SUBSTREAMS
        }
        self.oil_sands_groups = self._groups(stage="oil_sands_mining")

    # ---- loading --------------------------------------------------------------------
    @staticmethod
    def _load_factors(path: Path) -> list[dict]:
        factors = read_table(path)
        for f in factors:
            for col in KEY_COLUMNS:
                if f.get(col) is None:
                    f[col] = ""
            driver = f["driver_series"]
            if f["stage"] == "oil_sands_mining" and driver not in ("", OIL_SANDS_SERIES):
                raise LibError(
                    f"driver mismatch: factor {f['factor_id']!r} names driver_series {driver!r}, "
                    f"the script uses {OIL_SANDS_SERIES!r}"
                )
        return factors

    def _load_activity(self, folder: Path) -> None:
        seen: set[tuple[str, str, int]] = set()
        for name in ACTIVITY_FILES:
            path = folder / name
            if not path.is_file():
                continue
            for r in read_table(path):
                key = (r["series"], r["country"], r["year"])
                if key in seen:
                    raise LibError(
                        f"duplicate activity row: series {r['series']!r}, country "
                        f"{r['country']!r}, year {r['year']}"
                    )
                seen.add(key)
                if r["series"] not in USED_SERIES:
                    continue
                low = r["value_low"]
                bounds = Bounds(
                    low,
                    r["value_central"],
                    r["value_high"],
                    nd_floored=bool(r.get("below_detection")) and low == 0,
                )
                driver = _Driver(bounds, tuple(r["source_ids"] or ()), r.get("basis") or "")
                self.series.setdefault((r["series"], r["country"]), {})[r["year"]] = driver
                if r["country"] != WORLD_ACTIVITY:
                    self.countries_by_year.setdefault(r["series"], {}).setdefault(r["year"], []).append(
                        r["country"]
                    )
        for by_year in self.countries_by_year.values():
            for countries in by_year.values():
                countries.sort()

    def _groups(self, **match: str) -> list[str]:
        """Distinct groups of the registry rows matching ``match``, in file order."""
        out: dict[str, None] = {}
        for f in self.by_stage.get(match["stage"], []):
            if all(f[k] == v for k, v in match.items()):
                out.setdefault(f["group"])
        return list(out)

    # ---- plumbing ---------------------------------------------------------------------
    def sel(self, year: int, region: str, **match: Any) -> dict:
        key = (year, region, tuple(match.items()))
        hit = self._cache.get(key)
        if hit is None:
            try:
                hit = select(self.by_stage.get(match["stage"], []), year=year, region=region, **match)
            except LibError as exc:
                self._cache[key] = exc
                raise
            self._cache[key] = hit
        elif isinstance(hit, LibError):
            raise LibError(str(hit))
        return hit

    def try_sel(
        self, year: int, region: str, country: str, group: str, what: str, /, **match: Any
    ) -> dict | None:
        """``sel`` that turns ``no factor row`` into a logged run and ``None`` (OIL_GAS_SPEC 3.6)."""
        try:
            return self.sel(year, region, **match)
        except LibError as exc:
            if not _no_factor(exc):
                raise
            self.note_run("no_factor", year, country, group, what)
            return None

    def psel(
        self, year: int, region: str, country: str, group: str, what: str, /, **kw: Any
    ) -> dict | None:
        match: dict[str, Any] = {
            "stage": "production", "substream": "", "group": "", "tier": "", "route": "", "residue_type": ""
        }
        match.update(kw)
        return self.try_sel(year, region, country, group, what, **match)

    def family_present(self, label: str, **match: str) -> bool:
        if any(all(f[k] == v for k, v in match.items()) for f in self.factors):
            return True
        self.note("no_family", "", "", "", f"{label}: the registry has no rows for {match}")
        return False

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

    def negative(self, year: int, series: str, magnitude: float, what: str) -> None:
        """One ``negative_residual`` entry per year and series (OIL_GAS_SPEC 8)."""
        if (year, series) in self._negative_seen:
            return
        self._negative_seen.add((year, series))
        self.note(
            "negative_residual",
            year,
            WORLD_ROW,
            "",
            f"{series}: {what} is {magnitude:.6g} below zero at central; set to 0",
        )

    def flow_unit(self, driver_unit: str, factor: Mapping[str, Any]) -> str:
        key = (driver_unit, factor["unit"])
        hit = self._units.get(key)
        if hit is None:
            hit = self._units[key] = master_unit(result_unit(driver_unit, factor["unit"]), "flow")
        return hit

    @staticmethod
    def sources(
        factors: Iterable[Mapping[str, Any]], drivers: Iterable[_Driver], extra: Iterable[str] = ()
    ) -> list[str]:
        ids: set[str] = set(extra)
        for f in factors:
            ids.update(f["source_ids"] or [])
        for d in drivers:
            ids.update(d.sources)
        return sorted(ids)

    def emit(
        self,
        year: int,
        q: _Q,
        *,
        drivers: Sequence[_Driver],
        notes: str,
        alloc_basis: str = "",
        **fields: Any,
    ) -> None:
        # Suffix order (OIL_GAS_SPEC 3.3): rule text, driver basis, allocation basis, cause.
        basis = "+".join(sorted({d.basis for d in drivers} & DRIVER_BASIS_WORDS))
        if basis:
            notes += f"; driver basis: {basis}"
        if alloc_basis:
            notes += f"; allocation basis: {alloc_basis}"
        if q.b.nd_floored:
            causes = [c for c in CAUSE_ORDER if c in q.causes] or ["floor_dominance"]
            notes += "; below_detection cause: " + "+".join(causes)
        row = make_row(
            bounds=q.b,
            year=year,
            stream=STREAM,
            quantity="flow",
            basis="modelled",
            embedded_fuel=False,
            notes=notes,
            **fields,
        )
        (self.rows if year >= FIRST_YEAR_MAIN else self.rows_pre1950).append(row)

    def capped(self, year: int, geo: str, group: str, raw: _Q, ceiling: _Q, where: str) -> _Q:
        out, changed = _cap(raw.b, ceiling.b)
        if not changed:
            return raw
        for name in changed:
            self.note(
                "cap_applied",
                year,
                geo,
                group,
                f"{where}: bound={name}; {getattr(raw.b, name):.6g} reduced to "
                f"{getattr(ceiling.b, name):.6g} (D54 release cap)",
            )
        return _q_finish(out, (raw, ceiling))

    # ---- rest-of-world residual -----------------------------------------------------
    def residual(self, series: str, year: int) -> tuple[_Q, list[_Driver]] | None:
        """World aggregate minus the listed countries (OIL_GAS_SPEC 6.1), or ``None``."""
        key = (series, year)
        if key in self._residual_cache:
            return self._residual_cache[key]
        out: tuple[_Q, list[_Driver]] | None = None
        xwl = self.driver(series, WORLD_ACTIVITY, year)
        if xwl is not None:
            listed = [
                self.driver(series, c, year) for c in self.countries_by_year.get(series, {}).get(year, [])
            ]
            total = _qsum_independent([d.q for d in listed if d is not None])
            r, raw = _qdiff_independent(xwl.q, total)
            if abs(raw) <= RESIDUAL_TOLERANCE * xwl.bounds.central:
                pass  # rounding: exactly 0, no rows, no log
            elif raw < 0:
                self.negative(year, series, -raw, "the world aggregate minus the listed countries")
            elif r.b.central > 0:
                out = (r, [xwl, *[d for d in listed if d is not None]])
        self._residual_cache[key] = out
        return out

    # ---- D6 allocation (OIL_GAS_SPEC 4) -----------------------------------------------
    def alloc(self, geo: str, year: int, label: str) -> _Alloc | None:
        """Shares for a geography-year, or ``None`` after logging ``no_unit_value``."""
        key = (geo, year)
        if key not in self._alloc_cache:
            self._alloc_cache[key] = self._alloc(geo, year)
        out = self._alloc_cache[key]
        if out is None:
            self.note_run("no_unit_value", year, geo, "", f"{label}: no unit value to allocate by value")
        return out

    def _alloc(self, geo: str, year: int) -> _Alloc | None:
        q: dict[str, float] = {}
        v: dict[str, float] = {}
        used: list[_Driver] = []
        for p in PRODUCTS:
            series = QUANTITY_SERIES[p]
            if geo == "USA":
                x = self.driver(series, "USA", year)
                q[p] = x.bounds.central if x else 0.0
                if x:
                    used.append(x)
            else:
                xw = self.driver(series, WORLD_ACTIVITY, year)
                us = self.driver(series, "USA", year)
                if xw is None:
                    q[p] = 0.0
                else:
                    raw = xw.bounds.central - (us.bounds.central if us else 0.0)
                    if raw < 0:
                        self.negative(year, series, -raw, "the world quantity minus the USA quantity")
                    q[p] = max(raw, 0.0)
                    used.append(xw)
                    if us:
                        used.append(us)
            vs = VALUE_SERIES[p]
            pv = self.driver(vs, "USA", year) if geo == "USA" else None
            pv = pv or self.driver(vs, WORLD_ACTIVITY, year)
            if pv is not None:
                v[p] = pv.bounds.central
                used.append(pv)
            elif q[p] > 0:
                first = self.value_first_year[p]
                if first is None or year < first:
                    return None
                raise LibError(
                    f"no unit value in {vs!r} for {year} ({geo}) although {p} has a quantity "
                    f"of {q[p]:.6g}; a gap inside the series is a data error (OIL_GAS_SPEC 4.2)"
                )
            else:
                v[p] = 0.0
        if math.fsum(q[p] * v[p] for p in PRODUCTS) <= 0:
            return None
        products = {p: (q[p], v[p]) for p in PRODUCTS}
        main = _main_product(q, v)
        radio = _radio_product(geo, year, q, v)
        by_variant = {
            variant: alloc_shares(
                products,
                variant_token(variant, default_token="alloc:value"),
                main=main,
                radio=radio,
            )
            for variant in VARIANTS
        }
        basis = "+".join(sorted({d.basis for d in used} & ALLOC_BASIS_WORDS))
        sources = sorted({s for d in used for s in d.sources})
        return _Alloc(by_variant, basis, tuple(sources))

    def emit_joint(
        self,
        year: int,
        geo: str,
        r: _Q,
        *,
        code: str,
        text: str,
        factors: Sequence[Mapping[str, Any]],
        drivers: Sequence[_Driver],
        alloc: _Alloc,
        unit: str,
        substream: str,
        stage: str,
        group: str,
        tier: str,
        route: str | None,
        residue_type: str | None,
    ) -> None:
        """The nine rows (three products times three variants) of one joint key (OIL_GAS_SPEC 4.3)."""
        factor_ids = _merge([f["factor_id"] for f in factors])
        source_ids = self.sources(factors, drivers, alloc.sources)
        for p in PRODUCTS:
            for variant in VARIANTS:
                s = alloc.shares[variant][p]
                # A zero share is a structural zero: exact, unflagged, no cause text.
                q = _Q(Bounds.exact(0.0)) if s == 0.0 else (r if s == 1.0 else r.scale(s))
                self.emit(
                    year,
                    q,
                    drivers=drivers,
                    notes=f"{code}: {text}; D6 {variant}, product {p}",
                    alloc_basis=alloc.basis if variant == "default" else "",
                    substream=substream,
                    stage=stage,
                    product=p,
                    residue_type=residue_type,
                    country=geo,
                    group=group,
                    tier=tier,
                    unit=unit,
                    allocation_variant=variant,
                    allocation_rule=variant_token(variant, default_token="alloc:value"),
                    route=route,
                    factor_ids=factor_ids,
                    source_ids=source_ids,
                )

    # ---- single-driver rows: gas and oil radon, Pb-210 plate-out (OIL_GAS_SPEC 6) ---------
    def single_family(self, sp: _Single, year: int) -> None:
        series = sp.series
        sel_match = {
            "stage": "processing_transport", "substream": "all", "group": sp.group, "tier": sp.tier,
            "route": sp.route, "residue_type": sp.select_residue,
        }
        xwl = self.driver(series, WORLD_ACTIVITY, year)
        if xwl is None:
            self.note_run("no_driver", year, WORLD_ACTIVITY, "", f"{series} has no value")
        for c in self.countries_by_year.get(series, {}).get(year, []):
            d = self.driver(series, c, year)
            if d is None or d.bounds.high == 0:
                continue
            fac = self.try_sel(year, c, c, sp.group, f"{sp.code}: {sp.text}", **sel_match)
            if fac is None:
                continue
            self.emit_single(sp, year, c, _qapply(d.q, sp.driver_unit, fac), fac, [d], "")
        res = self.residual(series, year)
        if res is None:
            return
        r, drivers = res
        fac = self.try_sel(year, WORLD_ACTIVITY, WORLD_ROW, sp.group, f"{sp.code}: {sp.text}", **sel_match)
        if fac is None:
            return
        self.emit_single(sp, year, WORLD_ROW, _qapply(r, sp.driver_unit, fac), fac, drivers, REST_GAS)

    def emit_single(
        self, sp: _Single, year: int, country: str, q: _Q, fac: dict, drivers: list[_Driver], fragment: str
    ) -> None:
        text = f"{sp.code}: {sp.text}" + (f"; {fragment}" if fragment else "")
        self.emit(
            year,
            q,
            drivers=drivers,
            notes=text,
            substream="all",
            stage="processing_transport",
            product=sp.product,
            residue_type=sp.row_residue,
            country=country,
            group=sp.group,
            tier=sp.tier,
            unit=self.flow_unit(sp.driver_unit, fac),
            allocation_variant="default",
            allocation_rule="none",
            route=sp.route or None,
            factor_ids=[fac["factor_id"]],
            source_ids=self.sources([fac], drivers),
        )

    # ---- flaring (OIL_GAS_SPEC 6.4) -----------------------------------------------------
    def flaring(self, year: int) -> None:
        match = {
            "stage": "production", "substream": "all", "group": "Rn222+", "tier": "liberated",
            "route": "air_stack", "residue_type": "", "driver_series": FLARE_SERIES,
        }
        countries = self.countries_by_year.get(FLARE_SERIES, {}).get(year, [])
        xwl = self.driver(FLARE_SERIES, WORLD_ACTIVITY, year)
        if xwl is None:
            self.note_run("no_driver", year, WORLD_ACTIVITY, "", f"{FLARE_SERIES} has no value")

        def row(country: str, q: _Q, fac: dict, drivers: list[_Driver], fragment: str) -> None:
            text = "FL: radon in flared gas" + (f"; {fragment}" if fragment else "")
            self.emit(
                year,
                q,
                drivers=drivers,
                notes=text,
                substream="all",
                stage="production",
                product="oil",
                residue_type=None,
                country=country,
                group="Rn222+",
                tier="liberated",
                unit=self.flow_unit("m3", fac),
                allocation_variant="default",
                allocation_rule="none",
                route="air_stack",
                factor_ids=[fac["factor_id"]],
                source_ids=self.sources([fac], drivers),
            )

        # Use the country rows and the residual, or the world row; never both (6.4).
        if countries:
            for c in countries:
                d = self.driver(FLARE_SERIES, c, year)
                if d is None or d.bounds.high == 0:
                    continue
                fac = self.try_sel(year, c, c, "Rn222+", "FL: radon in flared gas", **match)
                if fac is not None:
                    row(c, _qapply(d.q, "m3", fac), fac, [d], "")
            res = self.residual(FLARE_SERIES, year)
            if res is not None:
                fac = self.try_sel(
                    year, WORLD_ACTIVITY, WORLD_ROW, "Rn222+", "FL: radon in flared gas", **match
                )
                if fac is not None:
                    row(WORLD_ROW, _qapply(res[0], "m3", fac), fac, res[1], REST_GAS)
        elif xwl is not None and xwl.bounds.high != 0:
            fac = self.try_sel(
                year, WORLD_ACTIVITY, WORLD_ROW, "Rn222+", "FL: radon in flared gas", **match
            )
            if fac is not None:
                row(WORLD_ROW, _qapply(xwl.q, "m3", fac), fac, [xwl], WORLD_FLARE)

    # ---- production: produced water, scale, sludge, retained scale (OIL_GAS_SPEC 5, 7.1) -------
    def production(self, year: int) -> None:
        usa = self.driver(WATER_SERIES, "USA", year)
        xwl = self.driver(WATER_SERIES, WORLD_ACTIVITY, year)
        label = f"{WATER_SERIES} has no value"
        if usa is None:
            self.note_run("no_driver", year, "USA", "", label)
        elif usa.bounds.high != 0:
            self.production_geo(year, "USA", usa.q, [usa], "USA", "")
        if xwl is None or usa is None:
            self.note_run("no_driver", year, WORLD_ROW, "", label)
            return
        v, raw = _qdiff_correlated(xwl.q, usa.q)
        if raw < 0:
            self.negative(year, WATER_SERIES, -raw, "the world water volume minus the USA volume")
        if v.b.high == 0:
            return
        self.production_geo(year, WORLD_ROW, v, [xwl, usa], WORLD_ACTIVITY, REST_WATER)

    def production_geo(
        self, year: int, geo: str, volume: _Q, drivers: list[_Driver], region: str, fragment: str
    ) -> None:
        share_row = self.psel(
            year, region, geo, "", "PW: unconventional share", driver_series=SHARE_SERIES
        )
        phi_row = self.try_sel(
            year, WORLD_ACTIVITY, geo, "", "PW: retained-scale fraction",
            stage="abandonment_scrap", substream="", group="", tier="", route="",
            residue_type="og_scale", driver_series="",
        )
        if share_row is None or phi_row is None:
            return
        u = _share_q(share_row)
        phi = _share_q(phi_row)
        alloc = self.alloc(geo, year, WATER_SERIES)
        if alloc is None:
            return
        frag = f"; {fragment}" if fragment else ""
        for sub in SUBSTREAMS:
            water: dict[str, tuple[_Q, dict]] = {}
            contrib: dict[tuple[str, str, str, str], list[_Contribution]] = {}
            for g in self.water_groups[sub]:
                conc = self.psel(year, region, geo, g, f"PW: {sub} concentration", substream=sub, group=g)
                if conc is None:
                    continue
                unit = self.flow_unit("m3", conc)
                a = _qproduct(_qapply(volume, "m3", conc), _complement_q(u) if sub == "conventional" else u)
                water[g] = (a, conc)
                for tier, route, residue in self.fate_keys:
                    fate = self.psel(
                        year, region, geo, g, f"PW: {sub} water fate, {tier}",
                        tier=tier, route=route, residue_type=residue, driver_series=WATER_SERIES,
                    )
                    if fate is None:
                        continue
                    w = self.capped(
                        year, geo, g, _qproduct(a, _share_q(fate)), a, f"{sub} {tier} water row"
                    )
                    contrib.setdefault((tier, route, residue, g), []).append(
                        _Contribution(w, [conc, share_row, fate], unit)
                    )

            # Solids formed from the water activity (5.4): additive to the water.
            solids: dict[tuple[str, str], tuple[_Q, list[dict], str]] = {}
            for g in self.solids_groups:
                if g not in water:
                    continue
                a, conc = water[g]
                for r in SOLID_RESIDUES:
                    sigma = self.psel(
                        year, WORLD_ACTIVITY, geo, g, f"PW: solids-bound fraction, {r}",
                        group=g, residue_type=r,
                    )
                    if sigma is None:
                        continue
                    solids[(g, r)] = (
                        _qproduct(a, _share_q(sigma)),
                        [conc, share_row, sigma],
                        self.flow_unit("m3", conc),
                    )
            for g in self.pb_groups:
                for r in SOLID_RESIDUES:
                    base = solids.get((RA226, r))
                    ratio = self.psel(
                        year, WORLD_ACTIVITY, geo, g, f"PW: Pb-210 ratio, {r}", group=g, residue_type=r
                    )
                    if base is None or ratio is None:
                        continue
                    solids[(g, r)] = (
                        _qproduct(base[0], _share_q(ratio)),
                        [*base[1], ratio],
                        base[2],
                    )

            retained: dict[str, tuple[_Q, list[dict], str]] = {}
            for (g, r), (s, fs, unit) in solids.items():
                if r == "og_scale":
                    removed = _qproduct(s, _complement_q(phi))
                    retained[g] = (_qproduct(s, phi), [*fs, phi_row], unit)
                    fs_removed = [*fs, phi_row]
                else:
                    # Sludge is assumed removed in operation entirely (5.4).
                    removed, fs_removed = s, fs
                for tier, route in self.removed_keys[r]:
                    rho = self.psel(
                        year, WORLD_ACTIVITY, geo, g, f"PW: removed {r} fate, {tier}",
                        tier=tier, route=route, residue_type=r, driver_series="",
                    )
                    if rho is None:
                        continue
                    x = _qproduct(removed, _share_q(rho))
                    # The liberated tier has no residue type; the registry one is a key device.
                    residue = "" if tier == "liberated" else r
                    contrib.setdefault((tier, route, residue, g), []).append(
                        _Contribution(x, [*fs_removed, rho], unit)
                    )

            for (tier, route, residue, g), lst in sorted(contrib.items()):
                self.emit_joint(
                    year, geo, _qsum_correlated([c.q for c in lst]),
                    code="PW",
                    text=f"produced water, scale and sludge, {sub}, {tier}{frag}",
                    factors=[f for c in lst for f in c.factors],
                    drivers=drivers,
                    alloc=alloc,
                    unit=lst[0].unit,
                    substream=sub,
                    stage="production",
                    group=g,
                    tier=tier,
                    route=route or None,
                    residue_type=residue or None,
                )

            # Retained scale, booked at abandonment_scrap in the creation year (7.1).
            for g, (ret, fs, unit) in retained.items():
                for tier, residue in self.retained_keys:
                    fate = self.try_sel(
                        year, WORLD_ACTIVITY, geo, g, f"AB: retained-scale fate, {tier}",
                        stage="abandonment_scrap", substream="", group="", tier=tier, route="",
                        residue_type=residue,
                    )
                    if fate is None:
                        continue
                    self.emit_joint(
                        year, geo, _qproduct(ret, _share_q(fate)),
                        code="AB",
                        text=f"retained scale at abandonment, {sub}, {tier}{frag}",
                        factors=[*fs, fate],
                        drivers=drivers,
                        alloc=alloc,
                        unit=unit,
                        substream=sub,
                        stage="abandonment_scrap",
                        group=g,
                        tier=tier,
                        route=None,
                        residue_type=residue,
                    )

    # ---- drilling (OIL_GAS_SPEC 7.2) ----------------------------------------------------
    def drilling(self, year: int) -> None:
        for sub, series in (("conventional", VERTICAL_SERIES), ("unconventional", HORIZONTAL_SERIES)):
            d = self.driver(series, "USA", year)
            if d is None:
                self.note_run("no_driver", year, "USA", "", f"{series} has no value")
                continue
            if d.bounds.high == 0:
                continue
            found = []
            for g in self.drilling_groups[sub]:
                fac = self.try_sel(
                    year, "USA", "USA", g, f"DR: {sub} cuttings",
                    stage="drilling", substream=sub, group=g, tier="impounded", route="",
                    residue_type="og_drill_cuttings",
                )
                if fac is not None:
                    found.append((g, fac))
            if not found:
                continue
            alloc = self.alloc("USA", year, series)
            if alloc is None:
                continue
            for g, fac in found:
                self.emit_joint(
                    year, "USA", _qapply(d.q, "1", fac),
                    code="DR",
                    text=f"drilling cuttings, {sub} wells",
                    factors=[fac],
                    drivers=[d],
                    alloc=alloc,
                    unit=self.flow_unit("1", fac),
                    substream=sub,
                    stage="drilling",
                    group=g,
                    tier="impounded",
                    route=None,
                    residue_type="og_drill_cuttings",
                )

    # ---- oil sands (OIL_GAS_SPEC 7.3) ---------------------------------------------------
    def oil_sands(self, year: int) -> None:
        d = self.driver(OIL_SANDS_SERIES, "CAN", year)
        if d is None:
            self.note_run("no_driver", year, "CAN", "", f"{OIL_SANDS_SERIES} has no value")
            return
        if d.bounds.high == 0:
            return
        for g in self.oil_sands_groups:
            fac = self.try_sel(
                year, "CAN", "CAN", g, "OS: oil sands tailings",
                stage="oil_sands_mining", substream="", group=g, tier="impounded", route="",
                residue_type="oil_sands_tailings",
            )
            if fac is None:
                continue
            self.emit(
                year,
                _qapply(d.q, "t", fac),
                drivers=[d],
                notes="OS: oil sands tailings, monazite thorium chain",
                substream="oil_sands",
                stage="oil_sands_mining",
                product="bitumen",
                residue_type="oil_sands_tailings",
                country="CAN",
                group=g,
                tier="impounded",
                unit=self.flow_unit("t", fac),
                allocation_variant="default",
                allocation_rule="none",
                route=None,
                factor_ids=[fac["factor_id"]],
                source_ids=self.sources([fac], [d]),
            )

    # ---- walk ---------------------------------------------------------------------------
    def run(self) -> None:
        families = {
            "production": self.family_present(
                "PW", stage="production", driver_series=SHARE_SERIES
            ),
            "singles": [
                sp
                for sp in SINGLES
                if self.family_present(
                    sp.code, stage="processing_transport", substream="all", group=sp.group,
                    tier=sp.tier, route=sp.route, residue_type=sp.select_residue,
                )
            ],
            "flaring": self.family_present("FL", stage="production", driver_series=FLARE_SERIES),
            "drilling": self.family_present("DR", stage="drilling"),
            "oil_sands": self.family_present("OS", stage="oil_sands_mining"),
        }
        for year in WALK_YEARS:
            if families["production"]:
                self.production(year)
            for sp in families["singles"]:
                self.single_family(sp, year)
            if families["flaring"]:
                self.flaring(year)
            if families["drilling"]:
                self.drilling(year)
            if families["oil_sands"]:
                self.oil_sands(year)


def build(root: Path | str) -> BuildResult:
    """Build the oil and gas master rows for 1950-2025, the pre-1950 flow rows and the build log.

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
        b.run()
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
    parser = argparse.ArgumentParser(prog="python -m pipeline.streams.oil_gas", description=__doc__)
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
    print(f"rows 1950-2025: {len(result.rows)}; rows 1900-1949: {len(result.rows_pre1950)}")
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
