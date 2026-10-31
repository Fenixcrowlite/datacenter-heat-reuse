function rows=run_closed_loop_cases_SK(hoursRun)
% Run coupled saved Simulink model with true T/TES/controller discrete feedback.
if nargin<1,hoursRun=168;end
assert(hoursRun>=72 && hoursRun<=8760 && floor(hoursRun)==hoursRun);
here=fileparts(mfilename('fullpath'));
root=fileparts(fileparts(here));
addpath(fullfile(root,'matlab'));
model='DC_Pool_Coupled_ClosedLoop_20261023_SK';
load_system(fullfile(here,[model '.slx']));
% Simulink From Workspace requires enabling extrapolation even for ZOH timeseries.
for blockName={'SrcAvail','Dhdemand','Activity','Cover'}
 set_param([model '/' blockName{1}],'Interpolate','on');
end
cfg=default_config();
cfg.sim.start=datetime(2025,1,1,0,0,0);
cfg.sim.hours=hoursRun;
cfg.sim.dt_h=1;
cfg.dc.pue=1.36;
input=dchr.make_inputs(cfg);
w=readtable(fullfile(root,'calibration','standards_20261023','official_datasets','weather_2025_BRATISLAVA_NASA_POWER_hourly_UTC.csv'));
input.outdoor_temp_C=w.T2M_C(1:hoursRun);
demand=dchr.heat_demand(input.outdoor_temp_C,cfg);
dt=300;
ts=(0:dt:(hoursRun*3600-dt))';
idx=min(hoursRun,1+floor(ts/3600));
dateUTC=cfg.sim.start+seconds(ts);
dateUTC.TimeZone='UTC';dateLocal=dateUTC;dateLocal.TimeZone='Europe/Bratislava';
hourLocal=hour(dateLocal)+minute(dateLocal)/60;
activity=0.5+0.5*double(hourLocal>=8 & hourLocal<20);
cover=double(hourLocal<8 | hourLocal>=20);
params=[997*500*4182,312.5,800,0.150,27.25,27.60,27.80,300,...
        0.50,70,12,50,5,5,0.95,0.95,1e-4,2.2,7];
assignin('base','cl_params',params);
assignin('base','cl_cop_pool',4);
assignin('base','cl_activity_series',setinterpmethod(timeseries([activity;activity(end)],[ts;hoursRun*3600]),'zoh'));
assignin('base','cl_cover_series',setinterpmethod(timeseries([cover;cover(end)],[ts;hoursRun*3600]),'zoh'));
assignin('base','cl_dh_series',setinterpmethod(timeseries([demand(idx);demand(idx(end))],[ts;hoursRun*3600]),'zoh'));
names={'no_pool_35','direct_35','heatpump_25','outage_35'};
modes=[0,1,2,1];sources=[35,35,25,35];
summary=struct([]);rows=[];
for k=1:numel(names)
 src=input.it_power_MW(idx)*cfg.dc.recovery_fraction;
 if k==4
   src(ts>=48*3600 & ts<72*3600)=0;
 end
 assignin('base','cl_source_series',setinterpmethod(timeseries([src;src(end)],[ts;hoursRun*3600]),'zoh'));
 assignin('base','cl_mode',modes(k));
 assignin('base','cl_source_temp',sources(k));
 out=sim(model,'StopTime',num2str(hoursRun*3600-dt));
 data=struct();
 signals={'Tnext','Enext','Hnext','Qpool','QsrcPool','Wpool','Qdh',...
   'QsrcDh','Wdh','Qgas','Qcharge','Qdischarge','Qloss','COPdh'};
 for j=1:numel(signals)
  v=out.get(['cl_' signals{j}]);
  data.(signals{j})=v.Data(:);
 end
 N=numel(ts);
 assert(numel(data.Tnext)==N,'Wrong number of simulation steps');
 assert(all(isfinite(data.Tnext)));
 assert(max(data.Tnext)<=27.800001);
 assert(max(abs(data.Qpool-data.QsrcPool-data.Wpool))<1e-8);
 assert(max(abs(data.Qdh-data.QsrcDh-data.Wdh))<1e-8);
 assert(max(data.QsrcDh+data.QsrcPool-src)<1e-8);
 assert(max(abs(data.Qdh-data.Qcharge+data.Qdischarge+data.Qgas-demand(idx)))<1e-8);
 energyResidual=params(1)*(data.Tnext(end)-16)/3.6e9-sum(data.Qpool-data.Qloss)*dt/3600;
 assert(abs(energyResidual)<1e-5);
 if modes(k)==0,assert(max(data.Qpool)<1e-9 && abs(data.Tnext(end)-16)<1e-7);end
 if modes(k)==1,assert(max(data.Wpool)<1e-12);end
 if modes(k)==2,assert(sum(data.Wpool)>0);end
 if k==4, assert(max(abs(data.Qpool(ts>=48*3600 & ts<72*3600)))<1e-12);end
 mat=table(ts/3600,data.Tnext,data.Qpool,data.QsrcPool,data.Wpool,...
     data.Qdh,data.QsrcDh,data.Wdh,data.Qgas,data.Qcharge,data.Qdischarge,...
     data.Enext,data.Qloss,src,...
     'VariableNames',{'time_h','PoolT_C','PoolHeat_MW','DCtoPool_MW',...
     'PoolHPElectric_MW','DistrictHPHeat_MW','DCtoDistrict_MW',...
     'DistrictHPel_MW','GasHeat_MW','TESCharge_MW','TESDischarge_MW',...
     'TES_E_MWh','PoolNetLoss_MW','DCAvailable_MW'});
 writetable(mat,fullfile(here,[names{k} '_' num2str(hoursRun) 'h.csv']));
 m=struct('name',names{k},'hours',hoursRun,'source_C',sources(k),...
    'max_pool_C',max(data.Tnext),'end_pool_C',data.Tnext(end),...
    'pool_heat_MWh',sum(data.Qpool)*dt/3600,...
    'pool_source_MWh',sum(data.QsrcPool)*dt/3600,...
    'pool_HP_electric_MWh',sum(data.Wpool)*dt/3600,...
    'DH_HP_heat_MWh',sum(data.Qdh)*dt/3600,...
    'DH_source_MWh',sum(data.QsrcDh)*dt/3600,...
    'gas_heat_MWh',sum(data.Qgas)*dt/3600,...
    'pool_energy_residual_MWh',energyResidual,...
    'max_source_overlap_MW',max(data.QsrcDh+data.QsrcPool-src),...
    'max_district_balance_MW',...
     max(abs(data.Qdh-data.Qcharge+data.Qdischarge+data.Qgas-demand(idx))));
 if isempty(summary),summary=m;else,summary(end+1)=m;end
 fprintf('SIMULINK_CLOSED_LOOP_CASE_OK %s steps=%d pool=%.4f MWh maxT=%.3f C gas=%.2f MWh\n',...
  names{k},N,m.pool_heat_MWh,m.max_pool_C,m.gas_heat_MWh);
end
target=fullfile(here,['simulink_closed_loop_summary_' num2str(hoursRun) 'h.json']);
fid=fopen(target,'w','n','UTF-8');assert(fid>0);
fprintf(fid,'%s',jsonencode(summary,PrettyPrint=true));fclose(fid);
rows=summary;
close_system(model,0);
fprintf('SIMULINK_CLOSED_LOOP_QA_PASS HOURS=%d\n',hoursRun);
end
