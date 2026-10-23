"""Bounded ownership comparison on actual density payloads, not a tuning sweep."""
import json,sys,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
from evaluate import run,compare,parse_stats,write_json,tree_hash
from initial_physics_gate import driver,check_checksum
from stage_reference import load_fields
from toolchain import verify
out=Path(__file__).resolve().parent/'copy-gather';out.mkdir(exist_ok=True)
lib=out/'sph';shutil.copytree(ROOT/'benchmarks/sph-exa/vine',lib,dirs_exist_ok=True)
p=lib/'physics.vi';s=p.read_text();a=s.index('fn point_at(');b=s.index('pub fn eos(',a)
body=s[a:b].replace('&t: &Tree','t: Tree').replace('&points: &Tree','points: Tree').replace('match &t','match t').replace('&Tree::','Tree::').replace('point_at(&l,','point_at(l,').replace('point_at(&r,','point_at(r,').replace('point_at(&points,','point_at(points,').replace('gather(&points,','gather(points,')
s=s[:a]+body+s[b:];s=s.replace('gather(&points,n,ids)','gather(points,n,ids)');p.write_text(s)
policy=json.loads((ROOT/'evaluations/sph-exa/physics-policy.json').read_text())
reference=out.parent/'reference/side12/i0-eos.tsv';rows=load_fields(reference,1728)
report={'passed':False,'diagnostic_only':True,'pin':verify(),'library':tree_hash(lib),'cases':[]}
try:
 for count in [1,8]:
  expected=out/f'expected{count}.tsv';expected.write_text('\n'.join(reference.read_text().splitlines()[:count])+'\n')
  for depth in [False,True]:
   name=f'q{count}_'+('depth' if depth else 'correctness');src=out/(name+'.vi');driver(src,12,'eos',count,depth)
   r=run([sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib','sph='+str(lib),'--heap','2G']+(['--depth'] if depth else [])+[str(src)],ROOT,out/name,600)
   if depth:
    check_checksum(r['stdout'],rows[:count],policy)
    report['cases'].append(dict(queries=count,**parse_stats(Path(r['stderr']).read_text()),peak_rss_bytes=r['peak_rss_bytes']))
   else:
    assert compare(expected,r['stdout'],policy['atol'],policy['rtol'],count,31)['passed']
  write_json(out/'progress.json',report)
 report['passed']=True
except Exception as exc:report['error']=str(exc)
write_json(out/'result.json',report);print(json.dumps({k:v for k,v in report.items() if k not in ('pin','library')},indent=2))
sys.exit(0 if report['passed'] else 1)
