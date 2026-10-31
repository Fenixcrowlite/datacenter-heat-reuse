function z=charge_branch_record_v61(s,p,E,total,request,age,cells,iterations)
% Correlated FLOOR->TANK charge event, constant REQUEST on both sides.
% Host prerequisite only. Exact manifold + interval ports, never scalar reset.
if nargin<7,cells=128;end
if nargin<8,iterations=80;end
assert(isa(total,'double')&&isreal(total)&&isscalar(total)&&isfinite(total)&&total>0&& ...
    isa(age,'double')&&isreal(age)&&isequal(size(age),[1 2])&&all(isfinite(age))&&age(1)>=0&&age(1)<=age(2)&& ...
    isa(cells,'double')&&isreal(cells)&&isscalar(cells)&&isfinite(cells)&&cells==fix(cells)&&cells>=1&&cells<=4096, ...
    'DCHR:v61:Domain','Positive total, nonnegative age interval and 1..4096 cells required.');
r=dchr.components.charge_regime_events_v56(s,p,E,request);
assert(strcmp(r.branch,'FLOOR')&&r.limiter_index==1,'DCHR:v61:UnsupportedRegime','Only incoming FLOOR/REQUEST supported.');
w=dchr.components.charge_event_window_v59(s,p,E,total,request,iterations);
assert(w.crossing_isolated&&any(strcmp(w.candidate_labels,'BRANCH'))&& ...
    all(ismember(w.candidate_labels,{'BRANCH','LIMIT_HOT_FLOW'})), ...
    'DCHR:v61:UnsupportedEvent','Require isolated branch event without unrelated contenders.');
R=@(v)dchr.components.exact_rational_v61('from',v);
addR=@(a,b)dchr.components.exact_rational_v61('add',a,b);subR=@(a,b)dchr.components.exact_rational_v61('sub',a,b);
mulR=@(a,b)dchr.components.exact_rational_v61('mul',a,b);divR=@(a,b)dchr.components.exact_rational_v61('div',a,b);
cmp=@(a,b)dchr.components.exact_rational_v61('cmp',a,b);bounds=@(a)dchr.components.exact_rational_v61('bounds',a);
F=addR(R(s.delivery_C),R(s.direct_approach_K));C=R(p.heat_capacity_MWh_per_K);Ta=R(p.ambient_C);d=R(s.charge_approach_K);
star=mulR(C,subR(subR(F,Ta),d));cap=mulR(C,subR(R(s.tank_max_C),Ta));q=R(request);
Te=subR(subR(R(s.source_in_C),R(s.source_glide_K)),R(s.evaporator_approach_K));
a=mulR(R(s.cooling_factor),addR(Te,R(273.15)));S=mulR(R(s.source_capacity_MW_per_K),R(s.source_glide_K));
Lfloor=subR(addR(F,R(s.condenser_approach_K)),Te);
sourceAt=mulR(S,addR(R(1),divR(Lfloor,a)));
limits={q,R(s.hp_capacity_MW),mulR(R(s.hot_capacity_MW_per_K),d),sourceAt,R(p.charge_limit_MW)};
names={'REQUEST','NAMEPLATE','HOT_FLOW','SOURCE','TES_PORT'};tied={};
for n=1:5
    assert(cmp(limits{n},q)>=0,'DCHR:v61:UnsupportedRegime','REQUEST ceases to be active on right branch.');
    if cmp(limits{n},q)==0
        assert(n~=4,'DCHR:v61:UnsupportedContact','Source contact has nonzero right slope; not equivalent.');
        tied{end+1}=names{n}; %#ok<AGROW>
    end
end
velocity=subR(mulR(R(p.eta_charge),q),mulR(R(p.loss_rate_per_h),star));
assert(cmp(velocity,R(0))>0&&cmp(star,R(E))>0&&cmp(cap,star)>0,'DCHR:v61:UnsupportedContact','Require increasing interior branch crossing.');
% Hot-flow contender must be mathematically simultaneous, not merely overlap.
if any(strcmp(w.candidate_labels,'LIMIT_HOT_FLOW'))
    assert(cmp(limits{3},q)==0,'DCHR:v61:UnresolvedOrdering','Overlapping unequal hot/branch events are unsupported.');
end
t=w.first_event_window_h;duration=sub(P(total),t);
assert(duration(1)>0,'DCHR:v61:UnresolvedHorizon','No certainly positive post-event span.');
eStar=bounds(star);eta=P(p.eta_charge);lambda=P(p.loss_rate_per_h);k=-fliplr(lambda);B=mul(eta,P(request));
[endE,intOut]=flow(eStar,duration,k,B);[~,intIn]=flow(P(E),t,k,B);
assert(endE(1)>eStar(2)&&endE(2)<bounds(cap)*[1;0],'DCHR:v61:UnsupportedEvent','Right endpoint must be strictly between branch and capacity.');
incomingHeat=mul(P(request),t);outgoingHeat=mul(P(request),duration);
srcIn=mul(incomingHeat,bounds(divR(a,addR(a,Lfloor))));srcOut=P(0);
l0=subR(addR(addR(Ta,d),R(s.condenser_approach_K)),Te);l1=divR(R(1),C);
for n=1:cells
    t0=mul(duration,div(P(n-1),P(cells)));t1=mul(duration,div(P(n),P(cells)));
    [e0,~]=flow(eStar,t0,k,B);[e1,~]=flow(eStar,t1,k,B);
    eh=[min(e0(1),e1(1)) max(e0(2),e1(2))];
    lift=add(bounds(l0),mul(bounds(l1),eh));
    rate=mul(P(request),div(bounds(a),add(bounds(a),lift)));
    % Each uncertain partition has exact duration/cells; avoid subtracting
    % independently enclosed nodes (would create artificial negative widths).
    srcOut=add(srcOut,mul(rate,div(duration,P(cells))));
