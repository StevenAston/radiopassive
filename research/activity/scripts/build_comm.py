import os,sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from lib import *
from common import *
import csv,glob,collections
O=Out('commodity_production')
from ds140_comm import add_ds140
ST=add_ds140(O)
from ree_myb import add_ree
REELOG=[]
NREE,REEEd=add_ree(O,REELOG)
import json as _j; _j.dump({'log':REELOG,'tot':{e[0]:e[3] for e in REEEd}},open(OUTDIR+'ree_log.json','w'))
cc=countries()
MAP={'OWID_USS':'SUN','OWID_YGS':'YUG','OWID_CZS':'CSK','OWID_GDR':'DDR','OWID_GFR':'DEU','OWID_SRM':'SCG','OWID_WRL':'XWL'}
SPEC={ # file: (series, unit note, mult, commodity note)
'Rare_earths__Mine':('prod_ree_oxide',2.0,'Rare-earth oxide equivalent, mine production (USGS: REO content of mined concentrates).'),
'Copper__Mine':('prod_copper',1.0,'Contained copper in mine output.'),
'Copper__Refinery':('prod_copper_refined',1.0,'Refined copper (primary + secondary as USGS reports). World total only 2020-2024 in the OWID series.'),
'Aluminum__Smelter':('prod_aluminium',1.0,'Primary aluminium (smelter) production.'),
'Bauxite__Mine':('prod_bauxite',1.0,'Bauxite, dry-equivalent gross weight.'),
'Steel__Processing_crude':('prod_steel',1.0,'Crude steel.'),
'Iron_ore__Mine_crude_ore':('prod_iron_ore',1.0,'Iron ore, crude (usable) ore gross weight.'),
'Iron__Smelter_pig_iron':('prod_pig_iron',1.0,'Pig iron.'),
'Cement__Processing':('prod_cement',1.5,'Hydraulic cement; country coverage thin before 1990 (world series from 1926).'),
'Silver__Mine':('prod_silver',1.0,'Contained silver in mine output.'),
'Selenium__Refinery':('prod_selenium',2.0,'Refined selenium; many producers undisclosed.'),
'Gallium__Refinery':('prod_gallium_refined',2.0,'Refined (high-purity) gallium; world coverage 1973-2021, partial (USGS withholds some producers).'),
'Gallium__Processing':('prod_gallium_primary',2.0,'Primary low-purity gallium production (MCS), 2020-2024.'),
'Zinc__Mine':('prod_zinc',1.0,'Contained zinc in mine output.'),
'Zinc__Refinery':('prod_zinc_refined',1.0,'Refined zinc; no world total in the OWID series.'),
'Lead__Mine':('prod_lead',1.0,'Contained lead in mine output.'),
'Lead__Refinery':('prod_lead_refined',1.0,'Refined lead (primary + secondary); no world total in OWID.'),
'Tin__Mine':('prod_tin',1.0,'Contained tin in mine output.'),
'Tin__Smelter':('prod_tin_smelter',1.0,'Smelter tin; no world total in OWID.'),
'Nickel__Mine':('prod_nickel',1.0,'Contained nickel in mine output (11 producers; check world coverage).'),
'Nickel__Processing':('prod_nickel_processing',1.0,'Nickel processing/refinery output (BGS/USGS); world 1977-2023.'),
'Zirconium_and_hafnium__Mine':('prod_zirconium',2.0,'Zirconium and hafnium mineral concentrates; world total only 2020-2024.'),
'Silicon__Processing':('prod_silicon_mg',2.0,'USGS "silicon" = silicon metal plus ferrosilicon on a gross-weight/contained-silicon basis as reported (1964-2022); metallurgical grade, not polysilicon alone.'),
'Cadmium__Refinery':('prod_cadmium',1.5,'Refined cadmium.'),
'Chromium__Mine':('prod_chromium',1.0,'Contained chromium; world only (1900-2022).'),
'Molybdenum__Mine':('prod_molybdenum',1.0,'Contained molybdenum in mine output.'),
}
for fn,(ser,mult,desc) in SPEC.items():
    for r in csv.DictReader(open(RAW+'min/%s.csv'%fn)):
        col=[k for k in r.keys() if k not in('Entity','Code','Year')][0]
        if r[col]=='': continue
        c=MAP.get(r['Code'],r['Code'])
        if r['Entity']=='World': c='XWL'
        if c not in cc: continue
        y=int(r['Year']); v=float(r[col])
        if y>2025 or y<1800: continue
        b=0.15 if y<1950 else 0.08 if y<1990 else 0.05
        b*=mult*(1 if c=='XWL' else 1.5)
        b=min(b,0.6)
        if (ser,y,c) in O.rows: continue
        O.add(ser,y,c,*bands(v,b),'t','compiled','S0807;S0410','OWID Minerals explorer (USGS Historical Statistics DS140 to 2022/23, USGS Mineral Commodity Summaries 2025 to 2024, BGS World Mineral Statistics for non-US country gaps). '+desc+' Bands assumed (approx. 5th-95th percentile): +-15% before 1950, +-8% 1950-1989, +-5% from 1990, scaled by commodity data quality and x1.5 for countries.')
