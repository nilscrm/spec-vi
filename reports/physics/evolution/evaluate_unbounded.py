"""Full runtime update candidate; independent original-oracle checks per stage."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
from evaluate import run,compare,write_json,tree_hash,sha
from stage_reference import STAGES,load_fields
from state_codec import decode_values,vine_state_dump
from neighbors_gate import validate_rows
from toolchain import verify
out=Path(__file__).resolve().parent
lib=out/'sph'
ref=ROOT/'reports/physics/first-stages/reference'
policy=json.loads((ROOT/'evaluations/sph-exa/physics-policy.json').read_text())


def source(side,updates):
 return 'use #sph::{evolution,physics,tree};use tree::Tree;\n'+vine_state_dump()+f'''pub fn main(&io:&IO){{
 let s=evolution::initialize(black_box({side}));snapshot("init",s,&io);
 for iteration in 0..black_box({updates}) {{
  let (prepared,rows)=evolution::prepare(s);s=prepared;
  snapshot("i{ '{iteration}' }-geometry",s,&io);
  dump_neighbors(rows,&io);let nn=evolution::neighbor_count(rows);io.println("COUNT {{nn}}");
  s=evolution::density(s,rows);snapshot("i{{iteration}}-density",s,&io);
  s=evolution::rest(s,iteration);snapshot("i{{iteration}}-rest",s,&io);
  s=evolution::eos(s);snapshot("i{{iteration}}-eos",s,&io);
  s=evolution::iad(s,rows);snapshot("i{{iteration}}-iad",s,&io);
  s=evolution::momentum(s,rows);snapshot("i{{iteration}}-momentum",s,&io);
  s=evolution::timestep(s);snapshot("i{{iteration}}-timestep",s,&io);
  s=evolution::positions(s);snapshot("i{{iteration}}-positions",s,&io);
  s=evolution::energy(s);snapshot("i{{iteration}}-energy",s,&io);
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
   if b['count']!=sum(map(len,expected)):raise ValueError('Wrong total neighbors')
   entry['membership_passed']=True
  elif b['neighbors'] or b['count'] is not None:raise ValueError('Unexpected neighbor output')
  results.append(entry)
  write_json(target/'progress.json',results)
  if not c['passed'] or not m['passed']:raise ValueError('Numerical failure: '+name)
 return results


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--side',type=int,required=True);ap.add_argument('--updates',type=int,required=True);ap.add_argument('--name',required=True);args=ap.parse_args()
 target=out/args.name;target.mkdir(exist_ok=True)
 report={'passed':False,'port_complete':False,'physics_accepted':False,'side':args.side,'updates':args.updates,'pin':verify(),'library':tree_hash(lib),'policy':policy}
 try:
  # These flags are diagnostics; acceptance still requires both fixed sides/all updates.
  if args.side not in policy['sides'] or args.updates<1 or args.updates>policy['updates']:raise ValueError('Unsupported diagnostic case')
  original=json.loads((ref/'result.json').read_text())
  if not original['reference_verified']:raise ValueError('Unverified oracle')
  for name,digest in original['snapshots'].items():
   if sha(ref/name)!=digest:raise ValueError('Oracle changed')
  src=target/'driver.vi';src.write_text(source(args.side,args.updates))
  r=run([sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib','sph='+str(lib),'--heap','2G',str(src)],ROOT,target/'run',policy['command_timeout_seconds'])
  report['checks']=validate(r['stdout'],args.side,args.updates,target/'decoded')
  report['passed']=True
 except Exception as exc:report['error']=str(exc)
 write_json(target/'result.json',report)
 print(json.dumps({k:v for k,v in report.items() if k not in ('pin','library','checks')},indent=2))
 return 0 if report['passed'] else 1

if __name__=='__main__':sys.exit(main())
