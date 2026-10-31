"""Additive dimensional-tolerance repair. Prior sources/models are read only."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT/'matlab/simulink'

def write(name, text):
    path = HERE/name
    assert not path.exists(), path
    path.write_text(text, encoding='utf-8')

time = '''function tol=stateflow_time_tolerance_v36(values)
%#codegen
% All inputs and the tolerance are physical HOURS. No energy/power inputs.
assert(all(isfinite(values)) && all(values>=0),'Invalid physical-hour scale.');
tol=64*eps(max(1,max(abs(values))));
% Explicit numerical-resolution contract: never silently relax dwell/clock QA.
assert(tol<=1e-8,'Physical-hour resolution exceeds 1e-8 h budget.');
end
'''
write('stateflow_time_tolerance_v36.m', time)
guard = '''function ok=stateflow_supervisor_guard_v36(target,s,p,c,age)
%#codegen
% Energy comparisons in MWh; dwell comparisons in physical hours.
etol=64*eps(max(1,p(2)));
ttol=stateflow_time_tolerance_v36([age;c(2);c(3)]);
ok=false;
if target==1
    ok=s(17)==3 && s(2)<=c(1)+etol && age>=c(3)-ttol && s(4)>0 && s(16)==0;
else
    ok=s(16)==0 && ((s(17)==2 && s(2)>=p(2)-etol && age>=c(2)-ttol) || ...
        (s(17)==1 && s(4)==0));
end
end
'''
write('stateflow_supervisor_guard_v36.m', guard)
for name in ['stateflow_allocate', 'stateflow_collect', 'stateflow_choose_mode', 'run_stateflow_faults']:
    write(name+'_v36.m', (HERE/(name+'_v34.m')).read_text().replace('v34','v36'))

s=(HERE/'dchr_segment_plan_v34.m').read_text().replace('v34','v36')
s=s.replace('etol=64*eps(max(1,p(2)));ttol=64*eps(max(1,dt));',
'''etol=64*eps(max(1,p(2)));
ptol=64*eps(max(1,max(abs([x(1);x(4);p(3);p(4);p(11);h(1)]))));
ttol=stateflow_time_tolerance_v36([dt;m(2);c(2);c(3)]);''')
s=s.replace('p(7)*p(2)+etol','p(7)*p(2)+ptol')
s=s.replace('remain=dt-offset;reason=0;',
'''ttol=stateflow_time_tolerance_v36([dt;age;c(2);c(3)]);
    remain=dt-offset;reason=0;''')
s=s.replace('age=age+span;offset=offset+span;',
'''assert(age+span>age && offset+span>offset,'DCHR:v36:TimeResolution','Positive segment must advance representable physical clocks.');
    age=age+span;offset=offset+span;''')
write('dchr_segment_plan_v36.m',s)

s=(HERE/'stateflow_contract_gate_v34.m').read_text().replace('v34','v36')
s=s[:s.index('\nfunction ok=stateflow_supervisor_guard_v36')]
s=s.replace('tol=1e-9*max(1,cap+(z(11)+cfg(11))*dt);ptol=tol/max(dt,eps);',
'''% Separate dimensional budgets; energy cancellation does not relax clocks.
    tol=1e-10+64*eps(max(1,cap+(h(1)+cfg(11))*dt)); % MWh
    ptol=1e-9+64*eps(max(1,max(abs([x(1);x(4);h(1);cfg(3);cfg(4);cfg(11)])))); % MW
    ktol=1e-9+64*eps(max(1,max(abs([cfg(10);z(22);z(23)])))); % K
    ctol=1e-10+64*eps(max(1,max(abs([h(3);h(4);(x(3)+273.15)/(x(3)-x(2))])))); % dimensionless
    ttol=stateflow_time_tolerance_v36([dt;prevAge;z(27);z(28);c(2);c(3)]); % h''')
s=s.replace('all(z(16:20)>=-tol)', 'z(16)>=-ptol && all(z(17:19)>=-tol) && z(20)>=-ptol')
s=s.replace('abs(z(11)-z(12)-z(13))*span<=tol && abs(z(11)-z(6)-z(7))*span<=tol',
            'abs(z(11)-z(12)-z(13))<=ptol && abs(z(11)-z(6)-z(7))<=ptol')
s=s.replace('abs(x(4)-z(6)-z(8)-z(9)-z(10))*span<=tol', 'abs(x(4)-z(6)-z(8)-z(9)-z(10))<=ptol')
s=s.replace('abs(z(20)-z(6)-z(8)-z(9))*span<=tol', 'abs(z(20)-z(6)-z(8)-z(9))<=ptol')
s=s.replace('z(15)>=h(3)-ptol && z(15)<=carnot+ptol', 'z(15)>=h(3)-ctol && z(15)<=carnot+ctol')
s=s.replace('abs(z(15)-expectedCOP)<=ptol', 'abs(z(15)-expectedCOP)<=ctol')
s=s.replace('<=tol/cfg(9)', '<=ktol')
s=s.replace("assert(abs(z(3)-offset)<=tol && abs(z(4)-previousE)<=tol", "assert(abs(z(3)-offset)<=ttol && abs(z(4)-previousE)<=tol")
for expr in ['abs(z(27)-s(16))','abs(z(28)-z(27)-span)','abs(z(28)-s(18))','abs(z(27)-prevAge)']:
    s=s.replace(expr+'<=tol',expr+'<=ttol')
s=s.replace('tol=1e-9*max(1,cap+(energy(6)+cfg(11)*dt));',
'''tol=1e-10+64*eps(max(1,cap+energy(6)+cfg(11)*dt));
ttol=stateflow_time_tolerance_v36([dt;prevAge;clock(2);c(2);c(3)]);''')
s=s.replace("assert(abs(offset-dt)<=tol", "assert(abs(offset-dt)<=ttol")
s=s.replace("assert(all(abs(clock-[prevOn;prevAge])<=tol)", "assert(clock(1)==prevOn && abs(clock(2)-prevAge)<=ttol")
s += '\n'+guard+'\n'+time
write('stateflow_contract_gate_v36.m',s)

s=(HERE/'build_dispatch_stateflow_v34.m').read_text().replace('v34','v36').replace('Release 0.34','Release 0.36')
s=s.replace("f.Script=fileread(fullfile(here,'stateflow_supervisor_guard_v36.m'));", """f.Script=fileread(fullfile(here,'stateflow_supervisor_guard_v36.m'));
f=Stateflow.EMFunction(hc);f.Name='stateflow_time_tolerance_v36';f.Position=[340 400 260 70];
f.Script=fileread(fullfile(here,'stateflow_time_tolerance_v36.m'));""")
s=s.replace('assert(abs(age-s(16))<=1e-9);', 'assert(abs(age-s(16))<=stateflow_time_tolerance_v36([age;s(16)]));')
write('build_dispatch_stateflow_v36.m',s)

s=(HERE/'export_stateflow_admissibility_v35.m').read_text().replace('v35','v36').replace('v34','v36')
s=s.replace("'dispatch',{},'segments',{}", "'dispatch',{},'plan',{},'segments',{}")
s=s.replace("'dispatch',[],'segments',[]", "'dispatch',[],'plan',[],'segments',[]")
s=s.replace('item.dispatch=samples', 'item.plan=samples(r.plan_trace_v36,1152);item.dispatch=samples')
# Full-domain harness MATs use a pre-fault variable named baseline.
s=s.replace("saved=load(fullfile(folder,paths(k).name),'result');r=saved.result;", """saved=load(fullfile(folder,paths(k).name));
    if isfield(saved,'result'),r=saved.result;else,r=saved.baseline;end""")
write('export_stateflow_admissibility_v36.m',s)
runner=(ROOT/'audit/run_stateflow_v35.ps1').read_text().replace('v35','v36')
assert not (ROOT/'audit/run_stateflow_v36.ps1').exists()
(ROOT/'audit/run_stateflow_v36.ps1').write_text(runner,encoding='utf-8')
print('Prepared additive v36 production sources.')
