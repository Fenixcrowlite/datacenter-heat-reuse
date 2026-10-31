# Executed held-boundary schedule and reporting v74

UTC 2026-10-12T08:03:27.669746+00:00. The preserved actual `DCHR_Earliest_Dispatch_Stateflow_v73r2.slx`
was simulated, with saved v66 and v57 comparisons. No SLX was created or resaved.
New MATLAB APIs encode authoritative held durations, rounded cumulative labels,
immutable policy and persistent state; reporting retains energy/clock/inventory
hulls, refuses incomplete traces and excludes unmet heat from delivery.

MATLAB **475 PASS / 0 FAIL**; independent original-MAT
closed-equation/report QA **60818 PASS / 0 FAIL**.
Seven deliberate reviewer corruptions are detected, counted separately.
18 probes, 12 complete accepted schedules and two separately labelled valid
prefixes; 382 held intervals / 394 positive segments /
12 interior events. All six final chart states execute. Six actual refusals
cover collision, root boundary, segment budget, early ON disable, span and clock.
Twelve actual v66 comparisons and two actual v57 comparisons completed.

The three 48-hour partitions share identical regime boundaries. Independently
integrated v73r2 energy and final-inventory totals agree within the declared
1e-85 closed-arithmetic comparison budget. This does not assert equal binary
uncertainty hulls or timestep invariance for the sampled v66 policy.

The dt=.5 synthetic schedule demands 63.5 MWh:

| Actual saved model | Delivered MWh | Unmet MWh | External electricity MWh | Final TES MWh |
|---|---:|---:|---:|---:|
| v73r2 earliest segments | 46.909537810 | 16.590462190 | 4.563586965 | 5.008188014 |
| v66 sampled | 46.993431002 | 16.506568998 | 4.686469645 | 5.041886284 |
| v57 fixed boundary | 46.889483217 | 16.610516783 | 8.005183050 | 4.999853045 |

These are rounded diagnostics from independently checked synthetic trajectories.
Original MAT-derived reports retain the actual enclosures. Delivered service
and final inventories differ, so this table supports no cost/efficiency ranking.
The v57 boundary fixes condenser support at tank maximum and hot return at
ambient; it lacks the later thermal-stop policy. It is not a pure controller
comparison or calibrated plant result.

The separate charge/discharge-disabled control delivers exactly 5 MWh at
the independent comparison resolution, with no unmet energy in all three
models. External electricity is 0.843390601,
0.843390601 and
1.422354843 MWh respectively. Differences
still include the fixed-versus-dynamic v57 temperature boundary. v73r2/v66
allocate tiny binary rounding margins to backup; no assertion of exactly zero
backup is made. Final inventories accompany the machine-readable comparison.

Evidence `results/held_schedule_v74_20261012T075732_044061Z` contains timestamped batch/exit logs, original SimulationOutputs,
reopened report MAT, row-major binary64 exports, closed-equation numeric CSV,
initial and final reviewer snapshots, and prior preservation hashes. The actual
Stateflow license test returns 1 and sfroot observes the six-state chart;
`ver('stateflow')` returns empty and no installed-version inference is made.

Development failures are preserved. Restricted MATLAB startup failed before
execution; the first legacy adapter packed initial age into the low-order
clock residual and rejected both schedules. That was a harness defect, repaired
to [latch,age,0,0], not a demonstrated v57 model defect. An onCleanup capture
warning was also repaired. The first reviewer found two JSON column-vector
shape mismatches; row/column-aware binary binding repaired them without changing
model results or relaxing numeric acceptance. Legacy undefined COP diagnostics
remain NaN in binary and null in JSON; finite earliest traces forbid NaN.

Limitations:

- Synthetic 48-hour operating motifs and short controls only, not an annual weather/demand representation or measured validation. No new primary source signoff; 0/31 remain.
- Actual unchanged saved v73r2 executes normal-mode analytic event segments inside protocol calls, not solver-clock thermal event firing. No new SLX or generated-code acceptance.
- Binary held durations are authoritative; cumulative labels follow canonical binary64 cumsum and must lie in saved physical-clock hulls. General span/clock/order/dwell/segment refusals remain; no hidden retry or subdivision.
- v66 sampled policy and v57 fixed maximum-tank condenser/fixed return boundary are materially different. Seasonal delivered service and final inventories differ; no cost/efficiency ranking. v57 cannot represent independent enable commands or variable timesteps in this adapter.
- Same-agent algorithmic independence using exact-binary Fraction and 120/160-digit closed exp/log equations. MAT reopening/export is performed by MATLAB, not an independent HDF5 reader or independent personnel.
- Finite normal engineering arithmetic only; arbitrary-scale, subnormal and overflow acceptance remain untested. Integrated electricity/service is a boundary diagnostic, not calibrated total primary-energy efficiency.

Next actionable task: Resume primary equipment-map evidence and boundary audit using audit/HP_upstream_boundary_results_v44.md: obtain and verify source20 upstream [62] primary text and performance-correlation supplement (DOI 10.1016/j.tsep.2025.103513), distinguish actual coefficients/domains from metadata, and document any access blocker. Trace refrigerant versus water axes, compressor/auxiliary power and admissible source/hot flow ranges before designing a separate calibrated backend. Preserve accepted v57/v66/v73r2 and v74 schedule evidence; do not interpret the synthetic comparison as calibrated or annual performance.
Stop after this coherent executed deliverable and clear handoff.
