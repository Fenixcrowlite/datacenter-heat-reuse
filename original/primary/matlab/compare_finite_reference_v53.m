function compare_finite_reference_v53(folder)
% Six representative physical-output comparisons against verified v30 MATLAB.
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'matlab'));
r=load(fullfile(folder,'finite_interface_v53.mat'),'report');items=struct('id',{},'reference',{},'actual',{},'columns',{},'max_delta',{},'passed',{});
for k=1:6
    item=r.report.cases(k);a=item.adapter;p=a.p;h=a.h;
    cfg=default_config_v2();cfg.sim.dt_h=p(1);cfg.backup.max_heat_MW=p(11);
    cfg.storage.heat_capacity_MWh_per_K=p(9);cfg.storage.ambient_C=p(10);
    cfg.storage.max_temperature_C=p(10)+p(2)/p(9);cfg.storage.delivery_cutoff_C=p(10)+p(8)/p(9);
    cfg.storage.initial_temperature_C=p(10)+a.initial_energy_MWh/p(9);
    cfg.storage.charge_limit_MW=p(3);cfg.storage.discharge_limit_MW=p(4);
    cfg.storage.eta_charge=p(5);cfg.storage.eta_discharge=p(6);cfg.storage.continuous_loss_rate_per_h=p(7);
    cfg.hp.max_heat_output_MW=h(1);cfg.hp.carnot_efficiency=h(2);cfg.hp.cop_min=h(3);
    cfg.hp.cop_max=h(4);cfg.hp.part_load_penalty=h(5);cfg.model.hp_backend='carnot';
    input=array2table(a.inputs,'VariableNames',{'Source_Heat_MW','Source_C','Sink_C','Heat_Demand_MW','Delivery_C'});
    ref=dchr.simulate_dispatch_v30(cfg,input);reference=table2array(ref(:,1:25));
    columns=[1:21 23:25];delta=abs(reference(:,columns)-item.dispatch(:,columns));
    nanmatch=isequal(isnan(reference(:,columns)),isnan(item.dispatch(:,columns)));delta(isnan(delta))=0;
    ok=nanmatch&&max(delta,[],'all')<1e-10;
    items(end+1)=struct('id',item.id,'reference',reference,'actual',item.dispatch, ...
        'columns',columns,'max_delta',max(delta,[],'all'),'passed',ok); %#ok<AGROW>
end
report=struct('reference','dchr.simulate_dispatch_v30','excluded_column',22, ...
    'exclusion_reason','Attempted request diagnostic differs when HP latch is OFF; every physical column retained.', ...
    'items',items,'passed',sum([items.passed]),'failed',sum(~[items.passed]));
assert(~isfile(fullfile(folder,'reference_v53.mat')));save(fullfile(folder,'reference_v53.mat'),'report','-v7.3');
writejson(fullfile(folder,'reference_v53.json'),report);reopen=load(fullfile(folder,'reference_v53.mat'),'report');
assert(isequaln(report,reopen.report));writejson(fullfile(folder,'reference_mat_reopen.json'),reopen.report);
fprintf('FINITE_REFERENCE_V53 PASS=%d FAIL=%d\n',report.passed,report.failed);
assert(all([items.passed]),'DCHR:v53:ReferenceFailure','Physical reference mismatch.');
end
function writejson(path,value)
assert(~isfile(path));fid=fopen(path,'w');assert(fid>0);cleanup=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(value,PrettyPrint=true));
end
