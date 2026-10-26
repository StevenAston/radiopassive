import os,sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from lib import *
from common import *
import csv,json,collections,statistics
cc=countries()
O=Out('capacity_additions'); P=Out('planning_parameters')
TECH={'wind_onshore':['5'],'wind_offshore':['21'],'solar_pv':['4'],'solar_csp':['9'],'coal':['7'],'gas':['6'],'oil':['2'],'hydro':['3'],'geothermal':['15'],'bioenergy':['10','8','12','20'],'peat':['23']}
CAP={};GEN={}
for t,codes in TECH.items():
    cap=collections.defaultdict(lambda: collections.defaultdict(float)); gen=collections.defaultdict(lambda: collections.defaultdict(float))
    for cd in codes:
        for c,d in irena('1',cd).items():
            for y,v in d.items(): cap[c][y]+=v/1000    # GW
        for c,d in irena('0',cd).items():
            for y,v in d.items(): gen[c][y]+=v/1000    # TWh
    CAP[t]=cap;GEN[t]=gen
def world(d): 
    w=collections.defaultdict(float)
    for c,x in d.items():
        for y,v in x.items(): w[y]+=v
    return dict(w)
WC={t:world(CAP[t]) for t in TECH}; WG={t:world(GEN[t]) for t in TECH}
srcI='S0810'
# --- realised CF
for t in TECH:
    for y in range(2000,2026):
        c=WC[t].get(y); g=WG[t].get(y)
        if c and g and c>0 and g>0:
            cf=g/(c*8.766)
            if cf>1.2: continue
            P.add('cf_realised_'+t,y,'XWL',cf*0.92,cf,min(cf*1.08,1.2),'1','measured',srcI,'World fleet-average realised capacity factor = IRENA generation / (year-end installed capacity x 8.766 TWh per GW-year); year-end capacity overstates average capacity in fast-growing fleets (wind, PV), so growth-years are biased low (bands +-8% assumed, wider for wind/PV in notes).')
# nuclear CF 1960-2024: OWID gen / RDS capacity (from nuclear.csv)
gen_n=owid('eps.csv','Nuclear')
nc=Out('x'); 
import csv as _c
capn={int(r['year']):float(r['value_central']) for r in _c.DictReader(open(OUT+'nuclear.csv')) if r['series']=='nuc_cap_total' and r['country']=='XWL'}
for y in range(1958,2025):
    avg=(capn.get(y,0)+capn.get(y-1,0))/2
    if avg>0 and gen_n.get(y):
        cf=gen_n[y]/(avg*8.766)
        P.add('cf_realised_nuclear',y,'XWL',cf*0.9,cf,min(cf*1.1,1.1),'1','compiled','S0116;S0800;S0803','World nuclear generation (OWID/Ember/EI) / (mean-of-year connected capacity from RDS-2 reconstruction x 8.766); capacity includes units in suspended operation, so CF is biased low when many units are suspended (Japan 2011-2020). Bands +-10% assumed.')
# --- planning parameters (IPCC AR5 WGIII Annex III Table A.III.1)
AR5={'coal':(40,3700,7400),'gas':(30,3700,7400),'nuclear':(60,3700,7400),'geothermal':(30,5300,7900),'hydro':(50,1800,7900),'solar_csp':(20,2200,3500),'solar_pv':(25,1100,2400),'wind_onshore':(25,1800,3500),'wind_offshore':(25,2600,3900),'bioenergy':(35,3500,7000)}
for t,(L,f1,f2) in AR5.items():
    lo,hi=(L*0.8,L*1.25) if t not in('coal',) else (30,50)
    P.add('plant_life_'+t,2010,'XWL',lo,L,hi,'a','compiled','S0819','IPCC AR5 WGIII Annex III Table A.III.1: standard plant lifetime used for LCOE (coal PC 40, gas CC 30, nuclear 60, geothermal 30, hydro 50, CSP 20, PV 25, onshore and offshore wind 25; biomass dedicated 40, CHP 30, mean taken 35). Single vintage (technology as of about 2010). Bands +-20%/+25% assumed (AR5 gives a point value).')
    mid=(f1+f2)/2/8766
    P.add('cf_planning_'+t,2010,'XWL',f1/8766,mid,f2/8766,'1','compiled','S0819','IPCC AR5 WGIII Annex III Table A.III.1 full-load hours range (min/max) divided by 8,766 h; central = midpoint of the AR5 range (the table gives only min and max). Planning ranges are wide: use cf_realised_* for vintage trends.')
