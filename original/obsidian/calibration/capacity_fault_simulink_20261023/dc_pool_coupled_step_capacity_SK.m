function [Tnext,Enext,Hnext,Qpool,QsrcPool,Wpool,Qdh,QsrcDh,Wdh,Qgas,Qcharge,Qdischarge,Qloss,COPdh] = ...
 dc_pool_coupled_step_capacity_SK(SrcAvail,Dhdemand,Activity,Cover,Tprev,Eprev,Hprev,Mode,SourceTemp,COPpool,P,HPmaxAvailable)
%#codegen
% Capacity + failover study. OWN copy, previous Simulink source unmodified.
% All thermal powers are MW. HPmaxAvailable [MW useful] 0..12.
Cp=P(1); A=P(2); UA=P(3); MaxPoolW=P(4)*1e6;
Ton=P(5); Toff=P(6); Tmax=P(7); dt=P(8);
etaC=P(9); Tdh=P(10); MaxDH=P(11);
TEScap=P(12); QchargeMax=P(13); QdischargeMax=P(14);
etaCharge=P(15); etaDischarge=P(16); leakPerHour=P(17);
COPmin=P(18); COPmax=P(19);
QlossW=0;QpoolW=0;QsourcePoolW=0;WpoolW=0;Hnext=Hprev;
if Mode>0.5
  pv=0.61094*exp(17.625*Tprev/(Tprev+243.04));
  pa=0.6*0.61094*exp(17.625*29/(29+243.04));
  mEvap=max(0,4e-5*A*(pv-pa)*Activity*(1-0.90*Cover));
  qEvap=mEvap*2440000;
  qConv=3*A*(Tprev-29)*(1-0.75*Cover);
  qRad=0.95*5.670374419e-8*A*((Tprev+273.15)^4-(27+273.15)^4)*(1-0.75*Cover);
  qGround=UA*(Tprev-20);
  qMakeup=mEvap*4182*(Tprev-15);
  QlossW=qEvap+qConv+qRad+qGround+qMakeup+2000;
  if Tprev<=Ton,Hnext=1;end
  if Tprev>=Toff,Hnext=0;end
  heatAllowed=(Mode>1.5 || SourceTemp>=Tprev+3);
  if Hnext>0.5 && heatAllowed
    qSafe=max(0,(Tmax-Tprev)*Cp/dt+QlossW);
    QpoolW=min(MaxPoolW,qSafe);
    if Mode>1.5
      qPoolCap=max(0,SrcAvail*1e6)*COPpool/(COPpool-1);
      QpoolW=min(QpoolW,qPoolCap);
      WpoolW=QpoolW/COPpool;
      QsourcePoolW=QpoolW-WpoolW;
    else
      QpoolW=min(QpoolW,max(0,SrcAvail*1e6));
      QsourcePoolW=QpoolW;
    end
  end
end
Tnext=Tprev+(QpoolW-QlossW)*dt/Cp;
Qpool=QpoolW/1e6;QsrcPool=QsourcePoolW/1e6;
Wpool=WpoolW/1e6;Qloss=QlossW/1e6;
remainder=max(0,SrcAvail-QsrcPool);
TdhK=Tdh+273.15;TsourceK=SourceTemp+273.15;
lift=max(1,TdhK-TsourceK);
COPdh=min(COPmax,max(COPmin,etaC*TdhK/lift));
% Live nameplate cap/failure enters on same sample and physically reallocates
% missing heat to TES/gas. Not a substitute for independent IT cooling.
possible=min(min(MaxDH,max(0,HPmaxAvailable)),remainder*COPdh/(COPdh-1));
Eavailable=Eprev*max(0,1-leakPerHour*dt/3600);
Qdh=0;Qgas=0;Qcharge=0;Qdischarge=0;
if possible>=Dhdemand
    Qdh=Dhdemand;
    if TEScap>0
        room=max(0,TEScap-Eavailable);
        Qcharge=min(min(possible-Dhdemand,QchargeMax),room/(etaCharge*dt/3600));
    end
    Qdh=Qdh+Qcharge;
    Enext=Eavailable+etaCharge*Qcharge*dt/3600;
else
    Qdh=possible;
    deficit=max(0,Dhdemand-possible);
    if TEScap>0
        Qdischarge=min(min(deficit,QdischargeMax),Eavailable*etaDischarge/(dt/3600));
    end
    Enext=max(0,Eavailable-Qdischarge*dt/3600/etaDischarge);
    Qgas=max(0,deficit-Qdischarge);
end
Wdh=Qdh/COPdh;
QsrcDh=Qdh-Wdh;
end
