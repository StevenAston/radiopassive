# Seepage fractions for `residue_types.csv` (`seepage_per_a_low/central/high`)

Research notes for Radiopassive, Option A. Written 2026-10-26. Nothing outside `research/seepage/` was edited.

Files in this folder:

- `notes.md` (this file)
- `proposed_seepage.csv`: one row per residue type (all 33), status `proposed` or `gap`
- `sources_seepage.csv`: 22 new sources, S0950 to S0971, same columns as `data/sources.csv`

## 0. Headline

- 33 residue types: **15 proposed triples**, **18 gaps**. Of the 15, one is grade B (a measured anchor agrees with the model), eight are grade C (model plus bench or qualitative evidence), six are grade D (analogue extension, no residue-specific evidence). Grades are defined in section 3.
- The central value for Ra-226 in a granular mineral residue comes out at about $6\times10^{-6}\ \mathrm{a^{-1}}$ (range $7\times10^{-7}$ to $6\times10^{-5}$), **three orders of magnitude below a "1 % per year" prior**. The only measured whole-facility figures I found (Elliot Lake flooded uranium tailings) give $3.6\times10^{-6}$ and $5.3\times10^{-6}\ \mathrm{a^{-1}}$ and agree with the model.
- Only two things come close to 1 % per year: potassium held as soluble salts (biomass ash, probably kiln dust) and, at high pH, uranium. The single-triple-per-residue schema therefore hides a **factor of about 30 between U and Ra** (section 4). That is the most consequential finding for the engine design.
- No residue type has a field-measured long-term seepage fraction on more than one site. Everything else is modelled from soil-derived Kd values and a generic hydrology.

## 1. What Steve's four PDFs are, and what I took from them

| File | What it is | Used? |
|---|---|---|
| `almahayni2018.pdf` (S0950) | Accepted manuscript, Almahayni and Vanhoudt, J. Hazard. Mater. 2018. HYDRUS-1D screening of U, Th and Ra leaching from fly-ash-stabilised road subbase (Wisconsin STH 60). | **Yes, main source for the ash model.** Table 1 (hydraulics), Table 2 (activities), Table 3 (Kd), Table 4 (leachate maxima), section 3.4 (leachate flux 7 to 100 mm/a). Caveat: the authors deliberately took Kd at 10 % of the Yu et al. geometric mean, and say Kd data for fly-ash/soil mixtures are lacking. |
| `1-s2.0-S0147651323014094-main.pdf` (S0951) | Chen et al. 2024, toxicology review of fly ash and leachate. | **No numbers.** Section 2.2.3 is qualitative (radionuclides silicate-bound, adsorbed or dissolved) and mislabels Rn-222/Rn-220 as ruthenium. Do not cite it for radionuclide behaviour. |
| `41598_2025_Article_86591.pdf` (S0952) | Xu et al. 2025, Sci. Rep. Soil- and ash-column tests and HYDRUS-1D for Pb, Ni, Cd, Cr(VI) from compacted fly ash at Fenyang, Shanxi. | **Context only.** Liner specification (1.5 m clay, $K<10^{-9}\ \mathrm{m\,s^{-1}}$) and mean rainfall 419.8 mm/a. Heavy metals, no radionuclides. |
| `EPA-HQ-OLEM-2020-0107-1384_content.pdf` (S0953) | The American Coal Ash Association 2024 CCP production and use survey filed in the EPA docket. | **No seepage content.** Production and use tonnages only (2024: fly ash 24.7 Mt, bottom ash 7.7 Mt, FGD gypsum 16.9 Mt). Useful for the stock side, not this task. |

Two further files in the same import folder (`2024-Production-and-Use-Charts.pdf`, `V.f.2.pdf`) were not part of the brief and were not opened.

## 2. Method per residue type

The seepage fraction $s$ is the annual fraction of the impounded activity that leaves the residue in water. I did not treat radon, and I did not treat transit time through the vadose zone or aquifer (see risk 2 in section 7).

Four methods are used. Each proposed row says which.

**M1, Kd-retardation flush (default for granular mineral residues).** A first-order, well-mixed flush of a deposit of thickness $H$, infiltration $I$, bulk density $\rho_b$, volumetric water content $\theta$ and distribution coefficient $K_d$:

