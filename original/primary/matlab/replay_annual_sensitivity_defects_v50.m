function replay_annual_sensitivity_defects_v50(folder)
% Two isolated actual saved-SLX replays and exact binary padding witnesses.
root=fileparts(fileparts(mfilename('fullpath')));here=fullfile(root,'matlab','simulink');
addpath(fullfile(root,'matlab'),here);s=load(fullfile(folder,'annual_sensitivity_v50.mat'));
d=load(fullfile(folder,'defect_evidence','defects_v50.mat'));
target=fullfile(folder,'defect_replay');assert(~isfolder(target));mkdir(target);
Simulink.fileGenControl('set','CacheFolder',fullfile(folder,'local_build','cache'), ...
    'CodeGenFolder',fullfile(folder,'local_build','codegen'),'createDir',true);
mdl='DCHR_Dispatch_Stateflow_v42';load_system(fullfile(here,[mdl '.slx']));
cleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
replays=[];
for j=1:numel(d.items)
    failed=d.items(j);c=failed.candidate;assert(~isempty(c));
    item=s.report.stateflow(strcmp({s.report.stateflow.id},failed.id));
    plan=dchr_segment_plan_v42(c.input,c.initial_energy_MWh,item.p,item.h,item.p(1),c.initial_clock,item.c);
    witnesses=[];
    for k=1:64
        pp=plan(:,k);if pp(1)>0,continue;end
        clock=[pp(15);pp(18);pp(20);pp(22)];mode=stateflow_choose_mode_v42(pp,item.p);
        v=stateflow_allocate_v42(mode,pp,item.p,clock);
        w=struct('slot',k,'span_h',pp(1),'input_energy_hex',num2hex(pp(2)), ...
            'output_energy_hex',num2hex(v(5)),'capacity_hex',num2hex(item.p(2)), ...
            'residual_hex',num2hex(v(21)),'input_energy_MWh',pp(2), ...
            'output_energy_MWh',v(5),'residual_MWh',v(21), ...
            'capacity_overshoot_MWh',pp(2)-item.p(2),'ulp_capacity_MWh',eps(item.p(2)), ...
            'mode',v(1),'power_ports',v(6:14)','loss_and_delivery',v(17:20)', ...
            'padding_predicate',v(1)==0&&all(v(6:14)==0)&&all(v(17:21)==0)&&v(5)==v(4));
        if isempty(witnesses),witnesses=w;else,witnesses(end+1)=w;end %#ok<AGROW>
    end
    simulation=Simulink.SimulationInput(mdl);names={'dt','stop','input','p','h','E0','c','m0'};
    values={item.p(1),0,[0 c.input],item.p,item.h,c.initial_energy_MWh,item.c,c.initial_clock};
    for k=1:numel(names),simulation=simulation.setVariable(['dchr_' names{k} '_v42'],values{k},'Workspace',mdl);end
    result=sim(simulation.setModelParameter('CaptureErrors','on'));
    save(fullfile(target,[item.id '_isolated_simulation.mat']),'result','plan','c','witnesses','-v7.3');
    entry=struct('id',item.id,'interval',c.interval,'input',c.input, ...
        'initial_energy_MWh',c.initial_energy_MWh,'initial_clock',c.initial_clock, ...
        'initial_energy_hex',num2hex(c.initial_energy_MWh),'input_hex',{cellstr(num2hex(c.input(:)))}, ...
        'error_message',result.ErrorMessage,'rejected',contains(result.ErrorMessage,'Zero-span segment has service.'), ...
        'positive_segments',sum(plan(1,:)>0),'witnesses',witnesses);
    assert(entry.rejected&&any(~[witnesses.padding_predicate]),'Isolated defect did not reproduce.');
    if isempty(replays),replays=entry;else,replays(end+1)=entry;end %#ok<AGROW>
    fprintf('ISOLATED_DEFECT_V50 id=%s interval=%d rejected=%d overshoot=%.17g\n', ...
        item.id,c.interval,entry.rejected,witnesses(1).capacity_overshoot_MWh);
end
save(fullfile(target,'isolated_replays_v50.mat'),'replays');
fid=fopen(fullfile(target,'isolated_replays_v50.json'),'w');assert(fid>0);clean=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(replays,PrettyPrint=true));fprintf('ISOLATED_REPLAY_V50 complete\n');
end
