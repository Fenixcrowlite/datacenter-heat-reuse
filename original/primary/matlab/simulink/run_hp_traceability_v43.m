function run_hp_traceability_v43(folder)
% Primary-text boundary audit. Executes unchanged HP v40 and saved model v42.
here=fileparts(mfilename('fullpath'));root=fileparts(fileparts(here));
addpath(fullfile(root,'matlab'),here);
spec=jsondecode(fileread(fullfile(folder,'spec.json')));
snap=fullfile(folder,'source_snapshot');mkdir(snap);
for name={'run_hp_traceability_v43.m','export_hp_traceability_v43.m','dchr_stateflow_hp_v42.m','DCHR_Dispatch_Stateflow_v42.slx'}
    copyfile(fullfile(here,name{1}),snap);
end
copyfile(fullfile(root,'matlab','+dchr','+components','heat_pump_step_v40.m'),snap);
copyfile(fullfile(folder,'spec.json'),snap);
work=fullfile(folder,'local_build');mkdir(work);
Simulink.fileGenControl('set','CacheFolder',fullfile(work,'cache'),'CodeGenFolder',fullfile(work,'codegen'),'createDir',true);
cfg.model.hp_backend='carnot';cfg.hp.max_heat_output_MW=spec.capacity_MW;
cfg.hp.cop_min=spec.cop_min;cfg.hp.cop_max=spec.cop_max;cfg.hp.part_load_penalty=0;
% Columns: vector index, TL K, TH K, paper-derived heating COP, mapped etaH,
% same-eta COP,Q,W,Qev; mapped COP,Q,W,Qev; proxy COP,Q,W,Qev.
matrix=zeros(size(spec.vectors,1),17);checks=struct('name',{},'passed',{});
for k=1:size(spec.vectors,1)
    v=spec.vectors(k,:);TL=v(1)-v(4)+273.15;TH=v(2)+v(4)+273.15;
    EER=v(3)*TL/(TH-TL);COP=1+EER;etaH=COP*(TH-TL)/TH;
    cfg.hp.carnot_efficiency=v(3);
    a=dchr.components.heat_pump_step_v40(v(5),v(1)-v(4),v(2)+v(4),v(6),cfg);
    cfg.hp.carnot_efficiency=etaH;
    b=dchr.components.heat_pump_step_v40(v(5),v(1)-v(4),v(2)+v(4),v(6),cfg);
    c=dchr.components.heat_pump_step_v40(v(5),v(1),v(2),v(6),cfg);
    matrix(k,:)=[k TL TH COP etaH packed(a) packed(b) packed(c)];
    record(sprintf('mapped_COP_%d',k),abs(b.cop_operating-COP)<=2e-13*COP);
    record(sprintf('factor_difference_%d',k),abs(COP-a.cop_operating-(1-v(3)))<2e-13*COP);
    for hp={a,b,c}
        z=hp{1};record(sprintf('flow_%d_%d',k,numel(checks)), ...
            z.available&&all([z.heat_output_MW z.electric_MW z.source_used_MW]>=0)&& ...
            z.source_used_MW<=v(5)+1e-12&&z.heat_output_MW<=v(6)+1e-12&& ...
            abs(z.heat_output_MW-z.electric_MW-z.source_used_MW)<1e-11);
    end
