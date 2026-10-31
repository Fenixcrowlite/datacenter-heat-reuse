"""Mutation-based tests for DCHR provenance chain. No source writes."""
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import dchr_lineage_audit as audit

class LineageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=audit.ROOT/"results"
        n="zdravy"
        paths=[
            root/"pool_redundancy_v07"/f"scenar_{n}_SK.csv",
            root/"pool_measurement_v08"/"source_D"/n/"recorded_measured_schema_D.csv",
            root/"pool_measurement_v08"/"source_D"/n/"source_operational_inputs_D_21.csv",
            root/"pool_measurement_v08"/"staged_D"/n/"normalized_measurements_v07.csv",
            root/"pool_measurement_v08"/f"sim_v08_{n}_SK.csv",
        ]
        cls.row=[audit.read_csv(p)[1] for p in paths]
        cls.case=n

    def check(self, rows=None, index=1):
        g,r,o,s,v=rows or copy.deepcopy(self.row)
        audit.verify_row(self.case,index,g,r,o,s,v)

    def test_live_full_lineage(self):
        result=audit.validate()
        self.assertEqual(result["status"],"PASS_STATIC_LINEAGE_NO_MATLAB_REEXECUTION")
        self.assertEqual(result["rows_verified"],5376)
        self.assertEqual(len(result["cases"]),8)
        self.assertEqual(len(result["model_sha256"]),3)

    def test_valid_row(self):
        self.check()

    def test_ingest_eight_significant_digits(self):
        raw=self.row[1]["Q_DC_available_W"]
        staged=self.row[3]["Q_DC_available_W"]
        self.assertEqual(staged,format(float(raw),".8g"))
        self.assertNotEqual(staged,raw)

    def test_stage_corruption(self):
        x=copy.deepcopy(self.row)
        x[3]["Q_DC_available_W"]="201306.76"
        with self.assertRaisesRegex(ValueError,"ingest mismatch"):self.check(x)

    def test_source_sensor_corruption(self):
        x=copy.deepcopy(self.row)
        x[1]["T_pool_sensor1_C"]="999"
        with self.assertRaisesRegex(ValueError,"raw.T_pool_sensor1_C"):self.check(x)

    def test_timestamp_corruption(self):
        x=copy.deepcopy(self.row)
        x[3]["timestamp_utc"]="2026-10-23T00:00:00Z"
        with self.assertRaisesRegex(ValueError,"timestamp mismatch"):self.check(x)

    def test_operational_corruption(self):
        x=copy.deepcopy(self.row)
        x[2]["activity"]="999"
        with self.assertRaisesRegex(ValueError,"operational.activity"):self.check(x)

    def test_external_sensor_corruption(self):
        x=copy.deepcopy(self.row)
        x[4]["external_T1_C"]="999"
        with self.assertRaisesRegex(ValueError,"sim.external.external_T1_C"):self.check(x)

    def test_safety_sensor_corruption(self):
        x=copy.deepcopy(self.row)
        x[4]["sensor2_C"]="999"
        with self.assertRaisesRegex(ValueError,"sim.external.sensor2_C"):self.check(x)

    def test_flow_corruption(self):
        x=copy.deepcopy(self.row)
        x[4]["flow_ok"]="0"
        with self.assertRaisesRegex(ValueError,"sim.flow"):self.check(x)

    def test_v07_temperature_regression(self):
        x=copy.deepcopy(self.row)
        x[4]["T_pool_C"]=str(float(x[0]["T_pool_C"])+.1)
        with self.assertRaisesRegex(ValueError,"temperature regression"):self.check(x)

    def test_v07_heat_regression(self):
        x=copy.deepcopy(self.row)
        x[4]["Q_pool_phys_W"]=str(float(x[0]["Q_pool_phys_W"])+300)
        with self.assertRaisesRegex(ValueError,"heat regression"):self.check(x)

    def test_raw_it_placeholder_corruption(self):
        x=copy.deepcopy(self.row)
        x[1]["P_IT_W"]="123"
        with self.assertRaisesRegex(ValueError,"raw.IT placeholder"):self.check(x)

    def test_nonfinite_rejected(self):
        with self.assertRaisesRegex(ValueError,"mismatch"):
            audit.close("nan","1","bad","zdravy",1)

    def test_invalid_csv_header_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"bad.csv"
            p.write_text("a,a\n1,2\n",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"invalid headers"):
                audit.read_csv(p)

    def test_missing_csv_cell_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"bad.csv"
            p.write_text("a,b\n1\n",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"malformed rows"):
                audit.read_csv(p)

    def test_sha(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"sample"
            p.write_bytes(b"123")
            self.assertEqual(audit.sha(p),hashlib.sha256(b"123").hexdigest())

    def test_model_sha_guard(self):
        real=audit.sha
        def broken(path):
            if str(path).endswith(".slx"):return "0"*64
            return real(path)
        with mock.patch.object(audit,"sha",side_effect=broken):
            with self.assertRaisesRegex(ValueError,"model SHA mismatch"):
                audit.validate()

if __name__=="__main__":
    unittest.main(verbosity=2)
