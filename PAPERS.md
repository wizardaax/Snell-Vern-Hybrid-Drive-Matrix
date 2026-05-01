# Snell-Vern Hybrid Drive Matrix — Research Papers

The "ADAM HIVE MATRIX" line traces the evolution of the hive-mesh dispatch architecture used in this repo. v1 → v2 → v11 → V10 reflects the actual development order (v1 → v2 → v11 with renumbering at V10 for the canonical baseline).

| Date | Paper | Status |
|---|---|---|
| 2025-11-23 | [ADAM HIVE MATRIX V10](ADAM%20HIVE%20MATRIX%20V10_251123_224308.pdf) | **Current canonical** baseline of the hive-mesh architecture. |
| 2025-11-20 | [ADAM HIVE MATRIX v11](ADAM%20HIVE%20MATRIX%20v11_251120_020459.pdf) | Pre-canonical revision (most recent before V10). |
| 2025-11-20 | [ADAM HIVE MATRIX v2](ADAM%20HIVE%20MATRIX%20v2_251120_005348.pdf) | Early second pass. |
| 2025-11-20 | [ADAM HIVE MATRIX v1](ADAM%20HIVE%20MATRIX%20v1_251120_004907.pdf) | Original conception. |

> **For a single read:** start with **V10** (canonical) and refer back to v1 only if you want the design history.

These papers describe the agent-cascade architecture that the repo implements in code (see `src/snell_vern_matrix/` for the runnable side). The `mesh.dispatch()` entry-point in code corresponds directly to the dispatcher described in the V10 paper.
