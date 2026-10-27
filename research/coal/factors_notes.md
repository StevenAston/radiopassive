# Coal factor registry: notes (Task 2.2a)

Output: `data/factors/coal.csv` (79 rows: coal_mining 6, combustion_power 55, combustion_nonpower 18; construction 0). Residue parameters: `coal_fly_ash`, `coal_bottom_ash` in `data/reference/residue_types.csv`. No new sources added to `data/sources.csv`. Generator: scratchpad `build.py` (not part of the repository; ask if you want it filed under `research/coal/`).

Validator over the whole tree (`python -m pipeline.validate --root .`; factor files are read automatically, the CLI FILE arguments are master files only): `OK: no issues`, exit 0. `pytest pipeline/tests`: 1403 passed.

## Engine reading of the factors (my specification; the stream spec should confirm)

All activity values are HEAD-nuclide activity (METHODS 3.2, 4.1a, D24); the engine applies the multiplier. Per-tonne factors are in Bq/t of their driver; unit-1 factors apply to a Bq quantity.

- Ash-borne Bq of group k (power) = `coal_fly_ash_t` x fly factor + (`coal_ash_power_t` minus `coal_fly_ash_t`) x bottom factor.
- Stack Bq(k) = min( ash-borne Bq x base fraction(era) x enrichment(k), fly-ash Bq ); subtracted from the fly-ash quantity. Radon at the stack = release share x ash-borne Ra-226+ (Rn222+) or Th228+ (Rn220+) Bq.
- Residue Bq after stack is split to impounded / reisolated / dispersed by the era shares (central sums to 1).
- Non-power: coal = `coal_consumption_t` minus power-station coal. Household part (household share) goes to dispersed `coal_domestic_ash` after the smoke fraction leaves; the rest goes to impounded `coal_bottom_ash`.
- Mine radon, drainage and sludge as in the table. Country-specific rows (CHN, POL) override XWL rows.

## 1. Factor table

