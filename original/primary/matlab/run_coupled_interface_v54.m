function run_coupled_interface_v54(folder)
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'matlab'),fullfile(root,'matlab','simulink'));
assert(isfolder(folder)&&~isfile(fullfile(folder,'report.json')));
Simulink.fileGenControl('set','CacheFolder',fullfile(folder,'local_build','cache'), ...
    'CodeGenFolder',fullfile(folder,'local_build','codegen'),'createDir',true);
spec=jsondecode(fileread(fullfile(folder,'spec.json')));base=spec.boundary;p=spec.policy;
checks=struct('name',{},'passed',{});vectors=struct('spec',{},'policy',{},'energy',{},'request',{},'boundary',{});
for T=[20 40 45 47 60 68 70]
for hot=[.6 4]
for source=[0 .8]
for request=[0 1 8]
for approach=[0 2]
    s=base;s.hot_capacity_MW_per_K=hot;s.source_capacity_MW_per_K=source;s.charge_approach_K=approach;
    E=p.heat_capacity_MWh_per_K*(T-p.ambient_C);b=dchr.components.coupled_temperature_boundary_v54(s,p,E,request);
    vectors(end+1)=struct('spec',s,'policy',p,'energy',E,'request',request,'boundary',b); %#ok<AGROW>
    record('instantaneous_balance',abs(b.heat_MW-b.compressor_MW-b.source_MW)<1e-12);
    record('finite_flow',b.hot_capacity_required_MW_per_K<=hot+1e-12&& ...
        b.source_capacity_required_MW_per_K<=source+1e-12);
    record('zero_glide_no_heat',b.hot_glide_K>0||b.heat_MW==0);
end
end
end
end
end
analytic=struct('spec',{},'policy',{},'request',{},'result',{});
b=dchr.components.coupled_temperature_boundary_v54(base,p,p.initial_energy_MWh,8);
critical=p.eta_charge*b.source_budget_MW/(base.cooling_factor*(b.evaporator_C+273.15)*p.heat_capacity_MWh_per_K);
for rate=[0 .05 critical critical-1e-10 critical+1e-10 1]
for dt=[.005 .05]
    pp=p;pp.loss_rate_per_h=rate;
    z=dchr.components.source_affine_charge_step_v54(base,pp,p.initial_energy_MWh,dt,8);
    analytic(end+1)=struct('spec',base,'policy',pp,'request',8,'result',z); %#ok<AGROW>
    record('analytic_first_law',abs(z.first_law_residual_MWh)<1e-11);
    record('analytic_ports',all([z.heat_MWh z.compressor_MWh z.source_MWh z.standing_loss_MWh z.charge_loss_MWh]>=0));
end
end
faults=struct('id',{},'identifier',{},'rejected',{});
s=base;s.source_glide_K=0;reject('glide',@()dchr.components.coupled_temperature_boundary_v54(s,p,1,8));
s=base;s.cooling_factor=1.1;reject('efficiency',@()dchr.components.coupled_temperature_boundary_v54(s,p,1,8));
s=base;s.hot_capacity_MW_per_K=-1;reject('negative_flow',@()dchr.components.coupled_temperature_boundary_v54(s,p,1,8));
s=base;s.evaporator_approach_K=400;reject('absolute_temperature',@()dchr.components.coupled_temperature_boundary_v54(s,p,1,8));
s=base;s.source_capacity_MW_per_K=realmax;reject('overflow',@()dchr.components.coupled_temperature_boundary_v54(s,p,1,8));
reject('negative_energy',@()dchr.components.coupled_temperature_boundary_v54(base,p,-1,8));
reject('over_capacity',@()dchr.components.coupled_temperature_boundary_v54(base,p,11,8));
reject('nonfinite_request',@()dchr.components.coupled_temperature_boundary_v54(base,p,1,NaN));
reject('floor_branch',@()dchr.components.source_affine_charge_step_v54(base,p,1,.05,8));
reject('request_limiter',@()dchr.components.source_affine_charge_step_v54(base,p,9.6,.05,1));
reject('capacity_event',@()dchr.components.source_affine_charge_step_v54(base,p,9.6,1,8));
s=base;s.hot_capacity_MW_per_K=.6;reject('hot_limiter',@()dchr.components.source_affine_charge_step_v54(s,p,9.6,.05,8));
pp=p;pp.eta_charge=1.1;reject('charge_efficiency',@()dchr.components.source_affine_charge_step_v54(base,pp,9.6,.05,8));
reject('zero_span',@()dchr.components.source_affine_charge_step_v54(base,p,9.6,0,8));
mdl='DCHR_Dispatch_Stateflow_v52';load_system(fullfile(root,'matlab','simulink',[mdl '.slx']));
cleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
rt=sfroot;charts=[rt.find('-isa','Stateflow.Chart','Path',[mdl '/Execute_Segments/Thermal_Dispatch']); ...
    rt.find('-isa','Stateflow.Chart','Path',[mdl '/Execute_Segments/HP_Supervisor'])];
