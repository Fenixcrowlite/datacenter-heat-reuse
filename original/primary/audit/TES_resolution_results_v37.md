# v37 executed saved-v36 numerical-domain defect audit

UTC 2026-10-10T08:01:23.118491+00:00. Defect reproduction PASS; controller repair OPEN.

Actual saved v36 executed in 24 scenarios: 19 completed,
5 rejected at runtime, 3382 completed intervals. Four host HP component
probes also executed. MATLAB harness 3/3 PASS; separate MAT export and
numeric-metadata batches exit 0. Independent QA 15924/15924 PASS,
including 6730 equation checks and
1781 preserved immutable entries. PASS counts describe
the audit and defect reproduction, not a corrected controller.

Six baseline modes/cases still match the independent v34/v30 numerical
reference. Saved SimulationOutput MATs, fresh numeric JSON traces, error
phase/time/messages, matched sources, exact inputs and timestamped logs
are in `results\stateflow_resolution_v37_20261010T075607048Z`. No production model/source is changed.

| Initial OFF age (h) | Partitions of 1.024e-7 h | Final clock bias (h) |
|---:|---:|---:|
| 1e6 | 1 | 4.548320770263299e-11 |
| 1e6 | 16 | 4.548320770263299e-11 |
| 1e6 | 128 | 1.908128356933590e-9 |
| 1e6 | 1024 | 1.6809289550781246e-8 |

The last value is about 60.51 microseconds, exceeding the 36 microsecond
comparison budget while local clock assertions pass. Changing demand halfway
through 1024 intervals gives the same bias. Initial-age-zero controls remain
within the comparison budget. A nonadvancing 1e-12 h interval at age 1e6 h
rejects with the existing resolution diagnostic. No early dwell transition
is observed in these OFF/source-unavailable stress fixtures.

At capacity 10 MWh, OFF age .25 h, zero demand/loss and available HP,
restart gaps 1/32/64 energy ulps pass strict configuration ordering but fail
with Nonpositive event progress during execution. Gaps 65/128/256 ulps keep
the HP OFF and energy constant. The exact policy has no capacity crossing
in any of these cases. A supported-band domain is missing.

At HP capacity/output 1e-309 MW, the preserved host component reports
available=true and COP=Inf with electricity zero. Separate saved-MAT flags
distinguish Inf from NaN; its intermediate slope is also Inf. The normalized
full-load reference gives COP=4. The actual saved Stateflow COP gate rejects
this response. 8, 1e-300 and 1e-308 MW component controls have finite COP=4;
the 1e-300 MW saved-model control completes.

Evidence: `results\stateflow_resolution_v37_20261010T075607048Z\independent_QA_v37_20261010T075836_225950Z.json`; `audit/TES_resolution_derivation_v37.md`;
`STATUS_stateflow_v37.json`; `MASTER_STAGEBOARD_stateflow_v37.md`.
The derivation identifies verified primary MathWorks software text separately
from engineering equations/assumed fixture values. No new primary article
equation, calibrated value or paper signoff was adopted; full signoffs stay 0/31.

Local MATLAB is R2026a Update 5. The Stateflow license test returns true;
the saved six thermal states and two HP supervisor states are inspected and
executed. The `ver('Stateflow')` lookup/full-product inventory did not expose
a standalone Stateflow version entry, so none is claimed.

Sandbox startup failed before simulation; its receipt/log is retained. The
local execution, MAT export, numeric metadata and both independent QA
revisions pass. Original reviewer snapshot/first QA remain; the final reviewer
revision has its own timestamped source snapshot. Known Stateflow argument
shadow warnings remain visible. No settings/runner/scheduler changes.

Limitations: Defect reproduction only; no new SLX or corrected-controller acceptance. Prior v36 fixture acceptance remains preserved. Clock bias is a cumulative-accuracy gap; v36 local tolerance checks pass. No observed early clean dwell transition is claimed. Aged-clock, near-ulp bands and subnormal HP powers are numerical stress fixtures, not plausible equipment specifications. HP component returns Inf but actual saved-model runtime COP gate rejects it; no invalid successful plant output is claimed. Stateflow license test is true and saved charts execute; ver(Stateflow) returned empty and the full installed-product list lacks a Stateflow entry. No standalone product version is fabricated. Independent QA is algorithm/artifact QA in the same agent, not a separate human/agent or physical validation. Normal-mode host planning and macro-time analytic segments remain; standalone code generation, solver-clock events, calibrated hydraulics/stratification/startup losses and article replication remain untested.

Next actionable task: Implement additive saved Stateflow v38: reject unresolved capacity/restart/cutoff bands before planning; replace overflow-prone HP slope arithmetic with a finite normalized-load component; implement compensated persistent physical-hour clocks with declared cumulative accuracy and reset/guard semantics. Execute six modes, v36 changing-input references, preserved v37 stress/counterexamples, clock partitions, cutoff overlap and source/request-limited HP cases; independently export MAT and compare exact-input Decimal clocks and normalized/analytic HP laws. Preserve every prior model/evidence; do not claim physical calibration.
