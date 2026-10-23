# SPH-EXA plan history

Verbatim copy of plan.md as of 2026-10-14, before the suite-wide reorientation.
Its gates, budgets and next actions are superseded by plan.md and AGENTS.md; kept as
history and evidence pointers.

## Former plan.md

## Status

- Done: pinned unchanged upstream, source manifest, serial C++ build and smoke run.
- Done: persistent workflow and mandatory documentation learning loop.
- Done: local status runner, bootstrap gate, table comparator, stats parser, and runtime diagnostic probe.
- Done: high-precision initialization/density pilot on sides 12 and 16, fixed correctness/depth/work/heap budgets. Evidence: reports/runs/20260915T161128Z-45040/pilot/.
- Done: bounded optional worker dispatch and independent re-verification tests; real CLI startup/tool-sandbox limitation documented in L013.
- Batch grid is integrated into the evaluator (L034): 72 membership checks pass, bootstrap/pilot pass, and all measured budgets except the depth ratio pass. Neighbor acceptance remains failed; full physics is the implementation priority.

## Active depth-first correction (2026-10-06)

User rejects artificial checksum scheduling barriers and authorizes larger heaps.
This supersedes stabilization-source acquisition as the immediate task. Candidate
and baseline: reports/physics/depth-first-20261006/. Remove inter-particle and
full-state checksum gates, preserving arithmetic/order/capacity checks. Validate
all56 stage snapshots (sides12/16,3 updates), native outputs and matched whole-update
measurements with explicit8GiB resources. Default historical2GiB policy/oracle stays
unchanged; new resource profiles are reported separately. Compare normal and depth
memory; do not infer hardware timing. No promotion or acceptance yet. Next: inspect
normal12 result, measure depth, then full fixed validation; preserve any failure.

## Toolchain transition

work/vine-lookup is the isolated lookup-based checkout with tested scalar sine/pi and large bounded lookup additions. Main Vine and stashes remain untouched. Support changes are staged; signed commits were blocked by unavailable GPG agent access. Preserve patches and exact source/binary hashes until checkpoint signing is available.

## Current scale-readiness cycle (2026-10-05)

Implemented N64 global neighbor counts/capacity products and allocation-free native
--describe. Audit: SCALE_READINESS.md; checks: tools/readiness_gate.py. Repeating
full fixed side12/16 three-update validation under unchanged limits in
reports/physics/scale-readiness-20261005/full-stages. Configuration boundaries and all56 fixed stage snapshots pass; heap unchanged
at both sizes. All three native output cases and36 unit tests pass. Independent
review.json verifies source/toolchain/oracle/policy and coverage. Source/evidence
checkpoint: reports/checkpoint-20261005-scale-readiness.tar.gz.
Next: obtain actual stabilization source and implement a separate verified adaptation.
Full-scale execution remains deferred. Invalid-state propagation and longer trajectories
remain readiness gaps. Prior evidence/failed runs below remain authoritative in scope.

## Earlier next-action record

Batch evaluator integration is verified (L034). Prioritize the full computational
port per user direction on 2026-09-26. Do not
spend the next cycle on another neighbor performance experiment. Preserve the
neighbor heuristic failure and all correctness/resource policies; neither later
implementation nor batch-driver integration advances a failed acceptance milestone.

Current implementation: separate stages.cpp reference instrumentation is verified
against unchanged upstream ordinary dumps/constants for three updates at sides12/16.
The full computational update is implemented in the isolated candidate
reports/physics/evolution/sph/: runtime initialization, grid neighbors, density/rest,
EOS, IAD, momentum/energy, timestep, positions and total energy. bounded_update/ passes
one complete side12 update with every stage/field/scalar/membership checked. All
full-port and performance acceptance flags remain false.

Three-update results are now preserved: side12 completes but fails19 pressures at
second-update EOS; side16 exceeds2GiB. Original-order C++ density replay on saved
Vine geometry exactly matches all original densities and removes pressure failures
(L038). The original oracle and tolerances are unchanged.

Both isolated ordered-evolution cases now pass all3 updates, every field/scalar,
and exact neighbor order at sides12/16 (L038). Sources are integrated as ordered.vi
and evolution.vi; physics density now uses original order. The prepare-entry guard
is rejected as a memory improvement: same side12 heap, extra work.

