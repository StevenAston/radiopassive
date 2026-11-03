"""Task 2.x nuclear-cycle activity series -> data/activity/nuclear_cycle.csv
  nuc_sea_dumped_tbq   TBq per year by country (IAEA-TECDOC-1105), 1946-1993, XWL 1946-2025
  nuc_reprocessed_gwa  civil spent fuel reprocessed, GW a (electrical energy equivalent), 1950-2025, countries and XWL
Run: python3 build_nuc2.py [--write]   (default: research/activity/out/)
"""
import os,sys,math; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from lib import *
from common import countries
import task2x_data as D
import task2y_data as Y
O=Out('nuclear_cycle'); CTY=countries()
for c in ('BEL','CHE','DEU','ITA','JPN','NLD','NZL','SWE','FRA','GBR','USA','XWL'): assert c in CTY,c
RANK={'compiled':0,'interpolated':1,'modelled':2,'extrapolated':3}
def rss(devs): return math.sqrt(sum(d*d for d in devs))
# =============================================================================================== sea dumping
Y0,Y1=1946,2025
comp={}   # (country,year) -> list of (central TBq, lo dev, hi dev, basis)
def add(c,y,tbq,rl,rh,bas): comp.setdefault((c,y),[]).append((tbq,rl*tbq,rh*tbq,bas))
for c,d in D.SEA_GBQ.items():
    cc='SWE' if c.startswith('SWE') else c
    assert abs(sum(d.values())-D.SEA_PRINTED_GBQ[c])<0.2,(c,sum(d.values()))
    for y,g in d.items(): add(cc,y,g/1e3,0.25,0.25,'compiled')
def us_spread(sites,tag):
    for (a,b,g) in sites:
        n=b-a+1
        for y in range(a,b+1): add('USA',y,g/1e3/n,0.6,1.0,'compiled' if n==1 else 'interpolated')
assert abs(sum(x[2] for x in D.US_ATL)-D.US_ATL_PRINTED)<0.01 and abs(sum(x[2] for x in D.US_PAC)-D.US_PAC_PRINTED)<0.01
atl=[(a,b,g-(D.SEAWOLF_GBQ if (a,b,g)==(1951,1960,2752800.00) else 0.0)) for (a,b,g) in D.US_ATL]   # Seawolf shell removed (naval)
us_spread(atl,'ATL'); us_spread(D.US_PAC,'PAC')
usa_tot=sum(sum(x[0] for x in v) for k,v in comp.items() if k[0]=='USA')
assert abs(usa_tot-(D.US_ATL_PRINTED+D.US_PAC_PRINTED-D.SEAWOLF_GBQ)/1e3)<1e-6
SEA_SRC='S0103'
FSU=D.FSU_TBQ
NOTE_XWL=("IAEA-TECDOC-1105 country annexes. Total activity (alpha + beta-gamma incl. H-3, TBq) estimated at packaging; sum of the country rows.||"
 "Sum of the country rows (analyst-assumed independent errors, deviations added in quadrature). Atlantic, Pacific and Baltic operators' national submissions, 1946-1982 "
 "(UK 1949-82, USA 1946-70). EXCLUDED: all former Soviet Union and Russian Federation dumping (Arctic: reactors with spent fuel %.0f TBq, reactors without fuel %.0f, solid LLW %.1f, "
 "liquid LLW %.0f, FSU Arctic total %.1f, Russian Federation Arctic %.1f; Pacific FSU %.1f, Russian Federation %.2f TBq; Table IV/V) because the civil share is undocumented "
 "and most of it is naval (D16); and the USS Seawolf reactor shell (%.0f TBq, 1959, within the US 38N 30' 72W site, naval). Not quantified in the source and not entered: Republic of Korea "
 "(115 containers 1968-72, activity not reported), UK additional operations retrieved from archive (Annex A.12-a, about 9.4 TBq, mostly upper bounds), liquid effluent poured at sea."
 )%(FSU['arctic_reactors_with_spent_fuel'],FSU['arctic_reactors_without_fuel'],FSU['arctic_solid_llw'],FSU['arctic_liquid_llw'],FSU['arctic_total_FSU'],FSU['arctic_RUS'],FSU['pacific_FSU'],FSU['pacific_RUS'],D.SEAWOLF_GBQ/1e3)
