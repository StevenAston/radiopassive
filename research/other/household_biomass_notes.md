# Task 1.6 addendum: household (domestic) biomass heating, factors for stream 5

Scope per D37: household and small-scale combustion of wood, pellets and briquettes, and charcoal production and use. Factors only; activity series are Task 1.9 (FAOSTAT wood fuel and charcoal, UNSD household use: S0846, S0847, S0848). New sources are S0530 to S0564 in `sources_task16b.csv` (35 rows, validated against `schema/sources.json`, 0 problems). Availability rows: `household_biomass_availability.csv` (12 factor lines x 9 decade rows = 108 rows; decades pre1950 to 2020s). The Task 1.6 files are untouched and vocab is not edited.

## 1. Method and limits

- Searched the web, then read papers and reports through a summarising fetch tool. Numbers marked "read" were taken from that summary. Stoulos et al. (S0531) was read from the PDF text directly and its key numbers were checked there. Spot-check the others before they enter the factor registry.
- "Derived" means my arithmetic on sourced values (script kept in the scratchpad). "Modelled" means an estimate with a stated method. Nothing is invented; placeholders are labelled as such.
- Dose figures appear in several sources (S0515, S0521 and others) and are deliberately not recorded (D1).
- Crossref was used to confirm DOIs, volumes and pages.
- Wikipedia was not used. Grokipedia was not used.

## 2. Factor ranges

### 2.1 Fuel (Bq/kg dry unless stated)

| Quantity | Value | Source |
|---|---|---|
| Cs-137 fuelwood, Sweden (Gavleborg, 10 houses, 1997; deposition 5-110 kBq/m2) | 3-280 (SSI 1998:15 table: 3-300; Stigsjo 42) | S0515, S0536 |
| Cs-137 pine shoots Sweden 1986-91 / 1995 | 200-900 / up to 2,000 | S0536 |
| Cs-137 wood chips Sweden 1990-91 (all Sweden) | 0.4-4 | S0536 |
| Cs-137 logging residue Sweden 1998 | 180-700 | S0536 |
| Cs-137 fuelwood Ukraine (Polissya, abstract, year not given) | <2 to 690; about 98% under the 600 limit | S0539 |
| Cs-137 wood Polissya pine plot (derived from Tag x deposition) | 1,240 (1991), 2,300 (2002), 730 (2020) | S0543 |
| Cs-137 firewood Belarus | no survey found; hygienic limit 740 (oak wood standard also 1,480) | S0540, S0541 |
| Cs-137 pellets Lithuania imports 2010 | Ukraine <=156, Belarus 30, Poland 4, Kaliningrad 1 | S0514 |
| Cs-137 Belarus-origin pellets, Belgium | up to 700 (secondary) | S0538 |
| Cs-137 firewood Belgium (AFCN, via a French parliamentary answer, not fetched) | 150-300 | see section 8 |
| Cs-137 wood fuel Austria 2020-22 (n=69) | 0.33-8.4, mean 2.1 (pellets mean 2.15) | S0530 |
| Cs-137 wood Poland (pine, birch) | 0.15-3.7 | S0535 |
| Cs-137 wood Greece | oak <0.05-1.3, beech/plane 8.2-11 | S0531 |
| Cs-137 wood/ash North America (weapons fallout) | ash 2.9-780, New England mean about 444; wood about 100 times lower by the 1% ash assumption (derived, about 4) | S0520 |
| Cs-137 per unit deposition, wood Tag (m2/kg) | Chernobyl pine plot 2.3e-3 (1991), 5.5e-3 (about 2002), 2.7e-3 (2020); Fukushima 1e-4 to 1e-3 | S0543, S0548 |
| Stemwood share of tree Cs-137 / mass (Finnish spruce, 1998) | 4-7% / 19-36% | S0546 |
| K-40 wood | 6-164 (building timber, Turkey); 12-37 (Greece) | S0559, S0531 |
| Ra-226 wood | 1.6-13; about 2.0 in one spruce | S0559, S0558 |
| Th-232 series wood | 0.8-9.5 (no separate Ra-228 or Th-228) | S0559 |
| Pb-210 wood (trunk) / bark | 1.0-3.3 / 1.9-2.8; 1.7 in spruce rings | S0556, S0558 |
| Po-210 wood (trunk) / bark | 1.0-5.5 / 2.6-2.9 | S0556 |

