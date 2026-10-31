# v22 Stateflow dispatch: independent equation and mode review

Reviewer scope: mathematical derivation and physical boundary review independent of the v22 builder and QA oracle. The reviewer read `STATUS_v21.json`, `MASTER_STAGEBOARD_v21.md`, `audit/research_frontier_2026_10_08.md`, `automation/STATEFLOW_ACCEPTANCE.md`, and the v14 HP / v16 TES / v16 sequential MATLAB implementations before reviewing the new model. No primary article or equipment data is newly verified by this review. All equations below are first-law deductions or explicitly declared engineering assumptions; no publication is credited for these model equations.

## Boundary, notation and domain

One fixed-duration interval has length `dt` in hours. Powers are MW and stored thermal energies are MWh. The boundary starts at recovered source heat available to the HP evaporator and ends at useful supplied heat and the TES external ports. It excludes source heat capture, HX pinch, network transport, pumps, fuel-to-boiler conversion, weather and economics.

Let `D >= 0` be demand; `S >= 0` recovered source heat available; `H >= 0` HP condenser heat; `W >= 0` compressor electricity; `U >= 0` evaporator source extraction; `B_max >= 0` finite backup heat capacity. TES has initial state `0 <= E <= K`, capacity `K >= 0`, charge/discharge port limits `P_c >= 0`, `P_d >= 0`, efficiencies `0 < eta_c, eta_d <= 1`, loss coefficient `lambda >= 0`, `dt > 0`, and `0 <= lambda*dt <= 1`. All numeric inputs and parameters must be finite real scalars.

The HP heating surrogate requires reservoir proxy temperatures `T_h > T_c > 0 K`, capacity `H_cap >= 0`, `cop_min > 1`, `cop_max >= cop_min`, Carnot fraction `0 < eta_C <= 1`, and part-load penalty `0 <= p < 1`. A polynomial alternative requires finite coefficients and a predicted COP no larger than reservoir Carnot COP. Temperature proxy use does not establish actual refrigerant or heat-exchanger temperatures.

## Independent derivation

1. HP first law is `H = U + W`. With heating COP `C = H/W`, this gives `W = H/C` and `U = H*(1 - 1/C)`. At zero compressor work, operating COP is undefined; reporting NaN for an off HP is appropriate.
2. For two reservoir proxies, nonnegative entropy production gives `H/T_h - U/T_c >= 0`, hence `C <= T_h/(T_h-T_c)`. The code's COP floor is an operating eligibility cutoff, not an upward efficiency adjustment.
3. The declared part-load assumption is `C(H) = C_nom*(1-p+p*H/H_cap) = a+b*H`, with `a = C_nom*(1-p)` and `b = C_nom*p/H_cap`. On the admissible interval `C >= cop_min > 1`, `dU/dH = 1-a/C^2 > 0`, because `0 <= a <= C` and therefore `a/C^2 <= 1/C < 1`. The source-limited feasible HP output can thus be found by monotone bisection. When `H_cap = 0`, the component must return off before forming `b`.
4. Standing loss is applied first: `E_a = E*(1-lambda*dt)`, `L_s = E-E_a`. This is an operator-split, linear-retention assumption. Feasible TES charge port room is `R_c = min(P_c, (K-E_a)/(eta_c*dt))`.
5. The HP output request is `R = D + R_c`. The HP component returns the greatest feasible `0 <= H <= min(R,H_cap)` on its admissible operating interval, respecting `U <= S`.
6. Direct useful HP heat is `H_d = min(H,D)`. TES charge and discharge external port powers are mutually exclusive:

   `Q_c = min(max(H-D,0), P_c, (K-E_a)/(eta_c*dt))`

   `Q_d = min(max(D-H,0), P_d, E_a*eta_d/dt)`.

   Since `H <= D+R_c`, all surplus HP heat fits charge room and the external charging power limit. Thus `H = H_d+Q_c`, except floating-point roundoff. No condenser heat rejection term is needed within this request policy.
7. TES update is `E_next = E_a + eta_c*Q_c*dt - Q_d*dt/eta_d`. The charge bound proves `E_next <= K`; the discharge bound proves `E_next >= 0`. Endpoint clipping can correct roundoff only; silently clipping a materially invalid state would break the model contract.
8. External port conversion losses are `L_c = (1-eta_c)*Q_c*dt` and `L_d = (1/eta_d-1)*Q_d*dt`, both nonnegative. TES port closure is `E + Q_c*dt - Q_d*dt = E_next+L_s+L_c+L_d`.
9. After HP and TES, `F = max(D-H_d-Q_d,0)`, backup heat is `B = min(B_max,F)`, and unmet demand is `M = F-B`. Useful supplied heat is `Y = D-M = H_d+Q_d+B`. Unmet demand is an accounting deficit, not a physical sink.
10. The complete interval first-law residual is

    `r = (U+W+B)*dt + E - Y*dt - E_next - L_s - L_c - L_d`.

    Substituting the HP first law, complete HP allocation, demand closure and TES closure gives identically `r = 0`. Stored initial energy and compressor electricity are both necessary terms. Boiler heat is an input at the thermal boundary; this does not audit fuel energy or combustion efficiency.

