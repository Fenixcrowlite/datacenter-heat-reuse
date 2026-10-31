# C116 | Two-way RH–evaporation–pool feedback (synthetic)

The sidecar computes a coupled hourly recurrence: room RH at hour start -> C93 pool evaporation and latent/makeup loss -> C104 ideal outdoor coil -> C112 capacity-limited room moisture storage -> updated dehumidifier electricity and condenser heat credit -> C108 shared heat dispatch -> pool temperature and room RH at next hour. It does not modify Simulink, SCADA, the original data, or any shared worktree.

Six annual scenarios (two source-priority policies, three humidity controls) generated 52,560 hourly rows. **Independent QA PASS:** 683,280 row checks, 105,108 state-continuity checks, 70,080 exact ideal-reference comparisons, four deliberately corrupted-row controls rejected.

| Source priority | Control | RH range | RH violations (<45% or >65%) | Minimum pool C | Evaporation kg/year |
| --- | --- | --- | ---: | ---: | ---: |
| Water first | Ideal | 55% | 0 | 27.7960 | 259431 |
| Water first | 5 kg/h | 21.17–86.25% | 5009 | 27.7800 | 212824 |
| Water first | C114 45.66/29.70 kg/h | 45.90–61.96% | 0 | 27.7851 | 258747 |
| Air first | Ideal | 55% | 0 | 27.7555 | 258813 |
| Air first | 5 kg/h | 21.19–86.10% | 4980 | 27.7213 | 212148 |
| Air first | C114 45.66/29.70 kg/h | 45.91–62.00% | 0 | 27.7453 | 258422 |

Energy accounting includes pool evaporation latent heat exactly once in pool losses and the same evaporation mass once in room moisture. Both source and pool energy balances are checked independently. All ideal-control hourly results reproduce immutable C111 within 3e-8 tolerance.

**Boundaries:** 29 C indoor temperature held constant; C104 outdoor coil remains idealized; no room sensible heat state, condensation heat recovery, subhour transient, equipment curve, or independent real-world validation. C114 capacities are model sensitivity only, not vendor specifications. All 31 primary source signoffs remain open.

**Next:** independently challenge hourly vs subhour RH peaks, couple room air temperature and enthalpy, then calibrate with measured equipment/weather/geometry. Keep VRS excluded and preserve C111/C112/C114 as immutable baselines.
