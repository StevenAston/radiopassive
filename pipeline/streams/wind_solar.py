"""Wind and solar materials stream script (Task 2.4). Contract: docs/WIND_SOLAR_SPEC.md (v1.1, D74).

Usage: ``python -m pipeline.streams.wind_solar [--root PATH] [--write]``

Stream 4 books the radioactivity mobilised in producing the commodities that new wind and solar
capacity needs (copper, aluminium, steel, rare earths and so on). Capacity additions times material
intensity give commodity tonnes per technology class; each class contribution is multiplied by a
per-tonne footprint of ``data/reference/commodity_factors.csv`` (head activity, before D6), split by
D6 for the joint-product families, and the classes are summed. The script is a pure function of
``data/activity/`` and the commodity registry. It never decays anything (decay, exhalation and
seepage belong to the Phase 3 engine) and reads no event, no fuel-input file and no engine parameter.
"""

from __future__ import annotations

import argparse
import csv
import logging
import math
import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pipeline.lib import LibError
from pipeline.lib.allocation import attribution_share, split, variant_token
from pipeline.lib.bounds import FLOOR_FRACTION, Bounds, product, sum_correlated
from pipeline.lib.factors import apply, master_unit, select
from pipeline.lib.io import read_table
from pipeline.lib.rows import make_row
from pipeline.streams._outputs import diff_mode_preflight, finish

STREAM = "wind_solar"
WORLD_ACTIVITY = "XWL"  # world aggregate in activity and factor tables
WORLD_ROW = "XXX"  # SCHEMA V10: master rows use XXX for global data
FIRST_YEAR_MAIN = 1950  # WIND_SOLAR_SPEC 13.17: the walk is 1950-2025, no pre-1950 walk
LAST_YEAR = 2025
VARIANTS = ("default", "bound_main", "bound_radio")
SHARE_TOL = 1e-12  # a share high above 1 by more than rounding raises (spec 3.4)

LOG_KINDS = (
    "no_factor",
    "no_driver",
    "no_family",
    "no_intensity",
    "no_footprint",
    "placeholder_share",
    "attribution",
    "lib_warning",
)
CAUSE_ORDER = (
    "zero_central_factor",
    "exact_zero",
    "clipped_difference",
    "floor_dominance",
    "inherited_flag",
)
BASIS_WORDS = ("interpolated", "extrapolated")
LOG_COLUMNS = ("kind", "year", "country", "group", "detail")

MAIN_OUTPUT = Path("data") / "streams" / "wind_solar.csv.gz"
PRE1950_OUTPUT = Path("data") / "streams_pre1950" / "wind_solar.csv.gz"
LOG_OUTPUT = Path("research") / "wind_solar" / "build_log.csv"
REGISTRY = Path("data") / "reference" / "commodity_factors.csv"

# (substream, capacity series, drivetrain or utility share series, complement of the share?)
CLASSES: dict[str, tuple[str, str, str, bool]] = {
    "wind_on_nopm": ("wind", "cap_add_wind_onshore", "wind_pm_share_onshore", True),
    "wind_on_pm": ("wind", "cap_add_wind_onshore", "wind_pm_share_onshore", False),
    "wind_off_nopm": ("wind", "cap_add_wind_offshore", "wind_pm_share_offshore", True),
    "wind_off_pm": ("wind", "cap_add_wind_offshore", "wind_pm_share_offshore", False),
    "pv_utility": ("solar", "cap_add_solar_pv", "pv_utility_share", False),
    "pv_rooftop": ("solar", "cap_add_solar_pv", "pv_utility_share", True),
}
CAPACITY_SERIES = frozenset(
    {"cap_add_wind_onshore", "cap_add_wind_offshore", "cap_add_solar_pv", "cap_add_solar_csp"}
)
CSP_SERIES = "cap_add_solar_csp"  # capacity without intensity: logged no_intensity (spec 7.3)

