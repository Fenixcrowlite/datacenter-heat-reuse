# C114 FINAL_HANDOFF · 2026-10-31 Bratislava

## Live intake and ownership
Read Synapse NIGHT_HANDOFF_20261021.md, AGENTS.md, agent_knowledge/INDEX.md, personal Kernel v1.2, registry lifecycle, isolation and MCP concurrency skills. Live SynapseMCP Web ping 03:54:51 CET: OK, control_enabled=true. At 03:55:17, DESKTOP-M9L3I4M had 3988 MiB free RAM, GPU 1077/8188 MiB VRAM, 0% utilization. STOP/PAUSE absent from checked project roots. Jarvice/Synapse/SCADA/Preview owner processes observed; worktrees listed, not modified. Synapse SQLite quick_check OK; existing DataCenter task queued. No new Codex/worker/GPU job. VRS skipped.

## Actual work
Implemented isolated C114 capacity search using SHA-pinned C112/C111/C106/C104 model sources. Searched symmetric and independent asymmetric maximum dehumidification/humidification rates for an hourly endpoint RH band 45–65%, two annual 8760-hour policies, 0.01 kg/h brackets. Results: symmetric 45.6543 kg/h; asymmetric dehumidification 45.6543 kg/h and humidification 29.6973 kg/h (water-first) or 29.6875 kg/h (air-first). Joint annual RH band violations 0/8760 in each synthetic policy. No shared model or GUI changes.

## QA
21 C112 baseline tests PASS; C112 baseline 5/20/ideal capacity rows matched. Independent closed-form recurrence replayed **140,160** hourly reference steps with **94** numeric comparisons and **3** negative controls PASS. Initial QA mistakes (missing humidifier argument, Pa/kPa pressure mismatch) corrected before final pass. Model is synthetic, one-way, endpoint-only; source signoffs added 0/31, no physical validation.

## Artifacts and registry
- C114_ASYMMETRIC_CAPACITY.csv SHA256: fe27a033f3e075ea494bc2b0d1d89a6d79ed40ad2ea6e5b1c2744ac9534df574
- C114_CAPACITY_ENVELOPE.csv SHA256: 47ac8ff94c319ecdd4c9b5bfd6b34f30d79303e3e65919268de7a5ca74af426d
- SHA256_MANIFEST_C114.json SHA256: 34fa9d305b5e3d62445240e291dd73b6221c53b056324df04ac3c9a4387006cf
- Existing Synapse DataCenter task scc-2aab24704c2bd0: **evidence event 1474** written and read back; status remains queued. Canonical receipt SHA256: 56366a717b8d99224785f708af735b1525596e78bdd21bb7ba445722835ebbbf.

## Exact next step
Create an independently tested two-way RH → evaporation → latent heat → pool temperature and shared heat dispatch model, preserving hourly energy/moisture conservation and ideal-baseline regression. Before real hardware sizing, obtain room geometry, measured airflow and equipment curves. Do not treat synthetic capacity as vendor specification.
