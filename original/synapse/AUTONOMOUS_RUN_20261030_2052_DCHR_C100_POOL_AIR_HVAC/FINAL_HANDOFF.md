# C100 finite-run handoff | 2026-10-30 20:56 CET

## Live intake and ownership
Primary SynapseMCP Web ping OK 20:51:14 CET, control_enabled=true. Read on Windows: NIGHT_HANDOFF_20261021.md, AGENTS.md, agent_knowledge/INDEX.md, personal-assistant-kernel v1.2, registry-task-lifecycle, workstream-isolation and synapsemcp-web-concurrency. Did not treat the 21 October handoff as live. Read-only process/worktree and scheduled task audit at 20:51:36 CET: Jarvice parent/child PIDs 32684->27020 and 12500->34364 preserved; existing Python SCADA and FUXA services preserved. Main Jarvice repo and peer worktrees not edited. No STOP/PAUSE in checked roots; task-local script checks STOP before writes and during runs. Free RAM 6.42 GB at preflight, 6498 MiB at 20:56:04; VRAM 1215/8188 MiB, GPU 0%. No new Codex, workers, GPU tasks, MATLAB, VRS, OAuth, GUI/browser, shared files, paid or external actions.

## Real C100 implementation
Task-local directory: this folder. New c100_air_hvac.py computes independent air-side moisture balance, dehumidification AND humidification mass, sensible HRV, dehumidifier electricity and bounded condenser-to-air heat credit. C88 synthetic outdoor temperature and C93 pool evaporation are SHA-pinned. 9 scenarios x 8760 hours = 78,840 rows. Water evaporation latent heat remains counted only in C93/C96 pool-water load, not twice in air heating.

Selected annual synthetic results: 263.67 tonnes evaporated; outdoor RH assumed 40/70/90% gives dehumidification 84.44/129.14/162.70 tonnes and humidification 139.08/100.47/77.99 tonnes. Ventilation sensible load before HRV 160.45 MWh; at 70% assumed outdoor RH and 50% HRV, external air heating 47.74 MWh and dehumidifier electricity 64.57 MWh. Humidifier energy, fan energy and cooling are excluded. This is NOT a validated building energy estimate.

## QA and provenance
Model selftests 13/13 PASS. Independent full-row arithmetic, energy/moisture balances, scenario summaries, monotonic checks and injected corruption controls: **1,419,217 assertions PASS** over 78,840 rows. Two initial QA defects fixed and original failure logs preserved: output rounding tolerance, and a negative RH control that checked dehumidification only during a humidification hour. Source model unchanged.
C100_AIR_HOURLY.csv.gz SHA256: 8ce8e04be652540eb635afb75958077c716220a26f3471526264985e0862fff4
C100_AIR_SUMMARY.csv SHA256: 16eea24a886be89157614a210495544c49433809885de470551f617bada6fe9a
SHA256_MANIFEST_C100.json SHA256: 8502c3d9c30768bc500220bfeb82e71b7c5bb19350e5760e9aa7fa6b29d08016
11/11 manifest file hashes independently verified on Windows; zero mismatch.
Synapse EXISTING DataCenter task scc-2aab24704c2bd0 evidence **#1460**, canonical receipt SHA256 dd491d25f618453a99da107fa9d86dea23bceea994b63c34441efddc6a276dd4; registry readback verified. Task status remains queued. 0/31 primary source signoffs.

## Exact next executable step
Measure/obtain hourly outside T and RH, actual air flow and indoor RH, HRV/frost/defrost and dehumidifier manufacturer curves. Quantify humidifier and fan electricity, cooling, and then couple air and pool-water loads through a single constrained thermal allocation without double-counting evaporation or condenser heat. Maintain all STOP/ownership gates. This run does not imply continuous work between scheduled invocations.
