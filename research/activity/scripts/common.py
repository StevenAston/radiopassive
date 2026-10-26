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
