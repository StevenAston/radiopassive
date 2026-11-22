"""D76 staging generator (proposal only; nothing is written under data/ or pipeline/).

Run from the repository root:  python research/wind_solar/build_d76_staging.py
Reads data/ and import/-derived constants below; writes build/d76_staging/ only, and prints the
impact summary used in research/wind_solar/d76_proposal.md. Standard library only, deterministic.

Three changes (research/wind_solar/d76_proposal.md):
  1. steel_bf_route_share -> steel_hot_metal_ratio = prod_pig_iron / prod_steel (XWL), every year;
     steel (ST) factor rows re-expressed per tonne of hot metal.
  2. prod_pig_iron / prod_steel additions from worldsteel, World Steel in Figures 2026 (2024-25) and
     Steel Statistical Yearbook 2005 (GBR pig iron 1995-2004, for benchmark B2).
  3. u_production_od 2024-25 from BHP reported payable uranium (FY2024 3,603 t; FY2025 3,154 t).
"""

from __future__ import annotations

import csv
import gzip
import io
import math
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "build" / "d76_staging"

S_WSIF = "S0861"  # worldsteel, World Steel in Figures 2026 (check for an id collision before applying)
S_SSY = "S0862"  # worldsteel, Steel Statistical Yearbook 2005
S_BHP25 = "S0863"  # BHP Annual Report 2025 (FY2024, FY2025 production)
S_BHP26 = "S0864"  # BHP Operational Review for the year ended 30 June 2026

NEW_SOURCES = [
    [S_WSIF, "worldsteel 2026, World Steel in Figures",
     "World Steel Association (2026). World Steel in Figures 2026. worldsteel, Brussels. Read: crude steel by "
     "country 2024-25 and by process 2025 (oxygen / electric / other, pp. 8-10), pig iron by country 2024-25 "
     "(p. 18), direct reduced iron 2021-25 (p. 19). Local copy import/World-Steel-in-Figures-2026.pdf.",
     "https://worldsteel.org/data/", "", "2026", "grey", "5", "open", "unknown",
     "READ (pdftotext -layout of the local PDF, 2026-11-22). 2025 values marked 'e' are worldsteel estimates. "
     "Industry association compilation; type grey (rank 5) as S0421."],
    [S_SSY, "worldsteel 2005, Steel Statistical Yearbook",
     "International Iron and Steel Institute (2005). Steel Statistical Yearbook 2005. IISI Committee on "
     "Economic Studies, Brussels. Table 1 Total production of pig iron 1995-2004; crude steel by country and "
     "by process (oxygen, electric) 1995-2004.",
     "https://worldsteel.org/wp-content/uploads/Steel-Statistical-Yearbook-2005.pdf", "", "2005", "grey", "5",
     "open", "unknown",
     "READ (downloaded 2026-11-22, pdftotext). United Kingdom 1999: pig iron 12,139 kt, crude steel 16,298 kt, "
     "oxygen 12,633 kt (77.5 percent), electric 3,662 kt. Used for GBR prod_pig_iron 1995-2004 (benchmark B2)."],
    [S_BHP25, "BHP Annual Report 2025",
     "BHP Group Limited (2025). Annual Report 2025 (released 19 August 2025). Section 4 Production: Copper "
     "South Australia cathode and payable uranium, years ended 30 June 2023-2025.",
     "", "", "2025", "grey", "5", "open", "unknown",
     "READ (local copy import/250819_bhpannualreport2025.pdf, p. 202). Uranium, payable metal in concentrate "
     "(t): FY2025 3,154; FY2024 3,603; FY2023 3,406. Cathode (Olympic Dam refinery): FY2025 214.0, FY2024 215.7, "
     "FY2023 212.5 kt. Unit of uranium not stated; treated as U3O8 (NUCLEAR_SPEC 14.2)."],
    [S_BHP26, "BHP Operational Review FY2026",
     "BHP Group Limited (2026). Operational Review for the year ended 30 June 2026 (16 July 2026).",
     "", "", "2026", "grey", "5", "open", "unknown",
     "READ (local copy import/260716_BHPOperationalReviewfortheyearended30June2026.pdf). Olympic Dam: payable "
     "uranium FY2026 3,647 t, FY2025 3,154 t; copper cathode (ER and EW) FY2026 221.3, FY2025 214.0 kt; "
     "payable metal in concentrate transferred to Olympic Dam from Prominent Hill/Carrapateena FY2026 9.9, "
     "FY2025 12.0 kt Cu."],
]

