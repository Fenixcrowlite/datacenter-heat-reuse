# Conservative retained-inventory service controller v65

This engineering derivation changes the controller policy. It is not an article
equation, calibrated model or earliest-event continuation of v64.

The new chart retains the original v64 capacity/restart trajectory and its port
and clock hulls. After its completed restart, scalar service is authorized from
the lower inventory bound; capacity authorization uses the upper bound. No
midpoint inventory or event root is selected. The exact original inventory remains
inside the propagated enclosure. The prefix has zero demand; subsequent service
can vary demand/source availability between held-power physical intervals.

For a held interval, E' = etaC*qcharge - qdis/etaD - lambda*E. Integrate this ODE
with the inherited outward Taylor enclosure, conditional on |lambda*dt|<=1.
Positive charging is bounded by half of (K.lower-E.upper)/(etaC*dt), leaving a
conservative capacity margin. Discharge authorization uses
qdis <= etaD*(E.lower-Ecut.upper-lambda*E.upper*dt)/dt, and zero if that bound
is negative. For decreasing inventory, standing loss never exceeds the budget
lambda*E.upper*dt; thus every admitted initial inventory stays above cutoff.
This policy can underutilize available heat. It provides safe service, not a
maximal or optimal solution. A sampled stop temperature below Tmax suppresses
further charging. Sampling is distinct from v64's earlier analytic capacity OFF.

Allocate direct HP heat first, then mutually exclusive TES charge/discharge,
then a limited boiler, then unmet demand. Every remaining-demand subtraction
uses an outward lower bound before selecting scalar service. Heating powers
are engineering binary inputs; exact real sums are enclosed for all cumulative
accounting. Delivered service excludes unmet demand.

The fixed-temperature water law is hot=max(delivery+directApproach,
Ta+E/C+chargeApproach), Te=sourceIn-glide-evapApproach,
a=coolingFactor*(Te+273.15), source=qHP*a/(a+hot+condApproach-Te).
The compiled model bounds and integrates changing source/compressor ports using
128 outward rectangles and the propagated tank trajectory. Nameplate, source
and water capacities constrain qHP before allocation. A common hot-water return
at the tank temperature and fixed refrigerant approaches are explicit engineering
assumptions. Correlation hot>=tank+chargeApproach proves the water denominator
bound without a subtractive interval midpoint. Cooling factor lies in (0,1],
which bounds this heating COP by the refrigerant Carnot COP.

HP OFF-to-ON requires the entire inventory hull below restart and the lower age
bound beyond OFF dwell. ON-to-OFF operator commands require ON dwell; no
source/capacity/sink permits a recorded safety override. Clock hulls persist
through ordinary steps; age resets only at actual sampled latch transitions.

Expanded first law: Einitial + cumulative HP heat + boiler - delivered - Efinal
- standing loss - charge inefficiency - discharge inefficiency = 0. Source plus
compressor equals HP heat. Auxiliary electricity is external, with equal rejected
auxiliary heat; it contributes no delivered service or tank energy.

Independent QA must evaluate the original correlated v64 inventory and exact
binary scalar service powers, with high precision exp/log or quadrature. A scalar
v30 reference can check constant-power storage without authorizing midpoint
service. General repeated exact thermal-root event chains, changing equipment
policy, generated standalone code, calibration and measured validation remain
outside this sampled implementation scope. Independent algorithms are same-agent
review, not independent personnel.

## Executed implementation refinements

The held duration dt is authoritative. Cumulative physical time is retained as
an outward sum of durations; the supplied rounded absolute horizon must lie in
that clock enclosure and advance beyond its previous upper bound. Subtracting
large rounded absolute horizons and comparing at eps(dt) rejects valid labels,
so the model certifies the sum at the cumulative-clock scale. This does not
authorize an arbitrary inconsistent duration or choose a capacity-root midpoint.

Scalar remaining-demand subtraction uses an error-free TwoSum residual for
finite normal binary64 engineering powers. Only residual exactly zero preserves
a singleton; other cases keep the outward subtraction. There is no epsilon
service credit. The mathematical discharge-loss identity at etaD=1 is exactly
zero and is implemented explicitly; zero standing loss has its exact zero-rate
integration limit. The independent reviewer uses exact Fractions for service
powers and separate 120/160-digit exp/log solutions with both-direction branch
splitting of max(floor,tank+approach).

The earlier unfinished scaffold failed before execution on heterogeneous JSON
and workspace-source extrapolation. Development evidence and saved development
models are preserved under timestamped results folders. Final acceptance uses a
fresh immutable manifest including the saved production model and reviewer.
