# Coal (stream 2): Task 1.3 notes

Files: `sources_task13.csv` (55 sources, S0200-S0254), `bibliography.md`, `availability.csv` (243 rows: 27 products x pre1950 + 8 decades; status counts: measured 33, compiled 69, modelled_possible 68, no_data 73).

## Method
Activity driver (coal tonnes by sector) x factor (Bq/kg coal, ash yield, partition, control efficiency, epsilon). Production from S0230/S0231/S0233; sector split from S0231/S0232/S0006; factors from UNSCEAR (S0001, S0006, S0008, S0010) and the sources here. Anything estimated is basis `modelled`.

## Pre-1950 (D31) key findings
- World coal energy (S0230): 97 TWh (1800), 569 (1850), 5350 (1900), 9227 (1913), 8728 (1945), 11333 (1950). Cumulative 1800-1949 about 436,440 TWh vs 2,039,844 TWh for 1950-2025: pre-1950 is about 21% of 1950-2025 by energy.
- Tonnes: calibrated against UK tonnes (S0231) at 6.85 MWh/t gives about 64 Gt; 8.14 MWh/t gives about 54 Gt (modelled; unit conversion is the main uncertainty). Country shares pre-1950: US 40%, UK 31%, Germany 12%, USSR 4.6%, France 3.7%, Poland 3.2%, China 1.2%. US/Germany/China start at 1900 in S0230; US 1800-1899 needs S0233.
- Power share was small: UK 2.5% (1913), 8.4% (1938), 15% (1949); US 17.4% (1949). Pre-1950 ash is overwhelmingly non-power: domestic (UK about 100 Mt/yr coal), rail (about 14 Mt), gasworks (about 18 Mt), coke ovens (17-24 Mt), bunkers. Mostly bottom ash/clinker, little or no particulate control. UK domestic/industry split not like-for-like before 1945.
- Illustrative (modelled): 54-64 Gt x ash 0.10-0.16 = about 5-10 Gt ash; Ra-226 head activity in that coal about 1.3 PBq at 20 Bq/kg (1950-2025 about 5-6 PBq). Pb-210 (22.3 a) and Po-210 emitted pre-1950 are largely decayed by the opening date; Ra-226, Th-232, U persist.
- No pre-1950 ash, radon, or mine-water measurements exist in what I found.

