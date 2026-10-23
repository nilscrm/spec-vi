"""Independent extra membership fixtures for the experimental grid, both APIs."""
import sys,json,random,math
from pathlib import Path
sys.path.insert(0,'tools')
from evaluate import ROOT,run,write_json,tree_hash
from neighbors_gate import driver,oracle,validate_rows
from toolchain import verify
out=ROOT/'reports/neighbors/cell-filter/extra';out.mkdir(exist_ok=True);lib=ROOT/'reports/neighbors/cell-filter/filtered/sph';verify();cases=[]
def add(name,pts,qs):cases.append(dict(name=name,points=pts,queries=qs,expected=[oracle(pts,q) for q in qs]))
add('empty_queries',[(0,0.,0.,0.)],[])
add('both_empty',[],[])
p=[(i,1.,-2.,3.) for i in range(64)];add('coincident',p,[(i,1.,-2.,3.,.1,0.) for i in [0,63,100]])
for axis in range(3):
 p=[]
 for i in range(65):
  xyz=[0.,0.,0.];xyz[axis]=(i-32)/16;p.append((i,*xyz))
 add('line'+str(axis),p,[(p[i][0],*p[i][1:],.125,0.) for i in [0,1,16,32,48,64]])
# Uniform quarter cut planes and their immediately adjacent representable values.
coords=[0.,1.]
for x in [.25,.5,.75]:coords.extend([math.nextafter(x,-math.inf),x,math.nextafter(x,math.inf)])
p=[(i,x,0.,0.) for i,x in enumerate(coords)]
qs=[]
for i,x,_,_ in p:
 for r in [math.nextafter(.25,0.),.25,math.nextafter(.25,math.inf)]:qs.append((i,x,0.,0.,r,0.))
add('cuts_and_radius_ulps',p,qs)
p=[(i,0.,0.,z) for i,z in enumerate([0.,math.nextafter(0.,1.),.25,.5,.75,math.nextafter(1.,0.),1.])]
qs=[(i,0.,0.,z,r,1.) for i,_,_,z in p for r in [.0001,.25,math.nextafter(.5,0.)]]
add('periodic_union',p,qs)
for seed in range(8):
 rng=random.Random(9980+seed);n=33+seed*7
 p=[(i,rng.uniform(-2,3),rng.uniform(-1,2),rng.random()*4) for i in range(n)];rng.shuffle(p)
 qs=[(i,x,y,z,rng.uniform(.02,1.8),4.) for i,x,y,z in p[::2]]
 qs=qs[::-1]+qs[:3]+[(n+9,9.,-7.,2.,.3,4.)]
 add('random3d_'+str(seed),p,qs)
write_json(out/'fixtures.json',cases);results=[]
for c in cases:
 for api in ['single','batch']:
  p=out/(c['name']+'_'+api+'.vi');driver(c['points'],c['queries'],p,'correctness')
  if api=='batch':p.write_text(p.read_text().replace('tree::map(queries,fn* ((i,q)) {(i,neighbors::find(index,q))})','neighbors::find_batch(index,queries)'))
  r=run([sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib','sph='+str(lib),'--heap','2G',str(p)],ROOT,p.with_suffix(''),180)
  validate_rows(Path(r['stdout']).read_text(),c['expected']);results.append(dict(case=c['name'],api=api,queries=len(c['queries']),passed=True));print(c['name'],api,'passed',flush=True)
  write_json(out/'result.json',{'passed':True,'library':tree_hash(lib),'cases':results})
