# v28 independent TES derivation, source review and executable QA

This reviewer read the acceptance contract, v27 status/stageboard, research frontier, v24 chart builder/allocator/selector/runtime gate and earlier independent v22 oracle before preparing new tests. The v22 numerical oracle remains unchanged. The v28 numerical reviewer calls no production MATLAB component or earlier Python physics kernel to obtain expected values. Only the generic runtime rejection evidence-schema checker from `verify_stateflow_runtime_v24.py` is reused; it has no TES equations and does not execute MATLAB. That generic module transitively imports v22, whose physics functions are never called by this v28 reviewer. Synthetic reviewer checks are separate from actual saved-model evidence.

## Independent equation derivation

Powers are MW, energy is MWh and the physical sampling duration `dt` is hours. A constant continuous decay coefficient `lambda >= 0` has units inverse hours. For an unforced lumped energy reservoir under the explicit engineering assumption `dE/dt = -lambda E`, separation of variables gives

`E_after = E_start exp(-lambda dt)` and `L_standing = E_start - E_after`.

The identity `exp(-lambda (dt1+dt2)) = exp(-lambda dt1) exp(-lambda dt2)` proves passive partition invariance. The implementation's `-E_start*expm1(-lambda dt)` is a numerically stable equivalent standing-loss calculation. Finite nonnegative lambda and a finite product `lambda*dt` are required numerically. A product greater than one is valid: it means strong attenuation, not negative energy. Exponential underflow is an accepted finite-precision limit of a positive state, and is explicitly tested separately from exponent-product overflow, which must be rejected.

This coefficient is not a dimensionless fraction of energy lost over an hour. If a one-hour fractional loss `f` is the calibrated datum, the corresponding continuous coefficient is `lambda = -log(1-f)/(1 h)` for `0 <= f < 1`. The preserved v24 map is `E_after = E_start (1-k dt)` with `0 <= k dt <= 1`; using the same numerical coefficient `k=lambda` only matches the exponential to first order in `dt`. At a particular interval, `k_effective = (1-exp(-lambda dt))/dt` makes the old map algebraically identical to v28. This explicit parameter conversion proves implementation parity at that interval, not validity of either physical model or invariance of the unconverted old coefficient.

After passive attenuation, the declared loss-first dispatch applies external TES port powers:

`Q_charge <= min(P_charge, (K-E_after)/(eta_charge dt))`

`Q_discharge <= min(P_discharge, E_after eta_discharge/dt)`

`E_next = E_after + eta_charge Q_charge dt - Q_discharge dt/eta_discharge`.

The upper/lower power bounds prove `0 <= E_next <= K`. Charging and discharging are mutually exclusive. Conversion losses are `L_charge=(1-eta_charge) Q_charge dt` and `L_discharge=(1/eta_discharge-1) Q_discharge dt`; hence the TES external-port first law is exactly

`E_start+(Q_charge-Q_discharge)dt = E_next+L_standing+L_charge+L_discharge`.

For a fixed heating COP `C>1`, the HP first law and COP definition give `W=H/C`, `U=H(1-1/C)` and source feasibility `H <= S/(1-1/C)`. The independent oracle requests `D+min(P_charge,(K-E_after)/(eta_charge dt))` and caps HP heat by that request, HP capacity and the source bound. Direct delivery is `min(D,H)`; any surplus fits charge room. TES serves the remaining deficit, then the finite backup boiler, then explicit unmet heat. These deductions independently reproduce all nineteen numeric accepted ports. They do not predict nonzero part-load HP operation; those supplemental intervals receive separate input-metadata, exponential state, port-balance, bounds, COP and mode checks plus MATLAB reference comparison.

The complete first law is

`(U+W+B)dt + E_start = supplied dt + E_next + L_standing+L_charge+L_discharge`.

Unmet demand is an accounting deficit rather than a physical heat sink. Backup is thermal heat supplied at this boundary rather than fuel energy. The six modes retain the existing priority: unmet > backup > discharge > charge > direct recovery > idle. Backup and unmet modes keep feasible HP direct and TES discharge contributions. Standing loss alone can coexist with IDLE; zero demand can coexist with STORAGE_CHARGE.

## Active-flow timing and physical limitations

Pure exponential passive attenuation does not make the loss-first active-flow model exact. New charge is added at the interval endpoint and experiences no standing loss until the next interval. For constant signed internal power `q`, an independently solved continuous reservoir equation is `dE/dt=q-lambda E`:

`E(T)=E(0)exp(-lambda T)+q(1-exp(-lambda T))/lambda` for nonzero lambda, and `E(T)=E(0)+qT` for lambda zero.