Integrated physics validation now passes both fixed domains at3 updates in
reports/physics/integration/validated-20260930. Shared bootstrap/pilot and all72
neighbor memberships pass; the unchanged neighbor depth heuristic still fails.
A native driver exists at app/square_patch.vi. Initial output validation passes;
the repaired argument parser passes five rejection probes and the positive side12
rerun, but its side16/3-update rerun times out at600s (L039–L040).

All four workers2 size/update combinations pass. Three depth cases pass; side16/3
hits600s, so the scaling matrix is failed. Native exit-status and general physics
error propagation, broader workloads and hardware acceptance remain unresolved.

## Current completion target (user clarification 2026-10-04)

Deliver SPEC-like workload readiness, not a completed full-scale benchmark campaign.
The user explicitly does not want full-scale runs now. Particle/step counts should
be configurable so the same validated implementation can later attempt the intended
workload without an algorithm rewrite. Do not launch the full SPEC test/train/ref
sizes merely to satisfy the previous plan. Full-scale feasibility/timing and official
SPEC score reproduction remain unmeasured, separately reported claims.

Immediate next action: audit the remaining semantic differences between the pinned
upstream reference and the intended SPEC-like workload (initial conditions, units,
stabilization, neighbor/capacity behavior, step semantics and sampled output). Use
actual source evidence where available; public descriptions alone do not establish
exact equivalence. Preserve the upstream oracle and create any changed-workload
reference as a separate reproducible adaptation.

Audit scale-dependent implementation limits without running large simulations:
integer widths for particle IDs/counts and total neighbor counts, capacity handling,
array/tree construction, memory growth and error propagation. In particular, current
global neighbor totals use N32; products of millions of particles and hundreds of
neighbors may exceed that range. Establish the required bounds and test counter
arithmetic independently before claiming parameter-only scale-up readiness.

Validate matching semantics on manageable particle counts with enough steps to
exercise stabilization and subsequent evolution. Preserve existing fixed-case
coverage, tolerances, resource policies and failed reports; any additional oracle or
validation profile must be explicit. Finish driver checks with isolated runs where
needed. Optimize only demonstrated barriers to readiness or impractical work/memory;
a missing large depth measurement or arbitrary depth heuristic is not, by itself,
a reason to delay this functional target. Do not mark those performance gates passed.

Completion evidence should state: implemented semantics, small-case validation,
supported parameter ranges, reviewed resource scaling, and the command to select a
larger workload. It must separately list full-scale execution and hardware timing as
not performed. Existing performance failures remain visible rather than being waived.

Software sine and runtime sine reuse are complete for the SPH domain (L027–L028), with integrated pilot passes. General all-range sine and actual target primitive latency/throughput remain unimplemented/unvalidated. The361.2 neighbor threshold is an assistant-chosen heuristic rather than a hardware requirement (L026); review policy rationale separately, without quietly changing gates to accept a candidate.

## Milestones

1. Evaluator: fixed valid cases, numerical policy, structured results, resource limits, depth driver that forces all outputs, separate parallel timing.
2. Initialization and density pilot: full dependency argument, C++ comparisons, multiple input sizes, measured alternative formulations, learned guidance updates.
3. Octree construction and neighbor search: brute-force small-case oracle plus upstream sets/order comparison; clustered and boundary cases.
4. Density, equation of state, IAD, momentum/energy, timestep selection, position update, total energy. Implement prerequisites needed for the density pilot before claiming the pilot complete.
5. Integrated update and multiple updates: intermediate states, error growth, depth/work/memory scaling.
6. Reconstruct documented SPEC-like driver/output behavior, keeping unresolved differences explicit.
7. SPEC-like workload readiness: parameterized execution, matching semantics, manageable-case validation and scale-limit review. Full-scale execution and target-hardware measurements are deferred by the user (2026-10-04), not claimed as passed.
8. Enable unattended milestone execution only after the pilot demonstrates reliable evaluator acceptance and checkpoint recovery.

For each milestone record candidate, evidence paths, numerical results, depth/work/memory, dependency rationale, changed Markdown files (or no new lessons), and next action. Reopen affected completed components when new evidence invalidates assumptions.

