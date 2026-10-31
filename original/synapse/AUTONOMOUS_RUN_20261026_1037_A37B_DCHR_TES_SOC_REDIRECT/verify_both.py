"""Final independent manifest/registry check of A37 and A37B."""
from pathlib import Path
import sqlite3,hashlib,json
HERE=Path(__file__).resolve().parent
A37=HERE.parent/"AUTONOMOUS_RUN_20261026_1025_A37_DCHR_IT_THERMAL_PROTECTION"
CENTER=HERE.parent.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    out={"status":"PASS","directories":[],"files_checked":0,"events":[]}
    with sqlite3.connect("file:"+str(CENTER/"tasks.sqlite3")+"?mode=ro",uri=True) as db:
        assert db.execute("pragma quick_check").fetchone()[0]=="ok"
        for d,actor,event_id in [(A37,"chatgpt-a37-dchr-it-thermal-n1-20261026",1216),
                                 (HERE,"chatgpt-a37b-dchr-tes-soc-20261026",1217)]:
            manifest=json.loads((d/"SHA256_MANIFEST.json").read_text(encoding="utf8"))
            for name,expected in manifest.items():
                assert sha(d/name)==expected,(d,name)
                out["files_checked"]+=1
            evidence_sha=sha(d/"EVIDENCE.json")
            manifest_sha=sha(d/"SHA256_MANIFEST.json")
            rows=db.execute("select id,data_json from task_events where task_id=? and actor=? and kind='evidence'",
                            ("scc-3d9d172beb6e1b",actor)).fetchall()
            assert len(rows)==1 and rows[0][0]==event_id
            payload=json.loads(rows[0][1])
            assert payload["evidence_sha256"]==evidence_sha
            assert payload["manifest_sha256"]==manifest_sha
            assert payload["artifact_directory"]==str(d)
            out["directories"].append(str(d))
            out["events"].append(event_id)
    (HERE/"FINAL_QA.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
