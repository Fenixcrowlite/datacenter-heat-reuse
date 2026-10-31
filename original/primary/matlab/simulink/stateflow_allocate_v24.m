function y = stateflow_allocate_v24(mode,hpPorts,energyStart,cfgPorts)
%#codegen
% Called by the active Stateflow state's entry and during actions.
% States determine which TES/backup/unmet ports may operate.
dt=cfgPorts(1); after=energyStart*(1-cfgPorts(7)*dt);
direct=0; charge=0; discharge=0; gas=0; unmet=0;
if mode>=1
    direct=min(hpPorts(1),hpPorts(2));
end
if mode==2
    charge=min([max(0,hpPorts(2)-direct),cfgPorts(3),(cfgPorts(2)-after)/dt/cfgPorts(5)]);
end
if mode>=3
    discharge=min([max(0,hpPorts(1)-direct),cfgPorts(4),after*cfgPorts(6)/dt]);
end
if mode>=4
    gas=min(cfgPorts(8),max(0,hpPorts(1)-direct-discharge));
end
if mode==5
    unmet=max(0,hpPorts(1)-direct-discharge-gas);
end
next=min(cfgPorts(2),max(0,after+cfgPorts(5)*charge*dt-discharge*dt/cfgPorts(6)));
standing=energyStart-after;
chargeLoss=(1-cfgPorts(5))*charge*dt;
dischargeLoss=discharge*dt/cfgPorts(6)-discharge*dt;
supplied=direct+discharge+gas;
residual=(hpPorts(4)+hpPorts(3)+gas)*dt+energyStart-supplied*dt-next-standing-chargeLoss-dischargeLoss;
y=[mode;direct;charge;discharge;gas;unmet;after;next;standing;chargeLoss;dischargeLoss;supplied;residual];
end
