function run_charge_correlated_v60(folder)
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'matlab'),fullfile(root,'matlab','simulink'));
assert(isfolder(folder)&&~isfile(fullfile(folder,'report.json')));spec=jsondecode(fileread(fullfile(folder,'spec.json')));
Simulink.fileGenControl('set','CacheFolder',fullfile(folder,'local_build','cache'), ...
    'CodeGenFolder',fullfile(folder,'local_build','codegen'),'createDir',true);
metadata=struct('matlab_version',version,'stateflow_license_test',license('test','Stateflow'), ...
    'stateflow_version',ver('stateflow'),'sfroot_class',class(sfroot),'simulation_mode','normal');disp(metadata);
mdl='DCHR_Charge_Event_Record_v60';model=fullfile(root,'matlab','simulink',[mdl '.slx']);
if ~isfile(model),build_charge_event_record_v60();end
load_system(model);cl=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
ch=sfroot;metadata.chart_count=numel(ch.find('-isa','Stateflow.Chart','Path',[mdl '/Event_Handoff']));
checks=struct('name',{},'passed',{});runs={};faults=struct('id',{},'rejected',{},'completed_samples',{},'error_message',{});
for j=1:numel(spec.cases)
    c=spec.cases(j);r=dchr.components.charge_regime_events_v56(c.s,c.p,c.E,c.request);horizon=r.next_event_h+c.post_h;
    z=dchr.components.charge_correlated_event_v60(c.s,c.p,c.E,horizon,c.request,c.clock0,128);
    packets=pack(z);result=execute(packets);source=sprintf('%s_simulation.mat',c.id);
    save(fullfile(folder,source),'result','packets','c','z','-v7.3');reopen=load(fullfile(folder,source));
    record([c.id '_executed'],isempty(result.ErrorMessage));assert(isempty(result.ErrorMessage),result.ErrorMessage);
    trace=reshape(result.event_trace_v60.Data,32,[])';
    record([c.id '_three_real_chart_phases'],isequal(trace(:,1)',[0 1 2]));
    record([c.id '_no_scalar_memory'],all(trace(:,30)==0)&&~z.scalar_memory_handoff_authorized);
    record([c.id '_exact_manifold_projection'],isequal(trace(2,2:3),z.event_energy_MWh_interval));
    record([c.id '_no_inventory_reset'],isequal(z.event_energy_MWh_interval,z.outgoing_flow.initial_energy_MWh_interval));
    record([c.id '_shared_clock'],isequal(trace(2,6:7),z.event_clock_h_interval)&&isequal(trace(3,6:7),z.end_clock_h_interval));
    record([c.id '_closure'],z.total.first_law_MWh_interval(1)<=0&&z.total.first_law_MWh_interval(2)>=0);
    record([c.id '_MAT_reopen'],isequaln(reopen.result,result)&&isequaln(reopen.z,z)&&isequaln(reopen.packets,packets));
    runs{end+1}=struct('id',c.id,'input',c,'record',reopen.z,'packets',reopen.packets,'trace',trace,'source_mat',source); %#ok<AGROW>
    fprintf('CORRELATED_V60 id=%s event=[%.17g %.17g] phases=%s equivalent=%s\n',c.id,z.event_time_h_interval,mat2str(trace(:,1)'),mat2str(z.equivalent_limiter_mask));
end
% Faults enter the saved compiled model; retain valid protocol prefix.
base=runs{1}.packets;ids={'scalar_authorization','energy_snap','clock_reset','duration_midpoint','negative_heat', ...
    'bad_source_closure','bad_first_law','tie_mask_change','skip_contact','changed_event_time','nonfinite'};
for j=1:numel(ids)
    u=base;
    switch j
        case 1,u(3,30)=1;
        case 2,u(2,2:3)=u(2,31);
        case 3,u(3,6:7)=0;
        case 4,u(3,8:9)=mean(u(3,8:9));
        case 5,u(3,10)=-1;
        case 6,u(3,12:13)=u(3,12:13)+1;
        case 7,u(3,16:17)=u(3,16:17)+1;
        case 8,u(3,24)=1-u(3,24);
        case 9,u(2,1)=2;
        case 10,u(3,22:23)=u(3,22:23)+.01;
        case 11,u(3,2)=NaN;
    end
    result=execute(u);file=['fault_' ids{j} '_simulation.mat'];save(fullfile(folder,file),'u','result','-v7.3');
    count=0;if any(strcmp(result.who,'event_trace_v60')),count=numel(result.event_trace_v60.Time);end
    rejected=~isempty(result.ErrorMessage)&&contains(result.ErrorMessage,'Event');
    record(['fault_' ids{j}],rejected);record(['fault_prefix_' ids{j}],count==1+(~ismember(j,[2 9])));
    faults(end+1)=struct('id',ids{j},'rejected',rejected,'completed_samples',count,'error_message',result.ErrorMessage); %#ok<AGROW>
end
% Unsupported contacts and capacity spans fail closed in the host proof.
c=spec.cases(1);r=dchr.components.charge_regime_events_v56(c.s,c.p,c.E,c.request);
for j=1:4
    en=c.E;h=r.next_event_h+c.post_h;clock=c.clock0;
    if j==1,h=.1;elseif j==2,en=6;elseif j==3,clock=[1 0];else,h=20;end
    identifier='';try,dchr.components.charge_correlated_event_v60(c.s,c.p,en,h,c.request,clock);catch e,identifier=e.identifier;end
    record(sprintf('host_unsupported_%d',j),~isempty(identifier));
end
report=struct('version','0.60','metadata',metadata,'new_scoped_model',true,'full_coupled_stateflow_acceptance',false, ...
    'runs',{runs},'faults',faults,'assertions',checks,'summary',struct('passed',sum([checks.passed]),'failed',sum(~[checks.passed])));
save(fullfile(folder,'charge_correlated_v60.mat'),'report','-v7.3');writejson(fullfile(folder,'report.json'),report);
reopen=load(fullfile(folder,'charge_correlated_v60.mat'),'report');assert(isequaln(reopen.report,report));writejson(fullfile(folder,'mat_reopen.json'),reopen.report);
mkdir(fullfile(folder,'binary'));records=struct('id',{},'field',{},'rows',{},'columns',{},'file',{});
for j=1:numel(reopen.report.runs),item=reopen.report.runs{j};walk(item.id,'input',item.input);walk(item.id,'record',item.record);emit(item.id,'packets',item.packets);emit(item.id,'trace',item.trace);end
writejson(fullfile(folder,'binary_manifest.json'),struct('source','ORIGINAL_REOPENED_MAT_BINARY64','source_mat','charge_correlated_v60.mat','records',records));
fprintf('CORRELATED_V60 PASS=%d FAIL=%d RUNS=%d ACTUAL_FAULTS=%d\n',report.summary.passed,report.summary.failed,numel(runs),sum([faults.rejected]));
assert(all([checks.passed]),'DCHR:v60:Acceptance','Inspect retained evidence.');
    function record(name,ok),checks(end+1)=struct('name',name,'passed',logical(ok));end
    function result=execute(packets)
        in=Simulink.SimulationInput(mdl);in=in.setVariable('event_packets_v60',[(0:2)' packets],'Workspace',mdl);
        result=sim(in,'ShowProgress','off','CaptureErrors','on');
    end
    function walk(id,prefix,value)
        if isnumeric(value)||islogical(value),emit(id,prefix,double(value));
        elseif isstruct(value)&&isscalar(value)
            keys=fieldnames(value);for n=1:numel(keys),walk(id,[prefix '.' keys{n}],value.(keys{n}));end
        end
    end
    function emit(id,field,v)
        file=sprintf('binary/%05d.bin',numel(records)+1);fd=fopen(fullfile(folder,file),'w','ieee-le');assert(fd>0);
        assert(fwrite(fd,v','double')==numel(v));fclose(fd);
        records(end+1)=struct('id',id,'field',field,'rows',size(v,1),'columns',size(v,2),'file',file);
    end
end
function packets=pack(z)
packets=zeros(3,32);packets(:,1)=(0:2)';packets(:,20)=z.initial_energy_MWh;packets(:,21)=z.horizon_h;
packets(:,22:23)=repmat(z.event_time_h_interval,3,1);packets(:,24:28)=repmat(z.equivalent_limiter_mask,3,1);
packets(:,29)=1;packets(:,31:32)=repmat(z.event_energy_MWh_interval,3,1);
packets(1,2:3)=z.initial_energy_MWh;packets(1,6:7)=z.initial_clock_h_interval;
packets(2,2:3)=z.event_energy_MWh_interval;packets(2,4:5)=z.event_time_h_interval;
packets(2,6:7)=z.event_clock_h_interval;packets(2,8:9)=z.event_time_h_interval;
packets(3,2:3)=z.total.end_energy_MWh_interval;packets(3,4:5)=z.horizon_h;
packets(3,6:7)=z.end_clock_h_interval;packets(3,8:9)=z.outgoing_flow.duration_h_interval;
names={'heat_MWh_interval','source_MWh_interval','compressor_MWh_interval','standing_loss_MWh_interval','charge_loss_MWh_interval'};
for n=1:5,cols=8+2*n:9+2*n;packets(2,cols)=z.incoming_flow.(names{n});packets(3,cols)=z.total.(names{n});end
end
function writejson(path,value)
assert(~isfile(path));fd=fopen(path,'w');assert(fd>0);cl=onCleanup(@()fclose(fd)); %#ok<NASGU>
fprintf(fd,'%s\n',jsonencode(value,PrettyPrint=true));
end
