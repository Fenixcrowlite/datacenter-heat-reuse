# v28 Stateflow exponential standing-loss acceptance

PASS: 1221/1221 MATLAB assertions, 105 experiment assertions, 46/46 actual domain rejections, 14575 independent evidence checks and 1039 separate reviewer self-tests. New saved model `matlab/simulink/DCHR_Dispatch_Stateflow_v28.slx` executed all six modes. v24 and previous evidence preserved.

Results and caveats: `audit/TES_Stateflow_results_v28.md`. Primary equation/units/offset audit: `audit/TES_standing_loss_primary_v28.md`. Exact passive decay; active loss-first splitting remains approximate. No source replication, calibrated equipment or measured-system validation; signoffs 0/31.

Evidence: `results/stateflow_v28_20261009T152826319Z`, `results/stateflow_v28_20261009T152826319Z/independent_qa_v28_20261009T153203999Z.json`, `automation/logs/stateflow_acceptance_v28_resume_local_20261009T152810989Z.log`.

Reproduce: `matlab -batch "addpath('matlab','matlab/simulink'); run_stateflow_acceptance_v28;"`. Builder refuses an existing versioned model. Run `audit/verify_stateflow_trace_v28.py --help` for independent trace/experiment/model/domain QA.

Next: Derive and independently test a temperature/cutoff-aware TES model with the ambient-loss offset and exact constant-flow integration; specify saturation/cutoff events before a new Stateflow version. Preserve v24 and v28 baselines.
