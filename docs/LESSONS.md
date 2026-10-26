# Porting lessons

Use entries with: status (source-confirmed / measured / hypothesis / superseded), context and revisions, observation, evidence or commands, correctness effects, depth/work/memory effects, decision and limits, affected components, and guidance updated. Include raw-result paths for measured claims. Keep durable evidence outside ignored work/ when accepting a milestone.

## L001: Depth instrumentation changes the execution mode

Status: source-confirmed; no performance experiment yet.
Evidence: /Users/nils/repos/vine/cli/src/common.rs, ivm/src/host/runner.rs, and ivm/src/runtime.rs inspected in this session.
Observation: --depth aliases breadth_first; Runner::normalize selects breadth-first before workers; depth counts breadth-first interaction rounds.
Decision: separate depth measurement from parallel timing. Do not interpret depth as elapsed hardware cycles. Applies to every port.
Guidance: PORTING.md measurement contract.

## L002: References and parallelism must be evaluated together

Status: hypothesis requiring measurements.
Observation: avoiding copies alone does not establish low dependency depth. Successive shared-reference access can impose ordering; broad duplication can raise work/memory.
Decision: compare alternatives on representative gather and neighbor-query cases. Do not universally prescribe references or duplication.
Affected components: SPH-EXA data layout, neighbor search, all particle kernels.
Guidance: AGENTS.md acceptance criteria; PORTING.md design hypotheses.

## L003: Read timestep semantics from executable source

Status: source-confirmed for upstream 7604c8241ee3f0e0fa2cf1c0b3c7821c122e0dd6.
Evidence: upstream/sph-exa/src/sqpatch.cpp uses iteration <= maxStep and executes physics within iteration zero.
Correction: -s 0 executes a full update in this upstream revision. It is not initialization-only. Exact SPEC behavior remains unverified.
Guidance: benchmarks/sph-exa/COMPATIBILITY.md; validation must state executed update counts.

## L004: Reconcile units before adapting constants

Status: source-confirmed for the pinned upstream.
Evidence: upstream/sph-exa/src/SqPatch.hpp explicitly converts fields to CGS units.
Observation: 3500 cm/s matches the documented 35 m/s; changing the numeric literal alone would change physics. Other constant and resolution differences remain unresolved.
Guidance: benchmarks/sph-exa/COMPATIBILITY.md.

## L005: Use the upstream release configuration for the initial oracle

Status: observed build failure and successful smoke run in the previous setup cycle.
Evidence: upstream Makefile defines -DNDEBUG; omitting it exposes undeclared names in a debug diagnostic in Domain.hpp. The root Makefile now matches that release define. make sph-exa-smoke ran 1728 particles for iteration labels 0 and 1.
Limits: this is a smoke run, not numerical equivalence validation. Debug diagnostics need a separate documented fix if a debug oracle is required. Raw smoke outputs are currently in work/smoke and are not durable validation fixtures.

## L006: Completion and worker assertions are different states

Status: tested in tests/test_evaluation.py and tests/test_runner.py.
Observation: a process can exit successfully without a valid fresh acceptance report; stale or incomplete milestones must not count as completion.
Decision: require all named milestones, successful gate exit, fresh report, exact milestone identity, and Boolean passed=true. Missing gates produce waiting, not complete. Worker claims do not override the gate, and changes to acceptance inputs stop the run.
Guidance: docs/RUNNER.md and the runner implementation. These checks establish orchestration integrity; scientific acceptance still depends on the quality of registered gates.

## L007: Check the compiled environment and explicit imports

Status: measured infrastructure probe; reports/runs/20260914T031302Z-28405/bootstrap/.
Observation: Array was not available unqualified in the probe. Importing #root::data::Array made the test compile. The existing release binary produced the expected 64 with --depth and separately with two workers.
Limits: binary hash identifies the executable, but a source revision alone does not prove an existing binary incorporates local modifications. This is no evidence of SPH performance or optimality.
Guidance: docs/RUNNER.md provenance limits; SPH evaluator must establish matching build provenance before interpreting optimization comparisons.

## L008: Superseded dirty builds are not supported dependencies

Status: user correction and source-confirmed audit, 2026-09-15.
The user stashed earlier local Vine changes. work/vine-source contains them, including facilities referenced by the partial pilot; it must not supply acceptance evidence for the new toolchain. origin/lookup at 7cf26c3e provides the preferred static lookup mechanism.
Decision: use an isolated lookup-based revision and independently tested generic library additions. Revalidate initialization and density after updating the dependency.
Guidance: docs/VINE_CHANGES.md and AGENTS.md.

## L009: Measure the numerical kernel without serial decimal formatting

Status: measured on lookup 7cf26c3e plus isolated support changes.
Evidence: reports/runs/20260915T161128Z-45040/pilot/result.json and generated drivers.
Full 30-field initialization and density outputs passed at fixed atol=1e-9, rtol=5e-12 on sides 12 and 16. Largest absolute initialization error was 4.3655745685100555e-11; density error was at most 1.11e-15. Balanced reductions reduced initialization depth from 826 to 441 for 32 particles and density depth from 1497 to 644 for 16 queries, with slightly lower work in both. These are local kernel experiments, not timestep or hardware throughput results.
Decision: retain full numerical output for correctness; force all fields with a balanced checksum and emit its two integer bit halves for depth. Decimal F64 formatting otherwise dominates the observed path. Validate that checksum independently too. Reassociation still needs multistep error checks.

## L010: Preserve computed geometry at lookup boundaries

Status: measured, same toolchain and pilot evidence as L009.
Replacing the computed periodic bounding-box extent by the algebraically expected 100 caused density differences around 1e-9. Passing the exact upstream bbox.zmax-bbox.zmin reduced these to machine precision. Turning off C++ FMA contraction alone did not resolve this discrepancy.
Decision: preserve floating-point operation order and computed geometry when lookup indices or strict geometric predicates depend on rounding. Do not widen tolerance to hide a discontinuity. Neighbor search must reproduce shifted-query arithmetic, not assume all periodic-distance formulas round identically.

## L011: Static table compilation has a stack cost

Status: measured with the 20,000-entry harmonic table and tests/programs/lookup_large.vi.
The default compiler process stack overflowed. tools/vine_exec.py uses a bounded 65,520 KiB stack via zsh before exec; the large lookup test then passed. Python setrlimit rejected this limit on this host, so the wrapper uses an argv-preserving shell invocation. Root Lookup was extended through Size32768 with explicit bounds checks; negative bounds tests fail as intended.
Decision: record compiler and runtime resource costs separately. Per-command RSS currently covers compilation plus execution. This stack workaround is not evidence of a runtime depth improvement; an upstream compiler-stack improvement remains a possible follow-up.

## L012: Spatial partitioning can cost more depth than a scan

Status: measured failed candidate, reports/neighbors/second-candidate/result.json.
The balanced midpoint spatial hierarchy passes eight membership cases including upstream sides12/16, exact radius, coincident points, z-periodicity, empty and shuffled clustered data. At64 points/queries it uses depth2120, work1,131,885; at256 it uses depth3453, work14,576,282. The trusted serial scan uses depth393/516 and work993,221/16,012,579 respectively. Candidate work grows12.88x for4x size, exceeding the fixed10x ceiling; depth also fails the required0.7 baseline ratio. Two-worker runtime at256 was138ms (process time includes compilation and was1.22s). This is a rejected candidate, not an optimization success.
Decision: measure construction, repeated bounds computation, partition/compaction and index duplication separately before choosing a more complex representation. The baseline's source-level accumulator does not imply measured linear depth: compiled dependency behavior is the authority. Fixed acceptance budgets remain unchanged. Vine logical syntax is `and`/`or`; use boolean bitwise operators only deliberately when eager parallel evaluation is desired.
Guidance: design.md and NEIGHBOR_WORKER.md. Generality and unsaturated membership only; output order/capacity and timestep checks remain pending.

## L013: Test real worker tool execution before claiming unattended work

Status: measured environment limitation, reports/worker-preflight2.stdout and .stderr.
Initial CLI startup failed on state database writes. Granted normal Codex state access enabled a model response, but its Node tool process could not start under the nested sandbox. Exit0 did not mean file access or implementation succeeded. No worker code changes occurred.
Decision: keep workspace sandboxing; stop blind CLI retries. The installed Continue SPH-EXA Vine port heartbeat resumes implementation directly in the existing task and uses the independent runner without --port. Model connectivity and actual tool execution are separate readiness checks. Acceptance remains independent of agent claims.

## L014: Cache partition summaries and separate pure predicates

Status: measured on the same pinned Vine toolchain; reports/neighbors/eager-cached-validation/result.json, plus reproducible probes under reports/neighbors/followup-1/.
Build-only consumption of all particle identities in the original hierarchy has depth1616/2835 at64/256 points, versus full build/query depth2120/3453. This probe discards final bounding metadata, so it is a lower-cost construction diagnostic, not a separable timing to subtract from full depth.
Changes: return counts/bounds alongside partitions rather than traverse both resulting trees again; keep small leaf buckets instead of additional bounding hierarchies; use infinities as the empty min/max reduction identity, removing count-dependent branches; evaluate total, pure geometric predicates with boolean bitwise operations. No spatial arithmetic reassociation or tolerance change was introduced.
Best full results at64/256: D1006/1587, W892378/11793450, heap1948912/20311232 bytes. At256 this lowers depth54.0% and work19.1% versus the original hierarchy. Heap rises from16318720 to20311232 bytes (24.5%); the depth reduction is not free. The cached-only intermediate used D1956 and heap17270976 at256; pure predicate/identity changes trade more live memory for lower depth.
All eight fixed membership cases pass, including upstream sides12/16. Depth/work acceptance still FAILS: required maximum depth361.2 versus observed1587; work growth13.22x exceeds10x. Do not label this milestone complete. Separate two-worker logs are retained; short timings are observations, not stable speedup claims.
Rejected probes: an eager parallel scan D506/W15507232 at256 with16.08x work growth; an unpartitioned bottom-up bounding tree D1146/W22481128; sampled splitting D3542/W11093894. Probe aggregate checksums match the oracle, but only the retained candidate has full membership validation. Keep the fixed budgets and evidence.
Guidance: PORTING.md and benchmark design/plan. Next investigate data routing and construction together, not another serial split heuristic.

