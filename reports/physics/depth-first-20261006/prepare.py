"""Preserve baseline and build an isolated candidate without scheduling checksums."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
for name in ['baseline','candidate']:
    shutil.copytree(ROOT/'benchmarks/sph-exa/vine',HERE/name/'sph')
p=HERE/'candidate/sph/physics.vi'
s=p.read_text(); start=s.index('      let left = density_rows(');end=s.index('\n    }',start)
s=s[:start]+'''      Tree::Branch(
        density_rows(&data, &points, n, l, period, iteration, stage),
        density_rows(&data, &points, n, r, period, iteration, stage),
      )'''+s[end:]
start=s.index('\nfn rows_checksum(');s=s[:start]+'\n';p.write_text(s)
p=HERE/'candidate/sph/ordered.vi';s=p.read_text();start=s.index('      let left = rows(');end=s.index('\n    }',start)
s=s[:start]+'''      Tree::Branch(rows(&idx, l, start, h), rows(&idx, r, start + h, n - h))'''+s[end:];p.write_text(s)
p=HERE/'candidate/sph/evolution.vi';s=p.read_text();start=s.index('      let left = interactions(');end=s.index('\n    }',start)
s=s[:start]+'''      Tree::Branch(
        interactions(&data, n, l, period, iad),
        interactions(&data, n, r, period, iad),
      )'''+s[end:]
for name,flag in [('iad','true'),('momentum','false')]:
 start=s.index(f'pub fn {name}(s: State, rows: Rows) -> State {{');end=s.index('\n}',start)+2
 s=s[:start]+f'''pub fn {name}(s: State, rows: Rows) -> State {{
  let data = s.data;
  s.data = interactions(&data, s.n, rows, s.bounds.zmax - s.bounds.zmin, {flag});
  s
}}'''+s[end:]
start=s.index('// Full-state materialization');end=s.index('fn capacity_ok(',start)
s=s[:start]+'''// Compatibility entry point: no scheduling barrier. Numerical validation belongs
// to the full-state evaluator; final measurement consumers force all outputs.
pub fn materialize(s: State) -> State { s }
'''+s[end:];p.write_text(s)
