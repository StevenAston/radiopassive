#!/usr/bin/env python3
"""Build research/coal/acaa_series.csv and acaa_uses.csv from the ACAA archive (import/acaa/).

Text-layer survey tables (2002-2015, 2021, 2023) are parsed with pdftotext -layout; every other year is a
hand transcription (scan read visually or OCR-then-checked) stored in the dicts below. Run:
    python3 -I research/coal/acaa_build_series.py [path-to-text-cache]
The transcribed dicts carry their own arithmetic checks (see check()).
"""
import csv, re, subprocess, sys, os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
ACAA = os.path.join(ROOT, 'import', 'acaa')
OUT = os.path.join(ROOT, 'research', 'coal')
ST2T = 0.90718474

def txt(fname):
    return subprocess.run(['pdftotext', '-layout', os.path.join(ACAA, fname), '-'], capture_output=True, text=True).stdout

num = re.compile(r'(?<![\d.])\d{1,3}(?:,\d{3})+(?![\d,])|(?<![\d.,])\d+(?![\d,.%])')
def nums(s): return [int(x.replace(',', '')) for x in num.findall(s)]

# ---- text-layer years -------------------------------------------------------------------------------
FILES = {
 2002: ('acaa_2002_ccp_svy(11-25-03).pdf', 2), 2003: ('2003_CCP_Survey(10-1-04).pdf', 1), 2004: ('2004_CCP_Survey(9-9-05).pdf', 1),
 2005: ('2005 CCP Survey (09-19-06)Corrected-11-09-07.pdf', 1), 2006: ('2006_CCP_Survey_(Final-8-24-07).pdf', 2),
 2007: ('2007_ACAA_CCP_Survey_Report_Form(09-15-08).pdf', 1), 2008: ('2008_ACAA_CCP_Survey_Report_FINAL_100509.pdf', 1),
 2009: ('2009_Production_and_Use_Survey_Revised_100511.pdf', 1), 2010: ('2010_CCP_Survey_FINAL_102011.pdf', 1),
 2011: ('Final2011CCPSurvey.pdf', 1), 2012: ('revisedFINAL2012CCPSurveyReport.pdf', 1), 2013: ('2013ReportFINAL.pdf', 1),
 2014: ('2014ReportFinal.pdf', 1), 2015: ('2015-Survey_Results_Table.pdf', 1),
 2021: ('2021-Production-and-Use-Survey-Results-FINAL.pdf', 1), 2023: ('2023-Production-and-Use-Survey-Results-FINAL.pdf', 1)}
STD = ['fly_ash', 'bottom_ash', 'boiler_slag', 'fgd_gypsum', 'fgd_wet', 'fgd_dry', 'fgd_other', 'fbc_ash']
ORD = {y: ['fly_ash', 'bottom_ash', 'fgd_gypsum', 'fgd_wet', 'boiler_slag', 'fgd_dry', 'fgd_other', 'fbc_ash'] for y in (2002, 2003, 2004, 2005)}
ORD[2006] = STD

def parse_text_year(y):
    """Column-aware parse with pdfplumber: numbers are assigned to the header columns by their right-edge x."""
    import pdfplumber
    f, page = FILES[y]
    order = ORD.get(y, STD)
    pl = pdfplumber.open(os.path.join(ACAA, f)).pages[page - 1]
    words = pl.extract_words(keep_blank_chars=False, use_text_flow=False)
    lines = []
    for w in sorted(words, key=lambda w: (round(w['top']), w['x0'])):
        for ln in lines:
            if abs(ln['top'] - w['top']) < 3: ln['w'].append(w); break
        else: lines.append({'top': w['top'], 'w': [w]})
    lines.sort(key=lambda l: l['top'])
    isnum = lambda t: re.fullmatch(r'\d{1,3}(,\d{3})*(\.00)?', t) is not None
    def text(l): return ' '.join(w['text'] for w in sorted(l['w'], key=lambda w: w['x0']))
    r = {'prod': None, 'used': None, 'uses': {}}
    edges = None
    pending = None
    for l in lines:
        t = text(l)
        nums_ = [w for w in sorted(l['w'], key=lambda w: w['x0']) if isnum(w['text'])]
        if re.match(r'(\d{4} )?(Total CCPs Produced by Category|CCP Production Category Totals)', t) and r['prod'] is None:
            edges = [w['x1'] for w in nums_]
            r['prod'] = [int(float(w['text'].replace(',', ''))) for w in nums_]
        elif re.match(r'(\d{4} )?(Total CCPs Used by Category|CCP Used Category Totals)', t) and r['used'] is None:
            r['used'] = [int(float(w['text'].replace(',', ''))) for w in nums_]
        elif re.match(r'(All )?CCP Production Total', t): r['tot_p'] = int(nums_[0]['text'].replace(',', ''))
        elif re.match(r'All CCP Used Total', t): r['tot_u'] = int(nums_[0]['text'].replace(',', ''))
        if edges is None: continue
        m = re.match(r'^(\d{1,2})\.\s*(.*)$', t)
        rowvals = None
        if nums_ and len(nums_) >= 1 and (m or pending):
            vals = [None] * len(edges)
            for w in nums_:
                j = min(range(len(edges)), key=lambda j: abs(edges[j] - w['x1']))
                if abs(edges[j] - w['x1']) < 25: vals[j] = int(float(w['text'].replace(',', '')))
            if m and 'Summary' not in t and len([v for v in vals if v is not None]) >= 1 and int(m.group(1)) not in r['uses']:
                lab = re.sub(r'[\d,\s]+$', '', m.group(2)).strip()
                r['uses'][int(m.group(1))] = [lab, vals]; pending = None
            elif pending is not None and not m:
                r['uses'][pending][1] = [a if a is not None else b for a, b in zip(r['uses'][pending][1], vals)]; pending = None
        elif m and not nums_ and int(m.group(1)) not in r['uses'] and len(m.group(2)) > 8:
            r['uses'][int(m.group(1))] = [m.group(2).strip(), [None] * len(edges)]; pending = int(m.group(1))
        elif pending is not None and not nums_ and 'Wallboard' in t:
            r['uses'][pending][0] += ' ' + t
    for k in r['uses']: r['uses'][k] = (r['uses'][k][0], [v or 0 for v in r['uses'][k][1]])
    if y == 2007:  # row 9 numbers are missing from the text layer (garbled); read from the rendered page
        r['uses'][9] = ('Blasting Grit/Roofing Granules', [0, 71903, 1377658, 0, 0, 0, 0, 0, 1449561, 0, 1449561])
    return r, order, f, page

