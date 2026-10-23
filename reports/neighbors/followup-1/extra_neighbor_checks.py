import sys,random
from pathlib import Path
sys.path.insert(0,'tools')
from neighbors_gate import driver,oracle,validate_rows
from evaluate import ROOT,run,write_json
out=ROOT/'reports/neighbors/eager-cached-extra';out.mkdir(parents=True,exist_ok=True)
cases=[]
points=[(i,0.,0.,0.) for i in range(64)];cases.append(('coincident64',points,[(*p,1.,0.) for p in points[::8]]))
points=[(i,0.,i*.125,0.) for i in range(96)];cases.append(('collinear96',points,[(*p,.5,0.) for p in points[::8]]))
rng=random.Random(33419)
for seed in range(3):
 points=[(i,rng.uniform(-10,10),rng.uniform(-10,10),rng.uniform(0,20)) for i in range(150)]
 cases.append((f'cloud{seed}',points,[(*p,rng.uniform(.01,4),20.) for p in points[::10]]))
results=[]
for name,pts,qs in cases:
 path=out/(name+'.vi');driver(pts,qs,path)
 r=run([sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib','sph='+str(ROOT/'benchmarks/sph-exa/vine'),str(path)],ROOT,out/name,180)
 validate_rows(Path(r['stdout']).read_text(),[oracle(pts,q) for q in qs])
 results.append({'case':name,'queries':len(qs),'passed':True});print(results[-1],flush=True)
write_json(out/'result.json',results)
