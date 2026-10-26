# SPH-EXA plan (803.sph_exa_s)

Status: **done** (wrapped up 2026-10-24, docs/ROADMAP.md). The known gaps below stay
open. History before 2026-10-14: HISTORY.md, LESSONS L001-L043, reports/.

## Current state

- Full square-patch physics is implemented in Vine without scheduling gates:
  initialization, ordered octree neighbors, density, EOS, IAD, momentum/energy,
  timestep, positions and total energy (design.md, "Promoted depth-first evolution").
- Correctness: all 56 stage snapshots pass at sides 12 and 16 over 3 updates, with
  exact upstream neighbor order and unchanged tolerances (L049,
  reports/physics/promoted-20261024/physics-gate-side{12,16}.json).
- Depth table: reports/physics/promoted-20261024/depth-table.json (sides 6-16, plus
  3 updates at side 12). At side 12, one update has depth 228,116 versus 16,653,836 for the
  gated library, with 4% less work and 8x the heap (2.66 GB).
- Native driver: app/square_patch.vi passes all three driver_gate cases, including
  side 16 / 3 updates (reports/physics/promoted-20261024/driver-gate.json).
- Toolchain: Vine spec-vi/sph-support pinned at fec2d8c8. The evidence from 2026-10-23
  onward was produced on a Linux host against a host-generated oracle (L046).

## Known gaps

- **Neighbor search is 89-96% of depth and grows with N** (L050). The suspected cause
  is ordered::rows threading a shared index reference through all queries. A
  batch-routed octree query that keeps upstream bucket order is the next depth
  improvement.
- Heap is ~1.6 MB per particle at sides 12-16, so medium inputs need a larger host:
  side 30 extrapolates to ~45 GB. This extrapolation is a hypothesis.
- SPEC stabilization phase and CSV output are not implemented; the stabilization
  source is unavailable (SCALE_READINESS.md).
- No native nonzero exit status on errors (L039). `F64.sin_bounded` covers only
  |x| <= 128; there is no all-range sine.
- Full-scale SPEC inputs and hardware timing are deferred (L048).
- The Mac stage oracle lacks 31 gitignored snapshots in git. Reruns on the original
  machine should regenerate the evidence against the canonical oracle.

## Next action

Start LBM (782.lbm_r) with the per-workload lifecycle in docs/ROADMAP.md: survey,
evaluator, port. Return to SPH-EXA only for the neighbor-search depth gap.
