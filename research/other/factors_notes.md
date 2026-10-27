# Other-energy factor registry: notes (Task 2.5, step 1)

Written 2026-10-27. Output: `data/factors/other.csv` (70 rows, `other:0001`-`other:0070`). Rows by stage: `geothermal` 9, `biomass_peat` 61 (peat 38, wood and Cs-137 23), `hydro` 0, `construction` 0. By substream served: geothermal 9; biomass_peat only 18; biomass_domestic only 9 (other:0011, 0041-0043, 0049, 0051, 0068-0070); shared by both 34. New sources S1400-S1401 are in `research/other/sources_factors.csv` (`data/sources.csv` not edited). Generator: scratchpad script (not part of the repository; ask if you want it filed under `research/other/`). No pipeline code and no tests were written.

Validator over the whole tree (`python -m pipeline.validate --root .`): **6 issues, all T04 "unresolved source" for S1400 (other:0004, other:0005) and S1401 (other:0044-0047)**, because `data/sources.csv` is not edited here. On a scratch copy of the tree with `research/other/sources_factors.csv` appended to `data/sources.csv`: `OK: no issues`. Merging the two source rows clears the six.

## Engine reading of the factors (my specification; the stream spec should confirm)

All activity values are HEAD-nuclide activity (METHODS 3.2, 4.1a, D24, D42); the engine applies group multipliers. Selectors matter because stage `biomass_peat` serves two fuels and two substreams: every lookup below names the exact `driver_series`, `group`, `tier`, `route` and `residue_type` (a `None` filter matches only a blank cell, LIB_SPEC 3.1).

- **Geothermal.** Rn-222 flow (Bq/a) = GW a x factor, where GW a = TWh / 8.766 (lib converts TWh to GW a automatically for `Bq/GWa`). ITA and USA rows override the XWL row; countries absent from `elec_gen_geothermal` fall into the `XXX` remainder.
- **Geothermal scale.** Mass (t) = GW a x other:0004, formed with lib `product` on Bounds (unit `t/GWa` is outside `apply`). Activity of group $g$ = `apply(mass, "t", other:0005..0009)`.
- **Peat** (same chain for plants, household and the "other peat use" residual):
  - dry peat (t) = `apply(peat_t, "t", dry fraction)`; ash (t) = dry peat x ash yield (other:0013); ash-borne $A_g$ = `apply(ash, "t", conc_g)` for the 11 natural groups.
  - Plants: $S_g=\min\big(p_y\,e_g\,A_g,\;f_{\mathrm{fly}}A_g\big)$, tier liberated, route `air_stack`; residue $A_g-S_g$ split by the two route shares to impounded / dispersed, residue `peat_ash`.
  - Household: $M_g=\min\big(s\,e_g\,A_g,\;A_g\big)$ (smoke), residue $A_g-M_g$ split by the household shares, residue `peat_ash`.
  - Cs-137 on peat: ash-borne $A_{\mathrm{Cs}}$ = `apply(ash, "t", Cs conc by era)`; stack part is a **re-release flow**, the remainder a **memo** (see 3).
- **Wood.** Dry wood $D_{\mathrm{tot}}$ = `wood_fuel_t` x other:0048; charcoal wood $D_{\mathrm{ch}}$ = `charcoal_production_t` x other:0051 (capped at $D_{\mathrm{tot}}$); household $D_{\mathrm{hh}}=\min\big(m_{\mathrm{hh}}\,\rho\,d,\;D_{\mathrm{tot}}-D_{\mathrm{ch}}\big)$ with $m_{\mathrm{hh}}$ = `household_fuelwood_m3`, $\rho$ = other:0049, $d$ = other:0048 (fallback where no UNSD series: other:0050 x $(D_{\mathrm{tot}}-D_{\mathrm{ch}})$); plants $D_{\mathrm{pl}}=D_{\mathrm{tot}}-D_{\mathrm{ch}}-D_{\mathrm{hh}}\ge0$ (independent difference, COAL_SPEC 7). No impounded or dispersed rows exist for wood (all of it is memo, see 3).

## 1. Factor table

