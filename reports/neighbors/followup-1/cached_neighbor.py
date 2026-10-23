from pathlib import Path
out=Path('reports/neighbors/followup-1')
s=(out/'original.vi').read_text()
a=s.index('fn partition(');b=s.index('fn inside(')
s=s[:a]+'''// Return bounds together with partitions, avoiding another traversal at each level.
fn partition(t: Tree[Point],axis: N32,mid: F64) -> ((Bounds,Tree[Point]),(Bounds,Tree[Point])) {
 match t {
  Tree::Empty() { ((bounds(Tree::Empty()),Tree::Empty()),(bounds(Tree::Empty()),Tree::Empty())) }
  Tree::Leaf(p) {
   let v=if axis==0 {p.x} else {if axis==1 {p.y} else {p.z}};
   let leaf=(bounds(Tree::Leaf(p)),Tree::Leaf(p));let empty=(bounds(Tree::Empty()),Tree::Empty());
   if v < mid {(leaf,empty)} else {(empty,leaf)}
  }
  Tree::Branch(l,r) {
   let ((a,ll),(b,lr))=partition(l,axis,mid);let ((c,rl),(d,rr))=partition(r,axis,mid);
   ((merge(a,c),join(ll,rl)),(merge(b,d),join(lr,rr)))
  }
 }
}
fn unsplit(t: Tree[Point]) -> Index {
 match t {
  Tree::Empty() {Index::Empty()}
  Tree::Leaf(p) {Index::Leaf(p)}
  Tree::Branch(l,r) {Index::Bucket(Tree::Branch(l,r))}
 }
}
pub fn build(points: Tree[Point]) -> Index {let b=bounds(points);build_rec(points,b,0)}
fn build_rec(points: Tree[Point],b: Bounds,level: N32) -> Index {
 if b.n<=8 or level>=32 {unsplit(points)} else {
  let dx=b.xmax-b.xmin;let dy=b.ymax-b.ymin;let dz=b.zmax-b.zmin;
  let axis=if (dx>=dy) & (dx>=dz) {0} else {if dy>=dz {1} else {2}};
  let lo=if axis==0 {b.xmin} else {if axis==1 {b.ymin} else {b.zmin}};
  let hi=if axis==0 {b.xmax} else {if axis==1 {b.ymax} else {b.zmax}};
  let mid=lo+(hi-lo)*0.5[F64];
  if (mid<=lo) | (mid>=hi) {unsplit(points)} else {
   let ((a,l),(c,r))=partition(points,axis,mid);
   Index::Branch(b,build_rec(l,a,level+1),build_rec(r,c,level+1))
  }
 }
}
fn scan(t: Tree[Point],q: Query) -> Tree[N32] {
 match t {Tree::Empty() {Tree::Empty()} Tree::Leaf(p) {if inside(p,q) {Tree::Leaf(p.id)} else {Tree::Empty()}} Tree::Branch(l,r) {Tree::Branch(scan(l,q),scan(r,q))}}
}
'''+s[b:]
s=s.replace('  Leaf(Point),','  Leaf(Point),\n  Bucket(Tree[Point]),')
s=s.replace('    Index::Empty() { Tree::Empty() }','    Index::Empty() { Tree::Empty() }\n    Index::Bucket(t) { scan(t,q) }')
lib=out/'cached'/'sph';lib.mkdir(parents=True,exist_ok=True)
(lib/'neighbors.vi').write_text(s)
(lib/'sph.vi').write_text('pub mod neighbors;pub mod tree;\n')
(lib/'tree.vi').write_text(Path('benchmarks/sph-exa/vine/tree.vi').read_text())
