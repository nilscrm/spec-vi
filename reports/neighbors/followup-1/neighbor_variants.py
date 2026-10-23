import sys,re,shutil
from pathlib import Path
sys.path.insert(0,'tools')
from neighbors_gate import synthetic,driver
from evaluate import ROOT,run,parse_stats,write_json
out=ROOT/'reports/neighbors/followup-1'
original=(out/'original.vi').read_text()
inside='''fn inside(p: Point,q: Query) -> Bool {
 let dx=q.x-p.x;let dy=q.y-p.y;let dz=q.z-p.z;
 let dxy=dx*dx+dy*dy;let r2=q.radius*q.radius;
 let local=(dxy+dz*dz < r2);
 let a=q.z-q.period_z-p.z;let b=q.z+q.period_z-p.z;
 (p.id != q.id) & (local | ((q.period_z > 0.0[F64]) & ((dxy+a*a < r2) | (dxy+b*b < r2))))
}
'''
simple='''use #sph::tree::Tree;
pub type Point = {id:N32,x:F64,y:F64,z:F64};
pub type Query = {id:N32,x:F64,y:F64,z:F64,radius:F64,period_z:F64};
pub type Index = Tree[Point];
pub fn build(p: Tree[Point]) -> Index {p}
pub fn find(t: Index,q: Query) -> Tree[N32] {
 match t { Tree::Empty() {Tree::Empty()} Tree::Leaf(p) {if inside(p,q) {Tree::Leaf(p.id)} else {Tree::Empty()}} Tree::Branch(l,r) {Tree::Branch(find(l,q),find(r,q))} }
}
'''+inside
# Unpartitioned tree with bounding boxes computed once bottom-up.
onepass=original[:original.index('fn min')]+original[original.index('fn min'):original.index('fn join')]+'''
fn construct(t: Tree[Point]) -> (Bounds,Index) {
 match t {
  Tree::Empty() { (bounds(Tree::Empty()),Index::Empty()) }
  Tree::Leaf(p) { (bounds(Tree::Leaf(p)),Index::Leaf(p)) }
  Tree::Branch(l,r) {let (a,l)=construct(l);let (b,r)=construct(r);let box=merge(a,b);(box,Index::Branch(box,l,r))}
 }
}
pub fn build(t: Tree[Point]) -> Index {construct(t).1}
'''+inside+original[original.index('fn overlap_z'):]
variants={'scan-eager':simple,'unpartitioned':onepass}
results=[]
for name,src in variants.items():
 lib=out/name/'sph';lib.mkdir(parents=True,exist_ok=True)
 (lib/'sph.vi').write_text('pub mod neighbors;pub mod tree;\n')
 (lib/'tree.vi').write_text((ROOT/'benchmarks/sph-exa/vine/tree.vi').read_text());(lib/'neighbors.vi').write_text(src)
 for case,pts,qs in synthetic():
  if not case.startswith('scaling_'):continue
  path=lib.parent/(case+'.vi');driver(pts,qs,path,'candidate')
  r=run([sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib','sph='+str(lib),'--depth',str(path)],ROOT,path.with_suffix(''),180)
  stats=parse_stats(Path(r['stderr']).read_text());results.append(dict(variant=name,case=case,**stats));print(results[-1],flush=True)
write_json(out/'variants.json',results)