## L015: Shared references reduced work but serialized the queries

Status: measured controlled scan comparison, reports/neighbors/followup-1/ref-scan/ versus scan-eager/.
Replacing the value tree by a shared reference in the otherwise equivalent eager scan reduces256-particle work from15507232 to9588962, but increases depth506 to6661. At64 particles depth is1797. Aggregate outputs agree with the brute-force oracle. This confirms the L002 risk for this access pattern; it is not a prohibition on references generally.
Decision: do not adopt a shared root reference for independent neighbor queries. Compare batched spatial routing or a purpose-built immutable access representation, including construction and cleanup, before proposing reusable Vine capabilities. Such alternatives are untested hypotheses. Changing a driver to permit batched queries would require a separately justified evaluator review preserving inputs, full output checks and budgets; it must not silently relax acceptance.

Follow-up validation for L014: five additional cases (64 coincident points, 96 collinear points, and three deterministic random periodic clouds) pass exact membership in reports/neighbors/eager-cached-extra/. The unchanged pilot passes again in reports/pilot/neighbor-followup-regression/result.json, including separate two-worker checks. All17 infrastructure/oracle tests pass. No full-timestep or hardware acceptance is implied.

## L016: Batched routing removes repeated index work, but compaction adds depth

Status: measured isolated experiment; reports/neighbors/batch-routing/ and batch-routing-uncompacted/. Production candidate, toolchain and acceptance gates are unchanged. Both variants pass all eight fixed full-membership cases, including unchanged upstream side12/16 fixtures; the compacted variant also passes empty-query, coincident64 and three random periodic cloud cases. Full output checks, checksum forcing, source hashes and exact commands are preserved. Separate two-worker runs pass. No milestone is accepted.

Implementation: prepare each query with its own negative-polarity result connection, then traverse the spatial index once while routing request subsets to children. Results retain their original query identities without a serial merge. This uses existing Vine facilities, not a native neighbor kernel or shared mutable root reference.

Compacted routing at64/256: depth1037/1596, work543199/4294285, heap1180720/7557088 bytes. Matched-library single-query controls reproduce depth1006/1587, work892378/11793450, heap1948912/20311232. Thus256-point work falls63.6% and heap62.8%, with slightly higher depth. Work growth7.91x now meets the unchanged10x ceiling. The depth limit361.2 still fails. budget-review.json records each original criterion explicitly; no acceptance policy was changed.

Removing request compaction gives depth998/1579 but work844335/10897175, growth12.91x: the small depth gain loses the required work scaling. Do not adopt this variant as a solution.

Query-only diagnostics prebuild the same index outside Vine solely to isolate access. At256, compacted batching has depth1229 versus single-query629; uncompacted batching558. These runs exclude required construction and are not acceptance evidence. They show that request compaction itself delays traversal; it is inaccurate to attribute the full compacted run's depth solely to construction. Do not subtract diagnostic depths from full depth.

Decision: retain compacted batching as a validated experimental API option, without replacing the failed production gate. Next investigate tiled routing (compact between fixed-size query groups, retain structure within groups), and independently reduce construction depth. A gate extension for batched input needs a separate review preserving all fixtures, output association/forcing, budgets, and the single-query correctness checks. Do not replay broad shared-root references or globally uncompacted routing without a new hypothesis.

Comparison limit: the isolated library omits unrelated pilot/table modules, so its process RSS and compile time cannot be compared directly with the full production library. Runtime interaction/depth/heap controls use the same isolated library and reproduce the prior values.

## L017: Coarse request compaction did not remove the depth bottleneck

Status: measured rejected variants, reports/neighbors/tiled-routing/{results,review}.json; exact source/drivers and hashes are preserved. No production/shared code or acceptance input changed.
An occupancy Bool reduction compacted request structure every1/2/3/4 tree levels, retaining holes between compacting levels. All four variants pass full membership at the fixed64/256 scaling cases. At256, (D,W) are (1629,7270948), (1593,8276168), (1584,8346762), (1579,10700502). Their work growth factors are9.67/10.29/9.77/13.31. Compared with compacted batching's D1596/W4294285, stride3 saves only12 rounds while nearly doubling work. Reject this tradeoff; do not promote any variant or broaden performance testing without a new hypothesis.
Vine correctly rejected implicitly dropping request trees containing negative-polarity output connections. The implementation explicitly drains trees in occupancy-false branches. Include that cleanup in work/depth; never use unsafe erasure to make logically empty but linearly typed data disappear.

Construction diagnostics in tiled-routing/construction/results.json show depth789/1286 at64/256 for the retained builder while consuming all particle identities, and bounds-only depth348/374 while consuming all six coordinates. These diagnostics have different consumers and omit final bounding-metadata consumption in the builder case. They cannot be subtracted from total depth or treated as a formal bound for a different consumer. They do show that another small routing change is unlikely to resolve the full depth target on this builder.
Decision: keep L016's compacted batch experiment as the work-efficient candidate. Next isolate scalar min/max selection, aggregate copying, and recursive partition construction; compare a bottom-up radix/bucket construction that avoids successive whole-subtree bounds/partition dependencies. Extend Vine only for a measured reusable scalar/collection gap, with standalone tests and a new pin. No budget relaxation or milestone advancement.

## L018: Spatial-key construction exposed a sequential root primitive

Status: source-confirmed and measured; reports/neighbors/radix-builder/, radix-fixed-bits/, radix-buckets/, independent-buckets/, builder-costs/ and reports/vine/clz/.
The bottom-up Morton prototype computes keys independently, merges compressed radix trees, then derives exact bounds. All eight fixed membership cases pass, but its256-point depth5366 loses to the retained compacted builder/query pipeline1596. Vine N32.leading_zeros scanned bits in a loop; substituting five fixed shift/OR rounds for highest-bit selection reduces radix depth to3056. Coalescing subtrees of at most8 particles reduces it to2809, still rejected. Key collisions retain all points, so quantization changes grouping only, not membership. Independent coarse buckets also fail to improve the overall tradeoff:8 cells give D1685/W5622354 at256 and64 cells D1954/W6349941 (both scaling cases passed full membership). Do not promote these builders.

Reusable finding: do not assume a scalar library operation has constant shallow implementation from its name. The existing leading_zeros also serves N64 and Nat division. A five-step binary search preserves zero->32 and all bit-count semantics. Independent Python bit_length vectors cover1118 boundary/random words; prototype batches reduce D238->74 for one high-bit word, D301->140 for32 mixed words, and D377->216 for1118 words. At1118, work286129->56217; live heap253488->579584 bytes. This trades higher parallel live memory for fewer dependencies and much less work. A separate highest-bit implementation passes1118 independent vectors.

The root-only leading_zeros change is now in isolated work/vine-lookup, with a standalone1118-vector Vine test and passing N64 division, Nat division/edge, F64 operations and sine regression output comparisons. Patch dependencies/vine/0003-bounded-leading-zeros.patch preserves it with snapshot updates. The executable is unchanged because it loads root sources when compiling; source hashes/pin distinguish this toolchain. Integrated revalidation completed in reports/runs/20260921T190441Z-95573: bootstrap and pilot pass; all eight neighbor memberships pass, with unchanged failing depth1587 versus limit361.2 and work growth13.22x. The dependency pin is validated; the neighbor milestone is not accepted. Actual root-function measurements in reports/vine/clz/root-after.json exactly reproduce the prototype depth/work/heap above, using the original drivers and identical outputs. Earlier measurements remain attached to the old root snapshot/pin; do not compare mixed-toolchain results as builder improvements.

## L019: Separate coordinate trees and deferred partition summaries lost depth

Status: rejected matched diagnostics under the validated CLZ pin; reports/neighbors/bounds-layout/{run,routing,exact}.py and {result,routing,exact}.json. These are component diagnostics, not neighbor acceptance or formal depth lower bounds. Every depth consumer forces six bounds, counts and particle identity checksums. Separate exact checks compare both F64 bit halves of every bound and every routed identity in order against Python expectations at64/256. Conversion, copying and cleanup are included.

Bounds layouts at64/256: existing aggregate D415/465, W17122/67426; six independent scalar reductions D493/541, W51129/203769; three coordinate-pair reductions D473/521, W35706/141690. At256 heap is512432/504608/398304 bytes respectively. Splitting fields into separate trees does not automatically expose a shallower graph: conversion and duplicated traversals can outweigh independence. Both alternatives are rejected before integration.

Fixed x-midpoint routing at64/256: cached summaries D388/430, W23863/94884; route then recompute bounds D521/600, W19625/78166. At256 deferred summaries lower work17.6% and heap992544->398096 bytes but raise depth39.5%. Keep cached summaries. These compare a fixed axis/split only and do not cover adaptive axis choice or full builder behavior.

