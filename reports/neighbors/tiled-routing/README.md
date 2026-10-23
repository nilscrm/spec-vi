# Request occupancy/compaction experiment

Run run.py and construction.py from the project root. before.vi checkpoints the compacted batch source. Each stride directory preserves full candidate source, generated drivers, full membership output, depth output, exact commands and source hashes. Production, toolchain and gate policies were not changed.

Hypothesis: replace repeated shape-dependent joins with a parallel occupancy reduction and compact at every k-th query-tree level. Holes remain inside groups; all inputs, outputs and consumers are unchanged. Tested k=1,2,3,4. No variant is accepted. Stride3 preserves the growth ceiling but nearly doubles work for only12 fewer depth rounds than ordinary compacted batching. Sweep results are preliminary two-size evidence, not full workload validation; no unnecessary hardware timing runs were performed for rejected variants.

Vine rejected dropping routed result connections in an occupancy-false branch. Even a logically empty tree has a linear request type; the candidate explicitly drains these trees through finish(..., Empty), resolving any result connections. That cleanup is included in the measurements. Never insert unsafe erasure to bypass this requirement.

Construction diagnostics use the same retained runtime builder. The build diagnostic forces all particle identities but drops final bounding metadata. Bounds-only forces all six bounding coordinates. Their consumers differ from full neighbor consumption: do not subtract depths or use them as formal lower bounds for a differently consumed program. They support investigating construction next, not relaxing the fixed depth limit.
