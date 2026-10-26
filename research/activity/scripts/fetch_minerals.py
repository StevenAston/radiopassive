import urllib.parse,os,sys,time,subprocess
import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from lib import RAW as _R
RAW=_R+'min/'
os.makedirs(RAW,exist_ok=True)
items=[('Aluminum','Smelter'),('Bauxite','Mine'),('Cement','Processing'),('Copper','Mine'),('Copper','Refinery'),('Gallium','Processing'),('Gallium','Refinery'),('Iron ore','Mine, crude ore'),('Iron ore','Mine, iron content'),('Iron','Smelter, pig iron'),('Lead','Mine'),('Lead','Refinery'),('Nickel','Mine'),('Nickel','Processing'),('Rare earths','Mine'),('Selenium','Refinery'),('Silicon','Processing'),('Silver','Mine'),('Steel','Processing, crude'),('Tin','Mine'),('Tin','Smelter'),('Zinc','Mine'),('Zinc','Refinery'),('Zirconium and hafnium','Mine'),('Cadmium','Refinery'),('Coal','Mine'),('Uranium','Mine'),('Chromium','Mine'),('Molybdenum','Mine'),('Cobalt','Mine')]
for m,t in items:
    q=urllib.parse.urlencode({'tab':'table','facet':'none','Mineral':m,'Metric':'Production','Type':t,'Share of global':'false','country':'~OWID_WRL'},quote_via=urllib.parse.quote)
    u='https://ourworldindata.org/explorers/minerals.csv?'+q
    fn=RAW+(m+'__'+t).replace(' ','_').replace(',','')+'.csv'
    r=subprocess.run(['curl','-sS','-m','90','-L','-o',fn,'-w','%{http_code} %{size_download}',u],capture_output=True,text=True)
    print(m,t,r.stdout,r.stderr[:100])
    time.sleep(0.5)