Regions with no wood-fuel data found: Russia (only tree-ring behaviour, S0545), global South (only a student report that I reject, S0561), most of Asia and Africa. Eastern Europe has fuel limits and one abstract (S0539), not a survey.

### 2.2 Ash and ash concentration factors (ACF = ash concentration / dry fuel concentration)

| Quantity | Value | Source |
|---|---|---|
| Ash yield, household wood | about 1% assumed (measured about 1.2%, K-40 based); stemwood about 0.5%; bark 3-5%; GROT 2% | S0515, S0520, S0536 |
| Ash yield, charcoal burned | 3% (30 g/kg) | S0564 |
| ACF Cs-137, Sweden houses | about 91 (wood/ash 1.1%, scatter +/-113%); K-40 gives 83 | S0515 |
| ACF, Greece (K-40 based) | fireplaces 77-209, wood stoves 107-118, pellet stove 85 | S0531 |
| ACF, Austria (ratio of group means) | chips 58, pellets 181, briquettes 144, single log 348 | S0530 |
| ACF, Lithuania / Zhytomyr / Netherlands-Belgium | 95-370 / 50-100 / 70 to over 200 | S0514, S0516, S0538 |
| ACF, charcoal burning (Japan) | 28 | S0564 |
| Ash Cs-137, houses Sweden 1997 | ash 2-21 kBq/kg; chimney soot 2-23 kBq/kg | S0515 |
| Ash Cs-137, Zhytomyr 2017 / Austria 2020-22 / Greece 2013 / US 1990-92 | 170-32,900 / 11.8-867 / 25-499 / 2.9-780 Bq/kg | S0516, S0530, S0531, S0520 |
| Ash K-40 | 1,036-5,708 (typical 2,960; converted from pCi/kg) ; 1,592-7,060 | S0520, S0531 |
| Fly ash vs bottom ash (large plants only) | Hasselby 6-9 vs 0.4-0.5 kBq/kg (12-20x); Belgium 100-500 vs 5-50 Bq/kg; fly ash 20-80% of ash mass | S0536, S0538 |

Reading: with $\mathrm{ACF}=\rho_{\mathrm{ret}}/y_{\mathrm{ash}}$, an ash yield of 0.5 to 1% and retention of 0.7 to 1 give 70 to 200, which covers most observations. The top of the range (370) needs a yield below 0.3% at full retention, so it signals clean stemwood or heterogeneity, not retention above 1. The ACF cannot separate retention from ash yield, so it is a cross-check on the flue-gas fraction, not an input.

### 2.3 Partitioning to flue gas (the unmeasured 0.10)

| Evidence | Implied flue-gas fraction $f_v$ | Type | Source |
|---|---|---|---|
| Sweden houses, wood/ash Cs ratio 1.1% vs K-40 ratio 1.2% | about 0 (Cs retained about 1.09 times K; scatter huge) | derived from unpaired means | S0515 |
| Japan charcoal burning: ash 30 g/kg, ACF 28 vs full-retention 33 | 0.16 (reported about 90% retained, so 0.10) | derived; demonstration | S0564 |
| Greek domestic fireplaces, stoves, pellet stove | 0.41-0.79 | indirect mass balance, unpaired samples, K-40 as ash proxy | S0531 |
| Lab, cedar bark, 10 g | 0.02 at 300 C; 0.15-0.25 at 350-450 C; 0.30-0.35 above 500 C | measured, lab | S0551 |
| Lab, Chalk River vegetation at 800 C | litter 0.45, alder twigs 0.77, alder leaves 0.92, organic soil 0.024 | measured, lab | S0550 |
| Lab, straw/wood/peat, 160-1,000 C, "typical field fire" | 0.40-0.70 | measured, lab | S0549 |
| Fukushima forestry-waste incinerator with wet scrubber | no gaseous Cs detected; 95% recovered in solids | measured, engineered | S0551 |
| Open burning of CEZ litter and moss | 0.00075-0.0045 (green branches up to 0.24) | measured, open fire | S0552 |
| Large-plant condensate scenario | 0.10 or 0.003 assumed | assumption | S0536 |
| Swedish household report | 0.10, "a fairly free assumption" | assumption | S0515 |

