"""Runtime fixed-grid buckets and direct value-tree selection.
O(B*N) population is deliberately included; independent queries enumerate selected
cells once, including the union of periodic z ranges, and use the exact scan.
"""
from pathlib import Path
import shutil
out=Path('reports/neighbors/direct-grid')
extra='''
pub struct* Grid(Bounds,Tree[Tree[Point]]);
fn cell(x:F64,lo:F64,hi:F64)->N32 {
 if hi<=lo {0}else{let d=hi-lo;CELL}
}
fn labels(t:Tree[Point],b:Bounds)->Tree[(N32,Point)] {match t{
 Tree::Empty(){Tree::Empty()}Tree::Leaf(p){Tree::Leaf((cell(p.x,b.xmin,b.xmax)+SIDE*cell(p.y,b.ymin,b.ymax)+SIDE*SIDE*cell(p.z,b.zmin,b.zmax),p))}
 Tree::Branch(l,r){Tree::Branch(labels(l,b),labels(r,b))}
}}
fn select(t:Tree[(N32,Point)],k:N32)->Tree[Point]{match t{
 Tree::Empty(){Tree::Empty()}Tree::Leaf((i,p)){if i==k {Tree::Leaf(p)}else{Tree::Empty()}}
 Tree::Branch(l,r){join(select(l,k),select(r,k))}
}}
fn buckets(t:Tree[(N32,Point)],first:N32,n:N32)->Tree[Tree[Point]] {
 if n==1 {Tree::Leaf(select(t,first))}else{let half=n/2;Tree::Branch(buckets(t,first,half),buckets(t,first+half,half))}
}
pub fn build(t:Tree[Point])->Grid {let b=bounds(t);Grid(b,buckets(labels(t,b),0,SIDE*SIDE*SIDE))}
fn pick(t:Tree[Tree[Point]],k:N32,n:N32)->Tree[Point]{match t{
 Tree::Empty(){Tree::Empty()}Tree::Leaf(p){p}Tree::Branch(l,r){let half=n/2;if k<half {pick(l,k,half)}else{pick(r,k-half,half)}}
}}
type Ranges=(N32,N32,N32,N32,N32,N32,N32,N32,N32,N32);
fn xs(t:Tree[Tree[Point]],q:Query,z:N32,y:N32,x:N32,n:N32)->Tree[N32]{
 if n==1 {scan(pick(t,x+SIDE*y+SIDE*SIDE*z,SIDE*SIDE*SIDE),q)}else{let half=n/2;Tree::Branch(xs(t,q,z,y,x,half),xs(t,q,z,y,x+half,n-half))}
}
fn ys(t:Tree[Tree[Point]],q:Query,z:N32,y:N32,n:N32,x:N32,nx:N32)->Tree[N32]{
 if n==1 {xs(t,q,z,y,x,nx)}else{let half=n/2;Tree::Branch(ys(t,q,z,y,half,x,nx),ys(t,q,z,y+half,n-half,x,nx))}
}
fn zs(t:Tree[Tree[Point]],q:Query,r:Ranges,z:N32,n:N32)->Tree[N32]{
 if n==1 {let(x0,x1,y0,y1,z0,z1,a0,a1,b0,b1)=r;
 if ((z>=z0)&(z<=z1)) | ((q.period_z>0.0[F64]) & (((z>=a0)&(z<=a1)) | ((z>=b0)&(z<=b1)))) {ys(t,q,z,y0,y1-y0+1,x0,x1-x0+1)}else{Tree::Empty()}
 }else{let half=n/2;Tree::Branch(zs(t,q,r,z,half),zs(t,q,r,z+half,n-half))}
}
pub fn find(Grid(b,t):Grid,q:Query)->Tree[N32]{
 if b.n==0 {Tree::Empty()}else{
 let r=(cell(q.x-q.radius,b.xmin,b.xmax),cell(q.x+q.radius,b.xmin,b.xmax),cell(q.y-q.radius,b.ymin,b.ymax),cell(q.y+q.radius,b.ymin,b.ymax),
 cell(q.z-q.radius,b.zmin,b.zmax),cell(q.z+q.radius,b.zmin,b.zmax),
 cell((q.z-q.period_z)-q.radius,b.zmin,b.zmax),cell((q.z-q.period_z)+q.radius,b.zmin,b.zmax),
 cell((q.z+q.period_z)-q.radius,b.zmin,b.zmax),cell((q.z+q.period_z)+q.radius,b.zmin,b.zmax));zs(t,q,r,0,SIDE)
 }
}
pub fn find_batch(g:Grid,qs:Tree[(N32,Query)])->Tree[(N32,Tree[N32])]{#sph::tree::map(qs,fn*((i,q)){(i,find(g,q))})}
'''
for variant in ['compact','grid2','grid4']:
 lib=out/variant/'sph';shutil.copytree('reports/neighbors/batch-routing/sph',lib,dirs_exist_ok=True)
 if variant=='compact':continue
 p=lib/'neighbors.vi';s=p.read_text();s=s[:s.index('// Return bounds together')]+s[s.index('fn scan('):s.index('fn overlap_z(')]
 side=int(variant[-1]);c='if x<lo+d*0.5[F64] {0}else{1}' if side==2 else 'if x<lo+d*0.5[F64] {if x<lo+d*0.25[F64] {0}else{1}}else{if x<lo+d*0.75[F64] {2}else{3}}'
 p.write_text(s+extra.replace('CELL',c).replace('SIDE',str(side)))
s=Path('reports/neighbors/point-branches/full.py').read_text().replace("out=ROOT/'reports/neighbors/point-branches'","out=ROOT/'reports/neighbors/direct-grid'").replace("['compact','preserve']","['compact','grid2','grid4']")
(out/'full.py').write_text(s)
