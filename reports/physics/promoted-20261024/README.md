# Promoted depth-first SPH-EXA library, 2026-10-24 (L049, L050)

Host and toolchain as in reports/physics/routed-20261023/README.md (Linux, Vine fec2d8c8,
binary d26ba8f4…, host oracle `work/reference-linux`). Library: benchmarks/sph-exa/vine
at this commit, tree sha256 92a477fd… including tables.vi f0bb9115….

| file | command (repo root; L = benchmarks/sph-exa/vine, R = work/reference-linux) |
|---|---|
| physics-gate-side12.json | `tools/physics_gate.py --sides 12 --library L --reference R --heap-gib 12 --timeout 14400` |
| physics-gate-side16.json | same with `--sides 16` |
| driver-gate.json | `tools/driver_gate.py --reference R --heap-gib 12 --timeout 14400` |
| measure-side12-u1.json | `tools/physics_measure.py --side 12 --updates 1 --mode depth --library L --reference R --baseline <gated> --heap-gib 12` |
| measure-side12-u3.json, measure-side16-u1.json | same with `--updates 3` / `--side 16` |
| measure-gated-side12-u1.json | gated library (depth-first-20261006/baseline/sph), `--heap-gib 4` |
| small-sides/ | sides 6/8/10, `depth.sh <lib> <side> 8` (all final fields and the neighbor count forced); `final` = this library, `baseline` = gated, `routed` = L047 |
| small-sides/neighbor-search-depth.log | `depth.sh final <side> 0` (prepare only) and `1` (plus density) |
| stage-heap/ | side 8 normal-mode heap per stage cut-off for each step of L049; `variants/<name>/evolution.vi` are the intermediate sources |
| depth-table.json | `python3 collect.py` |

The side-16 physics run was started from work/lean-candidate/sph, a byte-identical
copy of the library (same tree hash).