No production source, root dependency or acceptance policy changed. No milestone advanced and no integrated rerun was warranted. Next isolate structural compaction in point partitioning: compare cached summaries with compacting join versus structure-preserving branches, including both partition and full builder/query costs. This differs from previously rejected query-request compaction variants; predict increased work from empty point branches and reject promptly if it breaches the fixed budgets.

## L020: Point-branch compaction saves full-pipeline work despite local depth cost

Status: rejected alternatives; reports/neighbors/point-branches/{run,full,counted}.py, diagnostic.json, full.json, counted.json and review.json. Matched compact controls reproduce L016 on the current pin. No production, root or policy changes.

Preserving Tree::Branch instead of join in point partitioning removes the dependency on child tree shape. Fixed-split diagnostic depth improves388->348 at64 and430->374 at256, with work94884->93154 at256. Exact bound bits and ordered particle identities match the independent prior diagnostic outputs. However, empty branches survive successive splits: full compacted-batch builder/query depth worsens1037->1056 at64 and1596->1681 at256. Work grows543199->1896299 at64 and4294285->51193939 at256; growth27.00x fails10x. Heap at256 grows7557088->123446336 bytes. Reject preserving all point branches, despite the component improvement.

A second variant compacts using cached child point counts instead of inspecting child tree constructors. Full depth1049/1626 and work566145/4448977 at64/256 also lose to the retained compact version; heap7587920 at256. Reject this variant too. Both variants pass all eight fixed full-membership cases and separate two-worker checksum runs. Timings are observations, not stable hardware speedup claims. No neighbor milestone passes depth361.2. Local dependency removal is not sufficient evidence when it changes later traversal costs.

Next hypothesis: combine a topology-preserving bottom-up bounds tree with compacted query batching. Earlier bottom-up bounds evidence used independent queries, while batching substantially reduced repeated work in a different builder. A matched combined experiment can establish whether this interaction removes recursive point partition costs without violating the work ceiling; neither earlier result establishes the combination. Include all construction, exact membership, query association and output forcing; do not use prebuilt fixture indexes for acceptance.

## L021: Bottom-up construction and batch routing still need spatial locality

Status: full runtime-built variants rejected; reports/neighbors/bottom-up-batch/{setup,full}.py, full.json and review.json. Matched compact controls reproduce D1037/1596 and W543199/4294285 at64/256. Bottom-up construction retains input topology and computes exact parent bounds from child summaries, avoiding recursive point repartitioning. The leaf-only variant gives D1093/1689 and W1229739/19096390. Coalescing at most8 points per leaf gives D840/1370 and W1094891/17362009. Although buckets lower256-point depth14.2%, work is4.04x the compact control and grows15.86x for4x input; reject under unchanged budgets. Bucket heap at256 is121112896 bytes. Both variants pass all eight fixed memberships and separate two-worker checks. No production or gate changes.

A host-Morton-ordered diagnostic using the same bottom-up bucket builder gives D835/1360 and W495573/4820119 at64/256, with full membership checks on those scaling cases. Host key computation and sorting are EXCLUDED; this is not an executable port candidate or acceptance evidence. Spatial locality recovers much of the work but barely changes depth. Do not implement a spatial sorter solely on the assumption that it solves this depth bottleneck, or subtract these depths from full runs. Exact inputs/commands and excluded-cost declaration are in ordered.py/ordered.json. The result is consistent with earlier evidence that batched request routing has substantial independent depth.

Next hypothesis: dispatch bounded-size independent query groups through copies of the retained runtime-built index. This differs from varying compaction cadence within one globally routed request tree (L017). It could bound request-routing dependence but increase index duplication and traversal. Include one runtime construction, all index-copy/cleanup costs and full result association; compare group sizes8 and32 with the full batch and single-query controls. Reject if work, heap or depth tradeoffs fail; do not weaken gates.

## L022: Independent query groups give only a small depth improvement

Status: measured isolated variants; reports/neighbors/query-groups/{setup,full}.py, full.json and review.json. One balanced annotation pass computes query subtree sizes, then groups use independent index copies; construction, annotation, copying, routing, outputs and cleanup are included. No shared reference or host preprocessing. Both8/32 groups pass all eight membership cases and separate two-worker checks. Full-batch and single-query controls reproduce prior measurements on the current pin.

At64/256: group8 D1005/1566, W549444/4601958; group32 D1026/1570, W545502/4320138. Compare full batch D1037/1596, W543199/4294285. Group32 lowers256-point depth1.63%, raises work0.60%, and lowers heap7557088->7117984 bytes. Group8 lowers depth1.88% but raises work7.16%, heap7643536 bytes. Work growth8.38x/7.92x passes10x; both still fail depth361.2 by a wide margin. Keep these as experimental options; do not promote or expand a group-size sweep as the solution. No production/root/gate changes, hence no pilot rerun.

Next architectural question: can runtime-generated spatial cells be accessed independently without traversing a broad bounds/request tree? Source inspection shows root Lookup is static (trait const table and compile-time Array), whereas Array.get uses a reference and delegates to at. Neither static table lookup nor O(log n) API documentation proves shallow independent runtime reads. Before implementing a grid, measure runtime-built dynamic indexing with matched copied-value and shared-reference consumers across64/256 elements and query counts. Include construction/copy/cleanup and verify every result. A reusable library change requires measured evidence; do not invent a native SPH kernel or use fixture-specific static particle tables.

## L023: Dynamic indexed reads expose an ownership tradeoff, not a missing primitive

Status: completed scalar diagnostic reports/vine/dynamic-reads/run.py and result.json; exact outputs validated for64/256 elements,1/8/64/256 mixed reads, and256 repeated reads (30 cases). Each value is transformed at runtime after black_box; no static Lookup contains final values. Depth uses a balanced checksum. All allocation, copy and cleanup of the chosen representation are included. Separate two-worker checksum runs pass for the three256-element/256-query mixed modes (workers2.json). No reusable library change or neighbor acceptance follows from this scalar benchmark.

At256 elements and256 mixed reads: copied value Tree D390/W831894/heap6340448; copied Array with get D579/W336276/heap2299168; shared-reference Array D910/W75416/heap168560. At64 elements and256 mixed reads: D381/395/903, W231079/118434/53414 respectively. References save work and memory but add a long dependence path at higher read counts; this supports L015 for this access pattern without prohibiting references universally. At256 elements and1 mixed read depths are359/539/539. Array inputs include list-to-array conversion while Tree inputs use balanced construction, so cross-representation totals include differing construction costs and are not isolated get latency. Repeated-index256-array-copy depth430 versus mixed579 also shows access pattern affects total depth. Do not subtract construction depths or claim a universal bound from these cases.

Decision: existing Vine can express value-owned dynamic indexed selection; no root extension is justified yet. Before designing a reusable immutable collection, measure a real spatial-cell candidate where payloads are point buckets rather than N32. Build cells in Vine, select candidate cells by query geometry and retain original exact squared-distance arithmetic. Include global bounds, cell population, indexing, duplication and cleanup. Earlier independent coarse-bucket builders still routed through bounding trees; direct cell selection is a distinct untested hypothesis. Keep policies and source fixtures unchanged.

## L024: Direct spatial-cell reads lower depth but lose work budgets

Status: implemented and rejected runtime grid candidates, reports/neighbors/direct-grid/{setup,full}.py, full.json and review.json. Grids use2 or4 cells per axis. Global bounds and fixed floating-point cut planes assign particles; each cell independently filters the labeled input. Queries compute cell ranges and select bucket payloads through value trees. Periodic z ranges are unioned before scanning each z cell once, preventing duplicate results. Original strict squared-distance/self-exclusion arithmetic is reused unchanged. All construction, cell population, query enumeration, indexing, copying and cleanup are measured.

Both grids pass all eight exact membership cases, including upstream and periodic boundaries, and separate two-worker checksum runs. Matched compacted-batch control reproduces D1596/W4294285 at256. The8-cell grid has D713/901, W1733649/26610342 at64/256; growth15.35x fails10x, work exceeds the1.5x serial ceiling, heap46670448 at256. The64-cell grid has D738/876, W6607410/86457809; growth13.08x fails, heap115117264. Depth falls43.5–45.1% versus the batch control, but still fails361.2 and neither candidate satisfies work budgets. Do not promote or broaden grid-resolution sweeps. Correctness scope is the fixed cases; no complete floating-point boundary proof or multistep integration is claimed.

The source exposes repeated value-tree selection/copy/erasure and bucket scans for every query-cell access. This is a plausible work driver, not a separately measured attribution. Next transpose the grid computation: process each cell once with candidate queries, then combine per-query outputs using a balanced association-preserving merge. This may reduce repeated directory copying without introducing bounds-tree routing chains. Include query preparation/copying, all cell construction, output merges and cleanup. Use the same grid cut planes, query membership and exact scan predicate; do not change tolerances or budgets. No root/production/policy changes in this cycle.

## L025: Host sine violated the target hardware cost model

User correction: Vine targets approximately1000 hardware cores; extrinsics must represent hardware primitives. The added vi:f64:sin calls Rust f64::sin and hides its algorithm behind one runtime interaction. This is not a valid target implementation. Prior numerical comparisons remain observations, but initialization/pilot depth and work do not establish acceptance under the clarified model. The direct call is in pilot.vi's initialization perturbation; neighboring experiments contain no sine calls, though their primitive assumptions still need auditing. Density with supplied reference neighbors is not thereby an integrated-simulation validation.

