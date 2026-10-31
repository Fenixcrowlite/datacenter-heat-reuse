"""A29 deterministic regression and independent A28 integration tests. ALL fixtures synthetic."""
import csv
import hashlib
import json
import math
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

A28 = Path(r"C:\Users\Lysda\Desktop\SynapseControlCenter\recovery\AUTONOMOUS_RUN_20261025_2346_A28")
sys.path.insert(0, str(A28))
from field_calibration_gate import analyze as a28_analyze, FIELDS as A28_FIELDS
from holdout_heatmeter_gate import analyze, COLS, validated_covariance, UNITS

class HoldoutTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.d = Path(self.tmp.name)
        self.cal_csv = self.d/"cal.csv"
        self.cal_meta = self.d/"cal_meta.json"
        self.cal_report = self.d/"cal_report.json"
        self.csv = self.d/"holdout.csv"
        self.meta = self.d/"holdout_meta.json"
        self.meta_data = {
            "source_class":"SYNTHETIC_TEST", "units":dict(UNITS),
            "meter_independent":True, "sample_period_s":60,
            "density_kg_m3":997, "specific_heat_kj_kg_K":4.18,
            "meter_std_uncertainty_kw":1.0
        }
        self.cal_data = {
            "source_class":"SYNTHETIC_TEST",
            "units":{"flow":"m3/h","hot":"degC","cold":"degC"},
            "sample_period_s":60,"max_skew_s":1
        }
        t0=datetime(2026,10,1,tzinfo=timezone.utc)
        self.cal_rows=[]
        for i in range(32):
            t=(t0+timedelta(minutes=i)).isoformat()
            self.cal_rows.append({
                "flow_time_utc":t,"hot_time_utc":t,"cold_time_utc":t,
                "flow_read_m3h":30+0.08*math.sin(i*.7),"flow_ref_m3h":30,
                "hot_read_C":30+0.04*math.cos(i*.43),"hot_ref_C":30,
                "cold_read_C":27+0.03*math.sin(i*.37+.2),"cold_ref_C":27
            })
        self.rows=[]
        t0=datetime(2026,10,2,tzinfo=timezone.utc)
        for i in range(32):
            t=(t0+timedelta(minutes=i)).isoformat()
            q=997*4.18*30*3/3600
            self.rows.append({"time_utc":t,"flow_read_m3h":30,"hot_read_C":30,
                              "cold_read_C":27,"meter_kw":q+0.2*math.sin(i*.7)})
        self.save()

    def save(self):
        with self.cal_csv.open("w",newline="",encoding="utf8") as f:
            w=csv.DictWriter(f,fieldnames=A28_FIELDS);w.writeheader();w.writerows(self.cal_rows)
        self.cal_meta.write_text(json.dumps(self.cal_data),encoding="utf8")
        report=a28_analyze(self.cal_csv,self.cal_meta)
        self.cal_report.write_text(json.dumps(report),encoding="utf8")
        self.save_holdout()

    def save_holdout(self):
        with self.csv.open("w",newline="",encoding="utf8") as f:
            w=csv.DictWriter(f,fieldnames=COLS);w.writeheader();w.writerows(self.rows)
        self.meta.write_text(json.dumps(self.meta_data),encoding="utf8")

    def bad(self):
        with self.assertRaises((ValueError,TypeError,KeyError,FileNotFoundError)):
            analyze(self.cal_report,self.csv,self.meta,self.cal_csv,self.cal_meta)

    def test_integration_synthetic_holdout_never_released(self):
        x=analyze(self.cal_report,self.csv,self.meta,self.cal_csv,self.cal_meta)
        self.assertEqual(x["status"],"SYNTHETIC_ONLY_NOT_FIELD_VERIFIED")
        self.assertFalse(x["release_allowed"])
        self.assertEqual(x["sample_count"],32)
        self.assertLess(x["rmse_kw"],2)
        self.assertAlmostEqual(x["model_energy_kwh_left_rectangle"],53.8,delta=2)
        self.assertEqual(len(x["calibration_report_sha256"]),64)

    def test_energy_difference_consistent(self):
        x=analyze(self.cal_report,self.csv,self.meta,self.cal_csv,self.cal_meta)
        self.assertAlmostEqual(x["energy_difference_kwh"],x["model_energy_kwh_left_rectangle"]-x["meter_energy_kwh_left_rectangle"])

    def test_bias_correction_changes_model(self):
        before=analyze(self.cal_report,self.csv,self.meta,self.cal_csv,self.cal_meta)
        for row in self.cal_rows: row["hot_read_C"]+=0.6
        for row in self.rows: row["hot_read_C"]+=0.6
        self.save()
        after=analyze(self.cal_report,self.csv,self.meta,self.cal_csv,self.cal_meta)
        self.assertAlmostEqual(before["mean_bias_kw"],after["mean_bias_kw"],delta=0.00001)

    def test_positivity_of_propagated_uncertainty(self):
        x=analyze(self.cal_report,self.csv,self.meta,self.cal_csv,self.cal_meta)
        self.assertGreaterEqual(x["pointwise_combined_standard_uncertainty_kw"]["min"],1)

    def test_nonindependent_meter(self):
        self.meta_data["meter_independent"]=False;self.save_holdout();self.bad()

    def test_wrong_units(self):
        self.meta_data["units"]["meter"]="W";self.save_holdout();self.bad()

    def test_unknown_source(self):
        self.meta_data["source_class"]="REAL";self.save_holdout();self.bad()

    def test_source_mismatch(self):
        self.meta_data["source_class"]="FIELD_CALIBRATION";self.save_holdout();self.bad()

    def test_calibration_overlap(self):
        self.rows[0]["time_utc"]=self.cal_rows[-1]["flow_time_utc"]
        self.save_holdout();self.bad()

    def test_reversed_timestamp(self):
        self.rows[8]["time_utc"]=self.rows[7]["time_utc"]
        self.save_holdout();self.bad()

    def test_gap(self):
        for i in range(8,32):
            t=datetime.fromisoformat(self.rows[i]["time_utc"])+timedelta(minutes=3)
            self.rows[i]["time_utc"]=t.isoformat()
        self.save_holdout();self.bad()

    def test_missing_value(self):
        self.rows[5]["meter_kw"]="";self.save_holdout();self.bad()

    def test_nan(self):
        self.rows[5]["flow_read_m3h"]="nan";self.save_holdout();self.bad()

    def test_zero_meter(self):
        self.rows[5]["meter_kw"]=0;self.save_holdout();self.bad()

    def test_negative_temperature_difference(self):
        self.rows[5]["hot_read_C"]=26;self.save_holdout();self.bad()

    def test_nonphysical_water_properties(self):
        self.meta_data["density_kg_m3"]=1500;self.save_holdout();self.bad()

    def test_zero_meter_uncertainty(self):
        self.meta_data["meter_std_uncertainty_kw"]=0;self.save_holdout();self.bad()

    def test_forged_release_flag(self):
        x=json.loads(self.cal_report.read_text());x["release_allowed"]=True
        self.cal_report.write_text(json.dumps(x));self.bad()

    def test_forged_provenance_hash(self):
        x=json.loads(self.cal_report.read_text());x["csv_sha256"]="NOT_A_HASH"
        self.cal_report.write_text(json.dumps(x));self.bad()

    def test_non_psd_covariance(self):
        x=json.loads(self.cal_report.read_text())
        x["residual_sample_covariance"]=[[1,0.99,0.99],[0.99,1,-0.99],[0.99,-0.99,1]]
        self.cal_report.write_text(json.dumps(x));self.bad()

    def test_covariance_analytic_identity(self):
        self.assertEqual(validated_covariance([[1,0,0],[0,4,0],[0,0,9]]),[[1,0,0],[0,4,0],[0,0,9]])

    def test_too_few_holdout_samples(self):
        self.rows=self.rows[:11];self.save_holdout();self.bad()

    def test_tampered_raw_calibration_detected(self):
        self.cal_csv.write_bytes(self.cal_csv.read_bytes()+b"\n")
        self.bad()

    def test_forged_but_psd_covariance_detected(self):
        report=json.loads(self.cal_report.read_text())
        report["residual_sample_covariance"][0][0] *= 1.5
        self.cal_report.write_text(json.dumps(report))
        self.bad()

    def test_forged_bias_detected(self):
        report=json.loads(self.cal_report.read_text())
        report["residual_bias"]["hot"] += 0.1
        self.cal_report.write_text(json.dumps(report))
        self.bad()

    def test_tiny_scale_asymmetry_rejected(self):
        with self.assertRaises(ValueError):
            validated_covariance([[1e-12,5e-13,0],[0,1e-12,0],[0,0,1e-12]])

    def test_field_certificate_missing_fail_closed(self):
        self.cal_data["source_class"]="FIELD_CALIBRATION"
        self.cal_data["certificates"]={}
        for sensor in ("flow","hot","cold"):
            p=self.d/(sensor+".cert")
            p.write_text("SYNTHETIC MOCK CERT "+sensor)
            self.cal_data["certificates"][sensor]={
                "instrument_id":"mock-"+sensor,"reference_id":"mock-ref-"+sensor,
                "file":p.name,"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
                "expires_utc":"2027-01-01T00:00:00Z"}
        self.meta_data["source_class"]="FIELD_CALIBRATION"
        self.save()
        self.bad()

    def test_field_mock_certificate_still_no_release(self):
        self.cal_data["source_class"]="FIELD_CALIBRATION"
        self.cal_data["certificates"]={}
        for sensor in ("flow","hot","cold"):
            p=self.d/(sensor+".cert");p.write_text("MOCK CERT "+sensor)
            self.cal_data["certificates"][sensor]={
                "instrument_id":"mock-"+sensor,"reference_id":"mock-ref-"+sensor,
                "file":p.name,"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
                "expires_utc":"2027-01-01T00:00:00Z"}
        self.meta_data["source_class"]="FIELD_CALIBRATION"
        p=self.d/"meter.cert";p.write_text("MOCK METER CERT")
        self.meta_data["meter_certificate"]={
            "file":p.name,"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
            "instrument_id":"mock-meter","issuer":"mock-issuer",
            "expires_utc":"2027-01-01T00:00:00Z"}
        self.save()
        x=analyze(self.cal_report,self.csv,self.meta,self.cal_csv,self.cal_meta)
        self.assertFalse(x["release_allowed"])
        self.assertEqual(x["status"],"FIELD_HOLDOUT_CANDIDATE_REQUIRES_INDEPENDENT_REVIEW")

if __name__=="__main__":
    unittest.main(verbosity=2)
