"""Shared helpers for the Task 1.9 activity builders.

Paths are relative to the repository root (three levels above this file).
Command line (parsed from sys.argv by every builder, unknown flags ignored):
  --write            write into data/activity/ (default: research/activity/out/)
  --raw DIR          raw-input folder (default $RADIO_RAW or research/activity/raw/)
  --mirror DIR       root of Steve's USGS mirror (usgs.140), needed by the DS140 / REE builders
"""
import csv,json,os,math,argparse
HERE=os.path.dirname(os.path.abspath(__file__))
REPO=os.path.abspath(os.path.join(HERE,'..','..','..'))
_ap=argparse.ArgumentParser(add_help=False)
_ap.add_argument('--write',action='store_true'); _ap.add_argument('--raw'); _ap.add_argument('--mirror')
ARGS,_=_ap.parse_known_args()
RAW=(ARGS.raw or os.environ.get('RADIO_RAW') or os.path.join(REPO,'research','activity','raw'))
RAW=RAW.rstrip('/')+'/'
MIRROR=(ARGS.mirror or os.environ.get('USGS_MIRROR') or '').rstrip('/')+'/' if (ARGS.mirror or os.environ.get('USGS_MIRROR')) else None
OUTDIR=os.path.join(REPO,'research','activity','out')+'/'
OUT=(os.path.join(REPO,'data','activity') if ARGS.write else OUTDIR.rstrip('/'))+'/'
REGISTRY=os.path.join(REPO,'research','activity','note_registry.json')
os.makedirs(OUTDIR,exist_ok=True)
COLS=['series','year','country','value_low','value_central','value_high','unit','below_detection','basis','source_ids','notes']
def fmt(x):
    if x==0: return '0'
    return ('%.6g'%x) if abs(x)<1e15 else repr(x)
class Out:
    def __init__(self,name):
        self.name=name; self.rows={}
    def add(self,series,year,country,lo,c,hi,unit,basis,src,notes='',bd=False):
        assert basis in('measured','compiled','modelled','interpolated','extrapolated'),basis
        c=max(c,0.0); lo=max(min(lo,c),0.0); hi=max(hi,c)
        k=(series,year,country)
        assert k not in self.rows,k
        self.rows[k]=[series,year,country,fmt(lo),fmt(c),fmt(hi),unit,'false',basis,src,notes]
    def has(self,series,year,country): return (series,year,country) in self.rows
    def write(self):
        os.makedirs(OUT,exist_ok=True)
        REG=REGISTRY
        reg=json.load(open(REG)) if os.path.exists(REG) else {}
        for k,row in self.rows.items():
            if 'assum' not in row[10].lower() and 'published uncertaint' not in row[10].lower():
                if row[3]==row[5]: row[10]=(row[10]+' Zero-width band: the value is exactly zero (or defined) in the source; no uncertainty assigned.').strip()
                else: row[10]=(row[10]+' Band assumed (analyst-assumed approx. 5th-95th percentile, not a published uncertainty).').strip()
        for k,row in self.rows.items():
            t=row[10]
            if '||' in t:
                head,tail=t.split('||',1); head=head.strip(); tail=tail.strip()
                if tail not in reg: reg[tail]='N%03d'%(len(reg)+1)
                row[10]=head+' [%s, see research/activity/note_registry.csv]'%reg[tail]
            elif len(t)>140:
                if t not in reg: reg[t]='N%03d'%(len(reg)+1)
                short=t[:90].rsplit(' ',1)[0]
                row[10]=short+' ... [%s, see research/activity/note_registry.csv]'%reg[t]
        json.dump(reg,open(REG,'w'))
        with open(OUT+self.name+'.csv','w',newline='',encoding='utf-8') as f:
            w=csv.writer(f,lineterminator='\n'); w.writerow(COLS)
            for k in sorted(self.rows,key=lambda k:(k[0],k[2]!='XWL',k[2],k[1])): w.writerow(self.rows[k])
        import collections
        c=collections.Counter(k[0] for k in self.rows)
        for s,n in sorted(c.items()):
            ys=[k[1] for k in self.rows if k[0]==s]
            print(self.name,s,n,min(ys),max(ys))
def bands(c,rel_lo,rel_hi=None):
    rel_hi=rel_lo if rel_hi is None else rel_hi
    return c*(1-rel_lo),c,c*(1+rel_hi)
