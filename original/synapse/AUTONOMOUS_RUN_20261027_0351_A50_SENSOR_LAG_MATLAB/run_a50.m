% A50 isolated synthetic fault injection: sensor latency in graphical Stateflow.
% Never write A48 source; no physical hardware or external interfaces.
here=fileparts(mfilename('fullpath'));
src=fullfile(fileparts(here),'AUTONOMOUS_RUN_20261027_0150_A48_EXECUTABLE_QA','DCHR_A48_Graphical_Closed_Loop.slx');
assert(license('test','Simulink') && license('test','Stateflow'),'A50:License');
assert(isfile(src),'A50:MissingA48');
load_system(src);
sourceModel='DCHR_A48_Graphical_Closed_Loop';
dst=fullfile(here,'DCHR_A50_Sensor_Lag.slx');
save_system(sourceModel,dst);
close_system(sourceModel,0);
mdl='DCHR_A50_Sensor_Lag';
cases={'neither','backup_only'};
lags=[0,1,4];
fields={'qdc','hx','leak','qcharge','qdis','qpool','qdh'};
outs={'temp','energy','mode','active','residual','unhandled','served','required','cap','itres','tesres'};
expected={'T_next_C','E_next_J','state','active_it_W','residual_it_W', ...
 'unhandled_W','pool_dh_served_W','required_reject_W','effective_cap_W','it_balance_W','tes_balance_J'};
tol=[1e-7,1e-3,0,1e-6,1e-6,1e-6,1e-6,1e-6,1e-6,1e-5,1e-3];
allChecks=0;result=struct();
for j=1:numel(cases)
 for k=1:numel(lags)
  label=cases{j};lag=lags(k);
  load_system(dst);
  if lag>0
   delete_line(mdl,'DelayTemp/1','SupervisorSignals/1');
   prev='DelayTemp/1';
   for ix=1:lag
    block=sprintf('%s/SensorLag_%d',mdl,ix);
    add_block('simulink/Discrete/Unit Delay',block,'InitialCondition','30', ...
      'SampleTime','900','Position',[1320+100*ix 790 1350+100*ix 820]);
    add_line(mdl,prev,sprintf('SensorLag_%d/1',ix),'autorouting','on');
    prev=sprintf('SensorLag_%d/1',ix);
   end
   add_line(mdl,prev,'SupervisorSignals/1','autorouting','on');
  end
  ref=readtable(fullfile(here,sprintf('REF_%s_lag%d.csv',label,lag)));
  assert(height(ref)==240,'A50:InputCount');
  tgrid=(0:239)'*900;
  for s=1:8
   if s<=7,y=double(ref.(fields{s}));
   else,y=double(ref.nominal_cap_W);end
   assignin('base',sprintf('a48_sig_%d',s),[[tgrid;tgrid(end)+900],[y;y(end)]]);
  end
  set_param(mdl,'StopTime',num2str(239*900));
  so=sim(mdl,'ReturnWorkspaceOutputs','on');
  dif=zeros(1,numel(outs));
  for n=1:numel(outs)
   x=so.get(['a48_out_' outs{n}]);
   assert(size(x,1)==240,'A50:SimRows');
   got=double(x(:,end));
   if n==3
    mapping=containers.Map({'ACTIVE','TRIP_PENDING','TRIPPED','RAMPING'},[0,1,2,3]);
    want=zeros(240,1);
    for row=1:240,want(row)=mapping(char(string(ref.state(row))));end
   else,want=double(ref.(expected{n}));end
   dif(n)=max(abs(got-want));
   assert(dif(n)<=tol(n),'A50:Parity');
   allChecks=allChecks+numel(got);
  end
  modeSeries=so.get('a48_out_mode');
  first=find(double(modeSeries(:,end))==2,1,'first');
  expectedTrip=find(strcmp(string(ref.state),'TRIPPED'),1,'first');
  assert(isequal(first,expectedTrip),'A50:TripIndex');
  key=sprintf('%s_lag%d',label,lag);
  result.(key)=struct('samples',240,'trip_index_zero_based',first-1,'max_abs_differences',dif);
  fprintf('A50_PASS %s trip=%d comparisons=%d\n',key,first-1,numel(outs)*240);
  close_system(mdl,0);
 end
end
report=struct('status','A50_GRAPHICAL_SENSOR_LAG_PARITY_PASS', ...
 'model',dst,'comparisons',allChecks,'scenarios',result, ...
 'physical_release',false,'source_a48_unmodified',true,'trip_delay_steps',2);
fid=fopen(fullfile(here,'MATLAB_A50_RESULT.json'),'w');assert(fid>0);
fprintf(fid,'%s\n',jsonencode(report,PrettyPrint=true));fclose(fid);
fprintf('A50_ALL_PASS %d\n',allChecks);
