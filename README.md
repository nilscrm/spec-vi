# spec-vi

Vine ports of the SPEC CPU 2026 workloads, for benchmarking our own chip. Depth (critical-path
rounds) is the headline statistic. Workloads are ported in order of simplicity; see
[docs/ROADMAP.md](docs/ROADMAP.md). SPH-EXA (803.sph_exa_s) came first and is being wrapped up.

## Layout

- `benchmarks/<name>/`: port, compatibility notes, and validation configuration.
- `upstream/<name>/`: unmodified reference sources, with original licenses.
- `work/`: ignored downloads, builds, and run outputs.

Vine checkout: `/Users/nils/repos/vine`. It has local modifications; do not overwrite them.

The initial SPH-EXA source is pinned in `benchmarks/sph-exa/source.json`.
This is an upstream-based research port, not the SPEC source distribution or an official SPEC result.
The complete square-patch physics sequence is implemented in Vine. The ordered
physics candidate passes every intermediate state for three updates on both fixed
domains (12 cubed and 16 cubed). Integration, driver, scaling and hardware acceptance
are tracked separately in `benchmarks/sph-exa/plan.md`; the full port is not complete.

## LBM (782.lbm_r)

Active since 2026-10-24; state and next action in `benchmarks/lbm/plan.md`, notes in
`benchmarks/lbm/COMPATIBILITY.md` and `design.md`. The Vine library is
`benchmarks/lbm/vine` (`lbm`) and the native driver is `benchmarks/lbm/app/lbm_app.vi`:

```sh
python3 tools/vine_exec.py run --heap 4G --lib lbm=benchmarks/lbm/vine \
  benchmarks/lbm/app/lbm_app.vi -- -x 16 -y 16 -z 16 -n 10 --channel \
  --obstacles OBSTACLE_FILE --result velocity.dat
python3 tools/lbm_gate.py --output work/lbm/check            # correctness
python3 tools/lbm_gate.py --output work/lbm/m --measure      # plus depth/work/heap
make lbm-smoke                                               # reference only
```

## Fresh clone setup

`work/` is not in git. The pinned Vine toolchain is branch `spec-vi/sph-support` of
https://github.com/nilscrm/vine (commit in `evaluations/vine-pin.json`):

```sh
git clone -b spec-vi/sph-support https://github.com/nilscrm/vine.git work/vine
git -C work/vine checkout <commit from evaluations/vine-pin.json>
(cd work/vine && cargo build -r --bin vine --bin ivm)
mkdir -p work/bin && rm -f work/bin/vine && cp work/vine/target/release/vine work/bin/vine
```

Always `rm` before `cp`; overwriting the binary in place gets it SIGKILLed on macOS (L045).
The binary embeds its build path, so on a new machine its sha256 will differ from
`binary_sha256` in the pin and `tools/toolchain.py` will refuse to run. After confirming
that the checkout is at the pinned commit and its `root/` tree hash matches `source`,
record the new binary hash in the pin and note the machine in the commit message.
Large raw dumps (>1 MiB) under `reports/` are listed in `.gitignore` and exist only on
the original machine; regenerate them with the corresponding tools when needed.
Two of them are not reproducible bit-for-bit on another platform (L046):

- `benchmarks/sph-exa/vine/tables.vi` (sha256 `f0bb9115…`): extract it from
  `reports/checkpoint-20260926-batch-integration.tar.gz`. Regenerating it with
  `reference/generate_tables.cpp` on Linux/glibc gives different last digits.
- `reports/physics/first-stages/reference/` is missing 31 snapshots. On another host,
  generate a local oracle with `python3 tools/stage_reference.py --output work/reference-<host>`
  and pass it to the physics tools with `--reference`. Such an oracle is evidence
  only for that host.

On Linux `tools/vine_exec.py` sets the 64 MiB stack with `setrlimit`; zsh is only
needed on macOS.

## Build and smoke-run the upstream serial reference

```sh
make sph-exa-smoke
```

This uses the system C++ compiler without OpenMP. The smoke case is 12 cubed particles, with iteration labels 0 and 1. See the compatibility notes before interpreting `-s`.

## Porting workflow

Helix project settings live in `.helix/languages.toml`. Open Helix from this
checkout to load them. The server and formatter use `tools/vine_exec.py` and
the pinned `work/bin/vine`; the LSP loads the `sph` library and square-patch
application. Paths are absolute for this local checkout; update them if it moves.
The existing user-level Vine grammar configuration supplies syntax highlighting.

Read `AGENTS.md` and `docs/PORTING.md`. New discoveries must update `docs/LESSONS.md` and the relevant instructions/design/plan in the same work cycle. The suite roadmap is `docs/ROADMAP.md`; each benchmark's `plan.md` holds its current state and next action. The status runner and basic evaluation utilities are implemented. Full-state numerical evaluators are implemented. Fixed-domain correctness does not
establish full-workload or target-hardware acceptance.

## See and control the runner

```sh
cd ~/repos/spec-vi
make status  # current milestone, passed checks, and whether the full port is complete
make watch   # refresh while a run is active; exits when it stops or waits
make start   # run registered acceptance checks in the background
make stop    # stop the active runner
```

Open `STATUS.md` for a snapshot. `reports/status.json` is machine-readable; `reports/runs/` contains per-run evidence and logs. Use `make status` to detect a crashed runner rather than trusting an old snapshot. See `docs/RUNNER.md` for completion semantics.

## Run the Vine square-patch application

The native entry point is `benchmarks/sph-exa/app/square_patch.vi`. It uses the pinned
runtime through `tools/vine_exec.py`; no host implementation of the physics is used.
Run in a fresh output directory, since the upstream-style driver writes
`constants.txt` and optionally `dumpN.txt` into its working directory:

```sh
mkdir -p work/square-patch-run
cd work/square-patch-run
python3 ../../tools/vine_exec.py run --heap 2G \
  --lib sph=../../benchmarks/sph-exa/vine \
  ../../benchmarks/sph-exa/app/square_patch.vi -- -n 12 -s 0 -w 1
```

`-s 0` runs one complete update; `-s 2` runs three. Defaults match the upstream
serial program (`-n 50 -s 10 -w -1`); the default scale is not yet validated.
Nonpositive write frequency disables particle dumps. Constants are written every
update. Columns match upstream, including radial distance/velocity, but native
Vine decimal formatting is not a promise of byte-identical C++ text. This does not
implement the separate SPEC stabilization or CSV adaptations.

Run the complete stage evaluator against a verified instrumented reference:

```sh
python3 tools/stage_reference.py --output work/stage-reference
python3 tools/physics_gate.py --reference work/stage-reference --output work/physics-check
python3 tools/driver_gate.py --reference work/stage-reference --output work/driver-check
```

Use fresh output paths. Full-state checks retain every particle/field/stage and the
original tolerances. Whole-update depth and actual worker timing are separate
measurements, with reports under `reports/physics/`.


To inspect a large configuration without allocating particles, append `--describe`
to the native driver's arguments. For example: `--describe -n 210 -s 24 -w 7`.
See [scale-readiness audit](benchmarks/sph-exa/SCALE_READINESS.md) for limits,
storage lower bounds, and the remaining SPEC adaptation gaps.
