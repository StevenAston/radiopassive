# Radiopassive — Methods Specification (v1, Energy Edition)

> **Status:** DRAFT for sign-off (Task 0.1). Sections marked **PROPOSED** introduce rules beyond the confirmed plan and need Steve's approval.
> **Governs:** every dataset, script and chart in this project. If anything here conflicts with `PLAN.md`, the plan wins until this document is updated.

---

## 1. Purpose and framing

This document turns the confirmed decisions (D1–D20 in `PLAN.md` and `docs/DECISIONS.md`) into operational rules that a person or agent can apply without further judgement.

The framing thesis governs presentation, not calculation: **radiation is like water.** The calculations are deliberately neutral physical accounting (decays per second, watts, tonnes, containment), never bodily harm.

### 1.1 Rationale summary for D1–D20

| ID | Why |
|---|---|
| D1 | Bq and W are physical quantities with no bodily interpretation; W weights by decay energy without biology; dose stays internal because collective dose of tiny individual doses is not a valid predictor of harm (ICRP 103), and the page is about reservoirs, not casualties. |
| D2 | Separates material *mobilised* from material *released*; without it, impounded thorium and stack emissions would be added together as if equivalent. |
| D3 | Persistence differs by orders of magnitude between fission products and primordial chains; only a stock model shows it. |
| D4 | The four streams Steve asked for, plus one "other energy" bucket that fits the fifth chart colour; non-energy left for a sequel to keep v1 tractable. |
| D5 | A boundary that differs between streams invites the charge of a rigged comparison; material intensity is part of the story. |
| D6 | ISO 14044's fallback for co-products; showing both extremes removes any suspicion of a convenient choice. |
| D7 | Most pre-1990 values are modelled; showing that honestly is better than false precision. |
| D8 | Absolute totals reflect industry scale; per-TWh reflects intensity; the ranking differs between them. |
| D9 | Accidents are part of the civil record; weapons programmes are a different subject but give essential scale. |
| D10 | Global totals answer the question; country rows cost nothing to keep and allow later breakdowns. |
| D11 | Every industrial number needs a natural reference at the same scale — the water table the puddles sit on. |
| D12 | House style; SI coherence makes Bq ↔ W conversion trivial. |
| D14 | One start year keeps all charts aligned. |
| D15 | Accidents are real; a toggle lets the reader see routine operation without one year dominating. |
| D16 | Documented end use is the most defensible split; the 1965 default reflects that almost all earlier uranium went to weapons programmes. |
| D17 | Deep injection returns material underground; calling it a release would overstate, ignoring it would understate. |
| D18 | Bounds are proportionate to data quality; Monte Carlo adds machinery without adding information at this stage. |

---

## 2. Scope

### 2.1 Time

- Annual resolution, **1950 to the latest year with data** (D14), for every stream; the nuclear stream reads near zero until civil power begins (~1956). The target end year is 2025; streams whose data stop earlier are extrapolated to 2025 with `basis = extrapolated`.
- Years are calendar years. Where a source reports fiscal years, it is mapped to the calendar year containing most of its months, and this is noted.

### 2.2 Geography

- Global totals on the page; **country-level rows are kept** wherever a source provides them (D10). Countries are coded ISO 3166-1 alpha-3. Two codes from ISO's user-assigned range (X**) are used for non-countries: `XWL` for a global aggregate and `XXX` for an unallocated remainder. Historical states use their former alpha-3 codes as recorded in ISO 3166-3 (`SUN` USSR, `CSK` Czechoslovakia, `YUG` Yugoslavia, `DDR` East Germany); West Germany before 1990 is `DEU`.
- **No double counting:** global totals are calculated as the sum of country rows plus an explicit `XXX` remainder, never as a separate global figure added on top.

### 2.3 Streams

| # | Stream | Colour token | Sub-streams |
|---|---|---|---|
| ① | Nuclear (civil fuel cycle) | `chart-1` | by fuel-cycle stage; reactor type where relevant |
| ② | Coal | `chart-2` | by stage; power vs non-power use |
| ③ | Oil and gas | `chart-3` | **conventional**, **unconventional** and **oil sands / extra-heavy oil** (D4); oil vs gas |
| ④ | Wind and solar materials | `chart-4` | **wind** and **solar**; by commodity |
| ⑤ | Other energy | `chart-5` | geothermal; biomass and peat; hydro |

Non-energy sources (phosphate, mineral sands, metals for non-energy uses) are **out of scope** for v1 and left for the sequel. Military activity is out of scope except as a baseline (D9).

**Oil and gas sub-streams defined:**
- **Unconventional:** production from hydraulically fractured shale and tight formations (shale gas, tight gas, tight oil) and coalbed methane.
- **Oil sands / extra-heavy oil:** mined and in-situ bitumen and extra-heavy crude (e.g. Athabasca, Orinoco). Kept separate because its residues (mine tailings, coke) follow mining rather than well routes.
- **Conventional:** everything else.
- A well is classed by its producing formation in the source data; where a source does not say, the national or play-level share is used and flagged `modelled`.

---

## 3. Quantities, units and conventions

### 3.1 Core quantities

| Symbol | Quantity | SI unit | Meaning |
|---|---|---|---|
| $F_{k,j}(y)$ | Flow | Bq·a⁻¹ | Activity of nuclide group $k$ **added** to tier $j$ during year $y$, valued at the moment it is added |
| $S_{k,j}(y)$ | Stock | Bq | Activity of group $k$ in tier $j$ on 31 December of year $y$, after decay and ingrowth |
| $P$ | Radioactive power | W | Energy emitted per second by a stock or flow (§7) |
| $E$ | Generation | TWh | Electricity generated (for normalisation, §8) |

