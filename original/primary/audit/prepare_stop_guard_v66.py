"""Additive sampled stop-guard release; never overwrite accepted artifacts."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, shutil
ROOT=Path(__file__).resolve().parents[1]

def write_new(path, text):
    assert not path.exists(), path
    path.write_text(text, encoding='utf-8')

def main():
    for name in ['build_interval_dispatch', 'interval_dispatch_kernel', 'interval_service_core']:
        src=ROOT/'matlab/simulink'/f'{name}_v65.m'
        text=src.read_text().replace('v65','v66').replace('V65','V66')
        text=text.replace('==65','==66').replace('=65;','=66;')
        if name!='build_interval_dispatch':
            anchor='want=u(6)+chargeBound;'
            guard="""% A sampled charge must stay below the thermal stop for the ENTIRE
% held interval. E(t)<=E.upper+etaC*qcharge*dt because loss>=0.
% If the proposed charge cannot be certified, withhold it for this sample.
% This permits early sampled OFF; it does not choose an event-root midpoint.
stopRoom=minusiv(P(stop(1)),P(initial(2)));
growth=muliv(muliv(P(p(7)),P(chargeBound)),dt);
if chargeBound>0&&growth(2)>=stopRoom(1),chargeBound=0;end
"""
            assert text.count(anchor)==1
            text=text.replace(anchor,guard+anchor)
            anchor="assert(charge*dis==0,'v66 exclusive TES ports');"
            text=text.replace(anchor,anchor+"\nassert(charge==0||en(2)<stop(1),'v66 held thermal stop');")
        write_new(ROOT/'matlab/simulink'/f'{name}_v66.m',text)
    text=(ROOT/'matlab/run_interval_dispatch_v65.m').read_text().replace('v65','v66').replace('V65','V66').replace('0.65','0.66').replace('==65','==66')
    text=text.replace("record([c.id '_cutoff']", "record([c.id '_thermal_stop'],all(trace(service,122)==0|trace(service,38)<cfg(36)*(cfg(60)-cfg(37))));\n    record([c.id '_cutoff']")
    # Execute an unchanged saved-v65 counterexample before testing the repair.
    anchor="checks=struct('name',{},'passed',{});runs={};faults={};"
    extra="""
oldmdl='DCHR_Interval_Dispatch_Stateflow_v65';load_system(fullfile(root,'matlab','simulink',[oldmdl '.slx']));
w=spec.witness;mw=get_param(oldmdl,'ModelWorkspace');
assignin(mw,'dispatch_input_v65',[0 w.input]);assignin(mw,'dispatch_cfg_v65',[0 w.cfg]);
oldout=sim(oldmdl,'StopTime','0','ReturnWorkspaceOutputs','on');
oldtrace=reshape(oldout.interval_trace_v65.Data,205,[])';
save(fullfile(folder,'saved_v65_witness.mat'),'oldout','oldtrace','w','-v7.3');
baseline_witness=struct('cfg',w.cfg,'input',w.input,'trace',oldtrace);
writejson('baseline_witness.json',baseline_witness);close_system(oldmdl,0);
record('saved_v65_stop_overshoot_reproduced',oldtrace(37)>w.cfg(36)*(w.cfg(60)-w.cfg(37)));
"""
    assert anchor in text;text=text.replace(anchor,anchor+extra)
    text=text.replace("'new_model',true,'runs'", "'new_model',true,'baseline_witness',baseline_witness,'runs'")
    write_new(ROOT/'matlab/run_interval_dispatch_v66.m',text)
    script=(ROOT/'audit/run_interval_dispatch_v65.ps1').read_text().replace('v65','v66')
    write_new(ROOT/'audit/run_interval_dispatch_v66.ps1',script)
    folder=ROOT/'results'/('stop_guard_v66_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'));folder.mkdir()
    spec=json.loads((ROOT/'results/interval_dispatch_v65_20261011T212742_987732Z/spec.json').read_text())
    spec['version']='0.66';c=spec['cases'][0]['cfg']
    witness=dict(id='stop_overshoot_repair',cfg=c,input=[[1,0,.5,0,.5,0,20,1,1,9.5,1,1]],expected_modes=[0])
    spec['witness']=dict(cfg=c,input=witness['input'][0]);spec['cases'].insert(0,witness)
    # Four charge/cutoff cycles at each of three exact binary timesteps.
    for dt in [.25,.5,1.0]:
        inputs=[];t=0
        for cycle in range(4):
            for span,demand,source,enable,charge in [(10,0,20,1,1),(2,6,0,0,0),(1,0,0,0,0)]:
                for _ in range(int(span/dt)):
                    t+=dt;inputs.append([1,0,t,0,dt,demand,source,enable,charge,7.9,1,1])
        spec['cases'].insert(-1,dict(id='repeated_'+str(dt).replace('.','p'),cfg=c,input=inputs,expected_modes=[0,2,5]))
    (folder/'spec.json').write_text(json.dumps(spec,indent=2)+'\n')
    preserved=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))+list(ROOT.glob('STATUS*.json'))+list(ROOT.glob('MASTER_STAGEBOARD*.md'))
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    (folder/'preservation.json').write_text(json.dumps([dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in preserved if 'v66' not in p.name],indent=2)+'\n')
    print(folder.relative_to(ROOT).as_posix())

if __name__=='__main__':main()
