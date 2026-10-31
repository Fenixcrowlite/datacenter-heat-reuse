# Executed Stateflow energy pre-commit monitor v78

UTC 2026-10-13T05:23:44.568086+00:00. Actual saved v78 Stateflow model executes all six required modes.
MATLAB 77 PASS / 0 FAIL; independent numeric/artifact QA
21999 PASS / 0 FAIL; 16 separate reviewer self-checks.
Supplementary exact rational capacity QA: 1293 PASS / 0 FAIL,
with three separate boundary self-checks and no tolerance shared between MW and MWh.
13 schedules / 133 held intervals / 149 positive segments /
16 interior events, including stop, cutoff and restart.
Every trace double matches fresh saved-v77 execution on the same inputs.

16 isolated energy corruptions are accepted by the unsaved v77
temporal-monitor copy and rejected by the v78 energy monitor at the expected
runtime assertion. Exact monitor-bypass traces prove every injected field was
reached. Instrumented chart copies are never saved. Clean v78 is reopened and
rerun after instrumentation. The embedded v75 thermal kernel is unchanged.

The new monitor binds port limits/allocation, TES bounds, forcing, port energies,
efficiency/auxiliary losses, segment offsets, interval and cumulative totals,
initial inventory and both first-law residuals before emission and commit.
It calls the preserved v77 temporal monitor. Trace schema 75 and reporting API
0.76 remain compatible.

Saved model `matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v78.slx` SHA256 `cfd8eadca5d5a6c7dd6da6a20ee7f32e43cafd0084e3c0bd6453179bff184be9`.
Evidence `results/energy_commit_v78_20261013T050754_608388Z` contains timestamped MATLAB batch logs and receipts, Simulink
diagnostics, original/reopened MAT, binary exports, closed-form numeric CSV,
runtime fault logs, source snapshots and preservation hashes.
Compiler warnings that the energy monitor is unused arise in deliberate
monitor-bypass copies; the saved model retains every pre-commit call.

The unfinished earlier v78 attempt had no saved model or acceptance evidence. Its
harness incorrectly selected v78 as its own comparison model; this run repairs
that selector to v77 and retains a pre-edit snapshot. The restricted-startup
failure is retained in the evidence; only successful actual executions count.
The draft energy reviewer uses a power-ulp slack in its TES bound check.
The mandatory supplementary reviewer directly compares every actual TES hull
against exact C*(Tmax-Ta) in MWh, and checks all power limits separately in MW.
Thus acceptance does not depend on that dimensionally misplaced draft slack.

Limitations:
- Synthetic bounded normal-mode schedules only; no annual, calibrated equipment, primary article replication, measured physical validation or generated-code acceptance. Full primary signoffs remain 0/31.
- Same-agent algorithmic independence: Python Fraction operand equations and separate 120/160-digit closed exp/log trajectories call no production MATLAB solver. MAT binary exports depend on MATLAB reopening; no independent personnel or HDF5-reader claim.
- Thermal kernel, policy, trace schema 75 and reporting API 0.76 are unchanged. The monitor checks candidate consistency before emission and commit, not authentication against coordinated internally consistent replacement.
- HP source/work overlap is a necessary balance condition, not a physical COP proof. Standing losses and nonlinear event/dwell feasibility require the separate closed-form QA lane. Inherited finite span, clock, collision and segment-budget domains remain.
- Fault controls instrument unsaved chart copies after kernel evaluation. They are exact isolated output-corruption witnesses, never physical plant trajectories.

Next actionable task: Resume primary equipment-map evidence and boundary audit from audit/HP_upstream_boundary_results_v44.md. Seek accessible primary text and performance-correlation supplement for DOI 10.1016/j.tsep.2025.103513; distinguish verified equations, coefficients and domains from metadata and access blockers. Trace refrigerant/water and compressor/auxiliary boundaries before a calibrated backend. Preserve accepted v75-v78 artifacts.
