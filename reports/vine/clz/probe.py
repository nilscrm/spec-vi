"""Independent semantic vectors and matched consumers for a reusable CLZ fix."""
import sys,random,json
from pathlib import Path
sys.path.insert(0,'tools')
from evaluate import ROOT,run,parse_stats,write_json
from pilot_gate import balanced
out=ROOT/'reports/vine/clz';lib=out/'sph';lib.mkdir(parents=True,exist_ok=True)
(lib/'sph.vi').write_text('pub mod tree;pub mod bits;\n');(lib/'tree.vi').write_text((ROOT/'benchmarks/sph-exa/vine/tree.vi').read_text())
(lib/'bits.vi').write_text('''pub fn leading_zeros(n:N32)->N32 {
 if n==0 {32}else{
 let z=0;
 if n<0x10000 {n <<= 16;z += 16;}
 if n<0x1000000 {n <<= 8;z += 8;}
 if n<0x10000000 {n <<= 4;z += 4;}
 if n<0x40000000 {n <<= 2;z += 2;}
 if n<0x80000000 {z+1}else{z}
 }
}
''')
rng=random.Random(8827);xs=set([0,0xffffffff]+[rng.getrandbits(32) for _ in range(1024)])
for k in range(32):xs.update([(1<<k)-1,1<<k,(1<<k)+1])
xs=sorted(xs);pairs=[(x,32-x.bit_length()) for x in xs]
header='use #sph::{tree,bits};use tree::Tree;\n'
p=out/'correctness.vi';p.write_text(header+'''fn check(t:Tree[(N32,N32)])->N32 {match t{Tree::Empty(){0}Tree::Leaf((x,w)){if bits::leading_zeros(x)==w {0}else{1}}Tree::Branch(l,r){check(l)+check(r)}}}
pub fn main(&io:&IO){let t=black_box('''+balanced(pairs,lambda p:'('+str(p[0])+','+str(p[1])+')')+');io.println("{check(t)}");}\n')
argv=[sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib','sph='+str(lib)]
r=run(argv+[str(p)],ROOT,out/'correctness',180);assert Path(r['stdout']).read_text().strip()=='0'
results=[]
for count in [1,32,len(xs)]:
 values=[0xffffffff] if count==1 else xs[:count] if count==len(xs) else [xs[round(i*(len(xs)-1)/(count-1))] for i in range(count)]
 for mode in ['old','fast']:
  fn='x.leading_zeros()' if mode=='old' else 'bits::leading_zeros(x)'
  p=out/f'n{count}_{mode}.vi';p.write_text(header+'fn sum(t:Tree[N32])->N32 {match t{Tree::Empty(){0}Tree::Leaf(x){'+fn+'}Tree::Branch(l,r){sum(l)+sum(r)}}}\npub fn main(&io:&IO){let t=black_box('+balanced(values,str)+');io.println("{sum(t)}");}\n')
  r=run(argv+['--depth',str(p)],ROOT,p.with_suffix(''),180)
  assert int(Path(r['stdout']).read_text())==sum(32-x.bit_length() for x in values)
  entry=dict(count=count,mode=mode,**parse_stats(Path(r['stderr']).read_text()));results.append(entry);print(entry,flush=True)
write_json(out/'result.json',{'semantic_cases':len(xs),'passed':True,'measurements':results})
