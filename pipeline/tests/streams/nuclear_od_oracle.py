"""Independent oracle for the Olympic Dam amendment of the nuclear stream (NUCLEAR_SPEC v1.3 section 14, D74).

Written from docs/NUCLEAR_SPEC.md section 14, docs/WIND_SOLAR_SPEC.md section 6.3 and docs/DECISIONS.md D74
only. It extends (does not edit) nuclear_oracle.py: the bounds arithmetic (``B``, ``prod``, ``comp``,
``scale``) and the data access (``Oracle``) are re-used; nothing numeric is hard-coded, every value is read
from the tree it is given.

Provides
--------
``ODOracle(root)``
    ``.f6_aus()``        expected AUS F6 rows with the carve-out (key -> ``ER6``); years whose raw central
                         difference is <= 0 write no rows (14.3) and are listed in ``.no_f6``
                         (year -> raw central; < 0 is also logged as negative_residual),
    ``.f8()``            expected F8 rows (key -> ``ER8``),
    ``.pool(y, g)``      the whole pool P_OD(y, g) = Q_OD(y) x F_OD(g, y) as a ``B`` (Bq/a),
    ``.copper_ledger(y, g, variant)``  the copper-ledger share of the pool, from the files,
    ``.military(y, g, variant)``       the military remainder a_v (1 - phi) P_OD at central.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
from nuclear_oracle import B, Oracle, comp, prod, scale

VARIANTS = ("default", "bound_main", "bound_radio")
RULE = {"default": "civil:ratio;alloc:value", "bound_main": "civil:ratio;alloc:main",
        "bound_radio": "civil:ratio;alloc:radio"}
Y0, Y1 = 1988, 2025


def cdiff(a: B, b: B) -> tuple[B, bool, float]:
    """Correlated difference (COAL_SPEC 12.1 / OIL_GAS_SPEC 3.4): c = ca - cb, low = min(la - lb, c),
    high = max(ha - hb, c); each bound clipped to >= 0; a negative central set to 0.
    Returns (result, clipped, raw central). ``clipped`` is true when any raw bound or the raw central was
    below 0; the result is then flagged (cause ``clipped_difference``) when its low is 0."""
    raw_c = a.central - b.central
    c = max(raw_c, 0.0)
    lo_raw = min(a.low - b.low, raw_c)
    hi_raw = max(a.high - b.high, raw_c)
    lo, hi = max(lo_raw, 0.0), max(hi_raw, c)
    lo = min(lo, c)
    clipped = lo_raw < 0 or raw_c < 0 or hi_raw < 0
    nd = clipped and lo == 0.0
    return B(lo, c, hi, nd, ("clipped_difference",) if nd else ()), clipped, raw_c


@dataclass
class ER6:
    key: tuple
    b: B
    clipped: bool
    od_year: bool
    factor_ids: list
    src_req: set
    src_extra_ok: set
    basis: set
    rule: str
    raw_c: float = 0.0


@dataclass
class ER8:
    key: tuple          # (year, group, variant)
    b: B
    factor_id: str
    src: set
    basis: set
    rule: str
    share: float
    phi: B


def _read(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


class ODOracle:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.o = Oracle(self.root)
        act = self.root / "data" / "activity"
        self.od_u: dict[int, dict] = {}
        self.q_od: dict[int, dict] = {}
        self.w_u: dict[int, dict] = {}
        for r in self.o.act.values():
            if r["series"] == "u_production_od" and r["country"] == "AUS":
                self.od_u[int(r["year"])] = r
        p = act / "commodity_production.csv"
        if p.exists():
            df = pd.read_csv(p, dtype=str, keep_default_na=False)
            for r in df[df["series"] == "prod_copper_od"].to_dict("records"):
                if r["country"] == "AUS":
                    self.q_od[int(r["year"])] = r
        p = act / "wind_solar_shares.csv"
        if p.exists():
            df = pd.read_csv(p, dtype=str, keep_default_na=False)
            for r in df[df["series"] == "od_value_share_u"].to_dict("records"):
                if r["country"] == "AUS":
                    self.w_u[int(r["year"])] = r
        p = self.root / "data" / "reference" / "commodity_factors.csv"
        self.cf: list[dict] = []
        if p.exists():
            self.cf = [r for r in _read(p)
                       if r["commodity"] == "copper" and r["component"] == "own_residue"
                       and r.get("ore_type") == "iocg_olympic_dam" and r["tier"] == "impounded"
                       and r["residue_type"] == "metal_tailings" and r["region"] == "AUS"
                       and r["allocation_variant"] == "default"]
        self.groups = sorted({r["group"] for r in self.cf})
        self.no_f6: dict[int, float] = {}

    # ---- inputs -------------------------------------------------------------------------------
    @staticmethod
    def bnd(r: dict) -> B:
        return B(float(r["value_low"]), float(r["value_central"]), float(r["value_high"]))

    def factor(self, y: int, g: str) -> dict:
        c = [r for r in self.cf if r["group"] == g and int(r["year_from"]) <= y <= int(r["year_to"])]
        assert len(c) == 1, f"oracle: {len(c)} OD factor rows for {g} {y}"
        return c[0]

    def phi(self, y: int) -> B:
        return self.o.a("phi_civil", y, "XWL")

    def share(self, y: int, variant: str) -> float:
        """a_v(y): default w_U (exact central), bound_main 0, bound_radio 1."""
        if variant == "bound_main":
            return 0.0
        if variant == "bound_radio":
            return 1.0
        return float(self.w_u[y]["value_central"])

    # ---- pool and ledgers -----------------------------------------------------------------------
    def pool(self, y: int, g: str) -> B:
        return prod(self.bnd(self.q_od[y]), self.bnd(self.factor(y, g)))

    def copper_ledger(self, y: int, g: str, variant: str) -> B:
        """WIND_SOLAR_SPEC 6.3: (1 - w_U) default, 1 bound_main, 0 bound_radio, of the whole pool."""
        k = {"default": 1.0 - float(self.w_u[y]["value_central"]), "bound_main": 1.0, "bound_radio": 0.0}[variant]
        return scale(self.pool(y, g), k)

    def military(self, y: int, g: str, variant: str) -> float:
        """Central military remainder a_v (1 - phi) P_OD (not in either ledger, logged)."""
        return self.share(y, variant) * (1.0 - self.phi(y).central) * self.pool(y, g).central

    # ---- F8 -------------------------------------------------------------------------------------
    def f8(self) -> dict:
        out = {}
        for y in sorted(self.q_od):
            if not (Y0 <= y <= Y1) or y not in self.w_u or not self.o.has("phi_civil", y, "XWL"):
                continue
            phi = self.phi(y)
            srcs_act = self.o.src(self.q_od[y], self.w_u[y], self.o.arow("phi_civil", y, "XWL"))
            basis = self.o.basis_words(self.q_od[y], self.w_u[y], self.o.arow("phi_civil", y, "XWL"))
            for g in self.groups:
                f = self.factor(y, g)
                P = self.pool(y, g)
                for v in VARIANTS:
                    a = self.share(y, v)
                    if v == "bound_main":
                        b = B(0.0, 0.0, 0.0)
                    else:
                        b = prod(P, B(a, a, a), phi)
                    srcs = {x for x in f["source_ids"].split(";") if x} | srcs_act
                    out[(y, g, v)] = ER8((y, g, v), b, f["factor_id"], srcs, basis, RULE[v], a, phi)
        return out

    def conv_aus(self, y: int) -> B:
        """Conventional AUS tonnage before the civil share, bounds as the stream computes them (14.2)."""
        o = self.o
        P = o.a("u_production", y, "AUS")
        s_row = o.select(y, "AUS", stage="u_mining_isl", group="", tier="", route="", residue_type="",
                         driver_series="")
        return prod(P, comp(o.fb(s_row)))

    # ---- F6 AUS with the carve-out ----------------------------------------------------------------
    def f6_aus(self) -> dict:
        o = self.o
        fam = {f["group"] for f in o.factors if f["stage"] == "u_milling" and f["tier"] == "impounded"
               and f["residue_type"] == "u_tailings" and f["region"] == "XWL"}
        out = {}
        self.no_f6 = {}
        for y in range(1950, 2026):
            if not (o.has("u_production", y, "AUS") and o.has("phi_civil", y, "XWL")):
                continue
            P = o.a("u_production", y, "AUS")
            if o.is_zero(P):
                continue
            s_row = o.select(y, "AUS", stage="u_mining_isl", group="", tier="", route="", residue_type="",
                             driver_series="")
            conv = prod(P, comp(o.fb(s_row)))
            od_year = y in self.od_u
            clipped, raw_c = False, 0.0
            if od_year:
                conv_all = conv
                conv, clipped, raw_c = cdiff(conv, o.a("u_production_od", y, "AUS"))
                self.conv_all = conv_all
                if raw_c <= 0.0:       # 14.3: no row (negative: also logged; exactly 0: silent)
                    self.no_f6[y] = raw_c
                    continue
            T = prod(conv, o.a("phi_civil", y, "XWL"))
            rule = "civil:pre1965" if y <= 1964 else "civil:ratio"
            phi_row = o.arow("phi_civil", y, "XWL")
            rows = [o.arow("u_production", y, "AUS"), phi_row]
            base_src = o.src(*rows)
            for g in sorted(fam):
                f = o.try_select(y, "AUS", stage="u_milling", group=g, tier="impounded", route="",
                                 residue_type="u_tailings")
                if f is None:
                    continue
                b = prod(T, o.fb(f))
                k = (y, "fuel_cycle", "u_milling", "AUS", g, "impounded", "flow", "", "u_tailings", "")
                od_src = o.src(o.arow("u_production_od", y, "AUS")) if od_year else set()  # required (B4 ruled)
                out[k] = ER6(k, b, clipped, od_year, [s_row["factor_id"], f["factor_id"]],
                             base_src | o.src(s_row) | o.src(f) | od_src, set(), o.basis_words(*rows), rule, raw_c)
        return out