## Continuation status (2026-09-20)

Pilot revalidated with separate two-worker runs: reports/runs/20260920T180935Z-79500/pilot/result.json. Neighbor membership passes but depth/work gates fail. A real nested CLI worker cannot start its tool sandbox; no CLI implementation worker is active. Continue directly in the existing Codex task via the installed30-minute heartbeat; run acceptance without --port. Do not keep retrying nested workers or relax sandboxing. Next: isolate bounds/partition/copying costs and compare simpler eager-predicate representations. Preserve the failure and unchanged budgets.

## Latest completed experiment cycle

Cached partition summaries, empty-bounds identities and eager pure predicates are retained in neighbors.vi. Fixed membership cases and five additional degenerate/random cases pass; the pilot regression and17 infrastructure/oracle tests pass. Neighbor depth/work gates still fail; no milestone was advanced. Reproduction and alternatives: reports/neighbors/followup-1/, reports/neighbors/eager-cached-validation/, reports/neighbors/eager-cached-extra/, reports/pilot/neighbor-followup-regression/. Source checkpoint: reports/checkpoint-20260920-neighbor-followup.tar.gz. Continue from L014–L015 and the Next action above; do not reset to the original hierarchy.

## Scheduled experiment cycle (2026-09-21)

Completed compacted and uncompacted batch routing, matched-library controls, exact membership checks, extra edge/random checks, separate two-worker checks and query-only diagnostics. No production/shared code or acceptance inputs changed, so no pilot rerun was needed. Toolchain pin and unchanged production source were verified. Evidence: reports/neighbors/batch-routing/{result,controls,extra-checks,query-only,budget-review}.json and the uncompacted sibling. No milestone advanced; follow L016 and Next action.

## Scheduled cycle: grouped compaction rejected

Four occupancy/compaction variants were implemented and measured on full64/256 membership and depth workloads. Construction and bounds diagnostics were added. All variants are rejected; no production/shared files changed and no gate was re-registered. Reproduction: reports/neighbors/tiled-routing/run.py and construction.py; conclusions in L017. Do not spend another cycle on the same compaction sweep.


## Scheduled cycle: spatial builders and root bit count

Radix, radix buckets and independent coarse buckets were implemented, measured and rejected (L018). A reusable five-step N32.leading_zeros change was retained in isolated Vine with1118 independent vectors and affected N64/Nat/F64 regressions. Actual root batches match the prototype:1118 words D377->216, W286129->56217, heap253488->579584 bytes. The dependency pin is validated by reports/runs/20260921T190441Z-95573: bootstrap/pilot pass, all eight neighbor membership cases pass, unchanged neighbor depth/work failures remain. Root patch and previous pin are preserved; signed commits remain pending. Proceed with Next action, not another pin-validation cycle.


## Scheduled cycle: bounds layouts and partition summaries

Completed exact bounds/identity and matched depth diagnostics at64/256; both separate-coordinate representations and deferred summaries lose depth. Evidence: reports/neighbors/bounds-layout/, L019. Production, dependency and gates remain unchanged; no integrated rerun needed. Continue from Next action.


## Scheduled cycle: point-branch compaction

Completed exact diagnostic comparisons and full eight-case membership/depth/worker evaluations of preserved branches and cached-count joins. Both lose full-pipeline performance despite the preserved-branch component depth gain. Evidence: reports/neighbors/point-branches/, L020. Production and dependency unchanged; no pilot rerun needed. Checkpoint: reports/checkpoint-20260921-point-branches.tar.gz.


## Scheduled cycle: bottom-up construction with batching

Leaf and bucket variants pass all eight memberships and worker checks but fail depth/work budgets. Spatially ordered-input diagnostic isolates locality and explicitly excludes host sorting; it is not acceptance evidence. Reports: reports/neighbors/bottom-up-batch/, L021. Production/root/gates unchanged; checkpoint reports/checkpoint-20260921-bottom-up-batch.tar.gz.


## Scheduled cycle: independent query groups

Groups8/32 pass exact membership and worker checks, with only1.6–1.9% depth improvement and continued depth failure. Matched full-batch/single-query controls pass. Reports: reports/neighbors/query-groups/, L022. No shared code changed. Checkpoint: reports/checkpoint-20260921-query-groups.tar.gz.


