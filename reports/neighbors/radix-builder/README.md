# Bottom-up Morton radix builder experiment

Hypothesis: compute one global bounding reduction, generate all spatial keys independently, combine compressed radix trees along the existing balanced input tree, and compute exact per-node bounds in one final bottom-up pass. Avoid repeated bounds reductions and whole-subtree partitions at successive spatial levels. Compressed radix merge remains data-dependent and must be measured; no depth bound is assumed from its name.

Keys are 30-bit Morton codes, ten bits per coordinate after normalization. Keys only organize exact points: collisions retain all particles in a bucket and exact distance predicates still decide membership. Zero coordinate span maps to zero. Input construction, key generation, merging, conversion, batch routing, cleanup and the existing output consumer are included in full measurements. The registered gate and its budgets are unchanged. before.vi checkpoints the prior batched candidate; all changes remain isolated here.
