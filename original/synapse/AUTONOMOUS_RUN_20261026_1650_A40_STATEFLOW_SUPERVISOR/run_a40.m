% A40 isolated synthetic Stateflow supervisory controller, NO hardware interface.
here = fileparts(mfilename('fullpath'));
mdl = 'DCHR_A40_Safety_Controller';
assert(license('test','Stateflow') && license('test','Simulink'), 'A40:License');
if bdIsLoaded(mdl), close_system(mdl,0); end
new_system(mdl);
cleanup = onCleanup(@()close_system(mdl,0));
add_block('sflib/Chart',[mdl '/Supervisor'],'Position',[340 70 530 250]);
rt=sfroot;
ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Supervisor']);
assert(isscalar(ch),'A40:Chart');
ch.ActionLanguage='MATLAB';
inputNames={'requiredW','capacityW','tempC','soc'};
for k=1:numel(inputNames)
    d=Stateflow.Data(ch);d.Name=inputNames{k};d.Scope='Input';
end
outputNames={'mode','shedCeilingFraction','alarm'};
for k=1:numel(outputNames)
    d=Stateflow.Data(ch);d.Name=outputNames{k};d.Scope='Output';
end
n=Stateflow.State(ch);
n.LabelString=sprintf('NORMAL\nentry: mode=0; shedCeilingFraction=0; alarm=0;');
n.Position=[45 45 130 80];
d=Stateflow.State(ch);
d.LabelString=sprintf('DEGRADED\nentry: mode=1; shedCeilingFraction=0.4; alarm=1;');
d.Position=[260 45 150 80];
c=Stateflow.State(ch);
c.LabelString=sprintf('CRITICAL\nentry: mode=2; shedCeilingFraction=0.4; alarm=2;');
c.Position=[260 210 150 80];
z=Stateflow.State(ch);
z.LabelString=sprintf('TES_FULL\nentry: mode=3; shedCeilingFraction=0; alarm=1;');
z.Position=[45 210 130 80];
t=Stateflow.Transition(ch);t.Destination=n;t.DestinationOClock=0;t.SourceEndPoint=[110 5];
t=Stateflow.Transition(ch);t.Source=n;t.Destination=d;
t.LabelString='[requiredW > capacityW + 1e-6 && tempC < 42 && capacityW > 0]';
t=Stateflow.Transition(ch);t.Source=d;t.Destination=c;
t.LabelString='[tempC >= 42 || capacityW <= 0]';
t=Stateflow.Transition(ch);t.Source=c;t.Destination=d;
t.LabelString='[tempC < 39 && capacityW > 0]';
t=Stateflow.Transition(ch);t.Source=d;t.Destination=n;
t.LabelString='[requiredW + 5000 <= capacityW && tempC < 39 && soc < 0.999]';
% Safety priority: critical condition must also be caught directly from NORMAL.
t=Stateflow.Transition(ch);t.Source=n;t.Destination=c;
t.LabelString='[tempC >= 42 || capacityW <= 0]';
t=Stateflow.Transition(ch);t.Source=n;t.Destination=z;
t.LabelString='[soc >= 0.999 && requiredW <= capacityW && tempC < 42 && capacityW > 0]';
t=Stateflow.Transition(ch);t.Source=z;t.Destination=n;
t.LabelString='[soc <= 0.98 && requiredW + 5000 <= capacityW && tempC < 39]';
t=Stateflow.Transition(ch);t.Source=z;t.Destination=d;
t.LabelString='[requiredW > capacityW + 1e-6 && tempC < 42 && capacityW > 0]';
t=Stateflow.Transition(ch);t.Source=z;t.Destination=c;
t.LabelString='[tempC >= 42 || capacityW <= 0]';
t=Stateflow.Transition(ch);t.Source=d;t.Destination=z;
t.LabelString='[soc >= 0.999 && requiredW + 5000 <= capacityW && tempC < 39]';
% All critical transitions are disjoint from capacity-only guards.
trs=ch.find('-isa','Stateflow.Transition');
% We assert transition count below; priority is defined by geometry/order in chart.
assert(numel(trs)==11,'A40:Transitions');
set_param(mdl,'Solver','FixedStepDiscrete','FixedStep','900','StopTime',num2str(671*900));
% Synthetic replay from immutable A38 trace. Read-only input.
csvPath='C:\Users\Lysda\Desktop\SynapseControlCenter\recovery\AUTONOMOUS_RUN_20261026_1054_A38_TES_N1_INTEGRATION\trace_main_only_no_shed.csv';
tbl=readtable(csvPath);
assert(height(tbl)==672,'A40:Rows');
tgrid=(0:671)'*900;
vals={tbl.Q_reject_required_W,tbl.capacity_W,tbl.T_IT_start_C,tbl.TES_SOC_next};
names={'required_sig','capacity_sig','temperature_sig','soc_sig'};
for k=1:4
    v=double(vals{k}); assignin('base',names{k},[[tgrid;tgrid(end)+900],[v;v(end)]]);
    bn=sprintf('%s/In%d',mdl,k);
    add_block('simulink/Sources/From Workspace',bn,'VariableName',names{k}, ...
        'Interpolate','on','Position',[30 45+65*k 200 65+65*k]);
    add_line(mdl,sprintf('In%d/1',k),sprintf('Supervisor/%d',k),'autorouting','on');
