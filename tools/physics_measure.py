#!/usr/bin/env python3
"""Whole-update depth/timing diagnostics with all final fields and history forced.
Full stage correctness is separately established by evaluate.py, never this checksum.
"""
import argparse,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
from evaluate import run,write_json,tree_hash,sha,parse_stats,add_resource_args,resources,compare_baseline
from state_codec import decode_values
from stage_reference import load_fields,verify_reference
from toolchain import verify,identity
lib=ROOT/'benchmarks/sph-exa/vine';ref=ROOT/'reports/physics/first-stages/reference'
policy=json.loads((ROOT/'evaluations/sph-exa/physics-policy.json').read_text())

def source(side,updates):
 return f'''use #sph::{{evolution,physics,tree}};
 pub fn main(&io:&IO){{
 let s=evolution::materialize(evolution::initialize(black_box({side})));let history=0.0[F64];
 for iteration in 0..black_box({updates}){{
 let (prepared,rows)=evolution::prepare(s);s=prepared;let nn=evolution::neighbor_count(rows);
 s=evolution::materialize(evolution::density(s,rows));
 s=evolution::materialize(evolution::rest(s,iteration));
 s=evolution::materialize(evolution::eos(s));
 s=evolution::materialize(evolution::iad(s,rows));
 s=evolution::materialize(evolution::momentum(s,rows));
 s=evolution::materialize(evolution::timestep(s));
 s=evolution::materialize(evolution::positions(s));
 s=evolution::materialize(evolution::energy(s));
 history+=s.ttot+s.etot+s.ecin+s.eint+nn as F64;
 }}
 let total=tree::sum(tree::map(s.data,physics::particle_checksum));
 let scalar=s.ttot+s.etot+s.ecin+s.eint+s.bounds.xmin+s.bounds.xmax+s.bounds.ymin+s.bounds.ymax+s.bounds.zmin+s.bounds.zmax;
 let N64(lo,hi)=total.to_bits();io.println("{{lo}} {{hi}}");
 let N64(lo,hi)=scalar.to_bits();io.println("{{lo}} {{hi}}");
 let N64(lo,hi)=history.to_bits();io.println("{{lo}} {{hi}}");
 }}'''

def main():
 global lib,ref
 ap=argparse.ArgumentParser();ap.add_argument('--side',type=int,choices=policy['sides'],required=True);ap.add_argument('--updates',type=int,choices=[1,3],required=True);ap.add_argument('--mode',choices=['depth','workers2','normal'],required=True);ap.add_argument('--output',required=True);ap.add_argument('--library',type=Path,default=lib);ap.add_argument('--reference',type=Path,default=ref);ap.add_argument('--baseline',help='earlier physics_measure result.json to compare against');add_resource_args(ap,600);a=ap.parse_args();lib=a.library.resolve();ref=a.reference.resolve()
 target=Path(a.output).resolve();target.mkdir(parents=True);report={'passed':False,'physics_accepted':False,'port_complete':False,'side':a.side,'updates':a.updates,'mode':a.mode,'resources':resources(a),'policy':policy,'pin':verify(),'library':tree_hash(lib),'script_sha256':sha(Path(__file__))}
 try:
  report['toolchain']=identity(report['pin']);verify_reference(ref,policy)
  src=target/'driver.vi';src.write_text(source(a.side,a.updates));argv=[sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib','sph='+str(lib),'--heap',f'{a.heap_gib}G']
  argv+=['--depth'] if a.mode=='depth' else (['--workers','2'] if a.mode=='workers2' else [])
  r=run(argv+[str(src)],ROOT,target/'run',a.timeout);report['stats']=parse_stats(Path(r['stderr']).read_text(),require_depth=a.mode=='depth');report['process']=r
  got=decode_values(Path(r['stdout']).read_text().split(),3);case=ref/f'side{a.side}'
  fields=load_fields(case/f'i{a.updates-1}-energy.tsv',a.side**3);meta=list(map(float,(case/f'i{a.updates-1}-energy.meta').read_text().split()))
  hist=[]
  for i in range(a.updates):
   m=list(map(float,(case/f'i{i}-energy.meta').read_text().split()));nn=sum(len(l.split())-1 for l in (case/f'i{i}-neighbors.tsv').read_text().splitlines());hist+=m[:4]+[float(nn)]
  want=[math.fsum(v for row in fields for v in row),math.fsum(meta),math.fsum(hist)]
  counts=[a.side**3*30,10,a.updates*5];checks=[]
  for x,y,n in zip(got,want,counts):
   error=abs(x-y);limit=policy['atol']*n+policy['rtol']*abs(y);checks.append({'actual':x,'expected':y,'absolute_error':error,'accumulated_tolerance':limit,'passed':error<=limit})
  report['forcing_checks']=checks
  if not all(c['passed'] for c in checks):raise ValueError('Full state/history forcing mismatch')
  if a.baseline:report['comparison']=compare_baseline(report,a.baseline,['stats'])
  if tree_hash(lib)!=report['library']:raise ValueError('Library changed during measurement')
  report['passed']=True
 except Exception as exc:report['error']=str(exc)
 write_json(target/'result.json',report);print(json.dumps({k:v for k,v in report.items() if k not in ('pin','library')},indent=2));return 0 if report['passed'] else 1
if __name__=='__main__':sys.exit(main())