$$s=\frac{I}{H\,(\theta+\rho_b K_d)}$$

This is the same thing as the leachate-concentration form $s=qAC/(M a_{\mathrm{solid}})$ with $C=a_{\mathrm{solid}}/K_d$ and $M=\rho_b H A$, when $\rho_b K_d\gg\theta$. For a nuclide that is not sorbed ($K_d=0$) it reduces to $I/(H\theta)$, the pore volumes flushed per year.

**M2, measured leached fraction per unit liquid-to-solid ratio.** If a column or batch test leaches a fraction $F$ at a liquid-to-solid ratio $L/S$ (L/kg), take $dF/d(L/S)\approx F/(L/S)$ and multiply by the $L/S$ the deposit receives per year:

$$s=\frac{F}{L/S}\times\frac{1000\,I}{H\,\rho_b}\qquad (I\ \text{in m/a},\ \rho_b\ \text{in kg/m}^3)$$

This assumes the first $L/S$ increments are representative (S0225 reports later leachates are lower by a factor of 2 or more, so it is slightly conservative).

**M3, measured load over inventory.** $s=L/(M a)$ with $L$ the measured annual load (Bq/a), $M$ the residue mass and $a$ its specific activity.

**M4, solubility limit (gypsum).** When the carrier phase dissolves and the nuclide goes with it: $s=I\,C_{\mathrm{sat}}/(H\,\rho_b)$, with $C_{\mathrm{sat}}$ the carrier's saturation concentration.

### Parameter ranges (all inputs sourced or flagged)

| Parameter | Range used | Basis |
|---|---|---|
| Infiltration $I$ | 0.007 to 0.1 m/a (7 to 100 mm/a; 0.3 to 4 in/a), log-uniform; central 0.03 m/a | Field lysimeter leachate flux under fly-ash-stabilised subbase, minimum and maximum (S0950 section 3.4). The central matches a 1.5 m clay liner with $K\approx10^{-9}$ m/s at unit gradient: $10^{-9}\times3.156\times10^{7}=0.032$ m/a (S0952). |
| Thickness $H$ | 4 to 15 m (13 to 49 ft), log-uniform; central 10 m (33 ft) | Mean tailings thickness derived from S0956 Table 1 (mass / area / 1500 kg/m³): Stanleigh 3.8 m, Nordic 7.5 m, Panel 8.1 m, Quirke 14.6 m. US average CCR impoundment 20 ft (6 m) and landfill over 40 ft (12 m) (S0213, 80 FR 21302, section I.A). |
| Bulk density $\rho_b$ | 1000 to 1600 kg/m³ (62 to 100 lb/ft³) | Assumption (Almahayni uses 1540 for subgrade and aquifer, S0950 Table 1). The 1500 in the thickness derivation is the same assumption. |
| Water content $\theta$ | 0.35 | Saturated water content, subbase (S0950 Table 1). |
| $K_d$ Ra | 71 to 2500 L/kg | Low = Almahayni's deliberately reduced subbase value (S0950 Table 3). High = IAEA TRS 472 soil mean (S0954 Table 14; range 12 to 9.5e5). |
| $K_d$ U | 1 to 200 L/kg | High = TRS 472 soil mean 200. Low reflects carbonate complexation at pH 9 to 10 (EPA Table 5.17: below 1 to 5 mL/g) and Almahayni 6.8 (S0955, S0950). |
| $K_d$ Th | 31 to 1900 L/kg | Almahayni 31 (reduced) to TRS 472 mean 1.9e3. EPA Table 5.15 allows 20 to 1.7e5 mL/g by pH. |
| $K_d$ Pb | 200 to 20 000 L/kg | TRS 472 mean 2.0e3 divided and multiplied by its GSD of 9.9 (S0954). |
| $K_d$ Po | 39 to 1134 L/kg | TRS 472 mean 2.1e2, GSD 5.4. |
| $K_d$ K | 0.7 to 56 L/kg | TRS 472 min and mean × GSD (13 × 4.3). Used only for silicate-held K. |
| Gypsum $C_{\mathrm{sat}}$ | 2.5 to 3.1 kg/m³ | 0.0147 to 0.0182 mol/L as CaSO₄·2H₂O (S0964; my mass conversion). |

