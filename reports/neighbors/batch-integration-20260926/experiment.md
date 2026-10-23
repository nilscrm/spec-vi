# Batch evaluator integration

Scope: finish the partial integration found in the workspace: separate grid.vi,
explicit --candidate grid with one build/find_batch, preserved tree/single path,
and the original 16 extra fixtures. The integration review is
reports/neighbors/grid-clean/evaluator-review.md. No spatial algorithm change.

Dependencies: input point bounds precede runtime 64-cell population; queries depend
on those bounds for ranges. Cells filter query requests before duplicating buckets.
Each query result depends on contributing cells; independent result connections
preserve query identity. Fixed-cell population is O(64*N); worst-case query work
remains O(N*Q). No new asymptotic depth bound is claimed: retained measured 64/256
D634/775 is the comparison. Runtime build, copies, cleanup and every output are
included. Correctness emits full rows; measurement sums every neighbor id+1 then
every query using balanced consumers. Serial control stays byte-identical across
candidate selection. Exact arithmetic, fixtures and policy values are unchanged.

Verification commands:
- python3 -m unittest discover -s tests -v
- python3 tools/runner.py run
- python3 reports/neighbors/batch-integration-20260926/review.py

The ordinary runner independently evaluates shared integration and pilot regression;
a failing depth policy must remain a failed milestone. User direction on 2026-09-26:
after this integration prioritize full physics/timestep implementation rather than
another neighbor optimization cycle. Completion and hardware acceptance still require
all existing checks; the heuristic failure is retained, not waived.

The pre-integration sources are also preserved in reports/neighbors/batch-integration/before/.
The review script checks legacy module/driver identity, policy identity and reproduced
metrics against L033, independently of the status prose.

## Results

Ordinary run reports/runs/20260926T152748Z-33131 passes bootstrap/pilot and all72
membership checks. Both separate worker checks pass. Depth/work/heap/allocated
exactly reproduce L033. Only the depth-ratio budget fails (775 > 361.2); the runner
correctly exits1 and does not advance the milestone. All24 tests and the independent
review assertions pass. review.json records report hashes and budget outcomes.

New reusable guidance is evaluator API/provenance discipline and distinguishing
implementation sequencing from retained acceptance failures (L034). No new algorithm
or performance optimization lesson was produced. The reference audit is source-only;
no full physics, timestep or hardware validation is claimed. Full stage instrumentation
and physics implementation are now the concrete next action.
