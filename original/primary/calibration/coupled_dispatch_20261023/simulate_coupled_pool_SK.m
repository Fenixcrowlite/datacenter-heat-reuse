function [out,metrics]=simulate_coupled_pool_SK(cfg,input,opt)
% Vyuzitie zdroja DC pre siet a bazen. Nezasahuje do originalu DCHR a bazena.
% Hourly district dispatch; 300s pool integration with priority source reservation.
% Every hour the network gets source after MAX instantaneous pool reservation:
% conservative, prevents simultaneous double-use of DC source in subhour steps.
% Pool room temperature/RH fixed model SCENARIO, not real natatorium BMS data.
arguments
 cfg (1,1) struct
 input (1,1) struct
 opt.poolEnabled (1,1) logical = true
 opt.poolMode (1,1) string {mustBeMember(opt.poolMode,["DIRECT","HP"])} = "DIRECT"
 opt.initialPool_C (1,1) double = 16
 opt.poolOn_C (1,1) double = 27.25
 opt.poolOff_C (1,1) double = 27.60
 opt.poolMax_C (1,1) double = 27.80
 opt.poolHeaterMax_MW (1,1) double = 0.150
 opt.poolLength_m (1,1) double = 25
 opt.poolWidth_m (1,1) double = 12.5
 opt.poolDepth_m (1,1) double = 1.6
 opt.poolCOP (1,1) double = 4
 opt.hxApproach_K (1,1) double = 3
 opt.source_C (1,1) double = 35
 opt.rh (1,1) double = 0.60
 opt.coverAtNight (1,1) logical = true
 opt.thermalStep_s (1,1) double = 300
