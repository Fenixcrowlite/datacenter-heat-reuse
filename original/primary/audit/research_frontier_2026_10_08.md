# Research frontier and engineering backlog — 2026-10-08

## Evidence from peer-reviewed research
1. Yuan et al. (2025), *Data center waste heat for district heating networks: A review*, RSER 219, 115863, DOI 10.1016/j.rser.2025.115863. Investigate 4th/5th generation district heating, heat pumps, TES and infrastructure constraints. Review only, not a calibrated component model.
2. *Data centers waste heat recovery technologies: Review and evaluation* (2025), Applied Energy 384, 125489, DOI 10.1016/j.apenergy.2025.125489. PUE alone insufficient; evaluate exergy and useful recovered heat.
3. *Waste heat utilization of data centers based on heat pump technology from the perspectives of supply and demand* (2025), Sustainable Cities and Society 130, 106543, DOI 10.1016/j.scs.2025.106543. Examine heat source temperature vs IT cooling electricity, seasonal mismatch and storage.
4. *Large-scale long-distance data center waste heat district heating system* (2026), Energy 345, 140076, DOI 10.1016/j.energy.2026.140076. Case-study claims for multistage HP, transmission distance and TES must NOT be generalized without replicating assumptions.
5. Verzino et al. (2026), *Smart Reuse of Waste Heat from Data Centres*, Energies 19(3), 800, DOI 10.3390/en19030800. Compare energy/exergy balances with thermochemical storage scenario.
6. *Review of tools and methods to identify excess heat potentials in district heating* (2026), RSER 236, 117000, DOI 10.1016/j.rser.2026.117000. Spatial, temporal and temperature resolution often missing; enforce these in validation.

## Research questions to resolve before claiming validity
- Source heat: IT electric load, PUE, heat capture fraction and coolant outlet temperature; account for auxiliary electricity without double-counting.
- Heat pump: evaporator/condenser balances, Carnot-bound COP, variable temperature lift, partial load and source-side heat extraction.
- District network: supply/return temperatures, mass flow, transport losses, distance and pumping power.
- TES: state of charge, thermal losses, charging/discharging efficiencies, finite capacity and mutual exclusivity.
- Control: explicit operating modes in Stateflow (OFF, RECOVER, CHARGE, DISCHARGE, BACKUP, UNMET), guards, hysteresis, faults and transitions.
- Economic/exergy comparison: boundaries, reference environment, electricity and gas emissions factors, CAPEX/OPEX, sensitivities.

## Agent execution contract
For each source: locate full text; record equation number/page, definitions, units, domain and assumptions; classify as verified primary-source / secondary-source / engineering assumption / unverified. Do not invent constants.
Then derive independent Python equations and dimensional/energy tests; implement MATLAB components; build and execute Simulink/Stateflow; compare against numerical baselines; store immutable versioned evidence; open next highest-impact research gap. Failure must produce a concrete defect and a corrective task, not a success label.


## 2026-10-11T21:49:14.264886+00:00 — v67 event-certification handoff

Executed same-chart root observer; MATLAB 1372/0, independent 36166/0. New root existence/order and OFF-dwell certificates pass for tested paths; actual earliest switching remains open. No new primary-source signoff.

Next actionable task: Integrate one certified repeated earliest-event cycle into an additive SAME six-mode chart using the v67 strict root witnesses. Carry threshold identity plus correlated root-time, inventory, source/work/loss/service offsets and OFF-age across event segments; never substitute a midpoint. Certify OFF dwell and ordering against held demand/source boundaries; reject unresolved collisions. Compare actual original-MAT service and source/work enclosures with an independent event trajectory. Preserve v57-v67r2, and regress the near-boundary/delayed witnesses plus dt=0.25/0.5/1 repeated schedules. Primary calibration and measured validation remain OPEN.


## 2026-10-12T02:29:11.453341+00:00 — v69 event interface blocker

Saved-v68 actual execution/independent QA confirms observer roots require mode/forcing applicability before earliest-event integration. No primary-source signoff added.

Next actionable task: Implement additive v70 mode-conditioned event candidates in the SAME six-mode chart before correlated earliest-event segments. Retain inventory/OFF-age hulls and held boundary; derive candidate ports from eligible HP/TES allocation, evaluate OFF restart with discharge forcing, stop only for enabled charge and cutoff only for enabled discharge. Retain threshold/root/forcing provenance and reject unresolved ordering only among enabled candidates. Execute v69 inactive-contact/delayed/strict controls, blocked-stop and zero/positive-loss forced-restart witnesses; keep genuine collision rejection. Then integrate one certified repeated earliest cycle with correlated source/work/loss/service/clock offsets, regress v66 repeated dt=0.25/0.5/1 and v68 span boundary. Preserve v57-v69; calibration and measured validation remain OPEN.


## 2026-10-12T02:46:29.479645+00:00 — v70 executed event candidate repair

Mode-conditioned candidate records and closed-form QA repair v69 interface witnesses; no new primary-source signoff or earliest-switching claim.

Next actionable task: Implement one certified repeated earliest-event cycle in an additive SAME six-mode Stateflow chart using v70 enabled candidates. Carry threshold identity, root-time hull and correlated inventory/source/work/loss/service/clock offsets and OFF age across each segment; never substitute a root midpoint. Recompute forcing and candidates after cutoff/stop/restart and held input boundaries. A restart readiness prediction after cutoff is invalid under the old forcing. Retain strict collision rejection and dwell proofs; compare original-MAT event service/source/work enclosures with an independent exact-binary closed-form event trajectory. Regress inactive-contact/delayed/strict, forced discharge restart, pair ordering controls, future charge sink, repeated dt=0.25/0.5/1 and lambda*duration=1. Preserve v57-v70. Primary calibration, article replication and measured validation remain OPEN.


## 2026-10-12T03:04:12.782319+00:00 — v71 repeated earliest-event implementation handoff

Actual saved model now consumes repeated roots with correlated symbolic
threshold/port/clock/OFF-age records; independent closed-form trajectory QA
passes. No new primary text, source signoff or physical calibration.

Next actionable task: Audit saved-v71 earliest-segment numerical admissibility and conservation under long repeated service, small restart bands, finite source/water limiter ties, external-disable ON dwell and segment-budget exhaustion. Execute original-MAT counterexamples or scoped acceptance with closed-form QA; preserve v57-v71. Then adapt a held-boundary annual input/reporting interface for v71 before any annual earliest-event claim. Primary calibration and measured validation remain OPEN.


## 2026-10-12T03:15:54.936054+00:00 — v72 executed numerical-admissibility blockers

Saved-v71 runtime evidence and independent closed equations confirm four
numerical rejection classes. No new primary text or source signoff.

Next actionable task: Implement additive saved v73 numerical-admissibility repairs: stable monotone passive/affine inventory images; correlated ON-age equality certificate; source-capacity proof retaining selected limiter/denominator relation; correlated compressor-work/auxiliary nonnegativity proof. Execute all original v72 counterexamples and six modes, long passive/repeated schedules, exact/early/late disable, source/water ties, narrow bands, genuine collision and explicit segment-exhaustion controls. Preserve v57-v72. Accept only after saved-model execution and independent closed-form original-MAT QA; then develop the held-boundary annual adapter. Primary calibration and measured validation remain OPEN.


## 2026-10-12T07:44:02.667485+00:00 — v73r2 numerical repair handoff

Actual model and original-MAT closed-form QA repair the scoped v72 witnesses. No new primary text/signoff or physical calibration.

Next actionable task: Develop an additive held-boundary input/reporting adapter for the saved v73r2 earliest-event model. Begin with a bounded representative seasonal schedule and source/demand/enable changes, preserve held physical timestamps and uncertainty hulls, explicitly surface collision/span/segment/clock refusals, and independently audit service/source/work/TES/backup/unmet aggregation from original MAT. Compare identical schedules with verified v57/v66 and equal delivered-service reporting before any full annual claim. Primary calibration, article replication and measured validation remain OPEN.


