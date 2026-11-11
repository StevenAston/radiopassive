"""Build the D74 staging tree (build/d74_staging/) for Task 2.4.

Deterministic, standard library only. Reads data/ and research/ (never writes them);
writes the final files under build/d74_staging/<target path>. Run from the repository root:

    python research/wind_solar/build_d74_staging.py

Approved by Steve 2026-11-11 (D74, WIND_SOLAR_SPEC v1.0). Values marked PLACEHOLDER are
orchestrator defaults to be replaced when Steve supplies data.
"""
from __future__ import annotations

import csv
import io
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "build" / "d74_staging"
PH = "PLACEHOLDER (D74 orchestrator default; replace): "


def read(path):
    with open(ROOT / path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def header(path):
    with open(ROOT / path, newline="", encoding="utf-8") as f:
        return next(csv.reader(f))


def write(path, columns, rows):
    p = OUT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=columns, lineterminator="\n", extrasaction="raise")
    w.writeheader()
    for r in rows:
        w.writerow({c: r.get(c, "") for c in columns})
    p.write_text(buf.getvalue(), encoding="utf-8")
    return len(rows)


def g(x):
    """Six significant digits, as the stream files."""
    if x == 0:
        return "0"
    return f"{x:.6g}"


# ---------------------------------------------------------------- registry
def build_registry():
    draft = read("research/wind_solar/commodity_factors_draft.csv")
    keep = [r for r in draft if r["ore_type"] != "superseded" and r["component"] != "embedded_fuel"]
    out = []
    ree_map = {}  # draft index -> ree ore type
    for i, r in enumerate(draft):
        if r["commodity"] != "ree_oxide":
            continue
        if r["region"] == "MYS":
            ree_map[i] = "ree_mt_weld"
        elif r["region"] == "CHN" and r["residue_type"] == "other_commodity_residue":
            ree_map[i] = "ree_ionic_clay"
        elif r["region"] == "CHN":
            ree_map[i] = "ree_bayan_obo"
        else:
            ree_map[i] = "ree_monazite"
    od_template = None
    for i, r in enumerate(draft):
        if r["ore_type"] == "superseded" or r["component"] == "embedded_fuel":
            continue
        r = dict(r)
        if r["commodity"] == "ree_oxide":
            r["ore_type"] = ree_map[i]
            if r["ore_type"] in ("ree_bayan_obo", "ree_ionic_clay") and int(r["year_from"]) > 1982:
                # WIND_SOLAR_SPEC v1.1 §13 S1: wind REE tonnage exists from 1982; Bayan Obo has produced since the
                # late 1950s and ionic clays since the 1980s; the per-tonne values are carried back unchanged.
                r["notes"] = (f"Window extended {r['year_from']} -> 1982 (WIND_SOLAR_SPEC v1.1 S1; values carried back "
                              "unchanged, no earlier measurement). ") + r["notes"]
                r["year_from"] = "1982"
        if r["ore_type"] == "iocg_high_u":
            if r["year_from"] == "1988":  # OD-only era (weights OD 1.00): becomes iocg_olympic_dam
                r["ore_type"] = "iocg_olympic_dam"
                r["year_to"] = "2025"
                r["notes"] = r["notes"].replace("CLASS A iocg_high_u, Olympic Dam only", "CLASS A iocg_olympic_dam (D74 Q1), Olympic Dam only")
                r["notes"] = r["notes"].replace("Cu-tonnage weights OD 1.00, Prominent Hill 0.00, Carrapateena 0.00 (my production estimates, +-20 percent). ", "")
                r["notes"] = "Olympic Dam only (un-mixed; D74 Q1, one pool two ledgers: nuclear F8 reads this row). " + r["notes"]
                out.append(r)
            continue  # era-mixed rows dropped; replaced below
        out.append(r)
    # Prominent Hill + Carrapateena rows (iocg_high_u), from copper_classes.md section 3 inputs
    ph = {"u": (800, 1350, 1420), "tt": (80, 95, 110)}
    cp = {"u": (2000, 2700, 2950), "tt": (55, 66.3, 80)}
    th = (15, 40, 100)
    eras = [("2009", "2018", 1.0, 0.0), ("2019", "2025", 0.61, 0.39)]
    groups_u = ["U238+", "U234", "Th230", "Ra226+", "Pb210+", "Po210"]
    groups_th = ["Th232", "Ra228+", "Th228+"]
    src = "S0458;S0459;S0407"
    for y0, y1, wp, wc in eras:
        u = [wp * ph["u"][k] * ph["tt"][k] * 1000 + wc * cp["u"][k] * cp["tt"][k] * 1000 for k in range(3)]
        tt = [wp * ph["tt"][k] + wc * cp["tt"][k] for k in range(3)]
        t = [th[k] * tt[k] * 1000 for k in range(3)]
        base = dict(commodity="copper", component="own_residue", tier="impounded", route="",
                    residue_type="metal_tailings", region="AUS", ore_type="iocg_high_u",
                    year_from=y0, year_to=y1, allocation_variant="default", allocation_rule="alloc:value",
                    unit="Bq/t", below_detection="false", basis="modelled", source_ids=src)
        lead = (f"non-fuel process (own_residue). Per tonne of refined Cu, before D6 allocation. CLASS A iocg_high_u "
                f"(D74 Q1: Prominent Hill and Carrapateena only, Olympic Dam excluded). Cu-tonnage weights PH {wp:.2f}, CP {wc:.2f} "
                "(production estimates [A], +-20 percent). PH tailings U3O8 121-136 ppm in size fractions = 1,270-1,420 Bq/kg U-238 "
                "(S0458; low 800 assumed) x 80/95/110 t/t; CP tailings about 214 ppm U = 2,640-2,950 Bq/kg (S0459; low 2,000) x 55/66/80 t/t. "
                "No U recovered: chain members at the U-238 level.")
        for gname in groups_u:
            out.append({**base, "group": gname, "value_low": g(u[0]), "value_central": g(u[1]), "value_high": g(u[2]),
                        "notes": lead if gname == "U238+" else f"[{gname} member of the U238+ block, ratio 1.] " + lead})
        out.append({**base, "group": "U235+", "value_low": g(u[0] * 0.0461), "value_central": g(u[1] * 0.0461),
                    "value_high": g(u[2] * 0.0461), "notes": "[U235+ member of the U238+ block, ratio 0.0461.] " + lead})
        for gname in groups_th:
            out.append({**base, "group": gname, "value_low": g(t[0]), "value_central": g(t[1]), "value_high": g(t[2]),
                        "notes": (f"[{gname} member of the Th232 block, ratio 1.] " if gname != "Th232" else "")
                        + "CLASS A iocg_high_u (PH, CP). Th-232 assumed 15/40/100 Bq/kg x tailings t/t (no IOCG measurement)."})
    # region fix check and ids
    for n, r in enumerate(out, 1):
        r["factor_id"] = f"commodity:{n:04d}"
        assert ";" not in r["region"], r
    cols = ["factor_id", "commodity", "component", "group", "tier", "route", "residue_type", "region", "ore_type",
            "year_from", "year_to", "allocation_variant", "allocation_rule", "value_low", "value_central", "value_high",
            "unit", "below_detection", "basis", "source_ids", "notes"]
    return cols, out, len(keep)


