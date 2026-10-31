function run_earliest_rejection_probes_v72(folder)
% Diagnostic host replay ONLY. The actual saved-model rejection is already
% retained by run_earliest_admissibility_v72. Do not count this as Stateflow.
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'matlab','simulink'));
report=jsondecode(fileread(fullfile(folder,'report.json')));
source=fileread(fullfile(root,'matlab','simulink','earliest_dispatch_kernel_v71.m'));
diagnosticName=['diagnostic_earliest_kernel_v72_' char(datetime('now','TimeZone','UTC','Format','yyyyMMddHHmmssSSS'))];
text=strrep(source,'function y=earliest_dispatch_kernel_v71(u,p,old)',['function y=' diagnosticName '(u,p,old)']);
needle="assert(rate(2)<=muliv(P(u(7)),P(p(13)))*[0;1],'v71 finite source capacity');";
replacement="if ~(rate(2)<=muliv(P(u(7)),P(p(13)))*[0;1]),y(62:73)=[72;limit;rate';muliv(P(u(7)),P(p(13)))';q';duration';cell;slot];return;end";
assert(contains(text,needle));text=strrep(text,needle,replacement);
needle="assert(all(increment>=0),'v71 nonnegative energy');";
replacement="if ~all(increment>=0),y(62:75)=[73;limit;heat';src';work';duration';E';slot;event];y(101:120)=increment;return;end";
assert(contains(text,needle));text=strrep(text,needle,replacement);
file=fullfile(folder,[diagnosticName '.m']);assert(~isfile(file));fd=fopen(file,'w');assert(fd>0);fprintf(fd,'%s',text);fclose(fd);addpath(folder);
cleanup=onCleanup(@()rmpath(folder)); %#ok<NASGU>
probes={};
for id={'source_limited','rounded_source_water_tie','source_below_tie','restart_band_2m42'}
    p=report.probes(strcmp({report.probes.id},id{1}));assert(~p.accepted&&p.fault_tick==1);
    if isvector(p.input),p.input=p.input(:)';end
    y=feval(diagnosticName,p.input(1,:)',p.p(:),zeros(1380,1));assert(ismember(y(62),[72 73]));
    probes{end+1}=struct('id',id{1},'p',p.p,'input',p.input,'diagnostic',y'); %#ok<AGROW>
end
evidence_class='INSTRUMENTED_HOST_REPLAY_ONLY_NOT_STATEFLOW_OR_INDEPENDENT_QA';
save(fullfile(folder,'rejection_diagnostics_v72.mat'),'probes','evidence_class','-v7.3');reopened=load(fullfile(folder,'rejection_diagnostics_v72.mat'));assert(isequaln(reopened.probes,probes));
fd=fopen(fullfile(folder,'rejection_diagnostics_v72.json'),'w');assert(fd>0);fprintf(fd,'%s\n',jsonencode(struct('evidence_class',evidence_class,'diagnostic_function',diagnosticName,'probes',{reopened.probes}),PrettyPrint=true));fclose(fd);
manifest=struct('id',{},'file',{},'columns',{});
for j=1:numel(reopened.probes)
    r=reopened.probes{j};file=sprintf('binary/diagnostic_%d.bin',j);fd=fopen(fullfile(folder,file),'w','ieee-le');assert(fd>0);assert(fwrite(fd,r.diagnostic,'double')==1380);fclose(fd);
    manifest(end+1)=struct('id',r.id,'file',file,'columns',1380); %#ok<AGROW>
end
fd=fopen(fullfile(folder,'diagnostic_manifest_v72.json'),'w');assert(fd>0);fprintf(fd,'%s\n',jsonencode(manifest,PrettyPrint=true));fclose(fd);
fprintf('REJECTION_DIAGNOSTICS_V72 REOPENED=%d PROBES=%d\n',1,numel(probes));
end