# World Steel in Figures 2026 (t; 'e' = worldsteel estimate). Pig iron p. 18; crude steel pp. 8-10.
WSIF_PIG = {  # country: (2024, 2025, 2025 estimated?)
    "XWL": (1293.4, 1271.2, False), "GBR": (3.0, 1.6, False), "BRA": (26.5, 26.3, False),
    "CAN": (5.8, 5.7, False), "CHN": (851.7, 836.0, False), "DEU": (24.3, 21.9, False),
    "IND": (90.0, 95.6, False), "IRN": (3.6, 3.7, True), "ITA": (2.0, 2.0, True), "JPN": (61.0, 58.5, False),
    "KOR": (44.2, 43.7, False), "MEX": (0.5, 0.5, False), "RUS": (51.2, 50.4, False), "TUR": (10.2, 9.7, False),
    "TWN": (14.9, 9.4, False), "UKR": (7.1, 7.9, False), "USA": (20.5, 21.4, True),
}
WSIF_STEEL = {  # country: (2024, 2025, 2025 estimated?)
    "XWL": (1886.8, 1848.9, True), "GBR": (4.0, 2.6, False), "BRA": (33.9, 33.4, False),
    "CAN": (12.3, 11.5, False), "CHN": (1005.1, 960.8, True), "DEU": (37.3, 34.1, False),
    "IND": (149.4, 164.9, False), "IRN": (31.4, 32.0, True), "ITA": (20.0, 20.7, True), "JPN": (84.0, 80.7, False),
    "KOR": (63.6, 62.2, False), "MEX": (14.3, 13.5, False), "RUS": (71.0, 67.9, True), "TUR": (36.9, 38.1, False),
    "TWN": (19.2, 17.2, False), "UKR": (7.6, 7.4, False), "USA": (79.5, 81.9, True), "VNM": (22.0, 24.7, False),
}
# Steel Statistical Yearbook 2005, Table 1 (kt): United Kingdom pig iron.
SSY_GBR_PIG = {1995: 12236, 1996: 12830, 1997: 13054, 1998: 12746, 1999: 12139, 2000: 10890, 2001: 9870,
               2002: 8561, 2003: 10228, 2004: 10180}
SSY_GBR_STEEL_1999 = 16298  # kt, same yearbook (cross-check of the repository's GBR prod_steel 1999)

# BHP payable uranium (t, treated as U3O8): FY -> calendar year y (FY ending June y), NUCLEAR_SPEC 14.2.
BHP_U = {2024: (3603, S_BHP25, "FY2024, BHP Annual Report 2025 p. 202"),
         2025: (3154, S_BHP26, "FY2025, BHP Operational Review FY2026 (also Annual Report 2025 p. 202)")}
U3O8_TO_U = 0.848
ISL_XWL_2020_25 = (0.12, 0.165, 0.22)  # nuclear:1702 (low, central, high)

# Source pig-iron/steel ratios (t hot metal per t crude steel) used to re-express the ST rows.
R_W48 = 3.7 / 3.9  # NRPB-W48 Scunthorpe 1999: 3.7e9 kg liquid iron, 3.9e9 kg liquid steel
R_DEFAULT = 0.9  # flagged assumption where a source gives no ratio (task instruction)


def sf(x: float, n: int = 3) -> float:
    if x == 0:
        return 0.0
    return round(x, -int(math.floor(math.log10(abs(x)))) + (n - 1))


def g(x: float) -> str:
    return f"{x:.6g}"


