# Task 1.9 activity data spine: notes

Files: `data/activity/{electricity_generation,coal,oil_gas,uranium,nuclear,commodity_production,commodity_prices,capacity_additions,planning_parameters,biomass,peat}.csv` (173,254 rows, 215 series). Sources S0800-S0860 (all rows, old and new) in `research/activity/sources_task19.csv`. Long notes are abbreviated in the CSVs as `[Nxxx, see research/activity/note_registry.csv]`. Converters kept here (paths inside point to the scratch folder; edit before reuse): `ds140.py` (DS140 CSV sheet loader), `ds140_comm.py` (DS140 to commodity series), `build_prices.py`, `build_bio.py`, `build_peat.py`, `make_sources2.py`, `rds2_parse.py` (RDS-2 reactor table to fleet by type and year) and `redbook_u.py` (hand-transcribed Red Book uranium production table, column sums checked against printed totals).

Conventions: bounds are analyst-assumed approximate 5th-95th percentile bands, propagated in log-space quadrature (METHODS 11.1); they are not published uncertainties. `modelled` rows state their method in the note. No dose quantities are present.

## 1. Series and coverage

World = XWL. "World years" blank (-) means no XWL row (country-only series).

| file | series | unit | world years | countries | years | rows |
|---|---|---|---|---|---|---|
| biomass.csv | charcoal_production_t | t | 1961-2024 | 200 | 1961-2024 | 10366 |
| biomass.csv | household_charcoal_energy_twh | TWh | 2012-2023 | 165 | 1990-2023 | 4528 |
| biomass.csv | household_charcoal_t | t | 2012-2023 | 165 | 1990-2023 | 4528 |
| biomass.csv | household_fuelwood_energy_twh | TWh | 1990-2023 | 195 | 1990-2023 | 6089 |
| biomass.csv | household_fuelwood_m3 | m3 | 1990-2023 | 195 | 1990-2023 | 6089 |
| biomass.csv | wood_fuel_energy_twh | TWh | 1961-2024 | 205 | 1961-2024 | 11493 |
| biomass.csv | wood_fuel_m3 | m3 | 1961-2024 | 205 | 1961-2024 | 11493 |
| biomass.csv | wood_fuel_t | t | 1961-2024 | 205 | 1961-2024 | 11493 |
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
| coal.csv | coal_consumption_t | t | 1800-2025 | 33 | 1800-2025 | 2118 |
| coal.csv | coal_consumption_twh | TWh | 1800-2025 | 33 | 1800-2025 | 2118 |
| coal.csv | coal_fly_ash_t | t | 1900-2025 | 1 | 1900-2025 | 126 |
| coal.csv | coal_power_share | 1 | 1900-2025 | 3 | 1900-2025 | 313 |
| coal.csv | coal_production_t | t | 1800-2025 | 39 | 1800-2025 | 4558 |
| coal.csv | coal_production_twh | TWh | 1800-2025 | 39 | 1800-2025 | 4558 |
| commodity_prices.csv | price_aluminium_usd98_t | USD1998/t | - | 1 | 1900-2021 | 122 |
| commodity_prices.csv | price_aluminium_usd_t | USD/t | - | 1 | 1900-2021 | 122 |
| commodity_prices.csv | price_cement_usd98_t | USD1998/t | - | 1 | 1900-2021 | 122 |
| commodity_prices.csv | price_cement_usd_t | USD/t | - | 1 | 1900-2021 | 122 |
| commodity_prices.csv | price_copper_usd98_t | USD1998/t | - | 1 | 1900-2020 | 121 |
| commodity_prices.csv | price_copper_usd_t | USD/t | - | 1 | 1900-2020 | 121 |
| commodity_prices.csv | price_gold_usd98_t | USD1998/t | - | 1 | 1900-2022 | 123 |
| commodity_prices.csv | price_gold_usd_t | USD/t | - | 1 | 1900-2022 | 123 |
| commodity_prices.csv | price_iron_ore_usd98_t | USD1998/t | - | 1 | 1900-2021 | 122 |
| commodity_prices.csv | price_iron_ore_usd_t | USD/t | - | 1 | 1900-2021 | 122 |
| commodity_prices.csv | price_lead_usd98_t | USD1998/t | - | 1 | 1900-2021 | 122 |
| commodity_prices.csv | price_lead_usd_t | USD/t | - | 1 | 1900-2021 | 122 |
| commodity_prices.csv | price_molybdenum_usd98_t | USD1998/t | - | 1 | 1912-2022 | 111 |
| commodity_prices.csv | price_molybdenum_usd_t | USD/t | - | 1 | 1912-2022 | 111 |
| commodity_prices.csv | price_nickel_usd98_t | USD1998/t | - | 1 | 1900-2019 | 120 |
| commodity_prices.csv | price_nickel_usd_t | USD/t | - | 1 | 1900-2019 | 120 |
| commodity_prices.csv | price_phosphate_rock_usd98_t | USD1998/t | - | 1 | 1900-2022 | 123 |
| commodity_prices.csv | price_phosphate_rock_usd_t | USD/t | - | 1 | 1900-2022 | 123 |
| commodity_prices.csv | price_rare_earths_usd98_t | USD1998/t | - | 1 | 1922-2020 | 99 |
| commodity_prices.csv | price_rare_earths_usd_t | USD/t | - | 1 | 1922-2020 | 99 |
| commodity_prices.csv | price_silver_usd98_t | USD1998/t | - | 1 | 1900-2021 | 122 |
| commodity_prices.csv | price_silver_usd_t | USD/t | - | 1 | 1900-2021 | 122 |
| commodity_prices.csv | price_steel_usd98_t | USD1998/t | - | 1 | 1900-2010 | 111 |
| commodity_prices.csv | price_steel_usd_t | USD/t | - | 1 | 1900-2010 | 111 |
| commodity_prices.csv | price_thorium_usd98_t | USD1998/t | - | 1 | 1951-2010 | 60 |
| commodity_prices.csv | price_thorium_usd_t | USD/t | - | 1 | 1951-2010 | 60 |
| commodity_prices.csv | price_zinc_usd98_t | USD1998/t | - | 1 | 1900-2022 | 123 |
| commodity_prices.csv | price_zinc_usd_t | USD/t | - | 1 | 1900-2022 | 123 |
| commodity_production.csv | cons_apparent_alumina | t | - | 1 | 1955-2021 | 67 |
| commodity_production.csv | cons_apparent_aluminium | t | - | 1 | 1900-2021 | 122 |
| commodity_production.csv | cons_apparent_bauxite | t | - | 1 | 1900-2021 | 122 |
| commodity_production.csv | cons_apparent_cadmium | t | - | 1 | 1903-2010 | 108 |
| commodity_production.csv | cons_apparent_cement | t | - | 1 | 1900-2021 | 122 |
| commodity_production.csv | cons_apparent_chromium | t | - | 1 | 1900-2022 | 123 |
| commodity_production.csv | cons_apparent_copper | t | - | 1 | 1900-2020 | 121 |
| commodity_production.csv | cons_apparent_dri | t | - | 1 | 1985-2021 | 37 |
| commodity_production.csv | cons_apparent_gallium | t | - | 1 | 1970-2021 | 52 |
| commodity_production.csv | cons_apparent_indium | t | - | 1 | 1936-2022 | 87 |
| commodity_production.csv | cons_apparent_iron_ore | t | - | 1 | 1900-2021 | 122 |
| commodity_production.csv | cons_apparent_lead | t | - | 1 | 1900-2021 | 122 |
| commodity_production.csv | cons_apparent_molybdenum | t | - | 1 | 1900-2022 | 123 |
| commodity_production.csv | cons_apparent_nickel | t | - | 1 | 1900-2019 | 120 |
| commodity_production.csv | cons_apparent_peat | t | - | 1 | 1904-2021 | 118 |
| commodity_production.csv | cons_apparent_phosphate_rock | t | - | 1 | 1900-2022 | 123 |
| commodity_production.csv | cons_apparent_pig_iron | t | - | 1 | 1900-2021 | 122 |
| commodity_production.csv | cons_apparent_ree_oxide | t | - | 1 | 1900-2020 | 120 |
| commodity_production.csv | cons_apparent_selenium | t | - | 1 | 1900-2008 | 109 |
| commodity_production.csv | cons_apparent_silicon | t | - | 1 | 1954-2022 | 67 |
| commodity_production.csv | cons_apparent_silver | t | - | 1 | 1900-2021 | 122 |
| commodity_production.csv | cons_apparent_steel | t | - | 1 | 1900-2021 | 122 |
| commodity_production.csv | cons_apparent_tellurium | t | - | 1 | 1926-1984 | 59 |
| commodity_production.csv | cons_apparent_thorium | t | - | 1 | 1902-2017 | 94 |
| commodity_production.csv | cons_apparent_tin | t | - | 1 | 1900-2021 | 122 |
| commodity_production.csv | cons_apparent_zinc | t | - | 1 | 1900-2022 | 123 |
| commodity_production.csv | cons_apparent_zirconium | t | - | 1 | 1902-2021 | 101 |
| commodity_production.csv | cons_reported_gold | t | - | 1 | 1900-2022 | 123 |
| commodity_production.csv | prod_alumina | t | 1968-2021 | 2 | 1955-2021 | 121 |
| commodity_production.csv | prod_aluminium | t | 1900-2025 | 62 | 1900-2025 | 2479 |
| commodity_production.csv | prod_bauxite | t | 1900-2024 | 49 | 1900-2024 | 1729 |
| commodity_production.csv | prod_cadmium | t | 1900-2025 | 17 | 1900-2025 | 317 |
| commodity_production.csv | prod_cement | t | 1926-2025 | 15 | 1900-2025 | 290 |
| commodity_production.csv | prod_chromium | t | 1900-2022 | 2 | 1900-2022 | 246 |
| commodity_production.csv | prod_copper | t | 1900-2025 | 87 | 1900-2025 | 3120 |
| commodity_production.csv | prod_copper_refined | t | 2020-2024 | 60 | 1976-2024 | 2054 |
| commodity_production.csv | prod_dri | t | 1984-2021 | 2 | 1984-2021 | 75 |
| commodity_production.csv | prod_gallium_primary | t | 2020-2024 | 9 | 2007-2024 | 91 |
| commodity_production.csv | prod_gallium_refined | t | 1973-2021 | 2 | 1948-2021 | 95 |
| commodity_production.csv | prod_gold | t | 1900-2022 | 2 | 1900-2022 | 246 |
| commodity_production.csv | prod_indium | t | 1972-2025 | 2 | 1941-2025 | 99 |
| commodity_production.csv | prod_iron_ore | t | 1904-2024 | 18 | 1900-2024 | 325 |
| commodity_production.csv | prod_lead | t | 1900-2025 | 74 | 1900-2025 | 2521 |
| commodity_production.csv | prod_lead_primary | t | - | 1 | 1900-2021 | 122 |
| commodity_production.csv | prod_lead_refined | t | - | 96 | 1970-2023 | 3139 |
| commodity_production.csv | prod_molybdenum | t | 1900-2025 | 27 | 1900-2025 | 885 |
| commodity_production.csv | prod_nickel | t | 1900-2025 | 10 | 1900-2025 | 278 |
| commodity_production.csv | prod_nickel_plant | t | 1970-2019 | 1 | 1970-2019 | 50 |
| commodity_production.csv | prod_nickel_processing | t | 1977-2023 | 39 | 1977-2023 | 1194 |
| commodity_production.csv | prod_peat | t | 1935-2021 | 2 | 1904-2021 | 197 |
| commodity_production.csv | prod_phosphate_rock | t | 1900-2022 | 2 | 1900-2022 | 246 |
| commodity_production.csv | prod_pig_iron | t | 1910-2024 | 17 | 1900-2024 | 313 |
| commodity_production.csv | prod_ree_oxide | t | 1900-2025 | 21 | 1900-2025 | 505 |
| commodity_production.csv | prod_selenium | t | 1938-2024 | 16 | 1938-2024 | 152 |
| commodity_production.csv | prod_selenium_primary | t | - | 1 | 1900-1996 | 88 |
| commodity_production.csv | prod_silicon_mg | t | 1964-2022 | 14 | 1954-2022 | 161 |
| commodity_production.csv | prod_silver | t | 1900-2025 | 93 | 1900-2025 | 3485 |
| commodity_production.csv | prod_steel | t | 1943-2024 | 109 | 1900-2024 | 4357 |
| commodity_production.csv | prod_tellurium | t | 1930-2025 | 2 | 1926-2025 | 143 |
| commodity_production.csv | prod_thorium | t | 1960-1977 | 2 | 1959-2020 | 54 |
| commodity_production.csv | prod_tin | t | 1905-2025 | 16 | 1905-2025 | 194 |
| commodity_production.csv | prod_tin_primary | t | - | 1 | 1916-2021 | 82 |
| commodity_production.csv | prod_tin_smelter | t | - | 37 | 1970-2023 | 1016 |
| commodity_production.csv | prod_zinc | t | 1900-2025 | 79 | 1900-2025 | 2751 |
| commodity_production.csv | prod_zinc_primary | t | - | 1 | 1900-2022 | 123 |
| commodity_production.csv | prod_zinc_refined | t | - | 44 | 1970-2023 | 1798 |
| commodity_production.csv | prod_zirconium | t | 1944-2024 | 24 | 1902-2024 | 820 |
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
| peat.csv | peat_household_t | t | - | 16 | 1990-2024 | 372 |
| peat.csv | peat_power_heat_t | t | - | 11 | 1990-2024 | 228 |
| peat.csv | peat_production_t | t | - | 19 | 1990-2024 | 474 |
| peat.csv | peat_production_twh | TWh | - | 19 | 1990-2024 | 474 |
| peat.csv | peat_supply_t | t | - | 29 | 1990-2024 | 542 |
| peat.csv | peat_supply_twh | TWh | - | 29 | 1990-2024 | 542 |
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

