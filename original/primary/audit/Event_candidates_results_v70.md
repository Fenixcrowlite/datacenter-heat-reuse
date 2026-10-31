# Executed mode-conditioned event candidate interface v70

UTC 2026-10-12T02:46:29.479645+00:00. New saved model: `matlab/simulink/DCHR_Event_Candidates_Stateflow_v70r2.slx`.
Actual normal-mode simulations execute all six states and candidate records.
Sampled service remains schema 66; earliest-event switching is not accepted.

MATLAB **1147 PASS / 0 FAIL**; independent QA
**47316 PASS / 0 FAIL**; 37 runs / 450 protocol ticks;
414 v30 reference comparisons, 8 actual runtime rejections and
8 detected reviewer corruptions.

The v69 inactive HP-only cutoff contact and delayed strict witnesses now pass.
OFF/dwell-blocked charging has no stop root. Zero/positive-loss TES discharge
uses negative forcing in the restart certificate. Genuine active stop/cutoff
boundary collisions and overlapping cutoff/restart readiness still reject.
Separated cutoff-first/restart-first and above-stop future charge sink controls
execute. Repeated dt=0.25/0.5/1 and v68 span boundary regressions pass.

Evidence: `results/event_candidates_v70_20261012T024414_059326Z`. Timestamped MATLAB log/exit receipt, sealed source/model
snapshots, original/reopened MAT and little-endian binary exports, plant CSV,
`candidate_records_v70.csv`, closed-form root-box/source/work/service QA and
baseline preservation hashes retained. No earlier model/checkpoint overwritten.

Development failures retained: 02:36:04 sandbox startup plus harness matrix
scalar-reduction failure; 02:37:45 JSON fault-decoding failure; 02:39:20 sampled
zero-loss cutoff-domain rejection; 02:41:13 MATLAB 1133/3 and independent
47208/4 due ordering fixtures omitting etaD and the cutoff-domain fixture,
including failed receipts. Preflight-only specification folders also retained.
All are under `results/event_candidates_v70_*`; none was counted as acceptance.
The initial v70 SLX is preserved. Additive v70r2 retains unresolved derivative
records and rejects their strict consumption; a near-equilibrium witness passes.
Finalization uses the completed sealed execution, not a compile-only prototype.

Limitations:

- New saved v70 executes prospective mode-conditioned candidate records in the same chart. Sampled service/inventory schema remains 66. Candidates do not split intervals or switch at roots; general repeated earliest-event dispatch remains OPEN.
- Candidate powers precede sampled full-horizon withholding and cannot be delivered over an unsplit interval. The consumer must recompute after any earlier event; forcing beyond cutoff is hypothetical.
- Conditional normal-mode outward arithmetic and conservative eligibility hulls; generated code not tested.
- Independent QA uses same-agent algorithmically separate Fraction/120/160-digit exp/log/corner and first-law calculations, not independent personnel or measured validation.
- Original MAT reopened and binary-exported by MATLAB; no independent HDF5 parser. Stateflow license and actual chart execution observed; empty version metadata retained.
- Synthetic engineering equipment/thresholds; no new primary text, calibration, article replication or physical validation. Full source signoffs remain 0/31.
- Development startup, harness matrix assertion, JSON fault decoding, sampled cutoff-domain edge and ordering-fixture efficiency omission retained. Initial v70 model preserved; accepted v70r2 also rejects enabled derivative ambiguity. Final sealed execution passes.

Next actionable task: Implement one certified repeated earliest-event cycle in an additive SAME six-mode Stateflow chart using v70 enabled candidates. Carry threshold identity, root-time hull and correlated inventory/source/work/loss/service/clock offsets and OFF age across each segment; never substitute a root midpoint. Recompute forcing and candidates after cutoff/stop/restart and held input boundaries. A restart readiness prediction after cutoff is invalid under the old forcing. Retain strict collision rejection and dwell proofs; compare original-MAT event service/source/work enclosures with an independent exact-binary closed-form event trajectory. Regress inactive-contact/delayed/strict, forced discharge restart, pair ordering controls, future charge sink, repeated dt=0.25/0.5/1 and lambda*duration=1. Preserve v57-v70. Primary calibration, article replication and measured validation remain OPEN.
