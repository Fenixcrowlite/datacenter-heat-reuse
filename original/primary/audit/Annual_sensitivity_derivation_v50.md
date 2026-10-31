# Matched annual Stateflow sensitivity — v50

This checkpoint experiments on the preserved saved Stateflow 0.42 model.
It creates a versioned executable harness, not a new controller or SLX.
All profiles and parameters are synthetic project engineering assumptions.
No new primary-text equation, equipment calibration or physical validation is claimed.

The matched boundary is the v49 fixed 85 C condenser, 85 C tank maximum,
20 C ambient, original hourly source/weather/load and zero initial inventory.
Holding K=50 MWh and C=K/(85-20)=10/13 MWh/K fixed, cutoff inventory is
Ec=C(Tcut-20) and maximum usable discharge inventory is U=K-Ec.
At cutoff 80, 81, 82 C, U is respectively 50/13, 40/13, 30/13 MWh.
This is a thermal service restriction, not a reduction in nominal tank capacity.
Cutoff must support every original network delivery temperature (maximum 80 C).
Condenser must support the fixed tank maximum; zero approach is a reduced-model
assumption with no finite HX validation. Seasonal condenser mapping remains
unsupported, as independently documented in v49.

Baseline restart R=48 MWh, minimum ON=OFF=0.25 h. Nine annual executions are
baseline; cutoff 81 and 82 C; restart 47 and 49 MWh; ON dwell 0 and 0.5 h;
OFF dwell 0 and 0.5 h. Each variant changes exactly one policy coordinate.
Every restart band must satisfy Ec+2*etol < R < K-2*etol,
etol=64*eps(max(1,K)), before execution. All 8760 rows receive static domain
preflight in each scenario; this does not certify state-dependent event progress.
Runtime errors and SimulationOutputs must be retained without accepting a
truncated trajectory. Each experiment starts from identical inventory and clock.

Held segment power P=etaC*charge-discharge/etaD integrates the reduced ODE
dE/dt=P-lambda*E. Independently:

    E(t)=E0*exp(-lambda*t)+P*(1-exp(-lambda*t))/lambda,
    standing loss=E0+P*t-E(t).

The lambda=0 limit is E0+P*t. Here lambda=-log(1-1e-4)/h matches the paired
v48 passive hourly retention only; v48 active-port loss-first integration
and cutoff-free controller remain different policies.

System first law per segment and integrated hour is

    E0 + integral(source_used+HP_electric+gas-delivered)dt
       - E1 - standing_loss - charge_loss - discharge_loss = 0,
    delivered=HP_direct+TES_discharge+gas.

The independent Python reviewer uses inherited 60-digit Decimal exponential
endpoints and a closed-form source-constrained HP quadratic, never calling
production MATLAB, Stateflow or the planner. It sums segment powers and physical
clock spans, verifies mode authorization, cutoff/capacity events, port limits,
source limits and minimum dwell at latch changes. Safety OFF semantics and
capacity OFF follow saved-v42 policy; ON dwell is not an unconditional guarantee.
Clock lower-age/bound checks account for CSV serialization, and never use an
energy tolerance to grant time. Reviewer mutations are separately labelled.
MAT reopens bind CSV/JSON evidence to original stored SimulationOutputs.

For matched annual result Y, delta_i=Y_i-Y_baseline measures the conditional
effect of one changed policy coordinate on these synthetic inputs. It is not
an interaction estimate or global optimum. Delta_i_lossfirst=Y_i-Y_v48 combines
cutoff, active-port storage integration and controller differences, and must
not be attributed to numerical integration error. Each row reports terminal
inventory without valuing or crediting it. Equal delivered-service cost/CO2
comparisons include only active HP and boiler: auxiliaries, initial/terminal
inventory value, CAPEX, pumping and equipment calibration remain open.

Fresh baseline must reproduce preserved v49 annual traces and reports. The
paired v48 annual dispatch is recomputed on the same source/load/lift boundary.
Actual successful annual mode coverage is reported separately from the six
required acceptance modes, which remain covered by preserved v42/v49 fixtures.
No claim of six modes in every annual trajectory is made.
