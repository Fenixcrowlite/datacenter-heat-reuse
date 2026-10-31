# Uncertainty-aware Stateflow results, release 0.42

2026-10-10T13:10:54.029975+00:00. **PASS_SCOPED_IMPLEMENTATION**. Additive saved model
`matlab/simulink/DCHR_Dispatch_Stateflow_v42.slx` built, compiled and simulated
with MATLAB R2026a Update 5 and observed Stateflow license/product metadata.
Previous model releases and sealed v40/v41 evidence remain preserved.

The planner, saved HP supervisor and runtime contract gate now use the
physical-age lower enclosure `hi+lo-bound` for minimum dwell. Conservative
waits certify the post-add enclosure, including new roundoff uncertainty.
Unresolvable progress rejects explicitly. ON-dwell unavailable-HP safety
overrides remain active. See `audit/Clock_uncertainty_derivation_v42.md`.

Executed: 31 scenarios, 29 completed,
43 macro intervals, 65 positive segments,
all six operating modes. MATLAB harness 61 PASS / 0 FAIL.
All v41 seeds/ties retained; additional multi-sample waits exercise enclosure
persistence. Two invalid clock-budget seeds and 30 domain/monitor/timer faults
reject during execution. Four actual in-memory nominal-v40-planner attacks
reject in saved v42 runtime gate at initialization or HP supervisor at the
next sample, for both ON/OFF directions. Saved SLX is never modified by attacks.

Independent evidence QA: 8012 PASS / 0 FAIL; separate synthetic
reviewer self-checks 4 PASS / 0 FAIL. The 26
dwell transitions have exact-rational lower age at or above dwell; zero
unresolved/certainly-premature transitions. 1,016 executed MATLAB function
probes have independently checked outward margins, ready decisions,
certified waits and clock enclosures. These probes are numerical fixtures,
not additional plant simulations. Saved MAT re-exports bind JSON traces/errors;
Decimal TES ODE/first laws and verified independent v34 baseline comparisons
pass. Maximum independent balance residual 9.0205620750793969e-16 MWh.

The focused harness initially issued a cleanup-order warning after all four
attacks passed. Its restoration now executes before model-close cleanup;
the focused probes and attacks were rerun in a new result directory and
checked for absence of the deleted-handle error. Original warning, source,
MAT and console artifacts remain preserved. The failed sandbox startup and
inherited argument-shadow warnings are also retained.

Main results: results/stateflow_clock_v42_20261010T130432870Z.
Focused clean rerun: results/stateflow_dwell_v42_20261010T130858503Z.
Independent QA: results/stateflow_clock_v42_20261010T130432870Z/independent_QA_v42_20261010T131023_265654Z.json.
Three successful timestamped batch receipts and logs are recorded in STATUS.

Limitations:
- Scoped numerical/implementation acceptance, not measured equipment validation or article replication; primary full signoffs remain 0/31.
- Exact-rational timing QA uses independent algorithms in the same agent, not independent personnel.
- Clock bounds/seeds are engineering numerical fixtures; physical error signs and long-run histories remain unknown.
- Outward comparison and certified waits can conservatively defer equality and shift near-ties by a few binary64 spacings; exhaustive exact real-input ordering is unproved.
- Normal-mode host planner executes analytic intra-macro segments; generated-code and solver-clock event execution remain untested.
- Finite arithmetic and existing clock/event budgets remain explicit rejection domains; no global arbitrary-precision guarantee is claimed.
- Inherited Stateflow formal-argument shadow warnings remain in logs. Sandbox startup failure is retained. Focused harness cleanup-order warning was fixed and its probes/attacks rerun successfully.
- HP component release 0.40 and temperature/cutoff TES assumptions are inherited; equipment calibration, hydraulic/stratified physics and measured physical validation remain open.

Next actionable task: Resume primary equipment traceability: select the most relevant accessible primary full text from the existing 0/31 signoff ledger, record exact pages/equation numbers, variables, units and operating domain for HP performance or TES cutoff/loss assumptions, and map them to the accepted v42 implementation. Independently derive and dimensionally check the verified relationship; document an access block or assumption mismatch if full text does not support it. Do not repeat Stateflow regression without a new defect/change.