For `N=T/dt` unconstrained split intervals, the geometric-series terminal state is

`E_N = E_0 r^N + q dt (1-r^N)/(1-r)`, where `r=exp(-lambda dt)` for v28 and `r=1-lambda dt` for legacy v24.

For positive charge, the exponential loss-first sum overestimates the exact continuous charging term, because it gives every interval's fresh charge the full endpoint weight. The factor `lambda dt/(1-exp(-lambda dt))` tends to one on refinement and exceeds one for positive `lambda dt`. For constant discharge, the signed forcing error has the opposite direction while unconstrained. Capacity, energy and dispatch switching can change convergence behavior; neither the passive semigroup nor the unconstrained charge experiment proves convergence of arbitrary controlled trajectories.

The pure decay equation requires energy measured relative to constant ambient in a constant-property, fixed-volume lumped temperature reduction. If useful stored energy instead references a delivery/return threshold `T_ref`, a constant `T_ref-T_ambient` produces an affine offset: `dE_ref/dt=-lambda [E_ref+C_thermal(T_ref-T_ambient)]`. Omitting that offset is an engineering assumption. A literature equation for a tank temperature or ambient heat transfer does not calibrate this model's operational energy, lambda, capacity or efficiencies. This review does not newly verify any primary-paper equation; the separate source audit must supply its own full-text evidence. No article replication or measured physical validation is claimed.

## Pre-run production source review

Reviewed the new v28 builder, Stateflow selection/allocation/contract gate, host HP adapter, TES component, separate MATLAB dispatch reference, actual-model acceptance harness and loss experiment harness. The passive state, feasible power bounds, loss reports, complete first-law accounting, six mode priority, physical clock equality and nonnegative finite-domain checks match the derivation above. The adapter's storage preview, selector and allocator use the same exponential attenuation. Stable `expm1` loss reporting is appropriate. No mathematical or allocation defect was found in those sources for the stated domains.

The saved model embeds helpers and must be inspected after generation; external source equality alone does not certify a stale `.slx`. The independent verifier reads ZIP/XML directly, checks all six state actions, 30 mode changes, six initial guarded choices, sampled Unit Delay and index-eight state feedback, every runtime gate connection and absence of an unchecked chart bypass. It compares embedded selection/allocation/monitor scripts to their reviewed `.m` files. Static provenance proves model contents and wiring, not execution.

The 46 independent rejection vectors remove the former `lambda dt>1` invalid case and add nonfinite continuous rates plus finite-coefficient exponent-product overflow. Tick metadata in generic rejection records identifies intended placement only: it does not independently certify valid-prefix timing. Earlier v26 contract-corruption execution and v27 temporal acceptance apply to the preserved v24 gate/model and must not be described as newly executed v28 fault/temporal acceptance.

## Reviewer artifacts and current evidence

`stateflow_qa_vectors_v28.csv` contains 58 independently predicted intervals across 16 scenarios: all six dispatch modes and mode changes, zero/full capacity boundaries, filling and emptying limits, unity efficiencies, high `lambda dt>1`, exponential underflow and four passive/charging time partitions. `stateflow_domain_cases_v28.json` contains 46 independent invalid-domain/clock vectors. `verify_stateflow_trace_v28.py` checks actual accepted traces against rederived independent values and separately recomputes first laws, SOC, power limits, mutual exclusivity, sample times and memory continuity. Its experiment audit checks final values against independent geometric and integrating-factor solutions and checks every saved experiment sample's time, mode, charge/discharge, attenuation, update, standing loss and independently recomputed residual. It hashes the experiment traces.

The initial synthetic-only reviewer report `stateflow_oracle_selftest_v28_initial.json` records 1016/1016 passing reviewer checks, including 500 seeded random algebraic cases and deliberate trace corruptions. This is not actual Stateflow evidence. Subsequent timestamped test logs and actual-model review results will be recorded here after the root agent supplies completed traces.

The first actual acceptance run in `results/stateflow_v28_20261009T103528356Z` completed valid dispatch and all twenty timestep experiments, then failed during setup of the last invalid-domain case. Its heterogeneous JSON setup list mixes a `p` mutation with an `index` field and a scalar `model_dt` mutation without that field; MATLAB decoded this list as a cell array. The copied rejection harness assumed a struct array and raised `Dot indexing is not supported for variables of type cell` before the exponent-overflow simulation was attempted. Initial source review did not exercise that nested JSON decoding path. This is a test-harness schema defect, not an observed numerical storage defect. The root repaired setup cell/struct iteration; the generated model remains unchanged and all first-run logs/results are preserved. The first run must not be counted as completed acceptance.
