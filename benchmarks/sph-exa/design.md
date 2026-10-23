# SPH-EXA design decisions

No production representation is chosen yet. Preserve upstream numerical semantics as the initial comparison baseline; document reassociation explicitly. All simulation arithmetic and control belong in Vine; do not hide entire kernels in benchmark-specific native extrinsics.

## Dependency questions

For each stage enumerate input fields, output fields, particle-local operations, neighbor dependencies, global reductions, and dependencies on previous timesteps. Separate necessary physics dependencies from data-structure or traversal ordering.

## Candidates to evaluate

Balanced particle collections; partitioned field access; branching octree construction; independent neighbor queries with measured sharing/copying; balanced local and global reductions. Compare actual compiled depth and resource use before committing to layout.

## Evidence and decisions

Pilot uses balanced value trees for independent particle maps and reductions, and the original 20,000-entry harmonic value/derivative table in Lookup::Size32768. Initialization depth 441 versus serial-fold 826 (32 particles); density 644 versus 1497 (16 queries); work decreased slightly. Evidence and limits: LESSONS L009–L011 and reports/runs/20260915T161128Z-45040/pilot/.

Neighbor construction takes a balanced Tree of unique-id points. Queries depend on the constructed index and their own center/radius; they do not depend on other queries. A spatial hierarchy can prune independent child searches. Construction and index duplication must be included in measurements. Serial insertion and a serial neighbor accumulator are avoidable candidate dependencies. Measure a spatial hierarchy against a trusted serial point scan. Membership is exact, with strict squared-distance comparison and periodic query shifts. Return order can differ; downstream balanced arithmetic requires later multistep validation. Saturating the upstream neighbor capacity is outside this initial contract and must be resolved before full integration.

Initial neighbor hierarchy is rejected for performance: depth3453 versus scan516 at256 points, work growth12.88x for4x size. Exact membership passes. See LESSONS L012 and reports/neighbors/second-candidate/. Next experiments must isolate construction and data duplication costs; the candidate is not accepted for integration.

## Retained follow-up candidate

neighbors.vi now carries bounds/counts with partitions, uses small leaf buckets, infinity identities for empty bounds, and eager pure predicates. At256 particles/queries D1587, W11793450, heap20311232 bytes; full fixed membership cases pass. This improves D54.0% and W19.1% over the initial spatial tree but increases heap24.5%; it still fails the unchanged depth and work-growth gates. It remains experimental; physics implementation may proceed per the 2026-09-26 user priority below, but neither neighbor nor physics acceptance is implied. Failed scans, reference scans, bottom-up bounds and sampled splits are preserved under reports/neighbors/followup-1/. See L014–L015.

Next dependency question: can queries be routed in batches through an index so that construction, copying and cleanup do not serialize or repeat across all queries? The single-query value API makes broad duplication possible; the shared-root-reference experiment instead creates a long dependency chain. A batch representation needs an explicit output association scheme and the same correctness/resource measurements before adoption.

## Batched routing experiment (L016)

An isolated `find_batch(Index, Tree[(N32,Query)])` experiment associates each query with an independent result connection, allowing one spatial-index traversal to route request subsets. Compacted routing passes full fixed membership checks and reduces256-point work to4294285 and heap to7557088 bytes. Work growth7.91x passes the existing ceiling; depth1596 still fails. Removing all compaction gives depth1579 but fails work growth at12.91x. The production API and gate are unchanged; exact source/drivers live under reports/neighbors/batch-routing/. Next test bounded query tiles to balance routing depth and compaction work, and reduce construction independently. Query-only runs confirm compaction adds its own substantial dependency path.

## Rejected grouped compaction (L017)

Occupancy-based compaction every1–4 query-tree levels did not materially improve depth. Stride3 retained acceptable work growth but increased256-point work from4.29M to8.35M for depth1596 to1584; reject it. Diagnostic runtime construction depth is1286 when forcing all particle identities (different consumer, not a subtractable cost). Keep ordinary compacted batching and investigate construction topology/scalar reductions next. Evidence: reports/neighbors/tiled-routing/.

## Spatial-key builder results (L018)

Bottom-up compressed Morton merging, collision buckets, and independent coarse buckets preserve membership but do not beat the compacted recursive builder/query baseline. Best tested radix variant D2809 at256 remains worse than1596; do not promote it. A sequential N32.leading_zeros primitive was identified and a focused reusable root fix has passed separate and integrated dependency validation. No candidate is accepted by the neighbor depth gate. Future comparisons must use the new exact source pin consistently after integrated revalidation.

