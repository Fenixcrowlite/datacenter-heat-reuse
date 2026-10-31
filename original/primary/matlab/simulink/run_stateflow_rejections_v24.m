function summary=run_stateflow_rejections_v24(mdl,outputDir)
% Every independent invalid-domain vector is submitted to the actual .slx.
here=fileparts(mfilename('fullpath')); root=fileparts(fileparts(here));
spec=jsondecode(fileread(fullfile(root,'audit','stateflow_domain_cases_v24.json')));
cases=spec.cases; baseline=spec.baseline;
records=struct('id',{},'tick',{},'expected_identifier',{},'simulation_attempted',{}, ...
    'rejected',{},'actual_identifier',{},'cause_identifiers',{},'message',{}, ...
    'started_at_h',{},'accepted_invalid_trace',{},'expected_cause_observed',{},'failure_report',{});
for k=1:numel(cases)
    if iscell(cases), c=cases{k}; else, c=cases(k); end
    b=baseline;
    if isfield(c,'setup') && ~isempty(c.setup)
        for j=1:numel(c.setup), b=mutate(b,c.setup(j)); end
    end
    if strcmp(c.target,'x')
        rows=repmat(b.x(:)',2,1); rows(c.tick+1,c.index)=numeric(c.value);
    else
        b=mutate(b,c); rows=repmat(b.x(:)',2,1);
    end
    s=Simulink.SimulationInput(mdl);
    s=s.setVariable('dchr_dt_v24',b.model_dt,'Workspace',mdl);
    s=s.setVariable('dchr_stop_v24',b.model_dt,'Workspace',mdl);
    s=s.setVariable('dchr_input_v24',[(0:1)'*b.model_dt rows],'Workspace',mdl);
    s=s.setVariable('dchr_p_v24',b.p(:)','Workspace',mdl);
    s=s.setVariable('dchr_h_v24',b.h(:)','Workspace',mdl);
    s=s.setVariable('dchr_E0_v24',b.E,'Workspace',mdl);
    rejected=false; actual=''; causes={}; message=''; report=''; accepted=false;
    try
        invalidResult=sim(s);
        accepted=true;
        save(fullfile(outputDir,[c.id '_UNEXPECTED_ACCEPTANCE.mat']),'invalidResult');
    catch failure
        rejected=true; actual=failure.identifier; causes=identifiers(failure);
        message=failure.message; report=getReport(failure,'extended','hyperlinks','off');
    end
    expected=any(strcmp(c.expected_identifier,causes));
    reportFile=fullfile(outputDir,[c.id '_rejection.txt']);
    fid=fopen(reportFile,'w'); assert(fid>0); fprintf(fid,'%s\n',report); fclose(fid);
    records(end+1)=struct('id',c.id,'tick',c.tick,'expected_identifier',c.expected_identifier, ...
        'simulation_attempted',true,'rejected',rejected,'actual_identifier',actual, ...
        'cause_identifiers',{causes},'message',message,'started_at_h',NaN, ...
        'accepted_invalid_trace',accepted,'expected_cause_observed',expected,'failure_report',reportFile); %#ok<AGROW>
    fprintf('RUNTIME_DOMAIN %s rejected=%d expected_cause=%d\n',c.id,rejected,expected);
end
summary=struct('cases',numel(cases),'rejected',sum([records.rejected]), ...
    'expected_cause_observed',sum([records.expected_cause_observed]), ...
    'accepted_invalid_traces',sum([records.accepted_invalid_trace]), ...
    'spec_file','audit/stateflow_domain_cases_v24.json','records',records, ...
    'simulation_mode','normal','first_valid_tick_observed',false);
fid=fopen(fullfile(outputDir,'runtime_rejections_v24.json'),'w'); assert(fid>0);
fprintf(fid,'%s\n',jsonencode(summary,PrettyPrint=true)); fclose(fid);
end

function b=mutate(b,c)
if isfield(c,'index') && ~isempty(c.index)
    vector=b.(c.target); vector(c.index)=numeric(c.value); b.(c.target)=vector;
else
    b.(c.target)=numeric(c.value);
end
end
function v=numeric(value)
if isnumeric(value), v=double(value); else, v=str2double(value); end
end
function ids=identifiers(failure)
ids={failure.identifier};
for k=1:numel(failure.cause), ids=[ids identifiers(failure.cause{k})]; end %#ok<AGROW>
end
