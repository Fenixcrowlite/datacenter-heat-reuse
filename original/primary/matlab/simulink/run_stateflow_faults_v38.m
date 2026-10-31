function evidence=run_stateflow_faults_v38(mdl,folder,base)
% Only temporary in-memory chart edits. Saved SLX remains immutable.
base.p=reshape(base.p,1,[]);base.h=[8 .45 1.2 8 0 1 4 0 0];base.c=[8 .25 .25 64];
base.inputs=[6 35 75 1 45;6 35 75 1 45];base.initial_energy_MWh=9;base.initial_clock=[1;0;0;0];
baseline=sim(configure(mdl,base));save(fullfile(folder,'pre_fault_clean_simulation.mat'),'baseline');
evidence=struct('id',{},'rejected',{},'error_message',{},'phase',{},'time_h',{});
ids={'negative_source','negative_demand','delivery_above_cutoff','negative_rate','cutoff_above_capacity', ...
    'zero_heat_capacity','negative_boiler','invalid_backend','above_capacity_state','dt_mismatch', ...
    'invalid_restart','negative_on_dwell','negative_off_dwell','invalid_latch','negative_clock','event_budget', ...
    'delayed_source','delayed_nonfinite'};
for k=1:numel(ids)
    c=base;id=ids{k};expectedTime=0;
    switch id
        case 'negative_source',c.inputs(1,1)=-1;
        case 'negative_demand',c.inputs(1,4)=-1;
        case 'delivery_above_cutoff',c.inputs(1,5)=70;
        case 'negative_rate',c.p(7)=-1;
        case 'cutoff_above_capacity',c.p(8)=11;
        case 'zero_heat_capacity',c.p(9)=0;
        case 'negative_boiler',c.p(11)=-1;
        case 'invalid_backend',c.h(6)=2;
        case 'above_capacity_state',c.initial_energy_MWh=11;
        case 'dt_mismatch',c.p(1)=.5;
        case 'invalid_restart',c.c(1)=c.p(8);
        case 'negative_on_dwell',c.c(2)=-1;
        case 'negative_off_dwell',c.c(3)=-1;
        case 'invalid_latch',c.initial_clock=[.5;0;0;0];
        case 'negative_clock',c.initial_clock=[1;-1;0;0];
        case 'event_budget',c.c(4)=1;c.p(1)=4;
        case 'delayed_source',c.inputs(2,1)=-1;expectedTime=c.p(1);
        case 'delayed_nonfinite',c.inputs(2,1)=NaN;expectedTime=c.p(1);
    end
    s=configure(mdl,c);if strcmp(id,'dt_mismatch'),s=s.setVariable('dchr_dt_v38',1,'Workspace',mdl);end
    reject(id,s,expectedTime,'');
end
rt=sfroot;ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Execute_Segments/Thermal_Dispatch']);
f=ch.find('-isa','Stateflow.EMFunction','Name','stateflow_allocate_v38');original=f.Script;
restore=onCleanup(@()set(f,'Script',original)); %#ok<NASGU>
mutations={'z(1)=0;','z(15)=99;','z(11)=z(11)+1;','z(9)=cfg(11)+1;', ...
    'z(5)=z(5)+1;','z(2)=z(2)+.1;','z(3)=z(3)+.1;','z(17)=z(17)+1;', ...
    'z(26)=1-z(26);','z(27)=z(27)+.1;','z(28)=z(28)+.1;'};
for k=1:numel(mutations)
    id=sprintf('monitor_corruption_%02d',k);f.Script=regexprep(original,'end\s*$',sprintf('%s\nend\n',mutations{k}));
    fid=fopen(fullfile(folder,[id '_in_memory_allocation.m']),'w');fprintf(fid,'%s',f.Script);fclose(fid);
    reject(id,configure(mdl,base),0,'Runtime_Contract_Gate');f.Script=original;
end
hc=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Execute_Segments/HP_Supervisor']);
states=hc.find('-isa','Stateflow.State');labels=cell(numel(states),1);
for k=1:numel(states)
    labels{k}=states(k).LabelString;
    states(k).LabelString=strrep(labels{k},'stateflow_clock_add_v38(age,low,bound,s(1))','stateflow_clock_add_v38(age,low,bound,1)');
end
reject('iterator_tick_timer_corruption',configure(mdl,base),0,'');
for k=1:numel(states),states(k).LabelString=labels{k};end
result=sim(configure(mdl,base));save(fullfile(folder,'post_fault_clean_simulation.mat'),'result');
assert(isequaln(result.segment_trace_v38.Data,baseline.segment_trace_v38.Data)&& ...
    isequaln(result.clock_end_trace_v38.Data,baseline.clock_end_trace_v38.Data),'DCHR:v38:Restoration','Restored model differs.');
    function reject(id,s,t,where)
        result=sim(s.setModelParameter('CaptureErrors','on'));save(fullfile(folder,[id '_fault_simulation.mat']),'result');
        diag=result.SimulationMetadata.ExecutionInfo.ErrorDiagnostic;phase='';time=[];
        if ~isempty(diag),phase=diag.SimulationPhase;time=diag.SimulationTime;end
        ok=~isempty(result.ErrorMessage)&&strcmp(phase,'Execution')&&isequal(time,t);
        if ~isempty(where),ok=ok&&contains(result.ErrorMessage,where);end
        if strcmp(id,'event_budget'),ok=ok&&contains(result.ErrorMessage,'Event budget exhausted');end
        evidence(end+1)=struct('id',id,'rejected',ok,'error_message',result.ErrorMessage,'phase',phase,'time_h',time);
        fprintf('FAULT_EXECUTED=%s rejected=%d\n',id,ok);
    end
end
function s=configure(mdl,c)
dt=c.p(1);n=size(c.inputs,1);s=Simulink.SimulationInput(mdl);
names={'dt','stop','input','p','h','E0','c','m0'};
values={dt,(n-1)*dt,[(0:n-1)'*dt c.inputs],c.p,c.h,c.initial_energy_MWh,c.c,reshape(c.initial_clock,4,1)};
for k=1:numel(names),s=s.setVariable(['dchr_' names{k} '_v38'],values{k},'Workspace',mdl);end
end