- Uranium 2025 production and requirements are absent (WNA 2025 production and the matching requirements were not obtained), so there is **no 2025 `phi_civil` row**: phi is a ratio of the two world series, which both end in 2024. Red Book 2022 and earlier editions are inaccessible via oecd-nea.org; 1945-2003 transcribed from the edition obtained, 2004-2014 from OWID uranium, 2015-2024 WNA.
- Refined zinc, lead, tin and copper and smelter tin have country rows only (DS140 has no refined world total; its world column is mine output). Gallium primary world only 2020-2024 (MCS); thorium world only 1960-1977.
- Per-country coal ash, power share and burn exist only for XWL (power share also USA, GBR).
- Fly-ash utilisation: ACAA data not obtained (https://acaa-usa.org/publications/production-and-use-reports/).
- Wind direct-drive vs geared split and PV c-Si/CdTe/CIGS split: only the 2025 thin-film share anchor.
- Produced-water unconventional share: USA 2017 only. Wells drilled: US 1949-2010 only; none elsewhere or after 2010.
- Country REE production before 1990 (China, including Bayan Obo by year, Australia, USSR/CIS, USA before DS140): not reachable; see section 8.3 for the files needed.
- Peat before 1990 and peat products; wood fuel before 1961; household fuelwood for China.
- Capacity additions before 1950 absent (non-nuclear start 1951 modelled, wind/solar/etc. 2001 or later).
- Material intensity is **not** duplicated in the spine: it is in `research/wind_solar/material_intensity.csv` (Task 1.5).

## 3. Gap-filling and conversions

- Electricity by source: OWID/Ember/Pinto compilations; pre-1965 and world pre-1985 values modelled (basis modelled, notes give method).
- Coal energy-to-tonne: calorific divisor extremes 6.85 and 8.14 MWh/t; EIA 1985-89 ratio 5.52 used where needed; 2025 uses last observed ratio. Tonnes before ratios exist are modelled.
- Power shares: fuel burn derived from generation via a US/UK efficiency proxy scaled to the IEA/EIA anchors (section 8.1), then divided by consumption.
- Nuclear fleet by type reconstructed from the RDS-2 reactor table; generation by type is modelled from capacity and realised CF; spent fuel from generation and burn-up assumptions (section 8.2).
- phi_civil (METHODS 9.2): 0 before 1965, then min(1, R_civil / U_prod); modelled; saturated years carry an assumed lower bound (section 8.4).
- Commodities: DS140 world and US columns (from section 7); OWID minerals explorer where DS140 does not reach; Minerals Yearbooks for REE by country.
- Planning parameters: IPCC AR5 Annex III (2010 vintage) lifetimes and CFs; realised CFs from IRENA (and nuclear from the RDS-2-derived reactor table).

## 4. Conflicts and judgements

- Red Book total differs from sum of countries by 100 tU; two typos in printed totals column (Portugal, Spain). Sums of the entries were used.
- World coal power share: the first version gave 81% (2020) because the efficiency bounds were mis-ordered in the code (central efficiency was 0.85 of the US value, an implied fleet efficiency of about 27%). Fixed and recalibrated: 63.5% in 2020 and 65% in 2023 (section 8.1).
- Modelled spent-fuel discharge: 9,500 tHM in 2020 vs IAEA/NEA 7,000 tHM/a (about +36%); cumulative to 2020 is 402,000 tHM, matching IAEA's over 400,000 (section 8.2). IAEA itself publishes two annual figures (7,000 and about 10,000).
- EIA coal tonnes 1980-84 unreliable; EIA oil 1973-79 incomplete (physical-volume threshold 1980, ratio years 1980-89).
- Tellurium 2023 USGS revision (+62%, documented on the row). Red Book vs OWID vs WNA world uranium agree to under 0.1% in 2015 and 2023.

## 5. Inaccessible items and URLs

- USGS DS140: the usgs.gov/media/files pages still return 403, but the files are **now available** from Steve's S3 mirror (section 7) and the live S3 URLs answer HTTP 200 (pattern in the source rows S0821-S0845). Catalogue: https://pubs.usgs.gov/publication/ds140
- Energy Institute Statistical Review: https://www.energyinst.org/statistical-review (403)
- Red Book editions: https://www.oecd-nea.org (uranium resources, production and demand)
- IEA data portal (World Energy Balances): https://www.iea.org/data-and-statistics/data-product/world-energy-balances (licence); PRIS: https://pris.iaea.org; Stanford WGC geothermal papers (SSL error).
- IAEA/NEA/EC/WNA Status and Trends in Spent Fuel and Radioactive Waste Management (3rd ed.): primary document not accessed (only the NEI report, S0853).

## 6. Validation

- Against the real tree: `python3 -m pipeline.validate --root /mnt/user-data/outputs` reports only T04 "unresolved source" for the twelve new source IDs S0849-S0860 (not yet merged into `data/sources.csv`); no other rule fires. Earlier IDs (S0800-S0848) are already in the real `data/sources.csv`.
- Against a scratch copy of the tree with the unmerged rows of `sources_task19.csv` appended to `data/sources.csv`: "OK: no issues" (T01-T04 clean). Low <= central <= high holds on all 172,828 rows. `data/sources.csv` untouched.

## 7. Follow-up (25 Oct 2026): DS140 mirror, prices, biomass, peat

### 7.1 DS140 upgrade of `commodity_production.csv`
- Source: Steve's mirror of the USGS S3 bucket (derived CSVs, read-only). One source row per workbook, S0821-S0845 (25 workbooks; the iron and steel slag workbook was staged but not used). Original URL pattern `https://d9-wret.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/media/files/<workbook>.xlsx` (HEAD returned 200 on 25 Oct 2026). The mirror's `catalogue.csv` (which holds the exact `original_url`) was not staged, so the `assets/palladium/production/` prefix is the usual USGS one, not confirmed from the catalogue.
- DS140 `World production` is now the primary XWL row (basis `compiled`); DS140 US primary/mine production is a USA row (basis `measured`); DS140 apparent consumption is `cons_apparent_<commodity>` for USA (gold: `cons_reported_gold`; basis `compiled`, a calculated quantity). OWID-derived rows remain only where DS140 does not reach (mostly 2021/22 onward, and non-US countries).
- New series: `prod_gold`, `prod_thorium`, `prod_phosphate_rock`, `prod_peat`, `prod_alumina`, `prod_dri`, `prod_nickel_plant`, and 27 `cons_apparent_*`/`cons_reported_gold` series (US).
- Not DS140 world totals: US `Primary production` for zinc, lead, tin and selenium is smelter/refinery output from ore, not mine output. These are kept as separate `prod_<c>_primary` USA series so they do not splice with the OWID mine-output US rows (DS140/OWID ratio for zinc ranged 0.12 to 1.77, median 0.36).

### 7.2 DS140 vs OWID agreement (central values, overlap years; ratio = DS140/OWID)
- World: ratios are 1.000 for almost every year of aluminium, bauxite, cement, chromium, copper, gallium, iron ore, pig iron, REE, selenium, silver, steel, tin, lead (to 1.011) and zinc. This is expected: OWID's pre-2022 values for these are DS140 itself, so agreement is by construction, not independent confirmation. The differences are in the last DS140 years where OWID switches to MCS/BGS: cadmium 2021 0.91, nickel 2019 0.97, molybdenum 1.04 (2021), silicon 1.07 (2022), zinc 1.15 (2020), steel 1.05 (2020), tin 1.05 (2020).
- Tellurium and indium: DS140 world is 1.00 to 1.17 and 0.98 to 1.26 of my MCS-edition values for 2018-2020 (worst 2019: 1.17 and 1.26). DS140 (2020 edition for tellurium, 2022 for indium) is kept as primary for those years; MCS values remain for 2021-2025.
- US production: aluminium 0.97 (2019), copper 0.73 to 1.26 (2020 worst), cadmium 0.88 (2021), silicon 0.85 (2022), silver 1.05 (2020), zirconium up to 2.0 (2017): different editions or MCS-vs-DS140 definitions at the seam. Possible splice steps at 2020-2022 in USA series where DS140 ends and OWID/MCS values continue.
- Gaps filled: tellurium world 1930-2020 (was 2018+), indium world 1972-2022 (was 2018+), zirconium world 1944-2021 (was 2020-2024), US rows for all of the above from 1900. Rare earths: DS140 gives world from 1900, identical to OWID, so no extension. Refined zinc/lead/tin/copper world totals are NOT available in DS140 (its `World production` is mine output for these), so they remain country-only.

### 7.3 Unit-value (price) series: `commodity_prices.csv`
- 28 series (14 commodities x nominal `price_<c>_usd_t` and constant-1998 `price_<c>_usd98_t`), USA, 3,202 rows. Commodities: copper, gold, silver, iron ore, steel, aluminium, zinc, lead, nickel, molybdenum, rare earths, thorium, phosphate rock, cement. Spans are in the table above; steel stops 2010 (DS140 stops publishing the value), nickel 2019, thorium 2010, rare earths 2020.
- Units: `USD/t` and `USD1998/t`. SCHEMA 4.6 gives `unit` as a free string (SI or SI-derived examples) and the validator accepted both; a currency is not SI, so this is a convention to ratify, not an SI unit.
- These are US-market unit values (price of apparent consumption or market price as USGS defines it), not world prices; the real-dollar series uses the USGS deflator to 1998. Bands assumed: +-10% before 1950, +-5% after (x2 for rare earths and thorium).
- Uranium is not in DS140. For D6 value allocation of uranium the options (none fetched) are: EIA Uranium Marketing Annual Report (weighted-average US purchase prices, 1994 onward; https://www.eia.gov/uranium/marketing/), NEA/IAEA Red Book (market price and production cost classes), UxC/TradeTech spot and long-term indicators (commercial), and pre-1994 US AEC/DOE procurement prices.

### 7.4 Household biomass (D37): `biomass.csv`
- `wood_fuel_m3` (FAOSTAT item 1864, 1961-2024, XWL and about 205 countries, 11,493 rows), plus `wood_fuel_t` (x0.725 t/m3, range 0.625-0.75) and `wood_fuel_energy_twh` (x9.4 GJ/m3, range 7.2-14.0), both `modelled` from FAO/ITTO/UNECE/Eurostat questionnaire factors (S0848). `charcoal_production_t` (FAOSTAT 1630, 1961-2024). World wood fuel is about $1.5\times10^{9}$ m3 in 1961 and $1.95\times10^{9}$ m3 in 2023-24 (about 5,100 TWh gross).
- Household use: `household_fuelwood_m3`, `household_fuelwood_energy_twh`, `household_charcoal_t`, `household_charcoal_energy_twh` from the UN Energy Statistics database (S0847), 1990-2023, about 195 countries. The XWL row is the sum of reporting countries (a lower bound; about $1.11\times10^{9}$ m3 in 1990, $1.47\times10^{9}$ m3 in 2023, about 75% of FAO wood fuel). It was the substitute for IEA residential consumption of primary solid biofuels (IEA World Energy Balances: https://www.iea.org/data-and-statistics/data-product/world-energy-balances; not accessible without a licence, not tried).
- Caveats: China reports no household fuelwood to UNSD. UN household use exceeds FAO national wood fuel production in 73 of 185 reporting countries in 2023 (62 where FAO production is positive and exceeded; the rest have no FAO row); the excess is 2.65e8 m3, 18% of the XWL household sum. Worst cases: Iran (8.1e6 m3 UN vs 3e4 m3 FAO, x270), Canada (8.4e6 vs 1.2e6, x7), Nepal, Poland, Cameroon (x1.4-2.7) and India (3.8e8 vs 3.0e8, x1.3). The country rows are flagged in the first characters of the note ("WORST CASE UN>FAO" at ratio 5 or more, "CAUTION UN>FAO" below that). The UN fuelwood likely includes residues, branches and imports that FAO roundwood production does not count, so the XWL household sum is not a strict lower bound (China missing, but some countries too high). FAO wood fuel includes the roundwood converted to charcoal, so do not add charcoal to wood fuel. FAO values for most developing countries are estimated (flag E). Pre-1961 not covered; no compilation was found.

### 7.5 Peat by country: `peat.csv`
- UN Energy Statistics commodity 1100 Peat (S0847): `peat_production_t`/`_twh`, `peat_supply_t`/`_twh` (total energy supply, a proxy for energy use), `peat_household_t`, `peat_power_heat_t` (electricity and CHP transformation), 1990-2024, 29 countries. All six requested countries are covered: Finland and Ireland and Sweden from 1990; Belarus, Russia and Estonia from 1992. Examples (peat supply): Finland about 27 TWh (2010), 7 TWh (2023); Ireland about 15 TWh (1990), 3 TWh (2023); Belarus about 6 TWh (2023); Russia about 2.5 TWh (2023); Sweden 0.3 TWh (2023); Estonia 0.07 TWh (2023). Finland and Ireland 1990 values match the national statistics I know of (about 25 and 16 TWh) but I did not check them against a primary source.
- Energy uses UN's country conversion factors (8.1-13 GJ/t); this is peat for fuel and excludes horticultural peat. DS140 peat (`prod_peat`, world 1935-2021) is all peat including horticulture.
- Not obtained: pre-1990 data, peat products (UN commodity 1200), Eurostat (nrg_bal_c) cross-check, IEA.

### 7.6 Remaining gaps after the follow-up
- Refined zinc/lead/tin/copper world totals (DS140 has none); gallium primary world only 2020-2024 (MCS); thorium world only 1960-1977.
- DS140 ends 2019-2022 by commodity; 2021-2025 relies on OWID/MCS (splice risk noted above).
- Uranium price series; wood fuel pre-1961; household biomass for China; IEA residential data; fly-ash utilisation (ACAA); wind/PV technology splits; wells outside the US; the other earlier gaps in section 2.
- Slag workbook (ds140-iron-steel-slag-2021) staged but unused; `Employment`, `Net import reliance`, stocks and trade columns of DS140 not extracted.


## 8. Fixes after independent verification (25 Oct 2026)

### 8.1 World coal power share, burn and ash (recalibrated)
- Cause of the 81% (2020) / 84% (2023) bias: in `build_coal.py` the efficiency tuple was returned as (central, low, high) but consumed as (low, central, high), so the central efficiency was 0.85 of the US value (about 27%). Fixed.
- Calibration: world efficiency = US/UK proxy x k, with k = 1 to 1950, rising linearly to 1.05 in 2012 and 1.10 in 2023 (world fleets less efficient than the US only slightly once the ordering bug is removed). Anchors: 59% of world coal consumption in power in 2012 (EIA IEO coal chapter, energy basis, S0850) and 2023: IEA Coal 2024 gives 5,855 of 8,687 Mt = 67.4% by mass (S0849); because power-sector coal has a below-average calorific value the energy-basis anchor is taken as 0.65 (inference, +-0.04). Efficiency band +-10% after 1950, +-15% before. 2025 consumption (missing in OWID) extrapolated from 2024 by the production ratio.
- Result (central, 5-95% band): share 0.098 (1920), 0.163 (1950), 0.37 (1970), 0.50 (1990), 0.61 (2000), 0.59 (2012), 0.635 (0.57-0.71) in 2020, 0.65 (0.59-0.73) in 2023, 0.65 in 2025. Burn 26,900 TWh (2020), 29,500 TWh (2023). Ash from coal burned for power 584 Mt (2020), 640 Mt (2023); fly ash 467 Mt (2020), 512 Mt (2023). The ash and fly-ash bands remain wide (ash yield 0.08-0.16 and fly fraction assumed).
- Limits: only two anchors; the linear interpolation of k, and the assumption that the efficiency ratio to the US applies to the energy rather than mass share, are assumptions. The EIA IEO edition year (2016) is approximate.

### 8.2 Spent-fuel discharge
- GCR was split: UK units first connected 1976 or later are AGR (efficiency 0.38 = 600 MWe / 1560 MWth; discharge burnup 27 GWd/tHM, within 24-32 given for Hartlepool in arXiv:2301.07153, S0851); all other gas-graphite units are Magnox/UNGG type (efficiency 0.27, burnup 4 rising to 6). After the Magnox closures only AGR remains (GCR line 2020: about 180 tHM, was about 870). LWR burnup 2020 lowered from 50 to 48 GWd/tHM (TECDOC-1975: USA and most others above 45; Germany 50-65). PHWR left unchanged after review: natural-uranium CANDU at 7-7.5 GWd/tHM and net efficiency 0.30 gives about 2,700 tHM/a for about 145 TWh modelled PHWR output, which is consistent with Canadian bundle counts (about 1,600 tU/a) plus India, Korea and China.
- Result: 9,517 tHM in 2020 (6,660-12,370 band), 9,403 in 2015; components 2020: PWR 5,022, BWR 1,277, PHWR 2,678, AGR 182, LWGR 358. Cumulative to 2020 = 402,470 tHM (IAEA TECDOC-1975: over 400,000 tHM discharged to end-2020).
- Residual: +36% against the 7,000 tHM/a of TECDOC-1975 and of the IAEA/EC/NEA/WNA Status and Trends 3rd edition (data to end-2019; read via a NEI report, S0853). An IAEA web article (S0852) gives about 10,000 t/a for the same quantity, so IAEA's own annual figures differ by more than the model residual; the cumulative matches. The 7,000 tHM/a is inside the 5-95% band (lower bound 6,660). Not forced to 7,000: that would need LWR burnups of about 65 GWd/tHM or efficiencies far above 0.33.

### 8.3 Rare earths by country (Minerals Yearbooks)
- Seven yearbook tables parsed (S0854-S0860: MYB 1994, 1999, 2003, 2008, 2013, 2018 advance release, 2022): country rows in `prod_ree_oxide` for AUS, BDI, BRA, CHN, COD, IND, LKA, MDG, MMR, MYS, RUS (and SUN for 1990-91), THA, USA (gap years only; DS140 US kept where present), VNM, ZAF, covering 1990-2022 (plus OWID/MCS values to 2024 where they already existed). Later yearbook values override earlier ones; in the overlap years (1999, 2018) the figures were identical, so no revisions were found. XWL stays the DS140 world column (to 2020, then OWID/MCS).
- DS140 world differs from the yearbook totals as originally published: 1990 52,900 vs 60,100 (MYB 1994), 1999 86,600 vs 80,400 (MYB 1999)/81,600 (MYB 2003), because DS140 was revised and the yearbook totals include differently estimated producers; the country rows therefore need not sum to XWL.
- CIS/USSR: the 1992-2008 tables give one USSR/CIS figure (8,000 t in 1992, 2,000 t from 1995). It is booked to RUS with a band of +-40% and a note; Kazakhstan, Kyrgyzstan, Ukraine and Uzbekistan cannot be separated. Myanmar enters in 2014 (200 t) and reaches 35,500 t in 2020; Australia is large from 2014.
- Not reachable: China REE by year before 1990 (Bayan Obo), Australia and USSR before 1990, and US 1900-1989 beyond DS140. Files needed (from the mirror's catalogue): Minerals Yearbook rare-earth chapters for 1989 and earlier (USBM Minerals Yearbook Vol. I, "Rare-Earth Minerals and Metals"), if the mirror has them (its README says MYB coverage starts 1993), Mineral Industry Surveys on rare earths 1965-1993, and MYB rare-earth chapters 1995-1998, 2000-2002, 2004-2007, 2009-2012, 2014-2017, 2019-2021 to confirm revisions year by year. China REE by year from other sources: BGS World Mineral Statistics.

### 8.4 Bands, notes, seams, gap fills
- Every row's note now states that the band is analyst-assumed (approx. 5th-95th percentile), unless it is a zero-width band by definition (exact zeros or phi = 0 by rule), in which case the note says so. The 9,406 empty notes in `electricity_generation.csv` and 358 in `coal.csv` are filled (data source, units, bands). No zero-width band remains on a non-zero value (the 27 saturated phi_civil rows now carry a lower bound of 0.9, below).
- phi_civil: 1991-2011 and 2018-2023 are saturated (R_civil above U_prod beyond the bands). The value 1 is an upper bound under rule 3; the data give no lower bound (R minus P is secondary supply, not military use). Low bound set to 0.9, an analyst assumption (no weapons-purpose mining of new uranium after the Cold War); noted on each row. No 2025 row (section 2).
- Seams documented on the rows: tellurium 2022 to 2023 (+62%, USGS revision of Chinese output); REE 2020 to 2021 (+19%: DS140 243,000 to OWID/MCS 290,000; Minerals Yearbook 2022 gives 250,000 to 290,000, +16%, so about 3 points is source revision).
- Gaps filled: `prod_lead` XWL 1901-1905 and 1914-1918 and `prod_tellurium` XWL 2004-2012 by linear interpolation (basis interpolated; +-25% and +-40% bands; notes say why); `prod_molybdenum` XWL 2024 = 256,000 t from MCS 2026 (S0808). MCS tellurium chapters for 2005-2013 (mcs-YYYY-tellu in the mirror, if present) would replace the interpolation.

### 8.5 Reproducibility
- All builders are in `research/activity/scripts/` (see `research/activity/README.md`): lib.py, common.py, build_{elec,coal,og,u,nuc,cap,comm,prices,bio,peat}.py, ds140.py, ds140_comm.py, ree_myb.py, make_sources.py, make_sources2.py, eia_extract.py, irena_fetch.py, fetch_minerals.py, rds2_parse.py, redbook_u.py, fetch_inputs.py, run_all.py, plot_sanity.py. Paths are relative to the repository root; `--raw` and `--mirror` are arguments; nothing writes into `data/activity/` without `--write`.
- Small raw inputs (below 5 MB each, 27 MB in all) are in `research/activity/raw/`; large ones (OWID energy, FAOSTAT forestry, EIA INTL) are fetched by `fetch_inputs.py` and listed in `raw/.gitignore`. The note registry is `research/activity/note_registry.json` (append-only, 2,828 notes; readable copy `note_registry.csv`).
- Checked: `run_all.py` run twice (once with `--write`, once without) gives byte-identical files in `research/activity/out/` and `data/activity/` for all eleven CSVs and `sources_task19.csv`. The `out/` folder holds those check copies and can be deleted.

### 8.7 Coal activity defects fixed in `build_coal.py` (26-27 Oct 2026)
- Pre-1900 decadal gap: the world (XWL) series `coal_production_t`, `coal_consumption_t`, `coal_production_twh` and `coal_consumption_twh` had values only in 1800, 1810, ..., 1890 (no other country is decadal). The 1801-1899 non-decade years are now filled annually (90 rows per series, 360 rows), basis `interpolated`: log-linear (constant growth rate) interpolation of the central, low and high values between the two bracketing decadal points, which the note names; source ids are inherited from both brackets. The band is the interpolated decadal band, not widened. Decadal and 1900+ rows are untouched.
- Consumption 2025: both consumption series ended in 2024 (OWID and EIA have no 2025 consumption), so non-power coal had no 2025 rows. `coal_consumption_t` and `coal_consumption_twh` now carry 2024 forward to 2025 for all 33 countries with a 2024 row (66 rows), basis `extrapolated`: central = 2024 central; each band side is widened to sqrt(s_stat^2 + s_trend^2) in log space, s_stat the same-side log half-width of the 2024 band and s_trend the largest absolute year-on-year log change of the central value over 2015-2024. Production already had 2025 and is unchanged. Note that `coal_power_share` 2025 still uses the production-ratio extrapolation of 8.1 (unchanged).
- Inputs: `owid-energy.csv` and `eia_annual.json` were re-fetched with `fetch_inputs.py` on 27 Oct 2026; before the edits the unchanged builder reproduced the committed `coal.csv` and note registry byte-identically, and every pre-existing coal row is unchanged after the edits (426 rows added in total). `note_registry.json` gained two notes (the interpolation and carry-forward rules); `note_registry.csv` was rewritten from it. Only `coal.png` was regenerated (the other plot PNGs are not byte-reproducible and were left as committed).
- Reported, not fixed: CSK/CZE, SUN/successor and YUG/successor production series overlap (double counting if summed); the stream script handles exclusion.

### 8.8 Electricity generation: 2025 zero artefact and carry-forward (`build_elec.py`, 27 Oct 2026)
- Defect: `elec_gen_geothermal` XWL 2025 was written as 0 / 0 / 0, basis `measured`. IRENA 2025 is not yet published, and the world sum over countries with no data evaluated to 0. The world sum now exists only for years in which at least one country has data, so a no-data year is absent rather than zero. (The peat world sum was already guarded by `v>0`; country series skip missing years.)
- Carry-forward: every `elec_gen_*` series and country that ends in 2024 now has 2024 carried to 2025 by the coal rule (central = 2024 central; each band side widened to sqrt(s_stat^2 + s_trend^2) in log space, s_trend the largest absolute year-on-year log change of the central value over 2015-2024), basis `extrapolated`. 44 carry-forward rows (43 added; the geothermal XWL row replaced the zero): geothermal XWL and 26 countries (CHL, CHN, CRI, DEU, FRA, GLP, GTM, HND, HUN, IDN, ISL, ITA, JPN, KEN, MEX, NIC, NZL, PHL, PNG, PRT, RUS, SLV, THA, TUR, TWN, USA); peat XWL, EST, FIN, SWE; IDN (biomass, coal, gas, hydro, oil, solar, wind) and SAU (gas, oil, solar, wind, plus biomass and coal as zeros), whose OWID series stop in 2024. SAU biomass and coal are exactly zero in 2024 and are carried as zero-width zeros (note N2826). The geothermal XWL 2025 row was replaced (0 -> 97.68 TWh, 92.20 to 103.43). Small series carry very wide bands because s_trend is large (for example peat EST, s_trend 3.24); use with care.
- Other zero artefacts: none found. The remaining 2025 zeros in `electricity_generation.csv` (nuclear in countries without reactors, EGY biomass and coal, NOR and SWE coal, ZAF gas) are OWID/Ember source zeros. Zero 2025 rows in `capacity_additions.csv` are net IRENA capacity changes of zero, and the three in `coal.csv` (GBR power share, ESP production) are real zeros.

### 8.9 `prod_peat` world coverage break (`commodity_production.csv`)
- The world (XWL) `prod_peat` series drops from 170 Mt (1991) to 29 Mt (1992). This is a coverage break in USGS DS140, which no longer reports the USSR after 1991, not a change in production. Do not read it as a decline.
- No values were changed. The XWL rows for 1991 and 1992 carry a note (registry N2827, N2828) saying so. The series is not used as a driver by the other-energy stream.

### 8.6 Sanity plots
- `research/activity/plots/<file>.png`, one per data file (11), headline series with world (or USA, or the four peat countries) central line and shaded band: regenerate with `scripts/plot_sanity.py`.

## 9. Task 2.x series: nuclear cycle and oil and gas drivers (27 Oct 2026)

Builders `build_nuc2.py` (-> `data/activity/nuclear_cycle.csv`, 460 rows; 464 after section 10.2) and `build_og2.py` (-> `data/activity/oil_gas_drivers.csv`, 15,279 rows), inputs reduced by `fetch_task2x.py` into `raw/task2x/`, hand transcriptions in `task2x_data.py`, sources S1600-S1631 in `sources_task2x.csv` (already merged into `data/sources.csv`; corrected 2 Nov 2026, this sentence used to say they were not). Added to `run_all.py` after `build_peat`.

### 9.1 nuc_reprocessed_gwa (GWa, civil spent fuel reprocessed, electrical-energy equivalent)
- Rows: XWL 1950-2025 (76) and FRA 1966-2025, GBR 1994-2022, JPN 1977-2008, DEU 1971-90, BEL 1966-74 (by site country; site detail is in the notes). XWL is the sum of the country rows, errors in quadrature.
- FRA La Hague: 1971-97 UNSCEAR 2000 Table 40 (compiled; includes UNGG fuel at UP2), 1966-70 extrapolated at 0.9 GWa/a, 1998-2025 tHM x 0.33 x burnup/365.25 (burnup 33 GWd/t in 1998 rising to 45 in 2010 and 47 in 2025, assumed). tHM: IPFM RR4 Figure 6 bars to 2006 (pixel-read, total 22,584), 2007-21 evenly spread (1,065 tHM/a) from the Orano cumulative 41,236 tHM (end 2024), 2022 = 925, 2023 = 882 (cumulative difference), 2024 = 871, 2025 = 2024.
- GBR THORP (1994-2018), plus Sellafield B205 Magnox from 1995 (section 10.2): IPFM RR5 Figure 6 financial-year bars (read by eye), first ten years 5,045 tHM and lifetime 9,331 tHM as constraints, 0.030 GWa/tHM (AGR and LWR mix, assumed).
- JPN: Tokai 1977-97 UNSCEAR Table 40; Tokai 1998-2006 assumed 0.5 GWa/a in 2000-05 (band 0 to 3 times; JAEA's 1,052 tHM to March 2006 has no years); Rokkasho active tests 2006-08 at the CNIC planned 430 tHM (actuals not found). DEU WAK (about 200 tHM, spread evenly 1971-90) and BEL Eurochemic (181.5 tHM, 1966-74) are interpolated with wide bands.
- Excluded under D16 (undocumented civil share, flagged for Steve): Sellafield B205 Magnox before 1995 (the 1995-2022 throughput was added on 2 Nov 2026, section 10.2), Marcoule UP1, Mayak RT-1 (993 tHM in 2016-24, mixed fuel), West Valley (640 t, mixed), India, China pilot plant. Hence the series is far below UNSCEAR world totals before 1994 (UNSCEAR assumes 8% of generation, dominated by Magnox).
- Cross-check: mean 1998-2002 = 58.6 GWa/a (60.7 after the B205 addition of section 10.2) against the implied 62.6 (UNSCEAR 2008, all plants): 3% low, inside the bands; the shortfall is the excluded RT-1.
- UNSCEAR 2000 Table 40 Sellafield GWa for 1995-97 (6.9, 7.1, 6.8) look undercounted against the Kr-85 releases (100,000 TBq in 1996 is about 14-15 GWa at 6,900 TBq/GWa); not used.

### 9.2 nuc_sea_dumped_tbq (TBq, total activity at packaging)
- Rows: XWL 1946-2025 (zeros after 1982; 80 rows) and BEL, FRA, DEU, ITA, JPN, NLD, NZL, SWE, CHE, GBR (1949-82), USA (1946-70); 44,602 TBq in total (peak 1980). Transcribed per year from IAEA-TECDOC-1105 Annexes A.1-A.14; each country total reproduces the printed annex total (asserted in the builder; Japan within 0.1 GBq of rounding).
- USA: the annexes give site totals over date ranges only, so each is spread evenly over its period (basis interpolated, band -60%/+100%). The 1,221 TBq reactor shell of USS Seawolf (1959) is removed from the US Atlantic total (naval). The US waste came from AEC, Navy and contractor laboratories and its civil share is undocumented (flag for D16).
- Excluded and reported here: former Soviet Union and Russian Federation (Arctic: reactors with spent fuel 36,876 TBq, reactors without fuel 143, solid LLW 585, liquid LLW 764, FSU Arctic total 38,369; Pacific FSU 874 TBq as Sr-90 equivalent, Russian Federation 0.7 and 2.05), because the civil share is undocumented and most is naval. Not quantified in the source: Republic of Korea (115 containers 1968-72), UK archive operations (A.12-a, about 9.4 TBq).
- Factor note: the `sea_disposal` shares (data/factors/nuclear.csv) are Atlantic composition applied to the total of every country, including the Pacific US and Japanese dumps.

### 9.3 Oil and gas drivers
- `oil_sands_ore_processed_t` (CAN, 1967-2025, t): 2017-25 sum of the AER ST39 "Proc" rows (2024: 1,019.4 Mt, equals S0326); 1972-2016 mined bitumen (ST98-2015 Figure 6 bars to 2014, StatCan 25-10-0063-01 from 2016, 2015 interpolated) x 9.98 t ore per m3 (2017-25 mean, range 9.9-10.2); 1967-71 linear ramp (assumed). A first look at this ratio gave 5.0 because the StatCan Canada and Alberta rows had both been summed; only Alberta is used.
- `us_wells_drilled_horizontal` (1980-2025) and `us_wells_drilled_vertical` (1949-2025): EIA MER Table 5.2 reports horizontal and directional wells together; the horizontal part uses the Table 5.1 rig shares (1991+) or an interpolation to the 1990 anchor of about 2% of new wells, bands -50%/+50% before 2010. Vertical is the EIA vertical-trajectory count (the all-wells total before 1976). No world well count was found.
- `gas_flared_m3`: GGFR 2012-25 satellite estimates for 104 economies (the 2012-2025 workbook revises the June 2024 report) and XWL; XWL 1950-2011 is the Global Carbon Project flaring CO2 x 388 m3/t (2012-23 overlap), bands +40%/-30% before 1994 and +30%/-15% from 1994 (2005 gives 135 bcm against Elvidge's 172; 2010 gives 132 against 134). `gas_flared_reported_m3` (EIA, 1980-2017, 219 countries and XWL) is a different, reported basis that differs from GGFR by factors of 0.2 to 3; it is not stitched to the satellite series.
- `ngl_production_m3`: EIA INTL 58-1 by country from 1980 and XWL; USA 1949-2025 from MER Table 3.1; XWL 1950-79 = US plus rest-of-world gas energy x the 1980-84 ratio (12,056 m3/TWh), band -40%/+40% on the rest-of-world part.
- `unit_value_{oil,gas,ngl}_usd_per_m3` (D6 allocation; nominal US dollars per m3, a documented non-SI currency exception like USD/t): oil = OWID world crude price (XWL) and EIA first purchase price (USA); gas = US wellhead price (to 2012, then Henry Hub x 2005-12 ratio) used as the world proxy with band x0.5-x3 (no world series before 1989); NGL = 0.7 x Mont Belvieu propane (1992+, assumed basket factor) and before 1992 0.7 x the 1992-2025 propane/crude ratio (0.622) x crude, band x0.45-x1.6.

### 9.4 Produced-water world series (`build_og.py`, `oil_gas.csv`)
- Defect: XWL `produced_water_m3` was below USA before about 1970 (1950: XWL 5.8e8 m3, USA 1.5e9), so rest of world = XWL - USA was negative. Rule now: XWL = USA + ROW with ROW >= 0 at every bound, ROW = (world crude volume - USA crude volume) x a water/oil ratio rising linearly from 1.0 (1950) to the 2010 value 2.47 (the ratio at which the 2010 world value of 3.0 x world oil volume is met); from 2010 unchanged. Only the 76 pre-2010 XWL rows changed (central 1950 5.8e8 to 1.8e9; 1960 1.6e9 to 3.3e9; 1970 4.4e9 to 7.2e9; 1980 6.9e9 to 9.3e9; 1990 8.2e9 to 10.1e9; 2000 10.3e9 to 11.3e9; 2009 12.6e9 to 12.8e9 m3). The USA series is unchanged and may be high before 1985 (not changed).

### 9.5 Gaps
- No world wells-drilled count; no annual La Hague tHM for 2007-21 (Orano 2017 and 2019 editions not retrievable); THORP and Magnox charts are read by eye; Rokkasho and Tokai-after-1997 quantities are not published in the sources read; no world gas price before 1989 and no NGL price series before 1992; `us_wells_drilled_total` in `oil_gas.csv` still ends in 2010 (EIA Table 5.2 OGTWPUS continues to 2025).

## 10. Nuclear stream inputs (NUCLEAR_SPEC section 12 items A1, A2; D64; 2 Nov 2026)

### 10.1 A1: 2024 to 2025 carry-forward (`build_u.py`, `build_nuc.py`, helper `carry_2025` in `common.py`)
- Series: `u_production` (every country with a 2024 row: AUS, CAN, CHN, IND, KAZ, NAM, NER, RUS, UKR, USA, UZB, ZAF, plus XWL; 13 rows), `phi_civil` (XWL), `nuc_gen_<t>` and `nuc_cap_<t>` for t in pwr, bwr, phwr, gcr, lwgr, fbr (XWL; 12 rows). Basis `extrapolated`; 14 + 12 new rows. Not extended (not used by the nuclear stream): `nuc_cap_total`, `nuc_cap_htgr`, `nuc_cap_other`, `nuc_gen_htgr`, `nuc_spent_fuel_discharged_thm`, `u_requirements_civil`; `nuc_gen_other` ended in 2003.
- Rule: exactly that of `build_coal.py` and `build_elec.py` (central = 2024 central; each band side widened to sqrt(s_stat^2 + s_trend^2) in log space, s_trend the largest absolute year-on-year log change of the central value over 2015-2024); the long note is the same registry entry (N2825). One addition: where the 2024 high bound equals the central value (phi_civil, a fraction capped at 1) the high side stays at the central value and only the low side is widened; the row note says so. For `phi_civil` s_trend is 0 (flat at 1 since 1991), so the 2025 band equals 2024 (0.977 to 1).
- Large s_trend values follow from the rule, not from judgement: USA 2.62 and UKR 1.52 (production restarts after near-zero years), CAN 0.63, NER 0.58, so the 2025 country bands are very wide (USA by a factor of e^2.6 each way). XWL u_production s_trend 0.137.
- Existing rows are byte-identical; only 2025 rows were added (uranium.csv +14, nuclear.csv +12).

### 10.2 A2: Sellafield B205 (Magnox) civil throughput in `nuc_reprocessed_gwa` (`build_nuc2.py`, inputs in `task2y_data.py`)
- Scope (D64): B205 counts as civil from calendar 1995 (military feed ended with the 1995 decision); 1964-94 stays excluded. From 1995 the whole throughput is treated as civil, a limit (Calder Hall and Chapelcross fuel was military where still reprocessed). GBR rows now run 1994-2022 (1994 THORP only; 2019-22 B205 only); XWL recomputed as the country sum for 1995-2022.
- tHM by financial year (FY ends 31 March; calendar year = 0.75 x FY(y+1) + 0.25 x FY(y), as THORP; 2022 = 0.25 x FY2022 + the April to 17 July 2022 stub): FY1997-2000 604, 523, 467, 503 (IPFM RR5 Figure 4, S0130, bar tops measured; the bars labelled 2001-07 reproduce the NDA FY2000/01-2006/07 values, so labels are FY ending years); FY2001-2012 364, 787, 765, 1,040, 1,013, 256, 593, 458, 512, 449, 233, 607 (NDA MOP 9 Figure 4.1, S1700; 233 and 607 printed, the rest chart readings, +-10 t); FY2013 261 (by difference: S1701 1,338 t over 2011/12-2013/14 less 607 and 470); FY2014 470 (S1702); FY2017 466 (S1703); FY2019 341.5 (S1704).
- No annual figure found for FY2015, FY2016, FY2018, FY2020-22: they share equally the 2,261.5 tU left of the 3,800 tU still to reprocess in April 2012 (S1700) after the documented years, 359 tHM per full year and a 3.5-month stub (last feed 17 July 2022, S1609) of 105 tHM; band +-30%. FY1995 and FY1996 have no annual figure found: FY1997 (604 tHM) is carried with a band of -50%/+100% (basis `extrapolated`; RR5 says early throughput regularly exceeded 1,000 tHM/a). These two years (calendar 1995 and 1996) are the weakest values and can be dropped or replaced if a BNFL annual-report figure is found.
- Conversion: 0.27 x 5 GWd/tHM / 365.25 = 0.0037 GWa per tHM (Magnox burnup about 5 GWd/tHM; efficiency 0.27 as the spent-fuel model in `build_nuc.py`, which uses burnup 5.5-6; both assumed, conversion band +-20%, combined in quadrature with the throughput band).
- Result: calendar-year B205 throughput 604 (1995), 604 (1996), 399 (2000), 445 (2005), 287 (2010), 359 (2015-16 and 2020), 195 (2022) tHM; 13,729 tHM over 1995-2022 against the lifetime 54,920 tHM (S1609), so about 41,000 tHM before 1995 (RR5 says about 47,000 tHM by about 2006, consistent). GBR 1995 7.0 (5.1-9.5) GWa, 1996 13.0, 2019 1.3, 2022 0.72 GWa; XWL 1998-2002 mean 60.7 GWa/a (was 58.6).
- Sources: S1700-S1704 in `sources_task2y.csv` (`make_sources_task2y.py`, merged into `data/sources.csv` (2026-11-02); the validator reports no issues, without them only T04 for these five IDs). The 2018/19 Sellafield metric includes Dounreay Fast Reactor material, so FY2019 may slightly overstate Magnox fuel; the 2017/18 review gives 188 teU of decanning, which is a different metric and is not used.

## 11. Other-energy stream inputs (OTHER_SPEC; D70; 4 Nov 2026)

### 11.1 2024 to 2025 carry-forward for wood, charcoal and peat (`build_bio.py`, `build_peat.py`, helper `carry_2025` in `common.py`)
- Series: `wood_fuel_m3`, `wood_fuel_t`, `wood_fuel_energy_twh`, `charcoal_production_t` (every country with a 2024 row, plus XWL; 800 rows in `biomass.csv`) and `peat_production_t`, `peat_production_twh`, `peat_supply_t`, `peat_supply_twh`, `peat_household_t`, `peat_power_heat_t` (47 rows in `peat.csv`). Basis `extrapolated`.
- Rule: exactly that of `build_coal.py`, `build_elec.py`, `build_u.py` and `build_nuc.py` (section 10.1); the long note is the same registry entry (N2825). Exact-zero 2024 values (for example charcoal in FIN and IRL) are carried as exact zeros with the existing zero-width note (N2826).
- Not carried: the UNSD household series (`household_fuelwood_*`, `household_charcoal_*`) end in 2023 and have no 2024 row to carry.
- Examples (central; 2025): XWL wood fuel 1.949e9 m3, 1.413e9 t, 5,089 TWh; XWL charcoal 5.94e7 t; CHN wood fuel 1.457e8 m3, charcoal 2.42e6 t; IND wood fuel 2.97e8 m3; FIN peat production 1.009e6 t.
- Existing rows are byte-identical (checked row by row; order kept); only 2025 rows were added. `note_registry.json` gained no notes (the carry-forward notes already existed), so `note_registry.csv` is unchanged. Plot PNGs were not regenerated.
