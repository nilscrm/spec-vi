# Runtime original-order density candidate

Reproduce from the repository root:

```
python3 reports/physics/ordered-evolution/evaluate.py --side 12 --updates 3 --name NEW_OUTPUT_12
python3 reports/physics/ordered-evolution/evaluate.py --side 16 --updates 3 --name NEW_OUTPUT_16
```

Use new output names; preserve existing failed and passing evidence. These are
full-domain diagnostic runs at the fixed 2GiB heap, 600s timeout and original
1e-9 absolute / 5e-12 relative tolerance. Every run saves the pinned toolchain,
library hash, command, all bit-encoded fields/scalars, and exact neighbor order.
The original verified C++ reference remains in first-stages/reference, unchanged.

`ordered_12` preserves compiler diagnostics; `ordered_compile_before.vi` is that
source. `ordered_12_fixed` passes all three complete updates and exact neighbor
order on side12. Side16 results are recorded independently. The sibling
`guarded-evolution` differs only by a full-input checksum condition before entering
`prepare`; it tests cross-timestep memory pressure, not arithmetic.

`ordered.vi` builds stable128-particle octree buckets from runtime particles, visits
periodic z layers then y/x root cells in upstream order, and filters exact distances.
Density uses an ordered fold. Runtime construction, borrowed access, filtering,
checksumming and cleanup remain real computation. Other reduction stages remain
balanced and must pass the same original multistep oracle.

`advance` is not yet the tested entry point: the correctness driver explicitly
materializes each stage. Reconcile and validate this before exposing a runnable
production driver. Correctness-driver work/heap/time include full state transport;
there is no depth or hardware-performance acceptance from these runs.
