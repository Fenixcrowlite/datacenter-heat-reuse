function c=charge_coefficients_exact_v60(s,p,request,branch)
% Five affine charge limits derived exactly from the original binary inputs.
R=@(v)dchr.components.exact_rational_v60('from',v);
add=@(x,y)dchr.components.exact_rational_v60('add',x,y);
sub=@(x,y)dchr.components.exact_rational_v60('sub',x,y);
mul=@(x,y)dchr.components.exact_rational_v60('mul',x,y);
div=@(x,y)dchr.components.exact_rational_v60('div',x,y);
C=R(p.heat_capacity_MWh_per_K);Ta=R(p.ambient_C);d=R(s.charge_approach_K);
F=add(R(s.delivery_C),R(s.direct_approach_K));Te=sub(sub(R(s.source_in_C),R(s.source_glide_K)),R(s.evaporator_approach_K));
a=mul(R(s.cooling_factor),add(Te,R(273.15)));S=mul(R(s.source_capacity_MW_per_K),R(s.source_glide_K));H=R(s.hot_capacity_MW_per_K);
al=repmat({R(0)},5,1);be={R(request);R(s.hp_capacity_MW);R(0);R(0);R(p.charge_limit_MW)};
if strcmp(branch,'TANK')
    l0=sub(add(add(Ta,d),R(s.condenser_approach_K)),Te);l1=div(R(1),C);
    be{3}=mul(H,d);al{4}=div(S,mul(a,C));be{4}=mul(S,add(R(1),div(l0,a)));
else
    assert(strcmp(branch,'FLOOR'),'DCHR:v60:ExactDomain','Unknown branch.');
    l0=sub(add(F,R(s.condenser_approach_K)),Te);l1=R(0);
    al{3}=div(sub(R(0),H),C);be{3}=mul(H,sub(F,Ta));be{4}=mul(S,add(R(1),div(l0,a)));
end
c=struct('alpha',{al},'beta',{be},'a',a,'l0',l0,'l1',l1, ...
    'branch_energy',mul(C,sub(sub(F,Ta),d)),'capacity',mul(C,sub(R(s.tank_max_C),Ta)));
end
