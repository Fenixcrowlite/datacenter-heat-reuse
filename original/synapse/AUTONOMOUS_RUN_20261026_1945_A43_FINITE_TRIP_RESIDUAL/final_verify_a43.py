"""Read-only final A43 verification, writes only its own report."""
from __future__ import annotations
import datetime,hashlib,json,sqlite3
from pathlib import Path
D=Path(__file__).resolve().parent
ROOT=D.parent.parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
m=json.loads((D/"SHA256_MANIFEST.json").read_text(encoding="utf8"))
bad=[k for k,v in m.items() if sha(D/k)!=v]
assert not bad,("SHA_MISMATCH",bad)
for root in (ROOT,ROOT/"recovery",D):
    for flag in ("STOP","STOP.flag","PAUSE","PAUSE.flag",".STOP",".PAUSE"):
        assert not (root/flag).exists(),("STOP",root,flag)
db=sqlite3.connect(f"file:{(ROOT/'tasks.sqlite3').as_posix()}?mode=ro",uri=True)
try:
    assert db.execute("pragma quick_check").fetchone()[0]=="ok"
    ev=db.execute("select id,kind,actor,data_json from task_events where task_id=? and id in (1238,1239) order by id",
        ("scc-3d9d172beb6e1b",)).fetchall()
    assert len(ev)==2 and ev[0][0]==1238 and ev[1][0]==1239
    assert ev[0][1]=="evidence" and ev[1][1]=="qa"
    p=json.loads(ev[0][3]);q=json.loads(ev[1][3])
    assert p["model_sha256"]==sha(D/"DCHR_A43_Finite_Trip_Closed_Loop.slx")
    assert p["manifest_sha256"]==sha(D/"SHA256_MANIFEST.json")
    assert q["fix_sha256"]==sha(D/"register_a43_v2.py")
    assert q["errata_sha256"]==sha(D/"ERRATA_A43.md")
    assert db.execute("select status,stage,worker_pid from tasks where id=?",
        ("scc-3d9d172beb6e1b",)).fetchone()==("review","planned",None)
    assert db.execute("select count(*) from task_events where task_id=? and actor=?",
        ("scc-3d9d172beb6e1b","chatgpt-a43-finite-trip-20261026-1945")).fetchone()[0]==1
    assert db.execute("select count(*) from task_events where task_id=? and actor=?",
        ("scc-3d9d172beb6e1b","chatgpt-a43-replay-regression-fix-20261026")).fetchone()[0]==1
finally:
    db.close()
r=dict(status="A43_FINAL_QA_PASS",at=datetime.datetime.now().astimezone().isoformat(),
    task="scc-3d9d172beb6e1b",events=[1238,1239],
    manifest_files=len(m),manifest_mismatches=bad,
    model_sha256=sha(D/"DCHR_A43_Finite_Trip_Closed_Loop.slx"),
    handoff_sha256=sha(D/"FINAL_HANDOFF.md"),
    addendum_sha256=sha(D/"FINAL_HANDOFF_ADDENDUM_A43.md"),
    errata_sha256=sha(D/"ERRATA_A43.md"),
    simulator="Stateflow.EMChart MATLAB Function, not graphical Stateflow chart",
    physical_release=False)
(D/"FINAL_VERIFICATION_A43.json").write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print(json.dumps(r,ensure_ascii=False))
