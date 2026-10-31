"""Deterministic tests; all fixture measurements are synthetic."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from field_calibration_gate import FIELDS, analyze, covariance, lag1_effective_n


def fixture(root: Path, n=32, source="SYNTHETIC_TEST"):
    root.mkdir(parents=True, exist_ok=True)
    meta = {
        "source_class": source,
        "units": {"flow":"m3/h","hot":"degC","cold":"degC"},
        "sample_period_s": 60.0,
        "max_skew_s": 1.0,
    }
    t0 = datetime(2026, 10, 1, tzinfo=timezone.utc)
    rows = []
    for i in range(n):
        t = (t0+timedelta(seconds=60*i)).isoformat()
        rows.append({
            "flow_time_utc": t, "hot_time_utc": t, "cold_time_utc": t,
            "flow_read_m3h": 30+0.12*math.sin(i*0.71),
            "flow_ref_m3h": 30,
            "hot_read_C": 30+0.05*math.cos(i*0.49),
            "hot_ref_C": 30,
            "cold_read_C": 27+0.04*math.sin(i*0.31+0.7),
            "cold_ref_C": 27,
        })
    if source == "FIELD_CALIBRATION":
        meta["certificates"] = {}
        for s in ("flow","hot","cold"):
            p = root/(s+".cert")
            p.write_text("SYNTHETIC TEST CERTIFICATE ONLY: "+s, encoding="utf8")
            meta["certificates"][s] = {
                "instrument_id": "fixture-"+s,
                "reference_id": "fixture-ref-"+s,
                "file": p.name,
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                "expires_utc": "2027-01-01T00:00:00+00:00",
            }
    csv_path, meta_path = root/"paired.csv", root/"metadata.json"
    with csv_path.open("w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader(); w.writerows(rows)
    meta_path.write_text(json.dumps(meta), encoding="utf8")
    return csv_path, meta_path, rows, meta


def rewrite(csv_path, meta_path, rows, meta):
    with csv_path.open("w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader(); w.writerows(rows)
    meta_path.write_text(json.dumps(meta), encoding="utf8")


class CalibrationGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.csv, self.meta, self.rows, self.metadata = fixture(self.root)

    def assert_bad(self):
        with self.assertRaises((ValueError, FileNotFoundError, TypeError)):
            analyze(self.csv, self.meta)

    def test_synthetic_is_not_field_evidence(self):
        x = analyze(self.csv, self.meta)
        self.assertEqual(x["status"], "SYNTHETIC_ONLY_NOT_FIELD_VERIFIED")
        self.assertFalse(x["release_allowed"])
        self.assertEqual(x["sample_count"], 32)
        self.assertEqual(len(x["csv_sha256"]), 64)

    def test_residual_covariance_psd(self):
        x = analyze(self.csv, self.meta)
        c = x["residual_sample_covariance"]
        self.assertTrue(all(c[i][i] > 0 for i in range(3)))
        self.assertAlmostEqual(c[0][1], c[1][0], places=13)
        self.assertTrue(all(abs(x["residual_sample_correlation"][i][j]) <= 1.0000001
                            for i in range(3) for j in range(3)))

    def test_bias_separate_from_variability(self):
        for r in self.rows:
            r["hot_read_C"] += 0.7
        rewrite(self.csv,self.meta,self.rows,self.metadata)
        x = analyze(self.csv,self.meta)
        self.assertAlmostEqual(x["residual_bias"]["hot"], 0.7, delta=0.03)
        self.assertLess(x["residual_standard_deviation"]["hot"], 0.06)

    def test_ar1_diagnostic_is_bounded(self):
        x = analyze(self.csv,self.meta)
        for s in ("flow","hot","cold"):
            self.assertGreaterEqual(x["autocorrelation_diagnostic"][s]["ar1_heuristic_n_eff"],1)
            self.assertLessEqual(x["autocorrelation_diagnostic"][s]["ar1_heuristic_n_eff"],32)

    def test_ar1_negative_not_credited(self):
        self.assertEqual(lag1_effective_n([1,-1]*10)["ar1_heuristic_n_eff"],20)

    def test_too_few_samples(self):
        rewrite(self.csv,self.meta,self.rows[:11],self.metadata);self.assert_bad()

    def test_duplicate_timestamp(self):
        self.rows[5]["flow_time_utc"]=self.rows[4]["flow_time_utc"]
        rewrite(self.csv,self.meta,self.rows,self.metadata);self.assert_bad()

    def test_time_gap(self):
        for i in range(5,32):
            for k in FIELDS[:3]:
                dt=datetime.fromisoformat(self.rows[i][k])+timedelta(seconds=120)
                self.rows[i][k]=dt.isoformat()
        rewrite(self.csv,self.meta,self.rows,self.metadata);self.assert_bad()

    def test_unsynchronized_triplet(self):
        self.rows[4]["hot_time_utc"] = (
            datetime.fromisoformat(self.rows[4]["hot_time_utc"])+timedelta(seconds=2)).isoformat()
        rewrite(self.csv,self.meta,self.rows,self.metadata);self.assert_bad()

    def test_naive_time_rejected(self):
        self.rows[2]["cold_time_utc"]="2026-10-01T00:02:00"
        rewrite(self.csv,self.meta,self.rows,self.metadata);self.assert_bad()

    def test_nan_rejected(self):
        self.rows[3]["flow_read_m3h"]="nan"
        rewrite(self.csv,self.meta,self.rows,self.metadata);self.assert_bad()

    def test_missing_reading_rejected(self):
        self.rows[3]["cold_ref_C"]=""
        rewrite(self.csv,self.meta,self.rows,self.metadata);self.assert_bad()

    def test_nonpositive_flow(self):
        self.rows[3]["flow_ref_m3h"]=-1
        rewrite(self.csv,self.meta,self.rows,self.metadata);self.assert_bad()

    def test_wrong_units(self):
        self.metadata["units"]["flow"]="L/s"
        rewrite(self.csv,self.meta,self.rows,self.metadata);self.assert_bad()

    def test_unknown_class(self):
        self.metadata["source_class"]="REAL"
        rewrite(self.csv,self.meta,self.rows,self.metadata);self.assert_bad()

    def test_invalid_skew_limit(self):
        self.metadata["max_skew_s"]=40
        rewrite(self.csv,self.meta,self.rows,self.metadata);self.assert_bad()

    def test_constant_sensor_residuals(self):
        for r in self.rows:
            r["flow_read_m3h"]=30.1
        rewrite(self.csv,self.meta,self.rows,self.metadata);self.assert_bad()

    def test_field_candidate_still_not_released(self):
        self.csv,self.meta,self.rows,self.metadata=fixture(self.root,source="FIELD_CALIBRATION")
        x=analyze(self.csv,self.meta)
        self.assertFalse(x["release_allowed"])
        self.assertEqual(len(x["certificate_hashes"]),3)
        self.assertIn("REQUIRES_INDEPENDENT",x["status"])

    def test_field_requires_certificates(self):
        self.metadata["source_class"]="FIELD_CALIBRATION"
        rewrite(self.csv,self.meta,self.rows,self.metadata);self.assert_bad()

    def test_certificate_tamper(self):
        self.csv,self.meta,self.rows,self.metadata=fixture(self.root,source="FIELD_CALIBRATION")
        (self.root/"hot.cert").write_text("TAMPERED",encoding="utf8")
        self.assert_bad()

    def test_certificate_expired(self):
        self.csv,self.meta,self.rows,self.metadata=fixture(self.root,source="FIELD_CALIBRATION")
        self.metadata["certificates"]["cold"]["expires_utc"]="2025-01-01T00:00:00Z"
        rewrite(self.csv,self.meta,self.rows,self.metadata);self.assert_bad()

    def test_certificate_path_escape(self):
        self.csv,self.meta,self.rows,self.metadata=fixture(self.root,source="FIELD_CALIBRATION")
        self.metadata["certificates"]["cold"]["file"]="../outside.cert"
        rewrite(self.csv,self.meta,self.rows,self.metadata);self.assert_bad()

    def test_covariance_numerical_identity(self):
        bias,cov=covariance([(1,2,3),(2,3,4),(3,4,5),(4,5,6)])
        self.assertEqual(bias,[2.5,3.5,4.5])
        self.assertAlmostEqual(cov[0][0],5/3)
        self.assertAlmostEqual(cov[0][2],5/3)


if __name__=="__main__":
    unittest.main(verbosity=2)
