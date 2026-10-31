from pathlib import Path
p=Path(__file__).with_name("run_a40.m")
s=p.read_text(encoding="utf-8")
needle="fid=fopen(fullfile(here,'MATLAB_RESULT.json'),'w');assert(fid>0);"
assert s.count(needle)==1
block="""% Additional real Stateflow replay: alternative REJECT availability profiles.
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
        {'t_s','required_W','capacity_W','temperature_C','tes_soc','mode','shed_fraction','alarm'});
    writetable(tr,fullfile(here,['STATEFLOW_TRACE_' scenario '.csv']));
    counts=[sum(mo(:,end)==0),sum(mo(:,end)==1),sum(mo(:,end)==2),sum(mo(:,end)==3)];
    result.scenario_mode_counts.(scenario)=counts;
    fprintf('A40_SCENARIO_PASS %s counts=%s\\n',scenario,mat2str(counts));
end
assert(result.scenario_mode_counts.neither(3)>0,'A40:NoCriticalOnOutage');
"""
s=s.replace(needle,block+needle)
p.write_text(s,encoding="utf-8")
print("PATCHED_4_SCENARIOS")
