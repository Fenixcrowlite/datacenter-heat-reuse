function run_finite_interface_v53(folder)
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'matlab'),fullfile(root,'matlab','simulink'));
assert(isfolder(folder)&&~isfile(fullfile(folder,'report.json')));
Simulink.fileGenControl('set','CacheFolder',fullfile(folder,'local_build','cache'), ...
    'CodeGenFolder',fullfile(folder,'local_build','codegen'),'createDir',true);
s=jsondecode(fileread(fullfile(folder,'spec.json')));base=s.boundary;policy=s.policy;
checks=struct('name',{},'passed',{});vectors=struct('spec',{},'boundary',{});
for Tin=[35 45]
for glide=[5 10]
for approach=[2 5 10]
for eta=[.35 .5 .65]
for ratio=[0 .1]
for alpha=[0 .5 1]
    v=base;v.source_in_C=Tin;v.source_glide_K=glide;
    v.evaporator_approach_K=approach;v.condenser_approach_K=approach;
    v.cooling_factor=eta;v.aux_per_compressor=ratio;v.aux_hot_fraction=alpha;
    b=dchr.components.finite_temperature_boundary_v53(v);
    vectors(end+1)=struct('spec',v,'boundary',b); %#ok<AGROW>
    record('component_first_law',abs(b.rated_source_MW+b.rated_compressor_MW+b.rated_aux_MW- ...
        b.rated_counted_heat_MW-b.rated_aux_rejected_MW)<1e-12);
    record('component_capacity',b.required_source_capacity_MW_per_K<=v.source_capacity_MW_per_K+1e-12 && ...
        b.required_hot_capacity_MW_per_K<=v.hot_capacity_MW_per_K+1e-12);
end
end
end
end
end
end
faults=struct('id',{},'identifier',{},'message',{},'rejected',{});
bad=base;bad.source_glide_K=0;reject('zero_glide',@()dchr.components.finite_temperature_boundary_v53(bad));
bad=base;bad.cooling_factor=1.1;reject('factor_above_one',@()dchr.components.finite_temperature_boundary_v53(bad));
bad=base;bad.evaporator_approach_K=400;reject('below_absolute_zero',@()dchr.components.finite_temperature_boundary_v53(bad));
bad=base;bad.hot_in_C=100;reject('hot_glide_reversed',@()dchr.components.finite_temperature_boundary_v53(bad));
bad=base;bad.discharge_approach_K=30;reject('cutoff_above_tank',@()dchr.components.finite_temperature_boundary_v53(bad));
bad=base;bad.source_capacity_MW_per_K=-1;reject('negative_capacity',@()dchr.components.finite_temperature_boundary_v53(bad));
bad=base;bad.aux_hot_fraction=1.1;reject('aux_fraction',@()dchr.components.finite_temperature_boundary_v53(bad));
bad=base;bad.source_in_C=NaN;reject('nonfinite',@()dchr.components.finite_temperature_boundary_v53(bad));
bad=base;bad.source_capacity_MW_per_K=realmax;reject('overflow',@()dchr.components.finite_temperature_boundary_v53(bad));
bad=base;bad.aux_hot_fraction=.5;reject('unsupported_aux_heat',@()dchr.adapt_finite_stateflow_v53(bad,policy,1));
reject('negative_demand',@()dchr.adapt_finite_stateflow_v53(base,policy,-1));
bp=policy;bp.restart_C=80;reject('restart_above_tank',@()dchr.adapt_finite_stateflow_v53(base,bp,1));
mdl='DCHR_Dispatch_Stateflow_v52';load_system(fullfile(root,'matlab','simulink',[mdl '.slx']));
cleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
rt=sfroot;charts=[rt.find('-isa','Stateflow.Chart','Path',[mdl '/Execute_Segments/Thermal_Dispatch']); ...
    rt.find('-isa','Stateflow.Chart','Path',[mdl '/Execute_Segments/HP_Supervisor'])];
metadata=struct('matlab_version',version,'stateflow_license_test',license('test','Stateflow'), ...
    'stateflow_version',ver('stateflow'),'chart_count',numel(charts),'simulation_mode','normal');
record('actual_stateflow_charts',numel(charts)==2&&metadata.stateflow_license_test==1);
originals=struct('id',{},'adapter',{},'error_message',{},'dispatch',{},'segments',{},'plans',{},'clock_start',{},'clock_end',{},'raw_segments',{},'raw_plans',{});
cases=struct('id',{},'adapter',{},'dispatch',{},'segments',{},'plans',{},'padding_count',{}, ...
    'clock_start',{},'clock_end',{},'aux_energy_MWh',{},'compressor_energy_MWh',{});
ids={'zero_demand','hp_only','tes_charge','tes_discharge','boiler_limit','insufficient_heat', ...
    'approach_0','approach_5','approach_10','hot_capacity_limit','sequence'};
