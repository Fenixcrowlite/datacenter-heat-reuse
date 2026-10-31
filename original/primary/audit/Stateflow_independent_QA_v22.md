# Independent Stateflow acceptance QA — v22

Reviewer lane: `/root/stateflow_qa`. Read `automation/STATEFLOW_ACCEPTANCE.md`, `STATUS_v21.json`, `MASTER_STAGEBOARD_v21.md`, `audit/research_frontier_2026_10_08.md`, v14 Simulink builder/validator, v14 HP, v16 TES/dispatch, v18 vectors and v19 parity evidence before writing new QA artifacts. No unrelated project, Jarvice, settings, runner or scheduler was accessed or modified.

## Baseline defect and acceptance boundary

The v14 builder creates an EMChart MATLAB Function with a hardcoded 2 MW backup limit and constant 6/8 MW potential/demand. The validator adds a disconnected Stateflow chart with `[true]`/`[false]` transitions. Compilation and a two-second simulation do not demonstrate demand-dependent dispatch, storage memory, finite backup handling or working state-dependent flow allocation. The v14 baseline remains preserved.

The new model must execute Stateflow and use its state actions to produce dispatch flows. Six modes use codes 0 IDLE, 1 HEAT_RECOVERY, 2 STORAGE_CHARGE, 3 STORAGE_DISCHARGE, 4 BACKUP, 5 UNMET_DEMAND. The chosen dominant-mode priority is unmet, backup, discharge, charge, recovery, idle. Lower-priority flows may coexist: BACKUP can include HP and TES delivery, while UNMET_DEMAND can include all available sources. This hierarchy must be reflected in actual numeric outputs, not inferred from a chart picture.

## Independent equations and scope

The separate oracle `verify_stateflow_trace_v22.py` imports no production MATLAB or earlier Python component/dispatch code. For fixed heating COP C > 1, the HP first law gives Q_source_used = Q_HP(1 - 1/C), so the source bound is Q_HP <= Q_source_available / (1 - 1/C). Feasible HP output is the minimum of that source bound, rated HP capacity and demand plus feasible TES charging headroom. HP electrical work is Q_HP/C. This analytical source bound independently checks the MATLAB v14 bisection on the zero-part-load-penalty subset.

TES uses the previously verified discrete engineering assumption: E_after = E_start(1 - lambda dt); E_next = E_after + eta_charge Q_charge dt - Q_discharge dt / eta_discharge. External-port limits and state energy bound each TES flow. The charging request includes only headroom remaining after standing loss. Backup useful output is bounded by its finite capacity; unmet demand is explicit.

The independently recomputed system closure is:

E_start + (Q_source_used + W_HP + Q_backup)dt = E_next + Q_supplied dt + L_standing + L_charge + L_discharge.

Standing loss is E_start lambda dt; charge loss is (1 - eta_charge)Q_charge dt; discharge loss is (1/eta_discharge - 1)Q_discharge dt. The verifier checks both this system closure and the TES port closure, plus each loss definition. Powers are MW, energies MWh, time hours.

Fixed polynomial COP = 4 at source/sink reservoir proxies 35/70 C, storage efficiencies, capacities and standing losses are explicit scenario assumptions. COP 4 is below the reservoir Carnot bound. These vectors do not validate physical equipment, primary-paper equations, a continuous TES leakage model, weather, economic performance, auxiliaries, cycling or faults. Linear standing retention remains time-step dependent; testing lambda dt = 1 establishes its discrete boundary behavior only.

## Independent vectors and verifier self-test evidence

`stateflow_qa_vectors_v22.csv` contains 27 intervals across seven scenarios and all 19 verified v16 output fields plus an independently calculated expected mode. Coverage includes all six modes, every step of a multi-mode trace, nonzero initial TES memory, full and zero-capacity stores, charging on zero demand when headroom exists, idle on zero demand when the store is full, complete standing loss, HP nameplate saturation, finite backup saturation, near-full charging headroom and exact emptying.

The original vector SHA-256 is `1e9aa2cbac88b2f967a675cc73594f2eb1c2dba0922a79d57b0936cbbfc95551`. Vector generation refuses to overwrite the CSV. Trace reports also refuse to overwrite existing evidence.

Self-test completed: 2266/2266 oracle-trace checks pass; 500 deterministic randomized algebraic and monotonicity cases pass (seed 22009; maximum absolute first-law residual 7.993605777301127e-15 MWh). Independent hand anchors include charging from 10 MWh to 11.75 MWh with 0.05 MWh standing loss and 0.2 MWh charge loss, and discharge from 10 MWh to 8.075 MWh with 0.375 MWh discharge loss. Four deliberately corrupted trace classes are rejected: mode, final TES energy, source extraction and backup heat.