Immediate priority: replace host sine with a Vine algorithm using target-supported arithmetic/bit operations, preserve special cases and fixed tolerances, measure argument reduction and approximation explicitly, audit other extrinsics, rebuild and repin after removing the runtime registration, and revalidate affected gates. Start by deriving the actual SPH input domain; a bounded-domain helper must be named/documented as such rather than advertised as general F64.sin. Generic sine requires robust argument reduction for large finite inputs. Compare balanced polynomial evaluation with Horner under numerical/work/memory constraints; neither lower depth nor acceptable error is assumed. Do not hide this work in static fixture results or another host extrinsic. The source change is pending; documentation does not remove the existing extrinsic.

## L026: The361.2 neighbor threshold was a provisional heuristic

User requested its provenance. It is0.7 times the measured serial baseline516 at256 points, configured by the assistant rather than derived from SPEC, the chip, or a lower bound. Preserve historical gate outcomes, but do not describe this threshold as a user/hardware requirement or an independently justified blocker to all physics work. No policy was changed during the sine correction. Future acceptance-policy review must explicitly justify depth/work/memory scaling for the intended1000-core target and remain separate from candidate optimization. max(D,W/1000) is only an idealized uniform-cost lower bound; it is not a hardware performance predictor.

## L027: Bounded sine is now visible Vine computation

The host vi:f64:sin registration and generic .sin wrapper are removed. Root F64.sin_bounded supports finite |x|<=128, preserves signed zero, returns NaN for NaN/infinity, and explicitly fails for finite arguments outside its domain. It is NOT general all-range F64 sine. SPH initialization has x+0.5,y+0.5 within[0,1] and odd modes1..39, so all required arguments are within39*pi<128. The scope restriction is explicit at the API and call site, not a hidden fixture shortcut. General sine with robust large-argument reduction remains unimplemented.

Algorithm: nearest-quadrant reduction with a three-part pi/2 constant, compensated remainder, degree17 sine and degree18 cosine Taylor kernels on approximately[-pi/4,pi/4], first-order remainder-tail correction, and quadrant/sign reconstruction. Arithmetic and range checks execute in Vine, without host sine, floating remainder or a precomputed sine-result table. Coefficients are rounded reciprocal factorials; independent oracle uses110-digit Decimal, Chudnovsky pi and a long Taylor series. Source and reproducible drivers: reports/vine/sine-vine/.

Both Horner and balanced polynomial forms pass2420 oracle vectors spanning SPH side12/16 arguments, multiples of pi/2 and pi/4 with adjacent binary64 values, subnormals, domain endpoints and1024 deterministic random inputs. Maximum observed error is1 ULP, not a proof of correct rounding or a global error bound. Standalone root regression enforces a4-ULP envelope on these vectors and explicit special cases;129 is rejected. Compiled-root outputs match the chosen prototype bit-for-bit. Horner prototype depth364 versus balanced369 at256 calls, with52032 versus51012 interactions; select Horner for slightly lower depth. Actual formatted root function measures D316/347/365, W566/6460/49992 at1/32/256 calls, heap522592 at256. Separate two-worker output check passes.

Rebuilt from isolated lookup checkout offline after deleting the native registration; no main-checkout changes. Focused patch dependencies/vine/0004-software-bounded-sine.patch applies after previous support patches; reverse-apply check passes. Old pin/source/binary evidence is preserved. Compiled Ivy arithmetic audit contains no sine operation: the implementation uses floating add/sub/mul/comparison/conversion and integer operations. The driver also includes IO/formatting arithmetic. Existing f64_ops output matches the previous validated snapshot; f64_no_inline, f64_roundabout and tiny_f64 outputs pass. Signed commits still await the recorded GPG limitation.

Integrated run reports/runs/20260922T124634Z-2028: bootstrap/pilot pass with unchanged numerical tolerances. Initialization32 now D518/W4413315/heap51838960, versus historical hidden-host-sine D441/W241675/heap3626752. Serial initialization32 is D903/W4413379. Maximum initialization absolute error remains4.3655745685100555e-11; density metrics and errors unchanged. All eight neighbor memberships pass, with unchanged production D1587 and its still-failing heuristic policy. Hardware-model validation remains false: removing sine fixes this hidden algorithm, not unspecified chip latency/throughput or every existing primitive. F64 rem_euclid remains in the runtime and warrants hardware-policy review if used; the new sine does not call it.

Next useful initialization optimization: currently400 pressure terms compute800 sine calls but only40 distinct per-axis/mode arguments exist per particle. Compare a runtime-built20-by20 Cartesian product of precomputed axis terms with the current implementation, preserving arithmetic association and full outputs. Include duplication/indexing costs; do not replace runtime sine with fixture tables. Revalidate pilot if retained.

## L028: Hoisting runtime sine saves work with a small depth tradeoff

The pressure sum has400 terms but only20 distinct x-mode and20 distinct y-mode sine arguments. The candidate builds two balanced runtime mode trees, each storing (odd mode, mode*pi, sine), and selects their values when constructing the original400-term tree. Every coefficient operation and the original reduction topology/order are preserved; this is not a precomputed fixture table or a reassociation. All construction, lookup, copying and cleanup are included.

Evidence: reports/pilot/sine-hoist/{setup,run}.py, provenance.json, evaluation/result.json and decision.json. The independent pilot passes unchanged numerical and resource policies; initialization dumps at sides12/16 are byte-identical to the previous pure-Vine-sine version. Separate two-worker runs pass. At32 particles, depth518->528, interactions4413315->2249937, heap51838960->19319280, allocated146614000->42024944. Retain the49% work/63% heap reduction despite1.9% more depth; this is a documented multi-resource tradeoff, not a claim that the critical path improved or an actual1000-core speedup. Density remains unchanged.

The candidate is copied into production pilot.vi; original source is preserved as pilot-before.vi. The ordinary runner independently passed bootstrap and pilot at reports/runs/20260923T154358Z-6786, reproducing these measurements; all eight neighbor memberships pass and its existing heuristic performance failure is unchanged. Root/toolchain and acceptance policies are unchanged. Runtime hoisting does not eliminate ownership costs: selecting from the cached value trees still incurs considerable copying/traversal, explaining why20x fewer source-level sine expressions does not imply20x less total work. Do not attribute a precise fraction of work without separate measurements.

## L029: Cell-major processing recovered work but not depth

Implemented8/64-cell variants that prepare query ranges once, process each bucket against all candidate queries, and combine per-query results using a balanced zipper. Runtime grid population, range preparation, copying, all result merging and cleanup are measured. Both variants pass all eight exact memberships and separate two-worker checks. Matched compact control reproduces D1596/W4294285 at256 under the current pure-sine pin. Evidence: reports/neighbors/cell-major/{setup,full}.py, full.json, review.json.

At64/256:8 cells D776/2043, W919204/11288949;64 cells D770/2029, W2324641/15094860. The64-cell work is far below direct-grid86.46M but still above compact-batch4.29M, and depth exceeds both direct-grid876 and compact1596. Work growth6.49x passes10x for64 cells;8 cells growth12.28x fails. Reject as production. The361.2 threshold remains explicitly a heuristic, not a hardware fact.

Tested the specific hypothesis that result merging caused the depth increase: independent negative-polarity result connections replace the zipper while preserving query identity and output tree structure. Both8/64-cell variants again pass all eight memberships and separate workers. At256 the64-cell connection version reduces work15094860->13633118 but leaves depth2029 unchanged; heap41506816. Therefore the removed zipper was not the limiting depth path in this workload. Do not claim output merging was the cause. Source and results: connections_setup.py, connections.py, connections.json. No production/root/policy changes or milestone advancement; no pilot rerun warranted.

Next isolate query-range preparation and the cell-local scan/copy path before another representation change. Compare actual runtime-generated buckets with controlled query batches using the same output consumers, and prepare-only diagnostics that force every range. Include copied point payloads and vary query count independently of particle count. These diagnostics must not replace full runtime construction in acceptance or be subtracted from full depth. Stop repeating grid variants without identifying the limiting dependency.

## L030: A captured-bounds map introduced query-count-dependent depth

Diagnostics in reports/neighbors/cell-diagnostics/ force every prepared integer range and separately check exact results from a runtime-built selected bucket. Particle counts64/256 and query counts1/16/64/256 vary independently; every diagnostic passes its independent oracle. With256 input particles, range preparation depth is356/666/1820 at16/64/256 queries; single-bucket construction/scan depth is560/604/649. These differ in consumer and scope and must not be subtracted, but they identify preparation as a credible target. No static prebuilt buckets or omitted ownership costs were used in the scan diagnostic.

Controlled replacement: prepare previously used tree::map with a closure capturing Bounds. Explicit balanced recursion instead passes Bounds as a value to both children, with identical leaf arithmetic and output shape. At256 particles, preparation depth becomes271/295/299 at16/64/256 queries; at256 queries work217199->224836 and heap1351056->1418368. Exact ranges still match. This establishes a performance difference between these expressions; it is not yet a compiler-semantics proof or grounds to call every captured closure serial. Do not generalize beyond measured captures without a small controlled test.

Full pipeline evidence: reports/neighbors/explicit-prepare/{setup,full,diagnostic}.py, full.json and diagnostic/result.json. Both grid sizes pass all eight memberships and separate two-worker checks.64-cell independent-result version improves depth2029->794 at256, work13633118->13640755 (essentially unchanged), heap40113504; at64, D656/W1963400. Work growth6.95x passes10x.8 cells D651/839, W881363/11136676 still fails growth12.64x. The64-cell variant now substantially lowers depth relative to compacted bounds-tree1596 but uses3.18x its work4.29M; retain as an experimental alternative, not production or hardware acceptance. The assistant-chosen361.2 heuristic still fails. No root/production/policy change, so no pilot rerun required.