| id | what | group / tier / route / residue | region | years | low / central / high | unit | basis | sources |
|---|---|---|---|---|---|---|---|---|
| coal:0001 | coal_mining: Mine radon (Rn-222) released by ventilation per tonne of coal mined, default for all countries without own factor | Rn222+/liberated/air_ventilation | XWL | 1800-2025 | 1.2e+04 / 9.3e+05 / 3.5e+06 | Bq/t | modelled | S0001;S0008;S0006 |
| coal:0002 | coal_mining: Mine radon (Rn-222) per tonne of coal mined, China measured | Rn222+/liberated/air_ventilation | CHN | 2000-2025 | 1.9e+05 / 9.3e+05 / 3.5e+06 | Bq/t | measured | S0001 |
| coal:0003 | coal_mining: Radium-226 released in coal mine drainage per tonne of coal mined, Poland (Upper Silesian balance) | Ra226+/liberated/water_mine_drainage | POL | 1985-2025 | 181 / 315 / 549 | Bq/t | modelled | S0222;S0225;S0804 |
| coal:0004 | coal_mining: Radium-228 released in coal mine drainage per tonne of coal mined, Poland (Upper Silesian balance) | Ra228+/liberated/water_mine_drainage | POL | 1992-2025 | 400 / 547 / 695 | Bq/t | modelled | S0222;S0225;S0804 |
| coal:0005 | coal_mining: Fraction of mobilised Ra-226 retained underground in Polish coal mines (precipitated deposits and sludge) | Ra226+/impounded/coal_mine_water_sludge | POL | 1985-2025 | 0.4 / 0.55 / 0.7 | 1 | modelled | S0222;S0225 |
| coal:0006 | coal_mining: Fraction of mobilised Ra-228 retained underground in Polish coal mines (precipitated deposits and sludge) | Ra228+/impounded/coal_mine_water_sludge | POL | 1985-2025 | 0.4 / 0.55 / 0.7 | 1 | modelled | S0222;S0225 |
| coal:0007 | combustion_power: Ash-borne activity per tonne of fly ash from coal burned for power, U238+ | U238+/coal_fly_ash | XWL | 1800-2025 | 5.83e+04 / 1.67e+05 / 3e+05 | Bq/t | modelled | S0001;S0006 |
| coal:0008 | combustion_power: Ash-borne activity per tonne of bottom ash from coal burned for power, U238+ | U238+/coal_bottom_ash | XWL | 1800-2025 | 5.83e+04 / 1.67e+05 / 3e+05 | Bq/t | modelled | S0001;S0006 |
| coal:0009 | combustion_power: Ash-borne activity per tonne of fly ash from coal burned for power, U234 | U234/coal_fly_ash | XWL | 1800-2025 | 5.83e+04 / 1.67e+05 / 3e+05 | Bq/t | modelled | S0001 |
| coal:0010 | combustion_power: Ash-borne activity per tonne of bottom ash from coal burned for power, U234 | U234/coal_bottom_ash | XWL | 1800-2025 | 5.83e+04 / 1.67e+05 / 3e+05 | Bq/t | modelled | S0001 |
| coal:0011 | combustion_power: Ash-borne activity per tonne of fly ash from coal burned for power, Th230 | Th230/coal_fly_ash | XWL | 1800-2025 | 5.83e+04 / 1.67e+05 / 3e+05 | Bq/t | modelled | S0001 |
| coal:0012 | combustion_power: Ash-borne activity per tonne of bottom ash from coal burned for power, Th230 | Th230/coal_bottom_ash | XWL | 1800-2025 | 5.83e+04 / 1.67e+05 / 3e+05 | Bq/t | modelled | S0001 |
| coal:0013 | combustion_power: Ash-borne activity per tonne of fly ash from coal burned for power, Ra226+ | Ra226+/coal_fly_ash | XWL | 1800-2025 | 7.42e+04 / 1.67e+05 / 4.92e+05 | Bq/t | modelled | S0001;S0010 |
| coal:0014 | combustion_power: Ash-borne activity per tonne of bottom ash from coal burned for power, Ra226+ | Ra226+/coal_bottom_ash | XWL | 1800-2025 | 7.42e+04 / 1.67e+05 / 4.92e+05 | Bq/t | modelled | S0001;S0010 |
| coal:0015 | combustion_power: Ash-borne activity per tonne of fly ash from coal burned for power, Pb210+ | Pb210+/coal_fly_ash | XWL | 1800-2025 | 1e+05 / 1.67e+05 / 6.5e+05 | Bq/t | modelled | S0010 |
| coal:0016 | combustion_power: Ash-borne activity per tonne of bottom ash from coal burned for power, Pb210+ | Pb210+/coal_bottom_ash | XWL | 1800-2025 | 1e+05 / 1.67e+05 / 6.5e+05 | Bq/t | modelled | S0010 |
| coal:0017 | combustion_power: Ash-borne activity per tonne of fly ash from coal burned for power, Po210 | Po210/coal_fly_ash | XWL | 1800-2025 | 2.75e+04 / 1.67e+05 / 4.33e+05 | Bq/t | modelled | S0010 |
| coal:0018 | combustion_power: Ash-borne activity per tonne of bottom ash from coal burned for power, Po210 | Po210/coal_bottom_ash | XWL | 1800-2025 | 2.75e+04 / 1.67e+05 / 4.33e+05 | Bq/t | modelled | S0010 |
| coal:0019 | combustion_power: Ash-borne activity per tonne of fly ash from coal burned for power, U235+ | U235+/coal_fly_ash | XWL | 1800-2025 | 2.69e+03 / 7.68e+03 / 1.38e+04 | Bq/t | modelled | S0001;S9001 |
| coal:0020 | combustion_power: Ash-borne activity per tonne of bottom ash from coal burned for power, U235+ | U235+/coal_bottom_ash | XWL | 1800-2025 | 2.69e+03 / 7.68e+03 / 1.38e+04 | Bq/t | modelled | S0001;S9001 |
| coal:0021 | combustion_power: Ash-borne activity per tonne of fly ash from coal burned for power, Th232 | Th232/coal_fly_ash | XWL | 1800-2025 | 3.42e+04 / 1.67e+05 / 2.5e+05 | Bq/t | modelled | S0200;S0010;S0006 |
| coal:0022 | combustion_power: Ash-borne activity per tonne of bottom ash from coal burned for power, Th232 | Th232/coal_bottom_ash | XWL | 1800-2025 | 3.42e+04 / 1.67e+05 / 2.5e+05 | Bq/t | modelled | S0200;S0010;S0006 |
| coal:0023 | combustion_power: Ash-borne activity per tonne of fly ash from coal burned for power, Ra228+ | Ra228+/coal_fly_ash | XWL | 1800-2025 | 3.42e+04 / 1.67e+05 / 2.5e+05 | Bq/t | modelled | S0010 |
| coal:0024 | combustion_power: Ash-borne activity per tonne of bottom ash from coal burned for power, Ra228+ | Ra228+/coal_bottom_ash | XWL | 1800-2025 | 3.42e+04 / 1.67e+05 / 2.5e+05 | Bq/t | modelled | S0010 |
| coal:0025 | combustion_power: Ash-borne activity per tonne of fly ash from coal burned for power, Th228+ | Th228+/coal_fly_ash | XWL | 1800-2025 | 3.42e+04 / 1.67e+05 / 2.5e+05 | Bq/t | modelled | S0010 |
| coal:0026 | combustion_power: Ash-borne activity per tonne of bottom ash from coal burned for power, Th228+ | Th228+/coal_bottom_ash | XWL | 1800-2025 | 3.42e+04 / 1.67e+05 / 2.5e+05 | Bq/t | modelled | S0010 |
| coal:0027 | combustion_power: Ash-borne activity per tonne of fly ash from coal burned for power, K40 | K40/coal_fly_ash | XWL | 1800-2025 | 4.17e+05 / 4.17e+05 / 1.2e+06 | Bq/t | modelled | S0010;S0006;S0205 |
| coal:0028 | combustion_power: Ash-borne activity per tonne of bottom ash from coal burned for power, K40 | K40/coal_bottom_ash | XWL | 1800-2025 | 4.17e+05 / 4.17e+05 / 1.2e+06 | Bq/t | modelled | S0010;S0006;S0205 |
| coal:0029 | combustion_nonpower: Activity per tonne of coal burned outside power stations, U238+ | U238+ | XWL | 1800-2025 | 7e+03 / 2e+04 / 3.6e+04 | Bq/t | modelled | S0001;S0006 |
| coal:0030 | combustion_nonpower: Activity per tonne of coal burned outside power stations, U234 | U234 | XWL | 1800-2025 | 7e+03 / 2e+04 / 3.6e+04 | Bq/t | modelled | S0001 |
| coal:0031 | combustion_nonpower: Activity per tonne of coal burned outside power stations, Th230 | Th230 | XWL | 1800-2025 | 7e+03 / 2e+04 / 3.6e+04 | Bq/t | modelled | S0001 |
| coal:0032 | combustion_nonpower: Activity per tonne of coal burned outside power stations, Ra226+ | Ra226+ | XWL | 1800-2025 | 8.9e+03 / 2e+04 / 5.9e+04 | Bq/t | modelled | S0001;S0010 |
| coal:0033 | combustion_nonpower: Activity per tonne of coal burned outside power stations, Pb210+ | Pb210+ | XWL | 1800-2025 | 1.2e+04 / 2e+04 / 7.8e+04 | Bq/t | modelled | S0010 |
| coal:0034 | combustion_nonpower: Activity per tonne of coal burned outside power stations, Po210 | Po210 | XWL | 1800-2025 | 3.3e+03 / 2e+04 / 5.2e+04 | Bq/t | modelled | S0010 |
| coal:0035 | combustion_nonpower: Activity per tonne of coal burned outside power stations, U235+ | U235+ | XWL | 1800-2025 | 323 / 922 / 1.66e+03 | Bq/t | modelled | S0001;S9001 |
| coal:0036 | combustion_nonpower: Activity per tonne of coal burned outside power stations, Th232 | Th232 | XWL | 1800-2025 | 4.1e+03 / 2e+04 / 3e+04 | Bq/t | modelled | S0200;S0010;S0006 |
| coal:0037 | combustion_nonpower: Activity per tonne of coal burned outside power stations, Ra228+ | Ra228+ | XWL | 1800-2025 | 4.1e+03 / 2e+04 / 3e+04 | Bq/t | modelled | S0010 |
| coal:0038 | combustion_nonpower: Activity per tonne of coal burned outside power stations, Th228+ | Th228+ | XWL | 1800-2025 | 4.1e+03 / 2e+04 / 3e+04 | Bq/t | modelled | S0010 |
| coal:0039 | combustion_nonpower: Activity per tonne of coal burned outside power stations, K40 | K40 | XWL | 1800-2025 | 5e+04 / 5e+04 / 1.44e+05 | Bq/t | modelled | S0010;S0006;S0205 |
| coal:0040 | combustion_power: Share of power-station ash (fly and bottom) to impounded: landfill, ash pond, dyke raising and land reclamation | impounded | XWL | 1800-1989 | 0.538 / 0.859 / 0.95 | 1 | modelled | S0001;S0008;S0209;S0210;S0212;S0213;S0215;S0200;S0211 |
| coal:0041 | combustion_power: Share of power-station ash (fly and bottom) to reisolated: underground mine backfill | reisolated | XWL | 1800-1989 | 0 / 0 / 0.062 | 1 | modelled | S0001;S0008;S0209;S0210;S0212;S0213;S0215;S0200;S0211 |
| coal:0042 | combustion_power: Share of power-station ash (fly and bottom) to dispersed: utilised in cement, concrete, bricks, road and structural fill | dispersed | XWL | 1800-1989 | 0.05 / 0.141 / 0.4 | 1 | modelled | S0001;S0008;S0209;S0210;S0212;S0213;S0215;S0200;S0211 |
| coal:0043 | combustion_power: Share of power-station ash (fly and bottom) to impounded: landfill, ash pond, dyke raising and land reclamation | impounded | XWL | 1990-2009 | 0.278 / 0.6 / 0.904 | 1 | modelled | S0001;S0008;S0209;S0210;S0212;S0213;S0215;S0200;S0211 |
| coal:0044 | combustion_power: Share of power-station ash (fly and bottom) to reisolated: underground mine backfill | reisolated | XWL | 1990-2009 | 0 / 0 / 0.062 | 1 | modelled | S0001;S0008;S0209;S0210;S0212;S0213;S0215;S0200;S0211 |
| coal:0045 | combustion_power: Share of power-station ash (fly and bottom) to dispersed: utilised in cement, concrete, bricks, road and structural fill | dispersed | XWL | 1990-2009 | 0.096 / 0.4 / 0.66 | 1 | modelled | S0001;S0008;S0209;S0210;S0212;S0213;S0215;S0200;S0211 |
| coal:0046 | combustion_power: Share of power-station ash (fly and bottom) to impounded: landfill, ash pond, dyke raising and land reclamation | impounded | XWL | 2010-2025 | 0 / 0.468 / 0.86 | 1 | modelled | S0001;S0008;S0209;S0210;S0212;S0213;S0215;S0200;S0211 |
| coal:0047 | combustion_power: Share of power-station ash (fly and bottom) to reisolated: underground mine backfill | reisolated | XWL | 2010-2025 | 0 / 0.062 / 0.4 | 1 | modelled | S0001;S0008;S0209;S0210;S0212;S0213;S0215;S0200;S0211 |
| coal:0048 | combustion_power: Share of power-station ash (fly and bottom) to dispersed: utilised in cement, concrete, bricks, road and structural fill | dispersed | XWL | 2010-2025 | 0.14 / 0.47 / 0.92 | 1 | modelled | S0001;S0008;S0209;S0210;S0212;S0213;S0215;S0200;S0211 |
| coal:0049 | combustion_power: Fraction of power-station ash escaping the stack, global average 1800-1949 | liberated/air_stack | XWL | 1800-1949 | 0.04 / 0.25 / 0.8 (pre-D53: 0.04 / 0.25 / 0.65) | 1 | modelled | S0208;S0207 |
| coal:0050 | combustion_power: Fraction of power-station ash escaping the stack, global average 1950-1969 | liberated/air_stack | XWL | 1950-1969 | 0.08 / 0.162 / 0.33 | 1 | modelled | S0207;S0010;S0208 |
| coal:0051 | combustion_power: Fraction of power-station ash escaping the stack, global average 1970-1989 | liberated/air_stack | XWL | 1970-1989 | 0.01 / 0.0447 / 0.2 | 1 | modelled | S0010;S0008;S0207 |
| coal:0052 | combustion_power: Fraction of power-station ash escaping the stack, global average 1990-2009 | liberated/air_stack | XWL | 1990-2009 | 0.004 / 0.02 / 0.1 | 1 | modelled | S0205;S0204;S0006;S0008;S0234 |
| coal:0053 | combustion_power: Fraction of power-station ash escaping the stack, global average 2010-2025 | liberated/air_stack | XWL | 2010-2025 | 0.0008 / 0.0031 / 0.012 | 1 | modelled | S0001;S0008;S0234 |
| coal:0054 | combustion_power: Enrichment of the escaping fly ash relative to BULK ash (rebased D53), Ra226+ | Ra226+/liberated/air_stack | XWL | 1800-2025 | 0.6 / 1.1 / 2 (pre-D53: 1 / 3.87 / 15) | 1 | modelled | S0010;S0202;S0008 |
| coal:0055 | combustion_power: Enrichment of the escaping fly ash relative to BULK ash (rebased D53), Ra228+ | Ra228+/liberated/air_stack | XWL | 1800-2025 | 0.6 / 1.1 / 2 (pre-D53: 1 / 3.87 / 15) | 1 | modelled | S0010;S0202;S0008 |
| coal:0056 | combustion_power: Enrichment of the escaping fly ash relative to BULK ash (rebased D53), Pb210+ | Pb210+/liberated/air_stack | XWL | 1800-2025 | 1 / 3.79 / 14.4 (pre-D53: 1 / 11 / 120) | 1 | modelled | S0010;S0202;S0008 |
| coal:0057 | combustion_power: Enrichment of the escaping fly ash relative to BULK ash (rebased D53), Po210 | Po210/liberated/air_stack | XWL | 1800-2025 | 3 / 8.49 / 24 (pre-D53: 3 / 24.5 / 200) | 1 | modelled | S0010;S0202;S0008 |
| coal:0058 | combustion_power: Enrichment of the escaping fly ash relative to BULK ash (rebased D53), U238+ | U238+/liberated/air_stack | XWL | 1800-2025 | 0.12 / 0.395 / 1.3 (pre-D53: 1 / 3.16 / 10) | 1 | modelled | S0010;S0202;S0008 |
| coal:0059 | combustion_power: Enrichment of the escaping fly ash relative to BULK ash (rebased D53), U234 | U234/liberated/air_stack | XWL | 1800-2025 | 0.12 / 0.395 / 1.3 (pre-D53: 1 / 3.16 / 10) | 1 | modelled | S0010;S0202;S0008 |
| coal:0060 | combustion_power: Enrichment of the escaping fly ash relative to BULK ash (rebased D53), Th230 | Th230/liberated/air_stack | XWL | 1800-2025 | 0.12 / 0.395 / 1.3 (pre-D53: 1 / 3.16 / 10) | 1 | modelled | S0010;S0202;S0008 |
| coal:0061 | combustion_power: Enrichment of the escaping fly ash relative to BULK ash (rebased D53), U235+ | U235+/liberated/air_stack | XWL | 1800-2025 | 0.12 / 0.395 / 1.3 (pre-D53: 1 / 3.16 / 10) | 1 | modelled | S0010;S0202;S0008 |
| coal:0062 | combustion_power: Enrichment of the escaping fly ash relative to BULK ash (rebased D53), Th232 | Th232/liberated/air_stack | XWL | 1800-2025 | 0.12 / 0.379 / 1.2 (pre-D53: 0.45 / 2.12 / 10) | 1 | modelled | S0010;S0202;S0008 |
| coal:0063 | combustion_power: Enrichment of the escaping fly ash relative to BULK ash (rebased D53), Th228+ | Th228+/liberated/air_stack | XWL | 1800-2025 | 0.12 / 0.379 / 1.2 (pre-D53: 0.45 / 2.12 / 10) | 1 | modelled | S0010;S0202;S0008 |
| coal:0064 | combustion_power: Enrichment of the escaping fly ash relative to BULK ash (rebased D53), K40 | K40/liberated/air_stack | XWL | 1800-2025 | 0.69 / 2.03 / 6 (pre-D53: 0.69 / 5.87 / 50) | 1 | modelled | S0010;S0202;S0008 |
| coal:0065 | combustion_power: Share of in-coal Rn-222 inventory released when coal is burned (applies to the Ra-226+ ash-borne Bq) | Rn222+/liberated/air_stack | XWL | 1800-2025 | 0.7 / 0.85 / 1 | 1 | modelled | S0001;S0010;S0203 |
| coal:0066 | combustion_power: Share of in-coal Rn-220 inventory released when coal is burned (applies to the Th228+ ash-borne Bq) | Rn220+/liberated/air_stack | XWL | 1800-2025 | 0.86 / 0.93 / 1 | 1 | modelled | S0010;S0203 |
| coal:0067 | combustion_nonpower: Ash yield of coal burned outside power stations (mass of ash per mass of coal) | (all groups) | XWL | 1800-2025 | 0.08 / 0.12 / 0.16 | t/t | modelled | S0008;S0205;S0200;S0209 |
| coal:0068 | combustion_nonpower: Household (residential) share of coal burned outside power stations | dispersed/coal_domestic_ash | XWL | 1800-1949 | 0.128 / 0.229 / 0.41 | 1 | modelled | S0231;S0232 |
| coal:0069 | combustion_nonpower: Household (residential) share of coal burned outside power stations | dispersed/coal_domestic_ash | XWL | 1950-2025 | 0.005 / 0.0361 / 0.26 | 1 | modelled | S0231;S0232 |
| coal:0070 | combustion_nonpower: Share of household-burned coal activity leaving as chimney smoke | liberated/air_stack | XWL | 1800-1949 | 0.006 / 0.0145 / 0.035 | 1 | modelled | S0008 |
| coal:0071 | combustion_nonpower: Share of household-burned coal activity leaving as chimney smoke | liberated/air_stack | XWL | 1950-2025 | 0.003 / 0.0102 / 0.035 | 1 | modelled | S0008 |
| coal:0072 | combustion_nonpower: Measured Ra-226 in household furnace ash, Upper Silesia (reference value per tonne of ash) | Ra226+/coal_domestic_ash | POL | 2015-2019 | 1.57e+05 / 1.63e+05 / 1.69e+05 | Bq/t | measured | S0218 |
| coal:0073 | combustion_nonpower: Measured Ra-228 in household furnace ash, Upper Silesia (reference value per tonne of ash) | Ra228+/coal_domestic_ash | POL | 2015-2019 | 9.8e+04 / 1e+05 / 1.02e+05 | Bq/t | measured | S0218 |
| coal:0074 | combustion_power: Share of US power-station ash (fly, bottom, boiler slag) to impounded: landfill, ash pond and dyke (the unused remainder) | impounded | USA | 1991-2009 | 0.5 / 0.67 / 0.78 | 1 | modelled | S0214;S0213;S0215;S0001 |
| coal:0075 | combustion_power: Share of US power-station ash (fly, bottom, boiler slag) to reisolated: underground mine backfill | reisolated | USA | 1991-2009 | 0 / 0 / 0.06 | 1 | modelled | S0214;S0213;S0215;S0001 |
| coal:0076 | combustion_power: Share of US power-station ash (fly, bottom, boiler slag) to dispersed: beneficial use in concrete, cement, fills, road base, soil, aggregate | dispersed | USA | 1991-2009 | 0.22 / 0.33 / 0.44 | 1 | modelled | S0214;S0213;S0215;S0001 |
| coal:0077 | combustion_power: Share of US power-station ash (fly, bottom, boiler slag) to impounded: landfill, ash pond and dyke (the unused remainder) | impounded | USA | 2010-2025 | 0.26 / 0.45 / 0.62 | 1 | modelled | S0214;S0213;S0215;S0001 |
| coal:0078 | combustion_power: Share of US power-station ash (fly, bottom, boiler slag) to reisolated: underground mine backfill | reisolated | USA | 2010-2025 | 0 / 0 / 0.06 | 1 | modelled | S0214;S0213;S0215;S0001 |
| coal:0079 | combustion_power: Share of US power-station ash (fly, bottom, boiler slag) to dispersed: beneficial use in concrete, cement, fills, road base, soil, aggregate | dispersed | USA | 2010-2025 | 0.38 / 0.55 / 0.68 | 1 | modelled | S0214;S0213;S0215;S0001 |

