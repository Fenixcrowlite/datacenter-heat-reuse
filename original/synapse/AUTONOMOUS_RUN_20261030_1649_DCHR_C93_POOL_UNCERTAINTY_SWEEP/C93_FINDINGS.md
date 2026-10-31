# C93 | Uncertainty envelope for 500 m³ pool, 30 October 2026

## Scope and provenance
A new isolated 54-scenario dynamic simulation using the pinned C90 synthetic 8760-hour heat-source trace and C91/C92 thermostat and ASHRAE-informed evaporation logic. No modification of MATLAB, Simulink, SCADA, common Git worktrees or live workers. The source is **synthetic**; the result is a sensitivity envelope, not a measured plant prediction or a signed engineering design.

## Experiment
Each scenario integrates 8760 one-hour states (54 × 8760 = **473,040**). Varied three unmeasured parameters: indoor relative humidity 45/55/65%, overnight cover evaporation multiplier 0.05/0.15/0.35, and hypothetical recoverable fraction of the C90 heat-exchanger-rejected stream 0/10/25%. Each combination is run with no backup and with a 50 kW comfort backup. COP is fixed at 4 and remains **assumed**; temperature-lift feasibility, pinch, source temperature, actual ventilation and dehumidification are not included.

## Results
- With **10% hypothetical recovery and no backup**, across the 9 RH/cover cases the minimum water temperature ranges **27.428–27.817 °C**, with as many as **404 hours below 27.5 °C**.
- With **10% recovery and 50 kW comfort backup**, all 9 cases avoid the 27.5 °C breach; worst backup energy **22.75 MWh/year**.
- With **25% recovery**, all 9 RH/cover cases avoid 27.5 °C even without backup (minimum **27.774–27.806 °C**).
- With **no recovered heat and no backup**, temperature falls to **16.032–18.584 °C** across cases. A 50 kW backup alone maintains the 27.6 °C floor under this simplified model, but may require up to **254.86 MWh/year**.
- At RH 55%, cover multiplier 0.15, and no backup, C93 reproduces C92 at 10% recovery: **197.3570 MWh/year HP heat**, minimum **27.6529 °C**; at 25%: **201.7555 MWh/year**, minimum **27.7960 °C**.

**Interpretation:** 10% and 25% are arbitrary shares of a synthetic heat stream, not measured recoverability. The 25% scenario is not proof that the actual heat exchanger or heat pump can supply this energy at a useful temperature. The backup capacity is a thermal nameplate assumption; electricity and source temperatures are not validated. Humidity and cover values are scenario inputs, not observations.

## QA and limitations
- C93 self-tests: **8/8 PASS**.
- Separate output QA without importing the model: **24/24 PASS**. Checks include 54 unique grid cases, all finite numbers, annual energy conservation, COP consistency, zero-recovery/zero-backup invariants, expected RH/cover evaporation response, and numerical reproduction of C92.
- No changes to the 31 outstanding source signoffs. No real facility commissioning or design approval.
- Real next step: measure or document hourly HX inlet/outlet temperatures and flows, COP as a function of temperature lift, indoor air RH, occupancy, pool cover schedule and ventilation loads. Add temperature pinch/HP-map guard before making sufficiency claims.
