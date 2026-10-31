"""Retain the post-close checker repair without modifying sealed evidence."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
report=ROOT/'audit/Stateflow_postclose_v38_20261010T081954_887411Z.json'
qa=json.loads(report.read_text(encoding='utf-8'));assert qa['passed']==240 and qa['failed']==0
ts=datetime.now(timezone.utc);stamp=ts.strftime('%Y%m%dT%H%M%S_%fZ')
with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:
    f.write(f'''\nFinal v38 post-close packaging: 240/240 PASS, zero failures. All 227 sealed
entries retain hashes/sizes; saved-model hash, observed batch completion markers,
actual scope, separate independent/synthetic counts and scoped acceptance agree.
Evidence: audit/Stateflow_postclose_v38_20261010T081954_887411Z.json.
The original sealed post-close checker assumed UTF-8 but Windows PowerShell Tee
logs are BOM-tagged UTF-16. Its failed log/code remain; additive
audit/check_stateflow_checkpoint_v38a.py decodes the observed BOM and passes.
No model, numeric artifact, original checker or sealed manifest was changed.
Post-close files have a separate immutable manifest. Run complete; next action
remains the focused HP/clock domain audit and primary-equipment evidence handoff.
''')
files=[ROOT/'audit/check_stateflow_checkpoint_v38a.py',report,Path(__file__).resolve()]
files += list((ROOT/'automation/logs').glob('stateflow_v38_postclose_*.log'))
files += list((ROOT/'automation/logs').glob('stateflow_v38_finalize_console_*.log'))
manifest=ROOT/'audit'/('Stateflow_postclose_manifest_v38_'+stamp+'.json');assert not manifest.exists()
v=dict(timestamp_utc=ts.isoformat(),evidence_class='postclose_packaging_only',files=[
    dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(set(files))])
manifest.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
print('POSTCLOSE_MANIFEST='+str(manifest.relative_to(ROOT)))
