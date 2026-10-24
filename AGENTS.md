# spec-vi working instructions

## Objective and scope

Port every SPEC CPU 2026 workload to clear, idiomatic Vine so it can be benchmarked
on our own chip. Work through the suite in order of simplicity, as listed in
docs/ROADMAP.md. Finish one workload (wrap-up criteria below) before starting the
next, unless the user redirects. Rate/speed pairs (7xx_r/8xx_s) share one port.
Upstream MPI, OpenMP and accelerator backends are not separate port targets.

Read docs/ROADMAP.md, docs/PORTING.md, docs/VINE_CHANGES.md and docs/LESSONS.md, plus
the active benchmark's plan.md, design.md and COMPATIBILITY.md before implementing.
Resume from the recorded next action; do not restart completed work.

## What we measure

Depth (critical-path rounds under `vine run --depth`) is the headline statistic. It
crudely approximates the step count on an infinitely parallel machine. For every
workload, report depth together with work (interactions), runtime heap and numerical
error across several input sizes, so that depth scaling is visible. Measure actual
parallel timing in separate runs and never infer it from depth.

Optimize for depth. Work and memory are recorded and compared against the previous
baseline. They block progress only when a run becomes impractical on the development
machine (timeouts, heap exhaustion). In that case, raise the heap or time limit and
record the profile used before considering any algorithmic workaround. Never add
artificial sequential dependencies, such as checksum gates, to fit a small heap (L043).
Do not invent absolute depth thresholds. A candidate is better or worse relative to a
recorded baseline on the same toolchain.

## Hardware cost model

Target: a chip with about 1000 cores. Extrinsics must correspond to operations that
the target hardware can implement directly as primitives, not host software routines
hidden as one interaction. Host F64 sine is disallowed; transcendental functions are
implemented in Vine, so argument reduction, approximation, copying and dependencies
are measured (L025, L027). Hardware implementability alone does not justify inventing
an accelerator primitive. Primitive latency/throughput is a separate question from
graph depth.

## Acceptance

Numerical correctness is the hard gate. Everything else is measurement.

- Keep upstream sources and licenses unchanged. Put instrumentation and adaptations
  in separate files or reproducible patches.
- Validate against the upstream reference with fixed tolerances, intermediate states
  where available, several input sizes and multiple timesteps/iterations. Never weaken
  tolerances, change expected outputs, omit computation or shrink inputs to accept a
  candidate.
- Floating-point reassociation is allowed when it is documented and validated
  downstream across multiple steps (L038). Keep the original-order oracle.
- Depth measurements must force every output with a bounded-depth consumer and include
  construction, copying and cleanup.
- Before implementing a component, write down its data dependencies, the necessary
  sequential operations and the expected work/depth scaling.
- Record the Vine commit, compiler options, exact input and command for every reported
  measurement. Do not compare results from different toolchains as an improvement.
- Compilation, a checksum or a self-reported completion message is not evidence.
  Require evaluator output.

A workload is wrapped up when it passes correctness on several sizes, has a depth/work/
memory table across those sizes, has a parameterized native driver, and lists its known
gaps in plan.md. Full-scale SPEC runs and hardware timing are separate, deferred claims.

Input sizes (user direction 2026-10-24, L048): port every algorithm and compare Vine
against the reference, then on our hardware, on small-to-medium inputs first. SPEC's
large reference inputs are out of scope for now. Medium inputs must still fit on the
development machine, so per-element memory is a practical constraint.

## Vine changes

Changing the Vine standard library and implementing missing language/runtime features
is expected and encouraged. Reusable functionality belongs in Vine, not in benchmark-
local helpers. Benchmark kernels must not be hidden in extrinsics. Follow
docs/VINE_CHANGES.md: work on a branch or worktree of /Users/nils/repos/vine, commit
focused changes with tests, and pin the commit in spec-vi. Never modify or discard
uncommitted work in the user's main checkout.

## Learning loop

When an experiment, failure, review or user correction teaches something, record it in
docs/LESSONS.md in the same work cycle: observation, commands, results, limits, and
hypotheses marked as hypotheses. Promote reusable techniques to docs/PORTING.md.
Update the benchmark's design.md, COMPATIBILITY.md or plan.md as appropriate. Correct
superseded guidance in place and point to the evidence. If nothing new was learned,
say so instead of churning docs. Do not generalize from one workload or one measurement.

## Plans and checkpoints

Keep each benchmark's plan.md short: current state, open gaps and one concrete next
action. Put experiment history in LESSONS.md and reports/, not in the plan. Keep
docs/ROADMAP.md's status column current. At each milestone, preserve commands and
machine-readable results, and keep useful evidence from failed candidates.
