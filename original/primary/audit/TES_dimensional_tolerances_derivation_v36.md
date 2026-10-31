# v36 dimensional numerical contract

This additive release repairs the v35 counterexamples in an actual new Stateflow
model. It retains the assumed one-node TES equation and HP screening policy;
it adopts no new article equation, equipment parameter or cycling-loss value.

For constant internal power P (MW), loss rate lambda (h^-1), duration t (h),
and ambient-reference energy E (MWh), E'=P-lambda E gives
E(t)=E0 exp(-lambda t)+P[-expm1(-lambda t)]/lambda, with E0+Pt at zero loss.
Standing loss is E0+Pt-E(t), charge loss is (1-etaC)qc t and discharge loss
is (1/etaD-1)qd t. Capacity/cutoff hitting times and dwell bounds remain the
independent derivations in TES_hysteresis_derivation_v34.md and
TES_admissibility_derivation_v35.md. The v36 fixtures use the inherited
Decimal-coefficient/bisection oracle and separate RK4 integrations.

The numerical distinction is mandatory: subtraction of large energies can
need an MWh roundoff allowance; that does not justify an allowance in hours,
MW, kelvin or dimensionless COP. The monitor now checks HP and service
closure as instantaneous power equations instead of multiplying by a short
duration and comparing with a capacity-scaled energy tolerance.

| Quantity | Runtime monitor tolerance | Unit |
|---|---|---|
| TES, energy handoff and integrated balance | 1e-10 + 64 eps(max(1, capacity + interval heat budget)) | MWh |
| HP, source, service and port powers | 1e-9 + 64 eps(max(1, source, demand, HP/port limits)) | MW |
| Storage temperatures | 1e-9 + 64 eps(max(1, absolute temperature magnitudes)) | K |
| COP | 1e-10 + 64 eps(max(1, COP bounds, Carnot COP)) | dimensionless |
| Age, offset, partition and final clock | 64 eps(max(1, applicable time magnitudes)) | h |

The transition guard uses 64 energy ulps for capacity/restart comparisons
and a separate physical-hour budget for minimum ON/OFF age. The planner
uses energy ulps for energy snapping and power ulps for capacity-growth
comparisons. All latches and enumerated event/mode codes remain exact.

MathWorks defines eps(x) as the gap from abs(x) to the next larger floating
number of the same precision: [official eps reference](https://www.mathworks.com/help/matlab/ref/double.eps.html).
This definition was verified through the official documentation search on
2026-10-10; it is primary software documentation, not primary article evidence.
The constants 64 and the absolute floors are numerical engineering choices,
not physical uncertainty bounds or equipment calibration.

At 1e9 MWh, 64 binary64 energy ulps are 7.62939453125e-6 MWh. At .25 h,
the time scale uses max(1, time), so its budget is 1.4210854715202004e-14 h.
The .01 h corruption and .24 vs .25 h early-dwell counterexamples therefore
cannot be accepted by increasing TES capacity. Power, temperature and COP
injections of .01 in their own units test the same separation at all four
energy scales. Stress capacities are numerical adversaries, not installations.

The explicit time-resolution contract requires the 64-ulp hour budget to be
at most 1e-8 h (36 microseconds). A 1e6 h scale has 7.450580596923828e-9 h
budget and is admissible to the tolerance helper; a 1e9 h scale has
7.62939453125e-6 h budget and is rejected. Every positive planned segment
must also advance both the represented offset and persistent age. These
checks refuse unsupported precision instead of quietly broadening dwell
guards. They do not establish arbitrary-duration deployment or physical
sensor/actuator timing accuracy. Boundary and helper probes are labelled
component tests separately from actual simulated runtime fault injections.

Stateflow executes six guarded thermal modes and two persistent HP states
over up to 64 analytic segments per macro sample. Segment offsets represent
physical intra-interval times; the solver timestamp remains the macro start.
Normal-mode host planning, safety overrides of ON dwell, binding OFF dwell,
finite backup and TES cutoff behavior remain explicit. No standalone code
generation, solver-clock scheduling, calibrated hydraulics/stratification,
startup losses, measured validation or article replication is claimed.

Independent QA compares saved MAT exports, numerical traces, time/dwell
laws, the saved SLX scripts/guards/connections, and prior immutable hashes.
This is algorithm/artifact QA, not separate human or agent review. The v34
model and v35 defect evidence remain preserved for reproducibility.
