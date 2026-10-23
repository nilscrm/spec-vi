# SPEC CPU 2026 porting roadmap

Goal: Vine ports of every SPEC CPU 2026 workload, worked through from simplest to
hardest. The suite has 52 benchmarks: 14 intrate, 13 intspeed, 12 fprate and 13
fpspeed. Rate/speed pairs share one application and one port (the driver selects the
workload size), which leaves 38 distinct applications. The benchmark list comes from
https://www.spec.org/cpu2026/Docs/ (fetched 2026-10-14). Per-benchmark pages follow
`https://www.spec.org/cpu2026/Docs/benchmarks/<name>/<name>.html`.

## Ordering

The order below is a **provisional estimate** from each application's area, language
and typical code size. It is not based on inspecting the SPEC sources. Before starting
a workload, check the upstream source size, language features, I/O and Vine capability
gaps, and reorder if the estimate is wrong. Fortran and large C++ codebases may need
new Vine features (multidimensional arrays, complex numbers, string handling, hash
maps, and so on). Record those gaps here and in docs/VINE_CHANGES.md.

The very large programs at the end (sqlite, compilers, interpreters, simulators) are in
scope. What a port means for each still needs to be decided per program; for example,
a full program versus its hot computational core with the original inputs.

Status values: `active`, `wrap-up`, `done`, `next`, `queued`.

| # | Application | Benchmarks | Lang | Area | Status |
|---|---|---|---|---|---|
| 1 | SPH-EXA | 803.sph_exa_s | C++ | SPH hydrodynamics | wrap-up |
| 2 | LBM | 782.lbm_r | C | Lattice Boltzmann CFD | next |
| 3 | TeaLeaf | 811.tealeaf_s | C | Heat conduction, CG solver | queued |
| 4 | CloverLeaf | 820.cloverleaf_s | Fortran | Explicit hydrodynamics | queued |
| 5 | POT3D | 800.pot3d_s | Fortran | Solar physics, finite differences/CG | queued |
| 6 | Graph500 | 854.graph500_s | C | Graph analytics (BFS) | queued |
| 7 | fotonik3d | 749.fotonik3d_r, 849.fotonik3d_s | Fortran | Electromagnetics (FDTD) | queued |
| 8 | neutron | 881.neutron_s | C | Neutron transport | queued |
| 9 | NAB | 816.nab_s | C | Molecular modeling | queued |
| 10 | xz | 801.xz_s | C | Compression | queued |
| 11 | FLAC | 817.flac_s | C | Lossless audio compression | queued |
| 12 | zstd | 777.zstd_r | C | Compression | queued |
| 13 | NTest | 707.ntest_r, 807.ntest_s | C++ | Othello AI | queued |
| 14 | astcenc | 731.astcenc_r | C++ | Texture compression | queued |
| 15 | Cactus | 709.cactus_r, 809.cactus_s | C++/C | Relativity, finite differences | queued |
| 16 | NAMD | 857.namd_s | C++ | Molecular dynamics | queued |
| 17 | Stockfish | 706.stockfish_r | C++ | Chess engine, NN evaluation | queued |
| 18 | SEAL | 750.sealcrypto_r | C++ | Homomorphic encryption | queued |
| 19 | DIAMOND | 838.diamond_s | C++ | Protein sequence alignment | queued |
| 20 | NEST | 767.nest_r, 867.nest_s | C++ | Spiking neural networks | queued |
| 21 | flightdm | 748.flightdm_r | C++ | Flight dynamics | queued |
| 22 | OpenColorIO | 736.ocio_r | C++ | Color management | queued |
| 23 | ROMS | 765.roms_r, 865.roms_s | Fortran | Ocean modeling | queued |
| 24 | PALM | 722.palm_r, 822.palm_s | Fortran | Atmospheric LES | queued |
| 25 | femflow | 766.femflow_r | C++ | High-order FEM fluids | queued |
| 26 | Marian | 772.marian_r, 872.marian_s | C++ | Neural machine translation | queued |
| 27 | MiniZinc | 846.minizinc_s | C++ | Constraint programming | queued |
| 28 | SQLite | 708.sqlite_r | C | SQL database | queued |
| 29 | OMNeT++ | 710.omnetpp_r | C++ | Discrete-event simulation | queued |
| 30 | ns-3 | 753.ns3_r, 853.ns3_s | C++ | Network simulation | queued |
| 31 | VPR | 734.vpr_r, 834.vpr_s | C++ | FPGA place and route | queued |
| 32 | ABC | 729.abc_r, 829.abc_s | C++/C | Logic synthesis/verification | queued |
| 33 | Gmsh | 737.gmsh_r | C++ | Mesh generation | queued |
| 34 | Cppcheck | 727.cppcheck_r, 827.cppcheck_s | C++ | Static analysis | queued |
| 35 | CPython | 714.cpython_r | C | Python interpreter | queued |
| 36 | gem5 | 735.gem5_r, 835.gem5_s | C++ | Architecture simulation | queued |
| 37 | GCC | 721.gcc_r, 821.gcc_s | C | C compiler | queued |
| 38 | LLVM | 723.llvm_r, 823.llvm_s | C++ | C/C++ compiler | queued |

SPH-EXA came first for historical reasons. It is being wrapped up (see
benchmarks/sph-exa/plan.md) rather than taken to full completion before moving on.

## Per-workload lifecycle

1. Survey: find the upstream source SPEC is based on, pin it unchanged, build and run a
   reference smoke test, and list the Vine capability gaps.
2. Evaluator: reference outputs or intermediate states on several small sizes, fixed
   tolerances, and a depth driver that forces all outputs.
3. Port: dependency analysis, then component-by-component implementation with
   correctness and depth/work/memory measurements.
4. Wrap-up (AGENTS.md): correctness on several sizes, a depth-scaling table, a
   parameterized native driver, and known gaps written down.

Reuse infrastructure across workloads. Generalize tools/ (runner, gates, vine_exec,
state codec) as each new workload needs it, rather than copying SPH-specific scripts.
