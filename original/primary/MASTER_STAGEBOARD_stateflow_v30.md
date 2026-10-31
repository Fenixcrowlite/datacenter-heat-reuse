# v30: executed temperature-aware exact-flow Stateflow

PASS: 1334/1334 MATLAB assertions; 23 scenarios / 69 intervals / all six modes; 18/18 actual fault rejections. Independent equation QA 364/364 PASS; evidence QA counts {'actual_numeric': 3131, 'static_saved_model': 66, 'artifact_and_runtime_bindings': 2040, 'synthetic_reviewer_checks': 6}; zero failures.

Model: `matlab/simulink/DCHR_Dispatch_Stateflow_v30.slx`. Physical state is ambient-referenced sensible energy, with explicit heat capacity, temperature and delivery cutoff. Active held-power integration is exact under the stated constant-coefficient assumptions; endpoint powers are throttled before integration.

Evidence: `results/stateflow_v30_20261009T212727142Z`, `audit/Stateflow_independent_QA_v30_20261009T212925_625430Z.json`, `automation/logs/stateflow_acceptance_v30_local_20261009T212720326Z.log`. Derivation and primary-evidence boundary: `audit/TES_temperature_exact_flow_derivation_v30.md`. Actual v28/v30 charging and discharging comparisons confirm the predicted split bias over h=2,1,0.5,0.25 hours.

Reproduce: `matlab -batch "addpath('matlab','matlab/simulink'); outputDir=run_stateflow_acceptance_v30('audit/stateflow_spec_v30_20261009T212412_569508Z'); export_stateflow_mat_audit_v30(outputDir);"`, then `python -X utf8 audit/verify_stateflow_v30.py <fresh-result-directory>`. Builder refuses to overwrite the saved release.

- Exact solution is restricted to constant ambient/heat capacity/loss coefficient and uniformly held power. No stratification, hydraulic tank connections or measured calibration.
- Endpoint throttling is a conservative interval controller. No full-power cutoff/capacity event pulses; constrained dispatch can change with timestep.
- Condenser must support tank maximum and delivery must not exceed cutoff; reservoir proxies neglect approach temperatures and detailed exergy.
- Normal-mode host MATLAB HP calls; standalone generated code, sensor/equipment faults, hysteresis, dwell and cycling remain untested.
- Fault coverage is 12 finite domain, 2 delayed finite and 4 output-corruption cases. No full v29 fault-matrix claim for v30; delayed NaN/Inf timing is untested.
- Stateflow helper-output/parameter shadow warnings are retained in logs. Implementation acceptance does not establish physical validation or article replication.
- Sample at StopTime represents a complete following interval; timestamps are sample starts, not continuous event integration.
- Full primary source signoffs remain 0/31. Cadau article evidence inherited; EnergyPlus engineering documentation newly re-opened, no article results or parameter values adopted.

Next: Derive a full-power TES cutoff/capacity event controller and independently compare delivered heat against the uniform v30 policy at coarse/fine timesteps before adding another Stateflow version. Preserve v24/v28/v30.
