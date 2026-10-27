import os,sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from lib import *
from common import *
import csv,collections,math
import pandas as pd
O=Out('coal')
cc=countries()
MAP={'OWID_USS':'SUN','OWID_CZS':'CSK','OWID_YGS':'YUG','OWID_GDR':'DDR','OWID_WRL':'XWL'}
CT=['CHN','USA','IND','RUS','SUN','DEU','GBR','POL','ZAF','AUS','IDN','CAN','UKR','KAZ','CZE','CSK','FRA','JPN','TUR','KOR','PRK','COL','VNM','MNG','ESP','BEL','ROU','BGR','YUG','HUN','GRC','SRB','THA','IRN','PAK','NZL','MEX','BRA']
def load(f,col):
    d=collections.defaultdict(dict)
    for r in csv.DictReader(open(RAW+f)):
        if r[col]=='': continue
        c=MAP.get(r['Code'],r['Code'])
        if r['Entity']=='World': c='XWL'
        if c=='XWL' or c in CT: d[c][int(r['Year'])]=float(r[col])
    return d
prod=load('coal-production-by-country.csv','Coal')
# consumption from OWID energy dataset
cons=collections.defaultdict(dict)
for r in csv.DictReader(open(RAW+'owid-energy.csv')):
    if r['coal_consumption']=='': continue
    c='XWL' if r['country']=='World' else r['iso_code']
    if c=='XWL' or c in CT: cons[c][int(r['year'])]=float(r['coal_consumption'])
def relE(y,c):
    b=0.20 if y<1900 else 0.10 if y<1965 else 0.05 if y<1985 else 0.03
    return b*(1 if c=='XWL' else 1.5)
def srcE(y): return 'S0230;S0803' if y>=1965 else 'S0230'
def basisE(y): return 'measured' if y>=1985 else 'compiled'
NT='OWID series (Energy Institute from 1965; Etemad and Luciani 1991 for 1900-1979; Smil 2017 for world 1800-1899; NIC/Fouquet for UK before 1900). Energy units as published. Bands assumed (approx. 5th-95th percentile): +-20% before 1900, +-10% to 1964, +-5% to 1984, +-3% from 1985 (x1.5 for countries).'
for c,d in prod.items():
    for y,v in d.items():
        if y<1800 or y>2025: continue
        if c=='XWL' and y>=1800 or c!='XWL':
            lo,ce,hi=bands(v,relE(y,c)); O.add('coal_production_twh',y,c,lo,ce,hi,'TWh',basisE(y),srcE(y),NT)
for c,d in cons.items():
    for y,v in d.items():
        lo,ce,hi=bands(v,relE(y,c)); O.add('coal_consumption_twh',y,c,lo,ce,hi,'TWh','measured' if y>=1985 else 'compiled','S0803;S0805','Energy Institute Statistical Review via OWID energy dataset, TWh.')
for y,v in prod['XWL'].items():
    if y<1965:
        lo,ce,hi=bands(v,relE(y,'XWL')+0.02); O.add('coal_consumption_twh',y,'XWL',lo,ce,hi,'TWh','modelled','S0230','World consumption before 1965 set equal to world production (stock changes unknown), as OWID does; band widened by 2 points.')
# ---- tonnes
eiap=eia_geo('7','1','MT'); eiac=eia_geo('7','2','MT')
def eg(d,c): return d.get('WORL' if c=='XWL' else c,{})
def ratio85(c,P,E):
    xs=[P[c][y]*1e6/(eg(E,c)[y]*1e3) for y in range(1985,1990) if y in P.get(c,{}) and y in eg(E,c) and eg(E,c)[y]>0]
    return sum(xs)/len(xs) if xs else None
rW=ratio85('XWL',prod,eiap); print('world MWh/t 1985-89',rW)
def divisor(y,r85):
    if y<=1900: return 6.85
    if y>=1985: return r85
    return 6.85+(r85-6.85)*(y-1900)/85
