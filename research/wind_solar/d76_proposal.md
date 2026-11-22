# D76 proposal: steel driver per tonne of hot metal; pig iron and crude steel 2024–25; Olympic Dam uranium 2024–25

Status: **draft for Steve, 2026-11-22. Nothing applied.** Staged files: `build/d76_staging/` (manifest `APPLY.md`), generator `research/wind_solar/build_d76_staging.py` (standard library, deterministic; it writes only `build/d76_staging/` and prints every number below). `docs/DECISIONS.md` is not edited; the draft row is in §8.

Labels: **[E]** read in the source; **[I]** author arithmetic; **[A]** assumption. All quantities are Bq (or Bq/a), t, Mt, t U.

---

## 0. Summary

| # | Change | Effect |
|---|---|---|
| 1 | `steel_bf_route_share` (a placeholder for 1970–2025 and $Q_{\mathrm{pig}}/Q_{\mathrm{steel}}$ for 1950–69) is replaced by **`steel_hot_metal_ratio`** $h(y)=$ world `prod_pig_iron` / `prod_steel`, in **every** year, from measured data. The 35 steel-family (ST) factor rows become **per tonne of hot metal**. | ST rows +9.7 % (2010), +5.9 % (2020), +3.2 % (2024) at central; the ④ stream total rises by 0.8 %, 0.6 % and 0.2 % |
| 2 | 47 production rows: world and 16 countries' pig iron and crude steel for 2025 (and GBR for 2024) from worldsteel, World Steel in Figures 2026; GBR pig iron 1995–2004 from the IISI Steel Statistical Yearbook 2005 (for B2). 4 new source rows (S0861–S0864). | $h(2025)$ is measured (0.6875). B2 now uses the UK's own hot metal |
| 3 | `u_production_od` 2024–25 changes from the estimate 2,830 t U to the BHP-reported 3,055 and 2,675 t U. | Nuclear F6 (AUS, carved out) −22 % in 2024 and +15 % in 2025; F8 and the wind/solar CU-OD rows are unchanged |

Validation (a scratch copy of the tree with the staged files overlaid, `wind_solar.py` with only the series name changed):
- `python -m pipeline.validate --root .` reports **no issues**.
- `wind_solar` and `nuclear` rebuild. The rebuilt ST and F6 totals equal the multiplicative estimates below to 4 significant figures.
- `test_nuclear.py` and `test_nuclear_od.py`: **358 passed, 4 xfailed**.
- `test_wind_solar.py` with the series renamed: **235 passed, 1 failed**. The failure is `test_placeholder_rows_carry_placeholder_notes`, expected because the new series is not a placeholder (§7).

---

## 1. Steel driver

### 1.1 Why

A blast furnace makes **pig iron (hot metal)**, not steel. The ironmaking terms (sinter and BF stack, BF dust and sludge, BF slag, iron-ore tailings) scale with hot metal. The integrated route is BF → BOF, or BF → open hearth before about 1990.

The old construct was steel × `steel_bf_route_share` × a factor "per t of BF-BOF crude steel". It mixed two meanings:
- **1970–2025:** an era placeholder for a route share (0.80 / 0.68 / 0.71).
- **1950–69:** the pig-iron/steel ratio itself (S3, v1.1).

It also left out pig iron that is charged to EAFs and to foundries. Using the 2025 worldsteel process split [E, S0861 p. 10]:
- 1,271.2 Mt of pig iron against 69.4 % × 1,848.9 Mt of BOF steel is **0.99 t hot metal per t of BOF steel** [I];
- a plain BOF charge is about 0.85–0.92 t per t.

The difference is hot metal charged to EAFs (China, India) and foundry pig iron. $h$ counts all of it.

### 1.2 New series (staged: `data/activity/wind_solar_shares.csv`, rows replaced in place)

$$h(y)=\frac{\texttt{prod\_pig\_iron}_{\mathrm{XWL}}(y)}{\texttt{prod\_steel}_{\mathrm{XWL}}(y)}\quad(\text{central values, exact scalar; low}=\text{central}=\text{high})$$