The becquerel is already a rate (1 Bq = 1 decay·s⁻¹). A flow is therefore "becquerels added per year", and a stock is "how fast the accumulated material is decaying right now".

### 3.2 Counting convention — all decays counted (**PROPOSED, PD4**)

Activity is reported as the **total decays per second of every member of a nuclide group**, at the equilibrium assumed for that group (§4). For example, 1 Bq of U-238 in full secular equilibrium with its daughters is reported as 14 Bq of U-238 series activity, because 14 decays (8 α, 6 β) happen for each U-238 decay.

- *Why:* the becquerel counts decays; reporting only the parent understates the material's activity by a factor of 10–14 and hides the real effect of breaking the chain.
- *Consequence:* our NORM figures will be ~10–14× higher than regulatory figures quoted "per parent". The page states this convention prominently, and the dataset also keeps head-of-group activity so either convention can be shown.
- The same applies to artificial nuclides: regulators report Cs-137 as the parent only, so a reported Cs-137 value is multiplied by $m_{\mathrm{Cs137+}}$ on ingestion. Source values are always stored as reported (head activity), and the multiplier is applied in the pipeline, never in the raw data.

### 3.3 Display units

- Bq with SI prefixes (GBq, TBq, PBq, EBq, ZBq); W with prefixes (mW to TW).
- Customary equivalent in tooltips: curies, with 1 Ci = 3.7 × 10¹⁰ Bq exactly (so 1 PBq ≈ 27.0 kCi).
- Mass in t (tonnes); volume in m³; energy in TWh; time in a (Julian year = 3.155 76 × 10⁷ s).

### 3.4 Physical constants

- 1 eV = 1.602 176 634 × 10⁻¹⁹ J (exact, SI 2019).
- Half-lives, branching ratios and decay energies come from ICRP Publication 107, cross-checked against ENSDF/NNDC (Task 0.3).

---

## 4. Nuclide groups

To keep the decay engine tractable, short-lived daughters are folded into a long-lived **head** and assumed to be in equilibrium with it ("+" groups). The engine tracks heads only; activity is reported by multiplying by the group's **decay multiplier** $m_k$ (decays per head decay, branching-weighted).

**Our groups differ from the regulatory "+" convention.** In Euratom Directive 2013/59 (and e.g. UK Schedule 7), "Ra-226+" also includes Pb-210, Bi-210 and Po-210. Here those are split out (`Pb210+`, `Po210`) because they are often out of equilibrium with Ra-226 (fly ash, gas processing, scale). When a source quotes a regulatory "Ra-226+" value, it is mapped to `Ra226+`, `Pb210+` and `Po210` at equilibrium and flagged; it is never mapped to `Ra226+` alone.

### 4.1 Primordial chains

| Chain | Group (head+) | Members | $m_k$ |
|---|---|---|---|
| U-238 | `U238+` | U-238, Th-234, Pa-234m | 3 |
| | `U234` | U-234 | 1 |
| | `Th230` | Th-230 | 1 |
| | `Ra226+` | Ra-226, Rn-222, Po-218, Pb-214, Bi-214, Po-214 | 6 |
| | `Pb210+` | Pb-210, Bi-210 | 2 |
| | `Po210` | Po-210 (tracked separately because its 138 d half-life is often out of equilibrium) | 1 |
| | **U-238 series total** | | **14** |
| U-235 | `U235+` | U-235, Th-231 | 2 |
| | `Pa231` | Pa-231 | 1 |
| | `Ac227+` | Ac-227, Th-227/Fr-223, Ra-223, Rn-219, Po-215, Pb-211, Bi-211, Tl-207 | 8 |
| | **U-235 series total** | | **11** |
| Th-232 | `Th232` | Th-232 | 1 |
| | `Ra228+` | Ra-228, Ac-228 | 2 |
| | `Th228+` | Th-228, Ra-224, Rn-220, Po-216, Pb-212, Bi-212, Po-212 (64.06%) / Tl-208 (35.94%) | 7 |
| | **Th-232 series total** | | **10** |
| Radon released to air | `Rn222+` | Rn-222, Po-218, Pb-214, Bi-214, Po-214 | 5 |
| | `Rn220+` | Rn-220, Po-216, Pb-212, Bi-212, Po-212 (64.06%) / Tl-208 (35.94%) (geothermal, thoron-rich residues) | 5 |
| Potassium | `K40` | K-40 | 1 |

Natural uranium: the U-235 series head activity is 0.0461 × that of U-238 (from atom abundances 0.7204% and 99.2742%, half-lives 7.038 × 10⁸ a and 4.468 × 10⁹ a; Task 0.3 confirms).

