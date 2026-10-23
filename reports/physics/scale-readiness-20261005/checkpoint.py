"""Archive source, guidance and machine-readable evidence; raw dumps stay in place."""
import json
from pathlib import Path
import tarfile
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
if not json.loads((HERE/'review.json').read_text())['passed']:
    raise SystemExit('Review did not pass')
paths=[]
for name in ['docs','tools','tests','evaluations','benchmarks/sph-exa/vine','benchmarks/sph-exa/app']:
    paths.extend(p for p in (ROOT/name).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
for name in ['README.md','AGENTS.md','benchmarks/sph-exa/plan.md','benchmarks/sph-exa/design.md','benchmarks/sph-exa/COMPATIBILITY.md','benchmarks/sph-exa/SCALE_READINESS.md','benchmarks/sph-exa/source.json']:
    paths.append(ROOT/name)
paths.extend(p for p in HERE.rglob('*') if p.is_file() and p.suffix in ['.py','.vi','.json','.stderr','.log'] and 'decoded' not in p.parts and 'expected' not in p.parts)
archive=ROOT/'reports/checkpoint-20261005-scale-readiness.tar.gz'
with tarfile.open(archive,'x:gz') as tar:
    for p in sorted(set(paths)):
        tar.add(p,arcname=p.relative_to(ROOT))
print(archive)
