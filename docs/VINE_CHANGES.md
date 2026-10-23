# Coordinating Vine changes with SPEC ports

## Repository boundary

Reusable numerical operations, collection APIs, lookup mechanisms, and runtime/compiler fixes belong in Vine. Benchmark constants, SPH equations, data layouts, and compatibility adaptations belong in spec-vi. Do not hide benchmark kernels in native extrinsics to reduce measured depth.

## Where changes go (user direction 2026-10-14)

Changing the Vine standard library and implementing missing language, runtime or
compiler features is expected. Work on a dedicated branch (preferably a git worktree)
of /Users/nils/repos/vine, branched from the base the port needs. Use normal commits;
signing is not required. Never modify, stash or discard uncommitted work or stashes in
the user's main checkout. Pin spec-vi to an exact commit, never to a moving branch.
Do not push, open PRs or merge upstream unless the user asks.

This supersedes the isolated-checkout and signed-commit workflow. That workflow left
the lookup/sine/leading-zero changes uncommitted in work/vine-lookup for weeks because
GPG signing was unavailable. They are now committed (2026-10-14) on branch
`spec-vi/sph-support` in the worktree work/vine: N32.leading_zeros (6553d078), Lookup
sizes/bounds (1136083d), F64.pi/sin_bounded (fec2d8c8), on origin/lookup 7cf26c3e.
evaluations/vine-pin.json pins fec2d8c8. Evidence: reports/vine/repin-20261014/.
work/vine-lookup and patches 0001-0004 are historical records only.

Installing a rebuilt binary: delete work/bin/vine before copying the new one in. Copying
over the existing file on macOS gets the process SIGKILLed (exit 137) (L045). The binary
embeds its checkout path, so a rebuild in another location changes its hash even when
the sources are identical. Check that the root tree hash matches and that gate metrics
reproduce instead. Check Vine program snapshots with `tools/vine_snapcheck.py <checkout>`,
which mirrors tests.nix (`ivm run --no-perf`), or with the nix checks.

## Capability workflow

1. Check existing facilities first. Note the missing operation, call sites and smallest
   reusable API in the active benchmark plan.
2. Specify precision, boundary behavior and expected work/depth scaling.
3. Implement it on the Vine branch with semantic tests plus depth tests on growing
   batches of independent calls. Run Vine's relevant test suite. Generate snapshots
   with the harness command (`vine build` then `ivm run --no-perf`), not `vine run`.
4. Commit, pin the commit in spec-vi, and re-validate the affected benchmark kernels
   on that exact revision. Keep previous measurements; do not compare results across
   toolchains as an improvement.
5. Record lessons and API notes. Track open capability gaps in docs/ROADMAP.md and here.

Changing the toolchain must not weaken numerical oracles. Evaluator changes need their
own rationale and regression tests.

## History

Sections below record earlier decisions. Their references to an isolated checkout,
signed commits or fixed budgets are superseded by the sections above and AGENTS.md.

## Current transition

The user stashed the tracked local Vine edits. The previously built work/vine-source snapshot contains those edits and is superseded for future acceptance. Existing untracked files in the main checkout must not be silently imported.

The initialization/density pilot passed on the isolated lookup checkout with deliberate F64::pi/sin additions and bounded static lookup support. Evidence: reports/runs/20260915T161128Z-45040/pilot/. Support changes are staged; signed checkpoint creation was blocked by unavailable GPG agent access. The main checkout remains untouched.

origin/lookup provides static O(log n) lookup and Array::even_odd. Named sizes stop at Size4096; the 20000-entry SPH table needs a sufficient bound, such as 32768, with bounds behavior and build/code-size measurements. Generic size support belongs in Vine; generated table values and the original SPH interpolation formula belong in spec-vi. The earlier per-query trig reconstruction is an experiment superseded by the selected lookup strategy.

## Leading-zero dependency improvement

A root-only N32.leading_zeros implementation now uses at most five binary-search steps, preserving zero->32. Independent boundary/random vectors and affected N64/Nat/F64 regression outputs pass. Exact patch: dependencies/vine/0003-bounded-leading-zeros.patch. Prototype evidence and memory tradeoff: LESSONS L018, reports/vine/clz/. Compiler binary is unchanged; the loaded root source pin changes. The prior pin and N32 source are preserved in reports/vine/clz/pin-before.json and N32-before.vi. Integrated validation completed in reports/runs/20260921T190441Z-95573: bootstrap/pilot pass and all eight neighbor memberships pass. Neighbor depth/work failures are unchanged and remain open. Actual root measurements in reports/vine/clz/root-after.json reproduce the prototype improvements and memory tradeoff. The dependency pin is validated without accepting the neighbor milestone. Signed commits remain pending the previously recorded GPG limitation; focused patches preserve all changes.

## Dynamic-read investigation

Scalar diagnostics in reports/vine/dynamic-reads/ demonstrate dynamic indexed selection in existing Vine. Copied values and reference-based Array reads have different depth/work/memory tradeoffs (L023). No root capability is currently established as missing; defer an API extension until a runtime spatial-cell workload demonstrates the need.

## Hardware-model correction: sine support reopened

The host-backed F64.sin addition was disallowed by the user’s target hardware model (L025) and is now removed. Pure Vine F64.sin_bounded supports finite |x|<=128; general all-range sine is not implemented. Patch0004 removes the registration, adds the bounded algorithm/tests, and supersedes the host portion of patch0002. Rebuilt source/binary pin and pilot pass in reports/runs/20260922T124634Z-2028 (L027). Preserve old host-sine metrics only as historical evidence. Hardware throughput/primitive-cost validation remains open.

## Application error reporting blocker (L039)

Pinned root debug::error erases its result in non-debug execution; it is not a
release-mode abort. Root IO has no explicit exit-status API. The square-patch driver
must diagnose invalid arguments with IO and return before initialization/files.
Nonzero native application error status and general pure-physics error propagation
remain unresolved; any reusable root extension needs isolated semantic/depth tests
and a repin under the workflow above. No toolchain change is made in this cycle.
