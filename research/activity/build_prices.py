import sys; sys.path.insert(0,'/tmp/claude-0/-home-claude/7f015155-d930-5c34-900b-ab275f11b117/scratchpad/task19/scripts')
from lib import *
from ds140_comm import *
O=Out('commodity_prices')
for wbk,sh,ser,mult,pcol,cser,ccol,plab,desc in SP:
    if not plab: continue
    wb,sid=WB[wbk]; h,d,_=load(wb,sh); md=mod(wb,sh)
    nom=[c for c in h if c.lower().startswith('unit value') and '98' not in c][0]
    real=[c for c in h if c.lower().startswith('unit value') and '98' in c][0]
    cite='USGS DS140 %s, sheet %s (last modified %s); read from the mirror of the USGS S3 bucket.'%(wb[:-5],sh,md)
    for y in sorted(d):
        if y>2025: continue
        for col,sname,unit,what in((nom,'price_%s_usd_t'%plab,'USD/t','nominal (current) US dollars'),(real,'price_%s_usd98_t'%plab,'USD1998/t','constant 1998 US dollars')):
            v=d[y][col]
            if v is None or v<=0: continue
            rel=(0.10 if y<1950 else 0.05)*(2 if plab in('rare_earths','thorium') else 1)
            O.add(sname,y,'USA',*bands(v,rel),unit,'compiled',sid,'%s US unit value of %s per tonne of %s (DS140 column "%s"), in %s. A US-market value (unit value of apparent consumption/market price as defined by USGS for this commodity), not a world price. Bands assumed: +-10%% before 1950, +-5%% after (x2 for rare earths and thorium).'%(cite,plab.replace('_',' '),desc,col,what))
O.write()