Low, central and high for M1 and M4 rows are the 5th, 50th and 95th percentiles of $4\times10^{5}$ draws, each parameter log-uniform in its range (seed 20261026). They are **not** statistical confidence limits; they are the spread produced by the sourced parameter ranges alone.

### Worked examples

**M1, coal fly ash, Ra-226, central parameters.** $I=0.03$ m/a, $H=10$ m, $\rho_b=1300$ kg/m³, $K_d=420$ L/kg (geometric mean of 71 and 2500) $=0.42$ m³/kg, $\theta=0.35$:

$$s=\frac{0.03}{10\,(0.35+1300\times0.42)}=\frac{0.03}{10\times546.35}=5.5\times10^{-6}\ \mathrm{a^{-1}}$$

The Monte Carlo median is $6.4\times10^{-6}$. For U with $K_d=14$: $s=0.03/[10\,(0.35+18.2)]=1.6\times10^{-4}$.

**M3, uranium tailings, Elliot Lake (S0956, S0957).** Ore grade 2.1 lb per short ton (footnote in S0956; I read it as lb U₃O₈ per short ton, 0.105 % U₃O₈; if it is lb U the figure rises by 18 %). U-238 in ore: $1.05\ \mathrm{kg\,U_3O_8/t}\times0.848\times12.35\ \mathrm{kBq/g\ U}=11.0$ Bq/g. Taking Ra-226 in tailings equal to that (Ra extraction in the mill is about 0.5 %, S0960):

- Quirke: 42 Mt gives $4.6\times10^{14}$ Bq. The 2004 untreated water-cover load of 77 Bq/s is $2.4\times10^{9}$ Bq/a. So $s=5.3\times10^{-6}\ \mathrm{a^{-1}}$.
- Panel: 15 Mt gives $1.6\times10^{14}$ Bq. The 19 Bq/s load is $6.0\times10^{8}$ Bq/a. So $s=3.6\times10^{-6}\ \mathrm{a^{-1}}$.
- Cross-check on units: S0957 plots annual loads per tailings area in MBq/yr on a 0 to 2000 axis, and 77 Bq/s is 2430 MBq/a, so the scale is consistent. I could not read the plotted values from the text layer.

**M2, oil-field barite scale (S0961, S0225).** Swann et al.: 0.11 % of Ra leached in 1 L through a $0.9\times15$ cm bed. The solid mass is not stated; at 1.5 to 2.5 g/cm³ the bed holds about 14 to 24 g, so $L/S\approx40$ to $70$ L/kg (I use 55). $F/(L/S)=2\times10^{-5}$ per L/kg. At median hydrology the deposit receives $1000\times0.03/(10\times1300)=0.0023$ L/kg per year (Monte Carlo median 0.0027), so $s\approx5\times10^{-8}$. S0225's type A (Ba-carrier) deposits give 0.004 % at $L/S=10$, i.e. $4\times10^{-6}$ per L/kg and $s\approx1\times10^{-8}$.

**M4, FGD gypsum.** $s=0.03\times2.8/(10\times1000)=8.4\times10^{-6}$ at central values; Monte Carlo median $9.3\times10^{-6}$. It assumes Ra dissolves congruently with Ca; Ra re-uptake by barite or sorption lowers it.

## 3. Proposed triples

Column "grade": **B** = model plus at least one independent measured anchor within about a factor of 3 of the central value. **C** = model with sourced generic parameters plus bench-scale or qualitative residue-specific evidence. **D** = analogue extension or generic model only, no residue-specific evidence. All are `basis = modelled`. Driver group means the group whose long-term inventory the triple is meant for (section 4).

