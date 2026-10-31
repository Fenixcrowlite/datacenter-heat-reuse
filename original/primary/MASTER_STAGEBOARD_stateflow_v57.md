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
