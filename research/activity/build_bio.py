import sys; sys.path.insert(0,'/tmp/claude-0/-home-claude/7f015155-d930-5c34-900b-ab275f11b117/scratchpad/task19/scripts')
from lib import *
from common import *
import csv,collections,math,pycountry
cc=countries()
def a3(m49):
    try: return pycountry.countries.get(numeric='%03d'%int(m49)).alpha_3
    except Exception: return None
# ---- FAO
FA={}
for r in csv.DictReader(open(RAW+'fao/x/Forestry_E_AreaCodes.csv')): FA[r['Area Code']]=(r['M49 Code'].lstrip("'"),r['Area'])
FSPEC={'351':'CHN','228':'SUN','51':'CSK','248':'YUG','186':'SCG','5000':'XWL'}
SKIPFAO={'41','96','128','214'}
def fao_code(ac):
    if ac in SKIPFAO: return None
    if ac in FSPEC: return FSPEC[ac] if FSPEC[ac] in cc or FSPEC[ac]=='XWL' else None
    c=a3(FA[ac][0]); return c if c in cc else None
fw={};ch={};chsum=collections.defaultdict(float);chn=collections.Counter()
def is_country(ac):
    if ac in SKIPFAO: return False
    if ac in('351','228','51','248','186','206'): return True
    return a3(FA[ac][0]) is not None
for r in csv.DictReader(open(RAW+'fao/x/Forestry_E_All_Data_(Normalized).csv',encoding='latin-1')):
    if r['Item Code'] in('1864','1630') and r['Element Code'] in('5510','5516'):
        if r['Item Code']=='1630' and r['Value']!='' and is_country(r['Area Code']):
            chsum[int(r['Year'])]+=float(r['Value']); chn[int(r['Year'])]+=1
        c=fao_code(r['Area Code'])
        if not c or r['Value']=='': continue
        (fw if r['Item Code']=='1864' else ch)[(c,int(r['Year']))]=(float(r['Value']),r['Flag'])
O=Out('biomass')
SF='S0846'; SC='S0848'
D_T=0.725; D_LO=0.625; D_HI=0.75; E_C=9.4; E_LO=7.2; E_HI=14.0
def qa(*r): return math.sqrt(sum(x*x for x in r))
for (c,y),(v,fl) in sorted(fw.items()):
    if y>2025: continue
    b=0.12 if (c=='XWL' or fl=='A') else 0.25
    note='FAOSTAT Forestry production, item 1864 Wood fuel (roundwood equivalent, solid volume, all uses of wood as fuel including wood converted to charcoal), flag %s (%s). Bands assumed: +-12%% for world and FAO "official" flag A, +-25%% for estimated/imputed flags.'%(fl,{'A':'official','E':'estimated','I':'imputed','X':'external','F':'forecast'}.get(fl,fl))
    O.add('wood_fuel_m3',y,c,*bands(v*1,b),'m3','compiled',SF,note) if False else None
    V=v*1.0
    O.add('wood_fuel_m3',y,c,V*(1-b),V,V*(1+b),'m3','compiled',SF,note)
    t=V*D_T
    O.add('wood_fuel_t',y,c,t*(1-qa(b,1-D_LO/D_T)),t,t*(1+qa(b,D_HI/D_T-1)),'t','modelled',SF+';'+SC,'Wood fuel mass = FAOSTAT m3 x 0.725 t/m3 (general fuelwood density, FAO/ITTO/UNECE/Eurostat Joint Forest Sector Questionnaire guidelines; range 0.625 coniferous to 0.75 non-coniferous; moisture basis not stated by the source, about air-dry). Bands combine the volume band and the density range in quadrature.')
    e=V*E_C/3.6e6
    O.add('wood_fuel_energy_twh',y,c,e*(1-qa(b,1-E_LO/E_C)),e,e*(1+qa(b,E_HI/E_C-1)),'TWh','modelled',SF+';'+SC,'Wood fuel energy = FAOSTAT m3 x 9.4 GJ/m3 (solid fuelwood at 20-30%% moisture) / 3.6e6 GJ per TWh; source range 7.2 (green) to 14.0 (0%% moisture) GJ/m3 gives the asymmetric bounds, combined in quadrature with the volume band. Gross energy, not delivered heat.')
for (c,y),(v,fl) in sorted(ch.items()):
    if y>2025: continue
    b=0.15 if (c=='XWL' or fl=='A') else 0.3
    O.add('charcoal_production_t',y,c,v*(1-b),v,v*(1+b),'t','compiled',SF,'FAOSTAT Forestry production, item 1630 Wood charcoal, flag %s. Bands assumed: +-15%% for world and official, +-30%% for estimated/imputed (much charcoal is informal).'%fl)
