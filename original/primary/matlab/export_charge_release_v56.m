function export_charge_release_v56(folder)
% Reopen original SimulationOutputs and export their binary64 values for QA.
% Does not simulate, rebuild, modify a model, or reinterpret a JSON report.
assert(isfolder(folder)&&~isfile(fullfile(folder,'binary_manifest.json')));
binaryFolder=fullfile(folder,'binary');assert(~isfolder(binaryFolder));mkdir(binaryFolder);
records=struct('source_mat',{},'kind',{},'id',{},'field',{},'rows',{},'columns',{},'file',{});
ids={'zero_demand','hp_only','tes_charge','tes_discharge','boiler_limit','insufficient_heat'};
for j=1:numel(ids)
    source=[ids{j} '_simulation.mat'];a=load(fullfile(folder,source),'result','c');
    assert(isempty(a.result.ErrorMessage));emitRun(source,'run',ids{j},a.result,a.c);
end
source='temporal_simulation.mat';a=load(fullfile(folder,source),'result','c','blocker');
assert(isempty(a.result.ErrorMessage));emitRun(source,'temporal','sequence',a.result,a.c);
b=a.blocker.input;
emit(source,'temporal','sequence','blocker.witness', ...
    [b.E b.p.heat_capacity_MWh_per_K b.p.ambient_C b.s.charge_approach_K b.s.delivery_C b.s.direct_approach_K]);
assert(strcmp(a.blocker.endpoint_identifier,'DCHR:v55:UnresolvedBranch'));
manifest=struct('version','0.56','source','ORIGINAL_REOPENED_SIMULATIONOUTPUT_BINARY64', ...
    'encoding','IEEE_BINARY64_LITTLE_ENDIAN_ROW_MAJOR','records',records);
fid=fopen(fullfile(folder,'binary_manifest.json'),'w');assert(fid>0);
cl=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(manifest,PrettyPrint=true));
fprintf('CHARGE_BINARY_V56 RECORDS=%d ORIGINAL_MATS=7\n',numel(records));
    function emitRun(source,kind,id,r,c)
        emit(source,kind,id,'dispatch',samples(r.dispatch_trace_v52,25));
        raw=samples(r.segment_trace_v52,1792);plan=samples(r.plan_trace_v52,1472);
        if strcmp(kind,'run')
            raw=reshape(raw,28,64)';plan=reshape(plan,23,64)';
        end
        emit(source,kind,id,'raw_segments',raw);emit(source,kind,id,'raw_plans',plan);
        emit(source,kind,id,'clock_start',samples(r.clock_start_trace_v52,4));
        emit(source,kind,id,'clock_end',samples(r.clock_end_trace_v52,4));
        emit(source,kind,id,'energy_start',samples(r.energy_start_trace_v52,1));
        for key={'p','h','c','inputs','initial_energy_MWh','initial_clock'}
            emit(source,kind,id,['case.' key{1}],c.(key{1}));
        end
    end
    function emit(source,kind,id,field,v)
        assert(isa(v,'double')&&isreal(v)&&ismatrix(v));
        name=sprintf('%03d_%s_%s.bin',numel(records)+1,id,strrep(field,'.','_'));
        path=fullfile(binaryFolder,name);assert(~isfile(path));
        fd=fopen(path,'w','ieee-le');assert(fd>0);closefile=onCleanup(@()fclose(fd)); %#ok<NASGU>
        assert(fwrite(fd,v','double')==numel(v));
        records(end+1)=struct('source_mat',source,'kind',kind,'id',id,'field',field, ...
            'rows',size(v,1),'columns',size(v,2),'file',['binary/' name]);
    end
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;
if ismatrix(raw)&&isequal(size(raw),[n width]),v=raw;
elseif numel(raw)==n*width,v=reshape(raw,width,n)';
else,error('DCHR:v56:BinaryTraceShape','Unexpected original trace shape.');end
end
