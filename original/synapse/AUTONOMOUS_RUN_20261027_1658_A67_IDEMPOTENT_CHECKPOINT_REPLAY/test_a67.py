import hashlib,json,sqlite3,tempfile,unittest
from contextlib import closing
from pathlib import Path
from a67_replay_gate import audit,sha
TASK="scc-3d9d172beb6e1b"
ACTOR="test-actor"
class GateTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        self.d=Path(self.t.name)
        self.db=self.d/"registry.sqlite3"
        (self.d/"artifact.txt").write_text("verified",encoding="utf-8")
        (self.d/"EVIDENCE_A67.json").write_text(json.dumps({"task_id":TASK,"physical_release":False}),encoding="utf-8")
        (self.d/"FINAL_HANDOFF.md").write_text("handoff",encoding="utf-8")
        self.manifest={"artifact.txt":sha(self.d/"artifact.txt")}
        self.save_manifest()
        with closing(sqlite3.connect(self.db,isolation_level=None)) as c:
            c.execute("CREATE TABLE task_events(id INTEGER PRIMARY KEY,task_id TEXT,actor TEXT,kind TEXT,data_json TEXT)")
            c.execute("INSERT INTO task_events(task_id,actor,kind,data_json) VALUES(?,?,?,?)",(TASK,ACTOR,"evidence",json.dumps(self.payload())))
    def tearDown(self):self.t.cleanup()
    def save_manifest(self):
        (self.d/"SHA256_MANIFEST_A67.json").write_text(json.dumps(self.manifest),encoding="utf-8")
    def payload(self):
        return {"evidence_sha256":sha(self.d/"EVIDENCE_A67.json"),
                "manifest_sha256":sha(self.d/"SHA256_MANIFEST_A67.json"),
                "handoff_sha256":sha(self.d/"FINAL_HANDOFF.md"),"physical_release":False}
    def check(self):return audit(self.d,self.db,TASK,ACTOR,"A67")
    def test_valid_replay_twice(self):
        a=self.check();b=self.check()
        self.assertEqual(a,b)
        self.assertEqual(a["mutations"],0)
    def test_corrupted_artifact_rejected(self):
        (self.d/"artifact.txt").write_text("tampered")
        with self.assertRaisesRegex(ValueError,"HASH_MISMATCH"):self.check()
    def test_duplicate_event_rejected(self):
        with closing(sqlite3.connect(self.db,isolation_level=None)) as c:
            c.execute("INSERT INTO task_events(task_id,actor,kind,data_json) VALUES(?,?,?,?)",(TASK,ACTOR,"evidence",json.dumps(self.payload())))
        with self.assertRaisesRegex(ValueError,"EVENT_COUNT"):self.check()
    def test_event_digest_rejected(self):
        with closing(sqlite3.connect(self.db,isolation_level=None)) as c:
            c.execute("UPDATE task_events SET data_json=?",(json.dumps({"evidence_sha256":"0"*64}),))
        with self.assertRaisesRegex(ValueError,"EVENT_HASH_MISMATCH"):self.check()
    def test_path_traversal_rejected(self):
        self.manifest={"../artifact.txt":"0"*64};self.save_manifest()
        with self.assertRaisesRegex(ValueError,"UNSAFE_MANIFEST"):self.check()
    def test_missing_file_rejected(self):
        (self.d/"artifact.txt").unlink()
        with self.assertRaisesRegex(ValueError,"HASH_MISMATCH"):self.check()
    def test_evidence_provenance_rejected(self):
        (self.d/"EVIDENCE_A67.json").write_text(json.dumps({"task_id":TASK,"physical_release":True}))
        with self.assertRaisesRegex(ValueError,"EVIDENCE_PROVENANCE"):self.check()
if __name__=="__main__":unittest.main()