| id | what | group / tier / route / residue | region | years | low / central / high | unit | basis | sources |
|---|---|---|---|---|---|---|---|---|
| other:0001 | geothermal: Rn-222 vented with non-condensable gas per GW a of geothermal electricity, default for all countries without own factor | Rn222+/liberated/air_vented_gas | XWL | 1900-2025 | 2e+13 / 1.5e+14 / 4e+14 | Bq/GWa | modelled | S0001;S0008;S0010;S0509;S0505 |
| other:0002 | geothermal: Rn-222 vented with non-condensable gas per GW a, Italy (Larderello and Tuscan vapour-dominated fields) | Rn222+/liberated/air_vented_gas | ITA | 1913-2025 | 1e+14 / 2.6e+14 / 4e+14 | Bq/GWa | compiled | S0001;S0008;S0509 |
| other:0003 | geothermal: Rn-222 vented with non-condensable gas per GW a, United States (The Geysers value applied to US geothermal generation) | Rn222+/liberated/air_vented_gas | USA | 1960-2025 | 5e+12 / 3.85e+13 / 1.5e+14 | Bq/GWa | compiled | S0001;S0008;S0502 |
| other:0004 | geothermal: Mass of scale and sludge generated per GW a of geothermal electricity, tonnes (documentation row: the stream script forms mass = GW a x this factor, then applies the Bq/t rows) | impounded/geothermal_scale | XWL | 1900-2025 | 1 / 250 / 6.1e+04 | t/GWa | modelled | S1400 |
| other:0005 | geothermal: Activity per tonne of geothermal scale and sludge, Ra226+ | Ra226+/impounded/geothermal_scale | XWL | 1900-2025 | 1e+04 / 3.7e+05 / 1.34e+07 | Bq/t | modelled | S0501;S0503;S1400;S0500;S0502 |
| other:0006 | geothermal: Activity per tonne of geothermal scale and sludge, Ra228+ | Ra228+/impounded/geothermal_scale | XWL | 1900-2025 | 5e+03 / 1.1e+05 / 2.4e+06 | Bq/t | modelled | S0501;S0503;S0502 |
| other:0007 | geothermal: Activity per tonne of geothermal scale and sludge, Pb210+ | Pb210+/impounded/geothermal_scale | XWL | 1900-2025 | 1e+04 / 1.9e+05 / 3.6e+06 | Bq/t | modelled | S0501;S0502;S0500 |
| other:0008 | geothermal: Activity per tonne of geothermal scale and sludge, Po210 | Po210/impounded/geothermal_scale | XWL | 1900-2025 | 9e+03 / 2.5e+05 / 7e+06 | Bq/t | modelled | S0501;S0502 |
| other:0009 | geothermal: Activity per tonne of geothermal scale and sludge, K40 | K40/impounded/geothermal_scale | XWL | 1900-2025 | 5e+03 / 7e+04 / 9.67e+05 | Bq/t | modelled | S0501;S0503 |
| other:0010 | biomass_peat: Dry-matter fraction of UNSD energy-peat tonnage (plant peat (UNSD transactions 08811-08822)); one correlated factor, repeated per driver so that select() can tell the drivers apart | - | XWL | 1800-2025 | 0.45 / 0.52 / 0.6 | 1 | modelled | S0847;S0519 |
| other:0011 | biomass_domestic: Dry-matter fraction of UNSD energy-peat tonnage (household peat (UNSD transaction 1231)); one correlated factor, repeated per driver so that select() can tell the drivers apart | - | XWL | 1800-2025 | 0.45 / 0.52 / 0.6 | 1 | modelled | S0847;S0519 |
| other:0012 | biomass_peat: Dry-matter fraction of UNSD energy-peat tonnage (the 'other peat energy use' residual (supply minus plant minus household)); one correlated factor, repeated per driver so that select() can tell the drivers apart | - | XWL | 1800-2025 | 0.45 / 0.52 / 0.6 | 1 | modelled | S0847;S0519 |
| other:0013 | biomass_peat+biomass_domestic: Ash yield of energy peat (tonnes of ash per tonne of dry peat) | peat_ash | XWL | 1800-2025 | 0.02 / 0.05 / 0.08 | 1 | modelled | S0519 |
| other:0014 | biomass_peat: Fly-ash share of plant peat ash (cap on stack release: released activity cannot exceed the fly-ash activity) | peat_ash | XWL | 1800-2025 | 0.6 / 0.75 / 0.85 | 1 | modelled | S0519 |
| other:0015 | biomass_peat+biomass_domestic: Activity per tonne of peat ash from energy peat, U238+ | U238+/peat_ash | XWL | 1800-2025 | 1.2e+05 / 4e+05 / 4.5e+06 | Bq/t | modelled | S0519;S0008 |
| other:0016 | biomass_peat+biomass_domestic: Activity per tonne of peat ash from energy peat, U234 | U234/peat_ash | XWL | 1800-2025 | 1.2e+05 / 4e+05 / 4.5e+06 | Bq/t | modelled | S0519 |
| other:0017 | biomass_peat+biomass_domestic: Activity per tonne of peat ash from energy peat, Th230 | Th230/peat_ash | XWL | 1800-2025 | 5e+04 / 1.3e+05 / 1.35e+06 | Bq/t | modelled | S0519 |
| other:0018 | biomass_peat+biomass_domestic: Activity per tonne of peat ash from energy peat, Ra226+ | Ra226+/peat_ash | XWL | 1800-2025 | 5e+04 / 1.3e+05 / 1.35e+06 | Bq/t | modelled | S0519 |
| other:0019 | biomass_peat+biomass_domestic: Activity per tonne of peat ash from energy peat, Pb210+ | Pb210+/peat_ash | XWL | 1800-2025 | 1.4e+05 / 8e+05 / 4e+06 | Bq/t | modelled | S0519 |
| other:0020 | biomass_peat+biomass_domestic: Activity per tonne of peat ash from energy peat, Po210 | Po210/peat_ash | XWL | 1800-2025 | 3e+04 / 5e+05 / 4e+06 | Bq/t | modelled | S0519 |
| other:0021 | biomass_peat+biomass_domestic: Activity per tonne of peat ash from energy peat, U235+ | U235+/peat_ash | XWL | 1800-2025 | 5.5e+03 / 1.84e+04 / 2.07e+05 | Bq/t | modelled | S0519 |
| other:0022 | biomass_peat+biomass_domestic: Activity per tonne of peat ash from energy peat, Th232 | Th232/peat_ash | XWL | 1800-2025 | 4.5e+04 / 1.42e+05 / 3.7e+05 | Bq/t | modelled | S0519 |
| other:0023 | biomass_peat+biomass_domestic: Activity per tonne of peat ash from energy peat, Ra228+ | Ra228+/peat_ash | XWL | 1800-2025 | 4.5e+04 / 1.42e+05 / 3.7e+05 | Bq/t | modelled | S0519 |
| other:0024 | biomass_peat+biomass_domestic: Activity per tonne of peat ash from energy peat, Th228+ | Th228+/peat_ash | XWL | 1800-2025 | 4.5e+04 / 1.42e+05 / 3.7e+05 | Bq/t | modelled | S0519 |
| other:0025 | biomass_peat+biomass_domestic: Activity per tonne of peat ash from energy peat, K40 | K40/peat_ash | XWL | 1800-2025 | 1.5e+05 / 3.5e+05 / 1.5e+06 | Bq/t | modelled | S0519 |
| other:0026 | biomass_peat: Fraction of plant peat ash escaping the stack, 1800-1989 (analogue: coal 1970-1989) | liberated/air_stack | XWL | 1800-1989 | 0.01 / 0.0447 / 0.2 | 1 | modelled | S0519;S0010;S0008;S0207 |
| other:0027 | biomass_peat: Fraction of plant peat ash escaping the stack, 1990-2025 | liberated/air_stack | XWL | 1990-2025 | 0.002 / 0.01 / 0.025 | 1 | modelled | S0519;S0008;S0001 |
| other:0028 | biomass_peat: Enrichment of the escaping peat fly ash relative to BULK ash (analogue of coal:0054), Ra226+ | Ra226+/liberated/air_stack | XWL | 1800-2025 | 0.7 / 1.2 / 3 | 1 | modelled | S0519;S0010;S0202;S0008;S0237;S0240;S0241;S0245 |
| other:0029 | biomass_peat: Enrichment of the escaping peat fly ash relative to BULK ash (analogue of coal:0055), Ra228+ | Ra228+/liberated/air_stack | XWL | 1800-2025 | 0.9 / 1.2 / 1.7 | 1 | modelled | S0519;S0010;S0202;S0008;S0237;S0241 |
| other:0030 | biomass_peat: Enrichment of the escaping peat fly ash relative to BULK ash (analogue of coal:0056), Pb210+ | Pb210+/liberated/air_stack | XWL | 1800-2025 | 1 / 3.79 / 8 | 1 | modelled | S0519;S0010;S0202;S0008;S0237;S0239;S0240;S0241 |
| other:0031 | biomass_peat: Enrichment of the escaping peat fly ash relative to BULK ash (analogue of coal:0057), Po210 | Po210/liberated/air_stack | XWL | 1800-2025 | 2 / 4.5 / 12 | 1 | modelled | S0519;S0010;S0202;S0008;S0239;S0240;S0980;S0245 |
| other:0032 | biomass_peat: Enrichment of the escaping peat fly ash relative to BULK ash (analogue of coal:0058), U238+ | U238+/liberated/air_stack | XWL | 1800-2025 | 0.6 / 1.3 / 2.8 | 1 | modelled | S0519;S0010;S0202;S0008;S0237;S0240;S0241 |
| other:0033 | biomass_peat: Enrichment of the escaping peat fly ash relative to BULK ash (analogue of coal:0059), U234 | U234/liberated/air_stack | XWL | 1800-2025 | 0.6 / 1.3 / 2.8 | 1 | modelled | S0519;S0010;S0202;S0008;S0237;S0240;S0241 |
| other:0034 | biomass_peat: Enrichment of the escaping peat fly ash relative to BULK ash (analogue of coal:0060), Th230 | Th230/liberated/air_stack | XWL | 1800-2025 | 0.9 / 1.1 / 1.6 | 1 | modelled | S0519;S0010;S0202;S0008;S0237;S0240 |
| other:0035 | biomass_peat: Enrichment of the escaping peat fly ash relative to BULK ash (analogue of coal:0061), U235+ | U235+/liberated/air_stack | XWL | 1800-2025 | 0.6 / 1.3 / 2.8 | 1 | modelled | S0519;S0010;S0202;S0008;S0237;S0240;S0241 |
| other:0036 | biomass_peat: Enrichment of the escaping peat fly ash relative to BULK ash (analogue of coal:0062), Th232 | Th232/liberated/air_stack | XWL | 1800-2025 | 0.9 / 1.1 / 1.6 | 1 | modelled | S0519;S0010;S0202;S0008;S0237;S0240;S0241 |
| other:0037 | biomass_peat: Enrichment of the escaping peat fly ash relative to BULK ash (analogue of coal:0063), Th228+ | Th228+/liberated/air_stack | XWL | 1800-2025 | 0.9 / 1.1 / 1.6 | 1 | modelled | S0519;S0010;S0202;S0008;S0237;S0240;S0241 |
| other:0038 | biomass_peat: Enrichment of the escaping peat fly ash relative to BULK ash (analogue of coal:0064), K40 | K40/liberated/air_stack | XWL | 1800-2025 | 0.9 / 1.05 / 1.2 | 1 | modelled | S0519;S0010;S0202;S0008;S0237;S0241 |
| other:0039 | biomass_peat: Share of plant peat ash to impounded: landfill (Swedish class-2 landfill, fill) | impounded/peat_ash | XWL | 1800-2025 | 0.3 / 0.6 / 0.9 | 1 | modelled | S0519;S0537 |
| other:0040 | biomass_peat: Share of plant peat ash to dispersed: road construction, inert fill, forest or field spreading | dispersed/peat_ash | XWL | 1800-2025 | 0.1 / 0.4 / 0.7 | 1 | modelled | S0519;S0518;S0521 |
| other:0041 | biomass_domestic: Share of household peat ash to impounded (swept and landfilled) | impounded/peat_ash | XWL | 1800-2025 | 0.2 / 0.5 / 0.8 | 1 | modelled | S0520;S0516;S0519 |
| other:0042 | biomass_domestic: Share of household peat ash to dispersed (garden, field) | dispersed/peat_ash | XWL | 1800-2025 | 0.2 / 0.5 / 0.8 | 1 | modelled | S0520;S0516;S0519 |
| other:0043 | biomass_domestic: Share of household peat activity leaving as chimney smoke (analogue: coal:0071) | liberated/air_stack | XWL | 1800-2025 | 0.003 / 0.0102 / 0.035 | 1 | modelled | S0008;S0519 |
| other:0044 | biomass_peat+biomass_domestic: Fallout Cs-137 per tonne of peat ash, 1950-1962 | Cs137+/peat_ash | XWL | 1950-1962 | 1e+04 / 1e+05 / 1e+06 | Bq/t | modelled | S0519;S1401;S0008 |
| other:0045 | biomass_peat+biomass_domestic: Fallout Cs-137 per tonne of peat ash, 1963-1985 | Cs137+/peat_ash | XWL | 1963-1985 | 1e+05 / 6e+05 / 5e+06 | Bq/t | modelled | S0519;S1401;S0008 |
| other:0046 | biomass_peat+biomass_domestic: Fallout Cs-137 per tonne of peat ash, 1986-2000 | Cs137+/peat_ash | XWL | 1986-2000 | 1e+05 / 1e+06 / 2e+07 | Bq/t | modelled | S0519;S1401;S0008 |
| other:0047 | biomass_peat+biomass_domestic: Fallout Cs-137 per tonne of peat ash, 2001-2025 | Cs137+/peat_ash | XWL | 2001-2025 | 5e+04 / 5e+05 / 1e+07 | Bq/t | modelled | S0519;S1401;S0008 |
| other:0048 | biomass_peat+biomass_domestic: Dry-matter fraction of FAOSTAT wood-fuel mass (wood_fuel_t = m3 x 0.725 t/m3) | - | XWL | 1800-2025 | 0.6 / 0.75 / 0.85 | 1 | modelled | S0846;S0848 |
| other:0049 | biomass_domestic: Household fuelwood: dry-wood tonnes per m3 reported to UNSD (0.725 t/m3, range 0.625 coniferous to 0.75 non-coniferous) | - | XWL | 1800-2025 | 0.625 / 0.725 / 0.75 | t/m3 | compiled | S0848;S0847 |
| other:0050 | biomass_peat+biomass_domestic: Household share of FAOSTAT wood fuel where the country has no UNSD household series (or before 1990) | - | XWL | 1950-2025 | 0.55 / 0.75 / 0.9 | 1 | modelled | S0846;S0847 |
| other:0051 | biomass_domestic: Dry wood consumed per tonne of charcoal made (inverse of mass yield 0.26 t charcoal per t dry wood, range 0.19-0.31) | - | XWL | 1800-2025 | 3.23 / 3.85 / 5.26 | 1 | modelled | S0563;S0566 |
| other:0052 | biomass_peat+biomass_domestic: Natural K40 per tonne of dry wood burned (memo series: biosphere cycling, D44) | K40/memo_biosphere | XWL | 1800-2025 | 6e+03 / 3e+04 / 1.64e+05 | Bq/t | modelled | S0559;S0531;S0520 |
| other:0053 | biomass_peat+biomass_domestic: Natural Pb210+ per tonne of dry wood burned (memo series: biosphere cycling, D44) | Pb210+/memo_biosphere | XWL | 1800-2025 | 800 / 2e+03 / 1.02e+04 | Bq/t | modelled | S0556;S0565;S0558 |
| other:0054 | biomass_peat+biomass_domestic: Natural Po210 per tonne of dry wood burned (memo series: biosphere cycling, D44) | Po210/memo_biosphere | XWL | 1800-2025 | 200 / 1.5e+03 / 5.5e+03 | Bq/t | modelled | S0556;S0565 |
| other:0055 | biomass_peat+biomass_domestic: Natural Ra226+ per tonne of dry wood burned (memo series: biosphere cycling, D44) | Ra226+/memo_biosphere | XWL | 1800-2025 | 1.6e+03 / 3e+03 / 1.3e+04 | Bq/t | modelled | S0559;S0558 |
| other:0056 | biomass_peat+biomass_domestic: Natural Ra228+ per tonne of dry wood burned (memo series: biosphere cycling, D44) | Ra228+/memo_biosphere | XWL | 1800-2025 | 800 / 2.5e+03 / 9.5e+03 | Bq/t | modelled | S0559 |
| other:0057 | biomass_peat+biomass_domestic: Fallout Cs-137 per tonne of dry fuelwood, XWL 1950-1962 | Cs137+ | XWL | 1950-1962 | 20 / 200 / 2e+03 | Bq/t | extrapolated | S0520;S0543;S0544 |
| other:0058 | biomass_peat+biomass_domestic: Fallout Cs-137 per tonne of dry fuelwood, XWL 1963-1985 | Cs137+ | XWL | 1963-1985 | 200 / 2e+03 / 1.5e+04 | Bq/t | extrapolated | S0520;S0543;S0544 |
| other:0059 | biomass_peat+biomass_domestic: Fallout Cs-137 per tonne of dry fuelwood, XWL 1986-2000 | Cs137+ | XWL | 1986-2000 | 150 / 1.5e+03 / 1.5e+04 | Bq/t | modelled | S0520;S0515;S0536;S0530 |
| other:0060 | biomass_peat+biomass_domestic: Fallout Cs-137 per tonne of dry fuelwood, XWL 2001-2025 | Cs137+ | XWL | 2001-2025 | 100 / 1e+03 / 1e+04 | Bq/t | modelled | S0530;S0531;S0535;S0514 |
| other:0061 | biomass_peat+biomass_domestic: Fallout Cs-137 per tonne of dry fuelwood, SWE 1986-2000 | Cs137+ | SWE | 1986-2000 | 400 / 8e+03 / 2.8e+05 | Bq/t | modelled | S0515;S0536 |
| other:0062 | biomass_peat+biomass_domestic: Fallout Cs-137 per tonne of dry fuelwood, SWE 2001-2025 | Cs137+ | SWE | 2001-2025 | 400 / 5e+03 / 1.5e+05 | Bq/t | extrapolated | S0515;S0536;S0547 |
| other:0063 | biomass_peat+biomass_domestic: Fallout Cs-137 per tonne of dry fuelwood, UKR 1986-2000 | Cs137+ | UKR | 1986-2000 | 500 / 8e+03 / 6.9e+05 | Bq/t | extrapolated | S0539;S0543;S0542 |
| other:0064 | biomass_peat+biomass_domestic: Fallout Cs-137 per tonne of dry fuelwood, UKR 2001-2025 | Cs137+ | UKR | 2001-2025 | 500 / 5e+03 / 6.9e+05 | Bq/t | extrapolated | S0539;S0543 |
| other:0065 | biomass_peat+biomass_domestic: Fallout Cs-137 per tonne of dry fuelwood, BLR 1986-2000 | Cs137+ | BLR | 1986-2000 | 1e+03 / 1e+04 / 7.4e+05 | Bq/t | extrapolated | S0540;S0541;S0539 |
| other:0066 | biomass_peat+biomass_domestic: Fallout Cs-137 per tonne of dry fuelwood, BLR 2001-2025 | Cs137+ | BLR | 2001-2025 | 600 / 6e+03 / 7.4e+05 | Bq/t | extrapolated | S0540;S0541;S0539 |
| other:0067 | biomass_peat+biomass_domestic: Share of fuel Cs-137 leaving the stack from biomass or peat plants (power, heat, industrial boilers; after filters) | Cs137+/liberated/air_rerelease | XWL | 1950-2025 | 0.0005 / 0.005 / 0.05 | 1 | modelled | S0515;S0536;S0519;S0551 |
| other:0068 | biomass_domestic: Share of fuel Cs-137 leaving as stove or chimney emission, household wood and peat | Cs137+/liberated/air_rerelease | XWL | 1950-2025 | 0.05 / 0.25 / 0.7 | 1 | modelled | S0515;S0531;S0564;S0551;S0549;S0536 |
| other:0069 | biomass_domestic: Share of wood Cs-137 released in charcoal kilns during carbonisation (1 minus retention in char) | Cs137+/liberated/air_rerelease | XWL | 1950-2025 | 0.02 / 0.25 / 0.35 | 1 | modelled | S0551;S0564 |
| other:0070 | biomass_domestic: Share of charcoal Cs-137 leaving as stove emission when charcoal is burned | Cs137+/liberated/air_rerelease | XWL | 1950-2025 | 0.05 / 0.12 / 0.3 | 1 | modelled | S0564;S0560 |

