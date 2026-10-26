import os,sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from lib import *
from common import *
import csv,collections,math,json
import pandas as pd
O=Out('oil_gas')
MAP={'OWID_USS':'SUN','OWID_CZS':'CSK','OWID_YGS':'YUG','OWID_WRL':'XWL'}
CT=['USA','SAU','RUS','SUN','IRN','CAN','CHN','IRQ','ARE','KWT','BRA','NOR','VEN','MEX','NGA','KAZ','QAT','DZA','AGO','LBY','GBR','IDN','AZE','OMN','ARG','COL','EGY','IND','AUS','TKM','NLD','MYS','ROU','POL','DEU','UZB','ITA','TTO','PAK','THA','BGD','UKR']
def load(f,col):
    d=collections.defaultdict(dict)
    for r in csv.DictReader(open(RAW+f)):
        if r[col]=='': continue
        c='XWL' if r['Entity']=='World' else MAP.get(r['Code'],r['Code'])
        if c=='XWL' or c in CT: d[c][int(r['Year'])]=float(r[col])
    return d
oilE=load('oil-production-by-country.csv','Oil'); gasE=load('gas-production-by-country.csv','Gas')
cons={'oil':collections.defaultdict(dict),'gas':collections.defaultdict(dict)}
for r in csv.DictReader(open(RAW+'owid-energy.csv')):
    c='XWL' if r['country']=='World' else r['iso_code']
    for f in('oil','gas'):
        if r[f+'_consumption']!='' and (c=='XWL' or c in CT): cons[f][c][int(r['year'])]=float(r[f+'_consumption'])
def relE(y,c,floor=0.0):
    b=0.15 if y<1950 else 0.10 if y<1965 else 0.05 if y<1985 else 0.03
    b=max(b,floor)
    return b*(1 if c=='XWL' else 1.5)
NT='OWID series (Energy Institute from 1965; Etemad and Luciani 1991 for 1900-1979). Energy units as published. Bands assumed (approx. 5th-95th percentile): +-15% before 1950, +-10% to 1964, +-5% to 1984, +-3% from 1985 (x1.5 for countries).'
for name,E in(('oil',oilE),('gas',gasE)):
    for c,d in E.items():
        for y,v in d.items():
            if y<1900 or y>2025: continue
            lo,ce,hi=bands(v,relE(y,c)); O.add(f'{name}_production_twh',y,c,lo,ce,hi,'TWh','measured' if y>=1985 else 'compiled','S0806;S0803' if y>=1965 else 'S0806',NT)
# ---- physical volumes
oilm=eia_geo('57','1','TBPD'); oilt=eia_geo('57','1','MT'); gasd=eia_geo('26','1','BCF')
BBL=0.158987294928
def g(d,c): return d.get('WORL' if c=='XWL' else c,{})
# density t/m3 (world, 1980-1999)
rho=[]
for y in range(1980,2000):
    t=g(oilt,'XWL').get(y); b=g(oilm,'XWL').get(y)
    if t and b: rho.append((t*1e3)/(b*1e3*365.25*BBL))
RHO=sum(rho)/len(rho); print('rho t/m3',RHO,min(rho),max(rho))
# TWh per m3 ratio (1973-1979 for oil; 1980-1989 for gas)
def kfac(E,c,years,vol):
    xs=[E[c][y]/vol(c,y) for y in years if y in E.get(c,{}) and vol(c,y)]
    return sum(xs)/len(xs) if xs else None
