import sys
from pathlib import Path
sys.path.insert(0,'tools')
from neighbors_gate import synthetic,driver
from evaluate import ROOT,run,parse_stats,write_json
out=ROOT/'reports/neighbors/followup-1/ref-scan';lib=out/'sph';lib.mkdir(parents=True,exist_ok=True)
s=(out.parent/'scan-eager/sph/neighbors.vi').read_text()
s=s.replace('pub type Index = Tree[Point];','pub type Index = &Tree[Point];').replace('-> Index {p}','-> Index {&p}')
s=s.replace('match t { Tree::Empty()', 'match t { &Tree::Empty()').replace(' Tree::Leaf(p) {if inside(p,q)', ' &Tree::Leaf(p) {if inside(p,q)').replace(' Tree::Branch(l,r) {Tree::Branch', ' &Tree::Branch(l,r) {Tree::Branch')
s=s.replace('find(l,q),find(r,q)','find(&l,q),find(&r,q)')
(lib/'neighbors.vi').write_text(s);(lib/'sph.vi').write_text('pub mod neighbors;pub mod tree;\n');(lib/'tree.vi').write_text((ROOT/'benchmarks/sph-exa/vine/tree.vi').read_text())
results=[]
for name,pts,qs in synthetic():
 if not name.startswith('scaling_'):continue
 p=out/(name+'.vi');driver(pts,qs,p,'candidate')
 r=run([sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib','sph='+str(lib),'--depth',str(p)],ROOT,p.with_suffix(''),180)
 results.append(dict(case=name,**parse_stats(Path(r['stderr']).read_text())));print(results[-1],flush=True)
write_json(out/'result.json',results)
