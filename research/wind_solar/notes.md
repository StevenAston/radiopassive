# Wind and solar materials (stream 4): Task 1.5 notes

Files in this folder: `bibliography.md`, `availability.csv` (368 rows), `sources_task15.csv` (S0400-S0429, 30 sources), plus working tables for Tasks 1.9, 2.x and 3.x: `material_intensity.csv` (157 rows), `footprint_inputs.csv` (22 rows, seed values for `commodity_factors.csv`), `ree_end_use_shares.csv` (21 rows), `co_product_inputs.csv` (15 rows). UNSCEAR sources are cited by ID (S0001, S0005, S0008) and the coal task's IAEA TRS 419 as S0202.

All activity values below are **head activities** (Th-232, U-238, Ra-226 and so on). The METHODS 3.2 multiplier (10 for the Th-232 series, 14 for U-238) is applied in the pipeline, never here. "Basis modelled" means my own arithmetic from the cited inputs: the method is given in the `derivation_and_caveats` column of `footprint_inputs.csv`.

## 1. Method

- Read in full or in the relevant tables: JRC 2020 and 2023 (wind and PV chapters), IAEA SRS 68, the IAEA NORM VI Bayan Obo paper, IAEA TRS 419 (metal chapters), DOE 2022 magnets report, IEA 2021 and 2026, UNSCEAR 1988 Annex A (Tables 42-47 read from the page image), UNSCEAR 2000 Annex B Tables 27-28, BHP's 20-F and Olympic Dam EIS extract, USGS MCS 2025 (REE, tellurium).
- Per-tonne footprints were built from measured activity concentrations (Bq/g) times residue mass per tonne of commodity, or from published airborne releases of a reference plant divided by its throughput.
- Where a published input was missing (plant capacity, ore per tonne metal, recovery) I used a stated assumption and marked the row `modelled`; these are listed in section 9.

## 2. Material intensity (t per GW), by technology and vintage

Full table: `material_intensity.csv`. Headline values (JRC 2020, 2018 vintage, S0400; ranges are across turbine types or scenarios):

| Technology | Material | t/GW | Notes |
|---|---|---|---|
| Wind, all types | Steel | 107 000-132 000 | plus cast iron 18 000-20 800 |
| | Concrete | 243 000-413 000 | DD-PMSG (offshore proxy) lowest, GB-PMSG highest; JRC Table 2 prints the range as 243 500-413 000 but the DD-PMSG cell as 243 000 |
| | Copper | 950-5 000 | DD-EESG 5 000, DD-PMSG 3 000, GB-DFIG 1 400, GB-PMSG 950; array cables excluded |
| | Aluminium | 500-1 600 | |
| | Glass/carbon composites | 7 700-8 400 | glass fibre at most 88% |
| | Zinc | 5 500 | |
| | Cr / Mo / Ni | 470-580 / 99-119 / 240-440 | |
| Wind, DD-PMSG | Nd / Pr / Dy / Tb | 180 / 35 / 17 / 7 | |
| Wind, GB-PMSG (hybrid) | Nd / Pr / Dy / Tb | 51 / 4 / 6 / 1 | |
| Wind, GB-DFIG | Nd / Dy | 12 / 2 | small magnets in tower fixtures |
| Wind, NdFeB magnet mass | | 250-600 kg/MW (S0414); about 620 kg/MW for DD-PMSG implied by JRC Nd at 29% | the two differ by about 1.5x at the top; JRC element splits are themselves inconsistent (Nd 29% gives 621 kg/MW, Dy 4% gives 425, B 1% gives 600) and JRC text quotes 186 kg/MW Nd for direct drive vs 62 for hybrid |
| PV, balance of system and module (2018) | Concrete / steel / glass | 60 700 / 67 900 / 46 400 | from Jean et al. 2015 via JRC |
| | Aluminium / copper / plastic | 7 500 / 4 600 / 8 600 | |
| c-Si | Silicon (solar grade) | 16 000 (2004); 4 000 (2018); 2 100-3 000 expected 2028 | thrifting of 4x in 14 years |
| c-Si | Silver | 84 (2010, Nassar); 13-18 (2020 Nassar); 20 (2018-19); 4-11 (2030 JRC) | per cell 400 mg (2007), 130 (2016), 111 (2019) |
| CdTe (2018) | Te / Cd | 35-95 / 35-85 | |
| CIGS (2018) | In / Ga / Se / Cu | 10-27 / 3-7 / 22-60 / 20-24 | |
| a-Si (2018) | Si / Ge | 150 / 48 | |

