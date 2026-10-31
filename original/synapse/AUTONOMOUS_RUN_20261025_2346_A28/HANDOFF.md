# Synapse autonomous handoff | A28 | 2026-10-25 23:54 CET

## Admission, governance and live checks

Read the actual Windows files `NIGHT_HANDOFF_20261021.md`, `AGENTS.md`, `agent_knowledge/INDEX.md`, `skills/personal-assistant-kernel.md` v1.2, `registry-task-lifecycle.md`, `workstream-isolation.md`, `synapsemcp-web-concurrency.md`. Do not infer current state from old handoffs. Primary SynapseMCP Web ping returned ONLINE and control_enabled=true at 23:46:24 CET. Ordinary commands/writes executed serially through SynapseMCP Web. Desktop Commander was used only for initial policy reading, not development.

Live baseline: RAM free 3.58 GB; GPU 2526/8188 MiB, 34% utilization; 361 git worktrees; SQLite quick_check OK; 207 Synapse tasks; initial max event 1169. No root STOP/PAUSE found in initial checks. Existing Jarvice DevTeam PIDs 8860/35484, SCADA PID 5264, FUXA bridge PID 16288, MATLAB bridge 12692 and MATLAB 9076/27116. Shared Jarvice worktree has uncommitted changes; untouched.

Final resource snapshot `LIVE_FINAL_SNAPSHOT.json` at 23:53:57 CET: RAM free 3.391 GiB; GPU 2570/8188 MiB, 42%; 361 worktrees; same seven owner PIDs alive. Exact STOP/PAUSE name checks in five roots (9 names each) found zero flags; not a recursive guarantee.

## A28: calibrated paired residuals, not operational covariance

New isolated code: `field_calibration_gate.py` and 23 deterministic unit tests. It requires **matched reference readings** for flow, supply and return temperatures, enforces timestamp synchrony, monotonicity, sampling gaps, units, finite values, 12+ pairs and field certificate file hashes/declared expiry. Computes unbiased 3x3 sample covariance of measurement residuals, separate systematic biases, lag-1 autocorrelation diagnostic, and refuses to call synthetic data field evidence.

Why this matters: operational time-series covariance includes real process variation, so it cannot identify instrument-error covariance. Prior A26/A27 assumed correlations; this tool defines the data needed to estimate them. It does **not** certify metrological traceability or physical validity.

QA: Python compilation PASS; 23/23 unit tests PASS; 16/16 independent covariance and A27 PSD cross-checks PASS. CLI integration PASS with 32 explicitly synthetic paired readings. `FIELD_GATE_EVIDENCE.json` SHA256 `2bfec2d9a2330aeea1edf6b1afb535765db77417e4425267fa3c63863835c09b`. Decision: `SYNTHETIC_ONLY_NOT_FIELD_VERIFIED`, `release_allowed=false`. Slovak field measurement protocol included.

Existing Synapse DataCenter task `scc-3d9d172beb6e1b`, review/planned, received evidence event **1170**. No new card. Source, tests, report, independent QA, fixture, protocol and one-shot registration receipt are SHA256-pinned in `SHA256_MANIFEST.json`.

**QA defect caught on replay:** the original one-shot `register_a28.py` raised `REGISTRY_RESULT_CONFLICT` because its local receipt stores `action=CREATED_EVENT` while the next call reports `EXISTING_EVENT`. The SQLite event itself was not duplicated. The original file and historical event were left unchanged to preserve the manifest. New read-only `verify_a28_idempotency.py` compares stable event fields and manifest, and passed **twice** with event 1170 and count=1. For future registration code, ignore transient `action` when comparing a persisted receipt, but retain payload-conflict protection.

Read-only bounded search found `real_data_calibration_report.json` with NASA reanalysis, Eurostat prices and PUE benchmarks, but its own provenance states **no data-center IT telemetry** and does not provide paired flow/temperature sensor-reference calibration. Do not misclassify it as a field calibration certificate.

## Ownership and exact next step

No Codex session, GPU job, worker, card, public communication, payment, VRS work, shared GUI edit, OAuth/STOP change, production SCADA/MATLAB edit, peer process termination or Git commit/push.

**Next executable step:** find and independently authenticate actual field calibration certificates and time-synchronized sensor/reference triplets, convert into the documented A28 CSV+metadata contract in a new owned folder, run the gate and verify on an independent heat-meter holdout. If no field data exist, continue independent physical reference validation or another unblocked workstream; do not fabricate samples. A27 PSD production integration still needs owner-controlled review. EduMotion S04 dispatcher dedup remains ownership-blocked; do not deploy in another worker's scope.

This handoff documents only work completed in this invocation. Repeat live admission before the next run.