NOTE_C={
 'USA':("US Atlantic (A.13) and Pacific (A.14) site totals spread uniformly over each site's stated dumping period (interpolated; no annual split is published); Seawolf excluded.||"
        "Atlantic subtotal 2,942.2 TBq less the Seawolf reactor shell 1,221 TBq; Pacific 554.2 TBq (of which 536.5 TBq at the Farallon site 1946-70). Packaging-time estimates; "
        "the 1946-70 US waste came from AEC, Navy and contractor laboratories and its civil share is not documented (flag for D16). Band: -60%/+100% of the annual share because the timing within each period is unknown."),
 'SWE':"Annex A.9 (Atlantic, 1969: 3,242.7 GBq) plus A.10 (Baltic, 1959 and 1961: 14.8 GBq).",
 'GBR':"Annex A.12, sum of all dump sites per year (35,077.6 TBq in total). A.12-a archive operations (about 9.4 TBq, mostly upper bounds) not included.",
 'KOR':"",
}
cs=sorted({k[0] for k in comp})
for c in cs:
    ys=[k[1] for k in comp if k[0]==c]
    for y in range(min(ys),max(ys)+1):
        v=comp.get((c,y),[])
        ce=sum(x[0] for x in v); lo=rss([x[1] for x in v]); hi=rss([x[2] for x in v])
        bas=max((x[3] for x in v),key=lambda b:RANK[b]) if v else 'compiled'
        nt=NOTE_C.get(c,'IAEA-TECDOC-1105 annex A; sum of the dump operations of the year (total activity, TBq, estimated at packaging).')
        if not v: nt='No dumping reported in this year (within the national disposal period).'
        O.add('nuc_sea_dumped_tbq',y,c,ce-lo,ce,ce+hi,'TBq',bas,SEA_SRC,nt)
for y in range(Y0,Y1+1):
    v=[x for (c,yy),l in comp.items() if yy==y for x in l]
    ce=sum(x[0] for x in v); lo=rss([x[1] for x in v]); hi=rss([x[2] for x in v])
    bas='interpolated' if any(x[3]=='interpolated' for x in v) else 'compiled'
    O.add('nuc_sea_dumped_tbq',y,'XWL',ce-lo,ce,ce+hi,'TBq',bas,SEA_SRC,NOTE_XWL)
# =============================================================================================== reprocessing
ETA=0.33
def gwa_per_t(B,eta=ETA): return eta*B/365.25
rep={}    # (country,year) -> list of (central, dlo, dhi, basis, site)
def radd(c,y,ce,rl,rh,bas,site): rep.setdefault((c,y),[]).append((ce,rl*ce,rh*ce,bas,site))
# ---- La Hague
for y,v in D.LH_UNSCEAR.items(): radd('FRA',y,v,0.25 if y==1997 else 0.15,0.25 if y==1997 else 0.15,'compiled','La Hague')
for y in range(1966,1971): radd('FRA',y,0.9,0.55,1.0,'extrapolated','La Hague UP2 UNGG')
def B_lh(y): return 33+(45-33)*(y-1998)/12 if y<=2010 else 45+(47-45)*(y-2010)/15
thm={y:(v,0.15) for y,v in D.LH_CHART_THM.items() if y>=1998}
cum_chart=sum(D.LH_CHART_THM.values()); rest=D.ORANO_CUM[2024]-cum_chart
t2022,t2024=D.ORANO_YEAR[2022],D.ORANO_YEAR[2024]; t2023=D.ORANO_CUM[2024]-D.ORANO_CUM[2022]-t2024
mid=(rest-t2022-t2023-t2024)/15.0
for y in range(2007,2022): thm[y]=(mid,0.20)
thm[2022]=(t2022,0.03); thm[2023]=(t2023,0.03); thm[2024]=(t2024,0.03); thm[2025]=(t2024,0.15)
for y,(t,r) in thm.items():
    ce=t*gwa_per_t(B_lh(y)); rr=rss([r,0.12])
    bas='modelled' if (y<=2006 or y>=2022) else 'interpolated'
    radd('FRA',y,ce,rr,rr,bas,'La Hague LWR')
