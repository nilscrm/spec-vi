"""Controlled request-compaction experiment; does not modify registered gates.
Carry a parallel occupancy reduction and compact at selected tree levels.
Retaining holes between levels trades traversal work for fewer structural dependencies.
Construction, query identities, geometry and output forcing are unchanged.
"""
import sys,json,shutil
from pathlib import Path
sys.path.insert(0,'tools')
from evaluate import ROOT,run,write_json,parse_stats,tree_hash,sha
from neighbors_gate import synthetic,driver,oracle,validate_rows
from toolchain import verify
verify()
base=ROOT/'reports/neighbors/batch-routing';out=ROOT/'reports/neighbors/tiled-routing'
original=(base/'sph/neighbors.vi').read_text()
shutil.copy2(base/'sph/neighbors.vi',out/'before.vi')
replacement='''fn split_requests(requests: Tree[Request],b: Bounds) -> (Tree[Request],Tree[Request]) {
 let (_,l,r)=split_level(requests,b,0);(l,r)
}
fn split_level(requests: Tree[Request],b: Bounds,level: N32) -> (Bool,Tree[Request],Tree[Request]) {
 match requests {
  Tree::Empty() {(false,Tree::Empty(),Tree::Empty())}
  Tree::Leaf((q,output)) {
   if overlaps(b,q) {
    let l;let r;let next=(true,Tree::Leaf((q,~l)),Tree::Leaf((q,~r)));
    ~output=Tree::Branch(l,r);next
   } else {~output=Tree::Empty();(false,Tree::Empty(),Tree::Empty())}
  }
  Tree::Branch(l,r) {
   let (a,ll,lr)=split_level(l,b,level+1);let (c,rl,rr)=split_level(r,b,level+1);
   let any=a | c;
   if level % STRIDE == 0 {
    if any {(any,Tree::Branch(ll,rl),Tree::Branch(lr,rr))}
    else {finish(ll,Tree::Empty());finish(lr,Tree::Empty());finish(rl,Tree::Empty());finish(rr,Tree::Empty());(any,Tree::Empty(),Tree::Empty())}
   } else {(any,Tree::Branch(ll,rl),Tree::Branch(lr,rr))}
  }
 }
}
'''
results=[]
for stride in (1,2,3,4):
 target=out/f'stride{stride}';lib=target/'sph';lib.mkdir(parents=True,exist_ok=True)
 a=original.index('fn split_requests(');b=original.index('fn finish(',a)
 (lib/'neighbors.vi').write_text(original[:a]+replacement.replace('STRIDE',str(stride))+original[b:])
 for name in ['sph.vi','tree.vi']:shutil.copy2(base/'sph'/name,lib/name)
 write_json(target/'source.json',tree_hash(lib))
 for name,pts,qs in synthetic():
  if not name.startswith('scaling_'):continue
  expected=[oracle(pts,q) for q in qs]
  for mode in ['correctness','depth']:
   path=target/(name+'_'+mode+'.vi');driver(pts,qs,path,'correctness' if mode=='correctness' else 'candidate')
   path.write_text(path.read_text().replace('tree::map(queries,fn* ((i,q)) {(i,neighbors::find(index,q))})','neighbors::find_batch(index,queries)'))
   argv=[sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib','sph='+str(lib),'--heap','2G']
   if mode=='depth':argv+=['--depth']
   result=run(argv+[str(path)],ROOT,path.with_suffix(''),180)
   text=Path(result['stdout']).read_text()
   if mode=='correctness':validate_rows(text,expected)
   else:
    assert int(text)==sum(i+1 for row in expected for i in row)
    entry=dict(stride=stride,case=name,**parse_stats(Path(result['stderr']).read_text()))
    results.append(entry);print(entry,flush=True)
    write_json(out/'results.json',results)