- **Rows:** `steel_hot_metal_ratio`, `XWL`, 1950–2025, unit `1`, basis `compiled`.
- **Sources:** `source_ids` is the union of the two input rows (S0831 or S0807;S0410; S0861 for 2025).
- **Not a placeholder:** notes do not start `PLACEHOLDER`, so ST rows no longer carry `share basis: placeholder`, and the `placeholder_share` log drops its three steel runs (40 → 37 entries).

| Era | Old `steel_bf_route_share` | New $h$ (range) | New / old |
|---|---|---|---|
| 1950–69 | = ratio (0.71–0.75) | 0.708–0.749 | 1.000 |
| 1970–81 | 0.80 (placeholder) | 0.708–0.744 | 0.89–0.93 |
| 1982–89 | 0.80 | 0.691–0.710 | 0.86–0.89 |
| 1990–2009 | 0.68 | 0.670–0.747 | 0.99–1.10 |
| 2010–24 | 0.71 | 0.684–0.737 | 0.96–1.04 |
| 2025 | 0.71 | 0.6875 (S0861) | 0.968 |

Series break: 1950–2024 come from USGS DS140 / OWID; 2025 comes from worldsteel. For 2024 the two agree to 0.2 % in $h$: USGS/OWID 1,300/1,900 = 0.6842 and worldsteel 1,293.4/1,886.8 = 0.6855 [I].

### 1.3 Factor rows re-expressed per tonne of hot metal (staged: `data/reference/commodity_factors.csv`, `commodity:0031`–`0065`)

Rule: each per-t-steel number is divided by **its own source's hot-metal/steel ratio** where the source gives one; otherwise by **0.9** (flagged `ASSUMED` in the row notes). New values are rounded to 3 significant figures (chain members: head × ratio, 4 s.f.).

| Rows | Term | Source ratio used | Old low / central / high | New low / central / high | Central × |
|---|---|---|---|---|---|
| 0031 | Stack Pb-210 (own) | Rebuilt from components per t hot metal (HM):<br>• Scunthorpe 6.2e9 / 3.7 Mt iron = 1,676 (**W48 own ratio 3.7/3.9** [E]);<br>• IJmuiden 54 GBq / 5.2 Mt **primary iron** = 10,385 (RP-135 Table 15 is already per t iron [E]; the D74 note said "steel");<br>• UNSCEAR 1.0e4 / 0.9 = 11,111 [A] | 960 / 4,600 / 14,000 | 1,010 / 4,920 / 15,800 | 1.070 |
| 0032 | Stack Po-210 (own) | ENA 4.0e9 and W48 3.96e10 over 3.7 Mt iron; IJmuiden 84 GBq / 5.2 Mt iron; UNSCEAR 1.7e4 / 0.9 [A] | 600 / 12,000 / 24,000 | 649 / 12,600 / 26,400 | 1.050 |
| 0033 | Stack Rn-222 | 1.4 t ore per t BF-BOF steel (WSA) / 0.9 [A] = 1.56 t ore per t HM (W48 cross-check: 6 Mt ore / 3.7 Mt iron = 1.62) | 17,000 / 34,000 / 68,000 | 18,700 / 37,300 / 74,700 | 1.097 |
| 0034–0053 | Slag, U and Th series, impounded and dispersed (20 rows) | **W48 own ratio**: 1.6 Mt slag / 3.7 Mt iron = 0.43 t per t HM (BF + BOS slag), × 1.0541 | e.g. U-238 dispersed 2,800 / 22,000 / 77,000 | 2,950 / 23,200 / 81,200 | 1.050–1.055 (rounding) |
| 0054 | Dust and sludge Pb-210 | UK 5.7e7 kg / 3.7 Mt iron = 15.4 kg per t HM × 900 Bq/kg = 1.39e4. RP-135 (2 kt per Mt primary iron, already per t iron): UK 1.6e4, IJmuiden 3–5e4. Central = geometric mean of 1.39e4 and 1.6e4. Low [judgement] × 3.9/3.7. High unchanged | 5,000 / 15,000 / 40,000 | 5,270 / 14,900 / 40,000 | 0.993 |
| 0055 | Dust and sludge Po-210 | 290 Bq/kg × 15.4 kg per t HM; high unchanged (per t iron) | 1,000 / 4,000 / 15,000 | 1,050 / 4,470 / 15,000 | 1.117 |
| 0056–0065 | Iron-ore tailings, U and Th series (10 rows) | 1.4 t ore and 0.1–1.5 t tailings per t BF-BOF steel [A] / 0.9 [A] | U: 1,000 / 10,000 / 75,000<br>Th: 1,000 / 7,000 / 50,000 | U: 1,110 / 11,100 / 83,300<br>Th: 1,110 / 7,780 / 55,600 | 1.11 |

