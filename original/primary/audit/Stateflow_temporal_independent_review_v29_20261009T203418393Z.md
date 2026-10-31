# Independent temporal acceptance review v29

Review time: 2026-10-09T20:34:18.779525+00:00. Result: **PASS for the preserved actual v28 model's finite delayed-domain and sampled-boundary implementation gate**. No material temporal defect was found. This review does not replace the separate v29 monitor-corruption gate.

Reviewed the acceptance contract, v28 STATUS/stageboard and research frontier before the temporal specification, actual runner, saved SLX, HP adapter, chart helpers, storage component, reference dispatch, current source snapshots and exported evidence. The executed MATLAB result is `results/stateflow_temporal_v29_20261009T154520430Z`; model release remains 0.28. The v29 suffix identifies the additive acceptance harness/checkpoint, not a new physical model.

| Evidence class | Passed | Failed | Scope |
|---|---:|---:|---|
| Executed MATLAB assertions | 81 | 0 | 12 actual input schedules |
| Independent actual-artifact checks | 4724 | 0 | 89 integrity, 4547 trace/diagnostic/input checks, 24 saved-model structure, 64 clean-restart checks |
| Static specification checks | 101 | 0 | Case set, independent clock and baseline contract |
| Synthetic reviewer self-tests | 43 | 0 | Corrupted records/traces/diagnostics and seven in-memory corrupted SLX parameter fixtures |

The actual runs include ten finite delayed-domain faults and two future-invalid-input controls. Clean, reference and accepted-prefix exports contain 52, 52 and 22 samples respectively, plus two final clean-restart samples. Synthetic checks are reviewer tests only; none was executed as a model experiment or included in the actual-artifact count.

The following clocks were checked against configured input CSVs, raw dispatch/HP/energy times, diagnostics, accepted trace rows and the independent specification. Hours are the project's numerical clock unit. For these positive timestamps the first invalid sampled tick is `ceil(tau/dt)*dt`. Inputs remain on their original timestamps and are held without interpolation.

| Case | dt (h) | Input fault time (h) | Actual failure time (h) | Accepted prefix times (h) |
|---|---:|---:|---:|---|
| source_tick1_dt025 | 0.25 | 0.25 | 0.25 | 0 |
| demand_tick1_dt05 | 0.5 | 0.5 | 0.5 | 0 |
| zero_lift_tick1_dt1 | 1 | 1 | 1 | 0 |
| negative_lift_tick1_dt2 | 2 | 2 | 2 | 0 |
| source_tick3_dt025 | 0.25 | 0.75 | 0.75 | 0, 0.25, 0.5 |
| demand_tick3_dt05 | 0.5 | 1.5 | 1.5 | 0, 0.5, 1 |
| zero_lift_tick3_dt1 | 1 | 3 | 3 | 0, 1, 2 |
| absolute_zero_tick3_dt2 | 2 | 6 | 6 | 0, 2, 4 |
| source_before_boundary_dt1 | 1 | 0.75 | 1 | 0 |
| demand_after_boundary_dt05 | 0.5 | 0.625 | 1 | 0, 0.5 |
| future_invalid_stop_zero_dt1 | 1 | 1 | No failure; stops at 0 | 0 |
| future_invalid_after_stop_dt025 | 0.25 | 0.5 | No failure; stops at 0.25 | 0, 0.25 |

All ten faults have `Execution` diagnostics at the first sampled invalid input, the expected outer `DCHR:v28:PhysicalDomain` cause and domain-specific message. Captured and uncaptured simulations reject. Original inner host-component identifiers are checked in separately labelled direct host calls because Simulink flattens nested causes; those calls provide no model timing evidence. No accepted dispatch exists at or after a failed tick. A downstream accepted trace is distinguished from any allowed upstream partial evaluation at that tick. The final clean run restarts from the configured 1 MWh initial energy.

Independent arithmetic uses the fixed-COP hand case only: 6 MW available source and COP 4 give up to `6/(1-1/4)=8 MW` condenser heat. The 5 MW load leaves at most 3 MW charge. With `r=exp(-0.01*dt)` and `b=0.9*3*dt`, the unsaturated start-of-tick energy is `r^n*1 + b*(1-r^n)/(1-r)` MWh. Clip at 10 MWh; this sequence is monotone for the specified dt values and cap refill remains below the 3 MW charge limit. Charge is `min(3, (10-r*E_n)/(0.9*dt))`, HP heat is `5+charge`, electric input is HP heat/4 and source use is 3*HP heat/4. At dt=1 the initial after-loss energy is 0.9900498337491681 MWh and next energy is 3.6900498337491685 MWh. At the dt=2 cap the refill is 0.11000737051802625 MW. All exported ports match the closed-form oracle within `1e-10 + 1e-11*abs(expected)`.

TES closure independently subtracts next energy, standing loss, charging loss and discharging loss from initial energy plus external net port energy. Whole-system closure additionally includes source heat, HP electricity, boiler heat and supplied demand. The maximum recomputed whole-system residual across the clean/reference/prefix CSVs is 8.978928711655954e-15 MWh. Unit-delay continuity and energy bounds pass. This audit uses no production imports, numerical HP solver or previous acceptance implementation in its oracle. MATLAB reference parity is complementary: `simulate_dispatch_v28` has separate allocation code but shares physical HP/storage components with the host adapter, so reference parity alone is not independent physics validation.

Before, after, current and snapshot hashes agree for all 13 required model/source/spec files. Model SHA-256 remains `30ea3701f2f04d293d6c9bf528dc625762bf69db9a06c9d6d384293a98497a1d`. Saved allocation/mode/gate scripts match their current files exactly. The saved SLX routes validated outputs to accepted dispatch and TES memory. This review strengthened `audit/verify_stateflow_temporal_v29.py` to inspect the actual saved solver step, input clock/hold policy, chart clock, memory clock/initial condition, integration-step parameter and next-energy selector. Seven in-memory altered archives prove the reviewer rejects corrupted temporal parameters. No production model, physical-policy helper, harness, previous result or status was edited.

Limitations remain explicit: this temporal hand case executes STORAGE_CHARGE only; six-mode coverage belongs to inherited v28 dispatch acceptance. Finite domain faults do not establish delayed NaN/Inf semantics. Every sampled row, including a completed tick at StopTime, describes a full-duration dispatch update; these sample counts must not be treated as physical integrated-horizon totals without that endpoint convention. Passive exponential cooling is exact only under the reduced constant-rate ambient-reference assumption; active ports retain loss-first splitting. The review inspected exported CSV/JSON and saved SLX/source snapshots rather than independently deserializing MATLAB simulation objects or rerunning temporal MATLAB. Primary text, paper replication, equipment/physical validation and standalone code generation are not claimed.

Reproduce (exit code 0 in the timestamped log):

```powershell
python audit/verify_stateflow_temporal_v29.py --summary results/stateflow_temporal_v29_20261009T154520430Z/temporal_summary_v29.json --self-test --report audit/<new_timestamped_report>.json
```

Full machine evidence: `audit/Stateflow_temporal_independent_QA_v29_20261009T203418393Z.json`. Log: `automation/logs/stateflow_independent_temporal_qa_v29_20261009T203418393Z.log`. Supplemental review record: `audit/Stateflow_temporal_independent_review_v29_20261009T203418393Z.json`. The earlier baseline reviewer report/log at `20261009T203304033Z` are preserved. Next actionable task is the separate actual v29 monitor-corruption acceptance and checkpoint handoff, then the temperature/cutoff-aware TES derivation already identified in v28.
