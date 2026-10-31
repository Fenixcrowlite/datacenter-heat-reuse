"""Contract tests for the loopback native-v08 adapter (no network or MATLAB)."""
import io, json, sys, unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from live_bridge import read_native_v08

class Response:
    status = 200
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, _limit): return self.payload

class Opener:
    def __init__(self, status=None, history=None):
        self.status = status if status is not None else {
            "scenario_id": "zdravy", "index": 4, "csrf_token": "NEVER_FORWARD"}
        self.history = history if history is not None else {
            "scenario_id": "zdravy", "scope": "full",
            "metadata": {"source_class": "D_SYNTHETIC", "quality": "D",
                         "hardware_enabled": False},
            "rows": [{"sample_index": i, "values": {"cas_h": .25*i}}
                     for i in range(672)]
        }
        self.calls=[]
    def open(self, url, timeout=5):
        self.calls.append(url)
        if "/api/status" in url: return Response(self.status)
        return Response(self.history)

class ArchiveTests(unittest.TestCase):
    def get(self, obj):
        with patch("urllib.request.build_opener", return_value=obj):
            return read_native_v08()

    def test_exact_urls_and_no_token(self):
        o=Opener()
        data=self.get(o)
        self.assertEqual(len(data["rows"]),672)
        self.assertEqual(data["rows_kind"],"source_samples_not_visited_historian")
        self.assertNotIn("csrf_token",json.dumps(data))
        self.assertEqual(o.calls,[
          "http://127.0.0.1:8091/api/status",
          "http://127.0.0.1:8091/api/history?scenario=zdravy&scope=full&limit=672"])

    def test_reject_untrusted_scenario(self):
        for s in ("https://evil.test", "../x", "x?scope=foo","", "другое"):
            with self.subTest(s=s):
                o=Opener(status={"scenario_id":s})
                with self.assertRaises(ValueError):
                    self.get(o)
                self.assertEqual(len(o.calls),1)

    def test_reject_mismatched_provenance(self):
        o=Opener()
        for field,value in (("source_class","MEASURED"),("quality","A"),
                            ("hardware_enabled",True)):
            with self.subTest(field=field):
                history=json.loads(json.dumps(o.history))
                history["metadata"][field]=value
                with self.assertRaises(ValueError):
                    self.get(Opener(history=history))

    def test_reject_corrupted_grid_and_foreign_scenario(self):
        o=Opener()
        for kind in ("grid","foreign","short"):
            history=json.loads(json.dumps(o.history))
            if kind=="grid": history["rows"][20]["values"]["cas_h"]=5.5
            if kind=="foreign": history["scenario_id"]="other"
            if kind=="short": history["rows"].pop()
            with self.subTest(kind=kind),self.assertRaises(ValueError):
                self.get(Opener(history=history))

if __name__=="__main__":unittest.main()