# ---------------------------------------------------------------- fuel inputs
def build_fuel():
    cols = ["commodity", "fuel", "stream_ref", "region", "year_from", "year_to", "value_low", "value_central",
            "value_high", "unit", "basis", "source_ids", "notes"]
    rows = [
        ("steel", "coal", "coal", 0.6, 0.8, 1.0, "t/t", "compiled", "S0421;S0202",
         "Coking coal and PCI as coal, per t BF-route crude steel. Was draft embedded_fuel rows steel U238+/Th232 (D74(d)). Reference only, lifecycle view (D22)."),
        ("cement", "coal", "coal", 0.06, 0.10, 0.15, "t/t", "modelled", "S0432",
         "Coal-equivalent kiln fuel per t cement (clinker 3.3 GJ/t x 0.75 clinker ratio / 25 GJ/t coal; author arithmetic). Petcoke and waste fuels not separated. Reference only."),
        ("silicon_mg", "coal", "coal", 1.0, 1.7, 2.5, "t/t", "modelled", "S0422",
         "Carbothermic reductants per t Si, coal fraction taken as 1.0 (upper side; charcoal is biomass). ASSUMPTION: S0422 Tables 2-4 not read. Reference only."),
        ("aluminium", "electricity", "", 14, 14.5, 15, "MWh/t", "compiled", "S0437",
         "Smelting electricity per t primary aluminium (commodity_notes.md section 1 item 4). Reference only; mix not charged until Phase 3 design."),
        ("silicon_mg", "electricity", "", 11, 12, 13, "MWh/t", "compiled", "S0422",
         "Furnace electricity per t MG-Si (commodity_notes.md section 1 item 4). Reference only."),
    ]
    out = [dict(commodity=c, fuel=f, stream_ref=s, region="XWL", year_from="1950", year_to="2025",
                value_low=g(l), value_central=g(m), value_high=g(h), unit=u, basis=b, source_ids=src, notes=n)
           for c, f, s, l, m, h, u, b, src, n in rows]
    return cols, out


# ---------------------------------------------------------------- vocab
def build_vocab():
    v = json.loads((ROOT / "data/reference/vocab.json").read_text(encoding="utf-8"))
    for c in ("cast_iron", "tio2_pigment"):
        if c not in v["commodities"]:
            v["commodities"].append(c)
        if c not in v["products"]["commodity"]:  # SCHEMA §5.5: products.commodity mirrors commodities
            v["products"]["commodity"].append(c)
    v["commodity_components"] = ["own_residue"]  # SCHEMA v2.6 §4.7: embedded_fuel removed (fuel inputs in §4.13)
    v["ore_types"] = {
        "copper": ["porphyry_stratiform", "iocg_olympic_dam", "iocg_high_u", "cu_co_stratiform", "all"],
        "ree_oxide": ["ree_bayan_obo", "ree_ionic_clay", "ree_monazite", "ree_mt_weld"],
    }
    v["fuel_input_fuels"] = {"coal": "coal", "coke": "coal", "petroleum_coke": "oil_gas",
                             "natural_gas": "oil_gas", "fuel_oil": "oil_gas", "electricity": ""}
    return v