Vintage coverage: JRC gives 2018 with 2030 and 2050 scenarios; earlier vintages exist only for silicon (2004), silver (2007 per cell, 2010 per GW) and the Nassar 2010 values for Te, Cd, In, Ga, Se. There is **no vintage series for wind** (one 2018 snapshot, plus UNSCEAR's 85 000 t steel per GW(e) from White and Kulcinski, S0001): the older, geared designs are represented only by the GB-DFIG column.

Onshore versus offshore: JRC does not tabulate them. Proxies are DD-PMSG for offshore and GB-DFIG for onshore (S0400, S0402). Permanent-magnet penetration in 2020 installs: offshore 72% worldwide (nearly 100% in the EU), onshore 22% worldwide (13% EU) (S0401). Offshore needs more copper for array and export cables, outside the JRC boundary.

## 3. Per-tonne footprints (own residues), with ranges

Seed values are in `footprint_inputs.csv` (Bq per tonne of refined commodity, head activity, before co-product allocation).

| Commodity / residue | Group | Low | Central | High | Basis and key input |
|---|---|---|---|---|---|
| REE oxide, Bayan Obo tailings | Th232 | 1.1e8 | 1.5e8 | 1.8e8 | 113 t tailings per t REO at 1.0-1.6 Bq/g (high = 113 x 1.6 = 1.81e8); ore route agrees (S0404, S0405) |
| REE, Bayan Obo process residue (RE slag) | Th232 | 7.6e6 | 1.2e7 | 2.0e7 | concentrate 5.3-10 Bq/g at 50-70% REO |
| REE, Mount Weld to Lynas WLP | Th232 | 6e6 | 1.5e7 | 3.7e7 | ore 0.075% ThO2 at 17-18% REO; WLP measured 6.2 Bq/g, about 75 000 t/a (S0406) |
| REE, ionic clay | Th232 | 1.8e7 | 8.9e7 | 3.6e8 | ThO2 0.005%, REO 0.05-1%; soil-like concentrations, large tonnage |
| REE, monazite route | Th232 | 2.4e8 | 5e8 | 9.8e8 | monazite 4-12% Th, 50-68% REO (S0429); conversion mine |
| Copper, generic tailings | U238+ | 3e6 | 2.4e7 | 1.9e8 | 100-500 t ore per t Cu, 30 Bq/kg to 0.37 Bq/g (S0008, S0202); wide, judgement central |
| Copper, Olympic Dam tailings | Ra226+ | 3.5e8 | 3.8e8 | 7.6e8 | 50.8 t ore per t Cu, 6.8-8.2 Bq/g (15 Bq/g 1989-93) (S0407, S0408); 4-10x generic copper |
| Copper smelter off-gas | Pb210+, Po210 | 2.3e4 | 4e4 each | 7e4 | UNSCEAR 1988 reference smelter 7000 MBq/a each; **capacity assumed** 100-300 kt Cu/a |
| Aluminium, red mud (3.2 t per t Al) | Th232 | 3.2e5 | 1.3e6 | 1.8e6 | 100-550 Bq/kg (compiled range 87-1350) |
| | Ra226+ | 3.2e5 | 9.6e5 | 3.2e6 | |
| | U238+ | 3.2e5 | 9.0e5 | 1.9e6 | |
| Steel, stack (BF-BOF) | Pb210+ / Po210 | 5e3 / 8e3 | 1.0e4 / 1.7e4 | 1.5e4 / 2.5e4 | UNSCEAR 2000 Table 28 per t ore x 1.4 t ore per t steel |
| Cement, kiln stack | Po210 | 2e4 | 3.9e4 | 7.8e4 | UNSCEAR 2000 Table 28 per t throughput; fuel part not separable |
| Steel, embedded coal (0.8 t/t) | U238+, Th232 | 8e3 | 1.3e4 | 2e4 | coal 10-25 Bq/kg; replace with Task 1.3 factors |

Not found (gaps, with proposed methods in `availability.csv`): iron-ore tailings and blast-furnace slag per tonne steel (slag is 0.15 Bq/g U-series and Th-series, S0005, but slag tonnage per tonne steel is not sourced here); copper smelter slag per tonne Cu (slag 0.4-2 Bq/g Ra-226, S0423); alumina-plant and reduction-cell Pb-210/Po-210 per tonne (UNSCEAR 1988 Table 45 gives MBq/a for one plant, capacity not stated); metallurgical silicon (reductant masses in S0422 Tables 2-4 not read; electricity 11-13 MWh/t, electrodes about 100 kg/t); glass, glass fibre, zinc, nickel, chromium, molybdenum, tin. Silver, tellurium, selenium, indium, gallium and cadmium have no own residue: they are by-products and their share is allocated from the host chain (copper, lead-zinc, gold, alumina) by D6.

Other residue activities for context (S0423, S0404, S0405): REE-extraction sludges Ra-228 0.6-10 000 Bq/g; Bayan Obo alloy slag gross alpha 2.9-5 Bq/g; iron-smelting sludges Pb-210 12-100 Bq/g; Bayan Obo blast-furnace slag Th-232 0.5-1.6 Bq/g (mixed down with fly ash and cement to 0.2-0.3 Bq/g in bricks and cement).

## 4. Bayan Obo thorium: verification

- Steve's figure of about 0.04% ThO2 is confirmed as a representative value but not as a single number. IAEA SRS 68 (S0404) states "the ore is generally considered to contain 0.04% ThO2 [Chinese ref], corresponding to a Th-232 activity concentration of 1.4 Bq/g", with a higher 2.6 Bq/g (about 0.07% ThO2) also reported. The Chinese national study (Wu et al., S0405) gives a range **0.01-0.05% ThO2 and 0.0005-0.002% U3O8**, and an average of **0.032% ThO2** for the 600 Mt Main and East mine ore (34% Fe, 5% REO). SRS 68 Table 87 lists 0.04 and 0.07 (derived).
- Conversion used throughout: 1 g ThO2 = 3566 Bq Th-232; 1 g U3O8 = 10 470 Bq U-238 (S0404).
- The REE-mineral phase is a bastnaesite plus thorium-deficient monazite. Th is not an ore-wide constant: it follows the monazite fraction.
- Distribution in processing (S0405 Table 12 and text): iron concentrate 0.0073% ThO2 (0.26 Bq/g; was 0.024% early on); REE concentrate 0.2% ThO2 (7.1 Bq/g); tailings 0.028-0.048% ThO2 (1.0-1.6 Bq/g Th-232, U-238 0.022); ferrous slag 0.5-1.6 Bq/g; REE oxide product 0.0069% ThO2. In iron-making 96-98% of the Th goes to slag, 0.1-0.5% to off-gas, 0.6-2.0% to liquid effluent.
- Inventories (to end 2006): tailings 149 Mt (6.55 Mt in 2006), blast-furnace slag 55 Mt, alloy slag 0.96 Mt, RE slag 261 000 t produced (437 300 t stored), waste rock 560 Mt. Tailings pond covers 11 km2. Waste-rock Th is above 1 Bq/g only near the ore boundary.
- Implied thorium per tonne REO produced is about 1.1e8-1.8e8 Bq Th-232 (about 1.5e9 Bq for the whole series); only about 8% of the Th follows the REE concentrate. This implies an overall REO recovery near 15% (my inference).
- Not reconciled: S0405 gives 100 000 t/a RE concentrate and also "more than 7000 t/a of REO" at BTISP; China-wide REO was 98 kt in 2004 with 59% from Bayan Obo (S0404). Bayan Obo REO output by year is needed from Task 1.9.

## 5. Co-product allocation inputs (D6)

Table: `co_product_inputs.csv`.

**Bayan Obo** (iron, REE, niobium). Quantities found for 2006: ore processed 12 Mt, iron concentrate 4.5 Mt, REE concentrate 100 kt, steel 9 Mt (S0405). No niobium output, no pre-2000 split, and no Chinese price series. **Bound A** (iron) and **Bound B** (REE) need only masses; the default needs unit values. DS140 gives only US market values; the REE price is a poor proxy for Chinese domestic prices before 2000.

**Olympic Dam** (copper, uranium, gold, silver). FY2021-23 from the BHP 20-F (S0407): FY2023 cathode 212.5 kt, gold 186 029 oz, silver 1089 koz, uranium 3406 t (as U3O8, unconfirmed), ore milled 10.8 Mt. At the price assumptions behind BHP's FY2023 resource estimates the value split is Cu 74.3%, Au 12.7%, U3O8 12.0%, Ag 1.0% (extractor's arithmetic, indicative only). Time series before FY2021 are not in hand.

