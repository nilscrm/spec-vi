"""Diagnostic only: host Morton ordering excluded, never acceptance evidence."""
import sys,json
from pathlib import Path
sys.path.insert(0,'tools')
from evaluate import ROOT,run,parse_stats,write_json
from neighbors_gate import driver,validate_rows,oracle
from toolchain import verify
verify();out=ROOT/'reports/neighbors/bottom-up-batch'
fixtures=json.loads((ROOT/'reports/neighbors/eager-cached-validation/fixtures.json').read_text());rows=[]
for c in fixtures:
 if not c['name'].startswith('scaling_'):continue
 pts=c['points'];lo=[min(p[k] for p in pts) for k in (1,2,3)];hi=[max(p[k] for p in pts) for k in (1,2,3)]
 def key(p):
  xyz=[min(1023,int((p[k+1]-lo[k])/(hi[k]-lo[k])*1023)) if hi[k]>lo[k] else 0 for k in range(3)]
  return sum(((xyz[k]>>b)&1)<<(3*b+k) for b in range(10) for k in range(3))
 pts=sorted(pts,key=key);assert [oracle(pts,q) for q in c['queries']]==c['expected']
 for mode in ['correctness','depth']:
  p=out/('ordered_'+c['name']+'_'+mode+'.vi');driver(pts,c['queries'],p,'correctness' if mode=='correctness' else 'candidate')
  p.write_text(p.read_text().replace('tree::map(queries,fn* ((i,q)) {(i,neighbors::find(index,q))})','neighbors::find_batch(index,queries)'))
  r=run([sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib','sph='+str(out/'buckets/sph'),'--heap','2G']+(['--depth'] if mode=='depth' else [])+[str(p)],ROOT,p.with_suffix(''),180)
  value=Path(r['stdout']).read_text()
  if mode=='correctness':validate_rows(value,c['expected'])
  else:
   assert int(value)==sum(i+1 for row in c['expected'] for i in row)
   row=dict(case=c['name'],**parse_stats(Path(r['stderr']).read_text()));rows.append(row);print(row,flush=True)
write_json(out/'ordered.json',{'diagnostic_only':True,'excluded_cost':'host spatial-key calculation and sort','accepted':False,'correctness':True,'metrics':rows})
