from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
snapshot=folder/'source_snapshot';snapshot.mkdir()
sources=[p for parent in ['matlab','audit'] for p in (ROOT/parent).rglob('*v53*') if p.suffix in ['.m','.py','.ps1','.md'] and '__pycache__' not in p.parts]
records=[]
for p in sources:
    target=snapshot/p.name;assert not target.exists();target.write_bytes(p.read_bytes())
    records.append(dict(path=p.relative_to(ROOT).as_posix(),snapshot=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(folder/'source_hashes.json').write_text(json.dumps(records,indent=2)+'\n')
receipt=ROOT/'audit/Stateflow_padding_execution_v52_20261011T062943561Z.json'
r=json.loads(receipt.read_text(encoding='utf-8-sig'))
for p in [receipt,ROOT/r['log_path']]:
    target=folder/p.name;assert not target.exists();target.write_bytes(p.read_bytes())
(folder/'run_provenance.json').write_text(json.dumps(dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),
    preceding_failed_attempt='results/finite_interface_v53_20261011T062518_022505Z',
    failures='Initial harness: multi-sample reshape and auxiliary column defects; reviewer variable-name shadow caused one failed output-write attempt. All original sources, failed numeric report/logs/QA retained. Repaired fresh harness and source reviewer; no model/controller/source-equation change.',
    reference_receipt=receipt.relative_to(ROOT).as_posix(),
    new_source_files=[r['path'] for r in records],new_slx=False,actual_saved_model='0.52'),indent=2)+'\n')
print(f'SNAPSHOT_V53 {len(records)} sources')
