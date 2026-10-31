function z=charge_enclosure_v58(s,p,E,dt,request,cells)
% Bounded single-regime charge flow. No endpoint transition authorization.
% Exact binary inputs; outward basic arithmetic, finite Taylor tail, and
% interval rectangles for variable source/compressor energy. No exp/log calls.
if nargin<6,cells=256;end
assert(isa(dt,'double')&&isreal(dt)&&isscalar(dt)&&isfinite(dt)&&dt>0 && ...
    isa(cells,'double')&&isreal(cells)&&isscalar(cells)&&isfinite(cells)&&cells==fix(cells)&&cells>=1&&cells<=4096, ...
    'DCHR:v58:Domain','Positive finite span and 1..4096 integer cells required.');
r=dchr.components.charge_regime_events_v56(s,p,E,request);
P=@(v)[v v]; C=P(p.heat_capacity_MWh_per_K);Ta=P(p.ambient_C);
Te=sub(sub(P(s.source_in_C),P(s.source_glide_K)),P(s.evaporator_approach_K));
a=mul(P(s.cooling_factor),add(Te,P(273.15)));S=mul(P(s.source_capacity_MW_per_K),P(s.source_glide_K));
H=P(s.hot_capacity_MW_per_K);F=add(P(s.delivery_C),P(s.direct_approach_K));
d=P(s.charge_approach_K);eta=P(p.eta_charge);lambda=P(p.loss_rate_per_h);
alpha=zeros(5,2);beta=[P(request);P(s.hp_capacity_MW);P(0);P(0);P(p.charge_limit_MW)];
if strcmp(r.branch,'TANK')
    l0=sub(add(add(Ta,d),P(s.condenser_approach_K)),Te);l1=div(P(1),C);
    beta(3,:)=mul(H,d);alpha(4,:)=div(S,mul(a,C));beta(4,:)=mul(S,add(P(1),div(l0,a)));
else
    l0=sub(add(F,P(s.condenser_approach_K)),Te);l1=P(0);
    alpha(3,:)=neg(div(H,C));beta(3,:)=mul(H,sub(F,Ta));beta(4,:)=mul(S,add(P(1),div(l0,a)));
end
j=r.limiter_index;A=alpha(j,:);B=beta(j,:);k=sub(mul(eta,A),lambda);b=mul(eta,B);
v=add(mul(k,P(E)),b);span=P(dt);
assert(max(abs(mul(k,span)))<=1,'DCHR:v58:Span','Require |k*dt|<=1; split the interval.');
[finish,intE]=flow(span);hull=[min(E,finish(1)) max(E,finish(2))];
% Each exact member is monotone (velocity sign cannot change for affine ODE).
capacity=mul(C,sub(P(s.tank_max_C),Ta));gap=sub(add(add(Ta,div(hull,C)),d),F);
limits=zeros(5,2);for n=1:5,limits(n,:)=add(mul(alpha(n,:),hull),beta(n,:));end
branchOK=(strcmp(r.branch,'TANK')&&gap(1)>0)||(strcmp(r.branch,'FLOOR')&&gap(2)<0);
assert(hull(1)>=0&&hull(2)<capacity(1)&&branchOK && limits(j,1)>0 && ...
    limits(j,2)<min(limits([1:j-1 j+1:5],1)), ...
    'DCHR:v58:EventUnresolved','Energy enclosure touches a bound, branch or competing limiter.');
heat=add(mul(A,intE),mul(B,span));
if j==4
    source=mul(S,span); % q=S*(1+L/a): evaporator rate identically S.
elseif strcmp(r.branch,'FLOOR')
    source=mul(heat,div(a,add(l0,a)));
else
    source=P(0);
    for n=1:cells
        % Time nodes and widths also enclosed; no rounded partition gaps.
        t0=mul(span,div(P(n-1),P(cells)));t1=mul(span,div(P(n),P(cells)));
        [e0,~]=flow(t0);[e1,~]=flow(t1);
        eh=[min(e0(1),e1(1)) max(e0(2),e1(2))];
        q=add(mul(A,eh),B);lift=add(l0,mul(l1,eh));
        src=mul(q,div(a,add(lift,a)));
        source=add(source,mul(src,sub(t1,t0)));
    end
end
work=sub(heat,source);standing=mul(lambda,intE);chargeLoss=mul(sub(P(1),eta),heat);
aux=mul(P(s.aux_per_compressor),work);
residual=sub(sub(sub(add(P(E),heat),finish),standing),chargeLoss);
assert(work(1)>=0&&source(1)>=0&&residual(1)<=0&&residual(2)>=0, ...
    'DCHR:v58:Resolution','Unresolved work/source positivity or balance enclosure.');
z=struct('version','0.58','branch',r.branch,'limiter',r.limiter,'limiter_index',j, ...
    'span_h',dt,'cells',cells,'alpha_interval',A,'beta_interval',B,'k_interval',k,'B_interval',b, ...
    'lift0_interval',l0,'lift1_interval',l1,'cooling_coefficient_interval',a, ...
    'end_energy_MWh_interval',finish,'integral_energy_MWh_h_interval',intE, ...
    'heat_MWh_interval',heat,'source_MWh_interval',source,'compressor_MWh_interval',work, ...
    'standing_loss_MWh_interval',standing,'charge_loss_MWh_interval',chargeLoss, ...
    'aux_rejected_MWh_interval',aux,'first_law_MWh_interval',residual, ...
    'event_transition_authorized',false,'scope','BOUNDED_SINGLE_CHARGE_REGIME_NO_EVENT_ENDPOINT_OR_STATEFLOW_INTEGRATION');
    function [energy,integral]=flow(t)
        x=mul(k,t);
        assert(max(abs(x))<=1,'DCHR:v58:Span','Outward time nodes require |k*t|<=1.');
        f1=P(1);f2=P(.5);term=P(1);
        for ii=1:24
            term=div(mul(term,x),P(ii+1));f1=add(f1,term);f2=add(f2,div(term,P(ii+2)));
        end
        % |x|<=1. Remaining phi1 terms <= 3/26!; phi2 smaller.
        % Compute upper tail outward, including factorial arithmetic.
        factorial=P(1);for ii=2:26,factorial=mul(factorial,P(ii));end
        tail=div(P(3),factorial);f1=add(f1,[-tail(2) tail(2)]);f2=add(f2,[-tail(2) tail(2)]);
        energy=add(P(E),mul(mul(v,t),f1));
        integral=add(mul(P(E),t),mul(mul(v,mul(t,t)),f2));
    end
end
function z=add(x,y),z=out([x(1)+y(1) x(2)+y(2)]);end
function z=sub(x,y),z=out([x(1)-y(2) x(2)-y(1)]);end
function z=neg(x),z=[-x(2) -x(1)];end
function z=mul(x,y)
t=[x(1)*y(1) x(1)*y(2) x(2)*y(1) x(2)*y(2)];z=out([min(t) max(t)]);
end
function z=div(x,y)
assert(y(1)>0,'DCHR:v58:Resolution','Strictly positive denominator required.');
t=[x(1)/y(1) x(1)/y(2) x(2)/y(1) x(2)/y(2)];z=out([min(t) max(t)]);
end
function z=out(t)
assert(all(isfinite(t)),'DCHR:v58:Resolution','Nonfinite basic operation.');
z=[t(1)-2*eps(t(1)) t(2)+2*eps(t(2))];
assert(all(isfinite(z))&&z(1)<=z(2),'DCHR:v58:Resolution','Expansion overflow.');
end
