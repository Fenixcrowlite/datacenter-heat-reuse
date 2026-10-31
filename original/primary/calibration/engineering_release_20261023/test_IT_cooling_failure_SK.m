function R=test_IT_cooling_failure_SK()
% Independent 5-second Simulink faults: no heat-reuse sink is required.
here=fileparts(mfilename('fullpath'));addpath(here);
name='IT_Independent_HeatRejection_20261023_SK';load_system(fullfile(here,[name '.slx']));
for b={'IT_MW','HeatReuse_MW','CoolerAvailable_MW','PumpOK'}
 set_param([name '/' b{1}],'Interpolate','on');
end
t=(0:5:3600)';N=numel(t);
setSeries('safe_IT',10*ones(N,1),t);
setSeries('safe_reuse',zeros(N,1),t); % pool and district heat sinks both lost.
assignin('base','safe_params',[997*10*4182,5,35,40]);
names={'N6_nominal_fail30s','N7_der10_fail30s','N7_der10_fail300s',...
 'N6_der10_nominal_undersized','N7_der20_nominal_undersized','N7_der10_pump_fault'};
units=[6,7,7,6,7,7];derate=[0,.1,.1,.1,.2,.1];
dur=[30,30,300,30,30,30];
expectSafe=[true,true,false,false,false,false];
R=struct([]);
for k=1:numel(names)
 eff=2*(1-derate(k));
 cap=ones(N,1)*(units(k)-1)*eff;
 cap(t>=600&t<600+dur(k))=(units(k)-2)*eff;
 pumps=ones(N,1);
 if k==6,pumps(t>=600&t<610)=0;end
 setSeries('safe_capacity',cap,t);setSeries('safe_pump',pumps,t);
 o=sim(name,'StopTime','3600');
 vT=o.get('saf_Tnext');vTrip=o.get('saf_Trip');
 vReject=o.get('saf_Qrejected_MW');vFlow=o.get('saf_FlowTrip');
 T=vT.Data(:);tr=vTrip.Data(:);
 q=vReject.Data(:);flow=vFlow.Data(:);
 assert(numel(T)==N);
 assert(all(q>=-1e-8)&&all(q<=cap+1e-8));
 assert(all(isfinite(T)));
 safe=~any(tr>0.5);
 assert(safe==expectSafe(k),['Safety stress expected fail for ' names{k}]);
 if k==6,assert(any(flow>0.5));else,assert(~any(flow>0.5));end
 m=struct('caseName',names{k},'installedModules',units(k),...
    'derateFraction',derate(k),'faultDuration_s',dur(k),...
    'bufferVolume_m3',10,'coolantStart_C',35,'tripThreshold_C',40,...
    'maxTemperature_C',max(T),'safeSimulation',safe,...
    'tripSteps',sum(tr>0.5),'flowTripSteps',sum(flow>0.5),...
    'heatReused_MWh',0);
 if isempty(R),R=m;else,R(end+1)=m;end
 fprintf('IT_COOLING_STRESS_PASS %s SAFE=%d Tmax=%.3f C trips=%d\n',...
  names{k},safe,max(T),m.tripSteps);
 if k==2 || k==3
   mat=table(t,T,q,cap,tr,flow,'VariableNames',...
      {'time_s','coolant_T_C','Q_rejected_MW','cooler_cap_MW','Trip','FlowTrip'});
   writetable(mat,fullfile(here,[names{k} '.csv']));
 end
end
fid=fopen(fullfile(here,'IT_cooling_failsafe_simulink_results.json'),'w','n','UTF-8');assert(fid>0);
fprintf(fid,'%s',jsonencode(R,PrettyPrint=true));fclose(fid);
close_system(name,0);
fprintf('IT_COOLING_FAULT_SIMULINK_ALL_PASS %d cases 5s duration3600\n',numel(R));
end
function setSeries(n,v,t)
 assignin('base',n,setinterpmethod(timeseries(v,t),'zoh'));
end
