function mode = stateflow_choose_mode_v30(hpPorts,energyStart,cfgPorts)
%#codegen
% Highest service condition, using exact uniformly held TES ports.
direct=min(hpPorts(1),hpPorts(2));
st=storage_kernel_v30(energyStart,0,max(0,hpPorts(1)-direct),cfgPorts(1:10));
remaining=max(0,hpPorts(1)-direct-st(2));
if remaining>cfgPorts(11)
    mode=5;
elseif remaining>0
    mode=4;
elseif st(2)>0
    mode=3;
elseif hpPorts(2)>direct
    mode=2;
elseif direct>0
    mode=1;
else
    mode=0;
end
end
