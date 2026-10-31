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
