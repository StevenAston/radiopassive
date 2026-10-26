import os,sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from lib import *
from common import *
import csv,math,collections,html,re
ns={}; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'redbook_u.py')).read(),ns); D=ns['D']
O=Out('uranium')
def est(c,y):
    if c in('CHN','COD','IND','PAK','POL','UKR','SUN'): return True
    if c=='BGR' and 1965<=y<=1984: return True
    if c=='HUN' and 1965<=y<=1989: return True
    if c=='ROU' and (1965<=y<=1984 or y>=2001): return True
    if c=='DDR' and y<=1954: return True
    return False
RB='S0113'
base_note='NEA/IAEA Red Book Retrospective (2006) Appendix 7.1, transcribed by eye from image tables (printed pp. 255-258 and erratum page; every year column re-added and ties to the printed world total; printed 1945-2003 grand total 2,204,732 tU vs 2,204,632 tU from the columns: a 100 tU discrepancy in the source). Bands assumed (approx. 5th-95th percentile): +-5% where reported, +-25% for entries the Secretariat estimated (bold italics in the table) and for Soviet figures.'
wsum={}
for c,d in D.items():
    if c=='XWL': continue
    for y,v in d.items():
        e=est(c,y); rel=0.25 if e else 0.05
        if y<=1964 and c not in ('SUN',): rel=max(rel,0.10)
        lo,ce,hi=bands(v,rel)
        O.add('u_production',y,c,lo,ce,hi,'t','compiled' if not e else 'modelled',RB,base_note+(' Secretariat estimate.' if e else '')+(' Pre-1965 figures are new data from member countries and non-Red-Book sources (table note a).' if y<1965 else ''))
        a=wsum.setdefault(y,[0,0,0]); a[0]+=ce; a[1]+=(ce-lo)**2; a[2]+=(hi-ce)**2
for y,(ce,dl,dh) in wsum.items():
    W=D['XWL'][y]
    O.add('u_production',y,'XWL',max(0,W-math.sqrt(dl)),W,W+math.sqrt(dh),'t','compiled',RB,base_note+' World total as printed (bands: country bands in quadrature). Includes GDR, Czechoslovakia and the USSR under their then names; USSR*, as footnoted, includes later-independent republics.')
# 2004-2014 OWID (USGS/BGS), countries
CMAP={'Kazakhstan':'KAZ','Canada':'CAN','Australia':'AUS','Namibia':'NAM','Niger':'NER','Russia':'RUS','Uzbekistan':'UZB','United States':'USA','China':'CHN','South Africa':'ZAF','Ukraine':'UKR','India':'IND','Czechia':'CZE','Romania':'ROU','Brazil':'BRA','Germany':'DEU','Pakistan':'PAK','Malawi':'MWI','Iran':'IRN','Hungary':'HUN','Bulgaria':'BGR'}
own=collections.defaultdict(dict)
for r in csv.DictReader(open(RAW+'min/Uranium__Mine.csv')):
    e=r['Entity']; c='XWL' if e=='World' else CMAP.get(e)
    if c: own[c][int(r['Year'])]=float(r['Uranium production'])
on='OWID minerals explorer (USGS Mineral Commodity Summaries / Historical Statistics; BGS World Mineral Statistics), tonnes of contained U. Red Book 2022 (2004-2014 by country) was inaccessible, so this is the substitute; bands assumed +-5% world, +-10% country (OWID world and WNA totals agree to <0.1% in 2015 and 2023).'
for c,d in own.items():
    for y in range(2004,2015):
        if y in d:
            rel=0.05 if c=='XWL' else (0.25 if c in('CHN','IND','PAK','UKR') else 0.10)
            lo,ce,hi=bands(d[y],rel); O.add('u_production',y,c,lo,ce,hi,'t','compiled','S0807',on)
# WNA 2015-2024
t=open(RAW+'wna.html').read(); tb=re.findall(r'<table.*?</table>',t,flags=re.S)[0]
rows=[[html.unescape(re.sub(r'<[^>]+>','',x)).strip() for x in re.findall(r'<t[dh].*?</t[dh]>',r,flags=re.S)] for r in re.findall(r'<tr.*?</tr>',tb,flags=re.S)]
yrs=[int(x) for x in rows[0][1:]]
WM={'Kazakhstan':'KAZ','Canada':'CAN','Namibia':'NAM','Australia':'AUS','Uzbekistan':'UZB','Russia':'RUS','China':'CHN','Niger':'NER','India':'IND','South Africa':'ZAF','Ukraine':'UKR','USA':'USA'}
for r in rows[1:]:
    nm=r[0]; base=re.sub(r' \(est\.\)','',nm)
    isest='(est.)' in nm
    c=WM.get(base)
    if nm=='World total tU': c='XWL'
    if not c: continue
    for y,v in zip(yrs,r[1:]):
        v=float(v.replace(',',''))
        rel=0.03 if c=='XWL' else (0.25 if isest else 0.03)
        lo,ce,hi=bands(v,rel); O.add('u_production',y,c,lo,ce,hi,'t','compiled' if not isest else 'modelled','S0115','World Nuclear Association, World Uranium Mining Production (page updated 2026-10-09), tU. '+('WNA estimate (est.) for this country; ' if isest else '')+'Bands assumed +-3% (reported) or +-25% (WNA estimate). Not independent of the Red Book. 2025 not published at time of access.')