end
N=numel(input.time);
assert(N>0 && cfg.sim.dt_h==1, "Model podpory bazena pocita s 1-hodinovym krokom DC.");
assert(3600/opt.thermalStep_s==round(3600/opt.thermalStep_s));
assert(opt.poolOn_C<opt.poolOff_C && opt.poolOff_C<opt.poolMax_C);
assert(opt.poolMax_C<=28.0,"Prevadzkovy maximalny limit musime drzat pod 28 C.");
assert(opt.poolCOP>1 && opt.poolHeaterMax_MW>0 && opt.rh>=0 && opt.rh<=1);
assert(opt.poolLength_m>0 && opt.poolWidth_m>0 && opt.poolDepth_m>0);
assert(all(input.it_power_MW>=0));
nsub=round(3600/opt.thermalStep_s);
dt=cfg.sim.dt_h;
Cp=997*(opt.poolLength_m*opt.poolWidth_m*opt.poolDepth_m)*4182; % J/K
A=opt.poolLength_m*opt.poolWidth_m;
Aenvelope=A+2*(opt.poolLength_m+opt.poolWidth_m)*opt.poolDepth_m;
UA=800*Aenvelope/(312.5+2*(25+12.5)*1.6); % SCENARIO scaling, not measured
sigma=5.670374419e-8; hfg=2440000;
temp=opt.initialPool_C; heaterOn=true;
Tpool=zeros(N,1); PoolLoss=zeros(N,1);PoolHeated=zeros(N,1);
PoolSource=zeros(N,1);PoolElectric=zeros(N,1); PoolReserved=zeros(N,1);
maxPoolT=opt.initialPool_C; lossEnergy_MWh=0;poolCover=zeros(N,1);
demand=dchr.heat_demand(input.outdoor_temp_C,cfg);
available=input.it_power_MW.*cfg.dc.recovery_fraction;
sourceDistrict=zeros(N,1); hpElectric=zeros(N,1);
qHeat=zeros(N,1);qGas=zeros(N,1);qCharge=zeros(N,1);qDischarge=zeros(N,1);qCurtail=zeros(N,1);
E=zeros(N+1,1); E(1)=cfg.storage.initial_soc*cfg.storage.capacity_MWh;
cop=zeros(N,1);
clockUTC=input.time;clockUTC.TimeZone='UTC';clockLocal=clockUTC;clockLocal.TimeZone='Europe/Bratislava';
for k=1:N
    qMaxThisHour=0;
    sourceSum_MWh=0; deliveredSum_MWh=0; electricSum_MWh=0;
    lossSum_MWh=0; coverCount=0;
    for j=1:nsub
        tlocal=clockLocal(k)+seconds((j-1)*opt.thermalStep_s);
        localHour=hour(tlocal)+minute(tlocal)/60;
        active=(localHour>=8 && localHour<20);
        cover=double(~active && opt.coverAtNight);
        activity=1.0; if ~active, activity=0.5;end
        % Reduced correlation from parallel pool scenario, pressure in kPa.
        pw=0.61094*exp(17.625*temp/(temp+243.04));
        pa=opt.rh*0.61094*exp(17.625*29/(29+243.04));
        mdot=max(0,4e-5*A*(pw-pa)*activity*(1-0.90*cover));
        qe=mdot*hfg;
        qc=3*A*(temp-29)*(1-0.75*cover);
        qr=0.95*sigma*A*((temp+273.15)^4-(27+273.15)^4)*(1-0.75*cover);
        qground=UA*(temp-20);
        qmakeup=mdot*4182*(temp-15);
        qloss=qe+qc+qr+qground+qmakeup+2000;
        lossSum_MWh=lossSum_MWh+qloss*opt.thermalStep_s/3.6e9;
        coverCount=coverCount+cover;
        poolInput_W=0; sourceUse_W=0; electric_W=0;
        if opt.poolEnabled
            if temp<=opt.poolOn_C,heaterOn=true;end
            if temp>=opt.poolOff_C,heaterOn=false;end
            canDirect=(opt.source_C >= temp+opt.hxApproach_K);
            canHeat=(opt.poolMode=="HP" || canDirect);
            if heaterOn && canHeat
                limitW=max(0,(opt.poolMax_C-temp)*Cp/opt.thermalStep_s+qloss);
                poolInput_W=min(opt.poolHeaterMax_MW*1e6,limitW);
                if opt.poolMode=="HP"
                    poolInput_W=min(poolInput_W,available(k)*1e6*opt.poolCOP/(opt.poolCOP-1));
                    electric_W=poolInput_W/opt.poolCOP;
                    sourceUse_W=poolInput_W-electric_W;
                else
                    poolInput_W=min(poolInput_W,available(k)*1e6);
                    sourceUse_W=poolInput_W;
                end
            end
        else
            % Off branch has no pool heat, loss accounting or temperature evolution.
            qloss=0;
            lossSum_MWh=lossSum_MWh - ...
                (qe+qc+qr+qground+qmakeup+2000)*opt.thermalStep_s/3.6e9;
        end
        temp=temp+(poolInput_W-qloss)*opt.thermalStep_s/Cp;
        maxPoolT=max(maxPoolT,temp);
        assert(temp<=opt.poolMax_C+1e-7 || ~opt.poolEnabled,"POOL_OVERTEMPERATURE");
        qMaxThisHour=max(qMaxThisHour,sourceUse_W/1e6);
        sourceSum_MWh=sourceSum_MWh+sourceUse_W*opt.thermalStep_s/3.6e9;
        deliveredSum_MWh=deliveredSum_MWh+poolInput_W*opt.thermalStep_s/3.6e9;
        electricSum_MWh=electricSum_MWh+electric_W*opt.thermalStep_s/3.6e9;
    end
    PoolReserved(k)=qMaxThisHour;
    PoolSource(k)=sourceSum_MWh/dt;
    PoolHeated(k)=deliveredSum_MWh/dt;
    PoolElectric(k)=electricSum_MWh/dt;
    PoolLoss(k)=lossSum_MWh/dt;
    Tpool(k)=temp;
    poolCover(k)=coverCount/nsub;
    srcLeft=max(0,available(k)-PoolReserved(k));
    hp=dchr.heat_pump_capability(srcLeft,opt.source_C,cfg);
    cop(k)=hp.cop;
    qPossible=hp.max_heat_output_MW;
    eAvail=E(k)*(1-cfg.storage.loss_fraction_per_h*dt);
    qNeed=demand(k);
    if qPossible>=qNeed
        qDirect=qNeed;
        surplus=qPossible-qNeed;
        if cfg.storage.capacity_MWh>0
            room=max(0,cfg.storage.capacity_MWh-eAvail);
            qCharge(k)=min([surplus,cfg.storage.charge_limit_MW,room/(cfg.storage.eta_charge*dt)]);
        end
        qHeat(k)=qDirect+qCharge(k);
        qCurtail(k)=max(0,qPossible-qHeat(k));
        E(k+1)=eAvail+cfg.storage.eta_charge*qCharge(k)*dt;
    else
        qHeat(k)=qPossible;
        deficit=qNeed-qPossible;
        if cfg.storage.capacity_MWh>0
            qDischarge(k)=min([deficit,cfg.storage.discharge_limit_MW,eAvail*cfg.storage.eta_discharge/dt]);
        end
        E(k+1)=max(0,eAvail-qDischarge(k)*dt/cfg.storage.eta_discharge);
        qGas(k)=max(0,deficit-qDischarge(k));
    end
    hpElectric(k)=qHeat(k)/cop(k);
    sourceDistrict(k)=qHeat(k)-hpElectric(k);
    assert(sourceDistrict(k)+PoolReserved(k)<=available(k)+1e-8,"DOUBLE_COUNT_DC_SOURCE");
    assert(abs(PoolHeated(k)-PoolSource(k)-PoolElectric(k))<1e-8,"POOL_SOURCE_HP_BALANCE");
    assert(abs(qHeat(k)+qDischarge(k)+qGas(k)-qCharge(k)-qNeed)<1e-8,"DISTRICT_HEAT_BALANCE");