| Residue type | Driver | Low | Central | High | Method | Grade | Sources |
|---|---|---|---|---|---|---|---|
| `u_tailings` | Ra226+ (Th230 parent) | 7e-7 | 5e-6 | 6e-5 | M3 anchor, M1 cross-check | B | S0956, S0957, S0958, S0959, S0960, S0954, S0950 |
| `coal_fly_ash` | Ra226+ | 7e-7 | 6e-6 | 6e-5 | M1 | C | S0950, S0954, S0213, S0200, S0225 |
| `coal_bottom_ash` | Ra226+ | 7e-7 | 6e-6 | 6e-5 | M1 (analogue) | D | S0950, S0954, S0213 |
| `coal_fgd_residue` | Ra226+ | 7e-7 | 7e-6 | 4e-5 | M4 + M1 | C | S0964, S0213, S0950, S0954 |
| `coal_washery_refuse` | Ra226+ | 7e-7 | 3e-6 | 6e-5 | M2 bound + M1 | C | S0225, S0950, S0954 |
| `coal_mine_water_sludge` | Ra226+ | 3e-9 | 4e-7 | 8e-5 | M2 (types A and B) | C | S0225, S0968, S0969, S0962 |
| `coal_domestic_ash` | Ra226+ | 7e-7 | 6e-6 | 6e-5 | M1 (analogue) | D | S0950, S0954, S0967 |
| `og_scale` | Ra226+ | 3e-9 | 3e-8 | 4e-6 | M2 | C | S0961, S0225, S0962, S0971 |
| `og_sludge` | Ra226+ | 1e-8 | 5e-8 | 4e-6 | M2 | C | S0961, S0962, S0225 |
| `ree_tailings` | Th232 | 1e-6 | 1e-5 | 1e-4 | M1 (Th) | D | S0963, S0955, S0954, S0950 |
| `red_mud` | Th232 | 1e-6 | 1e-5 | 1e-4 | M1 (Th) + qualitative | C | S0963, S0955, S0954 |
| `metal_tailings` | Ra226+ | 7e-7 | 5e-6 | 6e-5 | analogue of `u_tailings` | D | S0956, S0957, S0958, S0950, S0954 |
| `iron_ore_tailings` | Ra226+ | 7e-7 | 6e-6 | 6e-5 | M1 generic | D | S0950, S0954 |
| `biomass_ash` | K40 | 2e-3 | 1e-2 | 4e-2 | M1 unretarded flush | C | S0965, S0954 |
| `peat_ash` | Ra226+ | 7e-7 | 6e-6 | 6e-5 | M1 (analogue) | D | S0950, S0954 |

Row-specific reasoning is in the `notes` column of `proposed_seepage.csv`. Points worth stating here:

- **Seven rows carry an identical or near-identical Ra triple**: fly ash, bottom ash, domestic ash, iron-ore tailings and peat ash are identical, and metal tailings and uranium tailings differ only in the central (5e-6). That is a finding, not a coincidence: with one hydrology and one Ra $K_d$ range, M1 cannot tell these residues apart. The only discriminating evidence is for uranium tailings (measured), barite sludges (leach tests) and gypsum (solubility).
- `coal_mine_water_sludge` has the widest span (five orders of magnitude) because the sludge is one of two different Ra hosts: Ba-carrier sulphate (very insoluble) or adsorbed Ra on sediment (leaches 5 to 7 % at $L/S=10$, S0225). The central is a geometric mean, chosen for want of a mix ratio.
- `biomass_ash` is for K-40 because Ra226+ is a minor share of its activity. Under D44 wood-ash natural nuclides are a memo series, so the triple matters only if the stream counts them.

## 4. Per-nuclide-class differences (for Steve's schema decision)

The schema allows one triple per residue type, but the engine applies seepage to every group in the impounded stock. The classes below behave very differently. M1 medians use the generic hydrology above (granular, near-neutral to alkaline ash-like medium); $t_b=H(\theta+\rho_b K_d)/I$ is the plug-flow breakthrough time at central parameters.