# ---------------------------------------------------------------- residue parameters
EPS = {  # residue: (e222 l,c,h), (e220 l,c,h), seepage or None, sources, grade note
    "metal_tailings": ((0.002, 0.03, 0.14), (5.7e-6, 6.5e-5, 5.0e-4), None, "S0242;S0408;S0467",
                       "Rn-222 epsilon = u_tailings triple (D62 precedent; Olympic Dam pool shared with nuclear F8, D74 Q8); Sakoda mill tailings emanation 0.17 is the upper side, OD flux implies about 0.004 effective. Rn-220: emanation 0.017/0.05/0.10 (Sakr 2025 range; 0.6 x 0.17) x D60 slab factor, L 0.005/0.01/0.02 m, H 4-15 m. Grade C."),
    "iron_ore_tailings": ((0.002, 0.03, 0.14), (5.7e-6, 6.5e-5, 5.0e-4), None, "S0242;S0467",
                          "As metal_tailings (no iron-ore tailings emanation found). Grade D."),
    "ree_tailings": ((0.002, 0.03, 0.14), (5.7e-6, 6.5e-5, 5.0e-4), None, "S0242;S0404;S0466;S0467",
                     "As metal_tailings; monazite grains emanate 0.002 (S0404 Table 26) and high-melting minerals less (S0466); Bayan Obo tailings are ground carbonate-fluorite ore. Rn-220 non-zero (thorium-rich). Grade D."),
    "red_mud": ((0.076, 0.13, 0.20), (7.7e-6, 8.4e-5, 7.0e-4), None, "S0425;S0462;S0463;S0464;S0436",
                "Rn-222 epsilon = emanation (D60 upper bound): dry untreated 0.20 (S0425/S0463), 0.076-0.20 over 0-28 percent moisture (S0462), highest of 19 residues (S0436). Effective alternative 0.003/0.02/0.1 not adopted (D74 Q8). Rn-220: 0.3/0.5/0.7 x Rn-222 emanation x slab factor, H 4-15 m. Grade B."),
    "ree_process_residue": ((0.005, 0.03, 0.20), (7.5e-7, 4.7e-5, 2.8e-3), (7e-7, 7e-6, 4e-5),
                            "S0242;S0404;S0466;S0970;S0470;S0964;S0950;S0954",
                            "No measurement. Rn-222: Sakoda mineral 0.03, soil 0.20 high, monazite-like low. Rn-220: 0.3/0.5/0.7 x, H 1-10 m [A]. Seepage: M4 gypsum dissolution as coal_fgd_residue (Lynas WLP gypsum-rich; Th refractory, under 5 percent recovered by acid digestion, S0470). Grade D."),
    "smelter_slag": ((0.001, 0.01, 0.05), (1.0e-7, 6.5e-6, 1.75e-4), (1e-7, 1e-6, 6e-5),
                     "S0436;S0465;S0466;S0202;S0468;S0950;S0954",
                     "Rn-222: high-temperature residues emanate less (S0436: 19 residues 0.6-8.6 percent; S0466); porous coal-slag 14 percent (S0465) excluded as not vitreous. Rn-220 0.3/0.5/0.7 x, H 4-15 m. Seepage: generic M1 Ra centre 6e-6 x 0.13-0.18 (U leached from copper smelter ash vs copper tailings, S0468) = 1e-6; high kept generic (crushed slag aggregate). Grade C (epsilon), D (seepage)."),
    "cement_kiln_residue": ((0.006, 0.027, 0.086), (6.0e-7, 1.7e-5, 3.0e-4), (7e-7, 6e-6, 6e-5),
                            "S0436;S0469;S0950;S0954",
                            "Rn-222: Sas 2019 dry residues incl. three kiln dusts 0.6-8.6 percent, mean 2.7 percent (S0436). Rn-220 0.3/0.5/0.7 x, H 4-15 m. Seepage: generic M1 Ra triple; K-40 override in residue_seepage_by_group (M2, S0469). No rows use this type yet. Grade C (epsilon), D (Ra)."),
    "other_commodity_residue": ((0.005, 0.03, 0.13), (7.5e-7, 4.7e-5, 1.8e-3), (7e-7, 6e-6, 6e-5),
                                "S0242;S0466;S0950;S0954",
                                "Mixed bucket (TiO2 chloride waste, sinter dust, foundry zircon sand, ionic-clay leached ore, Si residues): Sakoda mineral to rock; Rn-220 0.3/0.5/0.7 x, H 1-10 m [A]; seepage generic M1. Grade D."),
}


def build_residues():
    cols = header("data/reference/residue_types.csv")
    rows = read("data/reference/residue_types.csv")
    for r in rows:
        if r["residue_type"] not in EPS:
            continue
        e222, e220, seep, src, note = EPS[r["residue_type"]]
        for nm, trip in (("epsilon_rn222", e222), ("epsilon_rn220", e220)):
            assert not r[f"{nm}_central"], r["residue_type"]
            for k, v in zip(("low", "central", "high"), trip):
                r[f"{nm}_{k}"] = g(v)
        if seep is not None:
            assert not r["seepage_per_a_central"], r["residue_type"]
            for k, v in zip(("low", "central", "high"), seep):
                r[f"seepage_per_a_{k}"] = g(v)
        old = [s for s in r["source_ids"].split(";") if s]
        r["source_ids"] = ";".join(sorted(set(old) | set(src.split(";"))))
        r["basis"] = "modelled"
        prefix = "REVISION D74 (Steve, 2026-11-11; WIND_SOLAR_SPEC Appendix A): " + note
        r["notes"] = prefix + (" | " + r["notes"] if r["notes"] else "")
    return cols, rows


def build_seepage_by_group():
    cols = header("data/reference/residue_seepage_by_group.csv")
    rows = read("data/reference/residue_seepage_by_group.csv")
    rows.append(dict(residue_type="cement_kiln_residue", group="K40", seepage_low="1e-05", seepage_central="0.00012",
                     seepage_high="0.0023", basis="modelled", source_ids="S0469;S0950",
                     notes="D74 (WIND_SOLAR_SPEC Appendix A). M2: water removed at least 70 percent of K from kiln dust at L/S 20 (S0469); F/(L/S) 0.035/0.05/0.09 kg/L x deposit L/S per a 2.9e-4/2.3e-3/2.5e-2 L/kg (seepage notes M1 hydrology, S0950)."))
    return cols, rows


