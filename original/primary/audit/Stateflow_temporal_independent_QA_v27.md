# Independent Stateflow failure-time and sample-boundary QA — v27

Reviewer lane `/root/stateflow_qa` read `automation/STATEFLOW_ACCEPTANCE.md`, the authoritative v26 Stateflow status/stageboard, `audit/research_frontier_2026_10_08.md`, and the relevant v24 builder, adapter, chart helpers and acceptance/rejection code before specifying tests. This lane edited only versioned audit artifacts; the implementation owner created and ran the MATLAB harness. No production controller, saved model, scientific source data, settings, scheduler or unrelated project was modified by the reviewer.

## Evidence gap and independent contract

The v24 rejection runner stored an intended input tick but left `started_at_h=NaN` and `first_valid_tick_observed=false`. A second-row invalid input and a caught exception establish rejection; they cannot establish that a first valid interval executed or that rejection occurred at the intended model time. The v26 status correctly retained this limitation.

`stateflow_temporal_cases_v27.json` independently specifies 12 schedules: 10 finite physical-domain faults and two controls with invalid rows later than StopTime. The faults cover source, demand, zero/negative temperature lift and absolute-zero source temperature; on-grid tick 1/tick 3 at `dt=0.25,0.5,1,2 h`; and input timestamp offsets `0.75*dt` and `1.25*dt`. The expected first invalid sample is `ceil(t_invalid/dt)*dt`. The two complete controls stop at 0 and at one sample interval, retaining the future invalid row in their actual input schedule. NaN/Inf timing is excluded because workspace ingestion can reject nonfinite data before runtime; prior domain rejection evidence remains separate.

Every fault requires actual Simulink execution-phase error metadata at its independently specified first invalid sample, matching `StopEventTime`, and an accepted dispatch prefix containing exactly the specified earlier valid sample times. Actual input CSVs, raw per-port times, diagnostics and numerical traces are hashed. A CSV prefix is not inferred from input placement. Source-side or Unit Delay logging at a failed tick, if present, is partial block evaluation and does not constitute accepted dispatch or transactional simulation behavior.

The tested saved-model hash must remain `1f1c826f0f61d04bea58c2ab39d607268ac273bad9564e69bec89e361c461389`, the preserved v24 `.slx` from the v26 checkpoint. No regenerated model is required for this additive timing gate.

## Independent arithmetic

The declared hand case uses source 6 MW, demand 5 MW, fixed COP 4, HP capacity 8 MW, TES capacity 10 MWh, charging limit 3 MW, charge efficiency 0.9, standing loss 0.01 per hour and initial energy 1 MWh. These are engineering assumptions, not article or equipment values. Source-side closure gives `H <= 6/(1-1/4)=8 MW`. For each valid sample:

```
E_after = E_start * (1 - 0.01*dt)
Q_charge = min(3, (10 - E_after)/(0.9*dt))
H = 5 + Q_charge
W = H/4
U = 3*H/4
E_next = E_after + 0.9*Q_charge*dt
L_standing = E_start - E_after
L_charge = 0.1*Q_charge*dt
```

No discharge, boiler or unmet heat is required, and the actual mode must be 2 (STORAGE_CHARGE). Powers are in MW; every energy port and loss includes the interval in hours. Independently recomputed TES closure is `E_start+(Q_charge-Q_discharge)*dt-E_next-L_standing-L_charge-L_discharge=0`. Whole-system closure replaces the charge/discharge term with `(U+W+B-Y)*dt`; the reported chart residual is checked against that independent result.

Useful hand anchors are:

| dt (h) | E after first valid interval (MWh) | E after second (MWh) | E after third (MWh) |
|---:|---:|---:|---:|
| 0.25 | 1.6725 | 2.34331875 | 3.012460453125 |
| 0.5 | 2.345 | 3.683275 | 5.014858625 |
| 1 | 3.69 | 6.3531 | 8.989569 |
| 2 | 6.38 | 10 | 10 |

For `dt=2 h`, the second interval is capacity limited: `E_after=6.2524 MWh`, `Q_charge=2.082 MW`, `E_next=10 MWh`. The third interval compensates standing loss at `Q_charge=1/9 MW`. The independent verifier computes this capacity-limited recurrence directly, imports no MATLAB/Stateflow production algorithm and compares all physical ports in both the actual model and the v16 numerical reference. It also verifies actual TES memory continuity and the initialized clean restart after the rejection sequence.

## API evidence and cause-fidelity limitation