for j=1:numel(ids)
    v=base;p=policy;demand=1;
    if j==1,v.source_capacity_MW_per_K=0;demand=0;p.initial_energy_MWh=0;end
    if j==2,p.charge_limit_MW=0;p.initial_energy_MWh=0;end
    if j==4,v.source_capacity_MW_per_K=0;p.initial_energy_MWh=9;end
    if j==5,v.source_capacity_MW_per_K=0;demand=2;p.initial_energy_MWh=0;end
    if j==6,v.source_capacity_MW_per_K=0;demand=5;p.initial_energy_MWh=0;end
    if j>=7&&j<=9,v.evaporator_approach_K=(j-7)*5;v.condenser_approach_K=(j-7)*5;demand=6;p.initial_energy_MWh=0;end
    if j==10,v.hot_capacity_MW_per_K=.08;demand=6;p.initial_energy_MWh=0;end
    if j==11,demand=repmat([0;1;6;10;2;0],4,1);p.initial_energy_MWh=9;end
    a=dchr.adapt_finite_stateflow_v53(v,p,demand);
    si=Simulink.SimulationInput(mdl);n=size(a.inputs,1);
    names={'dt','stop','input','p','h','E0','c','m0'};
    values={a.p(1),(n-1)*a.p(1),[(0:n-1)'*a.p(1) a.inputs],a.p,a.h,a.initial_energy_MWh,a.c,a.initial_clock};
    for k=1:numel(names),si=si.setVariable(['dchr_' names{k} '_v52'],values{k},'Workspace',mdl);end
    result=sim(si.setModelParameter('CaptureErrors','on'));
    save(fullfile(folder,[ids{j} '_simulation.mat']),'result','a','-v7.3');
    record([ids{j} '_executed'],isempty(result.ErrorMessage));assert(isempty(result.ErrorMessage),result.ErrorMessage);
    dispatch=samples(result.dispatch_trace_v52,25);raw=samples(result.segment_trace_v52,1792);plan=samples(result.plan_trace_v52,1472);
    segments=[];plans=[];padding=0;
    for k=1:n
        z=reshape(raw(k,:),28,64)';q=reshape(plan(k,:),23,64)';positive=z(:,2)>0;
        record([ids{j} '_exact_handoff'],all(z(2:end,4)==z(1:end-1,5)) && all(q(:,2)==z(:,4)) && dispatch(k,8)==z(end,5));
        record([ids{j} '_padding_identity'],all(z(~positive,4)==z(~positive,5))&&all(z(~positive,6:14)==0,'all')&&all(z(~positive,17:21)==0,'all'));
        segments=[segments;repmat(k,sum(positive),1) z(positive,:)]; %#ok<AGROW>
        plans=[plans;repmat(k,sum(positive),1) q(positive,:)]; %#ok<AGROW>
        padding=padding+sum(~positive);
    end
    if j<=6,record([ids{j} '_required_mode'],dispatch(1,1)==j-1);end
    ce=sum(segments(:,13).*segments(:,3));ae=v.aux_per_compressor*ce;
    cases(end+1)=struct('id',ids{j},'adapter',a,'dispatch',dispatch,'segments',segments,'plans',plans, ...
        'padding_count',padding,'clock_start',samples(result.clock_start_trace_v52,4), ...
        'clock_end',samples(result.clock_end_trace_v52,4),'aux_energy_MWh',ae,'compressor_energy_MWh',ce); %#ok<AGROW>
    reopen=load(fullfile(folder,[ids{j} '_simulation.mat']));
    record([ids{j} '_original_MAT_reopen'],isequaln(result.dispatch_trace_v52,reopen.result.dispatch_trace_v52)&& ...
        isequaln(result.segment_trace_v52,reopen.result.segment_trace_v52)&&isequaln(result.plan_trace_v52,reopen.result.plan_trace_v52)&&isequaln(a,reopen.a));
    originals(end+1)=struct('id',ids{j},'adapter',reopen.a,'error_message',reopen.result.ErrorMessage, ...
        'dispatch',samples(reopen.result.dispatch_trace_v52,25),'segments',segments,'plans',plans, ...
        'clock_start',samples(reopen.result.clock_start_trace_v52,4),'clock_end',samples(reopen.result.clock_end_trace_v52,4), ...
        'raw_segments',samples(reopen.result.segment_trace_v52,1792),'raw_plans',samples(reopen.result.plan_trace_v52,1472)); %#ok<AGROW>
    fprintf('FINITE_INTERFACE_V53 id=%s intervals=%d segments=%d modes=%s\n',ids{j},n,size(segments,1),mat2str(unique(dispatch(:,1))'));
end
report=struct('version','0.53','model_version','0.52','new_model',false,'metadata',metadata, ...
    'vectors',vectors,'faults',faults,'cases',cases,'assertions',checks, ...
    'summary',struct('passed',sum([checks.passed]),'failed',sum(~[checks.passed]),'component_vectors',numel(vectors)));
save(fullfile(folder,'finite_interface_v53.mat'),'report','-v7.3');writejson(fullfile(folder,'report.json'),report);
writejson(fullfile(folder,'simulation_reopen.json'),originals);
reopened=load(fullfile(folder,'finite_interface_v53.mat'),'report');assert(isequaln(report,reopened.report));
writejson(fullfile(folder,'mat_reopen.json'),reopened.report);
fprintf('FINITE_INTERFACE_V53 PASS=%d FAIL=%d\n',report.summary.passed,report.summary.failed);
assert(all([checks.passed]),'DCHR:v53:AcceptanceFailure','Inspect retained report.');
    function record(name,ok),checks(end+1)=struct('name',name,'passed',logical(ok));end
    function reject(id,fn)
        identifier='';message='';
        try,fn();catch e,identifier=e.identifier;message=e.message;end
        ok=~isempty(identifier);record(['domain_' id],ok);
        faults(end+1)=struct('id',id,'identifier',identifier,'message',message,'rejected',ok);
    end
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;
if ismatrix(raw)&&isequal(size(raw),[n width]),v=raw;
elseif numel(raw)==n*width,v=reshape(raw,width,n)';else,error('DCHR:v53:TraceShape','Unexpected trace dimensions.');end
end
function writejson(path,value)
assert(~isfile(path));fid=fopen(path,'w');assert(fid>0);cleanup=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(value,PrettyPrint=true));
end
