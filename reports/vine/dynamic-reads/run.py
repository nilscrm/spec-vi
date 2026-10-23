"""Runtime-built indexed-read diagnostics, all ownership and cleanup included.
Copied trees select one path but erase the remainder. Array reference readers
thread exclusive references through balanced query recursion. Neither mode omits
construction. No static Lookup or fixture-specific native implementation.
"""
import sys,json,random,shutil
from pathlib import Path
sys.path.insert(0,'tools')
from evaluate import ROOT,run,parse_stats,write_json,tree_hash
from pilot_gate import balanced
from toolchain import verify
out=ROOT/'reports/vine/dynamic-reads';pin=verify();lib=out/'sph';lib.mkdir(exist_ok=True)
shutil.copy2(ROOT/'benchmarks/sph-exa/vine/tree.vi',lib/'tree.vi');(lib/'sph.vi').write_text('pub mod tree;\n')
header='''use #sph::tree;use tree::Tree;use #root::data::Array;
fn value(x:N32)->N32 {(x*1664525)+1013904223}
fn pick(t:Tree[N32],n:N32,i:N32)->N32 {match t {Tree::Empty(){0}Tree::Leaf(x){x}Tree::Branch(l,r){let mid=n/2;if i<mid {pick(l,mid,i)}else{pick(r,n-mid,i-mid)}}}}
fn tree_reads(t:Tree[N32],n:N32,qs:Tree[N32])->Tree[N32]{match qs{
 Tree::Empty(){Tree::Empty()}Tree::Leaf(i){Tree::Leaf(pick(t,n,i))}Tree::Branch(l,r){Tree::Branch(tree_reads(t,n,l),tree_reads(t,n,r))}
}}
fn array_copy(a:Array[N32],qs:Tree[N32])->Tree[N32]{match qs{
 Tree::Empty(){Tree::Empty()}Tree::Leaf(i){Tree::Leaf(a.get(i).assume())}Tree::Branch(l,r){Tree::Branch(array_copy(a,l),array_copy(a,r))}
}}
fn array_ref(&a:&Array[N32],qs:Tree[N32])->Tree[N32]{match qs{
 Tree::Empty(){Tree::Empty()}Tree::Leaf(i){Tree::Leaf(a.get(i).assume())}Tree::Branch(l,r){Tree::Branch(array_ref(&a,l),array_ref(&a,r))}
}}
fn sum(t:Tree[N32])->N32{match t{Tree::Empty(){0}Tree::Leaf(x){x}Tree::Branch(l,r){sum(l)+sum(r)}}}
fn dump(t:Tree[N32],&io:&IO){match t{Tree::Empty(){}Tree::Leaf(x){io.println("{x}");}Tree::Branch(l,r){dump(l,&io);dump(r,&io);}}}
'''
report={'pin':pin,'diagnostic_only':True,'cases':[],'measurements':[]}
for n in [64,256]:
 for count in [1,8,64,256]:
  for pattern in (['mixed','repeat'] if count==256 else ['mixed']):
   rng=random.Random(934+n+count);qs=[rng.randrange(n) for _ in range(count)] if pattern=='mixed' else [n//3]*count
   expected=[(q*1664525+1013904223)%2**32 for q in qs]
   for mode in ['tree_copy','array_copy','array_ref']:
    for measure in ['correctness','depth']:
     inputs='let raw=black_box('+balanced(list(range(n)),str)+');let data=tree::map(raw,fn*(x:N32)->N32 {value(x)});' if mode=='tree_copy' else 'let raw=black_box(['+','.join(map(str,range(n)))+']);let data=(raw as Array).map_unordered(fn*(x:N32)->N32 {value(x)});'
     expr=f'tree_reads(data,{n},queries)' if mode=='tree_copy' else 'array_copy(data,queries)' if mode=='array_copy' else 'array_ref(&data,queries)'
     consume='dump(result,&io);' if measure=='correctness' else 'io.println("{sum(result)}");'
     p=out/f'n{n}_q{count}_{pattern}_{mode}_{measure}.vi';p.write_text(header+'pub fn main(&io:&IO){'+inputs+'let queries=black_box('+balanced(qs,str)+');let result='+expr+';'+consume+'}\n')
     r=run([sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib','sph='+str(lib),'--heap','2G']+(['--depth'] if measure=='depth' else [])+[str(p)],ROOT,p.with_suffix(''),180)
     got=list(map(int,Path(r['stdout']).read_text().split()));assert got==(expected if measure=='correctness' else [sum(expected)%2**32])
     if measure=='depth':
      entry=dict(n=n,queries=count,pattern=pattern,mode=mode,**parse_stats(Path(r['stderr']).read_text()));report['measurements'].append(entry);print(entry,flush=True)
     else:report['cases'].append(dict(n=n,queries=count,pattern=pattern,mode=mode,passed=True))
    write_json(out/'result.json',report)
report['library']=tree_hash(lib);write_json(out/'result.json',report)
