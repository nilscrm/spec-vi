"""Bottom-up O(n) balanced construction; no spatial repartitioning.
Parent bounds depend only on child summaries. Shuffled leaves may produce broad
bounds and excessive query work; full runtime construction and routing are measured.
"""
from pathlib import Path
import shutil
out=Path('reports/neighbors/bottom-up-batch')
for variant in ['compact','bottom_up','buckets']:
 lib=out/variant/'sph';shutil.copytree('reports/neighbors/batch-routing/sph',lib,dirs_exist_ok=True)
 if variant=='compact':continue
 p=lib/'neighbors.vi';s=p.read_text().replace('pub fn build(points:', 'fn old_build(points:')
 if variant=='bottom_up':s+='''
pub fn build(points:Tree[Point])->Index {let (_,index)=bottom(points);index}
fn bottom(t:Tree[Point])->(Bounds,Index) {match t{
 Tree::Empty(){(bounds(Tree::Empty()),Index::Empty())}
 Tree::Leaf(p){(bounds(Tree::Leaf(p)),Index::Leaf(p))}
 Tree::Branch(l,r){let(a,l)=bottom(l);let(b,r)=bottom(r);let c=merge(a,b);(c,Index::Branch(c,l,r))}
}}
'''
 else:s+='''
pub fn build(points:Tree[Point])->Index {let (_,_,index)=bottom(points);index}
fn bottom(t:Tree[Point])->(Bounds,Tree[Point],Index) {match t{
 Tree::Empty(){(bounds(Tree::Empty()),Tree::Empty(),Index::Empty())}
 Tree::Leaf(p){(bounds(Tree::Leaf(p)),Tree::Leaf(p),Index::Leaf(p))}
 Tree::Branch(l,r){let(a,lp,l)=bottom(l);let(b,rp,r)=bottom(r);let c=merge(a,b);
 if c.n<=8 {let pts=Tree::Branch(lp,rp);(c,pts,Index::Bucket(pts))}
 else{(c,Tree::Empty(),Index::Branch(c,l,r))}}
}}
'''
 p.write_text(s)
s=Path('reports/neighbors/point-branches/full.py').read_text().replace("out=ROOT/'reports/neighbors/point-branches'","out=ROOT/'reports/neighbors/bottom-up-batch'").replace("['compact','preserve']","['compact','bottom_up','buckets']")
(out/'full.py').write_text(s)
