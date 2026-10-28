"""Task 2.x oil-and-gas driver series -> data/activity/oil_gas_drivers.csv
  oil_sands_ore_processed_t        CAN, t of mined oil sands ore processed, 1967-2025
  us_wells_drilled_horizontal      USA, wells drilled (horizontal), 1980-2025
  us_wells_drilled_vertical        USA, wells drilled (vertical trajectory), 1949-2025
  gas_flared_m3                    countries 2012-2025 (GGFR satellite), XWL 1950-2025 (GGFR 2012-25; back-cast from flaring CO2 before 2012)
  gas_flared_reported_m3           countries and XWL 1980-2017, as reported to EIA (vented and flared), a different basis
  ngl_production_m3                natural gas plant liquids, countries 1980-2025 (USA 1949-2025), XWL 1950-2025
  unit_value_{oil,gas,ngl}_usd_per_m3   nominal USD per m3 of crude oil, dry gas and NGL, for the D6 allocation
Inputs: research/activity/raw/task2x/ (made by fetch_task2x.py) and the raw files of the Task 1.9 builders.
Run: python3 build_og2.py [--write]
"""
import os,sys,csv,math,collections; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from lib import *
from common import *
import openpyxl,pandas as pd
O=Out('oil_gas_drivers'); CTY=countries(); T=RAW+'task2x/'
BBL=0.158987294928; DAYS=365.25; KCF=28.316847; GAL=264.172052
def mer(t,msn):
    d={}
    for r in csv.DictReader(open(T+'mer_%s.csv'%t)):
        if r['MSN']==msn and r['YYYYMM'].endswith('13'):
            try: d[int(r['YYYYMM'][:4])]=float(r['Value'])
            except ValueError: pass
    return d
def rss(*x): return math.sqrt(sum(a*a for a in x))
def N(head,tail): return head+'||'+tail
# =============================================================================================== 1. oil sands ore processed
ore=[(int(r['year']),float(r['ore_processed_t'])) for r in csv.DictReader(open(T+'st39_ore_processed_t.csv'))]
chart={int(r['year']):float(r['mined_bitumen_1e3_m3_per_d'])*1e3*DAYS for r in csv.DictReader(open(T+'st98_2015_fig6_mined_bitumen_kM3d.csv'))}   # m3/a
sc=collections.defaultdict(float)
for r in csv.DictReader(open(T+'statcan_25100063_alberta_mined_bitumen_m3.csv')): sc[int(r['REF_DATE'][:4])]+=float(r['VALUE'])
sc={y:v for y,v in sc.items() if y<=2025}
ratios=[t/sc[y] for y,t in ore]; RATIO=sum(ratios)/len(ratios)     # t ore per m3 of mined bitumen
assert abs(dict(ore)[2024]-1019.4e6)<0.2e6      # S0326 anchor
for y,t in ore: O.add('oil_sands_ore_processed_t',y,'CAN',t*0.98,t,t*1.02,'t','measured','S1620;S0326',
    N('AER ST39 mineable oil sands plant statistics: sum of the annual ore processed over all mines.','Sum of the "Proc" (oil sands processed, tonnes) annual totals of the eight mines and plants in the AER ST39 December supplement of the year. The 2024 total, 1,019.4 Mt, equals the AER/AGS INF 157 figure (S0326). Band +-2% assumed (operator-reported, rounding and mine-to-plant timing).'))
b2015=(chart[2014]+sc[2016])/2
bitumen=dict(chart); bitumen[2015]=b2015; bitumen[2016]=sc[2016]
for y in range(1972,2017):
    c=bitumen[y]*RATIO; rr=rss(0.05 if y<=2014 else 0.03,0.20) if y!=2015 else rss(0.10,0.20)
    bas='modelled'
    src='S1621;S0326' if y<=2014 else 'S1622;S1620'
    O.add('oil_sands_ore_processed_t',y,'CAN',c*(1-rr),c,c*(1+rr),'t',bas,src,
      N('Mined bitumen volume x %.2f t of ore per m3 (mean 2017-25 ratio of AER ST39 ore to StatCan Alberta mined bitumen).'%RATIO,
        'Mined bitumen: AER ST98-2015 Figure 6 (1972-2014, bar heights read from the vector graphic and calibrated to 165.0 thousand m3/d in 2014), 2015 interpolated, 2016 Statistics Canada 25-10-0063-01 (Alberta). Ore-to-bitumen ratio %.2f t/m3 is the 2017-25 mean (range %.2f-%.2f; ore grade about 10%% bitumen by mass at about 1.0 t/m3); earlier grades may differ, so the band is +-20%% (assumed) combined in quadrature with +-5%% for the chart reading.'%(RATIO,min(ratios),max(ratios))))
