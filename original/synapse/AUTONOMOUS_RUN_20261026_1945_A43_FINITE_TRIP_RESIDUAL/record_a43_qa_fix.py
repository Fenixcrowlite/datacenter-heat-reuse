"""Append distinct QA correction to existing A43 card; preserves evidence event 1238."""
import hashlib,json,sqlite3,time
from pathlib import Path
D=Path(__file__).resolve().parent
ROOT=D.parent.parent
TASK="scc-3d9d172beb6e1b"
ACTOR="chatgpt-a43-replay-regression-fix-20261026"
def sha(p):return hashlib.sha256((D/p).read_bytes()).hexdigest()
for folder in (ROOT,ROOT/"recovery",D):
    for name in ("STOP","STOP.flag","PAUSE","PAUSE.flag",".STOP",".PAUSE"):
        if (folder/name).exists():raise RuntimeError("STOP_ACTIVE")
for f in ("REGISTRY_REPLAY1.txt","REGISTRY_REPLAY2.txt"):
    b=(D/f).read_bytes()
    if b.decode("utf-16" if b.startswith(bytes.fromhex("fffe")) else "utf8").strip()!="EXISTING_EVENT_VERIFIED 1238 files=28":
        raise RuntimeError("REPLAY_QA_NOT_PASS")
for f in ("REGISTRY_REPLAY1_ERR.txt","REGISTRY_REPLAY2_ERR.txt"):
    if (D/f).stat().st_size:raise RuntimeError("REPLAY_STDERR")
payload=dict(scope="A43_idempotent_registry_replay_regression",
    original_evidence_event=1238,fix_sha256=sha("register_a43_v2.py"),
    errata_sha256=sha("ERRATA_A43.md"),
    replay1_sha256=sha("REGISTRY_REPLAY1.txt"),
    replay2_sha256=sha("REGISTRY_REPLAY2.txt"),
    qa="two repeated read-only registration verifications PASS; no event duplication",
    source_event_unchanged=True)
db=sqlite3.connect(ROOT/"tasks.sqlite3",timeout=10,isolation_level=None)
db.execute("pragma busy_timeout=10000")
assert db.execute("pragma quick_check").fetchone()[0]=="ok"
db.execute("begin immediate")
try:
    prior=db.execute("select id from task_events where task_id=? and id=1238",(TASK,)).fetchone()
    assert prior is not None
    state=db.execute("select status,stage,worker_pid from tasks where id=?",(TASK,)).fetchone()
    assert state==("review","planned",None)
    events=db.execute("select id,data_json from task_events where task_id=? and actor=? and kind='qa'",(TASK,ACTOR)).fetchall()
    assert len(events)<=1
    if events:
        assert json.loads(events[0][1])==payload
        eid,action=events[0][0],"EXISTING_QA"
    else:
        eid=db.execute("insert into task_events(task_id,at,kind,actor,data_json) values(?,?,?,?,?)",
            (TASK,time.time(),"qa",ACTOR,json.dumps(payload,ensure_ascii=False))).lastrowid
        action="CREATED_QA"
    db.commit()
except BaseException:
    db.rollback();raise
finally:
    db.close()
print(json.dumps(dict(action=action,event_id=eid,task_id=TASK,**payload),ensure_ascii=False))
