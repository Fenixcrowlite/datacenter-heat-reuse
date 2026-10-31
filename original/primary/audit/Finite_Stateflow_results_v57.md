# Compiled finite-water Stateflow acceptance v57

UTC 2026-10-11T11:27:40.637680+00:00. **Scoped v57 acceptance; continuous coupling remains OPEN.**

New saved actual model: `matlab/simulink/DCHR_Dispatch_Stateflow_v57.slx`.
Six guarded thermal modes and persistent HP supervisor execute 66
intervals / 78 positive segments / 13 scenarios.
Compiled water/refrigerant boundary and executed-flow/auxiliary accounting are new.
MATLAB 328/0; twelve runtime fault rejections including
two valid samples before delayed rejection; six verified v30 physical comparisons.
Independent QA 10972/0; 7 separate mutations;
18 certified latch changes; 31 macro mode changes;
220634 original binary64 values / 20 MATs.

Boundary inputs are held within each macro interval. Tank capacity/cutoff are fixed.
No continuously energy-linked condenser, bounded variable-power charge propagator,
equipment calibration, article replication or measured physical validation accepted.
The v56 endpoint blocker remains OPEN. All prior source/model/data hashes preserved.

Results: `audit/Finite_Stateflow_results_v57.md`; immutable evidence: `results/stateflow_finite_v57_20261011T112552_825681Z`.
Next actionable task: Resolve the still-open v56 coupled event-endpoint prerequisite: bounded-error propagation and compressor/source energy integrals for all ten charge regimes, plus an explicit one-sided branch/limiter equality protocol. Then build an additive continuously tank-linked Stateflow version preserving v57 compiled water/auxiliary guards, cutoff/restart/dwell and exact padding/handoff; execute six modes, fault/reference tests and independent original-MAT/equation QA. Preserve v52-v57. Primary equipment calibration remains OPEN; do not repeat unchanged annual matrices.

## Actual saved-model scenarios

| Case | Intervals | Positive segments | Modes |
|---|---:|---:|---|
| zero_demand | 1 | 1 | 0 |
| hp_only | 1 | 1 | 1 |
| tes_charge | 1 | 1 | 2 |
| tes_discharge | 1 | 1 | 3 |
| boiler_limit | 1 | 1 | 4 |
| insufficient_heat | 1 | 1 | 5 |
| approach_zero | 1 | 1 | 4 |
| approach_ten | 1 | 1 | 4 |
| hot_flow_limit | 1 | 1 | 5 |
| source_flow_limit | 1 | 1 | 5 |
| sequence | 24 | 28 | 2,3,4,5 |
| changing_water | 8 | 9 | 2,3,4,5 |
| capacity_dwell | 24 | 31 | 0,2,3,4 |

Numeric traces: `results/stateflow_finite_v57_20261011T112552_825681Z/numeric_traces_v57_20261011T112723_295344Z.csv`.

## Scope and limitations

- v57 accepts a compiled finite-water boundary held per macro interval. It is not continuous tank-temperature/condenser coupling; the v56 exact branch/limiter endpoint blocker remains OPEN.
- Synthetic variable-flow feasibility constraints, fixed saturation temperatures per interval, external fully rejected proportional auxiliary electricity. No finite UA, hydraulics, minimum-flow/standby law, equipment map or measured validation.
- Tank capacity, ambient reference and cutoff remain fixed per run. New boundary rejects attempts to redefine tank/cutoff or credit auxiliary heat; source/hot axes may change only at macro boundaries.
- Inherited host extrinsic planner and bounded 64 segment slots execute in normal mode. Standalone generated-code deployment and universal numerical-domain proof are untested.
- Inherited canonical positive endpoint normalization uses 64 ULPs; independent 80-digit comparisons use the existing 72-ULP equation allowance. Zero-span padding and energy/memory handoff are exact.
- Independent QA uses separately programmed Decimal/Fraction equations and original-MAT binary64 exports by the same agent, not independent personnel.
- Stateflow license, two actual charts and executable simulation observed; version list is empty and no installed-version claim is made. Legacy sfroot is Simulink.Root; inherited shadow warnings remain.
- Six v30 physical-output comparisons exclude only attempted-request diagnostic column 22 when the HP latch is OFF. No unchanged annual policy matrix was rerun.
- No primary literature retrieved in this run; inherited full signoffs remain 0/31. No article replication or physical calibration accepted.
- Initial sandbox startup failure, two incorrect harness sfroot-type assumptions, two reviewer Decimal-type exceptions and two source-snapshot mismatches are preserved in earlier timestamped evidence. Final acceptance uses a fresh complete source snapshot.
