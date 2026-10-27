"""Independent arithmetic oracle for the coal stream tests (Task 2.2).

Written from docs/COAL_SPEC.md, docs/LIB_SPEC.md (v1.2) and docs/METHODS.md 11.1 only.
It deliberately does NOT import pipeline.lib or pipeline.streams: all bounds arithmetic
(log-space quadrature products, the independent difference of COAL_SPEC 7, bound-wise
minimum) is re-implemented here with the standard library, and the data are read with
pandas straight from the CSV files.

Conventions (LIB_SPEC 8.1):
* A bounds triple is (low, central, high) plus a flag `nd` meaning "low is zero because of
  a non-detect, the floor rule or the zero-central rule".
* `prod` follows LIB_SPEC 1.2 and 7.7: an exact-zero term gives exact zero; a zero central
  with positive high gives (0, 0, product of highs) flagged; a zero low is replaced by
  10^-3 times the central inside the logarithm, and the result low is 0 (flagged) when the
  floored terms contribute more than half of the squared log distance.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

FLOOR = 1e-3
POWER_COAL_ASH_YIELD = 0.12


@dataclass(frozen=True)
class B:
    low: float
    central: float
    high: float
    nd: bool = False


def exact(x: float) -> B:
    return B(x, x, x)


def scale(a: B, k: float) -> B:
    return B(a.low * k, a.central * k, a.high * k, a.nd)


def prod(*terms: B) -> B:
    """Log-space quadrature product (METHODS 11.1, LIB_SPEC 1.2 with the 7.7 / 8.1 rules)."""
    if any(t.high == 0 for t in terms):
        return B(0.0, 0.0, 0.0, any(t.nd for t in terms))
    if any(t.central == 0 for t in terms):
        h = 1.0
        for t in terms:
            h *= t.high
        return B(0.0, 0.0, h, True)
    c = 1.0
    for t in terms:
        c *= t.central
    up = math.sqrt(sum(math.log(t.high / t.central) ** 2 for t in terms))
    total = 0.0
    floored = 0.0
    for t in terms:
        if t.low > 0:
            d2 = math.log(t.central / t.low) ** 2
            total += d2
        else:
            d2 = math.log(1.0 / FLOOR) ** 2
            total += d2
            floored += d2
    low = c * math.exp(-math.sqrt(total))
    floor_fired = floored > 0.5 * total
    if floor_fired:
        low = 0.0
    nd = (low == 0.0) and (floor_fired or any(t.nd for t in terms))
    return B(low, c, c * math.exp(up), nd)


def diff(a: B, b: B) -> B:
    """Independent difference (COAL_SPEC 7). Returns B with nd False (flag unspecified)."""
    c = a.central - b.central
    if c < 0:
        c = 0.0
    low = c - math.sqrt((a.central - a.low) ** 2 + (b.high - b.central) ** 2)
    high = c + math.sqrt((a.high - a.central) ** 2 + (b.central - b.low) ** 2)
    low = max(low, 0.0)
    high = max(high, c)
    return B(low, c, high)


def cdiff(a: B, b: B) -> B:
    """Correlated difference (COAL_SPEC 12.1): low = l_a - l_b, high = h_a - h_b, central = c_a - c_b.

    Negative central -> 0, each bound clipped to >= 0, then ordered by clamping around the central
    (the spec's "ordered" is ambiguous between clamping and sorting; callers avoid cases where they differ).
    The flag is True when the raw low was negative (a clipped low) or the central was negative.
    """
    c_raw = a.central - b.central
    low_raw = a.low - b.low
    high_raw = a.high - b.high
    c = max(c_raw, 0.0)
    clipped = low_raw < 0 or c_raw < 0
    low = min(max(low_raw, 0.0), c)
    high = max(max(high_raw, 0.0), c)
    return B(low, c, high, clipped and low == 0.0)


def raw_central_diff(a: B, b: B) -> float:
    return a.central - b.central


def sum_independent(terms: list[B]) -> B:
    c = sum(t.central for t in terms)
    lo = c - math.sqrt(sum((t.central - t.low) ** 2 for t in terms))
    hi = c + math.sqrt(sum((t.high - t.central) ** 2 for t in terms))
    return B(max(lo, 0.0), c, hi)


def sum_correlated(terms: list[B]) -> B:
    return B(sum(t.low for t in terms), sum(t.central for t in terms), sum(t.high for t in terms))


def bound_min(a: B, b: B) -> B:
    return B(min(a.low, b.low), min(a.central, b.central), min(a.high, b.high))


class Oracle:
    """Reads the real (or a copied) tree with pandas and answers 'what should this row be'."""

    def __init__(self, root: Path):
        self.root = Path(root)
        fac = pd.read_csv(self.root / "data" / "factors" / "coal.csv", dtype=str, keep_default_na=False)
        self.factors = fac.to_dict("records")
        act = pd.read_csv(self.root / "data" / "activity" / "coal.csv", dtype=str, keep_default_na=False)
        self.act = {}
        for r in act.to_dict("records"):
            self.act[(r["series"], int(r["year"]), r["country"])] = r
        self.countries_by_series_year: dict[tuple[str, int], list[str]] = {}
        for (s, y, c) in self.act:
            self.countries_by_series_year.setdefault((s, y), []).append(c)

    # ---- activity -------------------------------------------------------
    def has(self, series: str, year: int, country: str) -> bool:
        return (series, year, country) in self.act

    def a(self, series: str, year: int, country: str) -> B:
        r = self.act[(series, year, country)]
        return B(float(r["value_low"]), float(r["value_central"]), float(r["value_high"]))

    def a_sources(self, series: str, year: int, country: str) -> set[str]:
        return set(self.act[(series, year, country)]["source_ids"].split(";"))

    def listed_countries(self, series: str, year: int) -> list[str]:
        """Listed countries (not XWL); COAL_SPEC 12.2: CZE is dropped where CSK has a production value."""
        cs = set(self.countries_by_series_year.get((series, year), [])) - {"XWL"}
        if series == "coal_production_t" and "CSK" in cs:
            cs.discard("CZE")
        return sorted(cs)

    def dropped_czech(self, year: int) -> bool:
        cs = self.countries_by_series_year.get(("coal_production_t", year), [])
        return "CSK" in cs and "CZE" in cs

    # ---- factors ----------------------------------------------------------
    def select(self, year: int, region: str, **match: str) -> dict:
        cands = [
            f for f in self.factors
            if int(f["year_from"]) <= year <= int(f["year_to"])
            and f["region"] in (region, "XWL")
            and all(f[k] == v for k, v in match.items())
        ]
        exact_rows = [f for f in cands if f["region"] == region]
        pool = exact_rows if exact_rows else cands
        if len(pool) != 1:
            raise LookupError(f"oracle select: {len(pool)} candidates for {year} {region} {match}")
        return pool[0]

    @staticmethod
    def fb(f: dict) -> B:
        return B(float(f["value_low"]), float(f["value_central"]), float(f["value_high"]))

    def sources_of(self, *factor_rows: dict) -> set[str]:
        out: set[str] = set()
        for f in factor_rows:
            out |= set(f["source_ids"].split(";"))
        return out

    # ---- power-station chain ------------------------------------------------
    def ash(self, y: int) -> tuple[B, B, B]:
        tot = self.a("coal_ash_power_t", y, "XWL")
        fly = self.a("coal_fly_ash_t", y, "XWL")
        return tot, fly, cdiff(tot, fly)  # COAL_SPEC 12.1: A_bot is a correlated difference

    def conc(self, y: int, g: str, residue: str) -> dict:
        return self.select(y, "XWL", stage="combustion_power", group=g, residue_type=residue, tier="", route="")

    def F(self, y: int, g: str) -> tuple[B, dict]:
        f = self.conc(y, g, "coal_fly_ash")
        return prod(self.a("coal_fly_ash_t", y, "XWL"), self.fb(f)), f

    def Bk(self, y: int, g: str) -> tuple[B, dict]:
        f = self.conc(y, g, "coal_bottom_ash")
        _, _, bot = self.ash(y)
        return prod(bot, self.fb(f)), f

    def base_fraction(self, y: int) -> dict:
        return self.select(y, "XWL", stage="combustion_power", tier="liberated", route="air_stack", group="")

    def enrichment(self, y: int, g: str) -> dict:
        return self.select(y, "XWL", stage="combustion_power", tier="liberated", route="air_stack", group=g)

    def share(self, y: int, tier: str) -> dict:
        return self.select(y, "XWL", stage="combustion_power", tier=tier, group="", residue_type="", route="")

    def stack_variants(self, y: int, g: str) -> list[B]:
        """Uncapped stack release under the two sum conventions (the spec is silent on F+B)."""
        F, _ = self.F(y, g)
        Bb, _ = self.Bk(y, g)
        p = self.fb(self.base_fraction(y))
        e = self.fb(self.enrichment(y, g))
        out = []
        for summed in (sum_independent([F, Bb]), sum_correlated([F, Bb])):
            out.append(prod(p, e, summed))
        return out

    def stack(self, y: int, g: str) -> B:
        """Capped stack release with F+B summed as fully correlated (COAL_SPEC 11.3)."""
        F, _ = self.F(y, g)
        Bb, _ = self.Bk(y, g)
        p = self.fb(self.base_fraction(y))
        e = self.fb(self.enrichment(y, g))
        return bound_min(prod(p, e, sum_correlated([F, Bb])), F)

    # ---- non-power chain ------------------------------------------------------
    def nonpower_coal(self, y: int) -> tuple[B, bool]:
        cons = self.a("coal_consumption_t", y, "XWL")
        if self.has("coal_ash_power_t", y, "XWL"):
            power_coal = scale(self.a("coal_ash_power_t", y, "XWL"), 1.0 / POWER_COAL_ASH_YIELD)
        else:
            power_coal = exact(0.0)
        raw = cons.central - power_coal.central
        return diff(cons, power_coal), raw < 0

    def np_factor(self, y: int, g: str) -> dict:
        return self.select(y, "XWL", stage="combustion_nonpower", group=g, tier="", residue_type="", route="")

    def N(self, y: int, g: str) -> tuple[B, dict]:
        cnp, _ = self.nonpower_coal(y)
        f = self.np_factor(y, g)
        return prod(cnp, self.fb(f)), f

    def household_share(self, y: int) -> dict:
        return self.select(y, "XWL", stage="combustion_nonpower", tier="dispersed",
                           residue_type="coal_domestic_ash", group="", route="")

    def smoke_fraction(self, y: int) -> dict:
        return self.select(y, "XWL", stage="combustion_nonpower", tier="liberated",
                           route="air_stack", group="", residue_type="")

    def radon_factor(self, y: int, group: str) -> dict:
        return self.select(y, "XWL", stage="combustion_power", group=group)
