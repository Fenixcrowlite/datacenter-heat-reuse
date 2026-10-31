"""Additive release scaffolder. Exclusive creation preserves accepted files."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def write(rel, text):
    with (ROOT/rel).open('x', encoding='utf-8', newline='\n') as f:
        f.write(text)


b = (ROOT/'matlab/simulink/build_hp_partition_v79.m').read_text()
b = b.replace('build_hp_partition_v79', 'build_standing_loss_v80').replace('DCHR_Earliest_Dispatch_Stateflow_v79', 'DCHR_Earliest_Dispatch_Stateflow_v80')
anchor = "f=Stateflow.EMFunction(ch);f.Name='earliest_mode_v73';"
b = b.replace(anchor, "f=Stateflow.EMFunction(ch);f.Name='monitor_standing_loss_v80';f.Position=[2050 800 380 90];f.Script=fileread(fullfile(here,'monitor_standing_loss_v80.m'));\n"+anchor)
b = b.replace('monitor_hp_partition_v79(horizon_input,policy_input,retained_memory,core);', 'monitor_standing_loss_v80(horizon_input,policy_input,retained_memory,core);')
b = b.replace('v79 pre-commit HP partition/energy/temporal-monitored', 'v80 pre-commit standing-loss/HP/energy/temporal-monitored').replace('BUILT_HP_PARTITION_STATEFLOW_V79', 'BUILT_STANDING_LOSS_STATEFLOW_V80')
write('matlab/simulink/build_standing_loss_v80.m', b)
write('audit/run_standing_loss_v80.ps1', (ROOT/'audit/run_hp_partition_v79.ps1').read_text().replace('run_hp_partition_v79', 'run_standing_loss_v80'))

h = (ROOT/'matlab/run_hp_partition_v79.m').read_text()
h = h.replace('run_hp_partition_v79', 'run_standing_loss_v80').replace('build_hp_partition_v79', 'build_standing_loss_v80')
h = h.replace('DCHR_Earliest_Dispatch_Stateflow_v79', 'DCHR_Earliest_Dispatch_Stateflow_v80').replace("prior='DCHR_Earliest_Dispatch_Stateflow_v78'", "prior='DCHR_Earliest_Dispatch_Stateflow_v79'")
h = h.replace('monitor_hp_partition_v79(horizon_input', 'monitor_standing_loss_v80(horizon_input').replace('bitwise_saved_v78', 'bitwise_saved_v79').replace('PARTITION_V79', 'STANDING_LOSS_V80')
start = h.index("target=runs{find(")
end = h.index("record('restored_kernel'", start)
h = h[:start] + r'''for j=1:numel(spec.faults)
    f=spec.faults(j);target=runs{find(cellfun(@(r)strcmp(r.id,f.base_id),runs),1)};
    a=target.adapter;assert(size(target.trace,1)==1&&target.trace(1,13)==1);
    assert(all(target.trace(1,124:129)==0));
    % Change one passive record after the physical kernel, keeping copies and
    % first law consistent. Instrumented charts are never saved.
    injection=sprintf(['\nif old(2)==0\n' ...
        'y(113:114)=[%.17g;%.17g];y(5:6)=y(113:114);\n' ...
        'y(138:139)=[%.17g;%.17g];y(21:22)=y(138:139);y(37:38)=y(138:139);\n' ...
        'y(53:54)=minusiv(minusiv(y(51:52)\x27,y(5:6)\x27),y(37:38)\x27)\x27;\nend\n'], ...
        f.endpoint,f.endpoint,f.loss,f.loss);
    anchor="y(57)=limit;y(62:65)=[ageCert;ageHi;ageErr'];";
    assert(numel(strfind(original,anchor))==1);
    mutated=char(strrep(original,anchor,[char(anchor) injection]));
    kernel.Script=mutated;priorKernel.Script=mutated;
    [~,legacy]=execute(prior,a);priorKernel.Script=original;
    expected=['v80 ' f.expected];errorText='';errorId='';rejected=false;
    try,execute(mdl,a);catch e,errorText=getReport(e,'extended','hyperlinks','off');errorId=e.identifier;rejected=contains(errorText,expected);end
    record([f.id '_runtime_refuses_expected'],rejected);
    for s=1:numel(states),states(s).LabelString=strrep(labels{s},gate,'');end
    [~,bypass]=execute(mdl,a);
    for s=1:numel(states),states(s).LabelString=labels{s};end
    kernel.Script=original;
    expectedTrace=target.trace;
    expectedTrace(1,[5:6 113:114])=f.endpoint;
    expectedTrace(1,[21:22 37:38 138:139])=f.loss;
    law=minusiv_test(minusiv_test(expectedTrace(1,51:52),expectedTrace(1,5:6)),expectedTrace(1,37:38));
    expectedTrace(1,53:54)=law;
    record([f.id '_bypass_exact_endpoint_loss_and_copies'],isequal(bypass,expectedTrace));
    record([f.id '_saved_v79_monitor_accepts_same_fault'],isequal(legacy,expectedTrace));
    col=find(expectedTrace(1,:)~=target.trace(1,:));
    faults{end+1}=struct('id',f.id,'base_id',target.id,'row',1,'columns',col,'event',0, ...
        'endpoint',f.endpoint,'loss',f.loss,'input',a.input,'p',a.p,'trace',bypass,'legacy_trace',legacy, ...
        'expected_trace',expectedTrace,'expected_text',expected,'runtime_rejected',rejected,'error_id',errorId,'error_text',errorText,'injection',injection);
    fd=fopen(fullfile(folder,[f.id '_runtime_fault.txt']),'w');assert(fd>0);fprintf(fd,'%s\n',errorText);fclose(fd);
    fprintf('LOSS_CONTROL %s REJECTED=%d V79_ACCEPTED=%d BYPASS_MATCH=%d\n',f.id,rejected,isequal(legacy,expectedTrace),isequal(bypass,expectedTrace));
end
''' + h[end:]
# MATLAB sprintf uses a literal apostrophe encoded inside a double-quoted
# fragment, avoiding shell quoting; materialize the character in script text.
h = h.replace('\\x27', "'")
# Escape the apostrophes inside the MATLAB single-quoted sprintf fragment.
h = h.replace("'y(53:54)=minusiv(minusiv(y(51:52)',y(5:6)'),y(37:38)')';", "unused") if False else h
h = h.replace("'y(53:54)=minusiv(minusiv(y(51:52)',y(5:6)'),y(37:38)')';", "'y(53:54)=minusiv(minusiv(y(51:52)'',y(5:6)''),y(37:38)'')'';")
# Directly replace the entire source line with correct doubled apostrophes.
lines = h.splitlines()
for i, line in enumerate(lines):
    if "'y(53:54)=minusiv" in line:
        lines[i] = "        'y(53:54)=minusiv(minusiv(y(51:52)'',y(5:6)''),y(37:38)'')'';\\nend\\n'], ..."
h = '\n'.join(lines)+'\n'
h = h.replace("'0.79'", "'0.80'").replace('hp_partition_v79.mat', 'standing_loss_v80.mat').replace('DCHR:v79:AuditFailure', 'DCHR:v80:AuditFailure')
h = h[:h.index('\nfunction z=faultmul')] + r'''
function z=minusiv_test(x,y)
if all(y==0),z=x;elseif x(1)==x(2)&&y(1)==y(2)&&x(1)==y(1),z=[0 0];
else,t=[x(1)-y(2) x(2)-y(1)];z=[t(1)-2*eps(t(1)) t(2)+2*eps(t(2))];end
end
'''
write('matlab/run_standing_loss_v80.m', h)

q = (ROOT/'audit/hp_partition_v79.py').read_text()
q = q.replace('from hp_partition_checks_v79 import hp_checks', 'from hp_partition_checks_v79 import hp_checks\nfrom standing_loss_checks_v80 import loss_checks')
q = q.replace("MODEL='matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v79.slx'", "MODEL='matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v80.slx'")
start = q.index('NEW='); end = q.index('LEDGERS=', start)
q = q[:start]+"""NEW=['matlab/simulink/monitor_standing_loss_v80.m','matlab/simulink/build_standing_loss_v80.m',
     'matlab/run_standing_loss_v80.m','audit/run_standing_loss_v80.ps1',
     'audit/scaffold_standing_loss_v80.py','audit/standing_loss_v80.py',
     'audit/standing_loss_checks_v80.py','audit/Standing_loss_derivation_v80.md',
     'audit/hp_partition_checks_v79.py','matlab/simulink/monitor_hp_partition_v79.m']
