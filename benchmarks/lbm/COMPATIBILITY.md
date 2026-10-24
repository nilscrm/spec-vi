# LBM compatibility notes (782.lbm_r)

## What the upstream is

SPEC's lbm is Thomas Pohl's D3Q19 lattice Boltzmann kernel (SPEC CPU2006 470.lbm, CPU2017
519.lbm_r/619.lbm_s). The SPEC CPU 2026 page for 782.lbm_r could not be fetched from the
development host (www.spec.org did not resolve), so the SPEC-specific changes are unknown.
The pinned upstream is the CPU version of the same kernel from the Parboil suite
(`upstream/lbm/`, Illinois/NCSA license; pin in `source.json`). It is the closest openly
licensed copy that could be fetched. **Confirm it against the SPEC page or kit.**

Parboil's copy differs from the SPEC lineage in ways that matter for a port:

- **Precision.** Parboil converted the grid and the kernel locals to `float` and added `f`
  suffixes to the kernel literals, including `OMEGA (1.95f)`. The in/outflow code still uses
  double literals, so the Parboil build mixes precisions. SPEC lbm is double precision (its
  documented footprint of about 400 MB for 100x100x130 cells x 20 entries x 2 grids only fits
  8-byte values). The port is double precision.
- **Driver.** Parboil replaced the SPEC command line (`lbm <steps> <result> <action>
  <simType> [<obstacle file>]`) with its own harness, which hard-codes the lid-driven cavity
  and the store action. The kernel functions for channel flow are still present.
- **Grid size.** 120x120x150 in Parboil, 100x100x130 in SPEC 470.lbm. Both are compile-time
  constants.

## Reference used for validation (adaptations, all in `reference/`)

- `double-precision.patch`: grid, kernel locals and allocator to `double`; kernel literals
  without `f` suffix (`1.95`, `0.005`, `0.002`, `1.5`, `4.5`, `3.0`, `1.0`); `SIZE`,
  `SIZE_X/Y/Z` overridable with `-D`. Nothing else changes; the arithmetic expressions and
  their order are untouched. Restoring the exact SPEC literal spellings is an assumption.
- `ref_main.c`: replaces Parboil's `main.c`. SPEC-style arguments (actions nil/store, simType
  LDC/channel, optional obstacle file), the upstream initialization order and time-step loop,
  plus a `--dump` option that writes the flags and the full distribution state after every
  step. The SPEC `compare` action is not implemented.
- Built with `cc -std=c99 -O2 -ffp-contract=off` (no FMA contraction, so the reference
  rounds every operation like Vine does).
- `gen_obstacles.py`: SPEC's obstacle files are not available. The generator writes the
  upstream obstacle format with `none`, `sphere` and seeded `random` patterns.
- The unmodified upstream `lbm.c` still compiles (`cc -c`); its Parboil `main.c` needs the
  Parboil runtime (`parboil.h`) and is not built.

## Semantics the port reproduces

- Both simulation types: lid-driven cavity (ACCEL lid planes) and channel flow (in/outflow
  planes rewritten before every collision).
- Push-style stream-collide with the upstream linear cell indexing. Streaming moves values
  by `dx + dy*SX + dz*SX*SY` linear places, so values leaving one row enter the next
  row (wrap-around). This only affects wall cells, but they are part of the output.
- Double buffering. Destination entries that no source writes keep the destination
  buffer's old value. In the lid-driven cavity that is always the initial distribution. In
  channel flow it is the in/outflow value from the previous step. Both cases are
  reproduced, and both show up in the output of wall/inflow cells.
- Output: `LBM_storeVelocityField` in binary mode, ux/uy/uz per cell as float32 computed
  with float variables (the upstream `OUTPUT_PRECISION` arithmetic).
- Arithmetic is evaluated in exactly the reference order. All validated states and outputs
  are bit-identical; no reassociation is used.

## Not reproduced / gaps

- `LBM_showGridStatistics` text output and the SPEC `compare` action. Statistics use a
  sequential `mass +=` sum; a port would use a balanced (reassociated) sum.
- SPEC inputs: obstacle files, step counts and grid size are SPEC-specific and unknown here.
  The default driver size is 100x100x130 (SPEC 470.lbm) but large runs are deferred (L048).
- The native driver reads the obstacle file and writes the result through sequential IO;
  measurement drivers generate obstacles in Vine instead (`obstacles.vi`).
- Grids need every dimension >= 4 (in/outflow planes must not overlap; upstream needs this
  too).
