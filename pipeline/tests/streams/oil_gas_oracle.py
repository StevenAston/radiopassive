"""Independent arithmetic oracle for the oil and gas stream tests (Task 2.3).

Written from docs/OIL_GAS_SPEC.md (v1.0), docs/NUCLEAR_SPEC.md (13), docs/COAL_SPEC.md (11-12),
docs/LIB_SPEC.md (v1.4) and docs/SCHEMA.md only. It does NOT import pipeline.lib or pipeline.streams:
the bounds arithmetic (log-space quadrature product, independent and correlated differences, linear and
quadrature sums, the D6 shares) is re-implemented here with the standard library, and the data are read
with pandas straight from the CSV files of the tree it is given. Nothing numeric from the registry or the
activity files is hard-coded.

``Oracle(root).expected()`` returns an ``Expected`` holding

* ``rows``   dict key -> ``ER`` for data/streams/oil_gas.csv (1950-2025),
* ``pre``    dict key -> ``ER`` for data/streams_pre1950/oil_gas.csv (1900-1949),
* ``neg``    list of (year, label, magnitude) rest-of-world / quantity residuals below zero,
* ``no_unit_value`` list of (family, year) joint rows that cannot be allocated,
* ``parts``  dict of unallocated intermediate values for the conservation tests.

The key of a row is ``(year, substream, stage, country, group, tier, route, residue_type, product,
allocation_variant)`` with ``""`` for an empty cell (quantity is always ``flow``, event_id empty).

Reading choices where the spec is silent are listed in the header of test_oil_gas.py (A-items).
Products are nested stepwise as in OIL_GAS_SPEC 5.2 (D71 C4).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

FLOOR = 1e-3
TOL = 1e-5
CAUSE_ORDER = ["zero_central_factor", "exact_zero", "clipped_difference", "floor_dominance", "inherited_flag"]
PRODUCTS = ("oil", "gas", "ngl")
VARIANTS = (("default", "alloc:value"), ("bound_main", "alloc:main"), ("bound_radio", "alloc:radio"))
BASIS_WORDS = ("extrapolated", "interpolated")
ALLOC_BASIS_WORDS = ("extrapolated", "interpolated", "modelled")
REST_GAS = "rest of world (world aggregate minus listed countries)"
REST_WATER = "rest of world (world aggregate minus USA)"
WORLD_FLARE = "world aggregate (no country split before 2012)"


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
    hl: float | None = None     # alternative (nested-product) high bound for zero-central chains

    @property
    def hlo(self) -> float:
        return self.high if self.hl is None else self.hl


def _ordered(causes) -> tuple:
    s = set(causes)
    return tuple(c for c in CAUSE_ORDER if c in s)


def exact(x: float) -> B:
    return B(x, x, x)


def scale(a: B, k: float) -> B:
    return B(a.low * k, a.central * k, a.high * k, a.nd, a.causes, None if a.hl is None else a.hl * k)


def comp(s: B) -> B:
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
        h = hl = 1.0
        for t in terms:
            h *= t.high
            hl *= t.hlo
        return B(0.0, 0.0, h, True, _ordered(inc + ["zero_central_factor"]), hl if hl != h else None)
    c = 1.0
    for t in terms:
        c *= t.central
    up = math.sqrt(sum((math.log(t.high) - math.log(t.central)) ** 2 for t in terms))
    total = floored = 0.0
    for t in terms:
        if t.low > 0:
            total += (math.log(t.central) - math.log(t.low)) ** 2
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
    c = math.fsum(t.central for t in terms)
    lo = c - math.sqrt(sum((t.central - t.low) ** 2 for t in terms))
    hi = c + math.sqrt(sum((t.high - t.central) ** 2 for t in terms))
    return B(max(lo, 0.0), c, max(hi, c))


def sum_correlated(terms: list[B]) -> B:
    lo = math.fsum(t.low for t in terms)
    c = math.fsum(t.central for t in terms)
    hi = math.fsum(t.high for t in terms)
    nd = lo == 0.0 and any(t.nd for t in terms)
    causes = _ordered([x for t in terms for x in t.causes]) if nd else ()
    if nd and not causes:
        causes = ("inherited_flag",)
    hl = math.fsum(t.hlo for t in terms)
    return B(lo, c, hi, nd, causes, hl if hl != hi else None)


def diff(a: B, b: B) -> tuple[B, float]:
    """Independent difference (OIL_GAS_SPEC 3.4). Returns (result, raw central difference)."""
    raw = a.central - b.central
    c = max(raw, 0.0)
    lo_raw = c - math.sqrt((a.central - a.low) ** 2 + (b.high - b.central) ** 2)
    hi_raw = c + math.sqrt((a.high - a.central) ** 2 + (b.central - b.low) ** 2)
    low = max(lo_raw, 0.0)
    high = max(hi_raw, c)
    clipped = lo_raw < 0 or raw < 0
    nd = clipped and low == 0.0
    return B(low, c, high, nd, ("clipped_difference",) if nd else ()), raw


def cdiff(a: B, b: B) -> tuple[B, float]:
    """Correlated difference (OIL_GAS_SPEC 3.4, COAL_SPEC 12.1)."""
    raw = a.central - b.central
    c = max(raw, 0.0)
    lo_raw = min(a.low - b.low, c)
    hi_raw = max(a.high - b.high, c)
    low = max(lo_raw, 0.0)
    high = max(hi_raw, c)
    clipped = lo_raw < 0 or raw < 0
    nd = clipped and low == 0.0
    return B(low, c, high, nd, ("clipped_difference",) if nd else ()), raw


def cap(w: B, a: B) -> B:
    lo, c, hi = min(w.low, a.low), min(w.central, a.central), min(w.high, a.high)
    if (lo, c, hi) == (w.low, w.central, w.high):
        return w
    return B(lo, c, hi, w.nd and lo == 0.0, w.causes if (w.nd and lo == 0.0) else ())


# --------------------------------------------------------------------------------------------
# containers
# --------------------------------------------------------------------------------------------
@dataclass
class ER:
    key: tuple
    b: B
    unit: str
    code: str                       # notes prefix without colon (PW, AB, DR, OS, GD, GN, GV, GP, OR, FL)
    factor_ids: list
    fid_req: set
    fid_opt: set
    src_req: set
    src_opt: set
    driver_basis: set
    alloc_basis: set | None         # None: no allocation basis suffix expected
    rule: str
    product: str
    variant: str
    fragments: list = field(default_factory=list)
    tag: str = ""
    nd_ok: bool = True

    @property
    def year(self):
        return self.key[0]


@dataclass
class Expected:
    rows: dict
    pre: dict
    neg: list
    no_unit_value: list
    parts: dict
    missing: list


def rkey(year, substream, stage, country, group, tier, route, residue, product, variant):
    return (year, substream, stage, country, group, tier, route, residue, product, variant)


class Act:
    __slots__ = ("b", "basis", "src", "unit", "series", "year", "country")

    def __init__(self, r):
        self.series, self.year, self.country = r["series"], int(r["year"]), r["country"]
        self.b = B(float(r["value_low"]), float(r["value_central"]), float(r["value_high"]),
                   nd=r["below_detection"].strip().lower() == "true")
        self.basis = r["basis"]
        self.src = [s for s in r["source_ids"].split(";") if s]
        self.unit = r["unit"]


# --------------------------------------------------------------------------------------------
# the oracle
# --------------------------------------------------------------------------------------------
class Oracle:
    def __init__(self, root: Path):
        self.root = Path(root)
        fac = pd.read_csv(self.root / "data" / "factors" / "oil_gas.csv", dtype=str, keep_default_na=False)
        self.factors = fac.to_dict("records")
        for f in self.factors:
            f["yf"], f["yt"] = int(f["year_from"]), int(f["year_to"])
        self.fid = {f["factor_id"]: f for f in self.factors}
        self.act: dict = {}
        self.by_series: dict[str, dict[int, list[str]]] = {}
        for name in ("oil_gas", "oil_gas_drivers"):
            p = self.root / "data" / "activity" / f"{name}.csv"
            if not p.exists():
                continue
            df = pd.read_csv(p, dtype=str, keep_default_na=False)
            for r in df.to_dict("records"):
                k = (r["series"], int(r["year"]), r["country"])
                if k in self.act:
                    raise ValueError(f"oracle: duplicate activity key {k}")
                self.act[k] = Act(r)
                self.by_series.setdefault(r["series"], {}).setdefault(int(r["year"]), []).append(r["country"])
        self.missing: list = []
        self.neg: list = []
        self.nuv: list = []
        self.parts: dict = {}
        self._alloc_cache: dict = {}

    # ---- lookups -------------------------------------------------------------------------------
    def a(self, series, year, country):
        return self.act.get((series, year, country))

    def countries(self, series, year):
        return sorted(c for c in self.by_series.get(series, {}).get(year, []) if c != "XWL")

    def years(self, series):
        return sorted(self.by_series.get(series, {}))

    def select(self, year, region, **kw):
        exact_, world = [], []
        for f in self.factors:
            if not (f["yf"] <= year <= f["yt"]):
                continue
            if any(f[k] != v for k, v in kw.items()):
                continue
            if f["region"] == region:
                exact_.append(f)
            elif f["region"] == "XWL":
                world.append(f)
        win = exact_ or world
        if not win:
            raise LookupError(f"no factor row for {year} {region} {kw}")
        if len(win) > 1:
            raise LookupError(f"ambiguous factor rows for {year} {region} {kw}: {[w['factor_id'] for w in win]}")
        return win[0]

    def try_select(self, year, region, **kw):
        try:
            return self.select(year, region, **kw)
        except LookupError as exc:
            self.missing.append(str(exc))
            return None

    @staticmethod
    def fb(f) -> B:
        return B(float(f["value_low"]), float(f["value_central"]), float(f["value_high"]),
                 nd=f["below_detection"].strip().lower() == "true")

    @staticmethod
    def fsrc(f) -> set:
        return {s for s in f["source_ids"].split(";") if s}

    def groups_of(self, **kw) -> list[str]:
        out = []
        for f in self.factors:
            if all(f[k] == v for k, v in kw.items()) and f["group"] not in out:
                out.append(f["group"])
        return out

    # ---- driver basis ----------------------------------------------------------------------------
    @staticmethod
    def dbasis(acts) -> set:
        return {x.basis for x in acts if x is not None and x.basis in BASIS_WORDS}

    # ---- top level -------------------------------------------------------------------------------
    def expected(self) -> Expected:
        rows: dict = {}
        pre: dict = {}
        self._singles(rows, pre)
        self._flaring(rows)
        self._oil_sands(rows)
        self._joint(rows)
        seen, neg = set(), []
        for y, lab, mag in self.neg:
            if (y, lab) not in seen:
                seen.add((y, lab))
                neg.append((y, lab, mag))
        return Expected(rows, pre, neg, self.nuv, self.parts, self.missing)

    def _put(self, rows, pre, er: ER):
        d = pre if er.key[0] < 1950 else rows
        if er.key in d:
            raise ValueError(f"oracle produced a duplicate key {er.key}")
        d[er.key] = er

    # ---- single-driver gas and oil radon (6.1 - 6.3) -------------------------------------------
    SINGLES = {
        "GD": dict(series="gas_production_m3", unit="m3", product="gas", substream="all", stage="processing_transport",
                   group="Rn222+", tier="liberated", route="air_delivered_gas", residue="",
                   sel=dict(stage="processing_transport", substream="all", group="Rn222+", tier="liberated",
                            route="air_delivered_gas", residue_type="")),
        "GN": dict(series="gas_production_m3", unit="m3", product="ngl", substream="all", stage="processing_transport",
                   group="Rn222+", tier="liberated", route="air_delivered_gas", residue="",
                   sel=dict(stage="processing_transport", substream="all", group="Rn222+", tier="liberated",
                            route="air_delivered_gas", residue_type="og_processing_residue")),
        "GV": dict(series="gas_production_m3", unit="m3", product="gas", substream="all", stage="processing_transport",
                   group="Rn222+", tier="liberated", route="air_vented_gas", residue="",
                   sel=dict(stage="processing_transport", substream="all", group="Rn222+", tier="liberated",
                            route="air_vented_gas", residue_type="")),
        "GP": dict(series="gas_production_m3", unit="m3", product="gas", substream="all", stage="processing_transport",
                   group="Pb210+", tier="impounded", route="", residue="og_processing_residue",
                   sel=dict(stage="processing_transport", substream="all", group="Pb210+", tier="impounded",
                            route="", residue_type="og_processing_residue")),
        "OR": dict(series="oil_production_t", unit="t", product="oil", substream="all", stage="processing_transport",
                   group="Rn222+", tier="liberated", route="air_stack", residue="",
                   sel=dict(stage="processing_transport", substream="all", group="Rn222+", tier="liberated",
                            route="air_stack", residue_type="")),
    }

    def residual(self, series, y, label):
        """Rest-of-world residual of a country-level series. Returns (B or None, listed acts, xwl act)."""
        xwl = self.a(series, y, "XWL")
        listed = [self.a(series, y, c) for c in self.countries(series, y)]
        if xwl is None:
            return None, listed, None
        s = sum_independent([x.b for x in listed]) if listed else exact(0.0)
        r, raw = diff(xwl.b, s)
        if abs(raw) <= TOL * xwl.b.central:
            return None, listed, xwl
        if raw < 0:
            self.neg.append((y, label, -raw))
            return None, listed, xwl
        if r.central == 0.0:
            return None, listed, xwl
        return r, listed, xwl

    def _singles(self, rows, pre):
        for code, sp in self.SINGLES.items():
            series = sp["series"]
            for y in self.years(series):
                if not (1900 <= y <= 2025):
                    continue
                for c in self.countries(series, y):
                    d = self.a(series, y, c)
                    if d.b.high == 0 and d.b.central == 0 and d.b.low == 0:
                        continue
                    f = self.try_select(y, c, **sp["sel"])
                    if f is None:
                        continue
                    self._put(rows, pre, self._single_er(code, sp, y, c, f, prod(d.b, self.fb(f)), [d], False))
                r, listed, xwl = self.residual(series, y, series)
                if r is None:
                    continue
                f = self.try_select(y, "XWL", **sp["sel"])
                if f is None:
                    continue
                self._put(rows, pre, self._single_er(code, sp, y, "XXX", f, prod(r, self.fb(f)), [xwl] + listed, True))

    def _single_er(self, code, sp, y, country, f, b, drivers, rest, frag=None, stage=None, substream=None, product=None):
        key = rkey(y, substream or sp["substream"], stage or sp["stage"], country, sp["group"], sp["tier"],
                   sp["route"], sp["residue"], product or sp["product"], "default")
        src_all = set().union(*[set(x.src) for x in drivers]) if drivers else set()
        req = self.fsrc(f)
        if drivers:
            req = req | set(drivers[0].src)
        frags = [REST_GAS] if rest else ([frag] if frag else [])
        return ER(key, b, "Bq/a", code, [f["factor_id"]], {f["factor_id"]}, set(), req, src_all - req,
                  self.dbasis(drivers), None, "none", product or sp["product"], "default", frags, code)

    # ---- flaring (6.4) ---------------------------------------------------------------------------
    def _flaring(self, rows):
        series = "gas_flared_m3"
        sel = dict(stage="production", substream="all", group="Rn222+", tier="liberated", route="air_stack",
                   residue_type="", driver_series="gas_flared_m3")
        base = dict(substream="all", stage="production", group="Rn222+", tier="liberated", route="air_stack",
                    residue="", product="oil", series=series, unit="m3")
        for y in self.years(series):
            if not (1950 <= y <= 2025):
                continue
            ctry = self.countries(series, y)
            xwl = self.a(series, y, "XWL")
            if ctry:
                for c in ctry:
                    d = self.a(series, y, c)
                    if d.b.high == 0:
                        continue
                    f = self.try_select(y, c, **sel)
                    if f is None:
                        continue
                    er = self._single_er("FL", base, y, c, f, prod(d.b, self.fb(f)), [d], False)
                    rows[er.key] = er
                r, listed, xw = self.residual(series, y, series)
                if r is not None:
                    f = self.try_select(y, "XWL", **sel)
                    if f is not None:
                        er = self._single_er("FL", base, y, "XXX", f, prod(r, self.fb(f)), [xw] + listed, True)
                        rows[er.key] = er
            elif xwl is not None and xwl.b.high != 0:
                f = self.try_select(y, "XWL", **sel)
                if f is not None:
                    er = self._single_er("FL", base, y, "XXX", f, prod(xwl.b, self.fb(f)), [xwl], False, frag=WORLD_FLARE)
                    rows[er.key] = er

    # ---- oil sands (7.3) -------------------------------------------------------------------------
    def _oil_sands(self, rows):
        series = "oil_sands_ore_processed_t"
        for y in self.years(series):
            if not (1950 <= y <= 2025):
                continue
            d = self.a(series, y, "CAN")
            if d is None or d.b.high == 0:
                continue
            for g in self.groups_of(stage="oil_sands_mining"):
                f = self.try_select(y, "CAN", stage="oil_sands_mining", substream="", group=g, tier="impounded",
                                    route="", residue_type="oil_sands_tailings")
                if f is None:
                    continue
                key = rkey(y, "oil_sands", "oil_sands_mining", "CAN", g, "impounded", "", "oil_sands_tailings",
                           "bitumen", "default")
                req = self.fsrc(f) | set(d.src)
                rows[key] = ER(key, prod(d.b, self.fb(f)), "Bq/a", "OS", [f["factor_id"]], {f["factor_id"]}, set(),
                               req, set(), self.dbasis([d]), None, "none", "bitumen", "default", [], "OS")

    # ---- D6 allocation (4) ------------------------------------------------------------------------
    def alloc(self, geo, y):
        """Shares for a geography-year. Raises KeyError('no unit value') when q > 0 and no price."""
        ck = (geo, y)
        if ck in self._alloc_cache:
            v = self._alloc_cache[ck]
            if isinstance(v, Exception):
                raise v
            return v
        try:
            v = self._alloc(geo, y)
        except KeyError as exc:
            self._alloc_cache[ck] = exc
            raise
        self._alloc_cache[ck] = v
        return v

    def _alloc(self, geo, y):
        qs = {"oil": "oil_production_m3", "gas": "gas_production_m3", "ngl": "ngl_production_m3"}
        vs = {"oil": "unit_value_oil_usd_per_m3", "gas": "unit_value_gas_usd_per_m3", "ngl": "unit_value_ngl_usd_per_m3"}
        q, v, used = {}, {}, []
        for p in PRODUCTS:
            if geo == "USA":
                x = self.a(qs[p], y, "USA")
                q[p] = x.b.central if x else 0.0
                if x:
                    used.append(x)
            else:
                xw, us = self.a(qs[p], y, "XWL"), self.a(qs[p], y, "USA")
                if xw is None:
                    q[p] = 0.0
                else:
                    raw = xw.b.central - (us.b.central if us else 0.0)
                    if raw < 0:
                        self.neg.append((y, qs[p], -raw))
                    q[p] = max(raw, 0.0)
                    used.append(xw)
                    if us:
                        used.append(us)
            pv = (self.a(vs[p], y, "USA") or self.a(vs[p], y, "XWL")) if geo == "USA" else self.a(vs[p], y, "XWL")
            if pv is not None:
                v[p] = pv.b.central
                used.append(pv)
            elif q[p] > 0:
                raise KeyError(f"no unit value for {p} in {geo} {y}")
            else:
                v[p] = 0.0
        val = {p: q[p] * v[p] for p in PRODUCTS}
        tot = math.fsum(val.values())
        if tot <= 0:
            raise KeyError(f"allocation denominator 0 in {geo} {y}")
        order = list(PRODUCTS)
        main = max(order, key=lambda p: (val[p], -order.index(p)))
        rest = [p for p in order if p != main]
        radio = max(rest, key=lambda p: (val[p], -order.index(p)))
        shares = {
            "default": {p: val[p] / tot for p in PRODUCTS},
            "bound_main": {p: 1.0 if p == main else 0.0 for p in PRODUCTS},
            "bound_radio": {p: 1.0 if p == radio else 0.0 for p in PRODUCTS},
        }
        basis = {x.basis for x in used if x.basis in ALLOC_BASIS_WORDS}
        src = set()
        for x in used:
            src |= set(x.src)
        return dict(shares=shares, main=main, radio=radio, val=val, q=q, v=v, basis=basis, src=src)

    # ---- joint families (5, 7.1, 7.2) -----------------------------------------------------------
    def _emit(self, rows, y, geo, sub, stage, group, tier, route, residue, R: B, code, fids, fid_req, fid_opt,
              src_req, drv_basis, al, unit="Bq/a", tag="", frags=()):
        for p in PRODUCTS:
            for variant, tok in VARIANTS:
                s = al["shares"][variant][p]
                b = exact(0.0) if s == 0.0 else (R if s == 1.0 else scale(R, s))
                key = rkey(y, sub, stage, geo, group, tier, route, residue, p, variant)
                if key in rows:
                    raise ValueError(f"oracle produced a duplicate key {key}")
                ab = (al["basis"] if variant == "default" else None)
                rows[key] = ER(key, b, unit, code, list(fids), set(fid_req), set(fid_opt), set(src_req),
                               set(al["src"]), set(drv_basis), ab, tok, p, variant, list(frags), tag)

    def _joint(self, rows):
        cs = dict(stage="production", substream="conventional")
        cu = dict(stage="production", substream="unconventional")
        wgroups = self.groups_of(**cs)
        pw = "produced_water_m3"
        for y in range(1950, 2026):
            usa, xw = self.a(pw, y, "USA"), self.a(pw, y, "XWL")
            for geo in ("USA", "XXX"):
                if geo == "USA":
                    if usa is None:
                        continue
                    V, region, drivers, frag = usa.b, "USA", [usa], []
                else:
                    if xw is None or usa is None:
                        continue
                    V, raw = cdiff(xw.b, usa.b)
                    region, drivers, frag = "XWL", [xw, usa], [REST_WATER]
                    if raw < 0:
                        self.neg.append((y, pw, -raw))
                if V.high == 0:
                    continue
                try:
                    al = self.alloc(geo, y)
                except KeyError:
                    self.nuv.append(("production", y))
                    continue
                self._production(rows, y, geo, region, V, drivers, frag, al, wgroups)
        self._drilling(rows)

    def _sel(self, y, region, **kw):
        base = dict(stage="production", substream="", group="", tier="", route="", residue_type="")
        base.update(kw)
        return self.try_select(y, region, **base)

    def _production(self, rows, y, geo, region, V, drivers, frag, al, wgroups):
        pwsel = "produced_water_m3"
        sgroups = [g for g in self.groups_of(stage="production", substream="", tier="", residue_type="og_scale",
                                             route="", driver_series="") if g and g != "Pb210+"]
        u = self._sel(y, region, driver_series="produced_water_unconv_share")
        phi = self.try_select(y, "XWL", stage="abandonment_scrap", substream="", group="", tier="", route="",
                              residue_type="og_scale", driver_series="")
        if u is None or phi is None:
            return
        ub, phib = self.fb(u), self.fb(phi)
        drv_src = set().union(*[set(d.src) for d in drivers])
        drv_basis = self.dbasis(drivers)
        for sub in ("conventional", "unconventional"):
            contrib: dict = {}      # (tier, route, residue, group) -> list of (B, ids, opt)
            ret: dict = {}          # group -> list for abandonment
            A, W, S = {}, {}, {}
            for g in wgroups:
                c = self._sel(y, region, substream=sub, group=g)
                if c is None:
                    continue
                cb = self.fb(c)
                # D71 C4: stepwise nesting, A = product(apply(V, C), share)
                VC = prod(V, cb)
                Ab = prod(VC, comp(ub) if sub == "conventional" else ub)
                A[g] = Ab
                base_ids = [c["factor_id"], u["factor_id"]]
                src = self.fsrc(c) | self.fsrc(u)
                for tier, route, residue in (("reisolated", "", "og_produced_water"), ("impounded", "", "og_sludge"),
                                             ("liberated", "water_produced_discharge", ""),
                                             ("dispersed", "", "og_produced_water")):
                    t = self._sel(y, region, tier=tier, route=route, residue_type=residue if tier != "liberated" else "",
                                  driver_series=pwsel)
                    if t is None:
                        continue
                    Wb = cap(prod(Ab, self.fb(t)), Ab)
                    W[(g, tier)] = Wb
                    contrib.setdefault((tier, route, residue, g), []).append(
                        (Wb, base_ids + [t["factor_id"]], set(), src | self.fsrc(t)))
            # solids
            for g in sgroups:
                if g not in A:
                    continue
                c = self._sel(y, region, substream=sub, group=g)
                for r in ("og_scale", "og_sludge"):
                    sg = self._sel(y, "XWL", group=g, residue_type=r)
                    if sg is None:
                        continue
                    S[(g, r)] = (prod(A[g], self.fb(sg)), [c["factor_id"], u["factor_id"], sg["factor_id"]],
                                 self.fsrc(c) | self.fsrc(u) | self.fsrc(sg))
            pbg = "Pb210+"
            for r in ("og_scale", "og_sludge"):
                pi = self._sel(y, "XWL", group=pbg, residue_type=r)
                base = S.get(("Ra226+", r))
                if pi is None or base is None:
                    continue
                S[(pbg, r)] = (prod(base[0], self.fb(pi)), base[1] + [pi["factor_id"]], base[2] | self.fsrc(pi))
            for (g, r), (Sb, ids, src) in S.items():
                self.parts[(geo, y, sub, "S", g, r)] = Sb
                if r == "og_scale":
                    rem = prod(Sb, comp(phib))
                    rt = prod(Sb, phib)
                    self.parts[(geo, y, sub, "Srem", g, r)] = rem
                    self.parts[(geo, y, sub, "Sret", g, r)] = rt
                    rem_ids, rem_src = ids + [phi["factor_id"]], src | self.fsrc(phi)
                    ret_ids, ret_src = ids + [phi["factor_id"]], src | self.fsrc(phi)
                    ret[g] = (rt, ret_ids, ret_src)
                else:
                    rem, rem_ids, rem_src = Sb, ids, src
                    self.parts[(geo, y, sub, "Srem", g, r)] = rem
                for tier, route in (("impounded", ""), ("dispersed", ""), ("liberated", "water_produced_discharge")):
                    rho = self._sel(y, "XWL", tier=tier, route=route, residue_type=r, driver_series="")
                    if rho is None:
                        continue
                    X = prod(rem, self.fb(rho))
                    self.parts[(geo, y, sub, "X", g, r, tier)] = X
                    res = "" if tier == "liberated" else r
                    contrib.setdefault((tier, route, res, g), []).append(
                        (X, rem_ids + [rho["factor_id"]], set(), rem_src | self.fsrc(rho)))
            for (g, tier), Wb in W.items():
                self.parts[(geo, y, sub, "A", g)] = A[g]
                self.parts[(geo, y, sub, "W", g, tier)] = Wb
            # merge and emit production rows
            order_key = lambda k: k   # noqa: E731
            for (tier, route, residue, g), lst in sorted(contrib.items(), key=lambda kv: order_key(kv[0])):
                R = sum_correlated([x[0] for x in lst])
                self.parts[(geo, y, sub, "R", g, tier, route, residue)] = R
                ids, req, opt, src = [], set(), set(), set()
                for _, i, o, s in lst:
                    for x in i:
                        if x not in ids:
                            ids.append(x)
                    src |= s
                req = set(ids)
                # D71 C7: solids contributions do not list T
                opt = set()
                self._emit(rows, y, geo, sub, "production", g, tier, route, residue, R, "PW", ids, req, opt,
                           src | drv_src, drv_basis, al, tag="PW", frags=frag)
            # abandonment
            for g, (rt, ids, src) in ret.items():
                for tier, residue in (("impounded", "og_scale"), ("dispersed", "og_scaled_scrap")):
                    a = self.try_select(y, "XWL", stage="abandonment_scrap", substream="", group="", tier=tier,
                                        route="", residue_type=residue)
                    if a is None:
                        continue
                    Rb = prod(rt, self.fb(a))
                    self.parts[(geo, y, sub, "AB", g, tier)] = Rb
                    self._emit(rows, y, geo, sub, "abandonment_scrap", g, tier, "", residue, Rb, "AB",
                               ids + [a["factor_id"]], set(ids + [a["factor_id"]]), set(),
                               src | self.fsrc(a) | drv_src, drv_basis, al, tag="AB", frags=frag)

    def _drilling(self, rows):
        for sub, series in (("conventional", "us_wells_drilled_vertical"), ("unconventional", "us_wells_drilled_horizontal")):
            for y in self.years(series):
                if not (1949 <= y <= 2025):
                    continue
                d = self.a(series, y, "USA")
                if d is None or d.b.high == 0:
                    continue
                if y < 1950:
                    if sub == "conventional":
                        self.nuv.append(("drilling", y))
                    continue
                try:
                    al = self.alloc("USA", y)
                except KeyError:
                    self.nuv.append(("drilling", y))
                    continue
                for g in self.groups_of(stage="drilling", substream=sub):
                    f = self.try_select(y, "USA", stage="drilling", substream=sub, group=g, tier="impounded",
                                        route="", residue_type="og_drill_cuttings")
                    if f is None:
                        continue
                    R = prod(d.b, self.fb(f))
                    self.parts[(y, sub, "DR", g)] = R
                    self._emit(rows, y, "USA", sub, "drilling", g, "impounded", "", "og_drill_cuttings", R, "DR",
                               [f["factor_id"]], {f["factor_id"]}, set(), self.fsrc(f) | set(d.src),
                               self.dbasis([d]), al, tag="DR")