def norm_use(label):
    l = label.lower()
    for k, v in [('concrete', 'concrete_grout'), ('cement', 'blended_cement_clinker'), ('flowable', 'flowable_fill'),
                 ('structural', 'structural_fill'), ('road', 'road_base'), ('soil', 'soil_modification'),
                 ('mineral filler', 'mineral_filler_asphalt'), ('snow', 'snow_ice_control'), ('blasting', 'blasting_grit_roofing'),
                 ('mining', 'mining_applications'), ('gypsum panel', 'gypsum_panel'), ('wallboard', 'gypsum_panel'),
                 ('waste', 'waste_stabilisation'), ('agri', 'agriculture'), ('aggregate', 'aggregate'),
                 ('oil', 'oil_gas_field_services'), ('pond', 'ccr_pond_closure'), ('misc', 'miscellaneous')]:
        if k in l: return v
    return 'unmapped:' + label

# ---- hand-transcribed years -------------------------------------------------------------------------
# fly, bottom, slag (million short tons unless MST=False). (produced, used). Sources are the sheet of that year unless noted.
MT = {  # year: (file, page, method, notes, {type: (prod, used)}) in million short tons
 1966: ('ACAA-CCP-Svy-1966-1976.pdf', 1, {'fly_ash': (17.1, 1.4), 'bottom_ash': (8.1, 1.7)}, 'First survey year; boiler slag not collected (shown as -0- in later sheets).'),
 1967: ('ACAA-CCP-Svy-1966-1976.pdf', 1, {'fly_ash': (18.4, 1.4), 'bottom_ash': (9.1, 2.3)}, 'Boiler slag not collected.'),
 1968: ('ACAA-CCP-Svy-1966-1976.pdf', 1, {'fly_ash': (19.8, 1.9), 'bottom_ash': (7.3, 1.8), 'boiler_slag': (2.6, 1.5)}, ''),
 1969: ('ACAA-CCP-Svy-1966-1976.pdf', 1, {'fly_ash': (21.1, 1.9), 'bottom_ash': (7.6, 2.0), 'boiler_slag': (2.9, 1.0)}, ''),
 1970: ('ACAA-CCP-Svy-1966-1976.pdf', 1, {'fly_ash': (26.5, 2.2), 'bottom_ash': (9.9, 1.8), 'boiler_slag': (2.8, 1.1)}, ''),
 1971: ('ACAA-CCP-Svy-1966-1976.pdf', 1, {'fly_ash': (27.8, 3.3), 'bottom_ash': (10.1, 1.6), 'boiler_slag': (5.0, 3.7)}, ''),
 1972: ('ACAA-CCP-Svy-1966-1976.pdf', 1, {'fly_ash': (31.8, 3.6), 'bottom_ash': (10.7, 2.6), 'boiler_slag': (3.8, 1.3)}, ''),
 1973: ('ACAA-CCP-Svy-1966-1976.pdf', 1, {'fly_ash': (34.6, 3.9), 'bottom_ash': (10.7, 2.3), 'boiler_slag': (4.0, 1.8)}, ''),
 1974: ('ACAA-CCP-Svy-1966-1976.pdf', 1, {'fly_ash': (40.4, 3.4), 'bottom_ash': (14.3, 2.9), 'boiler_slag': (4.8, 2.4)}, ''),
 1975: ('ACAA-CCP-Svy-1966-1976.pdf', 1, {'fly_ash': (42.3, 4.5), 'bottom_ash': (13.1, 3.5), 'boiler_slag': (4.6, 1.8)}, ''),
 1976: ('ACAA-CCP-Svy-1966-1976.pdf', 1, {'fly_ash': (42.8, 5.7), 'bottom_ash': (14.3, 4.5), 'boiler_slag': (4.8, 2.2)}, ''),
 1977: ('ACAA-CCP-Svy-1977.pdf', 1, {'fly_ash': (48.5, 6.3), 'bottom_ash': (14.1, 4.6), 'boiler_slag': (5.2, 3.1)}, 'Published to 0.1 Mt; boiler slag reported as separated from bottom ash only if separated.'),
 1978: ('ACAA-CCP-Svy-1978.pdf', 1, {'fly_ash': (48.3, 8.4), 'bottom_ash': (14.7, 5.0), 'boiler_slag': (5.1, 3.0)}, 'Published to 0.1 Mt.'),
 1979: ('ACAA-CCP-Svy-1979.pdf', 1, {'fly_ash': (57.5, 10.0), 'bottom_ash': (12.5, 3.3), 'boiler_slag': (5.2, 2.4)}, 'Published to 0.1 Mt.'),
 1980: ('ACAA-CCP-Svy-1980.pdf', 1, {'fly_ash': (48.31, 6.42), 'bottom_ash': (14.45, 4.26), 'boiler_slag': (3.64, 1.75)}, ''),
 1981: ('ACAA-CCP-Svy-1981.pdf', 1, {'fly_ash': (50.26, 9.41), 'bottom_ash': (12.87, 4.07), 'boiler_slag': (5.18, 2.93)}, ''),
 1982: ('ACAA-CCP-Svy-1982.pdf', 1, {'fly_ash': (47.91, 7.95), 'bottom_ash': (13.13, 3.63), 'boiler_slag': (4.37, 1.97)}, ''),
 1983: ('ACAA-CCP-Svy-1984.pdf', 1, {'fly_ash': (47.15, 7.52), 'bottom_ash': (12.73, 2.76), 'boiler_slag': (3.94, 2.53)}, 'REVISED: values from the 1984-1986 sheets (comparative table); 1983 own sheet gave 52.35/14.0/3.94 Mt (total 70.29).'),
 1984: ('ACAA-CCP-Svy-1984.pdf', 1, {'fly_ash': (51.32, 10.43), 'bottom_ash': (13.62, 2.96), 'boiler_slag': (4.21, 2.65)}, ''),
 1985: ('ACAA-CCP-Svy-1985.pdf', 1, {'fly_ash': (48.31, 11.39), 'bottom_ash': (13.15, 4.10), 'boiler_slag': (3.65, 2.38)}, ''),
 1986: ('ACAA-CCP-Svy-1986.pdf', 1, {'fly_ash': (49.259, 8.776), 'bottom_ash': (13.411, 3.585), 'boiler_slag': (4.13, 2.145)}, 'Published to 0.001 Mt.'),
}
# exact short tons (own-year sheet): (file, page, {type: (prod, used)}, totals (prod_total, used_total) or None, note)
ST = {
 1987: ('ACAA-CCP-Svy-1987.pdf', 1, {'fly_ash': (50113178, 11049576), 'bottom_ash': (14715570, 4769054), 'boiler_slag': (4115899, 2436178), 'fgd_material': (14204638, 1021032)}, (83149285, 19275840), 'FGD column headed sludge.'),
 1988: ('ACAA-CCP-Svy-1988.pdf', 1, {'fly_ash': (50905161, 11364244), 'bottom_ash': (14272459, 5433161), 'boiler_slag': (5025540, 2833348), 'fgd_material': (13526701, 930210)}, (83729861, 20560963), ''),
 1989: ('ACAA-CCP-Svy-1989.pdf', 1, {'fly_ash': (53383591, 10153399), 'bottom_ash': (14205221, 4848288), 'boiler_slag': (4267563, 2518306), 'fgd_material': (15603436, 112635)}, (87459812, 17632627), 'FGD column headed sludge.'),
 1990: ('ACAA-CCP-Svy-1990.pdf', 1, {'fly_ash': (48931722, 12420163), 'bottom_ash': (13705653, 5360104), 'boiler_slag': (5234316, 3252220), 'fgd_material': (18932688, 215852)}, (86804378, 21248339), ''),
 1991: ('ACAA-CCP-Svy-1991.pdf', 1, {'fly_ash': (51300000, 13200000), 'bottom_ash': (13300000, 5000000), 'boiler_slag': (6050000, 3600000), 'fgd_material': (18100000, 350000)}, (88800000, 22150000), 'Sheet rounds tons to the nearest 50,000 (percentages use exact tonnage, not shown).'),
 1992: ('ACAA-CCP-Svy-1992.pdf', 1, {'fly_ash': (48061898, 13071114), 'bottom_ash': (13917623, 3870241), 'boiler_slag': (4112796, 3089714), 'fgd_material': (15883538, 289774)}, (81975855, 20320843), '1966-2013 fly ash table gives 13.10 Mt used (sheet 13.07).'),
 1993: ('ACAA-CCP-Svy-1993.pdf', 1, {'fly_ash': (47756492, 10507824), 'bottom_ash': (14215711, 4231249), 'boiler_slag': (6228523, 3424017), 'fgd_material': (20340130, 1163076)}, (88540856, 19326166), 'Heading CCB (byproduct); includes internal producer applications.'),
 1994: ('ACAA-CCP-Svy-1994.pdf', 1, {'fly_ash': (54835570, 12930690), 'bottom_ash': (14827165, 5082966), 'boiler_slag': (3785852, 3117838), 'fgd_material': (15545068, 944182)}, (88993655, 22075675), ''),
 1995: ('ACAA-CCP-Svy-1995.pdf', 1, {'fly_ash': (54166769, 13562813), 'bottom_ash': (15224269, 5068493), 'boiler_slag': (2806557, 2689309), 'fgd_material': (19974829, 1476662)}, (92172424, 22797277), ''),
 1996: ('ACAA-CCP-Svy-1996.pdf', 1, {'fly_ash': (59355009, 16234488), 'bottom_ash': (16060762, 4868253), 'boiler_slag': (2568349, 2396070), 'fgd_material': (23854328, 1656132)}, (101838447, 25154943), 'OCR; closes on sum and on printed utilisation percentages.'),
 1997: ('ACAA-CCP-Svy-1997.pdf', 1, {'fly_ash': (60264791, 19317362), 'bottom_ash': (16904663, 5096905), 'boiler_slag': (2741614, 2578851), 'fgd_material': (25163394, 2183363)}, (105074462, 29176481), 'OCR; closes on sum and on printed utilisation percentages.'),
 1998: ('ACAA-CCP-Svy-1998.pdf', 1, {'fly_ash': (62995872, 21105468), 'bottom_ash': (16760091, 5239184), 'boiler_slag': (2980627, 2387737), 'fgd_material': (25002877, 2494262)}, (107739467, 31226651), 'OCR; closes on sum and on printed utilisation percentages.'),
 1999: ('ACAA-CCP-Svy-1999.pdf', 1, {'fly_ash': (62699947, 20793473), 'bottom_ash': (16875991, 5420676), 'boiler_slag': (2890843, 2363464), 'fgd_material': (24608099, 4452405)}, (107074879, 33030018), 'Visual read.'),
 2000: ('2000_CCP_Production_and_Use_Survey.pdf', 1, {'fly_ash': (62943732, 20076909), 'bottom_ash': (16915826, 4937908), 'boiler_slag': (2684889, 2321568), 'fgd_material': (25652994, 4824727)}, (108197440, 32161112), 'Visual read.'),
 2001: ('2001_rev_svy_11-02.pdf', 1, {'fly_ash': (68123551, 22004955), 'bottom_ash': (18788004, 5712398), 'boiler_slag': (2536195, 1818473), 'fgd_material': (28482792, 7583495)}, (117930542, 37119321), 'File is a revised release (11-02); text layer.'),
}
# 2016-2020, 2022, 2024: visually read from scans. order = STD + total.
SC = {
 2016: ('2016-Survey-Results.pdf', [37817327, 10135360, 2188298, 32006516, 9556694, 1448752, 7508, 14267412, 107427866], [22634497, 3775480, 1310959, 18372663, 896141, 310607, 0, 12869437, 60169785]),
 2017: ('2017-Survey-Results.pdf', [38189790, 9655931, 2574673, 32707136, 11311344, 2454818, 6293, 14469553, 111369538], [24095590, 4839420, 1570375, 22839385, 3905009, 382048, 2407, 14134477, 71768712]),
 2018: ('2018-Survey-Results.pdf', [36178427, 9197362, 1534945, 32783995, 4732900, 2154301, 121126, 15571824, 102274881], [20081330, 4350321, 1036919, 18337477, 91036, 498532, 0, 15045225, 59440839]),
 2019: ('2019-Survey-Results.pdf', [29319239, 9150680, 965138, 22975581, 6217129, 3707974, 18428, 6293721, 78647890], [17768235, 2923586, 697001, 13285876, 359529, 90346, 0, 5882468, 41007041]),
 2020: ('2020-Production-and-Use-Survey-Results-FINAL.pdf', [26512322, 7973554, 834131, 17677439, 6065567, 2833942, 41364, 7217772, 69156091], [17104493, 2955653, 369729, 13147742, 292553, 106256, 2193, 6809788, 40788407]),
 2022: ('2022-Production-and-Use-Survey-Results-FINAL.pdf', [28227974, 7576840, 1565764, 17308377, 4576313, 3214471, 0, 12772198, 75241938], [16831464, 2981553, 733028, 14428769, 4677, 42903, 0, 11813474, 46835868]),
 2024: ('2024-Production-and-Use-Survey-Results-FINAL.pdf', [24718600, 7666800, 1580936, 16860200, 5122215, 1687795, 52602, 5885300, 63574448], [19386568, 2720561, 889947, 17142322, 0, 6388, 7255, 5885300, 46038342]),
}

