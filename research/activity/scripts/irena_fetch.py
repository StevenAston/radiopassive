import json,subprocess,sys
import os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from lib import RAW
U="https://pxweb.irena.org/api/v1/en/IRENASTAT/Power%20Capacity%20and%20Generation/Country_ELECSTAT_2026_H2_PX.px"
m=json.load(open(RAW+'irena_meta.json'))
cv=m['variables'][0]['values']
techs=['2','3','4','5','6','7','8','9','10','11','12','14','15','16','17','20','21','23','25','13','19','18','22']
for dt in ['0','1']:
  for t in techs:
    q={"query":[{"code":"Country/area","selection":{"filter":"item","values":cv}},{"code":"Technology","selection":{"filter":"item","values":[t]}},{"code":"Data Type","selection":{"filter":"item","values":[dt]}},{"code":"Grid connection","selection":{"filter":"item","values":["0"]}},{"code":"Year","selection":{"filter":"all","values":["*"]}}],"response":{"format":"csv"}}
    fn=RAW+f'irena_{dt}_{t}.csv'
    r=subprocess.run(['curl','-sS','-m','120','-X','POST','-H','Content-Type: application/json','-d',json.dumps(q),'-o',fn,'-w','%{http_code} %{size_download}',U],capture_output=True,text=True)
    print(dt,t,r.stdout,r.stderr[:80],flush=True)