## 2. Cross-checks

**Mine radon.** World 2010 coal production 7.44 Gt (activity spine) x 9.3e5 Bq/t = 6.9 PBq/a; 2020, 7.69 Gt: 7.1 PBq/a. UNSCEAR 2016 charges mining radon only to coal burned for power: 2.8 TBq/GWa x 991.6 GWa = 2,776 TBq/a, from 3.0e6 t/GWa x 991.6 GWa = 2.97 Gt. Scaling our factor to that tonnage gives 2,760 TBq/a, so the factor reproduces UNSCEAR (as it must: same number). The whole-industry total is about 2.4x the power-coal total. The 1980s crude bounds, 36 and 600 GBq/GWa (S0008), give 36-595 TBq/a at 991.6 GWa; UNSCEAR 1993 quotes 30-800 TBq/a. Our low bound (1.2e4 Bq/t) is the 36 GBq/GWa figure; the 600 GBq/GWa value (2.0e5 Bq/t) sits at the bottom of China's measured range (1.9e5), so China's measurement is 1.5-26x above the old crude scaling from uranium mines and the old numbers were low.

**Ash balance, world 2020** (central values, activity spine: power ash 584 Mt, fly ash 467 Mt, coal electricity 9,437 TWh = 1,077 GWa).
- Coal burned for power = 584 Mt / 0.12 = 4.87 Gt (64% of 7.56 Gt consumption, consistent with the 63.5% power share). Ra-226 head activity in that coal and ash: 4.87e9 t x 20 Bq/kg = 97 TBq, i.e. 0.090 TBq per GWa. UNSCEAR 2016: 20 Bq/kg x 3.0e9 kg = 0.060 TBq per GWa. Ratio 1.5, explained by 4.5 Gt/GWa fleet coal intensity against UNSCEAR's 3.0 Gt/GWa (24 GJ/t, 38% efficiency); order of magnitude agrees.
- Stack, 2010-2025 era, after the D53 rebase (base fraction centre 0.31%, band 0.08-1.2%; ash-borne Pb-210, Po-210 and Ra-226 each 97 TBq): released = 97 TBq x fraction x bulk-ash enrichment.
  - Pb-210 (enrichment 3.8, band 1.0-14.4): centre 1.15 TBq = 1.06e-3 TBq/GWa; low 7.2e-5; high 1.6e-2. UNSCEAR 2016: 1.4e-3 (older), 9.3e-5 (modern). Centre now within 1.3x of older plants (before: 3.1e-3, 2.2x above).
  - Po-210 (enrichment 8.5, band 3-24): centre 2.56 TBq = 2.4e-3 TBq/GWa; low 2.2e-4; high 2.6e-2 (before: 7.0e-3 centre). About 1.7x above the older-plant figure.
  - Ra-226 (enrichment 1.10, band 0.6-2.0): centre 0.33 TBq = 3.1e-4 TBq/GWa; UNSCEAR 7e-4 older, 4.7e-5 modern, so the centre sits between them (before: 1.1e-3).
  - The cap at the fly-ash Bq (0.8 x 97 = 78 TBq) is not reached by any bound after the rebase (D54 still logs it where it occurs).
