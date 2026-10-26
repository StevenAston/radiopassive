import os,sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from lib import *
from common import *
import csv,collections
CTRY=['CHN','USA','IND','RUS','JPN','DEU','CAN','FRA','BRA','KOR','GBR','ZAF','AUS','MEX','IDN','IRN','SAU','TUR','ITA','ESP','UKR','POL','TWN','EGY','VNM','THA','ARG','NOR','SWE','PAK']
O=Out('electricity_generation')
cols={'Coal':'coal','Gas':'gas','Oil':'oil','Nuclear':'nuclear','Hydropower':'hydro','Wind':'wind','Solar':'solar','Bioenergy':'biomass','Other renewables':'other_ren'}
rows=list(csv.DictReader(open(RAW+'eps.csv')))
data=collections.defaultdict(lambda: collections.defaultdict(dict))  # ent->series->year
for r in rows:
    code=r['Code']
    if r['Entity']=='World': ent='XWL'
    elif code in CTRY: ent=code
    else: continue
    for k,s in cols.items():
        if r[k]!='': data[ent][s][int(r['Year'])]=float(r[k])
def rel(year,s,ent):
    if year>=2000: b=0.02
    elif year>=1985: b=0.03
    elif year>=1965: b=0.05
    elif year>=1950: b=0.10
    else: b=0.20
    if s in('oil','gas') and year<1950: b=0.30
    if s=='biomass': b=max(b,0.10 if year>=2000 else 0.20)
    if s in('wind','solar') and year>=2000: b=0.03
    if ent!='XWL': b*=1.5
    return b
def meta(year,ent):
    if year>=2000: return 'measured','S0802;S0803;S0800'
    if year>=1965: return 'compiled','S0803;S0800'
    return 'modelled','S0801;S0800'
note_pre='World 1900-1964: historical reconstruction by Pinto et al. (2023) as redistributed by OWID; bands are analyst-assumed (approx. 5th-95th percentile), not published.'
for ent,d in data.items():
    for s,ys in d.items():
        if s=='other_ren': continue
        for y,v in ys.items():
            if ent=='XWL' and y<1900: continue
            b,src=meta(y,ent)
            if y<1965 and ent!='XWL':
                if ent=='GBR': b,src='compiled','S0800'   # DESNZ UK series via OWID
                else: continue
            r_=rel(y,s,ent)
            nt=('Ember Yearly Electricity Data and Energy Institute Statistical Review via OWID, annual generation (TWh).' if y>=2000 else 'Energy Institute Statistical Review of World Energy via OWID, annual generation (TWh).')
            if ent=='XWL' and y<1965: nt=note_pre
            elif ent=='GBR' and y<1965: nt='UK 1920-1964 from DESNZ Energy Trends June 2023 estimates, via OWID.'
            if s=='oil' and y>=1985: nt+=' Oil may include other fossil fuels in the Ember/EI categorisation.'
            if s=='biomass': nt+=' Biomass and waste; peat is treated separately where IRENA gives it (elec_gen_peat).'
            O.add('elec_gen_'+s,y,ent,v*(1-r_),v,v*(1+r_),'TWh',b,src,nt.strip())

# ---- geothermal: pre-1980 world from OWID other renewables (x0.95), 1980-1999 EIA, 2000+ IRENA
cc=countries()
oth=data['XWL']['other_ren']
eg=eia_geo('35','12','BKWH')
ig=irena('0','15')
ratio=[eg['WORL'][y]/oth[y] for y in range(1980,1991)]
k=sum(ratio)/len(ratio)
print('geo/other_ren mean ratio 1980-90',k)
world_ir={y:sum(ig[c].get(y,0) for c in ig)/1000 for y in range(2000,2026)}
for y in range(1900,2026):
    if y<1980:
        v=oth.get(y,0)*k
        if v==0 and oth.get(y,0)==0 and y<1950: continue
        if v==0: continue
        O.add('elec_gen_geothermal',y,'XWL',oth[y]*0.85,v,oth[y]*1.0,'TWh','modelled','S0800;S0801;S0804',
              'Modelled: OWID "other renewables" (Pinto et al. 2023 / EI; geothermal plus negligible tidal) scaled by the 1980-1990 mean ratio of EIA geothermal to other renewables (%.3f). Low = 0.85x, high = 1.0x of other renewables (assumed).'%k)
    elif y<2000:
        v=eg['WORL'][y]; O.add('elec_gen_geothermal',y,'XWL',v*0.95,v,v*1.05,'TWh','compiled','S0804','EIA International Energy Statistics, geothermal net generation, world; bands assumed +-5%.')
    else:
        v=world_ir[y]; O.add('elec_gen_geothermal',y,'XWL',v*0.97,v,v*1.03,'TWh','measured','S0810','IRENA electricity statistics 2026 H2, sum of countries; bands assumed +-3%.')
for c in sorted(set(eg)|set(ig)):
    if c not in cc or c=='XWL': continue
    for y in range(1980,2026):
        if y<2000: v=eg.get(c,{}).get(y); src='S0804'; b='compiled'
        else: v=ig.get(c,{}).get(y); v=None if v is None else v/1000; src='S0810'; b='measured'
        if v is None or v<=0: continue
        O.add('elec_gen_geothermal',y,c,v*0.9,v,v*1.1,'TWh',b,src,'EIA (1980-1999) / IRENA (2000-2025) country series; bands assumed +-10%.')
# ---- peat (IRENA 2000+)
ip=irena('0','23'); ipc=irena('1','23')
yrs=range(2000,2026)
for y in yrs:
    v=sum(ip[c].get(y,0) for c in ip)/1000
    if v>0: O.add('elec_gen_peat',y,'XWL',v*0.9,v,v*1.1,'TWh','measured','S0810','IRENA electricity statistics 2026 H2 "Peat and peat products" generation, sum of countries; bands assumed +-10%. Peat is not in OWID bioenergy.')
for c in sorted(ip):
    if c not in cc: continue
    for y in yrs:
        v=ip[c].get(y)
        if v is None or v<=0: continue
        O.add('elec_gen_peat',y,c,v/1000*0.9,v/1000,v/1000*1.1,'TWh','measured','S0810','IRENA electricity statistics 2026 H2 peat generation; bands assumed +-10%.')
O.write()
