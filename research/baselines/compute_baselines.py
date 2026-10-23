#!/usr/bin/env python3
"""Task 1.7 - reproduce every calculated value in data/baselines.csv.

stdlib only.  Reads data/reference/nuclides.csv and groups.csv for decay constants and
mean emitted energies (antineutrino excluded).  All other inputs are listed in INPUTS
below, each with the source ID that supplies it (research/baselines/sources_task17.csv,
or S9005 for IAEA LiveChart abundances).

Usage (from /mnt/user-data/outputs):
    python3 research/baselines/compute_baselines.py            # compare with data/baselines.csv
    python3 research/baselines/compute_baselines.py --write    # (re)write data/baselines.csv
    python3 research/baselines/compute_baselines.py --print    # print the table only

Bounds: each input carries (low, central, high), read as ~5th/50th/95th (METHODS 11.1);
products are combined by log-space quadrature, separately up and down.  Where the source
gives no uncertainty the bound is a stated judgement (flagged in derivations.md).
"""
import csv
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NUCL = ROOT / "data/reference/nuclides.csv"
GROUPS = ROOT / "data/reference/groups.csv"
OUT = ROOT / "data/baselines.csv"

# ---------------------------------------------------------------- constants
N_A = 6.02214076e23          # 1/mol (SI 2019, exact)
MEV_J = 1.602176634e-13      # J per MeV (exact)
YEAR_S = 3.15576e7           # Julian year, s (METHODS 3.3)
CI_BQ = 3.7e10               # Bq per Ci (exact)
M_K, M_U, M_TH = 39.0983, 238.02891, 232.0377   # g/mol (IUPAC standard atomic weights)

# ---------------------------------------------------------------- inputs (low, central, high)
INPUTS = {
    # S0602 Huang 2013: BSE Th/U ~ 3.9, K/U ~ 14000 (mass), total BSE radiogenic power 20.1 TW
    "bse_total_W": (None, 20.1e12, None),
    "th_over_u": 3.9,
    "k_over_u": 14000.0,
    # S0601 KamLAND 2022 whole-Earth total ~14.6 TW (Th/U fixed); S0600 Borexino 2020 whole-Earth total 38.2 (+13.6/-12.7) TW,
    # which already includes mantle K-40 (18 % assumption) and 8.1 TW lithosphere -- do not add K again
    "geo_low_W": 14.6e12,
    "geo_high_W": 38.2e12,              # Borexino 2020 total radiogenic heat (incl. K-40)
    # ocean: S0608 volume, S0610 K, S9005 abundance
    "ocean_vol_m3": (1.325e18, 1.332e18, 1.340e18),
    "sw_density": (1025.0, 1028.0, 1031.0),                  # kg/m3, TEOS-10 style constant (judgement bounds)
    "sw_K_mmol_kg": (10.21 * 34.5 / 35.0, 10.21, 10.21 * 1.005),  # at S = 35 (S0609/S0610); low scaled to S = 34.5
    "K40_abund": (0.000117 - 1.645e-6, 0.000117, 0.000117 + 1.645e-6),   # 0.0117(1) % ; 1 sigma = 1e-6
    "sw_U_nmol_kg": (13.0, 13.9, 14.8),                       # S0612 central; bounds judgement (+-6.5 %)
    "U238_abund": 0.992742,                                  # S9005 (99.2742 %)
    # land
    "land_total_m2": 148.94e12, "antarctica_m2": 14.2e12, "greenland_m2": 2.166086e12,   # S0613
    # radon: S0604 flux 0.016 Bq/m2/s; S0607 21.3 mBq/m2/s; S0606 totals in GCi/a
    "rn_flux_unscear": 0.016, "rn_flux_hirao": 0.0213,
    "rn_total_GCi_a": {"JA97": 1.94, "ZK11": 2.11, "ZKC": 2.22, "SW98": 2.41},
    # cosmogenic (S0604 Table 4), PBq/a and PBq, bounds judgement +-30 %
    "h3_prod_PBq_a": 72.0, "h3_inv_PBq": 1275.0, "c14_prod_PBq_a": 1.54, "c14_inv_PBq": 12750.0,
    "cosmo_rel": (0.7, 1.3),
    # S0614 Kovaltsov et al. 2012: modern C-14 production 1.64 atoms/cm2/s vs UNSCEAR 2.5 -> C-14 low bound
    "c14_rel": (1.64 / 2.5, 1.3),
    # fallout (S0605 Table 9, 'global release', PBq); bounds judgement
    "fallout_PBq": {"H3": 186000.0, "C14": 213.0, "Sr90": 622.0, "Cs137": 948.0, "I131": 675000.0},
    "fallout_rel": {"H3": (0.5, 1.5), "C14": (0.5, 1.5), "Sr90": (0.8, 1.2), "Cs137": (0.8, 1.2), "I131": (0.7, 1.3)},
    # soil (S0604 Table 6 medians, Bq/kg); bulk density kg/m3 (UNSCEAR uses 1.3 dry / 1.6 wet g/cm3)
    "soil_Bq_kg": {"K40": 400.0, "U238": 35.0, "Th232": 30.0},
    "soil_rel": (0.7, 1.3),
    "soil_density": (1300.0, 1500.0, 1700.0), "soil_depth_m": 1.0,
    # crust (S0611 upper continental crust U 2.7 +- 0.6 ppm); density judgement
    "crust_U_ppm": (2.7 - 1.645 * 0.6, 2.7, 2.7 + 1.645 * 0.6),
    "crust_density": (2500.0, 2700.0, 2900.0), "crust_depth_m": 1000.0,
}


