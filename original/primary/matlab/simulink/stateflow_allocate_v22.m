function y = stateflow_allocate_v22(mode,u,E,p)
%#codegen
% Called by the active Stateflow state's entry and during actions.
% States determine which TES/backup/unmet ports may operate.
dt=p(1); after=E*(1-p(7)*dt);
direct=0; charge=0; discharge=0; gas=0; unmet=0;
if mode>=1
    direct=min(u(1),u(2));
end
if mode==2
    charge=min([max(0,u(2)-direct),p(3),(p(2)-after)/dt/p(5)]);
end
if mode>=3
    discharge=min([max(0,u(1)-direct),p(4),after*p(6)/dt]);
end
if mode>=4
    gas=min(p(8),max(0,u(1)-direct-discharge));
end
if mode==5
    unmet=max(0,u(1)-direct-discharge-gas);
end
next=min(p(2),max(0,after+p(5)*charge*dt-discharge*dt/p(6)));
standing=E-after;
chargeLoss=(1-p(5))*charge*dt;
dischargeLoss=discharge*dt/p(6)-discharge*dt;
supplied=direct+discharge+gas;
residual=(u(4)+u(3)+gas)*dt+E-supplied*dt-next-standing-chargeLoss-dischargeLoss;
y=[mode;direct;charge;discharge;gas;unmet;after;next;standing;chargeLoss;dischargeLoss;supplied;residual];
end