# ---------------------------------------------------------------- sources
NEW_SOURCES = [
    ("S0462", "Kovacs et al. 2012 (red mud spill radiology)", "Kovacs, T., Sas, Z., Jobbagy, V., Csordas, A. and Szeiler, G. (2012). Radiological investigation of the effects of red mud disaster. Radiation Protection Dosimetry 152(1-3):76-79.", "https://doi.org/10.1093/rpd/ncs192", "10.1093/rpd/ncs192", "2012", "peer_reviewed", "3", "paywalled", "restricted", "Abstract read 2026-11-11: Rn-222 emanation 7.6-20 percent over 0-28 percent moisture; Ajka red mud Ra-226 180 Bq/kg. Author list beyond the first two to be verified."),
    ("S0463", "Jobbagy et al. 2009 (J. Hazard. Mater.)", "Jobbagy, V., Somlai, J., Kovacs, J., Szeiler, G. and Kovacs, T. (2009). Dependence of radon emanation of red mud bauxite processing wastes on heat treatment. Journal of Hazardous Materials 172(2-3):1258-1263.", "https://doi.org/10.1016/j.jhazmat.2009.07.131", "10.1016/j.jhazmat.2009.07.131", "2009", "peer_reviewed", "3", "paywalled", "restricted", "Journal version of S0425. Abstract read 2026-11-11: untreated dry red mud emanation about 20 percent, about 5 percent after heat treatment."),
    ("S0464", "Sas et al. 2015 (red mud heat treatment)", "Sas, Z., Szanto, J., Kovacs, J., Somlai, J. and Kovacs, T. (2015). Influencing effect of heat-treatment on radon emanation and exhalation characteristic of red mud. Journal of Environmental Radioactivity 148:27-32.", "https://doi.org/10.1016/j.jenvrad.2015.06.002", "10.1016/j.jenvrad.2015.06.002", "2015", "peer_reviewed", "3", "paywalled", "restricted", "Abstract and excerpts read 2026-11-11: massic exhalation 75 to 7 mBq/kg/h after 1200 C. Volume and pages to be verified."),
    ("S0465", "Somlai et al. 2008 (coal-slag emanation)", "Somlai, J., Jobbagy, V., Kovacs, J., Tarjan, S. and Kovacs, T. (2008). Connection between radon emanation and some structural properties of coal-slag as building material. Radiation Measurements 43(1):72-76.", "https://doi.org/10.1016/j.radmeas.2007.10.028", "10.1016/j.radmeas.2007.10.028", "2008", "peer_reviewed", "3", "paywalled", "restricted", "Abstract read 2026-11-11: emanation 1.35 and 14.3 percent for two coal-slags, controlled by pore volume. Pages to be verified."),
    ("S0466", "Krupp et al. 2017 (mineral emanation)", "Krupp, K., Baskaran, M. and Brownlee, S. (2017). Radon emanation coefficients of several minerals: How they vary with physical and mineralogical properties. American Mineralogist 102(7):1375-1383.", "https://doi.org/10.2138/am-2017-6017", "10.2138/am-2017-6017", "2017", "peer_reviewed", "3", "paywalled", "restricted", "Abstract read 2026-11-11: 14 minerals, 0.083-7.0 percent unheated; high-melting minerals lower."),
    ("S0467", "Sakr et al. 2025 (Rn and Tn emanation)", "Sakr, S., Sahoo, S. et al. (2025). Radon-thoron exhalation and emanation determinations from mylonitic rock samples collected in north Abu Rusheid, Egypt. Environmental Monitoring and Assessment 197:548.", "https://doi.org/10.1007/s10661-025-13997-5", "10.1007/s10661-025-13997-5", "2025", "peer_reviewed", "3", "paywalled", "restricted", "Abstract read 2026-11-11: Rn emanation 0.055-0.182, Tn 0.017-0.078 (27 samples); supports Tn/Rn 0.3-0.7 (D60 analogy)."),
    ("S0468", "Patra et al. 2011 (U leaching from wastes)", "Patra, A.C., Sumesh, C.G., Mohapatra, S., Sahoo, S.K., Tripathi, R.M. and Puranik, V.D. (2011). Long-term leaching of uranium from different waste matrices. Journal of Environmental Management 92(3):919-925.", "https://doi.org/10.1016/j.jenvman.2010.10.046", "10.1016/j.jenvman.2010.10.046", "2011", "peer_reviewed", "3", "paywalled", "restricted", "Abstract read 2026-11-11: 142-day semi-dynamic test, cumulative U leach 0.05-0.07 percent copper smelter (kinker) ash vs 0.39-0.59 percent copper tailings. Author initials and pages to be verified."),
    ("S0469", "Seo et al. 2019 (CKD leaching)", "Seo, M., Lee, S.-Y., Lee, C. and Cho, S.-S. (2019). Recycling of Cement Kiln Dust as a Raw Material for Cement. Environments 6(10):113.", "https://doi.org/10.3390/environments6100113", "10.3390/environments6100113", "2019", "peer_reviewed", "3", "open", "open", "Abstract and excerpts read 2026-11-11: water removed at least 70 percent K and 90 percent Cl at L/S 20. Author list to be verified."),
    ("S0470", "Al-Areqi et al. 2014 (WLP digestion)", "Al-Areqi, W.M., Majid, A.Ab. and Sarmani, S. (2014). Digestion study of water leach purification (WLP) residue for possibility of thorium extraction. Malaysian Journal of Analytical Sciences 18(1):221-225.", "https://www.ukm.my/mjas/v18_n1/html/18_1_26.html", "", "2014", "peer_reviewed", "3", "open", "unknown", "Read 2026-11-11: under 5 percent Th recovered by acid digestion (refractory after calcination); WLP Th 1953 mg/kg, U 17.2 mg/kg."),
]


def build_sources():
    cols = header("data/sources.csv")
    rows = read("data/sources.csv")
    have = {r["source_id"] for r in rows}
    prop = read("research/wind_solar/sources_task24_proposed.csv")
    for r in prop:
        if r["source_id"] == "S0448":  # Q17: S0448 kept, S1800 (tier2 memo proposal) is its duplicate
            r["url"] = "https://www-pub.iaea.org/MTCD/Publications/PDF/Pub1257_web.pdf"
            r["access"] = "open"
            r["notes"] = ("Read 2026-11-10/11 (Table 1, s3.1.9; copper slag Ra-226 0.4-2 Bq/g, precipitator dust Pb-210/Po-210 up to 200 Bq/g). "
                          "D74 Q17: this is the single ID for SRS-49; the Tier 2 memo's proposed S1800 is a duplicate and must not be added (cite S0448).")
        assert r["source_id"] not in have, r["source_id"]
        fixes = []
        if r["type"] in ("conference", "company"):
            fixes.append(f"type {r['type']} -> grey")
            r["type"] = "grey"
        if r["licence"] not in ("open", "restricted", "unknown"):
            fixes.append(f"licence '{r['licence']}' -> open")
            r["licence"] = "open"
        want = {"regulator": "1", "compilation": "2", "peer_reviewed": "3", "agency": "4", "grey": "5"}[r["type"]]
        if r["rank"] != want:
            fixes.append(f"rank {r['rank']} -> {want}")
            r["rank"] = want
        if fixes:
            r["notes"] = (r["notes"] + " " if r["notes"] else "") + "[Normalised to vocab.json at application (D74): " + "; ".join(fixes) + ".]"
        rows.append(r)
        have.add(r["source_id"])
    for t in NEW_SOURCES:
        rows.append(dict(zip(cols, t)))
        have.add(t[0])
    # S1806 is cited by the cu_co_stratiform rows; take the Tier 2 memo proposal, updated (paper now read in full)
    rows.append(dict(source_id="S1806", short_cite="Manzuk and Philippe 2026",
                     full_citation="Manzuk, R. and Philippe, S. (2026). Uranium in cobalt-hydroxide exports from the Democratic Republic of the Congo. Nature Communications (published 30 July 2026).",
                     url="https://www.nature.com/articles/s41467-026-75910-z", doi="10.1038/s41467-026-75910-z", year="2026",
                     type="peer_reviewed", rank="3", access="open", licence="unknown",
                     notes="Read in full 2026-11-11 (import/s41467-026-75910-z.pdf; copper_classes.md section 7). 2,000-5,000 t U exported in cobalt hydroxide 2000-2024; background ore U geometric mean 7 ppm. Page callout only (D74(b)). Supersedes the Tier 2 memo's 'NOT OBTAINED' proposal text."))
    rows.append(dict(source_id="S1814", short_cite="IISD cobalt profile 2026",
                     full_citation="IISD (2026). Commodity profile: cobalt. International Institute for Sustainable Development.",
                     url="https://www.iisd.org/system/files/2026-05/commodity-profile-cobalt.pdf", doi="", year="2026",
                     type="grey", rank="5", access="open", licence="unknown",
                     notes="From the Tier 2 memo proposal (section 9). 2024 world cobalt 290 kt, DRC 220 kt; 78 percent of cobalt from Cu-Co. Context for d6_value_share_copper_cu_co (D74). Authors to be added."))
    return cols, rows