Every head row's notes now start "Per tonne of hot metal (blast-furnace iron, integrated route; driver `steel_hot_metal_ratio` …)" and end with a `REVISION D76` sentence that gives the conversion. Members gain "REVISION D76: per t hot metal (head x ratio)."

**Reference only:** `commodity_fuel_inputs.csv`. The steel coal row (0.6/0.8/1.0 t per t BF-route steel) becomes 0.667/0.889/1.11 t per t hot metal (/0.9 [A]). It is never added to stream totals (D22).

### 1.4 Which terms stay per tonne of crude steel

**None of the 35 registered ST rows.** Two parts are physically per tonne of BOF steel:
- **BOS slag:** it is inside the slag rows, because W48's 1.6 Mt is BF + BOS slag.
- **BOS gas-cleaning slurry:** it is inside the dust rows.

At an integrated plant BOF steel is proportional to the hot metal charged, and both terms are converted with W48's own ratio, so the conversion is exact at the source plant. A per-crude-steel term would appear only if BF slag and BOS slag were split (open question Q-A). That split would need a BOF-share series, and the repository has none (worldsteel gives one year).

- **EAF slag and dust:** not counted. Scrap carries no ore-chain activity in this model. Artificial nuclides from melted orphan sources are out of scope.
- **Open-hearth slag (1950s–80s):** carried by the same per-t-HM slag factor, an approximation.

### 1.5 Known limits (stated, not fixed)

- **DRI-EAF is excluded by construction.** DRI was 153.0 Mt in 2025 and 145.8 Mt in 2024 [E, S0861 p. 19], about 12 % of primary iron.
  - Its pelletising emissions and its share of iron-ore tailings are missing.
  - For tailings the miss is of order 10 %. For the stack it is much smaller: the IJmuiden pellet plant emits 0.16 GBq/Mt Pb-210 against 10.4 for the sinter plant [E].
- **Sinter vs pellet.** The stack factors are sinter-dominated: UK plants are all sinter; IJmuiden is mostly sinter. Pellet-fed blast furnaces (North America, Sweden, part of Europe) emit roughly 10× less Pb-210 per t of iron. The world sinter share of the BF burden is not in the repository and World Steel in Figures 2026 does not give it (checked; it has iron ore, DRI and scrap tables only). The stack rows are therefore biased high for pellet-heavy regions. This is unchanged by D76.
- **$h$ includes foundry pig iron.** This double-counts slightly with `cast_iron` only if foundry pig iron also appears in wind-turbine castings. The `cast_iron` family is zircon sand only, so the effect is negligible.
- **Abatement.** UNSCEAR's ratio to steel (0.9) is assumed. The source has not been reread.

### 1.6 Impact on the steel rows (④, `allocation_variant = default`, Bq/a)

From the committed build × ($h/$old share) × (new/old factor), bound by bound. This equals the scratch rebuild.