# MCS 2026 estimates for 2025 (world), units converted to t
M26=[('prod_copper',23000*1000,'Copper mine, 2025e, thousand t'),('prod_aluminium',74000*1000,'Primary aluminium 2025e'),('prod_silver',26000,'Silver mine 2025e (t)'),('prod_zinc',13000*1000,'Zinc mine 2025e'),('prod_lead',4500*1000,'Lead mine 2025e'),('prod_tin',290*1000,'Tin mine 2025e'),('prod_nickel',3900*1000,'Nickel mine 2025e'),('prod_cadmium',23000,'Cadmium refinery 2025e (t)'),('prod_molybdenum',260*1000,'Molybdenum mine 2025e'),('prod_ree_oxide',390*1000,'Rare earths mine 2025e (REO)'),('prod_cement',3800000*1000,'Cement 2025e')]
for ser,v,desc in M26:
    if (ser,2025,'XWL') in O.rows: continue
    O.add(ser,2025,'XWL',*bands(v,0.08 if ser not in('prod_ree_oxide','prod_cement') else 0.15),'t','compiled','S0808','USGS Mineral Commodity Summaries 2026, world total (rounded) 2025e: '+desc+'. USGS estimate; bands assumed.')
# tellurium and indium (MCS refinery production, world totals; latest edition per year)
te={2018:(460,'2020'),2019:(470,'2020'),2020:(562,'2022'),2021:(580,'2022'),2022:(584,'2024'),2023:(944,'2025'),2024:(981,'2026'),2025:(1000,'2026')}
inn={2018:(741,'2020'),2019:(760,'2020'),2020:(960,'2022'),2021:(920,'2022'),2022:(999,'2024'),2023:(1020,'2025'),2024:(1090,'2026'),2025:(1100,'2026')}
for y,(v,ed) in te.items():
    if O.has('prod_tellurium',y,'XWL'): continue
    hi=0.5 if y<=2022 else 0.15
    O.add('prod_tellurium',y,'XWL',v*0.85,v,v*(1+hi),'t','compiled','S0808','USGS Mineral Commodity Summaries %s edition: world refinery production of tellurium (rounded; the US value is withheld and unreported producers are excluded). The 2025 edition revised 2023 China output from 430 t to 725 t (world 640 -> 944 t), so earlier editions probably understate: high bound +50%% for 2018-2022. 2023 value is the sum of country entries in the 2025 edition.'%ed)
for y,(v,ed) in inn.items():
    if O.has('prod_indium',y,'XWL'): continue
    O.add('prod_indium',y,'XWL',v*0.88,v,v*1.12,'t','compiled','S0808','USGS Mineral Commodity Summaries %s edition: world refinery production of indium (rounded; estimated from trade, capacity and zinc/lead smelter output for most countries). Bands assumed +-12%%.'%ed)

# ---- seams and gap fills (fix 5)
def interp(ser,c,years,rel,src,why):
    ys=sorted(k[1] for k in O.rows if k[0]==ser and k[2]==c)
    for y in years:
        if O.has(ser,y,c): continue
        a=max(x for x in ys if x<y); b=min(x for x in ys if x>y)
        va=float(O.rows[(ser,a,c)][4]); vb=float(O.rows[(ser,b,c)][4])
        v=va+(vb-va)*(y-a)/(b-a)
        O.add(ser,y,c,v*(1-rel),v,v*(1+rel),'t','interpolated',src,'Gap in the USGS DS140 world column (NA), filled by linear interpolation between %d (%g t) and %d (%g t); %s Band assumed +-%d%% (approx. 5th-95th percentile).'%(a,va,b,vb,why,rel*100))
interp('prod_lead','XWL',list(range(1901,1906))+list(range(1914,1919)),0.25,'S0832','World lead mine output for 1914-1918 was disrupted by the First World War and the true path may not be monotone.')
interp('prod_tellurium','XWL',range(2004,2013),0.40,'S0839','Tellurium refinery output was not published for most producers; a smooth path is assumed. MCS tellurium chapters for 2005-2013 would replace this (listed in notes.md).')
O.add('prod_molybdenum',2024,'XWL',256000*0.92,256000,256000*1.08,'t','compiled','S0808','USGS Mineral Commodity Summaries 2026, molybdenum, world mine production 2024 = 256,000 t (rounded; the 2026 edition revised Australia and Canada). Bands assumed +-8% (approx. 5th-95th percentile).')
def seam(k,txt):
    r=O.rows[k]; r[10]=txt+' '+r[10]
seam(('prod_tellurium',2023,'XWL'),'SEAM: +62% on 2022 (584 -> 944 t) is a USGS revision, not growth: the 2025 edition raised 2023 China output from 430 to 725 t; 2022 and earlier come from older editions and are probably understated.')
seam(('prod_ree_oxide',2021,'XWL'),'SEAM: +19% on 2020 (243,000 -> 290,000 t) joins DS140 (to 2020) to OWID/MCS (from 2021). Minerals Yearbook 2022 gives 250,000 (2020) -> 290,000 (2021), +16%, so about 3 points of the jump is source revision and the rest real growth (Myanmar, Thailand, USA, China); consistent with MCS.')
O.write()
