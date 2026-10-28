"""Fetch and reduce the public inputs for the Task 2.x activity series (build_nuc2.py, build_og2.py).

  python3 fetch_task2x.py [--cache DIR]

Writes small reduced files into research/activity/raw/task2x/ (the originals are not stored).
--cache DIR: reuse already-downloaded originals from DIR (same file names as the downloads below).
Needs: curl, pdftotext, pdftocairo (poppler), openpyxl is only used by the builders.
Inputs (all open access):
  EIA Monthly Energy Review tables T03.01, T05.01, T05.02, T09.01, T09.10 (csv.php?tbl=...)
  Statistics Canada table 25-10-0063-01 (zip) -> Alberta mined crude bitumen, m3, monthly
  AER ST39 (2017-2025 editions) -> ore processed (sum of 'Proc' rows, December annual column)
  AER ST98-2015 Figure 6 (page 30) -> mined bitumen, 10^3 m3/d, 1972-2014 (vector bars, calibrated to 2014)
  World Bank GGFR Flare-volume-and-intensity-estimates-2012-2025.xlsx (copied unchanged)
  OWID/GCB owid-co2-data.csv -> World flaring_co2 (Mt CO2)
  OWID crude-oil-prices.csv and natural-gas-prices.csv (copied unchanged); EIA Mont Belvieu propane spot (xls, copied unchanged)
"""
import os,sys,re,csv,json,subprocess,shutil,zipfile,argparse,collections,tempfile
HERE=os.path.dirname(os.path.abspath(__file__))
REPO=os.path.abspath(os.path.join(HERE,'..','..','..'))
OUT=os.path.join(REPO,'research','activity','raw','task2x')+'/'
ap=argparse.ArgumentParser(); ap.add_argument('--cache'); A=ap.parse_args()
os.makedirs(OUT,exist_ok=True)
TMP=tempfile.mkdtemp(prefix='task2x_')
def get(url,name):
    if A.cache and os.path.exists(os.path.join(A.cache,name)): return os.path.join(A.cache,name)
    p=os.path.join(TMP,name)
    subprocess.run(['curl','-sS','-L','-m','300','-o',p,url],check=True)
    return p
# --- EIA MER tables (unchanged copies)
for t in ('T03.01','T05.01','T05.02','T09.01','T09.10'):
    shutil.copy(get('https://www.eia.gov/totalenergy/data/browser/csv.php?tbl='+t,'mer_%s.csv'%t),OUT+'mer_%s.csv'%t)
# --- GGFR, OWID, propane (unchanged)
shutil.copy(get('https://thedocs.worldbank.org/en/doc/b34e0c054bb3fe3695e70154c28eef3f-0400072026/related/Flare-volume-and-intensity-estimates-2012-2025.xlsx','ggfr_2012_2025.xlsx'),OUT+'ggfr_2012_2025.xlsx')
shutil.copy(get('https://ourworldindata.org/grapher/crude-oil-prices.csv?v=1&csvType=full&useColumnShortNames=false','owid_crude.csv'),OUT+'owid_crude.csv')
shutil.copy(get('https://ourworldindata.org/grapher/natural-gas-prices.csv?v=1&csvType=full&useColumnShortNames=false','owid_gas_prices.csv'),OUT+'owid_gas_prices.csv')
shutil.copy(get('https://www.eia.gov/dnav/pet/hist_xls/EER_EPLLPA_PF4_Y44MB_DPGa.xls','eia_propane_mb.xls'),OUT+'eia_propane_mb.xls')
# --- OWID CO2: world flaring
p=get('https://nyc3.digitaloceanspaces.com/owid-public/data/co2/owid-co2-data.csv','owid_co2.csv')
with open(OUT+'owid_world_flaring_co2.csv','w',newline='') as f:
    w=csv.writer(f,lineterminator='\n'); w.writerow(['year','flaring_co2_Mt'])
    for r in csv.DictReader(open(p,encoding='utf-8')):
        if r['country']=='World' and r['flaring_co2']!='': w.writerow([r['year'],r['flaring_co2']])
# --- StatCan: Alberta mined crude bitumen, m3, monthly
z=get('https://www150.statcan.gc.ca/n1/tbl/csv/25100063-eng.zip','sc.zip')
with zipfile.ZipFile(z) as zz: raw=zz.read('25100063.csv').decode('utf-8-sig').splitlines()
with open(OUT+'statcan_25100063_alberta_mined_bitumen_m3.csv','w',newline='') as f:
    w=csv.writer(f,lineterminator='\n'); w.writerow(['REF_DATE','GEO','Supply and disposition','UOM','VALUE'])
    for r in csv.DictReader(raw):
        if r['GEO']=='Alberta' and r['Supply and disposition']=='Mined crude bitumen production' and r['UOM']=='Cubic metres' and r['VALUE']:
            w.writerow([r['REF_DATE'],r['GEO'],r['Supply and disposition'],r['UOM'],r['VALUE']])
# --- AER ST39: ore processed (t) = sum of the annual column of every 'Proc' row
with open(OUT+'st39_ore_processed_t.csv','w',newline='') as f:
    w=csv.writer(f,lineterminator='\n'); w.writerow(['year','ore_processed_t','n_rows'])
    for y in range(2017,2026):
        pdf=get('https://static.aer.ca/prd/documents/sts/ST39-%d.pdf'%y,'ST39-%d.pdf'%y)
        txt=subprocess.run(['pdftotext','-layout',pdf,'-'],capture_output=True,text=True).stdout.split('\n')
        t=0.0; n=0
        for l in txt:
            if re.match(r'^\s*Proc\s+[\d,]',l):
                nums=re.findall(r'[\d,]+\.\d+',l); t+=float(nums[-1].replace(',','')); n+=1
        w.writerow([y,'%.1f'%t,n])
# --- AER ST98-2015 Figure 6 (page 30): mined bitumen bars (light fill), calibrated to 2014 = 165.0 10^3 m3/d
pdf=get('https://static.aer.ca/prd/documents/sts/ST98/ST98-2015.pdf','ST98-2015.pdf')
svg=os.path.join(TMP,'p30.svg'); subprocess.run(['pdftocairo','-svg','-f','30','-l','30',pdf,svg],check=True)
s=open(svg).read(); light=[]
for a in re.findall(r'<path ([^>]*?)/>',s):
    m=re.search(r'fill="rgb\(65\.09',a); d=re.search(r' d="([^"]*)"',a)
    if not m or not d: continue
    nums=[float(x) for x in re.findall(r'-?\d+\.?\d*',d.group(1))]; xs=nums[0::2]; ys=nums[1::2]
    if min(xs)>100: light.append((min(xs),min(ys),max(ys)))
light=[b for b in light if abs(b[2]-662.1758)<0.01]
h=[b[2]-b[1] for b in light]; k=165.0/h[-1]; yrs=range(2014-len(h)+1,2015)
with open(OUT+'st98_2015_fig6_mined_bitumen_kM3d.csv','w',newline='') as f:
    w=csv.writer(f,lineterminator='\n'); w.writerow(['year','mined_bitumen_1e3_m3_per_d'])
    for y,x in zip(yrs,h): w.writerow([y,'%.2f'%(x*k)])
shutil.rmtree(TMP)
print('done',sorted(os.listdir(OUT)))
