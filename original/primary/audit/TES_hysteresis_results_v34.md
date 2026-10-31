# v34 executed HP hysteresis/dwell Stateflow

UTC: 2026-10-10T03:01:39.854221+00:00. Actual saved model v34 acceptance PASS.

MATLAB 28744/28744 assertions PASS; 37 scenarios / 255 intervals / 16320 slots (412 positive-duration); all six modes; 30/30 actual runtime rejections. Maximum first-law residual 1.24344979e-14 MWh. Independent RK4 equation checks 412, zero failures.

The saved SLX contains actual persistent HP_ON/HP_OFF states, six thermal modes, physical-hour elapsed accumulation, TES and clock memories, bounded 64-segment execution and a separate runtime monitor. Compilation alone was not treated as completion.

The v33 low-load capacity tail is repaired in the tested fixtures: TES serves heat throughout HP OFF until cutoff. Both E0=9.9 and E0=10 cases have zero unmet over four hours at every tested macro partition. The fresh saved-v32 comparison retains the original unmet-demand counterexample.

| Case | Macro step (h) | End TES (MWh) | HP electricity (MWh) | Unmet (MWh) | End physical age (h) |
|---|---:|---:|---:|---:|---:|
| fallback | 4 | 8.868769960 | 4.459459459 | 0.000000000 | 0.022889569 |
| fallback | 2 | 8.868769960 | 4.459459459 | 0.000000000 | 0.022889569 |
| fallback | 1 | 8.868769960 | 4.459459459 | 0.000000000 | 0.022889569 |
| fallback | 0.5 | 8.868769960 | 4.459459459 | 0.000000000 | 0.022889569 |
| fallback | 0.25 | 8.868769960 | 4.459459459 | 0.000000000 | 0.022889569 |
| fallback | 0.125 | 8.868769960 | 4.459459459 | 0.000000000 | 0.022889569 |
| initial_capacity | 4 | 8.974800545 | 4.459459459 | 0.000000000 | 0.081540764 |
| initial_capacity | 2 | 8.974800545 | 4.459459459 | 0.000000000 | 0.081540764 |
| initial_capacity | 1 | 8.974800545 | 4.459459459 | 0.000000000 | 0.081540764 |
| initial_capacity | 0.5 | 8.974800545 | 4.459459459 | 0.000000000 | 0.081540764 |
| initial_capacity | 0.25 | 8.974800545 | 4.459459459 | 0.000000000 | 0.081540764 |
| initial_capacity | 0.125 | 8.974800545 | 4.459459459 | 0.000000000 | 0.081540764 |

The independent closed-cycle recurrence verifies these energy, electricity, discharge and clock endpoints; fixture invariance is not an arbitrary-input or measured-equipment claim. Six base physical flow/energy cases also agree with newly executed saved v32; v34 explicitly commands request zero while HP OFF, whereas v32 recorded an unavailable nonzero request.

Other executed cases include source/demand changes, feasible capacity-hold ON dwell, OFF dwell above/below restart, cutoff before dwell, finite backup/unmet, source limitation, zero/small loss and HP-only operation. Runtime faults include domain/control/clock violations, two delayed input faults (one NaN), explicit event-budget exhaustion, eleven allocation/clock corruption cases and iterator-tick timing corruption.

Independent QA breakdown: `{"numeric": {"passed": 58045, "failed": 0}, "artifact": {"passed": 24018, "failed": 0}, "legacy": {"passed": 139, "failed": 0}, "alternate": {"passed": 14, "failed": 0}, "archive": {"passed": 26, "failed": 0}, "faults": {"passed": 32, "failed": 0}, "synthetic": {"passed": 8, "failed": 0}, "preservation": {"passed": 1040, "failed": 0}}`. Prior unique immutable entries preserved: 1040. Read-only saved MAT re-export binds every trace and fault diagnostic; SLX graph/functions bind the actual saved implementation. Synthetic reviewer challenges are separate from actual execution evidence.

Failed attempts retained: sandbox MATLAB startup failed before execution; authorized local retry succeeded. First builder missed the additive choose-mode source; second compile exposed integer/double collector indexing, captured with diagnostic diary and repaired. First full harness had seven assertion failures (four unavailable-request diagnostic comparisons and three singleton empty-array shape checks). Its physical/oracle tests and 30 runtime rejections passed; corrected harness reran against the unchanged saved SLX. The first independent reviewer encountered empty eml XML tags on ordinary states; it was corrected to skip those tags, then required all four embedded function bindings and reran successfully. Failed source snapshot/log and exact successful reviewer source are retained.

Evidence: `results\stateflow_v34_20261010T025818184Z`, `audit\Stateflow_QA_v34_20261010T030114_814113Z.json`, `audit\Stateflow_execution_v34_20261010T025814481Z.json`. Policy/equations: `audit/TES_hysteresis_derivation_v34.md`.

Remaining limitations:

- Implementation acceptance of assumed mixed TES/HP screening plant only; no calibrated or measured physical validation or article replication.
- ON dwell is overridden by capacity/HP infeasibility; OFF dwell remains binding. The first near-capacity ON leg may be shorter than the nominal ON dwell.
- Bounded 64-slot analytic segments share the macro solver timestamp. Explicit physical-hour timers are executed; no solver-clock event scheduler or seconds-based temporal logic.
- Normal-mode host HP/event planner; standalone code generation, deployment, hydraulic/network model, stratification, ramping and startup/cycling losses remain untested.
- Restart band requires positive usable TES capacity; zero-capacity and zero-width-band control are rejected.
- Held-input partition evidence covers the tested finite fixtures only; no arbitrary input-partition equivalence, universal policy superiority or economic optimum.
- Host screening availability is trusted for safety-off decisions. Domain/monitor injections do not establish physical equipment or sensor fault behavior.
- Nonfatal formal-argument Stateflow shadow warnings remain in logs; no warnings were hidden by settings changes.
- Independent algorithm/artifact QA includes Decimal/bisection, RK4, alternate closed recurrence, saved-MAT/SLX and immutable hashes; it is not a separate human/agent review. Synthetic reviewer tests are separately counted.
- No new primary article equation or calibrated value adopted; full primary signoffs remain 0/31.

Next: Audit primary equipment/engineering evidence for the minimum-load COP cutoff, compressor dwell and cycling-loss assumptions; derive admissible restart-band constraints under changing source/demand. Preserve accepted v34 and distinguish screening assumptions from calibrated hardware before adding an equipment-fault or cycling-loss plant model.
