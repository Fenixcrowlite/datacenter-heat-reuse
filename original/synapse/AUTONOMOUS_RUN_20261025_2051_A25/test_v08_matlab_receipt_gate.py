"""Mutation tests: synthetic fixture only; never claim MATLAB actually ran."""
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import v08_matlab_receipt_gate as gate

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

class ReceiptGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.top = Path(self.temp.name)
        self.root = self.top / "project"
        self.root.mkdir()
        self.receipt_dir = self.top / "receipt"
        self.receipt_dir.mkdir()
        self.log = self.receipt_dir / "matlab_v08.log"
        self.receipt = self.receipt_dir / "receipt.json"
        self.put(gate.MODEL, b"synthetic-model-fixture")
        self.put(gate.SCRIPT, b"synthetic-m-script-fixture")
        self.put(gate.MANIFEST, {"classification": "D_SYNTHETIC_NEVER_FIELD_MEASUREMENT",
                                "scenario_count": 8,
                                "cases": [{"case": x} for x in gate.CASES]})
        self.put(gate.RESULTS, {"classification": "D_SYNTHETIC_NO_REAL_SENSOR_MEASUREMENT",
                               "cases": [{"scenario": x} for x in gate.CASES]})
        self.put(gate.QA, {"status": "PASS", "source_class": "D_SYNTHETIC_REPLAY",
                           "cases": [{"name": x} for x in gate.CASES],
                           "models_sha256": {gate.MODEL: sha(self.root / gate.MODEL)}})
        for case in gate.CASES:
            self.put(f"{gate.BASE}/sim_v08_{case}_SK.csv", "cas_h,Q\n0,1\n")
        self.current = gate.snapshot(self.root)
        self.log.write_text("".join(f"V08_REPLAY_PASS {x} T_delta=0 C Q_delta=0 W latch_delta=0\n"
                                    for x in gate.CASES)
                            + "V08_ALL_REPLAY_CASES_PASS 8\n", encoding="utf-8")
        self.r = {"schema": "dchr.v08.matlab_execution_receipt.v1",
                  "source_class": "D_SYNTHETIC", "exit_code": 0,
                  "matlab_release": "R2026a",
                  "started_utc": "2026-10-25T12:00:00+00:00",
                  "finished_utc": "2026-10-25T12:05:00+00:00",
                  "sha256": {k: v for k, v in self.current["sha256"].items()
                             if k in {gate.MODEL, gate.SCRIPT, gate.MANIFEST,
                                      gate.QA, gate.RESULTS}},
                  "outputs": {x: self.current["sha256"][f"{gate.BASE}/sim_v08_{x}_SK.csv"]
                              for x in gate.CASES},
                  "log_file": self.log.name, "log_sha256": sha(self.log)}
        self.save()

    def put(self, rel, data):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, dict):
            path.write_text(json.dumps(data), encoding="utf-8")
        elif isinstance(data, bytes):
            path.write_bytes(data)
        else:
            path.write_text(data, encoding="utf-8")

    def save(self):
        self.receipt.write_text(json.dumps(self.r), encoding="utf-8")

    def reject(self, error):
        self.save()
        with self.assertRaisesRegex(ValueError, error):
            gate.validate_receipt(self.root, self.receipt, gate.snapshot(self.root))

    def test_valid_receipt_consistency(self):
        r = gate.validate_receipt(self.root, self.receipt, self.current)
        self.assertEqual(r["case_pass_markers"], 8)
        self.assertEqual(r["duration_seconds"], 300)
        self.assertIn("NOT_INDEPENDENT", r["status"])

    def test_no_receipt_is_blocked(self):
        r = gate.audit(self.root)
        self.assertEqual(r["status"], "BLOCKED_MATLAB_EXECUTION_RECEIPT_MISSING")
        self.assertEqual(len(r["current_sha256"]), 13)

    def test_mutated_model(self):
        self.put(gate.MODEL, b"changed")
        with self.assertRaisesRegex(ValueError, "MODEL_SHA_QA_MISMATCH"):
            gate.snapshot(self.root)

    def test_mutated_manifest_class(self):
        self.put(gate.MANIFEST, {"classification": "FIELD_MEASUREMENT",
                               "scenario_count": 8, "cases": [{"case": x} for x in gate.CASES]})
        with self.assertRaisesRegex(ValueError, "MANIFEST_SOURCE_CLASS"):
            gate.snapshot(self.root)

    def test_missing_manifest_case(self):
        self.put(gate.MANIFEST, {"classification": "D_SYNTHETIC_NEVER_FIELD_MEASUREMENT",
                               "scenario_count": 8, "cases": [{"case": x} for x in gate.CASES[:-1]]})
        with self.assertRaisesRegex(ValueError, "MANIFEST_CASES"):
            gate.snapshot(self.root)

    def test_receipt_wrong_source_hash(self):
        self.r["sha256"][gate.SCRIPT] = "0" * 64
        self.reject("INPUT_SHA_MISMATCH")

    def test_receipt_wrong_output_hash(self):
        self.r["outputs"][gate.CASES[0]] = "0" * 64
        self.reject("OUTPUT_SHA_MISMATCH")

    def test_receipt_missing_output(self):
        del self.r["outputs"][gate.CASES[0]]
        self.reject("OUTPUT_CASES")

    def test_receipt_nonzero_exit(self):
        self.r["exit_code"] = 1
        self.reject("NONZERO_EXIT")

    def test_receipt_bool_exit_rejected(self):
        self.r["exit_code"] = False
        self.reject("NONZERO_EXIT")

    def test_receipt_wrong_release(self):
        self.r["matlab_release"] = "unknown"
        self.reject("MATLAB_RELEASE_UNVERIFIED")

    def test_receipt_naive_timestamp(self):
        self.r["started_utc"] = "2026-10-25T12:00:00"
        self.reject("NAIVE_TIME")

    def test_receipt_negative_duration(self):
        self.r["finished_utc"] = "2026-10-25T11:00:00Z"
        self.reject("INVALID_RUN_DURATION")

    def test_receipt_log_tamper(self):
        self.log.write_text("different", encoding="utf-8")
        self.reject("LOG_SHA_MISMATCH")

    def test_receipt_duplicate_case_marker(self):
        self.log.write_text(self.log.read_text() +
                            f"V08_REPLAY_PASS {gate.CASES[0]} T_delta=0\n", encoding="utf-8")
        self.r["log_sha256"] = sha(self.log)
        self.reject("MATLAB_PASS_MARKERS")

    def test_receipt_missing_final_marker(self):
        self.log.write_text(self.log.read_text().replace("V08_ALL_REPLAY_CASES_PASS 8", ""),
                            encoding="utf-8")
        self.r["log_sha256"] = sha(self.log)
        self.reject("MATLAB_FINAL_MARKER")

    def test_receipt_final_before_cases(self):
        self.log.write_text("V08_ALL_REPLAY_CASES_PASS 8\n" +
                            self.log.read_text().replace("V08_ALL_REPLAY_CASES_PASS 8", ""),
                            encoding="utf-8")
        self.r["log_sha256"] = sha(self.log)
        self.reject("MATLAB_FINAL_MARKER")

    def test_receipt_log_path_escape(self):
        self.r["log_file"] = "../elsewhere.log"
        (self.top / "elsewhere.log").write_text("x", encoding="utf-8")
        self.reject("UNSAFE_PATH")

    def test_receipt_wrong_schema(self):
        self.r["schema"] = "not-v08"
        self.reject("RECEIPT_SCHEMA")

    def test_receipt_wrong_provenance(self):
        self.r["source_class"] = "REAL"
        self.reject("RECEIPT_PROVENANCE")

if __name__ == "__main__":
    unittest.main(verbosity=2)