The first mutation test exposed a defect in the QA verifier: converting a fractional mode to an integer could conceal malformed mode data. The verifier now requires exact integral modes and steps. The failing log is preserved at `automation/logs/stateflow_oracle_selftest_v22_20261009T025210752Z.log`; the corrected full self-test evidence is `audit/stateflow_oracle_selftest_v22_20261009T025503519Z.json` and its matching timestamped log. Self-testing synthetic oracle traces is not Stateflow execution evidence.

## Actual Stateflow execution gate — PASS

Actual MATLAB batch execution is evidenced in `automation/logs/stateflow_acceptance_v22_topology_20261009T045637.log` and `results/stateflow_v22_20261009T025644993Z/acceptance_summary_v22.json`. MATLAB R2026a Update 5 reports 476/476 checks passing over 10 scenarios and 39 intervals; the structure report records Stateflow license 1 and actual Simulink/Stateflow execution. The final trace uses the generated `matlab/simulink/DCHR_Dispatch_Stateflow_v22.slx`; the v14 baseline is preserved. All 19 fields from the independent references and all corresponding verified v16 MATLAB ports were compared by the executable acceptance runner.

This independent QA lane executed the trace verifier against the final CSV and obtained 2860/2860 passing checks, zero failures, all six modes and 28 observed mode changes. This includes the 27 independent fixed-COP intervals, each compared against every expected output field and expected mode, plus independent conservation/bounds/memory checks on all 39 intervals. The first sample of every scenario and next-to-start TES energy continuity pass. Final evidence: `results/stateflow_v22_20261009T025644993Z/stateflow_independent_qa_v22.json`; log: `automation/logs/stateflow_independent_qa_v22_20261009T025842705Z.log`. Final CSV SHA-256 is `c2af116fdf91f3df0aa6ef57d772a129d379b1fadbc6775f5f9404d80a281632`.

MATLAB reports an in-memory maximum absolute interval balance residual of 7.7715611723760958e-16 MWh. Independent recomputation from exported decimal CSV gives 2.867150961094467e-14 MWh. Both pass the 1e-9 MWh tolerance; the small difference is consistent with decimal serialization and independent arithmetic order. No physical interpretation is attached to numerical roundoff.

The separate read-only `verify_stateflow_structure_v22.py` independently opened the actual `.slx` ZIP/XML, rather than relying on the builder or runner's structure JSON. It passed 67/67 assertions for saved-model connectivity, Unit Delay TES memory, feedback vector index 8, configurable initial energy, interpolation disabled, common sample time, six operational OR states, state entry/during flow allocation, 30 guarded state changes, six guarded startup choices, the single default into their junction, and exact embedded helper equality with reviewed `.m` sources. Evidence: `results/stateflow_v22_20261009T025506909Z/stateflow_independent_structure_v22_20261009T025817687Z.json` and matching timestamped log. The model was unchanged across the two successful MATLAB acceptance runs. Its SHA-256 is `e1d3c1fe69597cd35a8c93a0706bcf81e7ffe8ed7edb0f9e05d9c359afc4f909`.

Code review confirms that the chart drives TES, backup and unmet ports through state-dependent allocation. HP request/operating-point calculation delegates to the verified v14 component, with the current delayed TES energy and explicit parameter inputs. Guarded initial-junction routing selects the correct startup mode; entry and during actions prevent stale state-transition outputs. This addresses the disconnected compile-only prototype defect.

Reproduce the independent numeric audit with a fresh report path:

```powershell
python audit/verify_stateflow_trace_v22.py --trace results/stateflow_v22_20261009T025644993Z/stateflow_trace_v22.csv --report results/stateflow_v22_20261009T025644993Z/stateflow_independent_qa_v22_RERUN.json
```

The verifier checks input/config provenance against the independent vectors, all expected numerical fields and modes, nonnegative finite flows, COP and capacity/source bounds, energy/SOC bounds, TES mutual exclusivity, loss equations, both first laws, actual flow-to-mode consistency, TES state continuity and the discrete time grid. It audits conservation and limits across the entire combined trace, including pre-existing v18 scenarios, while applying its fixed-COP numerical oracle to its 27 independent intervals.

The finite-HP/TES/boiler/unmet discrete-dispatch acceptance task passes at its stated simulation boundary. The HP adapter uses a host MATLAB extrinsic call in normal simulation mode; standalone code generation/deployment is untested. Model reservoir proxies, efficiencies and part-load curves remain engineering assumptions. Stateflow logs contain nonfatal formal-argument shadowing warnings (`u`, `E`, `p`); these are deliberate local function arguments supplied explicitly by chart actions. The warnings were inspected, preserved and not suppressed. No warning-free run, physical equipment validation, annual-network calibration, controller hysteresis/fault behavior or primary-paper replication is claimed.

Next actionable engineering task: make the next version explicitly test timestep sensitivity and a continuous TES leakage alternative, then integrate independently reviewed source/HX/network boundaries before extending the computational model's physical scope. Avoid treating repeated execution of these now-passing deterministic vectors as new physical evidence.
