import sys; sys.path.insert(0,'/tmp/claude-0/-home-claude/7f015155-d930-5c34-900b-ab275f11b117/scratchpad/task19/scripts')
from lib import *
from common import *
import csv,collections,pycountry
cc=countries()
def a3(m):
    try: return pycountry.countries.get(numeric='%03d'%int(m)).alpha_3
    except Exception: return None
SU='S0847'
T={'01':'peat_production_t','GA':'peat_supply_t','1231':'peat_household_t'}
P=['08811','08812','08821','08822']
d=collections.defaultdict(dict); pw=collections.defaultdict(lambda:[0.0,0.0,0,0.0])
cfs={}
for r in csv.DictReader(open(RAW+'un/undata.csv')):
    if r['COMMODITY']!='1100': continue
    c=a3(r['REF_AREA']); 
    if not c or c not in cc: continue
    y=int(r['TIME_PERIOD'])
    if y>2025: continue
    val=float(r['OBS_VALUE'])*10**int(r['UNIT_MULT']); cf=float(r['CONVERSION_FACTOR']) if r['CONVERSION_FACTOR'] else None
    t=r['TRANSACTION']
    if t in T: d[(T[t],c,y)]=(val,cf,r['OBS_STATUS'])
    if t in P:
        w=pw[(c,y)]; w[0]+=val; w[2]+=1; w[1]=cf if cf else w[1]
O=Out('peat')
for (s,c,y),(val,cf,st) in sorted(d.items()):
    b=0.10 if st=='A' else 0.25
    O.add(s,y,c,val*(1-b),val,val*(1+b),'t','compiled',SU,'UNSD Energy Statistics (UNdata DF_UNDATA_ENERGY), commodity 1100 Peat (peat for energy; horticultural peat is outside this series), transaction %s, status %s. Bands assumed: +-10%% for A, +-25%% for E.'%({'peat_production_t':'01 Production','peat_supply_t':'GA Total energy supply','peat_household_t':'1231 Consumption by households'}[s],st))
    if s in('peat_supply_t','peat_production_t') and cf:
        e=val*cf/3.6e6; nm=s.replace('_t','_twh')
        O.add(nm,y,c,e*(1-b-0.1),e,e*(1+b+0.1),'TWh','compiled',SU,'Peat energy = UNSD tonnes x UNSD country conversion factor (%.2f GJ/t, i.e. TJ per 1000 t; peat moisture varies by product, so 10 percentage points are added to the band) / 3.6e6 GJ per TWh. Gross energy content.'%cf)
for (c,y),(val,cf,n,_) in sorted(pw.items()):
    b=0.25
    O.add('peat_power_heat_t',y,c,val*(1-b),val,val*(1+b),'t','compiled',SU,'Peat transformed in electricity and CHP plants (UNSD transactions 08811+08812+08821+08822: main-activity and autoproducer electricity and CHP), summed over the %d transactions reported; includes the heat share of CHP, so not electricity generation alone. Bands assumed +-25%%.'%n)
O.write()
