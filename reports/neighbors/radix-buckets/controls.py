"""Matched-library controls and extra exact-membership batch checks."""
import sys,json,random
from pathlib import Path
sys.path.insert(0,'tools')
from evaluate import ROOT,run,parse_stats,write_json,tree_hash
from neighbors_gate import driver,validate_rows,oracle,synthetic
out=ROOT/'reports/neighbors/radix-buckets';argv=[sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib','sph='+str(out/'sph'),'--heap','2G']
controls=[]
for name,pts,qs in synthetic():
 if not name.startswith('scaling_'):continue
 path=out/(name+'_control.vi');driver(pts,qs,path,'candidate')
 r=run(argv+['--depth',str(path)],ROOT,path.with_suffix(''),180)
 assert int(Path(r['stdout']).read_text())==sum(i+1 for q in qs for i in oracle(pts,q))
 controls.append(dict(case=name,**parse_stats(Path(r['stderr']).read_text())))
write_json(out/'controls.json',controls)
points=[(i,0.,0.,0.) for i in range(64)]
cases=[('empty_queries',points,[]),('coincident64',points,[(*p,1.,0.) for p in points[::8]])]
rng=random.Random(2291)
for i in range(3):
 points=[(k,rng.uniform(-10,10),rng.uniform(-10,10),rng.uniform(0,20)) for k in range(150)]
 cases.append((f'random{i}',points,[(*p,rng.uniform(.01,4),20.) for p in points[::10]]))
checks=[]
for name,pts,qs in cases:
 path=out/(name+'_extra.vi');driver(pts,qs,path)
 s=path.read_text().replace('tree::map(queries,fn* ((i,q)) {(i,neighbors::find(index,q))})','neighbors::find_batch(index,queries)');path.write_text(s)
 r=run(argv+[str(path)],ROOT,path.with_suffix(''),180)
 validate_rows(Path(r['stdout']).read_text(),[oracle(pts,q) for q in qs]);checks.append({'case':name,'passed':True})
write_json(out/'extra-checks.json',checks)
write_json(out/'final-source.json',tree_hash(out/'sph'))
print(json.dumps({'controls':controls,'extra_checks':checks},indent=2))
