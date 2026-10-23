# First full-port cycle

Before implementation: use the dependency table in benchmark design.md (L034).
Freeze side12/16, three reference updates, all30 particle fields and original
atol1e-9/rtol5e-12. Stage snapshots are separate instrumentation; compare ordinary
constants/dumps byte-for-byte with unmodified upstream. No reassociated reference.

Runtime integration candidate: balanced tree of all initialized particles, runtime
grid build, grid batch query, runtime neighbor state gather, density, rest density
on iteration zero, then local EOS. O(N*400) initialization and O(64*N) grid population;
worst-case neighbor work O(NQ). Compare copied versus reference tree gathers where
copy costs dominate. Both include construction, copying and cleanup. Reference
gathers necessarily serialize access and are a functional baseline, not a depth win.
Measure actual compiled D/W/heap/RSS with full output forcing and separate workers.
Correctness must cover all particles on the fixed sides; partial diagnostics are
explicitly labeled and do not replace coverage. No native transcendental is added.

## Full-domain attempt

Reference stage instrumentation matches ordinary upstream constants/dumps byte-for-byte
at sides12/16 for three updates. Maximum observed neighbor count512, unsaturated.
All1728 side12 particles pass init/density/rest/EOS with unchanged tolerances; maximum
absolute field error7.275957614183426e-11. Full side16 membership run fails runtime
OOM under the fixed2GiB heap. See membership/side16.{json,stderr}. This does not identify
which part of the live graph dominates; isolate initialization before attributing it.
The candidate and gate are not accepted. Keep inputs/budgets unchanged.

Hypothesis for an alternative if initialization dominates: pressure and every initial
field except z/z_m1 repeat across z planes. Build one runtime xy plane and reuse its
values, computing each z explicitly with the original arithmetic. This is runtime
common-expression reuse (not a table of expected outputs); it changes graph ownership
and may add reference-access depth. Test all30 fields at both full sides and measure
whole-pipeline work/memory/depth. Preserve the original initializer as the control.
