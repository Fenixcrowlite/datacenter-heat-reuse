function run_annual_sensitivity_v50(folder)
% Nine independent annual executions of the preserved actual saved-v42 model.
root=fileparts(fileparts(mfilename('fullpath')));here=fullfile(root,'matlab','simulink');
addpath(fullfile(root,'matlab'),here);spec=jsondecode(fileread(fullfile(folder,'spec.json')));
assert(~isfile(fullfile(folder,'annual_sensitivity_v50.mat')),'Preserve existing evidence.');
checks=struct('name',{},'passed',{});cfg=default_config_v2();cfg.sim.hours=8760;cfg.backup.max_heat_MW=2;
input=dchr.make_inputs(cfg);cases=spec.scenarios;
% Common comparison is recomputed; never relabel a MATLAB trajectory Stateflow.
pairedCfg=cfg;pairedCfg.dh.supply_min_C=85;pairedCfg.dh.supply_max_C=85;
paired=dchr.simulate_system_v48(pairedCfg,input);pairedPorts=dchr.adapt_dispatch_energy_v46(paired,'explicit_actual_v45');
pairedReport=dchr.compute_service_comparison_v46(pairedCfg,pairedPorts);
writetable(paired,fullfile(folder,'paired_loss_first_v48.csv'));writetable(pairedPorts,fullfile(folder,'paired_loss_first_ports.csv'));
save(fullfile(folder,'paired_loss_first_v48.mat'),'paired','pairedPorts','pairedCfg','pairedReport');
work=fullfile(folder,'local_build');mkdir(work);
Simulink.fileGenControl('set','CacheFolder',fullfile(work,'cache'),'CodeGenFolder',fullfile(work,'codegen'),'createDir',true);
assert(license('test','Stateflow'),'Stateflow license unavailable');mdl='DCHR_Dispatch_Stateflow_v42';
load_system(fullfile(here,[mdl '.slx']));cleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
rt=sfroot;ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Execute_Segments/Thermal_Dispatch']);
metadata=struct('matlab_version',version,'products',ver,'stateflow_version',ver('Stateflow'), ...
    'stateflow_license_test',license('test','Stateflow'),'simulation_mode',get_param(mdl,'SimulationMode'), ...
    'thermal_states',{get(ch.find('-isa','Stateflow.State'),'Name')});