| Year | ST old (low / central / high) | ST new (low / central / high) | Central change | ④ stream total, central | Stream change |
|---|---|---|---|---|---|
| 2010 | 1.11e11 / 7.42e11 / 3.48e12 | 1.23e11 / 8.14e11 / 3.85e12 | **+9.7 %** | 8.66e12 → 8.73e12 | +0.83 % |
| 2020 | 6.19e11 / 4.30e12 / 2.01e13 | 6.61e11 / 4.55e12 / 2.15e13 | **+5.9 %** | 4.348e13 → 4.374e13 | +0.59 % |
| 2024 | 9.40e11 / 7.45e12 / 3.53e13 | 9.77e11 / 7.69e12 / 3.67e13 | +3.2 % | 1.084e14 → 1.086e14 | +0.22 % |
| 2025 (rebuild) | 1.20e12 / 9.26e12 / 4.38e13 | 1.25e12 / 9.61e12 / 4.58e13 | +3.7 % | 1.255e14 → 1.259e14 | +0.28 % |

By term, central:

| Term | 2010 | 2020 |
|---|---|---|
| Stack | +11.0 % | +7.1 % |
| Slag (impounded and dispersed) | +7.9 % | +4.2 % |
| Tailings | +13.7 % | +9.8 % |
| Dust | +4.4 % | +0.8 % |

The ST share of ④ moves from 8.6 % to 9.3 % (2010) and from 9.9 % to 10.4 % (2020). The change sits well inside the factor bounds, which span ×20–×60.

### 1.7 Benchmark B2 rerun (UK 1999)

The new stream-side quantity is: ST stack factor × GBR `prod_steel` 1999 × **GBR** hot-metal ratio. That equals GBR `prod_pig_iron` 1999, which is staged:
- **Pig iron:** 12,139 kt [E, S0862 Table 1].
- **Crude steel:** the same yearbook gives 16,298 kt (oxygen 77.5 %), so $h_{\mathrm{GBR}}=0.745$.
- **Reference:** NRPB-W48, four plants: Pb-210 2.1e10 and Po-210 1.35e11 Bq/a.

| Variant | Hot metal (Mt) | Pb-210 (ratio) | Po-210 (ratio) | Pass ($\tfrac13$–3)? |
|---|---|---|---|---|
| Old (16.28 Mt × 0.68 × per-steel factors) | — | 5.09e10 (2.43) | 1.33e11 (0.98) | yes / yes |
| **New, GBR ratio 0.7455** (proposed) | 12.14 | **5.97e10 (2.84)** | **1.53e11 (1.13)** | yes (near the limit) / yes |
| New, world ratio 0.6875 (for comparison) | 11.19 | 5.51e10 (2.62) | 1.41e11 (1.04) | yes / yes |

New factor bounds × 12.14 Mt: Pb-210 1.2e10–1.9e11 and Po-210 7.9e9–3.2e11. Both references lie inside.
- **Pb-210 stays a flagged known miss**, now at 2.84. The four UK plants give 2.1e10 / 12.14 Mt = 1.7e3 Bq per t HM total. The central (own) factor is 4.9e3 because it is the geometric mean with IJmuiden and UNSCEAR (each about 1.0e4–1.1e4 per t HM).
- **The ratio rises because the conversion is now right.** It does not reflect a change in the data.
- **The comparison is partly circular, as before.** W48 Scunthorpe is the factor's low. It also compares the own-residue factor (fuel part removed) with whole-plant emissions, which biases the ratio by 1/(1 − f_fuel), so about 15 % low at central.

Recommended B2 text: "ST stack factors × GBR `prod_pig_iron` 1999 (hot metal; S0862)".

---

## 2. Pig iron and crude steel data (staged: `data/activity/commodity_production.csv`, +47 rows appended, existing rows unchanged)

**What the repository has:**
- `prod_pig_iron` `XWL` 1910–2024 and 16 countries to 2024, from USGS/OWID. There is **no GBR pig iron in any year** and nothing for 2025.
- `prod_steel` `XWL` 1943–2024 and GBR 1970–2023, with no 2024–25.

**Added from World Steel in Figures 2026** (S0861; p. 18 pig iron, pp. 8–10 crude steel). Rows marked "e" are 2025 worldsteel estimates, set to ±5 %; reported values are ±3 %; `XWL` is ±5 %.

