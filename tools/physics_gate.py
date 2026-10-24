#!/usr/bin/env python3
"""Complete square-patch stage correctness. Performance/full-port acceptance is separate."""
import argparse,json,sys
from pathlib import Path
from evaluate import ROOT,run,compare,write_json,tree_hash,sha,parse_stats,add_resource_args,resources
from stage_reference import STAGES,verify_reference
from state_codec import decode_values,vine_state_dump
from neighbors_gate import validate_rows
from toolchain import verify
ref=ROOT/'reports/physics/first-stages/reference'
policy=json.loads((ROOT/'evaluations/sph-exa/physics-policy.json').read_text())
LIB=ROOT/'benchmarks/sph-exa/vine'

def source(side,updates):
 return 'use #sph::{evolution,physics,tree};use tree::Tree;\n'+vine_state_dump()+f'''pub fn main(&io:&IO){{
 let s=evolution::materialize(evolution::initialize(black_box({side})));snapshot("init",s,&io);
 for iteration in 0..black_box({updates}) {{
  let (prepared,rows)=evolution::prepare(s);s=prepared;
  snapshot("i{ '{iteration}' }-geometry",s,&io);
  dump_neighbors(rows,&io);let nn=evolution::neighbor_count(rows);io.println("COUNT {{nn}}");
  s=evolution::materialize(evolution::density(s,rows));snapshot("i{{iteration}}-density",s,&io);
  s=evolution::materialize(evolution::rest(s,iteration));snapshot("i{{iteration}}-rest",s,&io);
  s=evolution::materialize(evolution::eos(s));snapshot("i{{iteration}}-eos",s,&io);
  s=evolution::materialize(evolution::iad(s,rows));snapshot("i{{iteration}}-iad",s,&io);
  s=evolution::materialize(evolution::momentum(s,rows));snapshot("i{{iteration}}-momentum",s,&io);
  s=evolution::materialize(evolution::timestep(s));snapshot("i{{iteration}}-timestep",s,&io);
  s=evolution::materialize(evolution::positions(s));snapshot("i{{iteration}}-positions",s,&io);
  s=evolution::materialize(evolution::energy(s));snapshot("i{{iteration}}-energy",s,&io);
 }}
}}\n'''


def validate(path,side,updates,target):
 target.mkdir(exist_ok=True);expected_names=['init']+[f'i{i}-{s}' for i in range(updates) for s in STAGES]
 blocks={};block=None
 for line in Path(path).read_text().splitlines():
  words=line.split()
  if not words: raise ValueError('Empty output row')
  if words[0]=='STAGE':
   if len(words)!=2 or words[1] in blocks:raise ValueError('Duplicate/malformed stage')
   block={'fields':[],'neighbors':[],'meta':None,'count':None};blocks[words[1]]=block
  elif block is None: raise ValueError('Output before stage marker')
  elif words[0]=='P':
   if int(words[1])!=len(block['fields']):raise ValueError('Wrong particle identity')
   block['fields'].append(decode_values(words[2:],30))
  elif words[0]=='META':
   if block['meta'] is not None:raise ValueError('Duplicate metadata')
   block['meta']=decode_values(words[1:],10)
  elif words[0]=='N':block['neighbors'].append(' '.join(words[1:]))
  elif words[0]=='COUNT':
   if block['count'] is not None or len(words)!=2:raise ValueError('Duplicate/malformed count')
   block['count']=int(words[1])
  else:raise ValueError('Unknown output marker')
 if list(blocks)!=expected_names:raise ValueError('Missing/reordered stages')
 results=[]
 for name,b in blocks.items():
  if len(b['fields'])!=side**3 or b['meta'] is None:raise ValueError('Missing full state: '+name)
  fields=target/(name+'.tsv');fields.write_text(''.join(str(i)+' '+' '.join(format(x,'.17e') for x in row)+'\n' for i,row in enumerate(b['fields'])))
  meta=target/(name+'.meta');meta.write_text(' '.join(format(x,'.17e') for x in b['meta'])+'\n')
  c=compare(ref/f'side{side}'/(name+'.tsv'),fields,policy['atol'],policy['rtol'],side**3,31)
  m=compare(ref/f'side{side}'/(name+'.meta'),meta,policy['atol'],policy['rtol'],1,10)
  entry={'stage':name,'fields':c,'scalars':m}
  if name.endswith('-geometry'):
   neighbor_ref=ref/f'side{side}'/(name.replace('geometry','neighbors')+'.tsv')
   expected=[list(map(int,row.split()))[1:] for row in neighbor_ref.read_text().splitlines()]
   validate_rows('\n'.join(b['neighbors']),expected)
   actual=[list(map(int,row.split()))[1:] for row in b['neighbors']]
   if actual!=expected:raise ValueError('Neighbor order differs: '+name)
   if b['count']!=sum(map(len,expected)):raise ValueError('Wrong total neighbors')
   entry['membership_passed']=True
  elif b['neighbors'] or b['count'] is not None:raise ValueError('Unexpected neighbor output')
  results.append(entry)
  write_json(target/'progress.json',results)
  if not c['passed'] or not m['passed']:raise ValueError('Numerical failure: '+name)
 return results


def main():
 global ref, LIB
 ap=argparse.ArgumentParser()
 ap.add_argument('--output',required=True)
 ap.add_argument('--reference',required=True)
 ap.add_argument('--library',type=Path,default=LIB)
 add_resource_args(ap,600)
 args=ap.parse_args();LIB=args.library.resolve();out=Path(args.output).resolve();ref=Path(args.reference).resolve()
 out.mkdir(parents=True,exist_ok=True)
 report={'passed':False,'physics_accepted':False,'port_complete':False,
         'scope':'All fields/scalars and exact neighbor order after every stage, both full domains, three updates; no performance acceptance',
         'resources':resources(args),'policy':policy,'pin':verify(),'library':tree_hash(LIB),'evaluator_sha256':sha(Path(__file__)),'cases':[]}
 try:
  verify_reference(ref,policy)
  if tree_hash(ROOT/'upstream/sph-exa')!=json.loads((ROOT/'evaluations/upstream-files.json').read_text()):raise ValueError('Upstream changed')
  report['reference_report_sha256']=sha(ref/'result.json')
  for side in policy['sides']:
   target=out/f'side{side}';target.mkdir();src=target/'driver.vi';src.write_text(source(side,policy['updates']))
   r=run([sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib','sph='+str(LIB),'--heap',f'{args.heap_gib}G',str(src)],ROOT,target/'run',args.timeout)
   checks=validate(r['stdout'],side,policy['updates'],target/'decoded')
   stats=parse_stats(Path(r['stderr']).read_text(),require_depth=False)
   report['cases'].append({'side':side,'checks':checks,'stats_including_full_dump':stats,'process':r})
   write_json(out/'progress.json',report)
  if tree_hash(LIB)!=report['library']:raise ValueError('Library changed during validation')
  report['passed']=True
 except Exception as exc:report['error']=str(exc)
 write_json(out/'result.json',report)
 print(json.dumps({k:v for k,v in report.items() if k not in ('pin','library','cases')},indent=2))
 return 0 if report['passed'] else 1

if __name__=='__main__':sys.exit(main())
