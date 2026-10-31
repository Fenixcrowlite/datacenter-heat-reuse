# C98: synthetic UA feasibility boundary for the 500 m3 pool

Existing Synapse task: scc-2aab24704c2bd0. This is an independent scoped numerical sensitivity study, not a design specification or proof of real data-center heat availability.

## Reproducibility

- Read-only C96 simulation source pinned to SHA256 `c084e706fc79c635856df6ba6223c1fed1cb9b8c7c72c5aba0e67ae38b8700d9`.
- Reused its C93/C91/C92 annual hourly pool dynamics, heat-rejection input, counterflow epsilon-NTU, source return floor, heat-pump and electrical caps, pump electricity, and thermostat. No production file was edited.
- 8 combinations of source temperature, hot-side flow, cold-loop inlet and **assumed constant COP**; UA scanned 0.0001, 0.02, 0.1, 0.5, 1, 2, 10, 100 kW/K. A nine-step geometric bisection brackets transitions found in the coarse scan.
- 127 unique annual simulations = 1,112,520 simulated hours. Acceptance: **zero hours below 27.5 C**, no backup heater, over 8760 synthetic hours.

## Results: minimum UA brackets, kW/K

| Hot inlet (C) | Hot flow (kg/s) | Cold inlet (C) | COP assumed | Failing UA | Passing UA |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 35 | 0.5 | 15 | 2.2 | 0.75254 | 0.75356 |
| 35 | 0.5 | 25 | 2.2 | 2.00630 | 2.01261 |
| 35 | 0.5 | 32 | 2.2 | no feasible UA <=100 | no feasible UA <=100 |
| 35 | 2.0 | 32 | 2.2 | 7.94954 | 7.97457 |
| 38 | 0.5 | 32 | 2.2 | 9.47964 | 9.50949 |
| 50 | 0.5 | 32 | 2.2 | 0.85815 | 0.85931 |
| 35 | 0.5 | 15 | 4.0 | 1.13725 | 1.13879 |
| 38 | 0.5 | 25 | 4.0 | 2.21861 | 2.22559 |

The no-feasible case at 35 C source, 32 C secondary inlet and 0.5 kg/s source flow still has **8744 hours below 27.5 C** at UA=100 kW/K. Increasing UA alone cannot compensate for the small available temperature difference and flow under this model. This is a bounded numerical conclusion, not a universal impossibility proof.

## QA and limitations

Independent output checker: **820 assertions PASS** over 127 scenarios; all 7 brackets independently matched a failing and passing CSV row, all 8 coarse scans were monotone, and two injected corruptions (energy residual, feasibility flag) were rejected. Source SHA pinned. The numerical engine itself is reused from C96, so this is independent output QA, **not** independent physics implementation or field validation.

Limitations: all inlet temperatures, flows, UA, pump differential pressures, and COP are assumed. Constant COP does not respond to secondary inlet temperature. Source rejected heat is synthetic. No measured data, exchanger vendor UA/fouling curve, manufacturer COP map, ventilation or dehumidification load; no new primary-source signoffs (still 0/31). No modifications to shared Simulink, SCADA, GUI, OAuth, or Jarvice.

**Next executable step:** use vendor UA-vs-flow/fouling and COP-vs-temperature curves plus measured source temperature/flow; couple secondary inlet to realistic heat-pump evaporator behavior. Add pool ventilation/dehumidification, then rerun and independently validate the annual energy balance.
