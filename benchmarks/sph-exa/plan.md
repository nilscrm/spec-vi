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
  those gates. Side 12, 1 update, normal mode at 16 GiB completes: W 2.38e9, runtime
  heap 10.5 GB, 99 s. At 16 GiB and the 600 s limit, depth mode and full-stage
  validation both timed out, so the candidate has no depth number and is not yet
  numerically validated.
- The native driver is app/square_patch.vi. The side 16 / 3-update run timed out at
  600 s.
- Vine changes are committed on spec-vi/sph-support (work/vine) and pinned at fec2d8c8.
  Pilot, neighbor membership and full physics reproduce the previous metrics exactly
  (reports/vine/repin-20261014/).

## Wrap-up tasks

1. ~~**Migrate the Vine changes.**~~ Done 2026-10-14 (see above; L045).
2. **Turn performance gates into reports.** The thresholds in
   evaluations/sph-exa/neighbors-policy.json (max_depth_ratio, the 361.2 figure,
   max_depth_growth) and pilot-policy.json, plus the fixed 2 GiB heap, become reported
   metrics compared against a baseline rather than pass/fail gates (AGENTS.md).
   Correctness gates are unchanged. Make heap size and timeout explicit run
   parameters recorded with each result. Update tools/, docs/RUNNER.md and the runner
   status so a measurement no longer shows as a failed milestone.
3. **Validate the ungated candidate.** Run full-stage validation at sides 12 and 16
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

Task 2: turn the performance thresholds into reported metrics, so the runner reflects
the correctness-only acceptance policy. Then continue with task 3.
