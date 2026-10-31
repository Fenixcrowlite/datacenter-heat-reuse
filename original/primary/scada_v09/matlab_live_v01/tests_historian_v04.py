"""Independent tests: v04-only opt-in visited historian, no live DB touched."""
from __future__ import annotations
import pathlib,sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from historian_v04 import validate_record,record_visit,read_visited

JOB1="ca74c32211a44b6d9e83cd61d96cf59f"
JOB2="79b874c619674e1e966c72bf92eb67b3"

class HistorianV04Tests(unittest.TestCase):
    def setUp(self):
        self.dir=tempfile.TemporaryDirectory()
        self.db=pathlib.Path(self.dir.name)/"isolated_v04.sqlite"
    def tearDown(self):self.dir.cleanup()
    def test_exact_saved_job(self):
        sha,values=validate_record(JOB1,80)
        self.assertEqual(len(sha),64)
        self.assertAlmostEqual(values["cas_h"],20)
        self.assertIn("T_pool_C",values)
    def test_dedupe(self):
        self.assertTrue(record_visit(JOB1,0,self.db)["added"])
        self.assertFalse(record_visit(JOB1,0,self.db)["added"])
        rows=read_visited(JOB1,self.db)["rows"]
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["sample_index"],0)
    def test_order_and_indices(self):
        for i in (100,1,80):record_visit(JOB1,i,self.db)
        self.assertEqual([r["sample_index"] for r in read_visited(JOB1,self.db)["rows"]],[1,80,100])
    def test_job_namespace_separation(self):
        record_visit(JOB1,0,self.db)
        record_visit(JOB2,0,self.db)
        self.assertEqual(len(read_visited(JOB1,self.db)["rows"]),1)
        self.assertEqual(len(read_visited(JOB2,self.db)["rows"]),1)
    def test_enforced_source_class(self):
        with patch("historian_v04.safe_result", return_value={"metadata":
            {"source_class":"MEASURED","derived_quality":"A","hardware_enabled":True}}):
            with self.assertRaises(ValueError):record_visit(JOB1,0,self.db)
    def test_reject_path_and_negative(self):
        for jid in ("../a","../"+"a"*29,"G"*32,"b"*31,"","x"*32):
            with self.subTest(jid=jid),self.assertRaises(ValueError):
                record_visit(jid,0,self.db)
    def test_reject_bad_index(self):
        for index in (-1,672,True,1.3,"12"):
            with self.subTest(index=index),self.assertRaises(ValueError):
                record_visit(JOB1,index,self.db)
    def test_reject_checksum_drift_after_saved_run(self):
        bad={"metadata":{"source_class":"D_SYNTHETIC","derived_quality":"D_DERIVED",
             "hardware_enabled":False,"status":"VERIFIED_SIMULINK_NEW_RUN"},
             "source_sha256":"f"*64,
             "rows":[{"cas_h":0.0,"T_pool_C":16.0,"Q_pool_W":1.0,
                      "Q_DH_W":2.0,"Q_reject_W":3.0,"P_HP_W":4.0}]}
        with patch("historian_v04.safe_result", return_value=bad):
            with self.assertRaisesRegex(ValueError,"Source model changed"):
                record_visit(JOB1,0,self.db)

    def test_read_metadata_not_v08(self):
        record_visit(JOB1,0,self.db)
        m=read_visited(JOB1,self.db)["metadata"]
        self.assertEqual(m["derived_quality"],"D_DERIVED")
        self.assertTrue(m["not_v08_native_historian"])
        self.assertFalse(m["hardware_enabled"])
    def test_no_global_native_db_created(self):
        record_visit(JOB1,0,self.db)
        self.assertTrue(self.db.exists())
        self.assertEqual(len(list(pathlib.Path(self.dir.name).glob("*.sqlite"))),1)
    def test_history_limit_validation(self):
        record_visit(JOB1,0,self.db)
        for limit in (0,673,True,1.1,"5"):
            with self.subTest(limit=limit),self.assertRaises(ValueError):
                read_visited(JOB1,self.db,limit=limit)
if __name__=="__main__":unittest.main()