| Class (engine group) | $K_d$ range (L/kg) | $s$ P5 | $s$ P50 | $s$ P95 | Relative to Ra (P50) | $t_b$ (a) | Comment |
|---|---|---|---|---|---|---|---|
| U-238, U-234 (`U238+`, `U234`) | 1 to 200 | 1.1e-5 | 1.9e-4 | 2.9e-3 | **×29** | 6 200 | Carbonate complexation above pH 8 drives $K_d$ to about 1 mL/g (S0955), and S0200 says alkaline fly-ash leachate raises U solubility. Almahayni's modelled leachate gives $s_U=3\times10^{-4}$ to $7\times10^{-3}$ for a thin layer (section 6). |
| Th-230, Th-232 (`Th230`, `Th232`) | 31 to 1900 | 9.9e-7 | 1.1e-5 | 1.3e-4 | ×1.7 | 1.1e5 | Strong pH dependence (S0955 Table 5.15). Red-mud Th immobile over 12 months (S0963). The range is probably conservative for refractory hosts. |
| Ra-226 (`Ra226+`) | 71 to 2500 | 6.9e-7 | 6.4e-6 | 5.9e-5 | ×1 | 1.8e5 | Controlled by (Ra,Ba)SO₄ where sulphate is present (S0958, S0225); released when sulphate is depleted (S0957). |
| Ra-228 (`Ra228+`) | as Ra | as Ra | as Ra | as Ra | ×1 | 1.8e5 | 5.75 a half-life: decay beats transport in all but the shallowest layers, so its seepage is nearly irrelevant. |
| Pb-210 (`Pb210+`) | 200 to 20 000 | 1.0e-7 | 1.3e-6 | 1.8e-5 | ×0.2 | 8.7e5 | Mostly grown in place from Ra; leached Pb decays (22 a) long before it leaves. |
| Po-210 (`Po210`) | 39 to 1134 | 1.5e-6 | 1.3e-5 | 1.1e-4 | ×2 | 9.1e4 | 138 d half-life. A seepage fraction is meaningless as a transport rate; Po-210 is sustained by Pb-210 in place. |
| K-40, silicate-held (`K40`) | 0.7 to 56 | 3.4e-5 | 4.1e-4 | 4.3e-3 | ×64 | 2 700 | Upper bound only; K in glass or feldspar is dissolution-limited and probably far lower. No data. |
| K-40, soluble salts (biomass ash, kiln dust) | 0 | 2.4e-3 | 9.8e-3 | 3.9e-2 | **×1500** | 117 | Flush-limited. Loose field ash lost 50 to 60 % of K in a year (S0965). |
| Cs-137 (fallout in ash) | not assessed | | | | | | Memo series under METHODS 5.2 (D43); not assessed. |

$t_b$ for Ra, Th, Pb and Po far exceeds the Ra-226 half-life (1600 a; mean life 2300 a) at central parameters. In a dry deposit leaching from the top down, almost no Ra would reach the base before decaying. The M1 values are therefore **upper bounds for base leakage of strongly retarded nuclides**; they are realistic only where Ra leaves through the top or sides (water-covered tailings, dams, shallow lenses, preferential paths). This is why the Elliot Lake loads, which include surface exchange across a water cover, agree with M1 and should not be read as proof for dry stacks.

**Why a single triple understates the activity leaving.** Using Almahayni's Table 2 fly-ash activities (U-238 and U-234 340 Bq/kg each, Th-230 131, Ra-226 330) with the group multipliers from `groups.csv` (`U238+` 3.0016, `U234` 1, `Th230` 1, `Ra226+` 6) and the M1 medians above, the decay-weighted mean seepage fraction is

$$\bar s=\frac{\sum_i m_i A_i s_i}{\sum_i m_i A_i}=\frac{1020\,(1.9\times10^{-4})+340\,(1.9\times10^{-4})+131\,(1.1\times10^{-5})+1980\,(6.4\times10^{-6})}{3471}\approx7.7\times10^{-5}\ \mathrm{a^{-1}}$$

about 12 times the Ra-only central. If the engine applies the Ra triple to all groups, it will undercount U-chain activity moved to Liberated (and the Th-230/Ra-226 later grown in Liberated from it) by about that factor for fly ash. Conversely, weighting by decay energy (`e_per_head_decay_mev`: `Ra226+` 27.1, `U238+` 5.18, `U234` 4.86) shifts the weight back towards Ra. Which weighting is right depends on what the W conversion measures; that is Steve's call.

**Suggested extension (for Steve to decide).** Add a long table `residue_seepage_by_group.csv` with columns `residue_type, group, seepage_low, seepage_central, seepage_high, basis, source_ids`, falling back on the residue-type triple where a group row is absent. A minimum viable version is a relative-multiplier vector by class, e.g. U ×30, Th ×2, Ra ×1, Pb ×0.2, Po ×2, K (soluble) ×1500, applied to the residue's Ra triple. Both keep the current `residue_types.csv` columns intact.

## 5. Gap register (18 residue types, no triple proposed)

