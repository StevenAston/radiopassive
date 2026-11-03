import json,csv,os
from lib import RAW,REPO
_E=None
def eia():
    global _E
    if _E is None:
        _E=json.load(open(RAW+'eia_annual.json'))
        for v in _E.values(): v['data']={int(k):x for k,x in v['data'].items()}
    return _E
def es(sid): return eia()[sid]['data']
def owid(f,col,ent='World'):
    return {int(x['Year']):float(x[col]) for x in csv.DictReader(open(RAW+f)) if x['Entity']==ent and x[col]!=''}
import collections
_M=None
def irena(dt,tech):
    global _M
    if _M is None:
        m=json.load(open(RAW+'irena_meta.json'))
        _M=dict(zip(m['variables'][0]['valueTexts'],m['variables'][0]['values']))
    out=collections.defaultdict(dict)
    for r in list(csv.reader(open(RAW+f'irena_{dt}_{tech}.csv',encoding='latin-1')))[1:]:
        try: v=float(r[5])
        except: continue
        out[_M[r[0]]][int(r[4])]=v
    return out
def eia_geo(prod,act,unit):
    """returns {geo:{year:value}} for INTL.prod-act-GEO-unit.A"""
    out={}
    pre='INTL.%s-%s-'%(prod,act); suf='-%s.A'%unit
    for sid,v in eia().items():
        if sid.startswith(pre) and sid.endswith(suf):
            out[v['geo']]=v['data']
    return out
def countries():
    return {r['code'] for r in csv.DictReader(open(os.path.join(REPO,'data','reference','countries.csv')))}

def carry_2025(O,series,print_=True):
    """2024 -> 2025 carry-forward, identical rule to build_coal.py (_extrap_2025) and build_elec.py: central = 2024 central;
    each band side widened to sqrt(s_stat^2 + s_trend^2) in log space; s_trend = largest |yoy log change| of the central value 2015-2024.
    Same registry note tail as the coal/electricity rows. Two edge cases handled as build_elec.py does (exact zeros) or as stated here:
    a side with no width (hi == central, e.g. a fraction saturated at its cap of 1) keeps that side at the central value."""
    import math
    tail=('Carry-forward rule (analyst-assumed): central = 2024 central. Each side of the band is widened so that |ln(high/central)| = sqrt(s_stat^2 + s_trend^2) on the high side and |ln(central/low)| = sqrt(s_stat^2 + s_trend^2) on the low side, where s_stat is the same-side log half-width of the 2024 band and s_trend is the largest absolute year-on-year log change of the series central value over 2015-2024 (combined in quadrature).')
    for ser in series:
        for c in sorted({k[2] for k in O.rows if k[0]==ser}):
            if O.has(ser,2025,c) or not O.has(ser,2024,c): continue
            r=O.rows[(ser,2024,c)]; lo,ce,hi=float(r[3]),float(r[4]),float(r[5])
            if lo==ce==hi==0:
                O.add(ser,2025,c,0,0,0,r[6],'extrapolated',r[9],'Extrapolated: 2024 value (exactly zero in the source) carried forward to 2025; 2025 not yet published. Zero-width band: the value is exactly zero in the source.'); print('carry-forward',ser,c,'zero'); continue
            tr=[abs(math.log(float(O.rows[(ser,y,c)][4])/float(O.rows[(ser,y-1,c)][4]))) for y in range(2015,2025) if O.has(ser,y,c) and O.has(ser,y-1,c) and float(O.rows[(ser,y,c)][4])>0 and float(O.rows[(ser,y-1,c)][4])>0]
            if not tr or lo<=0 or ce<=0:
                print('carry-forward SKIPPED',ser,c,lo,ce,hi); continue
            st=max(tr)
            up=math.sqrt(math.log(hi/ce)**2+st**2) if hi>ce else None
            dn=math.sqrt(math.log(ce/lo)**2+st**2)
            if up is None:
                O.add(ser,2025,c,ce*math.exp(-dn),ce,ce,r[6],'extrapolated',r[9],'Extrapolated: 2024 central value carried forward to 2025 (persistence); 2025 not yet published. s_trend = %.4f. High side kept at the central value (the 2024 high bound equals the central value, a cap).||'%st+tail)
            else:
                O.add(ser,2025,c,ce*math.exp(-dn),ce,ce*math.exp(up),r[6],'extrapolated',r[9],'Extrapolated: 2024 central value carried forward to 2025 (persistence); 2025 not yet published. s_trend = %.4f.||'%st+tail)
            if print_: print('carry-forward',ser,c,'s_trend=%.4f'%st)
