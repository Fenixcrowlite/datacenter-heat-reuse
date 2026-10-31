# v36 saved-Stateflow execution results

UTC 2026-10-10T07:46:27.486567+00:00. Implementation acceptance PASS; physical validation not tested.

MATLAB R2026a Update 5 executed the saved new model: 3073 assertions,
zero failures; 51 scenarios, 351 intervals,
535 positive segments and 22464 slots. Six modes
are observed. A separate MATLAB batch re-exported the saved SimulationOutputs.

The v35 .01 h clock-corruption counterexample now rejects at 10, 1e4, 1e6 and
1e9 MWh. The .24 h versus .25 h guard probes reject at every scale. Actual
host-planner mutations force early restart at each scale and are rejected by
the runtime authorization gate. Power (.01 MW), COP (.01), temperature (.01 K)
and offset (.01 h) mutations reject at all four scales. A 1e9 h initial clock
is rejected for insufficient declared resolution. Together with the inherited
30 general faults, there are 55 actual runtime rejections. Thirty additional
ON/OFF boundary/helper probes and four early-guard probes are component tests.

Independent QA breakdown: `{"numeric": {"passed": 56698, "failed": 0}, "artifact": {"passed": 32771, "failed": 0}, "time": {"passed": 45641, "failed": 0}, "partition": {"passed": 21, "failed": 0}, "faults": {"passed": 68, "failed": 0}, "archive": {"passed": 20, "failed": 0}, "legacy": {"passed": 20, "failed": 0}, "synthetic": {"passed": 4, "failed": 0}, "preservation": {"passed": 1541, "failed": 0}}`. Equation checks:
536 PASS. 1541 prior immutable entries
retain their hashes and sizes. The saved SLX functions, guarded states and
memory connections bind to the current sources and executed snapshot.
Six representative cases compare actual saved v32 flows/energy; COP and HP-OFF
request conventions remain explicit. Held-input closed-cycle and changing-input
partition comparisons use the observed traces, not just expected vectors.

Maximum absolute clean balance residual: 4.7683715837e-08 MWh. This maximum is
from numerical stress; an energy cancellation allowance is never used for
time, power, temperature or COP. Numeric traces retain individual residuals.

Evidence: `results\stateflow_admissibility_v36_20261010T074332672Z`, `results\stateflow_admissibility_v36_20261010T074332672Z\independent_QA_v36_20261010T074604_519524Z.json`, `audit\Stateflow_completion_QA_v36_20261010T074627_486567Z.json`.
Build/execution/export observed zero-exit receipts:
`audit\Stateflow_execution_v36_20261010T074032473Z.json`, `audit\Stateflow_execution_v36_20261010T074328262Z.json`, `audit\Stateflow_execution_v36_20261010T074548163Z.json`.

Initial sandbox startup failed before testing. The first compile and first
simulation exposed vector concatenation errors in the new tolerance code;
they were repaired, with logs/source snapshots retained. No warnings were
hidden by settings changes. No new equipment value or primary article
equation was adopted.

Remaining limits:

- Implementation acceptance of finite tested fixtures only; numerical stress capacities are not plausible installations.
- Time budget capped at 1e-8 h; direct admissibility probes do not establish deployment at arbitrary ages or sensor timing accuracy.
- Binding OFF dwell can leave unmet demand; ON dwell has capacity/input safety overrides.
- Normal-mode host planner; up to 64 analytic physical-time segments share macro solver timestamps, no solver-clock event scheduler or standalone code generation.
- No measured/calibrated physical validation, stratification/hydraulics, startup/cycling-loss model or primary article replication; full article signoffs remain 0/31.
- Nonfatal Stateflow formal-argument shadow warnings remain visible. Independent QA is algorithm/artifact QA, not separate human/agent review.
- Unchanged inherited HP/domain/component routines still require their own numerical-domain audit.

Next actionable task: Audit near-boundary numerical admissibility and the remaining host HP/domain validation: exercise restart/capacity separation near energy ulps, short segments and long persistent ages with held and changing inputs; derive a supported resolution/parameter domain and reject unsupported cases before extending any physical claims. Preserve v36 acceptance and v34/v35 counterexamples; keep primary equipment assumptions uncalibrated.