Descriptions begin with the substream label that the rows serve. `biomass_peat+biomass_domestic` rows are shared by both substreams; the script picks them with the selectors in the outline (section 7). All values are Bq per tonne of the stated basis (ash, dry wood, scale) unless the unit is `1`; sources for activity figures quote Bq/kg and were multiplied by 1000. Central values are published numbers where they exist, otherwise the geometric mean of the stated low and high (coal notes rule 6).

## 2. Cross-checks and benchmark candidate list (done condition (e))

Arithmetic is mine, on central values, with the activity spine (`elec_gen_geothermal`, `peat.csv`, `biomass.csv`) and these factors. It is NOT a stream build.

**Geothermal Rn-222.** Spine: world 68.44 TWh (7.81 GW a) in 2010, 95.45 TWh (10.89 GW a) in 2020; ITA 5.376 / 6.026 TWh, USA 17.58 / 18.83 TWh.

| Year | Low | Central | High | Central per GW a | UNSCEAR 2016 (150) | Ratio |
|---|---|---|---|---|---|---|
| 2010 | 175 TBq/a | 1,015 TBq/a | 2,622 TBq/a | 130 TBq/(GW a) | 7.77 GW a x 150 = 1,166 TBq/a | 0.87 |
| 2020 | 241 TBq/a | 1,470 TBq/a | 3,819 TBq/a | 135 TBq/(GW a) | (same factor) | 0.90 |

