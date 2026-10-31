function mode = stateflow_choose_mode_v24(hpPorts,energyStart,cfgPorts)
%#codegen
% Highest service condition; BACKUP/UNMET can include HP and TES discharge.
% hpPorts = [demand, HP heat, electricity, source used, request, COP, available, unused]
% cfgPorts = [dt_h, capacity, charge limit, discharge limit, etaC, etaD, loss/h, boiler]
after=energyStart*(1-cfgPorts(7)*cfgPorts(1));
direct=min(hpPorts(1),hpPorts(2));
discharge=min([max(0,hpPorts(1)-direct),cfgPorts(4),after*cfgPorts(6)/cfgPorts(1)]);
remaining=max(0,hpPorts(1)-direct-discharge);
if remaining>cfgPorts(8)
    mode=5;
elseif remaining>0
    mode=4;
elseif discharge>0
    mode=3;
elseif hpPorts(2)>direct
    mode=2;
elseif direct>0
    mode=1;
else
    mode=0;
end
end
