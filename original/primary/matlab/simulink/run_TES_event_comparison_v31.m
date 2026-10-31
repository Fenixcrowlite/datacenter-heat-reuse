function outputDir = run_TES_event_comparison_v31(specDirectory)
% Execute new event component and preserved v30 SLX; never save/change SLX.
here=fileparts(mfilename('fullpath'));root=fileparts(fileparts(here));
addpath(fullfile(root,'matlab'),here);
assert(nargin==1 && isfolder(specDirectory),'DCHR:v31:Spec','Provide the independent specification.');
stamp=char(datetime('now','TimeZone','UTC','Format','yyyyMMdd''T''HHmmssSSS''Z'''));
outputDir=fullfile(root,'results',['TES_event_v31_' stamp]);assert(~isfolder(outputDir));mkdir(outputDir);
snap=fullfile(outputDir,'source_snapshot');mkdir(snap);copyfile(specDirectory,fullfile(snap,'spec'));
files=[dir(fullfile(here,'*v30.m'));dir(fullfile(root,'matlab','+dchr','*v30.m')); ...
    dir(fullfile(root,'matlab','+dchr','+components','*v30.m'))];
for k=1:numel(files),copyfile(fullfile(files(k).folder,files(k).name),snap);end
copyfile(fullfile(root,'matlab','+dchr','+components','storage_event_kernel_v31.m'),snap);
copyfile([mfilename('fullpath') '.m'],snap);
copyfile(fullfile(root,'matlab','+dchr','+components','heat_pump_step_v14.m'),snap);
copyfile(fullfile(root,'audit','TES_event_reference_v31.py'),snap);
copyfile(fullfile(root,'audit','stateflow_reference_v30.py'),snap);
spec=jsondecode(fileread(fullfile(specDirectory,'cases.json')));
vectors=readtable(fullfile(specDirectory,'component_vectors.csv'),'TextType','string');
names={'charge_avg_MW','discharge_avg_MW','passive_MWh','next_MWh','standing_MWh', ...
    'charge_loss_MWh','discharge_loss_MWh','start_C','next_C','usable_start_MWh', ...
    'usable_next_MWh','full_charge_MW','full_discharge_MW','event_time_h','event_kind', ...
    'tail_charge_MW','tail_discharge_MW','event_energy_MWh','charge_MWh','discharge_MWh'};