A uniform 150 would give 1,171 TBq/a (2010) and 1,633 TBq/a (2020). The result sits inside the x3 test because the XWL default is UNSCEAR's own number and ITA/USA are the two fields UNSCEAR averaged; this is **not independent** of Annex B. Independent routes are Larderello-only: George et al. 1980 as cited in S0509, 8 Ci/d = 108 TBq/a (derived: $8\times3.7\times10^{10}\times365.25$); UNSCEAR 1988 110 TBq/a at 400 MW (275 TBq/(GW a) at full load); RSE 2013 model 9.5e3 Bq/s per MW = 300 TBq/(GW a). The ITA row (260) is within 1.3x of all three (George 1980 converted with an assumed 0.32-0.40 GW a of Larderello generation in 1980; the source gives no generation). No independent estimate of the world value exists. Fluid concentrations (S0502 Table 4: Larderello 1,280, The Geysers 620, Wairakei 630, Salton Sea 110, Imperial Valley hot water 1.1 Bq/L) show the world default's spread but cannot be turned into a vent rate without steam flow per GW.

**Geothermal scale** (other:0004-0009). Mass 1,952 t (2010) and 2,722 t (2020) at the centre, 8 t to 4.8e5 t (2010) at the bounds. Central Ra-226 head activity 0.0007 and 0.0010 TBq/a; with mass high and concentration high together, Ra-226 6.4 and 8.9 TBq/a, and all five groups 13 TBq/a (2010). Against Rn-222 1,015 TBq/a that is about $10^{-6}$ at the centre (all five groups) and 1.3% at the joint high. Under METHODS 10.3 the stage is negligible at the centre and is not at the joint upper bound (choice 4).

**Peat** (UNSD plant tonnage x other:0010, ash 5%). 2010: plant peat 12.04 Mt, dry 6.26 Mt, ash 313 kt; ash-borne U-238 0.125 TBq, Ra-226 0.041, Pb-210 0.25, Po-210 0.156, K-40 0.11, Th-232 0.044; stack (p 0.01) Pb-210 0.0095, Po-210 0.0070, Ra-226 0.0005 TBq. Per GW a of IRENA peat electricity (spine: 5.90 TWh in 2000, 9.33 in 2010, 3.14 in 2020; the UNSD tonnage includes the heat share of CHP, so this overstates fuel per GW a(e)):

| Year | Dry peat per GW a(e) | U-238 per GW a(e) | UNSCEAR 1988 (S0008) | Ratio |
|---|---|---|---|---|
| 2000 | 7.3e9 kg | 0.147 TBq | 5e9 kg x 40 Bq/kg = 0.20 TBq | 0.74 |
| 2010 | 5.9e9 kg | 0.118 TBq | 0.20 TBq | 0.59 |
| 2020 | 7.0e9 kg | 0.139 TBq | 0.20 TBq | 0.70 |

UNSCEAR's mass per GW a (5e9 kg) agrees with the spine within 1.5x. The U-238 per kg dry peat implied by the stream is 0.05 x 400 = 20 Bq/kg, against UNSCEAR 40, Finnish mean 11 (Helariutta via S0519, 119 samples) and 15 (Mustonen 1984), and Swedish median 21 (ash 420 / 20): inside the measured spread. Not independent of UNSCEAR on the mass; independent on the concentration.

