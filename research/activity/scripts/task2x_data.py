"""Hand-transcribed inputs for build_nuc2.py (Task 2.x). Every block names its source and how it was read.
Nothing here is computed from other files; checks against the printed totals are in build_nuc2.py (asserts).
"""
# ---------------------------------------------------------------------------------------------
# IAEA-TECDOC-1105 (2001), Annexes A.1-A.14: total activity (GBq) per disposal year, transcribed from the
# 'Subtotal' / 'Total' column of each annex table (text layer of te_1105_prn.pdf). Alpha + beta-gamma, tritium included
# in beta-gamma, estimated at the time of packaging.
SEA_GBQ={
 'BEL':{1960:543.9,1962:1852.2,1963:2260.0,1967:7030.0,1969:17945.0,1971:91094.0,1972:71447.0,1973:66193.0,1975:121767.0,
        1976:77933.1,1978:169360.1,1979:41935.8,1980:858616.2,1981:345953.7,1982:246401.5},   # printed total 2,120,332.5
 'FRA':{1967:218970.0,1969:134421.0},                                                          # printed total 353,391
 'DEU':{1967:203.5},
 'ITA':{1969:185.0},
 'JPN':{1955:7.4,1957:29.6,1958:29.6+185.0,1959:222.0+185.0,1960:185.0+370.0,1962:1023.9,1963:2410.0,1964:2553.8,
        1965:1007.2,1967:2813.7,1968:1303.3,1969:2753.5},                                       # printed total 15,078.9
 'NLD':{1967:73.0,1969:1010.0,1971:750.0,1972:2030.0,1973:1850.0,1974:21020.0,1975:18190.0,1976:36370.0,1977:22190.0,
        1978:57060.0,1979:31310.0,1980:19960.0,1981:68840.0,1982:55400.0},                      # printed total 336,053
 'NZL':{1962:0.7,1972:117.0,1973:444.0,1976:477.3},                                             # printed total 1,039.0 (activity only where stated)
 'SWE_ATL':{1969:3242.7},                                                                       # Annex A.9
 'SWE_BAL':{1959:4.4,1961:10.4},                                                                # Annex A.10 (Baltic, 14.8 GBq)
 'CHE':{1969:12617.0,1971:13242.3,1972:22237.0,1974:79043.1,1975:43356.6,1976:27424.4,1977:35268.4,1978:166111.0,
        1979:63717.7,1980:1903960.0,1981:1405556.0,1982:646808.0},                              # printed total 4,419,341.5
 'GBR':{1949:37.0,1950:814.0,1951:703.0+222.0,1952:1147.0,1953:148.0+1813.0,1954:2886.0,1955:2923.0+1665.0,1956:2849.0,
        1957:9990.0+65231.0,1958:65860.0+4255.0,1959:2886.0,1960:10804.0,1961:12136.0+81141.0,1962:6660.0+2997.0,
        1963:1739.0+275243.0,1964:574758.0,1965:513116.0,1966:104340.0,1967:65601.0,1968:2796016.0,1969:665260.0,
        1970:756909.0,1971:330785.0,1972:729751.0,1973:458763.0,1974:3497425.0,1975:1967808.0,1976:1870943.0,
        1977:2803116.0,1978:2594478.0,1979:3051054.0,1980:3991190.0,1981:3949415.0,1982:3802710.0},   # printed total 35,077,587
}
SEA_PRINTED_GBQ={'BEL':2120332.5,'FRA':353391.0,'DEU':203.5,'ITA':185.0,'JPN':15078.9,'NLD':336053.0,'NZL':1039.0,
                 'SWE_ATL':3242.7,'SWE_BAL':14.8,'CHE':4419341.5,'GBR':35077587.0}
# United States (Annex A.13 Atlantic, A.14 Pacific): site totals (GBq) over a stated period [start,end]; annual split not given.
# Start blank in the source (Pacific, one-off sites) is read as a single dump in the end year.
US_ATL=[(1949,1967,3145.00),(1951,1960,2752800.00),(1951,1960,77700.00),(1952,1959,90280.00),(1955,1957,0.07),(1955,1960,0.19),
        (1955,1961,11.10),(1955,1962,24.42),(1958,1958,370.00),(1959,1960,17760.00),(1962,1962,74.00)]   # printed subtotal 2,942,164.78
US_PAC=[(1946,1962,3996.00),(1962,1962,19.98),(1962,1962,19.98),(1962,1962,3603.80),(1962,1962,44.40),(1962,1962,3570.50),
        (1946,1970,536500.00),(1955,1958,35.15),(1955,1958,35.15),(1955,1960,40.70),(1958,1966,3552.00),(1959,1960,3.33),
        (1959,1962,1258.00),(1960,1960,518.00),(1960,1960,2.96),(1960,1960,2.96),(1960,1960,8.14),(1962,1969,1036.00)]  # printed subtotal 554,247.05
US_ATL_PRINTED=2942164.78; US_PAC_PRINTED=554247.05
SEAWOLF_GBQ=1221000.0; SEAWOLF_YEAR=1959   # reactor shell of USS Seawolf inside the 1951-60 38N30 72W site (annex footnote: 1221 TBq)
# Reported in the notes, not in the series (former Soviet Union / Russian Federation, TBq, TECDOC-1105 Table IV and Table V):
FSU_TBQ={'arctic_reactors_with_spent_fuel':36876.0,'arctic_reactors_without_fuel':143.0,'arctic_solid_llw':585.4,
         'arctic_liquid_llw':764.0,'arctic_total_FSU':38369.1,'arctic_RUS':0.7,'pacific_FSU':873.6,'pacific_RUS':2.05}