## Held-boundary adapter acceptance — 2026-10-12T08:03:27.669746+00:00 / checkpoint v74

UTC 2026-10-12T08:03:27.669746+00:00. Unchanged saved v73r2 actually executes six final modes,
48-hour synthetic motifs at dt=.25/.5/1, variable holds and enable changes.
MATLAB 475/0; independent 60818/0;
seven reviewer corruptions detected. 382 accepted/prefix intervals,
394 positive segments, 12 interior events,
six actual expected refusals and fourteen actual saved-model comparisons.
No new SLX: accepted v57/v66/v73r2 and all prior artifacts remain unchanged.
Evidence `results/held_schedule_v74_20261012T075732_044061Z`; audit/Held_schedule_results_v74.md.
Implementation QA only; annual/calibration/primary replication/measured validation
remain OPEN, full primary signoffs 0/31.

Next actionable task: Resume primary equipment-map evidence and boundary audit using audit/HP_upstream_boundary_results_v44.md: obtain and verify source20 upstream [62] primary text and performance-correlation supplement (DOI 10.1016/j.tsep.2025.103513), distinguish actual coefficients/domains from metadata, and document any access blocker. Trace refrigerant versus water axes, compressor/auxiliary power and admissible source/hot flow ranges before designing a separate calibrated backend. Preserve accepted v57/v66/v73r2 and v74 schedule evidence; do not interpret the synthetic comparison as calibrated or annual performance.


## Saved-Stateflow reporting provenance repair — 2026-10-12T08:17:12.957594+00:00 / v75

UTC 2026-10-12T08:17:12.957594+00:00. New saved v75 Stateflow model executes all six modes.
MATLAB 298 PASS / 0 FAIL; independent closed-form/binary/artifact
QA 12049 PASS / 0 FAIL; 6 separate reviewer self-checks.
10 complete saved-v75 runs / 125 held intervals / 129 positive
segments / 4 interior events. Nine fresh saved-v73r2 comparisons preserve
every thermal output bitwise outside schema/provenance columns.
Seventeen actual reporting corruptions/misassociated-input controls reproduce
legacy reporter acceptance and are rejected by v75. No corrupted record is a
physical plant simulation. The changed-source control executes separately.
Evidence `results/reporting_provenance_v75_20261012T081420_308048Z`; actual model `matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v75.slx`.
Primary/calibration/annual/measured validation remain OPEN; signoffs 0/31.

Next actionable task: Resume primary equipment-map evidence and boundary audit using audit/HP_upstream_boundary_results_v44.md. Seek a new accessible route to source20 upstream [62] primary text and performance-correlation supplement, DOI 10.1016/j.tsep.2025.103513; distinguish verified text/coefficients/domains from metadata and document any access blocker. Trace refrigerant versus water axes and compressor/auxiliary power before a separate calibrated backend. Preserve accepted v57/v66/v73r2/v75 and all v74/v75 evidence; no annual or calibrated performance inference.
Stop after this coherent executed deliverable and clear handoff.


## Temporal reporting gate acceptance — 2026-10-12T08:29:17.887976+00:00 / checkpoint v76

UTC 2026-10-12T08:29:17.887976+00:00. Preserved saved Stateflow v75 freshly executes all six required modes.
MATLAB 329 PASS / 0 FAIL; independent algorithmic QA
13717 PASS / 0 FAIL; six separate reviewer self-checks.
10 complete actual saved-model runs / 128 held intervals /
132 positive segments / 4 interior events. All 19 isolated temporal
reporting corruptions are accepted by v75 and rejected by the additive v76 API.
Corrupted records are reporting controls, never physical simulation results.

No new SLX or thermal controller change. Model and trace schema remain 0.75;
reporting API is 0.76. Original saved-model hash `d394da93637334bf4be55ed8b31b2660a74b8970a96a11d1fd8aa172032defb5` and
prior model/code/checkpoints are preserved. Reporting summaries match v75 for
all actual complete schedules except the reporting API version.

Evidence `results/temporal_reporting_v76_20261012T082629_130610Z` contains timestamped MATLAB logs, both restricted-startup
failure and successful batch receipts, Simulink diagnostics, original/reopened
MAT, binary exports, closed-equation numeric CSV, source snapshots and hashes.

New gate binds physical-clock copies and held boundaries, segment elapsed and
remaining duration, incoming/endpoint TES, HP latch/age and symbolic contacts,
boundary transition reasons and event/reset identities. Independent QA uses
exact-binary Fraction enclosure sums/differences and 120/160-digit closed
exp/log equations for complete nonlinear trajectories and all energy totals.
No production MATLAB function is called by Python.

Limitations:
- Synthetic bounded schedules only. No annual, calibration, primary replication, measured physical validation or generated-code acceptance. Full primary signoffs remain 0/31.
- Same-agent algorithmic QA with Fraction exact-binary temporal checks and inherited 120/160-digit closed exp/log equations. MATLAB reopens original MAT; Python consumes its binary exports, not HDF5 independently. No independent personnel claim.
- No new SLX/controller or thermal-policy change. Saved model and trace schema remain 0.75; additive reporting API is 0.76. Production v75 reporting API remains preserved for compatibility and remains permissive for demonstrated controls.
- Temporal consistency is not authentication or a replacement for nonlinear trajectory QA. Coordinated record replacement and independent event/dwell feasibility proofs remain outside this production gate.
- Inherited finite span, segment-budget, clock and event-order domains remain. Four interior events execute in accepted schedules; the 19 isolated reporting controls use the second held interval of one non-event chain.

Next actionable task: Resume primary equipment-map evidence and boundary audit using audit/HP_upstream_boundary_results_v44.md. Seek a new accessible route to source20 upstream [62] primary text and performance-correlation supplement, DOI 10.1016/j.tsep.2025.103513. Distinguish verified coefficients/domains from metadata; document access blockers and refrigerant/water/compressor/auxiliary boundaries before a separately calibrated backend. Preserve accepted saved v75 and v76 reporting evidence; no annual or calibrated-performance inference.

Stop after this coherent executed deliverable and clear handoff.


## Stateflow temporal pre-commit acceptance — 2026-10-12T12:53:03.464637+00:00 / v77

UTC 2026-10-12T12:53:03.464637+00:00. New saved v77 Stateflow model executes all six required modes.
MATLAB 86 PASS / 0 FAIL; independent algorithmic QA
15216 PASS / 0 FAIL; 6 separate synthetic reviewer self-checks.
13 complete accepted schedules / 133 held intervals /
149 positive segments / 16 interior events, with actual stop/cutoff/restart coverage.
Every output double matches 13 fresh saved-v75 comparisons.
The clean saved v77 artifact is reopened after all unsaved instrumentation
and matches its original valid trace again.

29 actual runtime assertion rejections have matching exact
single-fault monitor-bypass traces. These deliberately corrupted chart copies
are unsaved QA controls, not physical plant results. The saved artifact has
the exact original v75 thermal kernel and new v77 temporal monitor, with both
entry/during actions in every state checking before trace emission and commit.
Trace schema stays 75; reporting API stays 0.76.

Saved model `matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v77.slx` SHA256 `f0764a6555467ea7e86ee7c7b90534c8debeb41f8e49239af8f4c1e4994a9ee4`.
Evidence `results/temporal_commit_v77_20261012T123639_894788Z` retains timestamped MATLAB batch and Simulink diagnostics,
original/reopened MAT, binary exports, precision numeric CSV, all runtime
fault logs, source snapshots, preservation hashes and QA receipts.
Earlier failed restricted startup and heterogeneous-fixture attempt are retained
in `results/temporal_commit_v77_20261012T123551_584301Z`; neither counts as acceptance.