**Peat share of the stream (METHODS 10.3 indicative test).** Counted peat (all groups x group multipliers, plant + household + other use, 1990-2020 tonnages) is 1.6-3.2 TBq of decays per year against 2,600-7,100 TBq/a of geothermal Rn-222 (x5): **0.02-0.07%**, below the 0.1% rule at the centre in every decade 1990-2020 (decade 1990 0.074%). The rule is not met-or-failed for 1950-1989 because there is no peat-for-energy driver then (gap G6). Wood contributes no counted Bq except Cs-137 re-release (0.26 TBq/a head in 2010, about $10^{-4}$ of the geothermal decays). So **geothermal radon is more than 99.9% of the counted stream at the centre**; the rest of the file matters for the memo series, for Steve's household requirement and for the bounds.

**Biomass (wood) memo and Cs-137** (FAOSTAT `wood_fuel_t` x 0.75 dry; world default Cs row only, no SWE/UKR/BLR weighting). 2010: dry wood 1.01 Gt, of which charcoal wood 0.18 Gt (charcoal_production_t 4.7e7 t x 3.85), household 0.80 Gt, plants 0.03 Gt (2020: 0.21, 0.79, 0.05 Gt). Memo natural nuclides 2010 (TBq/a): K-40 30, Pb-210 2.0, Po-210 1.5, Ra-226 3.0, Ra-228 2.5. Cs-137 in burned wood 1.0 TBq/a (2010), re-released 0.26 TBq/a (stove 0.25, plants 0.005, charcoal chain 0.34), memo ash 0.75 TBq/a; 1970: 1.7 / 0.37 / 1.3. These are fuel-weighted world defaults; regional hot spots (Chernobyl districts, Sweden) are in the country rows.

**Benchmark candidate list for stream ⑤ (D51; Steve to approve which two years and values).**

| # | Quantity | Annex B / UNSCEAR value | Independent value | Years | Stream (central) | Note |
|---|---|---|---|---|---|---|
| B1 | Geothermal Rn-222 per GW a | 150 TBq (S0001, UNSCEAR 2016 para 158) | None for the world. For ITA only: 275 (UNSCEAR 1988 110 TBq/a at 400 MW), 270-340 (George 1980, 8 Ci/d, S0509, generation assumed), 300 (RSE 2013 model, S0509) | 2010, 2020 | 130, 135 | Annex B test passes (0.87, 0.90) but is circular; the independent test is ITA-only (ITA row 260) |
| B2 | Peat U-238 in fuel per GW a(e) | 0.20 TBq (UNSCEAR 1988 para 213, S0008) | 0.055 (Finland peat mean 11 Bq/kg x 5e9 kg), 0.075 (Mustonen 15), 0.105 (Sweden median ash 420 / 20) via S0519 | 2000, 2010, 2020 | 0.147, 0.118, 0.139 | Passes both estimates within x3 (1.1-2.7x of the independent values) |
| B3 | Dry peat per GW a(e) | 5e9 kg (S0008) | SSI 100 MW reference plant: 5.8 kWh/kg dry peat gives 1.51e9 kg per GW a thermal (S0519), i.e. 4.3-5.0e9 kg per GW a(e) at efficiency 0.30-0.35 (efficiency is my assumption) | 2000, 2010, 2020 | 7.3e9, 5.9e9, 7.0e9 | Stream 1.2-1.7x the independent value, 1.2-1.5x UNSCEAR; the UNSD tonnage includes CHP heat, which inflates the stream side |
| B4 | Implied Cs-137 in wood ash (Bq/kg ash) | Excluded by UNSCEAR (para 191); no Annex B value | US 1990-92 mean 444 (range 2.9-780, S0520); Austria 2020-22 11.8-867 (S0530); Greece 2013 25-499 (S0531) | 1991, 2021 | World default 1986-2000 gives 112 (1991), 2001-2025 gives 75 (2021), at 1% ash yield and 75% retention | A factor-3 test on the US mean FAILS (4x low) by design: the world default is below NH mid-latitudes. Propose a range test (inside the measured range) instead; Steve to decide |
| B5 | Stove Cs-137 emission per kg wood | none | Thessaloniki winter 2013: 0.8-6.5 Bq/kg wood burned (S0531, air-derived) | 2013 | 0.25 Bq/kg (world default x f_v) | Greece has higher-Cs wood than the world default (beech 8-11 Bq/kg); consistent in order of magnitude only |
| B6 | Wood K-40 in ash | none | US typical 2,960 Bq/kg ash (S0520) | any | 30 Bq/kg wood / 1% = 3,000 | Not independent: S0520 is one input to the 30 |

Not benchmarkable: geothermal scale (no per-GW a figure anywhere), peat Cs-137, hydro (UNSCEAR excludes it, para 27).

## 3. Memo versus counted rows (Steve's requirement (b)), and the biomass_domestic stage restriction (requirement (a))

**Principle (D43/D44/D47/D48).** Natural nuclides in wood are biosphere cycling and Cs-137 on fuel is fallout already counted at deposition. So the ash side of both is memo; only the stack side of fallout Cs-137 is a flow (re-release). Peat natural nuclides stay flows (D44).

| Substream | Material | Groups | Tier / route | In tier totals? |
|---|---|---|---|---|
| biomass_peat (plants, "other peat use") | peat natural nuclides to stack | 11 natural groups | liberated, `air_stack` | **Yes** |
| | peat ash, natural nuclides | 11 | impounded, dispersed (`peat_ash`) | **Yes** |
| | peat Cs-137 to stack | `Cs137+` | liberated, `air_rerelease` | Yes (Liberated tier of ⑤), **reported separately from cross-stream totals** (SCHEMA 5.7) |
| | peat Cs-137 left in ash | `Cs137+` | `memo_biosphere` | **No** |
| | wood: the whole burned content of natural nuclides (ash and smoke are not split) | K40, Pb210+, Po210, Ra226+, Ra228+ | `memo_biosphere` | **No** |
| | wood Cs-137 to stack | `Cs137+` | liberated, `air_rerelease` | Yes, reported separately |
| | wood Cs-137 left in ash | `Cs137+` | `memo_biosphere` | **No** |
| biomass_domestic (household and charcoal) | household peat natural nuclides to chimney | 11 | liberated, `air_stack` | **Yes** |
| | household peat ash, natural | 11 | impounded, dispersed (`peat_ash`) | **Yes** |
| | household peat Cs-137 to chimney | `Cs137+` | liberated, `air_rerelease` | Yes, reported separately |
| | household peat Cs-137 in ash | `Cs137+` | `memo_biosphere` | **No** |
| | **household wood ash, every nuclide** (natural and Cs-137), including the share that is landfilled or spread | as above | `memo_biosphere` only | **No. There are no impounded or dispersed rows for household wood at all** |
| | household wood Cs-137 to chimney | `Cs137+` | liberated, `air_rerelease` | Yes, reported separately |
| | charcoal chain Cs-137 (kiln release, then stove release of the charcoal) | `Cs137+` | liberated, `air_rerelease` | Yes, reported separately |
| | charcoal chain: all wood natural nuclides and Cs-137 not released | as above | `memo_biosphere` | **No** |

Consequences: the residue types `biomass_ash` and `biomass_domestic_ash` get no data rows, so ε and seepage are not required for them; the memo tiers carry no `residue_type`, no `route`, no stock and no engine processing. The disposal split of household wood ash (Phase 1 prior dispersed 0.5, 0.2-0.8) is therefore **not needed and has no factor**; the same prior is used only for household peat ash (other:0041, 0042).