ramp=lambda y:2.0+(10.79-2.0)*(y-1967)/5.0   # 1e3 m3/d, linear from 1967 start-up to the first chart value (1972)
for y in range(1967,1972):
    c=ramp(y)*1e3*DAYS*RATIO
    O.add('oil_sands_ore_processed_t',y,'CAN',c*0.5,c,c*1.5,'t','extrapolated','S1621;S0326',
      N('Linear ramp from the 1967 start of the first mine to the 1972 chart value, x ore ratio.','No annual data found before 1972: mined bitumen assumed to rise linearly from 2.0 thousand m3/d (1967, first partial year; analyst assumption) to the 10.79 thousand m3/d read from ST98-2015 Figure 6 for 1972, converted with the %.2f t/m3 ratio. Band -50%%/+50%% assumed.'%RATIO))
# =============================================================================================== 2. US wells drilled
HR=mer('T05.02','HRTWPUS'); VT=mer('T05.02','VTTWPUS'); TOT=mer('T05.02','OGTWPUS')
RH=mer('T05.01','OGHRPUS'); RD=mer('T05.01','OGDRPUS')
for y in range(1949,2026):
    if y in VT:
        v=VT[y]; nt=N('EIA MER Table 5.2: crude oil, natural gas and dry wells drilled, vertical trajectory.','EIA Monthly Energy Review Table 5.2 (series VTTWPUS); "vertical" is EIA\'s category (the horizontal and directional wells are reported together). Band +-5% assumed (survey compilation).')
    else:
        v=TOT[y]; nt=N('Before 1976 EIA does not split wells by trajectory: total wells drilled, all taken as vertical.','EIA Monthly Energy Review Table 5.2 (series OGTWPUS, crude oil, natural gas and dry wells drilled). Directional wells before 1976 are not separated and are small; the same total is in us_wells_drilled_total (to 2010) of oil_gas.csv. Band +-5% assumed.')
    O.add('us_wells_drilled_vertical',y,'USA',v*0.95,v,v*1.05,'1','compiled','S1623',nt)
for y in range(1980,2026):
    hr=HR[y]
    if y>=1991: sh=RH[y]/(RH[y]+RD[y]); bas='modelled'; lo,hi=(0.5,1.5) if y<2010 else (0.8,1.1); nt=N('EIA horizontal-and-directional wells x rig share horizontal/(horizontal+directional).','EIA Monthly Energy Review Table 5.2 reports wells drilled with horizontal and directional trajectory together (series HRTWPUS). The horizontal part is estimated with the annual average rotary-rig counts of Table 5.1 (OGHRPUS and OGDRPUS): share horizontal/(horizontal + directional) is 0.41 in 1991 and 0.93 in 2019. Rig shares overstate well shares when horizontal wells take longer to drill, so the central value may be high: band %s (assumed), capped at the combined count. Check: 75%% of new wells horizontal in 2019 (EIA Today in Energy, 2020).'%('-50%/+50% before 2010' if y<2010 else '-20%/+10% from 2010'))
    else: sh=0.217*max(y-1979,0)/11.0; bas='interpolated'; lo,hi=0.3,2.0; nt=N('Share of horizontal wells interpolated from 0 (1979) to 0.217 (1990).','1990 anchor: about 2% of new wells were horizontal (EIA Today in Energy 2020, 30,826 wells in Table 5.2, so 616 of 2,839 horizontal-and-directional wells, share 0.217); zero before 1980 (first commercial horizontal wells assumed); linear in between. Band -70%/+100% (assumed), capped at the combined count.')
    c=hr*sh; O.add('us_wells_drilled_horizontal',y,'USA',c*lo,c,min(c*hi,hr) if c>0 else 0.0,'1',bas,'S1623',nt)