def read_csv(p: Path):
    with p.open(newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        return [row for row in r]


def write_csv(p: Path, rows) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerows(rows)
    p.write_text(buf.getvalue(), encoding="utf-8")


def raw_lines(p: Path) -> list[str]:
    return p.read_text(encoding="utf-8").splitlines(keepends=True)


def to_line(fields) -> str:
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerow(fields)
    return buf.getvalue()


# ---------------------------------------------------------------------------------------------
# 2. production rows
# ---------------------------------------------------------------------------------------------
def production_rows():
    hdr_note = "D76 proposal. worldsteel, World Steel in Figures 2026"
    out = []
    for series, table in (("prod_pig_iron", WSIF_PIG), ("prod_steel", WSIF_STEEL)):
        page = "p. 18 pig iron" if series == "prod_pig_iron" else "pp. 8-10 crude steel"
        for c, (v24, v25, est) in table.items():
            years = [(2025, v25, est)]
            if c == "GBR":
                years.insert(0, (2024, v24, False))
            for y, v, e in years:
                tol = 0.05 if (e or c == "XWL") else 0.03
                t = v * 1e6
                why = ("2025 value marked 'e' (worldsteel estimate)" if e else "reported value")
                if c == "XWL":
                    why = ("world total" + ("; includes worldsteel estimates for several producers" if y == 2025 else ""))
                out.append([series, str(y), c, g(t * (1 - tol)), g(t), g(t * (1 + tol)), "t", "false",
                            "compiled", S_WSIF,
                            f"{hdr_note} ({page}), {v} Mt; {why}; +-{int(tol * 100)} percent. "
                            "Series break: earlier years are USGS DS140 / OWID (S0831, S0807)."])
    for y, kt in SSY_GBR_PIG.items():
        t = kt * 1e3
        out.append(["prod_pig_iron", str(y), "GBR", g(t * 0.97), g(t), g(t * 1.03), "t", "false", "compiled", S_SSY,
                    f"D76 proposal. IISI Steel Statistical Yearbook 2005, Table 1 Total production of pig iron, "
                    f"United Kingdom {kt} kt; +-3 percent. For benchmark B2 (GBR hot-metal ratio 1999)."])
    return out


# ---------------------------------------------------------------------------------------------
# 1. hot-metal ratio series and ST factor rows
# ---------------------------------------------------------------------------------------------
def load_prod(extra):
    d = {}
    src = {}
    for row in csv.DictReader((ROOT / "data/activity/commodity_production.csv").open(encoding="utf-8")):
        if row["series"] in ("prod_pig_iron", "prod_steel"):
            d[(row["series"], row["country"], int(row["year"]))] = float(row["value_central"])
            src[(row["series"], row["country"], int(row["year"]))] = row["source_ids"]
    for r in extra:
        k = (r[0], r[2], int(r[1]))
        if k not in d:
            d[k] = float(r[4])
            src[k] = r[9]
    return d, src


def hot_metal_rows(prod, src):
    rows = []
    h = {}
    for y in range(1950, 2026):
        p, s = prod[("prod_pig_iron", "XWL", y)], prod[("prod_steel", "XWL", y)]
        v = p / s
        h[y] = v
        ids = sorted(set(src[("prod_pig_iron", "XWL", y)].split(";")) | set(src[("prod_steel", "XWL", y)].split(";")))
        rows.append(["steel_hot_metal_ratio", str(y), "XWL", g(v), g(v), g(v), "1", "false", "compiled",
                     ";".join(ids),
                     f"Hot-metal ratio (D76): world prod_pig_iron / prod_steel at central = {p / 1e6:.6g} / "
                     f"{s / 1e6:.6g} Mt, tonnes of blast-furnace hot metal (pig iron) per tonne of crude steel, "
                     "all routes (integrated BF-BOF, open hearth, and pig iron charged to EAFs and foundries). "
                     "Measured ratio, not a placeholder; low = central = high (exact scalar, WIND_SOLAR_SPEC 13.19). "
                     "Replaces steel_bf_route_share. DRI-EAF and scrap-EAF steel carry no ironmaking residue "
                     "by construction."])
    return rows, h


HEAD_NOTE_OLD = ("Per tonne of BF-BOF crude steel (multiply by the BF-BOF share of steel; EAF scrap route carries "
                 "little ore: OQ-STEEL-1).")
HEAD_NOTE_NEW = ("Per tonne of hot metal (blast-furnace iron, integrated route; driver steel_hot_metal_ratio = "
                 "prod_pig_iron / prod_steel, D76). Scrap-EAF and DRI-EAF steel carry no ironmaking residue here "
                 "(OQ-STEEL-1).")


def st_new_values(old):
    """old: dict factor_id -> (low, central, high, notes). Returns factor_id -> (low, c, high, notes)."""
    new = {}
    # Stack Pb-210 (commodity:0031). Components per t hot metal.
    scun_pb = 6.2e9 / 3.7e6
    ijm_pb = 54e9 / 5.2e6
    uns_pb = 1.0e4 / R_DEFAULT
    tot_c = math.exp((math.log(scun_pb) + math.log(ijm_pb) + math.log(uns_pb)) / 3)
    tot_l, tot_h = scun_pb, 1.5 * uns_pb
    new["commodity:0031"] = (sf(tot_l * 0.60), sf(tot_c * 0.85), sf(tot_h * 0.95), (
        f"non-fuel process (own_residue). {HEAD_NOTE_NEW} Sinter plant + blast furnace stack. Total observed per t "
        f"hot metal: UK Scunthorpe {scun_pb:.4g} (NRPB-W48 Table 3: 6.2e9 Bq/a over 3.7 Mt liquid iron; 3.9 Mt "
        f"steel), IJmuiden {ijm_pb:.4g} (RP-135 Table 15: sinter plant 54 GBq/a over 5.2 Mt primary iron), "
        f"UNSCEAR 2000 1.0e4 per t steel (seed) / 0.9 = {uns_pb:.4g} [ratio 0.9 ASSUMED, flagged]. Total "
        f"low/central/high {tot_l:.3g}/{tot_c:.3g}/{tot_h:.3g} (central geometric mean of three; high 1.5 x the "
        "largest, as before). Own = total x (1 - f_fuel) with f_fuel 0.05/0.15/0.40 (sinter coke breeze and BF "
        "coal); low = total_low x 0.60, high = total_high x 0.95. The removed part is in the coal stream "
        "(coal:0029-0039). REVISION D76: re-expressed from per t BF-BOF steel to per t hot metal; IJmuiden was "
        "already per t iron (the D74 note said steel)."))
    # Stack Po-210 (0032).
    ena_po = 4.0e9 / 3.7e6
    w48_po = 3.96e10 / 3.7e6
    ijm_po = 84e9 / 5.2e6
    uns_po = 1.7e4 / R_DEFAULT
    c_po = math.exp((math.log(w48_po) + math.log(ijm_po) + math.log(uns_po)) / 3)
    h_po = 2.5e4 * (uns_po / 1.7e4)
    new["commodity:0032"] = (sf(ena_po * 0.60), sf(c_po * 0.85), sf(h_po * 0.95), (
        f"non-fuel process (own_residue). {HEAD_NOTE_NEW} Total observed per t hot metal: {ena_po:.3g} (low: ENA "
        f"N3_6.1 Scunthorpe Po-210 4.0e9 Bq/a over 3.7 Mt iron), {w48_po:.4g} (NRPB-W48: 3.96e10 Bq/a over 3.7 Mt "
        f"iron), {ijm_po:.4g} (IJmuiden sinter plant 84 GBq/a over 5.2 Mt primary iron), {uns_po:.4g} (UNSCEAR "
        f"2000 1.7e4 per t steel / 0.9, ASSUMED ratio, flagged): total {ena_po:.3g}/{c_po:.4g}/{h_po:.4g} (central "
        "geometric mean of W48, IJmuiden and UNSCEAR; high scaled with the UNSCEAR value). CONTRADICTION: the two "
        "NRPB documents differ by 10x for Scunthorpe Po-210; the later W48 value is used for the centre. Own = "
        "total x (1 - f_fuel), f_fuel 0.05/0.15/0.40. REVISION D76: per t hot metal."))
    # Radon (0033): 2.4e4 Bq/t ore x 1.4 t ore per t BF-BOF steel (WSA) / 0.9.
    rn_c = 2.4e4 * 1.4 / R_DEFAULT
    new["commodity:0033"] = (sf(rn_c / 2), sf(rn_c), sf(rn_c * 2), (
        f"non-fuel process (own_residue). {HEAD_NOTE_NEW} UNSCEAR 2000 Table 28 typical integrated plant: Rn-222 "
        "180 GBq/a per 7500 kt/a ore = 2.4e4 Bq/t ore x 1.4 t ore per t BF-BOF steel (WSA, S0421) / 0.9 t hot metal "
        "per t steel [ASSUMED, flagged] = 1.56 t ore per t hot metal (cross-check NRPB-W48 Scunthorpe 1999: 6 Mt ore "
        "/ 3.7 Mt iron = 1.62). +-2x judgement. Read from a page image in Task 1.1 (unscear_notes.md); assumes the "
        "throughput is iron ore. REVISION D76: per t hot metal."))
    # Dust Pb-210 (0054) and Po-210 (0055).
    uk_dust = 5.7e7 / 3.7e6  # kg per t hot metal
    pb_uk = uk_dust * 900
    pb_c = math.sqrt(pb_uk * 16000)
    new["commodity:0054"] = (sf(5000 / R_W48), sf(pb_c), 40000.0, (
        f"non-fuel process (own_residue). {HEAD_NOTE_NEW} BF, sinter and BOS gas-cleaning dust and sludge to "
        f"lagoons and landfill. UK: {uk_dust:.1f} kg per t hot metal (5.7e7 kg/a over 3.7 Mt iron, NRPB-W48; was "
        f"14.6 kg per t steel) x 900 Bq/kg = {pb_uk:.3g}; RP-135: about 2 kt dust per Mt primary iron at 15-25 Bq/g "
        "(IJmuiden) = 3-5e4, UK 8 Bq/g = 1.6e4 (already per t iron). Central = geometric mean of the UK landfill and "
        "RP-135 UK values; low 5,000 [judgement] x 3.9/3.7; high 4.0e4 unchanged (per t iron). Some dust is "
        "recycled to the sinter strand or sold to Zn recovery (Waelz): not modelled (OQ-STEEL-3). REVISION D76: "
        "per t hot metal; only the per-t-steel components converted."))
    po_uk = uk_dust * 290
    new["commodity:0055"] = (sf(1000 / R_W48), sf(po_uk), 15000.0, (
        f"non-fuel process (own_residue). {HEAD_NOTE_NEW} As the Pb-210 dust row: UK landfill 290 Bq/kg x "
        f"{uk_dust:.1f} kg per t hot metal = {po_uk:.3g}; RP-135 'a few Bq/g' BF dust x about 2 kg per t iron "
        "(high, unchanged). Low [judgement] x 3.9/3.7. REVISION D76: per t hot metal."))
    return new, {"scun_pb": scun_pb, "ijm_pb": ijm_pb, "uns_pb": uns_pb, "pb_tot_c": tot_c,
                 "w48_po": w48_po, "ijm_po": ijm_po, "uns_po": uns_po, "po_tot_c": c_po}


MEMBER_RE = re.compile(r"^\[(\S+) member of the (\S+) block, ratio ([0-9.]+):")


def factor_rows():
    lines = raw_lines(ROOT / "data/reference/commodity_factors.csv")
    hdr = next(csv.reader([lines[0]]))
    rows = [next(csv.reader([ln])) for ln in lines[1:]]
    ix = {k: i for i, k in enumerate(hdr)}
    old = {r[0]: (float(r[ix["value_low"]]), float(r[ix["value_central"]]), float(r[ix["value_high"]]),
                  r[ix["notes"]]) for r in rows if r[ix["commodity"]] == "steel"}
    explicit, comp = st_new_values(old)
    out_lines = [lines[0]]
    changes = []
    head_new = None
    for ln, r in zip(lines[1:], rows):
        if r[ix["commodity"]] != "steel":
            out_lines.append(ln)
            continue
        fid = r[0]
        lo, c, hi, notes = old[fid]
        m = MEMBER_RE.match(notes)
        res = r[ix["residue_type"]]
        if fid in explicit:
            nl, nc, nh, nn = explicit[fid]
            kind = "rebuilt"
        elif m is None:  # block head: slag (W48 ratio) or tailings (0.9)
            k = 1 / R_W48 if res == "smelter_slag" else 1 / R_DEFAULT
            nl, nc, nh = sf(lo * k), sf(c * k), sf(hi * k)
            basis = ("NRPB-W48 Scunthorpe own ratio 3.7/3.9 (slag 1.6 Mt over 3.7 Mt iron = 0.43 t slag per t hot "
                     "metal; BF + BOS slag)" if res == "smelter_slag"
                     else "ratio 0.9 t hot metal per t steel ASSUMED, flagged (the 1.4 t ore and the 0.1-1.5 t "
                          "tailings per t steel are per t BF-BOF steel)")
            nn = notes.replace(HEAD_NOTE_OLD, HEAD_NOTE_NEW).replace("Per t steel: slag 0.41 t/t",
                                                                     "Per t steel: slag 0.41 t/t (0.43 per t hot metal)")
            nn += f" REVISION D76: x {k:.4f} to per t hot metal, {basis}."
            head_new = (nl, nc, nh, (lo, c, hi))
            kind = f"x{k:.4f}"
        else:  # member: head x chain ratio
            ratio = float(m.group(3))
            hl, hc, hh, _ = head_new
            nl, nc, nh = sf(hl * ratio, 4), sf(hc * ratio, 4), sf(hh * ratio, 4)
            nn = notes + " REVISION D76: per t hot metal (head x ratio)."
            kind = f"member r={ratio}"
        r2 = list(r)
        r2[ix["value_low"]], r2[ix["value_central"]], r2[ix["value_high"]] = g(nl), g(nc), g(nh)
        r2[ix["notes"]] = nn
        out_lines.append(to_line(r2))
        changes.append((fid, r[ix["group"]], r[ix["tier"]], res or r[ix["route"]], (lo, c, hi), (nl, nc, nh), kind))
    return out_lines, changes, comp


# ---------------------------------------------------------------------------------------------
# 3. uranium
# ---------------------------------------------------------------------------------------------
def uranium_lines():
    lines = raw_lines(ROOT / "data/activity/uranium.csv")
    rows = [next(csv.reader([ln])) for ln in lines]
    P = {}
    for r in rows[1:]:
        if r[0] == "u_production" and r[2] == "AUS":
            P[int(r[1])] = tuple(float(x) for x in r[3:6])
    out = [lines[0]]
    report = []
    sl, sc, sh = ISL_XWL_2020_25
    for ln, r in zip(lines[1:], rows[1:]):
        if r[0] == "u_production_od" and int(r[1]) in BHP_U:
            y = int(r[1])
            t, sid, where = BHP_U[y]
            c = t * U3O8_TO_U
            lo, hi = c * 0.98, c * 1.02
            pl, pc, ph = P[y]
            cap = (pl * (1 - sh), pc * (1 - sc), ph * (1 - sl))
            vals = [min(lo, cap[0]), min(c, cap[1]), min(hi, cap[2])]
            clipped = [i for i, (v, w) in enumerate(zip(vals, (lo, c, hi))) if v != w]
            note = (f"D74(a); D76. Olympic Dam uranium, t U, BHP fiscal year ending June ascribed to the calendar "
                    f"year. Read: BHP payable uranium {t:,} t ({where}) treated as U3O8 x 0.848 = {c:.1f} t U; "
                    "+-2 percent.")
            if clipped:
                note += (" Low bound capped at the AUS conventional low P_l(1 - s_h) = "
                         f"{cap[0]:.2f} t U (NUCLEAR_SPEC 14.2 rule; the 2025 AUS u_production is extrapolated "
                         "with wide bounds).")
            r2 = list(r)
            r2[3:6] = [g(v) for v in vals]
            r2[8] = "compiled"
            r2[9] = f"S0407;{sid}" if sid == S_BHP25 else f"S0407;{S_BHP25};{sid}"
            r2[10] = note
            out.append(to_line(r2))
            report.append((y, tuple(float(x) for x in r[3:6]), tuple(vals), cap, clipped))
        else:
            out.append(ln)
    return out, report


# ---------------------------------------------------------------------------------------------
# impact (on the committed stream outputs; multiplicative per bound)
# ---------------------------------------------------------------------------------------------
def stream_rows(name):
    with gzip.open(ROOT / f"data/streams/{name}.csv.gz", "rt", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def impact(changes, h_new, bf_old):
    fmap = {fid: (o, n) for fid, _, _, _, o, n, _ in changes}
    rows = stream_rows("wind_solar")
    out = {}
    for y in (2010, 2020, 2024):
        tot = [0.0, 0.0, 0.0]
        st_old = [0.0, 0.0, 0.0]
        st_new = [0.0, 0.0, 0.0]
        by = defaultdict(lambda: [0.0, 0.0])
        for r in rows:
            if int(r["year"]) != y or r["allocation_variant"] != "default":
                continue
            v = [float(r["value_low"]), float(r["value_central"]), float(r["value_high"])]
            for i in range(3):
                tot[i] += v[i]
            if r["product"] == "steel":
                o, n = fmap[r["factor_ids"]]
                k = h_new[y] / bf_old[y]
                nv = [v[i] * k * (n[i] / o[i] if o[i] else 0) for i in range(3)]
                for i in range(3):
                    st_old[i] += v[i]
                    st_new[i] += nv[i]
                key = (r["tier"], r["residue_type"] or r["route"])
                by[key][0] += v[1]
                by[key][1] += nv[1]
        out[y] = (tot, st_old, st_new, dict(by))
    return out


def nuclear_f6(report):
    rows = stream_rows("nuclear")
    res = {}
    for y, old, new, cap, _ in report:
        f6 = [0.0, 0.0, 0.0]
        aus_tot = 0.0
        for r in rows:
            if int(r["year"]) != y or r["country"] != "AUS":
                continue
            if r["allocation_variant"] not in ("", "default"):
                continue
            aus_tot += float(r["value_central"])
            if "Olympic Dam carved out" in (r["notes"] or ""):
                for i, k in enumerate(("value_low", "value_central", "value_high")):
                    f6[i] += float(r[k])
        rem_old = cap[1] - old[1]
        rem_new = cap[1] - new[1]
        res[y] = (f6, rem_old, rem_new, aus_tot)
    return res


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    prod_new = production_rows()
    prod, src = load_prod(prod_new)

    # commodity_production.csv: existing lines unchanged, new rows appended.
    pl = raw_lines(ROOT / "data/activity/commodity_production.csv")
    existing = {(r[0], r[1], r[2]) for r in csv.reader(pl[1:])}
    add = [r for r in prod_new if (r[0], r[1], r[2]) not in existing]
    dup = [r[:3] for r in prod_new if (r[0], r[1], r[2]) in existing]
    (OUT / "data/activity").mkdir(parents=True, exist_ok=True)
    (OUT / "data/activity/commodity_production.csv").write_text("".join(pl + [to_line(r) for r in add]),
                                                                  encoding="utf-8")

    # wind_solar_shares.csv: steel_bf_route_share rows replaced in place.
    hm_rows, h = hot_metal_rows(prod, src)
    sl = raw_lines(ROOT / "data/activity/wind_solar_shares.csv")
    bf_old = {}
    out, it = [sl[0]], iter(hm_rows)
    for ln in sl[1:]:
        r = next(csv.reader([ln]))
        if r[0] == "steel_bf_route_share":
            bf_old[int(r[1])] = float(r[4])
            out.append(to_line(next(it)))
        else:
            out.append(ln)
    (OUT / "data/activity/wind_solar_shares.csv").write_text("".join(out), encoding="utf-8")

    fl, changes, comp = factor_rows()
    (OUT / "data/reference").mkdir(parents=True, exist_ok=True)
    (OUT / "data/reference/commodity_factors.csv").write_text("".join(fl), encoding="utf-8")

    # commodity_fuel_inputs.csv (reference only, D22): steel coal re-expressed per t hot metal (/0.9, flagged).
    fil = raw_lines(ROOT / "data/reference/commodity_fuel_inputs.csv")
    fout = [fil[0]]
    for ln in fil[1:]:
        r = next(csv.reader([ln]))
        if r[0] == "steel" and r[1] == "coal":
            r[6:9] = [g(sf(float(x) / R_DEFAULT)) for x in r[6:9]]
            r[12] = ("Coking coal and PCI as coal, per t hot metal (blast-furnace iron; D76: the 0.6/0.8/1.0 t per t "
                     "BF-BOF crude steel of WSA / 0.9 t hot metal per t steel, ASSUMED ratio, flagged). Was draft "
                     "embedded_fuel rows steel U238+/Th232 (D74(d)). Reference only, lifecycle view (D22).")
            ln = to_line(r)
        fout.append(ln)
    (OUT / "data/reference/commodity_fuel_inputs.csv").write_text("".join(fout), encoding="utf-8")

    ul, ureport = uranium_lines()
    (OUT / "data/activity/uranium.csv").write_text("".join(ul), encoding="utf-8")

    srcl = raw_lines(ROOT / "data/sources.csv")
    have = {ln.split(",", 1)[0] for ln in srcl}
    clash = [s[0] for s in NEW_SOURCES if s[0] in have]
    if clash:
        raise SystemExit(f"source id clash: {clash}")
    (OUT / "data/sources.csv").write_text("".join(srcl + [to_line(s) for s in NEW_SOURCES]), encoding="utf-8")

    # ---- report ----
    print(f"production rows added: {len(add)}; skipped as existing: {dup}")
    print("h (XWL):", {y: round(h[y], 4) for y in (1950, 1970, 1982, 1990, 2000, 2010, 2020, 2024, 2025)})
    print("h/bf_old:", {y: round(h[y] / bf_old[y], 3) for y in (1982, 1990, 2010, 2020, 2024, 2025)})
    print("components:", {k: round(v, 1) for k, v in comp.items()})
    for fid, grp, tier, rr, o, n, kind in changes:
        print(f"  {fid} {grp:7s} {tier:10s} {rr:24s} {o} -> {n}  [{kind}]  ratio c {n[1] / o[1]:.3f}")
    imp = impact(changes, h, bf_old)
    for y, (tot, so, sn, by) in imp.items():
        print(f"{y}: stream total default (l/c/h) {[f'{x:.3e}' for x in tot]}; ST old {[f'{x:.3e}' for x in so]} "
              f"-> new {[f'{x:.3e}' for x in sn]}; ST share of stream {so[1] / tot[1]:.3%} -> "
              f"{sn[1] / (tot[1] - so[1] + sn[1]):.3%}; stream change {(sn[1] - so[1]) / tot[1]:+.3%}")
        for k, (a, b) in sorted(by.items()):
            print(f"     {k}: {a:.3e} -> {b:.3e} ({b / a - 1:+.1%})")
    # B2
    t99 = prod[("prod_steel", "GBR", 1999)]
    h_gbr = prod[("prod_pig_iron", "GBR", 1999)] / t99
    h_gbr_ssy = SSY_GBR_PIG[1999] / SSY_GBR_STEEL_1999
    f = {fid: n for fid, _, _, _, _, n, _ in changes}
    fo = {fid: o for fid, _, _, _, o, _, _ in changes}
    for lab, hh in (("GBR (repo prod_pig_iron/prod_steel)", h_gbr), ("GBR (SSY 2005 only)", h_gbr_ssy),
                    ("world 1999", h[1999])):
        pb = t99 * hh * f["commodity:0031"][1]
        po = t99 * hh * f["commodity:0032"][1]
        print(f"B2 {lab}: h={hh:.4f} HM={t99 * hh / 1e6:.3f} Mt; Pb {pb:.3e} ({pb / 2.1e10:.2f}); "
              f"Po {po:.3e} ({po / 1.35e11:.2f}); Pb range {t99 * hh * f['commodity:0031'][0]:.2e}-"
              f"{t99 * hh * f['commodity:0031'][2]:.2e}; Po range {t99 * hh * f['commodity:0032'][0]:.2e}-"
              f"{t99 * hh * f['commodity:0032'][2]:.2e}")
    print(f"B2 old: Pb {t99 * bf_old[1999] * fo['commodity:0031'][1]:.3e} Po {t99 * bf_old[1999] * fo['commodity:0032'][1]:.3e}")
    for y, old, new, cap, clipped in ureport:
        print(f"u_production_od {y}: old {old} -> new {tuple(round(v, 2) for v in new)}; cap {tuple(round(v, 2) for v in cap)}; clipped idx {clipped}")
    for y, (f6, ro, rn, aus) in nuclear_f6(ureport).items():
        print(f"F6 AUS {y}: committed sum (l/c/h) {[f'{x:.3e}' for x in f6]}; remainder central {ro:.1f} -> {rn:.1f} t U "
              f"(x{rn / ro:.3f}); F6 central -> {f6[1] * rn / ro:.3e}; AUS nuclear total default central {aus:.3e}")


if __name__ == "__main__":
    main()
