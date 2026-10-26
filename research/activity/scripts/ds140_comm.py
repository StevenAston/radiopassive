import os,sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from lib import *
from ds140 import *
# key: (workbook, sheet, source_id, production series, world mult, US production col, apparent-consumption series, cons col, price tag, commodity label)
WB={'aluminum':('ds140-aluminum-2021.xlsx','S0821'),'bauxite':('ds140-bauxite-alumina-2021.xlsx','S0822'),'cadmium':('ds140-cadmium-2022.xlsx','S0823'),'cement':('ds140-cement-2021.xlsx','S0824'),'chromium':('ds140-chromium-2022.xlsx','S0825'),'copper':('ds140-copper-2020.xlsx','S0826'),'gallium':('ds140-gallium-2021.xlsx','S0827'),'gold':('ds140-gold-2022.xlsx','S0828'),'indium':('ds140-indium-2022.xlsx','S0829'),'iron_ore':('ds140-iron_ore-2021.xlsx','S0830'),'iron_steel':('ds140-iron-steel-2021.xlsx','S0831'),'lead':('ds140-lead-2021.xlsx','S0832'),'molybdenum':('ds140-molybdenum-2022.xlsx','S0833'),'nickel':('ds140-nickel-2019.xlsx','S0834'),'rare_earths':('ds140-rare-earths-2020.xlsx','S0835'),'selenium':('ds140-selenium-2020.xlsx','S0836'),'silicon':('ds140-silicon-2022.xlsx','S0837'),'silver':('ds140-silver-2021.xlsx','S0838'),'tellurium':('ds140-tellurium-2020.xlsx','S0839'),'tin':('ds140-tin-2021.xlsx','S0840'),'zinc':('ds140-zinc-2022.xlsx','S0841'),'zirconium':('ds140-zirconium-2021.xlsx','S0842'),'thorium':('ds140-thorium-2021.xlsx','S0843'),'peat':('ds140-peat-2021.xlsx','S0844'),'phosphate':('ds140-phosphate-2022.xlsx','S0845')}
# (wbkey, sheet, series, mult, US prod col, cons series, cons col, price label or None, desc)
SP=[
('aluminum','01_Aluminum','prod_aluminium',1.0,'Primary production','cons_apparent_aluminium','Apparent consumption','aluminium','primary aluminium'),
('bauxite','01_Bauxite','prod_bauxite',1.0,'Production','cons_apparent_bauxite','Apparent consumption',None,'bauxite, gross weight'),
('bauxite','02_Alumina','prod_alumina',1.0,'Production','cons_apparent_alumina','Apparent consumption',None,'alumina, gross weight'),
('cadmium','01_Cadmium','prod_cadmium',1.5,'Production','cons_apparent_cadmium','Apparent consumption',None,'cadmium metal'),
('cement','01_Cement','prod_cement',1.5,'Production','cons_apparent_cement','Apparent consumption','cement','hydraulic cement'),
('chromium','01_Chromium','prod_chromium',1.0,'Primary production','cons_apparent_chromium','Apparent consumption',None,'chromium content'),
('copper','01_Copper','prod_copper',1.0,'Primary production','cons_apparent_copper','Apparent consumption','copper','copper content (mine output)'),
('gallium','01_Gallium','prod_gallium_refined',2.0,'Production','cons_apparent_gallium','Apparent consumption',None,'gallium content'),
('gold','01_Gold','prod_gold',1.0,'Primary production','cons_reported_gold','Reported consumption','gold','gold content (mine output)'),
('indium','01_Indium','prod_indium',1.5,'Production','cons_apparent_indium','Apparent consumption',None,'indium content'),
('iron_ore','01_Iron ore','prod_iron_ore',1.0,'Production','cons_apparent_iron_ore','Apparent consumption','iron_ore','iron ore, usable ore gross weight'),
('iron_steel','01_Pig Iron','prod_pig_iron',1.0,'Primary production','cons_apparent_pig_iron','Apparent consumption',None,'pig iron'),
('iron_steel','02_Direct Reduced Iron','prod_dri',1.0,'Production','cons_apparent_dri','Apparent consumption',None,'direct reduced iron'),
('iron_steel','03_Steel','prod_steel',1.0,'Raw steel production','cons_apparent_steel','Apparent consumption','steel','crude (raw) steel'),
('lead','01_Lead','prod_lead',1.0,'Primary production','cons_apparent_lead','Apparent consumption','lead','lead content (mine output)'),
('molybdenum','01_Molybdenum','prod_molybdenum',1.0,'Production','cons_apparent_molybdenum','Apparent consumption','molybdenum','molybdenum content'),
('nickel','01_Nickel','prod_nickel',1.0,'Primary production','cons_apparent_nickel','Apparent consumption','nickel','nickel content (mine output)'),
('rare_earths','01_Rare earths','prod_ree_oxide',2.0,'Production','cons_apparent_ree_oxide','Apparent consumption','rare_earths','rare-earth oxide equivalent'),
('selenium','01_Selenium','prod_selenium',2.0,'Primary production','cons_apparent_selenium','Apparent consumption',None,'selenium content'),
('silicon','01_Silicon','prod_silicon_mg',2.0,'Production','cons_apparent_silicon','Apparent consumption',None,'silicon content (metal plus ferrosilicon)'),
('silver','01_Silver','prod_silver',1.0,'Mine production','cons_apparent_silver','Apparent consumption','silver','silver content (mine output)'),
('tellurium','01_Tellurium','prod_tellurium',3.0,'Production','cons_apparent_tellurium','Apparent consumption',None,'tellurium content'),
('tin','01_Tin','prod_tin',1.0,'Primary production','cons_apparent_tin','Apparent consumption',None,'tin content (mine output)'),
('zinc','01_Zinc','prod_zinc',1.0,'Primary production','cons_apparent_zinc','Apparent consumption','zinc','zinc content (mine output)'),
('zirconium','01_Zirconium','prod_zirconium',2.0,'Production','cons_apparent_zirconium','Apparent consumption',None,'zirconium mineral concentrates, gross weight'),
('thorium','01_Thorium','prod_thorium',3.0,'Production','cons_apparent_thorium','Apparent consumption','thorium','thorium oxide content'),
('peat','01_Peat','prod_peat',2.0,'Production','cons_apparent_peat','Apparent consumption',None,'peat, gross weight (all uses incl. horticulture)'),
('phosphate','01_Phosphate rock','prod_phosphate_rock',1.0,'Production','cons_apparent_phosphate_rock','Apparent consumption','phosphate_rock','phosphate rock, gross weight'),
]
USNAME={'prod_zinc':'prod_zinc_primary','prod_lead':'prod_lead_primary','prod_tin':'prod_tin_primary','prod_selenium':'prod_selenium_primary'}
def band(y,mult,country):
    b=0.15 if y<1950 else 0.08 if y<1990 else 0.05
    b*=mult*(1 if country=='XWL' else 1.2)
    return min(b,0.6)
