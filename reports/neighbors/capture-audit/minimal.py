"""Minimal arithmetic capture-field versus local-copy control; no SPH kernel."""
import sys,struct,json
from pathlib import Path
sys.path.insert(0,'tools')
from evaluate import ROOT,run,parse_stats,write_json
from pilot_gate import balanced
out=ROOT/'reports/neighbors/capture-audit';lib=out/'local4/sph'
header='''use #sph::tree;use tree::Tree;
type Params={a:F64,b:F64};
fn sum(t:Tree[F64])->N32{match t{Tree::Empty(){0}Tree::Leaf(x){let N64(lo,hi)=x.to_bits();lo+hi}Tree::Branch(l,r){sum(l)+sum(r)}}}
fn dump(t:Tree[F64],&io:&IO){match t{Tree::Empty(){}Tree::Leaf(x){let N64(lo,hi)=x.to_bits();io.println("{lo} {hi}");}Tree::Branch(l,r){dump(l,&io);dump(r,&io);}}}
'''
rows=[]
for n in [1,16,64,256]:
 xs=list(range(n));expected=[struct.unpack('<II',struct.pack('<d',x*1.25-0.5)) for x in xs]
 for mode,expr in [('field','x*p.a+p.b'),('copy','let local=p;x*local.a+local.b')]:
  for measure in ['correctness','depth']:
   p=out/f'minimal_{n}_{mode}_{measure}.vi';p.write_text(header+'pub fn main(&io:&IO){let p:Params=black_box({a:1.25[F64],b:-0.5[F64]});let xs=black_box('+balanced(xs,lambda x:str(x)+'.0[F64]')+');let ys=tree::map(xs,fn*(x:F64)->F64 {'+expr+'});'+('dump(ys,&io);' if measure=='correctness' else 'io.println("{sum(ys)}");')+'}\n')
   r=run([sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib','sph='+str(lib)]+(['--depth'] if measure=='depth' else [])+[str(p)],ROOT,p.with_suffix(''),180)
   text=Path(r['stdout']).read_text()
   if measure=='correctness':assert [tuple(map(int,line.split())) for line in text.splitlines()]==expected
   else:
    assert int(text)==sum(sum(x) for x in expected)%2**32
    entry=dict(count=n,mode=mode,**parse_stats(Path(r['stderr']).read_text()));rows.append(entry);print(entry,flush=True)
write_json(out/'minimal.json',{'correctness':True,'metrics':rows})
