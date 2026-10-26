# SPH-EXA compatibility and next steps

Reference: https://www.spec.org/cpu2026/Docs/benchmarks/803.sph_exa_s/803.sph_exa_s.html

SPEC names upstream revision 7604c824 as its starting point and says some later changes were incorporated. The archive under `upstream/sph-exa` is unchanged, including its MIT license. The manifest records the full revision and archive hash. Exact SPEC equivalence remains unverified.

## Observed differences to investigate

- Upstream initialization explicitly converts to CGS units. Its sound speed is 3500 cm/s, consistent with the documented 35 m/s; this alone is not a physics difference. Never transplant constants without reconciling units throughout.
- Upstream uses h = 2.5 * dx, dx = 100 / side, mass = 1000000 / particle_count, and initial density 1. SPEC describes fixed smoothing length, mass, and a different initial density. Check units and resolution dependence before changing anything.
- Upstream has ng0=500 (target) and ngmax=650 (capacity); SPEC describes a target of 650. Increasing the target alone may exceed neighbor capacity.
- Upstream writes constants.txt and dump*.txt; SPEC describes CSV and sampling every 128th particle, with validation of intermediate state.
- SPEC removes OpenACC and OpenMP target support. The initial reference build here is serial and disables all accelerator/MPI paths.
- The upstream timestep loop is inclusive: iteration=0 through maxStep. Thus `-s 0` executes a complete update, not merely initialization. The prior chat claim that zero timesteps necessarily leaves evolution untested was incorrect for this source. Verify SPEC loop semantics when reconstructing its driver.
- SPEC describes 15 stabilization steps; its implementation has not been reconstructed.

## Port sequence

1. Freeze serial C++ reference outputs and add high-precision intermediate-state instrumentation separately from upstream.
2. Reproduce initialization in Vine F64, preserving units and precision.
3. Port octree and neighbor traversal; validate sets and order against C++ and a small brute-force oracle.
4. Port density, equation of state, IAD, momentum/energy, timestep selection, position update, and total energy, in source order.
5. Compare complete state after each stage on small valid domains, then multiple updates.
6. Reconstruct documented SPEC workload/output changes separately, with provenance for each change.
7. Measure memory and runtime before attempting the reference scale.

Use n >= 10 for the unmodified initialization's smoothing-length/domain constraint; the smoke case uses n=12. Do not blindly use a tiny 2x2x2 domain.

## Validated pilot scope

Initialization (all 30 fields at sampled particles) and density using upstream-provided neighbor lists pass on sides 12 and 16. This does not yet validate independent neighbor search or time evolution. Preserve computed periodic extent exactly and use the original value/derivative interpolation table. Balanced reductions reorder additions; multistep error growth remains unvalidated. See LESSONS L009–L011.

The retained neighbor-search candidate independently matches all fixed membership cases, including sampled upstream sides12/16, strict radius, self-exclusion, z-periodicity, empty and clustered inputs. Spatial membership is exact; returned order differs and capacity saturation remains outside the initial contract. Performance acceptance still fails, so this is not an accepted integrated neighbor stage. Bounds reduction uses infinity identities internally; all tested physical inputs remain finite.

Initialization sine is now computed in Vine with an explicit |argument|<=128 domain; the original modes/coordinates stay below39*pi. The fixed pilot numerical tolerances still pass after replacement. This is not a general all-range F64 sine implementation, and multistep error acceptance remains pending (L027).

## Full-update semantics to preserve (source audit 2026-09-26)

The serial timestep recomputes nonperiodic x/y bounds through DistributedDomain::distribute; BBox::compute preserves the initialized periodic z bounds (L035).
After density, iteration zero alone initializes ro_0. Equation of state resets c to
3500 and u to 1 on every update, in addition to computing pressure with exponent 7.
Timestep selection takes the global minimum of Kcour*h/c and caps it using
maxDtIncrease*dt_m1[0]. Position/energy updates consume previous-step fields before
replacing them; periodic wrapping is the upstream conditional single-period shift.
These observations come from sqpatch.cpp and include/sph/{density,equationOfState,
timestep,positions,totalEnergy}.hpp, not new validated Vine physics. The next stage
oracle must expose these transitions, all particle fields, scalar time/energy and
ordered neighbors. Unsaturated set agreement alone cannot establish multistep
numerical compatibility or capacity behavior.