metadata=struct('matlab_version',version,'stateflow_license_test',license('test','Stateflow'), ...
    'stateflow_version',ver('stateflow'),'chart_count',numel(charts),'simulation_mode','normal');
record('actual_charts',metadata.stateflow_license_test==1&&numel(charts)==2);
% Actual unsupported cold-tank interface, preserving the strict saved gate.
[r,a]=execute('cold_tank_rejection',base,p,1,.05,[1;0;0;0]);
record('cold_tank_runtime_rejected',~isempty(r.ErrorMessage)&&contains(r.ErrorMessage,'Condenser must support tank maximum'));
rejection=struct('error_message',r.ErrorMessage,'inputs',a,'simulation_mat','cold_tank_rejection_simulation.mat');
reference=dchr.components.source_affine_charge_step_v54(base,p,p.initial_energy_MWh,p.dt_h,8);
experiments=struct('chunks',{},'initial_energy_MWh',{},'end_energy_MWh',{},'heat_MWh',{}, ...
    'compressor_MWh',{},'source_MWh',{},'standing_loss_MWh',{},'charge_loss_MWh',{},'runs',{});
matExports=struct('id',{},'inputs',{},'dispatch',{},'raw_segments',{},'raw_plans',{},'clock_start',{},'clock_end',{});
for count=[1 2 4 8]
    E=p.initial_energy_MWh;clock=[1;0;0;0];tot=zeros(5,1);
    runs=struct('id',{},'inputs',{},'dispatch',{},'raw_segments',{},'raw_plans',{},'clock_start',{},'clock_end',{});
    for j=1:count
        id=sprintf('sampled_%d_%d',count,j);dt=p.dt_h/count;
        [r,a]=execute(id,base,p,E,dt,clock);
        record([id '_executed'],isempty(r.ErrorMessage));assert(isempty(r.ErrorMessage),r.ErrorMessage);
        d=samples(r.dispatch_trace_v52,25);raw=samples(r.segment_trace_v52,1792);plan=samples(r.plan_trace_v52,1472);
        zs=reshape(raw,28,64)';qp=reshape(plan,23,64)';
        record([id '_handoff'],all(zs(1:63,5)==zs(2:64,4))&&all(zs(:,5)==qp(:,23)));
        positive=zs(:,2)>0;
        record([id '_padding'],all(zs(~positive,4)==zs(~positive,5))&&all(zs(~positive,6:14)==0,'all')&&all(zs(~positive,17:21)==0,'all'));
        record([id '_mode'],d(1)==2&&all(zs(positive,1)==2));
        tot=tot+[sum(zs(:,11).*zs(:,2));sum(zs(:,12).*zs(:,2));sum(zs(:,13).*zs(:,2));sum(zs(:,17));sum(zs(:,18))];
        runs(end+1)=struct('id',id,'inputs',a,'dispatch',d,'raw_segments',raw,'raw_plans',plan, ...
            'clock_start',samples(r.clock_start_trace_v52,4),'clock_end',samples(r.clock_end_trace_v52,4)); %#ok<AGROW>
        E=d(8);clock=runs(end).clock_end';
        reopened=load(fullfile(folder,[id '_simulation.mat']));
        record([id '_MAT_binding'],isequaln(raw,samples(reopened.r.segment_trace_v52,1792))&& ...
            isequaln(plan,samples(reopened.r.plan_trace_v52,1472))&&isequaln(d,samples(reopened.r.dispatch_trace_v52,25))&&isequaln(a,reopened.a));
        matExports(end+1)=struct('id',id,'inputs',reopened.a,'dispatch',samples(reopened.r.dispatch_trace_v52,25), ...
            'raw_segments',samples(reopened.r.segment_trace_v52,1792),'raw_plans',samples(reopened.r.plan_trace_v52,1472), ...
            'clock_start',samples(reopened.r.clock_start_trace_v52,4),'clock_end',samples(reopened.r.clock_end_trace_v52,4)); %#ok<AGROW>
    end
    experiments(end+1)=struct('chunks',count,'initial_energy_MWh',p.initial_energy_MWh,'end_energy_MWh',E, ...
        'heat_MWh',tot(1),'compressor_MWh',tot(2),'source_MWh',tot(3),'standing_loss_MWh',tot(4),'charge_loss_MWh',tot(5),'runs',runs); %#ok<AGROW>
    fprintf('COUPLED_V54 chunks=%d E=%.17g E_error=%.9g W_error=%.9g\n',count,E,E-reference.end_energy_MWh,tot(2)-reference.compressor_MWh);
