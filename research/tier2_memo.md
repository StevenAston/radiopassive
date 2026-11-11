# Task 2.6: Tier 2 magnitude memo (transmission, storage and firming)

Status: research only, no code, nothing applied to `data/`. Approved by Steve 2026-11-10. Written 2026-11-10.
Scope reminder: activity in Bq and Bq/a only, no dose quantities (D1). Tier 2 is excluded from v1 (D5, METHODS 6); this memo measures how big it would be.

Confidence labels used throughout: **[E]** established by a source read in full or in the relevant table; **[R]** reported by a source I could read only in part or at second hand; **[I]** my inference or arithmetic from cited inputs; **[A]** my assumption, no source.

> **REVISION 2026-11-11 (copper factor; Task 2.4 copper classes, `research/wind_solar/copper_classes.md`).** The seed copper footprint used below (S5 $1.35\times10^{8}$ Bq/t, range $1.4\times10^{7}$ to $6.0\times10^{8}$) is **superseded**. Copper tailings are now split into three ore types and production-weighted. 2024 world factor, S5 tailings: low $2.6\times10^{7}$, central $4.8\times10^{7}$, high $2.0\times10^{8}$ Bq/t Cu (central 0.35 of the old; spread 8x instead of 43x).
>
> Re-run of section 4.1 (same tonnages: T&D copper 3.0 Mt (2.0 to 4.5), aluminium 5.5 Mt, D6 factor 0.7 / 0.85 / 1.0, storage chemistry term $2.5\times10^{12}$, BESS copper 0.1075 Mt):
>
> | Quantity (2024, Bq/a) | Old | New |
> |---|---|---|
> | T&D copper, central | $3.44\times10^{14}$ | $1.22\times10^{14}$ |
> | Grid (Cu + Al), low / central / high | $2.3\times10^{13}$ / $3.6\times10^{14}$ / $2.8\times10^{15}$ | $4.1\times10^{13}$ / $1.40\times10^{14}$ / $9.4\times10^{14}$ |
> | BESS copper, central | $1.2\times10^{13}$ | $4.4\times10^{12}$ |
> | $A_{\mathrm{T2}}$ central | $3.75\times10^{14}$ | **$1.46\times10^{14}$** (0.39 of old) |
>
> Effect on the percentages (central, basis A, pro-rata): ② coal C1 1.2 % to **0.45 %**, S5 11 % to **4.3 %** (now below the 5 % threshold at central; 28 % at the upper bound); ③ oil and gas C1 2.7 % to **1.0 %**, S5 30 % to **12 %**; ① nuclear C1 0.12 % to **0.047 %**, S5 3.3 % to **1.3 %**; ⑤ other C1 6.6 % to **2.6 %** (S5 still enormous); ④ **unchanged** (11 to 54 %, matched-factor ratio; the copper factor cancels). The "include narrowly" verdict stands because of ④, ⑤ and ③ on S5; ② no longer clears 5 % at central and ⑤ no longer clears it on C1 at central.
>
> Tonnage cross-check, Deetman et al. 2021 (S1805, now read): their **whole** electricity-sector copper inflow (generation, transmission and storage) is 2.09 Mt/a in 2015 (11.9 % of production) and 4.3 to 4.9 Mt/a in 2050. The 3.0 Mt/a for T&D alone (grey source S1818) is therefore on the high side; with 2.0 Mt/a the new $A_{\mathrm{T2}}$ is $1.06\times10^{14}$ (0.28 of old). The T&D split is in Deetman's SI, not the paper. Stated figures above keep 3.0 Mt.
>
> DRC cobalt-uranium: the paper is now read (section 7 of `copper_classes.md`). A Katanga copper override would lower, not raise, the tailings factor (DRC ore is 2 to 3 % Cu). Recommendation: page callout only; no `cobalt` commodity row for v2.

---

## 0. Answer first

