# v22: executable Stateflow dispatch acceptance

PASS: actual MATLAB/Simulink/Stateflow execution across 10 scenarios, 39 intervals, all six modes. MATLAB 476/476 checks; independent actual-trace QA 2860 checks, 0 failures. Maximum interval first-law residual 7.77156117238e-16 MWh.

The chart's entry/during actions allocate actual TES, backup and unmet flows. Guarded initial routing and state transitions operate on current demand/HP/TES capacity; Unit Delay retains interval TES energy. Compared all 19 v16 output fields and loss residual with verified MATLAB dispatch; independent fixed-COP oracle covers 27 additional intervals.

Evidence: `results/stateflow_v22_20261009T025644993Z`, `audit/Stateflow_independent_QA_v22.md`, `audit/Stateflow_equations_review_v22.md`, timestamped logs, and generated versioned `.slx`. Existing v14 baseline and v21 evidence preserved.

Engineering-assumption implementation QA only. No paper replication/equipment validation; 0/31 primary signoffs. Host MATLAB HP calls limit this delivery to normal-mode simulation. Linear TES loss, absent hysteresis/fault/cycling/network physics, and nonfatal Stateflow local-parameter shadow warnings remain documented.

Next: Audit a primary-text TES standing-loss model and derive an exact/exponential reference with timestep convergence before extending Stateflow; preserve v22's declared loss-first linear-retention baseline. Faults/hysteresis remain later control work.

Reproduce actual simulation from the project root: `matlab -batch "addpath('matlab','matlab/simulink'); run_stateflow_acceptance_v22"`. The runner requires the existing versioned `.slx` and writes a new timestamped directory. Run `python audit/verify_stateflow_trace_v22.py --trace <new_directory>/stateflow_trace_v22.csv --report <new_directory>/stateflow_independent_qa_v22.json` afterward. The builder refuses to replace an existing versioned model.

This task uses distinct Stateflow checkpoint filenames because a concurrent run replaced the generic MASTER_STAGEBOARD_v22.md with a Stenberg research checkpoint. Both deliverables are preserved; the Stateflow result is recorded here.
