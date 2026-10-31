# v53 finite-temperature boundary and saved-v52 interface

UTC 2026-10-11T06:31:42.115956+00:00. Scoped implementation PASS; saved model remains0.52, no new SLX.

MATLAB541/0; reference6/0;12 actual component/adapter domain rejections; independent8562/0 and separate reviewer mutations5/0. Actual34 intervals/38 positive segments/all six modes/8 latch changes.

Finite approaches reduce COP while source-limited condenser output increases because compressor work increases. The matched cases fix load6MW, evaporator budget4MW, all water temperatures, inventory and other assumptions; both evaporator and condenser approaches vary together. These are synthetic boundary sensitivities.

| Symmetric approach K | Compressor COP | HP MW | Compressor MW | Boiler MW | Aux MWh over0.25h |
|---|---:|---:|---:|---:|---:|

| 0 | 4.608929 | 5.108362 | 1.108362 | 0.891638 | 0.027709 |

| 5 | 3.866827 | 5.395271 | 1.395271 | 0.604729 | 0.034882 |

| 10 | 3.364113 | 5.691967 | 1.691967 | 0.308033 | 0.042299 |


Finite hot-side fixture caps HP output2.56MW, uses boiler2MW and leaves unmet1.44MW; source capacity is not the binding limit. Auxiliary heat is entirely rejected; it receives no demand/storage credit.


Original SimulationOutputs, numeric plans/segments/memory, report MATs/reopens, receipts, independent QA and source/preservation hashes retained. First attempt failed due new harness reshape/aux-column errors; corrected fresh run passes. Inherited controller is unchanged. Initial reviewer output-name shadow also repaired; original reviewer source/failed invocation retained.


Derivation: audit/Finite_temperature_interface_derivation_v53.md. Evidence: results/finite_interface_v53_20261011T062818_250661Z; independent QA: results/finite_interface_v53_20261011T062818_250661Z/independent_QA_v53_20261011T063124_120678Z.json.


Limitations:


- Synthetic steady fixed-saturation variable-flow boundary, not equipment calibration, article replication or measured physical validation; full primary signoffs0/31.

- Source20 local primary saturation definitions verified; upstream62 primary/supplement/coefficients inaccessible on attempted routes. Metadata/abstracts provide no equations.

- No new SLX/controller. Saved v52 remains0.52 and unchanged; actual focused new-interface simulations executed34 intervals, not an annual finite-interface acceptance.

- Water endpoint pinches and maximum heat-capacity rates are imposed feasibility constraints; UA, hydraulics, minimum/standby flow, capacity maps and pump laws are unvalidated.

- Fixed saturation axes/conversion across each scenario; a changing tank-linked condenser or factor requires a new interface, not silent generic annual reinterpretation.

- Auxiliary electricity is assumed proportional to compressor electricity and fully rejected for actual dispatch; thermal hot credit is explicitly rejected by adapter. No standby/auxiliary heat service claimed.

- Independent70-digit equations and original-MAT/binary handoff review by the same agent; not independent personnel or universal floating-point proof.

- Prior inherited bounded64-slot host planner, shadow warnings and normal-mode/standalone-code limits remain. Stateflow ver() is empty; license, charts and actual execution are directly observed.

- Initial new harness/reporting and reviewer errors are preserved. Corrected fresh execution and final QA pass; sandbox startup failure remains separately logged.


Next actionable task: Derive a coupled tank-temperature/condenser interface with finite HX and variable-flow constraints before a new Stateflow model. Use explicit saturation versus water temperatures and prove admissible source/hot-flow/temperature/energy domains independently. Keep upstream62 equipment-map calibration OPEN until verified primary supplement and operating envelope are acquired. Preserve saved v52 and the v53 fixed-temperature controls; do not repeat unchanged annual matrices.
