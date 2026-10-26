import json,sys
src,out=sys.argv[1],sys.argv[2]
d={}
with open(src) as f:
    for line in f:
        r=json.loads(line)
        if r.get('f')!='A' or 'series_id' not in r: continue
        sid=r['series_id']  # INTL.p-a-GEO-U.A
        p=sid[5:].split('-')
        prod,act,geo,unit=p[0],p[1],p[2],p[3].split('.')[0]
        d[sid]={'name':r['name'],'geo':geo,'unit':unit,'data':{int(y):v for y,v in r['data'] if v is not None and v!='--' and v!='NA' and v!='W'  and isinstance(v,(int,float))}}
json.dump(d,open(out,'w'))
print(len(d))
