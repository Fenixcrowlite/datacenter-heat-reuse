# DCHR seasonal mismatch | 2026-10-28 11:50 CET

VERIFIED isolated seasonal heat-vs-gas mismatch analysis on 8760 synthetic hourly records. Source SHA256 8125719923bae97901f37cf0f5354df77b46544df0477f863172255748873f25; original CSV and MATLAB model unchanged.

DISCOVERY: zero hours of simultaneous HP curtailment and gas heating. Curtailed potential 22545.421 MWh vs gas 12549.051 MWh. Direct same-hour gas displacement upper bound is 0 MWh; mismatch is seasonal.

Idealized buffer counterfactual: 100% efficient, unlimited charge/discharge power, no extra HP electricity, first synthetic year starts empty, following two years replay the same synthetic profile. This is a MATHEMATICAL UPPER BOUND, not feasible storage design, actual fuel savings, or incremental savings over existing 100 MWh model storage. See ENGINEERING_NOTE_SK.md for capacity table.

QA: 15/15 unit tests PASS; independent Decimal recomputation of 12 months, 8760 records, 120 storage fields PASS. Initial fixture bug fixed and retested; no remaining failures. SQLite integrity PASS.

SHA256 manifest: 7201c8d5743298820cea3191954c35dfd624a3b5f3df4d5be8ac3a9f5b35e7de
SHA256 evidence: ac06eb427929f73745029f095226a3aa40f00a21e8c157d6176da292a4902c2d
Existing Synapse task scc-2aab24704c2bd0, evidence event #1384 (RECORDED); task stays queued.
Card: https://desktop-m9l3i4m.taila1c6bd.ts.net/?synapse_task=scc-2aab24704c2bd0

Live intake: 2026-10-28 11:50 CET, SynapseMCP Web ping OK, RAM free 4.07 GiB, VRAM 1068/8188 MiB; STOP/PAUSE absent in checked roots; DCHR task queued with no worker PID, EduMotion task blocked. Existing Jarvice worktrees and worker processes observed, untouched. No Codex, GPU jobs, GUI, OAuth, VRS, public changes or expenses.

Limitations: original CSV timestamps have no timezone; synthetic source is not metered. HP_Heat curtailed is potential, not proven available without extra electricity. 0/31 primary source signoffs; ERF/REF/WUE unverified.

NEXT: Implement coupled seasonal thermal-storage sensitivity with actual HP electric demand/COP, MW charge-discharge limits, thermal losses, temperature constraints and independent physical QA; keep baseline immutable.
