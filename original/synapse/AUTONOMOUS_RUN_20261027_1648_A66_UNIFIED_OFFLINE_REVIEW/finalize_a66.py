"""Finalize A66 evidence and idempotent event in the existing DataCenter card."""
import hashlib,json,re,sqlite3,time
from pathlib import Path
from datetime import datetime
import a66_unified as m
import a66_source_audit
D=Path(__file__).resolve().parent
CENTER=D.parent.parent
TASK="scc-3d9d172beb6e1b"
ACTOR="chatgpt-a66-unified-offline-review-20261027-1648"
FILES=("a66_unified.py","a66_source_audit.py","test_a66.py","finalize_a66.py",
       "unified_review.html","A66_TECHNICKY_PROTOKOL_SK.md","QA_A66_CLEAN.txt",
       "BROWSER_A66.json","SOURCE_AUDIT_A66.json","EVIDENCE_A66.json")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def once(p,s):
    if p.exists():
        if p.read_text(encoding="utf-8")!=s:raise RuntimeError("IMMUTABLE_CONFLICT:"+str(p))
    else:p.write_text(s,encoding="utf-8")
def guard():
    for root in (CENTER,CENTER/"recovery",D,CENTER.parent/"temp_coding",CENTER.parent/"EduMotionPipeline"):
        for name in ("STOP","PAUSE","STOP.flag","PAUSE.flag"):
            if (root/name).exists():raise RuntimeError("STOP_PAUSE:"+str(root/name))
def main():
    guard()
    raw=(D/"QA_A66.txt").read_text(encoding="utf-8-sig")
    if not re.search(r"Ran 9 tests in [0-9.]+s",raw) or not re.search(r"\nOK\s*$",raw):
        raise RuntimeError("UNIT_QA_MISSING")
    clean=re.sub(r"Ran 9 tests in [0-9.]+s","Ran 9 tests in <variable>s",raw).lstrip("\ufeff")
    once(D/"QA_A66_CLEAN.txt",clean)
    browser=json.loads((D/"BROWSER_A66_RAW.txt").read_text(encoding="utf-8-sig"))
    if (browser["status"]!="PASS" or browser["scenario_checks"]!=6 or browser["errors"] or browser["external_requests"]
        or any(v["scroll"]>v["width"] for v in browser["viewports"].values())):
        raise RuntimeError("BROWSER_QA_FAILED")
    once(D/"BROWSER_A66.json",json.dumps(browser,indent=2,ensure_ascii=False,sort_keys=True)+"\n")
    audit=a66_source_audit.audit()
    assert audit["verified_hashes"]==8
    expected=json.loads((D/"SOURCE_AUDIT_A66.json").read_text(encoding="utf-8-sig"))
    assert expected==audit
    html,cmp=m.load()
    assert sha(m.OUT)=="2e69e2f36b17959aa099dc14429b5930f0005b8557454c16a42b05dc4ffc47e8"
    evidence={
        "scope":"A66_unified_offline_A63_A64_mobile_review",
        "task_id":TASK,"artifact_directory":str(D),"report":str(m.OUT),
        "a63_sha256":sha(m.A63),"a64_sha256":sha(m.A64),
        "unit_tests":"9/9 PASS","browser_scenario_checks":"6/6 PASS",
        "browser_viewports_px":[320,390,1440],
        "upstream_hash_checks":"8/8 PASS",
        "integration_identity":"10/10 PASS",
        "source_kind":"derived_simulation","physical_release":False,
        "upstream_files_modified":False,"external_network_requests":0,
        "status":"VERIFIED_OFFLINE_INTEGRATED_REPORT",
        "next_step":"Independent physical-device mobile review; calibrated SCADA telemetry and certificates required before physical acceptance."
    }
    once(D/"EVIDENCE_A66.json",json.dumps(evidence,indent=2,ensure_ascii=False,sort_keys=True)+"\n")
    manifest={f:sha(D/f) for f in FILES}
    once(D/"SHA256_MANIFEST_A66.json",json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    handoff=(
      "# A66 unified offline reviewer | "+datetime.now().astimezone().isoformat(timespec="seconds")+"\n"
      "SynapseMCP Web live; STOP/PAUSE checked; existing DataCenter task review/planned, no worker.\n"
      "New standalone HTML combines A63 charts and A64 integration comparison; A60-A65 unchanged.\n"
      "Both scenarios, five channels; exact delta identity 10/10; original source SHA256 8/8 PASS.\n"
      "QA: 9/9 unit tests; 6/6 headless Chrome scenario/viewport checks (320,390,1440 px); no overflow or network requests.\n"
      "One initial browser QA stdout CP1251 encoding failure; rerun with ASCII-escaped JSON PASS.\n"
      "All source data DERIVED_SIMULATION, physical_release=false. No Codex, GUI, GPU, VRS, OAuth or foreign branch modifications.\n"
      "Evidence SHA256: "+sha(D/"EVIDENCE_A66.json")+"\n"
      "Manifest SHA256: "+sha(D/"SHA256_MANIFEST_A66.json")+"\n"
      "NEXT: "+evidence["next_step"]+"\n"
    )
    once(D/"FINAL_HANDOFF.md",handoff)
    payload={
        "scope":evidence["scope"],"artifact_directory":str(D),"report":str(m.OUT),
        "evidence_sha256":sha(D/"EVIDENCE_A66.json"),"manifest_sha256":sha(D/"SHA256_MANIFEST_A66.json"),
        "handoff_sha256":sha(D/"FINAL_HANDOFF.md"),
        "QA":"9/9 unittest; 6/6 headless Chrome; 8/8 source hashes; 10/10 integration identities",
        "source_kind":"derived_simulation","physical_release":False,"next_step":evidence["next_step"]
    }
    guard()
    db=sqlite3.connect(CENTER/"tasks.sqlite3",timeout=15,isolation_level=None)
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
    finally:db.close()
    once(D/"REGISTRY_RESULT_A66.json",json.dumps({"event_id":event_id,"task_id":TASK,**payload},indent=2,ensure_ascii=False,sort_keys=True)+"\n")
    print(json.dumps({"event_id":event_id,"evidence_sha256":payload["evidence_sha256"],"handoff_sha256":payload["handoff_sha256"],"manifest_entries":len(manifest)}))
if __name__=="__main__":main()