# ---- THORP (calendar year = 0.75 x FY(y+1) + 0.25 x FY(y); FY label = year ending 31 March)
F=dict(D.THORP_FY); F[1995]=40.0; F[1996]=200.0
assert abs(F[1995]+F[1996]+sum(F[y] for y in range(1997,2005))-D.THORP_FIRST10)<1e-6
known=F[1995]+F[1996]+sum(D.THORP_FY.values())
tail_units=10+0.61   # FY2009-FY2018 full years plus FY2019 (fuel until 9 Nov 2018, about 7.3 of 12 months)
U=(D.THORP_TOTAL-known)/tail_units
for L in range(2009,2019): F[L]=U
F[2019]=0.61*U
for y in range(1994,2019):
    t=0.75*F.get(y+1,0)+0.25*F.get(y,0)
    if t<=0: continue
    ce=t*0.030; rr=rss([0.25,0.25])
    radd('GBR',y,ce,rr,rr,'modelled','THORP')
# ---- Sellafield B205 (Magnox reprocessing plant), civil from calendar 1995 only (D64: military feed ended 1995)
FYB={}    # FY label -> (tHM, lo dev frac, hi dev frac, kind)
for y,v in Y.IPFM_FY.items(): FYB[y]=(v,0.10,0.10,'chart')
for y,v in Y.MOP9_FY.items(): FYB[y]=(v,0.0 if y in Y.MOP9_PRINTED else 0.10,0.0 if y in Y.MOP9_PRINTED else 0.10,'printed' if y in Y.MOP9_PRINTED else 'chart')
FYB[2013]=(Y.FY2013,0.10,0.10,'derived'); FYB[2014]=(Y.FY2014,0.03,0.03,'printed')
FYB[2017]=(Y.FY2017,0.0,0.0,'printed'); FYB[2019]=(Y.FY2019,0.0,0.0,'printed')
RES=Y.REMAINING_APR2012-sum(FYB[y][0] for y in (2013,2014,2017,2019))      # tU left for the undocumented periods
GAPS=(2015,2016,2018,2020,2021,2022)
UB=RES/(len(GAPS)+Y.STUB_2022_FRAC)
for y in GAPS: FYB[y]=(UB,0.30,0.30,'spread')
FYB[1996]=(FYB[1997][0],0.50,1.00,'carried'); FYB[1995]=(FYB[1997][0],0.50,1.00,'carried')
STUB=UB*Y.STUB_2022_FRAC
GB=Y.ETA_MAGNOX*Y.BURNUP_MAGNOX/365.25     # GW a per tHM
def fy(y): return FYB[y]
for y in range(1995,2023):
    comps=[(0.25,fy(y)),(0.75,fy(y+1))] if y<2022 else [(0.25,fy(y))]
    t=sum(w*f[0] for w,f in comps); lo=rss([w*f[0]*f[1] for w,f in comps]); hi=rss([w*f[0]*f[2] for w,f in comps])
    if y==2022: t+=STUB; lo=rss([lo,STUB*0.30]); hi=rss([hi,STUB*0.30])
    kinds={f[3] for w,f in comps}|({'spread'} if y==2022 else set())
    bas='extrapolated' if 'carried' in kinds else ('interpolated' if ('spread' in kinds and not (kinds&{'chart','printed','derived'})) else 'modelled')
    ce=t*GB; rl=rss([lo/t,0.20]); rh=rss([hi/t,0.20])
    radd('GBR',y,ce,rl,rh,bas,'B205 Magnox')
