# Task 1.9 activity data spine: notes

Files: `data/activity/{electricity_generation,coal,oil_gas,uranium,nuclear,commodity_production,capacity_additions,planning_parameters}.csv` (95,326 rows, 134 series). Sources S0800-S0820 in `research/activity/sources_task19.csv`. Long notes are abbreviated in the CSVs as `[Nxxx, see research/activity/note_registry.csv]`. Converters kept here: `rds2_parse.py` (RDS-2 reactor table to fleet by type and year) and `redbook_u.py` (hand-transcribed Red Book uranium production table, column sums checked against printed totals).

Conventions: bounds are analyst-assumed approximate 5th-95th percentile bands, propagated in log-space quadrature (METHODS 11.1); they are not published uncertainties. `modelled` rows state their method in the note. No dose quantities are present.

## 1. Series and coverage

World = XWL. "World years" blank (-) means no XWL row (country-only series).

| file | series | unit | world years | countries | years | rows |
|---|---|---|---|---|---|---|
| capacity_additions.csv | cap_add_bioenergy | GW | 2001-2025 | 16 | 2001-2025 | 400 |
| capacity_additions.csv | cap_add_coal | GW | 1951-2025 | 16 | 1951-2025 | 398 |
| capacity_additions.csv | cap_add_gas | GW | 1951-2025 | 16 | 1951-2025 | 436 |
| capacity_additions.csv | cap_add_geothermal | GW | 2001-2025 | 16 | 2001-2025 | 383 |
| capacity_additions.csv | cap_add_hydro | GW | 1951-2025 | 16 | 1951-2025 | 450 |
| capacity_additions.csv | cap_add_nuclear | GW | 1954-2024 | 37 | 1954-2024 | 431 |
| capacity_additions.csv | cap_add_nuclear_bwr | GW | 1957-2005 | 1 | 1957-2005 | 36 |
| capacity_additions.csv | cap_add_nuclear_fbr | GW | 1962-2015 | 1 | 1962-2015 | 9 |
| capacity_additions.csv | cap_add_nuclear_gcr | GW | 1956-1989 | 1 | 1956-1989 | 22 |
| capacity_additions.csv | cap_add_nuclear_htgr | GW | 1967-2021 | 1 | 1967-2021 | 4 |
| capacity_additions.csv | cap_add_nuclear_lwgr | GW | 1954-1990 | 1 | 1954-1990 | 16 |
| capacity_additions.csv | cap_add_nuclear_other | GW | 1963-1978 | 1 | 1963-1978 | 6 |
| capacity_additions.csv | cap_add_nuclear_phwr | GW | 1962-2024 | 1 | 1962-2024 | 40 |
| capacity_additions.csv | cap_add_nuclear_pwr | GW | 1957-2024 | 1 | 1957-2024 | 62 |
| capacity_additions.csv | cap_add_oil | GW | 1951-2025 | 16 | 1951-2025 | 450 |
| capacity_additions.csv | cap_add_solar_csp | GW | 2001-2025 | 16 | 2001-2025 | 222 |
| capacity_additions.csv | cap_add_solar_pv | GW | 2001-2025 | 16 | 2001-2025 | 388 |
| capacity_additions.csv | cap_add_wind_offshore | GW | 2001-2025 | 16 | 2001-2025 | 282 |
| capacity_additions.csv | cap_add_wind_onshore | GW | 1982-2025 | 16 | 1982-2025 | 419 |
| capacity_additions.csv | pv_share_thin_film | 1 | 2025-2025 | 1 | 2025-2025 | 1 |
| coal.csv | coal_ash_power_t | t | 1900-2025 | 1 | 1900-2025 | 126 |
| coal.csv | coal_burn_power_twh | TWh | 1900-2025 | 1 | 1900-2025 | 126 |
| coal.csv | coal_consumption_t | t | 1800-2024 | 33 | 1800-2024 | 1995 |
| coal.csv | coal_consumption_twh | TWh | 1800-2024 | 33 | 1800-2024 | 1995 |
| coal.csv | coal_fly_ash_t | t | 1900-2025 | 1 | 1900-2025 | 126 |
| coal.csv | coal_power_share | 1 | 1900-2025 | 3 | 1900-2025 | 313 |
| coal.csv | coal_production_t | t | 1800-2025 | 39 | 1800-2025 | 4468 |
| coal.csv | coal_production_twh | TWh | 1800-2025 | 39 | 1800-2025 | 4468 |
| commodity_production.csv | prod_aluminium | t | 1900-2025 | 62 | 1900-2025 | 2409 |
| commodity_production.csv | prod_bauxite | t | 1900-2024 | 49 | 1900-2024 | 1729 |
| commodity_production.csv | prod_cadmium | t | 1900-2025 | 17 | 1900-2025 | 317 |
| commodity_production.csv | prod_cement | t | 1926-2025 | 15 | 1900-2025 | 290 |
| commodity_production.csv | prod_chromium | t | 1900-2022 | 1 | 1900-2022 | 123 |
| commodity_production.csv | prod_copper | t | 1900-2025 | 87 | 1900-2025 | 3050 |
| commodity_production.csv | prod_copper_refined | t | 2020-2024 | 60 | 1976-2024 | 2054 |
| commodity_production.csv | prod_gallium_primary | t | 2020-2024 | 9 | 2007-2024 | 91 |
| commodity_production.csv | prod_gallium_refined | t | 1973-2021 | 2 | 1948-2021 | 95 |
| commodity_production.csv | prod_indium | t | 2018-2025 | 1 | 2018-2025 | 8 |
| commodity_production.csv | prod_iron_ore | t | 1904-2024 | 18 | 1900-2024 | 325 |
| commodity_production.csv | prod_lead | t | 1900-2025 | 74 | 1900-2025 | 2511 |
| commodity_production.csv | prod_lead_refined | t | - | 96 | 1970-2023 | 3139 |
| commodity_production.csv | prod_molybdenum | t | 1900-2025 | 27 | 1900-2025 | 884 |
| commodity_production.csv | prod_nickel | t | 1900-2025 | 10 | 1900-2025 | 171 |
| commodity_production.csv | prod_nickel_processing | t | 1977-2023 | 39 | 1977-2023 | 1194 |
| commodity_production.csv | prod_pig_iron | t | 1910-2024 | 17 | 1910-2024 | 193 |
| commodity_production.csv | prod_ree_oxide | t | 1900-2025 | 18 | 1900-2025 | 279 |
| commodity_production.csv | prod_selenium | t | 1938-2024 | 16 | 1938-2024 | 152 |
| commodity_production.csv | prod_silicon_mg | t | 1964-2022 | 14 | 1954-2022 | 161 |
| commodity_production.csv | prod_silver | t | 1900-2025 | 93 | 1900-2025 | 3415 |
| commodity_production.csv | prod_steel | t | 1943-2024 | 109 | 1943-2024 | 4287 |
| commodity_production.csv | prod_tellurium | t | 2018-2025 | 1 | 2018-2025 | 8 |
| commodity_production.csv | prod_tin | t | 1905-2025 | 16 | 1905-2025 | 194 |
| commodity_production.csv | prod_tin_smelter | t | - | 37 | 1970-2023 | 1016 |
| commodity_production.csv | prod_zinc | t | 1900-2025 | 79 | 1900-2025 | 2751 |
| commodity_production.csv | prod_zinc_refined | t | - | 44 | 1970-2023 | 1798 |
| commodity_production.csv | prod_zirconium | t | 2020-2024 | 24 | 1970-2024 | 701 |
| electricity_generation.csv | elec_gen_biomass | TWh | 1900-2025 | 31 | 1900-2025 | 1001 |
| electricity_generation.csv | elec_gen_coal | TWh | 1900-2025 | 31 | 1900-2025 | 1391 |
| electricity_generation.csv | elec_gen_gas | TWh | 1900-2025 | 31 | 1900-2025 | 1391 |
| electricity_generation.csv | elec_gen_geothermal | TWh | 1916-2025 | 35 | 1916-2025 | 1039 |
| electricity_generation.csv | elec_gen_hydro | TWh | 1900-2025 | 31 | 1900-2025 | 1931 |
| electricity_generation.csv | elec_gen_nuclear | TWh | 1900-2025 | 31 | 1900-2025 | 1958 |
| electricity_generation.csv | elec_gen_oil | TWh | 1900-2025 | 31 | 1900-2025 | 1391 |
| electricity_generation.csv | elec_gen_peat | TWh | 2000-2024 | 7 | 2000-2024 | 139 |
| electricity_generation.csv | elec_gen_solar | TWh | 1900-2025 | 31 | 1900-2025 | 1662 |
| electricity_generation.csv | elec_gen_wind | TWh | 1900-2025 | 31 | 1900-2025 | 1693 |
| nuclear.csv | nuc_cap_bwr | GW | 1957-2024 | 1 | 1957-2024 | 68 |
| nuclear.csv | nuc_cap_fbr | GW | 1962-2024 | 1 | 1962-2024 | 63 |
| nuclear.csv | nuc_cap_gcr | GW | 1956-2024 | 1 | 1956-2024 | 69 |
| nuclear.csv | nuc_cap_htgr | GW | 1967-2024 | 1 | 1967-2024 | 58 |
| nuclear.csv | nuc_cap_lwgr | GW | 1954-2024 | 1 | 1954-2024 | 71 |
| nuclear.csv | nuc_cap_other | GW | 1963-2024 | 1 | 1963-2024 | 62 |
| nuclear.csv | nuc_cap_phwr | GW | 1962-2024 | 1 | 1962-2024 | 63 |
| nuclear.csv | nuc_cap_pwr | GW | 1957-2024 | 1 | 1957-2024 | 68 |
| nuclear.csv | nuc_cap_total | GW | 1954-2024 | 37 | 1954-2024 | 1740 |
| nuclear.csv | nuc_gen_bwr | TWh | 1957-2024 | 1 | 1957-2024 | 68 |
| nuclear.csv | nuc_gen_fbr | TWh | 1962-2024 | 1 | 1962-2024 | 63 |
| nuclear.csv | nuc_gen_gcr | TWh | 1956-2024 | 1 | 1956-2024 | 69 |
| nuclear.csv | nuc_gen_htgr | TWh | 1967-2024 | 1 | 1967-2024 | 27 |
| nuclear.csv | nuc_gen_lwgr | TWh | 1956-2024 | 1 | 1956-2024 | 69 |
| nuclear.csv | nuc_gen_other | TWh | 1963-2003 | 1 | 1963-2003 | 41 |
| nuclear.csv | nuc_gen_phwr | TWh | 1962-2024 | 1 | 1962-2024 | 63 |
| nuclear.csv | nuc_gen_pwr | TWh | 1957-2024 | 1 | 1957-2024 | 68 |
| nuclear.csv | nuc_spent_fuel_discharged_thm | t | 1956-2024 | 1 | 1956-2024 | 69 |
| oil_gas.csv | gas_burn_power_twh | TWh | 1920-2024 | 1 | 1920-2024 | 105 |
| oil_gas.csv | gas_power_share | 1 | 1920-2024 | 1 | 1920-2024 | 105 |
| oil_gas.csv | gas_production_m3 | m3 | 1900-2025 | 43 | 1900-2025 | 4946 |
| oil_gas.csv | gas_production_twh | TWh | 1900-2025 | 43 | 1900-2025 | 4946 |
| oil_gas.csv | oil_burn_power_twh | TWh | 1903-2024 | 1 | 1903-2024 | 122 |
| oil_gas.csv | oil_power_share | 1 | 1903-2024 | 1 | 1903-2024 | 122 |
| oil_gas.csv | oil_production_m3 | m3 | 1900-2025 | 43 | 1900-2025 | 4843 |
| oil_gas.csv | oil_production_t | t | 1900-2025 | 43 | 1900-2025 | 4843 |
| oil_gas.csv | oil_production_twh | TWh | 1900-2025 | 43 | 1900-2025 | 4843 |
| oil_gas.csv | produced_water_m3 | m3 | 1950-2025 | 2 | 1950-2025 | 152 |
| oil_gas.csv | produced_water_unconv_share | 1 | - | 1 | 2017-2017 | 1 |
| oil_gas.csv | us_wells_drilled_dry | 1 | - | 1 | 1949-2010 | 62 |
| oil_gas.csv | us_wells_drilled_gas | 1 | - | 1 | 1949-2010 | 62 |
| oil_gas.csv | us_wells_drilled_oil | 1 | - | 1 | 1949-2010 | 62 |
| oil_gas.csv | us_wells_drilled_total | 1 | - | 1 | 1949-2010 | 62 |
| planning_parameters.csv | cf_planning_bioenergy | 1 | 2010-2010 | 1 | 2010-2010 | 1 |
| planning_parameters.csv | cf_planning_coal | 1 | 2010-2010 | 1 | 2010-2010 | 1 |
| planning_parameters.csv | cf_planning_gas | 1 | 2010-2010 | 1 | 2010-2010 | 1 |
| planning_parameters.csv | cf_planning_geothermal | 1 | 2010-2010 | 1 | 2010-2010 | 1 |
| planning_parameters.csv | cf_planning_hydro | 1 | 2010-2010 | 1 | 2010-2010 | 1 |
| planning_parameters.csv | cf_planning_nuclear | 1 | 2010-2010 | 1 | 2010-2010 | 1 |
| planning_parameters.csv | cf_planning_solar_csp | 1 | 2010-2010 | 1 | 2010-2010 | 1 |
| planning_parameters.csv | cf_planning_solar_pv | 1 | 2010-2010 | 1 | 2010-2010 | 1 |
| planning_parameters.csv | cf_planning_wind_offshore | 1 | 2010-2010 | 1 | 2010-2010 | 1 |
| planning_parameters.csv | cf_planning_wind_onshore | 1 | 2010-2010 | 1 | 2010-2010 | 1 |
| planning_parameters.csv | cf_realised_bioenergy | 1 | 2000-2024 | 1 | 2000-2024 | 25 |
| planning_parameters.csv | cf_realised_coal | 1 | 2000-2024 | 1 | 2000-2024 | 25 |
| planning_parameters.csv | cf_realised_gas | 1 | 2000-2024 | 1 | 2000-2024 | 25 |
| planning_parameters.csv | cf_realised_geothermal | 1 | 2000-2024 | 1 | 2000-2024 | 25 |
| planning_parameters.csv | cf_realised_hydro | 1 | 2000-2024 | 1 | 2000-2024 | 25 |
| planning_parameters.csv | cf_realised_nuclear | 1 | 1958-2024 | 1 | 1958-2024 | 67 |
| planning_parameters.csv | cf_realised_oil | 1 | 2000-2024 | 1 | 2000-2024 | 25 |
| planning_parameters.csv | cf_realised_solar_csp | 1 | 2000-2024 | 1 | 2000-2024 | 25 |
| planning_parameters.csv | cf_realised_solar_pv | 1 | 2000-2024 | 1 | 2000-2024 | 25 |
| planning_parameters.csv | cf_realised_wind_offshore | 1 | 2000-2024 | 1 | 2000-2024 | 25 |
| planning_parameters.csv | cf_realised_wind_onshore | 1 | 2000-2024 | 1 | 2000-2024 | 25 |
| planning_parameters.csv | plant_life_bioenergy | a | 2010-2010 | 1 | 2010-2010 | 1 |
| planning_parameters.csv | plant_life_coal | a | 2010-2010 | 1 | 2010-2010 | 1 |
| planning_parameters.csv | plant_life_gas | a | 2010-2010 | 1 | 2010-2010 | 1 |
| planning_parameters.csv | plant_life_geothermal | a | 2010-2010 | 1 | 2010-2010 | 1 |
| planning_parameters.csv | plant_life_hydro | a | 2010-2010 | 1 | 2010-2010 | 1 |
| planning_parameters.csv | plant_life_nuclear | a | 2010-2010 | 1 | 2010-2010 | 1 |
| planning_parameters.csv | plant_life_nuclear_observed | a | 1960-2020 | 1 | 1960-2020 | 7 |
| planning_parameters.csv | plant_life_solar_csp | a | 2010-2010 | 1 | 2010-2010 | 1 |
| planning_parameters.csv | plant_life_solar_pv | a | 2010-2010 | 1 | 2010-2010 | 1 |
| planning_parameters.csv | plant_life_wind_offshore | a | 2010-2010 | 1 | 2010-2010 | 1 |
| planning_parameters.csv | plant_life_wind_onshore | a | 2010-2010 | 1 | 2010-2010 | 1 |
| uranium.csv | phi_civil | 1 | 1945-2024 | 1 | 1945-2024 | 80 |
| uranium.csv | u_production | t | 1945-2024 | 39 | 1945-2024 | 1745 |
| uranium.csv | u_requirements_civil | t | 1956-2024 | 1 | 1956-2024 | 69 |