# =============================================================================================== 3. flared gas
wb=openpyxl.load_workbook(T+'ggfr_2012_2025.xlsx',data_only=True); ws=wb['Flare volume']; rows=list(ws.iter_rows(values_only=True)); yrs=rows[0][1:]
names={r['name']:r['code'] for r in csv.DictReader(open(os.path.join(REPO,'data','reference','countries.csv')))}
names.update({'Bolivia':'BOL','Brunei':'BRN','Congo, Rep.':'COG','Dem Rep of the Congo':'COD','Iran':'IRN','Ivory Coast':'CIV','Palestinian Territory':'PSE','Russia':'RUS','South Korea':'KOR','Syria':'SYR','Tanzania':'TZA','Turkiye':'TUR','Venezuela':'VEN','Vietnam':'VNM'})
ggfr=collections.defaultdict(dict); wt=collections.defaultdict(float)
for r in rows[1:]:
    if not r[0]: continue
    c=names[r[0]]; assert c in CTY,r[0]
    for y,v in zip(yrs,r[1:]):
        if v is None: continue
        ggfr[c][y]=v*1e9; wt[y]+=v*1e9
GG=('Satellite estimate (VIIRS) of gas flared, World Bank GGFR 2012-2025 release; the 2012-2025 workbook revises the volumes of the June 2024 report (2023 world 153.5 bcm, report 148 bcm).||'
    'World Bank Global Gas Flaring Reduction Partnership, "Flare volume and intensity estimates 2012-2025" (satellite-derived, calibrated to reported national and field volumes). The programme does not publish country uncertainties; the Elvidge et al. (2009) estimates carried +-2.11 bcm per country. Band +-15% for countries and +-8% for the world total, assumed.')
for c,d in ggfr.items():
    for y,v in d.items(): O.add('gas_flared_m3',y,c,v*0.85,v,v*1.15,'m3','compiled','S1625;S1626',GG)
for y,v in wt.items(): O.add('gas_flared_m3',y,'XWL',v*0.92,v,v*1.08,'m3','compiled','S1625;S1626',N('Sum of the GGFR country estimates.',GG.split('||')[1]))
co2={int(r['year']):float(r['flaring_co2_Mt']) for r in csv.DictReader(open(T+'owid_world_flaring_co2.csv'))}
kk=[wt[y]/(co2[y]*1e6) for y in range(2012,2024)]; K=sum(kk)/len(kk)      # m3 per t CO2
for y in range(1950,2012):
    c=K*co2[y]*1e6; lo,hi=(0.70,1.40) if y<1994 else (0.85,1.30)
    O.add('gas_flared_m3',y,'XWL',c*lo,c,c*hi,'m3','modelled','S1628;S1625;S1627;S1630',
      N('World flared gas back-cast from CO2 from flaring (Global Carbon Project) x %.0f m3 per t CO2 (GGFR 2012-23 mean).'%K,
        'Pre-GGFR basis: no satellite series exists before 1994 and the DMSP series of Elvidge et al. (2009: 1994-2008 within 140-170 bcm, 172 bcm in 2005, 139 bcm in 2008) is not available by country and year. The Global Carbon Project flaring CO2 (reported energy statistics) is converted with the volume/CO2 ratio of the overlap years 2012-2023 (%.0f-%.0f m3/t). Check: 2010 gives %.0f bcm against 134 bcm (World Bank 2011 press release); 2005 gives %.0f bcm against Elvidge 172 bcm, so the upper band is +30%% from 1994 and +40%% before (assumed). Country breakdown before 2012: see gas_flared_reported_m3.'%(min(kk),max(kk),K*co2[2010]*1e-3,K*co2[2005]*1e-3)))
fl=eia_geo('43','1','BCM')
for g,d in fl.items():
    c='XWL' if g=='WORL' else g
    if c!='XWL' and c not in CTY: continue
    for y,v in d.items():
        if y>2025: continue
        O.add('gas_flared_reported_m3',y,c,v*1e9*0.6,v*1e9,v*1e9*2.0,'m3','compiled','S0804',
          N('Vented and flared natural gas as reported to EIA (national submissions); not the satellite basis of gas_flared_m3.','EIA International Energy Statistics, "Vented and flared natural gas production" (BCM), 1980-2017. Reported volumes differ from the GGFR satellite estimates by factors of 0.2 to 3 in 2012-15 (Algeria and Iraq are much higher in GGFR, Nigeria and Indonesia lower), and include venting. Band -40%/+100% assumed.'))
