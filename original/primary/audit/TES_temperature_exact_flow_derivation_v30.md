# v30 temperature and exact active-flow TES derivation

Engineering reduction, 2026-10-09. Read the current research v25 and Stateflow v29 status/stageboards, acceptance contract, research frontier, inherited primary TES audit, and all unfinished v30 kernel/adapter/builder sources before editing. Baselines v14, v22, v24, v28 are preserved.

## Evidence and assumptions

Inherited relevant primary article evidence: Cadau et al. (2019), DOI 10.3390/en12224275, article/PDF p4 Eq (4), ambient transfer proportional to node temperature minus ambient. Local editorial PDF SHA256 `693b8373e83c5b3cfcc17c449903a4dc320c9df76bb664b99aeab455d7d39dcb` and reviewed locators are in `audit/TES_standing_loss_primary_v28.md`. This run does not newly inspect its PDF or reproduce its multi-node model.

Newly re-opened primary engineering documentation: [EnergyPlus Engineering Reference 9.5, Mixed Water Thermal Tank / Energy Balance](https://bigladdersoftware.com/epx/docs/9-5/engineering-reference/water-thermal-tanks-includes-water-heaters.html#energy-balance), accessed 2026-10-09. Verified text/formulas: mixed heat-capacity balance; ambient UA term; constant-coefficient linear temperature ODE; analytical solution and zero-coefficient limit; control discussion uses separate integrations as operating conditions change. This is engineering documentation, not a peer-reviewed research article. Its hydraulic source/use connections depend on temperature and mass flow. Our fixed external power ports and uniformly throttled dispatch are added engineering assumptions, not implementation of those connections or its event-driven controls. No documentation parameter values are adopted. Full article signoffs remain 0/31.

All 23 acceptance scenarios use assumed values. Fixed ambient `Ta`, heat capacity `C>0` in MWh/K, loss coefficient `lambda>=0` in h^-1, efficiencies in (0,1], condenser/delivery reservoir proxies and finite power limits stay constant throughout a simulation. The store is mixed, sensible, and lacks stratification, hydraulic flow, phase change, calibrated conductance and equipment cycling. Ambient must not change while using this state definition. Condenser proxy is constrained to at least the tank maximum; delivery proxy must be at most the cutoff. These constraints neglect approach temperatures and conservatively reject unsupported temperature combinations even when ports would be idle.

## Physical energy and useful inventory

Define physical ambient-referenced sensible energy `A=C*(T-Ta)` MWh. Capacity is `Amax=C*(Tmax-Ta)` and delivery cutoff inventory is `Ac=C*(Tcut-Ta)`, with `Ta<=Tcut<=Tmax` and `Ta<=T0<=Tmax`. Report usable energy `U=max(0,A-Ac)` separately. Physical state may cool below cutoff; it must never be forced up to cutoff. Before clipping the service metric, `U'=-lambda*(U+Ac)+P`. Omitting `Ac` puts equilibrium at the delivery temperature and changes the ambient loss physics.

For held external charge/discharge powers `Qc,Qd` MW and efficiencies `etaC,etaD`, internal power `P=etaC*Qc-Qd/etaD` MW. The first law gives `A'=-lambda*A+P`. With interval `h>0` hours, let `r=exp(-lambda*h)` and `phi=(1-r)/lambda` hours, or `phi=h` at zero loss. Then

`A_next=r*A_start+phi*P`.

Standing loss is `L=A_start+P*h-A_next`, equivalently `A_start*(1-r)+P*(h-phi)`, in MWh. Production evaluates small `h-phi` by series to avoid cancellation; independent QA uses 60-digit Decimal arithmetic and a separate temperature/loss RK4 integration. Charge and discharge inefficiency losses are `(1-etaC)*Qc*h` and `(1/etaD-1)*Qd*h`. External closure is

`A_start+(Qc-Qd)*h=A_next+L+L_charge+L_discharge`.

## Chosen bound policy and proof

v30 holds power uniformly throughout each complete sample interval. It selects feasible power *before* integration. Charge is bounded by `(Amax-r*A_start)/(etaC*phi)`. Discharge is bounded by `max(0,(r*A_start-Ac)*etaD/phi)`. Both are additionally constrained by request and equipment limits; simultaneous positive requests are rejected.

For a scalar autonomous linear ODE with constant `P`, `A(t)` is monotone or constant: its derivative has the fixed sign of `P-lambda*A_start` multiplied by an exponential. Thus initial/endpoint bounds ensure the entire trajectory meets ambient/capacity constraints; positive discharge requires the entire trajectory to stay above cutoff. A cutoff or capacity limiting case reaches its bound at the end of the interval, with only roundoff correction at ambient/capacity. Passive loss can cross the delivery cutoff without clipping physical energy. At capacity, charging can offset standing loss without exceeding capacity. At cutoff, positive loss prevents useful discharge.

This policy intentionally differs from full-power operation until an internal event followed by shutdown. If passive cooling alone reaches cutoff during an interval, uniform dispatch supplies no TES heat for that interval, even though a shorter initial discharge pulse could have served some demand. For shorter intervals a different feasible uniform power is selected, so constrained dispatch is not claimed partition invariant. Exact partition invariance applies to fixed unthrottled power and constant coefficients only. No transient controller inside the step is implemented.

The chart assigns six operating states using demand, HP output and exact TES deficit service, then finite backup and unmet demand. State entry/during actions allocate ports; a numerical monitor gates all accepted energy feedback and traces. HP v14 has a source-constrained COP calculation and undefined operating COP when off. Condenser and district delivery temperatures are separate proxies, although heat delivery temperature degradation has no separate exergy or heat-exchanger model.

## Executable validation plan

Independent oracle: `audit/stateflow_reference_v30.py`. It uses Decimal TES coefficients and a closed-form HP source-limit root, importing no production code. Separate MATLAB numerical dispatch shares validated components but never calls Stateflow mode/allocation helpers. Actual saved model: `matlab/simulink/DCHR_Dispatch_Stateflow_v30.slx`; versioned builder refuses to overwrite it.

Acceptance includes zero demand, HP-only, TES charge/discharge, finite boiler and unmet demand; multi-step state transitions; passive cutoff crossing, endpoint cutoff/capacity, zero/high/small loss, zero capacity, variable part-load COP; eight actual v28/v30 active-flow comparisons at h=2,1,0.5,0.25 over two hours. Those unthrottled comparisons test analytical endpoints and v28 split error. Runtime faults include 12 domain rejections, 2 delayed finite faults, 4 in-memory monitor mutations and clean restoration. Compile success alone is never acceptance. Timestamped JSON/CSV/MAT/logs and independent evidence review determine the pass/fail record.

Read-only MAT audit exports error phase/time and logged prefixes and re-exports original numerical ports to bind acceptance CSVs. Independent ZIP/XML review checks saved model connectivity, six guarded states and embedded source. Synthetic corrupt-evidence tests are reported separately. These gates establish implementation correctness under stated assumptions, not physical validation, article replication, standalone code generation or equipment calibration.