# ---------------------------------------------------------------------------------------------
# UNSCEAR 2000 Annex C, Table 40: fuel reprocessed (GW a, electrical energy equivalent), read from the first column
# after the year (rows with no value in that column carry no GW a). The column alignment was checked against
# Table 41 period totals (1980-97 La Hague 36.3/62.5/131/160 GW a incl. Tokai+Sellafield; see build_nuc2.py).
LH_UNSCEAR={1971:0.9,1972:3.1,1973:2.6,1974:7.1,1975:3.3,1976:1.8,1977:1.4,1978:1.6,1979:2.9,1980:2.8,1981:3.3,1982:3.7,
 1983:5.2,1984:4.8,1985:9.3,1986:7.2,1987:9.1,1988:7.1,1989:10.8,1990:12.3,1991:18.5,1992:16.4,1993:21.5,1994:34.3,
 1995:43.4,1996:43.0,1997:49.8}   # 1997 'estimated from normalized 85Kr release of 6,020 TBq per GW a' (table footnote)
TOKAI_UNSCEAR={1977:0.04,1978:0.11,1979:0.18,1980:0.61,1981:0.60,1982:0.54,1983:0.01,1984:0.12,1985:1.2,1986:1.2,1987:0.93,
 1988:0.17,1989:1.1,1990:1.5,1991:1.5,1992:1.5,1993:0.8,1994:1.5,1995:1.0,1996:1.5,1997:0.0}
SELLAFIELD_UNSCEAR={1972:2.6,1975:3.2,1976:3.2,1977:2.1,1978:1.8,1979:2.5,1980:2.2,1981:3.7,1982:3.1,1983:3.0,1984:2.7,
 1985:1.7,1986:3.8,1987:2.4,1988:2.8,1989:3.7,1990:3.8,1991:4.5,1992:2.7,1993:5.7,1994:3.8,1995:6.9,1996:7.1,1997:6.8}
# Table 43 world totals by period (GW a) for the cross-check
UNSCEAR_WORLD_PERIOD={(1980,1984):36.3,(1985,1989):62.5,(1990,1994):130.0,(1995,1997):160.0}
# ---------------------------------------------------------------------------------------------
# La Hague LWR fuel reprocessed, tHM per year, 1976-2006: IPFM Research Report 4 (2008) Figure 6 ('Combined annual LWR
# fuel reprocessing at La Hague, UP2 and UP3'), read by pixel measurement of the bar heights (220 dpi raster of the
# page, 0.40175 px per tHM from the gridlines). The 31 bars sum to 22,584 tHM; the figure shows about 22,500 (text).
LH_CHART_THM={1976:12,1977:15,1978:37,1979:80,1980:105,1981:102,1982:152,1983:222,1984:254,1985:348,1986:331,1987:423,
 1988:343,1989:458,1990:525,1991:660,1992:665,1993:951,1994:1274,1995:1558,1996:1680,1997:1670,1998:1628,1999:1561,
 2000:1195,2001:948,2002:1058,2003:1113,2004:1100,2005:1110,2006:1006}
# Orano 'Traitement des combustibles usés provenant de l'étranger' reports (Art. 8 of the 2006 Act): cumulative tHM
# treated at La Hague since start-up (UP3-A 1990, UP2-800 1994; the figure continues the LWR series of the chart above).
ORANO_CUM={2022:39483.0,2024:41236.0}; ORANO_YEAR={2022:925.0,2024:871.0}
# THORP (Sellafield) throughput, tHM per financial year ending 31 March of the label: IPFM Research Report 5 (2006)
# Figure 6, bars read by eye (about +-25 t); 'Actual' bars only. First ten years 1994-2004 total 5,045 tHM (IPFM blog 2018);
# lifetime total 9,331 tHM (Sellafield Ltd / NDA statement, gov.uk 14 Nov 2018).
THORP_FY={1997:410,1998:760,1999:455,2000:895,2001:365,2002:740,2003:510,2004:670,2005:600,2006:55,2007:0,2008:35}
THORP_FIRST10=5045.0; THORP_TOTAL=9331.0; THORP_END_FY=2019   # last fuel sheared 9 Nov 2018 (FY ending March 2019)
# ---------------------------------------------------------------------------------------------
# Sites excluded under D16 (undocumented civil share) with the quantities found, for the notes only.
EXCLUDED_NOTE=("Excluded under D16 (civil share undocumented): Sellafield B205 Magnox plant (1964-2022, about 54,920 tHM; military "
 "campaigns for Calder Hall/Chapelcross fuel ended after 1995), Marcoule UP1 (1958-1997), Mayak RT-1 (about 100-130 tHM/a of mixed fuel; 993 tHM in 2016-2024), "
 "West Valley (640 t, 1966-72, mixed defence and commercial fuel), India (Trombay, Tarapur, Kalpakkam) and the Chinese pilot plant (sources S1609, S1610, S1611, S0132).")
