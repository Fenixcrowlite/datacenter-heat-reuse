import math, unittest
from pathlib import Path
from unittest.mock import patch
import live_bridge as live

class ConfigTests(unittest.TestCase):
    def test_defaults(self):
        d=live.parse_config({})
        self.assertEqual(d["pool_limit_kw"],150)
        self.assertEqual(d["dh_off_from_h"],168)
        self.assertTrue(d["hp_pool_enabled"])
    def test_disable_flags(self):
        d=live.parse_config({"pool_enabled":False,"hp_pool_enabled":False,"dh_off_from_h":12})
        self.assertFalse(d["pool_enabled"])
        self.assertFalse(d["hp_pool_enabled"])
        self.assertEqual(d["dh_off_from_h"],12)
    def test_unknown_field_rejected(self):
        with self.assertRaises(ValueError):live.parse_config({"shell":"powershell"})
    def test_invalid_numbers_rejected(self):
        for bad in (math.nan,math.inf,-1,151,True,"100",None):
            with self.subTest(bad=repr(bad)),self.assertRaises(ValueError):
                live.parse_config({"pool_limit_kw":bad})
    def test_incorrect_booleans_rejected(self):
        with self.assertRaises(ValueError):live.parse_config({"dh_enabled":1})
    def test_invalid_id_rejected(self):
        for bad in ("../result.json","X"*32,"0"*31,"0"*33):
            with self.subTest(bad=bad),self.assertRaises(ValueError):live.safe_result(bad)
    def test_stops_on_marker_without_launch(self):
        with patch.object(live,"stopped",return_value=True):
            with self.assertRaises(RuntimeError):live.launch({})
    def test_low_memory_refuses_new_matlab_without_creating_job(self):
        with patch.object(live,"stopped",return_value=False):
            with patch.object(live,"available_ram_mb",return_value=256):
                with self.assertRaisesRegex(RuntimeError,"free RAM"):
                    live.launch({})
    def test_private_source_and_local_python(self):
        self.assertEqual(live.PROJECT.name,"DataCenter_Heat_Reuse")
        self.assertTrue(live.SOURCE_MODEL.is_file())
        self.assertFalse(live.SOURCE_MODEL.is_relative_to(live.JOBS))
    def test_saved_real_simulink_runs(self):
        dirs=[p for p in live.JOBS.glob("*") if (p/"result.json").is_file()]
        self.assertGreaterEqual(len(dirs),2)
        for p in dirs:
            d=live.safe_result(p.name)
            self.assertEqual(len(d["rows"]),672)
            self.assertEqual(d["metadata"]["source_class"],"D_SYNTHETIC")
            self.assertLess(d["metadata"]["closure_flow_W"],1e-5)
    def test_stop_and_whitelist_protect_server(self):
        self.assertEqual(live.ORIGIN_PORT,8094)
        self.assertNotIn("hardware_enabled",live.LIMITS)
        self.assertNotIn("controller_cmd",live.BOOLS)

if __name__=="__main__":unittest.main(verbosity=2)