print('B205 tHM cal-year',{y:round(sum(x[0] for x in rep[('GBR',y)] if x[4]=='B205 Magnox')/GB) for y in (1995,1996,2000,2005,2010,2015,2020,2022)},'residual',round(RES,1),'unit',round(UB,1))
print('B205 cumulative 1995-2022 tHM',round(sum(x[0] for k,l in rep.items() if k[0]=='GBR' for x in l if x[4]=='B205 Magnox')/GB))
# ---- Japan
for y,v in D.TOKAI_UNSCEAR.items(): radd('JPN',y,v,0.15,0.15,'compiled','Tokai')
for y,v in {1998:0.0,1999:0.0,2000:0.5,2001:0.5,2002:0.5,2003:0.5,2004:0.5,2005:0.5,2006:0.25}.items():
    if v>0: radd('JPN',y,v,1.0,2.0,'modelled','Tokai (campaigns unresolved)')
for y,t in {2006:110.0,2007:200.0,2008:120.0}.items(): radd('JPN',y,t*gwa_per_t(37.0),0.40,0.40,'modelled','Rokkasho active tests')
# ---- Germany WAK (about 200 t, 1971-1990) and Belgium Eurochemic (181.5 t, 1966-1974)
for y in range(1971,1991): radd('DEU',y,200.0/20*gwa_per_t(25.0),0.8,1.0,'interpolated','WAK Karlsruhe')
for y in range(1966,1975): radd('BEL',y,181.5/9*gwa_per_t(8.0,0.30),0.7,1.0,'interpolated','Eurochemic Mol')
# ---- emit
UB_RES=RES; UB_STUB=STUB; B205_TOT=sum(x[0] for k,l in rep.items() if k[0]=='GBR' for x in l if x[4]=='B205 Magnox')/GB
NOTE_REP={
 'FRA':("La Hague (UP2/UP3), civil. 1971-97 UNSCEAR 2000 Table 40; 1966-70 extrapolated; 1998-2025 tHM x 0.33 x burnup/365.25.||"
        "1971-1997: UNSCEAR 2000 Annex C Table 40 'fuel reprocessed' (GW a), which includes the UNGG fuel of EDF reactors at UP2 (Orano: about 5,000 t, 1966-87). 1997 is UNSCEAR's own estimate from the normalised Kr-85 release. "
        "1966-70: no GW a published; 0.9 GW a/a assumed from the 1971 UNSCEAR value (UNGG at UP2). 1998-2006: LWR tHM from the IPFM RR4 Figure 6 bars (pixel-read); 2007-21: the Orano cumulative 41,236 tHM (end 2024) less the chart total 22,584, 2022 (925), 2023 (882, from the cumulative) and 2024 (871), spread evenly (%.0f tHM/a); "
        "2025 = 2024. GW a = tHM x 0.33 x B/365.25 with average discharge burnup B rising linearly from 33 GWd/t (1998) to 45 (2010) and 47 (2025) (analyst assumption; the implied value for 1995-97, 28-33 GWd/t, is consistent with UNSCEAR). Foreign fuel is included (France is the site country)."%mid),
 'GBR':("Sellafield THORP (1994-2018) and, from 1995, the B205 Magnox plant (to July 2022), civil.||"
        "THORP throughput: IPFM RR5 Figure 6 bars (financial years ending 31 March, read by eye), calendar year = 0.75 x FY(y+1) + 0.25 x FY(y); FY1995-96 = 240 tHM split 40/200 so that the first ten years total 5,045 tHM (IPFM blog 2018); "
        "FY2009-2019 spread evenly (%.0f tHM per full year) so that the lifetime total is 9,331 tHM (Sellafield Ltd/NDA, 14 Nov 2018). GW a = tHM x 0.030 (AGR about 24 GWd/t at 41%% efficiency and LWR 33-45 GWd/t at 33%%, roughly half each; analyst assumption). "
        "B205 (Magnox reprocessing plant), counted as civil from calendar 1995 only (D64: the military feed from Calder Hall and Chapelcross ended with the 1995 government decision; before 1995 the civil share is undocumented and B205 is excluded; "
        "from 1995 the whole throughput is treated as civil, a limit because Magnox fuel from Calder Hall and Chapelcross, where still reprocessed, was military). Throughput in tHM by financial year (ending 31 March; same calendar conversion as THORP): "
        "FY1997-2000 IPFM RR5 Figure 4, S0130 (604, 523, 467, 503; bar tops measured, about +-10 t); FY2001-2012 NDA MOP 9 (2012) Figure 4.1, S1700 (chart readings; FY2011 = 233 and FY2012 = 607 printed); "
        "FY2013 = 261 by difference (CORE briefing 04/14, S1701: 1,338 t over 2011/12-2013/14, less 607 and 470); FY2014 = 470 (Roche 2015, S1702); FY2017 = 466 (Sellafield Ltd Annual Review 2016/17, S1703); FY2019 = 341.5 (Annual Review 2018/19, S1704). "
        "FY2015, FY2016, FY2018 and FY2020-22 have no annual figure found: they share equally the %.0f tU left of the 3,800 tU still to reprocess in April 2012 (MOP 9) after the documented years, %.0f tHM per full year, the last period being the stub April-17 July 2022 (3.5 months, last feed, IPFM blog 2022) at %.0f tHM; band +-30%%. "
        "FY1995 and FY1996 have no annual figure found and carry FY1997 (604 tHM) with a band of -50%% to +100%% (basis extrapolated; IPFM RR5 says early-year throughput regularly exceeded 1,000 tHM/a and fell in the mid-1990s). "
        "GW a = tHM x 0.27 x 5 GWd/tHM / 365.25 = 0.0037 GW a per tHM (Magnox burnup about 5 GWd/tHM, thermal efficiency 0.27 as in the spent-fuel model of build_nuc.py; both assumed; conversion band +-20%%). "
        "Cross-check: the annual values sum to %.0f tHM over 1995-2022 (calendar years), against the 54,920 tHM lifetime total of the plant (IPFM blog 2022); the pre-1995 remainder is not reconstructed."%(U,UB_RES,UB,UB_STUB,B205_TOT)),
 'JPN':("Tokai 1977-97 UNSCEAR 2000 Table 40; Tokai 1998-2006 and Rokkasho active tests 2006-08 modelled.||"
        "Tokai: UNSCEAR Table 40 GW a to 1997; after the 1997 fire campaign years are unresolved (JAEA gives 1,052 tHM cumulative to March 2006 with no years), so 0.5 GW a/a in 2000-05 and 0.25 in 2006 are assumed with a band of 0 to 3 times the central value. "
        "Rokkasho active tests: CNIC planned 430 tHM (about 210 PWR, 220 BWR) over 2006-08, allocated 110/200/120 tHM at 37 GWd/t average burnup (low-burnup steps first); the actual quantities are not published in the sources read (TEPCO page: 156 tU of its own fuel)."),
 'DEU':"WAK Karlsruhe, about 200 tHM of fuel reprocessed 1971-90 (euronuclear); spread evenly, 25 GWd/t at 33% assumed.",
 'BEL':"Eurochemic (Mol), 181.5 tHM reprocessed 1966-74 (eurochemic.be), spread evenly; 8 GWd/t at 30% assumed (natural and low-enriched fuel).",
}
cs=sorted({k[0] for k in rep})
for c in cs:
    ys=[k[1] for k in rep if k[0]==c]
    for y in range(min(ys),max(ys)+1):
        v=rep.get((c,y),[])
        ce=sum(x[0] for x in v); lo=rss([x[1] for x in v]); hi=rss([x[2] for x in v])
        bas=max((x[3] for x in v),key=lambda b:RANK[b]) if v else 'interpolated'
        src={'FRA':'S0004;S0131;S1601;S1600','GBR':('S0130;S1602;S1603;S1609;S1700;S1701;S1702;S1703;S1704' if y>=1994 else 'S0130;S1602;S1603'),'JPN':'S0004;S1604;S1605;S1606','DEU':'S1608','BEL':'S1607'}[c]
        nt=NOTE_REP[c] if y==min(ys) else {'FRA':'La Hague, civil (see the first row of the series for the method).','GBR':('Sellafield THORP and B205 Magnox (see the first row for the method).' if 1995<=y<=2018 else 'Sellafield B205 Magnox only; THORP closed in 2018 (see the first row for the method).' if y>2018 else 'Sellafield THORP only; B205 not counted before 1995 (see the first row).'),'JPN':'Tokai and Rokkasho (see the first row for the method).','DEU':'WAK Karlsruhe (see the first row).','BEL':'Eurochemic (see the first row).'}[c]
        if not v: nt='No reprocessing campaign assumed in this year of the site operating period.'
        O.add('nuc_reprocessed_gwa',y,c,ce-lo,ce,ce+hi,'GWa',bas,src,nt)
