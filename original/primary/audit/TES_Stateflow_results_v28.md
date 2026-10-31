# v28 executed Stateflow storage comparison

UTC 2026-10-09T15:35:08.918445+00:00. PASS: 1221/1221 MATLAB dispatch assertions, 105 experiment assertions, 46 domain rejections and 14575 independent evidence checks. 1039 separate reviewer self-tests are not simulation evidence. Executed 19 scenarios/70 intervals and all six modes; maximum system residual 1.84574577844e-15 MWh. Saved v24 is unchanged.

The new production parameter is `storage.continuous_loss_rate_per_h` (h^-1). v28 replaces passive linear retention with exp(-lambda*dt), while preserving loss-first port allocation. Primary text review, independent RK4 derivation, units and the usable-energy offset defect are recorded in [TES_standing_loss_primary_v28.md](TES_standing_loss_primary_v28.md). The result is implementation acceptance of an explicit reduced assumption.

Actual v24/v28 comparisons use the explicitly converted legacy fraction `(1-exp(-lambda*dt))/dt` for parity. A separate sensitivity compares both methods at the same numerical coefficient .04/h for a 24 h synthetic horizon. Passive exponential results agree with the exact semigroup. Active charging still overestimates simultaneous continuous energy; refinement reduces that error. These are not observed tank parameters.

|Case|Scheme|dt (h)|Terminal (MWh)|Continuous exact (MWh)|Absolute error (MWh)|
|---|---|---:|---:|---:|---:|
|passive|linear_loss_first|4|3.51298032|3.82892886|0.315948544|
|passive|linear_loss_first|2|3.67666388|3.82892886|0.152264983|
|passive|linear_loss_first|1|3.75413247|3.82892886|0.0747963925|
|passive|linear_loss_first|0.5|3.79185423|3.82892886|0.0370746314|
|passive|linear_loss_first|0.25|3.81047118|3.82892886|0.0184576787|
|passive|exponential_loss_first|4|3.82892886|3.82892886|4.4408921e-16|
|passive|exponential_loss_first|2|3.82892886|3.82892886|4.4408921e-16|
|passive|exponential_loss_first|1|3.82892886|3.82892886|2.22044605e-15|
|passive|exponential_loss_first|0.5|3.82892886|3.82892886|1.0658141e-14|
|passive|exponential_loss_first|0.25|3.82892886|3.82892886|2.30926389e-14|
|constant_charge|linear_loss_first|4|16.2175492|15.4276779|0.789871359|
|constant_charge|linear_loss_first|2|15.8083403|15.4276779|0.380662458|
|constant_charge|linear_loss_first|1|15.6146688|15.4276779|0.186990981|
|constant_charge|linear_loss_first|0.5|15.5203644|15.4276779|0.0926865786|
|constant_charge|linear_loss_first|0.25|15.473822|15.4276779|0.0461441968|
|constant_charge|exponential_loss_first|4|16.6947904|15.4276779|1.26711257|
|constant_charge|exponential_loss_first|2|16.0530122|15.4276779|0.625334331|
|constant_charge|exponential_loss_first|1|15.7382884|15.4276779|0.310610526|
|constant_charge|exponential_loss_first|0.5|15.5824689|15.4276779|0.154791031|
|constant_charge|exponential_loss_first|0.25|15.5049448|15.4276779|0.077266953|

Evidence: `results/stateflow_v28_20261009T152826319Z`, independent QA `results/stateflow_v28_20261009T152826319Z/independent_qa_v28_20261009T153203999Z.json`, batch log `automation/logs/stateflow_acceptance_v28_resume_local_20261009T152810989Z.log`. Earlier v28 primary-text/derivation evidence and the saved model were inherited from unfinished work. The first earlier acceptance failed on the final rejection's mixed-cell JSON setup; its repaired rerun stopped without a summary and its interruption cause is unverified. This run preserved both attempts, retained a fresh sandbox startup failure, and completed a fresh automatically approved local MATLAB acceptance. Independent QA now requires every supplemental scenario interval and separates both synthetic self-test sections from actual evidence.

- Exponential retention is exact only for passive constant-coefficient zero-equilibrium/ambient-referenced energy.
- Active ports retain loss-first splitting; fresh charge loses no standing heat in its current interval. First-order timestep error is measured.
- Usable energy above a delivery temperature cutoff requires an ambient offset and cutoff events; current scalar model has no temperature state.
- New continuous_loss_rate_per_h is a rate coefficient, not a measured hourly fractional loss. All sensitivity parameters are scenario assumptions.
- Cadau primary Eq (4) is partially verified; its implementation has at least two nodes. No article reproduction or equipment calibration.
- Normal-mode host MATLAB HP adapter; standalone code generation, equipment faults, hysteresis/dwell, sensors and hydraulic/network/fuel/auxiliary models remain untested.
- Variable part-load v18 scenarios have reference/equivalent-baseline parity and independently checked laws; closed-form output predictions cover fixed-COP cases.
- v26 monitor-corruption and v27 delayed fault tests were executed on v24; they are not rerun evidence for v28.
- Nonfatal Stateflow allocator-output shadow warnings remain in v24/v28 execution logs.
- No measured-system physical validation; full primary signoffs remain 0/31.

Next: Derive and independently test a temperature/cutoff-aware TES model with the ambient-loss offset and exact constant-flow integration; specify saturation/cutoff events before a new Stateflow version. Preserve v24 and v28 baselines.