MathWorks documents `CaptureErrors='on'` for scalar `SimulationInput` and the return of partial simulation results/metadata after a failure. Current online documentation is labelled R2026b; actual local execution establishes installed R2026a Update 5 support. [MathWorks setModelParameter documentation](https://www.mathworks.com/help/simulink/slref/simulink.simulationinput.setmodelparameter.html).

`ExecutionInfo.StopEventTime` is simulation time, while `ErrorDiagnostic.SimulationPhase` and `SimulationTime` distinguish execution failures from initialization or termination failures. The verifier requires both time fields; elapsed wall-clock timestamps cannot satisfy this requirement. [MathWorks SimulationMetadata documentation](https://www.mathworks.com/help/simulink/slref/simulink.simulationmetadata.html).

Retained actual attempts exposed an API evidence limitation: the host adapter constructs a nested `MException`, but actual captured and thrown Simulink errors return only the `DCHR:v24:PhysicalDomain` wrapper, with the domain-specific message retained. Thus the initial expectation that actual simulation diagnostics would preserve the inner component identifier was unsupported. The completed specification requires wrapper plus independently specified message in both actual simulation error modes. A separately labelled direct host-adapter invocation verifies the original inner identifier. That direct call is component-domain evidence only; model failure timing comes exclusively from actual simulation metadata and accepted prefixes. This distinction is not a claim about equipment fault diagnosis.

## Executed outcome

Final actual MATLAB evidence is `results/stateflow_temporal_v27_20261009T081740297Z/temporal_summary_v27.json`, with batch log `automation/logs/stateflow_temporal_v27_local_20261009T081736272Z.log`. MATLAB R2026a Update 5 executed the saved Stateflow model and passed 80/80 temporal assertions, zero failures. All ten finite fault schedules rejected in Execution at the specified first invalid sample. Both future-invalid controls reached their requested StopTime without errors. The case traces contain 52 clean accepted intervals and 22 accepted partial/control intervals; every accepted time and physical port agrees with the independent oracle, and clean ports agree with v16.

The off-grid source schedule at `t_invalid=0.75 h`, `dt=1 h` rejects at `t=1 h` after accepting `t=0`. The off-grid demand schedule at `t_invalid=0.625 h`, `dt=0.5 h` rejects at `t=1 h` after accepting `t=0,0.5`. Tick-3 faults preserve exactly three valid dispatch packets; the absolute-zero case at `dt=2 h` reaches capacity in its valid prefix and rejects at `t=6 h`. Actual raw HP, energy-start and dispatch times coincide throughout these prefixes; no current trace contains an accepted failed-tick dispatch packet. Clean restart after the sequence begins again at the specified 1 MWh initial state.

The independent verifier passed 4763/4763 checks, zero failures: 4547 actual temporal/trace checks, 18 evidence-integrity checks, 64 actual post-fault clean-restart checks, 100 specification checks and 34 expressly synthetic reviewer tests. The synthetic tests exercise the reviewer; they are not additional executed model cases. Report: `results/stateflow_temporal_v27_20261009T081740297Z/independent_temporal_qa_v27_20261009T081939137Z.json`; log: `automation/logs/stateflow_independent_temporal_qa_v27_20261009T081939137Z.log`. The report records exact verifier/spec/evidence/model hashes. The current saved `.slx` retains the prior v24 hash.

The actual captured identifiers remain wrapper-only. Separate direct host adapter reports in the final result directory establish the expected original inner identifier for each invalid domain, including `DCHR:v14:InvalidInput`, `DCHR:v14:TemperatureLift` and `DCHR:v22:InputDomain`. These reports are independently labelled component evidence and do not replace model timing or accepted-prefix evidence.

Retained intermediate directories include `stateflow_temporal_v27_20261009T081053865Z` (one actual failure-time result followed by a record-container setup defect), `stateflow_temporal_v27_20261009T081249839Z` (60/70 assertions passed; all timing gates passed, ten unsupported inner-cause preservation expectations failed), and `stateflow_temporal_v27_20261009T081639030Z` (heterogeneous JSON/case setup failure before simulation). Their logs, results and applicable runner/spec snapshots were preserved. The fresh complete run supersedes their acceptance conclusions without deleting the failed evidence.

## Remaining limits and handoff

This gate concerns finite input-domain rejection and sampled timing on the preserved six-mode implementation. It does not add physical validation, primary-paper replication, delayed nonfinite timing, sensor/equipment faults, hysteresis, dwell, compressor cycling, standalone generated-code execution, hydraulic/network/fuel/auxiliary models or equipment calibration. The loss-first linear TES baseline remains dependent on time partition, and new charge experiences standing loss starting in the next interval.

After actual temporal acceptance passes, the next actionable task remains acquisition/inspection of primary-text TES standing-loss equations and an independently derived continuous/exponential storage reference with timestep-convergence comparison. Preserve the accepted v24 baseline and distinguish source text, model assumptions and executed results.
