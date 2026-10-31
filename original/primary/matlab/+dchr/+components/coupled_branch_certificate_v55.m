function c=coupled_branch_certificate_v55(s,p,E,request)
% Outward intervals for exact binary inputs under IEEE double round-to-nearest.
% Does not certify propagator error or event timing; no Stateflow integration.
b=dchr.components.coupled_temperature_boundary_v54(s,p,E,request);
T=plusI(point(p.ambient_C),divideI(point(E),point(p.heat_capacity_MWh_per_K)));
tankOutlet=plusI(T,point(s.charge_approach_K));
floorOutlet=plusI(point(s.delivery_C),point(s.direct_approach_K));
gap=minusI(tankOutlet,floorOutlet);
if gap(1)>0,branch='TANK';elseif gap(2)<0,branch='FLOOR';else,branch='UNRESOLVED';end
Te=minusI(minusI(point(s.source_in_C),point(s.source_glide_K)),point(s.evaporator_approach_K));
hot=[max(tankOutlet(1),floorOutlet(1)) max(tankOutlet(2),floorOutlet(2))];
Tc=plusI(hot,point(s.condenser_approach_K));
glide=minusI(hot,T);lift=minusI(Tc,Te);
a=timesI(point(s.cooling_factor),plusI(Te,point(273.15)));
assert(a(1)>0&&lift(1)>0,'DCHR:v55:UnresolvedDomain','Positive lift/coefficient not certified.');
S=timesI(point(s.source_capacity_MW_per_K),point(s.source_glide_K));
hotBudget=timesI(point(s.hot_capacity_MW_per_K),glide);
sourceBound=timesI(S,plusI(point(1),divideI(lift,a)));
limits=[point(request);point(s.hp_capacity_MW);hotBudget;sourceBound];
strict=sourceBound(2)<min(limits(1:3,1));
c=struct('branch',branch,'resolved',~strcmp(branch,'UNRESOLVED'), ...
    'tank_C_interval',T,'tank_outlet_interval',tankOutlet, ...
    'floor_outlet_interval',floorOutlet,'gap_K_interval',gap, ...
    'limit_MW_intervals',limits,'source_strictly_limited',strict, ...
    'nominal_boundary',b,'arithmetic','EXACT_BINARY_INPUTS_OUTWARD_2_EPS_PER_BASIC_OPERATION', ...
    'scope','INSTANTANEOUS_BRANCH_AND_SOURCE_LIMIT_INEQUALITIES_ONLY');
end
function v=point(x),v=[x x];end
function v=plusI(x,y),v=outward([x(1)+y(1) x(2)+y(2)]);end
function v=minusI(x,y),v=outward([x(1)-y(2) x(2)-y(1)]);end
function v=timesI(x,y)
z=[x(1)*y(1) x(1)*y(2) x(2)*y(1) x(2)*y(2)];v=outward([min(z) max(z)]);
end
function v=divideI(x,y)
assert(y(1)>0,'DCHR:v55:UnresolvedDomain','Positive denominator required.');
z=[x(1)/y(1) x(1)/y(2) x(2)/y(1) x(2)/y(2)];v=outward([min(z) max(z)]);
end
function v=outward(z)
assert(all(isfinite(z)),'DCHR:v55:UnresolvedDomain','Nonfinite interval endpoint.');
% One eps encloses the basic-operation rounding; the second covers expansion
% rounding, including a binade boundary. eps(0) covers gradual underflow.
v=[z(1)-2*eps(z(1)) z(2)+2*eps(z(2))];
assert(all(isfinite(v))&&v(1)<=v(2),'DCHR:v55:UnresolvedDomain','Interval expansion overflow.');
end
