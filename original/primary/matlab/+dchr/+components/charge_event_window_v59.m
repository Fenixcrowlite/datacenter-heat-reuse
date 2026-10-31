function z=charge_event_window_v59(s,p,E,horizon,request,iterations)
% Outward first-event isolation for a fixed initial charge regime.
% Flow after the first guard zero is a mathematical continuation ONLY.
% No midpoint, boundary snap, new branch or memory handoff is authorized.
if nargin<6,iterations=80;end
assert(isa(horizon,'double')&&isreal(horizon)&&isscalar(horizon)&&isfinite(horizon)&&horizon>0 && ...
    isa(iterations,'double')&&isreal(iterations)&&isscalar(iterations)&&isfinite(iterations)&& ...
    iterations==fix(iterations)&&iterations>=1&&iterations<=128, ...
    'DCHR:v59:Domain','Positive finite horizon and 1..128 iterations required.');
r=dchr.components.charge_regime_events_v56(s,p,E,request);
P=@(v)[v v];C=P(p.heat_capacity_MWh_per_K);Ta=P(p.ambient_C);
Te=sub(sub(P(s.source_in_C),P(s.source_glide_K)),P(s.evaporator_approach_K));
a=mul(P(s.cooling_factor),add(Te,P(273.15)));S=mul(P(s.source_capacity_MW_per_K),P(s.source_glide_K));
H=P(s.hot_capacity_MW_per_K);F=add(P(s.delivery_C),P(s.direct_approach_K));d=P(s.charge_approach_K);
alpha=zeros(5,2);beta=[P(request);P(s.hp_capacity_MW);P(0);P(0);P(p.charge_limit_MW)];
if strcmp(r.branch,'TANK')
    l0=sub(add(add(Ta,d),P(s.condenser_approach_K)),Te);
    beta(3,:)=mul(H,d);alpha(4,:)=div(S,mul(a,C));beta(4,:)=mul(S,add(P(1),div(l0,a)));
else
    l0=sub(add(F,P(s.condenser_approach_K)),Te);
    alpha(3,:)=neg(div(H,C));beta(3,:)=mul(H,sub(F,Ta));beta(4,:)=mul(S,add(P(1),div(l0,a)));
end
j=r.limiter_index;k=sub(mul(P(p.eta_charge),alpha(j,:)),P(p.loss_rate_per_h));
B=mul(P(p.eta_charge),beta(j,:));v=add(mul(k,P(E)),B);
assert(max(abs(mul(k,P(horizon))))<=1,'DCHR:v59:Span','Require outward |k*horizon|<=1.');
% Positive affine guards: zero, capacity, branch, heat, four rival limits.
ga=[P(1);P(-1);div(P(1),C);alpha(j,:)];
gb=[P(0);mul(C,sub(P(s.tank_max_C),Ta));sub(add(Ta,d),F);beta(j,:)];
if strcmp(r.branch,'FLOOR'),ga(3,:)=neg(ga(3,:));gb(3,:)=neg(gb(3,:));end
labels={'ZERO','CAPACITY','BRANCH','HEAT_ZERO'};names={'REQUEST','NAMEPLATE','HOT_FLOW','SOURCE','TES_PORT'};
for n=1:5
    if n==j,continue;end
    ga(end+1,:)=sub(alpha(n,:),alpha(j,:));gb(end+1,:)=sub(beta(n,:),beta(j,:)); %#ok<AGROW>
    labels{end+1}=['LIMIT_' names{n}]; %#ok<AGROW>
end
start=guards(P(E));assert(all(start(:,1)>0),'DCHR:v59:InitialUnresolved','Strict initial guards required.');
finish=flow(horizon);last=guards(finish);windows=zeros(8,2);endpoint=zeros(8,4);steps=zeros(8,1);exists=false(8,1);upperCertified=false(8,1);
for n=1:8
    if last(n,1)>0
        windows(n,:)=[horizon horizon];endpoint(n,:)=[last(n,:) last(n,:)];continue;
    end
    exists(n)=true;lo=0;hi=horizon;gl=start(n,:);gh=last(n,:);
    for it=1:iterations
        mid=lo+(hi-lo)/2;if mid==lo||mid==hi,break;end
        gm=guards(flow(mid));gm=gm(n,:);steps(n)=it;
        if gm(1)>0,lo=mid;gl=gm;
        elseif gm(2)<0,hi=mid;gh=gm;
        else,break;end % No tolerance or tie-breaking side at uncertain sign.
    end
    windows(n,:)=[lo hi];endpoint(n,:)=[gl gh];upperCertified(n)=gh(2)<0;