| Series | Country | Years | Values (Mt) | Flags |
|---|---|---|---|---|
| `prod_pig_iron` | `XWL` | 2025 | 1,271.2 | world |
| `prod_pig_iron` | `GBR` | 2024, 2025 | 3.0, 1.6 | — |
| `prod_pig_iron` | BRA, CAN, CHN, DEU, IND, IRN, ITA, JPN, KOR, MEX, RUS, TUR, TWN, UKR, USA | 2025 | 26.3, 5.7, 836.0, 21.9, 95.6, 3.7e, 2.0e, 58.5, 43.7, 0.5, 50.4, 9.7, 9.4, 7.9, 21.4e | IRN, ITA, USA e |
| `prod_steel` | `XWL` | 2025 | 1,848.9 | world; includes estimates |
| `prod_steel` | `GBR` | 2024, 2025 | 4.0, 2.6 | — |
| `prod_steel` | the 15 above + VNM | 2025 | e.g. CHN 960.8e, IND 164.9, USA 81.9e, RUS 67.9e | CHN, IRN, ITA, RUS, USA e |
| `prod_pig_iron` | `GBR` | 1995–2004 | 12.236 … 10.180 (1999: 12.139) | S0862 (SSY 2005), ±3 % |

VNM pig iron is not separate in the source ("Other Asia"), so it is not added.

**2024 is not overwritten.** The existing 2024 rows are rounded USGS/OWID figures. Against worldsteel 2024:

| Country | USGS/OWID 2024 (Mt) | worldsteel 2024 (Mt) |
|---|---|---|
| XWL | 1,300 | 1,293.4 |
| CHN | 840 | 851.7 |
| IND | 93 | 90.0 |
| TWN | 12 | 14.9 |
| TUR | 8 | 10.2 |
| ITA | 3 | 2.0 |
| MEX | 1 | 0.5 |
| RUS | 54 | 51.2 |

These differences are country-level noise beyond the world total; see Q-C.

**Crude steel by process: yes, 2025 only** [E, p. 10]:
- **World:** oxygen 69.4 %, electric 30.3 %, other (open hearth) 0.3 %.
- **GBR:** 59.2 / 40.8.

It is **used only as the cross-check in §1.1** (0.99 t HM per t BOF steel). With one year it cannot drive a series; that would need Q-A. **Sinter is not in the PDF.** DRI is (2021–25), cited in §1.5.