# ---------------------------------------------------------------- activity
ACT_COLS = ["series", "year", "country", "value_low", "value_central", "value_high", "unit", "below_detection",
            "basis", "source_ids", "notes"]


def arow(series, year, country, l, c, h, unit, basis, src, notes):
    assert l <= c <= h, (series, year, l, c, h)
    return dict(series=series, year=str(year), country=country, value_low=g(l), value_central=g(c), value_high=g(h),
                unit=unit, below_detection="false", basis=basis, source_ids=src, notes=notes)


def interp(anchors, y):
    """anchors: sorted list of (year, (l,c,h)). Linear between, flat outside. Returns (triple, basis)."""
    ys = [a[0] for a in anchors]
    if y in ys:
        return anchors[ys.index(y)][1], "compiled"
    if y < ys[0]:
        return anchors[0][1], "extrapolated"
    if y > ys[-1]:
        return anchors[-1][1], "extrapolated"
    for (y0, t0), (y1, t1) in zip(anchors, anchors[1:]):
        if y0 < y < y1:
            f = (y - y0) / (y1 - y0)
            return tuple(a + f * (b - a) for a, b in zip(t0, t1)), "interpolated"
    raise AssertionError


OX = {"Nd": 1.1664, "Pr": 1.2082, "Dy": 1.1477, "Tb": 1.1762}
JRC = {  # sub-tech: commodity: (l,c,h) t/GW, JRC 2018 (S0400;S0401)
    "GB-DFIG": dict(copper=(950, 1400, 5000), aluminium=(500, 1400, 1600), cast_iron=(18000, 18000, 20800),
                    glass_fibre=(7700, 7700, 8400), concrete=(243500, 355000, 413000), steel=(107000, 113000, 132000),
                    Nd=(12, 12, 180), Pr=(0, 0, 35), Dy=(2, 2, 17), Tb=(0, 0, 7)),
    "GB-PMSG": dict(copper=(950, 950, 5000), aluminium=(500, 1600, 1600), cast_iron=(18000, 20800, 20800),
                    glass_fibre=(7700, 8400, 8400), concrete=(243500, 413000, 413000), steel=(107000, 107000, 132000),
                    Nd=(12, 51, 180), Pr=(0, 4, 35), Dy=(2, 6, 17), Tb=(0, 1, 7)),
    "DD-PMSG": dict(copper=(950, 3000, 5000), aluminium=(500, 500, 1600), cast_iron=(18000, 20100, 20800),
                    glass_fibre=(7700, 8100, 8400), concrete=(243000, 243000, 413000), steel=(107000, 119500, 132000),
                    Nd=(12, 180, 180), Pr=(0, 35, 35), Dy=(2, 17, 17), Tb=(0, 7, 7)),
}
CEMENT = (0.10, 0.12, 0.15)  # t cement per t concrete [A]


def ree_oxide(d):
    return tuple(sum(OX[e] * d[e][k] for e in OX) for k in range(3))


def cement_of(conc):
    return tuple(conc[k] * CEMENT[k] for k in range(3))


def wind_class(cls):
    """Return {commodity: (anchors, src, note)} for a wind class."""
    sub = {"wind_on_nopm": "GB-DFIG", "wind_on_pm": "GB-PMSG", "wind_off_nopm": "GB-DFIG", "wind_off_pm": "DD-PMSG"}[cls]
    j = JRC[sub]
    off = cls.startswith("wind_off")
    s = "S0400;S0401"
    d = {}
    for c in ("copper", "aluminium", "cast_iron", "glass_fibre"):
        d[c] = ([(2018, j[c])], s, f"JRC 2018 {sub} (turbine, tower, foundation; cables and transformers excluded); flat outside 2018.")
    d["ree_oxide"] = ([(2018, ree_oxide(j))], s, f"JRC 2018 {sub}: Nd, Pr, Dy, Tb element masses x oxide factors 1.1664/1.2082/1.1477/1.1762 (Nd2O3, Pr6O11, Dy2O3, Tb4O7).")
    d["zinc"] = ([(2018, (30, 620, 5500))], "S0400;S0442", "CONFLICT kept in bounds: NREL 2022 0.03-0.11 t/MW vs JRC 5.5 t/MW; central geometric mean of 70 and 5500 t/GW (commodity_notes.md section 3.12).")
    d["tio2_pigment"] = ([(2018, (50, 75, 100))], "S0400", "ASSUMPTION [A] 50-100 t/GW blade and tower paint (commodity_notes.md section 3.10); no source gives the number.")
    if off:
        d["tin"] = ([(2022, (0.4, 0.7, 1.0))], "S0442", "NREL 2022 offshore.")
        d["steel"] = ([(2014, (130000, 259000, 419000)), (2022, (130000, 274500, 419000))], "S0441;S0442",
                      "Offshore steel: Bonou 2014 park 259 t/MW, NREL 2022 130-419 t/MW; JRC 120 t/MW below the band (commodity_notes.md section 7 conflict).")
        d["cement"] = ([(2014, cement_of((17000, 64000, 243000)))], "S0441;S0400",
                       "Offshore concrete 17 (Bonou) / 64 (geometric centre) / 243 (JRC DD-PMSG proxy) t/MW x 0.10/0.12/0.15 t cement per t concrete [A]; NREL says minimal.")
    else:
        d["tin"] = ([(2022, (0.2, 0.25, 0.3))], "S0442", "NREL 2022 land-based.")
        d["steel"] = ([(2010, (85000, 85000, 107000)), (2018, j["steel"]), (2022, (107000, 143000, 179000))],
                      "S0001;S0400;S0401;S0442", f"Onshore steel: White-Kulcinski 2010 85 t/MW (UNSCEAR reference), JRC 2018 {sub}, NREL 2022 land-based.")
        d["cement"] = ([(2018, cement_of(j["concrete"]))], s, f"JRC 2018 {sub} concrete x 0.10/0.12/0.15 t cement per t concrete [A].")
    return d


