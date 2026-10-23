"""Independent coarse buckets trade construction work for depth; no gate changes."""
import sys,shutil,json
from pathlib import Path
sys.path.insert(0,'tools')
from evaluate import ROOT,run,parse_stats,write_json,tree_hash
from neighbors_gate import synthetic,driver,oracle,validate_rows
base=ROOT/'reports/neighbors/batch-routing/sph';out=ROOT/'reports/neighbors/independent-buckets';out.mkdir(exist_ok=True)
original=(base/'neighbors.vi').read_text().replace('pub fn build(points: Tree[Point])','pub fn split_build(points: Tree[Point])')
extra='''
type Entry = (N32,Point);
fn bin(x:F64,lo:F64,hi:F64)->N32 {
 if hi>lo {let q=((x-lo)/(hi-lo)*AXIS.0[F64]) as N32;if q>=AXIS {AXIS-1}else{q}}else{0}
}
fn spread_bin(x:N32)->N32 {(x & 1) | ((x & 2) << 2) | ((x & 4) << 4)}
fn label(points:Tree[Point],b:Bounds)->Tree[Entry] {
 match points {
 Tree::Empty(){Tree::Empty()}
 Tree::Leaf(p){let k=spread_bin(bin(p.x,b.xmin,b.xmax)) | (spread_bin(bin(p.y,b.ymin,b.ymax)) << 1) | (spread_bin(bin(p.z,b.zmin,b.zmax)) << 2);Tree::Leaf((k,p))}
 Tree::Branch(l,r){Tree::Branch(label(l,b),label(r,b))}
 }
}
fn select(points:Tree[Entry],cell:N32)->Tree[Point] {
 match points {
 Tree::Empty(){Tree::Empty()}
 Tree::Leaf((k,p)){if k==cell {Tree::Leaf(p)}else{Tree::Empty()}}
 Tree::Branch(l,r){join(select(l,cell),select(r,cell))}
 }
}
fn cells(points:Tree[Entry],first:N32,count:N32)->(Bounds,Index) {
 if count==1 {
  let t=select(points,first);let b=bounds(t);
  (b,Index::Branch(b,unsplit(t),Index::Empty()))
 }else{
  let half=count/2;let (a,l)=cells(points,first,half);let (b,r)=cells(points,first+half,half);let box=merge(a,b);
  (box,Index::Branch(box,l,r))
 }
}
pub fn build(points:Tree[Point])->Index {let b=bounds(points);cells(label(points,b),0,CELLS).1}
'''
results=[]
for axis in [2,4]:
 target=out/f'axis{axis}';lib=target/'sph';lib.mkdir(parents=True,exist_ok=True)
 (lib/'neighbors.vi').write_text(original+extra.replace('AXIS',str(axis)).replace('CELLS',str(axis**3)))
 for name in ['sph.vi','tree.vi']:shutil.copy2(base/name,lib/name)
 write_json(target/'source.json',tree_hash(lib))
 for name,pts,qs in synthetic():
  if not name.startswith('scaling_'):continue
  expected=[oracle(pts,q) for q in qs]
  for mode in ['correctness','depth']:
   p=target/(name+'_'+mode+'.vi');driver(pts,qs,p,'correctness' if mode=='correctness' else 'candidate')
   p.write_text(p.read_text().replace('tree::map(queries,fn* ((i,q)) {(i,neighbors::find(index,q))})','neighbors::find_batch(index,queries)'))
   argv=[sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib','sph='+str(lib),'--heap','2G']
   if mode=='depth':argv+=['--depth']
   r=run(argv+[str(p)],ROOT,p.with_suffix(''),180);text=Path(r['stdout']).read_text()
   if mode=='correctness':validate_rows(text,expected)
   else:
    assert int(text)==sum(i+1 for row in expected for i in row)
    entry=dict(axis=axis,case=name,**parse_stats(Path(r['stderr']).read_text()));results.append(entry);print(entry,flush=True);write_json(out/'results.json',results)
