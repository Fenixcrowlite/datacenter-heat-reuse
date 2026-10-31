function diagnose_endpoint_protocol_v52(folder,prior)
% Unaccepted v51 diagnostics only. Temporary in-memory continuity relaxation
% exposes raw host/compiled mismatch; never counted as accepted execution.
root=fileparts(fileparts(mfilename('fullpath')));here=fullfile(root,'matlab','simulink');addpath(here);
if ~isfile(fullfile(prior,'padding_origin_v51_r2.json')),inspect_padding_origin_v51(prior);end
adapter=load(fullfile(prior,'baseline_adapter.mat'));a=adapter.a;
failed=load(fullfile(prior,'baseline_simulation.mat'));r=failed.result;
d=samples(r.dispatch_trace_v51,25);ends=samples(r.clock_end_trace_v51,4);
i=size(d,1)+1;E=a.initial_energy_MWh;m=a.initial_clock;
if i>1,E=d(end,8);m=ends(end,:)';end
Simulink.fileGenControl('set','CacheFolder',fullfile(folder,'diagnostic_build','cache'), ...
    'CodeGenFolder',fullfile(folder,'diagnostic_build','codegen'),'createDir',true);
mdl='DCHR_Dispatch_Stateflow_v51';load_system(fullfile(here,[mdl '.slx']));clean=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
rt=sfroot;gate=rt.find('-isa','Stateflow.EMChart','Path',[mdl '/Runtime_Contract_Gate']);original=gate.Script;
gate.Script=strrep(original,'z(4)==previousE','abs(z(4)-previousE)<=tol');
s=Simulink.SimulationInput(mdl);names={'dt','stop','input','p','h','E0','c','m0'};
values={a.p(1),0,[0 a.inputs(i,:)],a.p,a.h,E,a.c,m};
for k=1:numel(names),s=s.setVariable(['dchr_' names{k} '_v51'],values{k},'Workspace',mdl);end
result=sim(s.setModelParameter('CaptureErrors','on'));assert(isempty(result.ErrorMessage),result.ErrorMessage);
save(fullfile(folder,'unaccepted_v51_diagnostic_r2.mat'),'result','a','i','E','m','original','-v7.3');
z=reshape(samples(result.segment_trace_v51,1792),28,64)';p=reshape(samples(result.plan_trace_v51,1408),22,64)';
diffs=[];
for k=2:64
    if z(k,4)~=z(k-1,5)
        v=struct('slot',k,'start_hex',num2hex(z(k,4)),'previous_end_hex',num2hex(z(k-1,5)), ...
            'difference_MWh',z(k,4)-z(k-1,5),'span_h',z(k,2),'plan_start_hex',num2hex(p(k,2)));
        if isempty(diffs),diffs=v;else,diffs(end+1)=v;end %#ok<AGROW>
    end
end
assert(~isempty(diffs),'Expected host/compiled difference not exposed.');
report=struct('evidence_class','DIAGNOSTIC_RELAXED_GATE_NOT_ACCEPTANCE','original_actual_rejected',true, ...
    'interval',i,'original_error',r.ErrorMessage,'mismatches',diffs,'saved_v51_unchanged',true);
path=fullfile(folder,'unaccepted_v51_protocol_diagnostic.json');assert(~isfile(path));fid=fopen(path,'w');assert(fid>0);c=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(report,PrettyPrint=true));fprintf('UNACCEPTED_PROTOCOL_DIAGNOSTIC_V52 interval=%d mismatches=%d\n',i,numel(diffs));
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;
if ismatrix(raw)&&isequal(size(raw),[n width]),v=raw;
elseif numel(raw)==n*width,v=reshape(raw,width,n)';else,error('Unexpected saved trace dimensions.');end
end
