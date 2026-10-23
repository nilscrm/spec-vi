# Full update candidate

Continue the L034 dependency plan and L035 coverage cycle in an isolated candidate
library while the first-stages regression runs. Do not change the running evaluator's
library. Implement upstream IAD, momentum/energy, timestep, positions and total energy
using named particle fields. Stage order, old-state dependencies, constants and kernel
multiplication order are source-preserved. Neighbor/global summations are balanced
and therefore reassociated; compare every state field after each stage and across
three updates against the original C++ oracle, at the existing tolerances.

All neighbor state is runtime data. Borrowed balanced-tree gathers are the current
functional baseline; their serialization and resource cost remain explicit. Density,
IAD and momentum have O(NK log N) gather work in addition to O(NK) arithmetic. Global
min/sums add O(N) work and O(log N) arithmetic depth; gathers and construction can
increase actual compiled depth. Copy/gather alternatives are measured separately.

Correctness emits both32-bit halves of every binary64 field, plus every neighbor ID
and scalar state. Decode exact bits before the same numeric comparisons: no checksum
replaces full-state validation. This avoids repeated expensive decimal F64 formatting.
Depth consumers force every output field and per-update energy/time records; worker
timing remains separate. Capacity>=650 must be diagnosed rather than silently claiming
order/saturation equivalence. Original fixtures, domain sizes and2GiB heap stay fixed.
