import re,json,collections,os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from lib import RAW
T=open(RAW+'rds2.txt').read().split('\n')
# locate table ranges
def find(pat,start=0):
    for i in range(start,len(T)):
        if re.search(pat,T[i]): return i
idx={}
marks=[(i,re.search(r'TABLE (1[4-9])\.',l).group(1)) for i,l in enumerate(T) if re.search(r'^\s*TABLE 1[4-9]\.',l)]
tab=None;rows=[]
types={'PWR','BWR','PHWR','LWGR','GCR','FBR','HTGR','HWLWR','HWGCR','SGHWR','AGR','X','LWCHWR','HWGCR','GCHWR','OMR','HWBWR'}
date=re.compile(r'(\d{4})-(\d{1,2})\b')
ln2tab={}
cur=None
mi=0
for i,l in enumerate(T):
    m=re.search(r'^\s*TABLE (1[4-9])\.',l)
    if m: cur=m.group(1)
    if cur not in('14','15','16'): continue
    m=re.search(r'\b([A-Z]{2})\s*-\s*(\d+[A-Z]?)\s+(.+?)\s{2,}(\S+)\s+(.*)$',l)
    if m and m.group(4) not in types: m=None
    if not m: m=re.search(r'\b([A-Z]{2})\s*-\s*(\d+[A-Z]?)\s+(.+?)\s+(PWR|BWR|PHWR)\s+(.*)$',l)
    if not m: continue
    cc,num,name,typ,rest=m.groups()
    # type may be followed by a model; find first token in types
    toks=[(name,typ)]
    # rest begins possibly with model then numbers
    # numbers thermal gross net
    nums=re.search(r'(\d{2,5})\s+(\d{1,5})\s+(\d{1,5})\s+[A-Za-z]',rest)
    if typ not in types:
        # name may contain 2+ spaces? skip
        continue
    ds=[(int(a),int(b)) for a,b in date.findall(rest)]
    if not nums or not ds: continue
    rows.append(dict(tab=cur,cc=cc,id=num,name=name.strip(),type=typ,thermal=int(nums.group(1)),gross=int(nums.group(2)),net=int(nums.group(3)),dates=ds,line=i))
print(len(rows),collections.Counter(r['tab'] for r in rows))
json.dump(rows,open(RAW+'rds2_rows.json','w'))
print(collections.Counter(r['type'] for r in rows))
