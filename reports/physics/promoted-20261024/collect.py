#!/usr/bin/env python3
"""Build depth-table.json from the raw results in this directory (plan.md task 4)."""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows = []

# Sides 6-10: stage-heap drivers, 1 update, all final fields plus neighbor count forced.
# Numerical evidence is bit-identical forced checksums against the validated gated library.
pattern = re.compile(r'(\w+) side=(\d+) stage=8 depth=([\d_]+) heap=([\d_]+) W=([\d_]+) out=(\d+ \d+)')
small = {}
for line in (HERE/'small-sides/depth.log').read_text().splitlines():
    m = pattern.match(line)
    if m:
        lib, side, depth, heap, work, out = m.groups()
        small[(lib, int(side))] = dict(depth=int(depth.replace('_', '')), heap_bytes=int(heap.replace('_', '')),
                                       interactions=int(work.replace('_', '')), checksum_bits=out)
for side in sorted({s for _, s in small}):
    lean, gated = small[('final', side)], small[('baseline', side)]
    rows.append({'side': side, 'particles': side**3, 'updates': 1, 'source': 'small-sides/depth.log',
                 'numerical_check': 'forced checksum bits equal to gated library: ' + str(lean['checksum_bits'] == gated['checksum_bits']),
                 'depth': lean['depth'], 'interactions': lean['interactions'], 'heap_bytes': lean['heap_bytes'],
                 'gated': {k: gated[k] for k in ('depth', 'interactions', 'heap_bytes')}})

# Sides 12/16: tools/physics_measure.py with forcing checks against the stage oracle.
for name in sorted(HERE.glob('measure-*.json')):
    d = json.loads(name.read_text())
    if d['side'] == 12 and d['updates'] == 1 and 'measure-gated' not in name.name:
        gated = json.loads((HERE/'measure-gated-side12-u1.json').read_text())['stats']
    else:
        gated = None
    if 'measure-gated' in name.name:
        continue
    rows.append({'side': d['side'], 'particles': d['side']**3, 'updates': d['updates'], 'source': name.name,
                 'numerical_check': 'physics_measure forcing checks passed: ' + str(d['passed']),
                 'depth': d['stats']['depth'], 'interactions': d['stats']['interactions'],
                 'heap_bytes': d['stats']['heap_bytes'], 'resources': d['resources'],
                 'gated': {k: gated[k] for k in ('depth', 'interactions', 'heap_bytes')} if gated else None})

rows.sort(key=lambda r: (r['updates'], r['side']))
table = {'library': 'benchmarks/sph-exa/vine as promoted 2026-10-24 (tree sha256 in measure-*.json)',
         'toolchain': json.loads(next(HERE.glob('measure-*.json')).read_text())['toolchain'],
         'mode': 'vine run --depth (breadth-first); heap is the runtime heap high-water mark',
         'rows': rows}
(HERE/'depth-table.json').write_text(json.dumps(table, indent=2) + '\n')
for r in rows:
    g = r['gated']
    print(r['side'], r['updates'], r['depth'], r['interactions'], r['heap_bytes'], g and g['depth'])