# ---------------------------------------------------------------- helpers
def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


NUC = {r["nuclide"]: r for r in read_csv(NUCL)}
GRP = {r["group"]: r for r in read_csv(GROUPS)}


def lam_s(nuclide):                      # decay constant, 1/s
    return float(NUC[nuclide]["lambda_per_a"]) / YEAR_S


def e_head_J(group):                     # mean emitted energy per head decay, J (no antineutrino)
    return float(GRP[group]["e_per_head_decay_mev"]) * MEV_J


def chain_E_MeV(groups):
    return sum(float(GRP[g]["e_per_head_decay_mev"]) for g in groups)


def prod(*factors):
    """Product of (low, central, high) triples with log-quadrature bounds (METHODS 11.1)."""
    c = 1.0
    up = dn = 0.0
    for lo, ce, hi in factors:
        c *= ce
        up += math.log(hi / ce) ** 2
        dn += math.log(ce / lo) ** 2
    return c * math.exp(-math.sqrt(dn)), c, c * math.exp(math.sqrt(up))


def const(x):
    return (x, x, x)


def scale(t, k):
    return tuple(k * v for v in t)


def rel(c, r):
    return (c * r[0], c, c * r[1])


# ---------------------------------------------------------------- derived constants
E_U238_CHAIN = chain_E_MeV(["U238+", "U234", "Th230", "Ra226+", "Pb210+", "Po210"])
E_U235_CHAIN = chain_E_MeV(["U235+", "Pa231", "Ac227+"])
E_TH232_CHAIN = chain_E_MeV(["Th232", "Ra228+", "Th228+"])
E_K40 = float(GRP["K40"]["e_per_head_decay_mev"])

U235_FRAC = 1.0 - INPUTS["U238_abund"] - 0.000054        # U-234 0.0054 % (S9005 ground-state data)


def atoms_per_kg(molar_g, frac=1.0):
    return 1000.0 / molar_g * N_A * frac


# specific activities, Bq per kg of the element
A_K40 = lam_s("K-40") * atoms_per_kg(M_K, INPUTS["K40_abund"][1])
A_U238 = lam_s("U-238") * atoms_per_kg(M_U, INPUTS["U238_abund"])
A_TH232 = lam_s("Th-232") * atoms_per_kg(M_TH)
# specific radiogenic power, W per kg of the element
H_U = MEV_J * (lam_s("U-238") * atoms_per_kg(M_U, INPUTS["U238_abund"]) * E_U238_CHAIN
               + lam_s("U-235") * atoms_per_kg(M_U, U235_FRAC) * E_U235_CHAIN)
H_TH = MEV_J * A_TH232 * E_TH232_CHAIN
H_K = MEV_J * A_K40 * E_K40