end
if ~any(exists)
    status='CERTIFIED_NO_EVENT';first=[horizon horizon];contenders={};prefix=horizon;isolated=false;
else
    prefix=min(windows(exists,1));cert=exists&upperCertified;
    if any(cert),upper=min(windows(cert,2));status='ISOLATED_EVENT_BLOCKED';isolated=true;
    else,upper=horizon;status='HORIZON_UNRESOLVED_BLOCKED';isolated=false;end
    first=[prefix upper];contenders=labels(exists & windows(:,1)<=upper);
end
prefixEnergy=flow(prefix);prefixGuards=guards(prefixEnergy);
assert(all(prefixGuards(:,1)>0),'DCHR:v59:PrefixUnresolved','Prefix endpoint must retain strict guards.');
z=struct('version','0.59','branch',r.branch,'limiter',r.limiter,'limiter_index',j, ...
    'horizon_h',horizon,'iterations',iterations,'status',status,'guard_labels',{labels}, ...
    'guard_alpha_interval',ga,'guard_beta_interval',gb,'initial_guard_intervals',start, ...
    'horizon_guard_intervals',last,'guard_time_windows_h',windows,'guard_endpoint_intervals',endpoint, ...
    'guard_has_candidate',exists,'upper_crossing_certified',upperCertified,'bisection_steps',steps, ...
    'first_event_window_h',first,'candidate_labels',{contenders},'crossing_isolated',isolated, ...
    'unique_first_guard',isolated&&numel(contenders)==1,'safe_prefix_h',prefix, ...
    'safe_prefix_energy_MWh_interval',prefixEnergy,'safe_prefix_guard_intervals',prefixGuards, ...
    'continuation_energy_at_horizon_MWh_interval',finish,'k_interval',k,'B_interval',B, ...
    'initial_velocity_interval',v,'event_transition_authorized',false,'memory_handoff_authorized',false, ...
    'scope','CERTIFIED_PRE_EVENT_PREFIX_AND_EVENT_WINDOW_NO_POST_EVENT_PHYSICAL_FLOW_OR_MEMORY_RESET');
    function en=flow(t)
        if t==0,en=P(E);return;end
        x=mul(k,P(t));assert(max(abs(x))<=1,'DCHR:v59:Span','Outward evaluation node exceeds span.');
        phi=P(1);term=P(1);
        for ii=1:24,term=div(mul(term,x),P(ii+1));phi=add(phi,term);end
        factorial=P(1);for ii=2:26,factorial=mul(factorial,P(ii));end
        tail=div(P(3),factorial);phi=add(phi,[-tail(2) tail(2)]);
        en=add(P(E),mul(mul(v,P(t)),phi));
    end
    function gs=guards(en)
        gs=zeros(8,2);for q=1:8,gs(q,:)=add(mul(ga(q,:),en),gb(q,:));end
    end
end
function z=add(x,y),z=out([x(1)+y(1) x(2)+y(2)]);end
function z=sub(x,y),z=out([x(1)-y(2) x(2)-y(1)]);end
function z=neg(x),z=[-x(2) -x(1)];end
function z=mul(x,y)
t=[x(1)*y(1) x(1)*y(2) x(2)*y(1) x(2)*y(2)];z=out([min(t) max(t)]);
end
function z=div(x,y)
assert(y(1)>0,'DCHR:v59:Resolution','Strictly positive denominator required.');
t=[x(1)/y(1) x(1)/y(2) x(2)/y(1) x(2)/y(2)];z=out([min(t) max(t)]);
end
function z=out(t)
assert(all(isfinite(t)),'DCHR:v59:Resolution','Nonfinite basic operation.');
z=[t(1)-2*eps(t(1)) t(2)+2*eps(t(2))];assert(all(isfinite(z))&&z(1)<=z(2),'DCHR:v59:Resolution','Expansion overflow.');
end
