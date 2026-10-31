function mode = stateflow_choose_mode_v22(u,E,p)
%#codegen
% Highest service condition; BACKUP/UNMET can include HP and TES discharge.
% u = [demand, HP heat, electricity, source used, request, COP, available, unused]
% p = [dt_h, capacity, charge limit, discharge limit, etaC, etaD, loss/h, boiler]
after=E*(1-p(7)*p(1));
direct=min(u(1),u(2));
discharge=min([max(0,u(1)-direct),p(4),after*p(6)/p(1)]);
remaining=max(0,u(1)-direct-discharge);
if remaining>p(8)
    mode=5;
elseif remaining>0
    mode=4;
elseif discharge>0
    mode=3;
elseif u(2)>direct
    mode=2;
elseif direct>0
    mode=1;
else
    mode=0;
end
end