checks=struct('name',{},'passed',{});component=table();
for j=1:numel(spec.component_cases)
    c=spec.component_cases(j);p=reshape(c.p,1,[]);
    z=dchr.components.storage_event_kernel_v31(c.a,c.charge,c.discharge,p);
    expected=vectors(vectors.id==string(c.id),:);
    for k=1:numel(names),record([c.id '_' names{k}],near(z(k),expected.(names{k})));end
    small=p;small(1)=p(1)/4;energy=c.a;sums=zeros(5,1);
    for k=1:4
        part=dchr.components.storage_event_kernel_v31(energy,c.charge,c.discharge,small);
        sums=sums+part([19 20 5 6 7]);energy=part(4);
    end
    record([c.id '_production_partition'],near(energy,z(4)) && near(sums,z([19 20 5 6 7])));
    component=[component;table(string(c.id),'VariableNames',{'id'}),array2table(z','VariableNames',names)]; %#ok<AGROW>
end
% Actual component domain rejections, separately from synthetic evidence tests.
domain=struct('id',{},'passed',{},'identifier',{},'diagnostic',{});
base=[2 10 3 4 .9 .8 .1 5 .2 20];
for k=1:12
    p=base;A=7;qc=0;qd=1;
    switch k
        case 1,A=-1;id='negative_state';
        case 2,A=11;id='above_capacity_state';
        case 3,A=NaN;id='nan_state';
        case 4,qd=Inf;id='infinite_request';
        case 5,qc=1;id='simultaneous_ports';
        case 6,p(1)=0;id='zero_interval';
        case 7,p(7)=-1;id='negative_loss_rate';
        case 8,p(8)=11;id='cutoff_above_capacity';
        case 9,p(5)=0;id='zero_efficiency';
        case 10,p(9)=0;id='zero_heat_capacity';
        case 11,p(3)=-1;id='negative_limit';
        case 12,qd=-1;id='negative_request';
    end
    rejected=false;identifier='';diagnostic='';
    try,dchr.components.storage_event_kernel_v31(A,qc,qd,p);
    catch failure,rejected=strcmp(failure.identifier,'DCHR:v31:Domain');identifier=failure.identifier;diagnostic=failure.message;
    end
    record(['domain_' id],rejected);
    domain(end+1)=struct('id',id,'passed',rejected,'identifier',identifier,'diagnostic',diagnostic); %#ok<AGROW>
end
writetable(component,fullfile(outputDir,'component_trace_v31.csv'));
writejson(fullfile(outputDir,'component_domain_v31.json'),domain);
mdl='DCHR_Dispatch_Stateflow_v30';modelPath=fullfile(here,[mdl '.slx']);
assert(isfile(modelPath));copyfile(modelPath,snap);load_system(modelPath);
cleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
oldGen=Simulink.fileGenControl('getConfig');
genCleanup=onCleanup(@()Simulink.fileGenControl('setConfig','config',oldGen)); %#ok<NASGU>
Simulink.fileGenControl('set','CacheFolder',fullfile(outputDir,'cache'), ...
    'CodeGenFolder',fullfile(outputDir,'codegen'),'createDir',true);
ports={'Mode','HP_Direct_MW','Storage_Charge_MW','Storage_Discharge_MW','Gas_Heat_MW', ...
    'Unmet_Heat_MW','Storage_E_After_Loss_MWh','Storage_E_Next_MWh','Storage_Standing_Loss_MWh', ...
    'Storage_Charge_Loss_MWh','Storage_Discharge_Loss_MWh','Supplied_Heat_MW', ...
    'System_Balance_Residual_MWh','Storage_T_Start_C','Storage_T_Next_C', ...
    'Storage_Usable_Start_MWh','Storage_Usable_Next_MWh'};
hpNames={'Heat_Demand_MW','HP_Heat_MW','HP_Electric_MW','HP_Source_Used_MW', ...
    'HP_Request_MW','COP','HP_Available','Source_Unused_MW'};
combined=table();eventTrace=table();comparison=table();
for j=1:numel(spec.comparison_cases)
    c=spec.comparison_cases(j);c.p=reshape(c.p,1,[]);c.h=reshape(c.h,1,[]);
    dt=c.p(1);n=size(c.inputs,1);times=(0:n-1)'*dt;
    s=Simulink.SimulationInput(mdl);vars={'dt','stop','input','p','h','E0'};
    values={dt,(n-1)*dt,[times c.inputs],c.p,c.h,c.initial_energy_MWh};
    for k=1:numel(vars),s=s.setVariable(['dchr_' vars{k} '_v30'],values{k},'Workspace',mdl);end
    result=sim(s);save(fullfile(outputDir,[c.id '_simulation.mat']),'result');
    y=samples(result.dispatch_trace_v30,17);u=samples(result.hp_trace_v30,8);
    energies=reshape(result.energy_start_trace_v30.Data,[],1);
    actual=[array2table(y,'VariableNames',ports),array2table(u,'VariableNames',hpNames), ...
        table(energies,'VariableNames',{'Storage_E_Start_MWh'})];
    record([c.id '_sample_clock'],near(result.dispatch_trace_v30.Time,times));
    record([c.id '_first_law'],all(abs(y(:,13))<1e-9));
    record([c.id '_bounds'],all(y(:,8)>=-1e-10 & y(:,8)<=c.p(2)+1e-10));
    record([c.id '_energy_feedback'],near(energies(1),c.initial_energy_MWh) && near(reshape(energies(2:end),[],1),y(1:end-1,8)));
    combined=[combined;table(repmat(string(c.id),n,1),times,'VariableNames',{'scenario_id','Time_h'}),actual]; %#ok<AGROW>
    A=c.initial_energy_MWh;event=zeros(n,20);start=zeros(n,1);gas=zeros(n,1);unmet=zeros(n,1);
    for k=1:n
        start(k)=A;
        z=dchr.components.storage_event_kernel_v31(A,c.charge_request_MW,c.discharge_request_MW,c.p(1:10));
        event(k,:)=z';A=z(4);t=z(14);tail=dt-t;deficit=c.inputs(k,4)-c.hp_direct_MW;
        g1=min(c.p(11),max(0,deficit-z(13)));g2=min(c.p(11),max(0,deficit-z(17)));
        gas(k)=g1*t+g2*tail;
        unmet(k)=max(0,deficit-z(13)-g1)*t+max(0,deficit-z(17)-g2)*tail;
        record([c.id '_event_demand_' num2str(k)],near(z(20)+gas(k)+unmet(k)+c.hp_direct_MW*dt,c.inputs(k,4)*dt));
    end
    eventTrace=[eventTrace;table(repmat(string(c.id),n,1),times,start,gas,unmet, ...
        'VariableNames',{'scenario_id','Time_h','start_MWh','gas_MWh','unmet_MWh'}), ...
        array2table(event,'VariableNames',names)]; %#ok<AGROW>
    total=[sum(y(:,3))*dt,sum(event(:,19)),sum(y(:,4))*dt,sum(event(:,20)), ...
        sum(y(:,5))*dt,sum(gas),sum(y(:,6))*dt,sum(unmet),y(end,8),event(end,4), ...
        sum(y(:,9)),sum(event(:,5))];
    comparison=[comparison;table(string(c.id),string(c.family),dt, ...
        'VariableNames',{'scenario_id','family','dt_h'}),array2table(total,'VariableNames', ...
        {'v30_charge_MWh','event_charge_MWh','v30_discharge_MWh','event_discharge_MWh', ...
        'v30_gas_MWh','event_gas_MWh','v30_unmet_MWh','event_unmet_MWh', ...
        'v30_endpoint_MWh','event_endpoint_MWh','v30_standing_MWh','event_standing_MWh'})]; %#ok<AGROW>
    fprintf('COMPARISON_EXECUTED=%s intervals=%d\n',c.id,n);
end
record('all_six_saved_v30_modes',isequal(unique(combined.Mode),(0:5)'));
for family=unique(comparison.family)'
    group=comparison(comparison.family==family,:);
    for name={'event_charge_MWh','event_discharge_MWh','event_gas_MWh','event_unmet_MWh','event_endpoint_MWh','event_standing_MWh'}
        v=group.(name{1});record(char(family+"_partition_"+name{1}),max(v)-min(v)<1e-9);
    end
end
writetable(combined,fullfile(outputDir,'saved_v30_trace.csv'));
writetable(eventTrace,fullfile(outputDir,'event_trace_v31.csv'));
writetable(comparison,fullfile(outputDir,'policy_comparison_v31.csv'));
writetable(struct2table(checks),fullfile(outputDir,'assertions_v31.csv'));
summary=struct('checkpoint_version','0.31','model_release','0.30','timestamp_utc',stamp, ...
    'matlab_version',version,'stateflow_license',license('test','Stateflow'), ...
    'component_cases',numel(spec.component_cases),'component_domain_rejections',sum([domain.passed]), ...
    'saved_model_scenarios',numel(spec.comparison_cases),'saved_model_intervals',height(combined), ...
    'checks',numel(checks),'passed',sum([checks.passed]),'failed',sum(~[checks.passed]), ...
    'saved_v30_modes',unique(combined.Mode)','max_abs_v30_balance_MWh',max(abs(combined.System_Balance_Residual_MWh)), ...
    'new_stateflow_model',false,'event_component_embedded_in_stateflow',false, ...
    'physical_validation',false,'article_replication',false,'output_directory',outputDir);
writejson(fullfile(outputDir,'summary_v31.json'),summary);disp(summary);
assert(all([checks.passed]),'DCHR:v31:AcceptanceFailed','See timestamped assertions.');
fprintf('TES_EVENT_OUTPUT=%s\n',outputDir);
    function record(name,passed)
        checks(end+1)=struct('name',name,'passed',logical(passed));
        if ~passed,fprintf(2,'FAIL %s\n',name);end
    end
end

function ok=near(a,b)
a=double(a);b=double(b);ok=isequal(size(a),size(b)) && all(abs(a-b)<=2e-9+2e-11*abs(b),'all');
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;
if ismatrix(raw) && isequal(size(raw),[n width]),v=raw;
elseif size(raw,1)==width && numel(raw)==n*width,v=reshape(raw,width,n)';
else,error('DCHR:v31:TraceDimensions','Unexpected trace shape.');end
end
function writejson(path,value)
assert(~isfile(path));fid=fopen(path,'w');assert(fid>0);cleanup=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(value,PrettyPrint=true));
end