## Required mode semantics

The six required modes are supervisory labels, with descending priority `UNMET_DEMAND (5) > BACKUP (4) > STORAGE_DISCHARGE (3) > STORAGE_CHARGE (2) > HEAT_RECOVERY (1) > IDLE (0)`.

| Mode | Guard after feasible HP/TES allocation | Required allocation meaning |
| --- | --- | --- |
| UNMET_DEMAND | `M > 0` | HP direct, TES discharge and saturated backup remain active when available. |
| BACKUP | `M = 0` and `B > 0` | HP direct and TES discharge may remain active alongside backup. |
| STORAGE_DISCHARGE | `B = M = 0` and `Q_d > 0` | Direct HP heat and TES discharge serve demand. |
| STORAGE_CHARGE | `Q_c > 0`, no discharge/backup/unmet | Direct HP demand service may coexist with charging. |
| HEAT_RECOVERY | `H_d > 0`, no charge/discharge/backup/unmet | Demand is served directly by the HP. |
| IDLE | All port powers and unmet demand are zero | Standing losses may still lower TES state. |

This is a justified equivalent to six mutually exclusive plant-state labels; it does not mean only one device can operate. In particular, a BACKUP or UNMET_DEMAND state that omits prior HP or TES contributions would be physically wrong. The chart must determine and execute its state's allocation, rather than merely expose a label computed entirely in an external MATLAB controller.

Zero demand alone does not imply IDLE. Under the v16 request policy, source availability plus TES room can produce STORAGE_CHARGE with `D = 0`. A zero-demand IDLE test needs zero feasible HP heat (for example no recovered source), or no feasible storage room. Hysteresis, minimum dwell time, fault handling and cycling are absent and must remain explicit limitations.

## Independent hand examples

These values are arithmetic consequences of assumed inputs, not observations or article values. Set `dt = 0.5 h`, `K = 20 MWh`, `E = 10 MWh`, `lambda = 0.01 /h`, `eta_c = 0.9`, `eta_d = 0.8`, `P_c = 4 MW`, `P_d = 3 MW`. Standing loss is `0.05 MWh` and `E_a = 9.95 MWh`.

- A feasible HP surplus of 4 MW gives `Q_c = 4 MW`, `E_next = 11.75 MWh`, `L_c = 0.2 MWh`, and `L_d = 0`. TES closure is `10+2 = 11.75+0.05+0.2` MWh.
- A remaining demand deficit of 4 MW gives `Q_d = 3 MW`, `E_next = 8.075 MWh`, and `L_d = 0.375 MWh`. TES closure is `10-1.5 = 8.075+0.05+0.375` MWh. With backup limit 2 MW, the remaining 1 MW is served by backup: mode BACKUP despite simultaneous TES discharge.
- A remaining demand deficit of 6 MW gives the same 3 MW TES output, backup saturates at 2 MW, and unmet demand is 1 MW: mode UNMET_DEMAND. Omitting TES from this state's allocation would incorrectly raise unmet demand to 4 MW.

## Validation limits

Exact discrete port closure is necessary but does not establish real system validity. Linear standing retention depends on interval partition: with `E = 10 MWh` and `lambda = 0.2 /h`, one 2 h interval leaves 6 MWh while two 1 h intervals leave 6.4 MWh. The v22 model should reproduce the declared v16 numerical policy, not silently label it an exact continuous leakage model. New stored heat experiences no standing loss until the next interval.

Tests should check generated Stateflow states and guarded transitions, execution timing at the first sample, delay-state continuity, all six modes, zero-capacity storage, storage power/energy endpoints, off-COP behavior, part-load availability, finite boiler saturation, nonnegative flows, bounded TES states, port closures and reference parity. A transition label alone or a compile-only run is insufficient evidence.

## Implementation source review

Inspected `matlab/simulink/build_dispatch_stateflow_v22.m`, `dchr_stateflow_hp_v22.m`, `stateflow_choose_mode_v22.m`, and `stateflow_allocate_v22.m`. The new builder creates an actual Stateflow chart with six named states, input-dependent guarded transitions, a guarded default junction, and allocation on state entry/during actions. The Unit Delay feedback stores allocation element 8 (`E_next`) as the next interval's `E`; HP request and chart therefore use the same current interval energy. An input-dependent default junction avoids assuming startup IDLE when the first demand interval needs service.

The source equations match the independently derived loss-first contract: HP uses v14, request is demand plus charge room after standing loss, backup/unmet states retain HP and TES discharge, and reported system residual includes compressor electricity and all three TES losses. Selection and allocation helpers are embedded in the chart through copied source at build time. Consequently the generated `.slx` must be rebuilt if those helper files change; checking only the current external helper code does not certify an older saved model. The HP adapter remains external host MATLAB and calls v14 at runtime. This is explicitly a normal-mode execution design, not proof of standalone code generation.

