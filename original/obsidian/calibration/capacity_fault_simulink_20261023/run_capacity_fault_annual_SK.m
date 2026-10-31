function summary=run_capacity_fault_annual_SK()
% New Simulink nameplate/N+1 dynamic capacity study, independent v1 SLX untouched.
here=fileparts(mfilename('fullpath'));root=fileparts(fileparts(here));
addpath(fullfile(root,'matlab'));addpath(here);
name='DC_Pool_Capacity_Fault_20261023_SK';
load_system(fullfile(here,[name '.slx']));
cfg=default_config();cfg.sim.start=datetime(2025,1,1);cfg.sim.hours=8760;cfg.sim.dt_h=1;cfg.dc.pue=1.36;
x=dchr.make_inputs(cfg);
w=readtable(fullfile(root,'calibration','standards_20261023','official_datasets','weather_2025_BRATISLAVA_NASA_POWER_hourly_UTC.csv'));
x.outdoor_temp_C=w.T2M_C;
qdem=dchr.heat_demand(x.outdoor_temp_C,cfg);
[~,highest]=max(movsum(qdem,[23 0]));faultStart=max(0,min(8736,highest-24));
dt=300;t=(0:dt:8760*3600-dt)'; idx=1+floor(t/3600); final=8760*3600;
utc=cfg.sim.start+seconds(t);utc.TimeZone='UTC';
local=utc;local.TimeZone='Europe/Bratislava';hh=hour(local)+minute(local)/60;
activity=0.5+0.5*double(hh>=8&hh<20);cover=double(hh<8|hh>=20);
put('cl_activity_series',activity,t,final);
put('cl_cover_series',cover,t,final);
put('cl_dh_series',qdem(idx),t,final);
source=x.it_power_MW(idx)*cfg.dc.recovery_fraction;
put('cl_source_series',source,t,final);
P=[997*500*4182,312.5,800,0.150,27.25,27.60,27.80,300,0.5,70,12,50,5,5,0.95,0.95,1e-4,2.2,7];
assignin('base','cl_params',P);
assignin('base','cl_cop_pool',4);assignin('base','cl_source_temp',35);
names={'ref12','noPool10','direct10','direct_fail8_24h','direct_N1_30m','carrier9p42','carrier10p99'};
rated=[12,10,10,10,10,9.42,10.99];mode=[0 0 1 1 1 1 1];
summary=struct([]);
for k=1:numel(names)
 cap=ones(numel(t),1)*rated(k);
 if k==4,cap(t>=faultStart*3600 & t<(faultStart+24)*3600)=8;end
 if k==5,cap(t>=faultStart*3600 & t<faultStart*3600+1800)=8;end
 put('cl_hp_capacity_series',cap,t,final);
 assignin('base','cl_mode',mode(k));
 out=sim(name,'StopTime',num2str(final-dt));
 fields={'Tnext','Enext','Qpool','QsrcPool','Wpool','Qdh','QsrcDh','Wdh','Qgas','Qcharge','Qdischarge','Qloss'};
 data=struct;
 for j=1:numel(fields)
   sig=out.get(['cl_' fields{j}]);data.(fields{j})=sig.Data(:);
 end
 N=numel(t);assert(numel(data.Qdh)==N);
 assert(all(data.Qdh<=cap+1e-7),'NAMEPLATE_BREACH');
 assert(max(data.QsrcDh+data.QsrcPool-source)<1e-8,'DOUBLE_USE');
 assert(max(abs(data.Qpool-data.QsrcPool-data.Wpool))<1e-8);
 assert(max(abs(data.Qdh-data.QsrcDh-data.Wdh))<1e-8);
 assert(max(abs(data.Qdh-data.Qcharge+data.Qdischarge+data.Qgas-qdem(idx)))<1e-8);
 assert(max(data.Tnext)<=27.800001);
 assert(min(data.Enext)>=-1e-7 && max(data.Enext)<=50.001);
 res=P(1)*(data.Tnext(end)-16)/3.6e9-sum(data.Qpool-data.Qloss)/12;
 assert(abs(res)<1e-5);
 if k==1
   old=jsondecode(fileread(fullfile(root,'calibration','closed_loop_simulink_20261023','simulink_closed_loop_summary_8760h.json')));
   assert(abs(sum(data.Qgas)/12-old(1).gas_heat_MWh)<1e-6,'V1_REPRODUCE');
 end
 m=struct('name',names{k},'cap_MW',rated(k),...
  'hours',8760,'steps',N,'gas_MWh',sum(data.Qgas)/12,...
  'HPheat_MWh',sum(data.Qdh)/12,'HPel_MWh',sum(data.Wdh)/12,...
  'poolHeat_MWh',sum(data.Qpool)/12,'Tmax_C',max(data.Tnext),...
  'sourceToDH_MWh',sum(data.QsrcDh)/12,'sourceToPool_MWh',sum(data.QsrcPool)/12,...
  'storageEnd_MWh',data.Enext(end),'energyResidual_MWh',res,...
  'capacityLimitedHours',sum(data.Qdh>=cap-1e-9)/12,...
  'faultStartUTC_h',faultStart);
 if isempty(summary),summary=m;else,summary(end+1)=m;end
 fprintf('CAPACITY_TEST_PASS %s gas=%.3fMWh pool=%.3fMWh peakT=%.3fC\n',...
     names{k},m.gas_MWh,m.poolHeat_MWh,m.Tmax_C);
end
S=table(string({summary.name})',[summary.cap_MW]',[summary.gas_MWh]',...
 [summary.HPheat_MWh]',[summary.HPel_MWh]',[summary.poolHeat_MWh]',...
 [summary.capacityLimitedHours]',...
 'VariableNames',{'Case','Cap_MW','Gas_MWh','HPHeat_MWh','HPEl_MWh','PoolHeat_MWh','CapLimitHours'});
writetable(S,fullfile(here,'capacity_fault_simulink_2025.csv'));
fid=fopen(fullfile(here,'capacity_fault_simulink_2025.json'),'w','n','UTF-8');assert(fid>0);
fprintf(fid,'%s',jsonencode(summary,PrettyPrint=true));fclose(fid);
close_system(name,0);
fprintf('CAPACITY_FAULT_ANNUAL_VERIFIED %d cases, %d steps, faultStart=%d hours\n',numel(summary),N,faultStart);
end
function put(n,v,t,last)
 assignin('base',n,setinterpmethod(timeseries([v;v(end)],[t;last]),'zoh'));
end
