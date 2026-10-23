"""Transpose direct-grid queries; one bucket per cell, balanced output zipper.
Include all runtime construction, query range preparation, copying and merging.
"""
from pathlib import Path
import shutil
out=Path('reports/neighbors/cell-major')
extra='''
type Prepared=(N32,Query,Ranges);
fn prepare(qs:Tree[(N32,Query)],b:Bounds)->Tree[Prepared]{#sph::tree::map(qs,fn*((i,q):(N32,Query))->Prepared {
 let r=(cell(q.x-q.radius,b.xmin,b.xmax),cell(q.x+q.radius,b.xmin,b.xmax),cell(q.y-q.radius,b.ymin,b.ymax),cell(q.y+q.radius,b.ymin,b.ymax),
 cell(q.z-q.radius,b.zmin,b.zmax),cell(q.z+q.radius,b.zmin,b.zmax),
 cell((q.z-q.period_z)-q.radius,b.zmin,b.zmax),cell((q.z-q.period_z)+q.radius,b.zmin,b.zmax),
 cell((q.z+q.period_z)-q.radius,b.zmin,b.zmax),cell((q.z+q.period_z)+q.radius,b.zmin,b.zmax));(i,q,r)
})}
fn in_cell(q:Query,r:Ranges,k:N32)->Bool {
 let x=k%SIDE;let y=(k/SIDE)%SIDE;let z=k/(SIDE*SIDE);let(x0,x1,y0,y1,z0,z1,a0,a1,b0,b1)=r;
 (x>=x0)&(x<=x1)&(y>=y0)&(y<=y1)&(((z>=z0)&(z<=z1))|((q.period_z>0.0[F64])&(((z>=a0)&(z<=a1))|((z>=b0)&(z<=b1)))))
}
fn query_cell(points:Tree[Point],qs:Tree[Prepared],k:N32)->Tree[(N32,Tree[N32])]{#sph::tree::map(qs,fn*((i,q,r)){
 (i,if in_cell(q,r,k) {scan(points,q)}else{Tree::Empty()})
})}
fn combine(a:Tree[(N32,Tree[N32])],b:Tree[(N32,Tree[N32])])->Tree[(N32,Tree[N32])]{match(a,b){
 (Tree::Empty(),Tree::Empty()){Tree::Empty()}
 (Tree::Leaf((i,a)),Tree::Leaf((_,b))){Tree::Leaf((i,Tree::Branch(a,b)))}
 (Tree::Branch(al,ar),Tree::Branch(bl,br)){Tree::Branch(combine(al,bl),combine(ar,br))}
 _{debug::error("query shape mismatch");Tree::Empty()}
}}
fn dispatch(t:Tree[Tree[Point]],qs:Tree[Prepared],first:N32,n:N32)->Tree[(N32,Tree[N32])]{match t{
 Tree::Empty(){#sph::tree::map(qs,fn*((i,_,_)){(i,Tree::Empty())})}
 Tree::Leaf(points){query_cell(points,qs,first)}
 Tree::Branch(l,r){let half=n/2;combine(dispatch(l,qs,first,half),dispatch(r,qs,first+half,n-half))}
}}
pub fn find_batch(Grid(b,t):Grid,qs:Tree[(N32,Query)])->Tree[(N32,Tree[N32])]{
 if b.n==0 {#sph::tree::map(qs,fn*((i,_)){(i,Tree::Empty())})}else{dispatch(t,prepare(qs,b),0,SIDE*SIDE*SIDE)}
}
'''
for variant in ['compact','grid2','grid4']:
 lib=out/variant/'sph'
 source=Path('reports/neighbors/batch-routing/sph') if variant=='compact' else Path('reports/neighbors/direct-grid')/variant/'sph'
 shutil.copytree(source,lib,dirs_exist_ok=True)
 if variant!='compact':
  p=lib/'neighbors.vi';s=p.read_text();s=s[:s.index('pub fn find_batch(')];p.write_text(s+extra.replace('SIDE',variant[-1]))
s=Path('reports/neighbors/direct-grid/full.py').read_text().replace("out=ROOT/'reports/neighbors/direct-grid'","out=ROOT/'reports/neighbors/cell-major'")
(out/'full.py').write_text(s)
