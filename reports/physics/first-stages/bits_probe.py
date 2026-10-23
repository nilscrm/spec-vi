"""Full side16 density, same computation, lossless bit transport consumer."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
from state_codec import vine_state_dump,decode_values
from evaluate import run,compare,write_json,tree_hash
from toolchain import verify
out=Path(__file__).resolve().parent/'bits-density';out.mkdir(exist_ok=True)
src=out/'driver.vi';src.write_text('use #sph::{physics,tree};use tree::Tree;\n'+vine_state_dump().split('fn snapshot')[0]+'''pub fn main(&io:&IO){let data=tree::map(physics::initial_stages(black_box(16),0,4096,1),fn*((_,p)){p});dump_particles(data,0,4096,&io);}\n''')
report={'passed':False,'pin':verify(),'library':tree_hash(ROOT/'benchmarks/sph-exa/vine')}
try:
 r=run([sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib','sph='+str(ROOT/'benchmarks/sph-exa/vine'),'--heap','2G',str(src)],ROOT,out/'run',600)
 rows=[]
 for i,line in enumerate(Path(r['stdout']).read_text().splitlines()):
  v=line.split();assert v[0]=='P' and int(v[1])==i
  rows.append(decode_values(v[2:],30))
 decoded=out/'decoded.tsv';decoded.write_text(''.join(str(i)+' '+' '.join(format(x,'.17e') for x in p)+'\n' for i,p in enumerate(rows)))
 check=compare(out.parent/'reference/side16/i0-density.tsv',decoded,1e-9,5e-12,4096,31)
 report['check']=check;report['passed']=check['passed']
except Exception as exc:report['error']=str(exc)
write_json(out/'result.json',report);print(json.dumps({k:v for k,v in report.items() if k not in ('pin','library')},indent=2))
sys.exit(0 if report['passed'] else 1)
