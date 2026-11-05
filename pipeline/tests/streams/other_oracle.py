"""Independent arithmetic oracle for the `other` stream tests (Task 2.5).

Written from docs/OTHER_SPEC.md (v1.0 FINAL), docs/LIB_SPEC.md (v1.4), docs/COAL_SPEC.md and
docs/NUCLEAR_SPEC.md conventions only. It does NOT import pipeline.lib or pipeline.streams: the bounds
arithmetic (log-space quadrature product with the 1e-3 floor, independent and correlated sums,
independent and correlated differences, cap, complement) is re-implemented here with the standard
library, and the data are read with pandas straight from the CSV files. Nothing numeric from the
registry or the activity files is hard-coded; every value is read from the tree it is given.

``Oracle(root).expected()`` returns an ``Expected`` with

* ``rows`` / ``pre``   dict key -> ``ER`` for data/streams/other.csv and data/streams_pre1950/other.csv,
* ``log``              dict kind -> list of expectation tuples (see ``Expected``),
* ``units``            wood-partition bookkeeping per (country, year),
* ``peat``             peat-chain bookkeeping per (country, year),
* ``cs``               fuel Cs-137 bookkeeping per (substream, country, year).

The key of a row is ``(year, substream, stage, country, group, tier, route, residue_type)``
(``quantity`` is always ``flow`` in this stream).

Interpretation choices where the spec is silent are marked ``# AMBIGUITY <id>`` and listed in the
header of test_other.py.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field, replace
from pathlib import Path

import pandas as pd

FLOOR = 1e-3
GWA_TWH = 8.766
TOL_REL = 1e-5  # OTHER_SPEC 3.5 rest-of-world tolerance (D68, D70 resolution 7)
CAUSE_ORDER = [
    "zero_central_factor",
    "exact_zero",
    "clipped_difference",
    "floor_dominance",
    "inherited_flag",
]
BP, DOM, GEO = "biomass_peat", "biomass_domestic", "geothermal"

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
COMP_ORDER = {
    BP: ["peat_plant", "peat_other", "wood_plant"],
    DOM: ["peat_household", "wood_household", "charcoal"],
}


# --------------------------------------------------------------------------------------------
# bounds arithmetic
# --------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class B:
    low: float
    central: float
    high: float
    nd: bool = False
    causes: tuple = ()


def _ordered(causes) -> tuple:
    s = set(causes)
    return tuple(c for c in CAUSE_ORDER if c in s)


def exact(x: float) -> B:
    return B(x, x, x)


def is_zero_b(b: B) -> bool:
    return b.low == 0 and b.central == 0 and b.high == 0


def scale(a: B, k: float) -> B:
    return B(a.low * k, a.central * k, a.high * k, a.nd, a.causes)


def comp(s: B) -> B:
    """Complement 1 - s (OTHER_SPEC 3.5): anti-correlated."""
    if s.high > 1.0:
        raise ValueError("share high above 1")
    return B(1.0 - s.high, 1.0 - s.central, 1.0 - s.low)


def prod(*terms: B) -> B:
    inc = [c for t in terms for c in t.causes]
    any_nd = any(t.nd for t in terms)
    if any(t.high == 0 for t in terms):
        causes = _ordered(inc) if any_nd else ()
        if any_nd and not causes:
            causes = ("inherited_flag",)
        return B(0.0, 0.0, 0.0, any_nd, causes)
    if any(t.central == 0 for t in terms):
        h = 1.0
        for t in terms:
            h *= t.high
        return B(
            0.0, 0.0, h, True, _ordered(inc) or ("zero_central_factor",)
        )  # D71 13.15: a carried cause is not replaced
    c = 1.0
    for t in terms:
        c *= t.central
    up = math.sqrt(sum(math.log(t.high / t.central) ** 2 for t in terms))
    total = floored = 0.0
    for t in terms:
        if t.low > 0:
            total += math.log(t.central / t.low) ** 2
        else:
            d2 = math.log(1.0 / FLOOR) ** 2
            total += d2
            floored += d2
    fired = floored > 0.5 * total
    low = 0.0 if fired else c * math.exp(-math.sqrt(total))
    nd = (low == 0.0) and (fired or any_nd)
    causes = _ordered(inc)
    if nd and not causes:
        causes = ("floor_dominance",) if fired else ("inherited_flag",)
    return B(low, c, c * math.exp(up), nd, causes if nd else ())


def sum_independent(terms: list[B]) -> B:
    if not terms:
        return exact(0.0)
    c = sum(t.central for t in terms)
    lo = c - math.sqrt(sum((t.central - t.low) ** 2 for t in terms))
    hi = c + math.sqrt(sum((t.high - t.central) ** 2 for t in terms))
    return B(max(lo, 0.0), c, hi)


def sum_correlated(terms: list[B]) -> B:
    lo = sum(t.low for t in terms)
    c = sum(t.central for t in terms)
    hi = sum(t.high for t in terms)
    nd = lo == 0.0 and any(t.nd for t in terms)
    causes = _ordered([x for t in terms for x in t.causes]) if nd else ()
    if nd and not causes:
        causes = ("inherited_flag",)
    return B(lo, c, hi, nd, causes)


def diff_indep(a: B, b: B) -> tuple[B, float]:
    """Independent difference (OTHER_SPEC 3.5). Returns (result, raw central difference)."""
    raw = a.central - b.central
    c = max(raw, 0.0)
    lo_raw = c - math.sqrt((a.central - a.low) ** 2 + (b.high - b.central) ** 2)
    hi_raw = c + math.sqrt((a.high - a.central) ** 2 + (b.central - b.low) ** 2)
    low = max(lo_raw, 0.0)
    high = max(hi_raw, c)
    clipped = lo_raw < 0 or raw < 0
    nd = clipped and low == 0.0
    return B(low, c, high, nd, ("clipped_difference",) if nd else ()), raw


def diff_corr(a: B, b: B) -> B:
    """Correlated difference (OTHER_SPEC 3.5)."""
    craw = a.central - b.central
    lraw = min(a.low - b.low, craw)
    hraw = max(a.high - b.high, craw)
    c, lo, hi = max(craw, 0.0), max(lraw, 0.0), max(hraw, 0.0)
    clipped = lraw < 0 or craw < 0
    exact_zero = craw == 0.0 and hraw == 0.0 and lraw >= 0.0
    zero_central = (
        craw == 0.0 and hraw > 0.0
    )  # D71 13.15: (0, 0, h) is flagged, cause clipped_difference
    inherited = (a.nd or b.nd) and lo == 0.0
    causes = list(a.causes) + list(b.causes) if inherited else []
    if (clipped and lo == 0.0) or zero_central:
        causes.append("clipped_difference")
    if exact_zero:
        causes.append("exact_zero")
    nd = lo == 0.0 and (clipped or exact_zero or inherited or zero_central)
    cs = _ordered(causes)
    if nd and not cs:
        cs = ("inherited_flag",)
    return B(lo, c, hi, nd, cs if nd else ())


def cap_b(x: B, cap: B) -> tuple[B, list[str]]:
    lo, c, hi = min(x.low, cap.low), min(x.central, cap.central), min(x.high, cap.high)
    changed = [
        n
        for n, (xv, cv) in (
            ("low", (x.low, cap.low)),
            ("central", (x.central, cap.central)),
            ("high", (x.high, cap.high)),
        )
        if xv > cv
    ]
    nd = lo == 0.0 and (x.nd or cap.nd)
    causes = _ordered(list(x.causes) + list(cap.causes)) if nd else ()
    if nd and not causes:
        causes = ("inherited_flag",)
    return B(lo, c, hi, nd, causes), changed


# --------------------------------------------------------------------------------------------
# terms: bounds plus provenance
# --------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Tm:
    b: B
    f: tuple = ()  # factor ids in applied order
    s: frozenset = frozenset()  # source ids of the driver rows involved
    w: frozenset = frozenset()  # driver basis words of the rows involved
    c: frozenset = frozenset()  # component tags
    fb: bool = False  # depends on the household share fallback
    z: bool = (
        False  # a zero-central, positive-high term (0, 0, h) entered the derivation
    )


ZERO = Tm(exact(0.0))


def tzero(t: Tm) -> bool:
    return is_zero_b(t.b)


def _cat(ts) -> tuple:
    out: list = []
    for t in ts:
        for x in t.f:
            if x not in out:
                out.append(x)
    return tuple(out)


def _merge(ts, b: B, extra_f=()) -> Tm:
    nz = [t for t in ts if not tzero(t)] or list(ts)
    f = _cat(nz)
    for x in extra_f:
        if x not in f:
            f = f + (x,)
    z = any(t.z or (t.b.central == 0 and t.b.high > 0) for t in nz)
    return Tm(
        b,
        f,
        frozenset().union(*[t.s for t in nz]) if nz else frozenset(),
        frozenset().union(*[t.w for t in nz]) if nz else frozenset(),
        frozenset().union(*[t.c for t in nz]) if nz else frozenset(),
        any(t.fb for t in nz),
        z,
    )


def tprod(*ts: Tm) -> Tm:
    return _merge(ts, prod(*[t.b for t in ts]))


def tsum(ts: list[Tm]) -> Tm:
    nz = [t for t in ts if not tzero(t)]
    if not nz:
        return ZERO
    return _merge(nz, sum_correlated([t.b for t in nz]))


def tcap(x: Tm, cap: Tm) -> tuple[Tm, list[str]]:
    b, ch = cap_b(x.b, cap.b)
    return _merge([x, cap], b), ch


def tdiffc(a: Tm, b: Tm) -> Tm:
    return _merge([a, b], diff_corr(a.b, b.b))


# --------------------------------------------------------------------------------------------
# expected-row containers
# --------------------------------------------------------------------------------------------
@dataclass
class ER:
    key: tuple
    tag: str
    b: B
    rule: str
    appended: list = field(
        default_factory=list
    )  # appended texts after the rule text, in order
    comps: list | None = None  # canonical-ordered tags, None: no suffix
    fids: list = field(default_factory=list)  # ordered factor ids (OTHER_SPEC 13.13)
    src: set = field(
        default_factory=set
    )  # driver source ids (13.14); factor sources are added by the test
    basis: set = field(default_factory=set)  # driver basis words
    unit: str = "Bq/a"
    country: str = ""

    @property
    def year(self):
        return self.key[0]


@dataclass
class Expected:
    rows: dict
    pre: dict
    log: dict
    units: dict
    peat: dict
    cs: dict


def key(year, substream, stage, country, group, tier, route="", residue=""):
    return (year, substream, stage, country, group, tier, route, residue)


def runs(years: list[int]) -> list[tuple[int, int]]:
    ys = sorted(set(years))
    out: list[tuple[int, int]] = []
    for y in ys:
        if out and y == out[-1][1] + 1:
            out[-1] = (out[-1][0], y)
        else:
            out.append((y, y))
    return out


# --------------------------------------------------------------------------------------------
# the oracle
# --------------------------------------------------------------------------------------------
class Oracle:
    def __init__(self, root: Path, first_year: int = 1800, last_year: int = 2025):
        self.root = Path(root)
        self.y0, self.y1 = first_year, last_year
        fac = pd.read_csv(
            self.root / "data" / "factors" / "other.csv",
            dtype=str,
            keep_default_na=False,
        )
        self.factors = fac.to_dict("records")
        self.fby = {f["factor_id"]: f for f in self.factors}
        self.idx: dict = defaultdict(list)
        for f in self.factors:
            self.idx[
                (
                    f["stage"],
                    f["group"],
                    f["tier"],
                    f["route"],
                    f["residue_type"],
                    f["driver_series"],
                )
            ].append(f)
        self.act: dict = {}
        self.by_series: dict = defaultdict(lambda: defaultdict(list))
        for name in ("electricity_generation", "biomass", "peat"):
            p = self.root / "data" / "activity" / f"{name}.csv"
            if not p.exists():
                continue
            df = pd.read_csv(p, dtype=str, keep_default_na=False)
            for r in df.to_dict("records"):
                k = (r["series"], int(r["year"]), r["country"])
                if k in self.act:
                    raise ValueError(f"oracle: duplicate activity key {k}")
                self.act[k] = r
                self.by_series[r["series"]][int(r["year"])].append(r["country"])

    # ---- activity ---------------------------------------------------------------------------
    def has(self, series, year, country) -> bool:
        return (series, year, country) in self.act

    def arow(self, series, year, country):
        return self.act[(series, year, country)]

    def ab(self, series, year, country) -> B:
        r = self.act[(series, year, country)]
        return B(
            float(r["value_low"]), float(r["value_central"]), float(r["value_high"])
        )

    def drv(self, series, year, country) -> Tm:
        r = self.act[(series, year, country)]
        return Tm(
            self.ab(series, year, country),
            (),
            frozenset(x for x in r["source_ids"].split(";") if x),
            frozenset({r["basis"]} & {"interpolated", "extrapolated"}),
        )

    def countries(self, series, year) -> list[str]:
        """Listed (non-XWL) countries with a value; CZE dropped when CSK has a value (3.7)."""
        cs = sorted(c for c in self.by_series[series].get(year, []) if c != "XWL")
        if "CSK" in cs and "CZE" in cs:
            cs.remove("CZE")
            self.pred.append((series, year))
        return cs

    # ---- factors ----------------------------------------------------------------------------
    def sel(
        self, year, region, *, stage, group="", tier="", route="", residue="", driver=""
    ) -> dict:
        pool0 = self.idx.get((stage, group, tier, route, residue, driver), [])
        cands = [
            f
            for f in pool0
            if int(f["year_from"]) <= year <= int(f["year_to"])
            and f["region"] in (region, "XWL")
        ]
        ex = [f for f in cands if f["region"] == region]
        pool = ex or cands
        if not pool:
            raise LookupError(
                f"oracle: no factor row {year} {region} {stage}/{group}/{tier}/{route}/{residue}/{driver}"
            )
        if len(pool) > 1:
            raise RuntimeError(f"oracle: ambiguous {[p['factor_id'] for p in pool]}")
        return pool[0]

    @staticmethod
    def fb(f: dict) -> B:
        return B(
            float(f["value_low"]), float(f["value_central"]), float(f["value_high"])
        )

    def F(self, f: dict, complement: bool = False) -> Tm:
        b = self.fb(f)
        return Tm(comp(b) if complement else b, (f["factor_id"],))

    def fsrc(self, ids) -> set:
        out: set = set()
        for i in ids:
            out |= {x for x in self.fby[i]["source_ids"].split(";") if x}
        return out

    # ---- whole build ------------------------------------------------------------------------------
    def expected(self) -> Expected:
        self.rows: dict = {}
        self.pre: dict = {}
        self.pred: list = []
        self.log: dict = defaultdict(list)
        self.units: dict = {}
        self.peat: dict = {}
        self.cs: dict = {}
        self.fallback_years: dict = defaultdict(list)
        self.hhcap_years: dict = defaultdict(list)
        self.chcap_years: dict = defaultdict(list)
        self.geo_groups = sorted(
            {
                f["group"]
                for f in self.factors
                if f["stage"] == "geothermal"
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
        self._geothermal()
        self._biomass()
        self._log_runs()
        return Expected(self.rows, self.pre, self.log, self.units, self.peat, self.cs)

    def _put(self, er: ER, pre: bool = False):
        tgt = self.pre if pre else self.rows
        if er.key in tgt:
            raise RuntimeError(f"oracle: duplicate expected key {er.key}")
        tgt[er.key] = er

    def _er(self, k, tag, t: Tm, rule, *, appended=(), comps=None, pre=False):
        if tzero(t):
            return None  # D71 13.15: no row with bounds exactly (0, 0, 0) is written
        er = ER(
            k,
            tag,
            t.b,
            RULE[rule],
            list(appended),
            comps,
            list(t.f),
            set(t.s),
            set(t.w),
            "Bq/a",
            k[3],
        )
        self._put(er, pre)
        return er

    # ---- rest-of-world residual ---------------------------------------------------------------------
    def residual(self, series, y, listed):
        """('zero'|'neg'|'ok', Bounds-or-magnitude). Independent difference with the 1e-5 tolerance."""
        X = self.ab(series, y, "XWL")
        S = sum_independent([self.ab(series, y, c) for c in listed])
        R, raw = diff_indep(X, S)
        if abs(raw) <= TOL_REL * X.central:
            return "zero", None
        if raw < 0:
            return "neg", -raw
        return "ok", R

    # ---- geothermal ------------------------------------------------------------------------------------
    def _geothermal(self):
        ser = "elec_gen_geothermal"
        for y in range(self.y0, self.y1 + 1):
            pre = y < 1950
            listed = self.countries(ser, y)
            units = []
            if listed:
                for c in listed:
                    G = self.drv(ser, y, c)
                    if tzero(G):
                        continue
                    units.append((c, c, G, []))
                if self.has(ser, y, "XWL"):
                    kind, R = self.residual(ser, y, listed)
                    if kind == "neg":
                        self.log["negative_residual"].append(
                            ("XXX", y, R, "TWh", "world")
                        )
                    elif kind == "ok":
                        xr = self.drv(ser, y, "XWL")
                        src = set(xr.s)
                        bw = set(xr.w)
                        for c in listed:
                            d = self.drv(ser, y, c)
                            src |= d.s
                            bw |= d.w
                        units.append(
                            (
                                "XXX",
                                "XWL",
                                Tm(R, (), frozenset(src), frozenset(bw)),
                                [TXT_REST],
                            )
                        )
            elif self.has(ser, y, "XWL"):
                G = self.drv(ser, y, "XWL")
                if not tzero(G):
                    units.append(("XXX", "XWL", G, [TXT_WORLD]))
            for out_c, region, G, app in units:
                self._geo_unit(y, out_c, region, G, app, pre)

    def _geo_unit(self, y, out_c, region, G: Tm, app, pre):
        Gw = Tm(scale(G.b, 1.0 / GWA_TWH), G.f, G.s, G.w)
        f222 = self.sel(
            y,
            region,
            stage=GEO,
            group="Rn222+",
            tier="liberated",
            route="air_vented_gas",
            driver="elec_gen_geothermal",
        )
        t222 = tprod(Gw, self.F(f222))
        self._er(
            key(y, GEO, GEO, out_c, "Rn222+", "liberated", "air_vented_gas"),
            "geo222",
            t222,
            "geo222",
            appended=app,
            pre=pre,
        )
        f220 = self.sel(
            y,
            region,
            stage=GEO,
            group="Rn220+",
            tier="liberated",
            route="air_vented_gas",
            driver="elec_gen_geothermal",
        )
        if f220["unit"] != "1":
            raise RuntimeError("oracle: Rn-220 ratio unit")
        t220 = tprod(t222, self.F(f220))
        self._er(
            key(y, GEO, GEO, out_c, "Rn220+", "liberated", "air_vented_gas"),
            "geo220",
            t220,
            "geo220",
            appended=app,
            pre=pre,
        )
        fm = self.sel(
            y,
            region,
            stage=GEO,
            group="",
            tier="impounded",
            residue="geothermal_scale",
            driver="elec_gen_geothermal",
        )
        M = tprod(Gw, self.F(fm))
        for g in self.geo_groups:
            fg = self.sel(
                y,
                region,
                stage=GEO,
                group=g,
                tier="impounded",
                residue="geothermal_scale",
            )
            self._er(
                key(y, GEO, GEO, out_c, g, "impounded", "", "geothermal_scale"),
                "geoscale",
                tprod(M, self.F(fg)),
                "geoscale",
                appended=app,
                pre=pre,
            )

    # ---- biomass: peat, wood, charcoal, fallout Cs-137 ---------------------------------------------------------------
    def _srcw(self, rows_):
        return frozenset(
            x for r in rows_ for x in r["source_ids"].split(";") if x
        ), frozenset(
            r["basis"] for r in rows_ if r["basis"] in ("interpolated", "extrapolated")
        )

    def _residual_term(self, series, y, listed):
        """('zero'|'neg'|'ok', Tm or magnitude): the XWL row and every listed country row are the drivers."""
        kind, R = self.residual(series, y, listed)
        if kind != "ok":
            return kind, R
        rws = [self.arow(series, y, "XWL")] + [self.arow(series, y, c) for c in listed]
        s, w = self._srcw(rws)
        return kind, Tm(R, (), s, w)

    def _biomass(self):
        peat_series = ("peat_power_heat_t", "peat_household_t", "peat_supply_t")
        for y in range(1950, self.y1 + 1):
            pc = set()
            for s in peat_series:
                pc |= set(self.countries(s, y))
            wl = self.countries("wood_fuel_t", y)
            wood_units: dict = {}
            for c in wl:
                W = self.drv("wood_fuel_t", y, c)
                if not tzero(W):
                    wood_units[c] = (c, W)
            Cres = None
            if self.has("wood_fuel_t", y, "XWL"):
                kw, R = self._residual_term("wood_fuel_t", y, wl)
                if kw == "neg":
                    self.log["negative_residual"].append(("XXX", y, R, "t", "world"))
                elif kw == "ok":
                    wood_units["XXX"] = ("XWL", R)
                    if self.has("charcoal_production_t", y, "XWL"):
                        cl = self.countries("charcoal_production_t", y)
                        kc, Rc = self._residual_term("charcoal_production_t", y, cl)
                        if kc == "neg":
                            self.log["negative_residual"].append(
                                ("XXX", y, Rc, "t", "world")
                            )
                        elif kc == "ok":
                            Cres = Rc
            for c in sorted(set(pc) | set(wood_units)):
                peat = self._peat(y, c) if c in pc else None
                wu = (
                    self._wood_unit(y, c, wood_units[c], Cres if c == "XXX" else None)
                    if c in wood_units
                    else None
                )
                self._cs_rows(y, c, peat, wu)

    # ---- peat -----------------------------------------------------------------------------------------
    def _peat(self, y, c):
        def get(s):
            return self.drv(s, y, c) if (s, y, c) in self.act else None

        Tpl, Thh, Ts = (
            get("peat_power_heat_t"),
            get("peat_household_t"),
            get("peat_supply_t"),
        )
        allp = [t for t in (Tpl, Thh, Ts) if t is not None]
        if all(tzero(t) for t in allp):
            return None
        allsrc = frozenset().union(*[t.s for t in allp])
        allw = frozenset().union(*[t.w for t in allp])
        Ppl = Tpl if Tpl is not None else ZERO
        Phh = Thh if Thh is not None else ZERO
        Poth = ZERO
        if Ts is None:
            self.log["no_driver_supply"].append((c, y))
        else:
            sub = sum_independent([t.b for t in (Ppl, Phh) if not tzero(t)])
            R, raw = diff_indep(Ts.b, sub)
            if abs(raw) <= TOL_REL * Ts.b.central:
                Poth = ZERO
            else:
                if raw < 0:
                    self.log["negative_residual"].append((c, y, -raw, "t", "peat"))
                # the clipped residual (0, 0, h) is a contributing plant-type term (D71, 13.15)
                Poth = Tm(R, (), allsrc, allw, frozenset({"peat_other"}))
        if not tzero(Ppl):
            Ppl = Tm(Ppl.b, (), Ppl.s, Ppl.w, frozenset({"peat_plant"}))
        info: dict = {}
        f_d_pl = self.sel(y, "XWL", stage=BP, driver="peat_power_heat_t")
        f_d_oth = self.sel(y, "XWL", stage=BP, driver="peat_supply_t")
        Dpl = tprod(Ppl, self.F(f_d_pl)) if not tzero(Ppl) else ZERO
        Doth = tprod(Poth, self.F(f_d_oth)) if not tzero(Poth) else ZERO
        D = tsum([Dpl, Doth])
        pl_out = None
        if not tzero(D):
            f_ash = self.sel(y, "XWL", stage=BP, residue="peat_ash")
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
            A = tprod(D, self.F(f_ash))
            tags = [t for t in COMP_ORDER[BP] if t in A.c]
            ag, sg = {}, {}
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
                Ag = tprod(A, self.F(f_a))
                Sg, capped = tcap(
                    tprod(Ag, self.F(f_p), self.F(f_e)), tprod(Ag, self.F(f_fly))
                )
                if capped:
                    self.log["cap_applied"].append((c, y, g, capped, "plant"))
                Rg = tdiffc(Ag, Sg)
                ag[g], sg[g] = Ag, Sg
                self._er(
                    key(y, BP, BP, c, g, "liberated", "air_stack"),
                    "pstack",
                    Sg,
                    "pstack",
                    comps=tags,
                )
                self._er(
                    key(y, BP, BP, c, g, "impounded", "", "peat_ash"),
                    "pash",
                    tprod(Rg, self.F(f_imp)),
                    "pash",
                    comps=tags,
                )
                self._er(
                    key(y, BP, BP, c, g, "dispersed", "", "peat_ash"),
                    "pash",
                    tprod(Rg, self.F(f_dis)),
                    "pash",
                    comps=tags,
                )
            pl_out = {"D": D, "A": A, "Ag": ag, "Sg": sg}
        info["plant"] = pl_out
        hh_out = None
        if not tzero(Phh):
            f_d = self.sel(y, "XWL", stage=BP, driver="peat_household_t")
            f_ash = self.sel(y, "XWL", stage=BP, residue="peat_ash")
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
            Phh2 = Tm(Phh.b, (), Phh.s, Phh.w, frozenset({"peat_household"}))
            Ah = tprod(tprod(Phh2, self.F(f_d)), self.F(f_ash))
            hg, mg = {}, {}
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
                Hg = tprod(Ah, self.F(f_a))
                Mg, capped = tcap(tprod(Hg, self.F(f_s), self.F(f_e)), Hg)
                if capped:
                    self.log["cap_applied"].append((c, y, g, capped, "household"))
                Rg = tdiffc(Hg, Mg)
                hg[g], mg[g] = Hg, Mg
                self._er(
                    key(y, DOM, BP, c, g, "liberated", "air_stack"),
                    "hstack",
                    Mg,
                    "hstack",
                )
                self._er(
                    key(y, DOM, BP, c, g, "impounded", "", "peat_ash"),
                    "hash",
                    tprod(Rg, self.F(f_imp)),
                    "hash",
                )
                self._er(
                    key(y, DOM, BP, c, g, "dispersed", "", "peat_ash"),
                    "hash",
                    tprod(Rg, self.F(f_dis)),
                    "hash",
                )
            hh_out = {"A": Ah, "Hg": hg, "Mg": mg}
        info["hh"] = hh_out
        self.peat[(c, y)] = {"Ppl": Ppl.b, "Poth": Poth.b, "Phh": Phh.b}
        return info

    # ---- wood -----------------------------------------------------------------------------------------------
    def _wood_unit(self, y, c, wood, Cres):
        region, W = wood
        xxx = c == "XXX"
        d = self.sel(y, region, stage=BP, driver="wood_fuel_t")
        rho = self.sel(y, region, stage=BP, driver="household_fuelwood_m3")
        sh = self.sel(y, region, stage=BP, driver="wood_fuel_m3")
        kk = self.sel(y, region, stage=BP, driver="charcoal_production_t")
        if xxx:
            Ct = Cres if Cres is not None else ZERO
            mrow = None
        else:
            Ct = (
                self.drv("charcoal_production_t", y, c)
                if self.has("charcoal_production_t", y, c)
                else ZERO
            )
            mrow = (
                self.drv("household_fuelwood_m3", y, c)
                if self.has("household_fuelwood_m3", y, c)
                else None
            )
        cnz = not tzero(Ct)
        id48, id49, id50, id51 = (
            d["factor_id"],
            rho["factor_id"],
            sh["factor_id"],
            kk["factor_id"],
        )
        base_f = (id48,) + ((id51,) if cnz else ())
        base_s = frozenset(W.s) | (frozenset(Ct.s) if cnz else frozenset())
        base_w = frozenset(W.w) | (frozenset(Ct.w) if cnz else frozenset())
        Dtot = tprod(W, self.F(d))
        if cnz:
            Dch, capc = tcap(tprod(Ct, self.F(kk)), Dtot)
            Dch = replace(
                Dch,
                f=(id48, id51),
                s=frozenset(W.s) | frozenset(Ct.s),
                w=frozenset(W.w) | frozenset(Ct.w),
                c=frozenset({"charcoal"}),
            )
        else:
            Dch, capc = ZERO, []
        if capc:
            self.chcap_years[c].append(y)
        R1 = tdiffc(Dtot, Dch)
        fallback = mrow is None
        caph: list = []
        if fallback:
            Dhh = tprod(R1, self.F(sh))
            Dhh = replace(
                Dhh,
                f=base_f + (id50,),
                s=base_s,
                w=base_w,
                c=frozenset({"wood_household"}),
                fb=True,
            )
            path_f, path_s, path_w = base_f + (id50,), base_s, base_w
            self.fallback_years[c].append(y)
        elif tzero(mrow):
            Dhh = ZERO
            path_f, path_s, path_w = (
                base_f,
                base_s | frozenset(mrow.s),
                base_w | frozenset(mrow.w),
            )
        else:
            Dhh, caph = tcap(tprod(tprod(mrow, self.F(rho)), self.F(d)), R1)
            path_f, path_s, path_w = (
                base_f + (id49,),
                base_s | frozenset(mrow.s),
                base_w | frozenset(mrow.w),
            )
            Dhh = replace(
                Dhh, f=path_f, s=path_s, w=path_w, c=frozenset({"wood_household"})
            )
            if caph:
                self.hhcap_years[c].append(y)
        Dpl = tdiffc(R1, Dhh) if not tzero(R1) else ZERO
        Dpl = (
            replace(
                Dpl,
                f=path_f,
                s=path_s,
                w=path_w,
                c=frozenset({"wood_plant"}),
                fb=fallback,
            )
            if not tzero(Dpl)
            else Dpl
        )
        info = {
            "Dtot": Dtot,
            "Dch": Dch,
            "R1": R1,
            "Dhh": Dhh,
            "Dpl": Dpl,
            "fallback": fallback,
            "caph": caph,
            "capc": capc,
            "W": W,
            "Ct": Ct,
            "region": region,
            "xxx": xxx,
            "d": d,
        }
        self.units[(c, y)] = info
        app_r = [TXT_REST] if xxx else []
        app_f = app_r + ([TXT_FALLBACK] if fallback else [])
        for g in self.wood_groups:
            fm = self.sel(
                y,
                region,
                stage=BP,
                group=g,
                tier="memo_biosphere",
                driver="wood_fuel_t",
            )
            self._er(
                key(y, BP, BP, c, g, "memo_biosphere"),
                "memowood",
                tprod(Dpl, self.F(fm)),
                "memowood",
                appended=app_f,
                comps=["wood_plant"],
            )
            Ddom = tsum([Dhh, Dch])
            if not tzero(Ddom):
                # partition ids of the union, in the fixed order 0048, 0051, 0049, 0050
                order = [id48, id51, id49, id50]
                fl = [x for x in order if x in set(Ddom.f)]
                Ddom = replace(Ddom, f=tuple(fl))
            tags = [
                x
                for x in COMP_ORDER[DOM]
                if (x == "wood_household" and not tzero(Dhh))
                or (x == "charcoal" and not tzero(Dch))
            ]
            self._er(
                key(y, DOM, BP, c, g, "memo_biosphere"),
                "memowood",
                tprod(Ddom, self.F(fm)),
                "memowood",
                appended=(app_f if (fallback and not tzero(Dhh)) else app_r),
                comps=tags,
            )
        return info

    # ---- fallout Cs-137 ----------------------------------------------------------------------------------------------
    def _cs_rows(self, y, c, peat, wu):
        if peat is None and wu is None:
            return

        def share(drv):
            return self.sel(
                y,
                "XWL",
                stage=BP,
                group="Cs137+",
                tier="liberated",
                route="air_rerelease",
                driver=drv,
            )

        S67, S68, S69, S70 = (
            share("wood_fuel_t"),
            share("household_fuelwood_m3"),
            share("charcoal_production_t"),
            share("household_charcoal_t"),
        )
        L = {BP: [], DOM: []}
        N = {BP: [], DOM: []}
        Q = {BP: [], DOM: []}
        if peat is not None:
            conc = self.sel(y, "XWL", stage=BP, group="Cs137+", residue="peat_ash")
            if peat["plant"] is not None:
                Qp = tprod(peat["plant"]["A"], self.F(conc))
                L[BP].append(tprod(Qp, self.F(S67)))
                N[BP].append(tprod(Qp, self.F(S67, True)))
                Q[BP].append(Qp)
            if peat["hh"] is not None:
                Qh = tprod(peat["hh"]["A"], self.F(conc))
                L[DOM].append(tprod(Qh, self.F(S68)))
                N[DOM].append(tprod(Qh, self.F(S68, True)))
                Q[DOM].append(Qh)
        if wu is not None:
            kap = self.sel(
                y, wu["region"], stage=BP, group="Cs137+", driver="wood_fuel_t"
            )
            Fk = self.F(kap)
            Dpl, Dhh, Dch = wu["Dpl"], wu["Dhh"], wu["Dch"]
            if not tzero(Dpl):
                Qw = tprod(Dpl, Fk)
                L[BP].append(tprod(Qw, self.F(S67)))
                N[BP].append(tprod(Qw, self.F(S67, True)))
                Q[BP].append(Qw)
            if not tzero(Dhh):
                Qw = tprod(Dhh, Fk)
                L[DOM].append(tprod(Qw, self.F(S68)))
                N[DOM].append(tprod(Qw, self.F(S68, True)))
                Q[DOM].append(Qw)
            if not tzero(Dch):
                Qc = tprod(Dch, Fk)
                L[DOM] += [
                    tprod(Qc, self.F(S69)),
                    tprod(Qc, self.F(S69, True), self.F(S70)),
                ]
                N[DOM].append(tprod(Qc, self.F(S69, True), self.F(S70, True)))
                Q[DOM].append(Qc)
        for sub in (BP, DOM):
            if not L[sub] and not N[sub]:
                continue
            tl, tn = tsum(L[sub]), tsum(N[sub])
            for tm, tag, tier, route in (
                (tl, "rerel", "liberated", "air_rerelease"),
                (tn, "memocs", "memo_biosphere", ""),
            ):
                tags = [x for x in COMP_ORDER[sub] if x in tm.c]
                app = ([TXT_REST] if (wu and wu["xxx"]) else []) + (
                    [TXT_FALLBACK] if tm.fb else []
                )
                self._er(
                    key(y, sub, BP, c, "Cs137+", tier, route),
                    tag,
                    tm,
                    tag,
                    appended=app,
                    comps=tags,
                )
            self.cs[(sub, c, y)] = {
                "Q": tsum(Q[sub]).b if Q[sub] else exact(0.0),
                "L": tl.b,
                "N": tn.b,
            }

    # ---- log expectations ----------------------------------------------------------------------------------------------
    def _log_runs(self):
        lg = self.log
        lg["no_driver_runs"] = []
        for name, series_list in (
            ("elec_gen_geothermal", ["elec_gen_geothermal"]),
            ("wood_fuel_t", ["wood_fuel_t"]),
            (
                "peat_supply_t",
                ["peat_power_heat_t", "peat_household_t", "peat_supply_t"],
            ),
        ):
            have = set()
            for s in series_list:
                for y, cs in self.by_series[s].items():
                    if cs:
                        have.add(y)
            for a, b in runs([y for y in range(self.y0, self.y1 + 1) if y not in have]):
                lg["no_driver_runs"].append((name, "XXX", a, b))
        sup = defaultdict(list)
        for c, y in lg["no_driver_supply"]:
            sup[c].append(y)
        lg["no_driver_supply_runs"] = [
            ("peat_supply_t", c, a, b) for c in sorted(sup) for a, b in runs(sup[c])
        ]
        lg["fallback_runs"] = [
            (c, a, b)
            for c in sorted(self.fallback_years)
            for a, b in runs(self.fallback_years[c])
        ]

        def capruns(kind, years_by_c, key_):
            out = []
            for c in sorted(years_by_c):
                for a, b in runs(years_by_c[c]):
                    bs = set()
                    for yy in range(a, b + 1):
                        u = self.units[(c, yy)]
                        bs |= set(u[key_])
                    out.append(
                        (
                            c,
                            a,
                            b,
                            "+".join(x for x in ("low", "central", "high") if x in bs),
                        )
                    )
            return out

        lg["hhcap_runs"] = capruns("hh", self.hhcap_years, "caph")
        lg["chcap_runs"] = capruns("ch", self.chcap_years, "capc")
        lg["predecessor"] = sorted(set(self.pred))
