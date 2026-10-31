"""Create additive v79 tooling while preserving all accepted code/models."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def write(path,text):
    with (ROOT/path).open('x',encoding='utf-8',newline='\n') as f:f.write(text)

b=(ROOT/'matlab/simulink/build_energy_commit_v78.m').read_text()
b=b.replace('build_energy_commit_v78','build_hp_partition_v79').replace('DCHR_Earliest_Dispatch_Stateflow_v78','DCHR_Earliest_Dispatch_Stateflow_v79')
anchor="f=Stateflow.EMFunction(ch);f.Name='earliest_mode_v73';"
b=b.replace(anchor,"f=Stateflow.EMFunction(ch);f.Name='monitor_hp_partition_v79';f.Position=[1650 800 380 90];f.Script=fileread(fullfile(here,'monitor_hp_partition_v79.m'));\n"+anchor)
b=b.replace('monitor_energy_commit_v78(horizon_input,policy_input,retained_memory,core);','monitor_hp_partition_v79(horizon_input,policy_input,retained_memory,core);')
b=b.replace('v78 pre-commit energy/temporal-monitored','v79 pre-commit HP partition/energy/temporal-monitored').replace('BUILT_ENERGY_COMMIT_STATEFLOW_V78','BUILT_HP_PARTITION_STATEFLOW_V79')
write('matlab/simulink/build_hp_partition_v79.m',b)
write('audit/run_hp_partition_v79.ps1',(ROOT/'audit/run_energy_commit_v78.ps1').read_text().replace('run_energy_commit_v78','run_hp_partition_v79'))

h=(ROOT/'matlab/run_energy_commit_v78.m').read_text()
h=h.replace('run_energy_commit_v78','run_hp_partition_v79').replace('build_energy_commit_v78','build_hp_partition_v79')
h=h.replace('DCHR_Earliest_Dispatch_Stateflow_v78','DCHR_Earliest_Dispatch_Stateflow_v79').replace("prior='DCHR_Earliest_Dispatch_Stateflow_v77'","prior='DCHR_Earliest_Dispatch_Stateflow_v78'")
h=h.replace('monitor_energy_commit_v78(horizon_input','monitor_hp_partition_v79(horizon_input').replace('bitwise_saved_v77','bitwise_saved_v78').replace('COMMIT_V78','PARTITION_V79')
start=h.index('for j=1:numel(spec.faults)');end=h.index("record('restored_kernel'",start)
h=h[:start]+'''target=runs{find(cellfun(@(r)strcmp(r.id,'HP_only'),runs),1)};
assert(size(target.trace,1)==1&&target.trace(1,13)==1);
for j=1:numel(spec.faults)
    f=spec.faults(j);a=target.adapter;rowIndex=1;
    % Coordinated split/copy changes preserve v78 balance and accumulation.
    injection=sprintf(['\\nif old(2)==0\\n' ...
        'h=y(132:133); w=hp_fault_mul(h,%.17g); s=hp_fault_mul(h,%.17g);\\n' ...
        'aux=hp_fault_mul(w,p(21));\\n' ...
        'y(134:137)=[s;w];y(150:151)=aux;\\n' ...
        'y(17:20)=[s;w];y(33:36)=[s;w];y(49:50)=aux;\\nend\\n'],f.work_fraction,1-f.work_fraction);
    anchor="y(57)=limit;y(62:65)=[ageCert;ageHi;ageErr'];";
    assert(numel(strfind(original,anchor))==1);
    helper=sprintf(['\\nfunction z=hp_fault_mul(x,s)\\n' ...
        'if s==0||all(x==0),z=[0;0];else,v=x*s;z=[v(1)-2*eps(v(1));v(2)+2*eps(v(2))];end\\nend\\n']);
    mutated=[char(strrep(original,anchor,[char(anchor) injection])) helper];
    kernel.Script=mutated;priorKernel.Script=mutated;
    [~,legacy]=execute(prior,a);priorKernel.Script=original;
    expected=['v79 ' f.expected];errorText='';errorId='';rejected=false;
    try,execute(mdl,a);catch e,errorText=getReport(e,'extended','hyperlinks','off');errorId=e.identifier;rejected=contains(errorText,expected);end
    record([f.id '_runtime_refuses_expected'],rejected);
    for s=1:numel(states),states(s).LabelString=strrep(labels{s},gate,'');end
    [~,bypass]=execute(mdl,a);
    for s=1:numel(states),states(s).LabelString=labels{s};end
    kernel.Script=original;
    expectedTrace=target.trace;heat=expectedTrace(1,132:133);
    w=faultmul(heat,f.work_fraction);src=faultmul(heat,1-f.work_fraction);aux=faultmul(w,a.p(21));
    expectedTrace(1,[134:137 17:20 33:36])=repmat([src w],1,3);
    expectedTrace(1,[150:151 49:50])=[aux aux];
    record([f.id '_bypass_exact_partition_and_copies'],isequal(bypass,expectedTrace));
    record([f.id '_saved_v78_monitor_accepts_same_fault'],isequal(legacy,expectedTrace));
    col=find(expectedTrace(1,:)~=target.trace(1,:));
    faults{end+1}=struct('id',f.id,'base_id',target.id,'row',rowIndex,'columns',col,'event',0, ...
        'work_fraction',f.work_fraction,'input',a.input,'p',a.p,'trace',bypass,'legacy_trace',legacy, ...
        'expected_text',expected,'runtime_rejected',rejected,'error_id',errorId,'error_text',errorText,'injection',injection);
    fd=fopen(fullfile(folder,[f.id '_runtime_fault.txt']),'w');assert(fd>0);fprintf(fd,'%s\\n',errorText);fclose(fd);
    fprintf('PARTITION_CONTROL %s REJECTED=%d V78_ACCEPTED=%d BYPASS_MATCH=%d\\n',f.id,rejected,isequal(legacy,expectedTrace),isequal(bypass,expectedTrace));
end
''' +h[end:]
h=h.replace("'0.78'","'0.79'").replace('energy_commit_v78.mat','hp_partition_v79.mat').replace('ENERGY_COMMIT_V78','HP_PARTITION_V79').replace('DCHR:v78:AuditFailure','DCHR:v79:AuditFailure')
h+='''\nfunction z=faultmul(x,s)
if s==0||all(x==0),z=[0 0];else,v=x*s;z=[v(1)-2*eps(v(1)) v(2)+2*eps(v(2))];end
end
'''
h=h.replace("path=build_hp_partition_v79([a.protocol_ticks a.input],[a.protocol_ticks repmat(a.p,size(a.input,1),1)]);",
    "path=fullfile(root,'matlab','simulink','DCHR_Earliest_Dispatch_Stateflow_v79.slx');\nif ~isfile(path),path=build_hp_partition_v79([a.protocol_ticks a.input],[a.protocol_ticks repmat(a.p,size(a.input,1),1)]);end")
write('matlab/run_hp_partition_v79.m',h)

q=(ROOT/'audit/energy_commit_v78.py').read_text()
# Rename only release-owned paths; inherited production dependencies stay v78.
q=q.replace('energy_commit_v78','hp_partition_v79').replace('Energy_commit','HP_partition').replace('V78','V79').replace('0.78','0.79')
q=q.replace("MODEL='matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v78.slx'","MODEL='matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v79.slx'")
q=q.replace("NEW=['matlab/simulink/monitor_energy_commit_v78.m'","NEW=['matlab/simulink/monitor_hp_partition_v79.m'")
q=q.replace('build_hp_partition_v78','build_hp_partition_v79').replace('run_hp_partition_v78','run_hp_partition_v79').replace('scaffold_hp_partition_v78','scaffold_hp_partition_v79')
q=q.replace('hp_partition_v79','hp_partition_v79')
q=q.replace("from energy_checks_v78 import energy_checks","from energy_checks_v78 import energy_checks\nfrom hp_partition_checks_v79 import hp_checks")
q=q.replace("'audit/energy_checks_v78.py',","'audit/energy_checks_v78.py','audit/hp_partition_checks_v79.py',")
q=q.replace('HP_partition_derivation_v78','HP_partition_derivation_v79')
start=q.index('    spec=json.loads(',q.index('def prepare():'));end=q.index("    folder=ROOT/'results'",start)
q=q[:start]+'''    spec=json.loads((ROOT/'results/energy_commit_v78_20261013T050754_608388Z/spec.json').read_text())
    base=copy.deepcopy(next(c for c in spec['cases'] if c['id']=='HP_only'))
    for eta in [.2,.5,.8]:
        for source in [28.,45.]:
            for inventory in [3.,7.4]:
                c=copy.deepcopy(base);c['id']=f'axes_eta{eta}_source{source}_E{inventory}'
                c['p'][14]=eta;c['p'][11]=source;c['initial'][0]=inventory
                c['family']='HP_temperature_axes';spec['cases'].append(c)
    spec['faults']=[dict(id=name,work_fraction=w,expected='source temperature partition')
        for name,w in [('zero_compressor',0.),('zero_source',1.),('half_work',.5),('tiny_work',.01)]]
    spec.update(version='0.79',scope='SAVED_STATEFLOW_NECESSARY_HP_TEMPERATURE_PARTITION')
'''+q[end:]
q=q.replace("('hp_partition_v79_'", "('hp_partition_v79_'")
q=q.replace("if 'v78' not in p.name","if 'v79' not in p.name")
q=q.replace("'matlab/simulink/monitor_temporal_commit_v77.m']))", "'matlab/simulink/monitor_temporal_commit_v77.m','matlab/simulink/monitor_energy_commit_v78.m','audit/strict_capacity_v78.py']))")
q=q.replace('energy_checks(r)+temporal_checks(r)','hp_checks(r)+energy_checks(r)+temporal_checks(r)')
q=q.replace('cs=energy_checks(bad);changed=[]','cs=hp_checks(bad);changed=[]')
q=q.replace("check('legacy_acceptance',f['id'],", "check('legacy_energy_checks',f['id'],all(c['passed'] for c in energy_checks(bad)))\n            check('legacy_acceptance',f['id'],")
q=q.replace("for rel in ['matlab/simulink/monitor_energy_commit_v78.m'", "for rel in ['matlab/simulink/monitor_hp_partition_v79.m','matlab/simulink/monitor_energy_commit_v78.m'")
q=q.replace("gate='monitor_energy_commit_v78(horizon_input", "gate='monitor_hp_partition_v79(horizon_input")
# The injection anchor is old(2), not u(3), so also verify the helper is absent.
q=q.replace("not any('u(3)==' in s for s in scripts)","not any('u(3)==' in s or 'hp_fault_mul' in s for s in scripts)")
q=q.replace('closed_traces_v78','closed_traces_v79').replace('independent_QA_v78','independent_QA_v79')
write('audit/hp_partition_v79.py',q)
release=(ROOT/'audit/verify_energy_commit_release_v78.py').read_text().replace('energy_commit_v78','hp_partition_v79').replace('v78','v79')
write('audit/verify_hp_partition_release_v79.py',release)
print('Added v79 builder, harness, batch and exact/closed-form reviewer.')