oilvol=lambda c,y: (g(oilm,c).get(y,0)*1e3*365.25*BBL) or None   # m3/a
gasvol=lambda c,y: (g(gasd,c).get(y,0)*28.316847e6) or None
kW_o=kfac(oilE,'XWL',range(1980,1990),oilvol); kW_g=kfac(gasE,'XWL',range(1980,1990),gasvol)
print('TWh per m3 oil',kW_o,'gas',kW_g)
no='Crude oil including lease condensate (EIA thousand barrels per day x 365.25 x 0.158987 m3/bbl) from 1980 (EIA 1973-1979 world totals are incomplete: 50 Mb/d in 1973 against about 55 Mb/d). Before 1980: modelled from OWID/EI oil energy (crude plus NGL) divided by the %s TWh/m3 ratio observed %s (absorbs the NGL share and unit-conversion differences). Bands: measured +-3%% (x1.5 countries); modelled +-12%% before 1950 narrowing to +-8%% (assumed).'
for c,d in oilE.items():
    kc=kfac(oilE,c,range(1980,1990),oilvol) or kW_o
    for y,v in d.items():
        if y<1900 or y>2025: continue
        b=g(oilm,c).get(y)
        if b is not None and y>=1980 and b>0:
            m3=b*1e3*365.25*BBL; rel=0.03*(1 if c=='XWL' else 1.5); src='S0804'; bas='measured'; nt='EIA crude oil incl. lease condensate, kb/d converted to m3/a (0.158987 m3/bbl, 365.25 d). Bands assumed +-3% (x1.5 countries).'
        elif v>0:
            m3=v/kc; rel=(0.12 if y<1950 else 0.08)*(1 if c=='XWL' else 1.5); src='S0806;S0804'; bas='modelled'; nt=no%('%.3g'%kc,'1980-1989')
        else:
            m3=0; rel=0; src='S0806'; bas='modelled'; nt='Zero production in OWID/EI series.'
        lo,ce,hi=bands(m3,rel)
        O.add('oil_production_m3',y,c,lo,ce,hi,'m3',bas,src,nt)
        rr=math.sqrt(rel**2+0.06**2)
        lo,ce,hi=bands(m3*RHO,rr)
        O.add('oil_production_t',y,c,lo,ce,hi,'t',bas,src+(';S0804' if 'S0804' not in src else ''),nt+' Mass = volume x %.4f t/m3 (world mean of EIA crude MT / volume, 1980-1999; range %.3f-%.3f), +-6%% density uncertainty added in quadrature.'%(RHO,min(rho),max(rho)))
ng='Dry natural gas production (EIA billion cubic feet x 28.3168 million m3/bcf) from 1980. Before 1980 (and in years without EIA data): modelled from OWID/EI gas energy divided by the %s TWh/m3 ratio observed 1980-1989 (dry gas, standard conditions). Bands: measured +-4%% (x1.5 countries); modelled +-12%% before 1950 narrowing to +-8%% (assumed). Marketed versus dry/gross gas, flaring and reinjection not distinguished.'
for c,d in gasE.items():
    kc=kfac(gasE,c,range(1980,1990),gasvol) or kW_g
    for y,v in d.items():
        if y<1900 or y>2025: continue
        b=g(gasd,c).get(y)
        if b is not None and y>=1980 and b>0:
            m3=b*28.316847e6; rel=0.04*(1 if c=='XWL' else 1.5); src='S0804'; bas='measured'; nt='EIA dry natural gas production, bcf x 28.3168e6 m3. Bands assumed +-4% (x1.5 countries).'
        elif v>0:
            m3=v/kc; rel=(0.12 if y<1950 else 0.08)*(1 if c=='XWL' else 1.5); src='S0806;S0804'; bas='modelled'; nt=ng%('%.3g'%kc)
        else:
            m3=0;rel=0;src='S0806';bas='modelled';nt='Zero production in OWID/EI series.'
        lo,ce,hi=bands(m3,rel); O.add('gas_production_m3',y,c,lo,ce,hi,'m3',bas,src,nt)
# ---- power shares
etaUS=json.load(open(RAW+'eta_us.json')); etaUS={f:{int(k):v for k,v in d.items()} for f,d in etaUS.items()}
def smooth(d,w=2):
    ys=sorted(d); return {y:sum(d[k] for k in ys if abs(k-y)<=w)/sum(1 for k in ys if abs(k-y)<=w) for y in ys}
