% A44: Isolated graphical Stateflow supervisory state machine.
% Synthetic test vectors only. Not coupled to production or physical equipment.
here=fileparts(mfilename('fullpath'));
mdl='DCHR_A44_Graphical_Supervisor';
assert(license('test','Stateflow') && license('test','Simulink'),'A44:License');
if bdIsLoaded(mdl),close_system(mdl,0);end
new_system(mdl);
add_block('sflib/Chart',[mdl '/Supervisor'],'Position',[330 110 570 330]);
rt=sfroot;
ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Supervisor']);
assert(isscalar(ch),'A44:Chart');
ch.ActionLanguage='MATLAB';
inputs={'fault','recover','rampDone'};
for k=1:numel(inputs)
 d=Stateflow.Data(ch);d.Name=inputs{k};d.Scope='Input';
end
outputs={'mode','alarm'};
for k=1:numel(outputs)
 d=Stateflow.Data(ch);d.Name=outputs{k};d.Scope='Output';
end
d=Stateflow.Data(ch);d.Name='pending';d.Scope='Local';
d=Stateflow.Data(ch);d.Name='good';d.Scope='Local';
a=Stateflow.State(ch);
a.LabelString=sprintf('ACTIVE\nentry: mode=0; alarm=0;');
a.Position=[40 35 135 85];
p=Stateflow.State(ch);
p.LabelString=sprintf('TRIP_PENDING\nentry: mode=1; alarm=1; pending=1;\nduring: pending=pending+1;');
p.Position=[260 35 165 100];
t=Stateflow.State(ch);
t.LabelString=sprintf('TRIPPED\nentry: mode=2; alarm=2; good=0;\nduring: if recover && ~fault; good=good+1; else; good=0; end');
t.Position=[260 230 175 105];
r=Stateflow.State(ch);
r.LabelString=sprintf('RAMPING\nentry: mode=3; alarm=1;');
r.Position=[40 230 140 90];
q=Stateflow.Transition(ch);q.Destination=a;q.DestinationOClock=0;q.SourceEndPoint=[100 5];
q=Stateflow.Transition(ch);q.Source=a;q.Destination=p;q.LabelString='[fault]';
q=Stateflow.Transition(ch);q.Source=p;q.Destination=a;q.LabelString='[~fault && recover]';
q=Stateflow.Transition(ch);q.Source=p;q.Destination=t;q.LabelString='[pending>=2]';
q=Stateflow.Transition(ch);q.Source=t;q.Destination=r;q.LabelString='[good>=1 && recover && ~fault]';
q=Stateflow.Transition(ch);q.Source=r;q.Destination=a;q.LabelString='[rampDone && ~fault]';
q=Stateflow.Transition(ch);q.Source=r;q.Destination=p;q.LabelString='[fault]';
assert(numel(ch.find('-isa','Stateflow.Transition'))==7,'A44:TransitionCount');
for k=1:3
 name=sprintf('%s/In%d',mdl,k);
 add_block('simulink/Sources/From Workspace',name,'VariableName',sprintf('a44_sig_%d',k),...
  'Interpolate','on','Position',[40 70+90*k 230 105+90*k]);
 add_line(mdl,sprintf('In%d/1',k),sprintf('Supervisor/%d',k),'autorouting','on');
end
for k=1:2
 name=sprintf('%s/Out%d',mdl,k);
 add_block('simulink/Sinks/To Workspace',name,'VariableName',sprintf('a44_out_%d',k),...
  'SaveFormat','Array','Position',[690 110+100*k 830 145+100*k]);
 add_line(mdl,sprintf('Supervisor/%d',k),sprintf('Out%d/1',k),'autorouting','on');
end
set_param(mdl,'Solver','FixedStepDiscrete','FixedStep','900',...
 'StopTime',num2str(671*900),'SaveTime','off');
save_system(mdl,fullfile(here,[mdl '.slx']));
cases={'nominal','short_fault','sustained_fault','interrupted_recovery'};
checks=0;
results=struct();
for j=1:numel(cases)
 label=cases{j};
 tab=readtable(fullfile(here,['STIM_A44_' label '.csv']));
 assert(height(tab)==672,'A44:Rows');
 time=(0:671)'*900;
 vals={double(tab.fault),double(tab.recover),double(tab.ramp_done)};
 for k=1:3
  v=vals{k};
  assignin('base',sprintf('a44_sig_%d',k),[[time;time(end)+900],[v;v(end)]]);
 end
 so=sim(mdl,'ReturnWorkspaceOutputs','on');
 m=so.get('a44_out_1');al=so.get('a44_out_2');
 assert(size(m,1)==672 && size(al,1)==672,'A44:SimRows');
 gotmode=double(m(:,end));gotalarm=double(al(:,end));
 wantmode=double(tab.mode);wantalarm=double(tab.alarm);
 mismatch=sum(gotmode~=wantmode)+sum(gotalarm~=wantalarm);
 fprintf('A44_SCENARIO %s mismatch=%d counts=%s\n',label,mismatch,mat2str(histcounts(gotmode,-.5:1:3.5)));
 assert(mismatch==0,'A44:PythonStateParity');
 checks=checks+2*672;
 results.(label)=struct('samples',672,'mismatch',mismatch,...
  'mode_counts',[sum(gotmode==0),sum(gotmode==1),sum(gotmode==2),sum(gotmode==3)]);
end
audit=struct('status','A44_GRAPHICAL_STATEFLOW_PARITY_PASS',...
 'model',fullfile(here,[mdl '.slx']), 'state_count',4,...
 'transition_count',7,'comparisons',checks,'physical_release',false,...
 'hp_compressor_inertia_integrated',false,'scenarios',results);
fid=fopen(fullfile(here,'MATLAB_A44_RESULT.json'),'w');assert(fid>0);
fprintf(fid,'%s\n',jsonencode(audit,PrettyPrint=true));fclose(fid);
fprintf('A44_ALL_PASS %d\n',checks);
close_system(mdl,0);