| Residue type | Closest analogue | Analogue defensible? | Reason / where to look |
|---|---|---|---|
| `u_waste_rock` | `u_tailings` | No | Coarse, oxidising, preferential flow; U mobile, Ra not. Leads, none read: https://www.agriculture.gov.au/sites/default/files/documents/ssr166-radiological.pdf ; https://prod.camecoaustralia.com/sites/default/files/2024-03/Appendix_M3_-_Geochemical_Assessment_of_Tailings_and_Mine_Waste.pdf ; https://www.imwa.info/docs/imwa_2000/IMWA2000_35.pdf |
| `u_process_residue` | none | n/a | Fluoride/nitrate/sulphate matrices unlike tailings; no data. |
| `isl_pond_residue` | `og_sludge` (Ra solids only) | Partly | Lined evaporation ponds and deep-well disposal (Re-isolated, no seepage). Lead, not read: https://www.nrc.gov/reading-rm/doc-collections/nuregs/staff/sr1910/ |
| `coke_oven_residue` | none | n/a | No leaching data; activity side only (S0227). |
| `og_produced_water` | none | n/a | Liquid stock; injected water is Re-isolated by definition. A first-order fraction of a liquid stock is set by liner and evaporation, not $K_d$. |
| `og_drill_cuttings` | none | n/a | Low activity, mud matrix, mostly buried or injected. |
| `og_scaled_scrap` | `og_scale` | No | Rain on stored scrap, no deposit depth $H$; scale-on-steel dissolution rate not found. |
| `og_processing_residue` | `og_sludge` | No | Pb-210/Po-210 films and sulphide scale are chemically unlike Ra barite; Po-210 cannot take a $K_d$ flush. |
| `oil_sands_tailings` | none | n/a | Slurry ponds near crustal background; nothing located. |
| `oil_sands_coke` | none | n/a | Nothing located. |
| `ree_process_residue` | `coal_fgd_residue` (gypsum fractions); `ree_tailings` (Th cake) | Partly | Mixed matrix. Lynas LAMP review (S0970) is qualitative: https://www.oeko.de/oekodoc/1629/2013-002-en.pdf |
| `smelter_slag` | `coal_bottom_ash` | Partly | Glass-dissolution-limited, not sorption-limited; largely Dispersed as aggregate. Only datum seen is a tin-slag poster abstract whose units do not reconcile with its inventory (rejected): https://conferences.iaea.org/event/206/contributions/16951/contribution.pdf |
| `cement_kiln_residue` | `biomass_ash` (K only) | Physical bound only | Soluble alkali sulphates would behave like wood-ash K (about 1e-2 per a) but no kiln-dust leaching source was retrieved. |
| `other_commodity_residue` | `coal_fgd_residue` (M4) | Yes, if phosphogypsum | Undefined bucket; CaSO₄·2H₂O dissolution limit applies to phosphogypsum, not to other commodities. |
| `eol_waste` | none | n/a | No radionuclide inventory or leaching data. |
| `geothermal_scale` | `og_scale` | Sulphate (barite, celestine) scale only | Carbonate, silica and sulphide scale are more soluble or unknown (S0971, qualitative). Leads, not read: https://documentserver.uhasselt.be/handle/1942/48400 ; https://publications.jrc.ec.europa.eu/repository/handle/JRC138541 |
| `geothermal_brine` | none | n/a | Reinjected, so Re-isolated; no seepage by METHODS 5.1. |
| `biomass_domestic_ash` | `biomass_ash` (K) | No | Mostly spread or bagged to municipal waste; Impounded share and hydrology unknown. |

## 6. Cross-checks