# observed nuclear lifetimes at shutdown (RDS-2)
R=json.load(open(RAW+'rds2_rows.json'))
by=collections.defaultdict(list)
for a in R:
    if a['tab']=='16':
        sd=a['dates'][-1][0]; g=a['dates'][1][0]
        by[(sd//10)*10].append(sd-g)
for dec,ages in sorted(by.items()):
    if len(ages)>=3:
        ages=sorted(ages); m=statistics.mean(ages)
        P.add('plant_life_nuclear_observed',dec,'XWL',ages[int(0.05*(len(ages)-1))],m,ages[int(0.95*(len(ages)-1))],'a','compiled','S0116',f'Observed age at permanent shutdown (years from first grid connection to shutdown) of the {len(ages)} reactors in IAEA RDS-2 Table 16 that shut down in {dec}-{dec+9}; mean with 5th and 95th percentile. Includes early research-scale and accident closures; year = decade start. Compare with the 60-year planning life.')
# --- capacity additions
SPEC={'wind_onshore':'cap_add_wind_onshore','wind_offshore':'cap_add_wind_offshore','solar_pv':'cap_add_solar_pv','solar_csp':'cap_add_solar_csp','coal':'cap_add_coal','gas':'cap_add_gas','oil':'cap_add_oil','hydro':'cap_add_hydro','geothermal':'cap_add_geothermal','bioenergy':'cap_add_bioenergy'}
def topc(t,n=15):
    d=CAP[t]; return [c for c,_ in sorted(((c,x.get(2025,x.get(2024,0))) for c,x in d.items() if c in cc),key=lambda kv:-kv[1])[:n]]
fossil=('coal','gas','oil')
for t,ser in SPEC.items():
    ents=[('XWL',WC[t])]+[(c,CAP[t][c]) for c in topc(t)]
    for c,cap in ents:
        for y in range(2001,2026):
            if y not in cap or y-1 not in cap: continue
            d=cap[y]-cap[y-1]
            if t in fossil or t in('hydro','bioenergy','geothermal'):
                ce=max(d,0); lo=ce; hi=ce*1.5 if ce>0 else abs(d)*0.5 if d<0 else 0
                nt='Net change in IRENA year-end installed capacity (net of retirements; gross additions are higher, bound +50% assumed; negative net change recorded as zero central with high = half the net decline, i.e. possible gross additions).'
            else:
                ce=max(d,0); lo=ce*0.95; hi=ce*1.10; nt='Net change in IRENA year-end installed capacity; retirements of wind/PV are small so net approximates gross additions (bands -5%/+10% assumed). Includes repowering only as net MW.'
            O.add(ser,y,c,lo,ce,hi,'GW','measured' if c=='XWL' or True else 'measured',srcI,'IRENA Electricity Statistics 2026 H2 (installed capacity, all grid connections). '+nt+('' if c!='XWL' else ' World = sum of countries.'))
# pre-2000 wind from EIA (world only)
ew=es('INTL.37-7-WORL-MK.A')
for y in range(1982,2001):
    if y in ew and y-1 in ew:
        d=(ew[y]-ew[y-1])/1000; ce=max(d,0)
        O.add('cap_add_wind_onshore',y,'XWL',ce*0.9,ce,ce*1.15,'GW','compiled','S0804','Net change in EIA International Energy Statistics world installed wind capacity (million kW /1000); pre-2000 wind is all onshore for practical purposes. Bands assumed.')
# pre-2000 modelled for coal, gas, oil, hydro, geothermal from generation growth
gens={'coal':'Coal','gas':'Gas','oil':'Oil','hydro':'Hydropower'}
for t,col in gens.items():
    g=owid('eps.csv',col)
    cfs=[WG[t][y]/(WC[t][y]*8.766) for y in range(2000,2006) if y in WG[t] and y in WC[t]]
    CF=sum(cfs)/len(cfs)
    for y in range(1951,2001):
        if y in g and y-1 in g and g[y-1]>0:
            # use 3-year smoothed generation to damp noise
            def sm(yy): 
                xs=[g[k] for k in (yy-1,yy,yy+1) if k in g]; return sum(xs)/len(xs)
            d=(sm(y)-sm(y-1))/(8.766*CF); ce=max(d,0)
            O.add('cap_add_'+t,y,'XWL',ce*0.5,ce,ce*1.6,'GW','modelled','S0800;S0810','Modelled net capacity addition = change in 3-year-smoothed world generation (OWID/EI/Pinto) / (8.766 x CF), CF = IRENA world fleet-average realised %s capacity factor 2000-2005 (%.2f) held constant. Retirements and CF drift are ignored; bands -50%%/+60%% assumed. Negative changes set to zero.'%(t,CF))
# geothermal pre-2000 modelled from generation at CF 0.675 (Gutierrez-Negrin 2024) / IRENA CF; use EIA capacity 1980-1999
eg=es('INTL.35-7-WORL-MK.A')
for y in range(1981,2001):
    if y in eg and y-1 in eg:
        d=(eg[y]-eg[y-1])/1000; ce=max(d,0)
        O.add('cap_add_geothermal',y,'XWL',ce*0.8,ce,ce*1.3,'GW','compiled','S0804','Net change in EIA world geothermal electricity installed capacity 1980-1999 (bands assumed).')
# nuclear additions: RDS grid connections
ISO={'AE':'ARE','AM':'ARM','AR':'ARG','BE':'BEL','BG':'BGR','BR':'BRA','BY':'BLR','CA':'CAN','CH':'CHE','CN':'CHN','CZ':'CZE','DE':'DEU','ES':'ESP','FI':'FIN','FR':'FRA','GB':'GBR','HU':'HUN','IN':'IND','IR':'IRN','IT':'ITA','JP':'JPN','KR':'KOR','KZ':'KAZ','LT':'LTU','MX':'MEX','NL':'NLD','PK':'PAK','RO':'ROU','RU':'RUS','SE':'SWE','SI':'SVN','SK':'SVK','TW':'TWN','UA':'UKR','US':'USA','ZA':'ZAF'}
TY={'PWR':'pwr','BWR':'bwr','PHWR':'phwr','GCR':'gcr','LWGR':'lwgr','FBR':'fbr','HTGR':'htgr'}
for y in range(1954,2025):
    tot=sum(a['net'] for a in R if a['dates'][1][0]==y)/1000
    O.add('cap_add_nuclear',y,'XWL',tot*0.97,tot,tot*1.03,'GW','compiled','S0116','Net MW(e) of reactors with first grid connection in year y, IAEA RDS-2 No. 45 Tables 14-16 (units that connected and closed are included; reconnections after long shutdown are not counted). Bands +-3% assumed.')
    for ty in set(TY.values())|{'other'}:
        v=sum(a['net'] for a in R if a['dates'][1][0]==y and TY.get(a['type'],'other')==ty)/1000
        if v>0: O.add('cap_add_nuclear_'+ty,y,'XWL',v*0.97,v,v*1.03,'GW','compiled','S0116','As cap_add_nuclear, for reactor type '+ty+'.')
    for cc2,iso in ISO.items():
        v=sum(a['net'] for a in R if a['dates'][1][0]==y and a['cc']==cc2)/1000
        if v>0: O.add('cap_add_nuclear',y,iso,v*0.97,v,v*1.03,'GW','compiled','S0116','Net MW(e) with first grid connection in year y, country by plant location (RDS-2).')
# PV technology share anchor
O.add('pv_share_thin_film',2025,'XWL',0.015,16/706,0.03,'1','compiled','S0820','Fraunhofer ISE Photovoltaics Report (14 July 2026): thin film 16 GWp of 706 GWp module production in 2025 (First Solar only; CdTe), c-Si 98%. Only this anchor was extractable (other years are chart-only); CdTe/CIGS split not given. Bands assumed.')
O.write(); P.write()
