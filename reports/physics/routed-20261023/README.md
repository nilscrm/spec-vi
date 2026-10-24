# Routed-gather candidate on Linux, 2026-10-23 (L046, L047)

Host: Linux x86_64, 4 cores, 15 GiB RAM. Vine fec2d8c8 (pinned source), binary sha256
d26ba8f42da27bf579f07e44990ba9d777746bcec65be528b8c1e70b8d74db2c.
Library: reports/physics/depth-first-20261006/routed/sph plus tables.vi f0bb9115…
(tree sha256 fb0095fc…, recorded in physics-gate-result.json).
Oracle: host-generated, `python3 tools/stage_reference.py --output work/reference-linux`
(linux-oracle/result.json holds its snapshot hashes).

Commands (from the repo root, library copied to work/routed-check/sph):

```sh
python3 tools/physics_gate.py --output work/runs/routed-physics --reference work/reference-linux \
  --library work/routed-check/sph --heap-gib 12 --timeout 10800
python3 tools/physics_measure.py --side 12 --updates 1 --mode depth --output work/runs/routed-depth12 \
  --library work/routed-check/sph --reference work/reference-linux --heap-gib 13 --timeout 10800
python3 tools/physics_measure.py --side 12 --updates 1 --mode depth --output work/runs/gated-depth12 \
  --reference work/reference-linux --heap-gib 4 --timeout 7200
```

Results:

- `physics-gate-result.json`: side 12 passes all 28 snapshots (3 updates, exact neighbor
  order). Side 16 failed with heap exhaustion at 12 GiB (side16/). Overall `passed: false`.
- `depth12-1update-result.json` (routed) and `depth12-1update-gated-result.json`
  (current benchmarks/sph-exa/vine): depth 226,706 vs 16,653,836.
- `stage-heap/`: side 6/8/10 drivers (`stage<k>.vi` stops after k stages), `run.sh`
  (normal mode) and `depth.sh` (depth mode), raw runtime stats and `depth.log`.
  Library names in those scripts: `baseline` = benchmarks/sph-exa/vine,
  `candidate` = depth-first-20261006/candidate/sph, `routed` = the routed library.
