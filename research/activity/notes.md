# Task 1.9 activity data spine: notes

Files: `data/activity/{electricity_generation,coal,oil_gas,uranium,nuclear,commodity_production,commodity_prices,capacity_additions,planning_parameters,biomass,peat}.csv` (172,582 rows, 215 series). Sources S0800-S0848 (all rows, old and new) in `research/activity/sources_task19.csv`. Long notes are abbreviated in the CSVs as `[Nxxx, see research/activity/note_registry.csv]`. Converters kept here (paths inside point to the scratch folder; edit before reuse): `ds140.py` (DS140 CSV sheet loader), `ds140_comm.py` (DS140 to commodity series), `build_prices.py`, `build_bio.py`, `build_peat.py`, `make_sources2.py`, `rds2_parse.py` (RDS-2 reactor table to fleet by type and year) and `redbook_u.py` (hand-transcribed Red Book uranium production table, column sums checked against printed totals).

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
| coal.csv | coal_consumption_t | t | 1800-2024 | 33 | 1800-2024 | 1995 |
| coal.csv | coal_consumption_twh | TWh | 1800-2024 | 33 | 1800-2024 | 1995 |
| coal.csv | coal_fly_ash_t | t | 1900-2025 | 1 | 1900-2025 | 126 |
| coal.csv | coal_power_share | 1 | 1900-2025 | 3 | 1900-2025 | 313 |
| coal.csv | coal_production_t | t | 1800-2025 | 39 | 1800-2025 | 4468 |
| coal.csv | coal_production_twh | TWh | 1800-2025 | 39 | 1800-2025 | 4468 |
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
| commodity_production.csv | prod_lead | t | 1900-2025 | 74 | 1900-2025 | 2511 |
| commodity_production.csv | prod_lead_primary | t | - | 1 | 1900-2021 | 122 |
| commodity_production.csv | prod_lead_refined | t | - | 96 | 1970-2023 | 3139 |
| commodity_production.csv | prod_molybdenum | t | 1900-2025 | 27 | 1900-2025 | 884 |
| commodity_production.csv | prod_nickel | t | 1900-2025 | 10 | 1900-2025 | 278 |
| commodity_production.csv | prod_nickel_plant | t | 1970-2019 | 1 | 1970-2019 | 50 |
| commodity_production.csv | prod_nickel_processing | t | 1977-2023 | 39 | 1977-2023 | 1194 |
| commodity_production.csv | prod_peat | t | 1935-2021 | 2 | 1904-2021 | 197 |
| commodity_production.csv | prod_phosphate_rock | t | 1900-2022 | 2 | 1900-2022 | 246 |
| commodity_production.csv | prod_pig_iron | t | 1910-2024 | 17 | 1900-2024 | 313 |
| commodity_production.csv | prod_ree_oxide | t | 1900-2025 | 18 | 1900-2025 | 279 |
| commodity_production.csv | prod_selenium | t | 1938-2024 | 16 | 1938-2024 | 152 |
| commodity_production.csv | prod_selenium_primary | t | - | 1 | 1900-1996 | 88 |
| commodity_production.csv | prod_silicon_mg | t | 1964-2022 | 14 | 1954-2022 | 161 |
| commodity_production.csv | prod_silver | t | 1900-2025 | 93 | 1900-2025 | 3485 |
| commodity_production.csv | prod_steel | t | 1943-2024 | 109 | 1900-2024 | 4357 |
| commodity_production.csv | prod_tellurium | t | 1930-2025 | 2 | 1926-2025 | 134 |
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
- Caveats: China reports no household fuelwood to UNSD (so the world sum omits its household use); India's UN household fuelwood (3.8e8 m3 in 2023) exceeds FAO's national wood fuel production (3.0e8 m3), so the two sources are not mutually consistent (UN likely includes non-roundwood fuelwood such as branches and residues); FAO wood fuel includes the roundwood converted to charcoal, so do not add charcoal to wood fuel. FAO values for most developing countries are estimated (flag E). Pre-1961 not covered; no compilation was found.

### 7.5 Peat by country: `peat.csv`
- UN Energy Statistics commodity 1100 Peat (S0847): `peat_production_t`/`_twh`, `peat_supply_t`/`_twh` (total energy supply, a proxy for energy use), `peat_household_t`, `peat_power_heat_t` (electricity and CHP transformation), 1990-2024, 29 countries. All six requested countries are covered: Finland and Ireland and Sweden from 1990; Belarus, Russia and Estonia from 1992. Examples (peat supply): Finland about 27 TWh (2010), 7 TWh (2023); Ireland about 15 TWh (1990), 3 TWh (2023); Belarus about 6 TWh (2023); Russia about 2.5 TWh (2023); Sweden 0.3 TWh (2023); Estonia 0.07 TWh (2023). Finland and Ireland 1990 values match the national statistics I know of (about 25 and 16 TWh) but I did not check them against a primary source.
- Energy uses UN's country conversion factors (8.1-13 GJ/t); this is peat for fuel and excludes horticultural peat. DS140 peat (`prod_peat`, world 1935-2021) is all peat including horticulture.
- Not obtained: pre-1990 data, peat products (UN commodity 1200), Eurostat (nrg_bal_c) cross-check, IEA.

### 7.6 Remaining gaps after the follow-up
- Refined zinc/lead/tin/copper world totals (DS140 has none); gallium primary world only 2020-2024 (MCS); thorium world only 1960-1977.
- DS140 ends 2019-2022 by commodity; 2021-2025 relies on OWID/MCS (splice risk noted above).
- Uranium price series; wood fuel pre-1961; household biomass for China; IEA residential data; fly-ash utilisation (ACAA); wind/PV technology splits; wells outside the US; the other earlier gaps in section 2.
- Slag workbook (ds140-iron-steel-slag-2021) staged but unused; `Employment`, `Net import reliance`, stocks and trade columns of DS140 not extracted.
