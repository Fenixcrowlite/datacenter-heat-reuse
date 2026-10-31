# HANDOFF | A37 DCHR N−1 IT thermal replay | 2026-10-26

Scope: isolated directory only. Existing Synapse task `scc-3d9d172beb6e1b` (review); no new task or worker.

## Live admission snapshot
2026-10-26 10:23 CET: SynapseMCP Web ping ONLINE/control_enabled; host DESKTOP-M9L3I4M; RAM free 1.971 GiB / total 15.823 GiB; GPU 1834/8188 MiB, utilization 5%; 361 git worktrees; SQLite quick_check=ok, 209 tasks, 0 running registry tasks. STOP/PAUSE absent from seven checked root locations; NOT a claim of exhaustive recursive scan. SCADA PID 5264, FUXA PID 16288, MATLAB bridge PID 6124; no services or peers touched. Desktop Commander monthly quota exhausted; used primary SynapseMCP Web only. VRS skipped; no Codex/GPU worker started.

## Verified artifact
`thermal_n1.py`: source-backed thermal inertia + reject A/B + bounded hypothetical IT curtailment.
`run_a37.py`: 12 cases x 672 rows from verified v08/A36 sources.
`test_a37.py`: 16/16 PASS.
`independent_qa.py`: Decimal independent QA 8064 steps / 104832 checks PASS, 4 crosschecks against A36B.
`RESULTS_A37.json`: case metrics and SHA for each trace.
`DCHR_A37_THERMAL_RU.md`: derivation, limitations, results.
No physical release; scenario capacities and curtailment limits are not equipment ratings.

## Blockers and exact next action
1. Verify any STOP/ownership changes before work.
2. With MATLAB/Stateflow owner approval, port N−1 thermal recurrence to an isolated Simulink/Stateflow candidate, including TES SOC and control latency. Never modify the shared v85 SLX or live SCADA.
3. Obtain actual REJECT ratings, IT shedding capability, heat capacity, TES parameters and synchronized field data before physical validation.
4. Inspect `REGISTRY_RESULT.json` and `SHA256_MANIFEST.json` for evidence and event; no duplicate card creation.