LAND_ICEFREE = (INPUTS["land_total_m2"] - INPUTS["antarctica_m2"] - INPUTS["greenland_m2"])
LAND_T = (1.30e14, LAND_ICEFREE, INPUTS["land_total_m2"] - INPUTS["antarctica_m2"])


def build():
    rows = []

    def add(bid, name, quantity, group, year, t, unit, basis, deriv, src, notes):
        rows.append(dict(baseline_id=bid, name=name, quantity=quantity, group=group or "",
                         year="" if year is None else year,
                         value_low=t[0], value_central=t[1], value_high=t[2], unit=unit,
                         basis=basis, derivation=deriv, source_ids=src, notes=notes))

    # ---- B01-B04 radiogenic heat
    g_lo, g_hi = INPUTS["geo_low_W"], INPUTS["geo_high_W"]
    g_c = INPUTS["bse_total_W"][1]
    add("B01", "Earth radiogenic heat (U + Th + K), total", "power", None, None, (g_lo, g_c, g_hi), "W",
        "compiled",
        "Published geoneutrino/BSE totals: low KamLAND 2022 total 14.6 TW; central Huang 2013 BSE 20.1 TW; "
        "high Borexino 2020 total 38.2 TW (incl. mantle K-40). See derivations.md B1",
        "S0600;S0601;S0602;S0603",
        "Bounds span published central estimates, not a statistical 5th-95th interval. Surface heat loss 47 +- 2 TW (S0603).")
    share_u = H_U
    share_th = H_TH * INPUTS["th_over_u"]
    share_k = H_K * INPUTS["k_over_u"]
    tot = share_u + share_th + share_k
    for bid, nm, sh, grp in (("B02", "U-238 + U-235 series", share_u, None),
                             ("B03", "Th-232 series", share_th, None),
                             ("B04", "K-40", share_k, "K40")):
        f = sh / tot
        add(bid, f"Earth radiogenic heat from {nm} (BSE split at Th/U = 3.9, K/U = 14000)", "power", grp, None,
            (f * g_lo, f * g_c, f * g_hi), "W", "modelled",
            f"P_i = f_i x B01 with f_i = h_i m_i / sum(h m); h from nuclides.csv/groups.csv chain energies; "
            f"f = {f:.4f}. See derivations.md B1",
            "S0602;S0601;S0600" if bid != "B04" else "S0602;S0601",
            "Split fractions use the Huang 2013 BSE mass ratios; KamLAND 2022 with free Th/U gives a different split.")

    # ---- B05-B06 ocean K-40
    vol, rho, kmm = INPUTS["ocean_vol_m3"], INPUTS["sw_density"], INPUTS["sw_K_mmol_kg"]
    ab = INPUTS["K40_abund"]
    k_g_kg = scale(kmm, M_K / 1000.0)                                # g K per kg seawater
    ocean_mass = prod(vol, rho)
    k_mass_kg = prod(ocean_mass, scale(k_g_kg, 1e-3))                # kg K in ocean
    a_k = prod(k_mass_kg, (ab[0] / ab[1], 1.0, ab[2] / ab[1]), const(A_K40))
    add("B05", "K-40 in the oceans", "stock", "K40", None, a_k, "Bq", "modelled",
        "A = V rho w_K (N_A abund / M_K) lambda; see derivations.md B2", "S0608;S0609;S0610;S9005",
        f"Ocean K = {k_mass_kg[1]:.3e} kg; A_K40 = {A_K40:.4g} Bq/kg K. Seawater density bounds are judgement.")
    p_k = tuple(v * e_head_J("K40") for v in a_k)
    add("B06", "K-40 in the oceans, radioactive power", "power", "K40", None, p_k, "W", "modelled",
        "P = A x Ebar(K40) = A x 0.67847 MeV; see derivations.md B2", "S0608;S0609;S0610;S9005",
        "Antineutrino excluded (groups.csv).")

    # ---- B07 radon
    sec_a = YEAR_S
    unscear = INPUTS["rn_flux_unscear"] * LAND_T[1] * sec_a
    hirao = INPUTS["rn_flux_hirao"] * LAND_T[1] * sec_a
    gci = {k: v * 1e9 * CI_BQ for k, v in INPUTS["rn_total_GCi_a"].items()}
    t = (min(unscear, *gci.values()), gci["ZK11"], max(hirao, *gci.values()))
    add("B07", "Natural Rn-222 exhalation from ice-free land", "flow", "Rn222+", None, t, "Bq/a", "compiled",
        "Phi x A_land x t_a (UNSCEAR 0.016 Bq/m2/s; Hirao 0.0213) bracketed with Zhang 2021 inventories "
        "1.94-2.41 GCi/a; see derivations.md B3", "S0604;S0606;S0607;S0613",
        f"UNSCEAR-flux total {unscear:.3e}; Hirao-flux total {hirao:.3e}; JA97/ZK11/ZKC/SW98 = "
        + "/".join(f"{v:.3e}" for v in gci.values()) + ". Head activity is Rn-222 only (D24).")

    # ---- B08-B11 cosmogenic
    r = INPUTS["cosmo_rel"]
    for bid, nm, key, grp, q, unit, uf in (
            ("B08", "Cosmogenic H-3 production", "h3_prod_PBq_a", "H3", "flow", "Bq/a", 1e15),
            ("B09", "Cosmogenic H-3 natural inventory", "h3_inv_PBq", "H3", "stock", "Bq", 1e15),
            ("B10", "Cosmogenic C-14 production", "c14_prod_PBq_a", "C14", "flow", "Bq/a", 1e15),
            ("B11", "Cosmogenic C-14 natural inventory", "c14_inv_PBq", "C14", "stock", "Bq", 1e15)):
        c = INPUTS[key] * uf
        if grp == "C14":
            add(bid, nm, q, grp, None, rel(c, INPUTS["c14_rel"]), unit, "compiled",
                f"UNSCEAR 2000 Annex B Table 4: {INPUTS[key]} PBq{'/a' if q == 'flow' else ''} (x 1e15); "
                "low = central x 1.64/2.5 (Kovaltsov 2012 modern production); high +30 % judgement; "
                "steady-state check P = A lambda^-1 in derivations.md B4",
                "S0604;S0614", "UNSCEAR's 2.5 atoms/cm2/s is at the high end; Kovaltsov 2012 gives 1.64 (modern) and "
                "1.88 (pre-industrial), so the low bound uses 1.64/2.5. High bound is a judgement.")
        else:
            add(bid, nm, q, grp, None, rel(c, r), unit, "compiled",
                f"UNSCEAR 2000 Annex B Table 4: {INPUTS[key]} PBq{'/a' if q == 'flow' else ''} (x 1e15); "
                "bounds +-30 % judgement; steady-state check P = A lambda^-1 in derivations.md B4",
                "S0604", "UNSCEAR gives no uncertainty; bounds of +-30 % are a judgement.")

    # ---- B12-B14 soil
    soil_mass = prod(LAND_T, const(INPUTS["soil_depth_m"]), INPUTS["soil_density"])
    for bid, key, grp, nm in (("B12", "K40", "K40", "K-40"), ("B13", "U238", "U238+", "U-238 (head)"),
                              ("B14", "Th232", "Th232", "Th-232")):
        c = INPUTS["soil_Bq_kg"][key]
        t = prod(soil_mass, rel(c, INPUTS["soil_rel"]))
        add(bid, f"{nm} in the top metre of ice-free land soil", "stock", grp, None, t, "Bq", "modelled",
            "A = C_soil x A_land x 1 m x rho_soil; see derivations.md B5", "S0604;S0613",
            f"Soil mass {soil_mass[1]:.3e} kg treats all ice-free land as soil (no bare rock, lakes, bedrock correction): an upper-side bias. Median concentration {c} Bq/kg (UNSCEAR 2000 Table 6).")

    # ---- B15-B19 fallout
    for bid, key, grp, nm in (("B15", "H3", "H3", "H-3"), ("B16", "C14", "C14", "C-14"),
                              ("B17", "Sr90", "Sr90+", "Sr-90"), ("B18", "Cs137", "Cs137+", "Cs-137"),
                              ("B19", "I131", "I131", "I-131")):
        c = INPUTS["fallout_PBq"][key] * 1e15
        add(bid, f"Atmospheric weapons-test {nm} globally dispersed (cumulative 1945-1980, undecayed)",
            "stock", grp, None, rel(c, INPUTS["fallout_rel"][key]), "Bq", "compiled",
            f"UNSCEAR 2000 Annex C Table 9 'global release': {INPUTS['fallout_PBq'][key]:g} PBq at time of production; "
            "bounds judgement; see derivations.md B6", "S0605",
            "Cumulative activity produced and globally dispersed, not decayed; excludes local/regional deposition. Head activity (D24). Military baseline only (D9).")

    # ---- B20 ocean U, B21 crust U
    mass_u = prod(ocean_mass, scale(INPUTS["sw_U_nmol_kg"], 1e-9 * M_U / 1000.0))      # kg U
    a_u = prod(mass_u, const(A_U238))
    add("B20", "Natural U-238 dissolved in the oceans", "stock", "U238+", None, a_u, "Bq", "modelled",
        "A = V rho [U] M_U x A_U238/kg; see derivations.md B7", "S0608;S0612;S9005",
        f"Ocean U = {mass_u[1]:.3e} kg ({mass_u[1] / 1e3:.2e} t). Head activity U-238; U-234 adds ~1.14x more (not counted). Th not included (no sourced ocean mean).")
    crust_mass = prod(LAND_T, const(INPUTS["crust_depth_m"]), INPUTS["crust_density"])
    u_crust = prod(crust_mass, scale(INPUTS["crust_U_ppm"], 1e-6))
    a_c = prod(u_crust, const(A_U238))
    add("B21", "Natural U-238 in the top 1 km of the continental crust (ice-free land)", "stock", "U238+", None,
        a_c, "Bq", "modelled", "A = A_land x 1 km x rho x [U] x A_U238/kg; see derivations.md B8",
        "S0611;S0613;S9005",
        f"Crust mass {crust_mass[1]:.3e} kg; U {u_crust[1]:.3e} kg. Upper-continental-crust U (2.7 ppm) applied to the full depth; bounds from +-0.6 ppm as 1 sigma.")
    return rows