end
out=table(input.time,input.outdoor_temp_C,input.it_power_MW,available,demand,...
    Tpool,PoolLoss,PoolHeated,PoolSource,PoolElectric,PoolReserved,poolCover,...
    sourceDistrict,qHeat,hpElectric,qCharge,qDischarge,qGas,qCurtail,E(1:end-1),cop,...
    'VariableNames',{'Time','Tout_C','IT_MW','DC_Source_Available_MW','DH_Demand_MW',...
    'Pool_T_C','Pool_Loss_MW','Pool_Q_MW','Pool_Source_MW','Pool_El_MW',...
    'Pool_Source_Reserved_MW','Pool_Cover','DH_Source_MW','DH_HP_Q_MW','DH_HP_El_MW',...
    'TES_Charge_MW','TES_Discharge_MW','Gas_Q_MW','HP_Curtailed_MW','TES_E_MWh','DH_COP'});
metrics=struct();
metrics.pool_volume_m3=opt.poolLength_m*opt.poolWidth_m*opt.poolDepth_m;
metrics.pool_area_m2=A;
metrics.pool_UA_scenario_W_K=UA;
metrics.pool_heat_MWh=sum(PoolHeated)*dt;
metrics.pool_source_MWh=sum(PoolSource)*dt;
metrics.pool_electric_MWh=sum(PoolElectric)*dt;
metrics.pool_loss_MWh=sum(PoolLoss)*dt;
metrics.pool_end_C=temp;
metrics.pool_max_C=maxPoolT;
metrics.pool_min_C=min([opt.initialPool_C;Tpool]);
metrics.pool_energy_residual_MWh=Cp*(temp-opt.initialPool_C)/3.6e9-...
    (metrics.pool_heat_MWh-metrics.pool_loss_MWh);
metrics.dc_total_MWh=sum(input.dc_total_power_MW)*dt;
metrics.dc_source_available_MWh=sum(available)*dt;
metrics.dh_demand_MWh=sum(demand)*dt;
metrics.dh_heat_non_gas_MWh=sum(qHeat-qCharge+qDischarge)*dt;
metrics.dh_hp_electric_MWh=sum(hpElectric)*dt;
metrics.dh_source_used_MWh=sum(sourceDistrict)*dt;
metrics.gas_heat_MWh=sum(qGas)*dt;
metrics.total_source_used_MWh=metrics.pool_source_MWh+metrics.dh_source_used_MWh;
metrics.total_heat_consumed_MWh=metrics.pool_heat_MWh+metrics.dh_heat_non_gas_MWh;
metrics.source_utilization=metrics.total_source_used_MWh/metrics.dc_source_available_MWh;
metrics.ERF_source_proxy=metrics.total_source_used_MWh/metrics.dc_total_MWh;
metrics.pool_max_temp_screening_pass=(maxPoolT<=opt.poolMax_C+1e-6);
metrics.allocation_method='conservative MAX sub-hourly pool source reservation for hourly DH dispatch';
metrics.official_E_REUSE_measured=false;
assert(abs(metrics.pool_energy_residual_MWh)<1e-4,"POOL_ANNUAL_ENERGY_BALANCE");
assert(metrics.total_source_used_MWh<=metrics.dc_source_available_MWh+1e-5);
assert(abs(metrics.dh_demand_MWh-metrics.dh_heat_non_gas_MWh-metrics.gas_heat_MWh)<1e-4);
end