note_t='Modelled: energy (TWh) divided by a calorific divisor c(y) MWh/t, c=6.85 (UK calibration, S0230/S0231) up to 1900, falling linearly to the 1985-1989 mean ratio of OWID energy to EIA tonnes (%s MWh/t) in 1985 (rising lignite and sub-bituminous share). Low tonnes use 8.14 MWh/t before 1985 scaled likewise (1.19 x c); high tonnes use 0.85 x c. 6.85 and 8.14 MWh/t are the extremes found by the coal survey.'
for c,d in prod.items():
    r85=ratio85(c,prod,eiap) or rW
    for y,v in d.items():
        if y<1800 or y>2025: continue
        e=eg(eiap,c).get(y)
        if y>=1985 and e and e>0:
            t=e*1e3; lo,ce,hi=bands(t,0.04*(1 if c=='XWL' else 1.5))
            O.add('coal_production_t',y,c,lo,ce,hi,'t','measured','S0804','EIA International Energy Statistics, coal production (thousand metric tons, all ranks) x 1000; bands assumed +-4%.')
        elif y<1985 or (y>=1985 and not e):
            if v==0: 
                O.add('coal_production_t',y,c,0,0,0,'t','modelled','S0230','Zero coal production in the OWID energy series, so tonnes are exactly zero (zero-width band by definition).'); continue
            cdiv=divisor(y,r85); extra=''
            if y>1985:
                prev=[yy for yy in sorted(eg(eiap,c)) if yy<y and eg(eiap,c)[yy]>0 and yy in d and d[yy]>0]
                if prev:
                    yy=prev[-1]; cdiv=d[yy]*1e6/(eg(eiap,c)[yy]*1e3); extra=' Years after the last EIA tonnage use the last observed energy/tonne ratio (%d: %.2f MWh/t).'%(yy,cdiv)
            ce=v*1e6/cdiv
            lo=v*1e6/(1.188*cdiv) if y<1985 else ce*0.92; hi=v*1e6/(0.85*cdiv) if y<1985 else ce*1.08
            O.add('coal_production_t',y,c,lo,ce,hi,'t','modelled','S0230;S0804;S0231',(note_t%('%.2f'%r85))+extra)
# consumption tonnes
for c,d in cons.items():
    r85=ratio85(c,cons,eiac) or ratio85(c,prod,eiap) or rW
    for y,v in d.items():
        e=eg(eiac,c).get(y)
        if y>=1985 and e and e>0:
            lo,ce,hi=bands(e*1e3,0.04*(1 if c=='XWL' else 1.5)); O.add('coal_consumption_t',y,c,lo,ce,hi,'t','measured','S0804','EIA coal consumption, thousand metric tons x 1000; bands assumed +-4%.')
        else:
            cdiv=divisor(y,r85); ce=v*1e6/cdiv
            O.add('coal_consumption_t',y,c,v*1e6/(1.188*cdiv),ce,v*1e6/(0.85*cdiv),'t','modelled','S0803;S0805;S0804',note_t%('%.2f'%r85))
for y,v in prod['XWL'].items():
    if y<1965:
        cdiv=divisor(y,rW); O.add('coal_consumption_t',y,'XWL',v*1e6/(1.188*cdiv),v*1e6/cdiv,v*1e6/(0.85*cdiv),'t','modelled','S0230',"World consumption set equal to production before 1965. "+note_t%('%.2f'%rW))
# ---- electricity share of coal
def mer(t,msn):
    return {int(x['YYYYMM'][:4]):float(x['Value']) for x in csv.DictReader(open(RAW+t+'.csv')) if x['MSN']==msn and x['YYYYMM'].endswith('13') and x['Value'] not in('Not Available','Not Applicable','')}
usG={f:mer('T07.02A',m) for f,m in [('coal','CLETPUS'),('gas','NGETPUS'),('oil','PAETPUS')]}
usI={f:mer('T02.06',m) for f,m in [('coal','CLEIBUS'),('gas','NNEIBUS'),('oil','PAEIBUS')]}
etaUS={f:{y:usG[f][y]*3412.14/1e6/usI[f][y] for y in usG[f] if y in usI[f] and usI[f][y]>0} for f in usG}
json.dump(etaUS,open(RAW+'eta_us.json','w'))
# UK
d=pd.read_excel(RAW+'coal1853.xls',sheet_name='Coal Availability & Consumption',header=None)
uk={}
for _,r in d.iterrows():
    s=str(r[0]).strip()
    if len(s)==4 and s.isdigit():
        try: uk[int(s)]=(float(r[5]),float(r[16]))
        except: pass
