# Oil and gas factor registry: notes (Task 2.3, step 1)

Output: `data/factors/oil_gas.csv` (111 rows `oil_gas:0001`-`0111`; 0110 added by D65, see section 8, 0111 by D70, see section 10; 0071-0073 RETIRED by D70 but kept: production 74, processing_transport 5, abandonment_scrap 7, oil_sands_mining 3, drilling 22; construction 0). **Status 2026-11-04 (D70): this file is the factor-level rationale; the stream contract is `docs/OIL_GAS_SPEC.md` v1.0. Blockers B1-B6 below are all resolved (section 4), and the stale statements in sections 0-6 are corrected in place or marked.** New sources `S1200`-`S1209` are in `research/oil_gas/sources_factors.csv` (merged into `data/sources.csv`; with the D65 round-2/round-3 sources merged the validator prints `OK: no issues`). Generator: scratchpad `og/build_og.py` (not in the repository). No pipeline code or tests were written.

## 0. Engine reading of the factors (my specification; the stream spec should confirm)

All activity values are HEAD-nuclide activity (METHODS 3.2, 4.1a, D24); the engine applies the group multiplier. Unit-1 rows are shares or ratios that apply to a Bq quantity built from other rows. REVISED D65: `select` now has the `substream` key (D63, schema v2.4). Produced-water concentration rows 0001-0010 carry `substream` = `conventional` or `unconventional` (D70: gas, NGL, vented and oil radon, Pb-210 plate-out and flaring carry the new substream `all`); `driver_series` is deliberately left as before (see section 8) so lookups that do not pass `substream` still resolve. The key tuple (stage, substream, driver_series, group, tier, route, residue_type, region) is unique over overlapping years (checked at D65).

- **Produced-water activity** of group $g$ in region $c$, year $y$: with $V$ = `produced_water_m3`, $u$ = unconventional fraction (rows 0011-0018, selected with `driver_series='produced_water_unconv_share'`, blank group, blank substream), $C^{conv}_g$ (0001-0010 with `substream='conventional'`) and $C^{unc}_g$ (`substream='unconventional'`; legacy discriminator driver `produced_water_unconv_share` kept):
$$A_{g}=V\left[(1-u)\,C^{conv}_g+u\,C^{unc}_g\right]$$
  Rest of world = `XWL` minus `USA` as a **correlated** difference (D70; `XWL` is modelled as `USA` plus the rest of the world and the activity builder enforces world >= USA at every bound; this replaces the earlier "independent difference, as coal"). The two substreams are separate rows, not the blended sum shown above (spec section 5.2). The `produced_water_unconv_share` activity series (2017 only) is a cross-check, not a multiplier.
