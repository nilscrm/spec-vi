from pathlib import Path
p=Path('benchmarks/sph-exa/vine/neighbors.vi');s=p.read_text()
# Sentinel bounds make the empty element a genuine reduction identity.
s=s.replace('xmin: 0.0[F64]','xmin: F64::inf').replace('ymin: 0.0[F64]','ymin: F64::inf').replace('zmin: 0.0[F64]','zmin: F64::inf')
s=s.replace('xmax: 0.0[F64]','xmax: F64::neg_inf').replace('ymax: 0.0[F64]','ymax: F64::neg_inf').replace('zmax: 0.0[F64]','zmax: F64::neg_inf')
a=s.index('fn merge(');b=s.index('fn join(')
s=s[:a]+'''fn merge(a: Bounds,b: Bounds) -> Bounds {
 {n:a.n+b.n,xmin:min(a.xmin,b.xmin),xmax:max(a.xmax,b.xmax),ymin:min(a.ymin,b.ymin),ymax:max(a.ymax,b.ymax),zmin:min(a.zmin,b.zmin),zmax:max(a.zmax,b.zmax)}
}
'''+s[b:]
a=s.index('fn inside(');b=s.index('pub fn find(')
s=s[:a]+'''fn inside(p: Point,q: Query) -> Bool {
 let dx=q.x-p.x;let dy=q.y-p.y;let dz=q.z-p.z;
 let dxy=dx*dx+dy*dy;let r2=q.radius*q.radius;
 let a=q.z-q.period_z-p.z;let b=q.z+q.period_z-p.z;
 (p.id != q.id) & ((dxy+dz*dz < r2) | ((q.period_z > 0.0[F64]) & ((dxy+a*a < r2) | (dxy+b*b < r2))))
}
fn overlap_z(b: Bounds,z: F64,r: F64) -> Bool {(z+r>=b.zmin) & (z-r<=b.zmax)}
fn overlaps(b: Bounds,q: Query) -> Bool {
 ((q.x+q.radius>=b.xmin) & (q.x-q.radius<=b.xmax)) &
 ((q.y+q.radius>=b.ymin) & (q.y-q.radius<=b.ymax)) &
 (overlap_z(b,q.z,q.radius) | ((q.period_z>0.0[F64]) & (overlap_z(b,q.z-q.period_z,q.radius) | overlap_z(b,q.z+q.period_z,q.radius))))
}
'''+s[b:]
out=Path('reports/neighbors/followup-1/eager-cached/sph');out.mkdir(parents=True,exist_ok=True)
(out/'neighbors.vi').write_text(s);(out/'sph.vi').write_text('pub mod neighbors;pub mod tree;\n');(out/'tree.vi').write_text(Path('benchmarks/sph-exa/vine/tree.vi').read_text())
