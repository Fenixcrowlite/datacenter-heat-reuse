"""Create additive canonical-endpoint release; preserve every prior source/model."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil
ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'matlab/simulink'
def put(p,s):
    assert not p.exists(),p
    p.write_text(s,encoding='utf-8')
def main():
    for name in ('build_dispatch_stateflow','dchr_segment_plan','dchr_stateflow_hp',
                 'stateflow_allocate','stateflow_choose_mode','stateflow_collect',
                 'stateflow_contract_gate'):
        s=(HERE/(name+'_v42.m')).read_text().replace('v42','v51').replace('0.42','0.51')
        # Unchanged compensated clock, certified dwell and supervisor implementations.
        for helper in ('stateflow_clock_add','stateflow_dwell_ready','stateflow_dwell_wait','stateflow_supervisor_guard'):
            s=s.replace(helper+'_v51',helper+'_v42')
        if name=='build_dispatch_stateflow':
            s=s.replace("for k=1:3\n    f=Stateflow.EMFunction(ch)","functions{4}='stateflow_tes_endpoint_v51';\nfor k=1:4\n    f=Stateflow.EMFunction(ch)")
        if name=='stateflow_allocate':
            a=s.index('P=cfg(5)*qc');b=s.index('lc=(1-cfg(5))',a)
            s=s[:a]+'[endpoint,standing]=stateflow_tes_endpoint_v51(A,qc,qd,cfg,span,seg(13));\n'+s[b:]
        if name=='dchr_segment_plan':
            s=s.replace('if abs(E-p(2))<=etol,E=p(2);end\n    if abs(E-p(8))<=etol,E=p(8);end',
                        'atCapacity=abs(E-p(2))<=etol; % classify without changing initial inventory')
            s=s.replace('E==p(2)','atCapacity').replace('if E>p(8),','if E>p(8)+etol,')
            s=s.replace('E=advance(E,P,p(7),span);\n    if kind==1,E=p(2);elseif kind==2,E=p(8);end',
                        'E=stateflow_tes_endpoint_v51(E,qc,qd,p,span,kind);')
            s=s.replace('E=advance(E,P,p(7),extra);offset=dt;',
                        'E=stateflow_tes_endpoint_v51(plan(2,count),qc,qd,p,plan(1,count),kind);offset=dt;')
            a=s.index('function E=advance(');b=s.index('function u=hp(',a);s=s[:a]+s[b:]
        if name=='stateflow_contract_gate':
            s=s.replace("assert(abs(z(3)-offset)<=ttol && abs(z(4)-previousE)<=tol,'Ordered event/energy handoff failure.');",
                        "assert(abs(z(3)-offset)<=ttol && z(4)==previousE,'Ordered event/energy handoff failure.');")
        put(HERE/(name+'_v51.m'),s)
    for name in ('run_annual_sensitivity','export_annual_sensitivity','export_annual_sensitivity_binary'):
        s=(ROOT/'matlab'/(name+'_v50.m')).read_text().replace('v50','v51').replace('V50','V51').replace('0.50','0.51').replace('v42','v51').replace('0.42','0.51')
        if name=='run_annual_sensitivity':
            s=s.replace("'new_model',false","'new_model',true").replace('preserved actual saved-v51','new actual saved-v51')
            # Baseline comparison is approximate: canonical endpoint changes roundoff.
            s=s.replace('max(abs(delta),[],\'all\')<1e-10','max(abs(delta),[],\'all\')<1e-8')
        put(ROOT/'matlab'/(name+'_v51.m'),s)
    put(ROOT/'audit/run_stateflow_padding_v51.ps1',(ROOT/'audit/run_annual_sensitivity_v50.ps1').read_text().replace('annual_sensitivity_v50','stateflow_padding_v51').replace('Annual_sensitivity_execution_v50','Stateflow_padding_execution_v51'))
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    folder=ROOT/'results'/('stateflow_padding_v51_'+stamp);folder.mkdir()
    old=json.loads((ROOT/'STATUS_v50.json').read_text());prior=ROOT/old['result_directory']
    spec=json.loads((prior/'spec.json').read_text());spec.update(version='0.51',model_version='0.51',new_model=True,defect_evidence=old['result_directory'])
    (folder/'spec.json').write_text(json.dumps(spec,indent=2)+'\n')
    paths=set()
    for pat in ('STATUS*.json','MASTER_STAGEBOARD*.md','matlab/**/*.m','matlab/simulink/*.slx','audit/*v50*'):
        paths.update(ROOT.glob(pat))
    paths.update(prior.rglob('*'))
    entries=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(paths) if p.is_file() and 'v51' not in p.name and 'local_build' not in p.parts and '__pycache__' not in p.parts]
    (folder/'preservation.json').write_text(json.dumps(entries,indent=2)+'\n')
    print(folder.relative_to(ROOT).as_posix())
if __name__=='__main__':main()