The 0.10 in the Task 1.6 notes traces to S0536 via S0515. It is an assumption, not a measurement, and the only domestic-appliance estimate (S0531) is four to eight times higher. The lab results show strong temperature dependence, with a step between 300 and 500 C; household stoves run hotter than that in the bed. No stack measurement of any household stove or boiler was found. Proposed modelled $f_v$ for Cs-137: low 0.10, central 0.30, high 0.70 (central is the middle of the evidence, not a measurement).

Chimney soot: Swedish soot has the same concentration as ash (2-23 vs 2-21 kBq/kg, S0515) but its mass is unquantified. Treat soot with ash (swept and landfilled) until a mass is found.

### 2.4 Pb-210 and Po-210

No measurement of Pb-210 or Po-210 volatility in wood, charcoal or peat combustion was found. What exists:

- Open vegetation fires emit Po-210 preferentially: smoke Po-210/Pb-210 up to 12 and about 100 times the reference aerosol (S0554, S0555).
- Coal analogue: about 50% of Po-210 and 5% of Pb-210 not retained by electrofilters (S0557). Domestic stoves have no filters.
- Wood content is low (section 2.1), so activity per tonne is small, but the fuel tonnage is global.

Proposed placeholders (modelled, replace on any measurement): Po-210 $f_v$ 0.5 to 1.0; Pb-210 $f_v$ 0.05 to 0.5. Illustrative magnitude only, not for display: if the 1.4 Gt of the `wood_fuel_t` series (2020, basis `modelled` in `biomass.csv`, moisture basis unstated) were dry, fuel Po-210 would be 1.4-7.7 TBq/a and K-40 8-230 TBq/a (derived: $1.4\times10^{12}\ \mathrm{kg}\times$ range above).

### 2.5 Fate of household ash

- No survey of household ash handling was found for any country. The Swedish household report models scenarios (flower beds, lawn, vegetable and berry beds, burial, ash heap; S0515). US residential ash goes to landfill, home fertiliser or winter traction (S0520). Ukrainian household ash goes to gardens; about 9% would be low-level waste (S0516).
- Large plants (not households): Swedish ash above 10 kBq/kg must be landfilled, below may go to construction or forest (S0537). Dutch ash above 100 Bq/kg Cs-137 cannot be landfilled without a clearance decision (S0538).
- Chimney releases go to Liberated (`air_stack`).
- Proposed prior (modelled, uninformative): dispersed share 0.5 (range 0.2-0.8), impounded share the remainder. This is an assumption with no data behind it. Ash incinerated in municipal waste plants (which would re-volatilise Cs) is not handled.

### 2.6 Charcoal

- No radionuclide concentration in charcoal was found for any country, and none for Africa or Asia.
- Only partition evidence: Japanese charcoal combustion (ash 3%, ACF 28, about 84-90% of radiocaesium stays in the ash; S0564) and an indicator value of 280 Bq/kg that is a limit, not a measurement (S0560).
- Carbonisation: lab data say Cs retention in the residue falls as temperature rises (S0551: about 0.98 at 300 C, 0.75-0.85 at 350-450 C, 0.65-0.70 above 500 C). Kiln temperatures and yields are not sourced here; FAO Forestry Paper 41 (S0563) is the lead (not read beyond contents).
- Proposed: $C_{\mathrm{char}}=C_{\mathrm{wood}}\,r_c/y_c$, with $y_c$ the carbonisation mass yield and $r_c$ the Cs kept in char. Natural nuclides other than Pb-210 and Po-210 are assumed fully retained (inference), so they concentrate by $1/y_c$.

### 2.7 Time variation (Cs-137 in wood)