end
for k=1:3
    bn=sprintf('%s/Out%d',mdl,k);
    add_block('simulink/Sinks/To Workspace',bn,'VariableName',sprintf('out_%d',k), ...
        'SaveFormat','Array','Position',[630 70+65*k 760 95+65*k]);
    add_line(mdl,sprintf('Supervisor/%d',k),sprintf('Out%d/1',k),'autorouting','on');
end
save_system(mdl,fullfile(here,[mdl '.slx']));
simout=sim(mdl,'ReturnWorkspaceOutputs','on');
m=simout.get('out_1');
f=simout.get('out_2');
a=simout.get('out_3');
assert(size(m,1)==672 && size(f,1)==672 && size(a,1)==672,'A40:SimRows');
assert(all(ismember(m(:,end),[0,1,2,3])),'A40:Modes');
assert(all(abs(f(:,end)-0.4*ismember(m(:,end),[1,2]))<1e-12),'A40:Shed');
assert(all(a(:,end)==min(m(:,end),2)-(m(:,end)==3)),'A40:Alarm');
trace=table(tgrid,double(vals{1}),double(vals{2}),double(vals{3}),double(vals{4}), ...
 m(:,end),f(:,end),a(:,end),'VariableNames', ...
 {'t_s','required_W','capacity_W','temperature_C','tes_soc','mode','shed_ceiling_fraction','alarm'});
writetable(trace,fullfile(here,'STATEFLOW_TRACE.csv'));
result=struct('status','STATEFLOW_SIM_PASS','samples',size(m,1), ...
 'mode_counts',[sum(m(:,end)==0),sum(m(:,end)==1),sum(m(:,end)==2),sum(m(:,end)==3)], ...
 'model',fullfile(here,[mdl '.slx']),'physical_release',false);
% Additional real Stateflow replay: alternative REJECT availability profiles.
result.scenario_mode_counts=struct('main_only',result.mode_counts);
for idx=1:3
    scenarios={'both','backup_only','neither'};
    scenario=scenarios{idx};
    tb=readtable(fullfile(fileparts(csvPath),['trace_' scenario '_no_shed.csv']));
    assert(height(tb)==672,'A40:ScenarioRows');
    vs={tb.Q_reject_required_W,tb.capacity_W,tb.T_IT_start_C,tb.TES_SOC_next};
    for j=1:4
        v=double(vs{j});
        assignin('base',names{j},[[tgrid;tgrid(end)+900],[v;v(end)]]);
    end
    so=sim(mdl,'ReturnWorkspaceOutputs','on');
    mo=so.get('out_1'); sh=so.get('out_2'); al=so.get('out_3');
    assert(size(mo,1)==672 && size(sh,1)==672 && size(al,1)==672,'A40:ScenarioSimRows');
    assert(all(ismember(mo(:,end),[0,1,2,3])),'A40:ScenarioModes');
    assert(all(abs(sh(:,end)-0.4*ismember(mo(:,end),[1,2]))<1e-12),'A40:ScenarioShed');
    assert(all(al(:,end)==min(mo(:,end),2)-(mo(:,end)==3)),'A40:ScenarioAlarm');
    tr=table(tgrid,double(vs{1}),double(vs{2}),double(vs{3}),double(vs{4}), ...
        mo(:,end),sh(:,end),al(:,end),'VariableNames', ...
        {'t_s','required_W','capacity_W','temperature_C','tes_soc','mode','shed_ceiling_fraction','alarm'});
    writetable(tr,fullfile(here,['STATEFLOW_TRACE_' scenario '.csv']));
    counts=[sum(mo(:,end)==0),sum(mo(:,end)==1),sum(mo(:,end)==2),sum(mo(:,end)==3)];
    result.scenario_mode_counts.(scenario)=counts;
    fprintf('A40_SCENARIO_PASS %s counts=%s\n',scenario,mat2str(counts));
end
assert(result.scenario_mode_counts.neither(3)>0,'A40:NoCriticalOnOutage');
fid=fopen(fullfile(here,'MATLAB_RESULT.json'),'w');assert(fid>0);
fprintf(fid,'%s\n',jsonencode(result,PrettyPrint=true));fclose(fid);
fprintf('A40_STATEFLOW_SIM_PASS samples=%d modes=%s\n',size(m,1),mat2str(result.mode_counts));
