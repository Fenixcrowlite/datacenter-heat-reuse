# C124: 15-minute moist-air enthalpy and temperature

Implemented a self-contained synthetic indoor-air state with moist-air
enthalpy H = m_dry [1.006 T + w (2501 + 1.86 T)] kJ.
Per 15-minute step: prescribed C116 pool evaporation and latent transfer,
ventilation dry-air/moisture/enthalpy exchange, capped dehumidification and
humidification, capped proportional HVAC, and saturation condensation
with explicit liquid condensate enthalpy export.

Four scenarios (5/45.66 kg/h humidity capacity x 5/15 kW HVAC cap);
8,760 hours x 4 quarters x 4 scenarios = 140,160 rows. Source C116 SHA
pinned and unchanged. 7 embedded selftests, 140,160 independent
mass/enthalpy/state/continuity checks and 4 negative controls PASS.
CSV rounding causes small differences in recomputed H; independent QA
uses 2e-5 kJ tolerance and preserves rejected initial QA source.

Results (synthetic): dehum5_hvac5: 18,614 quarters RH>65%;
dehum45.66_hvac5: 8,760 quarters RH>65%. Total saturation
condensation across scenarios: 19,710 quarter-steps. High humidity is
a stress-test artifact, not real equipment sizing. Results depend strongly
on first-quarter evaporation pulse, fixed supply 26 C / 55% RH, and the
simplified dehumidifier energy export model. No return coupling to pool,
no wall capacitance, no measured HVAC curves, no field validation.
Energy closure is a mathematical bookkeeping test, NOT physical validation.

Next: replace assumed supply and dehumidifier heat-rejection models with
measured/traceable equipment curves, add pool feedback and compare with
field measurements. Do not edit original MATLAB/SCADA or C116.