**biomass_domestic stage restriction.** All `biomass_domestic` rows use stage `biomass_peat` (D45; no new stage) and only the tiers its vocab row allows: impounded, dispersed, liberated, memo_biosphere (SCHEMA 5.3). In use: liberated (routes `air_stack` for household peat; `air_rerelease` for Cs-137 only, as vocab requires), impounded and dispersed (household **peat** ash only), memo_biosphere (all wood, and Cs-137 ash). Not used: `reisolated`, `construction` (no household construction), `geothermal`, `hydro`, any route other than the two above, `air_process_vent` (the household notes proposed it for kiln smoke under Option A; with D45 and the vocab rule that `air_rerelease` is the only route for fallout Cs at `biomass_peat`, kiln Cs uses `air_rerelease` and kiln natural nuclides are memo). Justification in the notes: household_biomass_notes.md 2.5 (ash handling, uninformative prior), 2.3 (stack fractions), 2.6 (charcoal chain), 5 (Option B).

## 4. Gap register

| # | Item | Why no row (or weak row) | URL if inaccessible | Blocks the engine? |
|---|---|---|---|---|
| G1 | Rn-220 from geothermal gas | S0508 only says Rn-220 is present in all 23 NZ wells; no ratio. A vent-transit argument ($e^{-t/80\,\mathrm{s}}$ with a transit of minutes) says at most a few per cent of the Rn-222 flow reaches air, but it is inference. No row (a row needs a source) | S0508 https://link.springer.com/article/10.1007/BF02071237 | No; omits `Rn220+`, which METHODS 4.3 lists as a candidate |
| G2 | Rn-222 vent rate outside Larderello and The Geysers | Only two vapour-dominated fields ever measured (George et al. 1980 not located). The world default is UNSCEAR's two-plant mean. Fluid data (S0502 Table 4) show flash fields (Wairakei 630 Bq/L) as high as The Geysers and hot-water/binary fluid ~600x lower | George 1980: not located | No; this is the stream's dominant number and the least supported |
| G3 | Geothermal scale mass per GW a | One hypothetical hypersaline plant (S1400); the low bound 1 t/(GW a) is my assumption | S1400 https://digital.library.unt.edu/ark:/67531/metadc786588/ | No (rows exist; centre is a geometric mean) |
| G4 | Reinjected brine (tier `reisolated`, residue `geothermal_brine`) | No row. Salton Sea brine Ra-226 about 49-55 Bq/L (S1400 1,320 pCi/L; S0502 Table 3 55 Bq/L max) at 50 kg brine per kWh would give about 24 TBq per GW a for that one hypersaline field (my arithmetic), but all other fields lack both brine flow and Ra data, and reinjection returns the activity to its source formation | none | No |
| G5 | Country geothermal generation before 1980 | `elec_gen_geothermal` has only XWL before 1980, so the ITA and USA rows (Larderello was most of world output in the 1950s) cannot apply; the XWL row is used instead | none | No |
| G6 | Peat for energy before 1990 | UNSD series start 1990 (1992 for the former USSR). USGS `prod_peat` XWL is gross weight for all uses, falls from 170 Mt (1991) to 29 Mt (1992) when the USSR drops out, so no energy share can be derived. No factor row for it | UN World Energy Supplies 1950-1974 (lead only; not read) | No; peat is absent 1950-1989, an understatement of unknown size |
| G7 | Radon from peat combustion | Rn-222 from peat Ra-226 would be about 0.05 TBq/a (6.3e9 kg x 8 Bq/kg), 1e-5 of geothermal; no rows | none | No |
| G8 | Peat ash disposal split | Qualitative lists only (S0519). Modelled prior | none | No |
| G9 | Stack measurements for peat and wood plants and for household stoves | None found. The Cs-137 stack share (other:0067) spans 1e-3 to 4.5e-2 by two methods; stove f_v (other:0068) spans 0.05-0.70 | none | No |
| G10 | U-238 and Th-228 in wood | Not found in any source read | S0559 https://link.springer.com/article/10.1007/s10967-026-10807-1 (paywalled) | No; memo only |
| G11 | Wood burned in plants (industrial boilers, CHP, pellets, black liquor, forest-industry residues) | FAOSTAT wood fuel leaves only 0.03-0.05 Gt dry for plants in 2010-2020 after UNSD household and charcoal wood are removed; the real plant fuel is mostly outside item 1864. `elec_gen_biomass` (biomass and waste, includes biogas and MSW) is not usable as a wood tonnage | none | No; memo and Cs re-release for plants understated |
| G12 | Pellets and briquettes (household) | Not separate in FAOSTAT item 1864; S0514, S0530 show pellet ash Cs-137 above log ash | none | No |
| G13 | Radionuclides in charcoal | None in any region; only partition (S0551, S0564) | none | No |
| G14 | Time shape of Cs-137 in wood | The Phase 1 transfer-factor model (deposition x Tag) needs national deposition grids that are not in `data/`. Replaced by four era rows | none | No |
| G15 | Belarus, Russia, global-South firewood and ash | No surveys. BLR rows use the hygienic limit as high and Ukraine as analogue | S0540, S0541 per sources.csv | No |
| G16 | Other biomass fuels (crop residues, dung, bagasse, MSW) | Out of FAOSTAT 1864; no driver | none | No |
| G17 | Wood before 1961 | `wood_fuel_t` starts 1961. No 1950-1960 driver; pre-1950 not built (Phase 1 household notes, open issue 8) | none | No |
| G18 | Hydro numeric negligibility | Operation: zero by process; construction waits on `commodity_factors.csv`, which does not exist yet. No rows | S0522 https://doi.org/10.1073/pnas.1312753111 (lead, not read) | No |
| G19 | Construction (geothermal, biomass, hydro) | `data/reference/commodity_factors.csv` absent | none | No; zero rows, as coal |
| G20 | Primary of the Leonardi Table 4 fluid radon values | Table 4 cites its ref [38], not identified here | S0502 full text https://link.springer.com/content/pdf/10.1140/epjp/s13360-024-04917-6.pdf | No |
| G21 | Heat-only geothermal (district heating, greenhouses) | Outside the electricity driver; the Dutch, German and Italian heat-plant scale data are used only as bounds on concentration | none | No |

## 5. Choices where Phase 1 was silent, for Steve (numbered)

