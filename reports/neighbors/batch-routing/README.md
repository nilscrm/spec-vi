# Batched neighbor routing experiment

This is an isolated candidate extension, not a replacement acceptance gate. The checked-in benchmark, fixed policies and upstream remain unchanged. `before.vi` preserves the starting candidate; `sph/` holds the exact experimental source. Run experiment.py and controls.py from the project root. Exact argv/logs and the source/fixture/policy hashes accompany the results.

Each query is prepared with a unique negative-polarity result connection. Routing one index node partitions the request tree; accepted requests receive two independent child result connections. The output tree preserves original query identity and shape without an ordered merge. Child routing is independent after its request subset is ready. Small buckets use the existing exact distance predicate and scan. No physics runs in native code.

Expected work follows query visits plus routing/compaction and construction, rather than copying the entire index for every query. Construction remains unchanged. Compaction may create a dependency from all leaves of a request subset to its next traversal. These are hypotheses measured by the full experiments, not asymptotic guarantees.

Controls use the same isolated library, inputs and full output consumer as the batch runs. Full membership is checked against the unchanged independent oracle and recorded upstream fixtures. Query-only diagnostics use a Python-constructed tree with the same partition rule to isolate access; they explicitly exclude construction and are NEVER acceptance evidence for a runtime-built index. Their depths must not be subtracted from full-run depth.

The uncompacted sibling experiment retains empty internal branches to test that compaction dependency. This can expose child traversal earlier at the expense of visiting empty request structure. Its coverage, output checks and original acceptance budgets remain the same.