Limitations:
- Synthetic bounded normal-mode schedules only; no annual, equipment calibration, primary replication, measured physical validation or generated-code acceptance. Full primary signoffs remain 0/31.
- Same-agent algorithmic QA using Fraction exact-binary temporal equations and inherited 120/160-digit closed exp/log equations. MATLAB reopens original MAT and exports binary; no independent HDF5-reader or personnel claim.
- Release 0.77 embeds a pre-commit temporal monitor; thermal kernel, policy, trace schema 75 and v76 reporting API are unchanged. All accepted trace doubles match freshly executed saved v75.
- Runtime controls inject output-record faults into unsaved in-memory chart copies, with exact monitor-bypass witnesses. These controls are not physical plant simulations and are never saved as accepted models.
- The runtime guard proves protocol consistency, not every nonlinear event/dwell inequality or authentication against coordinated internally consistent replacement. Independent nonlinear QA remains required; inherited collision/span/clock/segment-budget domains remain.

Next actionable task: Resume primary equipment-map evidence and boundary audit using audit/HP_upstream_boundary_results_v44.md. Seek a new accessible route to source20 upstream [62] primary text and performance-correlation supplement, DOI 10.1016/j.tsep.2025.103513. Distinguish verified coefficients/domains from metadata and record access blockers; trace refrigerant/water and compressor/auxiliary boundaries before a separately calibrated backend. Preserve accepted v75/v76/v77 evidence; no annual or calibrated performance inference.

Stop after this coherent executed deliverable and clear handoff.


## Energy pre-commit acceptance — 2026-10-13T05:23:44.568086+00:00 / v78

UTC 2026-10-13T05:23:44.568086+00:00. Actual saved v78 Stateflow model executes all six required modes.
MATLAB 77 PASS / 0 FAIL; independent numeric/artifact QA
21999 PASS / 0 FAIL; 16 separate reviewer self-checks.
Supplementary exact rational capacity QA: 1293 PASS / 0 FAIL,
with three separate boundary self-checks and no tolerance shared between MW and MWh.
13 schedules / 133 held intervals / 149 positive segments /
16 interior events, including stop, cutoff and restart.
Every trace double matches fresh saved-v77 execution on the same inputs.

16 isolated energy corruptions are accepted by the unsaved v77
temporal-monitor copy and rejected by the v78 energy monitor at the expected
runtime assertion. Exact monitor-bypass traces prove every injected field was
reached. Instrumented chart copies are never saved. Clean v78 is reopened and
rerun after instrumentation. The embedded v75 thermal kernel is unchanged.

The new monitor binds port limits/allocation, TES bounds, forcing, port energies,
efficiency/auxiliary losses, segment offsets, interval and cumulative totals,
initial inventory and both first-law residuals before emission and commit.
It calls the preserved v77 temporal monitor. Trace schema 75 and reporting API
0.76 remain compatible.

Saved model `matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v78.slx` SHA256 `cfd8eadca5d5a6c7dd6da6a20ee7f32e43cafd0084e3c0bd6453179bff184be9`.
Evidence `results/energy_commit_v78_20261013T050754_608388Z` contains timestamped MATLAB batch logs and receipts, Simulink
diagnostics, original/reopened MAT, binary exports, closed-form numeric CSV,
runtime fault logs, source snapshots and preservation hashes.
Compiler warnings that the energy monitor is unused arise in deliberate
monitor-bypass copies; the saved model retains every pre-commit call.

The unfinished earlier v78 attempt had no saved model or acceptance evidence. Its
harness incorrectly selected v78 as its own comparison model; this run repairs
that selector to v77 and retains a pre-edit snapshot. The restricted-startup
failure is retained in the evidence; only successful actual executions count.
The draft energy reviewer uses a power-ulp slack in its TES bound check.
The mandatory supplementary reviewer directly compares every actual TES hull
against exact C*(Tmax-Ta) in MWh, and checks all power limits separately in MW.
Thus acceptance does not depend on that dimensionally misplaced draft slack.

Limitations:
- Synthetic bounded normal-mode schedules only; no annual, calibrated equipment, primary article replication, measured physical validation or generated-code acceptance. Full primary signoffs remain 0/31.
- Same-agent algorithmic independence: Python Fraction operand equations and separate 120/160-digit closed exp/log trajectories call no production MATLAB solver. MAT binary exports depend on MATLAB reopening; no independent personnel or HDF5-reader claim.
- Thermal kernel, policy, trace schema 75 and reporting API 0.76 are unchanged. The monitor checks candidate consistency before emission and commit, not authentication against coordinated internally consistent replacement.
- HP source/work overlap is a necessary balance condition, not a physical COP proof. Standing losses and nonlinear event/dwell feasibility require the separate closed-form QA lane. Inherited finite span, clock, collision and segment-budget domains remain.
- Fault controls instrument unsaved chart copies after kernel evaluation. They are exact isolated output-corruption witnesses, never physical plant trajectories.

Next actionable task: Resume primary equipment-map evidence and boundary audit from audit/HP_upstream_boundary_results_v44.md. Seek accessible primary text and performance-correlation supplement for DOI 10.1016/j.tsep.2025.103513; distinguish verified equations, coefficients and domains from metadata and access blockers. Trace refrigerant/water and compressor/auxiliary boundaries before a calibrated backend. Preserve accepted v75-v78 artifacts.


## HP partition acceptance — 2026-10-13T05:46:18.011900+00:00 / v79

UTC 2026-10-13T05:46:18.011900+00:00. Actual saved v79 Stateflow executes all six required modes.
MATLAB 60 PASS / 0 FAIL; independent actual equation/artifact QA
24379 PASS / 0 FAIL; exact MW/MWh capacity QA
1401 PASS / 0 FAIL; focused independent runtime branch QA
16 PASS / 0 FAIL. Reviewer self-checks are separately counted:
22 PASS, including explicit wide-hull overlap acceptance.

25 schedules / 145 held intervals / 161 positive segments /
16 interior events (stop/cutoff/restart); 12 eta/source-temperature/inventory
variants include both floor-limited and inventory-dependent hot proxies. Every valid
trace double matches fresh saved-v78 execution. Saved kernel remains exactly v75.

Six coordinated source/work/auxiliary/copy corruptions pass the unsaved v78
energy/temporal-monitored chart and are rejected by v79 before emission/commit.
Four source-partition controls use work shares 0, 1, .5 and .01. A source-wide
zero-work control specifically reaches the compressor assertion; a zero-HP
spurious-source hull reaches the OFF assertion. Exact bypass witnesses prove
the changes reached output. Both harnesses reopen the clean saved model after
all unsaved instrumentation. No corrupt chart is saved or called plant evidence.

The new monitor derives necessary whole-segment HP integral bounds from TES
endpoint extrema, monotone source/work fractions and positive Kelvin axes.
It invokes no thermal solver, event finder or production quadrature loop.
Independent Fraction equations and inherited 120/160-digit exp/log trajectories
review original-MAT binary exports, conservation, source/work and reporting.

Model `matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v79.slx` SHA256 `f93f47fec7caf5461916920f8f8983a426c7d62b644d4198e9e143bb00567822`.
Timestamped logs, receipts, original/reopened MAT, binary exports, numeric CSV,
fault logs, snapshots and preservation hashes: `results/hp_partition_v79_20261013T053839_629571Z`.
Three attempts executed all 25 valid schedules but failed in the fault harness
before fault acceptance: char/string concatenation, exact-zero handling, then
cumulative source/work copy indexing. All are preserved. The repaired harness
and scaffolder cast script text to char, retain exact zero, and use the correct
cumulative source/work columns 33:36. A separately labelled synthetic Python
preflight verifies all six fixture algebra controls before the completed batch.
The harness reuses the saved artifact without rebuilding or overwriting it.
Restricted-startup failure is also retained. Only complete successful batches count.
Compiler unused-monitor warnings arise in deliberate unsaved bypass copies.