SC_ORDER = ['fly_ash', 'bottom_ash', 'boiler_slag', 'fgd_gypsum', 'fgd_wet', 'fgd_dry', 'fgd_other', 'fbc_ash', 'total_ccp']
# use rows read visually (key categories only) for 2016-2024: {year: {use: {type: tons}}}
UH = {
 2016: {'structural_fill': {'fly_ash': 1696296, 'bottom_ash': 745213, 'fgd_gypsum': 1490267, 'fgd_wet': 896141},
        'mining_applications': {'fly_ash': 1043002, 'bottom_ash': 211670, 'fgd_gypsum': 794133, 'fgd_dry': 131738, 'fbc_ash': 12729673},
        'waste_stabilisation': {'fly_ash': 767895, 'bottom_ash': 318516, 'fgd_gypsum': 3632056, 'fgd_dry': 109244, 'fbc_ash': 139765},
        'ccr_pond_closure': {'fly_ash': 254521, 'bottom_ash': 3142, 'fgd_gypsum': 177013}, 'oil_gas_field_services': {'fly_ash': 190247, 'fgd_dry': 7904}},
 2017: {'structural_fill': {'fly_ash': 465653, 'bottom_ash': 871875},
        'mining_applications': {'fly_ash': 901181, 'bottom_ash': 232110, 'fgd_gypsum': 927949, 'fgd_wet': 3905009, 'fgd_dry': 202092, 'fbc_ash': 14037913},
        'waste_stabilisation': {'fly_ash': 1065993, 'bottom_ash': 48964, 'fgd_gypsum': 3026, 'fgd_dry': 114646, 'fbc_ash': 96564},
        'ccr_pond_closure': {'fly_ash': 1468203, 'bottom_ash': 730600, 'fgd_gypsum': 2270326}, 'oil_gas_field_services': {'fly_ash': 78716, 'fgd_dry': 11188}},
 2019: {'structural_fill': {'fly_ash': 501668, 'bottom_ash': 532676, 'boiler_slag': 67104, 'fgd_gypsum': 617122},
        'mining_applications': {'fly_ash': 17282, 'fbc_ash': 5831652},
        'waste_stabilisation': {'fly_ash': 604222, 'bottom_ash': 57689, 'fgd_gypsum': 16503, 'fgd_dry': 11858, 'fbc_ash': 47374},
        'ccr_pond_closure': {'fly_ash': 720411, 'bottom_ash': 357558, 'boiler_slag': 304592, 'fgd_gypsum': 713573, 'fgd_wet': 276826}, 'oil_gas_field_services': {'fly_ash': 152053, 'bottom_ash': 436, 'fgd_dry': 8128}},
 2020: {'structural_fill': {'fly_ash': 306379, 'bottom_ash': 510165},
        'mining_applications': {'fly_ash': 53930, 'fbc_ash': 6730060},
        'waste_stabilisation': {'fly_ash': 1117551, 'bottom_ash': 43634, 'fgd_gypsum': 118854, 'fgd_dry': 13415, 'fbc_ash': 73216},
        'ccr_pond_closure': {'fly_ash': 1558156, 'bottom_ash': 1026079, 'fgd_gypsum': 537176, 'fgd_wet': 292553}, 'oil_gas_field_services': {'fly_ash': 64163, 'fgd_dry': 6816}},
 2022: {'structural_fill': {'fly_ash': 207979, 'bottom_ash': 829295},
        'mining_applications': {'fbc_ash': 11813474},
        'waste_stabilisation': {'fly_ash': 852295, 'fgd_wet': 4677, 'fgd_dry': 10220},
        'ccr_pond_closure': {'fly_ash': 1221559, 'bottom_ash': 401725, 'fgd_gypsum': 140430}, 'oil_gas_field_services': {'fly_ash': 2499, 'fgd_dry': 32682}},
 2024: {'structural_fill': {'fly_ash': 97871, 'bottom_ash': 175649},
        'mining_applications': {'bottom_ash': 11592, 'fbc_ash': 5443670},
        'waste_stabilisation': {'fly_ash': 14517},
        'ccr_pond_closure': {'bottom_ash': 7364}, 'oil_gas_field_services': {'fly_ash': 9345, 'fgd_other': 7255}},
}
# 1999/2000 full use tables (4 columns: fly, bottom, slag, FGD material)
U4 = {
 1999: ('ACAA-CCP-Svy-1999.pdf', {
  'concrete_grout': (10084584, 701342, 11133, 289849), 'blended_cement_clinker': (1268000, 157027, 0, 0), 'flowable_fill': (847425, 13031, 0, 0),
  'structural_fill': (3204501, 1385413, 51983, 577615), 'road_base': (1216861, 1102254, 5513, 17398), 'soil_modification': (78154, 17444, 12941, 2095),
  'mineral_filler_asphalt': (158934, 62567, 12424, 0), 'snow_ice_control': (3201, 1108184, 50877, 0), 'blasting_grit_roofing': (0, 156777, 2132354, 0),
  'mining_applications': (1527272, 154481, 10000, 231463), 'gypsum_panel': (0, 0, 0, 3053268), 'waste_stabilisation': (1929150, 68996, 0, 15603),
  'agriculture': (13924, 42665, 0, 80463), 'miscellaneous': (461467, 450495, 76239, 184651)}),
 2000: ('2000_CCP_Production_and_Use_Survey.pdf', {
  'concrete_grout': (10586168, 419832, 276, 350928), 'blended_cement_clinker': (1133911, 173813, 0, 0), 'flowable_fill': (696675, 10958, 18000, 33452),
  'structural_fill': (2611054, 1351390, 35683, 547017), 'road_base': (1207750, 836568, 13, 93519), 'soil_modification': (111896, 27907, 0, 0),
  'mineral_filler_asphalt': (119011, 102063, 12424, 984), 'snow_ice_control': (3076, 831708, 58206, 0), 'blasting_grit_roofing': (0, 146983, 2098577, 0),
  'mining_applications': (1151536, 366584, 0, 182829), 'gypsum_panel': (0, 0, 0, 3328651), 'waste_stabilisation': (1986277, 35787, 0, 21031),
  'agriculture': (13979, 4748, 0, 75922), 'miscellaneous': (455576, 629567, 98389, 190394)}),
}
U4_TYPES = ['fly_ash', 'bottom_ash', 'boiler_slag', 'fgd_material_all']

