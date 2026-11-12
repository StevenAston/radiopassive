"""Independent oracle for the `wind_solar` stream tests (Task 2.4).

Written from docs/WIND_SOLAR_SPEC.md (v1.0 FINAL, D74), docs/LIB_SPEC.md (v1.5, v1.6), docs/SCHEMA.md (v2.6),
docs/OIL_GAS_SPEC.md and docs/OTHER_SPEC.md conventions only. It does NOT import pipeline.*: the bounds
arithmetic (log-space quadrature product with the 1e-3 floor, correlated sums, complement, scale) is
re-implemented here with the standard library, and every number is read from the CSV files of the tree it is
given (``data/activity/*.csv``, ``data/reference/commodity_factors.csv``). The only numeric constants in this
file are the ones the spec itself fixes as rule constants (REE charge-factor bounds 1 and 5.9, spec 6.2).

``Oracle(root).expected()`` returns an ``Expected`` with

* ``rows``     dict key -> ``ER`` (key = (year, substream, product, residue, country, group, tier, route, variant)),
* ``log``      dict kind -> structure (see ``Expected``),
* ``sigma``    attribution check: (commodity, year) -> sigma at central,
* ``tonnes``   (year, substream, commodity) -> list of (class, B tonnes),
* ``unalloc``  the unallocated values behind each joint key (parts),
* ``errors``   spec-mandated raises that the data trigger (e.g. sigma > 1, share high > 1).

SPEC v1.1 (13.9-13.20) settles the earlier ambiguities: stepwise per class then sum_correlated (4.2 steps 1-6), zero
step-3 tonnage skipped, missing years inside a series' span logged and years before its first year silent,
source_ids and driver basis from the rows behind computed contributions (capacity, intensity for the driver basis),
exact scalars at central for D6, class, route, charge and OD shares, steel route share as Bounds.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

FLOOR = 1e-3
CAUSE_ORDER = [
    "zero_central_factor",
    "exact_zero",
    "clipped_difference",
    "floor_dominance",
    "inherited_flag",
]
VARIANTS = ["default", "bound_main", "bound_radio"]
VAR_RULE = {
    "default": "alloc:value",
    "bound_main": "alloc:main",
    "bound_radio": "alloc:radio",
}
# spec 6.2: rule constants
CHARGE_MAIN = 1.0
CHARGE_RADIO = 5.9
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
# world production series used for the sigma check (spec 2.1 group Q / 4.3)
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

# class k -> (substream, capacity series, share series, complement?)  (spec 2.1 group I)
CLASSES = {
    "wind_on_nopm": ("wind", "cap_add_wind_onshore", "wind_pm_share_onshore", True),
    "wind_on_pm": ("wind", "cap_add_wind_onshore", "wind_pm_share_onshore", False),
    "wind_off_nopm": ("wind", "cap_add_wind_offshore", "wind_pm_share_offshore", True),
    "wind_off_pm": ("wind", "cap_add_wind_offshore", "wind_pm_share_offshore", False),
    "pv_utility": ("solar", "cap_add_solar_pv", "pv_utility_share", False),
    "pv_rooftop": ("solar", "cap_add_solar_pv", "pv_utility_share", True),
}
CSP_SERIES = "cap_add_solar_csp"
COPPER_CLASS_SERIES = {
    "porphyry_stratiform": "cu_class_share_porphyry_stratiform",
    "iocg_high_u": "cu_class_share_iocg_high_u",
    "cu_co_stratiform": "cu_class_share_cu_co_stratiform",
}
# joint families (spec 6.1): (commodity, ore_type) -> (d6 series or 'OD', country of the series, main share, radio share)
JOINT = {
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
OD_SHARE_SERIES = "od_value_share_u"
PROD_OD = "prod_copper_od"
PROD_COPPER = "prod_copper"
CHARGE_SERIES = "ree_charge_factor"
BF_SERIES = "steel_bf_route_share"
PRIMARY_ORE_ORDER = ["iocg_olympic_dam", "iocg_high_u"]  # registry (file) order decides the merged id order


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
    """D6 split with an exact share: a share of exactly 0 is a structural zero (spec 3.4)."""
    if k == 0:
        return exact(0.0)
    return B(a.low * k, a.central * k, a.high * k, a.nd, a.causes)


def comp(s: B) -> B:
    if s.high > 1.0 + 1e-12:
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
        return B(0.0, 0.0, h, True, _ordered(inc) or ("zero_central_factor",))
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


def sum_correlated(terms: list[B]) -> B:
    if not terms:
        return exact(0.0)
    lo = sum(t.low for t in terms)
    c = sum(t.central for t in terms)
    hi = sum(t.high for t in terms)
    nd = lo == 0.0 and any(t.nd for t in terms)
    causes = _ordered([x for t in terms for x in t.causes]) if nd else ()
    if nd and not causes:
        causes = ("inherited_flag",)
    return B(lo, c, hi, nd, causes)


# --------------------------------------------------------------------------------------------
# activity rows
# --------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Act:
    series: str
    country: str
    year: int
    b: B
    unit: str
    basis: str
    src: tuple
    notes: str
    kind: str  # cap | mi | share | prod | od

    @property
    def placeholder(self) -> bool:
        return self.notes.startswith("PLACEHOLDER")


def _f(v) -> float:
    return float(v)


def _bool(v) -> bool:
    return str(v).strip().lower() == "true"


def _ids(v) -> tuple:
    v = "" if v is None else str(v)
    return tuple(x for x in v.split(";") if x)


@dataclass
class ER:
    key: tuple
    family: str  # CU, RE, ...
    commodity: str
    ore_types: list
    variant: str
    joint: bool
    b: B
    fids: list
    src: set = field(default_factory=set)  # exact source_ids (spec 13.20)
    basis: set = field(default_factory=set)  # exact driver-basis words (capacity and intensity rows only)
    share_ph: bool = False
    alloc_ph: bool = False
    country: str = ""

    @property
    def year(self):
        return self.key[0]

    @property
    def alts(self):  # kept for callers that iterate; v1.1 has one reading (S4 settled)
        return [self.b]


@dataclass
class Expected:
    rows: dict
    log: dict
    sigma: dict
    tonnes: dict
    errors: list
    class_tonnes: dict


def runs(years) -> list[tuple[int, int]]:
    ys = sorted(set(years))
    out: list[list[int]] = []
    for y in ys:
        if out and y == out[-1][1] + 1:
            out[-1][1] = y
        else:
            out.append([y, y])
    return [(a, b) for a, b in out]


class Oracle:
    def __init__(self, root: Path | str, y0: int = 1950, y1: int = 2025):
        self.root = Path(root)
        self.y0, self.y1 = y0, y1
        a = self.root / "data" / "activity"
        self.act: dict[tuple, Act] = {}
        self.by_series: dict[str, dict[int, list[Act]]] = defaultdict(lambda: defaultdict(list))
        for fname, kind_of in (
            ("capacity_additions.csv", lambda s: "cap"),
            ("material_intensity.csv", lambda s: "mi"),
            ("wind_solar_shares.csv", lambda s: "share"),
            ("commodity_production.csv", lambda s: "od" if s == PROD_OD else "prod"),
        ):
            p = a / fname
            if not p.exists():
                continue
            df = pd.read_csv(p, dtype=str, keep_default_na=False)
            for r in df.itertuples(index=False):
                ser = r.series
                if fname == "capacity_additions.csv" and r.country != "XWL":
                    continue
                if fname == "commodity_production.csv" and not (
                    ser in WORLD_SERIES.values() or ser == PROD_OD
                ):
                    continue
                row = Act(
                    ser,
                    r.country,
                    int(r.year),
                    B(_f(r.value_low), _f(r.value_central), _f(r.value_high), _bool(r.below_detection)),
                    r.unit,
                    r.basis,
                    _ids(r.source_ids),
                    r.notes,
                    kind_of(ser),
                )
                self.act[(ser, r.country, row.year)] = row
        self.factors = self._read_factors()
        self.fsrc = {fid: tuple(f["src"]) for fid, f in self.fby.items()}

    # ---- registry -------------------------------------------------------------------------
    def _read_factors(self):
        p = self.root / "data" / "reference" / "commodity_factors.csv"
        self.fby: dict[str, dict] = {}
        self.forder: dict[str, int] = {}
        self.fam_rows: dict[tuple, list] = defaultdict(list)
        if not p.exists():
            return []
        df = pd.read_csv(p, dtype=str, keep_default_na=False)
        out = []
        for i, r in enumerate(df.to_dict("records")):
            d = dict(
                fid=r.get("factor_id", ""),
                commodity=r["commodity"],
                group=r["group"],
                tier=r["tier"],
                route=r["route"],
                residue=r["residue_type"],
                region=r["region"],
                ore=r.get("ore_type", ""),
                y0=int(r["year_from"]),
                y1=int(r["year_to"]),
                variant=r["allocation_variant"],
                b=B(_f(r["value_low"]), _f(r["value_central"]), _f(r["value_high"]), _bool(r["below_detection"])),
                src=_ids(r["source_ids"]),
                component=r["component"],
                unit=r["unit"],
            )
            self.fby[d["fid"]] = d
            self.forder[d["fid"]] = i
            out.append(d)
            self.fam_rows[(d["commodity"], d["ore"], d["region"])].append(d)
        return out

    def select(self, fam: tuple, combo: tuple, year: int):
        """Exact-equality select (LIB v1.6): returns the row, None for no factor, raises on ambiguity."""
        g, t, rt, rs = combo
        hit = [
            d
            for d in self.fam_rows[fam]
            if d["group"] == g
            and d["tier"] == t
            and d["route"] == rt
            and d["residue"] == rs
            and d["variant"] == "default"
            and d["component"] == "own_residue"
            and d["y0"] <= year <= d["y1"]
        ]
        if len(hit) > 1:
            raise ValueError(f"ambiguous factor rows {fam} {combo} {year}")
        return hit[0] if hit else None

    def combos(self, fam: tuple) -> list:
        seen = []
        for d in self.fam_rows[fam]:
            c = (d["group"], d["tier"], d["route"], d["residue"])
            if c not in seen:
                seen.append(c)
        return seen

    def families(self) -> list:
        return list(self.fam_rows.keys())

    # ---- series access -----------------------------------------------------------------------
    def a(self, series, year, country="XWL"):
        return self.act.get((series, country, year))

    def share_b(self, row: Act, series: str) -> B:
        if row.unit != "1":
            raise ValueError(f"share series {series} has unit {row.unit!r}")
        if row.b.high > 1.0 + 1e-12 and series != CHARGE_SERIES:
            raise ValueError(f"share {series} {row.year} high above 1")
        return row.b

    # ---- main --------------------------------------------------------------------------------
    def expected(self) -> Expected:
        rows: dict[tuple, ER] = {}
        nodrv: dict[tuple, set] = defaultdict(set)
        nofac: dict[tuple, set] = defaultdict(set)  # (country, group, detail) -> years
        nointensity: dict[tuple, set] = defaultdict(set)
        phs: dict[str, set] = defaultdict(set)
        errors: list = []
        sigma: dict[tuple, float] = {}
        class_tonnes: dict = {}
        first: dict[tuple, int] = {}
        for (s, c, y) in self.act:
            first[(s, c)] = min(first.get((s, c), 99999), y)

        def missing(series, y, country="XWL"):
            # spec 13.13: a missing year inside a series' span is logged; years before its first year are silent
            if (series, country) not in first or y >= first[(series, country)]:
                nodrv[(series, country)].add(y)

        mi_series = sorted({s for (s, c, y) in self.act if s.startswith("mi_")})
        class_comms: dict[str, list] = defaultdict(list)
        for s in mi_series:
            for k in sorted(CLASSES, key=len, reverse=True):
                if s.startswith(f"mi_{k}_"):
                    class_comms[k].append(s[len(f"mi_{k}_") :])
                    break
        parts_by_key: dict[tuple, list] = defaultdict(list)
        sig_acc: dict[tuple, float] = defaultdict(float)

        for y in range(self.y0, self.y1 + 1):
            contribs = []  # (sub, c, k, M, rows)
            for k, (sub, capser, shser, cmpl) in CLASSES.items():
                cap = self.a(capser, y)
                if cap is None:
                    missing(capser, y)
                    continue
                sh = self.a(shser, y)
                if sh is None:
                    missing(shser, y)
                    continue
                try:
                    pi = comp(self.share_b(sh, shser)) if cmpl else self.share_b(sh, shser)
                except ValueError as e:
                    errors.append((y, str(e)))
                    continue
                C = prod(cap.b, pi)
                for c in class_comms.get(k, []):
                    I = self.a(f"mi_{k}_{c}", y)
                    if I is None:
                        missing(f"mi_{k}_{c}", y)
                        continue
                    M = prod(C, I.b)
                    contribs.append((sub, c, k, M, (cap, sh, I)))
                    class_tonnes.setdefault((y, sub, c), []).append((k, M))
                    sig_acc[(y, c)] += M.central
            if self.a(CSP_SERIES, y) is not None:
                nointensity[(CSP_SERIES, "XWL")].add(y)
            for (yy, c), tot in list(sig_acc.items()):
                if yy == y and c in WORLD_SERIES:
                    q = self.a(WORLD_SERIES[c], y)
                    if q is not None and tot > 0:
                        sigma[(c, y)] = tot / q.b.central
            for sub, c, k, M, rows3 in contribs:
                if M.central == 0:
                    continue  # spec 13.13: zero tonnage is skipped
                for fam in [f for f in self.families() if f[0] == c]:
                    self._family_contrib(y, sub, c, fam, M, rows3, parts_by_key, nodrv, nofac, missing)

        # assemble rows
        for key, parts in parts_by_key.items():
            y, sub, c, rs, country, g, t, rt, v = key
            parts_sorted = sorted(parts, key=lambda p: self.forder.get(p["fid"], 0))
            b = sum_correlated([p["b"] for p in parts_sorted])
            fids = []
            for p in parts_sorted:
                if p["fid"] not in fids:
                    fids.append(p["fid"])
            src = set()
            basis = set()
            share_ph = alloc_ph = False
            for p in parts_sorted:
                src |= set(p["fsrc"])
                for r in p["rows"]:
                    src |= set(r.src)
                    if r.kind in ("cap", "mi") and r.basis in ("interpolated", "extrapolated"):
                        basis.add(r.basis)
                    if r.kind == "share" and r.placeholder:
                        share_ph = True
                        phs[r.series].add(y)
                        if _is_d6(r.series) and p["joint"] and v == "default":
                            alloc_ph = True
            ores = []
            for p in parts_sorted:
                if p["ore"] not in ores:
                    ores.append(p["ore"])
            rows[key] = ER(
                key=key, family=FAMILY_CODE.get(c, "??"), commodity=c, ore_types=ores, variant=v,
                joint=parts_sorted[0]["joint"], b=b, fids=fids, src=src, basis=basis,
                share_ph=share_ph, alloc_ph=alloc_ph, country=country,
            )

        comm_in_reg = {d["commodity"] for d in self.factors}
        nofoot = {}
        for k, cs in class_comms.items():
            for c in cs:
                if c not in comm_in_reg:
                    nofoot.setdefault(c, f"mi_{k}_{c}")
        nofamily = set()
        regpairs = {(d["commodity"], d["ore"]) for d in self.factors}
        if "copper" in comm_in_reg:
            for o in ("porphyry_stratiform", "iocg_olympic_dam", "iocg_high_u", "cu_co_stratiform", "all"):
                if ("copper", o) not in regpairs:
                    nofamily.add(("copper", o))
        if "ree_oxide" in comm_in_reg:
            for o in ("ree_bayan_obo", "ree_ionic_clay", "ree_monazite", "ree_mt_weld"):
                if ("ree_oxide", o) not in regpairs:
                    nofamily.add(("ree_oxide", o))
        att: dict[tuple, tuple] = {}
        for (c, y), s in sigma.items():
            kk = (c, y // 10 * 10)
            if kk not in att or s > att[kk][0]:
                att[kk] = (s, y)
            if s > 1.0 + 1e-12:
                errors.append((y, f"sigma_{c} = {s:.4g} > 1"))
        log = dict(
            no_driver=nodrv, no_factor=nofac, no_intensity=nointensity, placeholder_share=phs,
            no_footprint=nofoot, no_family=nofamily, attribution=att,
        )
        return Expected(rows, log, sigma, {}, errors, class_tonnes)

    # ---- one class contribution to one family (spec 4.2 steps 3-5) -----------------------------
    def _family_contrib(self, y, sub, c, fam, M, rows3, parts_by_key, nodrv, nofac, missing):
        comm, ore, region = fam
        rows_used = set(rows3)
        steel_b = None
        scalar = 1.0
        charge_c = None
        route_c = None

        def get(series, country="XWL"):
            r = self.a(series, y, country)
            if r is None:
                missing(series, y, country)
            return r

        if c == "copper":
            if ore == "iocg_olympic_dam":
                od, cu = self.a(PROD_OD, y, "AUS"), self.a(PROD_COPPER, y, "XWL")
                if od is None:
                    missing(PROD_OD, y, "AUS")
                    return
                if cu is None:
                    missing(PROD_COPPER, y)
                    return
                rows_used |= {od, cu}
                scalar = od.b.central / cu.b.central
            elif ore in COPPER_CLASS_SERIES:
                r = get(COPPER_CLASS_SERIES[ore])
                if r is None:
                    return
                rows_used.add(r)
                scalar = r.b.central
        elif c == "ree_oxide":
            r = get(f"ree_route_share_{ore[len('ree_'):]}")
            ch = get(CHARGE_SERIES)
            if r is None or ch is None:
                return
            rows_used |= {r, ch}
            route_c, charge_c = r.b.central, ch.b.central
        elif c == "steel":
            r = get(BF_SERIES)
            if r is None:
                return
            rows_used.add(r)
            steel_b = self.share_b(r, BF_SERIES)
        joint = JOINT.get((c, ore))
        shares = None
        if joint:
            ser, cty, s_main, s_radio = joint
            if ser == "OD":
                w = get(OD_SHARE_SERIES, "AUS")
                if w is None:
                    return
                sd = 1.0 - w.b.central
            else:
                w = get(ser, cty)
                if w is None:
                    return
                sd = w.b.central
            rows_used.add(w)
            shares = {"default": sd, "bound_main": s_main, "bound_radio": s_radio}
        variants = VARIANTS if joint else ["default"]
        country = "XXX" if region == "XWL" else region
        for v in variants:
            if c == "ree_oxide":
                cv = {"default": charge_c, "bound_main": CHARGE_MAIN, "bound_radio": CHARGE_RADIO}[v]
                T = prod(M, exact(route_c * cv))
            elif c == "steel":
                T = prod(M, steel_b)
            elif c == "copper" and ore != "all":
                T = prod(M, exact(scalar))
            else:
                T = M
            if T.central == 0:
                continue  # step-3 tonnage exactly 0 at central: skipped, no lookup
            for combo in self.combos(fam):
                F = self.select(fam, combo, y)
                g, t, rt, rs = combo
                if F is None:
                    det = f"{c}/{ore or '-'}/{t}/{rs or rt}"
                    nofac[(country, g, det)].add(y)
                    continue
                A = prod(T, B(F["b"].low, F["b"].central, F["b"].high, F["b"].nd))
                if shares is not None:
                    A = scale(A, shares[v])
                parts_by_key[(y, sub, c, rs, country, g, t, rt, v)].append(
                    dict(b=A, fid=F["fid"], fsrc=F["src"], rows=rows_used, ore=ore, joint=bool(joint))
                )



def _is_d6(series: str) -> bool:
    return series.startswith("d6_value_share_") or series == OD_SHARE_SERIES


# --------------------------------------------------------------------------------------------
# notes grammar helpers (spec 3.3, 3.6)
# --------------------------------------------------------------------------------------------
SUFFIX_RE = [
    ("driver", re.compile(r"^driver basis: (interpolated|extrapolated|interpolated\+extrapolated)$")),
    ("share", re.compile(r"^share basis: placeholder$")),
    ("alloc", re.compile(r"^allocation basis: placeholder$")),
    ("cause", re.compile(r"^below_detection cause: ([a-z_+]+)$")),
]


def parse_notes(notes: str) -> dict:
    """Split notes into the family text and the ordered suffixes. Free text between is kept in ``head``."""
    parts = [p for p in (notes or "").split("; ")]
    out = {"head": [], "suffix": []}
    seen_suffix = False
    for p in parts:
        hit = None
        for name, rx in SUFFIX_RE:
            m = rx.match(p)
            if m:
                hit = (name, m.group(1) if m.groups() else "")
                break
        if hit:
            seen_suffix = True
            out["suffix"].append(hit)
        else:
            if seen_suffix:
                out.setdefault("late_free_text", []).append(p)
            out["head"].append(p)
    return out