# requirements
a=[770,516,732,716,1655,1463,2079,3696,4543,4928,5082,7084,9625,12200,13964,15245,16245,17716,18499]
b=[19944,23137,25251,27117,29301,28044,29800,31872,34711,42268,42942,44599,46813,49906,52331,49950,55420,57272,58527]
c=[57009,61377,60488,63757,59551,61589,64014,64329,66815,68435]
req=dict(zip(range(1956,1975),a)); req.update(zip(range(1975,1994),b)); req.update(zip(range(1994,2004),c))
for y,v in req.items():
    rel=0.10 if y>=1980 else 0.15
    lo,ce,hi=bands(v,rel)
    O.add('u_requirements_civil',y,'XWL',lo,ce,hi,'t','compiled',RB,'World annual reactor-related uranium requirements, Red Book Retrospective Appendix 3.1 (PDF pp.177-179, world row transcribed from images; 1956-2003 sum 1,513,327 tU ties to the printed total). Country values before 1980 are estimates from IAEA PRIS capacity; requirements are acquisitions/loadings, not consumption. Bands assumed +-10% (+-15% before 1980).')
nuc=owid('eps.csv','Nuclear')
ratio=[req[y]/nuc[y] for y in range(1990,2004)]; K=sum(ratio)/len(ratio)
print('tU/TWh',K,min(ratio),max(ratio))
for y in range(2004,2025):
    v=nuc[y]*K
    lo,ce,hi=bands(v,0.15)
    O.add('u_requirements_civil',y,'XWL',lo,ce,hi,'t','modelled','S0113;S0800','Modelled for 2004-2024 (Red Book 2022 inaccessible): world nuclear generation (OWID/Ember/EI) x mean ratio %.1f tU/TWh of 1990-2003 requirements (range %.1f-%.1f). Neglects burnup rise (lowers future ratio) and plutonium/enrichment tails policy; bands +-15%% assumed.'%(K,min(ratio),max(ratio)))
# phi_civil world default
prod={y:float(O.rows[('u_production',y,'XWL')][4]) for y in range(1945,2025) if ('u_production',y,'XWL') in O.rows}
for y in range(1945,2025):
    if y not in prod: continue
    if y<1965:
        O.add('phi_civil',y,'XWL',0,0,0,'1','modelled','S0113','Zero-width band by definition. METHODS 9.2 rule 2: phi_civil = 0 before 1965 for undocumented country-years. (Rule 1, documented civil end use for 1956-1964 first-reactor fuel, to be applied per country by Task 2.1; world civil requirements 1956-1964 were 0.7-4.5 kt U, see u_requirements_civil.)')
    else:
        R=[float(O.rows[('u_requirements_civil',y,'XWL')][i]) for i in (3,4,5)]
        P=[float(O.rows[('u_production',y,'XWL')][i]) for i in (3,4,5)]
        c=min(1.0,R[1]/P[1]); lo=min(c,max(0.0,R[0]/P[2])); hi=min(1.0,R[2]/P[0])
        lo=min(lo,1.0)
        sat=(lo>=1.0 and y>=1991)
        if sat: lo=0.9
        O.add('phi_civil',y,'XWL',lo,c,max(hi,c),'1','modelled','S0113;S0115;S0807',('SATURATED: upper bound, rule 3 saturates; low 0.9 assumed. ||' if sat else '')+'METHODS 9.2 rule 3 global default phi = min(1, R_civil / U_prod) with U_doc = U_doc,civil = 0 (no documented country-years entered yet, so Task 2.1 must replace this by the documented-adjusted form). R_civil = u_requirements_civil, U_prod = u_production, both world. Requirements are acquisitions and include inventory/secondary-supply drawdown after 1990, so phi saturates at 1 from the mid-1980s; this is an upper bound, as noted in the Task 1.2 survey. Low = R_low / P_high, high = R_high / P_low (capped at 1).'+(' SATURATED: R_civil exceeds U_prod by more than the bands, so 1 is an upper bound under rule 3 and the data give no lower bound (R minus P is secondary supply, not military use); the low bound 0.9 is an analyst assumption (no weapons-purpose mining of new uranium after the end of Cold War production), approx. 5th percentile.' if sat else ''))
O.write()