## Bounds and point-routing diagnostics (L019)

Separate coordinate trees and deferred bounds were measured with exact output checks and rejected for increased depth. Keep aggregate bounds and cached partition summaries. Fixed-split diagnostics do not establish full-builder costs. Next test the dependency added by compacting point branches, preserving empty branches only as an isolated alternative with full work accounting.

## Point partition compaction (L020)

Preserved point branches improve the isolated split but lose full pipeline depth/work; cached-count compaction also loses. Retain constructor-based joins. Next test the previously separate bottom-up bounds representation together with compacted query batching, using matched controls and runtime construction. This combination is untested, not an accepted architecture.

## Bottom-up bounds with batch queries (L021)

The combined runtime-built pipeline passes membership but fails budgets:8-point buckets reduce depth1596->1370 while increasing work4.04x. Host spatial ordering restores much of the work efficiency but leaves depth1360; sorting costs are excluded and this is only diagnostic evidence. Reject both runtime builders. Next test bounded independent query groups on the retained compact spatial index, including duplication costs, rather than assume another builder change resolves request-routing depth.

## Independent query groups (L022)

Groups of32 provide a small experimental improvement: D1570/W4320138/heap7117984 at256, versus full-batch1596/4294285/7557088. Still far above the depth target; no production promotion. Stop incremental routing-group sweeps. Next investigate independent dynamic access as a prerequisite for a spatial-cell representation, with runtime data and complete cost accounting. Static Lookup cannot simply store evolving particles.

## Runtime dynamic reads (L023)

Copied scalar-tree selection is shallower than high-count reference-based Array reads, but uses more work and memory. This is a prerequisite diagnostic, not neighbor performance evidence. Next compare direct spatial-cell selection with the bounds-tree baseline, preserving point bucket payloads and including runtime population/indexing costs.

## Direct spatial-cell prototype (L024)

Runtime8/64-cell grids preserve all fixed memberships and reduce depth to901/876 at256. Work26.61M/86.46M fails the fixed ceilings and scaling requirements, so neither is retained as production. Next compare cell-major processing with balanced per-query output combination to avoid repeated directory selections, including all construction and merge costs.

## Hardware-model correction (L025)

Host F64 sine hides software computation and is not a valid primitive for the target1000-core chip. This correction is complete for the workload domain: F64.sin_bounded is pure Vine, the host registration is removed, and the rebuilt pilot passes (L027). Preserve existing numerical evidence with this limitation; neighbor experiments do not call sine.

## Software sine (L027)

Initialization uses explicitly bounded pure Vine sine, with all reduction/polynomial work measured.32-particle depth518 and work4413315 supersede hidden-host-sine441/241675 for current comparisons. Density supplied-neighbor metrics are unchanged. Next reduce repeated per-axis sine calls through a measured runtime Cartesian product; general all-range sine and chip timing validation remain separate work.

## Runtime sine reuse (L028)

Initialization computes20 modes per axis in balanced value trees and uses them to construct exactly the original400-term reduction tree. Isolated pilot output dumps match the previous pure-Vine-sine implementation. At32 particles D528/W2249937/heap19319280 trades10 additional rounds for49% less work and63% less heap. Retained in production after ordinary-runner bootstrap/pilot validation (reports/runs/20260923T154358Z-6786); no native math or static sine results were introduced.

## Cell-major queries (L029)

Processing cells independently recovered work but increased256-point depth to2029 for64 cells. Replacing result zipping with independent connections lowered work to13.63M without changing depth. Reject both, retain the current production tree, and isolate range preparation versus bucket copying/scanning before another grid redesign. Full membership and separate worker checks pass; no policy changed.

## Captured-bounds preparation (L030)

Controlled explicit recursion removes the large preparation depth growth and lowers the64-cell full pipeline2029->794 without materially changing work13.64M. All fixed memberships and workers pass. This remains an experimental depth/work tradeoff against compact batching1596/4.29M; no production promotion. Next audit analogous aggregate captures, with matched recursion rather than speculative spatial changes.

## Capture audit (L031)