UK context: GBR $h$ 2024 = 0.75 and 2025 = 0.62 (Port Talbot's blast furnaces closed in September 2024).

---

## 3. Olympic Dam uranium (staged: `data/activity/uranium.csv`, 2 rows changed)

**Verified [E]:**
- **FY2026 3,647 and FY2025 3,154 t:** BHP Operational Review FY2026, pdftotext line 429 (group table) and line 529 (Olympic Dam asset table, "Payable uranium").
- **FY2025 3,154, FY2024 3,603 and FY2023 3,406 t:** BHP Annual Report 2025, p. 202, "Uranium, payable metal in concentrate (t), Copper South Australia". The narrative gives "3.2 kt … (3.6 kt FY2024)".
- **FY2023 consistency:** 3,406 × 0.848 = 2,888 t U, as committed.

All of Copper SA's uranium is OD's: Prominent Hill and Carrapateena have no uranium circuit.

**Rule (NUCLEAR_SPEC §14.2, unchanged):** t × 0.848 (treated as U₃O₈; BHP does not state the unit), ±2 %, FY ending June $y$ → calendar year $y$. FY2026 (3,647 t → 3,093 t U) falls in 2026 and is outside the 1950–2025 window: it is recorded in S0864 only.

| Year | Old (estimate, AUS × 0.6154, ±20 %) | **New** (low / central / high, t U) | AUS conventional cap $C$ (low / central / high) | Cap binds? |
|---|---|---|---|---|
| 2024 | 2,264 / 2,830 / 3,395 | 2,994 / **3,055** / 3,116 | 3,479 / 3,839 / 4,168 | no |
| 2025 | 2,264 / 2,830 / 3,395 | **2,421** (capped from 2,621) / **2,675** / 2,728 | 2,421 / 3,839 / 5,994 | **low only** |

The 2025 low binds because AUS `u_production` 2025 is an extrapolation (3,104 / 4,598 / 6,811) with a wide low. The row is capped as the rule requires and the cap is noted. With the cap, the carve-out's low remainder is exactly 0, so no `clipped_difference` flag is raised. The premise `u_production_od` ≤ `u_production`$_{\mathrm{AUS}}$ holds.

Basis changes `modelled` → `compiled`. `source_ids` become S0407;S0863 (2024) and S0407;S0863;S0864 (2025).

**`prod_copper_od` consistency (not changed: copper files are left to the concurrent IOCG work).** BHP's Olympic Dam cathode [E] is:

| FY | Cathode (kt) | Repository `prod_copper_od` |
|---|---|---|
| 2023 | 212.5 | 212.5 (read) |
| 2024 | 215.7 | 215 [A] |
| 2025 | 214.0 | 215 [A] |
| 2026 | 221.3 | — |

- **The 215 kt estimate is confirmed** to within 0.3 % (2024) and 0.5 % (2025). Replacing it with 215.7 / 214.0 ±2 % would move CU-OD (④) and nuclear F8 by +0.3 % and −0.5 %, and shift `cu_class_share_iocg_high_u` by the same tiny OD share difference.
- **Caveat:** cathode includes Prominent Hill and Carrapateena concentrate smelted at OD (transfers of 12.0 kt in FY2025 and 9.9 kt in FY2026 [E]). OD's own-ore copper is therefore about 202 kt (FY2025) and 211 kt (FY2026) [I]. Which definition the OD pool should use is Q-E.

**Effects:**
- **Nuclear F6 (AUS, carved-out conventional tailings):** the remainder $C^{\mathrm{AUS}}_c-P^{\mathrm{OD}}$ changes as follows.

  | Year | Remainder (t U), old → new | F6 central (Bq/a), old → new |
  |---|---|---|
  | 2024 | 1,010 → 784 | 5.15e13 → 3.99e13 (−22 %) |
  | 2025 | 1,010 → 1,165 | 5.15e13 → 5.94e13 (+15 %); low 1.55e13 → 7.8e12 because of the cap |

  That is −0.8 % and +0.5 % of the AUS nuclear default total (1.44e15). The remainder is the ISR artefact of NUCLEAR_SPEC §14.2 ("not a real conventional mill"), so these numbers move an artefact, not a facility.
- **F8 and wind/solar CU-OD rows: unchanged.** Both are driven by `prod_copper_od` and $w_U$ (placeholder 0.12), not by uranium tonnage. If $w_U$ is later computed from values, the U tonnage would enter.
- **F1–F5: unchanged** (full AUS tonnage).

---

## 4. Wording fixes (text for the specs; not yet applied)

| Where | Now | Proposed |
|---|---|---|
| WIND_SOLAR_SPEC §0 Q10 | "BF-route steel share … Placeholder `steel_bf_route_share` 0.90/0.80/0.68/0.71 …" | Add "**Superseded by D76:** `steel_hot_metal_ratio` = world pig iron / crude steel (measured); ST factors per t hot metal." |
| §2.1 group S table | `steel_bf_route_share` \| XWL \| 1950–2025 \| Q10 eras \| S0421 | `steel_hot_metal_ratio` \| XWL \| 1950–2025 \| **not a placeholder**: `prod_pig_iron/prod_steel` (D76) \| S0831/S0807/S0410/S0861 |
| §2.1 group Q | "used only for the §4.3 attribution check …" | "… and, for `prod_pig_iron` / `prod_steel` `XWL`, the hot-metal ratio (D76)" |
| §2.3 family table ST | (unchanged list) | Add "per t hot metal" to the ST row |
| §4.2 step 3 | "`steel_bf_route_share` for steel" | "`steel_hot_metal_ratio` for steel (t hot metal per t crude steel)" |
| §4.2 after step 6 | "EAF scrap steel carries no ore residue (a stated simplification)." | "Only blast-furnace hot metal carries ironmaking residue: scrap-EAF and DRI-EAF steel carry none (a stated simplification; DRI about 12 % of primary iron in 2025). Open-hearth (to about 1990) and BOF steel enter through the hot metal they consume." |
| §5.3 | "sinter/BF dust" | "sinter, BF and BOS gas-cleaning dust and sludge; all ST rows per t hot metal" |
| §7.1 table, steel coal | "per t BF-route steel" | "per t hot metal" (0.667/0.889/1.11) |
| §9(e) B2 | "× GBR `prod_steel` 1999 × `steel_bf_route_share`"; indicative 2.43 / 0.98 | "× GBR `prod_pig_iron` 1999 (12.139 Mt, S0862)"; indicative 2.84 / 1.13 |
| §9(f) | "an ST stack Po210 row (BF share)" | "(hot-metal ratio)" |
| §13.11 S3 | the ±0.15 rule | "Superseded by D76: the series is the ratio in every year; the premise becomes equality to $10^{-9}$." |
| §13.19, §13.20 | "steel-route shares" | "hot-metal ratio" |
| `commodity_notes.md` §1 item 2, §2, §3.2 | "per t BF-BOF steel", "BF-BOF share of steel" | "per t hot metal", "hot-metal ratio"; IJmuiden "per t primary iron" |
| NUCLEAR_SPEC §14.2 table | 2024–25 "AUS × 0.6154 [A]" | "BHP FY2024 3,603 / FY2025 3,154 t × 0.848 (S0863, S0864); 2025 low capped" |
| WIND_SOLAR_SPEC §2.1 group D | "OD uranium follows … 2024–25 = AUS × 0.6154" | "… FY2021–25 read (BHP)" |

Code: `pipeline/streams/wind_solar.py` line 110, `BF_SERIES = "steel_bf_route_share"` → `"steel_hot_metal_ratio"` (constant name optional, e.g. `HM_SERIES`). Nothing else in the code changes.

---

## 5. Uncertainty flags

- **The 0.9 ratio [A]** is used for UNSCEAR (stack Pb and Po), WSA ore (Rn-222 and tailings) and the coal reference. If the true BOF charge is 0.85–0.95, those rows move by ±5 %.
- **W48's 3.7/3.9** is one plant-year (Scunthorpe 1999).
- **The UNSCEAR 2000 Table 28 basis** (steel or iron) is not re-verified here. The D74 note calls the 1.0e4 a "seed".
- **U unit:** BHP's "payable uranium (t)" is treated as U₃O₈, as in §14.2. If it is t U, OD 2024 would be 3,603 t U, still under the cap (3,839). The 2025 value would be 3,154 t U, above the cap low of 2,421; it would be capped there too.
- **2025 worldsteel values** include estimates ("e"), in particular China's crude steel (960.8e). $h(2025)$ is therefore ±a few per cent [A].

## 6. Open questions

- **Q-A.** Split ST slag into BF slag (per t HM, 0.2–0.3 t/t) and BOS slag (per t BOF steel, about 0.1–0.13 t/t)? This needs a BOF-share series by year. Recommendation: **not now**; the combined W48 basis is exact at the source plant.
- **Q-B.** Add an explicit pellet/sinter split or a DRI tailings term? Recommendation: **record as known limits** (§1.5) and revisit with a sinter-share source.
- **Q-C.** Replace the 2024 USGS/OWID pig-iron and steel rows with worldsteel 2024 for consistency with 2025? Recommendation: **keep USGS/OWID to 2024**. The $h$ break is 0.2 %.
- **Q-D.** Fill GBR `prod_pig_iron` 1970–94 and 2005–23 (worldsteel yearbooks)? This is not needed by any stream; useful for UK context only.
- **Q-E.** `prod_copper_od` 2024–25: the read cathode 215.7 / 214.0, or own-ore copper net of PH/CP transfers (about 202 kt FY2025)? This affects F8, CU-OD and `cu_class_share_iocg_high_u`, so it should go with the copper work, not D76.
- **Q-F.** A `u_production` AUS 2025 value (WNA) would remove the 2025 cap and the extrapolated AUS bounds.
- **Q-G.** Source ids S0861–S0864 were free on 2026-11-22. The generator refuses to stage on a clash; renumber if the concurrent IOCG task takes them first.

## 7. Tests and oracle (for the test-writer; not staged)

- **`test_wind_solar.py`:**
  - rename `steel_bf_route_share` → `steel_hot_metal_ratio` (8 places);
  - remove the series from `GROUP_S_PLACEHOLDER`;
  - turn `test_bf_share_near_pig_iron_ratio` into an equality premise ($h = Q_{\mathrm{pig}}/Q_{\mathrm{steel}}$ to $10^{-9}$, all years);
  - change B2 to GBR `prod_pig_iron` 1999 (the Pb-210 `known_miss` stays; the ratio is 2.84);
  - rename the method names that say "bf_share".
- **`wind_solar_oracle.py`:** rename the series (line 110).
- **Nuclear tests:** no change (they pass on the staged data).

## 8. Draft D76 row (not yet in `docs/DECISIONS.md`)

> | D76 | 2026-11-2x | Steel driver per tonne of hot metal; pig iron and crude steel 2024–25; Olympic Dam uranium 2024–25 (Steve, ‹wording of approval›). **(a)** A blast furnace makes hot metal (pig iron), not steel: `steel_bf_route_share` (route-share placeholder 1970–2025, pig-iron/steel ratio 1950–69) is replaced by **`steel_hot_metal_ratio`** = world `prod_pig_iron`/`prod_steel` in every year (measured, not a placeholder; exact scalar). The 35 steel (ST) rows of `commodity_factors.csv` (`commodity:0031`–`0065`) are re-expressed **per tonne of hot metal**. Each per-t-steel figure is divided by its own source's ratio (NRPB-W48 Scunthorpe 3.7/3.9; RP-135 IJmuiden already per t primary iron) or by 0.9 where none is given (UNSCEAR, WSA; flagged). No ST term stays per t crude steel: BOS slag and slurry are inside the W48-based slag and dust rows. DRI-EAF and scrap-EAF carry no ironmaking residue by construction; sinter- vs pellet-fed furnaces are a known limit. The `commodity_fuel_inputs.csv` steel coal row moves to per t hot metal. Effect: ST rows +9.7 % (2010) and +5.9 % (2020) at central; ④ +0.8 % and +0.6 %. B2 uses GBR `prod_pig_iron` 1999 (12.139 Mt): Pb-210 2.84 (known miss), Po-210 1.13. **(b)** `commodity_production.csv` +47 rows: worldsteel World Steel in Figures 2026 (S0861) pig iron and crude steel 2025 for `XWL` and 16 countries, GBR 2024–25 ('e' estimates flagged, ±5 %); GBR pig iron 1995–2004 from the IISI Steel Statistical Yearbook 2005 (S0862). **(c)** `u_production_od` 2024–25 = BHP payable uranium FY2024 3,603 t and FY2025 3,154 t (S0863, S0864) × 0.848, ±2 % (NUCLEAR_SPEC §14.2 rule); the 2025 low is capped at the AUS conventional low (2,421 t U). Nuclear F6 AUS changes by −22 % (2024) and +15 % (2025); F8 and CU-OD are unchanged. `prod_copper_od` 2024–25 (215 kt [A]) is confirmed by BHP cathode 215.7 / 214.0 kt and left for the copper work. Staged under `build/d76_staging/` (`APPLY.md`). | Steve, 2026-11-2x; `research/wind_solar/d76_proposal.md`; WIND_SOLAR_SPEC v1.2; NUCLEAR_SPEC §14.2 |
