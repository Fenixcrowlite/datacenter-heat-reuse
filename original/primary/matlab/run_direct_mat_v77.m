function run_direct_mat_v77(folder)
% Fresh saved-v75 execution; preserve native logged arrays for direct HDF5 QA.
root=fileparts(fileparts(mfilename('fullpath')));
addpath(fullfile(root,'matlab'),fullfile(root,'matlab','simulink'));
assert(isfolder(folder)&&~isfile(fullfile(folder,'execution_report.json')));
spec=jsondecode(fileread(fullfile(folder,'spec.json')));
mdl='DCHR_Earliest_Dispatch_Stateflow_v75';
load_system(fullfile(root,'matlab','simulink',[mdl '.slx']));
cleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
sldiagviewer.diary(fullfile(folder,'simulink_diagnostics.txt'));
checks=struct('name',{},'passed',{});runs=struct('id',{},'file',{},'intervals',{},'segments',{},'events',{});coverage=[];
for j=1:numel(spec.cases)
    c=spec.cases(j);a=dchr.adapt_held_schedule_v74(c.schedule,c.p,c.initial);
    mw=get_param(mdl,'ModelWorkspace');assignin(mw,'dispatch_input_v66',[a.protocol_ticks a.input]);
    assignin(mw,'dispatch_cfg_v66',[a.protocol_ticks repmat(a.p,size(a.input,1),1)]);
    out=sim(mdl,'StopTime',num2str(size(a.input,1)-1),'ReturnWorkspaceOutputs','on');
    raw_data=out.interval_trace_v66.Data;raw_time=out.interval_trace_v66.Time;
    native_shape=size(raw_data);trace=reshape(raw_data,1380,[])';
    rr=dchr.report_held_schedule_v76(a,trace);
    record([c.id '_finite'],all(isfinite(trace),'all'));
    record([c.id '_length'],size(trace,1)==size(a.input,1)&&numel(raw_time)==size(trace,1));
    record([c.id '_solver_ticks'],isequal(raw_time(:),a.protocol_ticks));
    record([c.id '_first_law'],all(trace(:,53)<=0&trace(:,54)>=0));
    record([c.id '_TES_bounds'],all(trace(:,5)>=0&trace(:,6)<=a.p(1)*(a.p(3)-a.p(2))));
    record([c.id '_nonnegative_totals'],all(trace(:,31:50)>=0,'all'));
    file=[c.id '.mat'];save(fullfile(folder,file),'out','raw_data','raw_time','native_shape','trace','a','rr','-v7.3');
    reopened=load(fullfile(folder,file),'raw_data','raw_time','native_shape','trace','a','rr');
    record([c.id '_MAT_reopen'],isequaln(reopened.raw_data,raw_data)&&isequaln(reopened.trace,trace)&&isequaln(reopened.a,a)&&isequaln(reopened.rr,rr));
    runs(end+1)=struct('id',c.id,'file',file,'intervals',size(trace,1),'segments',sum(trace(:,13)),'events',sum(trace(:,14))); %#ok<AGROW>
    coverage=[coverage;trace(:,1)]; %#ok<AGROW>
    fprintf('DIRECT_MAT_V77 %s INTERVALS=%d SEGMENTS=%d EVENTS=%d NATIVE_SHAPE=%s\n',c.id,size(trace,1),sum(trace(:,13)),sum(trace(:,14)),mat2str(native_shape));
end
record('six_final_modes',isequal(unique(coverage)',0:5));
% Asymmetric fixtures independently specify MATLAB-to-HDF5 axis mapping.
fixture_matrix=[11 12 13;21 22 23];fixture_tensor=reshape(1:24,[2 3 4]);
fixture_row=[3 5 7];fixture_column=[2;4;8];fixture_scalar=42;
fixture_empty=zeros(0,3);fixture_signed_zero=[0 -1/Inf];
fixture_nonfinite=[NaN Inf -Inf];fixture_logical=logical([1 0;0 1]);
fixture_char='MAT77';fixture_cell={fixture_matrix,struct('value',17)};
save(fullfile(folder,'parser_fixture.mat'),'fixture_matrix','fixture_tensor','fixture_row','fixture_column', ...
    'fixture_scalar','fixture_empty','fixture_signed_zero','fixture_nonfinite','fixture_logical','fixture_char','fixture_cell','-v7.3');
rt=sfroot;ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Six_Mode_Interval_Dispatch']);
metadata=struct('matlab_version',version,'license_observed',license('test','Stateflow'), ...
    'chart_count',numel(ch),'action_language',ch.ActionLanguage,'simulation_mode',get_param(mdl,'SimulationMode'), ...
    'states',{arrayfun(@(x)x.Name,ch.find('-isa','Stateflow.State'),'UniformOutput',false)});
report=struct('version','0.77','saved_model_version','0.75','new_model',false,'runs',runs, ...
    'mode_coverage',unique(coverage)','metadata',metadata,'assertions',checks, ...
    'summary',struct('passed',sum([checks.passed]),'failed',sum(~[checks.passed])));
save(fullfile(folder,'execution_report.mat'),'report','-v7.3');
fd=fopen(fullfile(folder,'execution_report.json'),'w');assert(fd>0);cl=onCleanup(@()fclose(fd)); %#ok<NASGU>
fprintf(fd,'%s\n',jsonencode(report,PrettyPrint=true));
fprintf('DIRECT_MAT_V77 PASS=%d FAIL=%d\n',report.summary.passed,report.summary.failed);
assert(all([checks.passed]),'DCHR:v77:AuditFailure','Inspect evidence');
    function record(name,ok),checks(end+1)=struct('name',name,'passed',logical(ok));end
end
