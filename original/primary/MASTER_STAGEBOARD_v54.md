# Coupled tank-temperature checkpoint v54

UTC 2026-10-11T06:46:08.797227+00:00. Exact restricted equations and scoped numeric QA PASS; coupled Stateflow integration and exact branch guards remain OPEN. Saved model stays0.52, unchanged.

MATLAB 621PASS/0FAIL;168 instantaneous vectors,12 source-affine regimes,14 component-domain rejections. Actual saved v52 executes15 charge-only intervals and one expected unsupported cold-tank rejection. Scoped independent QA 5326/0 plus5 reviewer mutations. Twelve exact-input branch classifications remain OPEN; these are not counted as certified discrete decisions.

The source-limited coupled charge ODE is affine even though COP varies with tank temperature. Independent70-digit closed form and separate min-envelope RK4 agree with MATLAB at all tested positive/negative/zero/near-zero rates. Aux heat is fully rejected outside storage. No paper fixture values, calibrated equipment or continuous Stateflow release are claimed.

| External macro chunks over0.05h | Terminal inventory MWh | Absolute energy error MWh | Absolute compressor error MWh |
|---:|---:|---:|---:|
| 1 | 9.816102055701 | 0.000653370973 | 0.000726572668 |
| 2 | 9.816428220090 | 0.000327206585 | 0.000363941242 |
| 4 | 9.816591692765 | 0.00016373391 | 0.000182134797 |
| 8 | 9.816673527022 | 8.18996522e-05 | 9.11084988e-05 |

These errors compare matched synthetic source-limited charging against the restricted continuous ODE. Each actual macro holds its sampled condenser/factor; externally carrying energy and clock between simulations is an approximation, not a new continuous controller. Refinement approaches the reference with approximately first-order error.

Cold tank example T=25C requires condenser52C at this imposed outlet floor, below the saved v52 tank maximum70C. The actual runtime correctly rejects that unsupported new interface. Its conservative old guard must be replaced only alongside a coupled flow/COP/energy contract.

At E=5MWh and binary C=0.2MWh/K, Ta=20C, charge approach2K and delivery/direct floor47C, nominal arithmetic yields tank45C and selects the tank branch. Exact arithmetic on those binary inputs yields T slightly below45C: gap -1.3877787807814456e-15K. Twelve related vectors have this unresolved discrete classification. Original failed exact-branch QA remains retained; the final reviewer records the flags and their2.8421709430404007e-14K rounding enclosure separately. This is an OPEN numerical guard/domain defect in the new component, not a v52 fixed-boundary regression.

Evidence: results/coupled_interface_v54_20261011T064243_962223Z; independent QA: results/coupled_interface_v54_20261011T064243_962223Z/independent_QA_v54_20261011T064501_582852Z.json. Derivation: audit/Coupled_temperature_derivation_v54.md. Original SimulationOutputs/report MATs/reopens, source snapshots, hashes and timestamped MATLAB/reviewer logs are preserved.

Limitations:

- No new SLX and no accepted coupled Stateflow model. Saved v52 remains accepted only within its previous fixed-temperature scope; fresh v54 successes cover 15 charge-only intervals, not all six modes or an annual run.
- Twelve exact-input branch classifications disagree at roundoff-scale kink: mathematical tank-branch gap -1.3877787807814456e-15K versus nominal rounded zero. Continuous powers pass tolerance; discrete branch/crossing certification remains OPEN.
- New analytic component supports one source-limited charging regime with no demand/discharge/capacity/limiter event. Its nominal endpoint branch test is not a certified general guard at unresolved kinks.
- Variable-flow tank-return topology is a synthetic engineering assumption distinct from v53 fixed return; no UA, hydraulics, pump/minimum-flow law, calibrated equipment map or physical validation.
- Exact affine derivation uses constant source/factor/ambient and no HP clips/part-load penalty. General charge/hot/request regimes, direct/discharge service and complete coupled controller remain unimplemented.
- Primary source20 local p8 definitions visually verified; upstream62 accessible record is metadata/abstract only and provides no primary equipment equations. Full primary signoffs0/31; no article replication.
- Independent QA is 70-digit equations and separately programmed min-envelope RK4/actual trace review by the same agent, not independent personnel or universal floating-point proof.
- Inherited v52 64-slot host-planner, normal-mode deployment and shadow warnings remain. Stateflow license/charts/execution observed; ver(Stateflow) empty is not an installed-version claim.
- Sandbox startup failure, initial reviewer singleton-struct exception and 5314-pass/12-fail exact-branch QA retained. Final scoped QA retains those 12 flags as OPEN; no MATLAB model/guard/tolerance was relaxed.

Next actionable task: Implement an additive conservative tank/outlet branch domain gate, reproduce the exact-binary E=5MWh,C=0.2MWh/K,Ta=20C kink and reject or explicitly resolve uncertainty. Then derive/verify all charge-side limiter regimes and their earliest event times before integrating energy-linked condenser/COP/flow and variable-power integrals into a new versioned Stateflow planner/allocation/contract. Keep demand service, cutoff/restart/dwell memory and exact padding/handoff strict; execute required six modes, fault tests and independent equation/MAT QA before any new SLX acceptance. Preserve accepted v52 and fixed-temperature v53; do not rerun unchanged annual policies or claim continuous coupling from sampled restarts. Primary equipment calibration remains OPEN.
