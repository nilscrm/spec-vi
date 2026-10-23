# Depth-first correction, 2026-10-06

User explicitly rejects checksum scheduling barriers and authorizes increased test
heap. Original 2GiB reports/policy remain historical controls, not a requirement to
serialize the new candidate. Begin with an explicit 8GiB experimental allocation.
Numerical tolerances, full sides12/16, three updates and 600s commands stay unchanged.

Dependency design: particles in each density/IAD/momentum stage independently read
immutable previous-stage data. Neighbor queries likewise depend on geometry/index,
not other query results. Replace gated tree branches with independent branches.
Retain original per-particle density sum order O(K), IAD/momentum balanced sums,
capacity checks and all physics. Arithmetic remains O(NK); ideal outer dispatch
is O(log N) instead of chained completion across N particles. Shared-reference
reads, copying and cleanup may still dominate measured depth. Remove full-state
checksum barriers including input guards; retain the materialize name as an identity
for driver compatibility. Timesteps and real data dependencies remain sequential.

Validation emits every field/scalar and exact ordered neighbors after all stages.
Measurement separately forces all final fields, scalars and time/energy/count history
with balanced consumers. Final forcing checksums are not scheduling gates between
particles. Compare normal, workers2 and depth separately; lower normal memory is a
hypothesis until matched runs establish it. Do not subtract standalone depths.

prepare.py preserves the unchanged library and generates the candidate reproducibly.
No toolchain, upstream, oracle or floating-point expression changes are intended.

Initial results: direct gate removal exhausts8GiB in both normal (26.41s) and
depth (77.04s) whole-update side12 runs. These failed runs yield no depth or
runtime-heap result; peak process RSS is not a substitute. A16GiB normal probe
is in progress. No larger workload or weakened numerical check is involved.

If pending reference gathers still exhaust memory, the next candidate will route
all indexed neighbor requests through a balanced value tree. Each request carries
an independent result connection; stable output trees preserve each neighbor's
position/order. Partition requests by index at each tree level, and duplicate only
the selected leaf payload into its consumers. Expected work O(R log N) for R neighbor
reads, routing depth O(log N * log R) before copying/cleanup. Each particle's density
fold remains ordered; IAD/momentum keep the same arithmetic. This is an unmeasured
hypothesis, not a hardware primitive or scheduling gate. Runtime construction,
request routing, payload copying and cleanup all remain in measurement.
