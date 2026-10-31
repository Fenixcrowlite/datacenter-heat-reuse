function z=source_affine_charge_step_v54(s,p,E,dt,request)
% Exact continuous tank-coupled SOURCE-limited charging only, no dispatch.
% Rejects a branch crossing/capacity hit instead of silently integrating it.
for v={dt,request,p.eta_charge,p.loss_rate_per_h}
    assert(isa(v{1},'double')&&isreal(v{1})&&isscalar(v{1})&&isfinite(v{1}), ...
        'DCHR:v54:Domain','Finite real double required.');
end
assert(dt>0&&request>0&&p.eta_charge>0&&p.eta_charge<=1&&p.loss_rate_per_h>=0, ...
    'DCHR:v54:Domain','Positive span/charge request and valid loss/efficiency required.');
b=dchr.components.coupled_temperature_boundary_v54(s,p,E,request);
assert(b.tank_branch&&b.source_budget_MW>0&&b.limiter==4, ...
    'DCHR:v54:BranchEventRequired','Need a strictly source-limited tank branch.');
C=p.heat_capacity_MWh_per_K;S=b.source_budget_MW;
a=s.cooling_factor*(b.evaporator_C+273.15);
L0=p.ambient_C+s.charge_approach_K+s.condenser_approach_K-b.evaporator_C;
alpha=S/(a*C);beta=S*(1+L0/a);
k=p.eta_charge*alpha-p.loss_rate_per_h;B=p.eta_charge*beta;x=k*dt;
if x==0,phi=dt;psi=dt^2/2;
else
    phi=expm1(x)/k;
    if abs(x)<1e-4
        psi=dt^2*(.5+x*(1/6+x*(1/24+x*(1/120+x/720))));
    else,psi=(phi-dt)/k;end
end
endE=E*exp(x)+B*phi;integralE=E*phi+B*psi;
assert(all(isfinite([endE integralE phi psi]))&&endE>=0&& ...
    endE<=C*(s.tank_max_C-p.ambient_C),'DCHR:v54:BranchEventRequired','Tank bound/event reached.');
finish=dchr.components.coupled_temperature_boundary_v54(s,p,endE,request);
assert(finish.tank_branch&&finish.limiter==4,'DCHR:v54:BranchEventRequired', ...
    'Temperature or active limiter changes; split at the event before integration.');
heat=alpha*integralE+beta*dt;work=S/a*(L0*dt+integralE/C);source=S*dt;
standing=p.loss_rate_per_h*integralE;chargeLoss=(1-p.eta_charge)*heat;
aux=s.aux_per_compressor*work;
z=struct('initial_energy_MWh',E,'end_energy_MWh',endE,'span_h',dt, ...
    'k_per_h',k,'B_MW',B,'integral_energy_MWh_h',integralE,'heat_MWh',heat, ...
    'compressor_MWh',work,'source_MWh',source,'aux_rejected_MWh',aux, ...
    'standing_loss_MWh',standing,'charge_loss_MWh',chargeLoss, ...
    'first_law_residual_MWh',E+source+work-endE-standing-chargeLoss, ...
    'start_boundary',b,'end_boundary',finish,'scope','EXACT_SINGLE_SOURCE_LIMITED_CHARGE_REGIME_NO_EVENTS');
end
