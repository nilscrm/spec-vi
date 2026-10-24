#!/usr/bin/env python3
"""Deterministic obstacle files in the upstream LBM format (spec-vi adaptation).

The SPEC obstacle inputs are not redistributable and not available here. Upstream
LBM_loadObstacleFile reads SIZE_Z planes of SIZE_Y lines of SIZE_X characters; any
character other than '.' marks an obstacle. Each line and each plane ends with one
separator character, so the file has SIZE_X*SIZE_Y*SIZE_Z + (SIZE_Y+1)*SIZE_Z bytes.

Patterns:
  none    all fluid (equivalent to running without an obstacle file)
  sphere  one ball of radius min(size)/4 at the domain centre
  random  each cell is an obstacle with probability 0.05 (seeded, reproducible)
"""
import argparse
import random


def cells(pattern, sx, sy, sz, seed):
    rng = random.Random(seed)
    r = min(sx, sy, sz) / 4
    cx, cy, cz = (sx - 1) / 2, (sy - 1) / 2, (sz - 1) / 2
    for z in range(sz):
        for y in range(sy):
            for x in range(sx):
                if pattern == 'none':
                    yield False
                elif pattern == 'sphere':
                    yield (x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2 <= r * r
                else:
                    yield rng.random() < 0.05


def render(pattern, sx, sy, sz, seed=1):
    it = cells(pattern, sx, sy, sz, seed)
    out = []
    for _ in range(sz):
        for _ in range(sy):
            out.append(''.join('#' if next(it) else '.' for _ in range(sx)) + '\n')
        out.append('\n')
    text = ''.join(out)
    assert len(text) == sx * sy * sz + (sy + 1) * sz
    return text


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('pattern', choices=('none', 'sphere', 'random'))
    p.add_argument('sx', type=int)
    p.add_argument('sy', type=int)
    p.add_argument('sz', type=int)
    p.add_argument('output')
    p.add_argument('--seed', type=int, default=1)
    a = p.parse_args()
    with open(a.output, 'w', newline='\n') as f:
        f.write(render(a.pattern, a.sx, a.sy, a.sz, a.seed))


if __name__ == '__main__':
    main()
