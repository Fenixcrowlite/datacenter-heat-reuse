"""Prepare additive annual HP audit evidence inside this project only."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil
ROOT = Path(__file__).resolve().parents[1]
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
folder = ROOT / 'results' / ('hp_annual_v47_' + stamp)
folder.mkdir()
paths = set()
prior = ROOT / 'results/period_v46_20261010T180131_369483Z/preservation.json'
paths.update(ROOT / x['path'] for x in json.loads(prior.read_text()))
paths.update(ROOT / x['path'] for x in json.loads((ROOT / 'audit/Period_manifest_v46_20261010T180657_219087Z.json').read_text())['files'])
for pattern in ['STATUS*.json', 'MASTER_STAGEBOARD*.md', 'matlab/**/*.m', 'matlab/simulink/*.slx']:
    paths.update(ROOT.glob(pattern))
paths = {p for p in paths if p.is_file() and 'v47' not in p.name}
(folder / 'preservation.json').write_text(json.dumps([
    dict(path=p.relative_to(ROOT).as_posix(), bytes=p.stat().st_size,
         sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(paths)
], indent=2) + '\n')
base = json.loads((ROOT / 'results/period_v46_20261010T180131_369483Z/spec.json').read_text())
spec = dict(version='0.47', model_version='0.42', new_model=False,
    evidence_class='SYNTHETIC_ENGINEERING_NOT_MEASURED', six_mode_cases=base['six_mode_cases'],
    annual_hours=8760, annual_boiler_cap_MW=2,
    source_comparison_MW=[1, 6], source_C=35, sink_C=70, request_MW=20,
    probe_sources_MW=[0, .001, .1, 1, 6, 20], probe_requests_MW=[0, .1, 4, 20],
    probe_penalties=[0, .08, .25])
(folder / 'spec.json').write_text(json.dumps(spec, indent=2) + '\n')
snap = folder / 'source_snapshot'
for p in list((ROOT / 'matlab').rglob('*.m')) + list((ROOT / 'audit').glob('*v47*')):
    if p.is_file():
        target = snap / p.relative_to(ROOT); target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, target)
target = snap / 'matlab/simulink/DCHR_Dispatch_Stateflow_v42.slx'
shutil.copyfile(ROOT / 'matlab/simulink/DCHR_Dispatch_Stateflow_v42.slx', target)
print(folder.relative_to(ROOT).as_posix())
