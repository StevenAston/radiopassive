"""Independent arithmetic oracle for the nuclear stream tests (Task 2.1).

Written from docs/NUCLEAR_SPEC.md (v1.2), docs/LIB_SPEC.md (v1.4) and docs/SCHEMA.md only. It does
NOT import pipeline.lib or pipeline.streams: the bounds arithmetic (log-space quadrature product,
independent difference, linear and quadrature sums) is re-implemented here with the standard
library, and the data are read with pandas straight from the CSV files. Nothing numeric from the
registry or the activity files is hard-coded; every value is read from the tree it is given.

What it produces
----------------
``Oracle(root).expected()`` returns an ``Expected`` object holding

* ``rows``     dict key -> ``ER``  for data/streams/nuclear.csv (years 1950-2025),
* ``pre``      dict key -> ``ER``  for data/streams_pre1950/nuclear.csv,
* ``missing``  list of ``Miss`` (a (group, route, year) with a driver value and no factor row),
* ``events``   per-event bookkeeping used by the conservation tests.

The key of a row is ``(year, substream, stage, country, group, tier, quantity, route, residue_type,
event_id)`` with ``""`` for an empty cell.

Bounds conventions (LIB_SPEC 1.2, 7.7, 8.1; NUCLEAR_SPEC 3.3, 3.4)
-------------------------------------------------------------------
``B`` carries ``nd`` (the master ``below_detection`` flag) and ``causes``, a tuple drawn from
``CAUSE_ORDER``. ``prod`` sets ``nd`` when the zero-low floor rule fired, when a term has a zero
central and a positive high, or when an exact-zero term meets a flagged input; the cause is the
union of the causes of the inputs, or ``floor_dominance`` / ``zero_central_factor`` /
``inherited_flag`` when the inputs give none.
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

FLOOR = 1e-3
GWA_TWH = 8.766
CAUSE_ORDER = ["zero_central_factor", "exact_zero", "clipped_difference", "floor_dominance", "inherited_flag"]
LWR_TYPES = ["pwr", "bwr", "phwr", "gcr", "lwgr", "fbr"]
TYPES = LWR_TYPES
EVENT_TYPE = {"E002": "pwr", "E004": "lwgr", "E013": "bwr"}


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


def scale(a: B, k: float) -> B:
    return B(a.low * k, a.central * k, a.high * k, a.nd, a.causes)


def comp(s: B) -> B:
    """ISL complement 1 - s (NUCLEAR_SPEC 3.4): anti-correlated, unflagged."""
    if s.high > 1.0:
        raise ValueError("share high above 1")
    return B(1.0 - s.high, 1.0 - s.central, 1.0 - s.low)


def prod(*terms: B) -> B:
    """Log-space quadrature product (LIB_SPEC 1.2 with 7.7 and 8.1)."""
    inc = [c for t in terms for c in t.causes]
    any_nd = any(t.nd for t in terms)
    if any(t.high == 0 for t in terms):
        causes = _ordered(inc) if any_nd else ()
        nd = any_nd
        if nd and not causes:
            causes = ("inherited_flag",)
        return B(0.0, 0.0, 0.0, nd, causes)
    if any(t.central == 0 for t in terms):
        h = 1.0
        for t in terms:
            h *= t.high
        causes = _ordered(inc + ["zero_central_factor"])
        return B(0.0, 0.0, h, True, causes)
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


def diff(a: B, b: B) -> tuple[B, float]:
    """Independent difference (NUCLEAR_SPEC 3.4). Returns (result, raw central difference)."""
    raw = a.central - b.central
    c = max(raw, 0.0)
    lo_raw = c - math.sqrt((a.central - a.low) ** 2 + (b.high - b.central) ** 2)
    hi_raw = c + math.sqrt((a.high - a.central) ** 2 + (b.central - b.low) ** 2)
    low = max(lo_raw, 0.0)
    high = max(hi_raw, c)
    clipped = lo_raw < 0 or raw < 0
    nd = clipped and low == 0.0
    return B(low, c, high, nd, ("clipped_difference",) if nd else ()), raw


def remainder(I: B, R: B) -> tuple[B, bool]:
    """Bound-wise damaged-core remainder of NUCLEAR_SPEC 7.3 item 1. Returns (D, low_was_clipped)."""
    raw_c = I.central - R.central
    raw_l = I.low - R.low
    raw_h = I.high - R.high
    dc = max(raw_c, 0.0)
    dl = min(max(raw_l, 0.0), dc)
    dh = max(max(raw_h, 0.0), dc)
    clipped = raw_l < 0 and dl == 0.0
    return B(dl, dc, dh, clipped, ("clipped_difference",) if clipped else ()), raw_c < 0


# --------------------------------------------------------------------------------------------
# expected-row containers
# --------------------------------------------------------------------------------------------
@dataclass
class ER:
    key: tuple
    b: B
    unit: str
    factor_ids: list
    rule: str
    src_req: set
    src_opt: set = field(default_factory=set)
    basis: set = field(default_factory=set)       # driver basis words (interpolated / extrapolated)
    flag_note: str = ""                           # "; civil share undocumented (D64)" text, or ""
    tag: str = ""
    ids_exact: bool = True                         # False: only the last factor id is asserted
    nd_policy: str = "exact"                       # "exact" or "loose"
    extra: dict = field(default_factory=dict)

    @property
    def year(self):
        return self.key[0]


@dataclass
class Miss:
    stage: str
    country: str
    group: str
    route: str
    year: int
    tag: str = ""


@dataclass
class Expected:
    rows: dict
    pre: dict
    missing: list
    events: dict
    no_family: list
    negative_residual: dict
    predecessor_dropped: list
    extras: dict


def key(year, substream, stage, country, group, tier, quantity, route="", residue="", event=""):
    return (year, substream, stage, country, group, tier, quantity, route, residue, event)


# --------------------------------------------------------------------------------------------
# the oracle
# --------------------------------------------------------------------------------------------
class Oracle:
    def __init__(self, root: Path):
        self.root = Path(root)
        fac = pd.read_csv(self.root / "data" / "factors" / "nuclear.csv", dtype=str, keep_default_na=False)
        self.factors = fac.to_dict("records")
        self.act: dict = {}
        for name in ("uranium", "electricity_generation", "nuclear", "nuclear_cycle"):
            p = self.root / "data" / "activity" / f"{name}.csv"
            if not p.exists():
                continue
            df = pd.read_csv(p, dtype=str, keep_default_na=False)
            for r in df.to_dict("records"):
                k = (r["series"], int(r["year"]), r["country"])
                if k in self.act:
                    raise ValueError(f"oracle: duplicate activity key {k}")
                self.act[k] = r
        ev = pd.read_csv(self.root / "data" / "events.csv", dtype=str, keep_default_na=False)
        self.events = {r["event_id"]: r for r in ev.to_dict("records") if r["stream"] == "nuclear"}
        self.by_series: dict[str, dict[int, list[str]]] = defaultdict(lambda: defaultdict(list))
        for (s, y, c) in self.act:
            self.by_series[s][y].append(c)

    # ---- activity ---------------------------------------------------------------------------
    def has(self, series, year, country) -> bool:
        return (series, year, country) in self.act

    def arow(self, series, year, country) -> dict:
        return self.act[(series, year, country)]

    def a(self, series, year, country) -> B:
        r = self.act[(series, year, country)]
        return B(float(r["value_low"]), float(r["value_central"]), float(r["value_high"]))

    def countries(self, series, year) -> list[str]:
        return sorted(c for c in self.by_series[series].get(year, []) if c != "XWL")

    def years_of(self, series, country) -> list[int]:
        return sorted(y for (s, y, c) in self.act if s == series and c == country)

    @staticmethod
    def is_zero(b: B) -> bool:
        return b.low == 0 and b.central == 0 and b.high == 0

    def basis_words(self, *rows: dict) -> set:
        return {r["basis"] for r in rows if r["basis"] in ("interpolated", "extrapolated")}

    @staticmethod
    def src(*rows: dict) -> set:
        out: set = set()
        for r in rows:
            out |= {x for x in r["source_ids"].split(";") if x}
        return out

    # ---- factors ----------------------------------------------------------------------------
    def _index(self):
        if not hasattr(self, "_idx"):
            idx = defaultdict(list)
            for f in self.factors:
                idx[(f["stage"], f["group"], f["tier"], f["route"])].append(f)
            self._idx = idx
        return self._idx

    def select(self, year: int, region: str, **match: str) -> dict:
        idx = self._index()
        if all(k in match for k in ("stage", "group", "tier", "route")):
            pool0 = idx.get((match["stage"], match["group"], match["tier"], match["route"]), [])
        else:
            pool0 = self.factors
        cands = [f for f in pool0
                 if int(f["year_from"]) <= year <= int(f["year_to"])
                 and f["region"] in (region, "XWL")
                 and all(f[k] == v for k, v in match.items())]
        ex = [f for f in cands if f["region"] == region]
        pool = ex or cands
        if not pool:
            raise LookupError(f"no factor row: {year} {region} {match}")
        if len(pool) > 1:
            raise RuntimeError(f"oracle: ambiguous factor rows {[p['factor_id'] for p in pool]} for {year} {region} {match}")
        return pool[0]

    def try_select(self, year, region, **match):
        try:
            return self.select(year, region, **match)
        except LookupError:
            return None

    @staticmethod
    def fb(f: dict) -> B:
        return B(float(f["value_low"]), float(f["value_central"]), float(f["value_high"]))

    def family(self, **match) -> list[tuple[str, str]]:
        """Distinct (group, route) pairs among registry rows matching ``match`` (all years, all regions)."""
        s = {(f["group"], f["route"]) for f in self.factors if all(f[k] == v for k, v in match.items())}
        return sorted(s)

    # ---- the whole build ----------------------------------------------------------------------
    def expected(self) -> Expected:
        self.rows: dict = {}
        self.pre: dict = {}
        self.missing: list = []
        self.no_family: list = []
        self.neg_res: dict = {}
        self.pred_dropped: list = []
        self.ev_info: dict = {}
        self._uranium()
        self._conv_enrich_fab()
        self._reprocessing()
        self._sea()
        self._reactors()
        self._events()
        return Expected(self.rows, self.pre, self.missing, self.ev_info, self.no_family, self.neg_res,
                        self.pred_dropped, {})

    def _put(self, er: ER, pre: bool = False):
        tgt = self.pre if pre else self.rows
        if er.key in tgt:
            raise RuntimeError(f"oracle: duplicate expected key {er.key}")
        tgt[er.key] = er

    # ---- uranium front end ----------------------------------------------------------------------
    def _uranium(self):
        fam = {
            "F1": {"stage": "u_mining_conv", "tier": "liberated", "route": "air_ventilation", "residue": "", "ds": "u_production",
                       "T": "conv", "qty": "flow", "tier_out": "liberated"},
            "F2": {"stage": "u_mining_isl", "tier": "liberated", "route": "air_process_vent", "residue": "", "ds": "u_production",
                       "T": "isl"},
            "F3": {"stage": "u_milling", "tier": "liberated", "route": "air_process_vent", "residue": "", "ds": None, "T": "all"},
            "F4": {"stage": "u_milling", "tier": "liberated", "route": "air_dust", "residue": "", "ds": None, "T": "all"},
            "F5": {"stage": "u_milling", "tier": "sealed_fuel_cycle", "route": "", "residue": "", "ds": None, "T": "all"},
            "F6": {"stage": "u_milling", "tier": "impounded", "route": "", "residue": "u_tailings", "ds": None, "T": "conv"},
        }
        self.u_fam = fam
        groups = {}
        for name, d in fam.items():
            match = {"stage": d["stage"], "tier": d["tier"], "route": d["route"], "residue_type": d["residue"]}
            if d["ds"]:
                match["driver_series"] = d["ds"]
            groups[name] = sorted({f["group"] for f in self.factors if all(f[k] == v for k, v in match.items())
                                   and f["region"] == "XWL"})
        self.u_groups = groups
        memo_match = {"stage": "u_mining_conv", "tier": "memo_earth_moved"}
        self.memo_groups = sorted({f["group"] for f in self.factors if all(f[k] == v for k, v in memo_match.items())})
        for y in range(1950, 2026):
            if not self.has("phi_civil", y, "XWL"):
                continue
            listed = self.countries("u_production", y)
            if "CSK" in listed and "CZE" in listed:
                listed.remove("CZE")
                self.pred_dropped.append(y)
            phi_row = self.arow("phi_civil", y, "XWL")
            phi = self.a("phi_civil", y, "XWL")
            used = []
            for c in listed:
                P = self.a("u_production", y, c)
                used.append(self.arow("u_production", y, c))
                if self.is_zero(P):
                    continue
                self._u_country(y, c, c, P, [self.arow("u_production", y, c)], phi, phi_row, row_note="")
            if self.has("u_production", y, "XWL"):
                xr = self.arow("u_production", y, "XWL")
                S = sum_independent([self.a("u_production", y, c) for c in listed]) if listed else exact(0.0)
                R, raw = diff(self.a("u_production", y, "XWL"), S)
                if raw < 0:
                    self.neg_res[y] = -raw
                elif R.central > 0:
                    self._u_country(y, "XXX", "XWL", R, [xr] + used, phi, phi_row, row_note="rest")

    def _u_country(self, y, out_country, region, P, drivers, phi, phi_row, row_note):
        s_row = self.select(y, region, stage="u_mining_isl", group="", tier="", route="", residue_type="",
                            driver_series="")
        s = self.fb(s_row)
        Tall = prod(P, phi)
        Tisl = prod(P, s, phi)
        Tconv = prod(P, comp(s), phi)
        rule = "civil:pre1965" if y <= 1964 else "civil:ratio"
        basis = self.basis_words(phi_row, *drivers)
        base_src = self.src(phi_row, *drivers)
        for name, d in self.u_fam.items():
            T = {"conv": Tconv, "isl": Tisl, "all": Tall}[d["T"]]
            uses_isl = d["T"] != "all"
            for g in self.u_groups[name]:
                match = {"stage": d["stage"], "group": g, "tier": d["tier"], "route": d["route"]}
                if d["residue"]:
                    match["residue_type"] = d["residue"]
                if d["ds"]:
                    match["driver_series"] = d["ds"]
                f = self.try_select(y, region, **match)
                if f is None:
                    self.missing.append(Miss(d["stage"], out_country, g, d["route"], y, name))
                    continue
                b = prod(T, self.fb(f))
                ids = ([s_row["factor_id"]] if uses_isl else []) + [f["factor_id"]]
                srcs = base_src | self.src(f) | (self.src(s_row) if uses_isl else set())
                opt = set() if uses_isl else self.src(s_row)
                tier = d["tier"]
                k = key(y, "fuel_cycle", d["stage"], out_country, g, tier, "flow", d["route"], d["residue"])
                self._put(ER(k, b, "Bq/a", ids, rule, srcs, opt, basis, "", name, ids_exact=uses_isl,
                             extra={"rest": row_note == "rest", "Tconv": Tconv, "Tall": Tall, "Tisl": Tisl}))
        # memo family: USA only, 1950-1988, never the rest-of-world residual
        if out_country == "USA":
            for g in self.memo_groups:
                f = self.try_select(y, "USA", stage="u_mining_conv", group=g, tier="memo_earth_moved", route="",
                                    residue_type="", driver_series="u_production")
                if f is None:
                    self.missing.append(Miss("u_mining_conv", "USA", g, "", y, "F7"))
                    continue
                b = prod(Tconv, self.fb(f))
                k = key(y, "fuel_cycle", "u_mining_conv", "USA", g, "memo_earth_moved", "flow")
                self._put(ER(k, b, "Bq/a", [s_row["factor_id"], f["factor_id"]], rule,
                             base_src | self.src(f) | self.src(s_row), set(), basis, "", "F7",
                             extra={"Tconv": Tconv}))

    # ---- generic pair writer ------------------------------------------------------------------
    def _pair(self, stage, country, y, g, items, rule, basis, base_src, flag_note, tag, pre=False):
        """items: list of (route, B, factor_row). Writes transfer_in per route and one transfer_out."""
        ins = []
        for route, b, f in items:
            ins.append(b)
            k = key(y, "fuel_cycle", stage, country, g, "liberated", "transfer_in", route)
            self._put(ER(k, b, "Bq", [f["factor_id"]], rule, base_src | self.src(f), set(), basis, flag_note, tag))
        out = sum_correlated(ins)
        k = key(y, "fuel_cycle", stage, country, g, "sealed_fuel_cycle", "transfer_out")
        ids = [f["factor_id"] for _, _, f in items]
        srcs = set(base_src)
        for _, _, f in items:
            srcs |= self.src(f)
        self._put(ER(k, out, "Bq", ids, rule, srcs, set(), basis, flag_note, tag))

    def _conv_enrich_fab(self):
        fam = self.family(stage="conv_enrich_fab", tier="liberated")
        for y in range(1950, 2026):
            if not self.has("elec_gen_nuclear", y, "XWL"):
                continue
            Gb = self.a("elec_gen_nuclear", y, "XWL")
            if self.is_zero(Gb):
                continue
            row = self.arow("elec_gen_nuclear", y, "XWL")
            G = scale(Gb, 1.0 / GWA_TWH)
            by_g: dict = defaultdict(list)
            for g, route in fam:
                f = self.try_select(y, "XWL", stage="conv_enrich_fab", group=g, tier="liberated", route=route,
                                    driver_series="elec_gen_nuclear")
                if f is None:
                    self.missing.append(Miss("conv_enrich_fab", "XXX", g, route, y, "enrich"))
                    continue
                by_g[g].append((route, prod(G, self.fb(f)), f))
            for g, items in by_g.items():
                self._pair("conv_enrich_fab", "XXX", y, g, items, "none", self.basis_words(row), self.src(row), "",
                           "enrich")

    def _reprocessing(self):
        fam = self.family(stage="reprocessing", tier="liberated")
        self.repro_fam = fam
        for y in range(1950, 2026):
            for c in self.countries("nuc_reprocessed_gwa", y):
                Gb = self.a("nuc_reprocessed_gwa", y, c)
                if self.is_zero(Gb):
                    continue
                row = self.arow("nuc_reprocessed_gwa", y, c)
                by_g: dict = defaultdict(list)
                for g, route in fam:
                    f = self.try_select(y, "XWL", stage="reprocessing", group=g, tier="liberated", route=route)
                    if f is None:
                        self.missing.append(Miss("reprocessing", c, g, route, y, "repro"))
                        continue
                    by_g[g].append((route, prod(Gb, self.fb(f)), f))
                for g, items in by_g.items():
                    self._pair("reprocessing", c, y, g, items, "civil:throughput", self.basis_words(row),
                               self.src(row), "", "repro")

    def _sea(self):
        fam = self.family(stage="sea_disposal", tier="liberated")
        self.sea_groups = sorted({g for g, _ in fam})
        for y in range(1946, 2026):
            for c in self.countries("nuc_sea_dumped_tbq", y):
                Db = self.a("nuc_sea_dumped_tbq", y, c)
                if self.is_zero(Db):
                    continue
                row = self.arow("nuc_sea_dumped_tbq", y, c)
                unit = row["unit"]
                D = scale(Db, 1e12) if unit == "TBq" else Db
                flag = "; civil share undocumented (D64)" if c == "USA" else ""
                by_g: dict = defaultdict(list)
                for g, route in fam:
                    f = self.try_select(y, "XWL", stage="sea_disposal", group=g, tier="liberated", route=route)
                    if f is None:
                        self.missing.append(Miss("sea_disposal", c, g, route, y, "sea"))
                        continue
                    by_g[g].append((route, prod(D, self.fb(f)), f))
                for g, items in by_g.items():
                    if y < 1950:
                        route, b, f = items[0]
                        k = key(y, "fuel_cycle", "sea_disposal", c, g, "liberated", "flow", route)
                        self._put(ER(k, b, "Bq/a", [f["factor_id"]], "none", self.src(row) | self.src(f), set(),
                                     self.basis_words(row), flag, "sea_pre", extra={"D": D}), pre=True)
                    else:
                        self._pair("sea_disposal", c, y, g, items, "none", self.basis_words(row), self.src(row),
                                   flag, "sea")

    # ---- reactors -------------------------------------------------------------------------------
    def _reactors(self):
        for t in TYPES:
            gen, cap = f"nuc_gen_{t}", f"nuc_cap_{t}"
            eff = self.family(stage="reactor_operation", tier="liberated", driver_series=gen)
            core = sorted({f["group"] for f in self.factors if f["stage"] == "reactor_operation"
                           and f["tier"] == "sealed_in_core" and f["driver_series"] == cap})
            spent = sorted({f["group"] for f in self.factors if f["stage"] == "spent_fuel"
                            and f["tier"] == "sealed_fuel_cycle" and f["driver_series"] == gen})
            if not eff:
                self.no_family.append((t, "effluent"))
            if not core:
                self.no_family.append((t, "in_core"))
            if not spent:
                self.no_family.append((t, "spent_fuel"))
            for y in range(1950, 2026):
                if self.has(gen, y, "XWL"):
                    Gb = self.a(gen, y, "XWL")
                    if not self.is_zero(Gb):
                        row = self.arow(gen, y, "XWL")
                        G = scale(Gb, 1.0 / GWA_TWH)
                        bw = self.basis_words(row)
                        for g, route in eff:
                            f = self.try_select(y, "XWL", stage="reactor_operation", group=g, tier="liberated",
                                                route=route, driver_series=gen)
                            if f is None:
                                self.missing.append(Miss("reactor_operation", "XXX", g, route, y, "eff:" + t))
                                continue
                            k = key(y, t, "reactor_operation", "XXX", g, "liberated", "flow", route)
                            self._put(ER(k, prod(G, self.fb(f)), "Bq/a", [f["factor_id"]], "none",
                                         self.src(row) | self.src(f), set(), bw, "", "eff"))
                        for g in spent:
                            f = self.try_select(y, "XWL", stage="spent_fuel", group=g, tier="sealed_fuel_cycle",
                                                route="", driver_series=gen)
                            if f is None:
                                self.missing.append(Miss("spent_fuel", "XXX", g, "", y, "spent:" + t))
                                continue
                            k = key(y, t, "spent_fuel", "XXX", g, "sealed_fuel_cycle", "flow")
                            self._put(ER(k, prod(G, self.fb(f)), "Bq/a", [f["factor_id"]], "none",
                                         self.src(row) | self.src(f), set(), bw, "", "spent"))
                if self.has(cap, y, "XWL"):
                    Cb = self.a(cap, y, "XWL")
                    if not self.is_zero(Cb):
                        row = self.arow(cap, y, "XWL")
                        for g in core:
                            f = self.try_select(y, "XWL", stage="reactor_operation", group=g, tier="sealed_in_core",
                                                route="", driver_series=cap)
                            if f is None:
                                self.missing.append(Miss("reactor_operation", "XXX", g, "", y, "core:" + t))
                                continue
                            k = key(y, t, "reactor_operation", "XXX", g, "sealed_in_core", "standing_inventory")
                            self._put(ER(k, prod(Cb, self.fb(f)), "Bq", [f["factor_id"]], "none",
                                         self.src(row) | self.src(f), set(), self.basis_words(row), "", "core"))

    # ---- events ---------------------------------------------------------------------------------
    def capacity_row(self, event_id: str) -> dict:
        e = self.events[event_id]
        y = int(e["date_start"][:4])
        return self.select(y, e["country"], stage="accident", group="", tier="", route="", residue_type="",
                           driver_series="")

    def _events(self):
        for eid, e in sorted(self.events.items()):
            y = int(e["date_start"][:4])
            c = e["country"]
            if e["stage"] == "accident":
                rel = [f for f in self.factors if f["stage"] == "accident" and f["tier"] == "liberated"
                       and f["region"] == c and int(f["year_from"]) <= y <= int(f["year_to"])]
                if rel:
                    self._accident(eid, e, y, c, rel)
            elif e["stage"] == "u_milling" and e["event_type"] == "impoundment_failure":
                self._impound(eid, e, y, c)

    def _accident(self, eid, e, y, c, rel):
        t = EVENT_TYPE[eid]
        inv_rows = [f for f in self.factors if f["stage"] == "accident" and f["tier"] == "sealed_in_core"
                    and f["region"] == c and int(f["year_from"]) <= y <= int(f["year_to"])]
        inv: dict = {}
        inv_ids: dict = {}
        cap = None
        if inv_rows:
            for g in sorted({f["group"] for f in inv_rows}):
                f = self.select(y, c, stage="accident", group=g, tier="sealed_in_core", route="")
                inv[g] = self.fb(f)
                inv_ids[g] = [f["factor_id"]]
        else:
            cap = self.capacity_row(eid)
            C = self.fb(cap)
            core_groups = sorted({f["group"] for f in self.factors if f["stage"] == "reactor_operation"
                                  and f["tier"] == "sealed_in_core" and f["driver_series"] == f"nuc_cap_{t}"})
            for g in core_groups:
                f = self.try_select(y, "XWL", stage="reactor_operation", group=g, tier="sealed_in_core", route="",
                                    driver_series=f"nuc_cap_{t}")
                if f is None:
                    continue
                inv[g] = prod(C, self.fb(f))
                inv_ids[g] = [cap["factor_id"], f["factor_id"]]
        relg: dict = defaultdict(list)
        for f in rel:
            relg[f["group"]].append(f)
        ev_src = {x for x in e["source_ids"].split(";") if x}
        info = {"type": t, "year": y, "country": c, "groups": {}, "central_sum": 0.0, "cap": cap,
                "release_rows": rel}
        for g in sorted(set(inv) | set(relg)):
            rels = sorted(relg.get(g, []), key=lambda f: f["route"])
            Rb = [self.fb(f) for f in rels]
            R = sum_correlated(Rb) if Rb else exact(0.0)
            has_inv = g in inv
            I = inv.get(g, exact(0.0))
            D, neg = remainder(I, R)
            O = B(R.low + D.low, R.central + D.central, R.high + D.high,
                  (R.low + D.low) == 0.0 and (R.nd or D.nd), ())
            info["groups"][g] = {"I": I, "R": R, "D": D, "O": O, "has_inv": has_inv, "has_rel": bool(rels), "neg": neg}
            ids_inv = inv_ids.get(g, [])
            for f, b in zip(rels, Rb):
                info["central_sum"] += b.central
                k = key(y, t, "accident", c, g, "liberated", "transfer_in", f["route"], "", eid)
                self._put(ER(k, b, "Bq", [f["factor_id"]], "none", self.src(f) | ev_src, set(), set(), "", "acc_rel",
                             ids_exact=False, nd_policy="loose", extra={"inv_ids": ids_inv}))
            allids = ids_inv + [f["factor_id"] for f in rels]
            srcs = ev_src.copy()
            for fid in allids:
                srcs |= self.src(next(f for f in self.factors if f["factor_id"] == fid))
            if has_inv and not (D.low == 0 and D.central == 0 and D.high == 0):
                k = key(y, t, "accident", c, g, "sealed_damaged_core", "transfer_in", "", "", eid)
                self._put(ER(k, D, "Bq", allids, "none", srcs, set(), set(), "", "acc_dmg", ids_exact=False,
                             extra={"inv_ids": ids_inv}))
            k = key(y, t, "accident", c, g, "sealed_in_core", "transfer_out", "", "", eid)
            self._put(ER(k, O, "Bq", allids, "none", srcs, set(), set(), "", "acc_out", ids_exact=False,
                         nd_policy="loose", extra={"inv_ids": ids_inv}))
        self.ev_info[eid] = info

    def _impound(self, eid, e, y, c):
        A = B(float(e["activity_low_bq"]), float(e["activity_central_bq"]), float(e["activity_high_bq"]))
        rows = [f for f in self.factors if f["stage"] == "u_milling" and f["region"] == c
                and int(f["year_from"]) <= y <= int(f["year_to"]) and f["description"].startswith(eid)]
        ev_src = {x for x in e["source_ids"].split(";") if x}
        by_g: dict = defaultdict(list)
        total = 0.0
        for f in sorted(rows, key=lambda f: (f["group"], f["tier"], f["route"])):
            b = prod(A, self.fb(f))
            total += b.central
            by_g[f["group"]].append((f, b))
            tier = f["tier"]
            residue = "u_tailings" if tier == "dispersed" else ""
            k = key(y, "fuel_cycle", "u_milling", c, f["group"], tier, "transfer_in", f["route"], residue, eid)
            self._put(ER(k, b, "Bq", [f["factor_id"]], "civil:doc", self.src(f) | ev_src, set(), set(), "", "e003_in"))
        for g, items in by_g.items():
            O = sum_correlated([b for _, b in items])
            k = key(y, "fuel_cycle", "u_milling", c, g, "impounded", "transfer_out", "", "u_tailings", eid)
            srcs = set(ev_src)
            for f, _ in items:
                srcs |= self.src(f)
            self._put(ER(k, O, "Bq", [f["factor_id"] for f, _ in items], "civil:doc", srcs, set(), set(), "",
                         "e003_out"))
        self.ev_info[eid] = {"central_sum": total, "A": A, "share_rows": rows, "groups": dict(by_g)}