Next audit analogous captured maps in the existing single-query driver and bucket scan with matched explicit-recursion controls. Include all copying and outputs, vary query count independently and preserve input/output topology. Inspect Vine closure lowering or create a minimal reusable reproducer before recommending syntax/library/compiler changes. This is more targeted than another grid-resolution sweep.

## L031: Copy captured records locally before repeated field reads

Controlled audit: replacing captured maps with explicit recursion does NOT improve the existing single-query tree or cell-local scan. Full single-query depth remains1006/1587 at64/256 and work differs by only one interaction. Every fixed membership and separate worker check passes. Bucket diagnostics at256 particles give identical depths418/560/604/649 for1/16/64/256 queries, again only one interaction difference. Therefore L030 does not imply all closures or all captures serialize. Evidence: reports/neighbors/capture-audit/{setup,full,bucket}.py, full.json and bucket/result.json.

Narrower fix: keep the query-preparation map but bind `let local=b;` inside its closure and read fields from local. This matches explicit recursion's range-preparation depths242/271/295/299 at256 particles with1/16/64/256 queries; exact range checks pass. Full64-cell independent-output pipeline again passes all eight memberships and workers at D794/W13640758/heap40113504. This is a simpler equivalent experimental formulation, not a production promotion. Reproducible source: local_copy.py, local_full.py and local4/sph/neighbors.vi; results local-copy/result.json and local-full.json.

A small independent reproducer maps x*p.a+p.b over a balanced F64 tree with a captured two-field record. At64/256 values, direct captured field reads give D341/545; a closure-local copy gives D278/290. At256, work8374->10125 and heap94656->102720. Every output bit matches an independent arithmetic oracle. Thus the depth effect exists outside SPH, but copying costs more work. minimal.py/minimal.json preserve the reproducer. Compiler closure and field-lowering sites were located (features/fn_.rs and composite.rs), but no compiler defect or intended-semantics conclusion has been established. Do not change the compiler based on source intuition alone.

Next cell-major work target: avoid duplicating bucket payloads into query branches known not to intersect the cell. Compare a per-cell compacted request filter followed by scanning, retaining independent output connections so rejected queries are resolved immediately. Measure whether reduced payload duplication offsets compaction depth, with all full memberships and unchanged budgets. This is local cell request compaction, not the earlier recursive bounds-tree compaction cadence sweep. Production/root/policies remain unchanged this cycle.

## L032: Filter cell requests before duplicating particle buckets

The64-cell candidate now filters and compacts its request tree using existing cell-range membership before passing the particle bucket into query scans. Rejected requests have their independent output connections resolved to Empty immediately; no unsafe erasure or missing output. Construction, range preparation, filtering, copying, cleanup and output forcing are all included. Source/reproduction: reports/neighbors/cell-filter/{setup,full}.py; full.json/review.json. Matched control reproduces L031.

At64/256, filtered D634/775, W1695850/7957961, heap8851312/38552928. Versus unfiltered D656/794, W1963403/13640758, this improves256-point depth2.4% and work41.7%, with slightly less heap. Work growth4.69x passes the unchanged10x ceiling; work ratio versus serial also passes. All eight fixed exact membership cases and separate two-worker runs pass. Compared with current production single-query D1587/W11793450, both depth and work improve, though heap rises from20311232 to38552928. Compared with experimental compact batching D1596/W4294285, the grid is shallower but uses more work. Do not claim1000-core speedup from these counters. The assistant's361.2 depth heuristic still fails.

Keep this as the preferred grid experiment and preserve the alternative work-efficient batch tree. Before promoting, expand correctness to degenerate axes/coincident points, cell-cut/radius ULP boundaries, empty/repeated/reordered queries, and deterministic3D periodic clouds. Then review a batch API/gate integration separately, preserving fixtures, single-query semantics, serial controls and all cost accounting. The current registered gate calls single-query find through a map, so simply copying this batch experiment into production would not test the same algorithm. No production/root/policy changes this cycle; no pilot rerun warranted.

## L033: Filtered-grid edge validation and cleaned candidate

Added16 independent extra cases: empty queries/both empty,64 coincident points, three degenerate coordinate axes, quarter-cell cuts and strict-radius adjacent binary64 values, periodic-cell union boundaries, and eight deterministic3D periodic clouds with repeated/reordered/external queries. Both single-query and batch APIs pass all16 cases (32 checks) against the unchanged brute-force arithmetic and duplicate/identity validation. Fixtures and exact commands: reports/neighbors/cell-filter/extra.py and extra/.

Cleaned the candidate in reports/neighbors/grid-clean/clean/sph/neighbors.vi: removed unused bounds-tree enum and obsolete zipper/query dispatch, named output-connection helpers explicitly, formatted code and documented fixed-grid scope. The cleaned code passes the eight fixed batch membership cases, separate workers and all32 extra checks. Depth/work/heap/allocated values at64/256 exactly reproduce the previous filtered candidate:256 D775/W7957961/heap38552928. This is broader correctness evidence, not proof across all finite floating-point inputs or a full workload. Fixed64 cells do not establish good asymptotic behavior for increasing or clustered data.

Prepared evaluator-review.md beside the cleaned source: integration must explicitly evaluate build+find_batch while retaining single-query correctness, all fixed/extra fixtures, the unchanged serial baseline, full output forcing and all existing policies. The current driver maps find and cannot stand in for this batch algorithm. No evaluator, production module, root or policy changed in this cycle; no pilot rerun warranted. Next implement the separately named batch candidate path with coverage tests and independent runner verification. Do not represent that integration as passing the still-failing heuristic or hardware acceptance.

## L034: Explicit batch integration and full-port sequencing

Status: integrated and independently evaluated; results and review are recorded in
reports/neighbors/batch-integration-20260926/. The workspace contained partial grid
integration (grid.vi, module export, candidate selection, promoted extra fixtures and
workflow selection) without driver tests or a validation checkpoint. Preserve and
finish that work rather than overwrite it. The cleaned grid matches the L033 source.

The reviewed driver must call build(points) once at runtime followed by
find_batch(index,queries); mapping single-query find is a different measurement.
Coverage tests check API selection, repeated query identities, full output forcing,
invalid modes and unchanged serial source. Promoted extra fixtures are checked
against both the preserved L033 fixtures and the independent oracle. All 24 tests
pass. No spatial algorithm, arithmetic, numerical tolerance or resource policy was
changed; reports now preserve all four depth/work policy outcomes instead of hiding
later outcomes behind the first failure. Full pin/local source hashes are saved.

User direction on 2026-09-26 makes complete physics and timestep coverage the next
priority after integration. L026 already established that the depth ratio is an
assistant-chosen heuristic, not a physics dependency. Retain its failure and all
acceptance requirements while implementing later stages; do not resume another
neighbor variant sweep just because the ordinary runner stops at that gate.

Source audit for the next stage: sqpatch.cpp calls the serial distribute path to
recompute bounds each iteration, initializes rest density only on iteration zero,
and EOS resets u=1 and c=3500 on every update. Positions consume old dt/du/positions
before replacing them. These are source-confirmed semantics, not newly validated
Vine physics. Preserve these operations in a separate stage-snapshot oracle. Guidance
updated in PORTING.md, benchmark design/compatibility, and the active plan. No new
performance optimization lesson is claimed for merely integrating the L033 algorithm.

L034 validation: ordinary runner reports/runs/20260926T152748Z-33131 passes bootstrap
and pilot with unchanged tolerances (initialization max absolute error4.3655745685100555e-11,
density at most1.1102230246251565e-15). All72 membership checks pass:24 cases through
legacy tree/single and both grid APIs. At64/256, D634/775, W1695850/7957961,
heap8851312/38552928 and allocated34977504/167548960 exactly reproduce L033.
Separate two-worker checks pass. Full-library process timing/RSS include compilation
and are not comparable to the isolated grid library as runtime speedups.
Depth775 still fails361.2; work ratio, work growth and depth growth pass. No milestone
advanced. review.py verifies unchanged legacy driver/module hashes and policy hashes
against preserved pre-integration source and prior runner provenance. The first
review attempt assumed a policy file existed in the partial source backup; corrected
to the actual prior-run provenance hash, then all review assertions passed. This was
an evidence-path correction, not a candidate or acceptance change.

## L035: Full-state coverage exposes resource limits hidden by sampled pilots

Status: initial full-state memory investigation complete; evidence under
reports/physics/first-stages/. Separate stages.cpp instrumentation calls unchanged
upstream functions and matches original constants/dumps byte-for-byte on sides12/16
for three complete updates. It records all30 particle fields after every stage,
ordered neighbor IDs and scalar time/energy/bounds. Observed maximum512 neighbors is
below650, but does not establish saturation behavior generally.

The first connected Vine path initializes all particles, builds the grid, gathers
runtime neighbor data, computes density/rest density/EOS and emits all fields. All
side12 particles pass the existing1e-9/5e-12 policy. Full-side16 initialization alone
and full initial neighbor membership both hit the unchanged2GiB runtime heap limit;
the failure is not just a neighbor-query issue. The sampled pilot remains valid in
its scope but did not establish this full-domain memory behavior. No physics milestone
is accepted. Preserve the initial failed evaluator/probes.

Measured alternative: initial pressure is independent of z, and runtime xy-plane
reuse reduces live initialization work/memory while preserving all fields. The
alternative computes the full xy plane using the existing pure-Vine sine/400-term
reduction, reuses values through measured reference accesses, and reconstructs z/z_m1
with the original arithmetic. It is not a static fixture table or a smaller domain.
Reference access may add sequential depth; numerical and full cost checks are required.