# Commodity code on the notes (spec 3.6) and the world production series of the sigma check (4.3).
FAMILY_CODE = {
    "copper": "CU",
    "ree_oxide": "RE",
    "steel": "ST",
    "cast_iron": "CI",
    "aluminium": "AL",
    "cement": "CE",
    "zinc": "ZN",
    "silver": "AG",
    "tin": "SN",
    "tio2_pigment": "TI",
    "silicon_mg": "SI",
    "glass": "GL",
    "glass_fibre": "GF",
}
WORLD_SERIES = {
    "copper": "prod_copper",
    "aluminium": "prod_aluminium",
    "steel": "prod_steel",
    "ree_oxide": "prod_ree_oxide",
    "silver": "prod_silver",
    "zinc": "prod_zinc",
    "tin": "prod_tin",
    "cement": "prod_cement",
}
PROD_COPPER, PROD_COPPER_OD = "prod_copper", "prod_copper_od"
OD_SHARE = "od_value_share_u"
BF_SERIES = "steel_bf_route_share"
CHARGE_SERIES = "ree_charge_factor"
CHARGE_BOUND_MAIN, CHARGE_BOUND_RADIO = 1.0, 5.9  # spec 6.2 rule constants

# Families (commodity, ore_type, region), spec 2.3. Fixed here, not discovered from the registry: an
# extra registry row with another ore type must not become a family (LIB_SPEC 12 exact equality).
# The (group, tier, route, residue) combinations of each family are read from the registry.
FAMILIES: dict[str, tuple[tuple[str, str], ...]] = {
    "copper": (
        ("porphyry_stratiform", "XWL"),
        ("iocg_olympic_dam", "AUS"),
        ("iocg_high_u", "AUS"),
        ("cu_co_stratiform", "COD"),
        ("all", "XWL"),
    ),
    "ree_oxide": (
        ("ree_bayan_obo", "CHN"),
        ("ree_ionic_clay", "CHN"),
        ("ree_monazite", "XWL"),
        ("ree_mt_weld", "MYS"),
    ),
}
COPPER_CLASS_SERIES = {
    "porphyry_stratiform": "cu_class_share_porphyry_stratiform",
    "iocg_high_u": "cu_class_share_iocg_high_u",
    "cu_co_stratiform": "cu_class_share_cu_co_stratiform",
}
# Joint families (spec 6.1): (commodity, ore_type) -> (D6 series or "OD", series country,
# share under bound_main, share under bound_radio).
JOINT: dict[tuple[str, str], tuple[str, str, float, float]] = {
    ("copper", "porphyry_stratiform"): ("d6_value_share_copper_porphyry", "XWL", 1.0, 0.0),
    ("copper", "all"): ("d6_value_share_copper_porphyry", "XWL", 1.0, 0.0),
    ("copper", "iocg_high_u"): ("d6_value_share_copper_iocg_ph_cp", "AUS", 1.0, 0.0),
    ("copper", "cu_co_stratiform"): ("d6_value_share_copper_cu_co", "COD", 1.0, 0.0),
    ("copper", "iocg_olympic_dam"): ("OD", "AUS", 1.0, 0.0),
    ("ree_oxide", "ree_bayan_obo"): ("d6_value_share_ree_bayan_obo", "CHN", 0.0, 1.0),
    ("ree_oxide", "ree_monazite"): ("d6_value_share_ree_monazite", "XWL", 0.0, 1.0),
    ("zinc", ""): ("d6_value_share_zinc", "XWL", 1.0, 0.0),
    ("silver", ""): ("d6_value_share_silver", "XWL", 0.0, 1.0),
}

ACTIVITY_FILES = (
    "capacity_additions.csv",
    "material_intensity.csv",
    "wind_solar_shares.csv",
    "commodity_production.csv",
)
PRODUCTION_SERIES = frozenset({*WORLD_SERIES.values(), PROD_COPPER_OD})


@dataclass(frozen=True)
class BuildResult:
    rows: list[dict]
    rows_pre1950: list[dict]
    log: list[dict]


# --------------------------------------------------------------------------------------
# terms: bounds plus the causes of their below-detection flag (spec 3.3)
# --------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Term:
    b: Bounds
    causes: tuple[str, ...] = ()