Whole-index and whole-bucket captured maps match explicit recursion, so keep them. A local Bounds copy inside query preparation recovers the same D794 full64-cell experiment as explicit recursion and passes all fixed checks. A standalone two-field affine map reproduces the capture-field depth effect. No compiler or production change is justified by this experiment alone. Next measure per-cell request filtering before bucket payload duplication.

## Filter before bucket distribution (L032)

The preferred grid experiment filters per-cell requests before copying points. At256 D775/W7957961/heap38552928; all fixed memberships and workers pass. This dominates production in depth/work but increases heap and remains a different batch API. Retain experimentally pending broader edge/random validation and explicit evaluator integration; keep compact batching as the lower-work alternative.

## Cleaned grid candidate and extra validation (L033)

The filtered grid passes16 extra fixtures through both APIs and reproduces D775/W7957961 after dead-code removal and formatting. Clean source: reports/neighbors/grid-clean/clean/sph/neighbors.vi. Ready for an explicit, separately reported batch evaluator path, with all controls and policies preserved; fixed-grid scalability and full physics remain open.

## Full-port implementation priority (2026-09-26)

Per user direction, finish batch evaluator integration, then prioritize an executable
complete square-patch update and multiple updates. The neighbor depth heuristic stays
failed; it does not prohibit implementing dependency-ready physics. Functional
coverage and performance acceptance remain separately reported. No acceptance budget
or required workload is removed.

Next implementation starts with separate reference instrumentation calling the same
functions and order as upstream sqpatch.cpp, dumping all particle fields and scalar
state after each stage. Preserve the original oracle and record ordered neighbor
lists, not just membership. The serial DistributedDomain::distribute recomputes the
bounding box each iteration; it must not be omitted as an assumed MPI-only operation.

Dependency plan before implementation (N particles, K neighbors per particle):

| Stage | Dependencies and necessary sequencing | Expected arithmetic work/depth, before measured gather/copy costs |
|---|---|---|
| Density and rest density | Current geometry, h, mass and neighbor membership; set ro_0 from computed ro only on iteration zero | O(NK); O(log K) with balanced sums, subject to numerical validation |
| Equation of state | Per-particle ro, ro_0, p_0; computes p and resets c=3500, u=1 each update | O(N), constant particle-local depth plus traversal |
| IAD | Current neighbor positions, mass, density; six moment sums precede local matrix inversion | O(NK), O(log K) reduction plus inversion |
| Momentum and energy rate | Neighbor velocity, pressure, density, sound speed and both IAD tensors | O(NK), O(log K) reductions |
| Timestep | h/c per particle, global minimum, maxDtIncrease*dt_m1[0]; broadcast minimum and advance ttot | O(N), O(log N) global reduction then broadcast |
| Positions and energy update | Current gradients/rates, selected dt, previous positions/dt/du; preserve read-before-write order and periodic wrap | O(N), constant particle-local depth plus traversal |
| Total energy | Updated velocity/u and mass, global kinetic/internal sums | O(N), O(log N) with reassociation validation |

These are proposed arithmetic scaling bounds, not compiled Vine measurements. State
gathers, copying, neighbor construction and consumers remain included in full-stage
and update measurements. Full dumps validate every field; balanced consumers must
force every output for depth runs. Compare copied/indexed state representations only
where actual gather costs block integration, rather than resuming broad grid tuning.
The next timestep necessarily consumes the prior updated state. Original sequential
C++ reductions remain the oracle; any alternative reduction-order reference is a
separate diagnostic. Integer-power arithmetic for EOS/kernel powers needs fixed
numerical validation and must not introduce native pow as a hidden algorithm.


## Integrated batch evaluator evidence (L034)

The cleaned grid is now benchmarks/sph-exa/vine/grid.vi, separately exported alongside
neighbors.vi. Explicit candidate selection measures build+find_batch; correctness
also covers both single-query paths. Ordinary runner20260926T152748Z-33131 reproduces
L033 metrics and passes all72 memberships plus bootstrap/pilot. Runtime construction,
all output forcing and unchanged serial baseline are verified. The depth heuristic
still fails; integration is not hardware or full-physics acceptance. The next work
is the full-update dependency plan above.

## First connected physics path (L035–L038)

