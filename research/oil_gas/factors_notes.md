# Oil and gas factor registry: notes (Task 2.3, step 1)

Output: `data/factors/oil_gas.csv` (109 rows `oil_gas:0001`-`0109`: production 73, processing_transport 4, abandonment_scrap 7, oil_sands_mining 3, drilling 22; construction 0). New sources `S1200`-`S1209` are in `research/oil_gas/sources_factors.csv` (not yet merged into `data/sources.csv`, so the committed tree reports T04 unresolved-source errors until they are merged; with them merged the validator prints `OK: no issues`). Generator: scratchpad `og/build_og.py` (not in the repository). No pipeline code or tests were written.

## 0. Engine reading of the factors (my specification; the stream spec should confirm)

All activity values are HEAD-nuclide activity (METHODS 3.2, 4.1a, D24); the engine applies the group multiplier. Unit-1 rows are shares or ratios that apply to a Bq quantity built from other rows. Because `select` has no substream or product column, rows are separated by `driver_series`, `region`, `residue_type` and `tier`; the key tuple (stage, driver_series, group, tier, route, residue_type, region) is unique over overlapping years (checked by the generator).

- **Produced-water activity** of group $g$ in region $c$, year $y$: with $V$ = `produced_water_m3`, $u$ = unconventional fraction (rows 0011-0018, selected with `driver_series='produced_water_unconv_share'` and blank group), $C^{conv}_g$ (0001-0010 with driver `produced_water_m3`) and $C^{unc}_g$ (same rows with driver `produced_water_unconv_share`):
$$A_{g}=V\left[(1-u)\,C^{conv}_g+u\,C^{unc}_g\right]$$
  Rest of world = `XWL` minus `USA` (independent difference, as coal). The `produced_water_unconv_share` activity series (2017 only) is a cross-check, not a multiplier.
