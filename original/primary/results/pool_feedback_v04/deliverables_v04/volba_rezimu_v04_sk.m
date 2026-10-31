function m=volba_rezimu_v04_sk(req,inputs,waterTemperature,storedEnergy)
% Opravena lokálna symbolika funkcie Stateflow, bez tienovania chart dat.
m=0;
if inputs(8)<0.5
    m=4; % IT zastavene
elseif inputs(1)<=1e-6
    if storedEnergy>100000 && inputs(10)>0.5 && inputs(3)>0
        m=3; % TES-only
    end
elseif inputs(11)>0.5 && inputs(9)>0.5 && req>0 && inputs(2)>waterTemperature+5
    m=1; % priamy HX bazena, TC sluzba siete
else
    m=2; % TC
end
end
