# Task 1.7 baselines: derivations, inputs and caveats

Reproduced by `research/baselines/compute_baselines.py` (stdlib only; reads `data/reference/nuclides.csv` and `groups.csv`). Run `python3 research/baselines/compute_baselines.py` from the outputs root to compare with `data/baselines.csv`; `--write` regenerates it; `--print` lists the table. Source IDs are in `sources_task17.csv` (S0600-S0613) or S9005 (IAEA LiveChart).

## Conventions

- Values are head activity (D24): the Bq of the named head nuclide only (Rn-222, U-238, Th-232, Cs-137, Sr-90), not the whole chain.
- Low/central/high are read as roughly 5th/50th/95th. Products combine by log-space quadrature (METHODS 11.1):

$$\ln\frac{x_\mathrm{high}}{x_\mathrm{c}}=\sqrt{\sum_i\ln^2\frac{x_{i,\mathrm{high}}}{x_{i,\mathrm{c}}}}$$

- **Where a source gives no uncertainty, the bound is a stated judgement** (marked J below). Only B01's bounds are neither statistical nor judgemental: they are the span of published central estimates.
- Power from activity: $P=A\,\bar E$, with $\bar E$ in J from `groups.csv` (antineutrino excluded), 1 MeV $=1.602\,176\,634\times10^{-13}$ J.
- Julian year $t_a=3.155\,76\times10^{7}$ s; 1 Ci $=3.7\times10^{10}$ Bq.
- Specific activity of an element from the nuclide's decay constant (`lambda_per_a` in nuclides.csv $/t_a$):

$$a_X=\lambda_X\,\frac{1000\,N_\mathrm{A}}{M}\,f_X\quad[\mathrm{Bq\,kg^{-1}\ of\ element}]$$

| Constant | Value | Source |
|---|---|---|
| $\lambda_{\mathrm{K40}}$ | $1.7558\times10^{-17}\ \mathrm{s^{-1}}$ (T½ 1.251 Ga) | nuclides.csv (ICRP 107) |
| K-40 atom fraction $f$ | 0.000117 (0.0117 %, ±0.0001 %) | S9005 |
| U-238 atom fraction | 0.992742 | S9005 |
| $M_\mathrm{K},M_\mathrm{U},M_\mathrm{Th}$ | 39.0983, 238.02891, 232.0377 g/mol | IUPAC standard atomic weights (not separately cited) |
| $a_\mathrm{K40}$ | $3.164\times10^{4}$ Bq/kg K | computed |
| $a_\mathrm{U238}$ | $1.235\times10^{7}$ Bq/kg U | computed |
| $a_\mathrm{Th232}$ | $4.057\times10^{6}$ Bq/kg Th | computed |

## Ice-free land area (used by B07, B12-B14, B21)

$$A_\mathrm{land}=148.94\times10^{12}-14.2\times10^{12}-2.166\times10^{12}=1.326\times10^{14}\ \mathrm{m^2}$$

Bounds $1.30\times10^{14}$ (J) to $1.347\times10^{14}$ (Greenland counted as land). Input from S0613 (grey, round figures). Small ice caps and the ice-free fringe of Greenland are ignored (a fraction of a per cent).

## B01-B04 Earth's radiogenic heat

**Observations (W, power only; D11).**

| Estimate | Heat (TW) | Source |
|---|---|---|
| Borexino 2020, total U+Th (68 %) | $38.2^{+13.6}_{-12.7}$ (mantle $24.6^{+11.1}_{-10.4}$, lithosphere $8.1^{+1.9}_{-1.4}$) | S0600 |
| KamLAND 2022, mantle U+Th, Th/U fixed 3.9 | $10.6^{+5.2}_{-4.2}$ (Th/U free: $15.4^{+8.3}_{-7.9}$; modern crust model: $9.2^{+9.0}_{-4.6}$) | S0601 |
| KamLAND 2022, crust (reference model) | U 3.4, Th 3.6 | S0601 |
| KamLAND 2022, total Earth incl. ~4 TW K-40 | ~14.6 | S0601 |
| Huang et al. 2013, BSE total | 20.1 (continental crust $6.8^{+1.4}_{-1.1}$) | S0602 |
| Surface heat loss (context) | $47\pm2$ | S0603 |

