"""Full compact/preserved point builder with unchanged compacted query routing."""
import sys,json
from pathlib import Path
sys.path.insert(0,'tools')
from evaluate import ROOT,run,parse_stats,write_json,tree_hash
from neighbors_gate import driver,validate_rows,oracle
from toolchain import verify
out=ROOT/'reports/neighbors/point-branches';pin=verify()
fixtures=json.loads((ROOT/'reports/neighbors/eager-cached-validation/fixtures.json').read_text())
report={'accepted_milestone':False,'correctness':[],'metrics':[],'pin':pin}
for variant in ['counted']:
 lib=out/variant/'sph'
 for case in fixtures:
  name=case['name'];pts=case['points'];qs=case['queries'];expected=case['expected']
  assert expected==[oracle(pts,q) for q in qs]
  if variant=='compact' and not name.startswith('scaling_'):continue
  for mode in ['correctness']+(['depth','workers2'] if name.startswith('scaling_') else []):
   p=out/variant/(name+'_'+mode+'.vi');driver(pts,qs,p,'correctness' if mode=='correctness' else 'candidate')
   s=p.read_text();old='tree::map(queries,fn* ((i,q)) {(i,neighbors::find(index,q))})';assert old in s;p.write_text(s.replace(old,'neighbors::find_batch(index,queries)'))
   argv=[sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib','sph='+str(lib),'--heap','2G']
   if mode=='depth':argv+=['--depth']
   if mode=='workers2':argv+=['--workers','2']
   r=run(argv+[str(p)],ROOT,p.with_suffix(''),180);value=Path(r['stdout']).read_text()
   if mode=='correctness':validate_rows(value,expected);report['correctness'].append(dict(variant=variant,case=name,passed=True))
   else:
    assert int(value)==sum(i+1 for row in expected for i in row)
    entry=dict(variant=variant,case=name,mode=mode,wall_seconds=r['wall_seconds'],peak_rss_bytes=r['peak_rss_bytes'])
    if mode=='depth':entry.update(parse_stats(Path(r['stderr']).read_text()))
    report['metrics'].append(entry)
   write_json(out/'counted.json',report);print(variant,name,mode,report['metrics'][-1:] if mode=='depth' else 'passed',flush=True)
report['libraries']={m:tree_hash(out/m/'sph') for m in ['counted']};write_json(out/'counted.json',report)