_old='Sellafield B205 Magnox plant (1964-2022, about 54,920 tHM; military campaigns for Calder Hall/Chapelcross fuel ended after 1995)'
assert _old in D.EXCLUDED_NOTE
EXCL=D.EXCLUDED_NOTE.replace(_old,'Sellafield B205 Magnox plant before 1995 (1964-94, military and civil feed mixed with an undocumented split; D64 counts B205 as civil from 1995, when the military campaigns ended, and it is in the GBR rows from then)')
NOTE_W=("Civil spent fuel reprocessed, GW a of electricity; sum of the country rows; dual-use sites excluded (D16).||"
 "Sum of the country rows, errors added in quadrature. Countries: France (La Hague), United Kingdom (THORP and, from 1995, B205 Magnox), Japan (Tokai, Rokkasho), Germany (WAK), Belgium (Eurochemic). "+EXCL+" "
 "Consequence: before 1994 the series is far below the UNSCEAR 2000 world totals (Table 43: 2.3 GW a before 1970, 7.0 in 1970-74, 22.2 in 1975-79, 36.3, 62.5, 130, 160 in the later periods), which are dominated by Magnox and by the excluded sites. "
 "Cross-check 1998-2002 mean, this series %.1f GW a/a against the implied 62.6 GW a/a (UNSCEAR 2008 Table 20, all plants incl. the excluded ones).")
chk=[sum(x[0] for k,l in rep.items() if k[1]==y for x in l) for y in range(1998,2003)]
CHK=sum(chk)/5
src_all='S0004;S0003;S0130;S0131;S0132;S1600;S1601;S1602;S1603;S1604;S1605;S1606;S1607;S1608;S1609;S1610;S1611;S1700;S1701;S1702;S1703;S1704'
for y in range(1950,2026):
    v=[x for (c,yy),l in rep.items() if yy==y for x in l]
    ce=sum(x[0] for x in v); lo=rss([x[1] for x in v]); hi=rss([x[2] for x in v])
    nt=(NOTE_W%CHK) if y==1950 else 'World civil total, sum of the country rows (method in the 1950 row).' if v else 'No civil reprocessing in the series (all operating plants before 1966 were military or dual-use; D16).'
    O.add('nuc_reprocessed_gwa',y,'XWL',ce-lo,ce,ce+hi,'GWa','modelled',src_all,nt)
print('mean 1998-2002 GW a/a',round(CHK,1),'vs 62.6;  La Hague mid-years tHM',round(mid,1),' THORP unit',round(U,1))
O.write()