end
errors=abs([experiments.end_energy_MWh]-reference.end_energy_MWh);
record('held_temperature_discrepancy',errors(1)>1e-6);
record('refinement_convergence',all(diff(errors)<0)&&errors(end)<errors(1)/4);
report=struct('version','0.54','model_version','0.52','new_model',false,'metadata',metadata, ...
    'vectors',vectors,'analytic',analytic,'faults',faults,'rejection',rejection,'reference',reference, ...
    'experiments',experiments,'assertions',checks,'summary',struct('passed',sum([checks.passed]),'failed',sum(~[checks.passed])));
save(fullfile(folder,'coupled_interface_v54.mat'),'report','-v7.3');writejson('report.json',report);
reopened=load(fullfile(folder,'coupled_interface_v54.mat'));assert(isequaln(report,reopened.report));writejson('mat_reopen.json',reopened.report);
writejson('original_simulation_reopen.json',matExports);
fprintf('COUPLED_INTERFACE_V54 PASS=%d FAIL=%d\n',report.summary.passed,report.summary.failed);
assert(all([checks.passed]),'DCHR:v54:AcceptanceFailure','Inspect retained evidence.');
    function record(name,ok),checks(end+1)=struct('name',name,'passed',logical(ok));end
    function reject(id,fn)
        identifier='';try,fn();catch e,identifier=e.identifier;end
        ok=startsWith(identifier,'DCHR:v54:');record(['domain_' id],ok);
        faults(end+1)=struct('id',id,'identifier',identifier,'rejected',ok);
    end
    function [r,a]=execute(id,s,pp,E,dt,clock)
        b=dchr.components.coupled_temperature_boundary_v54(s,pp,E,8);
        pv=[dt pp.heat_capacity_MWh_per_K*(s.tank_max_C-pp.ambient_C) pp.charge_limit_MW ...
            pp.discharge_limit_MW pp.eta_charge pp.eta_discharge pp.loss_rate_per_h ...
            pp.heat_capacity_MWh_per_K*b.cutoff_C-pp.heat_capacity_MWh_per_K*pp.ambient_C ...
            pp.heat_capacity_MWh_per_K pp.ambient_C pp.boiler_limit_MW];
        hv=[min(s.hp_capacity_MW,b.hot_budget_MW) b.heating_factor 1.1 b.cop_compressor+2 0 0 0 0 0];
        cv=[pp.heat_capacity_MWh_per_K*(pp.restart_C-pp.ambient_C) pp.min_on_h pp.min_off_h 64];
        xv=[b.source_budget_MW b.evaporator_C b.condenser_C 0 s.delivery_C];
        a=struct('p',pv,'h',hv,'c',cv,'x',xv,'E0',E,'m0',clock,'boundary',b,'dt_h',dt);
        si=Simulink.SimulationInput(mdl);names={'dt','stop','input','p','h','E0','c','m0'};
        values={dt,0,[0 xv],pv,hv,E,cv,clock};
        for jj=1:numel(names),si=si.setVariable(['dchr_' names{jj} '_v52'],values{jj},'Workspace',mdl);end
        r=sim(si.setModelParameter('CaptureErrors','on'));save(fullfile(folder,[id '_simulation.mat']),'r','a','-v7.3');
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
elseif numel(raw)==n*width,v=reshape(raw,width,n)';else,error('DCHR:v54:TraceShape','Unexpected trace shape.');end
end
