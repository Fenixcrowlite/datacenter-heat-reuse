"""Additive numerical-domain repair; preserved models/sources are read only."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'matlab/simulink'
def write(path,text):
    assert not path.exists(),path
    path.write_text(text,encoding='utf-8')
def create(name,text):write(HERE/name,text)

clock='''function [hi,lo,bound]=stateflow_clock_add_v38(hi,lo,bound,dt)
%#codegen
% TwoSum expansion in HOURS. bound encloses discarded low-order roundoff.
assert(all(isfinite([hi;lo;bound;dt])) && hi>=0 && bound>=0 && dt>=0,'Invalid compensated clock.');
stateflow_time_tolerance_v36([hi;dt]);
assert(abs(lo)<=eps(max(1,hi)) && abs(lo)+bound<=1e-8,'Clock cumulative accuracy budget exceeded.');
if dt==0,return;end
[s,e]=twosum(hi,dt);
[r,discard]=twosum(lo,e);
[hi,lo]=twosum(s,r);
candidate=bound+abs(discard);
% Conservative upward allowance, including when the addition rounds down.
if discard~=0,bound=candidate+eps(candidate);end
assert(isfinite(hi) && isfinite(lo) && abs(lo)+bound<=1e-8,'Clock cumulative accuracy budget exceeded.');
stateflow_time_tolerance_v36([hi;dt]);
end
function [s,e]=twosum(a,b)
s=a+b;z=s-a;e=(a-(s-z))+(b-z);
end
'''
create('stateflow_clock_add_v38.m',clock)
guard=(HERE/'stateflow_supervisor_guard_v36.m').read_text().replace('v36(target,s,p,c,age)','v38(target,s,p,c,age,low)')
guard=guard.replace('age>=c(3)-ttol','(age-c(3))+low>=0').replace('age>=c(2)-ttol','(age-c(2))+low>=0')
create('stateflow_supervisor_guard_v38.m',guard)
for name in ('stateflow_allocate','stateflow_collect','stateflow_choose_mode'):
    create(name+'_v38.m',(HERE/(name+'_v36.m')).read_text().replace('v36','v38'))

component=(ROOT/'matlab/+dchr/+components/heat_pump_step_v14.m').read_text().replace('v14','v38').replace('V14','V38')
start=component.index('a=nominal*(1-penalty); b=nominal*penalty/cap;')
end=component.index('% The lower bound',start)
component=component[:start]+'''% Normalize only after bounding Q<=capacity; no COP/MW slope is formed.
fraction=0;
if penalty>0,fraction=max(0,(double(cfg.hp.cop_min)/nominal-(1-penalty))/penalty);end
lower=cap*fraction;
if fraction>0 && lower==0
    error('DCHR:v38:HPResolution','Minimum operating output underflows.');
end
'''+component[end:]
component=component.replace('evaporator(lower,a,b)','evaporator(lower,cap,nominal,penalty)').replace('evaporator(upper,a,b)','evaporator(upper,cap,nominal,penalty)').replace('evaporator(middle,a,b)','evaporator(middle,cap,nominal,penalty)').replace('cop=a+b*q;','cop=nominal*(1-penalty+penalty*(q/cap));\nif ~isfinite(cop) || q/cop==0 || cop<cfg.hp.cop_min-32*eps(max(1,cop))\n    error(\'DCHR:v38:HPResolution\',\'Operating COP/electricity cannot be represented.\');\nend')
component=component.replace('function qev=evaporator(q,a,b)','function qev=evaporator(q,cap,nominal,penalty)').replace('qev=q-q/(a+b*q);','qev=q-q/(nominal*(1-penalty+penalty*(q/cap)));')
write(ROOT/'matlab/+dchr/+components/heat_pump_step_v38.m',component)
create('dchr_stateflow_hp_v38.m',(HERE/'dchr_stateflow_hp_v30.m').read_text().replace('v30','v38').replace('storage_step_v38','storage_step_v30').replace('heat_pump_step_v14','heat_pump_step_v38'))

s=(HERE/'dchr_segment_plan_v36.m').read_text().replace('v36','v38').replace('stateflow_time_tolerance_v38','stateflow_time_tolerance_v36').replace('dchr_stateflow_hp_v30','dchr_stateflow_hp_v38').replace('heat_pump_step_v14','heat_pump_step_v38')
s=s.replace('numel(m)==2','numel(m)==4').replace('m(2)>=0','m(2)>=0 && m(4)>=0')
s=s.replace('plan=zeros(18,64);on=m(1);age=m(2);offset=0;count=0;','''plan=zeros(22,64);on=m(1);age=m(2);low=m(3);bound=m(4);offset=0;count=0;
stateflow_clock_add_v38(age,low,bound,0);''')
s=s.replace('etol=64*eps(max(1,p(2)));','''etol=64*eps(max(1,p(2)));
assert(p(2)-c(1)>2*etol && c(1)-p(8)>2*etol && p(8)>2*etol, ...
    'DCHR:v38:BandResolution','Unresolved capacity/restart/cutoff tolerance bands.');''')
s=s.replace('age>=c(2)-ttol','(age-c(2))+low>=0').replace('age>=c(3)-ttol','(age-c(3))+low>=0').replace('age<c(2)-ttol','(age-c(2))+low<0')
s=s.replace('age=0;reason=','age=0;low=0;bound=0;reason=')
s=s.replace('max(0,c(3)-age)','max(0,(c(3)-age)-low)').replace('t=c(2)-age','t=(c(2)-age)-low')
s=s.replace('if t>ttol && t<span','if t>0 && t<span')
s=s.replace('plan(:,count)=[span;E;x(4);u(1:3);request;u(4:6);qc;qd;kind;offset;on;age;reason;age+span];','''[nextAge,nextLow,nextBound]=stateflow_clock_add_v38(age,low,bound,span);
    plan(:,count)=[span;E;x(4);u(1:3);request;u(4:6);qc;qd;kind;offset;on;age;reason;nextAge;low;nextLow;bound;nextBound];''')
s=s.replace("assert(age+span>age && offset+span>offset,'DCHR:v38:TimeResolution','Positive segment must advance representable physical clocks.');\n    age=age+span;offset=offset+span;","assert(offset+span>offset,'DCHR:v38:TimeResolution','Positive segment must advance macro offset.');\n    age=nextAge;low=nextLow;bound=nextBound;offset=offset+span;")
s=s.replace('extra=dt-offset;plan(1,count)=plan(1,count)+extra;plan(18,count)=age+extra;\n        E=advance(E,P,p(7),extra);age=age+extra;offset=dt;','''extra=dt-offset;plan(1,count)=plan(1,count)+extra;
        % Recompute from original clock and complete span to match supervisor.
        [age,low,bound]=stateflow_clock_add_v38(plan(16,count),plan(19,count),plan(21,count),plan(1,count));
        plan(18,count)=age;plan(20,count)=low;plan(22,count)=bound;
        E=advance(E,P,p(7),extra);offset=dt;''')
s=s.replace('dt;on;age;0;age]','dt;on;age;0;age;low;low;bound;bound]')
create('dchr_segment_plan_v38.m',s)

s=(HERE/'stateflow_contract_gate_v36.m').read_text().replace('v36','v38').replace('stateflow_time_tolerance_v38','stateflow_time_tolerance_v36')
s=s[:s.index('\nfunction ok=stateflow_supervisor_guard_v38')]
s=s.replace('prevAge=m(2);','prevAge=m(2);prevLow=m(3);prevBound=m(4);')
s=s.replace('h(5)*z(11)/h(1)','h(5)*(z(11)/h(1))')
s=s.replace('c,prevAge)','c,prevAge,prevLow)')
s=s.replace('prevOn=z(26);prevAge=z(28);','''[wantedAge,wantedLow,wantedBound]=stateflow_clock_add_v38(s(16),s(19),s(21),span);
    assert(s(18)==wantedAge && s(20)==wantedLow && s(22)==wantedBound,'Compensated segment clock mismatch.');
    if z(26)~=prevOn
        assert(s(19)==0 && s(21)==0,'Clock residual/bound reset failure.');
    else
        assert(s(19)==prevLow && s(21)==prevBound,'Persistent residual/bound continuity failure.');
    end
    prevLow=s(20);prevBound=s(22);
    prevOn=z(26);prevAge=z(28);''')
s=s.replace('nextClock=clock;','''assert(clock(3)==prevLow && clock(4)==prevBound,'Supervisor residual/bound mismatch.');
stateflow_clock_add_v38(clock(2),clock(3),clock(4),0);
nextClock=clock;''')
s += '\n'+guard+'\n'+clock+'\n'+(HERE/'stateflow_time_tolerance_v36.m').read_text()
create('stateflow_contract_gate_v38.m',s)

s=(HERE/'build_dispatch_stateflow_v36.m').read_text().replace('v36','v38').replace('Release 0.36','Release 0.38')
s=s.replace('[1;0]','[1;0;0;0]').replace('plan=zeros(18,64)','plan=zeros(22,64)').replace('[18 1]','[22 1]').replace('[2 1]','[4 1]')
pos=s.index("f=Stateflow.EMFunction(hc);f.Name='stateflow_time_tolerance_v38'")
end=s.index('hs=cell(2,1);',pos)
s=s[:pos]+'''f=Stateflow.EMFunction(hc);f.Name='stateflow_time_tolerance_v36';f.Position=[340 400 260 70];
f.Script=fileread(fullfile(here,'stateflow_time_tolerance_v36.m'));
f=Stateflow.EMFunction(hc);f.Name='stateflow_clock_add_v38';f.Position=[640 400 260 70];
f.Script=fileread(fullfile(here,'stateflow_clock_add_v38.m'));
for name={'low','bound'}
    d=Stateflow.Data(hc);d.Name=name{1};d.Scope='Local';d.DataType='double';d.Props.InitialValue='0';
end
'''+s[end:]
s=s.replace('age=s(16);\\n','age=s(16);low=s(19);bound=s(21);\\n').replace('age=age+s(1);\\nclock=[%d;age];','[age,low,bound]=stateflow_clock_add_v38(age,low,bound,s(1));\\nclock=[%d;age;low;bound];')
s=s.replace('stateflow_time_tolerance_v38([age;s(16)])','stateflow_time_tolerance_v36([age;s(16)])')
s=s.replace("'age=age+s(1);\\nclock=[%d;age];'","'assert(low==s(19) && bound==s(21));\\n[age,low,bound]=stateflow_clock_add_v38(age,low,bound,s(1));\\nclock=[%d;age;low;bound];'")
s=s.replace('s,p,c,age)]','s,p,c,age,low)]')
create('build_dispatch_stateflow_v38.m',s)
write(ROOT/'audit/run_stateflow_v38.ps1',(ROOT/'audit/run_stateflow_v37.ps1').read_text().replace('v37','v38'))
print('Prepared additive v38 component and model sources')