1. **Geothermal radon structure.** Recommended: ITA 260 and USA 38.5 override a world default of 150, bounds 20-400. Alternative A: uniform 150 (UNSCEAR as is; 2010 total 1,171 vs 1,015 TBq/a). Alternative B: a field-type model (vapour, flash, binary); not supported by any measurement outside two fields.
2. **Rn-220 from geothermal.** Omit (gap G1), or add a placeholder row with a physical vent-transit bound. I omitted it because a row needs a source.
3. **Geothermal scale rows.** Kept as five groups x one mass row, but the mass low (1 t/(GW a)) is an assumption and the mass is one hypothetical hypersaline plant. Alternative: declare the stage negligible under 10.3 (centre about 1e-6 of Rn-222; but 1.3% at the joint high), and drop the rows. D21 says processing residues count regardless, which is why I kept them.
4. **Reinjected brine.** No rows (G4).
5. **Residue type for household peat ash.** `peat_ash` (mineral peat ash, its seepage already filled). The alternative `biomass_domestic_ash` was defined for household wood ash and charcoal ash, which are now memo, so it would stay empty.
6. **Residue types `biomass_ash` and `biomass_domestic_ash`.** They receive no data rows under D43/D44. Keep them (harmless) or retire; ε and seepage for them are not needed.
7. **Re-release rows (`air_rerelease`).** I count them in the Liberated tier of stream ⑤ and exclude them from cross-stream sums, reading D43/D48/SCHEMA 5.7 literally. Please confirm.
8. **Household Cs-137 stack share.** Centre 0.25 (Phase 1 proposal 0.25-0.30). The geometric mean 0.19 is equally defensible. Bounds 0.05-0.70.
9. **Plant Cs-137 stack share.** 5e-4 / 5e-3 / 5e-2; centre between the two methods (G9).
10. **Wood natural nuclide set.** D44 names K-40, Pb-210, Po-210. I extended the memo to Ra-226 and Ra-228 on the same biosphere-cycling argument. Say if you want only the three.
11. **Charcoal chain in biomass_domestic.** Kiln release and charcoal stove release use `air_rerelease`; natural nuclides are memo. Alternative: leave charcoal out until a radionuclide measurement exists.
12. **Cs-137 in wood.** World default by four eras (anchored to US 1991 and Austria 2021) plus Sweden, Ukraine, Belarus rows. The BLR and UKR rows are extrapolations (the BLR high is the regulatory limit, 740 Bq/kg). Alternative: world default only.
13. **Benchmark B4.** Replace the factor-3 test with a range test (choice for the verifier brief).
14. **Peat analogues from coal.** Escaping fraction (1800-1989), group enrichment (11 rows) and household smoke fraction are borrowed from coal factors. No peat measurement exists.
15. **Peat negligibility.** Counted peat is 0.02-0.07% of the stream at the centre in 1990-2020. I kept it modelled because D44 makes it a flow and the data exist; you may instead mark it negligible (shown, not modelled in detail).
16. **Peat dry fraction 0.52** and **wood dry fraction 0.75** are derived from unit conversions, not measured (moisture bases are not stated by UNSD/FAO).
17. **`technology` column.** Left empty on all rows, as in coal (pipeline attributes by electricity share). Geothermal rows could carry `geothermal`.
18. **Peat before 1990** is absent (G6). Option: a USGS-based extension needs an energy-share factor with no source.
19. **S0563 charcoal yield (0.19-0.31)** comes from the Task 1.6 verification and has not been re-read by anyone.

## 6. Proposals for ε and seepage (notes only; `residue_types.csv` and `residue_seepage_by_group.csv` untouched)

Meaning follows D60: Rn-222 ε is the emanation coefficient used as an upper bound of effective exhalation; Rn-220 ε is effective exhalation, $\epsilon_{220}=\mathrm{em}\times f$ with $f=(L/H)\tanh(H/L)$, L = 0.005 / 0.01 / 0.02 m, low = em_low x f(L_low, H_high), central = em_c x f(L_c, H_geomean), high = em_high x f(L_high, H_low).

| residue type | needed? | ε Rn-222 low / central / high | ε Rn-220 low / central / high | seepage per a low / central / high | Basis |
|---|---|---|---|---|---|
| `peat_ash` | Yes (counted rows) | 0.005 / 0.03 / 0.15 | 6.7e-7 / 1.3e-5 / 5.0e-4 | already filled: 7e-7 / 6e-6 / 6e-5; K40 0.002 / 0.01 / 0.04 (per-group table) | Fly-ash analogue (coal_fly_ash): S0242, S0243, S0244. H = 4-15 m is the coal-ash range; no peat-ash landfill thickness is sourced (SSI gives a 75,000 t deposit, no depth). Low confidence |
| `geothermal_scale` | Yes (counted rows, if choice 3 keeps them) | 0.02 / 0.05 / 0.25 | 1.7e-5 / 4.1e-4 / 8.0e-3 | 3e-9 / 3e-8 / 4e-6 | Rn-222: barite and injection-well pipe scale 0.020-0.063 (S0991), Sakoda mineral 0.03 (S0242); high 0.25 allows soil-like sludge. Replaces the Phase 1 placeholder 0.2 (0.05-0.35), which is not supported for scale. Rn-220: the coal_mine_water_sludge calculation (em 0.01 / 0.05 / 0.20, H 0.5-3 m), an assumption. Seepage: og_scale triple (barite scale, grade C). Iceland stores scale sealed on site (S0512), Italy under NORM rules (S0501), so seepage may be zero for some plants |
| `geothermal_brine` | No (no rows, G4) | - | - | - | - |
| `biomass_ash`, `biomass_domestic_ash` | No (no data rows, section 3) | - | - | biomass_ash already filled (K-40 soluble) | Memo series have no engine processing |

## 7. Proposed stream-script outline for `docs/OTHER_SPEC.md`

**Substreams and stages (vocab only).** `geothermal` / stage `geothermal`; `biomass_peat` / stage `biomass_peat` (plants, heat, industrial); `biomass_domestic` / stage `biomass_peat` (household peat, household wood, charcoal chain). `hydro` and stage `construction`: no rows. Master country is `XXX` for world series and the ISO code otherwise; factor region and activity country stay `XWL` (COAL_SPEC 11.1 convention). `allocation_variant` default, `allocation_rule` none, `embedded_fuel` false, `basis` modelled, `technology` empty.

**Geothermal.**
- Driver: `elec_gen_geothermal`, per country; the rest-of-world row is XWL minus the listed countries (independent difference); 2025 XWL is 0 in the spine (out-of-scope issue 1) so the script must log `no_driver` rather than write zeros.
- Rows: Rn222+ liberated `air_vented_gas` (other:0001-0003; exact-region beats XWL). Scale: mass other:0004, then Ra226+, Ra228+, Pb210+, Po210, K40 impounded `geothermal_scale` (other:0005-0009). Pre-1950 file from 1916 (the spine), flow only.
- Reisolated: no rows.

**Peat** (drivers `peat_power_heat_t` for plants; `peat_household_t` for household; "other peat use" = `peat_supply_t` minus both, independent difference, negative to 0, substream biomass_peat; years 1990-2024 only).
- Selectors: dry fraction (driver = the series, group/tier/route/residue blank: other:0010, 0011, 0012); ash yield (driver blank, residue `peat_ash`, group blank, tier blank: other:0013); fly share (driver `peat_power_heat_t`, residue `peat_ash`, group and tier blank: other:0014); concentrations (residue `peat_ash`, group $g$, tier blank, driver blank: other:0015-0025); escaping fraction $p_y$ (driver `peat_power_heat_t`, tier liberated, route `air_stack`, group blank: other:0026-0027); enrichment $e_g$ (same plus group: other:0028-0038, also used for household smoke and the residual); route shares (plants: driver `peat_power_heat_t`, tier impounded / dispersed, residue `peat_ash`: other:0039-0040; household: driver `peat_household_t`: other:0041-0042); household smoke fraction $s$ (driver `peat_household_t`, tier liberated: other:0043).
- Groups: `U238+, U234, Th230, Ra226+, Pb210+, Po210, U235+, Th232, Ra228+, Th228+, K40` (11; U-234 and Th-230 are kept so Ra-226 stays supported, as in coal).
- Rows per substream: stack (liberated `air_stack`), ash impounded and dispersed (residue `peat_ash`), all counted.
- Cs-137 on peat: conc by era (other:0044-0047, group `Cs137+`, residue `peat_ash`); stack part = ash-borne x share (plants other:0067 via driver `wood_fuel_t`; household other:0068 via driver `household_fuelwood_m3`) -> liberated `air_rerelease`; remainder -> `memo_biosphere` (no residue, no route).
- Rn: none. Pre-1990 rows: none (G6).