Limitations:
- Reduced engineering HP assumption COP_h=1+A/lift; refrigerant/water temperature proxies and eta are not equipment calibration. No new primary-source signoff, article replication, measured validation, annual or generated-code acceptance; signoffs 0/31.
- Necessary integral overlap contract only: a recorded wide hull may include inadmissible members while overlapping valid values. An explicit independent wide-hull self-check documents this limit. No authentication or complete nonlinear trajectory certification is claimed by the runtime gate.
- Endpoint temperature extrema use monotonicity of held constant-forcing TES segments. Inherited closed exp/log QA independently checks actual trajectories. The gate does not independently reconstruct their ODE or event root.
- Same-agent algorithmic independence: exact Fraction HP bounds and 120/160-digit closed exp/log QA call no production MATLAB solver. MATLAB reopens original MAT and exports binary; no independent personnel or independent MAT parser claim.
- Bounded normal-mode synthetic schedules only. The added outward HP-bound arithmetic can reject unresolved/nonfinite extreme axes; unchanged policy/kernel retain finite span, clock, collision and segment-budget refusals.
- Six coordinated post-kernel record controls are unsaved chart instrumentation, never physical plant results. Thermal output, trace schema 75 and reporting API 0.76 remain unchanged.

Next actionable task: Resume primary equipment-map evidence and boundary audit from audit/HP_upstream_boundary_results_v44.md. Seek accessible primary text and performance-correlation supplement for DOI 10.1016/j.tsep.2025.103513. Distinguish verified equations/coefficients/domains from metadata and access blockers; trace refrigerant/water and compressor/auxiliary boundaries before a separately calibrated HP backend. Preserve v75-v79 acceptance.


## Standing-loss acceptance — 2026-10-13T05:55:02.799332+00:00 / v80

UTC 2026-10-13T05:55:02.799332+00:00. New saved v80 Stateflow actually executes all six required modes.
MATLAB 65 PASS / 0 FAIL; independent actual equation/artifact
QA 26696 PASS / 0 FAIL; exact MW/MWh capacity QA
1509 PASS / 0 FAIL. Separate reviewer self-checks:
22 PASS, including a wide loss hull overlap scope witness.

37 schedules / 157 held intervals / 173 positive segments /
16 interior events (stop/cutoff/restart). Twelve passive variants exercise
lambda=0/.01/.5/1 h^-1 and initial inventory=0/3/9 MWh, including lambda*dt=1.
Every valid trace double matches fresh saved-v79 execution on the same inputs.
The saved v75 thermal kernel, policy, trace schema and reporting API are unchanged.

The v79 monitor accepts four energy-balanced but constitutively impossible
passive records. v80 rejects each at the expected standing-loss assertion
before emission/commit. Exact bypass traces prove changed endpoint/loss/copy
fields reached output. Independent closed equations separately reject all four
controls. No corrupt chart is saved; clean v80 is reopened and rerun afterwards.

| Control | lambda (h^-1) | duration (h) | initial (MWh) | injected end (MWh) | injected loss (MWh) |
|---|---:|---:|---:|---:|---:|
| invented_loss_zero_lambda | 0 | 1 | 3 | 2 | 1 |
| suppressed_positive_decay | 0.5 | 1 | 3 | 3 | 0 |
| excess_positive_decay | 0.01 | 1 | 3 | 2 | 1 |
| deficient_positive_decay | 0.5 | 1 | 3 | 2.875 | 0.125 |


For held E'=B-lambda*E, monotonicity bounds integral(lambda E dt) by
lambda*duration*[minimum endpoint inventory, maximum endpoint inventory].
Zero lambda requires exact zero standing loss. The runtime check calls no
thermal flow, exponential, root finder or quadrature routine. Exact Fraction
operand QA and independent 120/160-digit exp/log trajectories verify original-MAT
binary exports, conservation, source/work/loss/service, reporting and temporal links.
The separate capacity reviewer keeps MW and MWh bounds distinct without slack.

Saved model `matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v80.slx` SHA256 `f7032682f4d6c338a99f1425311a807254c3022ba8527dba5f616f53b0ac66be`.
Evidence `results/standing_loss_v80_20261013T054910_671296Z` contains timestamped MATLAB logs and execution receipts,
Simulink diagnostics, original/reopened MAT, binary exports, numeric CSV,
all runtime fault logs, source snapshots and preservation hashes.
Restricted-startup failure is retained; only successful actual batches count.
Compiler unused-monitor warnings arise in deliberate unsaved bypass charts.

Limitations:
- Necessary standing-loss overlap bound only; wide or internally consistent wrong hulls can pass. Endpoint monotonicity follows from the assumed held reduced ODE; no complete nonlinear/event/dwell trajectory certification by this gate.
- Unchanged engineering TES and HP assumptions, thermal kernel, policy, trace schema 75 and reporting API 0.76. No primary replication, measured validation, equipment calibration, annual or generated-code acceptance; full primary signoffs 0/31.
- Same-agent algorithmic independence: exact Fraction operand bounds and separate 120/160-digit closed exp/log QA call no production MATLAB solver. Binary exports depend on MATLAB reopening original MAT; no independent personnel or independent MAT-parser claim.
- Bounded synthetic normal-mode schedules. Inherited finite span, clock, event collision and segment-budget refusals remain; the added positive multiplication rejects nonfinite loss bounds.
- Four coordinated post-kernel record faults use unsaved in-memory charts and are QA controls, never physical plant simulation results. Accepted SLX is reopened clean after instrumentation.

Next actionable task: Resume primary equipment-map evidence and boundary audit from audit/HP_upstream_boundary_results_v44.md. Seek primary text and performance-correlation supplement for DOI 10.1016/j.tsep.2025.103513; distinguish verified coefficients and domains from metadata and access blockers. Trace refrigerant/water and compressor/auxiliary boundaries before a calibrated backend. Preserve v75-v80 model acceptance and independent nonlinear QA.


## Saved-v80 partition acceptance — 2026-10-13T06:03:28.517890+00:00 / checkpoint v81

UTC 2026-10-13T06:03:28.517890+00:00. Preserved saved Stateflow v80 actually executes 26 complete schedules,
1581 held intervals, 1645 positive segments and 64 interior events;
all six required final modes observed. MATLAB 80 PASS / 0 FAIL;
independent equation/artifact QA 247353 PASS / 0 FAIL;
15 matched partition comparisons PASS / 0 FAIL and four separate reviewer
self-checks PASS. Saved model reopened clean and first fixture replayed bitwise.

Five identical physical input histories were split into 1, 2, 4 and 8 pieces
per original hold. Exact Fraction histories verify operand sums and held inputs.
Closed exp/log trajectories at 120/160 digits independently verify original-MAT
inventory, event ordering/dwell, source/work/loss/service/backup/unmet and reports.
Every compared reporting hull overlaps and every event sequence/time meets the
predeclared budget. Maximum absolute aggregate difference across all 15
comparisons is 5.79E-157 MWh. This is a reconstruction difference, not a
midpoint estimate of a simulated hull. Differences at roughly 160-digit
reviewer precision indicate reconstruction roundoff, not measured plant accuracy.

The practical tradeoff is in the enclosures. For the 48-hour schedule,
splitting 0.5-hour holds into eight 0.0625-hour holds reduces the recovered-source
hull width from about 0.00220020 to 0.000277281 MWh (about 7.94 times narrower),
while the final-inventory hull widens from about 3.36e-12 to 2.59e-11 MWh.
Additional protocol calls tighten the source quadrature rectangles but accumulate
more outward binary roundoff. Smaller steps do not uniformly tighten every hull.