- Wood is not a decaying surface deposit. Stemwood activity peaks roughly 15 years after deposition and then falls mainly by decay (S0544); young stands plateau at about 25 years (S0544).
- One Polissya plot (S0543): Tag 2.3e-3 (1991), 5.5e-3 (about 2002), 2.7e-3 m2/kg (2020), with deposition 539.6 to 269.9 kBq/m2. Derived wood activity 1,240, 2,300 and 730 Bq/kg. Post-peak effective half-life of the activity about 11 years (derived: $18\ \mathrm{a}\,\ln2/\ln(2305/729)$); Tag alone halves in about 17.5 years. Single 1-ha plot, three felled trees: a bound, not a regional value.
- Russia: no 1986 ring peak, Cs-137 penetrates into core wood (S0545). Forest components decline with T1/2 of 20-30 years (Chernobyl Forum 2005, via S0542).
- Fukushima, 2011-2020 (different soils and climate): whole wood rose 2.1-6.4 times in six of nine plots; decreasing plots show 6.8-7.2 years (S0547). Models project a decline for conifer wood (S0548).
- Consequence: a "physical half-life only" default is wrong in both directions. It overstates wood activity at 10-25 years after deposition and understates it in the first decade.
- Pre-1986: no wood time series or direct wood measurement found. The US ash survey (S0520, sampled 1990-92, weapons-fallout dominated) is the only artificial-nuclide anchor. Weapons-fallout deposition peaked in 1963 (Task 1.7), so the Tag peak would fall around the mid-1970s (inference).
- Pre-1950: no Cs-137. Natural factors in section 2.1 are assumed constant (inference).

### 2.8 Validation context only (no dose recorded)

- UNSCEAR 2016 Annex B para 191 (S0001) deliberately excluded Cs-137 in biomass ash and gives no biomass release factors; UNSCEAR 1988 Annex A para 213 gives peat U-238 only (S0008). Domestic wood burning is not treated in any UNSCEAR or IAEA document I could reach; non-electric use is excluded by scope (research/unscear_notes.md).
- No global or national estimate of domestic biomass radionuclide releases was found.
- Air signals: Thessaloniki winter 2013 Cs-137 up to 12 mBq/m3 attributed to residential wood burning, 0.8-6.5 Bq per kg of wood burned (S0531); Cs-137/K-40 air ratio 0.15 for contaminated wood heating (S0532); Puy de Dome correlation with levoglucosan (S0553). These could validate the order of magnitude of a modelled stack release, regionally only.

## 3. Contradictions and flags

1. **Flue-gas fraction.** The Swedish house data give about zero loss relative to K-40 and the Greek data give 0.41-0.79, using the same K-40 method. Both are unpaired means. The central value cannot be fixed from data; bounds are wide.
2. **"10%" is an assumption passed down a chain** (S0536 scenario, S0515 "fairly free", Task 1.6 notes). It should not be labelled measured.
3. **Stoulos mBq/m3 vs uBq/m3.** AGRIS gives micro-becquerels; the PDF gives milli-becquerels (S0531, checked in the text). Use mBq/m3.
4. **Nigerian K-40** (S0561): abstract 3,120 vs results 2,258 Bq/kg, and 10-100 times the other wood values. Reject.
5. **Strzalek units** (S0535): the original paper is in Bq/Mg for wood, not Bq/kg; cite the correction.
6. **Lithuanian ash** 2,340 vs 7,201 Bq/kg (already flagged in the Task 1.6 notes).
7. **Open-fire vs stove releases**: 0.075-0.45% (S0552) against 40-70% (S0549) differ by two orders of magnitude; fuel moisture, particle size and temperature explain it. Do not transfer wildfire fractions to stoves.

## 4. Proposed modelling (activity proxy x factor)

For nuclide group $n$, fuel $k$ (fuelwood, pellets and briquettes, charcoal), country $c$, year $y$, route $r$:

$$A_{n,r}(c,y)=\sum_{k}M_{k}(c,y)\,C_{n,k}(c,y)\,\phi_{n,k,r}$$

