% A53: 18-case graphical Stateflow crossproduct, isolated from source models.
here=fileparts(mfilename('fullpath'));
source=fullfile(fileparts(here),'AUTONOMOUS_RUN_20261027_0450_A51_TRIP_DELAY_GRAPHICAL');
cases={'neither','backup_only'};
lags=[0 1 4];trips=[0 2 4];
fields={'qdc','hx','leak','qcharge','qdis','qpool','qdh'};
outs={'temp','energy','mode','active','residual','unhandled','served','required','cap','itres','tesres'};
expected={'T_next_C','E_next_J','state','active_it_W','residual_it_W','unhandled_W','pool_dh_served_W','required_reject_W','effective_cap_W','it_balance_W','tes_balance_J'};
tol=[1e-7,1e-3,0,1e-6,1e-6,1e-6,1e-6,1e-6,1e-6,1e-5,1e-3];
assert(license('test','Stateflow') && license('test','Simulink'),'A53:License');
total=0; report=struct();
for ti=1:numel(trips)
 trip=trips(ti);
 srcModel=sprintf('DCHR_A51_TripDelay_%d',trip);
 src=fullfile(source,[srcModel '.slx']);
 assert(isfile(src),'A53:Source');
 load_system(src);
 mdl=sprintf('DCHR_A53_TripDelay_%d',trip);
 dst=fullfile(here,[mdl '.slx']);
 save_system(srcModel,dst);
 close_system(srcModel,0);
 for ci=1:numel(cases)
  for li=1:numel(lags)
   label=cases{ci};lag=lags(li);
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
   ref=readtable(fullfile(here,sprintf('REF_%s_lag%d_trip%d.csv',label,lag,trip)));
   assert(height(ref)==240,'A53:Rows');
   time=(0:239)'*900;
   for s=1:8
    if s<=7,y=double(ref.(fields{s}));else,y=double(ref.nominal_cap_W);end
    assignin('base',sprintf('a48_sig_%d',s),[[time;time(end)+900],[y;y(end)]]);
   end
   set_param(mdl,'StopTime',num2str(239*900));
   so=sim(mdl,'ReturnWorkspaceOutputs','on');
   dif=zeros(1,numel(outs)); actual=struct();
   for n=1:numel(outs)
    x=so.get(['a48_out_' outs{n}]);
    assert(size(x,1)==240,'A53:SimRows');
    got=double(x(:,end));
    if n==3
     mapping=containers.Map({'ACTIVE','TRIP_PENDING','TRIPPED','RAMPING'},[0,1,2,3]);
     want=zeros(240,1);
     for row=1:240,want(row)=mapping(char(string(ref.state(row))));end
    else,want=double(ref.(expected{n}));end
    dif(n)=max(abs(got-want));
    assert(dif(n)<=tol(n),sprintf('A53:Parity_%s_lag%d_trip%d_%s',label,lag,trip,outs{n}));
    total=total+numel(got);
    actual.(outs{n})=got;
   end
   first=find(actual.mode==2,1,'first');
   firstRef=find(strcmp(string(ref.state),'TRIPPED'),1,'first');
   assert(isequal(first,firstRef),'A53:TripIndex');
   key=sprintf('%s_lag%d_trip%d',label,lag,trip);
   report.(key)=struct('samples',240,'first_trip_index_zero_based',first-1,...
    'max_temperature_C',max(actual.temp),'max_abs_differences',dif);
   fprintf('A53_PASS %s first=%d comparisons=2640\n',key,first-1);
   close_system(mdl,0);
  end
 end
end
assert(total==47520,'A53:Total');
result=struct('status','A53_GRAPHICAL_CROSSPRODUCT_PARITY_PASS', ...
 'comparisons',total,'cases',report,'synthetic_only',true,'physical_release',false, ...
 'source_a51_unmodified',true,'sensor_lag_steps',[0 1 4],'trip_delay_steps',[0 2 4]);
fid=fopen(fullfile(here,'MATLAB_A53_RESULT.json'),'w');assert(fid>0);
fprintf(fid,'%s\n',jsonencode(result,PrettyPrint=true));fclose(fid);
fprintf('A53_ALL_PASS %d\n',total);

