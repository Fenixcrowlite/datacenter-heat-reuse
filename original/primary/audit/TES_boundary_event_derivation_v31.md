# v31 boundary-event comparator for the saved v30 Stateflow policy

The v30 model already passes implementation acceptance. This checkpoint implements the next handoff: derive/test internal TES boundary events and compare them against actual saved-v30 execution before changing its dispatch. The model release stays 0.30; the new MATLAB component is a comparator, not a new Stateflow release.

## Evidence boundary

Read STATUS/stageboards v25/v30, STATEFLOW_ACCEPTANCE, research frontier, progress and v30 component/builder/harness/oracle sources before changes. Cadau (2019), DOI 10.3390/en12224275, p4 Eq (4), is inherited primary article evidence for ambient heat transfer only; see `TES_standing_loss_primary_v28.md` and its preserved PDF/hash. No new article equation, parameter or experimental result is adopted.

Newly opened [EnergyPlus 9.5 Engineering Reference](https://bigladdersoftware.com/epx/docs/9-5/engineering-reference/water-thermal-tanks-includes-water-heaters.html#energy-balance), 2026-10-09: Mixed Water Thermal Tank / Energy Balance gives the mixed-temperature ODE, its analytic and zero-coefficient solutions, and inversion for reaching a target temperature; Water Heater Control Algorithm describes separate within-step integrations. This is primary engineering documentation, not article replication. Its hydraulic/cycling controls are not our simplified constant-power policy. All numerical inputs below are engineering assumptions; full article signoffs remain 0/31.

## Derivation and event policy

Ambient-referenced state `A=C(T-Ta)` MWh has `A'=P-lambda*A`, where `P=etaC*Qc-Qd/etaD` MW, `lambda` is h^-1 and time is hours. For a held port segment of length s, `A(s)=A0*exp(-lambda*s)+P*phi(s)`, with `phi=-expm1(-lambda*s)/lambda` hours or s at zero loss. Its ambient-loss integral is `L=A0*(1-exp(-lambda*s))+P*(s-phi)` MWh. External-port inefficiencies are `(1-etaC)*Qc*s` and `(1/etaD-1)*Qd*s`. Their sum with L gives first-law closure. A segment is monotone because `A'(s)=(P-lambda*A0)*exp(-lambda*s)`.

Charge at `Qc=min(surplus,chargeLimit)` until capacity M. A finite capacity event requires `etaC*Qc>lambda*M`; otherwise a state below M cannot reach it. The hitting time is

`tc=log1p(lambda*(M-A0)/(etaC*Qc-lambda*M))/lambda`.

At zero loss, `tc=(M-A0)/(etaC*Qc)`. After reaching capacity, **modulate** charge to `Qc_hold=lambda*M/etaC`, which is below the available charge power by the reachability condition. This maintains capacity and supplies ambient loss. This explicit engineering choice avoids a sample-dependent restart after immediate shutdown. It is not a hysteresis/cycling controller. Zero capacity has zero holding charge. Initial capacity with insufficient charge cools normally; equilibrium below capacity is not an event.

Discharge at `Qd=min(deficit,dischargeLimit)` only when `A0>Ac`. Its cutoff hitting time is

`td=log1p(lambda*(A0-Ac)/(Qd/etaD+lambda*Ac))/lambda`.

At zero loss, `td=(A0-Ac)*etaD/Qd`. At cutoff, shut discharge off and integrate passive cooling for the remaining interval: `Aend=Ac*exp(-lambda*(h-td))`. Physical energy may fall below cutoff. With Ac=0, the residual energy is zero. If the event lies beyond the interval, use the full held power for the whole interval. Initial state at/below cutoff serves no TES heat. Positive requests at both ports are invalid.

For a two-segment event, integrate each segment and add its port energies/losses. Report **interval-average** powers as total port energy/h and separately retain commanded segment powers, event time and event energy. Averages must never be treated as actual constant flows in a v30 monitor or nonlinear HP calculation. With constant requests and coefficients this autonomous charge/modulation or discharge/shutdown policy has a semigroup: splitting an interval preserves endpoint and integrated port/loss totals, up to numerical error.

## Comparison boundary and instantaneous backup

Actual v30 simulations use fixed source/demand/COP scenario inputs. Charge comparisons use constant COP=4 and source-limited available condenser heat of 3 MW; the event comparator receives this available surplus. The v30 adapter can reduce its HP request to its uniform headroom. Compare accepted TES heat and ambient/inefficiency losses only; the event comparator has no HP scheduling/electricity model. It does not claim whole-system event-model equivalence.

Discharge comparisons have no HP heat. For each event segment use `gas=min(B,max(0,D-Qd_segment))` and `unmet=max(0,D-Qd_segment-gas)`, then integrate. Computing backup/unmet from average TES power would hide within-interval supply shortfalls. The two policies can trade TES service against backup utilization: full-power service followed by cutoff can leave a late deficit that exceeds finite backup, even if its total TES delivery is larger. There is no universal dominance claim. Charging at capacity replaces losses; discharge cutoff is followed by passive cooling. Both assumptions are explicit and independently checked.

## Independent verification design

MATLAB uses log1p hitting times and stable exponential segment loss integration. A separate Python oracle imports no production MATLAB code, uses 60-digit Decimal exponentials and numerical bisection for event times, and independently integrates temperature/loss by RK4. Tests cover random states, zero/tiny/high loss, initial capacity/cutoff, zero capacity/cutoff, unreachable capacity and above-limit requests; partition and first-law checks test integrated totals. A timestamped spec carries oracle expectations. Actual saved-v30 SimulationOutput MATs and traces are exported independently and compared with the inherited v30 Decimal/analytic-HP oracle. Saved SLX connectivity/embedded functions are independently reviewed using the existing ZIP/XML reviewer. Synthetic corrupted-evidence checks are separately labelled.

Acceptance counts/results belong to the timestamped executed evidence and result report, not this planned derivation. Remaining deployment work: piecewise HP scheduling, explicit recovery curtailment, segment-level boiler/unmet accounting and event timing in a new versioned chart/monitor. No sensor faults, measured calibration, hydraulic/stratified tank, equipment cycling or standalone generated-code acceptance is claimed.