- **Tier split of $A_g$** (all groups alike): rows 0019-0046, selected by tier with `driver_series='produced_water_m3'`; reisolated and dispersed carry `og_produced_water`, impounded (evaporation pits) `og_sludge`, liberated route `water_produced_discharge`. Central shares sum to 1 per region and era.
- **Solids** (Ra-226+ and Ra-228+ only): $S_{g,r}=A_g\,\sigma_{g,r}$ for residue $r\in\{$`og_scale`, `og_sludge`$\}$ (0047-0050, additive to the water, not subtracted). Pb-210+ in solids $=0.05\times S_{\mathrm{Ra226+},r}$ (0051-0052; reservoir-derived Pb-210 only; supported Pb-210 is the engine's ingrowth).
- **Removed solids** (booked at `production`): $S\,(1-\phi)$ for scale ($\phi$ = row 0078) and $S$ for sludge, split by tier with rows 0053-0070 (blank driver; liberated rows carry the source residue type only to make the key unique, and the master row has no residue).
- **Retained scale** (booked at `abandonment_scrap` in the SAME year, creation-year windows with the ~20 year retirement lag built into the era boundaries, rows 0079-0084): $S\,\phi$ split to impounded `og_scale` and dispersed `og_scaled_scrap`. No Ra-228 survival factor is applied: decay of unmoved activity is the engine's job and a second factor would double-count it.
- **Gas**: delivered Rn (0074) and vented Rn (0075) are Bq per m3 of `gas_production_m3`; Pb-210 deposit (0076) likewise, tier impounded `og_processing_residue`. Oil radon (0077) and flaring (0071-0073) are per tonne of `oil_production_t`.
- **Oil sands** (0085-0087) per tonne of ore processed; driver does not exist yet (B1). **Drilling** (0088-0098 vertical, driver `us_wells_drilled_total`, 1949-2010; 0099-0109 horizontal, driver missing, B2): unit `Bq/1`, apply to the well count.
- Chronic radon exhalation and seepage from impounded/dispersed holdings are engine processes. No rows for them.

## 1. Factor table

| id | what | group / tier / route / residue | driver | region | years | low / central / high | unit | basis |
|---|---|---|---|---|---|---|---|---|
| oil_gas:0001 | production: Produced-water radium-226 concentration (post-precipitation), conventional, world default | Ra226+ | produced_water_m3 | XWL | 1950-2025 | 1e+03 / 5e+03 / 2e+04 | Bq/m3 | compiled |
| oil_gas:0002 | production: Produced-water radium-226 concentration, conventional, USA | Ra226+ | produced_water_m3 | USA | 1950-2025 | 1.5e+03 / 6e+03 / 2.5e+04 | Bq/m3 | compiled |
| oil_gas:0003 | production: Produced-water radium-226 concentration, unconventional (shale and tight), world default | Ra226+ | produced_water_unconv_share | XWL | 1950-2025 | 1e+04 / 3e+04 / 8e+04 | Bq/m3 | compiled |
| oil_gas:0004 | production: Produced-water radium-228 concentration (post-precipitation), conventional, world default | Ra228+ | produced_water_m3 | XWL | 1950-2025 | 800 / 4e+03 / 2e+04 | Bq/m3 | compiled |
| oil_gas:0005 | production: Produced-water radium-228 concentration, conventional, USA | Ra228+ | produced_water_m3 | USA | 1950-2025 | 3e+03 / 1e+04 / 4e+04 | Bq/m3 | compiled |
| oil_gas:0006 | production: Produced-water radium-228 concentration, unconventional (shale and tight), world default | Ra228+ | produced_water_unconv_share | XWL | 1950-2025 | 5e+03 / 2e+04 / 6e+04 | Bq/m3 | compiled |
| oil_gas:0007 | production: Produced-water potassium-40 concentration (post-precipitation), conventional, world default | K40 | produced_water_m3 | XWL | 1950-2025 | 3e+03 / 1e+04 / 3e+04 | Bq/m3 | compiled |
| oil_gas:0008 | production: Produced-water potassium-40 concentration, unconventional (shale and tight), world default | K40 | produced_water_unconv_share | XWL | 1950-2025 | 1e+04 / 4e+04 / 1.1e+05 | Bq/m3 | compiled |
| oil_gas:0009 | production: Produced-water lead-210 concentration (post-precipitation), conventional, world default | Pb210+ | produced_water_m3 | XWL | 1950-2025 | 15 / 250 / 3e+03 | Bq/m3 | modelled |
| oil_gas:0010 | production: Produced-water lead-210 concentration, unconventional (shale and tight), world default | Pb210+ | produced_water_unconv_share | XWL | 1950-2025 | 100 / 1.5e+03 / 2e+04 | Bq/m3 | modelled |
| oil_gas:0011 | production: Unconventional (shale and tight) fraction of produced water, USA, 1950-2005 |  | produced_water_unconv_share | USA | 1950-2005 | 0 / 0.005 / 0.02 | 1 | extrapolated |
| oil_gas:0012 | production: Unconventional (shale and tight) fraction of produced water, USA, 2006-2010 |  | produced_water_unconv_share | USA | 2006-2010 | 0.01 / 0.04 / 0.08 | 1 | interpolated |
| oil_gas:0013 | production: Unconventional (shale and tight) fraction of produced water, USA, 2011-2016 |  | produced_water_unconv_share | USA | 2011-2016 | 0.06 / 0.12 / 0.16 | 1 | interpolated |
| oil_gas:0014 | production: Unconventional (shale and tight) fraction of produced water, USA, 2017-2017 |  | produced_water_unconv_share | USA | 2017-2017 | 0.1 / 0.16 / 0.22 | 1 | compiled |
| oil_gas:0015 | production: Unconventional (shale and tight) fraction of produced water, USA, 2018-2025 |  | produced_water_unconv_share | USA | 2018-2025 | 0.15 / 0.2 / 0.28 | 1 | extrapolated |
| oil_gas:0016 | production: Unconventional (shale and tight) fraction of produced water, XWL, 1950-2005 |  | produced_water_unconv_share | XWL | 1950-2005 | 0 / 0 / 0.01 | 1 | extrapolated |
| oil_gas:0017 | production: Unconventional (shale and tight) fraction of produced water, XWL, 2006-2015 |  | produced_water_unconv_share | XWL | 2006-2015 | 0 / 0.01 / 0.03 | 1 | extrapolated |
| oil_gas:0018 | production: Unconventional (shale and tight) fraction of produced water, XWL, 2016-2025 |  | produced_water_unconv_share | XWL | 2016-2025 | 0.005 / 0.03 / 0.08 | 1 | extrapolated |
| oil_gas:0019 | production: Fate of produced-water activity (all groups), USA 1950-1969: re-injected, disposed down-hole, used for EOR or commercially disposed (reisolated) | reisolated/og_produced_water | produced_water_m3 | USA | 1950-1969 | 0.35 / 0.58 / 0.85 | 1 | extrapolated |
| oil_gas:0020 | production: Fate of produced-water activity (all groups), USA 1950-1969: evaporation pits and ponds (impounded) | impounded/og_sludge | produced_water_m3 | USA | 1950-1969 | 0.05 / 0.25 / 0.45 | 1 | extrapolated |
| oil_gas:0021 | production: Fate of produced-water activity (all groups), USA 1950-1969: discharged to surface water or sea (liberated) | liberated/water_produced_discharge | produced_water_m3 | USA | 1950-1969 | 0.03 / 0.15 / 0.3 | 1 | extrapolated |
| oil_gas:0022 | production: Fate of produced-water activity (all groups), USA 1950-1969: spread on roads or land (dispersed) | dispersed/og_produced_water | produced_water_m3 | USA | 1950-1969 | 0 / 0.02 / 0.08 | 1 | extrapolated |
| oil_gas:0023 | production: Fate of produced-water activity (all groups), USA 1970-1999: re-injected, disposed down-hole, used for EOR or commercially disposed (reisolated) | reisolated/og_produced_water | produced_water_m3 | USA | 1970-1999 | 0.7 / 0.85 / 0.93 | 1 | interpolated |
| oil_gas:0024 | production: Fate of produced-water activity (all groups), USA 1970-1999: evaporation pits and ponds (impounded) | impounded/og_sludge | produced_water_m3 | USA | 1970-1999 | 0.01 / 0.06 / 0.15 | 1 | interpolated |
| oil_gas:0025 | production: Fate of produced-water activity (all groups), USA 1970-1999: discharged to surface water or sea (liberated) | liberated/water_produced_discharge | produced_water_m3 | USA | 1970-1999 | 0.03 / 0.09 / 0.2 | 1 | interpolated |
| oil_gas:0026 | production: Fate of produced-water activity (all groups), USA 1970-1999: spread on roads or land (dispersed) | dispersed/og_produced_water | produced_water_m3 | USA | 1970-1999 | 0 / 0 / 0.01 | 1 | interpolated |
| oil_gas:0027 | production: Fate of produced-water activity (all groups), USA 2000-2009: re-injected, disposed down-hole, used for EOR or commercially disposed (reisolated) | reisolated/og_produced_water | produced_water_m3 | USA | 2000-2009 | 0.9 / 0.949 / 0.97 | 1 | compiled |
| oil_gas:0028 | production: Fate of produced-water activity (all groups), USA 2000-2009: evaporation pits and ponds (impounded) | impounded/og_sludge | produced_water_m3 | USA | 2000-2009 | 0 / 0.0105 / 0.04 | 1 | compiled |
| oil_gas:0029 | production: Fate of produced-water activity (all groups), USA 2000-2009: discharged to surface water or sea (liberated) | liberated/water_produced_discharge | produced_water_m3 | USA | 2000-2009 | 0.02 / 0.04 / 0.06 | 1 | compiled |
| oil_gas:0030 | production: Fate of produced-water activity (all groups), USA 2000-2009: spread on roads or land (dispersed) | dispersed/og_produced_water | produced_water_m3 | USA | 2000-2009 | 0.0001 / 0.0005 / 0.003 | 1 | compiled |
| oil_gas:0031 | production: Fate of produced-water activity (all groups), USA 2010-2014: re-injected, disposed down-hole, used for EOR or commercially disposed (reisolated) | reisolated/og_produced_water | produced_water_m3 | USA | 2010-2014 | 0.85 / 0.911 / 0.95 | 1 | compiled |
| oil_gas:0032 | production: Fate of produced-water activity (all groups), USA 2010-2014: evaporation pits and ponds (impounded) | impounded/og_sludge | produced_water_m3 | USA | 2010-2014 | 0.01 / 0.034 / 0.06 | 1 | compiled |
| oil_gas:0033 | production: Fate of produced-water activity (all groups), USA 2010-2014: discharged to surface water or sea (liberated) | liberated/water_produced_discharge | produced_water_m3 | USA | 2010-2014 | 0.03 / 0.054 / 0.08 | 1 | compiled |
| oil_gas:0034 | production: Fate of produced-water activity (all groups), USA 2010-2014: spread on roads or land (dispersed) | dispersed/og_produced_water | produced_water_m3 | USA | 2010-2014 | 0.0001 / 0.0005 / 0.003 | 1 | compiled |
| oil_gas:0035 | production: Fate of produced-water activity (all groups), USA 2015-2025: re-injected, disposed down-hole, used for EOR or commercially disposed (reisolated) | reisolated/og_produced_water | produced_water_m3 | USA | 2015-2025 | 0.88 / 0.941 / 0.97 | 1 | compiled |
| oil_gas:0036 | production: Fate of produced-water activity (all groups), USA 2015-2025: evaporation pits and ponds (impounded) | impounded/og_sludge | produced_water_m3 | USA | 2015-2025 | 0 / 0.004 / 0.02 | 1 | compiled |
| oil_gas:0037 | production: Fate of produced-water activity (all groups), USA 2015-2025: discharged to surface water or sea (liberated) | liberated/water_produced_discharge | produced_water_m3 | USA | 2015-2025 | 0.03 / 0.055 / 0.08 | 1 | compiled |
| oil_gas:0038 | production: Fate of produced-water activity (all groups), USA 2015-2025: spread on roads or land (dispersed) | dispersed/og_produced_water | produced_water_m3 | USA | 2015-2025 | 0.0001 / 0.0005 / 0.003 | 1 | compiled |
| oil_gas:0039 | production: Fate of produced-water activity (all groups), XWL 1950-1969: re-injected, disposed down-hole, used for EOR or commercially disposed (reisolated) | reisolated/og_produced_water | produced_water_m3 | XWL | 1950-1969 | 0.2 / 0.45 / 0.7 | 1 | extrapolated |
| oil_gas:0040 | production: Fate of produced-water activity (all groups), XWL 1950-1969: evaporation pits and ponds (impounded) | impounded/og_sludge | produced_water_m3 | XWL | 1950-1969 | 0.05 / 0.15 / 0.3 | 1 | extrapolated |
| oil_gas:0041 | production: Fate of produced-water activity (all groups), XWL 1950-1969: discharged to surface water or sea (liberated) | liberated/water_produced_discharge | produced_water_m3 | XWL | 1950-1969 | 0.15 / 0.38 / 0.6 | 1 | extrapolated |
| oil_gas:0042 | production: Fate of produced-water activity (all groups), XWL 1950-1969: spread on roads or land (dispersed) | dispersed/og_produced_water | produced_water_m3 | XWL | 1950-1969 | 0 / 0.02 / 0.08 | 1 | extrapolated |
| oil_gas:0043 | production: Fate of produced-water activity (all groups), XWL 1970-2025: re-injected, disposed down-hole, used for EOR or commercially disposed (reisolated) | reisolated/og_produced_water | produced_water_m3 | XWL | 1970-2025 | 0.45 / 0.72 / 0.88 | 1 | compiled |
| oil_gas:0044 | production: Fate of produced-water activity (all groups), XWL 1970-2025: evaporation pits and ponds (impounded) | impounded/og_sludge | produced_water_m3 | XWL | 1970-2025 | 0 / 0.03 / 0.1 | 1 | compiled |
| oil_gas:0045 | production: Fate of produced-water activity (all groups), XWL 1970-2025: discharged to surface water or sea (liberated) | liberated/water_produced_discharge | produced_water_m3 | XWL | 1970-2025 | 0.1 / 0.25 / 0.42 | 1 | compiled |
| oil_gas:0046 | production: Fate of produced-water activity (all groups), XWL 1970-2025: spread on roads or land (dispersed) | dispersed/og_produced_water | produced_water_m3 | XWL | 1970-2025 | 0 / 0.0005 / 0.003 | 1 | compiled |
| oil_gas:0047 | production: Radium solids-bound fraction: radium-226 in scale formed per unit of outlet-water radium-226 | Ra226+/og_scale | - | XWL | 1950-2025 | 0.0004 / 0.004 / 0.016 | 1 | modelled |
| oil_gas:0048 | production: Radium solids-bound fraction: radium-226 in sludge formed per unit of outlet-water radium-226 | Ra226+/og_sludge | - | XWL | 1950-2025 | 0.0006 / 0.006 / 0.024 | 1 | modelled |
| oil_gas:0049 | production: Radium solids-bound fraction: radium-228 in scale formed per unit of outlet-water radium-228 | Ra228+/og_scale | - | XWL | 1950-2025 | 0.0004 / 0.004 / 0.016 | 1 | modelled |
| oil_gas:0050 | production: Radium solids-bound fraction: radium-228 in sludge formed per unit of outlet-water radium-228 | Ra228+/og_sludge | - | XWL | 1950-2025 | 0.0006 / 0.006 / 0.024 | 1 | modelled |
| oil_gas:0051 | production: Pb-210 present at formation of scale from reservoir-derived Pb-210, ratio to Ra-226 head activity in the same solids | Pb210+/og_scale | - | XWL | 1950-2025 | 0.005 / 0.05 / 0.5 | 1 | modelled |
| oil_gas:0052 | production: Pb-210 present at formation of sludge from reservoir-derived Pb-210, ratio to Ra-226 head activity in the same solids | Pb210+/og_sludge | - | XWL | 1950-2025 | 0.005 / 0.05 / 0.5 | 1 | modelled |
| oil_gas:0053 | production: Fate of removed scale (all groups), 1950-1984: controlled disposal or storage (impounded) | impounded/og_scale | - | XWL | 1950-1984 | 0.15 / 0.35 / 0.6 | 1 | extrapolated |
| oil_gas:0054 | production: Fate of removed scale (all groups), 1950-1984: dispersed (land-farming, spreading, scrap sold on) | dispersed/og_scale | - | XWL | 1950-1984 | 0.3 / 0.6 / 0.85 | 1 | extrapolated |
| oil_gas:0055 | production: Fate of removed scale (all groups), 1950-1984: discharged offshore or to surface water (liberated) | liberated/water_produced_discharge/og_scale | - | XWL | 1950-1984 | 0 / 0.05 / 0.15 | 1 | extrapolated |
| oil_gas:0056 | production: Fate of removed scale (all groups), 1985-1999: controlled disposal or storage (impounded) | impounded/og_scale | - | XWL | 1985-1999 | 0.4 / 0.7 / 0.9 | 1 | extrapolated |
| oil_gas:0057 | production: Fate of removed scale (all groups), 1985-1999: dispersed (land-farming, spreading, scrap sold on) | dispersed/og_scale | - | XWL | 1985-1999 | 0.05 / 0.2 / 0.4 | 1 | extrapolated |
| oil_gas:0058 | production: Fate of removed scale (all groups), 1985-1999: discharged offshore or to surface water (liberated) | liberated/water_produced_discharge/og_scale | - | XWL | 1985-1999 | 0 / 0.1 / 0.2 | 1 | extrapolated |
| oil_gas:0059 | production: Fate of removed scale (all groups), 2000-2025: controlled disposal or storage (impounded) | impounded/og_scale | - | XWL | 2000-2025 | 0.55 / 0.85 / 0.95 | 1 | extrapolated |
| oil_gas:0060 | production: Fate of removed scale (all groups), 2000-2025: dispersed (land-farming, spreading, scrap sold on) | dispersed/og_scale | - | XWL | 2000-2025 | 0 / 0.05 / 0.2 | 1 | extrapolated |
| oil_gas:0061 | production: Fate of removed scale (all groups), 2000-2025: discharged offshore or to surface water (liberated) | liberated/water_produced_discharge/og_scale | - | XWL | 2000-2025 | 0 / 0.1 / 0.25 | 1 | extrapolated |
| oil_gas:0062 | production: Fate of removed sludge (all groups), 1950-1984: controlled disposal or storage (impounded) | impounded/og_sludge | - | XWL | 1950-1984 | 0.2 / 0.4 / 0.6 | 1 | extrapolated |
| oil_gas:0063 | production: Fate of removed sludge (all groups), 1950-1984: dispersed (land-farming, spreading, scrap sold on) | dispersed/og_sludge | - | XWL | 1950-1984 | 0.3 / 0.5 / 0.75 | 1 | extrapolated |
| oil_gas:0064 | production: Fate of removed sludge (all groups), 1950-1984: discharged offshore or to surface water (liberated) | liberated/water_produced_discharge/og_sludge | - | XWL | 1950-1984 | 0 / 0.1 / 0.2 | 1 | extrapolated |
| oil_gas:0065 | production: Fate of removed sludge (all groups), 1985-1999: controlled disposal or storage (impounded) | impounded/og_sludge | - | XWL | 1985-1999 | 0.15 / 0.3 / 0.55 | 1 | extrapolated |
| oil_gas:0066 | production: Fate of removed sludge (all groups), 1985-1999: dispersed (land-farming, spreading, scrap sold on) | dispersed/og_sludge | - | XWL | 1985-1999 | 0.3 / 0.6 / 0.8 | 1 | extrapolated |
| oil_gas:0067 | production: Fate of removed sludge (all groups), 1985-1999: discharged offshore or to surface water (liberated) | liberated/water_produced_discharge/og_sludge | - | XWL | 1985-1999 | 0 / 0.1 / 0.2 | 1 | extrapolated |
| oil_gas:0068 | production: Fate of removed sludge (all groups), 2000-2025: controlled disposal or storage (impounded) | impounded/og_sludge | - | XWL | 2000-2025 | 0.6 / 0.8 / 0.95 | 1 | extrapolated |
| oil_gas:0069 | production: Fate of removed sludge (all groups), 2000-2025: dispersed (land-farming, spreading, scrap sold on) | dispersed/og_sludge | - | XWL | 2000-2025 | 0.02 / 0.1 / 0.3 | 1 | extrapolated |
| oil_gas:0070 | production: Fate of removed sludge (all groups), 2000-2025: discharged offshore or to surface water (liberated) | liberated/water_produced_discharge/og_sludge | - | XWL | 2000-2025 | 0 / 0.1 / 0.2 | 1 | extrapolated |
| oil_gas:0071 | production: Rn-222 released by associated-gas flaring per tonne of crude produced, world 1900-1993 | Rn222+/liberated/air_stack | oil_production_t | XWL | 1900-1993 | 6.39e+03 / 3.12e+04 / 8.48e+04 | Bq/t | extrapolated |
| oil_gas:0072 | production: Rn-222 released by associated-gas flaring per tonne of crude produced, world 1994-2008 | Rn222+/liberated/air_stack | oil_production_t | XWL | 1994-2008 | 5.96e+03 / 2.5e+04 / 5.72e+04 | Bq/t | modelled |
| oil_gas:0073 | production: Rn-222 released by associated-gas flaring per tonne of crude produced, world 2009-2025 | Rn222+/liberated/air_stack | oil_production_t | XWL | 2009-2025 | 5.52e+03 / 2.31e+04 / 5.23e+04 | Bq/t | modelled |
| oil_gas:0074 | processing_transport: Rn-222 in marketed gas delivered to end users (reaches burners and kitchens), per m3 of gas produced | Rn222+/liberated/air_delivered_gas | gas_production_m3 | XWL | 1900-2025 | 47.6 / 300 / 779 | Bq/m3 | compiled |
| oil_gas:0075 | processing_transport: Rn-222 in vented and fugitive gas released at well sites, plants and pipelines, per m3 of gas produced | Rn222+/liberated/air_vented_gas | gas_production_m3 | XWL | 1900-2025 | 1.71 / 12.5 / 42.4 | Bq/m3 | modelled |
| oil_gas:0076 | processing_transport: Pb-210 formed from Rn-222 that decays inside gas wells, pipelines and processing plants and plates out (films, scale, sludge), per m3 of gas produced | Pb210+/impounded/og_processing_residue | gas_production_m3 | XWL | 1900-2025 | 0.0163 / 0.123 / 0.311 | Bq/m3 | modelled |
| oil_gas:0077 | processing_transport: Rn-222 released with crude oil handled and refined (equilibrium with Ra-226 in crude), per tonne of crude produced | Rn222+/liberated/air_stack | oil_production_t | XWL | 1900-2025 | 200 / 1e+03 / 1.3e+04 | Bq/t | compiled |
| oil_gas:0078 | abandonment_scrap: Fraction of newly formed scale that stays on tubulars and equipment until retirement | og_scale | - | XWL | 1950-2025 | 0.2 / 0.5 / 0.8 | 1 | modelled |
| oil_gas:0079 | abandonment_scrap: Fate of scale still on equipment at retirement (all groups), booked by creation year 1950-1964: controlled disposal or storage (impounded) | impounded/og_scale | - | XWL | 1950-1964 | 0.05 / 0.15 / 0.4 | 1 | extrapolated |
| oil_gas:0080 | abandonment_scrap: Fate of scale still on equipment at retirement (all groups), booked by creation year 1950-1964: dispersed (land-farming, spreading, scrap sold on) | dispersed/og_scaled_scrap | - | XWL | 1950-1964 | 0.6 / 0.85 / 0.95 | 1 | extrapolated |
| oil_gas:0081 | abandonment_scrap: Fate of scale still on equipment at retirement (all groups), booked by creation year 1965-1979: controlled disposal or storage (impounded) | impounded/og_scale | - | XWL | 1965-1979 | 0.2 / 0.5 / 0.8 | 1 | extrapolated |
| oil_gas:0082 | abandonment_scrap: Fate of scale still on equipment at retirement (all groups), booked by creation year 1965-1979: dispersed (land-farming, spreading, scrap sold on) | dispersed/og_scaled_scrap | - | XWL | 1965-1979 | 0.2 / 0.5 / 0.8 | 1 | extrapolated |
| oil_gas:0083 | abandonment_scrap: Fate of scale still on equipment at retirement (all groups), booked by creation year 1980-2025: controlled disposal or storage (impounded) | impounded/og_scale | - | XWL | 1980-2025 | 0.5 / 0.85 / 0.97 | 1 | extrapolated |
| oil_gas:0084 | abandonment_scrap: Fate of scale still on equipment at retirement (all groups), booked by creation year 1980-2025: dispersed (land-farming, spreading, scrap sold on) | dispersed/og_scaled_scrap | - | XWL | 1980-2025 | 0.03 / 0.15 / 0.5 | 1 | extrapolated |
| oil_gas:0085 | oil_sands_mining: Monazite thorium-chain activity in froth-treatment tailings per tonne of mined ore processed, Th232 (head nuclide) | Th232/impounded/oil_sands_tailings | - | CAN | 1967-2025 | 1.84e+03 / 5.68e+03 / 2.25e+04 | Bq/t | modelled |
| oil_gas:0086 | oil_sands_mining: Monazite thorium-chain activity in froth-treatment tailings per tonne of mined ore processed, radium-228 (head nuclide) | Ra228+/impounded/oil_sands_tailings | - | CAN | 1967-2025 | 1.84e+03 / 5.68e+03 / 2.25e+04 | Bq/t | modelled |
| oil_gas:0087 | oil_sands_mining: Monazite thorium-chain activity in froth-treatment tailings per tonne of mined ore processed, Th228+ (head nuclide) | Th228+/impounded/oil_sands_tailings | - | CAN | 1967-2025 | 1.84e+03 / 5.68e+03 / 2.25e+04 | Bq/t | modelled |
| oil_gas:0088 | drilling: Vertical well drill cuttings, uranium-238 activity per well drilled (cuttings mass x activity concentration) | U238+/impounded/og_drill_cuttings | us_wells_drilled_total | USA | 1949-2010 | 3.9e+06 / 1.36e+07 / 3.59e+07 | Bq/1 | measured |
| oil_gas:0089 | drilling: Vertical well drill cuttings, uranium-234 activity per well drilled (cuttings mass x activity concentration) | U234/impounded/og_drill_cuttings | us_wells_drilled_total | USA | 1949-2010 | 3.9e+06 / 1.36e+07 / 3.59e+07 | Bq/1 | measured |
| oil_gas:0090 | drilling: Vertical well drill cuttings, thorium-230 activity per well drilled (cuttings mass x activity concentration) | Th230/impounded/og_drill_cuttings | us_wells_drilled_total | USA | 1949-2010 | 3.9e+06 / 1.36e+07 / 3.59e+07 | Bq/1 | measured |
| oil_gas:0091 | drilling: Vertical well drill cuttings, uranium-235 activity per well drilled (cuttings mass x activity concentration) | U235+/impounded/og_drill_cuttings | us_wells_drilled_total | USA | 1949-2010 | 1.8e+05 / 6.27e+05 / 1.65e+06 | Bq/1 | measured |
| oil_gas:0092 | drilling: Vertical well drill cuttings, radium-226 activity per well drilled (cuttings mass x activity concentration) | Ra226+/impounded/og_drill_cuttings | us_wells_drilled_total | USA | 1949-2010 | 6.03e+06 / 2.61e+07 / 7.79e+07 | Bq/1 | measured |
| oil_gas:0093 | drilling: Vertical well drill cuttings, lead-210 activity per well drilled (cuttings mass x activity concentration) | Pb210+/impounded/og_drill_cuttings | us_wells_drilled_total | USA | 1949-2010 | 6.03e+06 / 2.61e+07 / 7.79e+07 | Bq/1 | measured |
| oil_gas:0094 | drilling: Vertical well drill cuttings, polonium-210 activity per well drilled (cuttings mass x activity concentration) | Po210/impounded/og_drill_cuttings | us_wells_drilled_total | USA | 1949-2010 | 6.03e+06 / 2.61e+07 / 7.79e+07 | Bq/1 | measured |
| oil_gas:0095 | drilling: Vertical well drill cuttings, thorium-232 activity per well drilled (cuttings mass x activity concentration) | Th232/impounded/og_drill_cuttings | us_wells_drilled_total | USA | 1949-2010 | 1.29e+06 / 9.34e+06 / 2.54e+07 | Bq/1 | measured |
| oil_gas:0096 | drilling: Vertical well drill cuttings, radium-228 activity per well drilled (cuttings mass x activity concentration) | Ra228+/impounded/og_drill_cuttings | us_wells_drilled_total | USA | 1949-2010 | 1.29e+06 / 9.34e+06 / 2.54e+07 | Bq/1 | measured |
| oil_gas:0097 | drilling: Vertical well drill cuttings, thorium-228 activity per well drilled (cuttings mass x activity concentration) | Th228+/impounded/og_drill_cuttings | us_wells_drilled_total | USA | 1949-2010 | 1.29e+06 / 9.34e+06 / 2.54e+07 | Bq/1 | measured |
| oil_gas:0098 | drilling: Vertical well drill cuttings, potassium-40 activity per well drilled (cuttings mass x activity concentration) | K40/impounded/og_drill_cuttings | us_wells_drilled_total | USA | 1949-2010 | 4.25e+07 / 1.66e+08 / 3.21e+08 | Bq/1 | measured |
| oil_gas:0099 | drilling: Horizontal well drill cuttings, uranium-238 activity per well drilled (cuttings mass x activity concentration) | U238+/impounded/og_drill_cuttings | - | USA | 2005-2025 | 3.83e+07 / 1.86e+08 / 4.69e+08 | Bq/1 | measured |
| oil_gas:0100 | drilling: Horizontal well drill cuttings, uranium-234 activity per well drilled (cuttings mass x activity concentration) | U234/impounded/og_drill_cuttings | - | USA | 2005-2025 | 3.83e+07 / 1.86e+08 / 4.69e+08 | Bq/1 | measured |
| oil_gas:0101 | drilling: Horizontal well drill cuttings, thorium-230 activity per well drilled (cuttings mass x activity concentration) | Th230/impounded/og_drill_cuttings | - | USA | 2005-2025 | 3.83e+07 / 1.86e+08 / 4.69e+08 | Bq/1 | measured |
| oil_gas:0102 | drilling: Horizontal well drill cuttings, uranium-235 activity per well drilled (cuttings mass x activity concentration) | U235+/impounded/og_drill_cuttings | - | USA | 2005-2025 | 1.77e+06 / 8.6e+06 / 2.16e+07 | Bq/1 | measured |
| oil_gas:0103 | drilling: Horizontal well drill cuttings, radium-226 activity per well drilled (cuttings mass x activity concentration) | Ra226+/impounded/og_drill_cuttings | - | USA | 2005-2025 | 1.84e+07 / 1.16e+08 / 2.8e+08 | Bq/1 | measured |
| oil_gas:0104 | drilling: Horizontal well drill cuttings, lead-210 activity per well drilled (cuttings mass x activity concentration) | Pb210+/impounded/og_drill_cuttings | - | USA | 2005-2025 | 1.84e+07 / 1.16e+08 / 2.8e+08 | Bq/1 | measured |
| oil_gas:0105 | drilling: Horizontal well drill cuttings, polonium-210 activity per well drilled (cuttings mass x activity concentration) | Po210/impounded/og_drill_cuttings | - | USA | 2005-2025 | 1.84e+07 / 1.16e+08 / 2.8e+08 | Bq/1 | measured |
| oil_gas:0106 | drilling: Horizontal well drill cuttings, thorium-232 activity per well drilled (cuttings mass x activity concentration) | Th232/impounded/og_drill_cuttings | - | USA | 2005-2025 | 3.95e+06 / 1.37e+07 / 2.59e+07 | Bq/1 | measured |
| oil_gas:0107 | drilling: Horizontal well drill cuttings, radium-228 activity per well drilled (cuttings mass x activity concentration) | Ra228+/impounded/og_drill_cuttings | - | USA | 2005-2025 | 3.96e+06 / 1.39e+07 / 2.61e+07 | Bq/1 | measured |
| oil_gas:0108 | drilling: Horizontal well drill cuttings, thorium-228 activity per well drilled (cuttings mass x activity concentration) | Th228+/impounded/og_drill_cuttings | - | USA | 2005-2025 | 3.96e+06 / 1.39e+07 / 2.61e+07 | Bq/1 | measured |
| oil_gas:0109 | drilling: Horizontal well drill cuttings, potassium-40 activity per well drilled (cuttings mass x activity concentration) | K40/impounded/og_drill_cuttings | - | USA | 2005-2025 | 1.05e+08 / 3.4e+08 / 7.29e+08 | Bq/1 | measured |

## 2. Cross-checks and benchmark candidates (done condition (e))

Arithmetic on the activity spine, central values, no stream build. Electricity: `elec_gen_gas` 4,807.9 TWh (2010) and 6,382.9 TWh (2020); `elec_gen_oil` 1,078.7 and 775.9 TWh; GWa = TWh / 8.766.

**Candidate B1: gas radon per GWa of gas-fired electricity** (the strongest, two or more independent estimates).
- Stream: $\sum$ delivered Rn $\times$ `gas_power_share` / GWa. 2010: 3.223e12 m3 $\times$ 300 Bq/m3 = 967 TBq; $\times$ 0.4255 = 411 TBq; / 548.5 GWa = 0.75 TBq/GWa. 2020: 1,189 TBq $\times$ 0.4453 = 529 TBq; / 728.2 GWa = 0.73 TBq/GWa.
- UNSCEAR 2016 Annex B (S0001): 0.286 m3/kWh $\times$ 300 Bq/m3 = 0.75 TBq/GWa. NOT independent in value (the factor centre is UNSCEAR's delivered concentration) but independent in method (activity-spine gas volume and power share against UNSCEAR's per-kWh gas use).
- Independent 1: Gesell 34% retention $\times$ Johnson 1973 US mean 1,370 Bq/m3 = 466 Bq/m3 delivered, i.e. 1.17 TBq/GWa (both read via S0001/S0318 only). Stream/benchmark = 0.64.
- Independent 2 (unverified): UK about 170 Bq/m3 gives 0.43 TBq/GWa (ratio 1.7) and Netherlands 74 Bq/m3 gives 0.19 TBq/GWa (ratio 3.9, outside $\times3$). These two figures come from Phase 1 notes; I could not re-confirm their source (S1208, Nowak, is a Polish case study with 30-1400 Bq/m3 site averages, not a UK figure).
- Independent 3: Nowak 2022 Poland site means 30-1400 Bq/m3 (S1208) bracket our delivered 48-780 Bq/m3.

**Candidate B2: oil radon per GWa of oil-fired electricity.** Stream 2010: 3.74 TBq $\times$ 0.0799 / 123.1 GWa = 0.0024 TBq/GWa; UNSCEAR 0.002. Weakly independent (same Ra-226 1 Bq/kg basis); Bell et al. 0.7 Bq/kg gives 0.0017.

**Candidate B3: US solids, about 1990 (partly circular).** US 1990 water (3.96e9 m3): Ra-226 24 TBq + Ra-228 40 TBq = 64 TBq at the USA centres; times total solids fraction 1% = 0.63 TBq. EPA 1993 draft via OGJ 1999 (S1209): 25,000 t scale $\times$ 17.76 Bq/g + 227,500 t sludge $\times$ 2.775 Bq/g = 0.44 + 0.63 = 1.1 TBq/a total Ra. Ratio 0.58. The 1% fraction was set with EPA as one anchor, so this is a consistency check, not an independent test.

**Candidate B4: produced-water radium, factor level.** Norway 451 GBq Ra-226 in 129 Mm3 (2011, S0308) = 3.5 Bq/L; OSPAR 0.73-1.1 TBq/a Ra-226 offshore NE Atlantic (S0307); RP 135 reference 10 Bq/L (S0204); UNSCEAR 2000 Table 28 typical installation 174 GBq/a (S0005). The world conventional centre 5 Bq/L sits between Norway and RP 135. The stream gives world Ra-226 to water of about 12 TBq/a liberated outside the USA (2010: 9.9e9 m3 $\times$ 5,000 Bq/m3 $\times$ 0.25) and 1.2 TBq/a in the USA (2010: 21 TBq $\times$ 0.054); no country-level water series exists to compare with OSPAR region by region.

**Other arithmetic checks.**
- Flaring: 40 m3/t $\times$ 3.9e9 t gives 156 bcm against Elvidge peak 172 (2005) and 139 (2008); radon 86 TBq/a in 2010 (23,125 Bq/t $\times$ 3.74e9 t), against 967 TBq delivered. Circular for volume (intensity derived from those volumes); the Rn concentration is the uncertain part.
- Vented Rn 2010: 12.5 $\times$ 3.22e12 = 40 TBq/a. Pb-210 plated out in gas systems 2010: 0.12 Bq/m3 $\times$ 3.22e12 = 0.40 TBq/a (head Pb-210).
- Oil sands 2024: 1,019.4 Mt $\times$ 5,684 Bq/t = 5.8 TBq/a Th-232 (and equal Ra-228, Th-228).
- Drilling, US vertical per well: Ra-226 2.6e7 Bq (range 6e6-7.8e7). Horizontal Ra-226 1.2e8 Bq per well. Cuttings Ra-226 is about 1.4 TBq/a against about 20 TBq/a in produced water at 2010.
- Basin check on the US unconventional blend: Ra-226 30 Bq/L against NPWGD v3 means 54-84 (Appalachia, Bakken) and Scanlon medians 10-73.

**Epsilon and seepage proposals (notes only; not written to `residue_types.csv`). D60 convention: Rn-222 epsilon = emanation coefficient (upper bound of effective exhalation); Rn-220 epsilon = emanation $\times$ slab factor $f=(L/H)\tanh(H/L)$, $L$ = 0.005 / 0.01 / 0.02 m. Bounds: low = em_low $\times f(L_{low},H_{high})$, central = em_c $\times f(L_c,H_{gm})$, high = em_high $\times f(L_{high},H_{low})$.**

| residue type | eps Rn-222 low / central / high | basis | eps Rn-220 low / central / high | seepage per a low / central / high |
|---|---|---|---|---|
| `og_scale` | 0.037 / 0.088 / 0.14 | S0321 White and Rood site means 0.037-0.138, geometric mean 0.088 | 1.8e-5 / 3.6e-4 / 3.9e-3 (emanation 0.011 / 0.044 / 0.098; H 0.5 / 1.2 / 3 m; thickness assumption) | already filled: 3e-9 / 3e-8 / 4e-6 |
| `og_sludge` | 0.05 / 0.15 / 0.25 | analogy to soil and sludge (assumption) | 2.5e-5 / 6.1e-4 / 5e-3 | already filled: 1e-8 / 5e-8 / 4e-6 |
| `og_drill_cuttings` | 0.05 / 0.15 / 0.25 | rock-and-soil analogy (assumption) | about 3e-5 / 3.2e-4 / 2.8e-3 | 7e-7 / 6e-6 / 6e-5 (generic M1 mineral-waste value, grade C) |
| `og_scaled_scrap` | as `og_scale` | scale on steel | as `og_scale` | as `og_scale` |
| `og_processing_residue` | not applicable (Pb-210 films; Rn-222 parent absent) | - | not applicable | as `og_sludge` |
| `og_produced_water` | 0.1 / 0.2 / 0.3 (soil after spreading) | assumption; reisolated fraction treated as permanent | 0 (spread water: negligible) | no value proposed; reisolated is permanent by construction |
| `oil_sands_tailings` | 0.002 | monazite emanation from `research/wind_solar/notes.md` (source ID not recorded there; verify) | 0.0002 $\times f$ | 1e-6 / 1.1e-5 / 1.25e-4 (the `ree_tailings` Th triple) |
| `oil_sands_coke` | no data | - | no data | no data |

Not blockers for the factor file, but the pipeline refuses residue types that have data rows and empty parameters, so `og_produced_water`, `og_drill_cuttings`, `og_scaled_scrap`, `og_processing_residue` and `oil_sands_tailings` (all used above) need these filled before the engine runs. `oil_sands_coke` has no rows.

## 3. Gap register

| # | Item | Why no row | URL if inaccessible | Blocks the engine? |
|---|---|---|---|---|
| G1 | Radium in produced water: Middle East, Russia, China, Africa, Latin America | no measurements in Phase 1 or NPWGD; XWL centre is extrapolated from US and Norway | S0315 https://doi.org/10.1016/j.scitotenv.2020.137085 | No (wide band) |
| G2 | NPWGD has no Ra data for TX, OK, KS, LA; Permian only via NM (S0316) | US volume-weighted value rests on ANL state volumes | S0313 https://digital.library.unt.edu/ark:/67531/metadc836481/m2/1/high_res_d/1007397.pdf | No |
| G3 | NGL, LPG and propane radon; refinery sludge; Pb-210 fouling of fractionation units | no activity driver (no NGL series), no factor data | none | No (understates) |
| G4 | Reservoir-sourced Pb-210/Po-210 in gas and oil; Po-210 films | volatile Po-210 not separable; only a mass-balance Pb-210 row | none | No |
| G5 | Oil-sands tailings and coke background (K-40, U, Th of sand and clay) | no measurements; quartz-sand placeholders would add hundreds of TBq of K-40 | none | No (choice 9) |
| G6 | Monazite U-series in oil-sands tailings; Th content only from an abstract | S0429 abstract only | S0429 https://apo.ansto.gov.au/dspace/handle/10238/12874 | No |
| G7 | World well counts and US horizontal well counts | no series | none | **B2** for horizontal; world drilling absent |
| G8 | Flared gas volume before 1994 and by country | satellite record starts 1994 | S1204 PDF (download failed) | No (extrapolated row, wide band) |
| G9 | Oil, gas and NGL unit values for the D6 default allocation | none in `commodity_prices.csv` | none | **B4** for the allocation (see section 5) |
| G10 | Retired tubular and scrap tonnage | no series; replaced by the retained-scale share $\phi$ (assumption) | none | No |
| G11 | Cuttings K-40, Th and U outside Pennsylvania; cuttings tonnage per well | only PA DEP and one NY figure | S0301 | No |
| G12 | Unconventional produced-water share by play; years before 2017 | single measured point | S0312 https://www.gwpc.org/publications/u-s-produced-water-volumes-and-management-practices-in-2017/ (check URL in `sources.csv`) | No |
| G13 | Pre-1950 produced water (no driver), so no pre-1950 solids | `produced_water_m3` starts 1950 | none | No; D31 opening stock omits O&G scale pre-1950 |
| G14 | Time variation of produced-water radium (water cut, reservoir souring) | no data | none | No |
| G15 | Overburden / earth moved memo for oil-sands mining | no series | none | No (memo tier) |
| G16 | Sludge retained at decommissioning; descaling dust and cutting releases (liberated at abandonment) | no data | none | No |
| G17 | Primary reports read only through secondaries: Johnson 1973 (EPA-520/1-73-004), Gesell 1975 (Health Phys 29:681), Bell et al., EPA 1993 diffuse-NORM (RAE-9232), Alberta Chamber of Resources 1996, Chachula and Erasmus 2008 | not obtained | IOGP Report 412 https://www.iogp.org/bookstore/product/412/ | No |

## 4. Blockers (for the orchestrator)

- **B1** Activity series `oil_sands_ore_processed_t` (Mt of ore, Canada, from 1967) is missing: rows 0085-0087 have a blank driver. 2024 anchor: 1,019.4 Mt (S0326).
- **B2** `us_wells_drilled_horizontal` (USA, 2005-2025) is missing: rows 0099-0109 have a blank driver. Also no world well count.
- **B3** Flared gas volume series is missing; flaring uses crude tonnage as a proxy driver.
- **B4** Oil, gas, NGL unit values (or an agreed alternative rule) for the D6 allocation across oil, gas and NGL for joint residues, and an NGL output series. Without them only `default` and the two bounds can follow a stated product-value rule.
- **B5** Residue-type parameters (section 2 table) for five used residue types.
- **B6** Source merge: `research/oil_gas/sources_factors.csv` (S1200-S1209) must be added to `data/sources.csv` before the committed tree validates.
- **Observation, out of scope:** in `data/activity/oil_gas.csv` the `XWL` produced-water series is below the `USA` series in early years (1950: XWL 5.8e8 m3 against USA 1.5e9 m3), so the "rest of world = XWL minus USA" difference goes negative before about 1985 and the independent-difference helper will log `negative_residual` for those years. Either XWL is not a true world total there, or the USA series is high. Needs the activity owner.

## 5. Choices for Steve

1. **Keying without a substream column.** Conventional/unconventional concentration rows use `driver_series` (`produced_water_m3` against `produced_water_unconv_share`) as a discriminator, and the unit-1 shares use blank group. Alternative: add a `substream` match key to `select` and the factor schema. Recommend the schema change if more streams need it.
2. **Unconventional produced-water fraction eras** (0.5% to 2005, 4% 2006-10, 12% 2011-16, 16% 2017, 20% 2018-25) are assumptions anchored on one point (2017).
3. **Rn-222 in-system decay.** Only Rn that leaves the system is Rn222+; Rn that decays in pipes and plants is not counted as Rn222+ and appears only as plated Pb-210 (0076). Alternative: count all wellhead Rn.
4. **Flaring placed at stage `production`, route `air_stack`**, radon at the wellhead concentration; no vocabulary stage exists for flaring. Alternative: processing_transport.
5. **Retained scale ($\phi$ = 0.5, 0.2-0.8) booked in the creation year at `abandonment_scrap`**, with the 20-year retirement lag built into the era windows and no decay survival factor (replaces my earlier Ra-228 survival idea, which would double-count decay). Sludge is assumed removed in operation.
6. **Era fate shares for removed and retained solids** (pre-1985, 1985-99, 2000+): wholly assumed.
7. **Pre-1970 and world produced-water route shares:** assumed; US 2007/2012/2017 are data. The world discharge share 25% (high 42% = IOGP members) could be higher if national oil companies discharge more.
8. **Solids fraction 1% of outlet water radium** (EPA 1993 about 0.9%; Norway 0.04-4%); scale/sludge split 40/60 assumed.
9. **Oil-sands background sand, clay and coke left out** of the registry (placeholders would add hundreds of TBq of K-40 and swamp the monazite signal); only the monazite thorium chain is carried. Alternative: add a background row with a clearly flagged assumption.
10. **Oil-sands monazite per tonne of ore:** 7.5e-6 / 2.0e-5 / 7.1e-5 t/t spans the AER arithmetic (0.3-0.5% of whole tailings) and the reading as heavy-mineral fraction (15-30% of tailings). Th in monazite 7% (4-12%).
11. **Wellhead radon 625 Bq/m3** world, (150-1,400); no USA or other country override although Johnson gives 1,370 for the USA. Delivered fraction 0.48 (0.15-0.8).
12. **Drilling:** vertical cuttings 250 t/well (assumption, lowered from 295 t), horizontal 600 t (330-1,000); U-chain taken from XRF (gamma U-238 is 5x lower for horizontal wells); Pb-210 and Po-210 at Ra-226 equilibrium.
13. **`bound_radio` product definition** (D6): proposed as the product with the larger share of the mobilised radium in the joint residue (water-borne radium: oil and NGL by volume of water produced; gas Pb-210 films: gas). Needs Steve's decision; the default allocation needs unit values (B4).
14. **No construction rows** (commodity table covers it) and no refinery residue rows.
15. **Oil sands start 1967** and the monazite factor is held constant over time.

## 6. Proposed stream-script outline (`pipeline/streams/oil_gas.py`, for `docs/OIL_GAS_SPEC.md`)

Interface as coal: `build(root) -> BuildResult(rows, rows_pre1950, log)`; `python -m pipeline.streams.oil_gas [--root] [--write]`; outputs `data/streams/oil_gas.csv` (1950-2025) and `data/streams_pre1950/oil_gas.csv` (1900-1949). World rows country `XXX`. Pure function of `data/`; no decay, ingrowth, exhalation or seepage.

**Drivers** (`data/activity/oil_gas.csv`): `oil_production_t`, `gas_production_m3` (43 countries plus `XWL`, rest of world by independent difference), `produced_water_m3` (`USA`, `XWL`), `us_wells_drilled_total` (USA to 2010), `gas_power_share`/`oil_power_share`/`elec_gen_*` for benchmarks only. Missing: B1-B4.

**Stages and rules.**
- `production`: (a) produced-water activity by group (blend of conventional and unconventional, section 0); (b) tier split with rows 0019-0046; (c) solids $S$, removed share by tiers 0053-0070; (d) flaring Rn222+ by country on `oil_production_t` (XWL factor, country rows if added).
- `processing_transport`: delivered Rn (`air_delivered_gas`), vented Rn (`air_vented_gas`), Pb-210 deposits (impounded `og_processing_residue`) per country on `gas_production_m3`; oil radon on `oil_production_t`. Product column: gas or oil as the driver; NGL and bitumen not covered.
- `abandonment_scrap`: retained scale $S\phi$ by creation-year window (impounded, dispersed).
- `oil_sands_mining` (CAN, substream `oil_sands`, product `bitumen`): ore $\times$ factor for Th232, Ra228+, Th228+, impounded `oil_sands_tailings`. Blocked by B1.
- `drilling` (USA, substream per well type): wells $\times$ per-well factor, impounded `og_drill_cuttings`. Horizontal blocked by B2.
- Allocation (D6): joint residues (water-borne radium, drilling cuttings) across oil, gas and NGL; variants `default`, `bound_main`, `bound_radio` all emitted once any is non-default (X03). Blocked by B4 for `default`.
- No inter-tier transfers at O&G stages. Rn222+/Rn220+ rows only as liberated flows. Release cap (D54) applies to the liberated shares of produced water: never above the group's water activity.
- Independent versus correlated helpers: concentrations, shares and $\sigma$ are independent; the rows made of several parameters are already combined in log-quadrature and must not be recombined. The delivered-Rn row (0074) and Pb-210 deposit row (0076) are anticorrelated through $r$; the Ra-226/Ra-228/K-40/Pb-210 concentration rows of one region are correlated (same reservoir water).

**Log kinds:** `no_factor`, `negative_residual` (see observation in section 4), `no_driver`, `cap_applied`, `blocked_driver` (B1, B2).

**Done conditions (proposed):** (a) validator passes; (b) share rows sum to 1 at centre per region and era; (c) key uniqueness; (d) every liberated row has a route; (e) benchmark B1 within $\times3$ of at least one independent value for 2010 and 2020 (stream 0.75/0.73 against Gesell 1.17, UK 0.43), B2 and B3 as consistency checks; (f) tiers within the stage-tier matrix; (g) pre-1950 file has flows only; (h) determinism.

## 7. Inaccessible or unverified items (most to least important)

1. EPA 1993 diffuse-NORM report (primary of S1209; the Ra solids fraction rests on it): not obtained. Search: EPA 402-R-93-083 / RAE-9232 "Diffuse NORM wastes".
2. S0313 Clark and Veil 2009 (ANL/EVS/R-09/1): read via https://digital.library.unt.edu/ark:/67531/metadc836481/m2/1/high_res_d/1007397.pdf; suggest updating its URL and access in `sources.csv`. S0312 GWPC 2020: https://www.gwpc.org/publications/u-s-produced-water-volumes-and-management-practices-in-2017/
3. S0315 Scanlon 2020: https://doi.org/10.1016/j.scitotenv.2020.137085 (paywalled); S0325 Tasker 2018: https://doi.org/10.1021/acs.est.8b00716 (paywalled).
4. World Bank GGFR 2024 tracker PDF (download failed): https://www.worldbank.org/en/programs/gasflaringreduction/publication/2024-global-gas-flaring-tracker-report
5. IOGP Report 412: https://www.iogp.org/bookstore/product/412/
6. Johnson 1973 (EPA-520/1-73-004), Gesell 1975 (Health Phys 29:681), Bell et al.: read only via UNSCEAR/Mitchell.
7. S0429 Anvia (abstract only): https://apo.ansto.gov.au/dspace/handle/10238/12874; Alberta Chamber of Resources 1996; Chachula and Erasmus 2008 (via S0326).
8. S1203 author list and S1208 UK/NL values unverified (section 2).
