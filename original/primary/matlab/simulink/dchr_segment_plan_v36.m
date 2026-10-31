function plan=dchr_segment_plan_v36(x,E,p,h,dt,m,c)
% Normal-mode held-input analytic planner. Clock is physical hours, not ticks.
% c=[restart_MWh,min_on_h,min_off_h,max_positive_segments]; m=[ON,age_h].
dchr_stateflow_hp_v30(x,E,p,h,dt);
assert(isreal(c)&&numel(c)==4&&all(isfinite(c))&&c(1)>p(8)&&c(1)<p(2)&& ...
    all(c(2:3)>=0)&&c(4)==floor(c(4))&&c(4)>=1&&c(4)<=64,'DCHR:v36:ControlDomain','Invalid hysteresis/dwell configuration.');
assert(isreal(m)&&numel(m)==2&&all(isfinite(m))&&ismember(m(1),[0 1])&&m(2)>=0, ...
    'DCHR:v36:ClockDomain','Invalid HP latch/physical clock.');
plan=zeros(18,64);on=m(1);age=m(2);offset=0;count=0;
etol=64*eps(max(1,p(2)));
ptol=64*eps(max(1,max(abs([x(1);x(4);p(3);p(4);p(11);h(1)]))));
ttol=stateflow_time_tolerance_v36([dt;m(2);c(2);c(3)]);
while offset<dt
    ttol=stateflow_time_tolerance_v36([dt;age;c(2);c(3)]);
    remain=dt-offset;reason=0;
    if abs(E-p(2))<=etol,E=p(2);end
    if abs(E-p(8))<=etol,E=p(8);end
    highRequest=x(4)+p(3);high=hp(x,highRequest,h);
    highC=max(0,high(1)-min(x(4),high(1)));
    cycle=p(5)*highC>p(7)*p(2)+ptol;
    request=highRequest;u=high;
    if on==1 && E==p(2) && cycle
        request=x(4)+min(p(3),p(7)*p(2)/p(5));u=hp(x,request,h);
        if age>=c(2)-ttol,on=0;age=0;reason=2;
        elseif u(1)==0,on=0;age=0;reason=1;end
    elseif on==1 && E==p(2)
        request=x(4)+min(p(3),p(7)*p(2)/p(5));u=hp(x,request,h);
    end
    if on==1 && u(1)==0,on=0;age=0;reason=1;end
    if on==0 && reason==0 && E<=c(1)+etol && age>=c(3)-ttol && high(1)>0
        on=1;age=0;reason=3;request=highRequest;u=high;
    end
    if on==0,request=0;u=[0;0;0;NaN;0;x(1)];end
    direct=min(x(4),u(1));qc=min(p(3),max(0,u(1)-direct));qd=0;
    if E>p(8),qd=min(p(4),max(0,x(4)-direct));end
    P=p(5)*qc-qd/p(6);span=remain;kind=0;
    % Earliest physical energy boundary, independent of macro clock.
    if qc>0 && P>p(7)*p(2)+ptol
        t=hit(E,p(2),P,p(7));if t<=span,span=t;kind=1;end
    elseif qd>0
        t=hit(E,p(8),P,p(7));if t<=span,span=t;kind=2;end
    end
    if on==0 && high(1)>0
        tr=0;
        if E>c(1)+etol
            tr=Inf;if P-p(7)*E<0,tr=hit(E,c(1),P,p(7));end
        end
        t=max(tr,max(0,c(3)-age));
        if t>ttol && t<span,span=t;kind=3;end
    elseif on==1 && E==p(2) && cycle && age<c(2)-ttol
        t=c(2)-age;if t<span,span=t;kind=4;end
    end
    assert(isfinite(span)&&span>0,'DCHR:v36:EventProgress','Nonpositive event progress.');
    count=count+1;
    assert(count<=c(4),'DCHR:v36:EventExhaustion','Event budget exhausted; no truncated result accepted.');
    plan(:,count)=[span;E;x(4);u(1:3);request;u(4:6);qc;qd;kind;offset;on;age;reason;age+span];
    E=advance(E,P,p(7),span);
    if kind==1,E=p(2);elseif kind==2,E=p(8);end
    assert(age+span>age && offset+span>offset,'DCHR:v36:TimeResolution','Positive segment must advance representable physical clocks.');
    age=age+span;offset=offset+span;
    if dt-offset<=ttol && offset~=dt
        % Include any representable roundoff remainder rather than drop energy.
        extra=dt-offset;plan(1,count)=plan(1,count)+extra;plan(18,count)=age+extra;
        E=advance(E,P,p(7),extra);age=age+extra;offset=dt;
    end
end
for k=count+1:64
    plan(:,k)=[0;E;x(4);0;0;0;0;NaN;0;x(1);0;0;0;dt;on;age;0;age];
end
end
function t=hit(E,target,P,rate)
if rate==0,t=(target-E)/P;
else,t=log1p(rate*(target-E)/(P-rate*target))/rate;end
assert(isreal(t)&&isfinite(t)&&t>=0,'DCHR:v36:EventDomain','Nonrepresentable boundary time.');
end
function E=advance(E,P,rate,t)
phi=t;if rate>0,phi=-expm1(-rate*t)/rate;end
E=E*exp(-rate*t)+P*phi;
end
function u=hp(x,request,h)
cfg.hp=struct('max_heat_output_MW',h(1),'carnot_efficiency',h(2),'cop_min',h(3), ...
    'cop_max',h(4),'part_load_penalty',h(5),'poly_c0',h(7),'poly_c1',h(8),'poly_c2',h(9));
cfg.model.hp_backend='carnot';if h(6)==1,cfg.model.hp_backend='lift_polynomial';end
a=dchr.components.heat_pump_step_v14(x(1),x(2),x(3),request,cfg);
u=[a.heat_output_MW;a.electric_MW;a.source_used_MW;a.cop_operating;double(a.available);max(0,x(1)-a.source_used_MW)];
end
