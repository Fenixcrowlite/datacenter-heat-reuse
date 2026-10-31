"""Boundary tests for the stdlib-only HTTP simulation server."""
import json
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from heat_reuse.server import make_server


class HttpBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.server = make_server("127.0.0.1", 0, self.temp.name)
        self.worker = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.worker.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.worker.join(timeout=5)
        self.temp.cleanup()

    def status(self, path, *, data=None, headers=None):
        try:
            with urlopen(Request(self.base + path, data=data, headers=headers or {}), timeout=10) as response:
                return response.status
        except HTTPError as error:
            return error.code

    def test_public_health_and_unknown_file(self):
        self.assertEqual(self.status("/api/health"), 200)
        self.assertEqual(self.status("/files/../../heat_reuse/server.py"), 404)
        self.assertEqual(self.status("/api/results/not-an-id"), 400)

    def test_run_requires_json_and_rejects_cross_origin(self):
        payload = json.dumps({"model_id":"pool-v04","steps":1}).encode()
        self.assertEqual(self.status("/api/run", data=payload), 415)
        self.assertEqual(self.status("/api/run", data=payload, headers={
            "Content-Type":"application/json","Origin":"https://foreign.example"}), 403)

    def test_run_refuses_bad_values(self):
        def post(raw):
            return self.status("/api/run", data=raw, headers={"Content-Type":"application/json"})
        self.assertEqual(post(b'{"model_id":"pool-v04","steps":NaN}'), 400)
        self.assertEqual(post(b'{"model_id":"pool-v04","steps":-1}'), 400)
        self.assertEqual(post(b'{"model_id":"pool-v04","unexpected":1}'), 400)


if __name__ == "__main__":
    unittest.main()