## Scheduled cycle: runtime indexed reads

Completed30 scalar correctness cases, depth/work/heap measurements and representative separate two-worker runs. Shared-reference reads trade lower work/memory for greater batch depth. Construction differences are explicitly recorded in L023; no source pin or production change. Evidence: reports/vine/dynamic-reads/. Checkpoint: reports/checkpoint-20260922-dynamic-reads.tar.gz.


## Scheduled cycle: direct spatial-cell lookup

Runtime8/64-cell grids pass all eight memberships and worker checks, but fail depth/work budgets despite substantially lower depth. Evidence: reports/neighbors/direct-grid/, L024. No root/production/policy changes; checkpoint reports/checkpoint-20260922-direct-grid.tar.gz.


## Sine hardware-model correction completed

Evidence: reports/vine/sine-vine/, reports/runs/20260922T124634Z-2028. Bootstrap and pilot pass; neighbor correctness passes while the existing heuristic performance gate fails. Root source and binary were repinned after removing host sine. No claim of full port or hardware completion.


## Runtime sine reuse completed

Production initialization now computes40 distinct runtime sine values per particle, with the original400-term reduction topology. Ordinary runner reports/runs/20260923T154358Z-6786 passes bootstrap/pilot; unchanged neighbor correctness passes and heuristic performance gate fails.32-particle initialization D528/W2249937/heap19319280. Evidence: reports/pilot/sine-hoist/, L028. No root/toolchain or policy changes.


## Cell-major experiment completed

Both grid sizes and independent-result-connection variants pass all eight memberships and worker checks, but fail to beat the retained full pipeline.64-cell depth2029 is unchanged when replacing the zipper; useful work reduction does not resolve the depth issue. Evidence: reports/neighbors/cell-major/, L029. Production/root/policies unchanged.


## Preparation dependency isolated

Diagnostics identify a captured-bounds map; explicit recursion reduces preparation depth1820->299 and full64-cell depth2029->794 at256 queries. All exact checks/workers pass. Evidence: reports/neighbors/cell-diagnostics/, reports/neighbors/explicit-prepare/, L030. No production/root/policy change; preserve the alternative and continue the targeted capture audit.


## Capture audit completed

Whole-value capture controls show no depth penalty. Local-copy record access matches explicit recursion, and a small affine-map reproducer confirms the narrower repeated-field-read effect. Full experimental memberships/workers pass; production/root/policies unchanged. Evidence: reports/neighbors/capture-audit/, L031.


## Per-cell request filtering completed

Filtered candidate passes all eight memberships and separate workers, improving256-point work13.64M->7.96M and depth794->775. Work-growth/ratio budgets pass; heuristic depth still fails. Reports: reports/neighbors/cell-filter/, L032. Production/root/policies unchanged.


## Grid correctness expansion and cleanup completed

16 extra fixtures pass through both APIs; cleaned code reproduces all fixed correctness, worker and performance results. Evidence: reports/neighbors/grid-clean/, L033. An explicit evaluator-integration review is prepared. Production/root/evaluator/policies unchanged.


## Batch evaluator integration verified (2026-09-26)

Separate grid.vi exposes both APIs; --candidate grid selects one runtime build and
find_batch for measurement. Legacy tree/single driver is preserved byte-for-byte.
The ordinary runner reports/runs/20260926T152748Z-33131 passes bootstrap and pilot;
all 72 memberships (24 cases across tree single, grid single, grid batch) pass, as do
separate two-worker checks. At64/256, D634/775, W1695850/7957961 and heap8851312/38552928
reproduce L033 exactly. Depth775 exceeds the unchanged361.2 heuristic; other
reported budgets pass. No neighbor or full-port milestone is accepted.

24 tests pass. Reproduction, reviewed invariants and machine-readable results:
reports/neighbors/batch-integration-20260926/. Source checkpoint:
reports/checkpoint-20260926-batch-integration.tar.gz. Next action is the full-stage
oracle and runtime density/EOS integration described above, not further grid tuning.
Risks: neighbor ordering/capacity, multistep floating-point error, fixed-grid scaling,
SPEC-specific behavior and actual hardware acceptance remain unresolved.