**B01.** Low $=14.6$ TW (KamLAND total), central $=20.1$ TW (Huang BSE, matching D11's ~20 TW), high $=38.2+4.0=42.2$ TW (Borexino U+Th plus the ~4 TW K-40 quoted by KamLAND/BSE):

$$P_{\mathrm{rad}}\in[1.46,\ 2.01,\ 4.22]\times10^{13}\ \mathrm{W}$$

These are published central estimates spanning the field, not a 5th-95th interval. The Borexino 68 % band alone runs to $38.2+13.6=51.8$ TW (U+Th), above the 47 TW surface heat loss.

**B02-B04 split (modelled).** Specific radiogenic power $h$ (W per kg of element) from the energy per chain, summing `e_per_head_decay_mev` of the chain groups (antineutrino excluded):

$$E_{\mathrm{U238}}=\sum_{g\in\{\mathrm{U238+,U234,Th230,Ra226+,Pb210+,Po210}\}}\bar E_g=47.750\ \mathrm{MeV}$$

$$E_{\mathrm{U235}}=44.468\ \mathrm{MeV},\qquad E_{\mathrm{Th232}}=40.346\ \mathrm{MeV},\qquad E_{\mathrm{K40}}=0.67847\ \mathrm{MeV}$$

$$h_\mathrm{U}=\bar E\!\left[\lambda_{238}n_{238}E_{\mathrm{U238}}+\lambda_{235}n_{235}E_{\mathrm{U235}}\right]=9.85\times10^{-5},\quad h_\mathrm{Th}=2.62\times10^{-5},\quad h_\mathrm{K}=3.44\times10^{-9}\ \mathrm{W\,kg^{-1}}$$

With BSE mass ratios Th/U $=3.9$ and K/U $=14\,000$ (S0602), the shares of total power are

$$f_i=\frac{h_i r_i}{\sum_j h_j r_j},\qquad f_\mathrm{U}=0.396,\ f_\mathrm{Th}=0.411,\ f_\mathrm{K}=0.193$$

which gives, at 20.1 TW, U series 7.95 TW, Th series 8.26 TW and K-40 3.89 TW; the low/high scale the same fractions. **Caveat:** the fractions follow the BSE mass ratios, not the (poorly constrained, Th/U-free) geoneutrino fits. Borexino and KamLAND constrain U and Th only; K-40 geoneutrinos are below the inverse-beta threshold, so K is always model-based.

## B05-B06 K-40 in the oceans

$$m_\mathrm{K}=V\,\rho_\mathrm{sw}\,w_\mathrm{K},\qquad w_\mathrm{K}=\frac{10.21\ \mathrm{mmol\,kg^{-1}}\times39.0983\ \mathrm{g\,mol^{-1}}}{1000}=0.3992\ \mathrm{g\,kg^{-1}}$$

$$m_\mathrm{K}=1.332\times10^{18}\ \mathrm{m^3}\times1028\ \mathrm{kg\,m^{-3}}\times3.992\times10^{-4}=5.47\times10^{17}\ \mathrm{kg}$$

$$A_\mathrm{K40}=m_\mathrm{K}\,a_\mathrm{K40}=5.47\times10^{17}\times3.164\times10^{4}=1.73\times10^{22}\ \mathrm{Bq}\quad(\text{range }1.69\text{-}1.76\times10^{22})$$

$$P=A\,\bar E_{\mathrm{K40}}=1.73\times10^{22}\times0.67847\times1.602\times10^{-13}=1.88\times10^{9}\ \mathrm{W}\ (1.9\ \mathrm{GW})$$

Inputs: ocean volume 1.332 Gm$^3$ (S0608), K$^+$ 10.21 mmol/kg at S $=35$ (Millero et al. 2008 via S0610/S0609), atom fraction (S9005). Caveats: (i) seawater density (1025-1031, J) is a standard constant, not cited to a primary table; (ii) the low bound uses S $=34.5$ (J) to reflect mean-ocean salinity slightly below 35; (iii) the bounds are narrow (~2 %) because K is conservative in seawater, and the answer is dominated by the choice of decay data (T½ 1.248 Ga in ENSDF vs 1.251 Ga in ICRP 107, 0.2 %); (iv) the 0.678 MeV includes the photons following electron capture to Ar-40 but excludes antineutrinos.

## B07 Natural radon exhalation from land

$$F_\mathrm{Rn}=\Phi\,A_\mathrm{land}\,t_a$$

- UNSCEAR 2000 mean worldwide flux $\Phi=0.016\ \mathrm{Bq\,m^{-2}\,s^{-1}}$ (S0604 para 99): $0.016\times1.326\times10^{14}\times3.156\times10^{7}=6.7\times10^{19}$ Bq/a.
- Hirao et al. (S0607) global average 21.3 mBq m$^{-2}$ s$^{-1}$: $8.9\times10^{19}$ Bq/a.
- Zhang et al. 2021 (S0606) inventories 1.94 (uniform 1 atom cm$^{-2}$ s$^{-1}$, JA97), 2.11 (ZK11), 2.22 (ZKC), 2.41 (SW98) GCi/a, with 1 GCi $=3.7\times10^{19}$ Bq: 7.2, 7.8, 8.2, 8.9 $\times10^{19}$ Bq/a.

Central $=7.81\times10^{19}$ Bq/a (ZK11), low $=6.69\times10^{19}$, high $=8.92\times10^{19}$ (the extremes of the above). Karstens et al. 2015 (European map, 10-15 mBq m$^{-2}$ s$^{-1}$) and Griffiths et al. 2010 (Australia) were consulted but give no global mean. **Caveats:** (i) head activity is Rn-222 only; the Rn222+ group's 5 decays per Rn would multiply this by 5 on ingestion; (ii) the Zhang inventories span only the simulated land (60° N-60° S for JA97) and may include some high-latitude land flux scaled differently; (iii) the S0606 paper's own regional unit labels look inconsistent, but the totals check against fluxes (1 atom cm$^{-2}$ s$^{-1}\approx0.021$ Bq m$^{-2}$ s$^{-1}$, $\times1.3\times10^{14}$ m$^{2}$ gives $2\times10^{12}$ Bq/s); (iv) 5th/95th interpretation is J.

## B08-B11 Cosmogenic H-3 and C-14

Taken directly from UNSCEAR 2000 Annex B Table 4 (S0604): H-3 72 PBq/a, 1275 PBq; C-14 1.54 PBq/a, 12 750 PBq. Consistency check, steady state $A_\mathrm{inv}=P/\lambda$ with $\lambda$ from nuclides.csv:

$$\frac{72}{0.05626}=1280\ \mathrm{PBq}\ (\text{table: }1275),\qquad\frac{1.54}{1.216\times10^{-4}}=1.27\times10^{4}\ \mathrm{PBq}\ (\text{table: }12\,750)$$

(The table's units are "PBq a$^{-1}$", i.e. activity of the atoms made per year.) **Caveats:** (i) UNSCEAR gives no uncertainty; the $\pm30\ \%$ bounds are J; (ii) 25 000 atoms m$^{-2}$ s$^{-1}$ (2.5 atoms cm$^{-2}$ s$^{-1}$) for C-14 is at the high end of the published range (more recent modelling gives roughly 1.6-2.0), so the true value may lie below the stated low bound. Not re-checked this session; the verifier should compare with Masarik and Beer (2009) or Kovaltsov et al. (2012); (iii) the C-14 inventory is the natural, pre-1950 one (excludes bomb and fossil perturbations); (iv) the H-3 inventory in the table is the atmosphere-ocean steady-state total.

## B12-B14 Top metre of global soil

$$A_i=C_i\ A_\mathrm{land}\,d\,\rho_\mathrm{soil}$$

with $d=1$ m, $\rho_\mathrm{soil}=1500$ kg m$^{-3}$ (J; range 1300-1700, UNSCEAR assumes 1.3 g cm$^{-3}$ dry and 1.6 wet), and the UNSCEAR 2000 Table 6 median concentrations (the population-weighted values are 420, 33 and 45):

| Nuclide | $C_i$ (Bq/kg) | Result (Bq), central (low-high) |
|---|---|---|
| K-40 | 400 | $7.95\times10^{19}$ ($5.4$-$10.6\times10^{19}$) |
| U-238 (head; the series figure of 35 Bq/kg is taken as the U-238 level) | 35 | $6.96\times10^{18}$ ($4.7$-$9.3\times10^{18}$) |
| Th-232 (series figure taken as the Th-232 level) | 30 | $5.97\times10^{18}$ ($4.1$-$8.0\times10^{18}$) |

Soil mass $=1.326\times10^{14}\times1\times1500=1.99\times10^{17}$ kg. **Kept as a candidate baseline** because UNSCEAR gives a sourced median. **Caveats:** the survey means are for inhabited, mostly agricultural soils and skew to populated regions; using them over all ice-free land, including bare rock, desert and lakes, is an upper-side bias that the $\pm30\ \%$ concentration and density bounds (J) do not fully cover. The row notes say so. The U-series and Th-series values in UNSCEAR are the parent (equilibrium) levels, so U-238 head activity is the same number.

## B15-B19 Atmospheric weapons-test fallout

UNSCEAR 2000 Annex C Table 9 "global release" (S0605), printed p. 213, PBq at the time of production, for the globally dispersed fraction (fission 160.5 Mt, fusion 250.6 Mt). Normalised production times the dispersed yield; e.g. Cs-137:

$$5.90\ \mathrm{PBq\,Mt^{-1}}\times160.5\ \mathrm{Mt}=947\ \mathrm{PBq}\ (\text{table: }948)$$

| Group | PBq | Bq | Bounds (J) |
|---|---|---|---|
| H-3 | 186 000 | $1.86\times10^{20}$ | ×0.5 to ×1.5 |
| C-14 | 213 | $2.13\times10^{17}$ | ×0.5 to ×1.5 |
| Sr-90 (Sr90+) | 622 | $6.22\times10^{17}$ | ±20 % |
| Cs-137 (Cs137+) | 948 | $9.48\times10^{17}$ | ±20 % |
| I-131 | 675 000 | $6.75\times10^{20}$ | ×0.7 to ×1.3 |

**Caveats:** (i) these are cumulative activities *produced and dispersed* (1945-1980), undecayed. The inventory remaining today is lower: Sr-90 deposit peaked at 460 PBq (NH, S0605 Table 8) and was projected at 250 PBq for 2000. I-131 (8 d) has long gone. (ii) Local and regional deposition is excluded. (iii) Table 9's H-3 and C-14 rows rest on Miskel's estimate and on fusion yield, so they are the weakest; the bounds are J. (iv) Military, baseline only (D9); the head activity convention means Cs137+ multiplier 1.944 is applied downstream, not here. (v) Rows are stocks with year left blank because they are time-invariant cumulative totals.

## B20 Natural uranium in the oceans

$$m_\mathrm{U}=V\rho\,[\mathrm{U}]\,M_\mathrm{U}=1.332\times10^{18}\times1028\times13.9\times10^{-9}\times0.23803\ \mathrm{kg\,mol^{-1}}\approx4.5\times10^{9}\ \mathrm{kg}$$

$$A_\mathrm{U238}=m_\mathrm{U}\,a_\mathrm{U238}=4.53\times10^{9}\times1.235\times10^{7}=5.6\times10^{16}\ \mathrm{Bq}$$

[U] $=13.9$ nmol/kg (S0612, secondary citation; ±6.5 % J). U-234 is about 1.14 times the U-238 activity in seawater and is not counted in the head activity. Thorium in seawater is orders of magnitude lower and no sourced ocean mean was found, so no Th row.

## B21 Uranium in the crust to 1 km

$$A=A_\mathrm{land}\,d\,\rho_\mathrm{c}\,[\mathrm{U}]\,a_\mathrm{U238}=1.326\times10^{14}\times10^{3}\times2700\times2.7\times10^{-6}\times1.235\times10^{7}=1.2\times10^{22}\ \mathrm{Bq}$$

Mass of U $=9.7\times10^{14}$ kg. [U] $=2.7\pm0.6$ ppm upper continental crust (S0611), treated as 1.645 σ for the 5-95 band; density 2500-2900 kg m$^{-3}$ (J). **Caveat:** upper-crust abundance applied to a full kilometre of ice-free land; it ignores shelves and thinner or more mafic rock, so it is an indicative scale marker (comparable with the ocean K-40 inventory, B05), not a resource figure.

## Considered, not included

- **Annual volcanic radon:** searches found no sourced global volcanic Rn-222 flux (nothing among the hits gave a number). Not added. Gap; see report.
- **Ocean thorium:** no sourced mean.
- **Karstens et al. 2015 / Griffiths et al. 2010:** regional radon maps only; not used for the global number.

## Inaccessible or unread sources

- Millero et al. 2008 (S0609): https://www.sciencedirect.com/science/article/pii/S0967063707002111 (robots-blocked; value read from S0610).
- Huang et al. 2013 publisher PDF: https://www.geol.umd.edu/~mcdonoug/KITP%20Website%20for%20Bill/papers/Earth%20GeonuFlux/Huang_etal_(G3_13).pdf (robots-blocked; Table 3 with U/Th/K split not read).
- KamLAND 2022 GRL final paper (S0601) and Borexino full text were read only through arXiv abstract pages.
