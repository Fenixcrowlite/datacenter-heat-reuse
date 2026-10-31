function out=run_stateflow_dimensional_faults_v36(mdl,folder,cases)
% Actual runtime injections across energy scales, plus labelled component probes.
rt=sfroot;ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Execute_Segments/Thermal_Dispatch']);
f=ch.find('-isa','Stateflow.EMFunction','Name','stateflow_allocate_v36');original=f.Script;
planner=rt.find('-isa','Stateflow.EMChart','Path',[mdl '/Segment_HP_Plan']);planOriginal=planner.Script;
out.faults=struct('id',{},'capacity_MWh',{},'rejected',{},'phase',{},'time_h',{},'error_message',{});
out.time=struct('name',{},'passed',{},'age_h',{},'tolerance_h',{},'classification',{});
mutations={'z(7)=cfg(3)+.01;','z(15)=z(15)+.01;','z(22)=z(22)+.01;','z(3)=z(3)+.01;'};
labels={'power','COP','temperature','offset'};
for j=1:numel(cases)
    c=cases{j};if ~startsWith(c.id,'scale_'),continue;end
    for k=1:numel(mutations)
        id=[c.id '_' labels{k}];f.Script=regexprep(original,'end\s*$',sprintf('%s\nend\n',mutations{k}));
        recordFault(id,c,'Runtime_Contract_Gate');f.Script=original;
    end
    % OFF age .24 h: falsely present a planner age .25 h to force early restart.
    c.initial_clock=[0;.24];
    planner.Script=strrep(planOriginal,'dt,m,c);','dt,[m(1);m(2)+.01],c);');
    assert(~strcmp(planner.Script,planOriginal),'Mutation did not bind planner.');
    recordFault([c.id '_early_restart'],c,'Runtime_Contract_Gate');planner.Script=planOriginal;
    % Guard both ON and OFF dwell around their physical boundaries.
    for target=0:1
        for delta=[-.01 0 .01]
            s=zeros(18,1);s(16)=0;s(4)=6;
            if target==1,s(17)=3;s(2)=.6*c.p(2);else,s(17)=2;s(2)=c.p(2);end
            age=.25+delta;allowed=stateflow_supervisor_guard_v36(target,s,reshape(c.p,1,[]),reshape(c.c,1,[]),age);
            out.time(end+1)=struct('name',sprintf('%s_target%d_delta%g',c.id,target,delta), ...
                'passed',allowed==(delta>=0),'age_h',age,'tolerance_h',stateflow_time_tolerance_v36([age;.25]), ...
                'classification','direct_guard_component_probe'); %#ok<AGROW>
        end
    end
end
% Explicit representability contract rather than unbounded ulp-based tolerance.
for age=[0 1 1e4 1e6 1e9 2^52]
    rejected=false;tol=NaN;
    try,tol=stateflow_time_tolerance_v36([age;.25]);catch,rejected=true;end
    expected=64*eps(max(1,age));
    out.time(end+1)=struct('name',sprintf('time_resolution_%g',age), ...
        'passed',rejected==(expected>1e-8) && (rejected || tol==expected),'age_h',age,'tolerance_h',tol, ...
        'classification','direct_time_resolution_component_probe'); %#ok<AGROW>
end
c=cases{end};c.initial_clock=[1;1e9];
recordFault('unrepresentable_clock',c,'resolution exceeds');
f.Script=original;planner.Script=planOriginal;
    function recordFault(id,c,where)
        dt=c.p(1);n=size(c.inputs,1);si=Simulink.SimulationInput(mdl);
        names={'dt','stop','input','p','h','E0','c','m0'};
        values={dt,(n-1)*dt,[(0:n-1)'*dt c.inputs],reshape(c.p,1,[]),reshape(c.h,1,[]), ...
            c.initial_energy_MWh,reshape(c.c,1,[]),reshape(c.initial_clock,2,1)};
        for ii=1:numel(names),si=si.setVariable(['dchr_' names{ii} '_v36'],values{ii},'Workspace',mdl);end
        result=sim(si.setModelParameter('CaptureErrors','on'));
        save(fullfile(folder,[id '_dimensional_simulation.mat']),'result');
        d=result.SimulationMetadata.ExecutionInfo.ErrorDiagnostic;phase='';t=[];
        if ~isempty(d),phase=d.SimulationPhase;t=d.SimulationTime;end
        ok=~isempty(result.ErrorMessage) && strcmp(phase,'Execution') && isequal(t,0) && contains(result.ErrorMessage,where);
        out.faults(end+1)=struct('id',id,'capacity_MWh',c.p(2),'rejected',ok,'phase',phase, ...
            'time_h',t,'error_message',result.ErrorMessage);
        fid=fopen(fullfile(folder,[id '_mutation.txt']),'w');fprintf(fid,'%s\n%s',f.Script,planner.Script);fclose(fid);
        fprintf('DIMENSIONAL_FAULT=%s rejected=%d\n',id,ok);
    end
end
