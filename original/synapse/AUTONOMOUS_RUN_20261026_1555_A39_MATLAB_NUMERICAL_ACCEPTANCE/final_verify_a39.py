"""Final independent integrity and idempotency check of A39 evidence."""
from pathlib import Path
import sqlite3,json,hashlib
HERE=Path(__file__).resolve().parent
CENTER=HERE.parent.parent
TASK='scc-3d9d172beb6e1b'
ACTOR='chatgpt-a39-dchr-matlab-acceptance-20261026-1555'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((HERE/'SHA256_MANIFEST.json').read_text(encoding='utf8'))
for name,digest in manifest.items():
 assert sha(HERE/name)==digest,('HASH_MISMATCH',name)
reg=json.loads((HERE/'REGISTRY_RESULT.json').read_text(encoding='utf8'))
assert reg['manifest_sha256']==sha(HERE/'SHA256_MANIFEST.json')
assert reg['evidence_sha256']==sha(HERE/'EVIDENCE.json')
db=sqlite3.connect('file:'+str(CENTER/'tasks.sqlite3').replace('\\','/')+'?mode=ro',uri=True)
assert db.execute('pragma quick_check').fetchone()[0]=='ok'
rows=db.execute('select id,data_json from task_events where task_id=? and actor=? and kind=?',(TASK,ACTOR,'evidence')).fetchall()
assert len(rows)==1
assert rows[0][0]==reg['event_id']
assert json.loads(rows[0][1])['manifest_sha256']==reg['manifest_sha256']
assert db.execute('select status,stage,worker_pid from tasks where id=?',(TASK,)).fetchone()==('review','planned',None)
db.close()
r=json.loads((HERE/'MATLAB_RESULT.json').read_text(encoding='utf8'))
assert r['comparisons']==80640 and r['max_error']<1e-6
print(json.dumps({'status':'PASS','manifest_files_verified':len(manifest),'event_id':rows[0][0],
 'exact_event_count':len(rows),'matlab_comparisons':r['comparisons'],
 'max_error':r['max_error'],'matlab_stateflow_executed':False,
 'physical_release_allowed':False},indent=2))
