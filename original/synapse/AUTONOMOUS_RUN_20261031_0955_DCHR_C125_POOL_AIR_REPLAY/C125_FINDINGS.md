# C125: two-way pool/air replay with 15-minute feedback (synthetic)

## Actual change
Added task-local Python model that recomputes C93 evaporation from live quarter-step
pool temperature and room relative humidity, propagates moist-air T/w via immutable
C124 step(), and updates pool thermal storage with the SAME latent heat removed
from water and added to air. Hourly pool heat is replayed from SHA-pinned C116,
not newly optimized or reallocated. No MATLAB, SCADA or shared runtime edits.

## Results (two 8760-hour scenarios, 70080 quarter-steps)
- Frozen evaporation RH=55%: total evaporation 259431.74 kg,
  final pool 28.0426 C, quarters RH>65% 19345.
- Feedback evaporation RH=actual: 199651.01 kg,
  final pool 31.1843 C, quarters RH>65% 19680.
- Difference: evaporation -59780.73 kg (-23.04%),
  final pool temperature +3.1417 C, high-RH quarters +335.
- These differences expose sensitivity to humidity feedback and the fixed heat replay.
  In particular, 31.18 C final pool is NOT a safe operating forecast.

## Verification and limits
6 embedded checks and 70080 independent CSV-only energy/mass/continuity checks;
5 negative controls PASS. Exact source and output SHA256 recorded in manifest.
All results are SYNTHETIC. Replayed C116 heating ignores thermostat response to
new pool temperature, which exaggerates heat accumulation. C93 hourly loss law
is sampled quarterly, and C124 synthetic supply/HVAC and dehumidifier assumptions
remain. No measured climate, real equipment curves, external physical validation,
or 31 primary-source signoffs have been obtained. Conservation is a mathematical
identity test, not field validation.

## Next executable engineering step
Implement a bounded quarter-step heat-dispatch/thermostat feedback instead of
replaying C116 pool heat, and explicitly report any source-capacity violation.
Do not present equipment sizing or operating temperatures as validated.
