function run_branch_guard_v55(folder)
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'matlab'),fullfile(root,'matlab','simulink'));
assert(isfolder(folder)&&~isfile(fullfile(folder,'report.json')));
Simulink.fileGenControl('set','CacheFolder',fullfile(folder,'local_build','cache'), ...
    'CodeGenFolder',fullfile(folder,'local_build','codegen'),'createDir',true);
spec=jsondecode(fileread(fullfile(folder,'spec.json')));checks=struct('name',{},'passed',{});
vectors=struct('id',{},'s',{},'p',{},'E',{},'request',{},'legacy_branch',{},'certificate',{},'accepted',{},'identifier',{});
for j=1:numel(spec.vectors)
    v=spec.vectors(j);c=dchr.components.coupled_branch_certificate_v55(v.s,v.p,v.E,v.request);
    identifier='';accepted=false;
    try,b=dchr.components.coupled_temperature_boundary_v55(v.s,v.p,v.E,v.request);accepted=true;
        record([v.id '_branch_matches'],b.tank_branch==strcmp(c.branch,'TANK'));
    catch e,identifier=e.identifier;end
    record([v.id '_gate'],accepted==c.resolved&& ...
        (accepted||strcmp(identifier,'DCHR:v55:UnresolvedBranch')));
    vectors(end+1)=struct('id',v.id,'s',v.s,'p',v.p,'E',v.E,'request',v.request, ...
        'legacy_branch',v.legacy_branch,'certificate',c,'accepted',accepted,'identifier',identifier); %#ok<AGROW>
end
known=find(strcmp({vectors.id},'kink_0.0_0'));assert(numel(known)==1);
record('original_exact_binary_kink_rejected',~vectors(known).accepted&& ...
    strcmp(vectors(known).identifier,'DCHR:v55:UnresolvedBranch'));
faults=struct('id',{},'identifier',{},'rejected',{});
s=spec.boundary;p=spec.policy;
bad=p;bad.heat_capacity_MWh_per_K=0;reject('zero_C',@()dchr.components.coupled_temperature_boundary_v55(s,bad,5,8));
bad=p;bad.heat_capacity_MWh_per_K=NaN;reject('NaN_C',@()dchr.components.coupled_temperature_boundary_v55(s,bad,5,8));
reject('negative_E',@()dchr.components.coupled_temperature_boundary_v55(s,p,-1,8));
reject('infinite_E',@()dchr.components.coupled_temperature_boundary_v55(s,p,Inf,8));
reject('NaN_request',@()dchr.components.coupled_temperature_boundary_v55(s,p,5,NaN));
bad=s;bad.source_capacity_MW_per_K=realmax;reject('overflow',@()dchr.components.coupled_temperature_boundary_v55(bad,p,5,8));
mdl='DCHR_Dispatch_Stateflow_v52';load_system(fullfile(root,'matlab','simulink',[mdl '.slx']));
cleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
rt=sfroot;charts=[rt.find('-isa','Stateflow.Chart','Path',[mdl '/Execute_Segments/Thermal_Dispatch']); ...
    rt.find('-isa','Stateflow.Chart','Path',[mdl '/Execute_Segments/HP_Supervisor'])];
metadata=struct('matlab_version',version,'stateflow_license_test',license('test','Stateflow'), ...
    'stateflow_version',ver('stateflow'),'chart_count',numel(charts),'simulation_mode','normal');