def find(h,name):
    for c in h:
        if c.lower()==name.lower(): return c
    raise KeyError(name)
def add_ds140(O):
    stats={}
    for wbk,sh,ser,mult,pcol,cser,ccol,plab,desc in SP:
        wb,sid=WB[wbk]; h,d,_=load(wb,sh); md=mod(wb,sh)
        wc=[c for c in h if c.lower().startswith('world')][0]
        pc=find(h,pcol); cc=find(h,ccol)
        cite='USGS DS140 %s, sheet %s (last modified %s); read from the mirror of the USGS S3 bucket.'%(wb[:-5],sh,md)
        nw=nu=nc=0
        for y in sorted(d):
            if y>2025: continue
            r=d[y]
            v=r[wc]
            if v is not None and v>0:
                b=band(y,mult,'XWL')
                O.add(ser,y,'XWL',*bands(v,b),'t','compiled',sid,'%s World production of %s as compiled by USGS (primary source; replaces the OWID-derived row where both exist). Bands assumed (approx. 5th-95th percentile): +-15%% before 1950, +-8%% 1950-1989, +-5%% from 1990, x%.1f for data quality.'%(cite,desc,mult)); nw+=1
            v=r[pc]
            if v is not None:
                b=band(y,mult,'USA')
                O.add(USNAME.get(ser,ser),y,'USA',*bands(v,b),'t','measured',sid,'%s US production (column "%s")%s; withheld (W) years omitted. Bands assumed: +-18%% before 1950, +-10%% 1950-1989, +-6%% from 1990, x%.1f.'%(cite,pcol,' - primary smelter/refinery output from ore, NOT mine output, hence the _primary series name (the OWID US mine-output series is a different quantity: DS140/OWID ratio 0.1-1.8)' if ser in USNAME else '',mult)); nu+=1
            v=r[cc]
            if v is not None:
                b=band(y,mult,'USA')*1.3
                b=min(b,0.6)
                O.add(cser,y,'USA',*bands(v,b),'t','compiled',sid,'%s US %s (column "%s"), calculated by USGS as production plus net imports plus stock change (not measured consumption, except gold: reported consumption). Bands assumed: wider than production by x1.3.'%(cite,'apparent consumption' if 'apparent' in cser else 'reported consumption',ccol)); nc+=1
        stats[ser]=(nw,nu,nc)
    # nickel world plant production
    h,d,_=load(WB['nickel'][0],'02_World plant production')
    for y,r in d.items():
        v=r['World plant production']
        if v: O.add('prod_nickel_plant',y,'XWL',*bands(v,band(y,1.0,'XWL')),'t','compiled','S0834','USGS DS140 ds140-nickel-2019, sheet 02_World plant production: world nickel plant (smelter/refinery) production, 1970-2019. Bands assumed +-8%/+-5%.')
    return stats
