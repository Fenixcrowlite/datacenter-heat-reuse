"""A65 reproducible QA and idempotent existing DataCenter card evidence."""
import hashlib,json,re,sqlite3,subprocess,sys,time
from datetime import datetime
from pathlib import Path
D=Path(__file__).resolve().parent
CENTER=D.parent.parent
TASK="scc-3d9d172beb6e1b"
ACTOR="chatgpt-a65-mobile-accessibility-20261027-1605"
FILES=("probe_a65.py","a65_mobile_reflow.py","browser_qa_a65.py","test_a65.py",
       "finalize_a65.py","A65_MOBILE_QA_SK.md","ORIGINAL_A64_BROWSER_PROBE.json",
       "A65_TRANSFORM_REPORT.json","BROWSER_QA_A65.json","QA_A65_CLEAN.txt",
       "mobile_comparison.html","desktop_original.png","mobile_original.png",
       "mobile_390.png","mobile_320.png","desktop_1440.png","EVIDENCE_A65.json")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def once(p,s):
    if p.exists():
        if p.read_text(encoding="utf-8")!=s:raise RuntimeError("IMMUTABLE_CONFLICT:"+str(p))
    else:p.write_text(s,encoding="utf-8")
def guard():
    for r in (CENTER,CENTER/"recovery",D,CENTER.parent/"temp_coding",CENTER.parent/"EduMotionPipeline"):
        for n in ("STOP","PAUSE","STOP.flag","PAUSE.flag"):
            if (r/n).exists():raise RuntimeError("STOP_PAUSE:"+str(r/n))
def run(*args):
    p=subprocess.run([sys.executable,*args],cwd=D,capture_output=True,text=True,timeout=45)
    if p.returncode:raise RuntimeError("QA_FAILED:"+repr(args)+p.stderr[-1000:]+p.stdout[-400:])
    return p
def main():
    guard()
    run("a65_mobile_reflow.py")
    b=run("browser_qa_a65.py")
    browser=json.loads(b.stdout)
    assert browser["qa"]=="PASS"
    assert all(v["scrollWidth"]<=v["width"] for v in browser["screens"].values())
    u=run("-m","unittest","-v","test_a65")
    if not re.search(r"Ran 8 tests in [0-9.]+s",u.stderr) or "\nOK" not in u.stderr:
        raise RuntimeError("UNEXPECTED_UNIT_OUTPUT")
    clean=re.sub(r"Ran 8 tests in [0-9.]+s","Ran 8 tests in <variable>s",u.stderr)
    once(D/"QA_A65_CLEAN.txt",clean)
    old=json.loads((D/"ORIGINAL_A64_BROWSER_PROBE.json").read_text(encoding="utf-8"))
    assert old["mobile"]["scrollWidth"]==599 and old["mobile"]["viewport"]==390
    assert browser["original_sha256"]=="5f8cd1410e4f598fe3e31b0254ae3a6e203e0734d0b674e37c01987f09b6c309"
    evidence={
      "scope":"A65_mobile_A64_offline_report_accessibility",
      "task_id":TASK,"artifact_directory":str(D),
      "mobile_report":str(D/"mobile_comparison.html"),
      "original_overflow_px":209,"fixed_mobile_overflow_px":0,
      "browser_viewports":[320,390,1440],"browser_checks":"3/3 PASS",
      "unit_tests":"8/8 PASS","preserved_numeric_cells":60,
      "source_kind":"derived_simulation","physical_release":False,
      "upstream_files_modified":False,
      "status":"VERIFIED_OFFLINE_MOBILE_REFLOW",
      "next_step":"Review the responsive offline report on actual mobile hardware; obtain calibrated measurements before physical validation."
    }
    once(D/"EVIDENCE_A65.json",json.dumps(evidence,indent=2,ensure_ascii=False,sort_keys=True)+"\n")
    manifest={f:sha(D/f) for f in FILES}
    once(D/"SHA256_MANIFEST_A65.json",json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    handoff=(
      "# A65 mobile QA | "+datetime.now().astimezone().isoformat(timespec="seconds")+"\n"
      "Primary SynapseMCP Web available; STOP/PAUSE checked; existing task review/planned without worker.\n"
      "Reproduced original A64 mobile overflow: 599px content in 390px viewport (+209px).\n"
      "New isolated mobile_comparison.html; 320px, 390px and 1440px browser tests all PASS without horizontal overflow.\n"
      "Preserved 2 tables, 10 rows, 60 cells, all numeric values and DERIVED_SIMULATION warning.\n"
      "QA: 8/8 unit tests, 3/3 headless Chrome viewports; original browser failure CP1251 console encoding corrected and retested.\n"
      "No modifications to A60-A64, shared GUI, browser profile, GPU, VRS, OAuth, Codex or foreign worktrees.\n"
      "Evidence SHA256: "+sha(D/"EVIDENCE_A65.json")+"\n"
      "Manifest SHA256: "+sha(D/"SHA256_MANIFEST_A65.json")+"\n"
      "NEXT: "+evidence["next_step"]+"\n"
    )
    once(D/"FINAL_HANDOFF.md",handoff)
    payload={
      "scope":evidence["scope"],"artifact_directory":str(D),"mobile_report":evidence["mobile_report"],
      "evidence_sha256":sha(D/"EVIDENCE_A65.json"),"manifest_sha256":sha(D/"SHA256_MANIFEST_A65.json"),
      "handoff_sha256":sha(D/"FINAL_HANDOFF.md"),
      "QA":"8/8 unittest; 3/3 isolated Chrome; 60/60 cells preserved",
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
    once(D/"REGISTRY_RESULT_A65.json",json.dumps({"event_id":event_id,"task_id":TASK,**payload},indent=2,ensure_ascii=False,sort_keys=True)+"\n")
    print(json.dumps({"event_id":event_id,"evidence_sha256":payload["evidence_sha256"],
                      "handoff_sha256":payload["handoff_sha256"],"manifest_entries":len(manifest)}))
if __name__=="__main__":main()
