import os,sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from lib import *
from common import *
import json,math,collections
O=Out('nuclear')
R=json.load(open(RAW+'rds2_rows.json'))
ISO={'AE':'ARE','AM':'ARM','AR':'ARG','BE':'BEL','BG':'BGR','BR':'BRA','BY':'BLR','CA':'CAN','CH':'CHE','CN':'CHN','CZ':'CZE','DE':'DEU','ES':'ESP','FI':'FIN','FR':'FRA','GB':'GBR','HU':'HUN','IN':'IND','IR':'IRN','IT':'ITA','JP':'JPN','KR':'KOR','KZ':'KAZ','LT':'LTU','MX':'MEX','NL':'NLD','PK':'PAK','RO':'ROU','RU':'RUS','SE':'SWE','SI':'SVN','SK':'SVK','TW':'TWN','UA':'UKR','US':'USA','ZA':'ZAF'}
TY={'PWR':'pwr','BWR':'bwr','PHWR':'phwr','GCR':'gcr','LWGR':'lwgr','FBR':'fbr','HTGR':'htgr'}
for a in R:
    a['t']=TY.get(a['type'],'other'); d=a['dates']; a['grid']=d[1][0]; a['sd']=d[-1][0] if a['tab']=='16' else None
types=['pwr','bwr','phwr','gcr','lwgr','fbr','htgr','other']
def cap(y,t=None,cc=None):
    return sum(a['net'] for a in R if a['grid']<=y and (a['sd'] is None or a['sd']>y) and (t is None or a['t']==t) and (cc is None or a['cc']==cc))/1000
def add(y,t=None):
    return sum(a['net'] for a in R if a['grid']==y and (t is None or a['t']==t))/1000
src='S0116'
nc='Reconstructed from IAEA RDS-2 No. 45 (2025) Tables 14-16 (every reactor: type, net MW(e), first grid connection, permanent shutdown date): capacity at year-end of units connected to the grid and not permanently shut down. Includes units in suspended operation (e.g. Japan 2011-2020), which IAEA Table 5 excludes from "operational", so it exceeds Table 5 by 2-7% (1995-2024; Table 5 values in notes.md). Units connected and shut down within one year are not counted. Bands assumed asymmetric: -7%/+2% from 1995 (low reaches IAEA Table 5 operational), -6%/+3% before.'
for y in range(1954,2025):
    rl,rh=(0.07,0.02) if y>=1995 else (0.06,0.03)
    rel=rl
    for t in types:
        v=cap(y,t)
        if v>0 or any(a['t']==t and a['grid']<=y for a in R):
            O.add('nuc_cap_'+t,y,'XWL',*bands(v,rl,rh),'GW','compiled',src,nc)
    O.add('nuc_cap_total',y,'XWL',*bands(cap(y),rl,rh),'GW','compiled',src,nc)
    for cc,iso in ISO.items():
        v=cap(y,None,cc)
        if v>0 : O.add('nuc_cap_total',y,iso,*bands(v,rl*1.3,rh*1.5),'GW','compiled',src,nc+' Country by plant location per RDS-2 (USSR-era reactors under their present-day country; East German reactors under DEU).')
# capacity vs Table 5 check values for notes
for y,t5 in [(1995,341.387),(2000,349.984),(2005,368.035),(2010,370.930),(2015,360.504),(2020,369.804),(2024,377.014)]:
    print('check',y,round(cap(y),1),t5)
# generation allocated by type: world generation (OWID) x capacity*UCF weights
UCF={'pwr':83.1,'bwr':92.9,'phwr':74.6,'gcr':72.0,'lwgr':80.5,'fbr':70.9,'htgr':75.0,'other':75.0}
gen=owid('eps.csv','Nuclear')
GENT={}
for y in range(1954,2025):
    w={t:(cap(y,t)+cap(y-1,t))/2*UCF[t] for t in types}
    tot=sum(w.values())
    if tot<=0: continue
    for t in types:
        v=gen.get(y,0)*w[t]/tot; GENT[(t,y)]=v
        if v>0:
            O.add('nuc_gen_'+t,y,'XWL',v*0.8,v,v*1.2,'TWh','modelled','S0116;S0800;S0803','Modelled allocation of world nuclear generation (OWID/Ember/EI; Pinto et al. 2023 before 1965) among reactor types in proportion to mean-of-year capacity (nuc_cap_<type>) x type capacity factor (IAEA RDS-2 Table 18 unit capacity factors 2022-2024: PWR 83.1, BWR 92.9, PHWR 74.6, LWGR 80.5, GCR 72.0, FBR 70.9; HTGR/other assumed 75). Time-invariant relative weights are an approximation (early reactors ran at lower capacity factors). Bands +-20% (assumed). Total generation measured; split modelled.')
