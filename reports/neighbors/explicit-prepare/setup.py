from pathlib import Path
import shutil
out=Path('reports/neighbors/explicit-prepare')
for variant in ['compact','wires2','wires4']:
 source=Path('reports/neighbors/batch-routing/sph') if variant=='compact' else Path('reports/neighbors/cell-major')/variant/'sph'
 lib=out/variant/'sph';shutil.copytree(source,lib,dirs_exist_ok=True)
 if variant=='compact':continue
 p=lib/'neighbors.vi';s=p.read_text();a=s.index('fn prepare(');b=s.index('\nfn in_cell',a);old=s[a:b]
 body=old[old.index(' let r='):old.index('\n})}')].replace(';(i,q,r)',';Tree::Leaf((i,q,r))')
 s=s[:a]+'''fn prepare(qs:Tree[(N32,Query)],b:Bounds)->Tree[Prepared]{match qs {
 Tree::Empty(){Tree::Empty()}
 Tree::Leaf((i,q)){'''+body+'''}
 Tree::Branch(l,r){Tree::Branch(prepare(l,b),prepare(r,b))}
}}
'''+s[b:];p.write_text(s)
s=Path('reports/neighbors/cell-major/full.py').read_text().replace("out=ROOT/'reports/neighbors/cell-major'","out=ROOT/'reports/neighbors/explicit-prepare'").replace("['compact','grid2','grid4']","['compact','wires2','wires4']")
(out/'full.py').write_text(s)