sm={f:smooth(etaUS[f]) for f in etaUS}
def eta(f,y):
    if y<1949: return 0.20,0.14,0.26
    v=sm[f].get(y,sm[f][max(sm[f])]); return v,v*0.8,v*1.2
def logq(num,den):
    n_lo,n_c,n_hi=num; d_lo,d_c,d_hi=den
    c=n_c/d_c
    up=math.sqrt(math.log(n_hi/n_c)**2+math.log(d_c/d_lo)**2); dn=math.sqrt(math.log(n_c/n_lo)**2+math.log(d_hi/d_c)**2)
    return c*math.exp(-dn),c,c*math.exp(up)
gen={f:owid('eps.csv',F) for f,F in(('gas','Gas'),('oil','Oil'))}
prodW={'gas':gasE['XWL'],'oil':oilE['XWL']}
for f in ('gas','oil'):
    for y in range(1900,2026):
        if y not in gen[f] or gen[f][y]<=0: continue
        E_=cons[f]['XWL'].get(y) if y>=1965 else prodW[f].get(y)
        if not E_ or E_<=0: continue
        extra=0.0 if y>=1965 else 0.03
        rE=relE(y,'XWL')+extra
        rg=0.30 if y<1950 else 0.10 if y<1965 else 0.05 if y<1985 else 0.03 if y<2000 else 0.02
        G=(gen[f][y]*(1-rg),gen[f][y],gen[f][y]*(1+rg)); e=eta(f,y)
        burn=logq(G,e); sh=logq(burn,(E_*(1-rE),E_,E_*(1+rE))); sh=tuple(min(1.0,x) for x in sh)
        O.add(f'{f}_burn_power_twh',y,'XWL',burn[0],burn[1],burn[2],'TWh','modelled','S0800;S0803;S0804',f'Thermal energy of {f} burned for electricity = {f} generation (OWID/Ember/EI) / efficiency. Efficiency proxy: US electric-power-sector fuel-to-net-generation efficiency, EIA Monthly Energy Review Tables 2.6 and 7.2a (5-year smoothed), bounds +-20%; 0.20 (0.14-0.26) before 1949 (assumed). World fleet differs from the US fleet.')
        O.add(f'{f}_power_share',y,'XWL',sh[0],sh[1],sh[2],'1','modelled','S0800;S0803;S0804;S0806',f'Share of world {f} energy used for power generation = {f}_burn_power_twh / {f} consumption (TWh; consumption equals production before 1965). Log-space quadrature bands (METHODS 11.1). Oil consumption includes all liquids, so the share is of total oil.')
# US measured gas share
usg=collections.defaultdict(dict)
for x in csv.DictReader(open(RAW+'T04.03.csv')):
    if x['YYYYMM'].endswith('13') and x['Value'] not in('Not Available','Not Applicable',''): usg[x['MSN']][int(x['YYYYMM'][:4])]=float(x['Value'])
for y in sorted(usg['NNEIPUS']):
    if y in usg['NNTCPUS'] and y<=2025:
        s=usg['NNEIPUS'][y]/usg['NNTCPUS'][y]; O.add('gas_power_share',y,'USA',s*0.98,s,min(1.0,s*1.02),'1','measured','S0804','US EIA Monthly Energy Review Table 4.3: natural gas consumed by electric power sector / total natural gas consumption (bcf). Bands assumed +-2%. (Lifecycle-view USA share.)')
# ---- wells drilled (US)
for s,nm in(('E_ERTW0','wells_drilled_total'),('E_ERTWO','wells_drilled_oil'),('E_ERTWG','wells_drilled_gas'),('E_ERTWD','wells_drilled_dry')):
    d=pd.read_excel(RAW+'wells_%s.xls'%s,sheet_name='Data 1',header=None).iloc[3:,:].dropna()
    for _,r in d.iterrows():
        y=r[0].year; v=float(r[1])
        O.add('us_'+nm,y,'USA',v*0.95,v,v*1.05,'1','measured','S0804','EIA Petroleum and Other Liquids, exploratory and developmental wells drilled (count), 1949-2010 (series discontinued). Bands assumed +-5%.')
