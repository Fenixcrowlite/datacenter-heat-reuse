# C120 FINAL_HANDOFF | 2026-10-31 06:58 CET

## Intake / live ownership
Read NIGHT_HANDOFF_20261021.md, AGENTS.md, agent_knowledge/INDEX.md, personal-assistant-kernel v1.2, registry lifecycle, workstream isolation and SynapseMCP Web concurrency. Live primary SynapseMCP Web ping at 06:53:24 CET OK, control_enabled=true. RAM free 3943 MiB and VRAM 1206/8188 MiB (GPU 0%) at 06:57:46 CET. STOP/PAUSE checked in Synapse/temp_coding/EduMotion and own scope: absent. Existing Jarvice workers, Ollama, OAuth, Git worktrees untouched. No Codex sessions, GPU tasks, persistent workers, shared GUI, MATLAB/SCADA, VRS, secret or external writes.

## Real change
Standalone 15-minute dehumidification controller comparison in isolated scope. Read-only SHA-pinned C116/C106/C104/C118; 16 annual synthetic variants, 140160 hourly rows and 560640 quarter-hour transitions. Four modes: legacy_fixed, fixed_capped, feedback_capped, predictive_capped. Two evaporation patterns, two original C116 control policies. Actual source and data in this folder; no shared files changed.

## Findings
For water_first/ideal/front_loaded, hidden >65% RH hours: legacy_fixed 4745, fixed_capped 4745, feedback_capped 4745, predictive_capped 4293. Quarter-hour threshold violations: 5110, 5336, 7919, 6295 respectively. Naive feedback worsened violation count; perfect-knowledge target calculation did not minimize all metrics. See C120_FINDINGS.md. No vendor-sizing or field-validation claims.

## QA and evidence
- Output C120_QUARTER_CONTROL.csv.gz SHA256: 8eddd1fcd5d5a456deaf4dd8994c38b063089dd0a405dae1e43761ace19b0f4c.
- 7 selftests, 140160 mass closure checks, 35040 C118 six-field regression comparisons, 105120 capacity checks, 16 summary checks, 4 source SHA pins, 5 negative controls: PASS.
- Manifest 8/8 PASS; SHA256_MANIFEST_C120.json SHA256: b42b6b6334b2362192951df518bc4ae1c0c83e30e087820200fddb129781cc28.
- Existing Synapse task scc-2aab24704c2bd0 evidence event 1480 written and read back; status queued. Registry SQLite quick_check ok.
- First finalizer attempt failed because PowerShell UTF8 Set-Content added BOM to owned metadata. Rewrote only owned files with UTF8 no BOM, reran finalizer successfully; regression data unchanged. This failure is documented rather than concealed.

## Blockers and exact next step
The model uses fixed 29 C air, no temperature/enthalpy dynamics or equipment response delay, synthetic evaporation pulses and no physical calibration; primary-source signoffs remain 0/31. Next independent engineering scope: implement coupled quarter-hour dry-air sensible/latent enthalpy balance with explicit thermal capacity, sensor delay and actuator lag; test both moisture and energy closure against independent numerical integration, then optimize RH/energy/switching tradeoff. Keep existing data and shared runtime immutable. EduMotion genuine mobile review remains a human-only gate; do not fabricate a receipt.