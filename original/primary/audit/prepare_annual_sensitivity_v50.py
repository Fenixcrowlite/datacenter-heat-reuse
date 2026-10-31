"""Prepare immutable matched sensitivity specification and prior hashes."""
from pathlib import Path
from datetime import datetime, timezone
import copy, hashlib, json, shutil

ROOT = Path(__file__).resolve().parents[1]

def info(p):
    return dict(path=p.relative_to(ROOT).as_posix(), bytes=p.stat().st_size,
                sha256=hashlib.sha256(p.read_bytes()).hexdigest())

def main():
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    folder = ROOT/'results'/('annual_sensitivity_v50_'+stamp)
    folder.mkdir()
    status = json.loads((ROOT/'STATUS_v49.json').read_text())
    prior = ROOT/status['result_directory']
    base = json.loads((prior/'spec.json').read_text())
    variants = [('baseline', '', 0), ('cutoff_81', 'delivery_cutoff_C', 81.),
                ('cutoff_82', 'delivery_cutoff_C', 82.),
                ('restart_47', 'restart_energy_MWh', 47.),
                ('restart_49', 'restart_energy_MWh', 49.),
                ('on_0', 'min_on_h', 0.), ('on_05', 'min_on_h', .5),
                ('off_0', 'min_off_h', 0.), ('off_05', 'min_off_h', .5)]
    scenarios = []
    for id, coordinate, value in variants:
        policy = copy.deepcopy(base['policy'])
        if coordinate:
            policy[coordinate] = value
        scenarios.append(dict(id=id, changed_coordinate=coordinate, policy=policy))
    spec = dict(version='0.50', model_version='0.42', new_model=False,
                baseline_evidence=status['result_directory'], scenarios=scenarios,
                port_columns=base['port_columns'], annual_intervals=8760,
                evidence_class='SYNTHETIC_ENGINEERING_NOT_CALIBRATED')
    (folder/'spec.json').write_text(json.dumps(spec, indent=2)+'\n')
    paths = {ROOT/x['path'] for x in json.loads((prior/'preservation.json').read_text())}
    manifest = sorted((ROOT/'audit').glob('Annual_stateflow_manifest_v49_*.json'))[-1]
    paths.update(ROOT/x['path'] for x in json.loads(manifest.read_text())['files'])
    for pattern in ['STATUS*.json', 'MASTER_STAGEBOARD*.md', 'matlab/**/*.m', 'matlab/simulink/*.slx']:
        paths.update(ROOT.glob(pattern))
    (folder/'preservation.json').write_text(json.dumps([info(p) for p in sorted(paths)
        if p.is_file() and 'v50' not in p.name], indent=2)+'\n')
    files = list((ROOT/'matlab').rglob('*.m')) + list((ROOT/'audit').glob('*v50*'))
    files += [ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v42.slx',
              ROOT/'audit/verify_annual_stateflow_v49.py', ROOT/'audit/verify_annual_dispatch_v48.py']
    for p in files:
        if p.is_file():
            dest = folder/'source_snapshot'/p.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, dest)
    print(folder.relative_to(ROOT).as_posix())

if __name__ == '__main__':
    main()
