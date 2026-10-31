function z=charge_correlated_event_v60(s,p,E,horizon,request,clock0,cells)
% Scoped FLOOR->TANK event record, retaining exact manifold and shared theta.
% Numeric arrays are projections of a correlated record, never scalar memory.
if nargin<7,cells=128;end
assert(isequal(size(clock0),[1 2])&&isreal(clock0)&&all(isfinite(clock0))&& ...
    clock0(1)>=0&&clock0(1)<=clock0(2),'DCHR:v60:Domain','Ordered nonnegative initial HP age required.');
R=@(v)dchr.components.exact_rational_v60('from',v);
add=@(x,y)dchr.components.exact_rational_v60('add',x,y);
sub=@(x,y)dchr.components.exact_rational_v60('sub',x,y);
mul=@(x,y)dchr.components.exact_rational_v60('mul',x,y);
cmp=@(x,y)dchr.components.exact_rational_v60('cmp',x,y);
iv=@(x)dchr.components.exact_rational_v60('interval',x);
text=@(x)dchr.components.exact_rational_v60('text',x);
event=dchr.components.charge_event_window_v59(s,p,E,horizon,request);
assert(strcmp(event.branch,'FLOOR')&&event.crossing_isolated && ...
    any(strcmp(event.candidate_labels,'BRANCH')) && ...
    all(ismember(event.candidate_labels,{'BRANCH','LIMIT_HOT_FLOW'})), ...
    'DCHR:v60:UnsupportedEvent','Only isolated upward branch with exact hot-flow co-contact is supported.');
before=dchr.components.charge_coefficients_exact_v60(s,p,request,'FLOOR');
after=dchr.components.charge_coefficients_exact_v60(s,p,request,'TANK');Ek=before.branch_energy;
incoming=event.limiter_index;Q=@(c,j,en)add(mul(c.alpha{j},en),c.beta{j});
assert(cmp(Ek,R(E))>0&&cmp(Ek,before.capacity)<0,'DCHR:v60:UnsupportedEvent','Interior upward branch required.');
for label=event.candidate_labels
    if strcmp(label{1},'LIMIT_HOT_FLOW')
        assert(cmp(Q(before,3,Ek),Q(before,incoming,Ek))==0,'DCHR:v60:ContactUnresolved','Overlapping windows are not proof of exact contact.');
    end
end
% Lexicographic value, then right derivative (positive velocity => slope).
outgoing=1;
for n=2:5
    order=cmp(Q(after,n,Ek),Q(after,outgoing,Ek));
    if order<0 || (order==0&&cmp(after.alpha{n},after.alpha{outgoing})<0),outgoing=n;end
end
eta=R(p.eta_charge);loss=R(p.loss_rate_per_h);
vin=sub(mul(eta,Q(before,incoming,Ek)),mul(loss,Ek));
vout=sub(mul(eta,Q(after,outgoing,Ek)),mul(loss,Ek));
assert(cmp(vin,R(0))>0&&cmp(vout,R(0))>0,'DCHR:v60:UnsupportedEvent','Positive one-sided velocity required.');
assert(cmp(Q(before,incoming,Ek),Q(after,outgoing,Ek))==0,'DCHR:v60:ContactUnresolved','Heat continuity required.');
equiv=false(1,5);for n=1:5,equiv(n)=cmp(after.alpha{n},after.alpha{outgoing})==0&&cmp(after.beta{n},after.beta{outgoing})==0;end
theta=event.first_event_window_h;post=[horizon-theta(2) horizon-theta(1)];
post=[post(1)-2*eps(post(1)) post(2)+2*eps(post(2))];
assert(theta(1)>0&&post(1)>0,'DCHR:v60:UnsupportedEvent','Positive certified times on both sides required.');
incomingFlow=dchr.components.charge_interval_flow_v60(before,incoming,[E E],theta,p,s,cells);
endpoint=iv(Ek);outgoingFlow=dchr.components.charge_interval_flow_v60(after,outgoing,endpoint,post,p,s,cells);
assert(incomingFlow.end_energy_MWh_interval(1)<=endpoint(1)&&incomingFlow.end_energy_MWh_interval(2)>=endpoint(2), ...
    'DCHR:v60:Resolution','Incoming trajectory does not enclose exact manifold.');
% Exact signs at the manifold and upper-energy projection prove all outgoing guards.
endHi=R(outgoingFlow.end_energy_MWh_interval(2));
assert(cmp(endHi,after.capacity)<0,'DCHR:v60:NextEvent','Outgoing inventory can reach capacity.');
for n=1:5
    if equiv(n),continue;end
    g0=sub(Q(after,n,Ek),Q(after,outgoing,Ek));g1=sub(Q(after,n,endHi),Q(after,outgoing,endHi));
    assert(cmp(g0,R(0))>=0&&cmp(g1,R(0))>0,'DCHR:v60:NextEvent','Another limiter event is unresolved.');
end
assert(cmp(Q(after,outgoing,Ek),R(0))>0&&cmp(Q(after,outgoing,endHi),R(0))>0,'DCHR:v60:NextEvent','Positive heat required.');
total=struct();names=fieldnames(incomingFlow);
for n=1:numel(names)
    name=names{n};if contains(name,'MWh_interval')&&~contains(name,'energy')&&~contains(name,'first_law')
        total.(name)=outadd(incomingFlow.(name),outgoingFlow.(name));
    end
end
total.end_energy_MWh_interval=outgoingFlow.end_energy_MWh_interval;
total.first_law_MWh_interval=outsub(outsub(outsub(outadd([E E],total.heat_MWh_interval), ...
    total.end_energy_MWh_interval),total.standing_loss_MWh_interval),total.charge_loss_MWh_interval);
clockEvent=outadd(clock0,theta);clockEnd=outadd(clock0,[horizon horizon]);
names={'REQUEST','NAMEPLATE','HOT_FLOW','SOURCE','TES_PORT'};
z=struct('version','0.60','scope','CORRELATED_UPWARD_BRANCH_RECORD_NOT_FULL_PLANT_CONTROLLER', ...
    'initial_energy_MWh',E,'horizon_h',horizon,'initial_clock_h_interval',clock0, ...
    'event_energy_exact',text(Ek),'event_energy_MWh_interval',endpoint,'event_time_h_interval',theta, ...
    'incoming_branch','FLOOR','outgoing_branch','TANK','incoming_limiter_index',incoming, ...
    'outgoing_limiter_index',outgoing,'equivalent_limiter_mask',double(equiv), ...
    'equivalent_limiter_names',{names(equiv)},'incoming_flow',incomingFlow,'outgoing_flow',outgoingFlow, ...
    'total',total,'event_clock_h_interval',clockEvent,'end_clock_h_interval',clockEnd, ...
    'correlation',struct('parameter','theta = exact first root of incoming E(theta)=event_energy_exact', ...
        'event_inventory','same exact rational manifold on both sides', ...
        'post_duration','horizon_h - theta','event_age','initial_age + theta', ...
        'end_age','initial_age + horizon_h; no HP transition/reset'), ...
    'record_handoff_authorized',true,'scalar_memory_handoff_authorized',false, ...
    'full_coupled_stateflow_acceptance',false,'event_window',event);
end
function z=outadd(x,y),z=expand([x(1)+y(1) x(2)+y(2)]);end
function z=outsub(x,y),z=expand([x(1)-y(2) x(2)-y(1)]);end
function z=expand(v)
assert(all(isfinite(v)),'DCHR:v60:Resolution','Nonfinite projection.');z=[v(1)-2*eps(v(1)) v(2)+2*eps(v(2))];
end
