# LBM design (782.lbm_r)

## Data dependencies (written before implementation)

Per time step, upstream does (channel flow only: step 0), then 1-2:

0. **In/outflow** (channel flow). Plane z=0 is rewritten from planes 1 and 2 (density
   extrapolation, parabolic inflow profile from x, y); plane SZ-1 from planes SZ-2 and SZ-3
   (velocity extrapolation, rho = 1). Per cell, independent within a plane. O(SX*SY) work,
   O(1) depth.
1. **Collide.** Each cell reads only its own 19 values and flags. Fully independent:
   O(N) work, O(1) depth. The density sum is a fixed left-to-right chain of 18 additions;
   it has constant length, so reassociation is not needed for depth scaling and is not
   used.
2. **Stream.** Every destination entry has exactly one source (linear index minus the
   direction offset), so the 19 directions are independent permutations. No arithmetic.
   On a flat array this is pure data movement. The only necessary sequential dependency
   in the whole program is between time steps.

Expected scaling of the port: work O(N) per step, depth O(log N) per step (tree
traversals for map/zip and O(log) push/pop for shifts), O(T log N) overall. Setup is the
same order as one step, except for sequential index rows (O(SX + SY + SZ), see gaps).

## Representation

- Grid = `Array[Array[Array[T]]]` (z, y, x). Array is a Braun-style balanced tree, so
  map/zip/unzip are balanced recursions and push/pop at either end is O(log n).
- State = grid of `Cell` records (19 F64) + static flag grid + channel boundary planes.
- **Stream as linear shifts.** A direction (dx, dy, dz) shifts values by
  dx + dy*SX + dz*SX*SY linear places. This is built from three structural shifts:
  x (pop the end of every row, shift the popped values one place in the row-major
  (z, y) order, push them onto the next row), y (the same with whole rows inside planes)
  and z (push/pop whole planes). This reproduces upstream wrap-around exactly. Work per
  shift is O(rows * log SX), so streaming is cheap next to collision.
- Directions whose components have opposite signs get one padding plane at each end,
  so values that step outside the grid at an intermediate stage come back (negative
  control: without padding channel-flow states fail from step 2).
- **Vacated entries.** Upstream destination entries that no source writes keep the old
  buffer value: in the lid-driven cavity the initial distribution (the shift fill value),
  in channel flow the previous step's in/outflow plane (`keep_vacated`, using the exact
  linear-index test). Negative control: without it channel flow fails from step 2.
- Split/merge: collision emits the 19 values as a balanced tree of pairs; five rounds of
  independent `Grid::unzip` split it into 19 grids, and five rounds of `Grid::zip` merge
  them back after the shifts.

## Measured (reports/lbm/candidate-20261024, pinned Vine fec2d8c8)

Command: `python3 tools/lbm_gate.py --output reports/lbm/candidate-20261024 --measure`
(heap 4 GiB, Linux host, `vine run [--depth]` on a generated driver). The driver covers
construction, all steps and a balanced checksum that forces every value. The checksum
bits match the reference final state reduced in the same order. Lid-driven cavity, cubes,
no obstacles. W = interactions, heap = normal-mode runtime heap.

| side | cells | D 0 steps | D 1 step | D 2 steps | D per step | W per cell-step | heap (2 steps) | heap/cell |
|---|---|---|---|---|---|---|---|---|
| 8 | 512 | 449 | 746 | 1,012 | 266 | 1836 | 1.2 MB | 2379 B |
| 12 | 1,728 | 482 | 777 | 1,043 | 266 | 1699 | 3.4 MB | 1972 B |
| 16 | 4,096 | 482 | 777 | 1,043 | 266 | 1626 | 7.0 MB | 1706 B |
| 24 | 13,824 | 515 | 808 | 1,074 | 266 | 1579 | 21.4 MB | 1548 B |
| 32 | 32,768 | 515 | 808 | 1,074 | 266 | 1551 | 47.9 MB | 1462 B |

16^3 over 8 steps: D 2,758 (about 283 per step after the first),
W 55.2M. Channel flow with the sphere obstacle:
357 depth per step at 16^3, 327 at 8^3.

Per-step depth is 266 at every size from 8^3 to 32^3. The O(log) terms are not visible
at these sizes. Before two depth fixes, it was 542 (LDC) and ~5000 for the first channel
step (L049).

Per-step cost split at 16^3 (controlled removals on the earlier chained split/merge,
LESSONS L049):

| part | depth/step | interactions/cell-step |
|---|---|---|
| collision (map) | 73 | 389 |
| split + merge (chain of 18 unzips + 18 zips) | 355 | 990 |
| shifts | 114 | 250 |

The balanced split/merge removed most of the 355 (per-step depth 542 -> 266, work
unchanged). Work is dominated by split/merge, not by arithmetic.

## Next candidates (measure before adopting)

- Single-pass n-way unzip/zip (needs a Vine Array primitive, e.g. a structural
  `Array::from_halves` inverse of `even_odd`, or a 19-way zip) to cut the ~990
  interactions/cell of split/merge.
- Parallel index construction (`Array::tabulate`-style) to replace sequential
  `Row::range` in setup.
- Group directions by dz/dy so a whole group shifts together (fewer padded shifts).