gbcoal=owid('eps.csv','Coal',ent='United Kingdom')
etaUK={y:gbcoal[y]/(uk[y][0]*6.85) for y in uk if y in gbcoal and y<=1983 and uk[y][0]>0}
def smooth(d,w=2):
    ys=sorted(d); return {y:sum(d[k] for k in ys if abs(k-y)<=w)/sum(1 for k in ys if abs(k-y)<=w) for y in ys}
uks=smooth(etaUK); uss=smooth(etaUS['coal'])
KA={}
def kfac(y):
    # world-to-US fleet efficiency ratio: 1 to 1950, linear to the 2012 anchor, then to the 2023 anchor, constant after
    if not KA: return 1.0
    if y<=1950: return 1.0
    if y<=2012: return 1+(KA[2012]-1)*(y-1950)/62
    if y<=2023: return KA[2012]+(KA[2023]-KA[2012])*(y-2012)/11
    return KA[2023]
def eta_coal(y):
    if y<=1920: return 0.05,0.07,0.10
    if y<1949: v=uks.get(y); 
    elif y<=1965: v=(uks[y]+uss[y])/2
    else: v=uss.get(y,uss[max(uss)])
    k=kfac(y)
    if y<=1950: return v*0.85,v,v*1.15
    tol=0.10
    return v*k*(1-tol),v*k,v*k*(1+tol)
def etaF(f,y):
    s=smooth(etaUS[f])
    v=s.get(y) if y>=1949 else 0.20
    if y>=1949 and v is None: v=s[max(s)]
    return v,v*(0.8 if y>=1949 else 0.7),v*(1.2 if y>=1949 else 1.3)
gen=owid('eps.csv','Coal')
def prodlog(c,lo_c,hi_c,vs):
    """vs: list of (lo,c,hi) central factors; quotient: last is denominator."""
    pass
def logq(num,den):
    n_lo,n_c,n_hi=num; d_lo,d_c,d_hi=den
    c=n_c/d_c
    up=math.sqrt(math.log(n_hi/n_c)**2+math.log(d_c/d_lo)**2) if n_c>0 and d_lo>0 else 0
    dn=math.sqrt(math.log(n_c/n_lo)**2+math.log(d_hi/d_c)**2) if n_lo>0 and d_c>0 else 0
    return c*math.exp(-dn),c,c*math.exp(up)
ANCH={2012:(0.59,0.04,'EIA IEO coal chapter: electric power 59% of world coal consumption in 2012 (energy basis)'),2023:(0.65,0.04,'IEA Coal 2024: 5855 Mt of 8687 Mt = 67.4% by mass in 2023; energy-basis share assumed 0.65 (power-sector coal has below-average calorific value)')}
for ay in ANCH:
    cs=cons['XWL'][ay]; raw=gen[ay]/uss.get(ay,uss[max(uss)])/cs
    KA[ay]=raw/ANCH[ay][0]
    print('anchor',ay,'raw share',raw,'k',KA[ay])
share_world={}
for y in range(1900,2026):
    if y not in gen or y not in prod['XWL'] : continue
    if y>=1965 and y in cons['XWL']: cs=cons['XWL'][y]
    elif y>=1965 and (y-1) in cons['XWL'] and (y-1) in prod['XWL']: cs=cons['XWL'][y-1]*prod['XWL'][y]/prod['XWL'][y-1]
    else: cs=prod['XWL'][y]
    g=gen[y]
    if g<=0 or cs<=0: continue
    gr=relE(y,'XWL') if True else 0
    rg=0.20 if y<1950 else 0.10 if y<1965 else 0.05 if y<1985 else 0.03 if y<2000 else 0.02
    E=(cs*(1-relE(y,'XWL')-(0.02 if y<1965 else 0)),cs,cs*(1+relE(y,'XWL')+(0.02 if y<1965 else 0)))
    G=(g*(1-rg),g,g*(1+rg))
    e=eta_coal(y)
    burn=logq(G,e)   # thermal TWh = G/eta
    sh=logq(burn,E)
    sh=tuple(min(1.0,x) for x in sh)
    share_world[y]=sh
    O.add('coal_burn_power_twh',y,'XWL',burn[0],burn[1],burn[2],'TWh','modelled','S0800;S0230;S0803;S0232;S0231;S0849;S0850',
      'Thermal energy of coal burned for electricity = coal generation / efficiency. Efficiency proxy (assumed bounds +-15%): UK coal generation / UK power-station coal use at 6.85 MWh/t (S0231, 1920-1964), mean of UK and US (S0232 plus EIA MER Tables 2.6 and 7.2a, S0804) 1949-1964, US alone from 1965; 0.07 (0.05-0.10) before 1920. World calibration: the US-based efficiency is multiplied by a world/US factor k, 1 up to 1950, rising linearly to 1.05 in 2012 and 1.10 in 2023 so that the world share matches two anchors: 59% (2012, EIA IEO coal chapter, energy basis, S0850) and 65% (2023; IEA Coal 2024 gives 5855 of 8687 Mt = 67.4% by mass, S0849; energy-basis value assumed). Efficiency band +-10% after 1950 and +-15% before; 2025 consumption extrapolated from 2024 by the production ratio. (An earlier version of this series mis-ordered the efficiency bounds and gave 81% in 2020; fixed.)')
    O.add('coal_power_share',y,'XWL',sh[0],sh[1],sh[2],'1','modelled','S0800;S0230;S0803;S0232;S0231;S0849;S0850',
      'Share of world coal energy consumed in power generation = coal_burn_power_twh / coal consumption (TWh). Products and quotients bounded in log-space quadrature (METHODS 11.1). Calibrated to 59% (2012, S0850) and 65% (2023, S0849). Check anchors: UK 2.5% (1913), 8.4% (1938), 15% (1949); US 18.6% (1950), 91% (2000).')