for y in sorted(chsum):
    if (('XWL',y) in ch) or y>2025: continue
    v=chsum[y]
    O.add('charcoal_production_t',y,'XWL',v*0.85,v,v*1.15,'t','compiled',SF,'FAOSTAT has no World aggregate for charcoal in the bulk file; this is the sum of %d national values (item 1630 Wood charcoal; former USSR, Czechoslovakia, Yugoslav SFR, Serbia and Montenegro and Sudan (former) summed as FAO reports them; China = FAO China total; Hong Kong, Macao, Taiwan not double-counted). Bands assumed +-15%%.'%chn[y])
# ---- UN energy statistics: households
SU='S0847'
hh=collections.defaultdict(dict); 
for r in csv.DictReader(open(RAW+'un/undata.csv')):
    if r['TRANSACTION']!='1231' or r['COMMODITY'] not in('5110','5160'): continue
    c=a3(r['REF_AREA'])
    y=int(r['TIME_PERIOD'])
    if not c or c not in cc: continue
    if y>2023: continue
    mult=10**int(r['UNIT_MULT']); val=float(r['OBS_VALUE'])*mult; cf=float(r['CONVERSION_FACTOR']) if r['CONVERSION_FACTOR'] else None
    hh[(r['COMMODITY'],c,y)]=(val,cf,r['OBS_STATUS'])
W=collections.defaultdict(lambda:[0.0,0.0,0])
for (com,c,y),(val,cf,st) in sorted(hh.items(),key=lambda t:(t[0][0],t[0][1],t[0][2])):
    b=0.15 if st=='A' else 0.30
    if com=='5110':
        O.add('household_fuelwood_m3',y,c,val*(1-b),val,val*(1+b),'m3','compiled',SU,'UNSD Energy Statistics (UNdata DF_UNDATA_ENERGY), commodity 5110 Fuelwood, transaction 1231 Consumption by households, status %s. Bands assumed: +-15%% for A (official), +-30%% for E (estimated).'%st)
        if cf:
            e=val*cf/3.6e6
            O.add('household_fuelwood_energy_twh',y,c,e*(1-b-0.05),e,e*(1+b+0.05),'TWh','compiled',SU,'Household fuelwood energy = UNSD volume x UNSD country conversion factor (%.2f GJ/m3) / 3.6e6. Gross energy content. Bands: volume band plus 5 percentage points for the conversion factor.'%cf)
        w=W[('5110',y)]; w[0]+=val; w[1]+=(val*cf/3.6e6 if cf else 0); w[2]+=1
    else:
        O.add('household_charcoal_t',y,c,val*(1-b),val,val*(1+b),'t','compiled',SU,'UNSD Energy Statistics, commodity 5160 Charcoal, transaction 1231 Consumption by households, status %s. Bands assumed: +-15%% for A, +-30%% for E.'%st)
        if cf:
            e=val*cf/3.6e6
            O.add('household_charcoal_energy_twh',y,c,e*(1-b-0.05),e,e*(1+b+0.05),'TWh','compiled',SU,'Household charcoal energy = UNSD tonnes x conversion factor (%.1f GJ/t) / 3.6e6. Bands: volume band plus 5 percentage points.'%cf)
        w=W[('5160',y)]; w[0]+=val; w[1]+=(val*cf/3.6e6 if cf else 0); w[2]+=1
for (com,y),(v,e,n) in sorted(W.items()):
    if n<140: continue
    if com=='5110':
        O.add('household_fuelwood_m3',y,'XWL',v*0.85,v,v*1.2,'m3','compiled',SU,'Sum of %d countries reporting household fuelwood to UNSD (ISO-coded countries in the project list only; non-reporters absent, so a lower bound on the world total - hence the asymmetric band). Same series as the country rows.'%n)
        O.add('household_fuelwood_energy_twh',y,'XWL',e*0.85,e,e*1.2,'TWh','compiled',SU,'Sum of %d reporting countries, UNSD volumes x country conversion factors; lower-bound world total.'%n)
    else:
        O.add('household_charcoal_t',y,'XWL',v*0.85,v,v*1.2,'t','compiled',SU,'Sum of %d countries reporting household charcoal to UNSD; lower-bound world total.'%n)
        O.add('household_charcoal_energy_twh',y,'XWL',e*0.85,e,e*1.2,'TWh','compiled',SU,'Sum of %d reporting countries, UNSD tonnes x conversion factor; lower-bound world total.'%n)
O.write()
