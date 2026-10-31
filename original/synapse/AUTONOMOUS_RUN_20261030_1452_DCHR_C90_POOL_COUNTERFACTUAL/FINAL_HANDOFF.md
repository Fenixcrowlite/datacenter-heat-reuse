# Synapse C90 | DataCenter 500 m³ pool counterfactual | 2026-10-30 14:52–14:57 CET

## Live intake (not copied from old handoff)
Primary SynapseMCP Web ping at 14:52:36 CET: OK, control_enabled=true. Read actual NIGHT_HANDOFF_20261021.md, AGENTS.md, agent_knowledge/INDEX.md, personal-assistant-kernel v1.2, registry lifecycle, workstream isolation and serial RPC/OAuth rules. Checked STOP/PAUSE in Synapse root/recovery, DataCenter, EduMotion and Jarvice scopes: none found in tested flag set. Main Jarvice worktree dirty and peer-owned, untouched. DataCenter SCADA processes 5148, 12472, 14512 active, untouched. Existing Jarvice worker 27020 preserved. No Codex, MATLAB, GPU job, duplicate worker, GUI, OAuth, shared SLX, source repository or external side effects.

RAM free 6561 MiB at intake, 6502 MiB at 14:56:57; NVIDIA VRAM 1208 then 1210/8188 MiB, GPU 0%. This is an isolated, CPU-only workstream.

## Actual changes
Created task-local Python scripts and outputs under this directory. Input is the *unchanged* 8760-hour synthetic MATLAB R2026a C88 CSV pinned to SHA256:
`07d1d7f19d92ce34d5b3e5a44a2131234a4a2e7991e21f018b197137ed0eb370`.

Implemented 500 m³ pool heat load: evaporation with explicit assumed mass-transfer coefficient, makeup water, radiation, convection, envelope loss and a separate sensible ventilation demand. Six RH/cover/recovery scenarios, 52,560 hourly scenario rows and 72 monthly rows. Built a second independent time-aligned threshold/sensitivity analysis using the C88 `HX_Rejected_MW` *counterfactually*, with an assumed auxiliary HP COP=4 and 75 kW electric/300 kW heat caps.

Baseline covered pool: 262.10 MWh/year water heat, peak 52.07 kW; ventilation sensible heating separately 160.45 MWh/year. Uncovered pool 378.25 MWh/year; dry RH40 covered pool 354.09 MWh/year. In the synthetic counterfactual, minimum recoverable fraction of HX_Rejected for every hour: 19.51% water only, 30.45% water plus separate ventilation, 26.54% water only at RH40. At 25% recovery, covered pool water is fully met but water+air has 826 unmet hours.

**These are illustrative assumptions, not a physical validation or proof of actual recoverability.** No 31 primary-source signoffs, measured pool operation, dynamic water thermostat, temperature pinch, electrical tariff, hydraulic design or existing load allocation were established. The C89 82.261% non-gas heat share must not be confused with a DC-only or pool share.

## QA, hashes, evidence
- Python `-W error -m py_compile` PASS on all 4 scripts.
- Main model self-tests **8/8 PASS**.
- Independent base model QA **20/20 PASS**.
- Independent threshold QA **29/29 PASS**.
- Source pin, 8760 timestamps, 52,560 hourly rows, 72 monthly rows, heat/source conservation, source cap, cover/RH monotonicity and monthly/annual reconciliation checked.
- SHA manifest: `SHA256_MANIFEST_C90.json` SHA256 `35f8094145a09077a68da6c18a94dc1a4ea581bd4b6b73098359b8e59d21ef49`.
- Findings: `C90_FINDINGS.md`, detailed coefficients, limitations and numbers; hash is in manifest.
- Evidence `EVIDENCE_C90.json` SHA256 `4e3f6562c01f2bd085d638bd4b39e626921de0623f63095500af1d713c26cad3`.
- Existing Synapse card **scc-2aab24704c2bd0**, event **#1450**, receipt SHA256 `3efca7d3b7ea98c7e44a6df848b0d41e13a56abcca2ef85b13c460573ab8d83a`.
- Re-verified event with C62 idempotent evidence CLI: **VERIFIED_EXISTING**. Task remains `queued`, no worker PID.
- Card: https://desktop-m9l3i4m.taila1c6bd.ts.net/?synapse_task=scc-2aab24704c2bd0

## Exact next executable step
Independently source and validate the evaporation/mass-transfer and ventilation coefficients against credible standards and measured indoor pool datasets. Then model *measured incremental* recoverable `HX_Rejected` with source/sink temperature, pinch, COP, electrical and hydraulic constraints; add dynamic water-temperature thermostat and verify time-aligned 8760-hour dispatch. Keep source signoffs 0/31 until actually checked. Preserve all shared OneDrive/Simulink/SCADA files and ownership. EduMotion C70 voice approval and K3s production ownership remain blocked.

This handoff records one completed invocation, not continuous activity between scheduled runs.
