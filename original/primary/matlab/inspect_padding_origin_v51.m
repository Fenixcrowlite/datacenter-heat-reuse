function inspect_padding_origin_v51(folder)
% Instrument a COPY of the preserved planner, bind its plan to original host.
root=fileparts(fileparts(mfilename('fullpath')));here=fullfile(root,'matlab','simulink');
spec=jsondecode(fileread(fullfile(folder,'spec.json')));
old=load(fullfile(root,spec.defect_evidence,'annual_sensitivity_v50.mat'));
seeds=load(fullfile(root,spec.defect_evidence,'defect_evidence','defects_v50.mat'));
target=fullfile(folder,'origin_instrumentation_r2');assert(~isfolder(target));mkdir(target);
text=fileread(fullfile(here,'dchr_segment_plan_v42.m'));
text=strrep(text,sprintf('\r\n'),newline); % stable marker matching on Windows
text=strrep(text,'function plan=dchr_segment_plan_v42','function [plan,w]=instrumented_padding_origin_v51');
text=strrep(text,'stateflow_clock_add_v42(age,low,bound,0);','w=[];stateflow_clock_add_v42(age,low,bound,0);');
text=strrep(text,'E=advance(E,P,p(7),span);', ...
    ['startE=E;E=advance(E,P,p(7),span);' newline ...
    'entry=struct(''kind'',kind,''span_before_remainder'',span,''offset_before'',offset,''start_MWh'',startE,''P_MW'',P,''rate_per_h'',p(7),''advance_endpoint_MWh'',E,''advance_endpoint_hex'',num2hex(E),''extra_h'',0);']);
text=strrep(text,'E=advance(E,P,p(7),extra);offset=dt;', ...
    'entry.extra_h=extra;E=advance(E,P,p(7),extra);offset=dt;');
text=strrep(text,[newline 'end' newline 'for k=count+1:64'], ...
    [newline 'entry.final_MWh=E;entry.final_hex=num2hex(E);if isempty(w),w=entry;else,w(end+1)=entry;end' newline 'end' newline 'for k=count+1:64']);
fid=fopen(fullfile(target,'instrumented_padding_origin_v51.m'),'w');assert(fid>0);fprintf(fid,'%s',text);fclose(fid);
addpath(target);cleanup=onCleanup(@()rmpath(target)); %#ok<NASGU>
items=[];
for j=1:numel(seeds.items)
    d=seeds.items(j);seed=d.candidate;a=old.report.stateflow(strcmp({old.report.stateflow.id},d.id));
    original=dchr_segment_plan_v42(seed.input,seed.initial_energy_MWh,a.p,a.h,a.p(1),seed.initial_clock,a.c);
    [copy,w]=instrumented_padding_origin_v51(seed.input,seed.initial_energy_MWh,a.p,a.h,a.p(1),seed.initial_clock,a.c);
    assert(isequaln(original,copy)&&numel(w)==sum(original(1,:)>0),'Instrumented planner does not match original.');
    item=struct('id',d.id,'matches_original',true,'capacity_hex',num2hex(a.p(2)), ...
        'padding_start_hex',num2hex(original(2,find(original(1,:)==0,1))), ...
        'segments',w,'p',a.p,'h',a.h);
    if isempty(items),items=item;else,items(end+1)=item;end %#ok<AGROW>
end
fid=fopen(fullfile(folder,'padding_origin_v51_r2.json'),'w');assert(fid>0);clean=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(items,PrettyPrint=true));fprintf('PADDING_ORIGIN_V51 matched_original=2\n');
end
