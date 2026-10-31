# Conservative electrical-ceiling Stateflow acceptance v83

UTC 2026-10-13T10:44:53.619681+00:00.

New actual saved model `matlab/simulink/DCHR_Electrical_Dispatch_Stateflow_v83r2.slx` executes 25 schedules / 42 held intervals / 53 positive segments / 11 interior events and all six required modes. MATLAB 113 PASS / 0 FAIL; independent equation/artifact QA 9674 PASS / 0 FAIL; 3 separate reviewer corruptions detected. Four actual saved-chart runtime refusals include a delayed nonbinding raw-rating change. 7 fresh saved-v80 reference comparisons are bitwise equal. The clean saved v83 model is reopened and replayed bitwise.

The chart transforms an explicit finite compressor ceiling into a conservative heat-output ceiling using an outward enclosure of the existing tank-capacity guard. The first candidate is preserved; accepted model release is v83r2. Exact rational QA proves the selected heat rate respects the compressor rating throughout every accepted segment, including hot tank and repeated stop/restart histories. Zero rating produces exact zero HP heat and compressor work. Existing source, water, thermal, TES, dwell and energy guards remain embedded.

| Initial TES (MWh) | Approaches evap/cond (K) | Compressor ceiling (MW) | Effective heat cap (MW) | Delivered service hull (MWh) | Compressor energy hull (MWh) |
|---|---|---:|---:|---|---|
| 3 | 1/1 | 0.05 | 0.2216761364 | [0.1108380681818175, 0.11083806818181761] | [0.01238232130209914, 0.012382321302099401] |
| 3 | 10/10 | 0.05 | 0.1682056452 | [0.08410282258064472, 0.08410282258064483] | [0.016951134062284226, 0.016951134062284545] |
| 8.5 | 1/1 | 0.05 | 0.2216761364 | [0.1108380681818175, 0.11083806818181761] | [0.021516160851772013, 0.021518499182792247] |
| 8.5 | 10/10 | 0.05 | 0.1682056452 | [0.08410282258064472, 0.08410282258064483] | [0.022762248575755217, 0.022764009757021562] |

Model SHA256 `6c3923c30e7058ec07e8d6f1667a5b9aae4db012775cba52bb0fb8d9cd98e1dd`. Evidence `results/electrical_ceiling_v83r2_20261013T104142_686092Z` contains timestamped MATLAB/Simulink and independent Python logs, execution receipt, original and reopened MAT, trace/certificate binary exports, numeric CSV, specification, sealed source snapshots, preservation hashes and fault logs. Prior attempted sources and logs remain separately linked in prior_attempts.json. No new primary article content was acquired or claimed. Derivation: `audit/Electrical_ceiling_derivation_v83.md`.

Limitations:

- Conservative global maximum-temperature cap, not a maximal instantaneous electrical limiter. Colder operation can leave compressor capacity unused.
- Synthetic compressor rating/constant cooling-factor reduction only; no acquired equipment supplement, calibration, article replication, measured physical validation, annual or generated-code acceptance. Full primary signoffs remain 0/31.
- Compressor electricity alone is limited. Configured auxiliary electricity remains separate and can make total external electricity exceed the compressor rating.
- The raw 26-operand policy is immutable within a schedule. Negative/nonfinite ceilings, invalid axes, nonfinite intermediate arithmetic and inherited span/clock/event-collision/segment-count domains reject.
- Trace schema 75 binds the effective 25-operand policy; separate certificate output binds raw electrical policy plus effective cap. Reporter v76 is preserved and does not itself authenticate raw electrical inputs.
- Same-agent independent exact Fraction and 120/160-digit closed exp/log algorithms call no production MATLAB solver. MATLAB reopens MAT for binary export; no independent personnel or independent MAT parser claim.
- Saved model executes analytic physical segments inside macro protocol ticks, not at solver-clock events. Tested bounded schedules do not establish arbitrary-input acceptance.
- Initial restricted MATLAB startup failure, builder quoting syntax error and first v83 candidate/proof-refinement evidence are retained in prior attempt evidence; only the successful corrected batch counts.

Next actionable task: Audit the conservatism of the new global-Tmax compressor ceiling against an independently derived temperature-conditioned electrical limiter on identical cold/hot and charging histories. Quantify foregone delivered service and source recovery before any new limiter implementation. Seek the reference62 primary equipment supplement/rating domain via a new accessible route; synthetic Pmax and constant cooling factor must not become equipment calibration. Preserve v80-v83.

Stop after this coherent executed deliverable and clear handoff.
