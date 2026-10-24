# LBM plan (782.lbm_r)

Status: **active** (docs/ROADMAP.md). Started 2026-10-24 on the user's direction, while
SPH-EXA wrap-up continues separately.

## Current state

- Survey done. The upstream is the Parboil CPU copy of the SPEC lbm kernel (`source.json`),
  because the SPEC page was unreachable. The reference is the documented double-precision
  adaptation plus a SPEC-style driver with state dumps (`reference/`, COMPATIBILITY.md).
- Full Vine port, both simulation types (lid-driven cavity, channel flow), obstacle files,
  and binary velocity output: `vine/` (library `lbm`) and `app/lbm_app.vi` (native driver,
  parameterized grid size, steps, simulation type and obstacles).
- Correctness (`tools/lbm_gate.py`): every state after every step and the velocity file are
  **bit-identical** to the reference on 6 cases (6 grid shapes from 8^3 to 16^3, both
  simulation types, none/sphere/random obstacles, 3-10 steps). Tolerances are fixed in the tool.
- Depth/work/heap table for 8^3-32^3 (0/1/2 steps), 16^3 over 8 steps, and channel flow at
  8^3 and 16^3: reports/lbm/candidate-20261024/result.json, summarized in design.md.
  Per-step depth is 266 at every size; work is about 1550-1840 interactions per cell-step.
- No Vine changes were needed; the pin is unchanged (fec2d8c8).

## Open gaps

- SPEC identity unconfirmed: SPEC page/kit, SPEC literal spellings, SPEC inputs (obstacle
  files, steps, size) and any SPEC-specific source changes.
- Work: about 61% of interactions are the 19-way split/merge around streaming (design.md).
- Setup builds index rows sequentially (O(SX+SY+SZ) depth); needs a parallel tabulate.
- Normal-mode heap is about 1.45 KB per cell at 32^3; the 100x100x130 SPEC size would need
  about 2 GB. Not yet run (L048: medium sizes first).
- Statistics output (`LBM_showGridStatistics`) and the SPEC compare action are not ported.
- No parallel timing yet (separate claim).

## Next action

Ask Nils to confirm the upstream against the SPEC 782.lbm_r page/kit. Then reduce
split/merge work with a measured Vine primitive (single-pass n-way zip/unzip or an
`even_odd` inverse) on a Vine branch, and extend the table to 48^3-64^3.
