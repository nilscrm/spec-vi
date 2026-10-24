# Vine porting workflow

## Evaluation first

Build an evaluator before scaling automated implementation. It must compile the pinned C++ reference and Vine candidate, compare intermediate and final states, measure depth/work/memory, and emit machine-readable results. Use valid small cases, increasing sizes, perturbed or clustered inputs where applicable, and multiple timesteps. Fix tolerances before judging candidates. Depth, work and memory are reported and compared against a baseline on the same toolchain, not gated by absolute thresholds (AGENTS.md, L044).

For each component: dependency analysis -> candidate -> correctness -> depth scaling -> investigate avoidable dependencies -> integrated checks -> documentation update -> checkpoint. Continue with the next dependency-ready component.

## Measurement contract

The inspected Vine implementation maps --depth to breadth-first normalization; it counts rounds of active interactions. It selects this path before the worker execution path. Measure depth and actual parallel runtime in separate runs. Extrinsic operations are counted at runtime interaction granularity; depth is not a hardware cycle prediction.

Capture total interactions W, depth D, runtime heap statistics, process peak memory, numerical errors, and separate parallel timings. Minimize D subject to fixed correctness; raise heap/time limits (and record them) when a run is impractical rather than adding dependencies. W/D is descriptive, not an optimization objective on its own.

Use full state dumps for correctness. A depth driver must force every measured output using a validated, bounded-depth consumer; unused results may be erased. Account for input construction, output consumption, duplication, and cleanup. Do not blindly subtract standalone depths from total depth. Record kernel, full-timestep, and multi-timestep measurements because integration can add dependencies.

## Initial design hypotheses to test

- Balanced array construction and map/zip traversal can expose independent particle work.
- Balanced reductions can remove accumulator chains; floating-point reassociation requires a fixed numerical acceptance policy.
- Spatial subdivision may expose more parallel tree construction than serial insertion.
- Independent neighbor queries may still serialize through shared access. Compare partitioned traversal and controlled duplication with shared references, measuring work and memory as well as depth.
- Cross-timestep state dependencies are necessary; whole-dataset sequencing inside a particle-independent stage requires justification.

These are candidate strategies, not measured performance conclusions. The local Array implementation provides map_unordered, zip_with, and reduce_unordered with branching recursion; benchmark their compiled behavior and closure captures before relying on a depth bound.

## Learning and continuation

Apply the mandatory learning loop in AGENTS.md after each useful discovery. Maintain evidence in LESSONS.md, general techniques here, and benchmark-specific decisions beside the port. The runner in tools/runner.py independently reruns registered acceptance gates, preserves reports, and refuses completion when any required gate is absent or fails. See RUNNER.md. Numerical comparison, high-precision pilot snapshots, full-stage snapshots, reported depth/work/heap scaling with optional `--baseline` comparison, and per-process peak-memory recording are implemented. Heap and timeout are recorded run parameters (L044).

## Construction belongs in the cost model

A spatial hierarchy is not automatically an improvement: the first SPH neighbor candidate passed membership but had much higher depth than a scan (L012). Measure construction, repeated reductions, partition compaction and duplication. A serial-looking source accumulator may compile to a shallower graph than expected. Require actual compiled comparisons before choosing the representation.

## Measured representation guidance

Carry partition summaries with partition results to avoid repeated traversals (L014). Where operations are total and pure, compare eager boolean composition with short-circuit control; it can reduce dependencies but increase live memory. A true reduction identity can eliminate branches guarding empty values. Preserve strict geometric arithmetic and test boundaries when applying these transformations.

A shared root reference can serialize independent queries even when it lowers work: the SPH scan changed from depth506 to6661 at256 points (L015). Measure depth and work together. Batched routing is a hypothesis to evaluate, not an established solution.

## Batch queries without an ordered output merge

Independent result connections can preserve query identity while routing batches through one index (L016). This reduced repeated index work and met the SPH work-growth budget, but compacting dynamic request trees added depth. Compare both routing and compaction costs; retaining every empty branch can recover depth while losing work scaling. Keep construction in acceptance measurements, and treat prebuilt-index runs only as diagnostics.

A logically empty routed-request collection can still contain linear result-connection types. Resolve or explicitly drain those connections rather than relying on unsafe erasure (L017). Include this cleanup in performance measurements. Coarser compaction is not inherently faster: reject tiny depth gains that substantially increase work, even when one resource ceiling still passes.

Inspect hot scalar library calls before redesigning an algorithm around them. SPH radix construction exposed a bit-by-bit N32.leading_zeros loop (L018). A bounded binary search preserved semantics and lowered measured depth/work. Test zero and every power-of-two boundary plus independent random vectors, check all library callers, and repin root sources before integrated comparisons. Primitive improvements do not establish that the enclosing algorithm is competitive.

Measure field extraction and conversion when comparing array-of-records with separate coordinate trees. Independent scalar reductions may increase both depth and work (L019). Likewise, deferring summary calculation can save work/memory while lengthening the critical path; use matched fully forced outputs before integrating either representation.

A local compaction dependency may prevent far greater work downstream. SPH point partitions became shallower without compaction, yet the full recursive pipeline became deeper and performed nearly12x the work (L020). Always measure repeated consumers before retaining a local structural optimization. Cached counts are not automatically a faster substitute for inspecting constructors.

Use preordered-input diagnostics to distinguish spatial-locality work costs from routing depth, but label all excluded preprocessing explicitly. Improved locality need not reduce the critical path (L021); a faster index builder alone cannot establish shallow query routing.

Separate static constant lookup from runtime-generated data access when planning spatial indexes. Inspect the API and measure independent runtime reads, including construction, ownership/copying and cleanup; logarithmic lookup work alone does not establish logarithmic batch depth (L022).