**Wood** (driver `wood_fuel_t` by country 1961-2025; household `household_fuelwood_m3` 1990+).
- Mass partition in the engine reading above. Memo natural rows: groups K40, Pb210+, Po210, Ra226+, Ra228+ with other:0052-0056 (driver `wood_fuel_t`, tier `memo_biosphere`, group $g$) x dry mass of each substream: `biomass_peat` gets $D_{\mathrm{pl}}$, `biomass_domestic` gets $D_{\mathrm{hh}}+D_{\mathrm{ch}}$.
- Cs-137: fuel concentration by region and era (other:0057-0066; exact region beats XWL); released part by substream: plants $\times$ other:0067; household $\times$ other:0068; charcoal wood $\times\big[x_k+(1-x_k)y\big]$ with $x_k$ = other:0069 (kiln) and $y$ = other:0070 (charcoal stove, applies to charcoal burned; the factor driver is `household_charcoal_t`, so the script applies it to the retained share); remainder to `memo_biosphere`. Release rows: liberated, route `air_rerelease`, group `Cs137+`, flow.
- **No impounded, dispersed or reisolated wood rows.** No Rn rows.

**Drivers needing a new lib helper or spec rule.** Ratio of two Bounds (household share = `household_fuelwood_m3` over `wood_fuel_m3`, capped at 1) is not in LIB_SPEC; I avoided it by using the mass form (m3 x 0.725 x 0.75) with the share only as a fallback. Division by yield is avoided by registering the inverse (3.85 t wood per t charcoal).

**Checks.** (a) Schema/validator pass. (b) Candidate groups: all 11 natural groups appear in peat ash tiers every year with peat driver data; Rn222+ every year with a geothermal driver; five wood memo groups every year with a wood driver. (c) Conservation: peat stack + residue shares = ash-borne (central, 1e-9); wood Cs-137 re-release + memo ash = fuel Cs-137; the two peat route shares sum to 1 at the centre. (d) Determinism. (e) Benchmarks per section 2, B1-B6. (f) Hand-computed rows: a geothermal ITA row, a USA row, a scale row, a peat plant stack row with cap, a household peat row, a wood memo K40 row, a Cs-137 re-release row, a charcoal Cs row, a SWE override row. (g) Fixtures: missing driver year, negative peat residual, hh wood above FAO total, charcoal above total, XWL 2025 zero.
**Log kinds.** `no_factor`, `no_driver`, `negative_residual`, `household_wood_capped`, `charcoal_wood_capped`, `cap_applied`, `predecessor_dropped` (DEU/DDR, CSK/CZE if present), `lib_warning`.
**Memo and re-release reporting.** Re-release rows carry notes text `re-release`; memo rows are flow only, outside every tier total, never `opening_stock`.
**Known limits to carry onto the rows.** Rn-222 world value from two fields; analogue peat factors; plant wood largely missing; Cs-137 time shape and regional rows extrapolated; peat absent before 1990.

## 8. Inaccessible or partial sources (URLs for Steve), most to least important

1. **'Health impacts of geothermal energy', LLNL preprint UCRL-85334 (author initials D.W.; year and surname not read; may hold Geysers, Larderello, Wairakei and Cerro Prieto radon emissions, content unverified)**: OSTI blocks automated access. https://www.osti.gov/servlets/purl/6388562
2. **George et al. (1980), primary for Larderello 8 Ci/d and Geysers radon**: not located; cited in S0509 (https://va.mite.gov.it/File/Documento/160922) and UNSCEAR.
3. **Radon-222 measurements at Wairakei, Broadlands and Ngawha (SGP-TR-40, CONF-791235, so about December 1979)**: only the OSTI landing page was read; no figures. https://www.osti.gov/biblio/7369330
4. **S0508 Whitehead & Ditchburn 1996 (Rn-220 and Rn-222 in NZ steam)**: paywalled; the only thoron evidence. https://link.springer.com/article/10.1007/BF02071237
5. **S0513 Pepin et al. 2023 (Cs-137 in firewood and biomass combustion review; likely best compilation of ash enrichment and emission factors)**: paywalled. https://doi.org/10.1093/rpd/ncad077
6. **S1401 Helariutta, Rantavaara & Lehtovaara (2000), radionuclides in peat bogs and energy peat**: abstract only. https://inis.iaea.org/records/sycm0-fd680
7. **S0563 FAO Forestry Paper 41 section 8.12 (charcoal mass yield 0.26)**: supplied on Task 1.6 verification, never re-read. https://www.fao.org/4/X5328E/X5328E00.htm
8. **S0551 Yoshida et al. 2016, S0550 Zhou et al. 2016, S0549 Amiro 1996 (Cs release on combustion)**: paywalled; numbers used here come from the Task 1.6 notes. https://www.frames.gov/catalog/36657 (S0549)
9. **S0559 Tasdemir et al. 2026 (natural radionuclides in 15 wood species)**: paywalled. https://doi.org/10.1007/s10967-026-10807-1
10. **S0507 Stewart et al. 1993 GNS SR 93/38 (Wairakei decay series)**: https://shop.gns.cri.nz/sr_1993-38-pdf/
11. **S0506 D'Amore et al. 1978 (Rn-222 in Larderello wells)**: https://link.springer.com/article/10.1007/BF00879751
12. **Ravila (1998), Lund thesis on radiocaesium in the forest industry (ash and Cs behaviour in pulp mills; abstract only)**: https://lup.lub.lu.se/record/38831
13. **S0518 Rantavaara & Aro 2009**: abstract only; full PDF linked from https://www.radioprotection.org/10.1051/radiopro/20095165
14. **S0522 Hertwich et al. 2015** (material intensity lead for construction): https://doi.org/10.1073/pnas.1312753111
15. **S0525 INIS peat record**: same record as S1401; S0525 is in `research/other/sources_task16.csv` but is missing from `data/sources.csv` (out-of-scope issue 2).

## 9. Out-of-scope issues noticed (not fixed)

1. `data/activity/electricity_generation.csv`: `elec_gen_geothermal` for XWL in 2025 is 0 (basis `measured`, IRENA 2025 not yet published); country rows for 2025 are absent. `elec_gen_hydro` and `elec_gen_biomass` 2025 look populated. A zero would silently give zero geothermal radon for 2025.
2. `data/sources.csv` lacks S0525 although `research/other/sources_task16.csv` lists it. S1401 duplicates it with the title and authors found now.
3. UNSD household fuelwood (`household_fuelwood_m3`) exceeds FAOSTAT wood fuel (`wood_fuel_m3`) for about 35-40% of countries (India 1.15, USA 1.31 in 2010), and China is absent from UNSD. The activity builder's note N2527 calls the sum "not a strict lower bound"; the ratio is therefore unreliable country by country.
4. USGS `prod_peat` XWL drops from 170 Mt (1991) to 29 Mt (1992): a coverage break (USSR), not a production change; the activity notes do not say so.
5. `research/other/notes.md` states the Wairakei and Cerro Prieto reservoirs have radon "about 40 times lower" than The Geysers (S0505); S0502 Table 4 gives Wairakei fluid 630 Bq/L against The Geysers 620 Bq/L. The two are different quantities and I could not reconcile them; it matters for the non-vapour fleet (gap G2).
6. `research/other/household_biomass_notes.md` section 5 recommends Option A (new stage); D45 chose Option B. The notes file is otherwise unchanged.
