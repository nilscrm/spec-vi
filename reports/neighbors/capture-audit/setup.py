from pathlib import Path
import shutil
out=Path('reports/neighbors/capture-audit')
for variant in ['single_map','single_rec']:
 lib=out/variant/'sph';shutil.copytree('reports/neighbors/batch-routing/sph',lib,dirs_exist_ok=True)
 p=lib/'neighbors.vi';s=p.read_text();s=s[:s.index('pub fn find_batch(')]
 if variant=='single_map':s+='pub fn find_batch(index:Index,qs:Tree[(N32,Query)])->Tree[(N32,Tree[N32])]{#sph::tree::map(qs,fn*((i,q)){(i,find(index,q))})}\n'
 else:s+='''pub fn find_batch(index:Index,qs:Tree[(N32,Query)])->Tree[(N32,Tree[N32])]{match qs{
 Tree::Empty(){Tree::Empty()}Tree::Leaf((i,q)){Tree::Leaf((i,find(index,q)))}
 Tree::Branch(l,r){Tree::Branch(find_batch(index,l),find_batch(index,r))}
}}\n'''
 p.write_text(s)
s=Path('reports/neighbors/point-branches/full.py').read_text().replace("out=ROOT/'reports/neighbors/point-branches'","out=ROOT/'reports/neighbors/capture-audit'").replace("['compact','preserve']","['single_map','single_rec']")
(out/'full.py').write_text(s)
# Match the bucket-only diagnostic from L030, changing only map to recursion.
s=Path('reports/neighbors/cell-diagnostics/run.py').read_text().replace("out=ROOT/'reports/neighbors/cell-diagnostics'","out=ROOT/'reports/neighbors/capture-audit/bucket'").replace("for mode in ['ranges','scan']:","for mode in ['scan']:")
s=s.replace('let b=bounds(points);let bucket=select(labels(points,b),0);#sph::tree::map(qs,fn*((i,q)){(i,scan(bucket,q))})','let b=bounds(points);let bucket=select(labels(points,b),0);explicit_scan(bucket,qs)')
s=s.replace("p.write_text(s)","s+='''\nfn explicit_scan(bucket:Tree[Point],qs:Tree[(N32,Query)])->Tree[(N32,Tree[N32])]{match qs{Tree::Empty(){Tree::Empty()}Tree::Leaf((i,q)){Tree::Leaf((i,scan(bucket,q)))}Tree::Branch(l,r){Tree::Branch(explicit_scan(bucket,l),explicit_scan(bucket,r))}}}\n''';p.write_text(s)",1)
(out/'bucket').mkdir(exist_ok=True);(out/'bucket.py').write_text(s)