| Physical schedule, split8 | Delivered service (MWh) | Final TES (MWh) | Max aggregate delta (MWh) | Source hull width, split1 → split8 (MWh) | Work hull width, split1 → split8 (MWh) |
|---|---:|---:|---:|---:|---:|
| multiple_cycles_one_call | 0 | 8.13633009 | 1.3e-158 | 0.000292153 → 0.000266396 | 0.000458425 → 0.000417981 |
| OFF_discharge_restart_0p01 | 1 | 9.05366417 | 8.66e-158 | 0.00126909 → 0.00023831 | 0.00202863 → 0.000381174 |
| seasonal_0p5 | 46.9095378 | 5.00818801 | 5.79e-157 | 0.0022002 → 0.000277281 | 0.00334957 → 0.000422453 |
| enable_changes | 3 | 2.9113366 | 6.14e-159 | 3.21965e-14 → 4.68514e-14 | 6.60583e-15 → 9.60343e-15 |
| passive_lambda0.5_E3.0 | 0 | 1.81959198 | 1e-159 | 0 → 0 | 0 → 0 |

No new SLX: actual model remains `matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v80.slx`,
SHA256 `f7032682f4d6c338a99f1425311a807254c3022ba8527dba5f616f53b0ac66be`. Its six-mode Stateflow builder and all prior models,
MATLAB code and status/stageboards are hash-preserved. Checkpoint version is 0.81.
This delivers a fresh executable MATLAB sensitivity harness and independent
physical-schedule comparison, not another runtime monitor.

Evidence `results/partition_sensitivity_v81_20261013T055938_959011Z` includes timestamped MATLAB/Simulink logs, execution receipts,
26 original MAT files and reopened combined MAT, binary exports, numeric CSV,
specification, source snapshots and preservation hashes. Initial restricted
MATLAB startup failure is retained separately; only the successful completed
batch counts. No runtime schedule refusals occurred.

Limits:
- Synthetic bounded normal-mode schedules for the reduced engineering HP/TES equations only; no annual, calibrated equipment, article replication, measured physical validation or generated-code acceptance. Primary signoffs remain 0/31.
- No new SLX or thermal/controller/reporting change: actual saved model 0.80, embedded thermal kernel/trace schema 75 and reporting API 0.76 remain preserved. Checkpoint and model versions differ.
- Same-agent algorithmic independence: Fraction operand histories and 120/160-digit closed exp/log trajectories call no production MATLAB solver. MATLAB reopens original MAT and exports binary; no independent personnel or independent MAT parser claim.
- Sensitivity budget 1e-10 relative to max(1,absolute quantity) is an experiment acceptance threshold, never a relaxed production guard. Hull overlap and widths are also recorded; no midpoint is used as physical truth.
- Five physical schedules and dyadic partitions do not prove arbitrary partition invariance. Existing clock/span/event collision/segment-budget domains and necessary-only runtime monitors remain.

Next actionable task: Resume primary equipment-map evidence and boundary audit from audit/HP_upstream_boundary_results_v44.md. Seek a new accessible route to primary text and the performance-correlation supplement for DOI 10.1016/j.tsep.2025.103513; distinguish verified coefficients/domains from metadata and access blockers. Preserve saved v80 and v81 actual partition evidence; do not repeat the same monitor or sensitivity fixtures without new evidence.


## Saved-v80 approach boundary checkpoint - 2026-10-13T10:29:50.956978+00:00 / v82

# Saved-Stateflow refrigerant approach experiment v82

UTC 2026-10-13T10:29:50.956978+00:00.

Preserved saved v80 actually executes 42 schedules / 78 held intervals / 78 positive segments / 0 interior events. MATLAB 128 PASS / 0 FAIL; independent equation/artifact QA 14765 PASS / 0 FAIL; 48 monotonic comparisons and four separate reviewer self-checks PASS. All six required final modes are observed. The clean saved model is reopened and replayed bitwise.

At source-water 30 C, changing both approaches from 1 K to 10 K increases fixed-output compressor electricity by 62.303507% while delivered service stays 0.25 MWh. At fixed evaporator budget 0.1 MW, source-limited service increases 11.190391% through added compressor work. COP decreases in both cases. Extra condenser output is not extra recovered waste heat.

| Boundary and approaches | Delivered (MWh) | Recovered source (MWh) | Compressor (MWh) | Heating COP |
|---|---:|---:|---:|---:|

| fixed_output_T30_e1_h1 | 0.250 | 0.2152325076 | 0.03476749239 | 7.190625000 |

| fixed_output_T30_e10_h10 | 0.250 | 0.1935711407 | 0.05642885933 | 4.430357143 |

| source_limited_T30_e1_h1 | 0.05807672892 | 0.05000000000 | 0.008076728925 | 7.190625000 |

| source_limited_T30_e10_h10 | 0.06457574180 | 0.05000000000 | 0.01457574180 | 4.430357143 |


