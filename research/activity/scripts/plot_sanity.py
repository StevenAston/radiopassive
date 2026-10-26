"""Sanity plots: one PNG per data/activity file in research/activity/plots/ (headline series, world or USA, band shaded)."""
import os,sys,csv,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from lib import REPO
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
A=os.path.join(REPO,'data','activity'); P=os.path.join(REPO,'research','activity','plots'); os.makedirs(P,exist_ok=True)
def load(f):
    d=collections.defaultdict(dict)
    for r in csv.DictReader(open(os.path.join(A,f+'.csv'))):
        d[(r['series'],r['country'])][int(r['year'])]=(float(r['value_low']),float(r['value_central']),float(r['value_high']),r['unit'],r['basis'])
    return d
SPEC={
'electricity_generation':[('elec_gen_coal','XWL'),('elec_gen_gas','XWL'),('elec_gen_nuclear','XWL'),('elec_gen_hydro','XWL'),('elec_gen_wind','XWL'),('elec_gen_solar','XWL')],
'coal':[('coal_production_t','XWL'),('coal_consumption_t','XWL'),('coal_power_share','XWL'),('coal_fly_ash_t','XWL')],
'oil_gas':[('oil_production_m3','XWL'),('gas_production_m3','XWL'),('oil_power_share','XWL'),('produced_water_m3','XWL')],
'uranium':[('u_production','XWL'),('u_requirements_civil','XWL'),('phi_civil','XWL')],
'nuclear':[('nuc_cap_total','XWL'),('nuc_cap_pwr','XWL'),('nuc_gen_pwr','XWL'),('nuc_spent_fuel_discharged_thm','XWL')],
'commodity_production':[('prod_copper','XWL'),('prod_aluminium','XWL'),('prod_steel','XWL'),('prod_ree_oxide','XWL'),('prod_silver','XWL'),('prod_zinc','XWL')],
'commodity_prices':[('price_copper_usd98_t','USA'),('price_gold_usd98_t','USA'),('price_steel_usd98_t','USA'),('price_rare_earths_usd98_t','USA')],
'capacity_additions':[('cap_add_solar_pv','XWL'),('cap_add_wind_onshore','XWL'),('cap_add_coal','XWL'),('cap_add_nuclear','XWL')],
'planning_parameters':[('cf_realised_nuclear','XWL'),('cf_realised_coal','XWL'),('cf_realised_wind_onshore','XWL'),('cf_realised_solar_pv','XWL')],
'biomass':[('wood_fuel_m3','XWL'),('charcoal_production_t','XWL'),('household_fuelwood_m3','XWL'),('wood_fuel_energy_twh','XWL')],
'peat':[('peat_supply_twh','FIN'),('peat_supply_twh','IRL'),('peat_supply_twh','BLR'),('peat_supply_twh','RUS')],
}
for f,L in SPEC.items():
    d=load(f); n=len(L); cols=2 if n<=4 else 3; rows=(n+cols-1)//cols
    fig,axs=plt.subplots(rows,cols,figsize=(5.2*cols,3.2*rows),squeeze=False)
    for ax,(s,c) in zip(axs.flat,L):
        v=d.get((s,c))
        if not v: ax.set_title(s+' '+c+' (missing)'); continue
        ys=sorted(v); lo=[v[y][0] for y in ys]; ce=[v[y][1] for y in ys]; hi=[v[y][2] for y in ys]
        ax.fill_between(ys,lo,hi,color='tab:blue',alpha=0.25,lw=0); ax.plot(ys,ce,color='tab:blue',lw=1.2)
        ax.set_title('%s (%s)'%(s,c),fontsize=9); ax.set_ylabel(v[ys[0]][3],fontsize=8); ax.tick_params(labelsize=7); ax.grid(alpha=0.3)
    for ax in list(axs.flat)[n:]: ax.axis('off')
    fig.suptitle('%s: central line, shaded band low to high (analyst-assumed ~5-95%%)'%f,fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(P,f+'.png'),dpi=90); plt.close(fig)
    print(f)
