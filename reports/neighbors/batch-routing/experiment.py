"""Batch API experiment: unchanged fixtures, arithmetic, forcing, and budgets.
Run from the project root with python3 reports/neighbors/batch-routing/experiment.py.
This does not register or replace an acceptance gate.
"""
import sys,json
from pathlib import Path
sys.path.insert(0,'tools')
from evaluate import ROOT,run,parse_stats,write_json,tree_hash,sha
from neighbors_gate import driver,validate_rows,oracle
from toolchain import verify
out=ROOT/'reports/neighbors/batch-routing'
verify()
fixtures=json.loads((ROOT/'reports/neighbors/eager-cached-validation/fixtures.json').read_text())
write_json(out/'provenance.json',{'library':tree_hash(out/'sph'),'original':sha(out/'before.vi'),'fixtures':sha(ROOT/'reports/neighbors/eager-cached-validation/fixtures.json'),'policy':sha(ROOT/'evaluations/sph-exa/neighbors-policy.json')})
report={'experiment':'batched query routing','accepted_milestone':False,'correctness':[],'metrics':[]}
for case in fixtures:
 name=case['name'];pts=case['points'];qs=case['queries'];expected=case['expected']
 assert expected==[oracle(pts,q) for q in qs]
 modes=['correctness']+(['depth','workers2'] if name.startswith('scaling_') else [])
 for mode in modes:
  path=out/(name+'_'+mode+'.vi');driver(pts,qs,path,'correctness' if mode=='correctness' else 'candidate')
  s=path.read_text();old='tree::map(queries,fn* ((i,q)) {(i,neighbors::find(index,q))})'
  assert old in s;s=s.replace(old,'neighbors::find_batch(index,queries)');path.write_text(s)
  argv=[sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib','sph='+str(out/'sph'),'--heap','2G']
  if mode=='depth':argv+=['--depth']
  if mode=='workers2':argv+=['--workers','2']
  result=run(argv+[str(path)],ROOT,path.with_suffix(''),180)
  value=Path(result['stdout']).read_text()
  if mode=='correctness':
   validate_rows(value,expected);report['correctness'].append({'case':name,'passed':True})
  else:
   assert int(value)==sum(i+1 for row in expected for i in row)
   metric={'case':name,'mode':mode,'peak_rss_bytes':result['peak_rss_bytes'],'process_wall_seconds':result['wall_seconds']}
   if mode=='depth':metric.update(parse_stats(Path(result['stderr']).read_text()))
   report['metrics'].append(metric)
  write_json(out/'result.json',report);print(name,mode,'passed',report['metrics'][-1:] if mode!='correctness' else '',flush=True)