record('actual_charts',metadata.stateflow_license_test==1&&numel(charts)==2);
runs=struct('id',{},'inputs',{},'dispatch',{},'raw_segments',{},'raw_plans',{},'clock_start',{},'clock_end',{});
originals=runs;
for hot=[4 .6]
    ss=s;ss.hot_capacity_MW_per_K=hot;id=sprintf('resolved_hot_%g',hot);
    b=dchr.components.coupled_temperature_boundary_v55(ss,p,9.6,8);dt=.005;
    pv=[dt p.heat_capacity_MWh_per_K*(ss.tank_max_C-p.ambient_C) p.charge_limit_MW ...
        p.discharge_limit_MW p.eta_charge p.eta_discharge p.loss_rate_per_h ...
        p.heat_capacity_MWh_per_K*(b.cutoff_C-p.ambient_C) p.heat_capacity_MWh_per_K p.ambient_C p.boiler_limit_MW];
    hv=[min(ss.hp_capacity_MW,b.hot_budget_MW) b.heating_factor 1.1 b.cop_compressor+2 0 0 0 0 0];
    cv=[p.heat_capacity_MWh_per_K*(p.restart_C-p.ambient_C) p.min_on_h p.min_off_h 64];
    xv=[b.source_budget_MW b.evaporator_C b.condenser_C 0 ss.delivery_C];clock=[1;0;0;0];
    a=struct('p',pv,'h',hv,'c',cv,'x',xv,'E0',9.6,'m0',clock,'boundary',b,'dt_h',dt);
    si=Simulink.SimulationInput(mdl);names={'dt','stop','input','p','h','E0','c','m0'};
    values={dt,0,[0 xv],pv,hv,9.6,cv,clock};
    for jj=1:numel(names),si=si.setVariable(['dchr_' names{jj} '_v52'],values{jj},'Workspace',mdl);end
    r=sim(si.setModelParameter('CaptureErrors','on'));save(fullfile(folder,[id '_simulation.mat']),'r','a','-v7.3');
    record([id '_actual_execution'],isempty(r.ErrorMessage));assert(isempty(r.ErrorMessage),r.ErrorMessage);
    item=struct('id',id,'inputs',a,'dispatch',samples(r.dispatch_trace_v52,25), ...
        'raw_segments',samples(r.segment_trace_v52,1792),'raw_plans',samples(r.plan_trace_v52,1472), ...
        'clock_start',samples(r.clock_start_trace_v52,4),'clock_end',samples(r.clock_end_trace_v52,4));
    z=reshape(item.raw_segments,28,64)';q=reshape(item.raw_plans,23,64)';positive=z(:,2)>0;
    record([id '_handoff'],all(z(1:63,5)==z(2:64,4))&&all(z(:,5)==q(:,23)));
    record([id '_padding'],all(z(~positive,4)==z(~positive,5))&&all(z(~positive,6:14)==0,'all')&&all(z(~positive,17:21)==0,'all'));
    record([id '_mode'],item.dispatch(1)==2&&all(z(positive,1)==2));
    runs(end+1)=item; %#ok<AGROW>
    reopened=load(fullfile(folder,[id '_simulation.mat']));
    record([id '_MAT_binding'],isequaln(a,reopened.a)&&isequaln(r,reopened.r));
    item.inputs=reopened.a;item.dispatch=samples(reopened.r.dispatch_trace_v52,25);
    item.raw_segments=samples(reopened.r.segment_trace_v52,1792);item.raw_plans=samples(reopened.r.plan_trace_v52,1472);
    item.clock_start=samples(reopened.r.clock_start_trace_v52,4);item.clock_end=samples(reopened.r.clock_end_trace_v52,4);
    originals(end+1)=item; %#ok<AGROW>
end
report=struct('version','0.55','model_version','0.52','new_model',false,'metadata',metadata, ...
    'vectors',vectors,'faults',faults,'runs',runs,'assertions',checks, ...
    'summary',struct('passed',sum([checks.passed]),'failed',sum(~[checks.passed]), ...
    'accepted',sum([vectors.accepted]),'unresolved_rejected',sum(~[vectors.accepted])));
save(fullfile(folder,'branch_guard_v55.mat'),'report','-v7.3');writejson('report.json',report);
reopened=load(fullfile(folder,'branch_guard_v55.mat'));assert(isequaln(report,reopened.report));writejson('mat_reopen.json',reopened.report);
writejson('original_simulation_reopen.json',originals);
fprintf('BRANCH_GUARD_V55 PASS=%d FAIL=%d ACCEPT=%d REJECT_UNRESOLVED=%d\n',report.summary.passed,report.summary.failed,report.summary.accepted,report.summary.unresolved_rejected);
assert(all([checks.passed]),'DCHR:v55:AcceptanceFailure','Inspect retained evidence.');
    function record(name,ok),checks(end+1)=struct('name',name,'passed',logical(ok));end
    function reject(id,fn)
        identifier='';try,fn();catch e,identifier=e.identifier;end
        ok=startsWith(identifier,'DCHR:v54:')||startsWith(identifier,'DCHR:v55:');record(['domain_' id],ok);
        faults(end+1)=struct('id',id,'identifier',identifier,'rejected',ok);
    end
    function writejson(name,value)
        path=fullfile(folder,name);assert(~isfile(path));fid=fopen(path,'w');assert(fid>0);
        closefile=onCleanup(@()fclose(fid)); %#ok<NASGU>
        fprintf(fid,'%s\n',jsonencode(value,PrettyPrint=true));
    end
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;
if ismatrix(raw)&&isequal(size(raw),[n width]),v=raw;
elseif numel(raw)==n*width,v=reshape(raw,width,n)';else,error('DCHR:v55:TraceShape','Unexpected trace shape.');end
end