# ---- produced water
# US anchors Veil/GWPC (S0311): million bbl/yr
anch={2007:20195,2012:21181,2017:24395}
usoil=eia_geo('57','1','TBPD').get('USA',{})
usoilE=oilE['USA']
us_m3={y:v*1e6*BBL for y,v in anch.items()}
for y,v in us_m3.items():
    O.add('produced_water_m3',y,'USA',v*0.9,v,v*1.1,'m3','compiled','S0311','Veil (2019, GWPC): US produced water 20,195 (2007), 21,181 (2012), 24,395 (2017) million bbl; x0.158987 m3/bbl. Bands assumed +-10% (state-reported data, mixed completeness).')
# US WOR (water per volume oil) anchors computed on crude production
wor={y:us_m3[y]/oilvol('USA',y) for y in anch}; print('US water/oil volume',wor)
def wor_us(y):
    ys=sorted(wor)
    if y<=ys[0]:
        # lower earlier: linear to 0.5x at 1950
        return wor[ys[0]]*(0.5+0.5*max(0,(y-1950))/(ys[0]-1950))
    if y>=ys[-1]: return wor[ys[-1]]
    for a,b in zip(ys,ys[1:]):
        if a<=y<=b: return wor[a]+(wor[b]-wor[a])*(y-a)/(b-a)
for y in range(1950,2026):
    if y in anch: continue
    vol=oilvol('USA',y) if y>=1980 else oilE['USA'].get(y,0)/kfac(oilE,'USA',range(1980,1990),oilvol)
    if not vol: continue
    c=vol*wor_us(y)
    O.add('produced_water_m3',y,'USA',c*0.5,c,c*1.5,'m3','modelled','S0311;S0804;S0806','Modelled: US crude oil volume x water/oil volume ratio. Ratio anchored to Veil (S0311) volumes in 2007, 2012, 2017 (interpolated between; held at the 2017 value after); before 2007 assumed to fall linearly to half the 2007 value in 1950 (older fields, lower water cut; analyst assumption, see 1.4 availability.csv). Bands +-50% (assumed). Gas-well water is implicitly included in the ratio.')
# world: oil volume x global WOR (central 3, S0332/S0333 advocacy anchors "above 3 and rising"); earlier lower
for y in range(1950,2026):
    vol=oilvol('XWL',y) if y>=1980 else oilE['XWL'].get(y,0)/kW_o
    if not vol: continue
    if y>=2010: w=3.0
    else: w=1.0+2.0*(y-1950)/60
    c=vol*w
    O.add('produced_water_m3',y,'XWL',c*0.6,c,c*1.5,'m3','modelled','S0332;S0333;S0314;S0804;S0806','Modelled: world crude oil volume x global water/oil volume ratio. Ratio 3.0 from 2010 (central; Texas Living Waters/EDF 2025 and Khatib give "above 3 and rising", advocacy-grade anchors, S0332/S0333), assumed to rise linearly from 1.0 in 1950. IOGP member data (814 Mt discharged + 1,107 Mt re-injected, 2018, S0314) are a partial check only. Bands -40%/+50% (assumed). No peer-reviewed global time series found.')
# unconventional share US: single anchor
O.add('produced_water_unconv_share',2017,'USA',0.10,0.16,0.22,'1','modelled','S0311;S0315','Unconventional (shale/tight) share of US produced water in 2017, about 16% (Task 1.4 inference from Scanlon et al. 2020 and Veil 2019, mixed sources, S0315/S0311); bounds assumed 10-22%. Other years not obtained: see notes.')
O.write()
