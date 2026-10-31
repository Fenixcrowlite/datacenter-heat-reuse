"""Idempotent A67 registration; preserves stable handoff on replay."""
from pathlib import Path
from datetime import datetime
import hashlib,json,re,sqlite3,time
import a67_replay_gate as gate
D=Path(__file__).resolve().parent
CENTER=D.parent.parent
TASK="scc-3d9d172beb6e1b"
ACTOR="chatgpt-a67-idempotent-checkpoint-replay-20261027-1658"
FILES=("a67_replay_gate.py","test_a67.py","finalize_a67.py",
       "A67_REGRESSION_SK.md","QA_A67_CLEAN.txt","REAL_REPLAY_A66.json","EVIDENCE_A67.json")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def once(p,s):
    if p.exists():
        if p.read_text(encoding="utf-8")!=s:raise RuntimeError("IMMUTABLE_CONFLICT")
    else:p.write_text(s,encoding="utf-8")
def guard():
    for root in (CENTER,CENTER/"recovery",D,CENTER.parent/"temp_coding",CENTER.parent/"EduMotionPipeline"):
        for name in ("STOP","PAUSE","STOP.flag","PAUSE.flag"):
            if (root/name).exists():raise RuntimeError("STOP_PAUSE:"+str(root/name))
def main():
    guard()
    raw=(D/"QA_A67.txt").read_text(encoding="utf-8-sig")
    assert re.search(r"Ran 7 tests in [0-9.]+s",raw) and re.search(r"\nOK\s*$",raw)
    clean=re.sub(r"Ran 7 tests in [0-9.]+s","Ran 7 tests in <variable>s",raw).lstrip("\ufeff")
    once(D/"QA_A67_CLEAN.txt",clean)
    a66=D.parent/"AUTONOMOUS_RUN_20261027_1648_A66_UNIFIED_OFFLINE_REVIEW"
    replay=gate.audit(a66,CENTER/"tasks.sqlite3",TASK,"chatgpt-a66-unified-offline-review-20261027-1648","A66")
    assert replay["status"]=="ALREADY_RECORDED" and replay["mutations"]==0 and replay["verified_files"]==10
    saved=json.loads((D/"REAL_REPLAY_A66.json").read_text(encoding="utf-8-sig"))
    assert replay==saved
    evidence={"scope":"A67_readonly_idempotent_checkpoint_replay","task_id":TASK,
      "artifact_directory":str(D),"replayed_event_id":replay["event_id"],
      "replayed_evidence_sha256":replay["evidence_sha256"],
      "unit_tests":"7/7 PASS","real_replay_checks":"10/10 PASS twice",
      "mutations":0,"source_kind":"derived_simulation","physical_release":False,
      "status":"VERIFIED_READONLY_REPLAY",
      "next_step":"Use a stable checkpoint timestamp in future finalizers; do not rewrite already registered A66 evidence."}
    once(D/"EVIDENCE_A67.json",json.dumps(evidence,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    manifest={f:sha(D/f) for f in FILES}
    once(D/"SHA256_MANIFEST_A67.json",json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    handoff_path=D/"FINAL_HANDOFF.md"
    if not handoff_path.exists():
        handoff=(
          "# A67 read-only replay | "+datetime.now().astimezone().isoformat(timespec="seconds")+"\n"
          "A66 repeat finalizer exposed a changing timestamp; original A66 artifacts and event remain intact.\n"
          "New read-only replay gate: 7/7 regression tests, 10/10 real SHA checks, repeated output identical, 0 mutations.\n"
          "Temporary SQLite handles explicitly closed after tests; initial Windows lock failure corrected.\n"
          "No Codex, GPU, VRS, shared GUI, OAuth or foreign worktree changes.\n"
          "Evidence SHA256: "+sha(D/"EVIDENCE_A67.json")+"\n"
          "Manifest SHA256: "+sha(D/"SHA256_MANIFEST_A67.json")+"\n"
          "NEXT: "+evidence["next_step"]+"\n")
        once(handoff_path,handoff)
    payload={"scope":evidence["scope"],"artifact_directory":str(D),
       "evidence_sha256":sha(D/"EVIDENCE_A67.json"),
       "manifest_sha256":sha(D/"SHA256_MANIFEST_A67.json"),
       "handoff_sha256":sha(handoff_path),
       "QA":"7/7 unittest; 10/10 real manifest; 2 identical replays; 0 mutations",
       "source_kind":"derived_simulation","physical_release":False,
       "next_step":evidence["next_step"]}
    guard()
    with sqlite3.connect(CENTER/"tasks.sqlite3",timeout=15,isolation_level=None) as db:
        db.execute("PRAGMA busy_timeout=15000")
        if db.execute("PRAGMA quick_check").fetchone()[0]!="ok":raise RuntimeError("REGISTRY_INTEGRITY")
        db.execute("BEGIN IMMEDIATE")
        try:
            state=db.execute("SELECT status,stage,worker_pid FROM tasks WHERE id=?",(TASK,)).fetchone()
            if state!=("review","planned",None):raise RuntimeError("TASK_STATE_CHANGED:"+repr(state))
            found=db.execute("SELECT id,data_json FROM task_events WHERE task_id=? AND actor=? AND kind='evidence'",(TASK,ACTOR)).fetchall()
            if len(found)>1:raise RuntimeError("DUPLICATE_EVENTS")
            if found:
                if json.loads(found[0][1])!=payload:raise RuntimeError("EVENT_CONFLICT")
                event_id=found[0][0]
            else:
                event_id=db.execute("INSERT INTO task_events(task_id,at,kind,actor,data_json) VALUES(?,?,?,?,?)",
                    (TASK,time.time(),"evidence",ACTOR,json.dumps(payload,ensure_ascii=False))).lastrowid
            db.commit()
        except BaseException:
            db.rollback();raise
    once(D/"REGISTRY_RESULT_A67.json",json.dumps({"event_id":event_id,"task_id":TASK,**payload},indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    print(json.dumps({"event_id":event_id,"evidence_sha256":payload["evidence_sha256"],
        "handoff_sha256":payload["handoff_sha256"],"manifest_entries":len(manifest)}))
if __name__=="__main__":main()
