# SPH-EXA plan (803.sph_exa_s)

Status: **wrap-up** (docs/ROADMAP.md). Per the user's 2026-10-14 direction, finish the
items below and then move on to the next workload instead of chasing full completion.
History before 2026-10-14: HISTORY.md, LESSONS L001-L043, reports/.

## Current state

- Full square-patch physics is implemented in Vine: initialization, grid neighbors,
  density, EOS, IAD, momentum/energy, timestep, positions and total energy.
- The gated, original-order candidate passes all 56 stage snapshots with exact
  neighbor order at sides 12 and 16 over 3 updates (reports/physics/integration/
  validated-20260930, scale-readiness-20261005). Its checksum gates serialize
  particles, so it is not a valid depth candidate (L043).
- The ungated depth-first candidate (reports/physics/depth-first-20261006/) removes
  those gates. Its reference-gather form exhausts memory. The routed-gather form
  (depth-first-20261006/routed/sph) passes all 28 side-12 snapshots over 3 updates
  (12 GiB heap, W 9.25e9, heap 9.6 GB). Whole-update depth at side 12 is 226,706
  versus 16,653,836 gated (73x lower, +10% work, 30x heap); sides 6-10 show 46-66x (L047, reports/physics/routed-20261023/).
  Side 16 exhausted 12 GiB on the 15 GiB Linux host, so it is not promoted yet.
- The native driver is app/square_patch.vi. The side 16 / 3-update run timed out at
  600 s.
- Vine changes are committed on spec-vi/sph-support (work/vine) and pinned at fec2d8c8.
  Pilot, neighbor membership and full physics reproduce the previous metrics exactly
  (reports/vine/repin-20261014/).

## Wrap-up tasks

1. ~~**Migrate the Vine changes.**~~ Done 2026-10-14 (see above; L045).
2. ~~**Turn performance gates into reports.**~~ Done 2026-10-23: gates check correctness
   only, report `scaling`/`comparison` sections, and take `--heap-gib`/`--timeout`
   (docs/RUNNER.md). Pilot and neighbors pass (reports/runs/linux-20261023/).
3. **Validate the ungated candidate.** In progress: routed candidate passes side 12 (L047). Run full-stage validation at sides 12 and 16
   over 3 updates with whatever heap and timeout it needs (record both). If it is
   impractical even then, implement the routed-gather candidate described in
   depth-first-20261006/EXPERIMENT.md. Promote it to benchmarks/sph-exa/vine only after
   full validation passes.
4. **Depth table.** Measure whole-update depth/work/heap for the promoted candidate at
   several sides (smaller sides such as 6, 8 and 10 are fine for the scaling curve;
   correctness is still checked at 12 and 16), plus a 3-update run on at least one
   size. Record them in a machine-readable table under reports/physics/.
5. **Driver check.** Re-run the native driver cases with the promoted candidate and
   recorded limits.
6. **Write down gaps.** Update COMPATIBILITY.md/README with what remains: the SPEC
   stabilization phase and CSV output, native error exit status, all-range sine,
   full-scale runs and hardware timing.
7. Set this workload to `done` in docs/ROADMAP.md and LBM (782.lbm_r) to `active`.

## Next action

Task 3: run tools/physics_gate.py with `--library` set to the routed candidate at
sides 12 and 16 on a host with at least ~32 GiB (record heap and timeout). If no such
host is available, reduce the per-pair live footprint first (L047 hypotheses), without
gates. Then promote it and measure the task 4 table with tools/physics_measure.py.
