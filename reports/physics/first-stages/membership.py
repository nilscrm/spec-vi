"""Full initial-domain membership from runtime Vine initialization and grid build."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from evaluate import run,write_json,tree_hash,sha
from neighbors_gate import validate_rows
from toolchain import verify
out=Path(__file__).resolve().parent/'membership-cached';out.mkdir(exist_ok=True)
report={'passed':False,'port_complete':False,'scope':'all initial particles; returned neighbor order remains different','pin':verify(),'library':tree_hash(ROOT/'benchmarks/sph-exa/vine'),'cases':[]}
header='''use #sph::{physics,tree};use tree::Tree;
fn ids(t:Tree[N32],&io:&IO){match t{Tree::Empty(){}Tree::Leaf(i){io.print(" {i}");}Tree::Branch(l,r){ids(l,&io);ids(r,&io);}}}
fn dump(t:Tree[(N32,Tree[N32])],&io:&IO){match t{Tree::Empty(){}Tree::Leaf((i,ns)){io.print("{i}");ids(ns,&io);io.println("");}Tree::Branch(l,r){dump(l,&io);dump(r,&io);}}}
'''
try:
 for side in [12,16]:
  n=side**3;src=out/f'side{side}.vi'
  src.write_text(header+f'pub fn main(&io:&IO){{let side=black_box({side});let data=physics::initialize(side,0,{n});let period=physics::initial_period(data,side);let rows=physics::neighbor_rows(data,{n},0,{n},period);dump(rows,&io);}}\n')
  r=run([sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib','sph='+str(ROOT/'benchmarks/sph-exa/vine'),'--heap','2G',str(src)],ROOT,out/f'side{side}',600)
  reference=out.parent/f'reference/side{side}/i0-neighbors.tsv'
  expected=[list(map(int,line.split()))[1:] for line in reference.read_text().splitlines()]
  assert len(expected)==n
  validate_rows(Path(r['stdout']).read_text(),expected)
  report['cases'].append({'side':side,'queries':n,'passed':True,'reference_sha256':sha(reference)})
  write_json(out/'progress.json',report)
 report['passed']=True
except Exception as exc:report['error']=str(exc)
write_json(out/'result.json',report)
print(json.dumps({k:v for k,v in report.items() if k not in ('pin','library')},indent=2))
sys.exit(0 if report['passed'] else 1)