COLS = ["baseline_id", "name", "quantity", "group", "year", "value_low", "value_central", "value_high",
        "unit", "basis", "derivation", "source_ids", "notes"]


def fmt(v):
    return f"{v:.4g}" if isinstance(v, float) else str(v)


def main():
    rows = build()
    for r in rows:
        for k in ("value_low", "value_central", "value_high"):
            assert r[k] >= 0
        assert r["value_low"] <= r["value_central"] <= r["value_high"], r["baseline_id"]
    if "--print" in sys.argv:
        for r in rows:
            print(r["baseline_id"], r["name"][:60].ljust(60), fmt(r["value_low"]), fmt(r["value_central"]),
                  fmt(r["value_high"]), r["unit"])
        print(f"constants: A_K40={A_K40:.4g} Bq/kg  A_U238={A_U238:.4g}  A_Th232={A_TH232:.4g}  "
              f"H_U={H_U:.4g} H_Th={H_TH:.4g} H_K={H_K:.4g} W/kg  E_chain U238/U235/Th232 = "
              f"{E_U238_CHAIN:.4f}/{E_U235_CHAIN:.4f}/{E_TH232_CHAIN:.4f} MeV")
        return 0
    if "--write" in sys.argv:
        with open(OUT, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=COLS, lineterminator="\n")
            w.writeheader()
            for r in rows:
                w.writerow({k: (fmt(v) if isinstance(v, float) else v) for k, v in r.items()})
        print(f"wrote {OUT} ({len(rows)} rows)")
        return 0
    existing = {r["baseline_id"]: r for r in read_csv(OUT)}
    bad = 0
    for r in rows:
        e = existing.get(r["baseline_id"])
        if not e:
            print("MISSING", r["baseline_id"]); bad += 1; continue
        for k in ("value_low", "value_central", "value_high"):
            a, b = float(e[k]), r[k]
            if abs(a - b) > 5e-4 * max(abs(b), 1e-300):
                print("MISMATCH", r["baseline_id"], k, a, b); bad += 1
    print("OK: all", len(rows), "baselines reproduced" if not bad else f"{bad} problems")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
