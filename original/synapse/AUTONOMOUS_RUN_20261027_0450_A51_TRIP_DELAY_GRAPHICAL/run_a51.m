% A51: isolated graphical Stateflow trip-delay variations, synthetic inputs.
here=fileparts(mfilename('fullpath'));
src=fullfile(fileparts(here),'AUTONOMOUS_RUN_20261027_0351_A50_SENSOR_LAG_MATLAB','DCHR_A50_Sensor_Lag.slx');
assert(isfile(src) && license('test','Stateflow') && license('test','Simulink'),'A51:Prerequisite');
srcModel='DCHR_A50_Sensor_Lag';
cases={'neither','backup_only'};
delays=[0 2 4];
fields={'qdc','hx','leak','qcharge','qdis','qpool','qdh'};
outs={'temp','energy','mode','active','residual','unhandled','served','required','cap','itres','tesres'};
expected={'T_next_C','E_next_J','state','active_it_W','residual_it_W','unhandled_W','pool_dh_served_W','required_reject_W','effective_cap_W','it_balance_W','tes_balance_J'};
tol=[1e-7,1e-3,0,1e-6,1e-6,1e-6,1e-6,1e-6,1e-6,1e-5,1e-3];
total=0;report=struct();
for k=1:numel(delays)
 trip=delays(k);
 load_system(src);
 mdl=sprintf('DCHR_A51_TripDelay_%d',trip);
 dst=fullfile(here,[mdl '.slx']);
 save_system(srcModel,dst);
 close_system(srcModel,0);
 load_system(dst);
 rt=sfroot;
 ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/GraphicalSupervisor']);
 assert(isscalar(ch),'A51:MissingGraphicalChart');
 states=ch.find('-isa','Stateflow.State');
 target=[];
 for si=1:numel(states)
  if startsWith(string(states(si).LabelString),"TRIPPED")
   target=states(si);break
  end
 end
 assert(~isempty(target),'A51:MissingTripState');
 transitions=ch.find('-isa','Stateflow.Transition');
 guardCount=0;faultCount=0;
 for ti=1:numel(transitions)
  label=char(transitions(ti).LabelString);
  if strcmp(label,'[pending>=2]')
   transitions(ti).LabelString=sprintf('[pending>=%d]',trip);
   guardCount=guardCount+1;
  elseif trip==0 && strcmp(label,'[fault]')
   transitions(ti).Destination=target;
   faultCount=faultCount+1;
  end
 end
 assert(guardCount==1 && (trip~=0 || faultCount==2),'A51:GuardMutation');
 save_system(mdl,dst);
 for j=1:numel(cases)
  scenario=cases{j};
  ref=readtable(fullfile(here,sprintf('REF_%s_trip%d.csv',scenario,trip)));
  assert(height(ref)==240,'A51:Rows');
  time=(0:239)'*900;
  for s=1:8
   if s<=7,y=double(ref.(fields{s}));
   else,y=double(ref.nominal_cap_W);end
   assignin('base',sprintf('a48_sig_%d',s),[[time;time(end)+900],[y;y(end)]]);
  end
  set_param(mdl,'StopTime',num2str(239*900));
  so=sim(mdl,'ReturnWorkspaceOutputs','on');
  dif=zeros(1,numel(outs));actual=struct();
  for n=1:numel(outs)
   x=so.get(['a48_out_' outs{n}]);
   assert(size(x,1)==240,'A51:SimRows');
   got=double(x(:,end));
   if n==3
    mapping=containers.Map({'ACTIVE','TRIP_PENDING','TRIPPED','RAMPING'},[0,1,2,3]);
    want=zeros(240,1);
    for row=1:240,want(row)=mapping(char(string(ref.state(row))));end
   else,want=double(ref.(expected{n}));end
   dif(n)=max(abs(got-want));
   assert(dif(n)<=tol(n),sprintf('A51:Parity_%s_trip%d_%s',scenario,trip,outs{n}));
   total=total+numel(got);
   actual.(outs{n})=got;
  end
  first=find(actual.mode==2,1,'first');
  firstRef=find(strcmp(string(ref.state),'TRIPPED'),1,'first');
  assert(isequal(first,firstRef),'A51:TripIndex');
  key=sprintf('%s_trip%d',scenario,trip);
  report.(key)=struct('samples',240,'first_trip_index_zero_based',first-1,...
    'max_temperature_C',max(actual.temp),'max_abs_differences',dif);
  fprintf('A51_PASS %s first=%d comparisons=%d\n',key,first-1,2640);
 end
 close_system(mdl,0);
end
result=struct('status','A51_GRAPHICAL_TRIP_DELAY_PARITY_PASS',...
 'comparisons',total,'cases',report,'synthetic_only',true,'physical_release',false,...
 'source_a50_unmodified',true,'delay_steps',[0 2 4]);
fid=fopen(fullfile(here,'MATLAB_A51_RESULT.json'),'w');assert(fid>0);
fprintf(fid,'%s\n',jsonencode(result,PrettyPrint=true));fclose(fid);
fprintf('A51_ALL_PASS %d\n',total);