**Multipliers for released radon** (`Rn222+`, `Rn220+`) assume full equilibrium with the progeny. That is a counting convention: in air, equilibrium is often not reached before dilution and deposition (Pb-212's half-life is 10.6 h). Every decay is still counted, because the progeny decay wherever they end up.

The members, $m_k$ and branching ratios in this table are provisional until Task 0.3 verifies them against ICRP 107. The checks done so far: the series totals 14 / 11 / 10 match the α + β counts (8 + 6, 7 + 4, 6 + 4), and the Bi-212 branching is 64.06% / 35.94%.

### 4.2 Artificial nuclides (nuclear stream)

| Class | Groups |
|---|---|
| Noble gases | Ar-41, Kr-85, Kr-85m, Kr-87, Kr-88, Xe-131m, Xe-133, Xe-133m, Xe-135, Xe-138 |
| Light / activation | H-3, C-14, Co-58, Co-60, Mn-54, Fe-55, Ni-63, Sb-125 |
| Fission products | `Sr90+` (Sr-90, Y-90; $m$=2), `Cs137+` (Cs-137, Ba-137m; $m$≈1.946, from the DDEP branching of 94.57%; final value from Task 0.3), Cs-134, Cs-135, `Ru106+` (Ru-106, Rh-106; $m$=2), Ru-103, `Ce144+` (Ce-144, Pr-144; $m$=2), `Ba140+` (Ba-140, La-140; $m$=2), `Zr95+` (Zr-95, Nb-95; $m$≈2), Mo-99, Tc-99, I-129, I-131, I-133, Te-132, Pm-147, Sm-151, Eu-154, Eu-155 |
| Actinides | U-233, U-234, U-236, Np-237, Np-239, Pu-238, Pu-239, Pu-240, Pu-241, Pu-242, Am-241, Am-243, Cm-242, Cm-244, Cm-245, Cm-246 |

For spent-fuel **inventory**, a reduced set is used that together accounts for ≥ 99% of activity and ≥ 99% of decay heat at every cooling time from 1 to 10⁴ years. The set is drawn from the lists above and is confirmed against a published per-tHM inventory in Task 1.2. Long-lived members such as Am-243, Cm-245/246, U-233/234/236 and Cs-135 are expected to be needed at long cooling times.

### 4.3 Candidate nuclides per stream (done condition (b))

| Stream | Candidate groups |
|---|---|
| ① Nuclear | Mining/milling: `U238+`, `U234`, `Th230`, `Ra226+`, `Pb210+`, `Po210`, `U235+`, `Pa231`, `Ac227+`, `Rn222+`. Effluents: noble gases, H-3, C-14, I-129, I-131, `Cs137+`, Cs-134, `Sr90+`, Co-60, Co-58, Mn-54, Sb-125, Tc-99, `Ru106+`, Pu/Am. Spent fuel and in-core inventory: §4.2 reduced inventory set. Accidents: I-131, I-133, Te-132, Cs-134, `Cs137+`, `Sr90+`, Xe-133, Kr-85, `Ba140+`, `Zr95+`, Ru-103, `Ru106+`, Mo-99, Np-239, `Ce144+`, Pu-isotopes. |
| ② Coal | `U238+`, `U234`, `Th230`, `Ra226+`, `Pb210+`, `Po210`, `U235+`, `Pa231`, `Ac227+`, `Th232`, `Ra228+`, `Th228+`, `K40`, `Rn222+` (mines, ash). |
| ③ Oil and gas | `Ra226+`, `Ra228+`, `Th228+` (ingrowth in scale), `Pb210+`, `Po210` (gas processing, scale), `Rn222+` (gas, processing), `K40` (produced water). |
| ④ Wind and solar materials | `Th232` series groups (monazite, Bayan Obo, ionic clays), U-238 and U-235 series groups (REE ores, copper-uranium ores, bauxite red mud), `Pb210+` and `Po210` (smelter off-gas), `Rn222+` (tailings), `K40`. |
| ⑤ Other energy | Geothermal: `Rn222+`, `Rn220+`, `Ra226+`, `Ra228+`, `Pb210+`. Biomass/peat: `K40`, `Cs137+` (re-released fallout), `Pb210+`, `Po210`, U-series heads in peat. Hydro: none (negligible, §10). |

---

## 5. Containment tiers (D2, D17)

### 5.1 Definitions

| Tier | Water analogue | Definition |
|---|---|---|
| **Sealed** | Tank | Material in engineered, licensed containment whose design purpose is radiological isolation: the in-core inventory of operating reactors (§5.4), spent fuel (pools, dry casks), vitrified high-level waste, licensed LLW/ILW facilities, uranium products and depleted-uranium stocks in licensed storage. |
| **Impounded** | Reservoir behind a dam | Solid or liquid residue held in a surface or near-surface deposit whose primary purpose is holding material, not radiological isolation: tailings dams, ash ponds and landfills, scale/sludge disposal sites, evaporation ponds. |
| ↳ **Re-isolated** (sub-tier) | Water pumped back into the aquifer | Material returned to deep geological formations: produced water injected into disposal wells **or** reinjected into the producing formation (waterflood, EOR); ISL waste injected into deep wells; residues backfilled into underground mines (coal-ash backfill, uranium paste backfill). Shown inside Impounded, distinguished by pattern. Material is assumed to stay re-isolated unless an event (§9) documents a return. |
| **Dispersed** | Spread on the fields | Material deliberately spread on land or built into products or the landscape in solid or adsorbed form: fly ash in concrete and fill, FGD gypsum in wallboard, produced brine spread on roads, land-farmed sludge, ash spread on soil. |
| **Liberated** | In the river or sky | Emitted to the atmosphere, surface water or sea, by routine discharge or accident. |

### 5.2 Transfer rules

- **Only newly mobilised or newly created activity is a flow.** Material that comes out of the ground or the crust, or activity created by fission or activation, enters the accounting exactly once, at the stage where it first appears.
- **Transfers within a tier are not flows.** For example, uranium moving from mill product to enriched fuel and depleted-uranium stock, or fuel moving from core to spent-fuel pool, stays in Sealed and is not counted again.
- **Transfers between tiers** happen only through stated stage rules or events (§9). The activity is subtracted from the source tier's stock and added to the destination's in the same year, so nothing is double counted.
- **Chronic radon from Impounded residues — no double count.** In an impounded residue a fraction $\varepsilon$ (the effective exhalation fraction) of the Rn-222 produced escapes. The decay engine handles this as a **branch to another tier**:
  - Ra-226 decaying in Impounded feeds $(1-\varepsilon)$ of its Rn-222 and progeny decays to the impounded `Ra226+` group;
  - the other $\varepsilon$ becomes a Liberated `Rn222+` flow;
  - the Pb-210 grown in from the escaped share is in Liberated, not Impounded.

  So the impounded group multiplier is $1+5(1-\varepsilon)$ rather than 6, and each Rn-222 decay is counted in exactly one tier. $\varepsilon$ is set per residue type in Tasks 1.3 and 1.5 (provisional default 0.2, bounds 0.05–0.35). The same branching applies to Rn-220 in thorium-bearing residues, with its own $\varepsilon$.
- **Seepage** from impoundments is a Liberated flow paired with an equal subtraction from Impounded.
- Once liberated, material **stays in the Liberated stock and decays there**. Dispersal reduces concentration, not activity.

### 5.3 Moved earth vs processed residue (**PROPOSED, PD1**)

Mining moves enormous masses of rock. To keep the accounting meaningful:

- **Counted in tiers:** every residue **generated by processing** (tailings, slag, ash, scale, sludge, red mud, refuse from coal washing, drill cuttings, mine water) regardless of its concentration, and all products.
- **Recorded as a memo series, outside the tier totals:** overburden and waste rock moved only to *reach* a deposit, *unless* the activity concentration of **any single radionuclide in the uranium or thorium decay chains exceeds 1 Bq·g⁻¹, or K-40 exceeds 10 Bq·g⁻¹** (the NORM scope thresholds in IAEA GSR Part 3). Above-threshold waste rock is counted in Impounded.
  - The test is **per nuclide, on its own activity**, not on the PD4 group-summed activity. This matters for material out of equilibrium (e.g. scale high in Ra-226 with no U-238).
- The memo series ("earth moved", in t and Bq) is kept, so a "total earth displacement" view can be added later.
- *Why:* moving ordinary rock from 10 m down to a spoil heap doesn't change its radioactivity or containment in any meaningful way; processing (concentration, chemical mobilisation, breaking decay chains) does.

### 5.4 Created activity and the in-core inventory

- **When created activity enters Sealed:** fission and activation products enter Sealed **as they are created in an operating reactor**. Each operating reactor carries a standing **in-core inventory**, modelled as an equilibrium core inventory per GW(e) by reactor type and burnup (Task 1.2). It enters Sealed at first criticality and leaves at final shutdown.
- **Discharge of spent fuel** moves fuel from the in-core sub-tier to the spent-fuel sub-tier. That is a transfer within Sealed (§5.2), not a flow; its subsequent decay is handled by the decay engine.
- **Sub-tiers of Sealed shown on the page:** "in core" and "spent fuel & waste". The in-core inventory is dominated by short-lived fission products that are continuously regenerated, so it is shown as its own band and never mistaken for accumulating waste.
- **Accidents draw on the in-core inventory** (§9): the released fraction of each group moves from Sealed (in core) to Liberated. The unreleased remainder of a destroyed core (e.g. the Chernobyl shelter, the Fukushima Daiichi debris) stays in Sealed as "damaged core", decaying normally.

---

## 6. System boundary and stage map (D5)

### 6.1 Two accounting views (**PROPOSED, PD2**)

A single stacked total cannot be both "what each industry did" and "what each kind of electricity costs", because some flows sit in both places (e.g. coking coal for wind-tower steel is part of the coal industry *and* of wind's supply chain). Two views are therefore defined; **totals are only stacked within one view**.

| View | Question it answers | Streams | Used for |
|---|---|---|---|
| **Industry view** (default for absolute charts) | What did each industry bring up, create or release? | ① civil fuel cycle; ② all coal mined and burned; ③ all oil and gas produced; ④ materials for wind and solar **excluding** contributions already inside ② or ③ (embedded coal, gas, oil); ⑤ other energy | Absolute flow and stock charts |
| **Electricity lifecycle view** | What does each kind of electricity carry with it per TWh? | Coal power, gas power, oil power, nuclear, wind, solar, geothermal, biomass, hydro — each with its full Tier 1 supply chain, **including** embedded coal and O&G | Per-TWh charts (§8); the UNSCEAR check (§11) |

In the industry view, streams ② and ③ cover the **whole industry** (as originally asked: "mining and burning coal"; "oil and gas wells"), not only fuel for power.

*If PD2 is approved,* the stage list in `PLAN.md` Task 2.4 (which names "Fe + coking coal" and "metallurgical Si via coal/coke" inside ④) will be amended to say that those embedded-fuel contributions sit in ④ **in the lifecycle view only**.

### 6.2 Construction materials — shared commodity footprint table

Every generating technology's plant materials (steel, concrete/cement, copper, aluminium, glass, silicon, silver, rare earths, tellurium, indium, etc.) are accounted for through **one shared table**, `data/reference/commodity_factors.csv`. It gives, per tonne of refined commodity, the activity by group and tier of:

- (i) **own residues**: mining and processing waste of that commodity (e.g. REE tailings, red mud, copper tailings, smelter off-gas);
- (ii) **embedded fuel**: residues from the coal, oil and gas used to make it (coking coal, coal-fired smelting power, carbothermic silicon reduction).

The industry view uses (i) only (since (ii) is already in ② and ③); the lifecycle view uses (i) + (ii). Material intensity per MW comes from Task 1.9.

The same table serves **every** stream's construction materials, which satisfies D5 symmetrically: nuclear, coal and gas plants are charged for their steel and concrete exactly as wind and solar are.

### 6.3 Stage map and tier assignment

| Stream | Stage | Sealed | Impounded (↳ Re-isolated) | Dispersed | Liberated |
|---|---|---|---|---|---|
| ① | U mining (open pit, underground) | — | mineralised waste rock > threshold (↳ paste backfill) | — | mine radon, mine water |
| ① | U mining (in-situ leach) | — | evaporation-pond residue (↳ deep-well injected ISL waste) | — | radon, wellfield excursions |
| ① | Milling | U product (mobilised U enters here once) | tailings | tailings used as fill or building material (e.g. Grand Junction, Colorado) | tailings radon (§5.2 branch), dust, seepage |
| ① | Conversion, enrichment, fabrication | product, depleted U (transfers within Sealed) | process residues | — | stack and liquid discharges |
| ① | Reactor operation | in-core inventory (created activity, §5.4); operational LLW/ILW | — | — | airborne and liquid effluents |
| ① | Spent fuel | spent fuel (transfer from in-core) | — | — | — |
| ① | Reprocessing | HLW, ILW (transfers within Sealed) | — | — | discharges to air and sea |
| ① | Waste disposal at sea (civil share, 1946–1993) | — | — | — | packaged LLW dumped at sea (transfer from Sealed) |
| ① | Plant construction & decommissioning | decommissioning waste | commodity own-residues | — | commodity off-gas |
| ① | Civil accidents | damaged core (remainder) | — | — | event releases (§9) |
| ② | Coal mining | — | washery refuse; above-threshold waste | — | mine radon, mine water (radium) |
| ② | Combustion — power | — | fly ash, bottom ash, FGD residue landfilled or ponded (↳ ash backfilled into mines) | ash and FGD gypsum used in products or fill | stack fly ash and volatiles (Pb-210, Po-210), ash-pond radon (§5.2 branch) |
| ② | Combustion — non-power (industrial, residential, coke ovens) | — | ash and coke-oven residues landfilled | domestic ash spread on gardens and land | stack and chimney emissions; coke-oven gas |
| ② | Plant construction | — | commodity own-residues | — | commodity off-gas |
| ③ | Drilling | — | drill cuttings | — | — |
| ③ | Production | — | scale, sludge at disposal sites (↳ produced water to disposal wells or reinjected for waterflood/EOR) | brine spread on roads; land-farmed sludge | surface-discharged produced water; spills |
| ③ | Oil sands mining and upgrading | — | tailings ponds; coke stockpiles | — | tailings-pond emissions |
| ③ | Gas processing, refining & transport | — | Pb-210/Po-210 scale and sludge from processing plants, refineries, pipelines and storage | — | radon in vented and delivered gas |
| ③ | Well abandonment & equipment scrapping | — | NORM-scaled tubulars at licensed disposal | scaled scrap melted into steel or reused (e.g. as fencing) | descaling dust and discharges |
| ③ | Plant & well construction | — | commodity own-residues | — | commodity off-gas |
| ④ | Commodity supply (REE, Cu, Al, Fe, Si, Ag, Te, In, glass, concrete…) | — | own-residues (tailings, red mud, slag) | residues used in products | off-gas, dust, seepage, discharges |
| ④ | End of life & recycling | — | landfilled panels and blades (no new mobilisation; expected negligible, §10.3) | — | recycling-smelter off-gas (expected negligible) |
| ⑤ | Geothermal | — | scale and sludge (↳ reinjected brine) | — | non-condensable gas radon |
| ⑤ | Biomass / peat | — | ash landfilled | ash spread on soil | stack emissions incl. re-released Cs-137 |
| ⑤ | Hydro | — | — | — | negligible (§10) |

Task 1.2–1.6 may add stages; any addition must be recorded here before data is built for it.

---

## 7. Radioactive power (D1)

For each group $k$, the mean energy **emitted** per head decay is

$$\bar{E}_k=\sum_{i\in k} b_i\left(E_{\alpha,i}+E_{\mathrm{recoil},i}+\bar{E}_{\beta,i}+E_{\gamma X,i}+E_{e,i}\right)$$

where $b_i$ is member $i$'s branching-weighted decays per head decay, $\bar{E}_{\beta}$ is the mean β energy (the antineutrino share is **excluded**, because it escapes the planet without depositing heat), $E_{\gamma X}$ covers γ and X-rays, and $E_e$ conversion and Auger electrons. The radioactive power of an activity $A_k$ (head activity) is then

$$P_k=A_k\,\bar{E}_k$$

with $\bar{E}_k$ in joules. The calculation is reproduced by hand for H-3, `Cs137+` and Po-210 in Task 3.3.

---

## 8. Normalisation (D8)

- Per-TWh values are calculated **only in the lifecycle view** (§6.1), and **only for flows**. Stocks are not normalised per TWh, because a stock built up over decades has no single year's generation to divide by. The page shows stocks in absolute terms only.
- **Fuel-cycle and operating flows** (mining, combustion, effluents, creation of spent fuel) that occur at the time of generation are divided by the same year's generation from that technology $t$:

$$\text{intensity}_t(y)=\frac{F_t(y)}{E_t(y)}\quad[\mathrm{Bq\,TWh^{-1}}]$$

- **Chronic flows from earlier residues — committed and attributed back (PROPOSED, PD5):** some flows in year $y$ come from residues created decades earlier, such as radon from tailings or ash ponds. If they were divided by year $y$'s generation, a retired fleet would read `n/a` while its legacy radon continued. Instead, for the per-TWh view, each residue created in year $y'$ is charged with the chronic flow it will emit over a fixed horizon $H$ (computed by the decay engine), and that is divided by the generation $E_t(y')$ that created it:

$$\text{intensity}_{\mathrm{chronic},t}(y')=\frac{1}{E_t(y')}\int_{y'}^{y'+H}F_{\mathrm{chronic}}(\tau\,|\,\text{residue of }y')\,d\tau$$

  The default horizon is $H=100$ a, with 500 a and 10 000 a kept in the data. The absolute charts are unaffected: they show the chronic flows in the year they actually occur.
- **Construction-phase flows — levelised (PROPOSED, PD3):** releases from building capacity in year $y$ are divided by the **expected lifetime generation** of that capacity, not by year $y$'s generation:

$$\text{intensity}_{\mathrm{constr}}(y)=\frac{F_{\mathrm{constr}}(y)}{C(y)\,\mathrm{CF}\,L\times 8.766\ \mathrm{TWh\,GW^{-1}a^{-1}}}$$

where $C(y)$ is capacity added (GW), $\mathrm{CF}$ the expected capacity factor and $L$ the expected lifetime (a); 1 GW × 8766 h = 8.766 TWh per GW-year. CF and $L$ are planning-lifetime values by technology and vintage, which ignore degradation and early retirement; that approximation is stated on the page. *Why:* dividing up-front construction releases by the current year's output penalises any fast-growing fleet (wind and solar now, nuclear in the 1970s–80s) and flatters any shrinking one. A simple "annual ratio" variant is kept in the data as a secondary series:

$$\text{intensity}_{\mathrm{constr,annual}}(y)=\frac{F_{\mathrm{constr}}(y)}{E_t(y)}$$
- Years with zero generation are marked `n/a`, never zero.
- **Electricity share of coal and O&G (lifecycle view):** the share of coal (by energy) and of gas and oil going to power generation each year, from IEA/EI balances, allocates mining and production stages to the power technologies.

---

## 9. Events and accidents (D9, D15, D16)

### 9.1 Inclusion threshold

An event is included if its central estimate meets **either**:
- ≥ 1 TBq moved into the Liberated or Dispersed tier; **or**
- ≥ 10⁵ t of NORM-bearing material released from impoundment.

Each event records: date, location, stream, source and destination tiers, activity by group (low/central/high) and ≥ 1 source. Events appear as markers on the timeline, and their activity transfers are included in the tier stocks.

**Accidents are shown by default (D15).** The "exclude accidents" toggle does not just hide markers: it switches to a second, fully recomputed run in which every accident transfer is set to zero. The activity that would have been released stays in its source tier (e.g. in the in-core inventory, §5.4) and decays there. Both runs are precomputed in the export (Task 3.7). Non-accident events (e.g. ash-pond failures) are always included.

### 9.2 Civil/military rule (D16)

- **Uranium production — rule order for each country-year $(c,y)$:**
  1. **Documented end use first.** If a source documents the civil share of country $c$'s production in year $y$ (e.g. sales contracts to civil utilities, weapons-programme procurement), that share is used, in any year, including before 1965 (e.g. fuel for the first civil reactors, 1956–64).
  2. **Otherwise, before 1965:** $\phi_{\mathrm{civil}}(c,y)=0$ (D16).
  3. **Otherwise, from 1965:** the global default civil share,

$$\phi_{\mathrm{civil}}(c,y)=\min\left(1,\ \frac{R_{\mathrm{civil}}(y)-U_{\mathrm{doc,civil}}(y)}{U_{\mathrm{prod}}(y)-U_{\mathrm{doc}}(y)}\right)$$

  where $R_{\mathrm{civil}}$ is world civil reactor requirements, $U_{\mathrm{prod}}$ world production, and $U_{\mathrm{doc}}$ and $U_{\mathrm{doc,civil}}$ the production (and its civil part) already allocated by rule 1, so documented country-years are not counted twice.

  Each row records which rule applied (`allocation_rule`).
- **Dual-use reprocessing sites** (e.g. Sellafield, Marcoule, and Mayak's RT-1, which reprocessed civil VVER fuel from the late 1970s): discharges are split by the civil fraction of documented throughput. Where throughput is undocumented, the site-year is excluded and flagged.
- **Excluded military events:** Windscale 1957, Kyshtym 1957, SL-1 1961, Hanford releases, and all weapons testing (which appears as a baseline only).
- **Included civil events (indicative):** Chernobyl 1986, Fukushima Daiichi 2011, Three Mile Island 1979, Church Rock 1979; coal ash and slurry failures (e.g. TVA Kingston 2008, Dan River 2014, Martin County 2000); large produced-water spills; tailings failures in commodity chains attributable to ④ (e.g. Mount Polley 2014, copper; Brumadinho 2019, iron ore), each attributed by the allocation rules in §10.

---

## 10. Allocation (D6) and negligibility

### 10.1 Split points with several products

At every split point that yields several products (e.g. Bayan Obo: iron, REE, niobium; Olympic Dam: copper, uranium, gold, silver; oil and gas wells: oil, gas, NGLs), residues are allocated:

- **Default — economic value:** in proportion to each product's share of the output's market value in that year, using unit-value series (USGS DS140 unit values where available; otherwise price series with a cited source).
- **Bound A — all to main product:** the full residue goes to the product that defines the mine (iron at Bayan Obo, copper at Olympic Dam).
- **Bound B — all to the radioactivity-bearing product:** the full residue goes to REE at Bayan Obo, uranium at Olympic Dam.

The page toggle switches among default, A and B; the uncertainty band shows only the default's own data uncertainty.

### 10.2 Attribution to wind and solar

- The share of a commodity attributed to ④ in year $y$ is

$$\sigma_{c}(y)=\frac{\sum_{t} C_{t}(y)\,I_{t,c}(y)}{Q_{c}(y)}$$

  where $C_t(y)$ is capacity added (incl. repowering and replacement) of technology $t$, $I_{t,c}$ its intensity of commodity $c$ (t·GW⁻¹), and $Q_c$ world production of $c$. The same formula, with each technology's own capacity additions, gives the construction-materials share for streams ①–③ and ⑤ (§6.2).
- Within one commodity, the split between end uses is by **mass**, because value per tonne is the same.
- REE: attribution follows NdFeB (and Dy/Tb) demand for wind generators; solar's REE intensity is taken as reported (expected to be near zero), pending Task 1.1's answer to the "why solar" question.

### 10.3 Negligibility rule

A stage may be marked **negligible** (shown, not modelled in detail) if its central estimate is < 0.1% of its stream's total in both Bq and W in every decade, with the estimate and source recorded. Hydro is expected to qualify (its only radiological link is construction materials, which are counted via §6.2).

---

## 11. Uncertainty and data basis (D7, D18)

### 11.1 Bounds

Every factor and every activity datum carries low/central/high. **Central is read as the median; low and high as approximately the 5th and 95th percentiles.** Bounds may be asymmetric, and the upper and lower sides are always propagated **separately**.

- **Products** (activity × factor × fraction): each side is combined in log space by quadrature,

$$\ln\frac{x_{\mathrm{high}}}{x_{\mathrm{c}}}=\sqrt{\sum_i\ln^2\frac{x_{i,\mathrm{high}}}{x_{i,\mathrm{c}}}},\qquad \ln\frac{x_{\mathrm{c}}}{x_{\mathrm{low}}}=\sqrt{\sum_i\ln^2\frac{x_{i,\mathrm{c}}}{x_{i,\mathrm{low}}}}$$

- **Zero or "not detected" lower bounds:** log space fails at zero. A factor whose low bound is 0 or below detection is given a floor of $10^{-3}\times$ its central value for the log calculation, and the result's low bound is then set to 0 if any such factor dominates it. Factors whose *central* value is "not detected" are set to half the detection limit, with low = 0, and flagged.
- **Sums** of independent terms: the upper deviations $(x_{i,\mathrm{high}}-x_{i,\mathrm{c}})$ are combined by quadrature, and the lower deviations likewise, separately. Terms that share a factor (e.g. one emission factor applied to several countries) are treated as fully correlated and their deviations summed linearly.
  - This is an approximation: a sum of medians is not the median of the sum (for right-skewed terms it underestimates it). The approximation is stated on the page and is the main reason Monte Carlo stays on the table.
- **Stocks:** a stream's flows in different years usually share the same factors, so they are treated as **fully correlated across years** when the bounds are carried through the decay engine. This widens the stock bands, and is stated.
- The invariant low ≤ central ≤ high is checked everywhere (Task 3.6).
- Monte Carlo is considered only if the bounds prove too crude (D18).

### 11.2 Basis flags

Each row carries `basis` ∈ {`measured`, `compiled` (an authoritative compilation of measurements, e.g. UNSCEAR/RADD), `modelled` (activity × factor), `interpolated`, `extrapolated`}. The page draws measured and compiled values solid and the rest hatched or lighter.

### 11.3 Source hierarchy

1. Regulator-reported measurements (NRC, CNSC, RADD, OSPAR, DIRATA, national NORM surveys).
2. UNSCEAR and IAEA compilations.
3. Peer-reviewed literature.
4. Government and agency reports (USGS, EIA, JRC, IEA).
5. Industry and grey literature (used only where nothing better exists; flagged).

**Excluded entirely:** Grokipedia. Wikipedia only as a lead to primary sources, never cited. Inaccessible sources are listed with their URL for Steve to try himself.

---

## 12. Decay and ingrowth model (D3)

### 12.1 Formulation

The engine tracks **atoms** of each head $k$ per tier, $N_{k,j}$, with decay constants $\lambda_k=\ln 2/T_{1/2,k}$ (a⁻¹). Within a chain,

$$\frac{dN_k}{dt}=-\lambda_k N_k+\sum_{p\to k}\beta_{p\to k}\lambda_p N_p+q_k(t)$$

where $\beta_{p\to k}$ is the branching from parent head $p$ and $q_k$ the source in atoms per year. Activity is $A_k=\lambda_k N_k$; reported group activity is $m_k A_k$ (§4). A flow given as activity is converted to atoms as $q_k=F_k/\lambda_k$, with $F_k$ in Bq·a⁻¹ converted to decays·a⁻¹.

Branches may cross tiers. The §5.2 radon rule is implemented as a branch of the Ra-226 → Pb-210 path from Impounded into Liberated, with weight $\varepsilon$.

### 12.2 Annual step

Each year is stepped exactly by the matrix exponential of the chain's decay matrix, with the year's flow treated as a **uniform source over the year** (the augmented-matrix method). For a single nuclide with no parent this reduces to

$$S(y)=S(y-1)\,e^{-\lambda}+F(y)\,\frac{1-e^{-\lambda}}{\lambda}$$

with $\lambda$ in a⁻¹. Short-lived releases therefore show in the flow chart but leave almost nothing in the stock: for I-131, $(1-e^{-\lambda})/\lambda\approx0.032$, and the short-lived noble gases (Xe-133, Kr-88 and others) leave even less. The longer-lived releases **do** accumulate: Kr-85 (10.8 a), H-3 (12.3 a) and C-14 (5730 a). Events are applied as instantaneous transfers at mid-year.

### 12.3 Disequilibrium at entry

Each stage records the **activity of each head** entering a tier, so broken chains are explicit. For example:
- Mill tailings carry `Th230`, `Ra226+`, `Pb210+`, `Po210` with only ~5–10% of the ore's uranium heads.
- Oil-field scale carries `Ra226+` and `Ra228+` with essentially no Th-232 or U-238; `Th228+` then grows in from Ra-228 over a few years and dies away with it.
- Fly ash fines may carry `Pb210+` and `Po210` enriched relative to `Ra226+`.

### 12.4 Required tests (Task 3.2)

Single-nuclide decay; a two-member analytic Bateman case; secular equilibrium of the U-238 chain; Ra-226 grow-in from separated Th-230; and conservation of atoms across a ten-member chain.

---

## 13. Baselines (D11)

All baselines are given in both Bq and W wherever meaningful, with the derivation shown and sourced in Task 1.7.

| Baseline | Quantity | Note |
|---|---|---|
| Earth's radiogenic heat | W (~20 TW) | Geoneutrino estimates; W only (a Bq equivalent would be a derived quantity) |
| K-40 in the oceans | Bq, W | Seawater K concentration × ocean volume × K-40 specific activity |
| Natural radon exhalation from land | Bq·a⁻¹ | Global mean exhalation flux × land area |
| Cosmogenic H-3 and C-14 | Bq·a⁻¹ production; Bq standing inventory | Direct comparator for nuclear's H-3 and C-14 releases |
| Top metre of global soil (candidate) | Bq | Mean soil activity × mass of the top metre of land soil; kept only if a defensible soil-activity mean is sourced |
| Atmospheric weapons-test fallout | Bq by group (I-131, `Cs137+`, `Sr90+`, C-14, H-3) | Baseline only (D9) |

---

## 14. Internal dose check (D1; Task 3.5)

Collective dose is calculated **for the 2010 reference year only**, in the lifecycle view, using UNSCEAR 2016 Annex A's own release-to-dose methodology, to check that our release estimates are of the right size. Tolerance: each stream within a factor of 3 of UNSCEAR's value, or the gap explained here. **No dose quantity is exported to the page data**; an automated check enforces this.

---

## 15. Inputs deferred to Phase 1

| Item | Task |
|---|---|
| Per-tHM spent-fuel inventory vs burnup and cooling time; choice of the reduced nuclide set | 1.2 |
| Civil fraction of Sellafield, Marcoule and RT-1 throughput by year | 1.2 |
| Reactor-type normalised effluent factors by period (UNSCEAR) | 1.1, 1.2 |
| U and Th content of coal by basin, and ash partitioning and enrichment factors | 1.3 |
| Global fly-ash production and utilisation by year | 1.3 |
| Produced-water volumes and Ra-226/Ra-228 concentrations by play; disposal-route shares | 1.4 |
| Material intensity by technology and year; commodity footprint factors (§6.2) | 1.5, 1.9 |
| Bayan Obo product split and unit values; Olympic Dam product split | 1.5, 1.9 |
| Geothermal non-condensable gas radon factors; biomass-ash Cs-137 | 1.6 |
| Electricity shares of coal, gas and oil by year | 1.9 |
| Emanation coefficients to bound the §5.2 double count | 1.3, 1.5 |

---

## 16. Proposed decisions needing sign-off

| ID | Section | Proposal |
|---|---|---|
| **PD1** | §5.3 | Count all processing residues; record overburden and waste rock as a memo series unless > 1 Bq·g⁻¹ (U/Th heads) or > 10 Bq·g⁻¹ (K-40). |
| **PD2** | §6.1 | Two accounting views: **industry** (default for absolute charts; ② and ③ are whole industries) and **electricity lifecycle** (per-TWh and UNSCEAR check); totals stacked only within a view. |
| **PD3** | §8 | Levelise construction-phase releases over expected lifetime generation for per-TWh charts; keep the simple annual ratio as a secondary series. |
| **PD4** | §3.2 | Count all decays in each group (e.g. ×14 for U-238 in equilibrium), keeping head-only activity in the data as an alternative. |
| **PD5** | §8 | For per-TWh charts, charge chronic flows from residues (e.g. tailings and ash-pond radon) to the generation that created the residue, integrated over a 100-year horizon (500 a and 10 000 a kept in the data). Stocks are not normalised per TWh. |
| **PD6** | §2.3 | Split oil and gas into three sub-streams: conventional, unconventional (fractured shale/tight + coalbed methane) and oil sands / extra-heavy oil. |

---

## Change log

| Date | Change |
|---|---|
| 2026-10-20 | First draft (Task 0.1). |
| 2026-10-20 | Revised after independent verification. Fixed the Rn220+ multiplier (5); rewrote the civil/military rule as a per-country-year rule order; added in-core inventory (§5.4) and the full accident-toggle mechanics. Also: per-nuclide NORM threshold; difference from the regulatory "+" convention; extra stages (non-power coal, sea disposal, tailings as fill, refining and pipeline scale, scrapping, oil sands, end of life); no-double-count rules; radon branching via $\varepsilon$; zero-bound and asymmetric uncertainty handling; Kr-85/H-3/C-14 persistence; per-TWh basic formula; country codes; rationale table; added PD5 and PD6. |
