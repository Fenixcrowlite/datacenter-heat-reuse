function run_stateflow_dwell_probes_v42(folder,specFile)
% Function probes plus actual saved-model attacks using only in-memory edits.
here=fileparts(mfilename('fullpath'));root=fileparts(fileparts(here));addpath(fullfile(root,'matlab'),here);
snap=fullfile(folder,'dwell_probe_source');mkdir(snap);
copyfile(specFile,fullfile(snap,'spec.json'));copyfile([mfilename('fullpath') '.m'],snap);
spec=jsondecode(fileread(specFile));outputs=[];
for k=1:size(spec.probes,1)
    v=spec.probes(k,:);[ok,margin]=stateflow_dwell_ready_v42(v(1),v(2),v(3),v(4));
    t=stateflow_dwell_wait_v42(v(1),v(2),v(3),v(4));
    [H,L,B]=stateflow_clock_add_v42(v(1),v(2),v(3),t);
    outputs(k,:)=[v double(ok) margin t H L B]; %#ok<AGROW>
end
writejson(fullfile(folder,'dwell_probes_v42.json'),struct('probes',outputs));
work=fullfile(folder,'dwell_attack_work');mkdir(work);
Simulink.fileGenControl('set','CacheFolder',fullfile(work,'cache'),'CodeGenFolder',fullfile(work,'codegen'),'createDir',true);
mdl='DCHR_Dispatch_Stateflow_v42';load_system(fullfile(here,[mdl '.slx']));clean=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
rt=sfroot;f=rt.find('-isa','Stateflow.EMChart','Path',[mdl '/Segment_HP_Plan']);original=f.Script;
f.Script=strrep(original,'dchr_segment_plan_v42','dchr_segment_plan_v40');
restore=onCleanup(@()set(f,'Script',original)); %#ok<NASGU>
items=[];
for on=0:1
    for delayed=0:1
        dt=.125;age=1;if delayed,age=.875;end
        inputs=repmat([6 35 75 1 45],1+delayed,1);n=size(inputs,1);
        names={'dt','stop','input','p','h','E0','c','m0'};
        values={dt,(n-1)*dt,[(0:n-1)'*dt inputs],[dt 10 3 4 .9 .8 .1 5 .2 20 .5], ...
            [8 .45 1.2 8 0 1 4 0 0],7+3*on,[8 1 1 64],[on;age;0;1e-9]};
        s=Simulink.SimulationInput(mdl);
        for j=1:numel(names),s=s.setVariable(['dchr_' names{j} '_v42'],values{j},'Workspace',mdl);end
        result=sim(s.setModelParameter('CaptureErrors','on'));
        id=sprintf('nominal_planner_on%d_delayed%d',on,delayed);
        save(fullfile(folder,[id '_attack.mat']),'result');
        diag=result.SimulationMetadata.ExecutionInfo.ErrorDiagnostic;phase='';time=[];
        if ~isempty(diag),phase=diag.SimulationPhase;time=diag.SimulationTime;end
        where='Runtime_Contract_Gate';if delayed,where='HP_Supervisor';end
        item=struct('id',id,'error_message',result.ErrorMessage,'phase',phase,'time_h',time, ...
            'expected_time_h',delayed*dt,'expected_component',where, ...
            'passed',~isempty(result.ErrorMessage)&&strcmp(phase,'Execution')&&isequal(time,delayed*dt)&&contains(result.ErrorMessage,where));
        if isempty(items),items=item;else,items(end+1)=item;end %#ok<AGROW>
        fprintf('UNCERTAINTY_ATTACK=%s passed=%d\n',id,item.passed);
    end
end
f.Script=original;
clear restore % Restore while Stateflow handles are still valid, before model close.
writejson(fullfile(folder,'uncertainty_attacks_v42.json'),items);
assert(all([items.passed]),'DCHR:v42:AttackAcceptance','Saved supervisor/runtime gate did not reject nominal planner.');
fprintf('DWELL_PROBES=%d\n',size(outputs,1));
end
function writejson(path,v)
assert(~isfile(path));fid=fopen(path,'w');assert(fid>0);clean=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(v,PrettyPrint=true));
end
