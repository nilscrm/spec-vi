"""Preserve point branches: remove join dependency, retain empty-branch costs.
Input routing and summary merges remain balanced. Full build may repeat traversal
of holes: measure full workload before accepting any component-depth benefit.
"""
import sys,json,shutil
from pathlib import Path
sys.path.insert(0,'tools')
from evaluate import ROOT,run,parse_stats,write_json,tree_hash
from toolchain import verify
out=ROOT/'reports/neighbors/point-branches';verify();results=[]
for mode in ['compact','preserve']:
 lib=out/mode/'sph';lib.mkdir(parents=True,exist_ok=True)
 for name in ['tree.vi','sph.vi','neighbors.vi']:shutil.copy2(ROOT/'reports/neighbors/batch-routing/sph'/name,lib/name)
 s=(lib/'neighbors.vi').read_text().replace('fn partition(', 'pub fn partition(')
 if mode=='preserve':
  assert s.count('join(ll, rl)')==1 and s.count('join(lr, rr)')==1
  s=s.replace('join(ll, rl)','Tree::Branch(ll, rl)').replace('join(lr, rr)','Tree::Branch(lr, rr)')
 (lib/'neighbors.vi').write_text(s)
 for count in [64,256]:
  for measure in ['correctness','depth']:
   source=ROOT/f'reports/neighbors/bounds-layout/scaling_{count}_routing_cached_{measure}.vi'
   p=out/mode/source.name;shutil.copy2(source,p)
   r=run([sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib','sph='+str(lib)]+(['--depth'] if measure=='depth' else [])+[str(p)],ROOT,p.with_suffix(''),180)
   assert Path(r['stdout']).read_text()==source.with_suffix('.stdout').read_text()
   if measure=='depth':
    entry=dict(count=count,mode=mode,**parse_stats(Path(r['stderr']).read_text()));results.append(entry);print(entry,flush=True)
write_json(out/'diagnostic.json',{'measurements':results,'exact_bounds_and_ids':True,'libraries':{m:tree_hash(out/m/'sph') for m in ['compact','preserve']}})