Source clarification: BBox::compute preserves axes marked periodic. Square patch
recomputes nonperiodic x/y bounds each update, while keeping the initialized z bounds.
Document this distinction when reconstructing the loop. General capacity handling,
multistep Vine evolution and hardware performance remain pending.

L035 measured ownership results: runtime xy-plane reuse passes all30 initialization
fields on both complete domains. Normal-run heap is13,384,976 bytes at1728 particles
and31,244,352 at4096; the original full initializer failed4096 under2GiB. The original
side12 normal heap was929,891,552. All initial memberships now pass at both sizes
(membership-cached/result.json). With full1728 inputs and1/8/32 forced EOS outputs,
reuse changes D2603/16178/69625 to14761/28336/81749, W137952831/140665010/152112146 to
27444046/30156225/41603361, and heap~1.047GB to~86.6MB. This is a memory/work tradeoff
with worse depth, not a target performance acceptance. Full connected regression in cached-evaluation/ still failed side16 density
under2GiB. Bounded dispatch subsequently passes one complete update on both sizes
(L037–L038); three-update pressure/memory failures remain. Do not substitute sampled
output timing for all-particle correctness.

A bounded actual-payload gather comparison (copy-gather/) passes full fields for its
1/8 query diagnostics, but copied gathers at8 queries use W1405749324/heap2006551856
versus referenced W30156225/heap86622432, despite D13755 versus28336. Reject copied
full trees as the full-workload representation; preserve references as the explicitly
serialized functional baseline. Do not repeat the sweep while completing physics.

## L036: Lossless state transport for full-stage validation

Status: full-state transport validated by one complete update on both fixed sides
and the completed side12 three-update run, under reports/physics/evolution/. Decimal F64 formatting has high cost at all-particle
coverage (as anticipated in L009). Emit both32-bit halves of every field and scalar,
decode exact IEEE binary64, then apply the unchanged original numerical comparator.
This preserves complete field/identity/stage checks; it is not checksum-only validation
or a relaxed tolerance. Tests cover signed zeros, subnormals, maximum finite values,
malformed halves, wrong field counts and nonfinite rejection. Original C++ snapshots
remain unchanged. Runtime/depth still require their own forcing consumers and timings;
transport savings are evaluator overhead savings, not faster SPH physics.

## L037: Historical memory workaround (superseded by L043)

Status: measured full-update candidate; reports/physics/evolution/. The first complete
update implementation and a variant materializing only stage results both exhausted
2GiB on side12. A side16 density-only run also exhausted2GiB with lossless bit output,
so decimal transport was not the cause of that heap failure. Preserved first_update/,
materialized_update_fixed/, and first-stages/bits-density/ reports identify the failures.

The retained candidate guards dispatch of the right query subtree on a finite checksum
of every completed left result. IAD/momentum also check full input state before
starting their gathers. This bounds pending query work while preserving every particle,
neighbor, field and arithmetic operation; it deliberately introduces sequential
completion dependencies. A materialized State argument alone did not prevent other
known inputs (neighbor rows) from expanding pending work. This is an observation on
this representation, not a universal compiler scheduling claim.

bounded_update/ passes every field, scalar and membership after all nine stages of
one complete side12 update, at the unchanged1e-9/5e-12 tolerances and2GiB heap. Including
full bit dumps, W3940224951, heap505789456, allocated90937840448 bytes, runtime73651ms.
These are correctness-driver costs, not kernel depth/timing evidence. Three-update
checks subsequently found pressure/memory failures (L038); separate measurement
runs and full acceptance remain pending. Source, commands and failed alternatives remain in the same report tree.

## L038: Density tolerance alone does not establish pressure compatibility

The preserved three_updates_12 run completed all three updates (W11847826661,
heap839764368 bytes, runtime249298ms including full dumps), but the original evaluator
fails19 pressures at i1-eos. Side16 three updates exhausted2GiB. This is not a loop
hang: the complete side12 output is available. No acceptance flags advance.

Diagnostic scripts in reports/physics/evolution/multistep-diagnosis isolate the first
failure. Replacing explicit power7 with host pow for diagnosis still fails the same19
pressures; original density inputs pass either expression (power-schedule maximum
error1.96451e-10). Replaying unchanged C++ density with original ordered neighbors
on all saved Vine geometries reproduces original densities exactly at all3 updates.
Using these replayed densities removes pressure failures (maximum2.11003e-10). This
supports restoring upstream density summation order; it is not a replacement oracle
or integrated Vine acceptance. Changes of a few ulps in ro/ro_0 are amplified by EOS.

Next candidate must compute ordering at runtime from full geometry, preserve the
original128-particle octree bucket rule and periodic root-cell traversal, then use
an ordered density fold. Necessary density depth becomes O(K), with O(NK) arithmetic;
ordered neighbor construction/gather/copy/cleanup remain separately measurable.
All fields remain forced through full-state bit dumps. Balanced IAD/momentum remain
subject to integrated multistep validation. Re-evaluate the formerly passing density
pilot's use in the full pipeline; standalone pilot coverage remains valid in scope.

L038 memory control: evolution/bounded_update_16 passes all stages/fields/scalars
and memberships for one full side16 update, W12488159091, heap1943192528 bytes,
runtime247595ms including full dumps. Thus the preserved three-update OOM requires
additional integration pressure beyond the passing single-update control; it does
not identify a single failing physical equation. Runtime ordering candidate source
is isolated in ordered-evolution/sph, with exact ordered-ID comparisons added to
its evaluator. Initial compile errors (boolean precedence and explicit reference
arguments) are preserved in ordered_12; corrected candidate is ordered_12_fixed.

L038 runtime confirmation: ordered-evolution/ordered_12_fixed passes all28 snapshots
(init plus9 stages across3 updates), all30 particle fields,10scalars, and exact
ordered neighbor lists for the complete1728-particle domain. Maximum absolute field
error2.1100277081131935e-10; tolerances unchanged. D not measured; correctness-driver
W8529715517, heap553140400 bytes, allocated200863779552 bytes, runtime179029ms.
This validates runtime original ordering plus ordered density for side12, including
balanced IAD/momentum on this workload. Side16 and kernel measurements remain pending;
no full milestone is accepted. ordered_12 preserves the initial compiler failure.

The ordered query implementation visits root z layers -1,0,1,2 (with periodic
coordinate shifts) in order, then y/x cells, and visits nested stable buckets in
upstream order. It filters intersecting boxes and exact spherical distance at leaves.
This is checked against every upstream ordered row, not inferred from source alone.
The original grid remains unchanged. The separate guarded-evolution candidate adds
only a finite full-state condition before entering prepare; its hypothesis is to
bound future-timestep expansion, and its costs remain included in measurements.

L038 side16 confirmation: ordered-evolution/ordered_16 passes all28 snapshots,
all fields/scalars and exact ordered neighbors for3 complete4096-particle updates.
Correctness-driver W22349601912, heap1309769984 bytes, allocated528174465856 bytes,
runtime550617ms. The original2GiB/600s budgets and numerical tolerances are unchanged.
The prepare-entry guard control also passes side12, but heap553140400 is unchanged
and work increases to8531379560; do not retain it as a demonstrated memory improvement.

The validated ordered/evolution sources are now copied into benchmarks/sph-exa/vine
and formatted; unused, unvalidated advance was removed. tools/physics_gate.py runs
full stage validation for both fixed sizes. Its first integrated side12 execution
passes all numerical/order checks, with exactly the experimental work/heap, but
reporting then fails because the shared stats parser required depth on a normal run.
This failed report is preserved in reports/physics/integration/validation. The parser
now has an explicit non-depth mode requiring work/heap/allocation/time; its default
still requires depth. A regression test verifies that neither mode invents a missing
metric.35 tests pass. Full reusable-gate rerun and ordinary regressions remain pending.

Whole-update measurement side12_one_depth forces all30 final fields,10scalars and
per-update time/energy/neighbor-count history, separately from complete state checking.
At1728 particles/1 update, D16636726, W2454904401, heap324075808 bytes,
allocated59392911024 bytes; evaluator forcing checks pass. Runtime169385ms is from
the depth evaluator, not actual parallel timing. This is a functional baseline with
substantial sequential depth, not hardware acceptance. Source/command/pin/results
are preserved beside measure.py. Full scaling and separate worker timing remain open.

## L039: Release-mode diagnostics do not establish application failure

The native square-patch driver preserves the validated stage sequence and upstream
inclusive -s/output columns. Its initial side12 -s0 -w1 output validation passes.
Argument probes in reports/physics/driver/arguments-20260930 exposed a separate bug:
unknown option continues into default work and times out; missing/invalid side
returns exit0 without a message. Source inspection of pinned root/debug/debug.vi
shows debug::error prints only with debug_state and erases its result in release;
it is not a general exception/exit API. Root IO has no process-exit API.

Correct driver parsing with explicit IO diagnostics and control-flow return before
initialization/file creation, not debug::error. Preserve the failing argument probes.
A nonzero native exit status needs a reusable runtime capability and remains a
recorded library blocker; do not claim it or manufacture it with a crash. Evaluators
continue to require complete numeric output, shapes, finite values and provenance,
so an exit0 alone never establishes acceptance. Re-evaluate native driver failure
reporting and pure physics error paths before general unsupported-domain claims.

L038 integration confirmation (2026-09-30): the fixed reusable physics gate passes
both domains in reports/physics/integration/validated-20260930/result.json, with56
complete snapshots and exact ordered neighbors. Work/heap/allocation exactly match
the isolated candidate at both sizes. Normal runtimes including full state dumps
are175913ms/496611ms; maximum field errors2.1100277081131935e-10 and
4.3655745685100555e-10. Validated source is copied into integration/validated-source.
No numerical/performance policy or upstream source changed. Full performance,
workload and hardware acceptance remain open.

