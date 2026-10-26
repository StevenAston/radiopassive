import sys; sys.path.insert(0,'/tmp/claude-0/-home-claude/7f015155-d930-5c34-900b-ab275f11b117/scratchpad/task19/scripts')
import csv,re,glob
from ds140 import *
from ds140_comm import WB
H=['source_id','short_cite','full_citation','url','doi','year','type','rank','access','licence','notes']
old=list(csv.reader(open('/mnt/user-data/outputs/research/activity/sources_task19.csv')))
rows=[r for r in old[1:] if int(r[0][1:])<=820]
S3='https://d9-wret.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/media/files/'
used={}
for wbk,(wb,sid) in WB.items():
    sheets=sorted(f for f in os.listdir(D+wb))
    first=D+wb+'/'+sheets[0]
    comp=''
    for r in csv.reader(open(first,encoding='utf-8-sig')):
        if r and 'Compiled by' in r[0]: comp=re.sub(r'^\d','',r[0]).strip().rstrip('.'); break
    m=mod(wb,sheets[0][:-4]); yr=int(re.search(r'-(\d{4})\.xlsx',wb).group(1))
    title=wb[:-5]
    rows.append([sid,'USGS DS140 %s'%title.replace('ds140-',''),
      'U.S. Geological Survey, National Minerals Information Center. Historical statistics for mineral and material commodities in the United States, Data Series 140: workbook %s.xlsx (%s; last modified %s). Series cited as Kelly, T., Matos, G., Buckingham, D.A., DiFrancesco, C.A., Porter, K.E., Berry, C., Crane, M., Goonan, T. and Sznopek, J. (2005), USGS Data Series 140, https://doi.org/10.3133/ds140.'%(title,comp or 'compiler line not in CSV',m),
      S3+title+'.xlsx','10.3133/ds140',yr,'agency',4,'open','open',
      'READ from Steve Aston\'s community mirror of the USGS S3 bucket (collected 15-16 Oct 2026; derived CSV exports of each sheet, staged read-only at usgs.140/derived/csv/s3fs-public/media/files/%s.xlsx/). Original URL pattern: https://d9-wret.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/media/files/%s.xlsx (HEAD returned 200 on 25 Oct 2026; the usgs.gov/media/files pages returned 403). Mirror DOI not yet minted (10.5281/zenodo.XXXXXXX placeholder). US statistics with a world-production column; USGS public domain. CSV conversion keeps NA/W as text.'%(title,title)])
rows.append(['S0846','FAOSTAT Forestry production and trade','Food and Agriculture Organization of the United Nations (accessed 25 Oct 2026). FAOSTAT Forestry Production and Trade, bulk file Forestry_E_All_Data_(Normalized).csv (last updated 2026-04-01): items 1864 Wood fuel (m3) and 1630 Wood charcoal (t), production, 1961-2024.','https://bulks-faostat.fao.org/production/Forestry_E_All_Data_(Normalized).zip','',2026,'compilation',2,'open','open','DOWNLOADED (18 MB zip). Roundwood-equivalent volumes; many developing-country values are FAO estimates (flag E) from household surveys, so the quality is lower than the official flag suggests. No World aggregate problems for wood fuel; the charcoal World row exists. CC BY-4.0 (FAOSTAT terms).'])
rows.append(['S0847','UNSD Energy Statistics database (SDMX API)','United Nations Statistics Division (accessed 25 Oct 2026). Energy Statistics Database, dataflow UNSD:DF_UNDATA_ENERGY(1.2): commodities 1100 Peat, 5110 Fuelwood, 5160 Charcoal; transactions 01 Production, GA Total energy supply, 1231 Consumption by households, 08811/08812/08821/08822 electricity and CHP transformation; annual, 1990-2024.','https://data.un.org/WS/rest/data/UNSD,DF_UNDATA_ENERGY,/','',2026,'compilation',2,'open','open','DOWNLOADED via the SDMX REST API with the CSV Accept header (4.3 MB). Country questionnaire data; a substitute for the paywalled/restricted IEA World Energy Balances (residential final consumption of primary solid biofuels). Units: peat in thousand tonnes, fuelwood in thousand m3, charcoal in thousand tonnes (UNIT_MULT 3). Starts 1990 (peat and fuelwood for the former USSR republics from 1992). China reports no household fuelwood. Database notes: http://data.un.org/_Docs/Energy_Statistics_Database_notes_UNdata.pdf.'])
rows.append(['S0848','FAO/ITTO/UNECE/Eurostat Joint Forest Sector Questionnaire conversion factors (fuelwood)','FAO. Conversion factors from the Joint ITTO/UNECE/FAO/Eurostat Joint Forest Sector Survey guidelines, Table of weight and volume (densities) and energy equivalents: fuelwood general 725 kg/m3 (coniferous 625, non-coniferous 750); 1 m3 solid fuelwood at 20-30% moisture 9.40 GJ (0% moisture 14.0; green 7.2).','https://www.fao.org/4/ad353e/AD353e12.htm','',2026,'agency',4,'open','open','READ (web page; publication year not stated on the page, so year = access year). Moisture basis of the density values is not stated; the page itself is inconsistent about the moisture range (20-30% vs 20-40%).'])
with open('/mnt/user-data/outputs/research/activity/sources_task19.csv','w',newline='',encoding='utf-8') as f:
    w=csv.writer(f,lineterminator='\n'); w.writerow(H); w.writerows(rows)
print(len(rows))