end
heat=mul(P(request),P(total));source=add(srcIn,srcOut);work=sub(heat,source);
standing=mul(lambda,add(intIn,intOut));chargeLoss=mul(bounds(subR(R(1),R(p.eta_charge))),heat);aux=mul(P(s.aux_per_compressor),work);
law=sub(sub(sub(add(P(E),heat),endE),standing),chargeLoss);
assert(source(1)>=0&&work(1)>=0&&standing(1)>=0&&chargeLoss(1)>=0&&law(1)<=0&&law(2)>=0, ...
    'DCHR:v61:Resolution','Port positivity or first-law enclosure unresolved.');
z=struct('version','0.61','exact_branch_energy_MWh',star,'exact_capacity_MWh',cap, ...
    'exact_right_heat_MW',q,'exact_event_velocity_MW',velocity,'exact_cooling_coefficient',a, ...
    'exact_source_budget_MW',S,'exact_floor_lift_K',Lfloor,'exact_right_lift0_K',l0,'exact_right_lift1_per_h',l1, ...
    'event_time_h_interval',t,'event_energy_MWh_interval',eStar,'incoming_energy_MWh',E, ...
    'right_branch','TANK','right_equivalent_limiters',{tied},'incoming_event',w, ...
    'total_h',total,'cells',cells,'post_event_duration_h_interval',duration, ...
    'end_energy_MWh_interval',endE,'incoming_heat_MWh_interval',incomingHeat,'outgoing_heat_MWh_interval',outgoingHeat, ...
    'incoming_source_MWh_interval',srcIn,'outgoing_source_MWh_interval',srcOut, ...
    'heat_MWh_interval',heat,'source_MWh_interval',source,'compressor_MWh_interval',work, ...
    'standing_loss_MWh_interval',standing,'charge_loss_MWh_interval',chargeLoss,'aux_rejected_MWh_interval',aux, ...
    'first_law_MWh_interval',law,'initial_hp_age_h_interval',age,'event_hp_age_h_interval',add(age,t), ...
    'end_hp_age_h_interval',add(age,P(total)),'hp_latch_retained',true,'scalar_memory_handoff_authorized',false, ...
    'compiled_stateflow_handoff_authorized',false,'bounded_branch_continuation',true, ...
    'correlation',struct('constraint','E_event=C*(delivery+direct-ambient-charge_approach)', ...
    'incoming_trajectory','E(t)=E0+(eta*q-lambda*E0)*t*phi1(-lambda*t)', ...
    'time_constraint','t_event is the unique increasing incoming trajectory root at exact E_event', ...
    'outgoing_duration','total_h-t_event','outgoing_initial_energy','same exact E_event rational; no scalar reset', ...
    'hp_age','age_event=age_initial+t_event; age_end=age_initial+total_h', ...
    'port_credit','enclosures only; neither midpoint nor upper endpoint is scalar service'), ...
    'scope','HOST_CORRELATED_CONSTANT_REQUEST_BRANCH_CONTINUATION_NOT_COMPILED_STATEFLOW_ACCEPTANCE');
end
function [e,integral]=flow(initial,t,k,B)
x=mul(k,t);assert(max(abs(x))<=1,'DCHR:v61:Span','Require outward |lambda*t|<=1.');
v=add(mul(k,initial),B);f1=P(1);f2=P(.5);term=P(1);
for ii=1:24,term=div(mul(term,x),P(ii+1));f1=add(f1,term);f2=add(f2,div(term,P(ii+2)));end
fac=P(1);for ii=2:26,fac=mul(fac,P(ii));end
tail=div(P(3),fac);f1=add(f1,[-tail(2) tail(2)]);f2=add(f2,[-tail(2) tail(2)]);
e=add(initial,mul(mul(v,t),f1));integral=add(mul(initial,t),mul(mul(v,mul(t,t)),f2));
end
function z=P(v),z=[v v];end
function z=add(x,y),if all(x==0),z=y;elseif all(y==0),z=x;else,z=out([x(1)+y(1) x(2)+y(2)]);end;end
function z=sub(x,y),if all(y==0),z=x;else,z=out([x(1)-y(2) x(2)-y(1)]);end;end
function z=mul(x,y)
if all(x==0)||all(y==0),z=[0 0];return;end
t=[x(1)*y(1) x(1)*y(2) x(2)*y(1) x(2)*y(2)];z=out([min(t) max(t)]);
end
function z=div(x,y)
assert(y(1)>0,'DCHR:v61:Resolution','Strictly positive denominator required.');
t=[x(1)/y(1) x(1)/y(2) x(2)/y(1) x(2)/y(2)];z=out([min(t) max(t)]);
end
function z=out(t)
assert(all(isfinite(t)),'DCHR:v61:Resolution','Nonfinite basic operation.');
z=[t(1)-2*eps(t(1)) t(2)+2*eps(t(2))];assert(all(isfinite(z))&&z(1)<=z(2),'DCHR:v61:Resolution','Expansion overflow.');
end

