import csv,glob,re,os,collections
import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from lib import MIRROR
if MIRROR is None: raise SystemExit('DS140 mirror root required: pass --mirror /path/to/usgs.140 (or set USGS_MIRROR)')
D=MIRROR+'derived/csv/s3fs-public/media/files/'
def load(wb,sheet):
    """return (header list, {year:{col:float|None}}, raw-nonnumeric counter)"""
    p=D+wb+'/'+sheet+'.csv'
    rows=list(csv.reader(open(p,encoding='utf-8-sig')))
    hi=[i for i,r in enumerate(rows) if r and r[0].strip().lower().startswith('year')][0]
    hdr=[re.sub(r'\s+',' ',h.strip()) for h in rows[hi]]
    out={}; odd=collections.Counter()
    for r in rows[hi+1:]:
        if not r or not re.fullmatch(r'\d{4}',r[0].strip()): continue
        y=int(r[0]); d={}
        for h,v in zip(hdr[1:],r[1:]):
            v=v.strip().replace(',','')
            if v in('','NA','W','--','-'):
                if v not in('','NA'): odd[v]+=1
                d[h]=None; continue
            try: d[h]=float(v)
            except: odd[v]+=1; d[h]=None
        out[y]=d
    return hdr[1:],out,odd
def mod(wb,sheet):
    rows=list(csv.reader(open(D+wb+'/'+sheet+'.csv',encoding='utf-8-sig')))
    for r in rows[:6]:
        if 'Last modification' in r[0]: return r[0].replace('Last modification:','').strip()