def pv_class(cls):
    s = "S0400;S0445"
    d = {
        "aluminium": ([(2013, (5000, 7100, 7500)), (2016, (5000, 6200, 7500)), (2018, (5000, 7500, 7500)), (2021, (5000, 5000, 7500)), (2023, (5000, 5700, 7500))],
                      s, "Qinghai LCA 2013-23 centrals, JRC 2018 7.5 t/MW; bounds are the min and max of these points."),
        "copper": ([(2018, (400, 2250, 4600))], s, "Qinghai 0.4-1.3 t/MW vs JRC 4.6 t/MW (BOS incl. cables): CONFLICT, flat, central geometric 2.25 t/MW."),
        "steel": ([(2018, (11500, 45000, 67900))], s, "Qinghai 11.5-67.8 t/MW, JRC 67.9 t/MW; flat."),
        "glass": ([(2018, (39800, 51000, 59200))], s, "Qinghai 39.8-59.2 t/MW, JRC 46.4 t/MW; flat."),
        "cement": ([(2018, cement_of((30000, 60700, 90000)))], "S0400", "JRC 2018 concrete 60.7 t/MW (bounds +-50 percent [A]) x 0.10/0.12/0.15 t cement per t concrete [A]."),
        "silicon_mg": ([(2004, (12800, 16000, 19200)), (2018, (3200, 4000, 4800)), (2030, (2000, 2750, 3500))], "S0400",
                       "c-Si: 2004 16 t/MW, 2018 4 t/MW (+-20 percent [A]), 2030 LDS/MDS/HDS 2.0/2.75/3.5 t/MW; flat before 2004."),
        "silver": ([(2010, (63, 84, 105)), (2019, (15, 20, 25)), (2020, (13, 15, 18)), (2030, (4, 6, 11))], "S0400",
                   "c-Si silver: 2010 84 t/GW, 2019 20, 2020 13/15/18, 2030 LDS/MDS/HDS 4/6/11; +-25 percent [A] where no band; flat before 2010."),
        "tin": ([(2018, (10, 13.3, 103))], "S0444", "IEA PVPS 2025-2050 average 13.3 t/GW, high 103 (PVPS upper); low 10 [A]; flat."),
        "tio2_pigment": ([(2018, (50, 75, 100))], "S0400", "ASSUMPTION [A] white backsheets 50-100 t/GW (commodity_notes.md section 3.10)."),
    }
    if cls == "pv_rooftop":
        d["cement"] = ([(2018, (0, 0, 0))], "S0400", "Rooftop: no foundation concrete [A] (WIND_SOLAR_SPEC Q12).")
        st = d["steel"][0][0][1]
        d["steel"] = ([(2018, tuple(x * 0.5 for x in st))], s, "Rooftop: utility steel x 0.5 (mounting rails only) [A]; Jungbluth 2010 Swiss 3 kWp inventory (S0001) is per kWh, not converted.")
    return d


def build_intensity():
    rows = []
    classes = [("wind_on_nopm", 1982), ("wind_on_pm", 1982), ("wind_off_nopm", 2001), ("wind_off_pm", 2001),
               ("pv_utility", 2001), ("pv_rooftop", 2001)]
    for cls, y0 in classes:
        spec = wind_class(cls) if cls.startswith("wind") else pv_class(cls)
        for com in sorted(spec):
            anchors, src, note = spec[com]
            for y in range(y0, 2026):
                (l, c, h), basis = interp(sorted(anchors), y)
                rows.append(arow(f"mi_{cls}_{com}", y, "XWL", l, c, h, "t/GW", basis, src,
                                 f"D74 / WIND_SOLAR_SPEC section 2.1 group I. {note}"))
    return rows


def era(y, table):
    for y0, y1, v in table:
        if y0 <= y <= y1:
            return v
    raise KeyError(y)


