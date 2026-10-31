"""Additive observer chart; embedded v66 plant is byte-for-byte preserved."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib
ROOT=Path(__file__).resolve().parents[1]

def new(path,text):
    with path.open('x',encoding='utf-8',newline='\n') as f:f.write(text)

def main():
    text=(ROOT/'matlab/simulink/build_interval_dispatch_v66.m').read_text()
    text=text.replace('build_interval_dispatch_v66','build_event_brackets_v67').replace('DCHR_Interval_Dispatch_Stateflow_v66','DCHR_Event_Brackets_Stateflow_v67')
    text=text.replace('DCHR:v66:PreserveModel','DCHR:v67:PreserveModel')
    text=text.replace("'[205 1]','[205 1]'","'[250 1]','[205 1]'")
    text=text.replace("f=Stateflow.EMFunction(ch);f.Name='interval_mode_v66';", "f=Stateflow.EMFunction(ch);f.Name='event_observer_v67';f.Position=[850 550 380 90];f.Script=fileread(fullfile(here,'event_observer_v67.m'));\nf=Stateflow.EMFunction(ch);f.Name='interval_mode_v66';")
    text=text.replace("trace=interval_dispatch_kernel_v66(horizon_input,policy_input,retained_memory);\\nassert(trace(115)==%d);\\nretained_memory=trace;", "core=interval_dispatch_kernel_v66(horizon_input,policy_input,retained_memory);\\nassert(core(115)==%d);\\ntrace=[core;event_observer_v67(horizon_input,policy_input,core)];\\nretained_memory=core;")
    text=text.replace("names={'horizon_input','policy_input','trace','retained_memory'};scopes={'Input','Input','Output','Local'};sizes={'[12 1]','[60 1]','[250 1]','[205 1]'};", "names={'horizon_input','policy_input','trace','retained_memory','core'};scopes={'Input','Input','Output','Local','Local'};sizes={'[12 1]','[60 1]','[250 1]','[205 1]','[205 1]'};")
    text=text.replace('for j=1:4','for j=1:5')
    text=text.replace("ch.Description='v66 conservative sampled service allocation; retained v64 restart provenance; six executed modes. Protocol ticks differ from physical hours. Enclosures are retained, never midpoint reset.';", "ch.Description='v67 executed event bracket observer in SAME six-mode sampled v66 chart. Observer does not switch at roots or reset inventory. Embedded plant schema remains v66.';")
    new(ROOT/'matlab/simulink/build_event_brackets_v67.m',text)
    # Include the certifier as a local function of the actual embedded observer.
    observer="""function z=event_observer_v67(u,cfg,core)
%#codegen
% Potential FULL held-power paths, not the sampled allocated charge/discharge.
% Each candidate retains the complete incoming inventory/age interval.
z=zeros(45,1);if u(1)==0,return;end
assert(u(4)==0||u(4)==1,'v67 strict event flag');
p=cfg(36:60);E=core(160:161)';age=core(162:163)';P=@(x)[x x];
C=P(p(1));Ta=P(p(2));lam=p(6);H=u(5);
stop=muliv(C,minusiv(P(p(25)),Ta));cut=muliv(C,minusiv(P(p(4)),Ta));restart=muliv(C,minusiv(P(p(5)),Ta));
Te=minusiv(minusiv(P(p(12)),P(p(13))),P(p(14)));a=muliv(P(p(15)),plusiv(Te,P(273.15)));
floor=plusiv(P(p(19)),P(p(20)));lift=minusiv(plusiv(floor,P(p(18))),Te);
source=muliv(muliv(P(u(7)),P(p(13))),plusiv(P(1),diviv(lift,a)));
hot=muliv(P(p(16)),P(p(17)));limit=max(0,min([p(11) source(1) hot(1)]));
charge=max(0,min(p(9),limit-min(u(6),limit)));
if u(8)==1&&u(9)==1&&charge>0
    B=muliv(P(p(7)),P(charge));
    % Only reachable increasing paths enter the root solver.
    deriv=minusiv(B,muliv(P(lam),stop));
    if deriv(1)>0,z(1:15)=certify_event_root_v67(E,B,lam,stop,1,H,0,[0 0]);end
end
dis=min(u(6),p(10));
if dis>0,z(16:30)=certify_event_root_v67(E,-fliplr(diviv(P(dis),P(p(8)))),lam,cut,-1,H,0,[0 0]);end
if core(164)==0&&u(8)==1&&charge>0
    if lam>0,z(31:45)=certify_event_root_v67(E,[0 0],lam,restart,-1,H,p(23),age);
    elseif E(2)<=restart(1),z(31:45)=certify_event_root_v67(E,[0 0],lam,restart,-1,H,p(23),age);end
end
if u(4)==1
    assert(all(z([1 16 31])~=2)&&all(z([12 27 42])~=2),'v67 unresolved event ordering');
end
end
"""
    new(ROOT/'matlab/simulink/event_observer_v67.m',observer+(ROOT/'matlab/simulink/certify_event_root_v67.m').read_text())
    folder=ROOT/'results'/('event_brackets_v67_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'));folder.mkdir()
    spec=json.loads((ROOT/'results/stop_guard_v66_final_20261011T213720530Z/spec.json').read_text())
    spec['version']='0.67';spec.pop('witness')
    # An exact binary zero-loss boundary collision. Arithmetic must not select
    # event-vs-demand-boundary order even though the exact witness is known.
    cfg=list(spec['cases'][0]['cfg']);cfg[40]=0;cfg[41]=1;cfg[43]=1
    E=8.6 # rounded input; horizon chosen from exact binary threshold difference
    from fractions import Fraction as F
    threshold=F(cfg[35])*(F(cfg[59])-F(cfg[36]));dt=float(threshold-F(E))
    spec['cases'].insert(1,dict(id='boundary_collision',cfg=cfg,input=[[1,0,dt,0,dt,0,20,1,1,E,1,1]],expected_modes=[0]))
    # Repeat with an interior root, including an uncertain retained interval
    # in subsequent roots through the ordinary repeated trajectories.
    spec['cases'].insert(2,dict(id='interior_stop',cfg=cfg,input=[[1,0,2,0,2,0,20,1,1,E,1,1]],expected_modes=[0]))
    inputs=[[1,0,.125,0,.125,0,20,1,1,E,1,1],[1,0,.25,0,.125,0,20,1,1,E,1,1],
            [1,0,dt,0,dt-.25,0,20,1,1,E,1,1]]
    spec['cases'].insert(3,dict(id='boundary_delayed',cfg=cfg,input=inputs,expected_modes=[0,2]))
    (folder/'spec.json').write_text(json.dumps(spec,indent=2)+'\n')
    paths=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))+list(ROOT.glob('STATUS*.json'))+list(ROOT.glob('MASTER_STAGEBOARD*.md'))
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    (folder/'preservation.json').write_text(json.dumps([dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in paths if 'v67' not in p.name],indent=2)+'\n')
    print(folder.relative_to(ROOT).as_posix())

if __name__=='__main__':main()
