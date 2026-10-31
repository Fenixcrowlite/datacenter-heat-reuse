# Held-boundary schedule and reporting adapter v74

Engineering derivation and synthetic implementation tests only. No weather
dataset, article equation, equipment calibration or measured result is used.
All earlier models, including actual saved v73r2, remain unchanged. This
checkpoint adds MATLAB input/reporting functions and executes those saved
Stateflow models; it does not manufacture a new SLX by changing its name.

## Time and state contract

The six schedule columns are hold duration in hours, cumulative end label in
hours, demand in MW, source heat-capacity rate in MW/K, HP enable and charge
enable. The first two columns serve different purposes. Binary hold durations
are authoritative operands. End labels must be the advancing binary64 cumsum
display of those durations. Labels are rounded displays, not exact real sums.
The adapter never subtracts successive rounded labels to recover a duration.
The actual saved model must enclose each label in its retained physical-clock
hull. Protocol solver ticks are 0,1,2,... regardless of physical hold duration.
The actual thermal events remain analytic segments within a protocol call,
not solver-clock event firings. External demand/source/enable changes are held
without interpolation and applied to the next physical interval.

One immutable 25-parameter equipment/policy vector and initial inventory,
HP latch and age are supplied. Initial fields are repeated as input operands
but the saved model reads them only on its first call. An external input change
does not reset inventory, latch, age, symbolic contact or cumulative energy.
Variable positive hold durations are supported by v73r2/v66. Public span,
clock, event ordering, ON dwell and sixteen-segment refusals remain explicit.
No adaptive retry, clipping or hidden subdivision changes a refused schedule.
Valid prefixes are separate records marked incomplete for the original
schedule. Reporting an incomplete trace as a complete schedule must reject.

## Energy accounting and ratios

For physical segment j with duration t_j and held ports in MW:

    direct_HP_service = sum(q_direct,j * t_j)
    TES_service       = sum(q_discharge,j * t_j)
    backup_heat       = sum(q_backup,j * t_j)
    delivered_service = direct_HP_service + TES_service + backup_heat
    unmet_demand      = sum(q_unmet,j * t_j)
    demand_energy     = sum(demand_k * held_duration_k)

Each energy is in MWh. Demand closure is checked separately from heat-pump
and storage first laws. Unmet heat earns no delivery credit. Compressor work
and recovered-source energy have the v73r2 analytic temperature-dependent
meaning. Auxiliary electricity is external and carries no thermal credit.

    HP_heat = recovered_source + compressor_work
    initial_TES + HP_heat + backup_heat
      = final_TES + delivered_service + standing_loss
        + charge_loss + discharge_loss
    external_electricity = compressor_work + auxiliary_work

The ten authoritative cumulative energy hulls are retained directly from the
saved model's final header. Direct/TES delivery and demand are separately
integrated using segment-duration hulls and authoritative holds, with outward
binary arithmetic. Inventory continuity, initial inventory/latch/age, physical
clock hulls, finite trace, immutable policy and each segment's demand allocation
are checked before constructing a report. No hull midpoint is a result.

For nonnegative energy hull X=[xL,xU] and certainly positive denominator
Y=[yL,yU], X/Y is enclosed by outward [xL/yU,xU/yL]. Otherwise the reported
ratio is empty. HP heating COP is integrated HP_heat/compressor_work; it is
not an arithmetic average of instantaneous COP. Electricity per delivered
service includes TES and boiler delivery in its denominator and is a boundary
accounting diagnostic, not HP COP or a total primary-energy efficiency.
Changing final inventory must accompany comparisons; there is no economic
ranking, boiler-fuel conversion or emissions calculation in this checkpoint.

The arithmetic contract is the inherited finite, normal engineering domain.
Two binary ulps widen positive products, sums and ratios. Underflow, overflow
and arbitrary-scale certification are not established here.

## Baseline comparisons

The synthetic seasonal motifs are six successive held regimes lasting
10, 2, 1, 13, 10 and 12 hours (48 hours total). They exercise charging,
source outage, idle time, direct service, changed source capacity and sustained
demand with finite boiler capacity. Identical physical regime boundaries are
partitioned at 0.25, 0.5 and 1 hour. They are operating motifs, not four actual
seasons or a representative annual weather model. Other fixtures cover the
original six modes, variable hold durations, independent enable changes and
the retained explicit-refusal controls.

Saved v66 uses the same 25 physical policy operands and the same complete
schedule, with conservative entire-hold charge/discharge guards. Its inherited
prefix configuration is unused because every call has service kind 1. Its
equations are checked independently before totals are compared.

Saved v57 has a different boundary: condenser temperature supports maximum
tank temperature, hot-water return is fixed at the ambient value used in this
mapping, and its planner has no v73r2 stop-temperature or independent enable
commands. It receives matching thermal capacity, cutoff, restart, efficiencies,
nameplate, approaches, source rates, demand and timer limits. Its physical
uniform timestep is preserved. Only schedules whose command meaning can be
expressed by source presence/absence are compared. Initial timer memory is
[latch, age_high, age_low, uncertainty_bound] = [latch, age, 0, 0].
An earlier harness incorrectly packed age into age_low; its rejected runs are
retained as harness failures, not evidence of a legacy model defect.

Every comparison records delivered service, unmet demand, electricity and
final inventory. A separate charge/discharge-disabled HP schedule supplies
an equal-delivered-service control. Equal service uses a stated 1e-10 relative
max(1,service) MWh comparison budget, accounting for v57 scalar rounding.
Unequal-service schedules cannot justify a cost/efficiency ranking. Even the
equal-service v57 comparison combines a fixed-temperature boundary change
with a controller change and is not a pure dispatch-algorithm experiment.

## Independent QA boundary

Original SimulationOutputs and report are saved as v7.3 MAT and reopened in
MATLAB. The reopened operands/trace arrays are exported in row-major binary64
and bound to JSON. The independent Python reviewer converts binary operands
to exact Fractions and integrates closed exponential/log inventory and source
equations at 120/160-digit precision. It calls only prior independent reviewers,
never the production adapter, reporting function or kernel. Every actual
energy/report hull must contain the independently derived real trajectory.
Separate synthetic reviewer mutations check source, delivery, TES, demand,
electricity, ratio and completeness corruption detection. Same-agent
algorithmic independence is claimed; independent personnel, an independent
HDF5 parser, generated code and physical validation are not.