## Key factor ranges
- Coal: U-238 typical 20 Bq/kg (S0001), K-40 50, Th-232 20 (S0010); China 36/104/30 U/K/Th (S0006); world U 2.40 mg/kg and China 2.43 mg/kg (about 30 Bq/kg; secondary via S0220, unverified); US Ra 8.9-59, Pb-210 12-78, Po-210 3.3-52; UK U 7-19; Germany Ra 10-145 (S0001 Table 25); Greek lignite Ra 346 (S0221).
- Ash yield: US about 10%, UK 16% (10-20%), India 33.9%, world 13% (1985, S0008).
- Fly/bottom: 80-85% fly (S0210, S0008); by firing type 10-100% (S0208).
- Enrichment: **conflicting sources, both recorded.** UNSCEAR 1982 via S0010 gives Ra 1–2×, Pb-210 1–11×, Po-210 about 5×. IAEA TRS 419 Table X (S0202) gives, for **ash particles** (not specifically the fine fraction), Ra-226 5–15×, Th and U 1–10×, K-40 10–50×, Pb-210 20–120× and Po-210 30–200×. Phase 2 must choose with a stated basis, or carry the spread as bounds. Escaping fly ash Bq/kg: K-40 265, U-238 200, Ra-226 240, Pb-210 930, Po-210 1700, Th-232 70 (S0010). US CCRs total Ra 213-297 (S0216).
- Stack release (share of ash): US 1972 8%, EPA standard about 1%, Poland 20%, India 10%, Italy 5%, USSR 10% old / 1% modern, UK 1998 0.4% (S0010, S0008, S0205). Efficiencies: ESP 83-99%, multicyclone 75-90%, bag filter 99% (S0207, S0208, S0234).
- Ash volumes: world 280 Mt/a (1985), 780 Mt CCP 2010 (53% used); US 110 Mt (2012), 66.7 Mt (2023); China 301 (2005) to 520 Mt (2013); India fly ash 69 (1996-97) to 233 Mt (2020-21); EU-15 48-64 Mt.
- Mine radon: China 9.3e5 Bq/t (1.9e5 large to 3.5e6 small mines); 2.8 TBq/GWa (S0001). 1980s crude bounds 36 and 600 GBq/GWa (S0006, S0008).
- Mine water: Silesian Ra-226 400 (1987) to 77 (2006) MBq/d; waters to 390 kBq/m3 of Ra (nuclide unspecified, cited from Skubacz 1990; the paper's own Ra-226 maximum is 110 kBq/m3 in original mine waters, ≤ 25 in mixed drainage); deposits to 400 kBq/kg; ponds Ra-226 median 409 Bq/kg (S0222, S0226).
- Washery refuse / gangue: Ra-226 50-80 Bq/kg, K-40 520-720 (S0202, S0225), all below D21 thresholds; China gangue 15-20% of output, 795 Mt in 2020 (S0254).
- Non-power: household ash Ra-226 163, Ra-228 100 Bq/kg (S0218); smoke 3.5% of coal open fire vs 0.3-0.6% smoke-reducing (S0008).

## Proposed epsilon (all basis modelled, from emanation coefficients)
| Residue | low | central | high | Basis |
|---|---|---|---|---|
| coal_fly_ash | 0.005 | 0.03 | 0.13 | Sakoda 0.03; Solecki 0.08-0.13; TRS 474 <0.1 (S0203, S0247, S0242) |
| coal_bottom_ash | 0.5 x fly | 0.75 x fly | 1.0 x fly | no data; coarser |
| coal_fgd_residue | placeholder = fly ash | | | no data |
| coal_washery_refuse | 0.05 | 0.2 | 0.35 | rocks/soils 0.1-0.3, METHODS default |
Moisture raises emanation (to about 20%) and fine particles raise it (S0243).

## UNSCEAR 2016 ash-radon term (revised after independent verification)
The builder's first reading (UNSCEAR overstated 5–20×) compared a year's Ra-226 inventory in disposed ash with UNSCEAR's flux × area × time term. Those are different conventions, so the comparison did not hold. The verifier redid it:
- Disposed ash per GW a ≈ 2.7×10⁸ kg; at 100 Bq/kg Ra-226 the stock is ≈ 2.7×10¹⁰ Bq.
- UNSCEAR's term implies a flux of ≈ 0.018 Bq m⁻² s⁻¹ over 5.26×10⁴ m² per GW a. That is at or below the ε-limited ceiling (ε × Ra stock × λt ≈ 0.054–0.23 TBq for ε = 0.03–0.13) and consistent with diffusion theory at the higher ε.
- Measured fluxes on Greek ash fields (S0221), scaled to 100 Bq/kg, are 0.2–2.7 mBq m⁻² s⁻¹. Against those, UNSCEAR's value looks high, perhaps by a factor of a few to tens, for covered or wet ash.

Conclusion: a 5–20× overstatement is **not established**, but UNSCEAR's ash term is probably high for real disposal conditions. Under METHODS, ash exhalation is an engine process (ε × Ra stock on an exhalation basis). UNSCEAR's 0.03 / 1.8 values are **not** entered as flows; they are used only as a cross-check.

Also derived: stack release 1.4e-3 TBq/GWa (older) and 9.3e-5 (modern) = about 2.0% and 0.13% of coal Pb-210 inventory.

## Open issues and contradictions
1. Radium retention underground: over 70% (S0222) vs about 40% (S0225); balances do not close.
2. TWh-to-tonne conversion for pre-1950 (54-64 Gt range).
3. FGD residue activity: no numbers (S0248, S0249 abstract-only).
4. Washery refuse mass ratio and strip ratios: not found.
5. World/China Th and U Clarke values unverified (S0252, S0253 paywalled).
6. ACAA historical 1966- table not obtained (S0214); US use fraction 1960s-70s only as a graph.
7. Coke ovens, gasworks, domestic smoke: no measured release data; UNSCEAR 1988 says none exist.
8. Mine radon only China; other countries by scaling.
9. Years inferred: S0205, S0207, S0221, S0225; titles unconfirmed: S0211, S0228.
10. Construction stage: no coal-plant material intensity; pass to Tasks 1.5/1.9. Proposed zero coal construction stage pre-1950.
11. COALQUAL, COALPROD and underlying OWID books (Etemad and Luciani; Smil) not read directly.

## Inaccessible / paywalled URLs for Steve
- ACAA: https://acaa-usa.org/publications/production-and-use-reports/ (S0214)
- NRPB-R327: https://inis.iaea.org/records/ssdeg-phf08 (S0206)
- Michalik 2005: https://doi.org/10.1051/radiopro:2005s1-074 (S0251)
- Paywalled: Tadmor 1986 (10.1016/0265-931X(86)90010-X), Papastefanou 2010, Coles 1978, Eisenbud and Petrow 1964, Kaakinen 1975, Sakoda 2011, Kovler 2005, Zeevaert 2006, Hedvall 1996, Wanke 2008, Ketris and Yudovich 2009, Dai 2012, Sahu 2014, Walencik-Lata 2020, Barton and Ziemer 1986 (URLs in sources_task13.csv).