- $M_k$: dry fuel mass (t/a). Wood: FAOSTAT item 1864 (m3, roundwood equivalent; S0846) x household share (UNSD, S0847, 1990 on) x dry density (S0848). Charcoal: FAOSTAT item 1630 (t; S0846) and UNSD household charcoal.
  - **Double-count guard:** item 1864 includes wood converted to charcoal (note N378 in Task 1.9). Charcoal feedstock = charcoal t / $y_c$ must be subtracted before burning the remainder as fuelwood.
  - Moisture basis of the 725 kg/m3 density (S0848) is unstated; factors here are Bq/kg dry.
- $C_{n,k}$:
  - Cs-137: $C=T_{ag}(t)\,D_0\,\mathrm{e}^{-\lambda t}$, with $D_0$ the deposition density from Task 1.7 baselines (weapons fallout and Chernobyl) and $T_{ag}(t)$ rising to a peak 10-16 years after deposition and then declining (section 2.7). Bounds 1e-4 to 5.5e-3 m2/kg; central is a geometric mean pending calibration against S0515, S0530, S0539 (modelled). Where deposition is unavailable, use regional measured ranges in section 2.1.
  - Natural nuclides: regional constants from section 2.1, time-invariant (modelled).
  - Charcoal: section 2.6.
- $\phi_{n,k,r}$: stack $=f_v$ (section 2.3, 2.4); ash $=1-f_v$ split into dispersed $s_d$ and impounded $1-s_d$ (section 2.5).
- Cross-check each year: predicted ash Cs-137 $=C_{\mathrm{fuel}}(1-f_v)/y_{\mathrm{ash}}$ against measured ash (section 2.2).
- Trade: pellet and firewood trade means country of use differs from origin (S0514, S0534); use national measured ranges for pellets where possible.
- Bands: widest where evidence is thinnest; $f_v$, $s_d$ and Pb/Po placeholders carry the largest uncertainty. No global total is proposed here.

## 5. Proposed stage and substream mapping (not applied; Steve or the orchestrator to decide)

**Does the current vocabulary cover household combustion?** Partly.

- Tier-wise, yes. `biomass_peat` allows impounded, dispersed and liberated, and the METHODS §6.3 row (ash landfilled, ash spread on soil, stack emissions) fits household burning. A route exists (`air_stack`, as used for coal chimney emissions) and residue types exist (`biomass_ash`, `peat_ash`).
- Not enough for the stated goal of matching coal. Coal separates `combustion_power` from `combustion_nonpower`, substreams `power` and `non_power`, and has `coal_domestic_ash`. Stream ⑤ has no end-use split, so household rows cannot be told apart from power and heating-plant rows, and the lifecycle view (D22) would attribute them to technology `biomass` by electricity share.

**Recommendation (Option A):**

| Item | Proposal |
|---|---|
| New stage in `other` | `biomass_domestic` (household and small-scale combustion of wood, pellets, briquettes, charcoal, domestic peat; kiln smoke) |
| Stage-tier matrix | impounded, dispersed, liberated (same as `biomass_peat`) |
| New substream in `other` | `biomass_domestic`, mirroring coal's `non_power`, so the pipeline can exclude it from electricity-share attribution |
| New residue type | `biomass_domestic_ash` (stream `other`), mirroring `coal_domestic_ash`; includes chimney soot |
| Routes | stove chimney `air_stack`; charcoal kiln `air_process_vent` |
| Groups used | `Cs137+`, `K40`, `Pb210+`, `Po210`, `Ra226+`, `Ra228+`, `Th228+` |
| `biomass_peat` stage | unchanged, restricted to power, heating-plant and industrial use |
| METHODS §6.3 | add row "⑤ Biomass / peat, household": ash landfilled (impounded), ash spread on soil (dispersed), chimney and kiln emissions (liberated) |

Alternatives: (B) stage only, with no new substream, if the pipeline can key lifecycle exclusion on stage; (C) no vocabulary change, with household rows distinguished only by `residue_type`, which cannot separate the Liberated rows and is not recommended. If charcoal must be separable on the page, a `charcoal` substream would be needed (optional; not recommended for v1). The availability CSV uses the existing code `biomass_peat` and names the proposed stage in the notes.

## 6. Open issues