# US measured
usc=collections.defaultdict(dict)
for x in csv.DictReader(open(RAW+'T06.02.csv')) if False else csv.DictReader(open(RAW+'t0602.csv')):
    if x['YYYYMM'].endswith('13') and x['Value'] not in('Not Available','Not Applicable',''):
        usc[x['MSN']][int(x['YYYYMM'][:4])]=float(x['Value'])
for y in sorted(usc['CLEIPUS']):
    if y in usc['CLTCPUS'] and y<=2025:
        s=usc['CLEIPUS'][y]/usc['CLTCPUS'][y]
        O.add('coal_power_share',y,'USA',s*0.98,s,min(1.0,s*1.02),'1','measured','S0232','US EIA Monthly Energy Review Table 6.2: coal consumed by electric power sector / total coal consumption (short tons). Bands assumed +-2%.')
for y,(e,t) in uk.items():
    if t>0 and y<=2025:
        s=e/t; 
        O.add('coal_power_share',y,'GBR',s*0.97,s,min(1.0,s*1.03),'1','measured','S0231','DESNZ Historical Coal Data: electricity use / total inland consumption. 1913-2025 annual. Bands assumed +-3%.')
# ---- ash
ashn='Total ash from coal burned for power = thermal coal burn (TWh) / calorific divisor c(y) (t) x ash yield. Ash yield central 0.12 (low 0.08, high 0.16; coal survey range 0.10-0.16 for ash content, S0230 notes and availability.csv; assumption). World coal anchors for validation: 280 Mt ash (1985), about 780 Mt coal combustion products (2010) in the Task 1.3 survey.'
for y,b in sorted(share_world.items()):
    pass
for y in range(1900,2026):
    if y not in share_world: continue
    rW_=rW
    cdiv=divisor(y,rW_)
    # burn TWh central from O rows
    k=('coal_burn_power_twh',y,'XWL'); r=O.rows[k]
    lo,ce,hi=float(r[3]),float(r[4]),float(r[5])
    t=(lo/(1.188*cdiv)*1e6/1e0 if False else 0)
    tb=(lo*1e6/(1.0*cdiv*1.188),ce*1e6/cdiv,hi*1e6/(0.85*cdiv))   # tonnes
    ay=(0.08,0.12,0.16)
    a=logq(( tb[0]*ay[0], tb[1]*ay[1], tb[2]*ay[2]),(1,1,1)) if False else None
    ce_=tb[1]*ay[1]
    up=math.sqrt(math.log(tb[2]/tb[1])**2+math.log(ay[2]/ay[1])**2); dn=math.sqrt(math.log(tb[1]/tb[0])**2+math.log(ay[1]/ay[0])**2)
    O.add('coal_ash_power_t',y,'XWL',ce_*math.exp(-dn),ce_,ce_*math.exp(up),'t','modelled','S0800;S0230;S0803;S0804;S0849;S0850',ashn)
    # fly fraction
    f=0.30 if y<=1920 else (0.30+0.50*(y-1920)/40 if y<1960 else 0.80)
    fl=(f*0.75,f,min(1.0,f*1.2))
    k2=('coal_ash_power_t',y,'XWL'); r2=O.rows[k2]
    alo,ac,ahi=float(r2[3]),float(r2[4]),float(r2[5])
    up=math.sqrt(math.log(ahi/ac)**2+math.log(fl[2]/fl[1])**2); dn=math.sqrt(math.log(ac/alo)**2+math.log(fl[1]/fl[0])**2)
    O.add('coal_fly_ash_t',y,'XWL',ac*f*math.exp(-dn),ac*f,ac*f*math.exp(up),'t','modelled','S0800;S0230;S0803;S0804;S0849;S0850',
      'Fly-ash fraction of power-station ash: 0.30 to 1920 rising linearly to 0.80 by 1960 and constant after (assumed: stoker/grate firing dominant early, pulverised-coal with collectors later; coal survey notes stokers 15% fly). '+ashn+' Utilisation share not obtained (ACAA data inaccessible).')