def uses_2001():
    out = []
    L = txt('2001_rev_svy_11-02.pdf').split('\n')
    on = False
    for l in L:
        if re.match(r'\s*CCP Use\s*$', l): on = True; continue
        if on and 'Total Use' in l: break
        if on:
            m = re.match(r'^\s*([A-Za-z][A-Za-z/ ]+?)\s{2,}([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s*$', l)
            if m:
                cat = norm_use(m.group(1)); v = [int(m.group(i).replace(',', '')) for i in range(2, 6)]
                for t, x in zip(U4_TYPES, v):
                    if x: out.append(dict(year=2001, ccp_type=t, use_category=cat, used_short_tons=x, source_file='2001_rev_svy_11-02.pdf', page=1,
                                          extraction_method='table', notes='Total CCPs block (Category I + II); ACAA label: ' + m.group(1).strip() + '; FGD material not split.'))
    return out

# 1994/1995 key categories (external + internal producer applications summed for structural fills), visual read
U9495 = {
 1994: {'structural_fill': (1211071, 478996), 'mining_applications': (80023, 28769), 'waste_stabilisation': (231028, 23331)},
 1995: {'structural_fill': (1232581, 450940), 'mining_applications': (478610, 30418), 'waste_stabilisation': (832232, 148451)},
}

