function plan=dchr_segment_plan_v32(x,E,p,h,model_dt)
% Host HP plan; Stateflow independently authorizes/integrates both segments.
% Normal-mode only. Inputs and scenario constants retain the v30 convention.
assert(isreal(p) && numel(p)==11 && all(isfinite(p)) && p(1)==model_dt, ...
    'DCHR:v32:Domain','Invalid parameters or physical/model timestep mismatch.');
% Inherited adapter validates the physical and HP domain before any planning.
dchr_stateflow_hp_v30(x,E,p,h,model_dt);
% Canonicalize only capacity roundoff after validation, using the allocator's
% existing 64-ulp energy tolerance. This is not a controller deadband.
if abs(E-p(2))<=64*eps(max(1,p(2))),E=p(2);end
request=x(4)+p(3);
if E==p(2),request=x(4)+min(p(3),p(7)*p(2)/p(5));end
u=hp(x,request,h);direct=min(x(4),u(1));
qc=min(p(3),max(0,u(1)-direct));qd=0;
if E>p(8),qd=min(p(4),max(0,x(4)-direct));end
z=dchr.components.storage_event_kernel_v31(E,qc,qd,p(1:10));
duration=z(14);kind=z(15);tail=p(1)-duration;
% The loss-replacement operating point is an equilibrium, not a zero-time
% capacity event caused by one-ulp multiplication/subtraction differences.
if E==p(2) && qd==0 && abs(p(5)*qc-p(7)*p(2))<=64*eps(max(1,p(7)*p(2)))
    duration=p(1);kind=0;tail=0;z(4)=E;
end
plan=zeros(14,2);
plan(:,1)=[duration;E;x(4);u(1:3);request;u(4:6);qc;qd;kind;0];
if kind>0 && tail>0
    eventE=z(18);tailRequest=request;
    if kind==1,tailRequest=x(4)+min(p(3),p(7)*p(2)/p(5));end
    v=hp(x,tailRequest,h);tailDirect=min(x(4),v(1));
    tailC=min(p(3),max(0,v(1)-tailDirect));
    % Cutoff disables discharge. Capacity hold may cool if HP becomes unavailable.
    plan(:,2)=[tail;eventE;x(4);v(1:3);tailRequest;v(4:6);tailC;0;kind;duration];
else
    plan(:,2)=[0;z(4);x(4);0;0;0;0;NaN;0;x(1);0;0;kind;duration];
end
end

function u=hp(x,request,h)
cfg.hp=struct('max_heat_output_MW',h(1),'carnot_efficiency',h(2), ...
    'cop_min',h(3),'cop_max',h(4),'part_load_penalty',h(5), ...
    'poly_c0',h(7),'poly_c1',h(8),'poly_c2',h(9));
cfg.model.hp_backend='carnot';if h(6)==1,cfg.model.hp_backend='lift_polynomial';end
a=dchr.components.heat_pump_step_v14(x(1),x(2),x(3),request,cfg);
u=[a.heat_output_MW;a.electric_MW;a.source_used_MW;a.cop_operating; ...
    double(a.available);max(0,x(1)-a.source_used_MW)];
end
