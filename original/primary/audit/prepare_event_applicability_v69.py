"""Seal a focused execution audit of the preserved saved v68 chart."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil

ROOT = Path(__file__).resolve().parents[1]

def main():
    spec = json.loads((ROOT/'results/span_repair_v68_release_20261011T215822_761796Z/spec.json').read_text())
    names = ['zero_demand', 'HP_only', 'TES_charge', 'TES_discharge', 'boiler_limit', 'insufficient_heat']
    cases = [dict(c, audit_kind='baseline') for c in spec['cases'] if c['id'] in names]
    cfg = list(cases[0]['cfg'])
    cfg[40] = 0.0  # exact zero standing loss isolates guard applicability
    cfg[42] = 1.0
    cfg[50] = 1.0  # water limiter has strict headroom above the 1 MW demand
    def case(id, inputs, config, mode, kind):
        cases.append(dict(id=id, cfg=config, input=inputs, expected_modes=[mode], audit_kind=kind))
    # A hypothetical full-discharge cutoff coincides with the horizon, but
    # actual HP direct delivery leaves the inventory exactly constant.
    for suffix, energy in [('contact', 6.0), ('separated', 7.0)]:
        for strict in [0, 1] if suffix == 'separated' else [0]:
            case(f'HP_only_{suffix}_strict{strict}', [[1,0,.4,strict,.4,1,20,1,0,energy,1,1]], cfg, 1, 'inactive_cutoff')
    case('HP_only_contact_delayed', [
        [1,0,.125,0,.125,1,20,1,0,6,1,1],
        [1,0,.25,0,.125,1,20,1,0,6,1,1],
        [1,0,.65,0,.4,1,20,1,0,6,1,1]], cfg, 1, 'inactive_cutoff')
    off = list(cfg); off[41] = 1.; off[43] = 1.; off[57] = 4.
    case('OFF_blocked_hypothetical_stop', [[1,0,2,1,2,0,20,1,1,8.5,0,0]], off, 0, 'inactive_stop')
    for loss in [0., .01]:
        dis = list(cfg); dis[40] = loss; dis[41] = .9; dis[42] = .8; dis[43] = 1.
        case('OFF_discharge_restart_'+str(loss).replace('.', 'p'),
             [[1,0,2,1,2,.5,20,1,1,8.5,0,1]], dis, 3, 'missing_forced_restart')
    faults = []
    for id, delayed in [('inactive_cutoff_strict', False), ('inactive_cutoff_delayed_strict', True)]:
        base = next(c for c in cases if c['id'] == ('HP_only_contact_delayed' if delayed else 'HP_only_contact_strict0'))
        ii = [list(row) for row in base['input']]; ii[-1][3] = 1
        faults.append(dict(id=id, base_id=base['id'], input=ii, cfg=base['cfg'], expected_guard='v67 unresolved event ordering'))
    # Positive rejection control: the full charge path really is enabled.
    boundary = next(c for c in spec['cases'] if c['id'] == 'boundary_collision')
    cases.append(dict(boundary, audit_kind='active_boundary_control'))
    ii = [list(row) for row in boundary['input']]; ii[-1][3] = 1
    faults.append(dict(id='active_stop_boundary_strict',base_id=boundary['id'],input=ii,cfg=boundary['cfg'],expected_guard='v67 unresolved event ordering'))
    folder = ROOT/'results'/('event_applicability_v69_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'))
    folder.mkdir()
    (folder/'spec.json').write_text(json.dumps(dict(version='0.69', cases=cases, faults=faults),indent=2)+'\n')
    prior = list((ROOT/'matlab').rglob('*.m')) + list((ROOT/'matlab').rglob('*.slx')) + list(ROOT.glob('STATUS*.json')) + list(ROOT.glob('MASTER_STAGEBOARD*.md'))
    prior = [p for p in prior if 'v69' not in p.name]
    (folder/'preservation.json').write_text(json.dumps([dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in prior],indent=2)+'\n')
    sources = ['audit/prepare_event_applicability_v69.py','audit/verify_event_applicability_v69.py','audit/run_event_applicability_v69.ps1','matlab/run_event_applicability_v69.m','matlab/simulink/event_observer_v68.m','matlab/simulink/interval_dispatch_kernel_v68.m','matlab/simulink/certify_event_root_v68.m','matlab/simulink/DCHR_Span_Repair_Stateflow_v68.slx',
        'audit/verify_interval_dispatch_v66.py','audit/verify_span_repair_v68r2.py','audit/verify_capacity_chain_v63.py',
        'audit/verify_restart_chain_v64.py','audit/verify_interval_dispatch_v65.py','audit/span_tail_review_v68r2.py','audit/earliest_service_reference_v66.py',
        'audit/Event_applicability_derivation_v69.md']
    manifest = []
    for rel in sources:
        src=ROOT/rel; dst=folder/'source_snapshot'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
        manifest.append(dict(path=rel,sha256=hashlib.sha256(src.read_bytes()).hexdigest()))
    (folder/'source_hashes.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(folder.relative_to(ROOT).as_posix())

if __name__ == '__main__': main()