def build_shares(od):
    rows = []

    def ph(series, years, table, src, note, country="XWL"):
        for y in years:
            v = era(y, table)
            t = v if isinstance(v, tuple) else (v, v, v)
            rows.append(arow(series, y, country, *t, "1", "modelled", src, PH + note))

    ph("wind_pm_share_onshore", range(1982, 2026), [(1982, 1999, 0.0), (2000, 2009, 0.10), (2010, 2019, 0.25), (2020, 2025, 0.30)], "S0400;S0413", "share of new onshore capacity with permanent-magnet generators [A] (Q11).")
    ph("wind_pm_share_offshore", range(2001, 2026), [(2001, 2009, 0.0), (2010, 2015, 0.20), (2016, 2019, 0.50), (2020, 2025, 0.75)], "S0400", "share of new offshore capacity with permanent-magnet generators [A] (Q11).")
    ph("pv_utility_share", range(2001, 2026), [(2001, 2009, 0.30), (2010, 2015, 0.55), (2016, 2025, 0.60)], "S0444", "utility-scale share of new PV [A] (Q12).")
    prod = {(r["series"], int(r["year"])): float(r["value_central"]) for r in read("data/activity/commodity_production.csv")
            if r["country"] == "XWL" and r["series"] in ("prod_pig_iron", "prod_steel")}
    for y in range(1950, 2026):
        v = era(y, [(1950, 1969, 0.90), (1970, 1989, 0.80), (1990, 2009, 0.68), (2010, 2025, 0.71)])
        note = "BF-route (BOF plus open hearth) share = 1 - EAF share (Q10)."
        src = "S0421"
        if ("prod_pig_iron", y) in prod and ("prod_steel", y) in prod:
            ratio = prod[("prod_pig_iron", y)] / prod[("prod_steel", y)]
            if abs(v - ratio) > 0.15:
                note = (f"Era placeholder {v:.2f} was outside +-0.15 of prod_pig_iron/prod_steel ({ratio:.3f}, open-hearth era: "
                        "pig iron plus scrap); set to that ratio (WIND_SOLAR_SPEC v1.1 S3).")
                v, src = ratio, "S0421;S0410"
        rows.append(arow("steel_bf_route_share", y, "XWL", v, v, v, "1", "modelled", src, PH + note))
    ph("ree_route_share_bayan_obo", range(1982, 2026), [(1982, 2011, 0.60), (2012, 2025, 0.55)], "S0403;S0411;S0404", "REE route share, Bayan Obo [A] (Q6).")
    ph("ree_route_share_ionic_clay", range(1982, 2026), [(1982, 2011, 0.35), (2012, 2025, 0.30)], "S0403", "REE route share, ionic clays [A].")
    ph("ree_route_share_monazite", range(1982, 2026), [(1982, 2025, 0.05)], "S0404", "REE route share, monazite [A].")
    ph("ree_route_share_mt_weld", range(1982, 2026), [(1982, 2011, 0.0), (2012, 2025, 0.10)], "S0406", "REE route share, Mt Weld / Lynas [A].")
    ph("ree_charge_factor", range(1982, 2026), [(1982, 2025, 2.5)], "S0404", "REO-equivalent charge factor, default variant (value split); bounds 1 and 5.9 are spec rule constants (Q5).")
    ph("d6_value_share_copper_porphyry", range(1950, 2026), [(1950, 2025, 0.85)], "S0410", "copper share of porphyry/stratiform mine value (Q4).")
    ph("d6_value_share_copper_iocg_ph_cp", range(2009, 2026), [(2009, 2025, 0.70)], "S0407", "copper share of PH/CP mine value, Cu against Au and Ag (Q4).", "AUS")
    ph("d6_value_share_copper_cu_co", range(1950, 2026), [(1950, 2025, 0.85)], "S1814", "copper share of DRC Cu-Co mine value (Q4).", "COD")
    ph("d6_value_share_ree_bayan_obo", range(1982, 2026), [(1982, 2025, 0.70)], "S0405", "REE share of Bayan Obo value against iron and niobium (Q4).", "CHN")
    ph("d6_value_share_ree_monazite", range(1982, 2026), [(1982, 2025, 0.10)], "S0404", "monazite share of mineral-sands value (Q4).")
    ph("d6_value_share_zinc", range(1950, 2026), [(1950, 2025, 0.60)], "S0410", "zinc share of Zn-Pb-Ag mine value (Q4).")
    ph("d6_value_share_silver", range(1950, 2026), [(1950, 2025, 0.15)], "S0410", "by-product silver share of host-mine value (Q4).")
    ph("od_value_share_u", range(1988, 2026), [(1988, 2025, 0.12)], "S0407", "U3O8 share of Olympic Dam product value, FY2023 indicative 12.0 percent (Cu 74.3, Au 12.7, Ag 1.0) at resource prices; all years (Q4, D74(a)).", "AUS")
    # copper class shares (not placeholders), OD removed from class A (Q1)
    cs = {int(r["year"]): r for r in read("research/wind_solar/copper_class_shares.csv")}
    for y in range(1950, 2026):
        r = cs[y]
        world = float(r["world_mine_cu_t"])
        c_t = float(r["C_cu_co_stratiform_COD_t"])
        note_c = ""
        if y == 2025 and c_t == 0:  # COD 2025 missing in prod_copper: carry 2024 share
            c_share = float(cs[2024]["C_share"])
            note_c = " 2025 DRC share carried from 2024 (COD prod_copper 2025 missing), basis extrapolated."
        else:
            c_share = c_t / world
        od_t = od.get(y, (0, 0, 0))[1]
        od_orig = {2024: 322000.0, 2025: 330000.0}.get(y, od_t)  # copper_classes.md A tonnage used Copper SA totals
        a_other = (float(r["A_iocg_high_u_t"]) - od_orig) / world  # PH + CP as in copper_classes.md
        assert a_other >= -1e-9, y
        a_other = max(a_other, 0.0)
        od_s = od_t / world
        b_share = 1.0 - a_other - c_share - od_s
        base = "D74 copper class share of world mined copper (copper_class_shares.csv, XWL denominators; prod_copper_od / prod_copper is the fourth share)."
        rows.append(arow("cu_class_share_porphyry_stratiform", y, "XWL", b_share, b_share, b_share, "1", "modelled", "S0826;S0807", base + " B = 1 - A - OD - C." + note_c))
        rows.append(arow("cu_class_share_iocg_high_u", y, "XWL", a_other, a_other, a_other, "1", "modelled", "S0826;S0407", base + " Prominent Hill + Carrapateena only (estimates [A] +-20 percent)."))
        rows.append(arow("cu_class_share_cu_co_stratiform", y, "XWL", c_share, c_share, c_share, "1",
                         "extrapolated" if note_c else "modelled", "S0826", base + " DRC prod_copper / XWL." + note_c))
    return rows


def od_series():
    """prod_copper_od (t Cu) and u_production_od (t U), AUS, 1988-2025."""
    cu = {}
    for y in range(1988, 2026):
        if y <= 1989:
            c = 45000
        elif y <= 1996:
            c = 60000
        elif y <= 1999:
            c = 100000
        elif y <= 2022:
            c = 190000
        elif y == 2023:
            c = 212500
        else:  # 2024-25: the 322/330 kt of copper_classes.md are BHP Copper South Australia totals (OD + PH + CP after the
            c = 215000  # OZ Minerals acquisition, May 2023); OD alone held at the FY2023 level [A] (+-20 percent)
        cu[y] = (c * 0.8, c, c * 1.2) if y != 2023 else (212500 * 0.98, 212500, 212500 * 1.02)
    cu[2021] = (205300 * 0.98, 205300, 205300 * 1.02)
    cu[2022] = (138400 * 0.98, 138400, 138400 * 1.02)
    u_read = {2021: 3267 * 0.848, 2022: 2375 * 0.848, 2023: 2888.0}
    ratio = 2888.0 / 212500
    od_share_aus = 2888.0 / 4693.0  # FY2023: OD is the only conventional mill since Ranger stopped processing (Jan 2021)
    aus = {int(r["year"]): r for r in read("data/activity/uranium.csv") if r["series"] == "u_production" and r["country"] == "AUS"}
    isl = [r for r in read("data/factors/nuclear.csv") if r["stage"] == "u_mining_isl" and r["region"] == "XWL"
           and not r["group"] and not r["driver_series"]]

    def conv(y):  # AUS conventional tonnage as the nuclear stream computes it: P x (1 - s), s = XWL default ISL share
        f = [r for r in isl if int(r["year_from"]) <= y <= int(r["year_to"])]
        assert len(f) == 1, y
        sl, sc, sh = (float(f[0][k]) for k in ("value_low", "value_central", "value_high"))
        a = aus[y]
        return (float(a["value_low"]) * (1 - sh), float(a["value_central"]) * (1 - sc), float(a["value_high"]) * (1 - sl))

    uu, how = {}, {}
    for y in cu:
        if y in u_read:
            v = u_read[y]
            t, how[y] = (v * 0.98, v, v * 1.02), "read"
        elif y >= 2024:
            v = float(aus[y]["value_central"]) * od_share_aus
            t, how[y] = (v * 0.8, v, v * 1.2), "share"
        else:
            v = cu[y][1] * ratio
            t, how[y] = (v * 0.7, v, v * 1.3), "ratio"
        cv = conv(y)
        capped = tuple(min(a, b) for a, b in zip(t, cv))
        if capped != t:
            how[y] += "+cap"
        uu[y] = capped
    return cu, uu, how


