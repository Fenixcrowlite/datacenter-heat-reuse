"""Preserve development sources/model, then complete observer trace provenance."""
from pathlib import Path
from datetime import datetime, timezone
import shutil, json, hashlib
ROOT=Path(__file__).resolve().parents[1]
dev=ROOT/'results/event_brackets_v67_20261011T214411_093986Z'
snap=dev/'development_sources';snap.mkdir(exist_ok=False)
for p in list((ROOT/'matlab/simulink').glob('*v67.*'))+[ROOT/'matlab/run_event_brackets_v67.m']+list((ROOT/'audit').glob('*v67.*')):
    dst=snap/p.relative_to(ROOT);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
p=ROOT/'matlab/simulink/build_event_brackets_v67.m';s=p.read_text().replace('DCHR_Event_Brackets_Stateflow_v67','DCHR_Event_Brackets_Stateflow_v67r2').replace('[250 1]','[256 1]')
p.write_text(s)
p=ROOT/'matlab/simulink/event_observer_v67.m';s=p.read_text().replace('u,cfg,core)','u,cfg,plant_trace)').replace('core(','plant_trace(').replace('zeros(45,1)','zeros(51,1)')
s=s.replace("if deriv(1)>0,z(1:15)=certify_event_root_v67(E,B,lam,stop,1,H,0,[0 0]);end", "if deriv(1)>0,z(1:15)=certify_event_root_v67(E,B,lam,stop,1,H,0,[0 0]);z(46:47)=B';end")
s=s.replace("if dis>0,z(16:30)=certify_event_root_v67(E,-fliplr(diviv(P(dis),P(p(8)))),lam,cut,-1,H,0,[0 0]);end", "if dis>0\n    B=-fliplr(diviv(P(dis),P(p(8))));z(16:30)=certify_event_root_v67(E,B,lam,cut,-1,H,0,[0 0]);z(48:49)=B';\nend")
p.write_text(s)
p=ROOT/'matlab/run_event_brackets_v67.m';s=p.read_text().replace('DCHR_Event_Brackets_Stateflow_v67','DCHR_Event_Brackets_Stateflow_v67r2').replace('Data,250,','Data,256,')
s=s.replace("'wide_charge',[8.5", "'exact_boundary',[8 8],[1 1],0,[9 9],1,1,0,[0 0];\n    'wide_charge',[8.5")
p.write_text(s)
p=ROOT/'audit/verify_event_brackets_v67.py';p.write_text(p.read_text().replace('DCHR_Event_Brackets_Stateflow_v67.slx','DCHR_Event_Brackets_Stateflow_v67r2.slx'))
folder=ROOT/'results'/('event_brackets_v67_final_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'));folder.mkdir()
spec=json.loads((dev/'spec.json').read_text())
for c in spec['cases']:
    if c['id'] in ['boundary_collision','interior_stop','boundary_delayed']:c['expected_modes']=[2]
(folder/'spec.json').write_text(json.dumps(spec,indent=2)+'\n')
preserved=json.loads((dev/'preservation.json').read_text());p=ROOT/'matlab/simulink/DCHR_Event_Brackets_Stateflow_v67.slx'
preserved.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(folder/'preservation.json').write_text(json.dumps(preserved,indent=2)+'\n')
(dev/'DEVELOPMENT_LIMITATIONS.md').write_text('Initial batch: MATLAB 1368 pass / 3 fail. All three failed expected-mode labels for zero-loss fixtures: inherited half-capacity allocation still safely charges, so expected mode is STORAGE_CHARGE, not IDLE. Twelve actual runtime guards rejected correctly. Initial observer trace lacked candidate B provenance; revision 2 appends it for independent equation verification. Renamed observer argument to remove Stateflow core shadow warning. Original model and source snapshot preserved. Initial sandbox startup failure retained.\n')
print(folder.relative_to(ROOT).as_posix())
