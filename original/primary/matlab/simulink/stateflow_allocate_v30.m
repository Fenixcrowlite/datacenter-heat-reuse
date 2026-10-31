function y = stateflow_allocate_v30(mode,hpPorts,energyStart,cfgPorts)
%#codegen
% Active state authorizes charge, discharge, boiler and unmet ports.
dt=cfgPorts(1); direct=0; chargeRequest=0; dischargeRequest=0; gas=0; unmet=0;
if mode>=1, direct=min(hpPorts(1),hpPorts(2)); end
if mode==2, chargeRequest=max(0,hpPorts(2)-direct); end
if mode>=3, dischargeRequest=max(0,hpPorts(1)-direct); end
st=storage_kernel_v30(energyStart,chargeRequest,dischargeRequest,cfgPorts(1:10));
if mode>=4, gas=min(cfgPorts(11),max(0,hpPorts(1)-direct-st(2))); end
if mode==5, unmet=max(0,hpPorts(1)-direct-st(2)-gas); end
supplied=direct+st(2)+gas;
residual=(hpPorts(4)+hpPorts(3)+gas)*dt+energyStart-supplied*dt-st(4)-sum(st(5:7));
y=[mode;direct;st(1);st(2);gas;unmet;st(3);st(4);st(5);st(6);st(7);supplied;residual;st(8:11)];
end