Batch evaluator integration is verified in ordinary run20260926T152748Z-33131:
all24 fixtures pass tree single-query, grid single-query and grid batch APIs (72
checks). The selected measured path is grid build+find_batch; the original tree
remains available. This broadens regression coverage but does not resolve returned
order, saturation, multistep error or the still-failing depth heuristic (L034).

Multistep evidence L038: balanced density with different neighbor order fails the
unchanged pressure tolerance on19 particles at the second side12 update. Exact
membership and per-density tolerance are insufficient. Original-order C++ replay
on candidate geometries recovers original densities; runtime ordering and ordered
Vine density remain to be validated. Full port acceptance is still false.

The isolated ordered-evolution/ordered_12_fixed candidate now passes all3 side12
updates, including exact upstream neighbor order and every stage field/scalar.
Density uses the original ordered fold; IAD/momentum remain balanced. Maximum field
error2.1100277081131935e-10. Side16 now also passes3 updates and exact order (L038). These are fixed-domain
functional checks; larger workloads, capacity behavior and performance acceptance
remain pending.

## Native driver scope

The new app/square_patch.vi reproduces upstream's -n/-s/-w defaults and inclusive
step loop, constants columns and particle dump columns, including radius/radial
velocity computed in Vine. It uses native decimal precision rather than promising
C++ default-format byte identity. driver_gate.py compares against high-precision
stage-reference values with the unchanged numerical tolerance and checks requested
file frequency. SPEC CSV/stabilization changes are not implemented by this driver.

Argument failures require explicit IO messages and control-flow return (L039).
The pinned runtime lacks an exit-status API, so native invalid-argument returns
currently exit0 after an ERROR diagnostic and no output files. Nonzero exit status
and general pure-physics failure propagation are open compatibility limitations;
evaluator success still requires complete finite numerical output.

The user's current target (2026-10-04) is SPEC-like workload readiness with manageable
validation, not full-scale execution or official score reproduction. Matching
initialization/stabilization/step/output semantics and reviewing larger-parameter
limits remain necessary; actual full-scale feasibility and timing remain unmeasured.


Scale audit2026-10-05 (L042): global ordered/evolution neighbor totals and capacity
products now use N64; local IDs/counts remain N32. Native --describe inspects
configuration without initialization. See SCALE_READINESS.md for dependencies,
arithmetic limits, storage lower bounds, and unresolved stabilization/error semantics.
Upstream's writeConstants narrows its64-bit total to int; Vine intentionally retains
the full total. Fixed small-domain numerical policies and upstream source are unchanged.


Depth-first correction2026-10-06 (L043): checksum scheduling gates were introduced
by the port, not upstream physics. Their removal is being tested separately with
an explicitly enlarged heap. Original equations, ordered density sums, exact neighbor
order and full numerical coverage remain required; no SPEC equivalence is implied.


Depth-first library promoted 2026-10-24 (L049): the ungated routed-gather library
passes all 56 stage snapshots (sides 12 and 16, 3 updates, exact neighbor order,
unchanged tolerances; max field error 2.68e-9 at side 16) against the host oracle on
Linux, and the outputs also pass against the committed Mac snapshot files.
Equations, the ordered density sum and neighbor order are unchanged; pair arithmetic is
bit-identical (projected payloads only drop unread fields).
The native driver passes driver_gate.py on the promoted library for all three cases
(side 12 -s 0 -w 1, side 16 -s 2 -w 2, side 12 -s 0 -w -1), with 12 GiB heap
(reports/physics/promoted-20261024/driver-gate.json).