# =============================================================================================== 4. NGL production
ngl=eia_geo('58','1','TBPD'); NGLUS=mer('T03.01','NLPRPUS')
vol=lambda kbd:kbd*1e3*BBL*DAYS
NG='EIA International Energy Statistics, natural gas plant liquids production (thousand b/d x 365.25 x 0.158987 m3/bbl).'
for g,d in ngl.items():
    if g in('WORL','USA') or g not in CTY: continue
    for y,v in d.items():
        if y<=2025 and v is not None: O.add('ngl_production_m3',y,g,vol(v)*0.9,vol(v),vol(v)*1.1,'m3','measured','S0804',N(NG,'Country submissions collated by EIA; definitions of NGL differ between countries (some include condensate or refinery LPG). Band +-10% assumed.'))
for y,v in NGLUS.items(): O.add('ngl_production_m3',y,'USA',vol(v)*0.95,vol(v),vol(v)*1.05,'m3','measured','S1623;S0804',N('EIA MER Table 3.1 natural gas liquids production, thousand b/d x 365.25 x 0.158987.','US natural gas plant liquids from the Monthly Energy Review (1949-2025; identical to the EIA international series from 1980). Band +-5% assumed.'))
W=ngl['WORL']; gasW=owid('gas-production-by-country.csv','Gas'); gasU=owid('gas-production-by-country.csv','Gas','United States')
rr=[(vol(W[y])-vol(NGLUS[y]))/(gasW[y]-gasU[y]) for y in range(1980,1985)]; RR=sum(rr)/len(rr)
for y in range(1950,2026):
    if y in W:
        c=vol(W[y]); O.add('ngl_production_m3',y,'XWL',c*0.93,c,c*1.07,'m3','measured','S0804',N(NG,'World total of the EIA international series (sum of countries, incomplete before the mid-1980s for some producers). Band +-7% assumed.'))
    else:
        c=vol(NGLUS[y])+RR*(gasW[y]-gasU[y]); u=vol(NGLUS[y])
        O.add('ngl_production_m3',y,'XWL',u+(c-u)*0.6,c,u+(c-u)*1.4,'m3','modelled','S1623;S0806;S0804',
          N('Before 1980: US NGL (EIA MER) plus rest-of-world NGL = %.3g m3 per TWh of rest-of-world gas production.'%RR,
            'EIA does not publish world NGL before 1980. Rest-of-world NGL is the OWID/Energy Institute gas production (TWh, S0806) minus the USA, times the ratio of rest-of-world NGL volume to gas energy observed in 1980-84 (%.3g m3/TWh). The ratio varied over time with gas composition and processing; band -40%%/+40%% on the rest-of-world part, assumed.'%RR))