# ---- post-pass (defect fixes 2026-10-26): annual interpolation of decadal pre-1900 XWL points; 2025 carry-forward of consumption
def _num(r): return float(r[3]),float(r[4]),float(r[5])
INTERP_TAIL='Interpolated, not observed: the series has decadal points only before 1900, so each intervening year is filled by log-linear interpolation (geometric, constant growth rate) between the bracketing decadal points, applied separately to the central value, the low bound and the high bound. Source ids are inherited from the two bracketing points. Do not read year-to-year variation within a decade as real; the band is the interpolated decadal band and is not widened for the interpolation.'
for ser in ('coal_production_t','coal_consumption_t','coal_production_twh','coal_consumption_twh'):
    for c in sorted({k[2] for k in O.rows if k[0]==ser}):
        ys=sorted(k[1] for k in O.rows if k[0]==ser and k[2]==c)
        for a,b in zip(ys,ys[1:]):
            if b-a<=1 or b>1900: continue      # only gaps closing on or before 1900
            ra,rb=O.rows[(ser,a,c)],O.rows[(ser,b,c)]
            va,vb=_num(ra),_num(rb)
            if min(va+vb)<=0: continue
            srcs=ra[9].split(';')+[x for x in rb[9].split(';') if x not in ra[9].split(';')]
            for y in range(a+1,b):
                f=(y-a)/(b-a)
                lo,ce,hi=[math.exp(math.log(x)*(1-f)+math.log(z)*f) for x,z in zip(va,vb)]
                O.add(ser,y,c,lo,ce,hi,ra[6],'interpolated',';'.join(srcs),'Interpolated log-linearly between %d and %d.||%s'%(a,b,INTERP_TAIL))
def _extrap_2025(ser):
    for c in sorted({k[2] for k in O.rows if k[0]==ser}):
        if O.has(ser,2025,c) or not O.has(ser,2024,c): continue
        r=O.rows[(ser,2024,c)]; lo,ce,hi=_num(r)
        tr=[abs(math.log(float(O.rows[(ser,y,c)][4])/float(O.rows[(ser,y-1,c)][4]))) for y in range(2015,2025) if O.has(ser,y,c) and O.has(ser,y-1,c) and float(O.rows[(ser,y,c)][4])>0 and float(O.rows[(ser,y-1,c)][4])>0]
        if not tr or lo<=0 or hi<=ce: continue
        st=max(tr)
        up=math.sqrt(math.log(hi/ce)**2+st**2); dn=math.sqrt(math.log(ce/lo)**2+st**2)
        O.add(ser,2025,c,ce*math.exp(-dn),ce,ce*math.exp(up),r[6],'extrapolated',r[9],
          'Extrapolated: 2024 central value carried forward to 2025 (persistence); 2025 not yet published. s_trend = %.4f.||Carry-forward rule (analyst-assumed): central = 2024 central. Each side of the band is widened so that |ln(high/central)| = sqrt(s_stat^2 + s_trend^2) on the high side and |ln(central/low)| = sqrt(s_stat^2 + s_trend^2) on the low side, where s_stat is the same-side log half-width of the 2024 band and s_trend is the largest absolute year-on-year log change of the series central value over 2015-2024 (combined in quadrature).'%st)
for _s in ('coal_consumption_t','coal_consumption_twh'): _extrap_2025(_s)
O.write()
