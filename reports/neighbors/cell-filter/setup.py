from pathlib import Path
import shutil
out=Path('reports/neighbors/cell-filter')
extra='''
fn join_requests(a:Tree[Request],b:Tree[Request])->Tree[Request]{match(a,b){
 (Tree::Empty(),b){b}(a,Tree::Empty()){a}(a,b){Tree::Branch(a,b)}
}}
fn filter(qs:Tree[Request],k:N32)->Tree[Request]{match qs{
 Tree::Empty(){Tree::Empty()}
 Tree::Leaf((q,r,o)){if in_cell(q,r,k){Tree::Leaf((q,r,o))}else{~o=Tree::Empty();Tree::Empty()}}
 Tree::Branch(l,r){join_requests(filter(l,k),filter(r,k))}
}}
fn scan_requests(points:Tree[Point],qs:Tree[Request]){match qs{
 Tree::Empty(){}Tree::Leaf((q,_,o)){~o=scan(points,q);}
 Tree::Branch(l,r){scan_requests(points,l);scan_requests(points,r);}
}}
'''
for variant in ['control','filtered']:
 lib=out/variant/'sph';shutil.copytree('reports/neighbors/capture-audit/local4/sph',lib,dirs_exist_ok=True)
 if variant=='filtered':
  p=lib/'neighbors.vi';s=p.read_text().replace('Tree::Leaf(points){finish(points,qs,first);}','Tree::Leaf(points){scan_requests(points,filter(qs,first));}')
  p.write_text(s+extra)
s=Path('reports/neighbors/point-branches/full.py').read_text().replace("out=ROOT/'reports/neighbors/point-branches'","out=ROOT/'reports/neighbors/cell-filter'").replace("['compact','preserve']","['control','filtered']").replace("variant=='compact'","variant=='control'")
(out/'full.py').write_text(s)
