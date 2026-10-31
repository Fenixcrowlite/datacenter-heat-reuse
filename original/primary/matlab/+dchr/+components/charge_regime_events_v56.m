function r=charge_regime_events_v56(s,p,E,request)
% Research prerequisite, NOT a certified endpoint or Stateflow planner.
% Zero-demand charge-only topology; unique instantaneous limiter is certified.
for v={p.charge_limit_MW,p.eta_charge,p.loss_rate_per_h}
    assert(isa(v{1},'double')&&isreal(v{1})&&isscalar(v{1})&&isfinite(v{1}), ...
        'DCHR:v56:Domain','Finite double charge policy required.');
end
assert(p.charge_limit_MW>0&&p.eta_charge>0&&p.eta_charge<=1&&p.loss_rate_per_h>=0&&request>0, ...
    'DCHR:v56:Domain','Positive request/port limit, admissible efficiency and loss required.');
b=dchr.components.coupled_temperature_boundary_v55(s,p,E,request);
c=b.branch_certificate;iv=[c.limit_MW_intervals;p.charge_limit_MW p.charge_limit_MW];
strict=false(5,1);
for j=1:5,strict(j)=iv(j,2)<min(iv([1:j-1 j+1:5],1));end
assert(sum(strict)==1,'DCHR:v56:UnresolvedLimiter','Unique minimum not certified; ties require an endpoint protocol.');
active=find(strict);C=p.heat_capacity_MWh_per_K;Ta=p.ambient_C;
F=s.delivery_C+s.direct_approach_K;d=s.charge_approach_K;
Te=b.evaporator_C;a=s.cooling_factor*(Te+273.15);S=b.source_budget_MW;H=s.hot_capacity_MW_per_K;
% q_j(E) = slope(j)*E + intercept(j); rows: request, HP, hot, source, TES.
if b.tank_branch
    slope=[0;0;0;S/(a*C);0];
    intercept=[request;s.hp_capacity_MW;H*d;S*(1+(Ta+d+s.condenser_approach_K-Te)/a);p.charge_limit_MW];
else
    slope=[0;0;-H/C;0;0];
    intercept=[request;s.hp_capacity_MW;H*(F-Ta);S*(1+(F+s.condenser_approach_K-Te)/a);p.charge_limit_MW];
end
names={'REQUEST','NAMEPLATE','HOT_FLOW','SOURCE','TES_PORT'};
k=p.eta_charge*slope(active)-p.loss_rate_per_h;B=p.eta_charge*intercept(active);
velocity=k*E+B;Ek=C*(F-Ta-d);Emax=C*(s.tank_max_C-Ta);
assert(all(isfinite([slope;intercept;k;B;velocity;Ek;Emax]))&&E<Emax, ...
    'DCHR:v56:Resolution','Nonfinite coefficients or initial capacity endpoint.');
targets=[0;Emax;Ek];labels={'ZERO';'CAPACITY';'BRANCH'};
for j=1:5
    if j==active||slope(active)==slope(j),continue;end
    target=(intercept(j)-intercept(active))/(slope(active)-slope(j));
    targets(end+1,1)=target;labels{end+1,1}=['LIMIT_' names{j}]; %#ok<AGROW>
end
events=struct('label',{},'energy_MWh',{},'time_h',{});
for j=1:numel(targets)
    target=targets(j);
    if ~isfinite(target)||target<0||target>Emax||velocity==0||(target-E)*velocity<=0,continue;end
    if b.tank_branch&&target<Ek,continue;end
    if ~b.tank_branch&&target>Ek,continue;end
    vt=k*target+B;
    % An equilibrium endpoint is approached asymptotically, never crossed.
    if vt*velocity<=0,continue;end
    if k==0,t=(target-E)/velocity;
    else,t=log1p(k*(target-E)/velocity)/k;end
    assert(isreal(t)&&isfinite(t)&&t>0,'DCHR:v56:Resolution','Unresolved event time.');
    events(end+1)=struct('label',labels{j},'energy_MWh',target,'time_h',t); %#ok<AGROW>
end
if isempty(events),next=Inf;first={};
else,next=min([events.time_h]);first={events([events.time_h]==next).label};end
r=struct('branch',c.branch,'limiter',names{active},'limiter_index',active, ...
    'limit_MW_intervals',iv,'slope_per_h',slope,'intercept_MW',intercept, ...
    'k_per_h',k,'B_MW',B,'initial_velocity_MW',velocity, ...
    'branch_energy_MWh',Ek,'capacity_energy_MWh',Emax,'events',events, ...
    'next_event_h',next,'first_event_labels',{first}, ...
    'instantaneous_certificate',c,'event_times_certified',false, ...
    'scope','CHARGE_ONLY_NOMINAL_EVENT_LANDSCAPE_NO_PROPAGATOR_OR_STATEFLOW_INTEGRATION');
end