# spent fuel discharge (modelled)
# GCR split: UK AGR (first grid 1976 or later) vs Magnox/UNGG-type gas-graphite fleet
def isagr(a): return a['t']=='gcr' and a['cc']=='GB' and a['grid']>=1976
def capg(y,agr):
    return sum(a['net'] for a in R if a['t']=='gcr' and a['grid']<=y and (a['sd'] is None or a['sd']>y) and isagr(a)==agr)
def burnup(t,y):
    if t in('pwr','bwr'):
        pts=[(1950,10),(1960,15),(1983,33),(1998,45),(2020,48),(2025,49)]
    elif t=='phwr': pts=[(1950,7),(2025,7.5)]
    elif t=='magnox': pts=[(1950,4),(1970,5),(1990,5.5),(2025,6)]
    elif t=='agr': pts=[(1950,27),(2025,27)]
    elif t=='lwgr': pts=[(1950,12),(1990,18),(2025,22)]
    else: return None
    for (a,x),(b,z) in zip(pts,pts[1:]):
        if a<=y<=b: return x+(z-x)*(y-a)/(b-a)
    return pts[-1][1]
ETA={'pwr':0.33,'bwr':0.33,'phwr':0.30,'magnox':0.27,'agr':0.38,'lwgr':0.31}
cum=0; tot={}; comp={}
for y in range(1954,2025):
    s_=0; cm={}
    for t in ETA:
        if t in('magnox','agr'):
            g=GENT.get(('gcr',y),0)
            ca=(capg(y,True)+capg(y-1,True))/2; cmg=(capg(y,False)+capg(y-1,False))/2
            if ca+cmg<=0: continue
            g=g*(ca if t=='agr' else cmg)/(ca+cmg)
        else: g=GENT.get((t,y),0)
        if g<=0: continue
        B=burnup(t,y); thm=g*1000/24/ETA[t]/B
        s_+=thm; cm[t]=thm
    tot[y]=s_; comp[y]=cm; cum+=s_
    if s_>0:
        O.add('nuc_spent_fuel_discharged_thm',y,'XWL',s_*0.7,s_,s_*1.3,'t','modelled','S0116;S0800;S0818;S0851;S0852;S0853',
              'Modelled heavy-metal discharge = generation(type) / (24 h/d x thermal efficiency x discharge burnup), summed over PWR, BWR, PHWR, LWGR and two gas-cooled sub-fleets (FBR/HTGR/other omitted). Gas-cooled reactors split by RDS-2 first-grid year: UK units connected 1976 or later are AGR (efficiency 0.38 = 600 MWe/1560 MWth, burnup 27 GWd/tHM, within 24-32 given for Hartlepool, S0851); all other gas-graphite units are Magnox/UNGG type (efficiency 0.27, burnup 4 rising to 6, assumed). Thermal efficiencies assumed: PWR/BWR 0.33, PHWR 0.30, LWGR 0.31. LWR discharge burnup (GWd/tHM) piecewise-linear: 15 (1960), 33 (1983; Germany PWR 35 per TECDOC-1975), 45 (1998), 48 (2020; TECDOC-1975: USA and most others above 45, Germany 50-65); PHWR 7-7.5; LWGR 12-22. Cross-checks: IAEA TECDOC-1975 (2021) says over 400,000 tHM discharged by end 2020 and accumulating at about 7000 tHM/a (IAEA/NEA Status and Trends, to end-2019, also 7000); an IAEA article gives about 10,000 t/a (undated). The model is within that range but about 30-40% above 7000 (see notes.md). Bands +-30% (assumed).')
print('cum to 2020',sum(v for y,v in tot.items() if y<=2020))
for y in(1990,2000,2010,2015,2016,2020,2024): print(y,round(tot[y]),{k:round(v) for k,v in comp[y].items()})
O.write()
