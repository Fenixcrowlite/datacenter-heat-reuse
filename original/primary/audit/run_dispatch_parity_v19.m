function run_dispatch_parity_v19()
root=fileparts(fileparts(mfilename('fullpath')));
ref=fullfile(root,'audit','dispatch_reference_vectors_v18.csv');
addpath(fullfile(root,'matlab'));
out=fullfile(root,'results','dispatch_parity_v19_20261009');
assert(~isfolder(out),'Existing evidence');
mkdir(out);
v=readtable(ref,'TextType','string');
ids=unique(v.scenario_id,'stable');a=table();
for j=1:numel(ids)
 r=v(v.scenario_id==ids(j),:); f=r(1,:);
 cfg=default_config_v2();cfg.sim.dt_h=f.dt_h;
 cfg.storage.capacity_MWh=f.storage_capacity_MWh;
 cfg.storage.charge_limit_MW=f.charge_limit_MW;
 cfg.storage.discharge_limit_MW=f.discharge_limit_MW;
 cfg.storage.eta_charge=f.eta_charge;
 cfg.storage.eta_discharge=f.eta_discharge;
 cfg.storage.loss_fraction_per_h=f.loss_fraction_per_h;
 cfg.storage.initial_soc=f.expected_Storage_E_Start_MWh/f.storage_capacity_MWh;
 cfg.backup.max_heat_MW=f.boiler_capacity_MW;
 cfg.hp.max_heat_output_MW=f.hp_capacity_MW;
 cfg.hp.carnot_efficiency=f.carnot_efficiency;
 cfg.hp.cop_min=f.cop_min;cfg.hp.cop_max=f.cop_max;
 cfg.hp.part_load_penalty=f.part_load_penalty;
 cfg.model.hp_backend=f.backend;
 cfg.hp.poly_c0=f.poly_c0;cfg.hp.poly_c1=f.poly_c1;cfg.hp.poly_c2=f.poly_c2;
 o=dchr.simulate_dispatch_v16(cfg,r(:,{'Source_Heat_MW','Source_C','Sink_C','Heat_Demand_MW'}));
 a=[a;[r(:,{'scenario_id','step'}),o]];
end
writetable(a,fullfile(out,'matlab_trace_v19.csv'));
fields=v.Properties.VariableNames(startsWith(v.Properties.VariableNames,'expected_'));
names=strings(numel(fields),1);max_delta=zeros(numel(fields),1);
passed=false(numel(fields),1);
for k=1:numel(fields)
 f=extractAfter(string(fields{k}),9);names(k)=f;
 expected=double(v.(fields{k}));observed=double(a.(f));
 same_nan=isnan(expected)&isnan(observed);
 finite=isfinite(expected)&isfinite(observed);
 delta=abs(observed(finite)-expected(finite));
 max_delta(k)=max([0;delta]);
 passed(k)=all(same_nan|finite)&&all(delta<=1e-9+1e-11*abs(expected(finite)));
end
report=table(names,passed,max_delta);
writetable(report,fullfile(out,'field_comparison_v19.csv'));
summary=struct('version','0.19','scenarios',numel(ids),'intervals',height(v),'fields',numel(fields),'passed',sum(passed),'failed',sum(~passed),'max_abs_delta',max(max_delta));
fid=fopen(fullfile(out,'parity_summary_v19.json'),'w');
fprintf(fid,'%s\n',jsonencode(summary,PrettyPrint=true));fclose(fid);
disp(summary);
if any(~passed), error('Cross-language mismatch'); end
end