Source20 printed pages 8 and 27 were visually verified against preserved publisher bytes. Its compressor balance and refrigerant-temperature convention support the limited derivation. The [university record](https://flore.unifi.it/handle/2158/1432822) lists no attached files; the new [research-group route](https://www.dief.unifi.it/vp-278-research.html) links the DOI, not a supplement. Direct publisher open returned 403 and the PDF-route tool cache missed. Metadata and abstract do not supply calibration coefficients. These observations do not establish global unavailability.


Model `matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v80.slx`, SHA256 `f7032682f4d6c338a99f1425311a807254c3022ba8527dba5f616f53b0ac66be`. Evidence `results/hp_approach_v82_20261013T101754_139297Z` includes timestamped MATLAB/Simulink logs, successful receipt, 42 original MAT files, reopened combined MAT, binary exports, independent numeric CSV, specification, primary observations, source snapshots, reviewer revision and preservation hashes. Failed attempts remain in the directory identified by prior_attempts.json.


Limitations:
- Synthetic reduced constant-cooling-factor HP and ambient-reference TES; no equipment calibration, article replication, measured physical validation, annual or generated-code acceptance. Full primary signoffs remain 0/31.
- Checkpoint 0.82 is an executed sensitivity experiment; saved model remains 0.80, thermal kernel/trace schema 75 and reporting API 0.76. No new SLX or production equation change.
- Approach values, eta=0.5, source coefficient, temperature/glide and auxiliary settings are engineering assumptions. The 2025 commercial-device correlation supplement is not acquired.
- No independent compressor-electricity capacity is enforced. Increased source-limited condenser service at larger approaches comes from added compressor work, not extra waste heat. This is a model-boundary limitation, not a numerical dispatch defect.
- Independent QA is same-agent algorithmic independence: exact Fraction algebra and 120/160-digit exp/log trajectories call no production MATLAB solver. MATLAB reopens MAT for binary export; no independent personnel or independent MAT-parser claim.
- The 36 comparison schedules remain below the hot-water floor and contain no interior events. Six standard fixtures cover final modes. No general nonlinear/variable-source-map sensitivity is proved.
- Restricted startup, first batch JSON cell/struct failure, and first QA single-row-shape failures are retained. The reviewer shape repair is separately hash-sealed; production outputs, equations and tolerances were unchanged.


Next actionable task: Acquire the reference62 primary supplement or inspect the author-group-linked 2022 predecessor DOI 10.1016/j.applthermaleng.2022.118194 as separately labelled primary evidence. Do not substitute predecessor coefficients for the 2025 fit. Trace compressor electrical rating, refrigerant axes, admissible map domain and auxiliary thermal destinations before adding a separate explicit electrical-power capacity backend. Preserve accepted v80 and v81-v82 evidence; no repeated monitor tests without a new hypothesis.



## 2026-10-13T10:44:53.619681+00:00 - v83 actual conservative electrical-ceiling Stateflow

Read STATUS/stageboards v82, full Stateflow acceptance/frontier, current code and existing primary-boundary evidence before changes. Work stayed in this project; Jarvice, unrelated files, settings, scheduler, runner and external publication untouched.

Files added: matlab/simulink/electrical_policy_v83r2.m, matlab/simulink/build_electrical_ceiling_v83r2.m, matlab/simulink/DCHR_Electrical_Dispatch_Stateflow_v83r2.slx, matlab/run_electrical_ceiling_v83r2.m, audit/electrical_ceiling_v83r2.py, audit/run_electrical_ceiling_v83r2.ps1, audit/close_electrical_ceiling_v83_final.py, derivation/results report, STATUS and stageboard twins. All prior production MATLAB/SLX/checkpoints are hash-preserved; shared ledgers appended only.

# Conservative electrical-ceiling Stateflow acceptance v83

UTC 2026-10-13T10:44:53.619681+00:00.

New actual saved model `matlab/simulink/DCHR_Electrical_Dispatch_Stateflow_v83r2.slx` executes 25 schedules / 42 held intervals / 53 positive segments / 11 interior events and all six required modes. MATLAB 113 PASS / 0 FAIL; independent equation/artifact QA 9674 PASS / 0 FAIL; 3 separate reviewer corruptions detected. Four actual saved-chart runtime refusals include a delayed nonbinding raw-rating change. 7 fresh saved-v80 reference comparisons are bitwise equal. The clean saved v83 model is reopened and replayed bitwise.

The chart transforms an explicit finite compressor ceiling into a conservative heat-output ceiling using an outward enclosure of the existing tank-capacity guard. The first candidate is preserved; accepted model release is v83r2. Exact rational QA proves the selected heat rate respects the compressor rating throughout every accepted segment, including hot tank and repeated stop/restart histories. Zero rating produces exact zero HP heat and compressor work. Existing source, water, thermal, TES, dwell and energy guards remain embedded.

| Initial TES (MWh) | Approaches evap/cond (K) | Compressor ceiling (MW) | Effective heat cap (MW) | Delivered service hull (MWh) | Compressor energy hull (MWh) |
|---|---|---:|---:|---|---|
| 3 | 1/1 | 0.05 | 0.2216761364 | [0.1108380681818175, 0.11083806818181761] | [0.01238232130209914, 0.012382321302099401] |
| 3 | 10/10 | 0.05 | 0.1682056452 | [0.08410282258064472, 0.08410282258064483] | [0.016951134062284226, 0.016951134062284545] |
| 8.5 | 1/1 | 0.05 | 0.2216761364 | [0.1108380681818175, 0.11083806818181761] | [0.021516160851772013, 0.021518499182792247] |
| 8.5 | 10/10 | 0.05 | 0.1682056452 | [0.08410282258064472, 0.08410282258064483] | [0.022762248575755217, 0.022764009757021562] |

Model SHA256 `6c3923c30e7058ec07e8d6f1667a5b9aae4db012775cba52bb0fb8d9cd98e1dd`. Evidence `results/electrical_ceiling_v83r2_20261013T104142_686092Z` contains timestamped MATLAB/Simulink and independent Python logs, execution receipt, original and reopened MAT, trace/certificate binary exports, numeric CSV, specification, sealed source snapshots, preservation hashes and fault logs. Prior attempted sources and logs remain separately linked in prior_attempts.json. No new primary article content was acquired or claimed. Derivation: `audit/Electrical_ceiling_derivation_v83.md`.

Limitations:

- Conservative global maximum-temperature cap, not a maximal instantaneous electrical limiter. Colder operation can leave compressor capacity unused.
- Synthetic compressor rating/constant cooling-factor reduction only; no acquired equipment supplement, calibration, article replication, measured physical validation, annual or generated-code acceptance. Full primary signoffs remain 0/31.
- Compressor electricity alone is limited. Configured auxiliary electricity remains separate and can make total external electricity exceed the compressor rating.
- The raw 26-operand policy is immutable within a schedule. Negative/nonfinite ceilings, invalid axes, nonfinite intermediate arithmetic and inherited span/clock/event-collision/segment-count domains reject.
- Trace schema 75 binds the effective 25-operand policy; separate certificate output binds raw electrical policy plus effective cap. Reporter v76 is preserved and does not itself authenticate raw electrical inputs.
- Same-agent independent exact Fraction and 120/160-digit closed exp/log algorithms call no production MATLAB solver. MATLAB reopens MAT for binary export; no independent personnel or independent MAT parser claim.
- Saved model executes analytic physical segments inside macro protocol ticks, not at solver-clock events. Tested bounded schedules do not establish arbitrary-input acceptance.
- Initial restricted MATLAB startup failure, builder quoting syntax error and first v83 candidate/proof-refinement evidence are retained in prior attempt evidence; only the successful corrected batch counts.

Next actionable task: Audit the conservatism of the new global-Tmax compressor ceiling against an independently derived temperature-conditioned electrical limiter on identical cold/hot and charging histories. Quantify foregone delivered service and source recovery before any new limiter implementation. Seek the reference62 primary equipment supplement/rating domain via a new accessible route; synthetic Pmax and constant cooling factor must not become equipment calibration. Preserve v80-v83.

Stop after this coherent executed deliverable and clear handoff.


## v84 electrical conservatism evidence and handoff

# Saved-Stateflow electrical conservatism experiment v84

UTC 2026-10-13T10:57:16.506408+00:00.

Preserved saved v83r2 actually executes 19 complete schedules / 56 held intervals / 67 positive segments / 11 interior events, with all six required modes. MATLAB 79 PASS / 0 FAIL; independent equation/artifact QA 12063 PASS / 0 FAIL; 3 separate reviewer corruptions detected. One fresh nonbinding saved-v80 reference comparison and clean saved-v83r2 reopening are bitwise equal.

The global maximum-temperature electrical cap is safe but leaves useful capacity unused on every one of twelve tested service/charging histories. A new independently derived temperature-conditioned comparator quantifies the gap on identical raw policies, initial conditions and four 0.25-hour inputs. It is a hypothetical reduced-model calculation, not a saved Stateflow dynamic controller. No hull midpoint is used: actual totals are reconstructed from original-MAT binary exports and checked against reporting hulls.

| Case | Global HP heat (MWh) | Conditioned HP heat (MWh) | Additional recovered source (MWh) | Additional delivered service (MWh) | Additional final TES (MWh) | Heat increase (%) |
|---|---:|---:|---:|---:|---:|---:|
| service_E3.0_a1.0 | 0.2216761364 | 0.4475657895 | 0.2006542957 | 0.2258896531 | 0 | 101.9007534 |
| service_E3.0_a10.0 | 0.1682056452 | 0.2480743243 | 0.06377094729 | 0.07986867916 | 0 | 47.48275784 |
| service_E4.95_a1.0 | 0.2216761364 | 0.4475657895 | 0.2006542957 | 0.2258896531 | 0 | 101.9007534 |
| service_E4.95_a10.0 | 0.1682056452 | 0.2480743243 | 0.06377094729 | 0.07986867916 | 0 | 47.48275784 |
| service_E8.5_a1.0 | 0.2216761364 | 0.2569520548 | 0.0284116187 | 0.03527591843 | 0 | 15.91326834 |
| service_E8.5_a10.0 | 0.1682056452 | 0.1844724771 | 0.01185781866 | 0.0162668319 | 0 | 9.67080022 |
| charge_E3.0_a1.0 | 0.2216761364 | 0.4475657895 | 0.2006542957 | 0 | 0.2033006878 | 101.9007534 |
| charge_E3.0_a10.0 | 0.1682056452 | 0.2480743243 | 0.06377094729 | 0 | 0.07188181125 | 47.48275784 |
| charge_E4.95_a1.0 | 0.2216761364 | 0.4327021812 | 0.1861140359 | 0 | 0.1899234404 | 95.19565268 |
| charge_E4.95_a10.0 | 0.1682056452 | 0.2463130016 | 0.0621335841 | 0 | 0.07029662083 | 46.43563324 |
| charge_E8.5_a1.0 | 0.2216761364 | 0.2537676976 | 0.02570033293 | 0 | 0.02888240508 | 14.47677758 |
| charge_E8.5_a10.0 | 0.1682056452 | 0.1834623063 | 0.01107785522 | 0 | 0.013730995 | 9.070243211 |

For service-only cold E=3 MWh and approaches 1/1 K, delivered service rises from 0.2216761364 to 0.4475657895 MWh in one hour. The extra heat is supported by both more recovered source and more compressor work. At hot E=8.5 MWh the gap is smaller. Charging near the hot-water floor at E=4.95 MWh crosses that floor on both compared paths; the nonlinear comparator uses a separated logarithmic solution and explicit crossing time, independently checked by RK4 at 1024/2048 steps. The dynamic endpoint stays strictly below the stop threshold in every comparator case.

Model `matlab/simulink/DCHR_Electrical_Dispatch_Stateflow_v83r2.slx`, SHA256 `6c3923c30e7058ec07e8d6f1667a5b9aae4db012775cba52bb0fb8d9cd98e1dd`. No production model or prior checkpoint changed. Evidence `results/electrical_conservatism_v84_20261013T105537_783028Z` contains timestamped MATLAB/Simulink and Python logs, execution receipt, 19 individual original MAT files and a reopened aggregate MAT, binary exports, comparison/trajectory CSV, predeclared specification, source snapshots and preservation hashes. Derivation: `audit/Electrical_conservatism_derivation_v84.md`. Prior failed scope attempts: `results/electrical_conservatism_v84_20261013T105044_893030Z` and `results/electrical_conservatism_v84_20261013T105247_497281Z`.

Limitations:

- Checkpoint 0.84 is a fresh saved-v83r2 experiment and independent hypothetical comparator; no new SLX or dynamic-cap Stateflow implementation is accepted.
- Twelve comparison histories are zero-loss, HP initially ON, service-only or charge-only, with disabled boiler/TES discharge and no stop/restart on the dynamic paths. Six modes and an interior event control execute separately.
- Dynamic heat/source gains use increased compressor work. Service-only gains are delivered service; charging gains are stored inventory, never delivered district heat or equal-electricity savings.
- Reduced constant cooling-factor/refrigerant proxy equations, approach values, storage efficiencies and 0.05 MW compressor ratings are synthetic engineering assumptions. No new primary text/signoff or commercial supplement was acquired; full signoffs remain 0/31.
- Same-agent algorithmic independence: Fraction/binary inputs and 120/160-digit closed equations call no production MATLAB solver; a separate RK4 integrates the comparator ODE. MATLAB reopens MAT for binary export; no independent personnel or independent MAT parser claim.
- Independent comparator budgets are 1e-100 precision agreement, 1e-110 primitive residual and 1e-10 MWh RK4 endpoint agreement, not relaxed production guards or measured accuracy.
- No positive-loss dynamic comparator, mixed service/charge optimization, source-map calibration, annual performance, article replication, measured physical validation or generated-code acceptance.
- Inherited saved-model span, clock, segment-count and event-collision domains remain. Its protocol ticks are not solver-clock event times.
- Initial restricted MATLAB startup failed. Two complete candidates each passed MATLAB 79/79 and 11008 independent checks but failed the interior-event coverage gate at 0.2/0.5 MW. Both attempts and original snapshots are preserved; only the corrected 1000 MW nonbinding event-fixture batch and QA count as checkpoint acceptance.

Next actionable task: Derive and independently verify a temperature-conditioned ON charging backend with positive passive loss, hot-water floor crossing and TES stop events before integration into an additive six-mode Stateflow model. The affine held-power kernel cannot accept a start-temperature electrical cap safely while charging. Choose a certified whole-segment constant cap or a certified nonlinear flow/event solver explicitly, bind raw and effective policies with versioned trace/report provenance, and regress v84 histories plus zero/nonbinding ratings and stop/restart/dwell/refusal controls. Preserve v80-v84. Keep primary equipment supplement acquisition/calibration open; synthetic Pmax is not a commercial rating.

Stop after this coherent executed deliverable and clear handoff.


## 2026-10-13T11:16:28.197369+00:00 - v85 certified reachable-temperature Stateflow

Read current STATUS/stageboards, acceptance, frontier and relevant code before edits. Work stayed inside this project. Added versioned cap, builder/SLX, execution and QA harnesses, derivation/results, status/stageboard twins. All prior models, MATLAB and checkpoints are hash-preserved; shared ledgers append-only.

# Certified reachable-temperature Stateflow acceptance v85

UTC 2026-10-13T11:16:28.197369+00:00.

New saved `matlab/simulink/DCHR_Electrical_Dispatch_Stateflow_v85.slx` actually executes 28 schedules / 87 held intervals / 100 positive segments / 13 interior events, with all six modes. MATLAB 129 PASS / 0 FAIL; independent QA 25354 PASS / 0 FAIL; 3 separate reviewer corruptions detected. Seven actual chart refusals include exhausted/mutated horizon and uncertified ON dwell. 8 fresh saved-v80 comparisons and clean saved-v85 reopening are bitwise equal. Every schedule also executes preserved v83r2 on identical inputs.

A declared-horizon inventory upper bound replaces the global maximum-temperature electrical cap. It safely raises available heat for cold schedules while retaining the verified held-power loss/event kernel. Positive-loss charging crosses the hot-water floor; binding stop and repeated stop/cutoff/restart histories execute and pass independent closed-equation and pointwise electrical-power QA.

| Case | v83r2 HP heat (MWh) | v85 HP heat (MWh) | Extra recovered source (MWh) | Extra compressor work (MWh) | Extra delivered service (MWh) | Extra final TES (MWh) |
|---|---:|---:|---:|---:|---:|---:|
| service_E3.0_a1.0 | 0.2216761364 | 0.4475657895 | 0.2006542957 | 0.02523535740 | 0.2258896531 | 0e-55 |
| service_E8.5_a1.0 | 0.2216761364 | 0.2460272341 | 0.01961264608 | 0.004738451643 | 0.02435109772 | 0e-55 |
| charge_E4.95_a1.0 | 0.2216761364 | 0.4134373660 | 0.1691661984 | 0.02259503115 | 0.00 | 0.1725851066 |
| loss_charge_E4.95_a1.0 | 0.2216761364 | 0.4134373660 | 0.1692986016 | 0.02246262799 | 0.00 | 0.1717250503 |

Gains use additional compressor work. Charging gains are inventory, not delivered district heat. Comparisons use closed equations reconstructed from original-MAT binary exports, never reporting-hull midpoints.

Model SHA256 `2a9de22c0c55e8c4a87f7b0e0cfe9cd97db08c991f09d98361b009de310adde7`. Timestamped execution/QA logs, original/reopened MAT, binary traces/certificates, source/preservation seals, predeclared cases and comparison evidence: `results/reachable_cap_v85_20261013T111338_510493Z`. Derivation: `audit/Reachable_cap_derivation_v85.md`.

Limitations:

- One certified constant cap over the declared horizon, not a maximal nonlinear instantaneous electrical limiter. Ignoring passive loss in the reachability bound is conservative; larger horizons can recover global-cap behavior.
- Compressor rating, approaches, cooling-factor and storage parameters remain synthetic. No new primary text, equipment calibration, article replication, measured physical validation, annual or generated-code acceptance; full signoffs remain 0/31.
- Auxiliary electricity is separate and total external electricity may exceed the compressor ceiling.
- Raw 27-operand policy and declared horizon are immutable. Thermal schema 75/reporter 76 authenticate effective policy; separate 29-operand certificate and independent QA bind raw policy, cap and reachable inventory.
- Same-agent algorithmic independence: exact Fraction and 120/160-digit closed exp/log equations call no production MATLAB solver. MATLAB reopens MAT for binary export; no independent personnel or independent MAT parser.
- Inherited finite-span, physical-clock, segment-count and unresolved-event domains remain. Analytic event segments execute within macro protocol ticks, not solver-clock events.
- Restricted startup failure, first successful 122-assertion candidate with stale inherited release label, and corrected 124-assertion/24930-pass candidate with one missing-cutoff-coverage QA failure are retained. Final expanded suite adds a focused cutoff witness; saved production model remains v85 and execution harness v85r2.

Next actionable task: Compare declared-horizon cap dependence against the v84 nonlinear comparator at H=1/2/4 hours and held-input partitions on identical histories, then derive a versioned interval-renewal contract before changing the immutable effective-policy kernel. Seek primary equipment supplement/calibration through a new accessible route. Preserve v80-v85 and all failed attempts.

Stop after this coherent executed deliverable and handoff.


## 2026-10-13T11:30:20.465974+00:00 — checkpoint v86

# Saved-v85 horizon and partition sensitivity v86

UTC 2026-10-13T11:30:20.465974+00:00.

The preserved actual saved v85 Stateflow model executes 64 schedules / 243 held intervals / 256 positive segments / 13 interior events, with all six required modes. MATLAB 274 PASS / 0 FAIL; independent equation/artifact QA 65387 PASS / 0 FAIL; three separate reviewer corruptions detected. Seven actual chart refusals and fresh saved-v80/global-v83r2 comparisons execute; clean saved-v85 reopening is bitwise equal. No new SLX is created.

Twelve identical one-hour v84 histories execute at nominal H=1/2/4. Larger declared horizon never increases the effective cap or reconstructed HP heat. Twelve paired partition comparisons (0.125/0.5 versus 0.25 h) preserve the cap exactly and match closed trajectories to the predeclared 1e-90 budget; maximum observed difference 5.91e-158 MWh-equivalent across reconstructed fields. Original report hulls overlap. The hypothetical nonlinear comparator is independently reconstructed at 120/160 digits and checked against floor-aware RK4; it is not an implemented renewable controller.

| History | Nominal H (h) | Cap (MW) | Actual HP heat (MWh) | Hypothetical dynamic HP heat (MWh) | Gap (MWh) |
|---|---:|---:|---:|---:|---:|
| service_E3.0_a1.0 | 1 | 0.4475657895 | 0.4475657895 | 0.4475657895 | 2.120244769e-15 |
| service_E3.0_a1.0 | 2 | 0.4475657895 | 0.4475657895 | 0.4475657895 | 2.120244769e-15 |
| service_E3.0_a1.0 | 4 | 0.4475657895 | 0.4475657895 | 0.4475657895 | 2.120244769e-15 |
| charge_E4.95_a1.0 | 1 | 0.4137898886 | 0.4137898886 | 0.4327021812 | 0.01891229264 |
| charge_E4.95_a1.0 | 2 | 0.3816234725 | 0.3816234725 | 0.4327021812 | 0.05107870876 |
| charge_E4.95_a1.0 | 4 | 0.3317913188 | 0.3317913188 | 0.4327021812 | 0.1009108624 |
| charge_E8.5_a1.0 | 1 | 0.2461297442 | 0.2461297442 | 0.2537676976 | 0.007637953378 |
| charge_E8.5_a1.0 | 2 | 0.2363830644 | 0.2363830644 | 0.2537676976 | 0.01738463319 |
| charge_E8.5_a1.0 | 4 | 0.2216761364 | 0.2216761364 | 0.2537676976 | 0.0320915612 |

Nominal H=1 uses actual H=1+2^-40 h, a predeclared certificate margin (~3.27 nanoseconds); all simulated histories remain exactly one hour. The separately executed exact H=1 endpoint probe was REFUSED by the saved declared-horizon upper-clock guard. Its original MAT and actual diagnostic are retained. This outcome is an implementation-domain observation, not a changed production guard.

The exact-rational charging witness proves that an electrical cap taken only at the initial temperature can exceed its compressor rating at the charged endpoint. The proposed renewal contract therefore certifies a reachable inventory upper bound over each renewal window and preserves clock, inventory hull, latch, dwell and correlated event/energy memory. Current v85 raw/effective policy immutability does not implement that contract; restarting the model is not renewal.

Evidence `results/horizon_sensitivity_v86_20261013T112610_976653Z` contains timestamped MATLAB/Simulink and independent QA logs, execution receipts, original/reopened MAT, binary exports, predeclared specification, source snapshots and preservation hashes, numeric trajectory CSV and 48 comparisons. Model SHA256 `2a9de22c0c55e8c4a87f7b0e0cfe9cd97db08c991f09d98361b009de310adde7`. Derivation: `audit/Horizon_renewal_derivation_v86.md`.

Files added: `matlab/run_horizon_sensitivity_v86.m`, `audit/run_horizon_sensitivity_v86.ps1`, `audit/scaffold_horizon_v86.py`, `audit/horizon_sensitivity_v86.py`, `audit/close_horizon_v86.py`, `audit/Horizon_renewal_derivation_v86.md`, `audit/Horizon_sensitivity_results_v86.md`, and v86 STATUS/stageboard twins. Shared engineering progress, acceptance and research-frontier ledgers are appended only. Prior MATLAB, SLX and checkpoints are hash-preserved.

Limitations:

- No new SLX or renewal implementation: actual saved model remains 0.85, checkpoint/harness is 0.86.
- Nominal H=1 uses actual certificate horizon 1+2^-40 h. Exact H=1 endpoint outcome is retained separately; no elapsed history or production tolerance changed.
- The nonlinear comparator is hypothetical, zero-loss, HP initially ON and nonbinding except for compressor rating, with no switching. Positive-loss/event controls execute the actual saved model separately.
- Additional heat may use more compressor work; charging inventory is not delivered heat or equal-electricity savings.
- Same-agent algorithmic independence: exact-binary Fraction/120-160 digit closed equations and separate RK4 call no production MATLAB solver. MATLAB reopens MAT; no independent personnel or MAT parser claim.
- Synthetic rating, refrigerant proxy, approaches, efficiencies and fixtures are engineering assumptions. No new primary text/signoff, equipment calibration, article replication, measured physical validation, annual or generated-code acceptance. Full signoffs 0/31.
- Inherited span, clock uncertainty, segment-count and event-collision refusal domains remain. Protocol ticks are not solver-clock event times. Auxiliary electricity is outside compressor ceiling.
- Restricted MATLAB startup failed before model loading; the authorized unrestricted local batch and all retained logs provide the execution evidence.

Next actionable task: Implement additive interval-renewable electrical cap in the SAME six-mode saved Stateflow chart using audit/Horizon_renewal_derivation_v86.md. Preserve raw policy, retained inventory hull, physical clock, latch, ON/OFF age and correlated event/energy memory; certify expiry, generation and provenance in a versioned schema/reporter. Regress v86 histories/partitions and positive-loss, floor, stop/cutoff/restart/dwell, zero/nonbinding and corruption/refusal controls with independent original-MAT closed equations. Do not reset the simulation or use the start-temperature cap alone. Preserve v80-v86. Primary equipment supplement/calibration remains open.

Stop after this coherent executed deliverable and handoff.
