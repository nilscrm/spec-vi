"""Alternative to serialized reference gathers; retains independently routed outputs."""
from pathlib import Path
import shutil
HERE=Path(__file__).resolve().parent
out=HERE/'routed/sph';shutil.copytree(HERE/'candidate/sph',out)
(out/'sph.vi').write_text((out/'sph.vi').read_text()+'\npub mod routed;\n')
(out/'routed.vi').write_text((HERE/'routed-source.vi').read_text())

p=out/'evolution.vi';s=p.read_text().replace('use #sph::{ordered, physics, pilot, tree};','use #sph::{ordered, physics, pilot, tree, routed};')
a=s.index('  let result = physics::density_rows(');b=s.index('\n  s\n}',a)
s=s[:a]+'''  let neighbors = routed::gather(points, s.n, rows);
  let period = s.bounds.zmax - s.bounds.zmin;
  s.data = tree::map(routed::zip(data, neighbors), fn* ((p,ns)) {
    physics::density(p, ns, period)
  });'''+s[b:]
for name,func in [('iad','iad_particle'),('momentum','momentum_particle')]:
 a=s.index(f'pub fn {name}(s: State, rows: Rows) -> State {{');b=s.index('\n}',a)+2
 s=s[:a]+f'''pub fn {name}(s: State, rows: Rows) -> State {{
 let data=s.data;let ns=routed::gather(data,s.n,rows);
 let period=s.bounds.zmax-s.bounds.zmin;
 s.data=tree::map(routed::zip(data,ns),fn* ((p,neighbors)) {{ {func}(p,neighbors,period) }});
 s
}}'''+s[b:]
p.write_text(s)
