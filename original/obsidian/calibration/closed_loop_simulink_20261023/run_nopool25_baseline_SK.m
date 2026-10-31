% Individualny baseline HP25 bez bazena: PRESNE rovnaky 300s solver.
here=fileparts(mfilename('fullpath'));root=fileparts(fileparts(here));addpath(fullfile(root,'matlab'));
name='DC_Pool_Coupled_ClosedLoop_20261023_SK';
load_system(fullfile(here,[name '.slx']));
cfg=default_config();cfg.sim.start=datetime(2025,1,1);cfg.sim.hours=8760;cfg.sim.dt_h=1;cfg.dc.pue=1.36;
x=dchr.make_inputs(cfg);
w=readtable(fullfile(root,'calibration','standards_20261023','official_datasets',...
  'weather_2025_BRATISLAVA_NASA_POWER_hourly_UTC.csv'));
x.outdoor_temp_C=w.T2M_C;
dh=dchr.heat_demand(x.outdoor_temp_C,cfg);
time=(0:300:8760*3600-300)';idx=min(8760,floor(time/3600)+1);
inTime=[time;8760*3600];
dateUTC=cfg.sim.start+seconds(time);dateUTC.TimeZone='UTC';
local=dateUTC;local.TimeZone='Europe/Bratislava';
hourL=hour(local)+minute(local)/60;
cover=double(hourL<8|hourL>=20);
activity=0.5+0.5*double(hourL>=8&hourL<20);
a=[x.it_power_MW(idx)*cfg.dc.recovery_fraction];p=dh(idx);
feed={'cl_source_series',a;'cl_dh_series',p;...
      'cl_activity_series',activity;'cl_cover_series',cover};
for j=1:size(feed,1)
 v=feed{j,2};assignin('base',feed{j,1},setinterpmethod(timeseries([v;v(end)],inTime),'zoh'));
end
assignin('base','cl_mode',0);assignin('base','cl_source_temp',25);assignin('base','cl_cop_pool',4);
assignin('base','cl_params',[997*500*4182,312.5,800,0.150,27.25,27.60,27.8,300,0.5,70,12,50,5,5,0.95,0.95,1e-4,2.2,7]);
out=sim(name,'StopTime',num2str(8760*3600-300));
signals={'Qpool','QsrcPool','Wpool','Qdh','QsrcDh','Wdh','Qgas'};
Z=struct;
for j=1:numel(signals)
 t=out.get(['cl_' signals{j}]);Z.(signals{j})=t.Data(:);
end
assert(max(abs(Z.Qpool))<1e-10);
assert(max(Z.QsrcDh-a)<1e-7);
assert(max(abs(Z.Qdh-Z.QsrcDh-Z.Wdh))<1e-8);
result=struct('scenario','no_pool_25','hours',8760,...
 'DH_HP_heat_MWh',sum(Z.Qdh)/12,'DH_source_MWh',sum(Z.QsrcDh)/12,...
 'DH_HP_el_MWh',sum(Z.Wdh)/12,'gas_heat_MWh',sum(Z.Qgas)/12,...
 'max_source_over_MW',max(Z.QsrcDh-a));
fid=fopen(fullfile(here,'simulink_nopool25_baseline_8760h.json'),'w','n','UTF-8');assert(fid>0);
fprintf(fid,'%s',jsonencode(result,PrettyPrint=true));fclose(fid);
fprintf('SIMULINK_NOPPOOL25_VERIFIED gas_MWh=%.5f DH_HP_EL_MWh=%.5f\n',result.gas_heat_MWh,result.DH_HP_el_MWh);
close_system(name,0);
