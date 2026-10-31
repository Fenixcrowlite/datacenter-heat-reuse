"""Freeze the reviewer actually run; keep initial development snapshots intact."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');snapshot='reviewer_snapshot_'+stamp;manifest=[]
    names=['verify_held_schedule_v74.py','earliest_closed_form_v73.py','verify_interval_dispatch_v66.py','verify_stateflow_finite_v57.py','verify_restart_chain_v64.py','verify_capacity_chain_v63.py','verify_interval_dispatch_v65.py','earliest_service_reference_v66.py','seal_held_reviewer_v74.py']
    for name in names:
        src=ROOT/'audit'/name;rel=src.relative_to(ROOT).as_posix();dst=folder/snapshot/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);manifest.append(dict(path=rel,sha256=sha(src)))
    out=folder/('reviewer_manifest_'+stamp+'.json');out.write_text(json.dumps(dict(snapshot=snapshot,records=manifest),indent=2)+'\n');print(out.relative_to(ROOT).as_posix())
if __name__=='__main__':main()
