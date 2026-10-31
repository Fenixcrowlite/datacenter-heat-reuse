function [Tnext,Qrejected_MW,Residual_MW,Trip,FlowTrip] = ...
 it_independent_cooling_step_SK(IT_MW,Reuse_MW,CoolerCap_MW,PumpOK,Tprev,P)
%#codegen
% IT safety thermal buffer, independent rejection capacity. Screening, not PLC.
% P = [rhoVcp_JK, dt_s, normal_T_C, max_T_C]
C=P(1);dt=P(2);Tnom=P(3);Tmax=P(4);
qIT=max(0,IT_MW);
use=max(0,min(qIT,Reuse_MW));
qtoReject=qIT-use;
FlowTrip=double(PumpOK<0.5);
if PumpOK>=0.5
  available=max(0,CoolerCap_MW);
  buffered=max(0,Tprev-Tnom)*C/(dt*1e6);
  Qrejected_MW=min(available,qtoReject+buffered);
else
  % Flow fault -> heat recovery and rejection cannot protect chips.
  Qrejected_MW=0;
  qtoReject=qIT;
end
Residual_MW=qtoReject-Qrejected_MW;
Tnext=Tprev+Residual_MW*1e6*dt/C;
Trip=double(Tnext>Tmax || FlowTrip>0.5);
end