def build_activity_appends(cu, uu, how):
    aus_u = {int(r["year"]): r for r in read("data/activity/uranium.csv") if r["series"] == "u_production" and r["country"] == "AUS"}
    aus_cu = {int(r["year"]): r for r in read("data/activity/commodity_production.csv") if r["series"] == "prod_copper" and r["country"] == "AUS"}
    cu_rows, u_rows = [], []
    for y in sorted(cu):
        read_cu = y in (2021, 2022, 2023)
        cu_rows.append(arow("prod_copper_od", y, "AUS", *cu[y], "t", "compiled" if read_cu else "modelled",
                            "S0407", "D74(a). Olympic Dam refined copper, BHP fiscal year ending June ascribed to the calendar year. "
                            + ("Read (S0407: FY2021 205.3 kt, FY2022 138.4 kt, FY2023 212.5 kt); +-2 percent." if read_cu else
                               ("ESTIMATE [A] +-20 percent: OD alone held at the FY2023 level; the 322 and 330 kt of copper_classes.md section 4.1 are BHP Copper South Australia totals (OD + Prominent Hill + Carrapateena after May 2023) and are not used; replace from BHP annual reports." if y >= 2024 else
                               "ESTIMATE [A] +-20 percent (copper_classes.md section 4.1); replace from BHP/WMC annual reports."))))
        h = how[y]
        txt = {"read": "Read (S0407 payable U3O8 x 0.848; +-2 percent).",
               "share": "ESTIMATE [A]: AUS u_production x FY2023 OD share 0.6154 (OD is the only conventional mill since Ranger stopped processing in January 2021); +-20 percent.",
               "ratio": "ESTIMATE [A]: prod_copper_od x FY2023 ratio 0.01359 t U per t Cu, +-30 percent."}[h.split("+")[0]]
        if h.endswith("+cap"):
            txt += " Bounds capped at the AUS conventional tonnage P x (1 - s) of the nuclear stream (NUCLEAR_SPEC 14.3 rule)."
        u_rows.append(arow("u_production_od", y, "AUS", *uu[y], "t", "compiled" if h.startswith("read") else "modelled",
                           "S0407", "D74(a). Olympic Dam uranium, t U, BHP fiscal year to calendar year. " + txt
                           + ("" if h.startswith("read") else " Replace from BHP/WMC annual reports.")))
        if y in aus_u:
            assert uu[y][1] <= float(aus_u[y]["value_central"]), (y, uu[y], aus_u[y]["value_central"])
        if y in aus_cu:
            assert cu[y][1] <= float(aus_cu[y]["value_central"]) * 1.0001, (y, cu[y], aus_cu[y]["value_central"])
    return cu_rows, u_rows


def main():
    counts = {}
    cols, reg, kept = build_registry()
    counts["data/reference/commodity_factors.csv"] = write("data/reference/commodity_factors.csv", cols, reg)
    fcols, fuel = build_fuel()
    counts["data/reference/commodity_fuel_inputs.csv"] = write("data/reference/commodity_fuel_inputs.csv", fcols, fuel)
    v = build_vocab()
    p = OUT / "data/reference/vocab.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(v, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    rcols, res = build_residues()
    counts["data/reference/residue_types.csv"] = write("data/reference/residue_types.csv", rcols, res)
    scols, sbg = build_seepage_by_group()
    counts["data/reference/residue_seepage_by_group.csv"] = write("data/reference/residue_seepage_by_group.csv", scols, sbg)
    socols, src = build_sources()
    counts["data/sources.csv"] = write("data/sources.csv", socols, src)
    counts["data/factors/wind_solar.csv"] = write("data/factors/wind_solar.csv", header("data/factors/oil_gas.csv"), [])
    counts["data/activity/material_intensity.csv"] = write("data/activity/material_intensity.csv", ACT_COLS, build_intensity())
    cu, uu, uy = od_series()
    for y in sorted(uu):
        print("OD", y, round(cu[y][1]), [round(x) for x in uu[y]], uy[y])
    counts["data/activity/wind_solar_shares.csv"] = write("data/activity/wind_solar_shares.csv", ACT_COLS, build_shares(cu))
    cu_rows, u_rows = build_activity_appends(cu, uu, uy)
    for target, extra in (("data/activity/commodity_production.csv", cu_rows), ("data/activity/uranium.csv", u_rows)):
        counts[target] = write(target, header(target), read(target) + extra)
    # region-code fix in the Phase 1 seed (research file, staged copy)
    fp = "research/wind_solar/footprint_inputs.csv"
    raw = (ROOT / fp).read_bytes().decode("utf-8")
    assert raw.count(",AUS;MYS,") == 1 and raw.count(",CHN;MMR,") == 1
    fixed = raw.replace(",AUS;MYS,", ",MYS,").replace(",CHN;MMR,", ",CHN,")
    (OUT / fp).parent.mkdir(parents=True, exist_ok=True)
    (OUT / fp).write_bytes(fixed.encode("utf-8"))
    counts[fp] = len(read(fp))
    for k, n in counts.items():
        print(f"{n:7d}  {k}")
    print("draft rows kept before the OD rewrite:", kept)


if __name__ == "__main__":
    main()
