# Proposed batch evaluator integration

This reviews evaluator coverage, not relaxation of acceptance or hardware approval.

The cleaned grid exposes build(points), find(index,query), and find_batch(index,queries).
The existing gate evaluates a map of find calls. Evaluating this batch algorithm
requires a separate candidate path that calls find_batch once after build.

Required preserved checks:

- Keep the existing eight fixtures, reference inputs, oracle and exact membership checks.
- Validate both APIs; preserve query identity and reject duplicated neighbors.
- Include the16 extra fixtures through both APIs as regression coverage.
- Construct the grid in Vine inside each measured program, once per workload.
- Force every query output with the existing balanced checksum; correctness uses full rows.
- Preserve the existing serial-scan baseline and all policy values, including the
  explicitly provisional0.7 depth ratio. Any policy review is a separate change.
- Measure64/256 scaling, runtime heap, process memory and separate two-worker runs.
- Report the selected API/representation in provenance; no successful milestone is
  implied by changing the driver. This candidate still fails the current depth heuristic.

Implementation approach: add the grid as a separately named module and an explicit
batch candidate option in the neighbor evaluator. Keep the existing neighbor module
and single-query driver available. Add small driver/oracle tests that establish
query coverage, API selection and runtime-construction inclusion. Run the ordinary
runner after shared module/evaluator changes; preserve old baseline reports.

Known limits: fixed64-cell population costs O(64*N), and clustered or increasing-N
workloads can still approach all-pairs scanning. No variable-resolution policy,
capacity-saturation behavior, neighbor-order integration, full timestep validation,
or target1000-core performance acceptance is established by these tests.
