"""End-to-end HTTP smoke tests with an isolated temporary experiment database."""
import json
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from heat_reuse.server import make_server


class HttpIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.server = make_server("127.0.0.1", 0, self.tmp.name)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = "http://127.0.0.1:" + str(self.server.server_port)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.tmp.cleanup()

    def request(self, path, payload=None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"} if payload is not None else {}
        with urlopen(Request(self.base + path, data=data, headers=headers), timeout=30) as response:
            return response.status, response.headers, response.read()

    def test_health_and_models(self):
        status, _, raw = self.request("/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(raw)["mode"], "SIMULATION")
        _, _, raw = self.request("/api/models")
        models = json.loads(raw)["models"]
        self.assertTrue({"annual-v2", "pool-v04", "stateflow-v85"}.issubset({m["id"] for m in models}))

    def test_run_persist_reload_and_export(self):
        status, _, raw = self.request("/api/run", {
            "model_id": "pool-v04", "scenario": "zaklad", "steps": 8
        })
        self.assertEqual(status, 200)
        result = json.loads(raw)
        self.assertEqual(result["source_kind"], "PYTHON_COMPUTED")
        self.assertEqual(len(result["rows"]), 8)
        identifier = result["id"]
        _, _, raw = self.request("/api/results/" + identifier)
        self.assertEqual(json.loads(raw)["id"], identifier)
        _, headers, raw = self.request("/api/results/" + identifier + ".csv")
        self.assertIn("text/csv", headers["Content-Type"])
        self.assertEqual(len(raw.decode("utf-8").splitlines()), 9)
        _, _, raw = self.request("/api/results")
        self.assertTrue(any(r["id"] == identifier for r in json.loads(raw)))

    def test_invalid_payload_is_rejected(self):
        try:
            self.request("/api/run", {"model_id": "unported", "steps": 2})
        except HTTPError as error:
            self.assertEqual(error.code, 400)
        else:
            self.fail("Unsupported model was accepted")


if __name__ == "__main__":
    unittest.main()
