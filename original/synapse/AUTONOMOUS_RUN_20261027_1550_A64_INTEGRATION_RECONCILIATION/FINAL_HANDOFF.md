# A64 integration reconciliation | 2026-10-27T15:54:48+01:00
Primary SynapseMCP Web live at start; STOP/PAUSE checked in governed scope. Existing DataCenter task remains review/planned, no worker.
New offline OUTPUT/comparison.html and OUTPUT/comparison.json compare 5 power channels for v08/v09.
A60 trapezoid: 671 x 900s = 167.75h. A62 discrete: 672 x 900s = 168h.
Pool delta v08 = 20.0003977213447875 kWh; v09 = 20.000397709776125 kWh.
Verified algebraic decomposition into last rectangle and slope correction, with endpoint identity.
QA 12/12 unit tests; 8107/8107 independent Decimal checks; 10 source SHA cross-checks and provenance guards.
All inputs DERIVED_SIMULATION; no physical calibration, no SCADA live link, physical_release=false.
No Codex, new workers, GPU tasks, VRS, shared GUI, OAuth or foreign-branch changes.
Evidence SHA256: 1ea083c0e186a3ad3d5bb34ba604dd1c932f6af07a6b52138ab87e4c1525ddc6
Manifest SHA256: 11975d1e8dfa48f5ea49155f6b675b30dc368a94122581f5175b97e37ae9cfbe
NEXT: Use the isolated A64 report alongside A63; obtain calibrated physical telemetry and verify UTC/channel identity before A55-A58 physical acceptance.
