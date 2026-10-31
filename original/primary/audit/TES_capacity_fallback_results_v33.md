# v33: executed capacity fallback defect and sensitivity

UTC: 2026-10-10T02:42:41.191702+00:00. Checkpoint v33 executes the unchanged accepted model v32. MATLAB 16200/16200 assertions PASS over 25 scenarios, 310 intervals and 620 segment slots; maximum balance residual 3.3306691e-15 MWh. Independent equations: 643/643 PASS.

**Confirmed open controller defect:** when loss-replacement HP request falls below its assumed part-load COP cutoff, the capacity tail disables HP and TES discharge. Demand remains unmet although TES starts the tail at capacity above the delivery cutoff. At an initial capacity sample, the same unavailable HP permits discharge; that branch difference has executed evidence. These successful reproduction assertions establish a defect, not corrected-controller acceptance.

For the low-load unavailable-tail fixture (4 h, E0=9.9 MWh, D=3 MW, backup=.5 MW):

| Macro step (h) | End TES (MWh) | HP electricity (MWh) | Unmet (MWh) | HP availability changes |
|---:|---:|---:|---:|---:|
| 2 | 9.037117 | 1.696545 | 7.384494 | 3 |
| 1 | 9.420758 | 2.029663 | 6.870936 | 7 |
| 0.5 | 9.689321 | 2.236429 | 6.552172 | 15 |
| 0.25 | 9.843117 | 2.349239 | 6.378257 | 31 |
| 0.125 | 9.921425 | 2.405807 | 6.291047 | 63 |

Availability changes count adjacent ordered positive-duration HP states reconstructed from analytic segments; they are not measured compressor cycles or solver-clock transitions. Finer macro steps increase modeled switching and do not remove unmet demand in this fixture. Initial-capacity unmet varies non-monotonically over the tested steps (2.219359, 1.605507, 3.811313, 5.020353, 5.648135 MWh).

Controls: feasible modulation holds the tank at 10 MWh, with 4.460839839 MWh HP electricity and zero unmet across all five tested steps. Constant-COP source shortage at initial capacity gives E(4)=8.681280184 MWh and electricity 2/3 MWh across all steps. Passive cooling gives E(4)=6.703200460 MWh. Under fixed inputs, monotonic source extraction proves that reaching capacity with admitted high HP load cannot create a source shortage at a smaller admitted loss-replacement load; minimum-load unavailability and initial-state source shortage are distinct.

Independent QA categories: `{'actual_generic_oracle': {'passed': 34863, 'failed': 0}, 'alternate_targeted_recurrence': {'passed': 625, 'failed': 0}, 'static_saved_model': {'passed': 73, 'failed': 0}, 'artifact_runtime_preservation': {'passed': 24898, 'failed': 0}, 'synthetic_reviewer_checks': {'passed': 3, 'failed': 0}}`; zero failures. 941 unique earlier immutable entries retained. Separate MAT re-export binds table values/times/memory to saved SimulationOutput; SLX archive graph review binds the six-state chart and iterator. Synthetic corruption checks are separate from actual numeric checks.

Derived candidate only: assuming minimum ON/OFF .25 h and OFF TES delivery 3 MW, restart energy 8.827220821 MWh gives ON 0.667114809 h and OFF .25 h. RK4 independently checks both endpoints. See `TES_capacity_fallback_derivation_v33.md` for feasibility bounds, timing units and multi-event requirements. No new SLX or physical compressor policy is claimed.

Observed failed attempts preserved: sandbox MATLAB startup failed before model execution; local authorized retry passed. First reviewer used the obsolete nonhierarchical chart-name check; it was replaced with the accepted v32 completion reviewer. Second reviewer reached packaging but rejected relative-path handling; absolute paths were fixed. Both logs and original snapshots remain. Exact successful reviewer has its own timestamped QA source snapshot.

Evidence: `results\stateflow_fallback_v33_20261010T023623898Z`, `audit\Stateflow_fallback_QA_v33_20261010T023838_807159Z.json`, `audit\Stateflow_execution_v33_20261010T023605574Z.json`, `audit\Stateflow_fallback_sources_v33_20261010T024241_191718Z.json`.

Research candidates were discovered through search, but MDPI returned 429 and Elsevier redirected to an inaccessible page. No new article equation, dwell value or signoff adopted. Primary engineering documentation is distinguished from article evidence.

Remaining limitations:

- Checkpoint v33 executes unchanged saved model v32; no new SLX or corrected production controller.
- Capacity-tail TES-service defect remains open despite passing implementation/oracle assertions.
- Four-hour, five-family, five-timestep assumed sensitivity study; no universal optimizer or policy-superiority claim.
- Proposed hysteresis/dwell equations and RK4 example are not an executed Stateflow policy or calibrated equipment requirement.
- Iterator segments share macro solver time; physical-hour timers and seconds-based Stateflow temporal logic need explicit unit handling.
- Normal-mode host planner; standalone code generation, stratification, hydraulics, calibration and physical validation remain untested.
- v32 six-mode/fault acceptance inherited; v33 does not add equipment faults, cycling losses, delayed nonfinite faults or runtime corruption coverage.
- Independent algorithm/artifact QA is not separate human/agent review or paper replication; full primary signoffs remain 0/31.
- New research candidates were search-index discovery only; full-text retrieval failed and no equations/values were adopted.

Next: Implement additive Stateflow model v34 with persistent HP hysteresis/dwell latch, explicit physical-duration timers, TES service during HP OFF and a bounded multi-event integrator; test exact-capacity initialization, changing inputs, finite backup, cutoff safety, timer units and timestep partitions against the preserved v32 counterexample.