**DS140 series needed** (S0410; series file names could not be checked because the USGS file pages return 403, so confirm against Steve's mirror): rare earths (production, apparent consumption, unit value); iron ore, pig iron and steel; niobium (columbium); copper; gold; silver; bauxite and aluminium; cement; silicon (metal, ferrosilicon); tellurium; selenium; cadmium; indium; gallium; zinc; lead; tin; nickel; chromium; molybdenum; zirconium. **Uranium is not confirmed to be in DS140**: a separate price series (e.g. an industry or government spot and contract price record) will be needed for the Olympic Dam split. Unit value in DS140 is the US price per tonne of apparent consumption, not a world or Chinese price.

## 6. REE end-use shares and solar REE

Table: `ree_end_use_shares.csv`.

- NdFeB magnet demand 2020 (S0413): total 119.2 kt; **wind 14.2% (16.9 kt)**, EVs 6.1%, consumer electronics 29.4%, industrial motors 30.2%, non-drivetrain vehicle motors 7.9%, other sintered 5.5%, bonded 6.7%. The DOE label says "offshore wind turbines"; whether onshore PM turbines are missing or included in "industrial" is unresolved. Projected high-growth shares: wind 36% in 2030 and 2050; EVs 29.5% and 35%.
- IEA 2026 (S0403): magnet rare-earth demand OUTSIDE CHINA is about 40 kt today, about 70 kt by 2040; global demand crosses 120 kt by 2030 and 175 kt by 2050.
- Earlier: 2015 wind 17% (23% in a six-sector subset), cars 43%, HDD 15%, EV/HEV 14% (S0414, incomplete statistics); 2006 magnets were 19% of REE consumption by mass (S0404 Table 1); 2008 about 26 kt REO into NdFeB.
- Gaps for sigma_c: no annual series 1990-2024 and no pre-2006 end-use split. Proposed method: wind magnet demand = annual capacity additions x PM penetration x magnet kg/MW (250-600) divided by annual NdFeB production, calibrated to the 2015 and 2020 shares. Heim and Vander Wal 2023 (S0416, not read) is the lead for a longer series.
- **Solar PV uses no rare earths** in the JRC 2020 and 2023 element lists (Si, Ag, Cd, Te, Cu, In, Ga, Se, Ge, Al, Sn, Pb and others). UNSCEAR 2016 mentions "small amounts of rare earth elements" in c-Si cells (paras 182-187) without any quantity; JRC does not support it. Set solar REE intensity to zero.

## 7. End of life

- Volumes: PV panel waste about 78 Mt cumulative by 2050 (S0417); blade waste 43.4 Mt cumulative by 2050 (range 21.4-69.4 Mt; includes manufacturing, testing and in-service waste as well as end of life), with more than 2 Mt of blade waste in 2050 (S0418); IEA says that by 2030 Europe (not the world) is set to generate about 50% of global end-of-life magnet feedstock from wind turbines and 25% from EV motors (S0403). By-year series are a gap (the IRENA full report and the IEA-PVPS tables were not opened).
- **Radiologically negligible, with this basis:** (i) end-of-life panels and blades are made of refined commodities, in which U and Th have been separated into residues during refining (for example 96-98% of Bayan Obo Th goes to iron-making slag, S0405); (ii) there is no new mobilisation: any activity associated with making the materials was counted at the commodity-supply stage; (iii) the one REE-bearing component, the NdFeB magnet, carries about 0.09 Bq/g Th-232 at most (REE oxide product 0.0069% ThO2 = 0.25 Bq/g, times about 35% oxide-equivalent in the magnet; my arithmetic), below the 1 Bq/g D21 threshold. Recycling-smelter off-gas Pb-210/Po-210 is a small fraction of the primary-smelter figures.
- Caveat for the orchestrator: if all end-of-life mass were assumed to carry soil-level activity (0.04 Bq/g), the cumulative activity to 2050 would be of order 4e15 Bq. The METHODS 10.3 test (0.1% of the stream total in every decade) would then depend on the comparison basis. The robust argument is the D21 threshold plus "already counted at supply", not a comparison of totals.

## 8. Radon exhalation inputs for epsilon

Residue types asked for: ree_tailings, ree_process_residue, red_mud, metal_tailings, iron_ore_tailings, smelter_slag.

Measured or published inputs:

- Emanation coefficient E (fraction of Rn atoms formed that leave the grain): mill tailings, rocks and soils 0.1-0.3, fly ash below 0.1 (S0203, from the Task 1.3 notes); **untreated dry red mud 0.20** (S0425); monazite grains 0.002 for Rn-222 and 0.0002 for Rn-220 (S0404 Table 26; the mineral is bound, ground tailings will be higher: no value found).
- Measured flux: Olympic Dam tailings 0.3-1.27 Bq/m2/s (mean 0.48; 2010 monitoring 0.3, 31 samples); completed tailings facility 13.9 MBq/s, 520 TBq/a (S0408; source quirk: 13.9 MBq/s is about 439 TBq/a, about 18% below the 520 TBq/a in Table 4 of the same document). Ore in the pit 2.5 Bq/m2/s unbroken, 12.5 broken.
- No measured flux found for REE tailings, red mud, iron-ore tailings or slag. Thoron (Rn-220) near the Bayan Obo disposal site was measured as potential alpha energy concentration only (S0405).

**Important finding for the engine (METHODS 5.2):** the provisional epsilon of 0.2 (0.05-0.35) equals the emanation coefficient, not the fraction that escapes from a thick deposit. In a deposit of depth H only a surface layer of thickness about the diffusion length L contributes to the flux, so

$$\varepsilon\approx E\,\frac{L}{H},\qquad \varepsilon=\frac{J\,A_{\text{area}}}{\lambda_{\text{Rn}}\,A_{\text{Ra}}}$$

where $J$ is the measured flux in Bq m$^{-2}$ s$^{-1}$, $A_{\text{area}}$ the surface area, $\lambda_{\text{Rn}}=2.1\times10^{-6}$ s$^{-1}$ and $A_{\text{Ra}}$ the Ra-226 inventory in Bq. With $L\approx1$-$2$ m for Rn-222 in unsaturated material and $H\approx5$-$30$ m, $\varepsilon\approx0.002$-$0.05$. Check against Olympic Dam (extractor's arithmetic; the 100-800 Mt tailings inventory is my own unsourced assumption, as is the 7 Bq/g Ra-226 used with it): $J\,A_{\text{area}}=1.39\times10^{7}$ Bq/s gives $\varepsilon\approx0.1$-$1\%$. The implied ε of about 0.004 (0.1-1%) is therefore only as good as that assumed inventory. A further datum (leads, not read by me): effective radon diffusion coefficients measured at western US uranium tailings average about $1.4\times10^{-7}$ m$^2$/s (WISE Uranium calculator page, after Nielson 1986), which gives $L=\sqrt{D/\lambda}\approx0.25$ m, so ε could be lower still than the 1-2 m slab case above. So 0.2 may overstate radon from deep tailings by one to two orders of magnitude; thin or shallow residues (spread fly ash, thin red-mud layers) approach $E$. For thoron the diffusion length is a few centimetres, so for a deep deposit $\varepsilon_{\mathrm{Rn220}}$ is of order $10^{-4}$-$10^{-3}$. Whether the pipeline's flow in Bq/a for Rn-222+ counts decays or Bq-exhaled needs a check against the UNSCEAR flux convention (a flux of 1 Bq m$^{-2}$ s$^{-1}$ is an atom flux times $\lambda$).

Proposed values (all `modelled`; slab model $E\,L/H$; need Task 3 review):

| Residue type | Rn-222 epsilon low / central / high | Rn-220 epsilon | Basis |
|---|---|---|---|
| metal_tailings | 0.002 / 0.01 / 0.05 | n/a | S0203 E, S0408 flux (Olympic Dam implied about 0.004) |
| iron_ore_tailings | 0.002 / 0.01 / 0.05 | n/a | no data; copy of metal_tailings |
| red_mud | 0.003 / 0.02 / 0.1 | 1e-4 / 1e-3 / 1e-2 | E = 0.20 dry (S0425); wet or saturated lower |
| ree_tailings | 0.002 / 0.01 / 0.05 (U-238 only 0.022 Bq/g, minor) | 1e-5 / 1e-4 / 1e-3 | Th-232 dominates; no thoron E for ground tailings |
| ree_process_residue | 0.005 / 0.02 / 0.1 | 1e-4 / 1e-3 / 5e-2 | stored in covered trenches or cells; Ra-228 and Th-228 rich |
| smelter_slag | 1e-4 / 1e-3 / 0.01 | negligible | vitreous slag, activity "unlikely to migrate" (S0202) |

## 9. Contradictions, quality flags and assumptions I made

- Silicon commodity code: `silicon_mg` is used in availability.csv for the silicon intensity of c-Si modules. Solar-grade polysilicon is made from metallurgical-grade silicon, so the code refers to the upstream MG-Si (quartz, reductant, electrodes, electricity) and the Si t/GW figures are solar-grade output; the MG-Si input is larger by the process yield (not sourced).
- Bayan Obo REE output: 100 000 t/a concentrate vs "7000 t/a REO" in the same paper (S0405); the 2004 China figure (S0404) is in a different year from the 2006 tailings figure used for the per-REO value. Result is robust (two routes agree within 30%) but rests on an inferred 15% recovery.
- Bayan Obo ThO2: 0.04% (S0404, 1.4 Bq/g) vs 0.032% (S0405) vs 0.07% (2.6 Bq/g): all kept as a range.
- Lynas data: the author calculates Th mass 1532 mg/kg and 1655 mg/kg from the same activity (S0406), and Lynas Malaysia supported the work. WLP tonnage 75 000 t/a is one reported average.
- JRC 2020: some text lines print "t/MW" where the table is in t/GW; the DD-PMSG magnet mass implied by Nd (620 kg/MW) exceeds the literature range 250-600 kg/MW (S0414), and implied by Dy (425 kg/MW) differs again.
- Red mud tonnage in S0409: 70 Mt/a printed against about 210 Mt implied by 1.7 kg per kg alumina and 123 Mt alumina; the ratio is used.
- Olympic Dam uranium (3406 t) is labelled uranium in the 20-F table; U3O8 assumed. The Ra-226 per tonne Cu is before allocation. Cumulative tailings tonnage is not in hand.
- Cu smelter off-gas: UNSCEAR 1988 Table 47 values were read from a page image; the smelter capacity is not stated; my 100-300 kt Cu/a is an assumption. The data are about 1980-85 US plants.
- Generic copper tailings activity spans a factor of 60 between the two sources (UNSCEAR 1988 ore at 30-80 Bq/kg vs EPA via IAEA 0.37 Bq/g); the central value is a geometric mean (judgement).
- Steel stack values assume the UNSCEAR 2000 Table 28 "ore throughput" is iron ore.
- UNSCEAR 2016 PV ore mass: silver is about 34% of the ore mass at 0.01% grade (unscear_notes.md section 3). After D6 allocation the silver residue will fall sharply (silver is about 1% of Olympic Dam value). The "why solar" result will therefore not survive allocation unchanged, which is expected.

## 10. Source quality summary

- Strong (rank 2-4, read): IAEA SRS 68 and NORM VI paper (S0404, S0405), TRS 419 (S0202), JRC 2020 and 2023 (S0400, S0401), UNSCEAR 1988 and 2000 tables (S0008, S0005), DOE 2022 (S0413), USGS MCS 2025 (S0411, S0412).
- Medium: BHP filings and EIS (S0407, S0408; company documents, measured radon fluxes), Xhixha et al. (S0409; review, preprint), Aziman and Ismail (S0406), Liu and Barlow (S0418).
- Weak or secondary: pv magazine reports of CRU studies (S0419, S0420), WSA fact sheet (S0421), IAEA training slides (S0423, S0424), the ANSTO abstract (S0429), IEA 2021 (not independent of JRC).
- Not covered: IEA Global Critical Minerals Outlook 2024/2025 (not retrieved), NREL material-intensity work (not retrieved), academic LCAs other than via UNSCEAR/JRC (Jungbluth, Jean et al., Nassar et al. 2016 are reached only through S0400/S0001). Intensities therefore rest on one lineage (JRC/Nassar/Jean).

## 11. Inaccessible or unread sources (for Steve to try)

- MDPI Minerals 2023, Heim and Vander Wal, NdFeB sector shares: https://www.mdpi.com/2075-163X/13/10/1274 (S0416, HTTP 403).
- BHP Olympic Dam Draft EIS Appendix S, Uranium and Radiation (2009): https://www.bhp.com/-/media/bhp/regulatory-information-media/copper/olympic-dam/0000/draft-eis-appendices/odxeisappendixsuraniumandradiation.pdf (S0428; curl gives 403, but the fetch tool retrieves it). The extract has no tailings Ra-226, slag Pb-210/Po-210 values or stack data; it says only that Pb-210 in flash-furnace slag is about 10 times Po-210.
- BHP Supplementary EIS Appendix M (read only through the fetch tool; curl gives 403): https://www.bhp.com/-/media/bhp/regulatory-information-media/copper/olympic-dam/0000/supplementary-eis-appendices/appendix-m_radiation.pdf (S0408).
- Poffijn, NORM in the non-ferrous industry in Belgium: https://ena-norm.eu/wp-content/uploads/2024/04/1_2_06_Poffijn-Experience-non-ferrous-Belgium.pdf (S0427, 403).
- IRENA full end-of-life report (403 to curl): https://www.irena.org/publications/2016/Jun/End-of-life-management-Solar-Photovoltaic-Panels (S0417; only the IEA-PVPS summary was read).
- Nostvold et al. 2025, metallurgical silicon LCA, Tables 2-4: https://link.springer.com/article/10.1007/s40831-024-00941-z (S0422).
- USGS DS140 series files (403 to curl): https://www.usgs.gov/centers/national-minerals-information-center/historical-statistics-mineral-and-material-commodities-united-states
- pv magazine pages return 403 to curl but were read through the fetch tool.
- IAEA SRS 68 and the NORM VI proceedings downloaded without problems from www-pub.iaea.org.

## 12. Hand-offs

- Task 1.9: wind and PV capacity additions by technology and year, PM penetration by year, REO production by country and route, NdFeB production by year, silver and silicon use per W by year, Bayan Obo REO output by year, alumina and steel routes.
- Task 1.3 (coal factors) for embedded coal in steel (0.8 t/t), silicon reductant and cement kilns; Task 1.4 for embedded gas in glass and polymers.
- Task 3.x (engine): the epsilon issue in section 8; the Rn-222 versus Bq-exhaled convention.
- Task 3.5 (check against UNSCEAR): UNSCEAR's PV result is driven by ore mass (S0001); compare after allocation, not before.
- Not done: no data series were written to `data/`; `footprint_inputs.csv` is a seed, not a validated `commodity_factors.csv`.