Shared regression run20260930T135245Z-36163 passes bootstrap and pilot. All72
neighbor memberships pass, with grid W7957961/D775 at256 unchanged. Only the existing
depth-ratio heuristic fails775>361.2; work ratio/work growth/depth growth still pass.
This confirms no new shared regression and does not advance neighbor acceptance.

L039 driver numerical evidence: driver/validation-20260930 passes the positive
side12 -s0 -w1 and side16 -s2 -w2 cases, including high-precision constants and all
16 dump columns, complete particle coverage and exact file frequency. These checks
use original stage-reference values, including independently derived radius/radial
velocity; they do not substitute reduced-precision upstream text for the fixed
physics oracle. The disabled-output case is the remaining initial-driver check.
The argument-fix candidate passes unknown/missing/invalid-side/invalid-frequency/
negative-step probes with explicit ERROR messages and no files. Its computation
and output suffix is byte-identical to the positive-tested driver. Native exit0 on
rejected arguments remains an explicit runtime limitation, not a passing exit-code
compatibility claim.

## L040: Complete field validation and execution-mode limits are separate

Final reports inspected2026-10-04: integrated stage correctness passes both fixed
sizes for3 updates (integration/validated-20260930). All four separate workers2
whole-update cases pass full-state/history forcing and2GiB: sides12/16 at1 update
W2454904401/6379466527, heap275322736/681400864, runtime51226/140601ms;
at3 updates W7286971002/19476841651, heap407002144/609117056,
runtime193123/484084ms. These are host timings, not1000-core target evidence.

Depth mode passes side12/1 (D16636726,W2454904401,heap324075808), side16/1
(D40881272,W6379466527,heap804246608), and side12/3
(D49477685,W7286971002,heap324129696). Side16/3 reaches the unchanged600s deadline;
no final depth/work/heap measurement is available. Matrix result is false. Do not
infer its missing depth from smaller cases or treat workers2 success as a depth pass.
Exact commands, pins, source hashes and outputs: reports/physics/scaling-20260930/.

Initial native driver validation passes all three positive/disabled-output cases.
After the isolated explicit argument-error repair, side12 -s0 -w1 passes again,
but side16 -s2 -w2 times out at600s; final disabled-output rerun was not reached.
The repaired computation/output suffix is byte-identical to the earlier passing
source (driver/parser-review.json), but that does not waive the timeout. Initial
integration, driver and measurement jobs overlapped; contention is a hypothesis,
not an established explanation. Next isolate the repaired driver timing without
concurrent benchmark jobs at the same budget before changing physics or limits.
Reports: driver/validated-parser-20260930/. Full driver/scaling acceptance remains
false; original policies and reference outputs are unchanged.

## L041: Separate workload readiness from full-scale measurement

User clarification2026-10-04: the objective is a configurable, validated implementation
that could later run SPEC-like particle/step counts; full-scale execution would take
too long and is not requested. Correct the plan in place rather than repeatedly
blocking functional readiness on large-run timing. This is a user-directed scope
change, not numerical evidence or permission to pass failed performance gates.

Readiness still requires workload semantics, manageable-case multistep validation
and a scale-limit audit. Current global neighbor totals use N32; millions of particles
times hundreds of neighbors can exceed32-bit totals. This is an audit risk, not a
measured failure at SPEC scale. Check required arithmetic widths and memory/construction
limits independently; configurable CLI arguments alone do not establish scalability.
No experiment was run for this clarification and no new performance claim is made.


## L042: Audit aggregate widths and allocation bounds before scaling

Source audit2026-10-05 found N32 global neighbor reductions and a `650*h`
guard in the production ordered path. Side210 has9,261,000 particles;
its capacity bound6,019,650,000 exceeds N32 even though particle IDs fit.
Widen global reductions and operands before multiplication to N64, retaining
local IDs/row counts and the unchanged floating-point equations/order. The
first compile exposed inferred N32 zero identities; explicit `0[N64]` fixes
the return-type mismatch. No root/toolchain changes were needed.

Native `--describe` now reports configuration and a30-F64-field storage lower
bound without building particles. Side210 fields alone require2,222,640,000
bytes, exceeding the small-test2GiB heap before trees/neighbors/temporaries.
Do not infer feasibility from CLI acceptance or extrapolate exact heap from
small runs. Source audit also found upstream's64-bit total narrowed to int
in writeConstants; preserve the oracle, document the widened output behavior.

Evidence and reproducible checks: tools/readiness_gate.py and
reports/physics/scale-readiness-20261005/. Configuration gate passes seven capacity values (including the32-bit boundary),
five native preflight sizes and seven argument rejections. The capacity probe
measures D539/W3697/heap6208; each preflight uses heap5968. These measurements
force only configuration arithmetic, not physics. Side12 repeats28 full-state
snapshots successfully: W8,530,050,485, heap553,140,400, allocated200,870,937,184
and runtime179,380ms. Heap matches the prior run; work increases334,968.
Configuration probes overlapped part of regression, so timing is not an isolated
performance comparison. Side16 also passes28 snapshots: W22,350,462,444, heap1,309,769,984,
allocated528,192,954,864, runtime483,431ms; heap unchanged and work increases860,532.
All56 stage snapshots pass, including exact neighbor ordering. The isolated side16 native
output rerun passes in510,016ms under the unchanged600-second limit. This resolves
the outstanding rerun, without proving the cause of the historical timeout. All three native output cases and36 unit tests pass. Independent review.py
checks current source hashes, full fixed coverage, unchanged upstream/oracle/policy
and pinned toolchain; review.json passes. No full-port milestone is accepted.
Checkpoint: reports/checkpoint-20261005-scale-readiness.tar.gz. Next obtain actual
stabilization source; then validate a separate adaptation and longer small-domain
trajectories, and add explicit invalid-state propagation.
See benchmarks/sph-exa/SCALE_READINESS.md for dependency/capacity analysis.
SPEC stabilization remains source-blocked; ng0 in the pinned upstream does not
activate the commented smoothing-length update. A documented count alone is
not sufficient to reconstruct the algorithm.

### Helix configuration check (2026-10-06)

Added `.helix/languages.toml` using the existing pinned Vine wrapper, `--lib
sph=.../benchmarks/sph-exa/vine`, and the square-patch application entrypoint.
Source inspection of `work/vine-lookup/cli/src/vine_cli.rs` confirms entrypoints
are module paths/globs; the root library loads by default. Helix's documented
project configuration merges with user settings. Absolute checkout paths avoid
dependence on the server working directory and must change if the checkout moves.
`hx --health vine` recognizes the server, formatter, grammar and highlights;
indent queries are absent. `python3 tools/vine_exec.py check --lib
sph=/Users/nils/repos/spec-vi/benchmarks/sph-exa/vine
/Users/nils/repos/spec-vi/benchmarks/sph-exa/app/square_patch.vi` passes with an
unused Lookup import warning. A sequential JSON-RPC initialize request using
the configured command returns server capabilities. The probe's shutdown with
explicit null params was rejected; this does not establish an editor shutdown
failure. No interactive editor session was tested. No new numerical or
performance porting lesson, benchmark change, or accepted milestone results
from this editor configuration cycle.


## L043: Depth takes priority over the historical small test heap

Status: user correction and source-confirmed, 2026-10-06; experiments in progress.
The user rejects checksum scheduling gates and explicitly permits larger test heaps.
Upstream density.hpp:64 parallelizes particles; the port's density_rows,
interactions and ordered::rows instead waited for left results before dispatching
right results. These are artificial dependencies, not upstream physics. L037's
workaround enabled correctness under2GiB but must not guide the depth-first port.
Shared-reference gathers and original-order density sums are separate remaining
sources of dependency; removing gates is not proof of hardware scalability.

Experiment reports/physics/depth-first-20261006/ preserves baseline/candidate sources,
preimplementation dependency design, exact commands and machine-readable results.
Candidate removes inter-particle gates and full-state materialization checksums;
capacity checks, equations and original density order stay unchanged. Full-stage
validation and balanced final measurement consumers remain mandatory. Evaluators
accept an explicit --heap-gib profile (default2, this experiment8) and record it
separately from the unchanged historical oracle policy. Normal/depth memory difference
is a hypothesis to test, not an assumption. No acceptance claimed yet.

Re-evaluate all56 stage snapshots at sides12/16 over3 updates, exact neighbor order,
native outputs and whole-update depth/normal memory before promotion. Historical
failures remain preserved; full-scale runs remain deferred. Results pending.

L043 preliminary evidence: direct ungated side12/one-update execution exhausts8GiB
in normal and depth modes. Normal mode passes final-state/history forcing at16GiB:
W2,384,286,962, runtime heap10,528,499,216 bytes,98,782ms. This is not complete
numerical acceptance. Process peak RSS8,654,241,792 is recorded separately from
runtime heap; allocator size and resident memory are not interchangeable. Full-stage
validation and depth remain pending. A tiny routed-gather prototype returns repeated,
reordered IDs correctly (33,11,22,33), but is unvalidated for physics and is not promoted.
Its first compile required explicit droppable generic bounds on shape-error branches;
no unsafe erasure of result connections was added.

## L044: Suite-wide goal; depth is reported, correctness is the gate

Status: user direction, 2026-10-14. The goal is porting all SPEC CPU 2026 workloads to
Vine, simplest first, to benchmark the team's chip. Depth is the most interesting
statistic because it approximates step count on an infinitely parallel machine. Changing
the Vine standard library and adding missing features is expected.

