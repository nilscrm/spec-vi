import sys
from pathlib import Path
sys.path.insert(0,'tools')
from neighbors_gate import synthetic,driver,point
from pilot_gate import balanced,lit
from evaluate import ROOT,run,parse_stats,write_json
out=ROOT/'reports/neighbors/followup-1'
consume='''fn consume(i: neighbors::Index) -> N32 { match i { neighbors::Index::Empty() {0} neighbors::Index::Leaf(p) {p.id+1} neighbors::Index::Branch(_,l,r) {consume(l)+consume(r)} } }\n'''
for name,pts,qs in synthetic():
 if not name.startswith('scaling_'):continue
 p=out/(name+'_build.vi');p.write_text('use #sph::{neighbors,tree};use tree::Tree;\n'+consume+'pub fn main(&io:&IO) {let t=black_box('+balanced(pts,point)+');io.println("{consume(neighbors::build(t))}");}\n')
 r=run([sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib','sph='+str(ROOT/'benchmarks/sph-exa/vine'),'--depth',str(p)],ROOT,p.with_suffix(''),180)
 print(name,'build',parse_stats(Path(r['stderr']).read_text()),flush=True)
