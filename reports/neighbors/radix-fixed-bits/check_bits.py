import sys,random,shutil,json
from pathlib import Path
sys.path.insert(0,'tools')
from evaluate import ROOT,run,write_json,parse_stats
from pilot_gate import balanced
out=ROOT/'reports/neighbors/radix-fixed-bits/bit-check';lib=out/'sph';lib.mkdir(parents=True,exist_ok=True)
base=ROOT/'reports/neighbors/radix-fixed-bits/sph'
for name in ['sph.vi','tree.vi']:shutil.copy2(base/name,lib/name)
s=(base/'neighbors.vi').read_text().replace('fn high_bit(', 'pub fn high_bit(');(lib/'neighbors.vi').write_text(s)
rng=random.Random(7183);values=set([0,0xffffffff]+[rng.getrandbits(32) for _ in range(1024)])
for k in range(32):
 for x in [(1<<k)-1,1<<k,(1<<k)+1]:
  if x<=0xffffffff:values.add(x)
values=sorted(values);pairs=[(x,0 if x==0 else 1<<(x.bit_length()-1)) for x in values]
p=out/'check.vi';p.write_text('''use #sph::{tree,neighbors};use tree::Tree;
fn check(t:Tree[(N32,N32)])->N32 {match t{Tree::Empty(){0}Tree::Leaf((x,want)){if neighbors::high_bit(x)==want {0}else{1}}Tree::Branch(l,r){check(l)+check(r)}}}
pub fn main(&io:&IO){let t=black_box('''+balanced(pairs,lambda p:'('+str(p[0])+','+str(p[1])+')')+');io.println("{check(t)}");}\n')
r=run([sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib','sph='+str(lib),'--depth',str(p)],ROOT,out/'check',180)
assert Path(r['stdout']).read_text().strip()=='0'
write_json(out/'result.json',{'passed':True,'cases':len(pairs),'coverage':'zero, max, every power-of-two and adjacent values, 1024 seeded random words','stats':parse_stats(Path(r['stderr']).read_text())})
print(len(pairs),'bit-operation cases passed')
