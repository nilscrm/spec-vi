"""Diagnostic builder/bounds cost on the retained runtime-built representation.
Identity checksum forces every particle leaf; final bounding metadata is discarded.
Bounds checksum separately forces all six bounding coordinates. No depth subtraction.
"""
import sys,shutil,json,struct,math
from pathlib import Path
sys.path.insert(0,'tools')
from evaluate import ROOT,run,parse_stats,write_json
from neighbors_gate import synthetic,point
from pilot_gate import balanced
out=ROOT/'reports/neighbors/builder-costs/radix';lib=out/'sph';lib.mkdir(parents=True,exist_ok=True)
source=ROOT/'reports/neighbors/radix-fixed-bits/sph'
for name in ['tree.vi','sph.vi']:shutil.copy2(source/name,lib/name)
s=(source/'neighbors.vi').read_text().replace('fn bounds(', 'pub fn bounds(')
(lib/'neighbors.vi').write_text(s)
consume='''use #sph::{neighbors,tree};use tree::Tree;
fn points(t: Tree[neighbors::Point])->N32 {match t{Tree::Empty(){0}Tree::Leaf(p){p.id+1}Tree::Branch(l,r){points(l)+points(r)}}}
fn index(t:neighbors::Index)->N32 {match t{neighbors::Index::Empty(){0}neighbors::Index::Leaf(p){p.id+1}neighbors::Index::Bucket(t){points(t)}neighbors::Index::Branch(_,l,r){index(l)+index(r)}}}
'''
results=[]
for name,pts,qs in synthetic():
 if not name.startswith('scaling_'):continue
 for mode in ['bounds','build']:
  p=out/(name+'_'+mode+'.vi')
  expr='let b=neighbors::bounds(t);let value=((b.xmin+b.xmax)+(b.ymin+b.ymax))+(b.zmin+b.zmax);let N64(lo,hi)=value.to_bits();io.println("{lo} {hi}");' if mode=='bounds' else 'io.println("{index(neighbors::build(t))}");'
  p.write_text(consume+'pub fn main(&io:&IO){let t=black_box('+balanced(pts,point)+');'+expr+'}\n')
  r=run([sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib','sph='+str(lib),'--depth',str(p)],ROOT,p.with_suffix(''),180)
  value=Path(r['stdout']).read_text()
  if mode=='build':assert int(value)==sum(p[0]+1 for p in pts)
  else:
   lo,hi=map(int,value.split());actual=struct.unpack('<d',struct.pack('<II',lo,hi))[0]
   expected=sum(min(p[k] for p in pts)+max(p[k] for p in pts) for k in (1,2,3));assert actual==expected
  results.append(dict(case=name,mode=mode,**parse_stats(Path(r['stderr']).read_text())))
write_json(out/'results.json',results);print(json.dumps(results,indent=2))
