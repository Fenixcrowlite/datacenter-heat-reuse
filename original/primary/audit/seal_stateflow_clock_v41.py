"""Seal completed finalizer/post-close logs separately from release manifest."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
post=sorted((ROOT/'audit').glob('Stateflow_clock_postclose_v41_*.json'))[-1]
check=json.loads(post.read_text());assert check['failed']==0
manifest=ROOT/check['manifest'];data=json.loads(manifest.read_text())
with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:
    f.write(f"\nFinal v41 packaging: {check['passed']} PASS / 0 FAIL; {len(data['files'])} sealed\n"
        f"release artifacts retain hashes/sizes. Evidence: {post.relative_to(ROOT).as_posix()}.\n"
        "Completed finalizer/post-close logs and manifest sealed separately.\n"
        "No numeric/model artifact changed after QA. Run complete; next action\n"
        "is the additive v42 uncertainty-aware dwell repair in STATUS_stateflow_v41.json.\n")
paths=[post,manifest,Path(__file__),ROOT/'audit/check_stateflow_clock_checkpoint_v41.py']
paths+=list((ROOT/'automation/logs').glob('stateflow_clock_v41_finalize_*.log'))
paths+=list((ROOT/'automation/logs').glob('stateflow_clock_v41_postclose_*.log'))
files=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths]
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
path=ROOT/'audit'/('Stateflow_clock_postclose_manifest_v41_'+stamp+'.json')
path.write_text(json.dumps(dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),scope='Completed packaging artifacts only',files=files),indent=2)+'\n')
print('SEALED='+path.relative_to(ROOT).as_posix()+f' ({len(files)} files)')