end
writejson(fullfile(folder,'component_vectors_v43.json'),struct('matrix',matrix));
save(fullfile(folder,'component_vectors_v43.mat'),'matrix');
mdl='DCHR_Dispatch_Stateflow_v42';load_system(fullfile(here,[mdl '.slx']));
cleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
assert(license('test','Stateflow'),'Stateflow license unavailable');
z=spec.stateflow_case;TL=z.source_C-z.pinch_K+273.15;TH=z.sink_C+z.pinch_K+273.15;
etaH=(TH-TL+z.eta_cooling*TL)/TH;
ids={'same_factor_refrigerant','converted_refrigerant','converted_water_proxy','converted_with_assumed_partload'};
items=[];
for j=1:4
    sc=z.source_C-z.pinch_K;tc=z.sink_C+z.pinch_K;eta=etaH;penalty=0;
    if j==1,eta=z.eta_cooling;end
    if j==3,sc=z.source_C;tc=z.sink_C;end
    if j==4,penalty=.08;end
    p=[1 10 0 0 1 1 0 5 .2 20 0];h=[100 eta 1.000001 1000 penalty 0 4 0 0];
    x=[z.source_MW sc tc z.demand_MW 45];
    s=Simulink.SimulationInput(mdl);
    names={'dt','stop','input','p','h','E0','c','m0'};
    values={1,0,[0 x],p,h,5,[8 0 0 64],[1;0;0;0]};
    for n=1:numel(names),s=s.setVariable(['dchr_' names{n} '_v42'],values{n},'Workspace',mdl);end
    result=sim(s.setModelParameter('CaptureErrors','on'));
    id=ids{j};save(fullfile(folder,[id '_simulation.mat']),'result');
    record([id '_actual_execution'],isempty(result.ErrorMessage));
    assert(isempty(result.ErrorMessage),'DCHR:v43:SimulationFailure','%s',result.ErrorMessage);
    dispatch=samples(result.dispatch_trace_v42,25);raw=samples(result.segment_trace_v42,1792);
    bridge=dchr_stateflow_hp_v42(x,5,p,h,1);
    item=struct('id',id,'input',x,'p',p,'h',h,'dispatch',dispatch,'bridge',bridge', ...
        'segments',reshape(raw(1,:),28,64)','error_message',result.ErrorMessage);
    if isempty(items),items=item;else,items(end+1)=item;end %#ok<AGROW>
    record([id '_unchanged_energy'],abs(dispatch(8)-5)<1e-12);
    record([id '_first_law'],abs(dispatch(13))<1e-11);
    record([id '_bridge'],max(abs(dispatch(19:21)-bridge(2:4)'))<1e-11);
    fprintf('FOCUSED_STATEFLOW=%s HP_MW=%.16g electric_MW=%.16g unmet_MW=%.16g mode=%d\n', ...
        id,dispatch(19),dispatch(20),dispatch(6),dispatch(1));
end
record('same_factor_meets_demand',items(1).dispatch(6)==0);
record('converted_factor_exposes_unmet',items(2).dispatch(6)>0);
writejson(fullfile(folder,'stateflow_cases_v43.json'),items);
writejson(fullfile(folder,'assertions_v43.json'),checks);
summary=struct('version','0.43','model_version','0.42','new_model',false, ...
    'fixture_class','ENGINEERING_SYNTHETIC_NOT_MEASURED', ...
    'component_vectors',size(matrix,1),'component_calls',3*size(matrix,1), ...
    'fresh_saved_model_scenarios',numel(items),'harness_passed',sum([checks.passed]), ...
    'harness_failed',sum(~[checks.passed]),'matlab_version',version, ...
    'stateflow_license_test',license('test','Stateflow'),'product_versions',ver);
writejson(fullfile(folder,'summary_v43.json'),summary);disp(summary);
assert(all([checks.passed]),'DCHR:v43:CheckFailed','See retained evidence.');
    function record(name,ok)
        checks(end+1)=struct('name',name,'passed',logical(ok));
    end
end
function v=packed(hp)
v=[hp.cop_operating hp.heat_output_MW hp.electric_MW hp.source_used_MW];
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;
if ismatrix(raw)&&isequal(size(raw),[n width]),v=raw;
elseif numel(raw)==n*width,v=reshape(raw,width,n)';else,error('Unexpected trace dimensions.');end
end
function writejson(path,v)
assert(~isfile(path));fid=fopen(path,'w');assert(fid>0);clean=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(v,PrettyPrint=true));
end