1. **Elliot Lake loads over ingrown stock** (section 2): $3.6\times10^{-6}$ (Panel) and $5.3\times10^{-6}$ (Quirke) against the M1 range of $6.9\times10^{-7}$ to $5.9\times10^{-5}$. Both sit between the M1 P5 and median. Both come from flooded, untreated water-cover loads; the Ra inventory is derived, not measured.
2. **Local worst case at Quirke Cell 14** (S0958 Table 2): 3.01 Bq cm⁻² a⁻¹ in the anoxic vegetated zone. Stock per cm² with 14.6 m of tailings at 11.0 Bq/g and 1.5 g/cm³ is about 24 000 Bq/cm², giving $1.2\times10^{-4}$ locally. The shallow oxic zone (0.009 Bq cm⁻² a⁻¹) gives $4\times10^{-7}$. The M1 P95 ($5.9\times10^{-5}$) is within a factor of 2 of the anoxic bound. S0959 notes inter-cell leakage about three times design, which is exactly the kind of hydrology that pushes $I$ above my 0.1 m/a ceiling.
3. **Almahayni's modelled leachate** (S0950 Table 4, thin 0.3 m subbase with 10 % fly ash, solid activity from Table 2; my derivation): Ra-226 $s=2.6\times10^{-7}$ (low-leaching scenario, 7 mm/a) to $2.4\times10^{-4}$ (high-leaching peak, 100 mm/a). U-238 $s=3.1\times10^{-4}$ to $6.6\times10^{-3}$. Ra brackets the M1 range; U is above the M1 median ($1.9\times10^{-4}$) and the high scenario is above the M1 P95 ($2.9\times10^{-3}$), as expected from Almahayni's reduced Kd. These are modelled peaks, not measurements.
4. **Landfill leachate, Pennsylvania** (S0967): raw leachate at landfills that took oil and gas waste averaged 3.148 pCi/L (0.116 Bq/L) combined Ra-226 + Ra-228, no higher than at landfills that did not. With $I=0.03$ m/a, $H=10$ m, $\rho_b=1300$ kg/m³, $s=IC/(H\rho_b a)$ for NORM waste at 1000 Bq/kg is $2.7\times10^{-7}$ and at 100 Bq/kg $2.7\times10^{-6}$. These are upper bounds only if the leachate Ra came from the NORM; the report finds no link between Ra in leachate and oil and gas waste acceptance, so the real NORM contribution is smaller still.
5. **Bench leachability bounds on stock** (S0960, S0225): Jaduguda tailings gave about 0.5 % of Ra soluble in rain or distilled water; Ba-carrier deposits 0.004 % and adsorbed-Ra sediments 5 to 7 % at $L/S=10$. At the median $L/S$ of 0.0027 L/kg per year, reaching $L/S=10$ takes about 3700 a, by which time Ra-226 (half-life 1600 a) has decayed by a factor of about 5. So even the most leachable material in these tests would not be flushed within the engine horizon, consistent with Ra seepage of $10^{-6}$ to $10^{-5}$ per year.
6. **Sanity against 1 % per year.** A seepage fraction of $10^{-2}\ \mathrm{a^{-1}}$ removes half the stock in 69 years, so the residue would hold no memory of its past on the engine's century horizon. That is plausible only for fully soluble salts (K in wood-ash, kiln dust, perhaps Na and K sulphates) or for U in alkaline, low-$K_d$ media with high infiltration. For Ra, Th, Pb and Po every piece of evidence I have (measured loads, batch tests, Kd) lies between about $10^{-9}$ and $10^{-4}$.
7. **Plug-flow caveat** (section 4): $t_b$ for Ra in a dry 10 m deposit is about $1.8\times10^{5}$ a, so M1 overstates base leakage there. This check pulls the dry-stack values down, not up.

## 7. Uncertainty statement and top five risks

**Statement.** The proposed ranges describe the spread produced by the sourced ranges of infiltration, thickness, density and $K_d$, sampled log-uniformly. They do not include structural error: a first-order well-mixed flush, equilibrium sorption, no preferential flow, no change of chemistry with time (acid generation, sulphate depletion, carbonation), no transit time to surface water, and no extra loss routes such as dam breach (that is an event, not seepage). I would expect the true value for a given facility to fall within a factor of 10 of the central for a grade B row, within two orders of magnitude for grade C, and I would not defend a grade D row to better than three orders. For nuclides other than the driver, the section 4 table applies instead of the triple.

**Top five risks to the numbers.**

