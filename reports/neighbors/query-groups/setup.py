"""Annotate query subtree sizes once; dispatch independent bounded groups.
Counts depend on balanced child reductions. Each group duplicates the constructed
index; outputs keep original tree order. Include annotation/copy/cleanup costs.
"""
from pathlib import Path
import shutil
out=Path('reports/neighbors/query-groups')
extra='''
enum* SizedQueries {Empty(),Leaf((N32,Query)),Branch(N32,SizedQueries,SizedQueries)}
fn sized(t:Tree[(N32,Query)])->(N32,SizedQueries){match t{
 Tree::Empty(){(0,SizedQueries::Empty())}
 Tree::Leaf(q){(1,SizedQueries::Leaf(q))}
 Tree::Branch(l,r){let(a,l)=sized(l);let(b,r)=sized(r);(a+b,SizedQueries::Branch(a+b,l,r))}
}}
fn plain(t:SizedQueries)->Tree[(N32,Query)]{match t{
 SizedQueries::Empty(){Tree::Empty()}SizedQueries::Leaf(q){Tree::Leaf(q)}
 SizedQueries::Branch(_,l,r){Tree::Branch(plain(l),plain(r))}
}}
fn groups(index:Index,t:SizedQueries)->Tree[(N32,Tree[N32])]{match t{
 SizedQueries::Empty(){Tree::Empty()}
 SizedQueries::Leaf(q){find_batch(index,Tree::Leaf(q))}
 SizedQueries::Branch(n,l,r){if n<=LIMIT {find_batch(index,plain(SizedQueries::Branch(n,l,r)))}
 else{Tree::Branch(groups(index,l),groups(index,r))}}
}}
pub fn grouped(index:Index,t:Tree[(N32,Query)])->Tree[(N32,Tree[N32])]{let(_,t)=sized(t);groups(index,t)}
'''
for variant in ['compact','single','group8','group32']:
 lib=out/variant/'sph';shutil.copytree('reports/neighbors/batch-routing/sph',lib,dirs_exist_ok=True)
 if variant.startswith('group'):
  p=lib/'neighbors.vi';p.write_text(p.read_text()+extra.replace('LIMIT',variant[5:]))
s=Path('reports/neighbors/point-branches/full.py').read_text().replace("out=ROOT/'reports/neighbors/point-branches'","out=ROOT/'reports/neighbors/query-groups'").replace("['compact','preserve']","['compact','single','group8','group32']").replace("if variant=='compact' and", "if variant in ['compact','single'] and")
s=s.replace("s.replace(old,'neighbors::find_batch(index,queries)')","s.replace(old,old if variant=='single' else 'neighbors::grouped(index,queries)' if variant.startswith('group') else 'neighbors::find_batch(index,queries)')")
(out/'full.py').write_text(s)
