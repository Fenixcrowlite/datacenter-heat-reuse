# Executed Stateflow constitutive standing loss v80

UTC 2026-10-13T05:55:02.799332+00:00. New saved v80 Stateflow actually executes all six required modes.
MATLAB 65 PASS / 0 FAIL; independent actual equation/artifact
QA 26696 PASS / 0 FAIL; exact MW/MWh capacity QA
1509 PASS / 0 FAIL. Separate reviewer self-checks:
22 PASS, including a wide loss hull overlap scope witness.

37 schedules / 157 held intervals / 173 positive segments /
16 interior events (stop/cutoff/restart). Twelve passive variants exercise
lambda=0/.01/.5/1 h^-1 and initial inventory=0/3/9 MWh, including lambda*dt=1.
Every valid trace double matches fresh saved-v79 execution on the same inputs.
The saved v75 thermal kernel, policy, trace schema and reporting API are unchanged.

The v79 monitor accepts four energy-balanced but constitutively impossible
passive records. v80 rejects each at the expected standing-loss assertion
before emission/commit. Exact bypass traces prove changed endpoint/loss/copy
fields reached output. Independent closed equations separately reject all four
controls. No corrupt chart is saved; clean v80 is reopened and rerun afterwards.

| Control | lambda (h^-1) | duration (h) | initial (MWh) | injected end (MWh) | injected loss (MWh) |
|---|---:|---:|---:|---:|---:|
| invented_loss_zero_lambda | 0 | 1 | 3 | 2 | 1 |
| suppressed_positive_decay | 0.5 | 1 | 3 | 3 | 0 |
| excess_positive_decay | 0.01 | 1 | 3 | 2 | 1 |
| deficient_positive_decay | 0.5 | 1 | 3 | 2.875 | 0.125 |


For held E'=B-lambda*E, monotonicity bounds integral(lambda E dt) by
lambda*duration*[minimum endpoint inventory, maximum endpoint inventory].
Zero lambda requires exact zero standing loss. The runtime check calls no
thermal flow, exponential, root finder or quadrature routine. Exact Fraction
operand QA and independent 120/160-digit exp/log trajectories verify original-MAT
binary exports, conservation, source/work/loss/service, reporting and temporal links.
The separate capacity reviewer keeps MW and MWh bounds distinct without slack.

Saved model `matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v80.slx` SHA256 `f7032682f4d6c338a99f1425311a807254c3022ba8527dba5f616f53b0ac66be`.
Evidence `results/standing_loss_v80_20261013T054910_671296Z` contains timestamped MATLAB logs and execution receipts,
Simulink diagnostics, original/reopened MAT, binary exports, numeric CSV,
all runtime fault logs, source snapshots and preservation hashes.
Restricted-startup failure is retained; only successful actual batches count.
Compiler unused-monitor warnings arise in deliberate unsaved bypass charts.

Limitations:
- Necessary standing-loss overlap bound only; wide or internally consistent wrong hulls can pass. Endpoint monotonicity follows from the assumed held reduced ODE; no complete nonlinear/event/dwell trajectory certification by this gate.
- Unchanged engineering TES and HP assumptions, thermal kernel, policy, trace schema 75 and reporting API 0.76. No primary replication, measured validation, equipment calibration, annual or generated-code acceptance; full primary signoffs 0/31.
- Same-agent algorithmic independence: exact Fraction operand bounds and separate 120/160-digit closed exp/log QA call no production MATLAB solver. Binary exports depend on MATLAB reopening original MAT; no independent personnel or independent MAT-parser claim.
- Bounded synthetic normal-mode schedules. Inherited finite span, clock, event collision and segment-budget refusals remain; the added positive multiplication rejects nonfinite loss bounds.
- Four coordinated post-kernel record faults use unsaved in-memory charts and are QA controls, never physical plant simulation results. Accepted SLX is reopened clean after instrumentation.

Next actionable task: Resume primary equipment-map evidence and boundary audit from audit/HP_upstream_boundary_results_v44.md. Seek primary text and performance-correlation supplement for DOI 10.1016/j.tsep.2025.103513; distinguish verified coefficients and domains from metadata and access blockers. Trace refrigerant/water and compressor/auxiliary boundaries before a calibrated backend. Preserve v75-v80 model acceptance and independent nonlinear QA.
