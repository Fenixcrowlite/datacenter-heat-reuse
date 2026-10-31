function [nextState, out] = dchr_a38_step(raw, d, state, capW, policy, active)
%DCHR_A38_STEP Synthetic reference only. No equipment or Stateflow control.
% Mirrors independently QA'd Python A38; must be executed in MATLAB before acceptance.
% raw: v08 row struct; d: A36 both_off row struct.
% state: struct(E_J,T_C,shed_W), capW hypothetical REJECT capacity [W].
dt=900; Emax=900*3.6e6; etaC=.93; etaD=.91;
qdc=double(raw.Q_DC_eff_W);
qHx=double(d.Q_HX_W);
qLeak=double(raw.Q_leak_W);
qCharge=double(d.Q_HP_charge_W);
qDischarge=double(d.Q_TES_discharge_W);
if any(~isfinite([qdc,qHx,qLeak,qCharge,qDischarge,capW,state.E_J,state.T_C,state.shed_W]))
    error('A38:Nonfinite','Nonfinite input');
end
if any([qdc,qHx,qLeak,qCharge,qDischarge,capW] < -1e-8)
    error('A38:Negative','Negative physical input');
end
if qCharge>1e-7 && qDischarge>1e-7
    error('A38:TESMode','Simultaneous charge and discharge');
end
E=state.E_J;
loss=.002*E/86400;
available=max(0,(E-loss*dt)*etaD/dt);
if qDischarge>available+1e-5
    error('A38:TESUnderflow','Insufficient TES energy');
end
room=max(0,(Emax-E+dt*(qDischarge/etaD+loss))/(etaC*dt));
charge=min(qCharge,room);
Enew=E+dt*(etaC*charge-qDischarge/etaD-loss);
if Enew < -1e-4 || Enew > Emax+1e-4
    error('A38:TESOverflow','TES outside capacity');
end
Enew=max(0,min(Emax,Enew));
oldCondenser=double(d.Q_HP_pool_W)+double(d.Q_HP_DH_W)+qCharge;
newCondenser=oldCondenser-(qCharge-charge);
oldPower=double(d.P_HP_proxy_W);
if oldCondenser>1e-8
    newPower=oldPower*newCondenser/oldCondenser;
else
    newPower=0;
end
sourceNew=newCondenser-newPower;
rawRequired=double(d.Q_reject_required_W)+double(d.Q_HP_source_W)-sourceNew;
if rawRequired < -1e-7 || ~isfinite(rawRequired)
    error('A38:RejectNegative','Invalid REJECT demand');
end
required=max(0,rawRequired);
if ~active
    capW=330000;
    policy='no_shed';
end
previous=min(state.shed_W,qdc);
if strcmp(policy,'no_shed')
    shed=0;
elseif strcmp(policy,'ideal_40pct') || strcmp(policy,'ramp15k_40pct')
    target=min([max(0,required-capW),.4*qdc,required]);
    if strcmp(policy,'ramp15k_40pct')
        shed=min(target,previous+15000);
    else
        shed=target;
    end
else
    error('A38:UnknownPolicy','Unknown shedding policy');
end
reject=min(required-shed,capW);
unhandled=max(0,required-shed-reject);
passive=max(0,2000*(state.T_C-30));
Tnew=max(30,state.T_C+dt*(unhandled-passive)/8e6);
residual=qdc-shed-qHx-sourceNew-qLeak-reject-unhandled;
if abs(residual)>1e-5
    error('A38:DCBalance','DC first law mismatch');
end
nextState=struct('E_J',Enew,'T_C',Tnew,'shed_W',shed);
out=struct('Q_reject_actual_W',reject,'Q_unhandled_W',unhandled, ...
    'Q_IT_shed_W',shed,'T_IT_next_C',Tnew,'E_TES_next_J',Enew, ...
    'TES_SOC_next',Enew/Emax,'Q_TES_charge_actual_W',charge, ...
    'P_HP_proxy_W',newPower,'Q_HP_source_W',sourceNew, ...
    'DC_residual_W',residual,'alarm_next',double(Tnew>=42));
end
