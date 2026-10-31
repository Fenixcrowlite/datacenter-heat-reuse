# C112: Finite room humidity and bounded HVAC moisture capacity

**Status:** verified synthetic sensitivity experiment, NOT a validated building or equipment design. Existing DataCenter Synapse card: scc-2aab24704c2bd0.

## Actual change
A separate one-way room-moisture model now replays the SHA-pinned C111 evaporation and C106 weather. It replaces the ideal instantaneous 55% RH assumption with a finite 3540 kg dry-air room inventory, 3540 kg/h dry-air ventilation, exact one-hour first-order mixing, and capacity-limited dehumidification/humidification. Four equipment-capacity assumptions are compared for both heat-dispatch priorities: 8 annual cases, 70,080 hourly rows.

The indoor humidity controller chooses the hourly dehumidification or humidification rate needed to hit RH=55% at the end of the hour, then clips that demand at the configured equipment capacity. Supersaturation is clipped to RH=100% with explicitly recorded simplified endpoint condensation. Electricity covers only room dehumidifier and humidifier. Existing water temperature, evaporation, outdoor-coil supply and heat allocation are held fixed: **do not add these numbers to C111 HVAC totals without replacing the corresponding components.**

## Water-first, synthetic results
| Control capacity | Minimum RH | Maximum RH | Hours below 45% | Hours above 65% | Saturation hours | Room moisture-control electricity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Ideal unlimited | 55.0% | 55.0% | 0 | 0 | 0 | 137.76 MWh/year |
| 20 kg/h dehumidifier + 20 kg/h humidifier | 34.2% | 92.7% | 1630 | 1833 | 0 | 94.89 MWh/year |
| 5 kg/h + 5 kg/h | 17.3% | 100% | 3133 | 3859 | 380 | 26.91 MWh/year |
| 10 kg/h dehumidifier + no humidifier | 11.6% | 100% | 3777 | 2851 | 78 | 21.41 MWh/year |

A lower calculated electricity total in an undersized scenario is **unserved humidity-control demand**, not an equivalent-service efficiency gain. The ideal case exactly reproduces the original C111 room dehumidifier and humidifier loads, hour by hour. Both heat-dispatch priorities were simulated.

## QA and provenance
21/21 built-in physics/invalid-input tests PASS. Independent replay: 70,080 rows, 1,121,344 checks, three deliberately corrupted records detected. C111, C106 and C104 SHA256 pinned. Input files and all previous outputs remain untouched. Results stored in C112_ROOM_HUMIDITY_HOURLY.csv.gz, C112_SUMMARY.csv, C112_METADATA.json, C112_INDEPENDENT_QA.json.

## What is still NOT solved
The humidity result is not yet fed back to pool evaporation or to the heat pump. The C104 outdoor-air coil retains an assumed unlimited ability to remove outdoor moisture to the target supply humidity. Indoor air stays at 29 C. Room saturation clipping ignores latent heat release. Equipment capacities, fan curves, room volume and weather are synthetic. No manufacturer performance map, MATLAB/Simulink integration, field measurement, or primary-source signoff (still 0/31) was performed.

**Next executable engineering step:** run a bounded-capacity search to identify dehumidification/humidification capacities that satisfy a defined RH comfort band, then couple actual RH into C93 evaporation and the water/air energy dispatch with an explicit condensate latent-heat ledger. Independently compare the result with the original ideal-controller baseline.