1. **Accounting of fallout Cs-137.** Fuel Cs-137 is deposited fallout, already in the Liberated stock via events and tests. METHODS §5.2 says only newly mobilised activity is a flow. The §6.3 row for ⑤ lists "stack emissions incl. re-released Cs-137" as Liberated. Decide whether stack release is a flow or a transfer, and whether the ash is a Liberated to Impounded/Dispersed transfer. I have not resolved this.
2. **K-40, Pb-210 and Po-210 in biomass** are annual nutrient and deposition cycling. Decide whether they count as newly mobilised (as for peat) or are baseline.
3. **Charcoal feedstock double count** in FAOSTAT 1864 (section 4).
4. **Household vs non-household share before 1990.** UNSD household series start in 1990; FAOSTAT has no end-use split.
5. **Other domestic biomass** (crop residues, dung) is outside FAOSTAT wood fuel; scope to be decided.
6. **Domestic peat** (Ireland, Finland, Russia, Belarus) belongs with this stage if adopted; UNSD has household peat from 1990.
7. **Ash incinerated with municipal waste** and chimney soot mass are unhandled.
8. **Pre-1950 residues:** long-lived Ra-226/Th-232-bearing ash from 1800-1949 persists, but no fuel series exists before 1961. Apply the negligibility rule (METHODS §10.3) rather than build it.
9. **Calibration data** for the Tag central and for $f_v$ do not exist yet. A household-stove stack measurement would change the Cs-137 result more than any other missing item.

## 7. Not found

- Stack or flue-gas measurement of Cs-137, Pb-210 or Po-210 from household stoves, boilers or charcoal stoves.
- Radionuclides in charcoal (any region); kiln partitioning; wood-to-charcoal mass yield (S0563 lead).
- Household ash handling survey (any country).
- Ra-226, Ra-228, Th-228, Pb-210, Po-210 in wood ash.
- Belarus, Russia and global-South firewood or ash surveys; Chernobyl multi-site wood half-life; pre-1986 wood measurements.
- Any UNSCEAR or IAEA estimate for domestic wood, and any global estimate.

## 8. Inaccessible or partial sources (URLs for Steve)

- Pepin et al. 2023 review (S0513, paywalled; likely the best compilation of ash enrichment, emission factors and national rules): https://academic.oup.com/rpd/article/199/8-9/759/7205049 (DOI 10.1093/rpd/ncad077)
- NCASI TB 0639 (S0562, only the catalogue introduction read): https://ncasi.org/resource/technical-bulletin-no-0639-cesium-137-in-industrial-wood-ash-concentrations-fate-and-human-health-risks
- Finnish government household wood-burning survey (fetch failed; may hold ash-handling shares): https://valtioneuvosto.fi/sv/-/1410903/enkat-belyser-finlandarnas-vedeldningsvanor and https://yle.fi/a/7-1352074
- INIS record on Chernobyl wood (robots disallowed; content unknown): https://inis.iaea.org/records/va4mx-82129
- Cantaluppi et al. 2023 full text (S0533; URL too long for the fetch tool): see the `url` column of `sources_task16b.csv`
- Pradel thesis (27 ash results): https://thesis.unipd.it/handle/20.500.12608/42386
- IIASA record of a forests paper (Anubis access denied): https://pure.iiasa.ac.at/id/eprint/16325/1/forests-11-00270.pdf
- Stirling file (binary): https://www.stir.ac.uk/research/hub/file/1605283
- French parliamentary answer reporting the Belgian AFCN firewood range 150-300 Bq/kg and an IRSN 2017 study (PRP-HOM/SER/2017-00009), neither fetched: https://www.assemblee-nationale.fr/dyn/15/questions/QANR5L15QE24892.pdf
- Hus, Kosutic and Lulic, "Radioactive contamination of wood and its products" (Croatian beech, oak, fir wood and bark Cs-137 1.6-37.3 Bq/kg; year not stated, so not registered): https://www.bib.irb.hr/75580
- Fesenko slides citing IAEA (2009) pine-wood Tag against time after the accident (graph only): https://enep.ied.tsukuba.ac.jp/wp-content/uploads/sites/9/2016/06/4.-Prof.Fesenko.pdf
- Hedvall & Erlandsson (S0246, in the coal range, not read) may hold biomass-boiler Cs partitioning.
