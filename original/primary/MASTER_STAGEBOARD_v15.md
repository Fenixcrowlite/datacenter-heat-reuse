# DataCenter Heat Reuse - stageboard v0.15

UTC checkpoint: 2026-10-08T22:04:04.084833+00:00. Additive to STATUS_v14.json and MASTER_STAGEBOARD_v14.md.

Completed one bounded research/equation task: visually verified Sintong p30 Eq15-16 and p31 Fig14, derived both-stream endpoint/first-law limits, and traced Park [38] to publisher primary body text. No full source signoff or author-result replication.

The flow-function interpretation requires `0<=epsilon*(1+r)/2<=min(1,r)` under positive-flow passive sensible equal-cp assumptions. New hidden-outdoor counterexample: r=.25, scenario epsilon=.8, return35 C/outdoor5 C gives return20 C but derived outdoor65 C; transfer15075 W exceeds maximum7537.5 W. This is a conditional adoption/domain defect, not proof that the authors executed that point.

- Python15/15 PASS;1342 exact main-interpretation points,671 alternative points;2000 reference plus1000 diagnostic random cases;66-row comparison. Evidence: audit/Sintong_IASE_tests_v15_20261008T220043_794544Z.json.
- Park provenance integrity8/8 PASS; these are evidence checks, not physical tests. Publisher primary parsed Eq22-23 read, visual checking pending, upstream Ham unverified. Local acquisition WinError10013; web screenshots cache miss. No local Park original is claimed.
- Independent equation/code review found no material issue within the declared model domain. Prior v14 immutable artifact hashes checked unchanged: 27; append-only progress ledger excluded from prior hash check.

M1 remains partial with0 full source signoffs. M2 gains an explicit IASE endpoint domain. M3/v14 annual integration and M4/M5 actual Simulink/Stateflow remain open. No new MATLAB runtime result; Stateflow availability not checked. Existing v07 Eq17/24 work was not repeated.

Next engineering task: Integrate heat_pump_step_v14 into a separate finite-boiler/TES/unmet-demand dispatch; review TES parameter/time-step validation first, then compare a deterministic multi-step trace with independent Python before a new Simulink model. Keep unresolved IASE algebra out of annual dispatch.

Next source task: Visually verify Park p9 and acquire upstream Ham et al. (2015) primary model/author code to resolve the Park/Sintong coefficient normalization and unequal-flow domain.

Report: audit/Sintong_IASE_domain_audit_v15.md. Ledger: automation/engineering_progress.md. Immutable evidence hashes: audit/IASE_evidence_manifest_v15_20261008T220404_084833Z.json. Stop after this task and handoff; scheduler/runner/settings and unrelated projects were not modified.
