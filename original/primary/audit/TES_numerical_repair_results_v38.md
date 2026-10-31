# v38 executed numerical-domain Stateflow repair

UTC 2026-10-10T08:19:30.779040+00:00. Scoped implementation acceptance PASS.

New actual saved model: `matlab\simulink\DCHR_Dispatch_Stateflow_v38.slx`; SHA256 `fe60aaee835973195ccb94b323f516e7c1a6f413f5016f9b9f4d319251d297b2`.
MATLAB R2026a Update 5 builds and executes its six thermal states and two HP
supervisor states. The Stateflow license check passes. ver('Stateflow') is empty;
no standalone product version is asserted. All earlier SLX models are preserved.

MATLAB harness **2110/2110 PASS**:
80 scenarios, 69 completed,
11 deliberate unsupported-domain runtime rejections,
3725 completed intervals and 3910 positive
segments. All six required modes execute. Ten representative cases execute the
preserved v36 model afresh; six-mode and changing-input outputs agree. The
independent inherited v34 reference covers all 51 v36 fixture scenarios.
219 component probes cover normalized HP request/source/part-load limits and
subnormal full/partial load. 30/30 actual runtime faults reject. Exact restored
clean traces agree after temporary in-memory fault injection; saved SLX is unchanged.

Separate MAT-export and numeric-metadata batches exit zero. Independent QA:
**128974/128974 actual evidence/algorithm/artifact checks PASS**, with
**3/3 separately labelled synthetic reviewer checks PASS**.
1792 prior immutable entries retain sizes/hashes.
There are 61080 independent equation checks and
27260 clock checks; counts are per assertion, not
independent experiments or measured plant observations.

## Repair observations

| v37 counterexample | Saved v38 result |
|---|---|
| Age 1e6 h, 1024 intervals of 1e-10 h; bias 1.6809289550781246e-8 h | Maximum reported-high error 5.817381143570185e-11 h; final residual -4.548320770263299e-11 h; exact-input expansion error zero in held/changing-demand fixtures |
| 1e-12 h increment cannot advance binary64 age at 1e6 h | Executed with unchanged high age and retained +1e-12 h residual |
| Restart gaps <=64 ulps lead to zero-time EventProgress failure | Gaps <=128 ulps reject explicitly before event planning; 256-ulp control remains OFF |
| Unresolved cutoff/restart overlap not exercised | 1/64/128-ulp gaps reject; 129/256-ulp controls execute |
| HP cap/output 1e-309 MW returns Inf COP | Actual model executes finite normalized COP=4 with nonzero electricity; analytic component references pass |
| Smallest subnormal output cannot represent electricity | Explicit HPResolution component rejection |

The maximum independent segment first-law residual is
4.7683715781454694e-08 MWh, occurring within the
inherited large-capacity numerical stress scope. Energy and clock tolerances
remain separate; this does not establish measurement accuracy.

## Evidence and failures retained

Evidence directory: `results\stateflow_v38_20261010T081205294Z`. Primary numeric artifacts are execution,
positive segment/plan traces, saved SimulationOutput MATs, independent QA,
component MAT/JSON, actual v36 comparison MATs, and source/spec snapshots.
All successful batch commands and observed exits are in the status receipts.
Derivation: `audit/TES_numerical_repair_derivation_v38.md`.

Sandbox MATLAB startup failed before simulation. First local compile exposed
assignment to an outer Stateflow input name; its source snapshot and receipt
remain. Renaming the TwoSum local sum repaired compilation. The first reviewer
run encountered a manifest-size field mismatch; the next found two packaging
issues (harmless generator revision/source binding and a model-workspace value
stored outside XML). The executed generator was restored from its source
snapshot and the archive check now verifies its clock variable/dimension.
Failed reviewer logs/reports and source revisions are retained. Numeric
artifacts and the saved model were not changed during reviewer repairs.

## Limits and handoff

- Scoped numerical implementation acceptance only: finite fixtures, not all finite inputs or physical validation.
- 80-iteration HP source search and near-COP-cutoff classification retain a domain audit; subnormal tests are numerical stress fixtures, not plausible equipment sizes.
- Compensated clock initial expansion is a supplied exact seed; full adversarial residual/domain and strict event-ordering proof with nonzero error bounds remain open.
- Conservative band domain excludes zero/near-zero cutoff and bands <=128 capacity-scale energy ulps; this is numerical policy, not a physical equipment restriction.
- Normal-mode host planner/HP, bounded analytic segments at macro solver timestamps; standalone code generation and solver-clock events untested.
- No calibrated hydraulics/stratification/startup loss model, article replication or measured-system validation; primary signoffs remain 0/31.
- Independent algorithms/artifact QA in the same agent, not separate human/agent review. Synthetic reviewer checks are separately counted.
- Stateflow license test and actual saved-chart execution pass; ver(Stateflow) lacks a standalone version entry, and none is fabricated. Formal-argument shadow warnings remain in logs.

Next actionable task: Audit the normalized HP solver near the COP cutoff and across extreme source/output ratios, and verify compensated-clock initial residual/bound and event-guard domains before broadening acceptance. Use independent analytic/exact-input counterexamples rather than repeating the current suite. Then return to primary heat-pump/equipment evidence and physical parameter traceability; no calibrated or article-derived control values are accepted yet. Preserve all prior models/evidence.