"""+q[end:]
start = q.index('    spec=json.loads(', q.index('def prepare():'));end = q.index("    preserved=", start)
q = q[:start]+'''    spec=json.loads((ROOT/'results/hp_partition_v79_20261013T053839_629571Z/spec.json').read_text())
    base=copy.deepcopy(next(c for c in spec['cases'] if c['id']=='zero_demand'))
    for lam in [0.,.01,.5,1.]:
        for E in [0.,3.,9.]:
            c=copy.deepcopy(base);c['id']=f'passive_lambda{lam}_E{E}'
            c['p'][5]=lam;c['initial'][0]=E
            c['schedule']=[[1.,1.,0.,0.,0.,0.]]
            c['family']='loss_rate_axes';spec['cases'].append(c)
    spec['faults']=[
        dict(id='invented_loss_zero_lambda',base_id='passive_lambda0.0_E3.0',endpoint=2.,loss=1.,expected='zero coefficient standing loss'),
        dict(id='suppressed_positive_decay',base_id='passive_lambda0.5_E3.0',endpoint=3.,loss=0.,expected='standing loss rate'),
        dict(id='excess_positive_decay',base_id='passive_lambda0.01_E3.0',endpoint=2.,loss=1.,expected='standing loss rate'),
        dict(id='deficient_positive_decay',base_id='passive_lambda0.5_E3.0',endpoint=2.875,loss=.125,expected='standing loss rate')]
    spec.update(version='0.80',scope='SAVED_STATEFLOW_NECESSARY_TES_CONSTITUTIVE_LOSS')
    folder=ROOT/'results'/('standing_loss_v80_'+stamp());folder.mkdir();dump(folder/'spec.json',spec)
''' +q[end:]
q=q.replace("if 'v79' not in p.name", "if 'v80' not in p.name")
q=q.replace("folder/'hp_partition_v79.mat'", "folder/'standing_loss_v80.mat'")
q=q.replace('hp_checks(r)+energy_checks(r)+temporal_checks(r)', 'loss_checks(r)+hp_checks(r)+energy_checks(r)+temporal_checks(r)')
q=q.replace('cs=hp_checks(bad);changed=[]', 'cs=loss_checks(bad);changed=[]')
q=q.replace("check('legacy_energy_checks',f['id'],all(c['passed'] for c in energy_checks(bad)))", "check('legacy_energy_HP_temporal_checks',f['id'],all(c['passed'] for c in energy_checks(bad)+hp_checks(bad)+temporal_checks(bad)))\n            check('exact_fault_trace',f['id'],mutated==rows(f['expected_trace']))\n            mapped=copy.deepcopy(bad)\n            for rr in rows(mapped['trace']):rr[1]=73;rr[72:75]=[0,0,0]\n            nonlinear,_=analyze(mapped)\n            check('independent_ODE_rejection',f['id'],any(not c['passed'] for c in nonlinear if c['name'].endswith('_inventory_end') or c['name'].endswith('_energy_3')))")
q=q.replace("for rel in ['matlab/simulink/monitor_hp_partition_v79.m'", "for rel in ['matlab/simulink/monitor_standing_loss_v80.m','matlab/simulink/monitor_energy_commit_v78.m','matlab/simulink/monitor_hp_partition_v79.m'")
q=q.replace("gate='monitor_hp_partition_v79(horizon_input", "gate='monitor_standing_loss_v80(horizon_input")
q=q.replace('closed_traces_v79_', 'closed_traces_v80_').replace('independent_QA_v79_', 'independent_QA_v80_').replace("version='0.79'", "version='0.80'")
anchor="    check('Stateflow','six_actual_modes'"
pos=q.index(anchor)
q=q[:pos]+'''    # Separate reviewer controls: zero lambda, positive lambda and a wide
    # overlapping hull acceptance witness document the necessary-only scope.
    for name in ['invented_loss_zero_lambda','suppressed_positive_decay']:
        f=next(x for x in report['faults'] if x['id']==name)
        bad=copy.deepcopy(by_id[f['base_id']]);bad['trace']=copy.deepcopy(f['trace'])
        selfchecks.append(dict(name='loss_control_'+name,passed=any(not c['passed'] for c in loss_checks(bad))))
    bad=copy.deepcopy(by_id['passive_lambda0.5_E3.0'])
    rows(bad['trace'])[0][137:139]=[0.,3.]
    selfchecks.append(dict(name='wide_loss_overlap_scope_witness',passed=all(c['passed'] for c in loss_checks(bad))))
''' +q[pos:]
write('audit/standing_loss_v80.py', q)
print('Added versioned v80 builder, actual runtime harness and independent reviewer.')