def row(year, t, p, u, f, page, note='', status='adopted', method='table', tot=False):
    return dict(year=year, ccp_type=t, produced_short_tons=p, used_short_tons=u,
                use_fraction=(None if (p in (None, 0) or u is None) else u / p), source_file=f, page=page,
                extraction_method=method, status=status, notes=note)

def build():
    rows, uses, qa = [], [], []
    # --- million-ton years
    for y, (f, pg, d, note) in MT.items():
        P = U = 0
        for t, (p, u) in d.items():
            rows.append(row(y, t, round(p * 1e6), round(u * 1e6), f, pg, note if t == 'fly_ash' else '', 'adopted'))
            P += p; U += u
        rows.append(row(y, 'fa_ba_bs_subtotal', round(P * 1e6), round(U * 1e6), f, pg,
                        'Sum of fly, bottom and boiler slag as published in million short tons (the sheet total may differ by rounding).', 'adopted'))
    # superseded 1983 own sheet
    for t, (p, u) in {'fly_ash': (52.35, 7.52), 'bottom_ash': (14.0, 2.76), 'boiler_slag': (3.94, 2.53)}.items():
        rows.append(row(1983, t, round(p * 1e6), round(u * 1e6), 'ACAA-CCP-Svy-1983.pdf', 1, 'Own-year sheet (total ash 70.29 Mt); superseded by the revised production in the 1984+ sheets.', 'superseded'))
    # --- short-ton years 1987-2001
    for y, (f, pg, d, tot, note) in ST.items():
        P = U = 0
        for t, (p, u) in d.items():
            tt = 'fgd_material_all' if t == 'fgd_material' else t
            rows.append(row(y, tt, p, u, f, pg, note if t == 'fly_ash' else ''))
            if t != 'fgd_material': P += p; U += u
        rows.append(row(y, 'fa_ba_bs_subtotal', P, U, f, pg, 'Sum of the three ash types (equals the sheet subtotal where printed).'))
        rows.append(row(y, 'total_ccp', tot[0], tot[1], f, pg, 'Sheet total of all byproducts/CCPs incl. FGD material.'))
        if abs(P + d['fgd_material'][0] - tot[0]) > 2 or abs(U + d['fgd_material'][1] - tot[1]) > 2:
            qa.append(('sum-mismatch', y, P + d['fgd_material'][0] - tot[0], U + d['fgd_material'][1] - tot[1]))
    # --- text years
    for y in sorted(FILES):
        r, order, f, pg = parse_text_year(y)
        p, u = r['prod'], r['used']
        assert len(p) >= 8 and len(u) >= 8, (y, p, u)
        D = {t: (p[i], u[i]) for i, t in enumerate(order)}
        for t in ('fly_ash', 'bottom_ash', 'boiler_slag', 'fgd_gypsum', 'fbc_ash'):
            note = ''
            if y == 2007 and t == 'fbc_ash':
                D[t] = (p[9], u[9]); note = '2007: FBC combined with ARIPPA data (6,092,756 t produced); survey-respondent-only FBC was 1,273,061 produced / 323,741 used (see superseded alt row).'
            rows.append(row(y, t, D[t][0], D[t][1], f, pg, note))
        ow = sum(D[k][0] for k in ('fgd_wet', 'fgd_dry', 'fgd_other')); ou = sum(D[k][1] for k in ('fgd_wet', 'fgd_dry', 'fgd_other'))
        comp = '; '.join('%s %d/%d' % (k.replace('fgd_', ''), D[k][0], D[k][1]) for k in ('fgd_wet', 'fgd_dry', 'fgd_other'))
        rows.append(row(y, 'other_fgd', ow, ou, f, pg, 'Wet + dry + other FGD (produced/used): ' + comp))
        P = sum(D[k][0] for k in ('fly_ash', 'bottom_ash', 'boiler_slag')); U = sum(D[k][1] for k in ('fly_ash', 'bottom_ash', 'boiler_slag'))
        rows.append(row(y, 'fa_ba_bs_subtotal', P, U, f, pg, 'Sum of the three ash types.'))
        if y in (2002, 2003, 2004, 2005, 2006): tp, tu = r['tot_p'], r['tot_u']
        elif y == 2007: tp, tu = p[10], u[10]
        else: tp, tu = p[8], u[8]
        note = 'Sheet total.' if y != 2007 else 'Total incl. ARIPPA FBC; 2008 sheet states 2007 utilisation should read 44.81%, not 42.74%, after under-reporting was detected (not re-tabulated).'
        rows.append(row(y, 'total_ccp', tp, tu, f, pg, note))
        cs = sum(v[0] for v in D.values()) if y != 2007 else sum(D[k][0] for k in D if k != 'fbc_ash') + D['fbc_ash'][0]
        cu = sum(v[1] for v in D.values()) if y != 2007 else sum(D[k][1] for k in D if k != 'fbc_ash') + D['fbc_ash'][1]
        if y == 2007:
            # D['fbc_ash'] was replaced by the ARIPPA-combined values for 2007; the printed total (131,127,693) reflects that
            pass
        if abs(cs - tp) > 3 or abs(cu - tu) > 3: qa.append(('sum-mismatch', y, cs - tp, cu - tu))
        if y == 2007:
            rows.append(row(y, 'fbc_ash', p[7], u[7], f, pg, 'Survey-respondent-only FBC (not combined with ARIPPA).', 'superseded'))
        # uses
        for k, (label, n) in r['uses'].items():
            cat = norm_use(label)
            for i, t in enumerate(order):
                if y == 2007 and t == 'fbc_ash' and len(n) > 9: n = list(n); n[i] = n[9]
                if i < len(n) and n[i]:
                    uses.append(dict(year=y, ccp_type=t, use_category=cat, used_short_tons=n[i], source_file=f, page=pg,
                                     extraction_method='table', notes='ACAA label: ' + label))
        # use-row column sums vs category totals
        for i, t in enumerate(order):
            s_ = sum((n[9] if (y == 2007 and t == 'fbc_ash') else n[i]) for (lab, n) in r['uses'].values() if i < len(n))
            if t in D and abs(s_ - D[t][1]) > max(3, 0.0005 * D[t][1]) :
                qa.append(('use-sum', y, t, s_ - D[t][1]))
    # --- scan years 2016-2024
    for y, (f, p, u) in SC.items():
        D = dict(zip(SC_ORDER, zip(p, u)))
        for t in ('fly_ash', 'bottom_ash', 'boiler_slag', 'fgd_gypsum', 'fbc_ash'):
            rows.append(row(y, t, *D[t], f, 1, 'Scan read visually.'))
        rows.append(row(y, 'other_fgd', D['fgd_wet'][0] + D['fgd_dry'][0] + D['fgd_other'][0], D['fgd_wet'][1] + D['fgd_dry'][1] + D['fgd_other'][1], f, 1,
                        'Wet + dry + other FGD (produced/used): wet %d/%d; dry %d/%d; other %d/%d' % (D['fgd_wet'] + D['fgd_dry'] + D['fgd_other'])))
        rows.append(row(y, 'fa_ba_bs_subtotal', sum(D[k][0] for k in ('fly_ash', 'bottom_ash', 'boiler_slag')), sum(D[k][1] for k in ('fly_ash', 'bottom_ash', 'boiler_slag')), f, 1, 'Sum of the three ash types.'))
        rows.append(row(y, 'total_ccp', *D['total_ccp'], f, 1, 'Sheet total.'))
        cs = sum(D[k][0] for k in SC_ORDER[:-1]); cu = sum(D[k][1] for k in SC_ORDER[:-1])
        if abs(cs - D['total_ccp'][0]) > 3 or abs(cu - D['total_ccp'][1]) > 3: qa.append(('sum-mismatch', y, cs - D['total_ccp'][0], cu - D['total_ccp'][1]))
    for y, d in UH.items():
        f = SC[y][0]
        for cat, dd in d.items():
            for t, v in dd.items():
                uses.append(dict(year=y, ccp_type=t, use_category=cat, used_short_tons=v, source_file=f, page=1, extraction_method='table',
                                 notes='Key categories only; scan read visually.'))
    uses.extend(uses_2001())
    for y, d in U9495.items():
        for cat, (fa, ba) in d.items():
            for t, v in (('fly_ash', fa), ('bottom_ash', ba)):
                uses.append(dict(year=y, ccp_type=t, use_category=cat, used_short_tons=v, source_file='ACAA-CCP-Svy-%d.pdf' % y, page=1, extraction_method='table',
                                 notes='Key categories only; scan read visually' + ('; external market + internal producer applications summed' if cat == 'structural_fill' and y == 1994 else '') + '.'))
    for y, (f, d) in U4.items():
        for cat, vals in d.items():
            for t, v in zip(U4_TYPES, vals):
                if v: uses.append(dict(year=y, ccp_type=t, use_category=cat, used_short_tons=v, source_file=f, page=1, extraction_method='table', notes='Scan read visually; FGD material not split.'))
    return rows, uses, qa

