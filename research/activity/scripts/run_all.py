"""Run every Task 1.9 builder in dependency order.

  python3 run_all.py --raw research/activity/raw --mirror /path/to/usgs.140 [--write]

Without --write the outputs go to research/activity/out/ (data/activity/ is never touched).
Order matters: build_coal writes eta_us.json (read by build_og); build_nuc must precede build_cap.
The mirror is only needed by build_comm, build_prices and make_sources2.
"""
import subprocess,sys,os
HERE=os.path.dirname(os.path.abspath(__file__))
ORDER=['build_elec','build_coal','build_og','build_u','build_nuc','build_cap','build_comm','build_prices','build_bio','build_peat','make_sources','make_sources2']
for b in ORDER:
    print('==',b,flush=True)
    r=subprocess.run([sys.executable,'-I',os.path.join(HERE,b+'.py')]+sys.argv[1:],capture_output=True,text=True)
    if r.returncode: print(r.stdout[-1500:],r.stderr[-3000:]); sys.exit(r.returncode)
print('done')
