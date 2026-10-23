# Scale readiness audit

The current application implements the pinned upstream square-patch equations.
It does not yet reproduce the SPEC adaptation. No full-scale simulation was run
for this audit. Configuration acceptance is not a memory or runtime feasibility result.

Use the native configuration-only path from the repository root:

```
python3 tools/vine_exec.py run --lib sph=benchmarks/sph-exa/vine \
  benchmarks/sph-exa/app/square_patch.vi -- --describe -n 210 -s 24 -w 7
```

Remove `--describe` only when intentionally running the simulation in a fresh output
directory with an appropriate heap setting. The upstream inclusive loop means
`-s 24` performs 25 updates. No stabilization phase is inserted.

## Arithmetic and storage

Particle IDs/counts are N32. Accepted side lengths are 10 through 1625;
1625 cubed is 4,291,015,625 and 1626 cubed exceeds N32. The maximum last-step
argument is 4,294,967,294 so the inclusive loop endpoint does not overflow.
These are arithmetic limits, not supported physical or practical operating ranges.
Global neighbor totals and capacity products now use N64, widening before
multiplication. Individual neighbor rows retain N32 lengths and the existing
unsaturated contract (fewer than 650 entries). Maximum aggregate capacity for any
N32 particle count is 2,791,728,741,750, safely below N64 and the exact-integer
range of F64 used by measurement checksums.

At side210, 9,261,000 particles have a capacity product of 6,019,650,000,
beyond N32. The 30 binary64 particle fields alone require 2,222,640,000 bytes,
already more than the current 2GiB test heap. This lower bound excludes tree nodes,
neighbor IDs, the spatial index, duplicate live states, runtime overhead, and
allocation temporaries. Dense 650-slot N32 neighbor storage would additionally
require 24,078,600,000 bytes; Vine uses dynamic trees instead, whose actual memory
must be measured. Small-run heap ratios are not a large-run feasibility proof.

Tree indices/start offsets stay below the validated particle-count bound.
Each update consumes its predecessor; stage materialization and bounded query
and gather dispatch remain necessary for the current measured memory baseline.
The capacity-width change preserves the reduction topology: O(total neighbor
entries) traversal, with O(log N) outer reduction depth before runtime copying
costs. Configuration inspection uses constant-size integer arithmetic and IO,
without constructing particles. Outputs are forced through native decimal output.

## Source semantics and remaining work

Public workload description: https://www.spec.org/cpu2026/Docs/benchmarks/803.sph_exa_s/803.sph_exa_s.html
(rechecked2026-10-05).

The pinned source `src/sqpatch.cpp` contains one inclusive evolution loop and no
15-step stabilization phase. Its `Domain.hpp` smoothing-length update is commented
out; ng0=500 does not implement an active convergence iteration. Public descriptions
of a stabilization count cannot establish what state is evolved/reset or when
sampling begins. Obtain the actual adaptation source before implementing this.
Initialization uses CGS units, h=2.5*100/side and mass=1000000/side^3. Copying
documented constants without unit and resolution reconciliation would change physics.

Upstream computes `totalNeighbors` as long long but passes it to the `int nntot`
parameter of `SqPatch::writeConstants`. The Vine output now keeps the complete
64-bit aggregate instead of reproducing this large-count narrowing. The original
source/oracle remain unchanged; fixed small-domain outputs remain the comparison.

Readiness still requires stabilization/output semantics, longer trajectory checks,
and explicit propagation of capacity/nonfinite/IO failures. In release execution,
`debug::error` is not an abort and the native driver has no nonzero exit-status API.
Current row saturation can therefore erase invalid results; it is not safe to claim
arbitrary trajectories are supported. The octree also has no bounded fallback for
more than128 coincident points. Existing depth failures and the largest depth-mode
timeout remain open. Full-scale runtime and target-hardware performance are unmeasured.

## Current validation evidence (2026-10-05)

`reports/physics/scale-readiness-20261005/full-stages/result.json` passes both
fixed domains, three updates each:56 snapshots of all30 fields and10 scalars,
plus exact ordered neighbors. Maximum field errors are2.1100277081131935e-10
(side12) and4.3655745685100555e-10 (side16), unchanged from the earlier library.
The fixed atol1e-9/rtol5e-12,2GiB heap and600-second command limits are unchanged.

| Side | Interactions including full dumps | Heap bytes | Runtime ms |
| --- | ---: | ---: | ---: |
| 12 | 8,530,050,485 | 553,140,400 | 179,380 |
| 16 | 22,350,462,444 | 1,309,769,984 | 483,431 |

These are normal execution measurements with correctness IO, not target-chip timing
or depth measurements. Configuration probes overlapped part of the regression;
runtime differences are not an isolated performance comparison. Work increased by
334,968 /860,532 interactions relative to the prior respective runs; heap is unchanged.

`configuration/result.json` passes capacity arithmetic across the32-bit boundary,
five native configuration sizes, and seven invalid-argument probes. The aggregate
probe measures D539/W3697/heap6208 bytes; native preflight heap is5968 bytes for every
size. These costs describe only allocation-free configuration inspection.


The native output gate passes all three original cases, including side16/three
updates within the unchanged timeout (510,016ms). The historical timeout is retained;
its cause is not established. All36 unit tests pass. `review.json` independently
verifies report coverage, current source hashes, unchanged upstream/oracle/policy,
and the pinned toolchain. Source and machine-readable evidence are checkpointed in
`reports/checkpoint-20261005-scale-readiness.tar.gz`. This accepts the counter and
configuration change within tested scope; SPEC-like workload readiness remains incomplete.
