"""Additive uncertainty-aware release. Preserve all previous production files."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, copy
ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'matlab/simulink'

def put(path,text):
    assert not path.exists(),path
    path.write_text(text,encoding='utf-8')

def main():
    ready='''function [ok,margin]=stateflow_dwell_ready_v42(hi,lo,bound,dwell)
%#codegen
% Outward lower endpoint of hi+lo-bound-dwell, in physical hours.
% TwoSum detects downward rounding; no time tolerance authorizes transition.
assert(all(isfinite([hi;lo;bound;dwell])) && hi>=0 && bound>=0 && dwell>=0,'Invalid dwell enclosure.');
a=lower_add(hi,-dwell);b=lower_add(lo,-bound);
margin=lower_add(a,b);ok=margin>=0;
end
function s=lower_add(a,b)
s=a+b;z=s-a;e=(a-(s-z))+(b-z);
assert(isfinite(s) && isfinite(e),'Nonrepresentable dwell comparison.');
if e<0,s=s-eps(abs(s));end
end
'''
    wait='''function t=stateflow_dwell_wait_v42(hi,lo,bound,dwell)
% Normal-mode wait: certify the post-add lower age, including new discard.
[ok,margin]=stateflow_dwell_ready_v42(hi,lo,bound,dwell);
if ok,t=0;return;end
t=-margin;t=t+eps(t);
for k=1:16
    [H,L,B]=stateflow_clock_add_v42(hi,lo,bound,t);
    [ok,shortfall]=stateflow_dwell_ready_v42(H,L,B,dwell);
    if ok,return;end
    extra=max(-shortfall,eps(t));next=t+extra+eps(t);
    assert(isfinite(next) && next>t,'DCHR:v42:DwellResolution','Unresolvable conservative dwell progress.');
    t=next;
end
error('DCHR:v42:DwellResolution','Cannot certify conservative dwell wait.');
end
'''
    put(HERE/'stateflow_dwell_ready_v42.m',ready)
    put(HERE/'stateflow_dwell_wait_v42.m',wait)
    for name in ('build_dispatch_stateflow','dchr_segment_plan','dchr_stateflow_hp','stateflow_allocate',
                 'stateflow_choose_mode','stateflow_collect','stateflow_clock_add','stateflow_supervisor_guard',
                 'stateflow_contract_gate','run_stateflow_faults'):
        text=(HERE/(name+'_v40.m')).read_text().replace('v40','v42').replace('0.40','0.42')
        # Keep independently accepted HP component release unchanged.
        text=text.replace('components.heat_pump_step_v42','components.heat_pump_step_v40')
        if name=='dchr_segment_plan':
            text=text.replace('(age-c(2))+low>=0','stateflow_dwell_ready_v42(age,low,bound,c(2))')
            text=text.replace('(age-c(3))+low>=0','stateflow_dwell_ready_v42(age,low,bound,c(3))')
            text=text.replace('(age-c(2))+low<0','~stateflow_dwell_ready_v42(age,low,bound,c(2))')
            text=text.replace('max(0,(c(3)-age)-low)','stateflow_dwell_wait_v42(age,low,bound,c(3))')
            text=text.replace('t=(c(2)-age)-low;','t=stateflow_dwell_wait_v42(age,low,bound,c(2));')
        if name in ('stateflow_supervisor_guard','stateflow_contract_gate'):
            text=text.replace('c,age,low)','c,age,low,bound)')
            text=text.replace('c,prevAge,prevLow)','c,prevAge,prevLow,prevBound)')
            text=text.replace('(age-c(2))+low>=0','stateflow_dwell_ready_v42(age,low,bound,c(2))')
            text=text.replace('(age-c(3))+low>=0','stateflow_dwell_ready_v42(age,low,bound,c(3))')
            if name=='stateflow_contract_gate':text+='\n'+ready
        if name=='build_dispatch_stateflow':
            text=text.replace('s,p,c,age,low)]','s,p,c,age,low,bound)]')
            marker="for name={'low','bound'}"
            addition="f=Stateflow.EMFunction(hc);f.Name='stateflow_dwell_ready_v42';f.Position=[940 400 260 70];\nf.Script=fileread(fullfile(here,'stateflow_dwell_ready_v42.m'));\n"
            text=text.replace(marker,addition+marker)
            text=text.replace('physical-hour elapsed timer.','uncertainty-aware physical-hour elapsed timer.')
        put(HERE/(name+'_v42.m'),text)
    for name in ('run_stateflow_clock','export_stateflow_clock'):
        text=(HERE/(name+'_v41.m')).read_text().replace('v41','v42').replace('v40','v42').replace('0.41','0.42').replace('0.40','0.42')
        text=text.replace('new_model,false','new_model,true').replace("'new_model',false","'new_model',true")
        text=text.replace("'heat_pump_step_v42.m'","'heat_pump_step_v40.m'")
        text=text.replace('% Fresh execution of immutable v42','% Fresh execution of saved uncertainty-aware v42')
        if name=='run_stateflow_clock':
            marker="writejson(fullfile(folder,'execution_v42.json'),outputs);"
            text=text.replace(marker,"faults=run_stateflow_faults_v42(mdl,folder,cases{1});\nwritejson(fullfile(folder,'faults_v42.json'),faults);\nrecord('actual_runtime_fault_rejections',all([faults.rejected]));\n"+marker)
        put(HERE/(name+'_v42.m'),text)
    launcher=(ROOT/'audit/run_stateflow_clock_v41.ps1').read_text().replace('v41','v42')
    put(ROOT/'audit/run_stateflow_clock_v42.ps1',launcher)
    prior=ROOT/'audit/stateflow_clock_spec_v41_20261010T125621_525409Z/cases.json'
    cases=copy.deepcopy(json.loads(prior.read_text())['cases'])
    sup=json.loads((ROOT/'audit/stateflow_clock_spec_v41_20261010T125838_905451Z/cases.json').read_text())
    cases+=copy.deepcopy(sup['cases'])
    # Nonzero-enclosure clocks persist across sample boundaries; energy event
    # can interrupt a certified wait and force recomputation.
    for on in (0,1):
        base=copy.deepcopy(next(c for c in cases if c['id']==('on' if on else 'off')+'_uncertain_equal'))
        base.update(id=('on' if on else 'off')+'_persistent_wait',kind='persistent_clock',
                    initial_clock=[on,.8,0.,1e-9],inputs=base['inputs']*5)
        cases.append(base)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    folder=ROOT/'audit'/('stateflow_clock_spec_v42_'+stamp);folder.mkdir()
    put(folder/'cases.json',json.dumps(dict(version='0.42',model_release='0.42',new_model=True,cases=cases,
        assumptions='Numerical engineering fixtures. Dwell requires lower age enclosure; no measured equipment/primary equations.'),indent=2)+'\n')
    preserve=[]
    for parent in ('matlab','audit'):
        for path in (ROOT/parent).rglob('*'):
            if path.is_file() and path.suffix in ('.m','.slx') and '_v42' not in path.name and path.parent.name!='slprj':
                preserve.append(dict(path=path.relative_to(ROOT).as_posix(),bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    put(folder/'preservation.json',json.dumps(dict(files=preserve),indent=2)+'\n')
    print('SPEC='+folder.relative_to(ROOT).as_posix())
if __name__=='__main__':main()