items=[];matrix=[];baselineDispatch=[];
for j=1:numel(cases)
    cc=cases(j);a=dchr.adapt_annual_stateflow_v49(cfg,input,cc.policy);
    save(fullfile(folder,[cc.id '_adapter.mat']),'a');writetable(a.preflight,fullfile(folder,[cc.id '_preflight.csv']));
    record([cc.id '_static_domain'],a.admissible&&height(a.preflight)==8760);
    if j==1,sharedInputs=a.inputs;writematrix(sharedInputs,fullfile(folder,'annual_inputs.csv'));
    else,record([cc.id '_matched_input'],isequal(a.inputs,sharedInputs));end
    item=struct('id',cc.id,'changed_coordinate',cc.changed_coordinate,'policy',cc.policy, ...
        'p',a.p,'h',a.h,'c',a.c,'initial_energy_MWh',a.initial_energy_MWh, ...
        'initial_clock',a.initial_clock,'intervals',0,'positive_segments',0,'elapsed_seconds',0, ...
        'error_message','','execution_success',false,'report',struct(),'terminal_inventory_MWh',NaN);
    if a.admissible
        p=a.p;h=a.h;n=size(a.inputs,1);
        s=Simulink.SimulationInput(mdl);names={'dt','stop','input','p','h','E0','c','m0'};
        values={p(1),(n-1)*p(1),[(0:n-1)'*p(1) a.inputs],p,h,a.initial_energy_MWh,a.c,a.initial_clock};
        for k=1:numel(names),s=s.setVariable(['dchr_' names{k} '_v42'],values{k},'Workspace',mdl);end
        timer=tic;
        try
            result=sim(s.setModelParameter('CaptureErrors','on'));
            save(fullfile(folder,[cc.id '_simulation.mat']),'result','-v7.3');
            item.error_message=result.ErrorMessage;
            if isempty(result.ErrorMessage)
                dispatch=samples(result.dispatch_trace_v42,25);raw=samples(result.segment_trace_v42,1792);
                chunks=cell(n,1);
                for i=1:n,z=reshape(raw(i,:),28,64)';pos=find(z(:,2)>0);chunks{i}=[repmat(i,numel(pos),1) pos z(pos,:)];end
                segments=vertcat(chunks{:});ports=array2table(dispatch(:,[18 2 3 4 5 6 19 20]),'VariableNames',spec.port_columns);
                ports=dchr.adapt_dispatch_energy_v46(ports,'explicit_actual_v45');m=dchr.compute_service_comparison_v46(cfg,ports);
                item.intervals=size(dispatch,1);item.positive_segments=size(segments,1);item.report=m;
                item.terminal_inventory_MWh=dispatch(end,8);item.execution_success=true;
                record([cc.id '_samples'],size(dispatch,1)==n);
                record([cc.id '_first_law'],max(abs(dispatch(:,13)))<1e-9);
                record([cc.id '_inventory'],all(dispatch(:,8)>=0&dispatch(:,8)<=p(2)));
                record([cc.id '_service'],abs(m.energy.heat_demand_MWh-m.energy.total_delivered_MWh-m.energy.unmet_heat_MWh)<1e-6);
                record([cc.id '_hours'],m.energy.reported_period_h==8760);
                if j==1
                    baselineDispatch=dispatch;old=readmatrix(fullfile(root,spec.baseline_evidence,'annual_8760h_dispatch.csv'));
                    delta=dispatch-old;delta(isnan(delta))=0;
                    record('baseline_v49_reproduced',isequal(isnan(dispatch),isnan(old))&&max(abs(delta),[],'all')<1e-10);
                end
                writetable(ports,fullfile(folder,[cc.id '_ports.csv']));writematrix(dispatch,fullfile(folder,[cc.id '_dispatch.csv']));
                writematrix(segments,fullfile(folder,[cc.id '_segments.csv']));
                writematrix(samples(result.clock_start_trace_v42,4),fullfile(folder,[cc.id '_clock_start.csv']));
                writematrix(samples(result.clock_end_trace_v42,4),fullfile(folder,[cc.id '_clock_end.csv']));
                lattice=int32(segments(:,28));latch=int32(a.initial_clock(1));latchChanges=sum(lattice~=[latch;lattice(1:end-1)]);
                row=struct('id',cc.id,'cutoff_C',cc.policy.delivery_cutoff_C,'restart_MWh',a.c(1), ...
                    'min_on_h',a.c(2),'min_off_h',a.c(3),'cutoff_inventory_MWh',p(8), ...
                    'maximum_usable_inventory_MWh',p(2)-p(8),'initial_inventory_MWh',a.initial_energy_MWh, ...
                    'terminal_inventory_MWh',item.terminal_inventory_MWh,'unmet_MWh',m.energy.unmet_heat_MWh, ...
                    'gas_heat_MWh',m.energy.gas_heat_MWh,'hp_electric_MWh',m.energy.hp_electric_MWh, ...
                    'charge_MWh',m.energy.storage_charge_MWh,'discharge_MWh',m.energy.storage_discharge_MWh, ...
                    'standing_loss_MWh',sum(dispatch(:,9)),'latch_changes',double(latchChanges), ...
                    'mode_changes',sum(diff(segments(:,3))~=0),'positive_segments',size(segments,1), ...
                    'unmet_delta_baseline_MWh',m.energy.unmet_heat_MWh-sum(baselineDispatch(:,6))*p(1), ...
                    'unmet_delta_lossfirst_MWh',m.energy.unmet_heat_MWh-pairedReport.energy.unmet_heat_MWh);
                if isempty(matrix),matrix=row;else,matrix(end+1)=row;end %#ok<AGROW>
            end
        catch err
            item.error_message=getReport(err,'extended','hyperlinks','off');
            writejson(fullfile(folder,[cc.id '_exception.json']),struct('identifier',err.identifier,'message',item.error_message));
        end
        item.elapsed_seconds=toc(timer);
    else,item.error_message='Static preflight rejected; no simulation accepted.';end
    record([cc.id '_executed'],item.execution_success);
    if isempty(items),items=item;else,items(end+1)=item;end %#ok<AGROW>
    writejson(fullfile(folder,[cc.id '_evidence.json']),item);
    fprintf('ACTUAL_SENSITIVITY_V50 id=%s success=%d intervals=%d segments=%d seconds=%.3f\n', ...
        cc.id,item.execution_success,item.intervals,item.positive_segments,item.elapsed_seconds);
end
writetable(struct2table(matrix),fullfile(folder,'sensitivity_matrix.csv'));
summary=struct('version','0.50','model_version','0.42','new_model',false,'scenarios',numel(cases), ...
    'completed_annual_scenarios',sum([items.execution_success]),'saved_intervals',sum([items.intervals]), ...
    'positive_segments',sum([items.positive_segments]),'harness_passed',sum([checks.passed]),'harness_failed',sum(~[checks.passed]));
report=struct('metadata',metadata,'cfg',cfg,'stateflow',items,'paired_cfg',pairedCfg, ...
    'paired_report',pairedReport,'matrix',matrix,'assertions',checks,'summary',summary);
save(fullfile(folder,'annual_sensitivity_v50.mat'),'report','spec');writejson(fullfile(folder,'annual_sensitivity_v50.json'),report);
fprintf('ANNUAL_SENSITIVITY_V50 pass=%d fail=%d completed=%d intervals=%d\n',summary.harness_passed,summary.harness_failed,summary.completed_annual_scenarios,summary.saved_intervals);
assert(all([checks.passed]),'DCHR:v50:Failure','Inspect retained runtime/preflight evidence.');
    function record(name,ok),checks(end+1)=struct('name',name,'passed',logical(ok));end
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;if ismatrix(raw)&&isequal(size(raw),[n width]),v=raw;
elseif numel(raw)==n*width,v=reshape(raw,width,n)';else,error('Unexpected trace dimensions.');end
end
function writejson(path,value)
assert(~isfile(path));fid=fopen(path,'w');assert(fid>0);cleanup=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(value,PrettyPrint=true));
end