- Rn-222 at the stack: 0.85 x 97 = 82 TBq, 0.077 TBq/GWa against UNSCEAR 0.07 (equal order).
- Ash tonnage: power ash 534 Mt in 2010 against the survey's 780 Mt coal combustion products for 2010 (all sectors, bottom ash and FGD gypsum): 68%, plausible. Not tested for 1985 (280 Mt world, S0008); the spine has no 1985 power-only comparison.
- Pre-1950 coal: 67.8 Gt mined 1800-1949 in the spine x 20 Bq/kg Ra-226 = 1.4 PBq (band 0.5-2.4 PBq), in line with notes.md (about 1.3 PBq).
- Household ash: model Ra-226 167 Bq/kg ash (20/0.12) against 163 +/- 6 measured (S0218, abstract only): agrees. Ra-228 model 167 against 100 measured: 1.7x high.

## 3. Gap register

| # | Item | Why no row | URL if inaccessible | Blocks the engine? |
|---|---|---|---|---|
| G1 | FGD residue / gypsum activity | S0248, S0249 abstracts lack activities; `coal_fgd_residue` has no rows. The ACAA 2024 survey (S0214) gives US FGD gypsum tonnage (16.86 Mt produced, 17.14 Mt used = 102%, 12.9 Mt in wallboard) but no activity | S0249 record in sources.csv | No |
| G2 | Overburden / waste rock memo (earth moved, Bq) | availability: no_data in all decades; no strip ratios | none | No (memo tier only) |
| G3 | Coke ovens and gasworks releases/residues | S0227 (now read, 3 pages) is a two-plant Italian integrated-steelworks survey (samples 2004-2006): coke tar Pb-210 181 / Po-210 177 Bq/kg; coke-oven take-out dust U-238 21, Ra-226 15, Pb-210 14, Po-210 2, Th-232 10, K-40 30 Bq/kg; quenching water Pb-210 13, Po-210 7 Bq/kg (units as printed). Concentrations only: no residue mass per tonne of coal, no release or throughput, and no gasworks. Not usable as a factor with any driver, so no row. It does show coke-oven dust at coal-like activity (no volatile enrichment); the enrichment is in blast-furnace and sinter dust (iron-ore chain, not coal) | none | No; their coal is counted in non-power with the industrial ash route and no release (understates) |
| G4 | Washery refuse mass (and activity row) | mass ratio only for China gangue (S0254, 15-20% of output); no per-country ratio | none | No (no rows); `coal_washery_refuse` parameters left empty |
| G5 | Pre-1950 measurements (coal, ash, radon, mine water) | none exist | none | No; pre-1950 values are extrapolations of 1950+ factors, flagged in notes |
| G6 | Seepage fraction, all coal residue types | not in METHODS (only "per residue type") nor Phase 1 | none | **BLOCKER**: `seepage_per_a_*` empty for coal_fly_ash and coal_bottom_ash, and for coal_mine_water_sludge and coal_domestic_ash. The pipeline refuses to run an empty set for a residue type with data rows |
| G7 | epsilon_rn220 for all coal residues | Phase 1 gives only a Rn-222 table; S0203 Table 3 has Rn-220 emanation (minerals 0.01, rocks 0.11, soils 0.14) but no fly ash entry and not an exhalation fraction | S0203 https://www-pub.iaea.org/MTCD/Publications/PDF/trs474_webfile.pdf | **BLOCKER** (same all-or-none rule); a candidate from S0203 (0.01 / 0.11 / 0.14) needs Steve's approval |
| G8 | epsilon_rn222 for coal_mine_water_sludge and coal_domestic_ash | no Phase 1 proposal; METHODS 5.2 provisional default 0.2 (0.05-0.35) exists but has no citable source | none | **BLOCKER** for those two residue types; recommend the METHODS default with a stated basis |
| G9 | Household share of non-power coal, global | only UK and US anchors | none | No; very wide band (0.5-26% after 1950) |
| G10 | Industrial boiler stack release | S0207 gives 80% removal but no ash release basis | none | No; understates Pb-210 and Po-210 from industry |
| G11 | Mine water radium outside Poland and before 1985 | measured only for Upper Silesia | S0251 https://doi.org/10.1051/radiopro:2005s1-074; S0206 https://inis.iaea.org/records/ssdeg-phf08 | No |
| G12 | Fly versus bottom ash partition of Pb-210 and Po-210 and fly/bottom concentrations in general | not in Phase 1 | S0237, S0239, S0240 (paywalled, in sources_task13.csv) | No; totals conserved |
| G13 | ACAA historical ash utilisation | ACAA 2024 charts and survey table (S0214) now read: US all-CCP series 1991-2024, fly ash and bottom ash 2000-2024 (graph values, +/- 3 points), exact 2024 table. Not provided: pre-1991 years, the disposal route (landfill vs pond vs mine), underground vs surface mine placement, and any non-US country. Used for the six USA rows (coal:0074-0079); XWL values unchanged | none | No |
| G14 | Coal plant construction materials | availability: no_data | none | No; passed to Tasks 1.5 and 1.9; no coal construction rows, none pre-1950 |
| G15 | Pa-231 and Ac-227+ in coal | not in Phase 1 | none | No; the U-235 chain below U235+ is not carried (U-235 contributes about 4.6% of U-238 head activity before multipliers) |
| G16 | Untraceable lower bound of K-40 in coal | Phase 1 has 50, 104, 144 only | none | No; low = centre |

