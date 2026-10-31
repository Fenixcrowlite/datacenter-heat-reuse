"""Additive numerical-padding repair; preserve all previous saved models."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil

ROOT = Path(__file__).resolve().parents[1]

def new(path, content):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        f.write(content)

def main():
    kernel = (ROOT/'matlab/simulink/interval_dispatch_kernel_v66.m').read_text()
    kernel = kernel.replace('function y=interval_dispatch_kernel_v66(', 'function y=interval_dispatch_kernel_v68(')
    kernel = kernel.replace("assert(max(abs(x))<=1,'v63 outward span exceeds one')",
                            "assert(max(abs(x))<=2,'v68 outward span exceeds two')")
    kernel = kernel.replace('tail=diviv([3 3],fac);',
                            '% On the outward evaluation interval |x|<=2, e^2<8.\n'
                            '% Tail for both phi1 and phi2 is <=8*2^25/26!.\n'
                            'tail=diviv([268435456 268435456],fac);')
    assert kernel.count('268435456') == 2 and 'outward span exceeds one' not in kernel
    new(ROOT/'matlab/simulink/interval_dispatch_kernel_v68.m', kernel)
    cert = (ROOT/'matlab/simulink/certify_event_root_v67.m').read_text()
    cert = cert.replace('certify_event_root_v67', 'certify_event_root_v68')
    cert = cert.replace("assert(max(abs(x))<=1,'v67 outward root span')",
                        "assert(max(abs(x))<=2,'v68 outward root span')")
    cert = cert.replace('tail=diviv(P(3),fac);',
                        '% Expanded arguments have a separate proven numerical domain.\n'
                        '% e^2<8 gives |tail(phi1)|<=8*2^25/26!.\n'
                        'tail=diviv(P(268435456),fac);')
    new(ROOT/'matlab/simulink/certify_event_root_v68.m', cert)
    obs = (ROOT/'matlab/simulink/event_observer_v67.m').read_text()
    obs = obs[:obs.index('function z=certify_event_root_v67')]
    obs = obs.replace('event_observer_v67', 'event_observer_v68').replace('certify_event_root_v67', 'certify_event_root_v68')
    new(ROOT/'matlab/simulink/event_observer_v68.m', obs+cert)
    builder = (ROOT/'matlab/simulink/build_event_brackets_v67.m').read_text()
    builder = builder.replace('build_event_brackets_v67','build_span_repair_v68').replace('DCHR_Event_Brackets_Stateflow_v67r2','DCHR_Span_Repair_Stateflow_v68')
    builder = builder.replace('interval_dispatch_kernel_v66','interval_dispatch_kernel_v68').replace('event_observer_v67','event_observer_v68')
    builder = builder.replace('DCHR:v67:PreserveModel','DCHR:v68:PreserveModel')
    builder = builder.replace('v67 executed event bracket observer', 'v68 numerical-span repaired event bracket observer')
    new(ROOT/'matlab/simulink/build_span_repair_v68.m', builder)
    harness = (ROOT/'matlab/run_event_brackets_v67.m').read_text()
    harness = harness.replace('run_event_brackets_v67','run_span_repair_v68').replace('DCHR_Event_Brackets_Stateflow_v67r2','DCHR_Span_Repair_Stateflow_v68')
    harness = harness.replace('build_event_brackets_v67','build_span_repair_v68').replace('certify_event_root_v67','certify_event_root_v68')
    harness = harness.replace("'version','0.67'", "'version','0.68'").replace('event_brackets_v67.mat','span_repair_v68.mat').replace('EVENT_BRACKETS_V67','SPAN_REPAIR_V68')
    harness = harness.replace("'scope','EXECUTED_ROOT_OBSERVER_SAMPLED_DISPATCH_UNCHANGED_EARLIEST_SWITCHING_OPEN'", "'scope','NUMERICAL_SPAN_REPAIR_SAMPLED_POLICY_EARLIEST_SWITCHING_OPEN'")
    harness = harness.replace('base=spec.cases(end);', "base=spec.cases(strcmp({spec.cases.id},'delayed_fault_control'));")
    harness = harness.replace("isequal(prefix,runs{end}.trace(1:2,:))", "isequal(prefix,runs{find(cellfun(@(r)strcmp(r.id,base.id),runs))}.trace(1:2,:))")
    anchor = "[prefix,~]=execute(input(1:2,:),rows(1:2,:));"
    extra = (ROOT/'audit/span_repair_harness_extra_v68.txt').read_text()
    assert anchor in harness
    harness = harness.replace(anchor, extra+'\n'+anchor)
    harness = harness.replace("'root_probes',{probes},'valid_prefix'", "'root_probes',{probes},'legacy_defects',{legacy_defects},'valid_prefix'")
    new(ROOT/'matlab/run_span_repair_v68.m', harness)
    runner = (ROOT/'audit/run_event_brackets_v67.ps1').read_text().replace('run_event_brackets_v67','run_span_repair_v68')
    new(ROOT/'audit/run_span_repair_v68.ps1', runner)
    folder = ROOT/'results'/('span_repair_v68_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'))
    folder.mkdir()
    spec = json.loads((ROOT/'results/event_brackets_v67_final_20261011T214624_493950Z/spec.json').read_text())
    spec['version'] = '0.68'
    cfg = list(spec['cases'][0]['cfg']); cfg[40] = .125
    # Passive retained-box trajectory crosses restart strictly inside H=8.
    for id, dt in [('span_equal_one',8.), ('span_near_one',float.fromhex('0x1.fffffffffffffp+2')),
                   ('span_inside_one',float.fromhex('0x1.ffffffffffffep+2'))]:
        spec['cases'].append(dict(id=id,cfg=cfg,input=[[1,0,dt,0,dt,0,20,1,1,8.5,0,0]],expected_modes=[0]))
    spec['cases'].append(dict(id='span_delayed',cfg=cfg,input=[
        [1,0,.5,0,.5,0,0,0,0,8.5,0,0],
        [1,0,1.,0,.5,0,0,0,0,8.5,0,0],
        [1,0,9.,0,8.,0,20,1,1,8.5,0,0]],expected_modes=[0]))
    (folder/'spec.json').write_text(json.dumps(spec,indent=2)+'\n')
    previous = list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))
    previous += list(ROOT.glob('STATUS*.json'))+list(ROOT.glob('MASTER_STAGEBOARD*.md'))
    previous = [p for p in previous if 'v68' not in p.name]
    (folder/'preservation.json').write_text(json.dumps([
        dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
        for p in previous],indent=2)+'\n')
    print(folder.relative_to(ROOT).as_posix())

if __name__ == '__main__':
    main()