Initial source review found domain gaps in the new adapter: backup capacity `p(8)` was unchecked, a negative demand `x(4)` could survive when charging room kept total HP request nonnegative, and all nonzero backend codes were silently interpreted as the polynomial backend. The implementation owner corrected these findings. Reinspection verified finite real vector/size checks for `x`, `p`, `h`, explicit nonnegative demand and backup checks, and backend restricted to codes 0/1. The adapter's v16 preview rejects invalid TES parameters/state, and the v14 call rejects source/temperature/HP configuration domains. Thus these three findings are resolved at source-review level; corresponding runtime rejection results remain part of the executable acceptance gate.

The allocation helper currently clips `E_next` to `[0,K]`; analytical power bounds make that correction roundoff-only under valid inputs. Executable tests still need to establish that no material clipping hides a numerical or scheduling defect, by checking TES port closure independently.

Source-review conclusion: no unresolved mathematical or physical-allocation defect identified in the inspected v22 source under the stated domains.

## Independent generated-model archive inspection

`audit/inspect_stateflow_archive_v22.py` reads the generated `.slx` ZIP/XML directly using Python standard-library tools; it imports neither the production dispatch kernel nor the QA oracle and invokes no MATLAB/Stateflow runtime API. It verifies the six actual operating-state allocation actions, all 30 ordered mode transitions and six initial choices, correct destination mode guards, 37 total / 36 guarded transitions, absence of unconditional test guards, discrete parameterized chart sample time, and exact normalized equality of both embedded helpers with their `.m` sources. It also checks actual model XML for chart-output-to-selector-to-Unit-Delay feedback, state feedback to both HP and chart, initial energy/sample-time/index-8 settings, and scenario-to-HP-to-chart-to-numeric-trace connectivity.

Expanded inspection passed 18/18 with 0 failures; evidence: `audit/stateflow_archive_review_v22_20261009T025811_396033Z.json` and `automation/logs/stateflow_archive_review_v22_20261009T025811_396033Z.log`. The report records the generated-model SHA256 and source helper SHA256 values. The earlier 13-check inspection is preserved separately; this later run added guard-destination and feedback-connectivity checks. Archive/source provenance establishes that the inspected saved model contains the intended controller, but does not itself execute simulation or validate equipment physics.

## Reviewed executable evidence

Inspected the expanded acceptance artifacts in `results/stateflow_v22_20261009T025644993Z`, including summary, actual interval CSV, assertions, model structure and independent Python QA report. MATLAB R2026a Update 5 reports 476/476 passing checks, 10 scenarios and 39 executed intervals, with all six modes observed. The model structure records Stateflow license availability, the six actual states, guarded topology and Unit Delay. Direct runtime adapter rejection checks pass for negative demand, negative backup, invalid backend, zero charge efficiency and zero timestep, closing the initial domain findings.

The independent QA report records 2860/2860 passing actual-trace checks with no failures across all 39 intervals; 27 intervals have the separate fixed-COP closed-form oracle. The remaining 12 exercise the earlier independent v18 reference scenarios and verified v16 parity, including nonzero HP part-load penalty. The model-reported maximum interval energy residual is `7.7715611723760958e-16 MWh`; the independent calculation from the saved CSV reports `2.867150961094467e-14 MWh`. Both are below the declared numeric acceptance tolerances. These are model implementation checks, not measured energy performance.

Actual `qa_mode_sequence` trace follows `0 -> 1 -> 2 -> 3 -> 4 -> 5 -> 2 -> 0`. Its BACKUP interval retains 2 MW TES discharge plus 1 MW boiler heat to meet 3 MW demand. Its UNMET_DEMAND interval retains 2 MW TES discharge and 1 MW boiler heat while explicitly reporting 2 MW unmet out of 5 MW demand. Its seventh interval charges TES at 3 MW despite zero demand. These numerical observations directly confirm the priority-mode semantics and zero-demand distinction derived above.

The saved MATLAB log `automation/logs/stateflow_acceptance_v22_topology_20261009T045637.log` contains nonfatal local-function-argument shadowing diagnostics. Selection/allocation functions deliberately use explicit local arguments with chart-data names; tested numerical output parity succeeds. The warnings persist and should not be described as a warning-free build. The earlier 474-check gate and initial From Workspace extrapolation build failure are preserved; the expanded 476-check gate is the final reviewed evidence.

Review conclusion: the v22 artifact satisfies the declared discrete mathematical/source/structural acceptance contract for the tested scenarios and passes reviewed executable acceptance plus independently persisted ZIP provenance checks. The reviewer personally ran the ZIP inspection, independently derived the physical equations, and reviewed the saved MATLAB/Python evidence; this report does not claim that the ZIP inspection executed MATLAB. No primary article replication, real-equipment validation, standalone generated-code execution, continuous TES leakage validity, annual dispatch/weather integration, hysteresis or fault handling is established.
