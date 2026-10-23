# Neighbor optimization scope

The current user priority (2026-09-26) is full physics and timestep coverage after
batch evaluator integration. Do not start another neighbor optimization cycle solely
because the heuristic gate fails. Follow benchmarks/sph-exa/plan.md. The instructions
below apply only when a neighbor optimization task is explicitly resumed.

Optimize and finish the SPH-EXA neighbor milestone. Follow AGENTS.md and read all required project guidance. The grid passes membership and work budgets but still FAILS the depth heuristic: reports/neighbors/grid-clean/full.json (experimental grid); consult the latest ordinary-runner report for integrated acceptance. Do not accept correctness alone.

Implement the public API in benchmarks/sph-exa/vine/neighbors.vi:
- Point = {id:N32,x:F64,y:F64,z:F64}; unique ids, finite coordinates.
- Query = {id:N32,x:F64,y:F64,z:F64,radius:F64,period_z:F64}; nonnegative radius; period_z=0 disables periodicity, otherwise coordinates occupy one period and radius<period_z/2.
- build(Tree[Point]) -> Index (your representation).
- find(Index, Query) -> Tree[N32]. Return each qualifying id exactly once, exclude self, strict squared distance < radius squared, only z periodic. Use shifted-query arithmetic as the oracle does. Return order is flexible; downstream reassociation remains subject to integrated numerical checks.
- General implementation, no fixture-specific branches, ids, geometry shortcuts, cached expected answers, or native whole-kernel extrinsics.

Run `python3 tools/neighbors_gate.py --candidate grid --output reports/neighbors/<unique-experiment>` for independent verification. The gate includes construction, query batch, duplication, cleanup and output consumption. Expected membership comes from an independent Python brute-force implementation and unchanged upstream C++ on sides12/16. Empty, exact-radius, coincident, periodic, shuffled and clustered cases are included. Growth tests use64/256 points with all points queried. The gate's serial scan is faster in depth than its source structure suggests; do not assume textbook depth without measurement. Current partition recursion, repeated bounding reductions, and broad index duplication are suspect. Try simpler representations and targeted microbenchmarks before adding complexity. Preserve all failed evidence.

You may change benchmark Vine code and Markdown and add candidate probes under work/ or reports/. Do NOT edit tools/, evaluations/, upstream/, benchmarks/sph-exa/reference/, dependencies/, or the pinned Vine checkout/binary. Those inputs are fingerprinted. If a legitimate root-library change is needed, describe the smallest API/semantics/tests and stop for the supervising task to implement it. Do not use --depth as a proxy for wall-clock parallel performance; the gate separately runs two workers.

After a change passes neighbor acceptance, rerun the pilot gate because shared tree/library changes can regress it. Update LESSONS.md, PORTING.md, design.md, COMPATIBILITY.md and plan.md in the same cycle as new learning. A complete milestone requires correctness, depth, work, memory, documentation and an independent supervisor rerun. Do not declare the entire port complete. Do not launch additional workers or modify /Users/nils/repos/vine or stashes.
