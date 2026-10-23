"""Controlled runtime xy-plane reuse; full input/output sizes unchanged."""
import json,sys,shutil,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from evaluate import run,compare,parse_stats,write_json,tree_hash
from initial_physics_gate import driver
from toolchain import verify
out=Path(__file__).resolve().parent/'cached-plane';out.mkdir(exist_ok=True)
lib=out/'sph'
shutil.copytree(ROOT/'benchmarks/sph-exa/vine',lib,dirs_exist_ok=True)
p=lib/'physics.vi';s=p.read_text()
a=s.index('pub fn initialize(');b=s.index('// Reference reads',a)
old=s[a:b].replace('initialize(', 'initialize_independent(').replace('pilot::initialize_independent(', 'pilot::initialize(')
new='''// The initial state is invariant across z except z and z_m1. All cached
// pressure values are computed in Vine with the original pilot reduction.
fn from_plane(&plane: &Tree[Particle], side:N32, start:N32, count:N32)->Tree[Particle] {
  if count==0 {Tree::Empty()} else {if count==1 {
    let p=at(&plane,side*side,start%(side*side));
    let size=side as F64;
    let z=(-0.5[F64]+1.0[F64]/(2.0[F64]*size)+(start/(side*side)) as F64*1.0[F64]/size)*100.0[F64];
    p.z=z;p.z_m1=z;
    Tree::Leaf(p)
  } else {
    let half=count/2;
    Tree::Branch(from_plane(&plane,side,start,half),from_plane(&plane,side,start+half,count-half))
  }}
}
pub fn initialize(side:N32,start:N32,count:N32)->Tree[Particle] {
  let plane=initialize_independent(side,0,side*side);
  from_plane(&plane,side,start,count)
}

'''
p.write_text(s[:a]+old+new+s[b:])
report={'passed':False,'pin':verify(),'library':tree_hash(lib),'cases':[]}
try:
 for side in [12,16]:
  src=out/f'init{side}.vi';driver(src,side,'init')
  r=run([sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib','sph='+str(lib),'--heap','2G',str(src)],ROOT,out/f'init{side}',600)
  check=compare(out.parent/f'reference/side{side}/init.tsv',r['stdout'],1e-9,5e-12,side**3,31)
  assert check['passed']
  report['cases'].append(dict(side=side,**check,interactions=int(re.search(r'Total\s+([\d_]+)',Path(r['stderr']).read_text())[1].replace('_','')),heap_bytes=int(re.search(r'Heap\s+([\d_]+)',Path(r['stderr']).read_text())[1].replace('_','')),peak_rss_bytes=r['peak_rss_bytes']))
  write_json(out/'progress.json',report)
 report['passed']=True
except Exception as exc:report['error']=str(exc)
write_json(out/'result.json',report);print(json.dumps({k:v for k,v in report.items() if k not in ('pin','library')},indent=2))
sys.exit(0 if report['passed'] else 1)