1. **Should v2 include Tier 2? Yes, but narrowly.** The threshold in PLAN Task 2.6 (more than 5 % of any stream's total) is exceeded for stream ④ on every basis tried, for stream ⑤ on every basis, for ② and ③ on a like-for-like chain-solids basis at central values, for ② and ③ at the upper bound of the stream-total basis, and for ① only at the upper bound of the chain-solids basis. The exceedance is driven by **one item: copper in the transmission and distribution (T&D) grid**, through copper-mine tailings. Aluminium (red mud) is a distant second. Everything specific to batteries (Li, Co, Ni, graphite, Mn, V, Pb, phosphate) sums to **less than 1 % of the Tier 2 total** at the 2024 benchmark.
2. **Recommended v2 scope:** one new stage, `grid` (T&D copper, aluminium, and their steel/zinc/concrete, plus the copper and aluminium in battery energy storage systems), driven by the Task 2.4 commodity table times a grid material intensity. No new radiological research is needed for it. Battery chemistries, flow batteries, lead-acid, pumped hydro and firming plant stay **memo-only or excluded** (table in section 7).
3. **Most material Tier 2 item:** T&D copper, about $3\times10^{14}$ Bq/a on the chain-solids basis at 2024 (range $2\times10^{13}$ to $3\times10^{15}$, a factor of about 40 either way, almost all of it the copper-tailings factor). **[Revised 2026-11-11: $1.2\times10^{14}$ central, range about $4\times10^{13}$ to $9\times10^{14}$; see the revision box.]** It is about 13 % of the whole world copper-mining burden on the same basis, because the grid takes about 13 % of world copper.
4. **The ④ result does not depend on the copper factor.** Tier 1 for ④ is also dominated by copper (PV and wind plant), so grid-to-plant copper tonnage is the ratio, and the per-tonne factor cancels. Whatever Task 2.4 settles on, Tier 2 is **11–54 %** of ④ (pro-rata by TWh) or **18–190 %** (all storage and VRE connection grid charged to ④).
5. **Fuel streams ①②③ do depend on the copper factor.** **[Superseded 2026-11-11: now 0.45 %, 1.0 %, 0.05 % of C1 and 4.3 %, 12 %, 1.3 % of S5; see the revision box.]** Original text: at central values Tier 2 is 1.2 % (②), 2.7 % (③), 0.1 % (①) of stream totals including radon and fission products, and 11 %, 30 % and 3.3 % of the chain-solids total. Re-run when `commodity_factors.csv` exists (formula in section 4.1).
6. **Notable finding for the page, not for Tier 2:** a peer-reviewed study (Manzuk and Philippe, *Nature Communications*, 2026) estimates 2 000–5 000 t of natural uranium left the DRC in cobalt-hydroxide exports in 2000–2024. That is about 0.5–1 % of world uranium mining per year, small as a Bq flux but a genuinely unexpected radioactivity route in battery supply chains. It belongs in Task 2.4's copper/cobalt regional factors or the sequel, not in Tier 2 (section 3.2).

---

## 1. Boundary, benchmark and method

### 1.1 What Tier 2 means here

- D5: Tier 1 = generating plant + fuel cycle / material supply chain including construction materials. Tier 2 = transmission, storage, firming.
- UNSCEAR 2016 Annex B (S0001) excludes Tier 2 explicitly: "Exposures from electrical energy storage, transmission and distribution are not considered" (¶9), and again as limitation (e) in ¶221 (printed p. 226): these infrastructures "are used regardless of the type of electricity generation" and "could be included in any future update". **[E]** (Note: `research/unscear_notes.md` §5 cites this as ¶10; the sentence is in ¶9, and ¶10 is "normal operations only". Minor correction for the notes.) This gives the attribution logic in 1.3: the grid is shared by all generators.
- Storage in scope here is **grid storage** (stationary). EV batteries are demand-side transport and outside the energy-generation streams; they appear only as context for scale.

### 1.2 Benchmark year and measures

- **Primary benchmark: 2024** (latest complete year in the committed streams; stationary storage only became large in 2023–24). **Secondary: 2020** (Phase 2 benchmark year, D51).
- Stream totals are read from `data/streams/*.csv.gz` (`quantity = flow`, central values, non-Sealed tiers only: impounded, reisolated, dispersed, liberated; memo tiers excluded). Three measures:
  - **C1**: all groups, the "stream total" that the page would show.
  - **S5**: the chain-solids groups `U238+`, `Th232`, `Ra226+`, `Pb210+`, `Po210`. This is like-for-like with a mineral-residue footprint, which has no radon, K-40 or fission products. It matches the groups in the Task 2.4 seed copper footprint.
  - Sealed nuclear (in-core and fuel-cycle inventory, $1.2\times10^{21}$ Bq/a flow in 2020) is excluded from C1; including it makes ① immune to any Tier 2 effect ($<10^{-6}$).
- Why two measures: C1 is dominated by radon (coal 77 %, geothermal 96 % of the stream) and H-3 (nuclear), which a mineral-residue footprint cannot compete with, while S5 is the like-for-like comparison. Stream ⑤ shows the effect plainly: C1 $9.6\times10^{14}$ Bq/a but S5 only $1.4\times10^{11}$ Bq/a in 2024.
- Per-tonne factors come from the Task 1.5 seed table `research/wind_solar/footprint_inputs.csv` (read only; the Task 2.4 agent is revising it; I cross-reference by commodity name: `copper`, `aluminium`, `steel`, `cement`, `zinc`, `lead`, `nickel`, `silicon_mg`). They are head-activity residue footprints before D6 allocation.

### 1.3 Attribution of Tier 2 to streams (two bases)

- **A. Pro-rata by electricity generated** (the grid and storage serve all generators; UNSCEAR's own reasoning). Shares of 2024 generation (`data/activity/electricity_generation.csv`, 30 940 TWh): coal 34.1 %, nuclear 9.0 %, gas + oil (③) 25.0 %, wind + solar (④) 15.0 %, hydro + biomass + geothermal + peat (⑤) 16.9 %. 2020 (26 736 TWh): 35.3, 9.9, 26.8, 9.1, 18.9 %.
- **B. Incremental (VRE-driven)**: all storage plus the wind and solar connection grid (inter-array and export lines) charged to ④; no share of the existing T&D grid to anyone.
- Caveat on D22: streams ② and ③ in the industry view cover the whole industry (non-power coal, transport oil). Tier 2 is an electricity-sector item and fits the **lifecycle (per-TWh) view**, where the Tier 1 denominators for coal and oil/gas are smaller (power share only), so the percentages below are conservative for ② and ③. I have not quantified this; it is a v2 task.

---

## 2. Tier 1 reference totals (committed streams, read from the files)

Central values, non-Sealed flows, Bq/a:

| Stream | 2020 C1 | 2020 S5 | 2024 C1 | 2024 S5 | Composition note |
|---|---|---|---|---|---|
| ① Nuclear | $2.70\times10^{16}$ | $7.7\times10^{14}$ | $2.90\times10^{16}$ | $1.01\times10^{15}$ | H-3 ($1.4\times10^{16}$ in 2020) and Rn-222 ($7.3\times10^{15}$) dominate C1; Sealed flow $1.15\times10^{21}$ excluded |
| ② Coal | $9.58\times10^{15}$ | $1.00\times10^{15}$ | $1.10\times10^{16}$ | $1.16\times10^{15}$ | Rn-222+ $7.3\times10^{15}$ (2020) |
| ③ Oil and gas | $3.24\times10^{15}$ | $2.8\times10^{14}$ | $3.49\times10^{15}$ | $3.2\times10^{14}$ | Rn-222+ $2.2\times10^{15}$; Ra-226+/Ra-228+ ($2.5\times10^{14}$ each) |
| ⑤ Other | $9.45\times10^{14}$ | $4.6\times10^{11}$ | $9.60\times10^{14}$ | $1.4\times10^{11}$ | geothermal Rn-222+ $9.1\times10^{14}$ |
| ④ Wind and solar | not built | est. $9\times10^{13}$ | not built | est. $2.8\times10^{14}$ | **[I]** placeholder, below |

**④ placeholder (Tier 1 is not built; Task 2.4 not started).** Capacity added (`capacity_additions.csv`): 2024 PV 458.6 GW, onshore wind 106.0 GW, offshore wind 8.3 GW; 2020 PV 131.1, onshore 104.1, offshore 6.1 GW. Material intensities, 2018 vintage, JRC 2020 (S0400; `research/wind_solar/material_intensity.csv`): PV copper 4 600 t/GW and aluminium 7 500 t/GW (balance of system and module); wind copper 1 400 t/GW (geared, onshore proxy) to 3 000 t/GW (direct-drive, offshore proxy), range 950–5 000; wind aluminium 500–1 600 t/GW. This gives 2024 copper 2.3 Mt (1.5–2.7) and aluminium 3.6 Mt (2.4–3.6). With the seed footprints (section 3.1) the central S5 is $2.8\times10^{14}$ Bq/a (range $1.7\times10^{13}$ to $1.7\times10^{15}$), copper being 93 % of it. REE, steel and cement stack terms add about $3.5\times10^{12}$ **[I]**. D6 value allocation for copper is applied as a factor 0.7 / 0.85 / 1.0 (Olympic Dam Cu share 74 %, `co_product_inputs.csv`).

---

## 3. Findings by item

### 3.1 Transmission

**Quantities.** The global T&D grid takes about 3 Mt/a copper and 5–6 Mt/a aluminium (Thunder Said Energy, grey, S1818; "10 % of copper demand, 8 % of aluminium demand") **[R]**, single source for the absolute figure. Cross-checks, all different bases: IEA ETP 2023 says grid and transformer copper in 2022–2030 is "almost 20 % of global copper production in 2030" and that grain-oriented electrical steel capacity is 3.8 Mt/a, heading to 6 Mt/a (S1820) **[R]**; the Energy Transitions Commission copper factsheet gives 200 Mt cumulative T&D copper over 2022–2050 in its baseline (average 7 Mt/a, an upper-bound scenario) (S1819) **[R]**. Chen, Kleijn and Lin (2023, S1804) give the wind and utility-PV connection grid alone (inter-array cables and export lines, excluding general T&D) as 27–81 Mt copper and 11–31 Mt aluminium cumulative for 2021–2050, with cables about 90 % of the copper; in their SDS scenario 4.3 Mt copper and 2.7 Mt aluminium per 5-year period at the start (0.86 and 0.54 Mt/a) **[E for the figures, but see 'scope']**. I use 2024 grid copper 3.0 Mt (2.0–4.5) and aluminium 5.5 Mt (4.0–8.0), assumed unchanged from 2020 within the band **[A]**. Gap: no primary-literature global T&D tonnage in hand (Deetman et al. 2021 is the obvious source; its tables were not retrievable, section 8).

**NORM pathway.** Entirely through the commodity: copper-mine tailings and smelter slag/off-gas, bauxite-residue (red mud). The grid itself adds no new process. Copper in the project seed table (Bq per tonne of refined copper, head activity, before allocation; `footprint_inputs.csv`, from IAEA TRS 419 Table XX (S0202) and UNSCEAR 1988 (S0008)):

| Group | Low | Central | High |
|---|---|---|---|
| $U238+$ | $3\times10^{6}$ | $2.4\times10^{7}$ | $1.9\times10^{8}$ |
| $Th232$ | $2.3\times10^{6}$ | $2.1\times10^{7}$ | $1.9\times10^{8}$ |
| $Ra226+$ | $3.8\times10^{6}$ | $3.8\times10^{7}$ | $9.5\times10^{7}$ |
| $Pb210+$, $Po210$ (each) | $2.6\times10^{6}$ | $2.6\times10^{7}$ | $6.5\times10^{7}$ |
| **Sum (S5)** | $1.4\times10^{7}$ | $1.35\times10^{8}$ | $6.0\times10^{8}$ |

Aluminium red mud, S5 (three groups only): $9.6\times10^{5}$ / $3.2\times10^{6}$ / $6.9\times10^{6}$ Bq/t. IAEA SRS-49 (S1800) Table 1 corroborates the order of magnitude: metal ores such as Cu "up to 10 Bq/g", red mud 0.1–3 Bq/g, copper-smelting slag Ra-226 0.4–2 Bq/g, and Pb-210/Po-210 precipitator dust up to 200 Bq/g (§3.1.9) **[E]**. The seed copper central rests on a 200 t ore per t Cu assumption and spans a factor of 60 between UNSCEAR 1988 and EPA/IAEA sources (Task 1.5 notes §9): **this is the weakest and most consequential number in the memo.** Olympic Dam, a U-bearing copper deposit, is 4–10 times the generic value ($3.8\times10^{8}$ Bq/t Ra-226+ alone).

**Sub-items** (all roll into the copper/aluminium/steel tonnage):

| Component | Material | Tier 2 treatment |
|---|---|---|
| Overhead conductors (ACSR, AAAC) | aluminium (red mud) with galvanised steel core | in grid Al tonnage |
| Underground and subsea cables | copper, aluminium, lead sheath on some HVAC subsea cables, polymer | in grid Cu/Al; lead memo-only |
| Towers and poles | steel, zinc (galvanising), concrete foundations | steel stack footprint is only $\sim10^{4}$ Bq/t; negligible. Embedded coking coal is in ② (industry view) |
| Power transformers | copper windings (in grid Cu), grain-oriented electrical steel, insulating oil | see transformer oil below |
| HVDC converter stations | steel, copper, aluminium, concrete, power semiconductors (silicon) | covered by the same commodities; silicon wafers trivial in mass |

**Transformer oil.** Mineral insulating oil is a refined vacuum-distillate product. Radium and lead-210 partition to produced water, scale and sludge upstream (already in ③: `og_scale`, `og_sludge`, `og_processing_residue`), not into refined distillates; SRS-49 Table 1 lists no refined-product entry **[I, from process chemistry; no measurement found]**. Treat as zero NORM and a pure overlap with ③ (the crude is already counted). Recommendation: **exclude**.

**Materiality.** Tier 2 grid (Cu + Al), 2024, S5: low $2.3\times10^{13}$, central $3.6\times10^{14}$, high $2.8\times10^{15}$ Bq/a ($\approx$ 10 kCi/a at central). Copper is 95 % of it. For scale, world copper mining on the same basis is about $2.6\times10^{15}$ Bq/a (23 Mt Cu, `prod_copper` 2024), larger than coal's whole S5 ($1.2\times10^{15}$): the grid share is about 13 % of that, in line with grid copper being 13 % of copper demand.

**Recommendation: include in v2** as stage `grid`, commodity-driven.

### 3.2 Storage

#### Context: how much storage, and what chemistry

- Stationary storage deployed in 2024: 205 GWh, +53 % on 2023 (Rho Motion via *Energy-Storage.News*, S1816; grid-scale 160 GWh, up from 96 GWh) and 168–170 GWh (BNEF, Dec 2024, S1817); 2023 about 96–134 GWh **[R]**. 98 % of 2024 grid deployments were lithium-ion and LFP's dominance grew (S1816) **[R]**. I use 190 GWh (170–205), LFP share 90 % (80–95 %) **[A: no sourced LFP share for stationary found]**. 2020: about 10 GWh **[A, order of magnitude only; not sourced]**.
- Battery bill of materials per kWh of pack (Argonne BatPaC-based, Knehr, Kubal and Ahmed 2024, ANL/CSE-24/1, S1803) **[E for automotive packs; I apply them to stationary packs, which is an assumption]**:

| Chemistry | Cathode active material | Li | Co | Ni | Mn | Anode active (graphite) |
|---|---|---|---|---|---|---|
| LFP (MY2023) | 1.93 kg/kWh | 0.09 kg/kWh | — | — | — | 0.98 kg/kWh |
| NMC622 (MY2023) | 1.42 | 0.10 | 0.17 | 0.52 | 0.16 | 0.89 |
| NMC811 (MY2026) | 1.30 | 0.09 | 0.08 | 0.63 | 0.07 | 0.65 |

  LFP is stationary storage's chemistry, so **Co, Ni and Mn demand from stationary storage is a small share (I assume 1–5 % of the battery demand for each) [A]**. Battery demand for these metals is dominated by EVs. Li: 190 GWh $\times$ 0.09 kg/kWh = 17 kt Li, about 7 % of 2024 world production of 240 kt (USGS MCS 2025, S1812; batteries 87 % of lithium use) **[R/I]**.
- IAEA coverage test: I searched SRS-49 (S1800), SRS-78 (S1801) and IAEA-TECDOC-1712 *Management of NORM Residues* (S1802) for lithium, cobalt, nickel, manganese, graphite, vanadium and batteries. **None of the three mentions any of them.** The IAEA screening lists (SRS-49 Table 1) do not flag these industries as NORM-relevant **[E]**. This is itself evidence of absence of regulatory concern, but not of measurements: the gaps below are measurement gaps.

#### Lithium (spodumene and brine)

- Sources 2024: hard rock (Australia 88 kt, Zimbabwe 22 kt, Brazil 10 kt, Canada 4.3 kt, Namibia 2.7 kt, Portugal 0.4 kt, part of China 41 kt) and brine (Chile 49 kt, Argentina 18 kt, part of China). World 240 kt (S1812) **[R]**. Hard rock roughly 54 % **[I]**.
- NORM, hard rock: the one measurement set found is Gbondo et al. (2025, *J. Hazard. Mater. Adv.* 18, S1809): three Western Australian surface lithium mines, 2018–2024; highest mean radiation emission **2.169 Bq/g in tantalum concentrate**; the abstract gives no ore, spodumene-concentrate or tailings activities **[R, abstract only]**. Tantalum concentrate is a co-product at some pegmatite mines (SRS-49 Table 1: niobium/tantalum slags up to 120 Bq/g Th-232, so co-product allocation could matter if Ta is recovered, D6).
- NORM, brine: I found no radionuclide data for Li brines (a BGS salar-chemistry paper, Al-Jawad et al. 2024, *Sci. Total Environ.* 906:167647, reports only Li at 16–1 000 mg/L and total dissolved solids of 20–247 g/L). Brine residues are evaporite salts. **Gap.**
- Residue mass **[I, my arithmetic]**: 1 t of lithium carbonate equivalent (LCE) contains 0.188 t Li. At 6 % Li$_2$O concentrate, 1.3 % Li$_2$O ore and 70 %/88 % stage recoveries, about 7.5 t concentrate and **about 50 t ore per t LCE, i.e. about 270 t ore per t Li**. This is an engineering estimate, not sourced.
- Order of magnitude: 17 kt Li for stationary storage, 54 % hard rock, 270 t ore/t Li gives 2.5 Mt tailings. At crustal levels (UNSCEAR 2000 soil medians in `baselines.csv`: U-238 35, Th-232 30 Bq/kg; S5 about 0.17 Bq/g **[A, crustal assumption]**) the S5 total is $4\times10^{11}$ Bq/a (range $7\times10^{10}$ to $1.6\times10^{12}$). Whole-world Li on the same basis is about $10^{13}$ Bq/a: under 1.5 % of coal's S5.
- **Recommendation: memo-only.** Revisit if measured spodumene tailings exceed 1 Bq/g.
- Forward flag (overlap, not yet material): direct lithium extraction from oilfield produced water or geothermal brine would sit on ③ `og_produced_water` or ⑤ `geothermal_brine`/`geothermal_scale` and would create sorbent waste not in either. No commercial-scale data found.

#### Cobalt (Cu–Co, DRC; Ni–Co laterites)

- Supply: world 290 kt, DRC 220 kt (75.9 %) in 2024; 78 % of cobalt is a by-product of copper-cobalt mining and 22 % of nickel; crude cobalt hydroxide is about 31 % Co (IISD commodity profile 2026, S1814) **[R]**.
- **Uranium in cobalt hydroxide [R].** Manzuk and Philippe, "Uranium in cobalt-hydroxide exports from the Democratic Republic of the Congo", *Nature Communications* (published 30 July 2026; DOI 10.1038/s41467-026-75910-z derived from the URL; full text not retrievable by me, S1806) estimate that **2 000–5 000 t of natural uranium** left in cobalt-hydroxide exports in 2000–2024, mostly to China, less than 10 % of it apparently declared to the IAEA, and that a further **1 000–4 000 t** was discarded in highly mobile forms at the mines (Princeton SPIA summary, S1807). The study "relies on extrapolating previous Katanga analyses and geochemical models"; leaked Tenke Fungurume records show 1 100 ppm U in December 2016 (about 15 times the export limit) (Intellinews, 3 August 2026, S1808). CMOC rejected the findings. Not independently verified.
- Arithmetic **[I]**: natural uranium is $1.235\times10^{7}$ Bq U-238 per kg U (`research/baselines/derivations.md`), so 1 t U = $1.24\times10^{10}$ Bq U-238 and about $2.5\times10^{10}$ Bq with U-234. The 25-year average is 80–200 t U/a, i.e. $2\times10^{12}$ to $5\times10^{12}$ Bq/a of U-238+U-234. Recent years will be higher because DRC cobalt output grew about twentyfold over the period; scaling by cobalt output gives my rough 275–680 t U in 2024 (**[A]** on the cumulative cobalt series, recalled rather than read; recompute from USGS DS140 or MCS history). That is 0.5–1 % of world uranium mining (about 60 kt U in 2024) and, in Bq, $7\times10^{12}$ to $1.7\times10^{13}$ for U-238+U-234: not material against the stream totals above, but comparable to the whole of ①'s non-Sealed `U238+` flow ($1.8\times10^{13}$ Bq/a in 2024), because ① moves the uranium it mines into the Sealed tier. The world uranium production figure (about 60 kt U in 2024) is recalled, not read **[A]**.
- Regional river-sediment context: Luilu River 154 Bq/kg and Dilala River 378 Bq/kg U-238 (Atibu et al. 2021, via a citing paper, S1811, not read) **[R]**; consistent with elevated U in the Kolwezi belt.
- Stationary share: LFP uses no cobalt, so stationary storage's share of this flux is 1–5 % **[A]**, about $3\times10^{11}$ Bq/a.
- Overlap: this U is **not** in ① (not a nuclear-fuel flow, mostly undeclared), and the generic copper factor undercounts Katanga copper. **Recommendation: not Tier 2.** Pass to Task 2.4 as a candidate regional override for `copper` and a new `cobalt` commodity (DRC), and flag it to Steve as a candidate callout ("unexpected source"). Memo-only for Tier 2. **[Updated 2026-11-11: paper read in full. Katanga override rejected (it would lower the tailings factor); cobalt commodity not recommended for v2; page callout only. Intermediate-mobility total more than 7,000 t U extracted 2000 to 2024, 2,000 to 5,000 t exported; method and numbers in `copper_classes.md` section 7.]**
- Ni–Co laterites (Indonesia, Philippines, New Caledonia, Cuba): no cobalt-specific NORM data; see nickel.

#### Nickel (sulphide and laterite, including HPAL residues)

- Indonesia dominates growth and nickel supply (IEA GCMO 2025, S1815: top three refiners about 86 % of refining; Indonesia about 90 % of refining supply growth for nickel) **[R]**. World nickel production in the project data: 2.51 Mt (2020), 3.70 Mt (2024) (`prod_nickel`).
- Residue mass: for HPAL, PT Lygend (Obi) produces "approximately 1.2 tonnes of waste for each tonne of ore", 11 Mt/a of waste (Benchmark Minerals, S1821); dividing by 60 kt/a Ni capacity gives about 180 t waste per t Ni **[I, indicative; mixes whole-operation waste with MHP capacity]**.
- NORM: **no measurement found** for laterite ore or HPAL residue. A search found only a Sulawesi paper (Rosianna et al. 2020, *Geosciences* 10:376) on volcanic "laterite" at U-rich sites, not nickel laterite, so I did not use it. Lateritic iron-oxide soils are expected to sit near crustal levels (**[A]**).
- Magnitude test **[I]**: as an upper bound, all battery nickel (I assume 15 % of 3.7 Mt **[A]**, EV-dominated) made via HPAL at 180 t/t and crustal S5 0.17 Bq/g gives about $2\times10^{13}$ Bq/a, and the stationary share is a few per cent of that. Not material.
- **Recommendation: memo-only.** Sulphide nickel (Norilsk, Sudbury, Jinchuan) and `nickel` are in the Task 2.4 commodity list; no Tier 2 treatment.

#### Graphite (natural and synthetic) and manganese

- Natural flake graphite: no NORM measurement found (the one table my search surfaced could not be opened). Assumed crustal. Stationary anode graphite: 0.98 kg/kWh $\times$ 190 GWh = $1.9\times10^{5}$ t. If half is natural at about 15 t tailings per t concentrate **[A]** and 0.17 Bq/g **[A]**, the S5 total is $2\times10^{11}$ Bq/a. Not material.
- Synthetic graphite: made from petroleum needle coke or coal-tar pitch and graphitised by electric furnace. Its radiological content is embedded fuel and power already in ③/② (industry view) and lifecycle-only. **Exclude.** (Acheson electricity per tonne not sourced here.)
- Manganese: high-purity manganese sulphate is 95 % Chinese (IEA GCMO 2025, S1815). The only ore measurement found is a single Egyptian (Sinai) ore, mean 3 543 Bq/kg U-238, 222 Th-232, 3 483 K-40 (Abdel-Ghany 2009, S1810) **[E for that deposit; one site, not representative]**. NMC is a minority of stationary storage. **Memo-only.**

#### Phosphate for LFP: a pathway the battery literature misses

- LiFePO$_4$ is 19.6 % P by mass, which is 45 % P$_2$O$_5$ equivalent **[I, stoichiometry]**. At 1.93 kg cathode per kWh (S1803): 0.87 kg P$_2$O$_5$/kWh. Battery-grade LFP precursors use purified phosphoric acid (China holds 75 % of purified phosphoric acid supply, S1815) from the wet process, which creates phosphogypsum.
- IAEA SRS-78 (S1801): "Each tonne of P$_2$O$_5$ produced in the form of phosphoric acid is matched by 4–6 t of phosphogypsum (dry weight)" (wet-process description), with 5.2 t dry typical for Florida rock; Ra-226 in phosphogypsum 0.015–3.2 Bq/g by country (Table 56, with 0.4–1.0 typical), Pb-210 and Po-210 often similar. World phosphogypsum production about 160 Mt/a in the mid-2000s (SRS-78, chapter 10) **[E]**.
- Arithmetic **[I]**: 190 GWh $\times$ 90 % LFP $\times$ 0.87 kg P$_2$O$_5$/kWh $\times$ 5.2 t/t $\approx$ $8\times10^{5}$ t phosphogypsum $\times$ 0.6 Bq/g Ra-226 = $5\times10^{11}$ Bq/a Ra-226, or $1.5\times10^{12}$ Bq/a S5 with Pb-210, Po-210 and U-238 (range $3\times10^{11}$ to $5\times10^{12}$). Counting all LFP (EVs included) multiplies this by perhaps 5–8: still under $2\times10^{13}$.
- Not material, but it is a fresh instance of the "phosphate" gap: D4 leaves phosphate to the non-energy sequel. **Pointer only; no Tier 2 row.** `prod_phosphate_rock` is already in `commodity_production.csv`, so the sequel can start from there.

#### Vanadium flow batteries

- World vanadium 118 kt (2024), China about 71 % mostly from vanadiferous titanomagnetite in steelmaking; US data show more than 90 % of consumption is metallurgical; flow-battery installations are growing but USGS gives no quantity (USGS MCS 2026 vanadium, S1813) **[R]**. Utah uranium-vanadium production ceased in early 2020 (S1813), so the historic U–V co-production route (already inside ① mining) is now zero.
- Vanadium from petroleum residues and ash is a secondary source (US 7 500 t in 2025, S1813): overlap with ③ (`oil_sands_coke`) and ② ash, already counted.
- Magnitude: flow-battery deployments are of order 1 GWh/a **[A, not sourced]**; at roughly 5–10 kg V per kWh **[A]** that is under 10 t V, under 0.01 % of world V. **Exclude.**

#### Lead-acid

- Stationary lead-acid (UPS, telecom) is mostly not grid storage. Lead is in the vocabulary (`lead`) but has no seed footprint. Pb-210 follows lead into the metal: one lead-containing sample from a Belgian secondary smelter measured 53 Bq/g Pb-210 (Lutter et al. 2017, S1823) **[E for that sample only; not representative]**; SRS-49 §3.1.9 gives precipitator dust Pb-210/Po-210 up to 200 Bq/g.
- Magnitude **[I]**: even 10 GWh/a of lead-acid at about 20 kg Pb/kWh **[A]** is 2×10$^5$ t Pb, and at 0.5 Bq/g **[A]** this is $10^{11}$ Bq/a locked in product, largely recycled. **Exclude.**

#### Pumped hydro

- NREL's closed-loop pumped-storage life-cycle assessment (Simon et al. 2022, NREL/PR-6A20-81315, S1822) finds concrete 34 % and steel 26 % of the 0.086 kg CO$_2$-eq/kWh base case; it gives no tonnages in the slides, so I have no sourced material intensity per GW **[R]**. Commodities are cement, aggregate and steel only.
- Magnitude **[I]**: cement kiln stack Po-210 is about $4\times10^{4}$ Bq/t of cement (seed table); even 10 GW/a of new pumped hydro at an assumed 2 Mt concrete per GW **[A]** is $\sim10^{12}$ Bq/a or less. METHODS 10.3 already treats hydro as negligible via construction materials. **Exclude** (covered by the commodity table when hydro construction is counted).

#### BESS balance of plant (copper, aluminium, steel)

- Cell copper foil and busbars, aluminium cathode foil and casings, steel enclosures. ETC gives 1 Mt cumulative copper for stationary batteries over 2022–2050 (S1819). I assume 0.3–0.8 kg Cu/kWh **[A]**: 51–164 kt Cu in 2024, S5 $5\times10^{11}$ to $10^{14}$ (central $1.1\times10^{13}$), about 3 % of the grid-copper term. **Include in the `grid` stage** (as storage substream) with the same factors; it is the largest storage term.

### 3.3 Firming

| Item | Finding | Recommendation |
|---|---|---|
| Gas peakers (OCGT, CCGT) | Fuel production, processing, delivery and plant construction are already in ③ (`production`, `processing_transport`, `construction`, whole-industry scope). Lower capacity factors raise construction per TWh, which is a per-TWh lifecycle-view effect, not new Bq. | **Exclude** (already in ③) |
| Hydro and pumped hydro | In ⑤ (hydro, negligible, construction only) | **Exclude** |
| Biomass, geothermal | In ⑤ | **Exclude** |
| Coal and nuclear load-following | In ② and ① | **Exclude** |
| Demand response, interconnectors | Copper/aluminium in cables: in the grid term | covered |

---

## 4. Tier 2 totals and percentages of Tier 1

### 4.1 Formula (for the verifier and for the Task 2.4 re-run)

$$A_{\mathrm{T2}}=\sum_{c}M_{c}\,f_{c}\;+\;A_{\mathrm{stor,chem}}$$

where $M_c$ is the annual Tier 2 tonnage of commodity $c$ (copper and aluminium dominate), $f_c$ the S5 footprint in Bq/t (D6-allocated), and $A_{\mathrm{stor,chem}}$ the summed phosphogypsum, lithium, graphite and cobalt-uranium terms. The percentage for stream $s$ under basis A is

$$p_{s}=\frac{w_{s}\,A_{\mathrm{T2}}}{A_{s}},\qquad w_{s}=\frac{\mathrm{TWh}_{s}}{\mathrm{TWh}_{\mathrm{all}}}$$

with $A_s$ the Tier 1 total (C1 or S5 above).

**Worked check for ② coal, 2024, central, S5-based** (for the verifier):

$$A_{\mathrm{grid}}=3.0\times10^{6}\ \mathrm{t}\times(1.35\times10^{8}\times0.85)+5.5\times10^{6}\ \mathrm{t}\times3.16\times10^{6}=3.44\times10^{14}+1.74\times10^{13}=3.62\times10^{14}\ \mathrm{Bq/a}$$

$$A_{\mathrm{T2}}=3.62\times10^{14}+1.34\times10^{13}=3.75\times10^{14}\ \mathrm{Bq/a}$$

$$p_{\mathrm{coal}}^{\mathrm{C1}}=\frac{0.341\times3.75\times10^{14}}{1.10\times10^{16}}=1.2\ \%,\qquad p_{\mathrm{coal}}^{\mathrm{S5}}=\frac{0.341\times3.75\times10^{14}}{1.16\times10^{15}}=11\ \%$$

(The storage term $1.34\times10^{13}$ is PG $1.5\times10^{12}$ + Li $4.2\times10^{11}$ + graphite $2.4\times10^{11}$ + Co–U $3.4\times10^{11}$ + BESS copper $1.1\times10^{13}$.)

### 4.2 Results, 2024 benchmark (basis A, pro-rata; low – central – high)

The low and high are outer bounds that take every input at its extreme together (not independent, so wider than a 95 % interval).

| Stream | Tier 2 as % of C1 (stream total) | Tier 2 as % of S5 (chain solids) | > 5 %? |
|---|---|---|---|
| ① Nuclear | 0.008 – 0.12 – 0.9 | 0.2 – 3.3 – 26 | upper bound only |
| ② Coal | 0.08 – 1.2 – 8.9 | 0.7 – 11 – 85 | S5 central; C1 upper bound |
| ③ Oil and gas | 0.2 – 2.7 – 21 | 1.9 – 30 – 230 | S5 central; C1 upper bound |
| ④ Wind and solar | not applicable (Tier 1 unbuilt) | **11 – 20 – 54** (matched-factor ratio, tonnage bounds) | **yes, all bounds** |
| ⑤ Other | 0.4 – 6.6 – 51 | $3\times10^{3}$ – $5\times10^{4}$ – $4\times10^{5}$ | **yes, central** |

Basis B (storage and VRE connection grid, with Chen's 0.5–0.86–2.0 Mt/a copper and 0.3–0.54–1.2 Mt/a aluminium, charged to ④ alone): ④ **18 – 41 – 190 %** (matched factors). Other streams 0 %.

2020 benchmark (grid only, central; storage about 10 GWh and negligible): ② 1.3 % of C1 / 13 % of S5; ③ 3.0 % / 34 %; ① 0.13 % / 4.7 %; ⑤ 7.2 % / $1.5\times10^{4}$ %; ④ 16 – 35 – 79 %. Absolute grid S5 $3.6\times10^{14}$ Bq/a.

### 4.3 Reading the table

- **④ and ⑤ exceed 5 % because their Tier 1 is small, not because Tier 2 is large.** Hydro, biomass and geothermal have almost no residue footprint. ⑤'s C1 is geothermal radon; its S5 is $10^{11}$ Bq/a. Any grid share is therefore enormous against S5. Conclusion: the per-TWh lifecycle view (D22) will show the technologies with the least Tier 1 residue carrying the largest relative Tier 2 addition.
- **The copper factor controls ①②③.** At the low copper bound, grid S5 falls to $2.3\times10^{13}$ and ②'s S5 percentage to 0.7 %. The "include" verdict still stands because of ④ and ⑤.
- **Chemistry-specific storage items are negligible**: summed chemistries $2.5\times10^{12}$ Bq/a central at 2024 (0.7 % of Tier 2); BESS copper $1.1\times10^{13}$ (3 %); grid $3.6\times10^{14}$ (96 %).
- **Radon and the engine**: these are Tier 2 residue inputs (impounded tailings). Their radon exhalation arises in the Phase 3 engine through $\varepsilon$ for `metal_tailings` and `red_mud`; it is not in the stream rows and is not in C1 here. With the seed epsilon (0.002–0.05, `research/wind_solar/notes.md` §8) the chronic exhalation from grid copper tailings will add to Tier 2's effective size in the engine, not in this table.

---

## 5. Double-counting register

| Overlap | With | Commodity name (Task 2.4) | Rule |
|---|---|---|---|
| Cu, Al, steel, cement, zinc, lead, silicon, nickel footprints | Task 2.4 registry and Tier 1 construction (every stream) | `copper`, `aluminium`, `steel`, `cement`, `aggregate`, `zinc`, `lead`, `silicon_mg`, `nickel` | One shared table (METHODS 6.2). Tier 2 tonnes are additional tonnes; the footprints are identical, so the factors do not double count. |
| In-plant cabling | ④ JRC intensities (PV BoS 4 600 t Cu/GW; wind excludes array cables and transformers per `material_intensity.csv` notes) vs Chen connection grid | `copper`, `aluminium` | **Boundary rule needed**: Tier 2 starts at the plant's point of interconnection (substation). PV BoS cabling stays in Tier 1; Chen's inter-array and export-line figures partly overlap it for PV. Estimate the overlap before use. |
| Embedded fuel in smelting and graphitisation (Al electrolysis, Cu smelting, Ni, Acheson graphite) | ② and ③ (industry view); ④ lifecycle view | — | Counted in ②/③ already; add to Tier 2 only in the lifecycle view (D22). |
| Gas for peakers; crude for transformer oil, polymers, petroleum coke | ③ | — | Already in ③ (whole industry). |
| Coal for coke, power for smelters | ② | — | Already in ②. |
| Hydro and pumped hydro | ⑤ hydro | `cement`, `aggregate`, `steel` | ⑤ hydro negligible by construction (METHODS 10.3). |
| Brine Li (DLE) | ③ `og_produced_water`; ⑤ `geothermal_brine`, `geothermal_scale` | — | Watch item. |
| Vanadium from oil/coal ash and spent catalyst; U–V co-production | ③ `oil_sands_coke`; ② ash; ① uranium mining | — | Already counted at source. |
| Phosphogypsum from LFP | D4 sequel (phosphate) | `phosphate_rock` (not in the commodity vocabulary; present in `commodity_production.csv`) | Pointer to sequel; no Tier 2 row. |
| DRC cobalt hydroxide uranium | Not in ① (not fuel-cycle); not a copper-tailings undercount (revised 2026-11-11) | none for v2 | Page callout only (`copper_classes.md` section 7). |
| Steel scrap with NORM scale | ③ `abandonment_scrap` | `steel` | Not Tier 2. |

---

## 6. Uncertainty, contradictions and caveats

1. **Copper tailings footprint** is the dominant uncertainty: factor 40 spread (seed table), single-source tonnages per tonne ore, and the D6 allocation (0.7–1.0 assumed for copper). **Task 2.4 changed it 2026-11-11: spread now 8x, central 0.35x; remaining uncertainty is Chilean tailings (unmeasured), other IOCG uranium and the 200 t/t tonnage; see the revision box.**
2. **Grid tonnage** rests on one grey source (3 Mt Cu, 5–6 Mt Al) plus cross-checks on different bases (IEA 2030 share, ETC cumulative, Chen's VRE-only grid). The T&D split (transmission only, versus distribution) is unknown; if Tier 2 were limited to transmission above, say, 100 kV, I would expect a smaller fraction of the copper, but I found no source for the split, so I include all T&D **[A]**.
3. **Stationary storage in 2020** (10 GWh) is unsourced; 2024 values come from two independent trackers (170 vs 205 GWh), a 20 % spread. Rho Motion's "deployments" and BNEF's "installations" definitions differ.
4. **LFP share and bill of materials** for stationary storage are applied from automotive BatPaC packs.
5. **No NORM measurements found** for: lithium ore and tailings, Li brine, HPAL residue, laterite ore, natural graphite, synthetic graphite. Crustal assumption (0.17 Bq/g S5) is used for magnitude testing only.
6. **Cobalt–uranium**: one peer-reviewed study (not read in full by me), contested by the main operator, with press reports of leaked data. Strong enough to cite, not strong enough to enter a stream.
7. **Contradiction on bounds:** Chen et al. cumulative copper for VRE connection grids (27–81 Mt, 2021–2050; about 0.9–2.7 Mt/a averaged) is not far below the ETC/Thunder Said total grid copper (3–7 Mt/a). That implies VRE connection could be a third or more of all grid copper, which supports basis B; but Chen's scenarios (SDS/NZE) are forward-looking deployments, not 2024 actuals.
8. **Measure choice flips the verdict for ②③** (C1 central 1–3 %; S5 central 11–30 %). The memo reports both rather than choosing.
9. **Percentages are conservative for ② and ③** because the industry-view denominators include non-power use (D22).
10. **Minor corrections to project notes**: `research/unscear_notes.md` §5 cites ¶10 for the storage/T&D exclusion; it is ¶9 and limitation (e) in ¶221.
11. **Not verified**: DRC cumulative cobalt output (used for the 2024 uranium scaling) and the 2020 DRC cobalt figure were recalled, not read; recompute from USGS (section 8).

---

## 7. Recommendation table

| Item | NORM pathway | Order of magnitude (2024) | Material vs Tier 1? | Recommendation | Reason |
|---|---|---|---|---|---|
| Conductors, Cu cables (T&D) | Cu tailings, smelter slag and off-gas | **$1.2\times10^{14}$ Bq/a S5 ($3.7\times10^{13}$–$8.8\times10^{14}$; revised 2026-11-11, was $3.4\times10^{14}$)** | **Yes** (④ always; ②③ central S5) | **Stream (stage `grid`)** | Largest item; no new factors; commodity-driven |
| Conductors Al (ACSR, AAAC) | Red mud | $1.7\times10^{13}$ Bq/a | Marginal | **Stream (same stage)** | Same mechanism; 5 % of grid term |
| Steel towers, cores, GOES, galvanising (Zn) | Iron-ore tailings, slag; stack Pb/Po | $\sim10^{12}$ Bq/a | No | **Include in tonnage, no separate item** | Steel and zinc footprints tiny |
| Subsea cable lead sheath | Pb mining and smelting | $\ll10^{12}$ Bq/a | No | **Memo-only** | No seed factor; small tonnage |
| Transformer oil | Refined distillate (NORM stays upstream) | $\approx0$ | No | **Exclude** | Overlap with ③ |
| HVDC converter stations | Cu, Al, steel, Si, concrete | included in grid tonnage | No | **Exclude as separate item** | Same commodities |
| Li-ion BESS Cu/Al/steel | Cu tailings etc. | $1.1\times10^{13}$ Bq/a | Marginal | **Stream (stage `grid`, storage substream)** | Largest storage term |
| Lithium (spodumene) | Pegmatite tailings (crustal assumed) | $4\times10^{11}$ Bq/a stationary; $\sim10^{13}$ all Li | No | **Memo-only** | No measured NORM; revisit if over 1 Bq/g |
| Lithium (brine) | Evaporite salts | no data | No | **Memo-only; watch DLE overlap with ③/⑤** | Data gap |
| Cobalt (Cu–Co, DRC) | U co-precipitating in Co hydroxide; Katanga tailings | $2$–$5\times10^{12}$ Bq/a (25-yr mean U-238+U-234); stationary share about $3\times10^{11}$ | No (Tier 2 share tiny) | **Memo-only for Tier 2; pass to Task 2.4/sequel; flag to Steve** | Notable "unexpected source"; EV-dominated |
| Co, Ni (laterite, HPAL residue) | Soil-like residue, 180 t/t Ni | $<2\times10^{13}$ all battery Ni | No | **Memo-only** | No NORM data |
| Ni (sulphide) | Sulphide tailings | not estimated | No | **Memo-only (in `nickel`)** | Task 2.4 |
| Graphite (natural) | Flake tailings | $2\times10^{11}$ Bq/a | No | **Memo-only** | No NORM data |
| Graphite (synthetic) | Petroleum coke, electricity | embedded fuel | No | **Exclude** | Counted in ③/② |
| Manganese (HPMSM) | Mn ore (one site 3.5 Bq/g U-238) | no estimate | No | **Memo-only** | Unrepresentative data |
| Phosphate for LFP | Phosphogypsum (Ra-226 0.4–1 Bq/g, 5 t/t P$_2$O$_5$) | $1.5\times10^{12}$ Bq/a S5 | No | **Memo-only, pointer to non-energy sequel** | Outside D4 |
| Pumped hydro | Cement, steel | $\lesssim10^{12}$ Bq/a | No | **Exclude** | Hydro negligible (10.3) |
| Vanadium flow batteries | Titanomagnetite slag; oil ash | under 0.01 % of world V | No | **Exclude** | Tiny deployment |
| Lead-acid | Pb-210 in lead | $\sim10^{11}$ Bq/a locked in product | No | **Exclude** | Little grid use |
| Gas peakers | Gas production | in ③ | n/a | **Exclude** | Already in ③ |
| Other firming (hydro, biomass, nuclear, coal) | in ⑤, ①, ② | n/a | n/a | **Exclude** | Already counted |

**Most material Tier 2 item: T&D copper.** If v2 includes only one new row family, it is the `grid` stage.

---

## 8. Inaccessible, unread or partly read sources (most to least important)

1. Manzuk and Philippe 2026, *Nature Communications*, "Uranium in cobalt-hydroxide exports from the Democratic Republic of the Congo": https://www.nature.com/articles/s41467-026-75910-z (fetch failed; DOI inferred 10.1038/s41467-026-75910-z). Needed for U ppm in hydroxide, annual masses and the Chinese refining fate.
2. Deetman et al. 2021, *Resources, Conservation and Recycling*, "Projected material requirements for the global electricity infrastructure: generation, transmission and storage": https://doi.org/10.1016/j.resconrec.2020.105200 (open access; the Leiden repository https://scholarlypublications.universiteitleiden.nl/access/item:3275389/view gave only the abstract). Needed for primary T&D copper, aluminium and steel tonnages and storage intensities.
3. IEA, *Electricity Grids and Secure Energy Transitions* (2023) and *Global Critical Minerals Outlook 2025*: https://www.iea.org/reports/global-critical-minerals-outlook-2025/overview-of-outlook-for-key-minerals (fetch failed). Needed for grid copper demand and battery metal shares.
4. USGS Mineral Commodity Summaries 2026 for lithium, cobalt, graphite, nickel (my requests were blocked): https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-lithium.pdf, https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-cobalt.pdf, https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-graphite.pdf, https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-nickel.pdf. Needed for 2025 production, DRC cobalt history, and natural graphite tonnage.
5. Gbondo et al. 2025, *J. Hazard. Mater. Adv.* 18, "Radioactivity and exposure to radiation in lithium mining in Western Australia": https://espace.curtin.edu.au/handle/20.500.11937/97173 (abstract read; full tables needed for ore, concentrate and tailings activities).
6. Chen, Kleijn and Lin 2023, *Environ. Sci. Technol.* 57(2):1080–1091, Supporting Information Table S2 (per-km and per-GW intensities): https://pmc.ncbi.nlm.nih.gov/articles/PMC9850911 (main text read; SI not).
7. Atibu et al. 2021, "Assessment of natural radioactivity in the copper belt region, Kolwezi Province, DRC", *J. Geosci. Environ. Prot.* 9:1–20 (cited in https://access.archive-ouverte.unige.ch/access/metadata/bcecfc39-96a3-45bc-a812-ae4bbdc89ecf/download; not read).
8. Lighthouse Reports investigation (with the *Financial Times*): https://www.lighthousereports.com/investigation/congos-hidden-uranium-exports/ (appeared in search; not opened) and the phys.org summary https://phys.org/news/2026-09-drc-cobalt-exports-unreported-uranium.html (fetch failed).
9. Thunder Said Energy, "Power grids down to the wire" (2023), paywalled; only a summary read: https://thundersaidenergy.com/downloads/power-grids-down-to-the-wire/. The 3 Mt Cu and 5–6 Mt Al figures are from this summary.
10. IEA, *The Role of Critical Minerals in Clean Energy Transitions* (2021) and Argonne GREET battery updates (https://greet.anl.gov/files/battery_updates) for stationary-pack intensities.
11. NREL pumped-storage life-cycle assessment full report (https://www.nrel.gov/water/life-cycle-assessment-closed-loop-pumped-storage-hydropower-facilities) and Simon et al. 2023 *Environ. Sci. Technol.* (DOI 10.1021/acs.est.2c09189, listed in search) for pumped-hydro tonnages.
12. BNEF / Rho Motion primary reports on 2023–2024 stationary storage (only trade-press summaries read).
13. IAEA-TECDOC-1712 (https://www-pub.iaea.org/MTCD/Publications/PDF/TE-1712_web.pdf): searched by keyword only, not read in full.
14. Wikipedia pages appeared in search results; not used (banned source).

---

## 9. Proposed rows for `data/sources.csv` (not applied)

Columns: `source_id,short_cite,full_citation,url,doi,year,type,rank,access,licence,notes`. IDs S1800–S1823 are unused in `data/sources.csv` and the `research/*/sources*.csv` files (highest in use S1704). Check for clashes with the concurrent Task 2.4 work before applying. The `access` values follow `vocab.json` (`open`, `paywalled`, `inaccessible`). Existing sources cited by ID: S0001 (UNSCEAR 2016 Annex B), S0008 (UNSCEAR 1988), S0202 (IAEA TRS 419), S0400 (JRC 2020), S0404 (IAEA SRS 68), `baselines.csv` S0604/S0613 (UNSCEAR 2000 soil medians).

```csv
S1800,IAEA SRS-49 (2006),"IAEA (2006). Assessing the Need for Radiation Protection Measures in Work Involving Minerals and Raw Materials. Safety Reports Series No. 49, STI/PUB/1257. IAEA, Vienna.",https://www-pub.iaea.org/MTCD/Publications/PDF/Pub1257_web.pdf,,2006,compilation,2,open,restricted,"Read 2026-11-10. Table 1 (materials for possible regulatory control) and s3.1.9; no entry for Li, Co, Ni, Mn, graphite or V. Licence: IAEA copyright; not checked."
S1801,IAEA SRS-78 (2013),"IAEA (2013). Radiation Protection and Management of NORM Residues in the Phosphate Industry. Safety Reports Series No. 78. IAEA, Vienna.",https://www-pub.iaea.org/MTCD/Publications/PDF/Pub1582_web.pdf,,2013,compilation,2,open,restricted,"Read 2026-11-10. 4-6 t phosphogypsum per t P2O5 (dry); Table 56 Ra-226 in phosphogypsum 0.015-3.2 Bq/g; world production about 160 Mt/a (mid-2000s)."
S1802,IAEA-TECDOC-1712,"IAEA (2013). Management of NORM Residues. IAEA-TECDOC-1712. IAEA, Vienna.",https://www-pub.iaea.org/MTCD/Publications/PDF/TE-1712_web.pdf,,2013,compilation,2,open,restricted,"Keyword search only 2026-11-10 (no hits for lithium, cobalt, nickel, graphite, vanadium, manganese or batteries). Year to be verified."
S1803,Knehr et al. 2024 (ANL/CSE-24/1),"Knehr, K., Kubal, J. and Ahmed, S. (2024). Cost Analysis and Projections for U.S.-Manufactured Automotive Lithium-ion Batteries. ANL/CSE-24/1. Argonne National Laboratory.",https://publications.anl.gov/anlpubs/2024/01/187177.pdf,,2024,agency,4,open,open,"Bill of materials per kWh of pack (Tables 34-36 as reported by the extraction tool): LFP CAM 1.93, Li 0.09, graphite AAM 0.98 kg/kWh; automotive packs applied to stationary use (assumption)."
S1804,Chen et al. 2023 (VRE grids),"Chen, Z., Kleijn, R. and Lin, H.X. (2023). Metal requirements for building electrical grid systems of global wind power and utility-scale solar photovoltaic until 2050. Environmental Science & Technology 57(2):1080-1091.",https://pmc.ncbi.nlm.nih.gov/articles/PMC9850911,,2023,peer_reviewed,3,open,open,"Main text read 2026-11-10; Supporting Information Table S2 (intensities) not read. 27-81 Mt Cu and 11-31 Mt Al cumulative 2021-2050 for wind and utility PV connection grids only. DOI to be added."
S1805,Deetman et al. 2021,"Deetman, S. et al. (2021). Projected material requirements for the global electricity infrastructure: generation, transmission and storage. Resources, Conservation and Recycling, article 105200.",https://scholarlypublications.universiteitleiden.nl/access/item:3275389/view,10.1016/j.resconrec.2020.105200,2021,peer_reviewed,3,open,open,"Abstract only read; tables not retrieved. Primary candidate for global T&D tonnages. Author list and volume to be completed."
S1806,Manzuk and Philippe 2026,"Manzuk, R. and Philippe, S. (2026). Uranium in cobalt-hydroxide exports from the Democratic Republic of the Congo. Nature Communications (published 30 July 2026).",https://www.nature.com/articles/s41467-026-75910-z,10.1038/s41467-026-75910-z,2026,peer_reviewed,3,inaccessible,unknown,"NOT OBTAINED (fetch failed). Content from Princeton SPIA summary: 2000-5000 t U in Co hydroxide exports 2000-2024; 1000-4000 t U discarded in mobile forms at mines; under 10 percent apparently declared. DOI inferred from the URL."
S1807,Princeton SPIA 2026 news,"Princeton School of Public and International Affairs (2026). Undocumented Uranium Exports in the Democratic Republic of the Congo (news item on Manzuk and Philippe).",https://spia.princeton.edu/news/undocumented-uranium-exports-democratic-republic-congo,,2026,grey,5,open,unknown,"Secondary summary of S1806, read 2026-11-10."
S1808,Intellinews 2026-08-03,"bne IntelliNews (3 August 2026). DRC cobalt exports to China may have contained up to 5,000 tonnes of uranium, study finds.",https://intellinews.com/drc-cobalt-exports-to-china-may-have-contained-up-to-5-000-tonnes-of-uranium-study-finds-458657,,2026,grey,5,open,unknown,"Press report; Tenke Fungurume record of 1100 ppm U (December 2016); CMOC rejected the findings."
S1809,Gbondo et al. 2025,"Gbondo, D., Pham, M., Zhao, Y. and Rumchev, K. (2025). Radioactivity and exposure to radiation in lithium mining in Western Australia. Journal of Hazardous Materials Advances 18.",https://espace.curtin.edu.au/handle/20.500.11937/97173,,2025,peer_reviewed,3,open,open,"Abstract only. Tantalum concentrate highest mean emission 2.169 Bq/g; no ore, spodumene or tailings activities in the abstract. Full text needed."
S1810,Abdel-Ghany 2009 (Mn ore),"Abdel-Ghany, H.A. (2009). Monitoring of natural radioactivity in manganese ore. Nuclear Physics and Atomic Energy 10(4):433-436.",https://jnpae.kinr.kyiv.ua/10.4/html/jnpae-2009-10-433-Abdel-Ghany.html,,2009,peer_reviewed,3,open,open,"Sinai (Egypt) manganese ore: U-238 3543, Th-232 222, K-40 3483 Bq/kg. One site; not representative."
S1811,Atibu et al. 2021 (Kolwezi),"Atibu, E.K., Oliveira, J.M., Malta, M., Santos, M., Mulaji, C.K., Mpiana, P.T. and Carvalho, F.P. (2021). Assessment of natural radioactivity in the copper belt region, Kolwezi Province, of the Democratic Republic of the Congo. Journal of Geosciences and Environment Protection 9:1-20.",,,2021,peer_reviewed,3,inaccessible,unknown,"NOT OBTAINED. Cited in a 2022 Minerals paper (Atibu et al.) via https://access.archive-ouverte.unige.ch/access/metadata/bcecfc39-96a3-45bc-a812-ae4bbdc89ecf/download: river sediments Luilu 154, Dilala 378 Bq/kg U-238."
S1812,USGS MCS 2025 Lithium,"USGS (2025). Mineral Commodity Summaries 2025: Lithium. U.S. Geological Survey.",https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-lithium.pdf,,2025,agency,4,open,open,"World mine production 2023 204 kt, 2024e 240 kt Li; batteries 87 percent of end use."
S1813,USGS MCS 2026 Vanadium,"USGS (2026). Mineral Commodity Summaries 2026: Vanadium. U.S. Geological Survey.",https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-vanadium.pdf,,2026,agency,4,open,open,"World 118 kt V (2024); China about 71 percent from titanomagnetite coproduct; Utah U-V production ceased early 2020; flow batteries mentioned without tonnage."
S1814,IISD cobalt profile 2026,"IISD (2026). Commodity profile: cobalt.",https://www.iisd.org/system/files/2026-05/commodity-profile-cobalt.pdf,,2026,grey,5,open,unknown,"2024 world 290 kt, DRC 220 kt (75.9 percent); 78 percent of cobalt from Cu-Co, 22 percent from Ni; crude Co hydroxide about 31 percent Co. Authors to be added."
S1815,IEA GCMO 2025 executive summary,"IEA (2025). Global Critical Minerals Outlook 2025, Executive summary.",https://www.iea.org/reports/global-critical-minerals-outlook-2025/executive-summary,,2025,agency,4,open,restricted,"China 75 percent of purified phosphoric acid and 95 percent of high-purity manganese sulphate; energy sector 85 percent of demand growth for Li, Ni, Co, graphite over two years."
S1816,Rho Motion 2024 BESS (Energy-Storage.News),"Hughes, I. (Rho Motion) (2025). Global BESS deployments soared 53 percent in 2024. Energy-Storage.News / PV Tech Power.",https://www.energy-storage.news/global-bess-deployments-soared-53-in-2024,,2025,grey,5,open,unknown,"2024: 205 GWh (+53 percent); grid-scale 160 GWh vs 96 GWh in 2023; 98 percent of grid deployments lithium-ion."
S1817,BNEF 2024 stationary storage (ESS News),"BloombergNEF via ESS News (18 December 2024). Stationary storage installations surge to 170 GWh in 2024.",https://www.ess-news.com/2024/12/18/bloombergnef-stationary-storage-installations-surge-to-170-gwh-in-2024/,,2024,grey,5,open,unknown,"2024 about 168 GWh; 2023 96.1 GWh; 2025 forecast 71 GW / 193 GWh. December 2024 estimate, not a year-end count."
S1818,Thunder Said Energy grids,"Thunder Said Energy (2023). Power grids: down to the wire.",https://thundersaidenergy.com/downloads/power-grids-down-to-the-wire/,,2023,grey,5,paywalled,restricted,"Summary page only: grids use 5-6 Mt/a Al (8 percent of demand) and about 3 Mt/a Cu (10 percent). Single source for the absolute T&D tonnage; verify against S1805."
S1819,ETC copper factsheet,"Energy Transitions Commission (2023). Materials factsheets: copper.",https://www.energy-transitions.org/wp-content/uploads/2023/07/ETC_Materials_Factsheets_copper.pdf,,2023,grey,5,open,unknown,"Cumulative 2022-2050 baseline copper: T&D 200 Mt, stationary batteries 1 Mt, wind 102 Mt, solar 97 Mt, EVs 224 Mt."
S1820,IEA ETP 2023 enabling infrastructure,"IEA (2023). Energy Technology Perspectives 2023, Enabling infrastructure.",https://www.iea.org/reports/energy-technology-perspectives-2023/enabling-infrastructure,,2023,agency,4,open,restricted,"Grid and transformer copper almost 20 percent of global production in 2030; GOES capacity 3.8 Mt/a to 6 Mt/a by 2030."
S1821,Benchmark Minerals HPAL waste,"Benchmark Source (n.d.). Opinion: Overcoming mining waste issues will be key to Indonesia's nickel ambitions.",https://source.benchmarkminerals.com/article/opinion-overcoming-mining-waste-issues-will-be-key-to-indonesias-nickel-ambitions,,,grey,5,open,unknown,"PT Lygend (Obi): about 1.2 t waste per t ore; about 11 Mt/a waste. Date and author to be added."
S1822,Simon et al. 2022 (NREL PSH),"Simon, T., Inman, D., Heath, G., Hanes, R. and Avery, G. (2022). Life Cycle Assessment for Closed-Loop Pumped Hydropower Energy Storage in the United States. NREL/PR-6A20-81315.",https://nrel.gov/docs/fy22osti/81315.pdf,,2022,agency,4,open,open,"Slides; concrete 34 percent and steel 26 percent of 0.086 kg CO2-eq/kWh; no tonnages."
S1823,Lutter et al. 2017,"Lutter, G., Vandael Schreurs, I., Croymans, T., Schroeyers, W., Schreurs, S., Hult, M., Marissens, G., Stroh, H. and Tzika, F. (2017). A low-energy set-up for gamma-ray spectrometry of NORM tailored to the needs of a secondary smelting facility. Applied Radiation and Isotopes 126:296-299.",https://documentserver.uhasselt.be/bitstream/1942/25401/2/SchroeyersW.pdf,,2017,peer_reviewed,3,open,open,"One 47 percent Pb sample at 53 Bq/g Pb-210; proof of concept; not representative."
```

---

## 10. Gaps and hand-offs

**For the orchestrator and Steve**
- Decide whether v2 adds a `grid` stage (recommended) and whether the threshold measure is C1 (stream total as the page shows it) or S5 (like-for-like). The verdict is "yes" either way, for different streams.
- Boundary rule needed with Task 2.4: where PV/wind balance-of-system cabling ends and Tier 2 begins (section 5).
- The cobalt–uranium paper is a candidate "unexpected source" callout for the page; it is not a Tier 2 matter.
- Phosphate for LFP is another instance of the D4 sequel gap (non-energy phosphate).

**For Task 2.4**
- Copper footprint (generic and regional: Katanga, Olympic Dam) is the single most consequential input in this memo. Report the final D6-allocated copper and aluminium S5 so section 4.1 can be re-run; a `cobalt` commodity (DRC) and a Katanga copper override are worth considering.
- The seed aluminium footprint has three groups only; add Pb-210/Po-210 if available.

**Research gaps (no data found)**
- NORM in lithium ore, concentrate and tailings; Li brines; laterite ore and HPAL residue; natural and synthetic graphite; Mn ore beyond one Egyptian site.
- Primary global T&D tonnage (Deetman 2021 tables); transmission-only share.
- Stationary-storage chemistry split and stationary-specific bill of materials; 2020 stationary GWh.
- Pumped-hydro tonnage per GW; flow-battery deployments; vanadium kg per kWh.
- DRC cobalt production history for the cobalt–uranium scaling.

**Verification note.** Section 4.1 gives the full arithmetic for ② coal 2024 (central) so a verifier can recompute one stream from the stream files and the seed footprints. The stream totals in section 2 were computed by summing `value_central` for `quantity = flow` over the non-Sealed, non-memo tiers in `data/streams/<stream>.csv.gz` for years 2020 and 2024.