## 2. Gaps (not filled; nothing invented)

- Uranium 2025 production absent (WNA 2025 not yet available to me). Red Book 2022 and earlier editions inaccessible via oecd-nea.org; 1945-2003 transcribed from the edition obtained, 2004-2014 from OWID uranium, 2015-2024 WNA.
- Tellurium and indium world only 2018-2025; zirconium and primary gallium world only 2020-2024; refined zinc, lead, tin, copper, and smelter tin have country rows only (no world total).
- Per-country coal ash, power share and burn exist only for XWL (power share also USA, GBR).
- Fly-ash utilisation: ACAA data not obtained (https://acaa-usa.org/publications/production-and-use-reports/).
- Wind direct-drive vs geared split and PV c-Si/CdTe/CIGS split: only the 2025 thin-film share anchor.
- Produced-water unconventional share: USA 2017 only. Wells drilled: US 1949-2010 only; none elsewhere or after 2010.
- Peat: only IRENA peat generation (7 countries, 2000-2024); no peat energy use by country.
- Material intensity is Task 1.5's. Capacity additions before 1950 absent (non-nuclear start 1951 modelled, wind/solar/etc. 2001 or later).
- Sanity plots not produced.

## 3. Gap-filling and conversions

- Electricity by source: OWID/Ember/Pinto compilations; pre-1965 and world pre-1985 values modelled (basis modelled, notes give method).
- Coal energy-to-tonne: calorific divisor extremes 6.85 and 8.14 MWh/t; EIA 1985-89 ratio 5.52 used where needed; 2025 uses last observed ratio. Tonnes before ratios exist are modelled.
- Power shares: fuel burn derived from generation via UK/US efficiency proxies, then divided by consumption.
- Nuclear fleet by type reconstructed from the RDS-2 reactor table; generation by type is modelled from capacity and realised CF; spent fuel from generation and burn-up assumptions.
- phi_civil (METHODS 9.2): 0 before 1965, then min(1, (R_civil - U_doc,civil)/(U_prod - U_doc)); modelled.
- Commodities: OWID Minerals explorer (USGS DS140 + MCS + BGS) substituting for DS140 itself.
- Planning parameters: IPCC AR5 Annex III (2010 vintage) lifetimes and CFs; realised CFs from IRENA (and nuclear from PRIS-derived reactor table).

## 4. Conflicts and judgements

- Red Book total differs from sum of countries by 100 tU; two typos in printed totals column (Portugal, Spain). Sums of the entries were used.
- Modelled world coal power share is about 81% in 2020; likely overshoots (inference: nearer two-thirds, unsourced). Treat as upper-leaning; bands are wide.
- Modelled spent-fuel discharge is about 40% above IAEA's 7,000 tHM/a figure; flagged, not tuned.
- EIA coal tonnes 1980-84 unreliable; EIA oil 1973-79 incomplete (physical-volume threshold 1980, ratio years 1980-89).
- Tellurium 2023 USGS revision. Red Book vs OWID vs WNA world uranium agree to under 0.1% in 2015 and 2023.

## 5. Inaccessible items and URLs

- USGS DS140 per-commodity files (usgs.gov/media/files returned 403). Pattern: https://www.usgs.gov/media/files/<commodity>-historical-statistics-data-series-140 for copper, aluminum, bauxite-and-alumina, iron-ore, iron-and-steel, cement, silver, zinc, lead, tin, nickel, zirconium-and-hafnium, silicon, gallium, selenium, tellurium, indium, cadmium, rare-earths, molybdenum, chromium (plus uranium, coal if mirrored). Catalogue: https://pubs.usgs.gov/publication/ds140
- Energy Institute Statistical Review: https://www.energyinst.org/statistical-review (403)
- Red Book editions: https://www.oecd-nea.org (uranium resources, production and demand)
- IEA data portal; PRIS: https://pris.iaea.org; Stanford WGC geothermal papers (SSL error).

## 6. Validation

`python3 -m pipeline.validate --root <scratch>` with data, schema, pipeline copied, my sources merged into the scratch `data/sources.csv` and activity files added: "OK: no issues" (T01-T04 clean). Task 1.6's S0525 (no year, S01) was dropped from the scratch sources only; `data/sources.csv` untouched.