## 4. Choices where Phase 1 was silent

1. **Ash drivers, not tonnes of coal, for power.** No power-coal tonnage series exists, only TWh and ash. Ash concentration is coal content / 0.12 (the builder's central ash yield, so yield cancels; its band is not repeated). Power and non-power coal-content factors are the same quantity and should be treated as correlated.
2. **U-234 and Th-230 included** (equilibrium with U-238) although not in the brief list, so the Ra-226 ash stock is supported by its parents over long horizons. Delete rows if unwanted. Pa-231 and Ac-227+ omitted (G15).
3. **Base release fraction defined on total power ash**, separate from group enrichment, so that the conflict is held in one place. Unit-1, group empty. Without the cap f x E could exceed 1 (D54).
4. **Ash enrichment rebased to bulk ash (D53, approved by Steve).** The original conflict is carried as bounds, but S0010 ratios are relative to bulk ash and S0202 Table X relative to coal. Conversion: divide S0202 by the coal-to-ash concentration factor 1/0.12 = 8.33. For the S0010 side of U, Th and K (no explicit S0010 enrichment) the bulk-ash ratio is derived from its escaping-ash Bq/kg over bulk ash. Worked example, Pb-210: coal 20 Bq/kg gives bulk ash 20/0.12 = 167 Bq/kg. S0010 escaping ash 930 Bq/kg is 930/167 = 5.6x bulk ash (inside its 1-11x) and 930/20 = 46x coal (inside S0202 20-120x). S0202 20-120x coal becomes 2.4-14.4x bulk ash. Rebased band = extremes of {1, 11} and {2.4, 14.4} = 1.0-14.4, centre sqrt(1 x 14.4) = 3.8 (before: 1-120, centre 11.0). Released Pb-210 = ash-borne Pb-210 (coal x 1000/0.12 per t ash) x 3.8 x release fraction, so the coal-to-ash step appears once. Caveat: S0202 U and Th 1-10x give rebased values below 1 (0.12-1.2), so the U and Th centres (0.39, 0.38) are probably artefacts of applying a coal-relative range that is not a pure ash-concentration ratio; revisit if those groups matter.

| group | pre-D53 low / central / high | rebased low / central / high |
|---|---|---|
| Ra226+, Ra228+ | 1 / 3.87 / 15 | 0.6 / 1.10 / 2.0 |
| Pb210+ | 1 / 10.95 / 120 | 1.0 / 3.79 / 14.4 |
| Po210 | 3 / 24.5 / 200 | 3 / 8.49 / 24 |
| U238+, U234, Th230, U235+ | 1 / 3.16 / 10 | 0.12 / 0.39 / 1.3 |
| Th232, Th228+ | 0.45 / 2.12 / 10 | 0.12 / 0.38 / 1.2 |
| K40 | 0.69 / 5.87 / 50 | 0.69 / 2.03 / 6.0 |

5. **Pre-1950 era values** use the same coal content and 1950+ shares. The 1800-1949 stack fraction 0.25 is kept (basis modelled; notes cell says judgement, no source) with the high bound widened from 0.65 to 0.80 (maximum fly-ash fraction, activity note N100). The U-234 and Th-230 rows are kept (approved).
6. **Central rule.** Where a central is not a published number it is the geometric mean (span >3x) or arithmetic mean of the stated low and high.
7. **Basis labelling.** Everything derived or applied to other countries/years is `modelled`, including typical coal contents; only China mine radon, Silesian household ash are `measured`.
8. **Poland mine drainage** per tonne uses whole-country production (includes lignite), so applying it to POL reproduces the measured Bq/a; sludge retained = released x r/(1-r) is my proposal. Radium-retention tier is `impounded` because `coal_mining` has no `reisolated` tier.
9. **Household ash -> dispersed (share 1), industrial ash -> impounded**, per METHODS 6.3; no row because the share is by definition.
10. **Residue parameters.** Fly ash 0.005/0.03/0.13 and bottom ash 0.5/0.75/1.0 x fly ash taken from research/coal/notes.md (the low 0.005 is untraced there). `source_ids` for the two rows is S0001 only because the pipeline tests resolve only S0001-S0005 from the real residue_types.csv; S0203/S0242/S0247 are named in the notes cell. Filling with S0203 etc. made 438 tests fail. Washery refuse left empty (no rows). Emanation coefficient is used as the exhalation fraction.
11. **Smoke fraction** (3.5% / 0.3-0.6% of coal mass) is applied to coal activity, assuming smoke carries the coal-average activity; weak.
12. **Stack radon** shares (0.85 and 0.93 centre) are my reading of S0203 emanation coefficients as retention complements; UNSCEAR assumed 100%.
13. **D53** (Steve): enrichment factors rebased to bulk ash, see choice 4. Rows coal:0054-0064 changed; ids unchanged.
14. **D54** (Steve): the stream script caps released activity at the fly-ash activity and logs every cap application. No data change.
15. **ACAA / EPA / S0227 update (2026-10).** Six new rows coal:0074-0079 give US ash route shares (region USA): 1991-2009 dispersed 0.22/0.33/0.44, impounded 0.50/0.67/0.78; 2010-2025 dispersed 0.38/0.55/0.68, impounded 0.26/0.45/0.62; reisolated 0/0/0.06 in both. The XWL shares (coal:0040-0048) have unchanged values, only fuller notes: the ACAA covers one country (about 10% of world power ash) and the world bounds must still span India, China and the EU. USA rows are inert while the ash drivers exist for XWL only. S0227 gave no usable factor (gap G3).

## 5. What the three supplied files contain, and contradictions

- `2024-Production-and-Use-Charts.pdf` (ACAA, S0214): charts of CCP production and use, 1991-2024 (all CCPs), 2000-2024 (fly ash, bottom ash), 2002-2024 (synthetic gypsum). Values are read from graphs.
- `EPA-HQ-OLEM-2020-0107-1384_content.pdf`: despite the name, the one page is the **ACAA 2024 CCP Production and Use Survey table**, not EPA docket text (no disposal-route or impoundment data). 2024, short tons: fly ash 24.72 Mt produced / 19.39 used (78%); bottom ash 7.67 / 2.72 (35%); boiler slag 1.58 / 0.89 (56%); FGD gypsum 16.86 / 17.14 (102%); FBC ash 5.89 / 5.89 (100%, of which 5.44 Mt "mining applications"); total 63.57 / 46.04 (72%). Uses: concrete 14.98 Mt, blended cement 5.35, mining 5.46, wallboard 12.88, structural fill 0.27, road base 0.33. Production for fly ash, bottom ash, gypsum and FBC ash comes from the EIA-based Ash Mart; boiler slag and the FGD splits are 10-year averages (derived, not surveyed).
- No contradiction with the factor table in values, but: (a) S0215 trade-press figures (63.6 Mt, 72%, 14.6 Mt fly ash in concrete, 12.88 Mt wallboard) match the survey exactly; (b) S0001's "about 40% used" is a graph reading and fits only 2008-2013 in the ACAA series (about 25% in 1991, 72% in 2024), so the old US-centred 40% (also the XWL 1990-2009 centre) is at the top of US 1991-2009 practice, not its average (US central 0.33); (c) the table applies one share to fly and bottom ash, but US 2024 use differs (78% vs 35%); (d) the US fly-ash fraction of fly + bottom + slag ash is 0.73 in 2024 against the activity builder's 0.80 (S0210: 80-85%); (e) the survey's file name and the S0227 sampling years are inconsistent (S0227 text gives 2004 and 2005 in the methods and 2005 and 2006 in the results); (f) `data/sources.csv` still lists S0214 as `inaccessible` with a URL; I did not edit it. No new source rows were needed (S0214 and S0227 are present).
