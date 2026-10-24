# Runner operation

## What is installed

`tools/runner.py` is a local background milestone supervisor. It executes acceptance gates in order and updates `STATUS.md`, `reports/status.json`, and `reports/runs/<run-id>/status.json`. Each gate preserves argv, working directory, exit status, duration, stdout, stderr, and an evaluation report. The bootstrap gate verifies unchanged upstream sources, runs infrastructure tests and C++ smoke cases, and checks Vine depth and worker execution separately.

This bootstrap is not a SPH-EXA Vine implementation. Do not register a passing placeholder to advance a milestone.

## Correctness gates, reported measurements (L044)

Gates pass or fail on numerical correctness only (fixed tolerances, exact neighbor
membership/order, checksum consumers). Depth, work and heap are measurements:

- `pilot_gate.py` and `neighbors_gate.py` write a `scaling` section (candidate vs the
  serial control at the largest size, and growth across sizes). The retired budgets
  (`max_depth_ratio`, `max_depth_growth`, ..., fixed 2 GiB heap) are no longer read.
- Every gate and measurement tool takes `--heap-gib` and `--timeout` and records them
  under `resources` in result.json. workflow.json passes them explicitly. A run that
  exhausts its heap or hits the timeout fails as a command failure; rerun it with a
  larger profile and record the profile used (AGENTS.md).
- `--baseline <earlier result.json>` (pilot, neighbors, physics_measure) adds a
  `comparison` section with current/baseline ratios for every depth/work/heap figure.
  `same_toolchain` is true only when both reports carry the same `toolchain` identity
  (Vine commit and binary hash); otherwise the ratios are not an improvement claim.
- The physics-stage oracle is matched on sides/updates/atol/rtol only
  (`stage_reference.verify_reference`), so resource changes do not invalidate it.

## Commands

From `~/repos/spec-vi`:

- `make start`: background acceptance run.
- `make run`: foreground acceptance run.
- `make status`: current status, including stale-process detection.
- `make watch`: refresh every two seconds while running; exits on terminal/waiting state.
- `make stop`: stop the active runner and its gate process group.
- `make test`: infrastructure tests, with no model calls.
- `python3 tools/runner.py status --json`: machine-readable status.

Only one runner can hold the lock. Repeated starts are refused while active. A new run rechecks earlier gates, which avoids trusting results for changed source. Reports from earlier runs remain available.

## Code-writing mode (obsolete)

The user no longer has the Codex setup (2026-10-14). `runner.py start --port` and the
Codex heartbeat are obsolete and must not be used; docs/WORKER_PROMPT.md and
docs/NEIGHBOR_WORKER.md are kept only as history. The runner is an acceptance checker.
Porting work happens in interactive agent sessions that follow AGENTS.md.

## Status meanings

- `running`: a runner holds the lock and is checking or implementing the named milestone.
- `waiting`: a required acceptance check is missing. No background work continues.
- `failed`: a command, numerical check, resource deadline, or acceptance report failed.
- `stopped` / `interrupted`: unfinished work remains; inspect evidence before resuming.
- `complete`: ALL required registered milestones passed independent gates. The required list includes full selected workloads and hardware validation.

`port_complete` is separate from individual passed checks. The runner cannot establish scientific validity by itself: gate coverage, tolerances, and depth/resource budgets must be sound before registration. It rejects omitted required milestones, missing/false/wrong reports, and stale output reports.

## Notifications and limits

Completion and failure update the local status and runner log. `make watch` exits visibly with the final status. There is no scheduled follow-up task.

Bootstrap probes the pinned worktree (`work/vine`) and installed binary (`work/bin/vine`, overridable with `VINE_BIN`) and records the binary hash plus checkout status; later gates verify both against evaluations/vine-pin.json. The scalar diagnostic exercises the metrics pipeline, not a SPH kernel. Reference smoke dumps use upstream's default output precision. High-precision pilot snapshots, complete pilot output consumption, and process RSS are implemented. Full evolution and target-hardware timings remain unvalidated. Vine support changes are committed on branch spec-vi/sph-support and pinned in evaluations/vine-pin.json (docs/VINE_CHANGES.md).

## Batch neighbor integration

The registered neighbor command selects `--candidate grid` explicitly. The gate also
checks the retained tree single-query path and both grid APIs on the fixed and extra
cases; the default standalone candidate remains `tree`. Each report identifies the
selected representation/API and records the full pinned toolchain.

Physics, integration and workload milestones have no registered gate yet, so a run
ends in `waiting` after the neighbor milestone. tools/physics_gate.py is the physics
correctness check; register it once the depth-first candidate passes
(benchmarks/sph-exa/plan.md).