def write(rows, uses):
    rows.sort(key=lambda r: (r['year'], r['ccp_type'], r['status']))
    cols = ['year', 'ccp_type', 'produced_short_tons', 'used_short_tons', 'use_fraction', 'produced_t', 'used_t', 'source_file', 'page', 'extraction_method', 'status', 'notes']
    with open(os.path.join(OUT, 'acaa_series.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, cols); w.writeheader()
        for r in rows:
            r = dict(r)
            r['produced_t'] = None if r['produced_short_tons'] is None else round(r['produced_short_tons'] * ST2T)
            r['used_t'] = None if r['used_short_tons'] is None else round(r['used_short_tons'] * ST2T)
            r['use_fraction'] = '' if r['use_fraction'] is None else '%.4f' % r['use_fraction']
            w.writerow({k: ('' if r.get(k) is None else r.get(k)) for k in cols})
    uses.sort(key=lambda r: (r['year'], r['ccp_type'], r['use_category']))
    ucols = ['year', 'ccp_type', 'use_category', 'used_short_tons', 'used_t', 'source_file', 'page', 'extraction_method', 'notes']
    with open(os.path.join(OUT, 'acaa_uses.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, ucols); w.writeheader()
        for r in uses:
            r = dict(r); r['used_t'] = round(r['used_short_tons'] * ST2T); w.writerow(r)

if __name__ == '__main__':
    rows, uses, qa = build()
    write(rows, uses)
    print(len(rows), 'series rows;', len(uses), 'use rows')
    for q in qa: print('QA', q)
