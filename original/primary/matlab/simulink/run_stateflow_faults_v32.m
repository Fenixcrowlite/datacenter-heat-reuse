function evidence=run_stateflow_faults_v32(mdl,folder,spec)
% Faults run against loaded saved model; only temporary in-memory chart edits.
here=fileparts(mfilename('fullpath'));base=spec.cases;
if iscell(base),base=base{1};else,base=base(1);end
base.p=reshape(base.p,1,[]);base.h=reshape(base.h,1,[]);
base.inputs=[6 35 75 1 45;6 35 75 1 45];base.initial_energy_MWh=9;
baseline=sim(configure(mdl,base));save(fullfile(folder,'pre_fault_clean_simulation.mat'),'baseline');
evidence=struct('id',{},'rejected',{},'error_message',{},'stop_event',{},'phase',{},'time_h',{});
for k=1:numel(spec.domain_faults)
    id=spec.domain_faults{k};c=base;
    switch id
        case 'negative_source',c.inputs(1,1)=-1;
        case 'negative_demand',c.inputs(1,4)=-1;
        case 'delivery_above_cutoff',c.inputs(1,5)=70;
        case 'condenser_below_max',c.inputs(1,3)=60;
        case 'negative_rate',c.p(7)=-1;
        case 'cutoff_above_capacity',c.p(8)=11;
        case 'zero_heat_capacity',c.p(9)=0;
        case 'negative_boiler',c.p(11)=-1;
        case 'invalid_efficiency',c.p(5)=0;
        case 'invalid_backend',c.h(6)=2;
        case 'invalid_lift',c.inputs(1,2)=80;
        case 'above_capacity_state',c.initial_energy_MWh=11;
        case 'dt_mismatch',c.p(1)=.5;
        otherwise,error('Unspecified domain fixture');
    end
    s=configure(mdl,c);if strcmp(id,'dt_mismatch'),s=s.setVariable('dchr_dt_v32',1,'Workspace',mdl);end
    reject(id,s,false);
end
for k=1:2
    c=base;id='delayed_negative_source';c.inputs(2,1)=-1;
    if k==2,id='delayed_delivery_fault';c.inputs(2,1)=6;c.inputs(2,5)=70;end
    reject(id,configure(mdl,c),true);
end
rt=sfroot;ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Execute_Segments/Thermal_Dispatch']);
f=ch.find('-isa','Stateflow.EMFunction','Name','stateflow_allocate_v32');original=f.Script;
restore=onCleanup(@()set(f,'Script',original)); %#ok<NASGU>
mutations={'z(1)=0;','z(15)=99;','z(11)=z(11)+1;','z(9)=cfg(11)+1;', ...
    'z(5)=z(5)+1;','z(2)=z(2)+.1;','z(3)=z(3)+.1;','z(17)=z(17)+1;'};
for k=1:numel(spec.monitor_faults)
    id=spec.monitor_faults{k};f.Script=regexprep(original,'end\s*$',sprintf('%s\nend\n',mutations{k}));
    fid=fopen(fullfile(folder,[id '_in_memory_allocation.m']),'w');assert(fid>0);fprintf(fid,'%s',f.Script);fclose(fid);
    reject(id,configure(mdl,base),false);f.Script=original;
end
result=sim(configure(mdl,base));save(fullfile(folder,'post_fault_clean_simulation.mat'),'result');
assert(isempty(result.ErrorMessage) && isequaln(result.segment_trace_v32.Data,baseline.segment_trace_v32.Data), ...
    'DCHR:v32:FaultRestoration','Restored model differs from baseline.');
assert(strcmp(f.Script,fileread(fullfile(here,'stateflow_allocate_v32.m'))),'Saved allocator not restored.');
    function reject(id,s,delayed)
        result=sim(s.setModelParameter('CaptureErrors','on'));
        save(fullfile(folder,[id '_fault_simulation.mat']),'result');
        info=result.SimulationMetadata.ExecutionInfo;diag=info.ErrorDiagnostic;
        phase='';t=[];if ~isempty(diag),phase=diag.SimulationPhase;t=diag.SimulationTime;end
        ok=~isempty(result.ErrorMessage) && strcmp(phase,'Execution');
        if delayed,ok=ok && isequal(t,base.p(1));else,ok=ok && isequal(t,0);end
        if startsWith(id,'segment_'),ok=ok && contains(result.ErrorMessage,'Runtime_Contract_Gate') && contains(result.ErrorMessage,'assert(');
        else,ok=ok && (contains(result.ErrorMessage,'physical-domain') || contains(result.ErrorMessage,'Invalid parameters'));end
        evidence(end+1)=struct('id',id,'rejected',ok,'error_message',result.ErrorMessage, ...
            'stop_event',info.StopEvent,'phase',phase,'time_h',t);
        fprintf('FAULT_EXECUTED=%s rejected=%d\n',id,ok);
    end
end
function s=configure(mdl,c)
n=size(c.inputs,1);dt=c.p(1);s=Simulink.SimulationInput(mdl);
names={'dt','stop','input','p','h','E0'};values={dt,(n-1)*dt,[(0:n-1)'*dt c.inputs],c.p,c.h,c.initial_energy_MWh};
for k=1:numel(names),s=s.setVariable(['dchr_' names{k} '_v32'],values{k},'Workspace',mdl);end
end