def _ordered(causes: Iterable[str]) -> tuple[str, ...]:
    have = set(causes)
    return tuple(c for c in CAUSE_ORDER if c in have)


def _floor_fired(terms: Sequence[Term]) -> bool:
    """Whether the lib's floor-dominance rule zeroed the low bound of a product (LIB_SPEC 8.1)."""
    total = floored = 0.0
    for t in terms:
        if t.b.low > 0:
            total += (math.log(t.b.central) - math.log(t.b.low)) ** 2
        else:
            part = math.log(1.0 / FLOOR_FRACTION) ** 2
            total += part
            floored += part
    return floored > 0 and floored > total / 2


def _product_causes(terms: Sequence[Term], b: Bounds) -> tuple[str, ...]:
    if not b.nd_floored:
        return ()
    inherited = _ordered(c for t in terms for c in t.causes)
    if inherited:
        return inherited
    if any(t.b.high == 0 for t in terms):
        return ("inherited_flag",)
    if any(t.b.central == 0 for t in terms):
        return ("zero_central_factor",)
    return ("floor_dominance",) if _floor_fired(terms) else ("inherited_flag",)


def _tproduct(*terms: Term) -> Term:
    b = product(*(t.b for t in terms))
    return Term(b, _product_causes(terms, b))


def _tapply(driver: Term, unit: str, factor: Mapping[str, Any]) -> Term:
    """``apply`` (unit check included) with the cause bookkeeping of ``_product_causes``."""
    b = apply(driver.b, unit, factor)
    f = Term(_factor_bounds(factor))
    return Term(b, _product_causes((driver, f), b))


def _tsum(terms: Sequence[Term]) -> Term:
    """Fully correlated sum of class contributions (spec 3.2)."""
    b = sum_correlated(t.b for t in terms)
    if not b.nd_floored:
        return Term(b)
    return Term(b, _ordered(c for t in terms for c in t.causes) or ("inherited_flag",))


def _tsplit(a: Term, share: float) -> Term:
    """D6 split with an exact share; exactly 0 is a structural zero, never flagged (spec 3.4)."""
    if share == 0.0:
        return Term(Bounds.exact(0.0))
    out = split(a.b, {"x": share})["x"]
    return Term(out, a.causes if out.nd_floored else ())


def _factor_bounds(row: Mapping[str, Any]) -> Bounds:
    low = row["value_low"]
    return Bounds(
        low,
        row["value_central"],
        row["value_high"],
        nd_floored=bool(row.get("below_detection")) and low == 0,
    )


# --------------------------------------------------------------------------------------
# activity rows
# --------------------------------------------------------------------------------------
class Act:
    """One activity row. Identity-hashed so that sets of rows can name what a contribution used."""

    __slots__ = ("b", "basis", "country", "kind", "placeholder", "series", "sources", "unit", "year")

    def __init__(self, r: Mapping[str, Any], kind: str) -> None:
        low = r["value_low"]
        self.series: str = r["series"]
        self.country: str = WORLD_ROW if r["country"] == WORLD_ACTIVITY else r["country"]
        self.year: int = r["year"]
        self.b = Bounds(
            low,
            r["value_central"],
            r["value_high"],
            nd_floored=bool(r.get("below_detection")) and low == 0,
        )
        self.unit: str = r["unit"]
        self.basis: str = r.get("basis") or ""
        self.sources: tuple[str, ...] = tuple(r.get("source_ids") or ())
        # Placeholders are data: only the PLACEHOLDER prefix marks them (spec 13.5).
        self.placeholder: bool = (r.get("notes") or "").startswith("PLACEHOLDER")
        self.kind = kind

    @property
    def term(self) -> Term:
        return Term(self.b)


def _kind(series: str) -> str:
    if series in CAPACITY_SERIES:
        return "cap"
    if series.startswith("mi_"):
        return "mi"
    if series in PRODUCTION_SERIES:
        return "prod"
    return "share"


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