- **Tier split of $A_g$** (all groups alike): rows 0019-0046, selected by tier with `driver_series='produced_water_m3'`; reisolated and dispersed carry `og_produced_water`, impounded (evaporation pits) `og_sludge`, liberated route `water_produced_discharge`. Central shares sum to 1 per region and era.
- **Solids** (Ra-226+ and Ra-228+ only): $S_{g,r}=A_g\,\sigma_{g,r}$ for residue $r\in\{$`og_scale`, `og_sludge`$\}$ (0047-0050, additive to the water, not subtracted). Pb-210+ in solids $=0.05\times S_{\mathrm{Ra226+},r}$ (0051-0052; reservoir-derived Pb-210 only; supported Pb-210 is the engine's ingrowth).
- **Removed solids** (booked at `production`): $S\,(1-\phi)$ for scale ($\phi$ = row 0078) and $S$ for sludge, split by tier with rows 0053-0070 (blank driver; liberated rows carry the source residue type only to make the key unique, and the master row has no residue).
- **Retained scale** (booked at `abandonment_scrap` in the SAME year, creation-year windows with the ~20 year retirement lag built into the era boundaries, rows 0079-0084): $S\,\phi$ split to impounded `og_scale` and dispersed `og_scaled_scrap`. No Ra-228 survival factor is applied: decay of unmoved activity is the engine's job and a second factor would double-count it.
- **Gas**: delivered Rn (0074), NGL/LPG Rn (0110, D65; key distinguished by `residue_type='og_processing_residue'`) and vented Rn (0075) are Bq per m3 of `gas_production_m3`; Pb-210 deposit (0076) likewise, tier impounded `og_processing_residue`. Oil radon (0077) is per tonne of `oil_production_t`. Flaring is per m3 of `gas_flared_m3` (0111, D70; the per-tonne rows 0071-0073 are RETIRED).
- **Oil sands** (0085-0087) per tonne of ore processed; driver `oil_sands_ore_processed_t` (set on the rows by D70; B1 closed). **Drilling** (0088-0098 vertical, driver `us_wells_drilled_vertical`, 1949-2025; 0099-0109 horizontal, driver `us_wells_drilled_horizontal`, 1980-2025, both since D66): unit `Bq/1`, apply to the well count.
- Chronic radon exhalation and seepage from impounded/dispersed holdings are engine processes. No rows for them.

## 1. Factor table

| id | what | group / tier / route / residue | driver | region | years | low / central / high | unit | basis |
|---|---|---|---|---|---|---|---|---|
| oil_gas:0001 | production: Produced-water radium-226 concentration (post-precipitation), conventional, world default | Ra226+ | produced_water_m3 [substream conventional] | XWL | 1950-2025 | 1e+03 / 5e+03 / 2e+04 | Bq/m3 | compiled |
| oil_gas:0002 | production: Produced-water radium-226 concentration, conventional, USA | Ra226+ | produced_water_m3 [substream conventional] | USA | 1950-2025 | 1.5e+03 / 6e+03 / 2.5e+04 | Bq/m3 | compiled |
| oil_gas:0003 | production: Produced-water radium-226 concentration, unconventional (shale and tight), world default | Ra226+ | produced_water_unconv_share [substream unconventional] | XWL | 1950-2025 | 1.18e+03 / 1.49e+04 / 6.71e+04 (D66) | Bq/m3 | compiled |
| oil_gas:0004 | production: Produced-water radium-228 concentration (post-precipitation), conventional, world default | Ra228+ | produced_water_m3 [substream conventional] | XWL | 1950-2025 | 800 / 4e+03 / 2e+04 | Bq/m3 | compiled |
| oil_gas:0005 | production: Produced-water radium-228 concentration, conventional, USA | Ra228+ | produced_water_m3 [substream conventional] | USA | 1950-2025 | 3e+03 / 1e+04 / 4e+04 | Bq/m3 | compiled |
| oil_gas:0006 | production: Produced-water radium-228 concentration, unconventional (shale and tight), world default | Ra228+ | produced_water_unconv_share [substream unconventional] | XWL | 1950-2025 | 766 / 9.92e+03 / 4.55e+04 (D66) | Bq/m3 | compiled |
| oil_gas:0007 | production: Produced-water potassium-40 concentration (post-precipitation), conventional, world default | K40 | produced_water_m3 [substream conventional] | XWL | 1950-2025 | 3e+03 / 1e+04 / 3e+04 | Bq/m3 | compiled |
| oil_gas:0008 | production: Produced-water potassium-40 concentration, unconventional (shale and tight), world default | K40 | produced_water_unconv_share [substream unconventional] | XWL | 1950-2025 | 1e+04 / 4e+04 / 1.1e+05 | Bq/m3 | compiled |
| oil_gas:0009 | production: Produced-water lead-210 concentration (post-precipitation), conventional, world default | Pb210+ | produced_water_m3 [substream conventional] | XWL | 1950-2025 | 15 / 250 / 3e+03 | Bq/m3 | modelled |
| oil_gas:0010 | production: Produced-water lead-210 concentration, unconventional (shale and tight), world default | Pb210+ | produced_water_unconv_share [substream unconventional] | XWL | 1950-2025 | 100 / 1.5e+03 / 2e+04 | Bq/m3 | modelled |
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
| oil_gas:0047 | production: Radium solids-bound fraction: radium-226 in scale formed per unit of outlet-water radium-226 | Ra226+/og_scale | - | XWL | 1950-2025 | 0.00037 / 0.008 / 0.0485 | 1 | modelled |
| oil_gas:0048 | production: Radium solids-bound fraction: radium-226 in sludge formed per unit of outlet-water radium-226 | Ra226+/og_sludge | - | XWL | 1950-2025 | 0.00037 / 0.012 / 0.0616 | 1 | modelled |
| oil_gas:0049 | production: Radium solids-bound fraction: radium-228 in scale formed per unit of outlet-water radium-228 | Ra228+/og_scale | - | XWL | 1950-2025 | 0.00037 / 0.008 / 0.0485 | 1 | modelled |
| oil_gas:0050 | production: Radium solids-bound fraction: radium-228 in sludge formed per unit of outlet-water radium-228 | Ra228+/og_sludge | - | XWL | 1950-2025 | 0.00037 / 0.012 / 0.0616 | 1 | modelled |
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
| oil_gas:0071 | production: RETIRED (D70): Rn-222 released by associated-gas flaring per tonne of crude produced, world 1900-1993 | Rn222+/liberated/air_stack | oil_production_t | XWL | 1900-1993 | 6.53e+03 / 4e+04 / 9.01e+04 | Bq/t | extrapolated |
| oil_gas:0072 | production: RETIRED (D70): Rn-222 released by associated-gas flaring per tonne of crude produced, world 1994-2008 | Rn222+/liberated/air_stack | oil_production_t | XWL | 1994-2008 | 5.97e+03 / 3.2e+04 / 5.76e+04 | Bq/t | modelled |
| oil_gas:0073 | production: RETIRED (D70): Rn-222 released by associated-gas flaring per tonne of crude produced, world 2009-2025 | Rn222+/liberated/air_stack | oil_production_t | XWL | 2009-2025 | 5.53e+03 / 2.96e+04 / 5.25e+04 | Bq/t | modelled |
| oil_gas:0074 | processing_transport: Rn-222 in marketed gas delivered to end users (reaches burners and kitchens), per m3 of gas produced | Rn222+/liberated/air_delivered_gas | gas_production_m3 [substream all] | XWL | 1900-2025 | 47.6 / 300 / 1e+03 | Bq/m3 | compiled |
| oil_gas:0075 | processing_transport: Rn-222 in vented and fugitive gas released at well sites, plants and pipelines, per m3 of gas produced | Rn222+/liberated/air_vented_gas | gas_production_m3 [substream all] | XWL | 1900-2025 | 1.82 / 16 / 46.8 | Bq/m3 | modelled |
| oil_gas:0076 | processing_transport: Pb-210 formed from Rn-222 that decays inside gas wells, pipelines and processing plants and plates out (films, scale, sludge), per m3 of gas produced | Pb210+/impounded/og_processing_residue | gas_production_m3 [substream all] | XWL | 1900-2025 | 0.0144 / 0.107 / 0.292 (D70) | Bq/m3 | modelled |
| oil_gas:0077 | processing_transport: Rn-222 released with crude oil handled and refined (equilibrium with Ra-226 in crude), per tonne of crude produced | Rn222+/liberated/air_stack | oil_production_t [substream all] | XWL | 1900-2025 | 200 / 1e+03 / 1.3e+04 | Bq/t | compiled |
| oil_gas:0078 | abandonment_scrap: Fraction of newly formed scale that stays on tubulars and equipment until retirement | og_scale | - | XWL | 1950-2025 | 0.6 / 0.9 / 0.97 | 1 | modelled |
| oil_gas:0079 | abandonment_scrap: Fate of scale still on equipment at retirement (all groups), booked by creation year 1950-1964: controlled disposal or storage (impounded) | impounded/og_scale | - | XWL | 1950-1964 | 0.05 / 0.15 / 0.4 | 1 | extrapolated |
| oil_gas:0080 | abandonment_scrap: Fate of scale still on equipment at retirement (all groups), booked by creation year 1950-1964: dispersed (land-farming, spreading, scrap sold on) | dispersed/og_scaled_scrap | - | XWL | 1950-1964 | 0.6 / 0.85 / 0.95 | 1 | extrapolated |
| oil_gas:0081 | abandonment_scrap: Fate of scale still on equipment at retirement (all groups), booked by creation year 1965-1979: controlled disposal or storage (impounded) | impounded/og_scale | - | XWL | 1965-1979 | 0.2 / 0.5 / 0.8 | 1 | extrapolated |
| oil_gas:0082 | abandonment_scrap: Fate of scale still on equipment at retirement (all groups), booked by creation year 1965-1979: dispersed (land-farming, spreading, scrap sold on) | dispersed/og_scaled_scrap | - | XWL | 1965-1979 | 0.2 / 0.5 / 0.8 | 1 | extrapolated |
| oil_gas:0083 | abandonment_scrap: Fate of scale still on equipment at retirement (all groups), booked by creation year 1980-2025: controlled disposal or storage (impounded) | impounded/og_scale | - | XWL | 1980-2025 | 0.5 / 0.85 / 0.97 | 1 | extrapolated |
| oil_gas:0084 | abandonment_scrap: Fate of scale still on equipment at retirement (all groups), booked by creation year 1980-2025: dispersed (land-farming, spreading, scrap sold on) | dispersed/og_scaled_scrap | - | XWL | 1980-2025 | 0.03 / 0.15 / 0.5 | 1 | extrapolated |
| oil_gas:0085 | oil_sands_mining: Monazite thorium-chain activity in froth-treatment tailings per tonne of mined ore processed, Th232 (head nuclide) | Th232/impounded/oil_sands_tailings | oil_sands_ore_processed_t | CAN | 1967-2025 | 1.84e+03 / 5.68e+03 / 2.25e+04 | Bq/t | modelled |
| oil_gas:0086 | oil_sands_mining: Monazite thorium-chain activity in froth-treatment tailings per tonne of mined ore processed, radium-228 (head nuclide) | Ra228+/impounded/oil_sands_tailings | oil_sands_ore_processed_t | CAN | 1967-2025 | 1.84e+03 / 5.68e+03 / 2.25e+04 | Bq/t | modelled |
| oil_gas:0087 | oil_sands_mining: Monazite thorium-chain activity in froth-treatment tailings per tonne of mined ore processed, Th228+ (head nuclide) | Th228+/impounded/oil_sands_tailings | oil_sands_ore_processed_t | CAN | 1967-2025 | 1.84e+03 / 5.68e+03 / 2.25e+04 | Bq/t | modelled |
| oil_gas:0088 | drilling: Vertical well drill cuttings, uranium-238 activity per well drilled (cuttings mass x activity concentration) | U238+/impounded/og_drill_cuttings | us_wells_drilled_vertical [substream conventional] | USA | 1949-2025 | 3.9e+06 / 1.36e+07 / 3.59e+07 | Bq/1 | measured |
| oil_gas:0089 | drilling: Vertical well drill cuttings, uranium-234 activity per well drilled (cuttings mass x activity concentration) | U234/impounded/og_drill_cuttings | us_wells_drilled_vertical [substream conventional] | USA | 1949-2025 | 3.9e+06 / 1.36e+07 / 3.59e+07 | Bq/1 | measured |
| oil_gas:0090 | drilling: Vertical well drill cuttings, thorium-230 activity per well drilled (cuttings mass x activity concentration) | Th230/impounded/og_drill_cuttings | us_wells_drilled_vertical [substream conventional] | USA | 1949-2025 | 3.9e+06 / 1.36e+07 / 3.59e+07 | Bq/1 | measured |
| oil_gas:0091 | drilling: Vertical well drill cuttings, uranium-235 activity per well drilled (cuttings mass x activity concentration) | U235+/impounded/og_drill_cuttings | us_wells_drilled_vertical [substream conventional] | USA | 1949-2025 | 1.8e+05 / 6.27e+05 / 1.65e+06 | Bq/1 | measured |
| oil_gas:0092 | drilling: Vertical well drill cuttings, radium-226 activity per well drilled (cuttings mass x activity concentration) | Ra226+/impounded/og_drill_cuttings | us_wells_drilled_vertical [substream conventional] | USA | 1949-2025 | 6.03e+06 / 2.61e+07 / 7.79e+07 | Bq/1 | measured |
| oil_gas:0093 | drilling: Vertical well drill cuttings, lead-210 activity per well drilled (cuttings mass x activity concentration) | Pb210+/impounded/og_drill_cuttings | us_wells_drilled_vertical [substream conventional] | USA | 1949-2025 | 6.03e+06 / 2.61e+07 / 7.79e+07 | Bq/1 | measured |
| oil_gas:0094 | drilling: Vertical well drill cuttings, polonium-210 activity per well drilled (cuttings mass x activity concentration) | Po210/impounded/og_drill_cuttings | us_wells_drilled_vertical [substream conventional] | USA | 1949-2025 | 6.03e+06 / 2.61e+07 / 7.79e+07 | Bq/1 | measured |
| oil_gas:0095 | drilling: Vertical well drill cuttings, thorium-232 activity per well drilled (cuttings mass x activity concentration) | Th232/impounded/og_drill_cuttings | us_wells_drilled_vertical [substream conventional] | USA | 1949-2025 | 1.29e+06 / 9.34e+06 / 2.54e+07 | Bq/1 | measured |
| oil_gas:0096 | drilling: Vertical well drill cuttings, radium-228 activity per well drilled (cuttings mass x activity concentration) | Ra228+/impounded/og_drill_cuttings | us_wells_drilled_vertical [substream conventional] | USA | 1949-2025 | 1.29e+06 / 9.34e+06 / 2.54e+07 | Bq/1 | measured |
| oil_gas:0097 | drilling: Vertical well drill cuttings, thorium-228 activity per well drilled (cuttings mass x activity concentration) | Th228+/impounded/og_drill_cuttings | us_wells_drilled_vertical [substream conventional] | USA | 1949-2025 | 1.29e+06 / 9.34e+06 / 2.54e+07 | Bq/1 | measured |
| oil_gas:0098 | drilling: Vertical well drill cuttings, potassium-40 activity per well drilled (cuttings mass x activity concentration) | K40/impounded/og_drill_cuttings | us_wells_drilled_vertical [substream conventional] | USA | 1949-2025 | 4.25e+07 / 1.66e+08 / 3.21e+08 | Bq/1 | measured |
| oil_gas:0099 | drilling: Horizontal well drill cuttings, uranium-238 activity per well drilled (cuttings mass x activity concentration) | U238+/impounded/og_drill_cuttings | us_wells_drilled_horizontal [substream unconventional] | USA | 1980-2025 | 3.83e+07 / 1.86e+08 / 4.69e+08 | Bq/1 | measured |
| oil_gas:0100 | drilling: Horizontal well drill cuttings, uranium-234 activity per well drilled (cuttings mass x activity concentration) | U234/impounded/og_drill_cuttings | us_wells_drilled_horizontal [substream unconventional] | USA | 1980-2025 | 3.83e+07 / 1.86e+08 / 4.69e+08 | Bq/1 | measured |
| oil_gas:0101 | drilling: Horizontal well drill cuttings, thorium-230 activity per well drilled (cuttings mass x activity concentration) | Th230/impounded/og_drill_cuttings | us_wells_drilled_horizontal [substream unconventional] | USA | 1980-2025 | 3.83e+07 / 1.86e+08 / 4.69e+08 | Bq/1 | measured |
| oil_gas:0102 | drilling: Horizontal well drill cuttings, uranium-235 activity per well drilled (cuttings mass x activity concentration) | U235+/impounded/og_drill_cuttings | us_wells_drilled_horizontal [substream unconventional] | USA | 1980-2025 | 1.77e+06 / 8.6e+06 / 2.16e+07 | Bq/1 | measured |
| oil_gas:0103 | drilling: Horizontal well drill cuttings, radium-226 activity per well drilled (cuttings mass x activity concentration) | Ra226+/impounded/og_drill_cuttings | us_wells_drilled_horizontal [substream unconventional] | USA | 1980-2025 | 1.84e+07 / 1.16e+08 / 2.8e+08 | Bq/1 | measured |
| oil_gas:0104 | drilling: Horizontal well drill cuttings, lead-210 activity per well drilled (cuttings mass x activity concentration) | Pb210+/impounded/og_drill_cuttings | us_wells_drilled_horizontal [substream unconventional] | USA | 1980-2025 | 1.84e+07 / 1.16e+08 / 2.8e+08 | Bq/1 | measured |
| oil_gas:0105 | drilling: Horizontal well drill cuttings, polonium-210 activity per well drilled (cuttings mass x activity concentration) | Po210/impounded/og_drill_cuttings | us_wells_drilled_horizontal [substream unconventional] | USA | 1980-2025 | 1.84e+07 / 1.16e+08 / 2.8e+08 | Bq/1 | measured |
| oil_gas:0106 | drilling: Horizontal well drill cuttings, thorium-232 activity per well drilled (cuttings mass x activity concentration) | Th232/impounded/og_drill_cuttings | us_wells_drilled_horizontal [substream unconventional] | USA | 1980-2025 | 3.95e+06 / 1.37e+07 / 2.59e+07 | Bq/1 | measured |
| oil_gas:0107 | drilling: Horizontal well drill cuttings, radium-228 activity per well drilled (cuttings mass x activity concentration) | Ra228+/impounded/og_drill_cuttings | us_wells_drilled_horizontal [substream unconventional] | USA | 1980-2025 | 3.96e+06 / 1.39e+07 / 2.61e+07 | Bq/1 | measured |
| oil_gas:0108 | drilling: Horizontal well drill cuttings, thorium-228 activity per well drilled (cuttings mass x activity concentration) | Th228+/impounded/og_drill_cuttings | us_wells_drilled_horizontal [substream unconventional] | USA | 1980-2025 | 3.96e+06 / 1.39e+07 / 2.61e+07 | Bq/1 | measured |
| oil_gas:0109 | drilling: Horizontal well drill cuttings, potassium-40 activity per well drilled (cuttings mass x activity concentration) | K40/impounded/og_drill_cuttings | us_wells_drilled_horizontal [substream unconventional] | USA | 1980-2025 | 1.05e+08 / 3.4e+08 / 7.29e+08 | Bq/1 | measured |
| oil_gas:0110 | processing_transport: Rn-222 carried in natural gas liquids and LPG (diverted from sales gas at gas plants and released at handling and end use), per m3 of gas produced | Rn222+/liberated/air_delivered_gas/og_processing_residue | gas_production_m3 [substream all] | XWL | 1900-2025 | 10 / 200 / 1e+03 | Bq/m3 | modelled |
| oil_gas:0111 | production: Rn-222 released by flaring per m3 of gas flared (D70, NEW) | Rn222+/liberated/air_stack | gas_flared_m3 [substream all] | XWL | 1950-2025 | 150 / 800 / 1.4e+03 | Bq/m3 | modelled |

## 2. Cross-checks and benchmark candidates (done condition (e))

Arithmetic on the activity spine, central values, no stream build. Electricity: `elec_gen_gas` 4,807.9 TWh (2010) and 6,382.9 TWh (2020); `elec_gen_oil` 1,078.7 and 775.9 TWh; GWa = TWh / 8.766.

**Candidate B1: gas radon per GWa of gas-fired electricity** (the strongest, two or more independent estimates).
- Stream: $\sum$ delivered Rn $\times$ `gas_power_share` / GWa. 2010: 3.223e12 m3 $\times$ 300 Bq/m3 = 967 TBq; $\times$ 0.4255 = 411 TBq; / 548.5 GWa = 0.75 TBq/GWa. 2020: 1,189 TBq $\times$ 0.4453 = 529 TBq; / 728.2 GWa = 0.73 TBq/GWa.
- UNSCEAR 2016 Annex B (S0001): 0.286 m3/kWh $\times$ 300 Bq/m3 = 0.75 TBq/GWa. NOT independent in value (the factor centre is UNSCEAR's delivered concentration) but independent in method (activity-spine gas volume and power share against UNSCEAR's per-kWh gas use).
- REVISION D70 (Steve, 2026-11-04): the pass rule is the one in `docs/OIL_GAS_SPEC.md` section 9(e): the stream (delivered-gas rows only) must be within a factor 3 of at least one of 1.38 (Johnson direct), 0.42 (bottom-up) and 0.50 (Dixon) TBq/GWa; the 0.3-0.5 band and the two unverified figures below are reported, not tested. The NGL row is excluded from B1 (it goes to LPG users).
- REVISION D66 (Steve, 2026-11-04): the Gesell $\times$ Johnson '34 % retention' benchmark (466 Bq/m3, 1.17 TBq/GWa) is withdrawn (round 3). Round-3 position: Johnson 1973 point-of-use 740-851 Bq/m3; consumption-weighted 410-860 Bq/m3; bottom-up about 170 Bq/m3; stream delivered-gas geometric mean 300 Bq/m3. B1 benchmark band 0.3-0.5 TBq/GWa (the UK-type and bottom-up concentrations); the stream sits at 0.73-0.75 TBq/GWa on the 300 Bq/m3 centre (ratio to the band roughly 1.5-2.5), so B1 is a loose check, not a tight one. The NGL row (oil_gas:0110) raises burner radon by about 67 %, which moves the stream further above the band and must be included when the build is compared.
- Independent 2 (unverified): UK about 170 Bq/m3 gives 0.43 TBq/GWa (ratio 1.7) and Netherlands 74 Bq/m3 gives 0.19 TBq/GWa (ratio 3.9, outside $\times3$). These two figures come from Phase 1 notes; I could not re-confirm their source (S1208, Nowak, is a Polish case study with 30-1400 Bq/m3 site averages, not a UK figure).
- Independent 3: Nowak 2022 Poland site means 30-1400 Bq/m3 (S1208) bracket our delivered 48-780 Bq/m3.

**Candidate B2: oil radon per GWa of oil-fired electricity.** Stream 2010: 3.74 TBq $\times$ 0.0799 / 123.1 GWa = 0.0024 TBq/GWa; UNSCEAR 0.002. Weakly independent (same Ra-226 1 Bq/kg basis); Bell et al. 0.7 Bq/kg gives 0.0017.

**Candidate B3: US solids, about 1990 (partly circular).** US 1990 water (3.96e9 m3): Ra-226 24 TBq + Ra-228 40 TBq = 64 TBq at the USA centres; times total solids fraction 1% = 0.63 TBq. EPA 1993 draft via OGJ 1999 (S1209): 25,000 t scale $\times$ 17.76 Bq/g + 227,500 t sludge $\times$ 2.775 Bq/g = 0.44 + 0.63 = 1.1 TBq/a total Ra. Ratio 0.58. The 1% fraction was set with EPA as one anchor, so this is a consistency check, not an independent test.

**Candidate B4: produced-water radium, factor level.** Norway 451 GBq Ra-226 in 129 Mm3 (2011, S0308) = 3.5 Bq/L; OSPAR 0.73-1.1 TBq/a Ra-226 offshore NE Atlantic (S0307); RP 135 reference 10 Bq/L (S0204); UNSCEAR 2000 Table 28 typical installation 174 GBq/a (S0005). The world conventional centre 5 Bq/L sits between Norway and RP 135. The stream gives world Ra-226 to water of about 12 TBq/a liberated outside the USA (2010: 9.9e9 m3 $\times$ 5,000 Bq/m3 $\times$ 0.25) and 1.2 TBq/a in the USA (2010: 21 TBq $\times$ 0.054); no country-level water series exists to compare with OSPAR region by region.

**Other arithmetic checks.**
- Flaring (superseded by D70, kept for the record): 40 m3/t $\times$ 3.9e9 t gives 156 bcm against Elvidge peak 172 (2005) and 139 (2008); the per-tonne form gave 111 TBq/a in 2010 against 106 TBq/a for the new per-m3 row 0111 (132.3 bcm x 800 Bq/m3), 4 % apart. Circular for volume; the Rn concentration is the uncertain part.
- Vented Rn 2010 (D65 value 16 Bq/m3): 16 $\times$ 3.22e12 = 52 TBq/a (was 12.5 and 40 TBq/a). Pb-210 plated out in gas systems 2010 (D70 value 0.107 Bq/m3): 0.107 $\times$ 3.22e12 = 0.35 TBq/a head Pb-210 (was 0.12 Bq/m3 and 0.40 TBq/a before D65, 0.189 Bq/m3 and 0.61 TBq/a under D65).
- Oil sands 2024: 1,019.4 Mt $\times$ 5,684 Bq/t = 5.8 TBq/a Th-232 (and equal Ra-228, Th-228).
- Drilling, US vertical per well: Ra-226 2.6e7 Bq (range 6e6-7.8e7). Horizontal Ra-226 1.2e8 Bq per well. Cuttings Ra-226 is about 1.4 TBq/a against about 20 TBq/a in produced water at 2010.
- Basin check on the US unconventional blend: Ra-226 30 Bq/L against NPWGD v3 means 54-84 (Appalachia, Bakken) and Scanlon medians 10-73.

**Epsilon and seepage proposals (WRITTEN by D62 for og_produced_water, og_drill_cuttings, og_scaled_scrap and oil_sands_tailings, and by D70 for the rest: og_scale and og_sludge Rn-222 only, og_processing_residue 0/0/0 for both radons; Rn-220 for og_scale and og_sludge WRITTEN by D71, 2026-11-05, see section 11). D60 convention: Rn-222 epsilon = emanation coefficient (upper bound of effective exhalation); Rn-220 epsilon = emanation $\times$ slab factor $f=(L/H)\tanh(H/L)$, $L$ = 0.005 / 0.01 / 0.02 m. Bounds: low = em_low $\times f(L_{low},H_{high})$, central = em_c $\times f(L_c,H_{gm})$, high = em_high $\times f(L_{high},H_{low})$.**

| residue type | eps Rn-222 low / central / high | basis | eps Rn-220 low / central / high | seepage per a low / central / high |
|---|---|---|---|---|
| `og_scale` | 0.037 / 0.088 / 0.14 | S0321 White and Rood site means 0.037-0.138, geometric mean 0.088 | 1.8e-5 / 3.6e-4 / 3.9e-3 (emanation 0.011 / 0.044 / 0.098; H 0.5 / 1.2 / 3 m; thickness assumption) | already filled: 3e-9 / 3e-8 / 4e-6 |
| `og_sludge` | 0.05 / 0.15 / 0.25 | analogy to soil and sludge (assumption) | 2.5e-5 / 6.1e-4 / 5e-3 | already filled: 1e-8 / 5e-8 / 4e-6 |
| `og_drill_cuttings` | 0.05 / 0.15 / 0.25 | rock-and-soil analogy (assumption) | about 3e-5 / 3.2e-4 / 2.8e-3 | 7e-7 / 6e-6 / 6e-5 (generic M1 mineral-waste value, grade C) |
| `og_scaled_scrap` | as `og_scale` | scale on steel | as `og_scale` | as `og_scale` |
| `og_processing_residue` | not applicable (Pb-210 films; Rn-222 parent absent); **D70: explicit 0 / 0 / 0** | - | not applicable; **D70: explicit 0 / 0 / 0** | as `og_sludge` |
| `og_produced_water` | 0.1 / 0.2 / 0.3 (soil after spreading) | assumption; reisolated fraction treated as permanent | 0 (spread water: negligible) | no value proposed; reisolated is permanent by construction |
| `oil_sands_tailings` | 0.002 | monazite emanation from `research/wind_solar/notes.md` (source ID not recorded there; verify) | 0.0002 $\times f$ | 1e-6 / 1.1e-5 / 1.25e-4 (the `ree_tailings` Th triple) |
| `oil_sands_coke` | no data | - | no data | no data |

Not blockers for the factor file, but the pipeline refuses residue types that have data rows and empty parameters; with D62 and D70 every oil and gas residue type that has data rows is now filled (`og_scale` and `og_sludge` Rn-222 by D70 and their Rn-220 triples by D71). `oil_sands_coke` has no rows.

## 3. Gap register

| # | Item | Why no row | URL if inaccessible | Blocks the engine? |
|---|---|---|---|---|
| G1 | Radium in produced water: Middle East, Russia, China, Africa, Latin America | no measurements in Phase 1 or NPWGD; XWL centre is extrapolated from US and Norway | S0315 https://doi.org/10.1016/j.scitotenv.2020.137085 | No (wide band) |
| G2 | NPWGD has no Ra data for TX, OK, KS, LA; Permian only via NM (S0316) | US volume-weighted value rests on ANL state volumes | S0313 https://digital.library.unt.edu/ark:/67531/metadc836481/m2/1/high_res_d/1007397.pdf | No |
| G3 | NGL, LPG and propane radon (PARTLY CLOSED by D65 row 0110, low confidence; the radon budget now closes with 0076 recomputed by D70); refinery sludge; Pb-210 fouling of fractionation units | NGL Rn now a per-m3-of-gas inference; refinery sludge and fouling still no data | none | No (understates) |
| G4 | Reservoir-sourced Pb-210/Po-210 in gas and oil; Po-210 films | volatile Po-210 not separable; only a mass-balance Pb-210 row | none | No |
| G5 | Oil-sands tailings and coke background (K-40, U, Th of sand and clay) | no measurements; quartz-sand placeholders would add hundreds of TBq of K-40 | none | No (choice 9) |
| G6 | Monazite U-series in oil-sands tailings; Th content only from an abstract | S0429 abstract only | S0429 https://apo.ansto.gov.au/dspace/handle/10238/12874 | No |
| G7 | World well counts and US horizontal well counts | no series | none | No (the US split series exist since D66; world drilling absent) |
| G8 | Flared gas volume before 1994 and by country | satellite record starts 1994 | S1204 PDF (download failed) | No (the volume series `gas_flared_m3` now exists, 1950-2025; row 0111 is per m3 flared) |
| G9 | Oil, gas and NGL unit values for the D6 default allocation | none in `commodity_prices.csv` | none | No (resolved: `unit_value_*` series exist; D6 by value, spec section 4) |
| G10 | Retired tubular and scrap tonnage | no series; replaced by the retained-scale share $\phi$ (assumption) | none | No |
| G11 | Cuttings K-40, Th and U outside Pennsylvania; cuttings tonnage per well | only PA DEP and one NY figure | S0301 | No |
| G12 | Unconventional produced-water share by play; years before 2017 | single measured point | S0312 https://www.gwpc.org/publications/u-s-produced-water-volumes-and-management-practices-in-2017/ (check URL in `sources.csv`) | No |
| G13 | Pre-1950 produced water (no driver), so no pre-1950 solids | `produced_water_m3` starts 1950 | none | No; D31 opening stock omits O&G scale pre-1950 |
| G14 | Time variation of produced-water radium (water cut, reservoir souring) | no data | none | No |
| G15 | Overburden / earth moved memo for oil-sands mining | no series | none | No (memo tier) |
| G16 | Sludge retained at decommissioning; descaling dust and cutting releases (liberated at abandonment) | no data | none | No |
| G17 | Primary reports read only through secondaries: Johnson 1973 (EPA-520/1-73-004), Gesell 1975 (Health Phys 29:681), Bell et al., EPA 1993 diffuse-NORM (RAE-9232), Alberta Chamber of Resources 1996, Chachula and Erasmus 2008 | not obtained | IOGP Report 412 https://www.iogp.org/bookstore/product/412/ | No |

## 4. Blockers (for the orchestrator): ALL RESOLVED (status 2026-11-04)

Original text kept in brackets for the record.

- **B1 (resolved)** [Activity series `oil_sands_ore_processed_t` missing; rows 0085-0087 blank driver.] The series exists (`data/activity/oil_gas_drivers.csv`, CAN 1967-2025) and D70 set `driver_series` on 0085-0087. 2024 anchor: 1,019.4 Mt (S0326).
- **B2 (resolved)** [`us_wells_drilled_horizontal` missing.] The series exists (USA 1980-2025); D66 set the drivers, years and substreams of 0088-0109.
- **B3 (resolved)** [Flared gas volume series missing; per-tonne proxy.] `gas_flared_m3` exists (XWL 1950-2025, GGFR country rows 2012-2025); D70 added `oil_gas:0111` (per m3 flared) and retired 0071-0073.
- **B4 (resolved)** [Oil, gas, NGL unit values and an NGL series for the D6 allocation.] `unit_value_oil_usd_per_m3`, `unit_value_gas_usd_per_m3`, `unit_value_ngl_usd_per_m3` and `ngl_production_m3` exist; D70 fixed the rules: default by value, `bound_main` = largest value, `bound_radio` = gas (R3, spec section 4.5).
- **B5 (resolved)** [Residue-type parameters for five used residue types.] D62 filled four; D70 filled `og_scale` and `og_sludge` (Rn-222) and `og_processing_residue` (0/0/0).
- **B6 (done)** Source merge: `research/oil_gas/sources_factors.csv` (S1200-S1209) merged into `data/sources.csv`.
- **Observation (resolved), previously out of scope:** the `XWL` produced-water series was below `USA` in early years (1950: 5.8e8 against 1.5e9 m3). The activity series now satisfy world >= USA at every bound (smallest central gap 3.05e8 m3 in 1950, checked in OIL_GAS_SPEC section 5.1), and D70 settles the rest-of-world water volume as a **correlated** difference; `negative_residual` is not expected for water.

## 5. Choices for Steve

1. **Keying (resolved by D63/D65: the `substream` column now separates conventional and unconventional; see section 8).** Original text: **Keying without a substream column.** Conventional/unconventional concentration rows use `driver_series` (`produced_water_m3` against `produced_water_unconv_share`) as a discriminator, and the unit-1 shares use blank group. Alternative: add a `substream` match key to `select` and the factor schema. Recommend the schema change if more streams need it.
2. **Unconventional produced-water fraction eras** (0.5% to 2005, 4% 2006-10, 12% 2011-16, 16% 2017, 20% 2018-25) are assumptions anchored on one point (2017).
3. **Rn-222 in-system decay.** Only Rn that leaves the system is Rn222+; Rn that decays in pipes and plants is not counted as Rn222+ and appears only as plated Pb-210 (0076). Alternative: count all wellhead Rn. (D70: the in-system decay is wellhead 800 less delivered 300, NGL 200 and vented 16 = 284 Bq/m3, so the budget closes.)
4. **Flaring placed at stage `production`, route `air_stack`**, radon at the wellhead concentration; no vocabulary stage exists for flaring. Alternative: processing_transport. (D70: confirmed, per m3 flared via row 0111, product `oil`, substream `all`.)
5. **Retained scale ($\phi$ = 0.9, 0.6-0.97 since D65; was 0.5, 0.2-0.8) booked in the creation year at `abandonment_scrap`**, with the 20-year retirement lag built into the era windows and no decay survival factor (replaces my earlier Ra-228 survival idea, which would double-count decay). Sludge is assumed removed in operation.
6. **Era fate shares for removed and retained solids** (pre-1985, 1985-99, 2000+): wholly assumed.
7. **Pre-1970 and world produced-water route shares:** assumed; US 2007/2012/2017 are data. The world discharge share 25% (high 42% = IOGP members) could be higher if national oil companies discharge more.
8. **Solids fraction 2% (0.1-10%) of outlet water radium since D65** (was 1%; EPA 1991 draft 5.1%, EPA 1993 via OGJ 1.7%; Norway 0.04-4%); scale/sludge split 0.4/0.6 (scale share band 0.2-0.9).
9. **Oil-sands background sand, clay and coke left out** of the registry (placeholders would add hundreds of TBq of K-40 and swamp the monazite signal); only the monazite thorium chain is carried. Alternative: add a background row with a clearly flagged assumption.
10. **Oil-sands monazite per tonne of ore:** 7.5e-6 / 2.0e-5 / 7.1e-5 t/t spans the AER arithmetic (0.3-0.5% of whole tailings) and the reading as heavy-mineral fraction (15-30% of tailings). Th in monazite 7% (4-12%).
11. **Wellhead radon 800 Bq/m3 since D65** (was 625), world (150-1,400); no USA or other country override. Delivered 300 Bq/m3 kept, so the implied delivered fraction is 0.375 (was 0.48; 0.15-0.8).
12. **Drilling:** vertical cuttings 250 t/well (assumption, lowered from 295 t), horizontal 600 t (330-1,000); U-chain taken from XRF (gamma U-238 is 5x lower for horizontal wells); Pb-210 and Po-210 at Ra-226 equilibrium.
13. **`bound_radio` product definition** (D6) (RESOLVED by D70: `bound_radio` = gas, rule R3 of the spec, the second-ranked product by value; default allocation by value, `bound_main` = the largest value). Original text: proposed as the product with the larger share of the mobilised radium in the joint residue (water-borne radium: oil and NGL by volume of water produced; gas Pb-210 films: gas).
14. **No construction rows** (commodity table covers it) and no refinery residue rows.
15. **Oil sands start 1967** and the monazite factor is held constant over time.

## 6. Proposed stream-script outline (SUPERSEDED: the contract is `docs/OIL_GAS_SPEC.md` v1.0; this outline is the original proposal and is stale where it names `us_wells_drilled_total`, B1-B4, per-tonne flaring or the blended water formula)

Interface as coal: `build(root) -> BuildResult(rows, rows_pre1950, log)`; `python -m pipeline.streams.oil_gas [--root] [--write]`; outputs `data/streams/oil_gas.csv` (1950-2025) and `data/streams_pre1950/oil_gas.csv` (1900-1949). World rows country `XXX`. Pure function of `data/`; no decay, ingrowth, exhalation or seepage.

**Drivers** (`data/activity/oil_gas.csv`): `oil_production_t`, `gas_production_m3` (43 countries plus `XWL`, rest of world by independent difference), `produced_water_m3` (`USA`, `XWL`), `us_wells_drilled_total` (USA to 2010), `gas_power_share`/`oil_power_share`/`elec_gen_*` for benchmarks only. Missing at the time: B1-B4 (all now present).

**Stages and rules.**
- `production`: (a) produced-water activity by group (blend of conventional and unconventional, section 0); (b) tier split with rows 0019-0046; (c) solids $S$, removed share by tiers 0053-0070; (d) flaring Rn222+ by country on `gas_flared_m3` (row 0111; D70).
- `processing_transport`: delivered Rn (`air_delivered_gas`), vented Rn (`air_vented_gas`), Pb-210 deposits (impounded `og_processing_residue`) per country on `gas_production_m3`; oil radon on `oil_production_t`. Product column: gas or oil as the driver; NGL and bitumen not covered.
- `abandonment_scrap`: retained scale $S\phi$ by creation-year window (impounded, dispersed).
- `oil_sands_mining` (CAN, substream `oil_sands`, product `bitumen`): ore $\times$ factor for Th232, Ra228+, Th228+, impounded `oil_sands_tailings`. Blocked by B1.
- `drilling` (USA, substream per well type): wells $\times$ per-well factor, impounded `og_drill_cuttings`. Horizontal blocked by B2.
- Allocation (D6): joint residues (water-borne radium, drilling cuttings) across oil, gas and NGL; variants `default`, `bound_main`, `bound_radio` all emitted once any is non-default (X03). Blocked by B4 for `default`.
- No inter-tier transfers at O&G stages. Rn222+/Rn220+ rows only as liberated flows. Release cap (D54) applies to the liberated shares of produced water: never above the group's water activity.
- Independent versus correlated helpers: concentrations, shares and $\sigma$ are independent; the rows made of several parameters are already combined in log-quadrature and must not be recombined. The delivered-Rn row (0074) and Pb-210 deposit row (0076) are anticorrelated through $r$; the Ra-226/Ra-228/K-40/Pb-210 concentration rows of one region are correlated (same reservoir water).

**Log kinds:** `no_factor`, `negative_residual` (see observation in section 4), `no_driver`, `cap_applied`, `blocked_driver` (B1, B2).

**Done conditions (proposed):** (a) validator passes; (b) share rows sum to 1 at centre per region and era; (c) key uniqueness; (d) every liberated row has a route; (e) benchmark B1 within $\times3$ of at least one independent value for 2010 and 2020 (D70 rule: at least one of 1.38, 0.42, 0.50 TBq/GWa; the Gesell figure is withdrawn), B2 and B3 as consistency checks; (f) tiers within the stage-tier matrix; (g) pre-1950 file has flows only; (h) determinism.

## 7. Inaccessible or unverified items (most to least important)

1. EPA 1993 diffuse-NORM report (primary of S1209; the Ra solids fraction rests on it): not obtained. Search: EPA 402-R-93-083 / RAE-9232 "Diffuse NORM wastes".
2. S0313 Clark and Veil 2009 (ANL/EVS/R-09/1): read via https://digital.library.unt.edu/ark:/67531/metadc836481/m2/1/high_res_d/1007397.pdf; suggest updating its URL and access in `sources.csv`. S0312 GWPC 2020: https://www.gwpc.org/publications/u-s-produced-water-volumes-and-management-practices-in-2017/
3. S0315 Scanlon 2020: https://doi.org/10.1016/j.scitotenv.2020.137085 (paywalled); S0325 Tasker 2018: https://doi.org/10.1021/acs.est.8b00716 (paywalled).
4. World Bank GGFR 2024 tracker PDF (download failed): https://www.worldbank.org/en/programs/gasflaringreduction/publication/2024-global-gas-flaring-tracker-report
5. IOGP Report 412: https://www.iogp.org/bookstore/product/412/
6. Johnson 1973 (EPA-520/1-73-004), Gesell 1975 (Health Phys 29:681), Bell et al.: read only via UNSCEAR/Mitchell.
7. S0429 Anvia (abstract only): https://apo.ansto.gov.au/dspace/handle/10238/12874; Alberta Chamber of Resources 1996; Chachula and Erasmus 2008 (via S0326).
8. S1203 author list and S1208 UK/NL values unverified (section 2).

## 8. D65 revisions (Steve, 2026-11-04; oil and gas part)

Source of numbers: `research/oil_gas/papers_round2.md`, `papers_round3.md`. Sources merged into `data/sources.csv` (S1210-S1215, S1250-S1263; corrections to S0315, S0325, S1204, S0429, S0246, S1209; S1211 combines the round-2 row and the round-3 supplement). Type and licence fixes at merge: S1210 `industry_body` to `grey` (rank 5); S1212 `intergovernmental` to `compilation` (rank 2); S1214/S1215 rank 1 (regulator); licence `CC BY` to `open` (S0315, S1204); landing-page URLs added for inaccessible sources (schema requires a URL).

| Row(s) | Old low / central / high | New low / central / high | Note |
|---|---|---|---|
| 0003 Ra-226 unconventional | 1e4 / 3e4 / 8e4 Bq/m3 | 1e3 / 1.24e4 / 5.5e4 | total Ra 24.8 Bq/L (Scanlon, volume-weighted) split equally with Ra-228; band spans total 2-110 Bq/L |
| 0006 Ra-228 unconventional | 5e3 / 2e4 / 6e4 | 1e3 / 1.24e4 / 5.5e4 | as above |
| 0001, 0002, 0004, 0005, 0007, 0009 | unchanged | unchanged | conventional (0001 is already 5 Bq/L Ra-226); `substream` = conventional added |
| 0008, 0010 | unchanged | unchanged | `substream` = unconventional added |
| 0047, 0049 scale (Ra-226, Ra-228) | 4e-4 / 4e-3 / 1.6e-2 | 3.7e-4 / 8e-3 / 4.85e-2 | total 0.001/0.02/0.10 x scale share 0.4 (0.2-0.9), log-quadrature |
| 0048, 0050 sludge | 6e-4 / 6e-3 / 2.4e-2 | 3.7e-4 / 1.2e-2 / 6.16e-2 | total x sludge share 0.6 (0.1-0.8) |
| 0078 retained scale $\phi$ | 0.2 / 0.5 / 0.8 | 0.6 / 0.9 / 0.97 | EPA 1991 draft |
| 0074 delivered Rn-222 | 47.6 / 300 / 779 | 47.6 / 300 / 1,000 | round-2 cut withdrawn; high only |
| wellhead Rn (parameter; in 0071-0073, 0075, 0076 and 0110) | 625 (150-1,400) | 800 (150-1,400) | production-weighted Johnson 1973; bounds kept (round 3 suggested 185-3,700) |
| 0071 flaring, 1900-93 | 6395 / 31250 / 84772 | 6534 / 40000 / 90059 | wellhead x intensity, same log-quadrature |
| 0072 flaring, 1994-2008 | 5963 / 25000 / 57151 | 5968 / 32000 / 57645 | |
| 0073 flaring, 2009-25 | 5525 / 23125 / 52315 | 5528 / 29600 / 52540 | |
| 0075 vented | 1.71 / 12.5 / 42.4 | 1.82 / 16 / 46.8 | 2% x wellhead |
| 0076 Pb-210 plate-out | 0.0163 / 0.1226 / 0.311 | 0.0188 / 0.1886 / 0.356 | wellhead 800 and (1 - r) = 0.625 (r = 300/800 = 0.375) |
| 0110 NEW NGL/LPG Rn-222 | none | 10 / 200 / 1,000 Bq/m3 gas | 800 x 0.5 x 0.5; LOW CONFIDENCE (flagged) |

**Keying for the OIL_GAS_SPEC (select calls).**
- Produced-water concentration, stage `production`: `select(stage="production", substream="conventional"|"unconventional", group=<Ra226+|Ra228+|K40|Pb210+>, region=<USA|XWL>, year=y)` (exact region beats `XWL`; USA override exists for the conventional Ra rows only). The legacy `driver_series` (`produced_water_m3` for conventional, `produced_water_unconv_share` for unconventional) is unchanged, so calls that include it and omit `substream` still resolve uniquely. Recommended later clean-up (not done, would break such calls): set the unconventional driver to `produced_water_m3` and require `substream`.
- Unconventional share $u$ (0011-0018): `select(stage="production", driver_series="produced_water_unconv_share", group="", substream="", region=...)`; blank group and substream separate it from the concentration rows.
- NGL radon 0110: `select(stage="processing_transport", group="Rn222+", route="air_delivered_gas", residue_type="og_processing_residue")` for NGL; the delivered-gas row 0074 has blank `residue_type`. The residue type is only a key device (as for the liberated fate rows); the master row carries no residue. Cleaner alternative: add route `air_delivered_ngl` to vocab.json, then drop the residue type.
- Drilling rows gained substreams in D66 (see section 9); oil sands rows keep `substream` blank in the registry and the stream writes `oil_sands`; gas, NGL, vented, oil radon, plate-out and flaring gained `all` in D70 (section 10). All other rows keep a blank `substream`.

**Drilling driver switch (proposal only; not built).** Rows 0088-0098 (vertical, `us_wells_drilled_total`, 1949-2010) and 0099-0109 (horizontal, blank driver, 2005-2025): `data/activity/oil_gas_drivers.csv` now has `us_wells_drilled_vertical` (USA, 1949-2025; before 1976 the EIA total is taken as vertical) and `us_wells_drilled_horizontal` (USA, 1980-2025). Cleanest switch: (1) set the driver of 0088-0098 to `us_wells_drilled_vertical` and `year_to` to 2025, and set that of 0099-0109 to `us_wells_drilled_horizontal`; (2) set `substream` to `conventional` for the vertical and `unconventional` for the horizontal cuttings rows, so the spec selects by substream and the series by driver; (3) extend `year_from` of the horizontal rows from 2005 back to 1980 (or cap at 2005 and accept that about 700-2,000 horizontal wells a year in 1995-2004 get no cuttings), a choice for Steve; (4) retire `us_wells_drilled_total` for drilling (it ends 2010 in `oil_gas.csv`, and in 2010 vertical 20,478 + horizontal 10,180 = 30,658 against a total of 36,611, so the total includes wells the split series does not count: re-check the per-well factors against which count they assumed). Until the rows are switched the spec must not use `us_wells_drilled_total` beyond 2010.

## 9. D66 revisions (Steve, 2026-11-04)

| Row(s) | Old low / central / high | New low / central / high | Note |
|---|---|---|---|
| 0003 Ra-226 unconventional | 1,000 / 12,400 / 55,000 Bq/m3 | 1,181 / 14,880 / 67,100 | total Ra 24.8 Bq/L x share 0.6 (0.45-0.75); total range 2-110 Bq/L; log-quadrature (arithmetic in the row notes); source S0300 added |
| 0006 Ra-228 unconventional | 1,000 / 12,400 / 55,000 | 766 / 9,920 / 45,500 | share 0.4 (0.25-0.55) |
| 0088-0098 vertical cuttings | driver `us_wells_drilled_total`, 1949-2010, substream blank | driver `us_wells_drilled_vertical`, 1949-2025, substream `conventional` | per-well values unchanged |
| 0099-0109 horizontal cuttings | driver blank, 2005-2025, substream blank | driver `us_wells_drilled_horizontal`, 1980-2025, substream `unconventional` | per-well values unchanged |

- Rowan et al. 2011 is already in `data/sources.csv` as S0300 (same report, SIR 2011-5135), so no S1270 row was added (it would duplicate S0300); the D66 quotation was appended to the S0300 notes and S0300 added to the source IDs of 0003 and 0006.
- Per-well cuttings factors: each is cuttings mass per well (100/250/450 t vertical; 330/600/1,000 t horizontal) times a PA DEP TENORM concentration. None divides a total by a well count, so the change of count (36,611 total against 20,478 vertical + 10,180 horizontal = 30,658 in 2010) changes the number of wells the factors multiply, not the factors. The cuttings mass per well is a typical-well assumption, so the 5,953 wells in 2010 that the split series does not count (36,611 - 30,658) simply carry no cuttings now.
- `us_wells_drilled_total` is retired for drilling: no factor row uses it. It remains in `data/activity/oil_gas.csv` (outside this task's file scope; see the report to the orchestrator).
- Keying: drilling rows are selected by `stage="drilling"`, `substream` (`conventional` vertical, `unconventional` horizontal), group, and the driver; keys remain unique (disjoint drivers and substreams). The produced-water rows use the same substream values.
- Early horizontals (1980-2004) take the 2-3 km-lateral cuttings mass, probably an overstatement.

## 10. D70 revisions (Steve, 2026-11-04; oil and gas part)

Schema v2.4b: `vocab.json` `substreams.oil_gas` gains `all`.

| Row(s) | Old | New | Note |
|---|---|---|---|
| 0071-0073 flaring per tonne of crude | active | RETIRED (D70); values and years unchanged, description and notes marked | superseded by 0111; never selected (select passes `driver_series="gas_flared_m3"` and `substream="all"`); kept because DECISIONS.md, the spec and these notes cite them by id |
| 0111 NEW flaring per m3 flared | none | 150 / 800 / 1,400 Bq/m3, `Rn222+`, liberated, `air_stack`, stage `production`, substream `all`, driver `gas_flared_m3`, XWL 1950-2025, basis modelled, S1203;S1204;S0001 | the D65 wellhead Rn parameter; radon is not destroyed in the flame |
| 0074, 0075, 0077, 0110 | `substream` empty | `all` | values unchanged |
| 0076 Pb-210 plate-out | 0.0187889 / 0.1886 / 0.356009 Bq/m3 (`substream` empty) | 0.0144083 / 0.107125 / 0.29161, substream `all` | in-system decay = 800 - 300 - 200 - 16 = 284 Bq/m3 (was 500 = 800 x 0.625): central 284 x 4.715e-4 x 0.8 = 0.107125; bounds by log-quadrature with the decayed fraction 0.355 (band 0.15-0.8 kept), wellhead 150-1,400, p_dep 0.4-0.95: exp(-2.0062) and exp(+1.0014) |
| 0085-0087 oil sands | `driver_series` empty | `oil_sands_ore_processed_t` | values unchanged |
| `og_scale` epsilon Rn-222 | empty | 0.037 / 0.088 / 0.14 | White and Rood site means (S0321, added to source_ids) |
| `og_sludge` epsilon Rn-222 | empty | 0.05 / 0.15 / 0.25 | soil/sludge analogy (S0242, added to source_ids) |
| `og_processing_residue` epsilon Rn-222 and Rn-220 | empty | 0 / 0 / 0 | Pb-210 and Po-210 films, no parent |

Not applied by D70: Rn-220 epsilon for `og_scale` (1.8e-5 / 3.6e-4 / 3.9e-3) and `og_sludge` (2.5e-5 / 6.1e-4 / 5e-3): D70 names only the Rn-222 triples. Applied later by D71 (section 11).

Other D70 decisions (spec text, no registry change): `bound_radio` = gas (R3), default by value, `bound_main` = largest value; drilling US only, 1949 omitted; rest-of-world produced water a correlated difference; gas-radon benchmark within a factor 3 of at least one of 1.38, 0.42, 0.50 TBq/GWa; solids merged into the liberated and impounded-sludge rows.

## 11. D71 revisions (Steve, 2026-11-05; oil and gas part)

| Row(s) | Old | New | Note |
|---|---|---|---|
| `og_scale` epsilon Rn-220 | empty | 1.8e-5 / 3.6e-4 / 3.9e-3 | the section 2 proposal: emanation 0.011 / 0.044 / 0.098 times the D60 slab factor (L 0.005 / 0.01 / 0.02 m, H 3 / 1.2 / 0.5 m, a thickness assumption); same triple as `og_scaled_scrap`; source S0321 already on the row |
| `og_sludge` epsilon Rn-220 | empty | 2.5e-5 / 6.1e-4 / 5e-3 | the section 2 proposal: soil and sludge analogy (assumption) with the same slab factors (equivalent to emanation about 0.015 / 0.075 / 0.125, back-computed); source S0242 already on the row |

With D71 every epsilon and seepage parameter that a used tier needs is filled for every oil and gas residue type with data rows. `python -m pipeline.validate --root .` reports no issues. The other D71 items (C1–C9) are spec clarifications with no registry change: `docs/OIL_GAS_SPEC.md` v1.1, section 13.
