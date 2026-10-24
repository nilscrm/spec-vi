# LBM compatibility notes (782.lbm_r)

## What the upstream is

SPEC's lbm is Thomas Pohl's D3Q19 lattice Boltzmann kernel (SPEC CPU2006 470.lbm, CPU2017
519.lbm_r/619.lbm_s). The pinned upstream is the CPU version of the same kernel from the
Parboil suite (`upstream/lbm/`, Illinois/NCSA license; pin in `source.json`). It is the
closest openly licensed copy available, **not the SPEC source**. The SPEC kit has not been
available, so source-level differences between it and SPEC 782.lbm_r cannot be checked yet.

### What the SPEC 782.lbm_r page says (read 2026-10-24)

From https://www.spec.org/cpu2026/Docs/benchmarks/782.lbm_r/782.lbm_r.html, also recorded
in `source.json`:

- Author Thomas Pohl, licensed to SPEC directly. ANSI C. The page does not mention Parboil.
- Command line `lbm <time steps> <result file> <0: nil, 1: cmp, 2: str> <0: ldc, 1: channel
  flow> [<obstacle file>]`, which matches `reference/ref_main.c` except for `cmp`.
- refrate: **1200 time steps on an obstacle file, 200 x 200 x 130 domain**. test and train
  use the same geometry with fewer steps (counts not stated).
- Obstacle files are ASCII: `.` is a fluid cell, any other character (`#`) is an obstacle.
- Output: a statistics summary on stdout. Action `str` writes binary little-endian
  vx/vy/vz per cell, single precision by default, double selectable in `config.h`.
- **Validation: SPEC validates the stdout statistics summary** (`LBM_showGridStatistics`).
  The `cmp` action reports the maximum absolute per-cell velocity difference against a
  threshold.
- "Highly similar" to 519.lbm_r, resized to about 1.6 GiB (about 4x CPU2017).
  `SPEC_LBM_NO_HUGE_ARRAY` exists for systems that cannot allocate large static arrays.
- Not stated: internal precision, lattice, test/train step counts, and which simulation
  type refrate uses. 200x200x130 cells x 20 entries x 2 grids x 8 bytes = 1.55 GiB, so the
  1.6 GiB footprint implies double precision.

### How Parboil's copy differs from SPEC

- **Precision.** Parboil converted the grid and the kernel locals to `float` and added `f`
  suffixes to the kernel literals, including `OMEGA (1.95f)`. The in/outflow code still uses
  double literals, so the Parboil build mixes precisions. SPEC lbm is double precision (see
  the footprint above). The port is double precision.
- **Driver.** Parboil replaced the SPEC command line with its own harness, which hard-codes
  the lid-driven cavity and the store action. The kernel functions for channel flow are
  still present.
- **Grid size.** 120x120x150 in Parboil, 100x100x130 in SPEC 470.lbm/519.lbm_r and
  **200x200x130 in SPEC 782.lbm_r**. All are compile-time constants. The native driver
  defaults to 200x200x130.
- **Allocation.** Parboil allocates the grids with `malloc`. The SPEC 2026 page implies
  large static arrays by default, which `SPEC_LBM_NO_HUGE_ARRAY` disables. This does not
  affect results.

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

- **`LBM_showGridStatistics`, the SPEC validation output.** SPEC validates the stdout
  statistics summary, so the port is not validated the way SPEC validates it until this
  is ported. The upstream statistics use a sequential `mass +=` sum. A port would use a
  balanced (reassociated) sum, validated against the original-order oracle with a fixed
  tolerance (L038). The SPEC `compare` action is also not ported.
- SPEC inputs: the 200x200x130 grid and 1200 refrate steps are known from the SPEC page.
  The obstacle files, test/train step counts and refrate simulation type are only in the
  kit. Large runs are deferred (L048).
- The native driver reads the obstacle file and writes the result through sequential IO;
  measurement drivers generate obstacles in Vine instead (`obstacles.vi`).
- Grids need every dimension >= 4 (in/outflow planes must not overlap; upstream needs this
  too).
