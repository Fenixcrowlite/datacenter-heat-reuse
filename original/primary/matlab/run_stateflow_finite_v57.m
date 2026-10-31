function run_stateflow_finite_v57(folder)
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'matlab'),fullfile(root,'matlab','simulink'));
assert(isfolder(folder) && ~isfile(fullfile(folder,'report.json')));
Simulink.fileGenControl('set','CacheFolder',fullfile(folder,'local_build','cache'), ...
    'CodeGenFolder',fullfile(folder,'local_build','codegen'),'createDir',true);
spec=jsondecode(fileread(fullfile(folder,'spec.json')));base=spec.boundary;policy=spec.policy;
mdl='DCHR_Dispatch_Stateflow_v57';modelPath=fullfile(root,'matlab','simulink',[mdl '.slx']);
% Observe the current API/license before building; never infer installed version.
metadata=struct('matlab_version',version,'stateflow_license_test',license('test','Stateflow'), ...
    'stateflow_version',ver('stateflow'),'simulation_mode','normal');
disp(metadata);rt=sfroot;metadata.sfroot_class=class(rt);disp(metadata.sfroot_class);
assert(metadata.stateflow_license_test); % sfroot is a legacy UDD Simulink.Root.
if ~isfile(modelPath),build_dispatch_stateflow_v57();end
load_system(modelPath);cleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
metadata.chart_count=numel(rt.find('-isa','Stateflow.Chart','Path',[mdl '/Execute_Segments/Thermal_Dispatch']))+ ...
    numel(rt.find('-isa','Stateflow.Chart','Path',[mdl '/Execute_Segments/HP_Supervisor']));
checks=struct('name',{},'passed',{});cases=struct('id',{},'intervals',{},'positive_segments',{},'modes',{});
faults=struct('id',{},'error_message',{},'completed_samples',{},'rejected',{});
references=struct('id',{},'passed',{},'max_delta',{});
records=struct('source_mat',{},'id',{},'field',{},'rows',{},'columns',{},'file',{});
binaryFolder=fullfile(folder,'binary');mkdir(binaryFolder);
ids={'zero_demand','hp_only','tes_charge','tes_discharge','boiler_limit','insufficient_heat', ...
    'approach_zero','approach_ten','hot_flow_limit','source_flow_limit','sequence','changing_water','capacity_dwell'};