1. **Hydrology is generic, not residue-specific.** $s$ is linear in $I$. The 7 to 100 mm/a range comes from one road-subbase lysimeter study (S0950), supported by a liner specification (S0952). Unlined ponds with hydraulic head, leaking dams (Quirke inter-cell leakage was about three times design, S0959), mine-backfilled ash and humid climates can exceed 0.1 m/a by a factor of 10 or more, which scales every row up in proportion. Dry-climate covers would lower it.
2. **Kd is transferred from soils to residues and from batch to field.** TRS 472 and EPA Kd are for soils; Almahayni's own values are an admitted conservative guess; Ra control at Elliot Lake is by barite solubility, not sorption, and it shifted as sulphate fell (S0957). A pH or sulphate change can move Ra by one to two orders and U by more (S0955 Table 5.17). The delay to arrival at surface water is not credited, so the numbers are upper bounds on timing for strongly sorbed nuclides (section 4).
3. **One triple per residue, but nuclide classes differ by a factor of about 30 for U and about 1500 for soluble K.** For fly ash, the decay-weighted mean is about 12 times the Ra-only central (section 4). The schema choice, not the data, may be the largest source of error in the Liberated totals.
4. **Thin measured evidence.** The only whole-facility anchor is one district of flooded uranium tailings (S0956, S0957, S0958), and its Ra inventory is derived from an ore grade whose unit is ambiguous in the source. No ash-pond, red-mud, REE or metal-tailings Ra, Th or U load was found. Six of the 15 proposed rows are an analogue or generic extension (grade D) and are labelled as such.
5. **Leach-test extrapolation.** Swann's columns ran at roughly 2.4 mm/h, thousands of times field infiltration, with an estimated $L/S$ of 40 to 70 L/kg; the "about 20 % solubilised" figure is the authors' own inference from partition coefficients and I did not use it as a rate (the high value uses the measured 0.36 %). Batch tests with 10 g/L NaCl (S0225) are not rainwater. Linear scaling of leached fraction with $L/S$ ignores depletion and kinetics.

## 8. Sources, quality and what could not be read

| Tier | Sources | Note |
|---|---|---|
| Regulator | S0967 (PA DEP 2026), S0213 (EPA CCR rule, existing) | Cross-check and geometry only. |
| Compilation | S0954 (IAEA TRS 472), S0960 (IAEA TECDOC-370) | Soil Kd; one-off 1980s batch result. |
| Agency | S0955 (EPA Kd), S0961 (DOE Mississippi report), S0965 (Forest Research), S0200 (USGS, existing) | S0965 undated; year approximated. |
| Peer-reviewed | S0950, S0958, S0963, S0962, S0964, S0966, S0968, S0951, S0952 | S0962, S0964, S0966, S0968 read at abstract level only. |
| Grey | S0956, S0957, S0959 (operator reports, licence monitoring), S0225 (existing), S0953, S0969, S0970, S0971 | S0225 supplies the most useful bench data and is an ENA-NORM conference paper. |

Existing registry IDs reused: S0200, S0213, S0225, S0227.

**Could not be read or rejected:**

- PubMed Central page for Gamaletsos 2016 sits behind a browser check; I read the full text through Europe PMC instead (https://www.ebi.ac.uk/europepmc/webservices/rest/PMC4761986/fullTextXML).
- NRC ML19322C881 returned a non-PDF page: https://www.nrc.gov/docs/ML1932/ML19322C881.pdf
- NRCan open-file gid_325831 returned 404: https://download-telecharger.services.geo.ca/pub/nrcan_rncan/publications/STPublications_PublicationsST/325/325831/gid_325831.pdf
- Steenari, Karlsson and Lindqvist (1999), Biomass and Bioenergy 16, 119-136 (the primary for the wood-ash K loss): record at https://research.chalmers.se/en/publication/172502 ; I relied on Forest Research's summary of it (S0965).
- Goronovski et al. (2020), J. Clean. Prod., radiological assessment of bauxite residue: https://doi.org/10.1016/j.jclepro.2020.125165 (only a web summary seen).
- Publisher full texts for S0962, S0966, S0968 (abstract level only).
- Not located at all: NUREG-0706 and NUREG-1910 seepage assumptions, Argonne ANL/EAD-2 landfill leaching parameters (OSTI abstract page https://www.osti.gov/biblio/750601 has no parameters), any Cu, Zn, Pb, Ni or Fe tailings radionuclide-seepage study, any measured ash-pond radionuclide load.
- Lauer et al. 2015 (S0216 in the registry) was read in full; it has no leaching data and says so.
- Semantic Scholar, PubMed and Consensus tools were not available in this session (no tool-search facility); web search, direct fetch and the Europe PMC REST interface were used instead.
- Wikipedia and Grokipedia were not used.