@dataclass
class _Part:
    """One class contribution to one master key and variant, before the §3.2 merge."""

    term: Term
    factor_id: str
    order: int  # registry file position: the order of ``factor_ids``
    factor_sources: tuple[str, ...]
    acts: frozenset  # the activity rows behind the contribution
    ore: str
    joint: bool


@dataclass(frozen=True)
class _Contribution:
    year: int
    substream: str
    commodity: str
    cls: str
    mass: Term  # M_{k,c} in t
    acts: frozenset


# --------------------------------------------------------------------------------------
# builder
# --------------------------------------------------------------------------------------
class _Builder:
    def __init__(self, root: Path) -> None:
        self.registry = self._load_registry(root / REGISTRY)
        self.by_commodity: dict[str, list[dict]] = defaultdict(list)
        for f in self.registry:
            self.by_commodity[f["commodity"]].append(f)
        self.act: dict[tuple[str, str], dict[int, Act]] = {}
        self._load_activity(root / "data" / "activity")
        # first year of every (series, country): a missing year before it is silent (spec 13.13)
        self.first = {key: min(by_year) for key, by_year in self.act.items()}

        self.parts: dict[tuple, list[_Part]] = defaultdict(list)
        self.no_driver: dict[tuple[str, str], set[int]] = defaultdict(set)
        self.no_factor: dict[tuple[str, str, str], set[int]] = defaultdict(set)
        self.no_intensity: dict[str, set[int]] = defaultdict(set)
        self.sigma: dict[tuple[str, int], float] = {}
        self._select_cache: dict[tuple, Any] = {}
        self._combo_cache: dict[tuple, list[tuple[str, str, str, str]]] = {}

        # class -> commodities with an intensity series (series name mi_<class>_<commodity>)
        self.class_commodities: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for series in sorted(s for (s, _c) in self.act if s.startswith("mi_")):
            for k in sorted(CLASSES, key=len, reverse=True):
                prefix = f"mi_{k}_"
                if series.startswith(prefix):
                    self.class_commodities[k].append((series[len(prefix) :], series))
                    break

    # ---- loading -----------------------------------------------------------------------
    @staticmethod
    def _load_registry(path: Path) -> list[dict]:
        if not path.is_file():
            return []
        rows = read_table(path)
        for n, f in enumerate(rows):
            for col in ("group", "tier", "route", "residue_type", "ore_type", "region"):
                if f.get(col) is None:
                    f[col] = ""
            f["_order"] = n
            f["source_ids"] = list(f.get("source_ids") or [])
        return rows

    def _load_activity(self, folder: Path) -> None:
        for name in ACTIVITY_FILES:
            path = folder / name
            if not path.is_file():
                continue
            for r in read_table(path):
                series, country = r["series"], r["country"]
                if name == "capacity_additions.csv":
                    # The file note says "sum countries or use XWL, not both" (spec 2.1 group C).
                    if series not in CAPACITY_SERIES or country != WORLD_ACTIVITY:
                        continue
                elif name == "commodity_production.csv":
                    if series not in PRODUCTION_SERIES:
                        continue
                elif name == "material_intensity.csv" and not series.startswith("mi_"):
                    continue
                by_year = self.act.setdefault((series, country), {})
                if r["year"] in by_year:
                    raise LibError(
                        f"duplicate activity row: series {series!r}, country {country!r}, "
                        f"year {r['year']}"
                    )
                by_year[r["year"]] = Act(r, _kind(series))

    # ---- plumbing ----------------------------------------------------------------------
    def get(self, series: str, year: int, country: str = WORLD_ACTIVITY) -> Act | None:
        """The activity row, or ``None`` with ``no_driver`` noted when it is a gap in its span."""
        row = self.act.get((series, country), {}).get(year)
        if row is None:
            first = self.first.get((series, country))
            if first is None or year >= first:
                self.no_driver[(series, country)].add(year)
        return row

    @staticmethod
    def share_term(row: Act, *, charge: bool = False) -> Term:
        if row.unit != "1":
            raise LibError(f"share series {row.series!r} {row.year}: unit {row.unit!r}, expected '1'")
        if row.b.high > 1.0 + SHARE_TOL and not charge:
            raise LibError(
                f"share series {row.series!r} {row.year}: high {row.b.high!r} is above 1"
            )
        return row.term

    @staticmethod
    def complement(row: Act) -> Term:
        """$1-s$, anti-correlated with $s$ (spec 3.4)."""
        s = _Builder.share_term(row).b
        return Term(Bounds(1.0 - s.high, 1.0 - s.central, 1.0 - s.low))

    def combos(self, commodity: str, ore: str, region: str) -> list[tuple[str, str, str, str]]:
        key = (commodity, ore, region)
        hit = self._combo_cache.get(key)
        if hit is None:
            seen: dict[tuple[str, str, str, str], None] = {}
            for f in self.by_commodity.get(commodity, []):
                if f["ore_type"] == ore and f["region"] == region:
                    seen.setdefault((f["group"], f["tier"], f["route"], f["residue_type"]))
            hit = self._combo_cache[key] = list(seen)
        return hit

    def factor(
        self, year: int, commodity: str, ore: str, region: str, combo: tuple[str, str, str, str]
    ) -> dict | None:
        """The registry row, ``None`` for ``no factor row``; ambiguity and other errors propagate."""
        key = (year, commodity, ore, region, combo)
        if key in self._select_cache:
            hit = self._select_cache[key]
        else:
            g, t, rt, rs = combo
            try:
                hit = select(
                    self.by_commodity.get(commodity, []),
                    year=year,
                    region=region,
                    commodity=commodity,
                    component="own_residue",
                    ore_type=ore,
                    group=g,
                    tier=t,
                    route=rt,
                    residue_type=rs,
                    allocation_variant="default",
                )
            except LibError as exc:
                if not str(exc).startswith("no factor row"):
                    raise
                hit = None
            self._select_cache[key] = hit
        return hit

    # ---- the walk ----------------------------------------------------------------------
    def run(self) -> None:
        for year in range(FIRST_YEAR_MAIN, LAST_YEAR + 1):
            contributions = self.year_contributions(year)
            self.attribution(year, contributions)
            for c in contributions:
                if c.mass.b.central == 0:
                    continue  # spec 13.13: zero tonnage, no lookup, no row, no log
                for ore, region in FAMILIES.get(c.commodity, (("", WORLD_ACTIVITY),)):
                    self.family(c, ore, region)

    def year_contributions(self, year: int) -> list[_Contribution]:
        """Steps 1 and 2 of spec 4.2: $C_k$ in GW and $M_{k,c}$ in t, for every class and commodity."""
        out: list[_Contribution] = []
        if year in self.act.get((CSP_SERIES, WORLD_ACTIVITY), {}):
            self.no_intensity[CSP_SERIES].add(year)
        for k, (sub, cap_series, share_series, complement) in CLASSES.items():
            cap = self.get(cap_series, year)
            if cap is None:
                continue
            share = self.get(share_series, year)
            if share is None:
                continue
            if cap.unit != "GW":
                raise LibError(f"{cap_series!r} {year}: unit {cap.unit!r}, expected 'GW'")
            pi = self.complement(share) if complement else self.share_term(share)
            capacity_k = _tproduct(cap.term, pi)  # C_k
            for commodity, series in self.class_commodities.get(k, []):
                intensity = self.get(series, year)
                if intensity is None:
                    continue
                if intensity.unit != "t/GW":
                    raise LibError(f"{series!r} {year}: unit {intensity.unit!r}, expected 't/GW'")
                mass = _tproduct(capacity_k, intensity.term)  # M_{k,c}
                out.append(
                    _Contribution(year, sub, commodity, k, mass, frozenset({cap, share, intensity}))
                )
        return out

    def attribution(self, year: int, contributions: Sequence[_Contribution]) -> None:
        """Spec 4.3: $\\sigma_c\\le1$ at central, else ``LibError``; the value goes to the log."""
        for commodity, series in WORLD_SERIES.items():
            mine = [c for c in contributions if c.commodity == commodity]
            if not mine:
                continue
            world = self.act.get((series, WORLD_ACTIVITY), {}).get(year)
            if world is None or sum(c.mass.b.central for c in mine) <= 0:
                continue
            # Class keys are unique across the two substreams, so one call covers the commodity.
            cap = {c.cls: c.mass.b.central for c in mine}
            sigma = attribution_share(cap, {c.cls: 1.0 for c in mine}, world.b.central)
            self.sigma[(commodity, year)] = sigma

    # ---- one class contribution to one family (spec 4.2 steps 3-5) ------------------------
    def family(self, c: _Contribution, ore: str, region: str) -> None:
        year, commodity = c.year, c.commodity
        acts = set(c.acts)
        tonnage_scalar = 1.0  # copper class share, or the OD share
        route_scalar = charge_default = 0.0
        steel_share: Term | None = None
        if commodity == "copper" and ore == "iocg_olympic_dam":
            od = self.get(PROD_COPPER_OD, year, "AUS")
            if od is None:
                return
            world = self.get(PROD_COPPER, year)
            if world is None:
                return
            acts |= {od, world}
            tonnage_scalar = od.b.central / world.b.central
        elif commodity == "copper" and ore in COPPER_CLASS_SERIES:
            row = self.get(COPPER_CLASS_SERIES[ore], year)
            if row is None:
                return
            self.share_term(row)
            acts.add(row)
            tonnage_scalar = row.b.central
        elif commodity == "ree_oxide":
            route = self.get(f"ree_route_share_{ore[len('ree_') :]}", year)
            charge = self.get(CHARGE_SERIES, year)
            if route is None or charge is None:
                return
            self.share_term(route)
            self.share_term(charge, charge=True)
            acts |= {route, charge}
            route_scalar, charge_default = route.b.central, charge.b.central
        elif commodity == "steel":
            row = self.get(BF_SERIES, year)
            if row is None:
                return
            steel_share = self.share_term(row)
            acts.add(row)

        joint = JOINT.get((commodity, ore))
        d6: dict[str, float] | None = None
        if joint is not None:
            series, country, main, radio = joint
            if series == "OD":
                w = self.get(OD_SHARE, year, "AUS")
                if w is None:
                    return
                self.share_term(w)
                default = 1.0 - w.b.central  # copper ledger of the OD pool (spec 6.3)
            else:
                w = self.get(series, year, country)
                if w is None:
                    return
                self.share_term(w)
                default = w.b.central
            acts.add(w)
            d6 = {"default": default, "bound_main": main, "bound_radio": radio}

        frozen = frozenset(acts)
        out_country = WORLD_ROW if region == WORLD_ACTIVITY else region
        for variant in VARIANTS if joint else ("default",):
            # Step 3: the family's one tonnage share, as an exact scalar (spec 13.19).
            if commodity == "ree_oxide":
                charge_v = {
                    "default": charge_default,
                    "bound_main": CHARGE_BOUND_MAIN,
                    "bound_radio": CHARGE_BOUND_RADIO,
                }[variant]
                tonnes = _tproduct(c.mass, Term(Bounds.exact(route_scalar * charge_v)))
            elif commodity == "steel":
                assert steel_share is not None
                tonnes = _tproduct(c.mass, steel_share)
            elif commodity == "copper" and ore != "all":
                tonnes = _tproduct(c.mass, Term(Bounds.exact(tonnage_scalar)))
            else:
                tonnes = c.mass
            if tonnes.b.central == 0:
                continue
            share = d6[variant] if d6 is not None else None
            for combo in self.combos(commodity, ore, region):
                g, t, rt, rs = combo
                f = self.factor(year, commodity, ore, region, combo)
                if f is None:
                    detail = f"{commodity}/{ore or '-'}/{t}/{rs or rt}"
                    self.no_factor[(out_country, g, detail)].add(year)
                    continue
                if share == 0.0:
                    a = Term(Bounds.exact(0.0))  # structural zero: nothing to multiply
                else:
                    a = _tapply(tonnes, "t", f)  # step 4
                    if share is not None:
                        a = _tsplit(a, share)  # step 5
                key = (year, c.substream, commodity, rs, out_country, g, t, rt, variant)
                self.parts[key].append(
                    _Part(
                        a,
                        f["factor_id"],
                        f["_order"],
                        tuple(f["source_ids"]),
                        frozen,
                        ore,
                        joint is not None,
                    )
                )

    # ---- rows -----------------------------------------------------------------------------
    def rows(self) -> tuple[list[dict], dict[str, set[int]]]:
        """Step 6 (sum over classes and ore types per master key) and the master rows."""
        out: list[dict] = []
        placeholder_years: dict[tuple[str, str], set[int]] = defaultdict(set)
        for key in sorted(self.parts):
            year, sub, commodity, rs, country, g, t, rt, variant = key
            parts = sorted(self.parts[key], key=lambda p: p.order)
            total = _tsum([p.term for p in parts])
            factor_ids: list[str] = []
            ores: list[str] = []
            sources: set[str] = set()
            words: set[str] = set()
            share_placeholder = alloc_placeholder = False
            for p in parts:
                if p.factor_id not in factor_ids:
                    factor_ids.append(p.factor_id)
                if p.ore not in ores:
                    ores.append(p.ore)
                sources.update(p.factor_sources)
                for a in p.acts:
                    sources.update(a.sources)
                    if a.kind in ("cap", "mi") and a.basis in BASIS_WORDS:
                        words.add(a.basis)
                    if a.kind == "share" and a.placeholder:
                        share_placeholder = True
                        placeholder_years[(a.series, a.country)].add(year)
                        if p.joint and variant == "default" and self._is_d6(a.series):
                            alloc_placeholder = True
            joint = parts[0].joint
            notes = self.note_head(commodity, ores, variant if joint else None)
            driver = "+".join(w for w in BASIS_WORDS if w in words)
            if driver:
                notes += f"; driver basis: {driver}"
            if share_placeholder:
                notes += "; share basis: placeholder"
            if alloc_placeholder:
                notes += "; allocation basis: placeholder"
            if total.b.nd_floored:
                causes = total.causes or ("inherited_flag",)
                notes += "; below_detection cause: " + "+".join(causes)
            out.append(
                make_row(
                    bounds=total.b,
                    year=year,
                    stream=STREAM,
                    substream=sub,
                    stage="commodity_supply",
                    product=commodity,
                    residue_type=rs or None,
                    country=country,
                    group=g,
                    tier=t,
                    quantity="flow",
                    unit=master_unit("Bq", "flow"),
                    basis="modelled",
                    allocation_variant=variant,
                    allocation_rule=variant_token(variant) if joint else "none",
                    embedded_fuel=False,
                    technology=sub,
                    route=rt or None,
                    factor_ids=factor_ids,
                    source_ids=sorted(sources),
                    notes=notes,
                )
            )
        return out, placeholder_years

    @staticmethod
    def _is_d6(series: str) -> bool:
        return series.startswith("d6_value_share_") or series == OD_SHARE

    @staticmethod
    def note_head(commodity: str, ores: Sequence[str], variant: str | None) -> str:
        code = FAMILY_CODE.get(commodity, commodity.upper())
        named = ", ".join(o for o in ores if o)
        if commodity == "copper" and ores == ["all"]:
            text = "smelter and refinery residue (ore type all)"
        elif named:
            text = f"{named} own-residue footprint"
        else:
            text = f"{commodity} own-residue footprint"
        head = f"{code}: {text}"
        if variant is not None:
            head += f"; D6 {variant}, commodity {commodity}"
        return head

    # ---- log --------------------------------------------------------------------------------
    def log_entries(
        self, placeholder_years: dict[tuple[str, str], set[int]], lib_warnings: Counter[str]
    ) -> list[dict]:
        log: list[dict] = []

        def entry(kind: str, year: Any, country: str, group: str, detail: str) -> None:
            log.append(
                {"kind": kind, "year": year, "country": country, "group": group, "detail": detail}
            )

        def shown(country: str) -> str:
            return WORLD_ROW if country == WORLD_ACTIVITY else country

        for (country, group, detail), years in sorted(self.no_factor.items()):
            for a, b in _runs(years):
                entry("no_factor", a, country, group, f"{detail}: {_run_text(a, b)}")
        for (series, country), years in sorted(self.no_driver.items()):
            for a, b in _runs(years):
                entry("no_driver", a, shown(country), "", f"{series}: {_run_text(a, b)}")
        for series, years in sorted(self.no_intensity.items()):
            for a, b in _runs(years):
                entry("no_intensity", a, WORLD_ROW, "", f"{series}: {_run_text(a, b)}")

        present = {f["commodity"] for f in self.registry}
        seen: set[str] = set()
        for k in sorted(self.class_commodities):
            for commodity, series in self.class_commodities[k]:
                if commodity not in present and commodity not in seen:
                    seen.add(commodity)
                    entry("no_footprint", "", "", "", f"{commodity} ({series})")
        for commodity in FAMILY_CODE:
            if commodity not in present:
                continue
            for ore, region in FAMILIES.get(commodity, (("", WORLD_ACTIVITY),)):
                if not self.combos(commodity, ore, region):
                    entry(
                        "no_family",
                        "",
                        "",
                        "",
                        f"{commodity}/{ore or '-'}/{region}: the registry has no rows",
                    )

        for (series, country), years in sorted(placeholder_years.items()):
            for a, b in _runs(years):
                entry("placeholder_share", a, country, "", f"{series}: {_run_text(a, b)}")

        decade_max: dict[tuple[str, int], tuple[float, int]] = {}
        for (commodity, year), sigma in sorted(self.sigma.items()):
            key = (commodity, year // 10 * 10)
            if key not in decade_max or sigma > decade_max[key][0]:
                decade_max[key] = (sigma, year)
        for (commodity, decade), (sigma, year) in sorted(decade_max.items()):
            entry("attribution", decade, WORLD_ROW, "", f"{commodity}: max sigma {sigma:.4g} in {year}")

        if lib_warnings:
            total = sum(lib_warnings.values())
            kinds = "; ".join(f"{n} x {name}" for name, n in sorted(lib_warnings.items()))
            entry("lib_warning", "", "", "", f"{total} pipeline.lib warnings captured: {kinds}")
        return log


def build(root: Path | str) -> BuildResult:
    """Build the wind and solar master rows for 1950-2025, the (empty) pre-1950 rows and the log.

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
        rows, placeholder_years = b.rows()
    finally:
        lib_logger.removeHandler(handler)
        lib_logger.propagate, level = saved
        lib_logger.setLevel(level)
    log = b.log_entries(placeholder_years, handler.counts)
    return BuildResult(rows=rows, rows_pre1950=[], log=log)


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
        prog="python -m pipeline.streams.wind_solar", description=__doc__
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="repository root (default: the checkout containing this file)",
    )
    parser.add_argument("--write", action="store_true", help="overwrite the committed outputs")
    args = parser.parse_args(argv)
    root: Path = args.root

    if not args.write:
        # Ambiguity is decidable before the (slow) build.
        early = diff_mode_preflight(root, (MAIN_OUTPUT, PRE1950_OUTPUT))
        if early is not None:
            return early

    result = build(root)
    counts = Counter(e["kind"] for e in result.log)
    print(f"rows 1950-2025: {len(result.rows)}; rows 1800-1949: {len(result.rows_pre1950)}")
    for kind in LOG_KINDS:
        print(f"log {kind}: {counts.get(kind, 0)}")

    targets = ((MAIN_OUTPUT, result.rows), (PRE1950_OUTPUT, result.rows_pre1950))
    return finish(root, targets, result.log, LOG_OUTPUT, write_log, args.write)


if __name__ == "__main__":
    raise SystemExit(main())