physics.vi introduces named particle fields, conversions preserving the30-field
pilot schema, runtime balanced initialization, grid batch membership and density
payload gathering. Reference reads are a functional baseline with explicit serialized
access, not a depth improvement. EOS uses an explicit multiplication schedule for
power7 and resets u/c as upstream does. Independent full side16 initialization
and membership hit2GiB. Runtime xy-plane reuse passes all30 initial fields and
memberships on both sides while reducing work/memory and increasing depth (L035).
Bounded gather dispatch then passes one full update on both sides (L037–L038).
Three-update pressure and heap failures remain; the ordered candidate addresses
the former, and input-dispatch gating is a separate untested memory hypothesis.
The full original initializer is preserved in the experiment as a control.

L038 revises the proposed balanced density baseline: three-update side12 fails
pressure despite locally passing density. An original-order replay reproduces
all original densities from candidate geometry and removes pressure failures.
Implement runtime upstream octree ordering and a sequential density fold as a
correctness candidate. Its O(K) necessary sum depth is explicit; the retained grid
remains available and its failed performance gate is unchanged. Build from full
runtime points with stable128-particle buckets, traverse periodic root cells in
upstream order, and force all returned IDs and fields during validation. This is
numerical compatibility work, not another grid performance sweep.

The original-order candidate passes all3 updates on both fixed domains (L038) and
is integrated as ordered.vi/evolution.vi. The first full-update depth measurement
is16,636,726 rounds for1728 particles: ordered density and bounded query dispatch
are a correctness/resource baseline, not a shallow hardware implementation. The
extra prepare-entry checksum guard showed no side12 heap benefit and is not retained.

## Runnable serial driver plan (2026-09-30)

Add a native Vine entry point outside the library so ongoing library validation is
unchanged. Parse upstream -n/-s/-w options (defaults50/10/-1), with inclusive -s.
Each iteration calls the already validated prepare/density/rest/EOS/IAD/momentum/
timestep/positions/energy sequence and materializes each state. Write the original
seven constants columns each update and sixteen dump columns at the requested
frequency; radial distance/velocity are computed in Vine from updated state.
Native decimal formatting may differ from upstream's default six significant digits;
compare against separately derived high-precision reference fields, never relax the
original physics oracle. File output is necessarily ordered O(N) IO; it is excluded
from separate kernel measurements, which retain all-field/history forcing. Parsing,
file creation, formatting and final cleanup require actual CLI validation, including
-s0 and positive/disabled output frequencies. Invalid arguments fail before output.

L039: Native argument handling must not call debug::error as an exception in release.
The isolated argument-fix driver explicitly diagnoses and returns before simulation
or file creation. All five invalid-argument probes pass this observable contract;
nonzero exit status is unsupported by the pinned IO API and is not claimed. Keep the
computational loop unchanged when promoting this parser repair and validate positive
arguments against the original reference as well.

L040: Workers2 passes both sizes at1/3 updates, but depth mode side16/3 times out.
The repaired driver also times out on its largest check despite the unchanged
computational suffix. Isolate timing before attributing causality; preserve limits.

## Readiness scope (L041, user clarification2026-10-04)

Prioritize matching workload semantics and parameter-only scale-up capability,
validated on manageable domains. Full-scale timing is deferred. Review global count
widths (currently N32 neighbor totals), capacity/error handling and memory scaling
before claiming readiness. Separate SPEC-like adaptations from the unchanged upstream
oracle. Existing depth/resource failures remain recorded; no performance gate is
silently passed or tolerance relaxed by this scope clarification.


Scale audit2026-10-05 (L042): global ordered/evolution neighbor totals and capacity
products now use N64; local IDs/counts remain N32. Native --describe inspects
configuration without initialization. See SCALE_READINESS.md for dependencies,
arithmetic limits, storage lower bounds, and unresolved stabilization/error semantics.
Upstream's writeConstants narrows its64-bit total to int; Vine intentionally retains
the full total. Fixed small-domain numerical policies and upstream source are unchanged.


## Depth-first correction (L043, 2026-10-06)

The user rejects L037's checksum scheduling barriers. They are not a chosen final
architecture. Independent density/IAD/momentum particles and ordered neighbor queries
must not wait on other particles' completed checksums merely to fit2GiB. The isolated
candidate removes those gates and makes materialize an identity; unchanged dataflow
still enforces real stage/timestep dependencies. Original density fold remains O(K),
outer tree dispatch can branch O(log N); reference gathers may still serialize.
Use explicit8GiB experiment resources, full fixed numerical validation and separate
normal/depth measurements. See depth-first-20261006/EXPERIMENT.md; results pending.
