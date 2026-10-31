# C96 | DataCenter UA/NTU and pump energy | verified 2026-10-30 18:55 CET

## Live intake
Primary SynapseMCP Web ping OK at 18:45:49 and 18:54:43 CET. Read historical NIGHT_HANDOFF_20261021.md, current AGENTS.md, agent_knowledge/INDEX.md, personal-assistant-kernel v1.2, registry-task-lifecycle, workstream-isolation, synapsemcp-web-concurrency. No fallback transport. STOP/PAUSE absent in bounded roots at preflight and 18:54:56 final audit. Live resources at 18:54:56: 6522 MiB RAM free; VRAM 1221/8188 MiB, GPU 0%. SQLite quick_check ok. Jarvice PIDs 32684 -> 27020 and 12500 -> 34364 preserved; Jarvice main worktree has at least 6 tracked uncommitted entries, untouched.

## Actual implementation
Task-local C96 directory contains c96_ua_ntu_pool.py, independent QA, 227760-row compressed hourly data, 26-row summary, metadata, findings, logs and SHA manifest. Source C93 script SHA 0686860f25ac42735bdecf9b896278e093177dc8062426f7cd232d232e48d923 pinned; upstream C90 pinned transitively.

Counterflow exchanger epsilon-NTU with finite hot/cold heat capacities, source outlet floor, source rejected-heat cap, assumed COP scenarios, electric/thermal HP limits, pressure-drop pump electricity and 8760-hour pool thermostat. 26 scenarios across 35 C baseline and 38/50 C sensitivity, hot flow 0.5/2 kg/s, UA 2/10 kW/K, COP 2.2/4.0, plus two backup cases. All are synthetic scenarios. None proves physical feasibility.

## Evidence
C96_HOURLY.csv.gz SHA256: 12adf23a7d8b4c9096ed0a091660e6406ac6ff8088955cb90da764539deb2b88
C96_SUMMARY.csv SHA256: e0cc2cf68bb6e38a627d8b22b00cadf9909bfbb0d54a56d3c9069f9bf982370f
SHA256_MANIFEST_C96.json SHA256: 66d6582e6ab3572cf426eed89e80ff4cd57952208ef173eedd7d30f9e7896bb4
Independent QA: 227760/227760 hourly rows, 26/26 scenario totals, 12/12 independent LMTD checks, corruption negative control PASS; 16/16 model selftests PASS.
Observed: all 26 scenarios maintained >27.5 C, pump electric 0.284-1.107 MWh/year. Selected UA grid did NOT locate failure threshold. Source temperatures/flows, UA, COP and pump pressure assumptions are NOT field data.
Existing DataCenter Synapse task scc-2aab24704c2bd0: evidence event #1456, read-back verified, task remains queued. No new card, worker, GPU job, Codex, shared MATLAB/Simulink/SCADA edits, OAuth changes, expenses or VRS work.

## Exact next step
In separate task-local C98: sweep UA below 2 kW/K and cold-loop temperature/flow to identify actual synthetic failure boundary, then seek measured source temperature/flow and vendor COP/pressure curves. Preserve original baseline 35 C separately from 38-50 C uncertainty. Add ventilation/dehumidification, and do not mark any of the 31 catalog sources signed off without primary-source review (currently 0/31).