for j=1:numel(ids)
    v=base;pol=policy;demand=1;
    if j==1,v.source_capacity_MW_per_K=0;demand=0;pol.initial_energy_MWh=0;end
    if j==2,pol.charge_limit_MW=0;pol.initial_energy_MWh=0;end
    if j==4,v.source_capacity_MW_per_K=0;pol.initial_energy_MWh=9;end
    if j==5,v.source_capacity_MW_per_K=0;demand=2;pol.initial_energy_MWh=0;end
    if j==6,v.source_capacity_MW_per_K=0;demand=5;pol.initial_energy_MWh=0;end
    if j==7,v.evaporator_approach_K=0;v.condenser_approach_K=0;demand=6;end
    if j==8,v.evaporator_approach_K=10;v.condenser_approach_K=10;demand=6;end
    if j==9,v.hot_capacity_MW_per_K=.02;demand=6;end
    if j==10,v.source_capacity_MW_per_K=.02;demand=6;end
    if j==11,demand=repmat([0;1;6;10;2;0],4,1);pol.initial_energy_MWh=9;end
    if j==12,demand=[0;1;6;10;2;0;5;1];pol.initial_energy_MWh=9;end
    if j==13,demand=repmat([0;5;0;1],6,1);pol.initial_energy_MWh=9.9;end
    a=dchr.adapt_finite_stateflow_v53(v,pol,demand);n=numel(demand);inputs=repmat(pack(v),n,1);inputs(:,17)=demand;
    if j==12
        inputs(:,1)=[35;40;45;35;40;45;35;40];inputs(:,3)=[0;2;5;10;0;2;5;10];
        inputs(:,4)=[10;5;2;0;10;5;2;0];inputs(:,11)=[.8;.4;0;.1;.8;.4;0;.1];
        inputs(:,12)=[.6;.1;.3;.6;.6;.1;.3;.6];inputs(:,14)=[.35;.5;.65;.35;.5;.65;.35;.5];
        inputs(:,15)=[0;.1;.3;0;.1;.3;0;.1];
    end
    input=struct('inputs',inputs,'p',a.p,'c',a.c,'dt',a.p(1),'E0',a.initial_energy_MWh,'m0',a.initial_clock);
    result=execute(input);source=[ids{j} '_simulation.mat'];save(fullfile(folder,source),'result','input','-v7.3');
    record([ids{j} '_executed'],isempty(result.ErrorMessage));assert(isempty(result.ErrorMessage),result.ErrorMessage);
    dispatch=samples(result.dispatch_trace_v57,25);raw=samples(result.segment_trace_v57,1792);plans=samples(result.plan_trace_v57,1472);
    bound=samples(result.finite_boundary_trace_v57,13);account=samples(result.finite_accounting_trace_v57,7);
    record([ids{j} '_sample_count'],size(dispatch,1)==n);
    positive=0;mode=[];
    for i=1:n
        z=reshape(raw(i,:),28,64)';q=reshape(plans(i,:),23,64)';active=z(:,2)>0;
        positive=positive+sum(active);mode=union(mode,z(active,1));
        record([ids{j} '_strict_handoff'],all(z(2:end,4)==z(1:end-1,5)) && all(q(:,2)==z(:,4)) && dispatch(i,8)==z(end,5));
        record([ids{j} '_exact_padding'],all(z(~active,4)==z(~active,5)) && all(z(~active,6:14)==0,'all') && all(z(~active,17:21)==0,'all'));
        record([ids{j} '_finite_first_law'],abs(account(i,5))<1e-9 && account(i,2)==account(i,3));
        record([ids{j} '_flow_limits'],account(i,6)<=inputs(i,11)+1e-10 && account(i,7)<=inputs(i,12)+1e-10);
    end
    if j<=6,record([ids{j} '_required_mode'],dispatch(1,1)==j-1);end
    cases(end+1)=struct('id',ids{j},'intervals',n,'positive_segments',positive,'modes',mode'); %#ok<AGROW>
    % Bind the QA exports to reopened original SimulationOutputs.
    reopen=load(fullfile(folder,source),'result','input');record([ids{j} '_MAT_reopen'],isequaln(result,reopen.result)&&isequaln(input,reopen.input));
    emit(source,ids{j},'dispatch',samples(reopen.result.dispatch_trace_v57,25));
    emit(source,ids{j},'raw_segments',samples(reopen.result.segment_trace_v57,1792));
    emit(source,ids{j},'raw_plans',samples(reopen.result.plan_trace_v57,1472));
    emit(source,ids{j},'boundary',samples(reopen.result.finite_boundary_trace_v57,13));
    emit(source,ids{j},'accounting',samples(reopen.result.finite_accounting_trace_v57,7));
    emit(source,ids{j},'clock_start',samples(reopen.result.clock_start_trace_v57,4));
    emit(source,ids{j},'clock_end',samples(reopen.result.clock_end_trace_v57,4));
    emit(source,ids{j},'energy_start',samples(reopen.result.energy_start_trace_v57,1));
    for key={'inputs','p','c','E0','m0','dt'},emit(source,ids{j},['input.' key{1}],reopen.input.(key{1}));end
    if j<=6
        cfg=reference_config(a);tableInput=array2table(a.inputs,'VariableNames',{'Source_Heat_MW','Source_C','Sink_C','Heat_Demand_MW','Delivery_C'});
        ref=table2array(dchr.simulate_dispatch_v30(cfg,tableInput));cols=[1:21 23:25];delta=abs(ref(:,cols)-dispatch(:,cols));delta(isnan(delta))=0;
        ok=isequal(isnan(ref(:,cols)),isnan(dispatch(:,cols))) && max(delta,[],'all')<1e-10;
        record([ids{j} '_v30_reference'],ok);references(end+1)=struct('id',ids{j},'passed',ok,'max_delta',max(delta,[],'all')); %#ok<AGROW>
        save(fullfile(folder,[ids{j} '_reference.mat']),'ref','cfg','tableInput','-v7.3');
        r=load(fullfile(folder,[ids{j} '_reference.mat']),'ref');emit([ids{j} '_reference.mat'],ids{j},'reference',r.ref(:,1:25));
    end
    fprintf('FINITE_STATEFLOW_V57 id=%s intervals=%d positive=%d modes=%s\n',ids{j},n,positive,mat2str(mode'));
end
% All faults enter the actual saved model, including one delayed finite fault.
faultIds={'zero_glide','negative_capacity','factor_above_one','below_absolute_zero', ...
    'reversed_hot_glide','aux_hot_credit','tank_redefinition','cutoff_redefinition','negative_demand', ...
    'nonfinite','overflow','delayed_capacity'};
a=dchr.adapt_finite_stateflow_v53(base,policy,1);
for j=1:numel(faultIds)
    u=pack(base);u(17)=1;
    if j==1,u(2)=0;end
    if j==2,u(11)=-1;end
    if j==3,u(14)=1.1;end
    if j==4,u(3)=400;end
    if j==5,u(10)=100;end
    if j==6,u(16)=.5;end
    if j==7,u(5)=71;end
    if j==8,u(8)=4;end
    if j==9,u(17)=-1;end
    if j==10,u(1)=NaN;end
    if j==11,u(11)=realmax;end
    if j==12,good=pack(base);good(17)=1;u=[good;good;good];u(3,11)=-1;end
    input=struct('inputs',u,'p',a.p,'c',a.c,'dt',a.p(1),'E0',a.initial_energy_MWh,'m0',a.initial_clock);
    result=execute(input);source=['fault_' faultIds{j} '_simulation.mat'];save(fullfile(folder,source),'result','input','-v7.3');
    failed=~isempty(result.ErrorMessage);completed=0;
    if isprop(result,'dispatch_trace_v57') || any(strcmp(result.who,'dispatch_trace_v57')),completed=numel(result.dispatch_trace_v57.Time);end
    record(['runtime_fault_' faultIds{j}],failed && contains(result.ErrorMessage,'finite','IgnoreCase',true));
    if j==12
        record('delayed_fault_valid_prefix',completed==2);
        if completed>0
            reopen=load(fullfile(folder,source),'result','input');
            emit(source,'fault_delayed_capacity','dispatch',samples(reopen.result.dispatch_trace_v57,25));
            emit(source,'fault_delayed_capacity','inputs',reopen.input.inputs);
        end
    end
    faults(end+1)=struct('id',faultIds{j},'error_message',result.ErrorMessage,'completed_samples',completed,'rejected',failed); %#ok<AGROW>
    fprintf('FINITE_RUNTIME_FAULT_V57 id=%s rejected=%d prefix=%d\n',faultIds{j},failed,completed);
end
report=struct('version','0.57','model_version','0.57','new_model',true,'metadata',metadata, ...
    'scope',spec.scope,'cases',cases,'faults',faults,'references',references,'assertions',checks, ...
    'summary',struct('passed',sum([checks.passed]),'failed',sum(~[checks.passed])));
save(fullfile(folder,'stateflow_finite_v57.mat'),'report','-v7.3');writejson(fullfile(folder,'report.json'),report);
r=load(fullfile(folder,'stateflow_finite_v57.mat'),'report');assert(isequaln(report,r.report));writejson(fullfile(folder,'mat_reopen.json'),r.report);
writejson(fullfile(folder,'binary_manifest.json'),struct('version','0.57','source','ORIGINAL_REOPENED_MAT_BINARY64', ...
    'encoding','IEEE_BINARY64_LITTLE_ENDIAN_ROW_MAJOR','records',records));
fprintf('FINITE_STATEFLOW_V57 PASS=%d FAIL=%d\n',report.summary.passed,report.summary.failed);
assert(all([checks.passed]),'DCHR:v57:AcceptanceFailure','Inspect retained evidence.');
    function result=execute(input)
        n=size(input.inputs,1);si=Simulink.SimulationInput(mdl);
        names={'dt','stop','input','p','E0','c','m0'};values={input.dt,(n-1)*input.dt,[(0:n-1)'*input.dt input.inputs],input.p,input.E0,input.c,input.m0};
        for k=1:numel(names),si=si.setVariable(['dchr_' names{k} '_v57'],values{k},'Workspace',mdl);end
        result=sim(si.setModelParameter('CaptureErrors','on'));
    end
    function record(name,ok),checks(end+1)=struct('name',name,'passed',logical(ok));end
    function emit(source,id,field,v)
        assert(isa(v,'double') && isreal(v) && ismatrix(v));name=sprintf('%03d_%s_%s.bin',numel(records)+1,id,strrep(field,'.','_'));
        fd=fopen(fullfile(binaryFolder,name),'w','ieee-le');assert(fd>0);cl=onCleanup(@()fclose(fd)); %#ok<NASGU>
        assert(fwrite(fd,v','double')==numel(v));
        records(end+1)=struct('source_mat',source,'id',id,'field',field,'rows',size(v,1),'columns',size(v,2),'file',['binary/' name]);
    end
end
function v=pack(s)
names={'source_in_C','source_glide_K','evaporator_approach_K','condenser_approach_K', ...
    'tank_max_C','delivery_C','charge_approach_K','discharge_approach_K','direct_approach_K', ...
    'hot_in_C','source_capacity_MW_per_K','hot_capacity_MW_per_K','hp_capacity_MW', ...
    'cooling_factor','aux_per_compressor','aux_hot_fraction'};
v=zeros(1,17);for k=1:16,v(k)=s.(names{k});end
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;
if ismatrix(raw)&&isequal(size(raw),[n width]),v=raw;
elseif numel(raw)==n*width,v=reshape(raw,width,n)';else,error('DCHR:v57:TraceShape','Unexpected trace shape.');end
end
function writejson(path,value)
assert(~isfile(path));fd=fopen(path,'w');assert(fd>0);cl=onCleanup(@()fclose(fd)); %#ok<NASGU>
fprintf(fd,'%s\n',jsonencode(value,PrettyPrint=true));
end
function cfg=reference_config(a)
p=a.p;h=a.h;cfg=default_config_v2();cfg.sim.dt_h=p(1);cfg.backup.max_heat_MW=p(11);
cfg.storage.heat_capacity_MWh_per_K=p(9);cfg.storage.ambient_C=p(10);
cfg.storage.max_temperature_C=p(10)+p(2)/p(9);cfg.storage.delivery_cutoff_C=p(10)+p(8)/p(9);
cfg.storage.initial_temperature_C=p(10)+a.initial_energy_MWh/p(9);
cfg.storage.charge_limit_MW=p(3);cfg.storage.discharge_limit_MW=p(4);cfg.storage.eta_charge=p(5);
cfg.storage.eta_discharge=p(6);cfg.storage.continuous_loss_rate_per_h=p(7);
cfg.hp.max_heat_output_MW=h(1);cfg.hp.carnot_efficiency=h(2);cfg.hp.cop_min=h(3);cfg.hp.cop_max=h(4);
cfg.hp.part_load_penalty=h(5);cfg.model.hp_backend='carnot';
end
