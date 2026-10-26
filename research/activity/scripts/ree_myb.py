import pandas as pd,re,warnings
warnings.filterwarnings('ignore')
import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from lib import MIRROR
if MIRROR is None: raise SystemExit('USGS mirror root required: pass --mirror /path/to/usgs.140 (or set USGS_MIRROR)')
U=MIRROR+'files/'
MYB=[('myb2003','mineral-pubs/rare-earth/rareemyb03.xls','Table06',2003),('myb2008','mineral-pubs/rare-earth/myb1-2008-raree.xls','T6',2008),('myb2013','mineral-pubs/rare-earth/myb1-2013-raree.xls','T6',2013),('myb2018','s3fs-public/atoms/files/myb1-2018-raree-adv.xlsx','T8',2018),('myb2022','s3fs-public/media/files/myb1-2022-raree-ert.xlsx','T8',2022)]
def num(v):
    if v is None or (isinstance(v,float) and v!=v): return None
    s=str(v).strip().replace(',','')
    m=re.match(r'^(-?\d+(\.\d+)?)',s)
    if s in('--','-','NA','W') or not m: return None
    return float(m.group(1))
def parse(path,sheet,root=U):
    d=pd.read_excel(root+path,sheet_name=sheet,header=None)
    hr=None
    for i in range(len(d)):
        ys=[num(x) for x in d.iloc[i] if num(x) is not None and 1980<=num(x)<=2030 and re.fullmatch(r'\d{4}',str(x).strip().split('.')[0].replace('e',''))]
        if len(ys)>=3: hr=i; break
    cols={}
    for j,x in enumerate(d.iloc[hr]):
        s=str(x).strip().split('.')[0]
        if re.fullmatch(r'\d{4}[a-z]?',s): cols[j]=int(s[:4])
    out={}
    for i in range(hr+1,len(d)):
        name=str(d.iloc[i,0]).strip()
        if name in('nan',''): continue
        name=re.sub(r'\s*\d[\d, ]*$','',name).strip()
        if name.lower().startswith(('see footnote','e estimated','1 table','1estimated','revised','total','ee')) and not name.lower().startswith('total'): break
        row={}
        for j,y in cols.items():
            v=num(d.iloc[i,j]); 
            if v is not None: row[y]=v
        out[name]=(row)
    return out
if __name__=='__main__':
    for n,p,s,e in MYB:
        o=parse(p,s); print('==',n,sorted({y for r in o.values() for y in r}))
        for k,v in o.items(): print('  ',k,v)

import subprocess,collections
CM={'Australia':'AUS','Brazil':'BRA','China':'CHN','India':'IND','Malaysia':'MYS','Madagascar':'MDG','South Africa':'ZAF','Sri Lanka':'LKA','Thailand':'THA','United States':'USA','Vietnam':'VNM','Burma':'MMR','Burundi':'BDI','Zaire':'COD','Russia':'RUS','Commonwealth of Independent States':'RUS','U.S.S.R.':'RUS'}
def cname(n):
    n=re.sub(r'[\s,]+(e|r|e,)?$','',n.strip())
    n=re.sub(r'(?<=[a-z])e,?$','',n) if n.endswith(('Australiae','Brazile','Burmae','Burundie','Indiae','Indiae,','Madagascare','Malaysiae','Thailande','Thailande,','United Statese','Vietname','Vietname,')) else n
    n=n.rstrip(',')
    for k in CM:
        if n.startswith(k): return CM[k]
    return None