What went wrong: SPH-EXA was treated as the whole objective, and assistant-chosen
performance thresholds (neighbor depth 361.2, depth-ratio/growth ceilings, a fixed
2 GiB heap) were enforced as acceptance gates. About ten experiment cycles (L014-L034)
chased the depth threshold. The heap limit led to checksum gates that serialized
particles (L037), which hurt the headline metric directly. The isolated Vine checkout
with signed commits left needed library changes uncommitted for weeks.

Correction: correctness with fixed tolerances is the only hard gate. Depth, work and
memory are measured across sizes and compared against a baseline. Heap and timeout are
recorded run parameters. Workloads follow docs/ROADMAP.md and are wrapped up, not
perfected, before moving on. Vine changes go on committed branches of ~/repos/vine.
Updated: AGENTS.md, docs/ROADMAP.md (new), docs/VINE_CHANGES.md, docs/PORTING.md,
README.md, benchmarks/sph-exa/plan.md (history moved to HISTORY.md). Re-evaluation:
evaluator policies and the runner still enforce the old thresholds (sph-exa plan task 2).

## L045: Repinning Vine: binary install and snapshot provenance

Status: observed 2026-10-14 while migrating work/vine-lookup to branch spec-vi/sph-support.
1. `cp new work/bin/vine` over the existing executable made every gate fail at once with
   exit -9 (even `--version`); macOS kills an overwritten signed binary. Deleting the file
   first and copying fixes it. Evidence: reports/vine/repin-20261014/failed-sigkill-cp/.
2. The binary embeds VINE_ROOT_PATH/source paths, so rebuilding the same sources elsewhere
   changes binary_sha256. Equivalence was established by an identical root tree hash plus
   490 identical gate metric fields (pilot, neighbors, full physics), not by binary hash.
3. Four staged snapshots were wrong: three stats files were never refreshed after the
   leading_zeros change, and lookup_oob was produced with `vine run` (which prints a
   --debug hint) instead of the harness's `ivm run`. Per-commit snapshot checks
   (tools/vine_snapcheck.py) caught both problems. No numerical or source changes.

## L046: A second host reproduces metrics but not every generated file

Status: measured 2026-10-23 on Linux x86_64 (4 cores, 15 GiB RAM, glibc, clang/gcc),
fresh clone, Vine worktree at the pinned fec2d8c8 (root tree and all checkout files match
the pin; binary sha256 d26ba8f4…, differs as expected, L045).
1. `tools/vine_exec.py` needed /bin/zsh. It now uses `setrlimit` off macOS.
2. `generate_tables.cpp` on glibc differs from the committed table (f0bb9115…) in
   1787 of 40000 values, at most 1.4e-13 relative. The checkpoint copy was used, so
   Vine runs read the same table as the Mac runs.
3. The stage oracle is missing 31 gitignored snapshots. A Linux-regenerated oracle
   (`tools/stage_reference.py`) differs from the Mac files in 59 of 126 hashes. Every
   comparable file is within the fixed atol/rtol (max abs 1.1e-11). Every `.meta` file
   is identical. Linux validation used this host oracle
   (reports/physics/routed-20261023/linux-oracle/result.json), and the decoded side-12
   outputs were also compared with the 56 Mac files present: 0 failures.
4. Pilot and neighbor gates on this host pass, and all 48 + 16 depth/work/heap figures
   equal the 2026-09-30 Mac run (reports/runs/20260930T135245Z-36163) exactly. So depth
   is host-independent for the same Vine source; only the binary hash differs.
   Evidence: reports/runs/linux-20261023/.
Decision: oracles generated on another host are host-local evidence; the Mac oracle
stays canonical. Same-source metrics may be compared across hosts, binaries may not
be assumed identical.

## L047: Routed gather removes particle serialization; live heap is the cost

Status: measured 2026-10-23, same host as L046. Candidate:
reports/physics/depth-first-20261006/routed/sph (unchanged; plus tables.vi), the
routed-gather design from that EXPERIMENT.md. No equations, order or tolerances changed.
Correctness: physics_gate at side 12, 3 updates, 12 GiB heap, passes all 28 stage
snapshots with exact neighbor order (max field error 2.1100277081131935e-10, equal to
the gated candidate). W 9,250,333,305, heap 9,600,894,416 B, 996 s including full
dumps. Side 16 exhausted the 12 GiB heap after 156 s; this host cannot give more.
Evidence: reports/physics/routed-20261023/.
Whole-update depth (1 update, all final fields plus neighbor count forced, identical
checksum bits for both libraries; stage-heap/depth.log):

| side | N | gated D | routed D | gated W | routed W | gated heap | routed heap |
|---|---|---|---|---|---|---|---|
| 6 | 216 | 1,434,639 | 31,404 | 173,771,058 | 186,880,553 | 26.0 MB | 0.80 GB |
| 8 | 512 | 4,014,659 | 69,877 | 539,058,794 | 583,985,222 | 77.0 MB | 2.48 GB |
| 10 | 1000 | 8,763,517 | 132,966 | 1,287,697,961 | 1,400,817,003 | 168 MB | 5.20 GB |
| 12 | 1728 | 16,653,836 | 226,706 | 2,455,015,925 | 2,697,571,526 | 324 MB | 9.92 GB |

Sides 6-10 use the stage-heap drivers. Side 12 uses tools/physics_measure.py
(depth mode, forcing checks against the host oracle pass for both, heap 4/13 GiB;
depth12-1update-*.json, compared with `--baseline` semantics: same_toolchain true).
Depth drops 46-73x for 7-10% more work. Routed depth still grows about linearly in N
at these sizes. (The density-fold hypothesis first recorded here was refuted by L050:
neighbor search dominates.)
Heap: normal-mode stage cut-offs at side 8 (stage-heap/e_routed_8_*.txt) give
prepare 21 MB, +density 260 MB, through IAD 782 MB, +momentum 2.16 GB. The ungated
reference-gather candidate uses 2.45 GB and the gated library 36 MB on the same cut.
So the heap comes from all particle-pair computations being live at once once the
gates are gone, not from routing. Hypothesis: per-pair net size (two kernel lookups,
full 30-field neighbor copies) sets the constant; projecting gathered payloads and
hoisting per-particle terms out of `force` could cut it without adding dependencies.
Decision: do not reintroduce gates (L043). Side 16 validation needs a host with more
memory, or a lower per-pair footprint.

## L048: Small-to-medium inputs first; large SPEC inputs deferred

Status: user direction, 2026-10-24. Goal: port every algorithm, compare it with the
reference in Vine and later on the team's hardware, starting with small-to-medium
inputs. Large SPEC reference inputs are not required for now.
Consequence for SPH-EXA: side 16 (4,096 particles) is itself a small input. It fails
only because the ungated candidate holds ~5.7 MB of heap per particle (L047), which
would rule out medium inputs too (side 30, 27,000 particles, extrapolates to ~150 GB).
This extrapolation is a hypothesis. So per-pair memory, not input size, is the
blocker. Updated: AGENTS.md (input sizes).

## L049: Delay pair instantiation until its inputs exist; project gathered payloads

Status: measured 2026-10-24 on the L046 host. Candidate built from the L047 routed
library and promoted to benchmarks/sph-exa/vine (design.md, "Promoted depth-first
evolution").
Observation: with the gates removed, the runtime instantiates every particle pair's
arithmetic network as soon as the tree structure exists. Those networks then stay
allocated while their F64 inputs from earlier stages are still pending.
Evidence: side 8, normal mode, through momentum (reports/physics/promoted-20261024/stage-heap/):
routed 2.16 GB. Projected `Body` payload: 1.91 GB. Same with a trivial `force`:
0.95 GB, so arithmetic waiting on inputs was ~1 GB. Adding `after(key, …)`, a branch
on a late input of the pair whose two arms are the same call: 0.90 GB. Guarding
density and IAD and projecting IAD to `Mass`/`Site`: 0.60 GB for the whole update
(3.6x less). Work fell 13%, below the gated library. Depth rose ~2%
(69,877 -> 71,144). Forced checksums are bit-identical.
Correctness: physics_gate passes all 28 snapshots at side 12 (heap 3.07 GB, was 9.6)
and side 16 (heap 7.78 GB, W 2.18e10, 2,672 s; previously out of memory). Exact
neighbor order; max field error 2.68e-9. Outputs also pass against the committed Mac
snapshot files (56 + 31).
Decision: `after` is a scheduling hint, not a gate. It orders a pair only after its own
inputs, which the pair already needs, and never waits on another particle. Keep payloads
limited to the fields a pair reads. Hypothesis: the same idiom applies to any ungated
gather-heavy kernel in later workloads; consider a Vine helper once a second workload
needs it.

## L050: Neighbor search is now 89-96% of whole-update depth

Status: measured 2026-10-24, promoted library, depth mode, 1 update.
Stage cut-offs (reports/physics/promoted-20261024/small-sides/neighbor-search-depth.log):
prepare alone (bounds, ordered::build, ordered::rows, checks) reaches depth 28,789 /
66,727 / 129,218 at sides 6 / 8 / 10. The full update reaches 32,408 / 71,144 / 134,346.
Density through energy adds only ~3.6-5.1k. Whole-update depth scales with N
(228,116 at side 12, 531,553 at side 16) although K barely grows (~364 -> ~400), so the
O(K) density fold is not the cause.
Hypothesis (untested): ordered::rows threads one shared `&idx` reference through
all N queries, which serializes them, as L015 measured for the scan. Next candidate:
route queries through the octree as a batch (like routed::gather, or grid::find_batch
in L016), keeping upstream's bucket visit order so neighbor order stays exact.