# =============================================================================================== 5. unit values (nominal USD per m3)
crude=owid('task2x/owid_crude.csv','Oil price - Crude prices since 1861')     # USD per m3, world
cr_us={y:v/BBL for y,v in mer('T09.01','CODPUUS').items()}
gas_us={y:v/KCF for y,v in mer('T09.10','NGWPUUS').items()}
hh={int(r['Year']):float(r['Gas price']) for r in csv.DictReader(open(T+'owid_gas_prices.csv')) if r['Entity']=='US Henry Hub'}   # USD/MWh
hh_m3={y:v/3.41214*1.036/KCF for y,v in hh.items()}                  # USD/m3 (1 MWh = 3.41214 MMBtu; 1.036 MMBtu per thousand ft3)
QW=[gas_us[y]/hh_m3[y] for y in range(2005,2013)]; QW=sum(QW)/len(QW)
gas_mod={y:hh_m3[y]*QW for y in range(2013,2026)}
x=pd.read_excel(T+'eia_propane_mb.xls',sheet_name='Data 1',header=None,skiprows=3)
prop={int(pd.Timestamp(a).year):float(b)*GAL for a,b in zip(x[0],x[1])}     # USD/m3
PR=[prop[y]/crude[y] for y in prop if y in crude]; PRC=sum(PR)/len(PR)
for y in range(1950,2026):
    c=crude[y]; O.add('unit_value_oil_usd_per_m3',y,'XWL',c*0.9,c,c*1.1,'USD/m3','compiled','S1629',N('World crude oil price, nominal USD per m3 (Our World in Data, Energy Institute), D6 oil unit value.','Annual average crude price (nominal US dollars) converted by Our World in Data to USD per m3 (about 159 USD/m3 per USD 25.3 per barrel is not used: the published value is used as is). Realised wellhead values differ by grade and region: band +-10% assumed.'))
    if y in cr_us:
        v=cr_us[y]; O.add('unit_value_oil_usd_per_m3',y,'USA',v*0.9,v,v*1.1,'USD/m3','compiled','S1623',N('US crude oil domestic first purchase price (EIA MER Table 9.1), USD per barrel / 0.158987.','Nominal US dollars. Band +-10% assumed.'))
    if y in gas_us:
        v=gas_us[y]; O.add('unit_value_gas_usd_per_m3',y,'USA',v*0.9,v,v*1.1,'USD/m3','compiled','S1623',N('US natural gas wellhead price (EIA MER Table 9.10), USD per thousand ft3 / 28.317.','Nominal US dollars per m3 of dry gas. Band +-10% assumed.'))
        O.add('unit_value_gas_usd_per_m3',y,'XWL',v*0.5,v,v*3.0,'USD/m3','extrapolated','S1623',N('World gas unit value taken as the US wellhead price (proxy); band 0.5-3 times.','No world gas price series exists for 1950-1988; the US wellhead price is used for every year as the only long series. Regional prices ranged from well below it (Russia, Middle East domestic) to about five times above it (European and Asian imports in 2022). Band x0.5 to x3.0 assumed; refine with Henry Hub, NBP and TTF (our world in data, from 1989) if a regional allocation is needed.'))
    if y in gas_mod:
        v=gas_mod[y]; O.add('unit_value_gas_usd_per_m3',y,'USA',v*0.85,v,v*1.15,'USD/m3','modelled','S1631;S1623',N('US wellhead price continued after the EIA series ended (2012) from Henry Hub x %.2f.'%QW,'EIA discontinued the wellhead price series after 2012. Henry Hub (Our World in Data, USD/MWh, converted with 3.41214 MMBtu/MWh and 1.036 MMBtu per thousand ft3) times the mean wellhead/Henry Hub ratio of 2005-12 (%.2f). Band +-15%% assumed.'%QW))
        O.add('unit_value_gas_usd_per_m3',y,'XWL',v*0.5,v,v*3.0,'USD/m3','extrapolated','S1631;S1623',N('World gas unit value taken as the US wellhead price (proxy); band 0.5-3 times.','See the 1950 row.'))
    npc=prop[y]*0.7 if y in prop else crude[y]*PRC*0.7
    if y in prop: lo,hi,bas,nt=0.64,1.43,'modelled',N('NGL basket value taken as 0.7 x the Mont Belvieu propane spot price (EIA).','NGL are a mix of ethane, propane, butanes and natural gasoline; only the propane price (EIA, USD per gallon x 264.17) is published as a long series. The basket is assumed to be worth 0.7 of propane (ethane is much cheaper, natural gasoline dearer); band 0.45-1.0 of propane (assumed).')
    else: lo,hi,bas,nt=0.45,1.6,'extrapolated',N('NGL basket value before 1992: 0.7 x propane/crude price ratio (%.3f, 1992-2025 mean) x world crude price.'%PRC,'No NGL price series before 1992. The mean 1992-2025 ratio of the Mont Belvieu propane price to the world crude price per m3 (%.3f) is applied to the crude price and the 0.7 basket factor (assumed); band x0.45 to x1.6 (assumed).'%PRC)
    O.add('unit_value_ngl_usd_per_m3',y,'XWL',npc*lo,npc,npc*hi,'USD/m3',bas,'S1624;S1629',nt)
print('RATIO t/m3',round(RATIO,2),'K m3/tCO2',round(K,1),'NGL ratio',RR,'propane/crude',round(PRC,3))
O.write()