def parse_pdf(path,start,nyears,ystart):
    txt=subprocess.run(['pdftotext','-layout',U+path,'-'],capture_output=True,text=True).stdout.split('\n')
    i=[k for k,l in enumerate(txt) if 'WORLD MINE PRODUCTION' in l][-1 if 'rare-earth/740499' in path else 0]
    out=collections.defaultdict(dict); tot={}
    for l in txt[i+4:i+30]:
        if l.startswith(('e/','1/')): break
        m=re.match(r'^\s*(.*?\S)\s{2,}(.*)$',l)
        if not m: continue
        name=re.sub(r'(\s+[erw]?\d?/)+$','',m.group(1)).strip(); rest=m.group(2)
        toks=re.findall(r'(\(\d/\)|--|[\d,]+)(?:\s+(?:r/|e/|\d/))*',rest)
        vals=[]
        for t in toks:
            if t=='--': vals.append(0.0)
            elif t.startswith('('): vals.append(None)
            else: vals.append(float(t.replace(',','')))
        if len(vals)!=nyears: continue
        if name.startswith('Total'):
            tot={ystart+k:v for k,v in enumerate(vals) if v is not None}
        else:
            c='MDG' if name in('Bastnasite','Monazite') else cname(name)
            if c:
                for k,v in enumerate(vals):
                    if v is not None: out[c][ystart+k]=out[c].get(ystart+k,0)+v
    return out,tot
def editions():
    """returns list of (edition label, source id, {country:{year:val}}, {year:total})"""
    E=[]
    o,t=parse_pdf('mineral-pubs/rare-earth/740494.pdf',0,5,1990); E.append(('myb1994','S0854',o,t))
    o,t=parse_pdf('mineral-pubs/rare-earth/740499.pdf',0,5,1995); E.append(('myb1999','S0855',o,t))
    for (n,p,s,e),sid in zip(MYB,['S0856','S0857','S0858','S0859','S0860']):
        d=parse(p,s); t={}
        oo=collections.defaultdict(dict)
        for k,v in d.items():
            if k=='Total': t=v; continue
            c=cname(k)
            if c: 
                for y,x in v.items(): oo[c][y]=oo[c].get(y,0)+x
        E.append((n,sid,oo,t))
    return E
if __name__=='__main__':
    for n,sid,o,t in editions():
        print(n,sid,sorted(t.items())[:2],{c:len(v) for c,v in o.items()})

def add_ree(O,log=None):
    E=editions(); best={}; hist=collections.defaultdict(list)
    for n,sid,o,t in E:
        for c,v in o.items():
            for y,x in v.items():
                if (c,y) in best and best[(c,y)][0]!=x: hist[(c,y)].append((best[(c,y)][1],best[(c,y)][0]))
                best[(c,y)]=(x,n,sid)
    names={'myb1994':'Minerals Yearbook 1994 (Table 8)','myb1999':'Minerals Yearbook 1999 (Table 6)','myb2003':'Minerals Yearbook 2003 (Table 6)','myb2008':'Minerals Yearbook 2008 (Table 6)','myb2013':'Minerals Yearbook 2013 (Table 6)','myb2018':'Minerals Yearbook 2018 advance release (Table 8)','myb2022':'Minerals Yearbook 2022 (Table 8)'}
    n_add=0
    for (c,y),(x,n,sid) in sorted(best.items()):
        if c=='USA' and O.has('prod_ree_oxide',y,'USA'): continue
        cc_=c
        if c=='RUS' and y<=1991 and n=='myb1994': cc_='SUN'
        rel=0.40 if (c=='RUS' and y<=2008) else 0.15
        h=hist.get((c,y))
        extra=' Earlier edition value(s) superseded: %s.'%'; '.join('%s %g'%(names[a].split(' (')[0],b) for a,b in h) if h else ''
        cis=' Table label is U.S.S.R./Commonwealth of Independent States; USGS could not split the successor states, so the aggregate is booked to RUS (mostly Russian output, Kazakhstan, Kyrgyzstan, Ukraine, Uzbekistan uncertain); band widened to +-40%.' if (c=='RUS' and y<=2008) else ''
        O.add('prod_ree_oxide',y,cc_,x*(1-rel),x,x*(1+rel),'t','compiled',sid,'USGS %s: world mine production of rare earths by country, REO equivalent; most values are USGS estimates rounded to three significant digits. Bands assumed (approx. 5th-95th percentile): +-%d%%.%s%s Read from the mirror of the USGS S3 bucket.'%(names[n],rel*100,cis,extra)); n_add+=1
        if h and log is not None: log.append((c,y,n,x,h))
    return n_add,E