When comparing indexed-read ownership, report construction differences and access distribution as well as batch size. Scalar results may favor copied values in depth and references in work/memory; benchmark actual bucket payloads before proposing a reusable library addition (L023).

A shallow scalar indexed-read result may hide excessive work when the payload becomes a tree of particle buckets. Measure full query-by-cell workloads; compare cell-major processing if repeated directory copying dominates in the source, but require a controlled measurement before attributing costs (L024).

Extrinsics must reflect the intended hardware primitive set. A host library function is not an acceptable single interaction just because it is exposed through the runtime. Transcendental argument reduction and approximation must remain visible in Vine unless an actual target hardware primitive has been established. Graph depth still does not model heterogeneous primitive latency or1000-core throughput by itself (L025).

Use an explicitly named bounded-domain math helper when the workload proves a bounded input range; reject unsupported finite arguments instead of silently advertising a general function. Validate reduction boundaries and nearby representable values with an independent high-precision oracle. Measure polynomial schedules rather than assuming balanced evaluation wins (L027). Hoist repeated runtime mathematical expressions before considering new primitives.

Before optimizing a software transcendental kernel further, identify repeated arguments in the calling algorithm. Runtime hoisting can substantially reduce work while adding lookup depth. Preserve reduction order when comparing, include ownership costs, and report the tradeoff explicitly rather than equating fewer function calls with proportional total savings (L028).

Test suspected dependencies with a controlled replacement. Removing a result zipper reduced SPH work but left depth unchanged (L029); source-level sequential appearance alone did not identify the critical path. Separate causal observations from hypotheses before designing the next representation.

Compare a parallel-looking map that captures aggregate data with explicit balanced recursion passing that data by value. A captured-bounds map made SPH query preparation depth grow with query count; explicit recursion reduced1820->299 with nearly unchanged work (L030). Do not assume captures preserve independence or that all closures serialize; measure identical leaf arithmetic, output topology and ownership costs.

For repeated field reads from a captured record, test copying the record into a closure-local binding first. This preserved idiomatic map use while removing the measured SPH preparation dependency; a minimal affine-map reproducer confirms the pattern (L031). Whole-value index/bucket captures did not show the same effect. Account for extra copying work and avoid a blanket ban on closures.

When per-query filtering would otherwise copy a large payload into branches that are immediately rejected, compare filtering the request tree first and only then distributing the payload. Preserve output connections for rejected requests and include compaction/cleanup costs. In the cell-major SPH experiment this reduced both work and depth (L032), unlike earlier compaction variants; topology and data ownership matter.

When integrating a batch API into an evaluator, select it explicitly and retain the
single-query path. Verify runtime construction and complete output consumption in
the generated driver, keep serial controls identical, and record API/representation
in provenance. Report individual budget outcomes even when the overall gate fails.
A retained performance failure does not establish a scientific dependency blocking
implementation of later stages; preserve acceptance requirements while prioritizing
end-to-end numerical coverage when directed (L034).

Expand sampled pilots to all-particle state coverage before extrapolating memory to
a full update. A correct sampled kernel may still exhaust the fixed heap when its
initialization and consumers are connected (L035). Isolate the failing stage, preserve
the failed run, and change live-state construction or reuse only with full-domain
numerical checks; do not reduce domain size. Raising the heap is allowed when recorded explicitly (L043, L044).

For large correctness dumps, lossless binary64 bit halves can avoid expensive decimal
formatting while preserving every field (L036). Validate row/stage/identity coverage,
unsigned-half bounds and finiteness, reconstruct exact values, and apply the original
numerical tolerance. Keep full dumps distinct from checksums used only for measurement.

Do not serialize independent particles with checksum completion gates to fit a
small evaluator heap. The L037 approach is superseded by the user's depth-first
correction (L043): use explicit larger heap profiles and measure normal, parallel
and depth execution separately. Preserve full numerical checks and final output
forcing; do not confuse those consumers with inter-particle scheduling barriers.
If memory still blocks independent execution, measure data-layout/access alternatives
and report the limit rather than silently introducing sequential dependencies.

Validate downstream sensitivity before accepting a reassociated reduction (L038).
SPH density differences within its local tolerance can fail pressure after EOS.
Use saved states and a separate original-order replay to isolate the cause while
preserving the original integrated oracle. Restore necessary ordering at runtime;
fixture-provided order is diagnostic evidence only.

Do not treat debug::error as a release-mode exception or process failure (L039).
Inspect the pinned semantics, return explicitly from invalid application paths,
and verify observable diagnostics plus absence of side effects. Evaluators must
check complete outputs independently of the process exit status. Record missing
runtime exit/error propagation capabilities instead of inventing failure extrinsics.

Successful worker execution does not fill in a timed-out depth result (L040).
Record each mode independently and preserve missing measurements as failures.
When benchmark jobs overlap, isolate a repeat before attributing a timeout to a
source change; retain the same input and deadline and preserve the failed run.

When the requested deliverable is workload readiness rather than full-scale timing,
state the distinction explicitly (L041). Verify semantics and configurable dimensions
with manageable cases, and audit integer widths, capacity and resource growth for
the intended larger parameters. Preserve failed measurements as failures; do not
require unrequested expensive runs or infer measured scores from small cases.


For parameter-only scale-up, audit aggregate widths independently of index widths:
N particle IDs fitting in32 bits does not imply N*K interactions fit. Widen operands
before multiplication, including guards and output formatting. Provide allocation-free
configuration inspection with storage lower bounds; label it separately from actual
large-run feasibility. Audit reference output narrowing rather than silently adopting
it as intended mathematical behavior (L042).
