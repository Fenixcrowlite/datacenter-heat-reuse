"""Create an additive execution harness; never edit the accepted v85 builder/model."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT/'matlab/run_electrical_ceiling_v85r2.m').read_text()
src = src.replace('run_electrical_ceiling_v85r2', 'run_horizon_sensitivity_v86')
src = src.replace("if ~isfile(path),build_electrical_ceiling_v85([a.protocol_ticks a.input],cfg);end",
                  "assert(isfile(path),'Accepted saved v85 is required; this experiment does not build a model');")
src = src.replace("report=struct('version','0.85'", "report=struct('version','0.86'")
src = src.replace('electrical_ceiling_v85.mat', 'horizon_sensitivity_v86.mat')
src = src.replace('REACHABLE_V85', 'HORIZON_V86')
marker = 'close_system(mdl,0);load_system(path);'
probe = """% Execute the exact one-hour declared endpoint, retaining either outcome.
probeIndex=find(arrayfun(@(j)contains(getcase(j).id,'service_E3.0_a1.0_H1_dt0.25'),1:numel(spec.cases)),1);
c=getcase(probeIndex);a=dchr.adapt_held_schedule_v74(c.schedule,c.p,c.initial);
raw=[a.p c.ceiling_MW 1];a.p=electrical_policy_v85(raw',c.initial(1))';
probeTrace=[];probeCertificate=[];probeMessage='';probeAccepted=false;
try
    [~,probeTrace,probeCertificate]=execute(mdl,a,raw);probeAccepted=true;
catch e
    probeMessage=getReport(e,'extended','hyperlinks','off');
end
record('exact_horizon_probe_classified',probeAccepted||contains(probeMessage,'v85 declared horizon exceeded'));
endpoint_probe=struct('accepted',probeAccepted,'horizon_h',1,'adapter',a,'raw_policy',raw, ...
    'trace',probeTrace,'certificate',probeCertificate,'message',probeMessage);
writejson('exact_horizon_probe.json',endpoint_probe);
save(fullfile(folder,'exact_horizon_probe.mat'),'endpoint_probe','-v7.3');
"""
assert src.count(marker)==1
src = src.replace(marker, probe+marker)
dst = ROOT/'matlab/run_horizon_sensitivity_v86.m'
with dst.open('x', encoding='utf-8') as f:f.write(src)
ps = (ROOT/'audit/run_electrical_ceiling_v85r2.ps1').read_text().replace(
    'run_electrical_ceiling_v85r2', 'run_horizon_sensitivity_v86')
with (ROOT/'audit/run_horizon_sensitivity_v86.ps1').open('x',encoding='utf-8') as f:f.write(ps)
print('Created versioned MATLAB execution harness and timestamped batch wrapper.')
