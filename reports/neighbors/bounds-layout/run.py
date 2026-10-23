"""Matched bounds-layout diagnostics; includes conversion and point identity consumption.
Balanced reductions have logarithmic tree dependence; six independent reductions
may remove aggregate dependencies at increased traversal/copy work. No acceptance.
"""
import sys,json,shutil,struct
from pathlib import Path
sys.path.insert(0,'tools')
from evaluate import ROOT,run,parse_stats,write_json,tree_hash
from neighbors_gate import synthetic,point
from pilot_gate import balanced
from toolchain import verify
out=ROOT/'reports/neighbors/bounds-layout';pin=verify()
base=(ROOT/'benchmarks/sph-exa/vine/neighbors.vi').read_text().replace('fn bounds(', 'pub fn bounds(')
extra='''
fn low(t:Tree[F64])->F64 {match t {Tree::Empty(){F64::inf} Tree::Leaf(x){x} Tree::Branch(l,r){min(low(l),low(r))}}}
fn high(t:Tree[F64])->F64 {match t {Tree::Empty(){F64::neg_inf} Tree::Leaf(x){x} Tree::Branch(l,r){max(high(l),high(r))}}}
fn extent(t:Tree[F64])->(F64,F64) {match t {Tree::Empty(){(F64::inf,F64::neg_inf)} Tree::Leaf(x){(x,x)} Tree::Branch(l,r){let (a,b)=extent(l);let(c,d)=extent(r);(min(a,c),max(b,d))}}}
fn count(t:Tree[Point])->N32 {match t {Tree::Empty(){0}Tree::Leaf(_){1}Tree::Branch(l,r){count(l)+count(r)}}}
pub fn soa(t:Tree[Point])->Bounds {
 let x=#sph::tree::map(t,fn*(p:Point)->F64 {p.x});let y=#sph::tree::map(t,fn*(p:Point)->F64 {p.y});let z=#sph::tree::map(t,fn*(p:Point)->F64 {p.z});
 {n:count(t),xmin:low(x),xmax:high(x),ymin:low(y),ymax:high(y),zmin:low(z),zmax:high(z)}
}
pub fn pairs(t:Tree[Point])->Bounds {
 let x=#sph::tree::map(t,fn*(p:Point)->F64 {p.x});let y=#sph::tree::map(t,fn*(p:Point)->F64 {p.y});let z=#sph::tree::map(t,fn*(p:Point)->F64 {p.z});
 let (xmin,xmax)=extent(x);let(ymin,ymax)=extent(y);let(zmin,zmax)=extent(z);
 {n:count(t),xmin,xmax,ymin,ymax,zmin,zmax}
}
'''
lib=out/'sph';lib.mkdir(exist_ok=True)
(lib/'sph.vi').write_text('pub mod tree;pub mod neighbors;\n')
shutil.copy2(ROOT/'benchmarks/sph-exa/vine/tree.vi',lib/'tree.vi')
(lib/'neighbors.vi').write_text(base+extra)
header='''use #sph::{neighbors,tree};use tree::Tree;
fn ids(t:Tree[neighbors::Point])->N32 {match t{Tree::Empty(){0}Tree::Leaf(p){p.id+1}Tree::Branch(l,r){ids(l)+ids(r)}}}
fn bits(x:F64)->N32 {let N64(a,b)=x.to_bits();a+b}
'''
results=[]
for name,pts,qs in synthetic():
 if name not in ['scaling_64','scaling_256']:continue
 vals=[v for k in (1,2,3) for v in (min(p[k] for p in pts),max(p[k] for p in pts))]
 expected=[sum(struct.unpack('<II',struct.pack('<d',v)))%(2**32) for v in vals]
 expected += [len(pts),sum(p[0]+1 for p in pts)]
 for mode in ['bounds','soa','pairs']:
  for measure in ['correctness','depth']:
   p=out/f'{name}_{mode}_{measure}.vi'
   fields=['bits(b.'+x+')' for x in ['xmin','xmax','ymin','ymax','zmin','zmax']]+['b.n','ids(t)']
   lets=''.join(f'let v{i}={x};' for i,x in enumerate(fields))
   output=' '.join('{v'+str(i)+'}' for i in range(8)) if measure=='correctness' else '{value}'
   expr='' if measure=='correctness' else 'let value=((v0+v1)+(v2+v3))+((v4+v5)+(v6+v7));'
   p.write_text(header+'pub fn main(&io:&IO){let t=black_box('+balanced(pts,point)+');let b=neighbors::'+mode+'(t);'+lets+expr+'io.println("'+output+'");}\n')
   r=run([sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib','sph='+str(lib)]+(['--depth'] if measure=='depth' else [])+[str(p)],ROOT,p.with_suffix(''),180)
   actual=list(map(int,Path(r['stdout']).read_text().split()))
   assert actual==(expected if measure=='correctness' else [sum(expected)%(2**32)]),(actual,expected)
   if measure=='depth':
    entry=dict(case=name,mode=mode,**parse_stats(Path(r['stderr']).read_text()));results.append(entry);print(entry,flush=True)
write_json(out/'result.json',{'measurements':results,'correctness':True,'accepted_milestone':False,'library':tree_hash(lib),'pin':pin})
