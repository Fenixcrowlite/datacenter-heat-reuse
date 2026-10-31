# Executed segment-Stateflow v32 results

Accepted execution: `results/stateflow_v32_20261010T022704149Z`.
Observed zero-exit receipt:
`audit/Stateflow_execution_v32_accept_20261010T022650039Z.json`.
Independent review:
`audit/Stateflow_independent_QA_v32_20261010T022948_982369Z.json`.
Derived comparison/sweep metrics:
`audit/Stateflow_result_metrics_v32_20261010T022932416Z.json`.

The fresh R2026a Update 5 batch executes the actual saved
`matlab/simulink/DCHR_Dispatch_Stateflow_v32.slx`, with its host HP planner,
and freshly executes preserved v30 for nine representative scenarios.
All numerical values below are assumed engineering fixtures, not measured
equipment data or replicated article results.

## Acceptance evidence

| Evidence category | Passed | Failed |
|---|---:|---:|
| MATLAB acceptance assertions | 13,868 | 0 |
| Actual runtime fault rejections | 23 | 0 |
| Independent equation checks | 1,294 | 0 |
| Independent actual numeric checks | 27,202 | 0 |
| Saved SLX structural checks | 73 | 0 |
| MAT/runtime/spec/source/preservation checks | 20,312 | 0 |
| Synthetic reviewer self-checks, separate | 9 | 0 |

There are 65 scenarios, 242 macro intervals, 484 segment slots and 272
positive-duration segments. All six modes execute with positive durations.
Maximum absolute interval first-law residual is 3.552713678800501e-15 MWh.
Faults comprise 13 finite input/domain violations, two delayed finite faults
and eight actual in-memory allocator corruptions. Each corruption stops in
the runtime monitor at time zero; delayed domain faults stop at time 1 h
after a valid prefix sample. The clean simulation after restoring the allocator
matches the saved clean baseline. Saved models remain unchanged on disk.
Independent QA verifies 597 entries from prior immutable manifests.

Mode changes are inferred from ordered, state-authorized numeric segment
outputs and corroborated by the saved chart's six states and 37 guarded
transitions. The fixtures observe 13 distinct changing mode pairs, including
16 STORAGE_DISCHARGE -> UNMET_DEMAND changes. This does not claim execution
coverage of all 30 possible interstate transitions or solver-clock event logging.

## Finite-boiler timing counterexample

Fixture: initial TES energy 7 MWh, capacity 10 MWh, cutoff 5 MWh,
loss rate 0.1 h^-1, discharge efficiency 0.8, demand 1 MW, boiler limit
0.5 MW, unavailable HP/source, two-hour interval. Full TES discharge
continues for 1.0821358464 h; the remaining 0.9178641536 h has no TES
discharge and requires 0.5 MW boiler plus 0.5 MW unmet heat.

| Two-hour integral, MWh | Event segments v32 | Uniform v30 |
|---|---:|---:|
| TES delivered heat | 1.0821358464 | 0.6453297812 |
| Boiler heat | 0.4589320768 | 1.0000000000 |
| Unmet heat | 0.4589320768 | 0.3546702188 |

Using average TES power in `max(0,demand-averageDischarge-boilerLimit)`
would falsely predict zero unmet heat for v32. Event dispatch supplies more
TES heat in this fixture but increases unmet heat because it leaves a later
deficit larger than boiler capacity. The result is a policy tradeoff, not
universal superiority of the event policy.

## Separate HP operating points

The capacity/nonlinear-COP fixture starts at 9 MWh with 1 MW demand,
6 MW available source, 8 MW condenser capacity, nominal COP 4 and
part-load penalty 0.15. Its first two-hour interval uses 4 MW condenser
heat at COP 3.7 for 0.5715841384 h, then 2.1111111111 MW at
COP 3.5583333333 for 1.4284158616 h to replace tank losses at capacity.
Integrated electricity is 1.4653886381 MWh. Recomputing electricity using
the average condenser power and its COP would give 1.4732274329 MWh.

Across the complete four-hour/two-sample fixture, actual v32 condenser
heat/electricity are 9.5241033725/2.6519616279 MWh; actual v30 gives
9.4481456814/2.6398443920 MWh. This compares different dispatch policies,
not a calibrated efficiency improvement.

## Timestep comparison and implementation limits

Five constant-input families (capacity, cutoff, near-cutoff, HP-only, idle)
run over the same two-hour horizon at h=2,1,0.5,0.25,0.125 h. Across these
fixtures the largest range among integrated TES/boiler/unmet/HP/electric/source
energies is 4.89e-15 MWh, consistent with roundoff. These cases do not test
all operating maps. In particular, a separately executed low-load-unavailable
capacity-tail fixture lets the store cool until the next macro sample;
its timestep sensitivity and restart policy remain the next task.

Both segment chart activations occur within the macro Simulink timestep.
The physical event durations/offsets are analytically integrated metadata.
Normal-mode host MATLAB HP calls are required; standalone generated code,
hydraulics, stratification, variable ambient, calibrated equipment, cycling,
hysteresis, dwell and sensor/equipment faults are untested. Delayed NaN/Inf
timing is untested. The sample at StopTime denotes another complete following
interval. Existing v30 helper-shadow warnings remain in comparison logs.

The first failed complete batch, older compile attempts, sandbox startup
failure and static reviewer failures remain preserved. They are not included
in the acceptance counts. See `Stateflow_completion_review_v32.md` for the
capacity roundoff and diagnostic/reviewer repairs. Independent algorithm QA
is not separate human/agent review, physical validation or article replication.
Full primary article signoffs remain 0/31.
