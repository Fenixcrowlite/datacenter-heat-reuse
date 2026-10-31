"""Behavioral regression tests for the local, synthetic SCADA replay.

The source CSVs are read only. Runtime databases and STOP fixtures are isolated
inside this workspace and removed after each test. HTTP servers bind ephemeral
loopback ports and are always shut down before a test returns.
"""
from __future__ import annotations

import csv
import hashlib
import http.client
import json
import math
from pathlib import Path
import tempfile
import threading
import time
import unittest

import scada_server as scada

WORKSPACE = Path(__file__).resolve().parents[1]
DATA_DIR = WORKSPACE.parent / "results" / "pool_measurement_v08"


class DatasetFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = scada.Dataset(data_dir=DATA_DIR)


class DatasetTests(DatasetFixture):
    def test_all_eight_native_runs_have_672_finite_rows_at_900_seconds(self):
        self.assertEqual(8, len(self.dataset.scenarios))
        for scenario_id, scenario in self.dataset.scenarios.items():
            with self.subTest(scenario=scenario_id):
                self.assertEqual(672, len(scenario.rows))
                self.assertEqual(0, scenario.rows[0]["cas_h"])
                self.assertEqual(167.75, scenario.rows[-1]["cas_h"])
                for index, row in enumerate(scenario.rows):
                    self.assertEqual(index / 4, row["cas_h"])
                    self.assertTrue(all(math.isfinite(value) for value in row.values()))
                self.assertIn("COP", scenario.rows[0])
                self.assertIn("T_IT_model_C", scenario.rows[0])
                self.assertIn("E_TES_J", scenario.rows[0])

    def test_import_preserves_every_native_csv_value_without_interpolation(self):
        for scenario_id, scenario in self.dataset.scenarios.items():
            source = DATA_DIR / f"sim_v08_{scenario_id}_SK.csv"
            with self.subTest(scenario=scenario_id):
                with source.open(encoding="utf-8-sig", newline="") as handle:
                    expected = [{key: float(value) for key, value in row.items()}
                                for row in csv.DictReader(handle)]
                self.assertEqual(expected, scenario.rows)
                self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), scenario.sha256)

    def test_independent_qa_is_loaded_with_synthetic_classification(self):
        self.assertEqual("PASS", self.dataset.qa["status"])
        self.assertEqual("D_SYNTHETIC_REPLAY", self.dataset.qa["source_class"])
        self.assertEqual(8, len(self.dataset.qa["cases"]))
        self.assertTrue(all(case["source_class"] == "D_SYNTHETIC"
                            for case in self.dataset.qa["cases"]))
        self.assertIn("not field sensor independence", self.dataset.qa["semantic_warning"])


class EngineFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = scada.Dataset(data_dir=DATA_DIR)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="scada-test-", dir=WORKSPACE)
        self.runtime = Path(self.tmp.name)
        self.stop_path = self.runtime / "STOP"
        self.engine = scada.ReplayEngine(self.dataset, self.runtime,
                                         stop_path=self.stop_path, start_worker=False)

    def tearDown(self):
        self.engine.close()
        self.tmp.cleanup()


class AlarmTests(DatasetFixture):
    def test_native_alarm_flags_have_codes_messages_and_severity(self):
        healthy = self.dataset.scenarios["zdravy"].rows[0]
        self.assertEqual([], scada.evaluate_alarms(healthy))
        fault = next(row for row in self.dataset.scenarios["primarny_ventil_zaseknuty"].rows
                     if row["safety_latch"] and row["primary_valve_fault"])
        alarms = scada.evaluate_alarms(fault)
        codes = {alarm["code"] for alarm in alarms}
        self.assertIn("safety_latch", codes)
        self.assertIn("primary_valve_fault", codes)
        for alarm in alarms:
            self.assertTrue(alarm["message"])
            self.assertIn(alarm["severity"], {"INFO", "WARNING", "CRITICAL"})

    def test_it_model_risk_and_unhandled_heat_use_real_csv_signals(self):
        scenario = self.dataset.scenarios["oba_REJECT_off_bez_shedding"]
        row = max(scenario.rows, key=lambda item: item["T_IT_model_C"])
        self.assertEqual(1, row["IT_model_alarm"])
        codes = {alarm["code"] for alarm in scada.evaluate_alarms(row)}
        self.assertIn("IT_model_alarm", codes)
        unhandled = max(scenario.rows, key=lambda item: item["Q_unhandled_W"])
        self.assertGreater(unhandled["Q_unhandled_W"], 40000)
        self.assertIn("Q_unhandled_W", {alarm["code"] for alarm in scada.evaluate_alarms(unhandled)})


class ReplayTests(EngineFixture):
    def test_pause_play_tick_use_one_exact_csv_sample(self):
        initial = self.engine.snapshot()
        self.assertFalse(initial["status"]["playing"])
        self.assertEqual(0, initial["status"]["index"])
        self.engine.tick()
        self.assertEqual(0, self.engine.status()["index"])
        self.engine.control({"action": "play"})
        self.engine.tick()
        current = self.engine.snapshot()
        self.assertEqual(1, current["status"]["index"])
        scenario = self.dataset.scenarios[current["status"]["scenario_id"]]
        self.assertEqual(scenario.rows[1], current["values"])
        self.engine.control({"action": "pause"})
        self.engine.tick()
        self.assertEqual(1, self.engine.status()["index"])

    def test_seek_and_reset_preserve_csv_values_and_pause(self):
        self.engine.control({"action": "seek", "index": 17})
        snapshot = self.engine.snapshot()
        self.assertEqual(17, snapshot["status"]["index"])
        self.assertEqual(4.25, snapshot["values"]["cas_h"])
        scenario = self.dataset.scenarios[snapshot["status"]["scenario_id"]]
        self.assertEqual(scenario.rows[17], snapshot["values"])
        self.engine.control({"action": "reset"})
        self.assertEqual(0, self.engine.status()["index"])
        self.assertFalse(self.engine.status()["playing"])

    def test_scenario_switch_uses_fixed_identifier(self):
        self.engine.control({"action": "scenario", "scenario_id": "oba_REJECT_off_bez_shedding"})
        snapshot = self.engine.snapshot()
        self.assertEqual("oba_REJECT_off_bez_shedding", snapshot["status"]["scenario_id"])
        self.assertEqual(self.dataset.scenarios["oba_REJECT_off_bez_shedding"].rows[0], snapshot["values"])
        self.assertFalse(snapshot["status"]["playing"])
        with self.assertRaises(ValueError):
            self.engine.control({"action": "scenario", "scenario_id": "../../STOP"})

    def test_replay_stops_at_last_exact_sample(self):
        self.engine.control({"action": "seek", "index": 670})
        self.engine.control({"action": "play"})
        self.engine.tick()
        self.engine.tick()
        snapshot = self.engine.snapshot()
        self.assertEqual(671, snapshot["status"]["index"])
        self.assertEqual(167.75, snapshot["values"]["cas_h"])
        self.assertFalse(snapshot["status"]["playing"])

    def test_stop_file_prevents_replay_and_is_never_deleted(self):
        self.engine.control({"action": "play"})
        self.stop_path.write_text("Persisted user STOP", encoding="utf-8")
        self.engine.tick()
        self.assertFalse(self.engine.status()["playing"])
        self.assertEqual(0, self.engine.status()["index"])
        with self.assertRaises(RuntimeError):
            self.engine.control({"action": "play"})
        self.assertTrue(self.stop_path.exists())
        self.assertIn("STOP", json.dumps(self.engine.alarms(), ensure_ascii=False))
        self.engine.close()
        self.engine = scada.ReplayEngine(self.dataset, self.runtime,
                                         stop_path=self.stop_path, start_worker=False)
        self.assertFalse(self.engine.status()["playing"])
        with self.assertRaises(RuntimeError):
            self.engine.control({"action": "play"})
        self.assertEqual("Persisted user STOP", self.stop_path.read_text(encoding="utf-8"))

    def test_worker_observes_stop_without_browser_polling(self):
        self.engine.start_worker()
        self.engine.control({"action": "speed", "speed": 16})
        self.engine.control({"action": "play"})
        deadline = time.monotonic() + 1
        while self.engine.index == 0 and time.monotonic() < deadline:
            threading.Event().wait(0.01)
        self.assertGreater(self.engine.index, 0)
        self.stop_path.write_text("worker STOP", encoding="utf-8")
        deadline = time.monotonic() + 1
        # Inspect the public state directly so status() cannot mask a worker bug
        # by performing the STOP check itself.
        while self.engine.playing and time.monotonic() < deadline:
            threading.Event().wait(0.01)
        self.assertFalse(self.engine.playing)
        index = self.engine.index
        threading.Event().wait(0.15)
        self.assertEqual(index, self.engine.index)
        self.assertTrue(self.stop_path.exists())

    def test_snapshot_cannot_export_control_token(self):
        snapshot = self.engine.snapshot()
        self.assertNotIn("csrf_token", snapshot["status"])
        self.assertNotIn(self.engine.token, json.dumps(snapshot))

    def test_speed_and_seek_clamp_to_safe_replay_bounds(self):
        self.engine.control({"action": "speed", "speed": 0})
        self.assertEqual(0.5, self.engine.status()["speed"])
        self.engine.control({"action": "speed", "speed": 999})
        self.assertEqual(16, self.engine.status()["speed"])
        self.engine.control({"action": "speed", "speed": 10 ** 3000})
        self.assertEqual(16, self.engine.status()["speed"])
        self.engine.control({"action": "speed", "speed": -(10 ** 3000)})
        self.assertEqual(0.5, self.engine.status()["speed"])
        self.engine.control({"action": "seek", "index": -20})
        self.assertEqual(0, self.engine.status()["index"])
        self.engine.control({"action": "seek", "index": 99999})
        self.assertEqual(671, self.engine.status()["index"])
        for value in (True, 1.5, "2", None):
            with self.subTest(index=value):
                with self.assertRaises(ValueError):
                    self.engine.control({"action": "seek", "index": value})

    def test_historian_deduplicates_replay_and_survives_restart(self):
        self.engine.control({"action": "seek", "index": 17})
        initial = self.engine.historian(limit=99999)["rows"]
        self.assertEqual({0, 17}, {row["sample_index"] for row in initial})
        for _ in range(3):
            self.engine.control({"action": "reset"})
            self.engine.control({"action": "seek", "index": 17})
        rows = self.engine.historian(limit=99999)["rows"]
        self.assertEqual(2, len(rows))
        for row in rows:
            self.assertEqual("D", row["quality"])
            self.assertEqual("D_SYNTHETIC", row["source_class"])
            self.assertTrue(row["first_seen"])
            self.assertTrue(row["last_seen"])
        self.engine.close()
        self.engine = scada.ReplayEngine(self.dataset, self.runtime,
                                         stop_path=self.stop_path, start_worker=False)
        self.assertEqual(2, len(self.engine.historian()["rows"]))

    def test_history_is_exact_source_prefix_and_full_comparison_is_bounded(self):
        self.engine.control({"action": "seek", "index": 17})
        history = self.engine.history(limit=3)["rows"]
        self.assertEqual([15, 16, 17], [row["sample_index"] for row in history])
        for row in history:
            self.assertEqual(self.dataset.scenarios["zdravy"].rows[row["sample_index"]], row["values"])
        complete = self.engine.history(limit=99999, scenario_id="oba_ventily_zaseknute", scope="full")["rows"]
        self.assertEqual(672, len(complete))
        self.assertEqual(671, complete[-1]["sample_index"])
        with self.assertRaises(ValueError):
            self.engine.history(scenario_id="../../STOP")

    def test_alarm_events_are_changes_acknowledgment_does_not_change_csv(self):
        scenario = self.dataset.scenarios["primarny_ventil_zaseknuty"]
        index = next(index for index, row in enumerate(scenario.rows) if row["safety_latch"])
        self.engine.control({"action": "scenario", "scenario_id": scenario.id})
        self.engine.control({"action": "seek", "index": index})
        alarms = self.engine.alarms()
        event = next(event for event in alarms["events"] if event["code"] == "safety_latch" and event["state"] == "ACTIVE")
        before = self.engine.snapshot()["values"]
        self.engine.control({"action": "ack", "alarm_id": event["id"]})
        self.assertEqual(before, self.engine.snapshot()["values"])
        active = next(alarm for alarm in self.engine.alarms()["active_alarms"] if alarm["code"] == "safety_latch")
        self.assertTrue(active["acknowledged"])
        count = len(self.engine.alarms(limit=5000)["events"])
        for _ in range(4):
            self.engine.control({"action": "pause"})
            self.engine.snapshot()
        self.assertEqual(count, len(self.engine.alarms(limit=5000)["events"]))
        self.engine.control({"action": "reset"})
        clears = self.engine.alarms(limit=5000)["events"]
        self.assertTrue(any(event["code"] == "safety_latch" and event["state"] == "CLEARED" for event in clears))

    def test_historical_ack_preserves_original_scenario_and_sample(self):
        scenario = self.dataset.scenarios["primarny_ventil_zaseknuty"]
        index = next(index for index, row in enumerate(scenario.rows) if row["safety_latch"])
        self.engine.control({"action": "scenario", "scenario_id": scenario.id})
        self.engine.control({"action": "seek", "index": index})
        original = next(event for event in self.engine.alarms()["events"]
                        if event["code"] == "safety_latch" and event["state"] == "ACTIVE")
        self.engine.control({"action": "scenario", "scenario_id": "zdravy"})
        self.engine.control({"action": "seek", "index": 17})
        self.engine.control({"action": "ack", "alarm_id": original["id"]})
        ack = next(event for event in self.engine.alarms()["events"]
                   if event["code"] == "safety_latch" and event["state"] == "ACK")
        self.assertEqual(original["scenario_id"], ack["scenario_id"])
        self.assertEqual(original["sample_index"], ack["sample_index"])
        self.assertEqual(original["time_h"], ack["time_h"])
        self.assertEqual("zdravy", self.engine.status()["scenario_id"])
        self.assertEqual(17, self.engine.status()["index"])
        self.assertFalse(self.engine.snapshot()["active_alarms"])

    def test_ack_of_prior_episode_does_not_ack_current_alarm(self):
        scenario = self.dataset.scenarios["primarny_ventil_zaseknuty"]
        index = next(index for index, row in enumerate(scenario.rows[:-1])
                     if row["safety_latch"] and scenario.rows[index + 1]["safety_latch"])
        self.engine.control({"action": "scenario", "scenario_id": scenario.id})
        self.engine.control({"action": "seek", "index": index})
        original = next(alarm for alarm in self.engine.snapshot()["active_alarms"]
                        if alarm["code"] == "safety_latch")
        self.engine.control({"action": "reset"})
        self.engine.control({"action": "seek", "index": index + 1})
        self.engine.control({"action": "ack", "alarm_id": original["id"]})
        current = next(alarm for alarm in self.engine.snapshot()["active_alarms"]
                       if alarm["code"] == "safety_latch")
        self.assertNotEqual(original["id"], current["id"])
        self.assertFalse(current["acknowledged"])

    def test_invalid_controls_do_not_enable_hardware_or_accept_paths(self):
        for payload in ({"action": "write_plc"}, {"action": "seek", "index": "STOP"},
                        {"action": "speed", "speed": float("nan")},
                        {"action": "speed", "speed": float("inf")},
                        {"action": "scenario", "scenario_id": "C:/Windows"}):
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    self.engine.control(payload)
        snapshot = self.engine.snapshot()
        self.assertFalse(snapshot["metadata"]["hardware_enabled"])
        self.assertEqual("D", snapshot["metadata"]["quality"])
        self.assertEqual("D_SYNTHETIC", snapshot["metadata"]["source_class"])


class HttpTests(EngineFixture):
    def setUp(self):
        super().setUp()
        self.server = scada.make_server(self.engine, port=0)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.assertFalse(self.thread.is_alive())
        super().tearDown()

    def request(self, method, path, payload=None, headers=None, raw=None):
        body = raw if raw is not None else (json.dumps(payload) if payload is not None else None)
        request_headers = dict(headers or {})
        if body is not None:
            request_headers.setdefault("Content-Type", "application/json")
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        try:
            connection.request(method, path, body=body, headers=request_headers)
            response = connection.getresponse()
            raw_body = response.read()
            result_headers = dict(response.getheaders())
            try:
                parsed = json.loads(raw_body)
            except (json.JSONDecodeError, UnicodeDecodeError):
                parsed = raw_body.decode("utf-8", "replace")
            return response.status, parsed, result_headers
        finally:
            connection.close()

    def test_all_read_apis_respond_with_synthetic_metadata(self):
        for path in ("/api/health", "/api/status", "/api/scenarios", "/api/snapshot",
                     "/api/history?limit=4", "/api/historian?limit=4", "/api/alarms?limit=4"):
            with self.subTest(path=path):
                status, body, headers = self.request("GET", path)
                self.assertEqual(200, status)
                self.assertIn("D_SYNTHETIC", json.dumps(body))
                self.assertNotIn("Access-Control-Allow-Origin", headers)

    def test_static_hmi_assets_are_deliverable_with_local_content_policy(self):
        for path, mime in (("/", "text/html"), ("/styles.css", "text/css"),
                           ("/app.js", "text/javascript")):
            with self.subTest(path=path):
                status, body, headers = self.request("GET", path)
                self.assertEqual(200, status)
                self.assertTrue(headers["Content-Type"].startswith(mime))
                self.assertIsInstance(body, str)
                self.assertTrue(body.strip())
                policy = headers.get("Content-Security-Policy", "")
                for directive in ("default-src 'self'", "script-src 'self'", "connect-src 'self'"):
                    self.assertIn(directive, policy)
                self.assertNotIn("http:", policy)
                self.assertNotIn("https:", policy)
                self.assertNotIn("'unsafe-inline'", policy)
                self.assertNotIn("'unsafe-eval'", policy)
                self.assertNotIn(str(WORKSPACE).casefold(), body.casefold())
                self.assertNotIn(WORKSPACE.as_posix().casefold(), body.casefold())
                self.assertNotIn("file://", body.casefold())
                if path == "/":
                    self.assertIn("D_SYNTHETIC", body)
                    self.assertIn("LOCAL SIMULATION ONLY", body)
                    self.assertIn('src="/app.js"', body)
                    self.assertIn('href="/styles.css"', body)

    def test_control_denies_missing_wrong_token_and_foreign_origin(self):
        for headers in ({}, {"X-SCADA-Token": "invalid"},
                        {"X-SCADA-Token": self.engine.token, "Origin": "https://evil.example"}):
            with self.subTest(headers=tuple(headers.keys())):
                status, _, _ = self.request("POST", "/api/control", {"action": "play"}, headers)
                self.assertEqual(403, status)
        status, _, _ = self.request("POST", "/api/control", {"action": "play"},
                                    {"X-SCADA-Token": self.engine.token,
                                     "Origin": f"http://127.0.0.1:{self.port}"})
        self.assertEqual(200, status)

    def test_control_rejects_invalid_commands_and_malformed_json(self):
        token = {"X-SCADA-Token": self.engine.token}
        for payload in ({"action": "write_plc", "value": 1}, {"action": "scenario", "scenario_id": "../../etc"},
                        {"action": "seek", "index": "../../STOP"}):
            with self.subTest(payload=payload):
                status, _, _ = self.request("POST", "/api/control", payload, token)
                self.assertEqual(400, status)
        status, _, _ = self.request("POST", "/api/control", headers=token, raw="{broken")
        self.assertEqual(400, status)

    def test_invalid_numeric_and_nested_json_return_client_error(self):
        token = {"X-SCADA-Token": self.engine.token}
        for raw, expected_status in (('{"action":"speed","speed":' + '9' * 400 + '}', 200),
                                     ('[' * 1100 + '0' + ']' * 1100, 400)):
            with self.subTest(body_kind="numeric" if "speed" in raw else "nested"):
                status, _, _ = self.request("POST", "/api/control", headers=token, raw=raw)
                self.assertEqual(expected_status, status)

    def test_duplicate_listener_cannot_bind_owned_port(self):
        with self.assertRaises(OSError):
            scada.make_server(self.engine, port=self.port)

    def test_invalid_host_and_repeated_query_arguments_are_denied(self):
        status, _, _ = self.request("GET", "/api/health", headers={"Host": "evil.example"})
        self.assertEqual(403, status)
        for path in ("/api/history?limit=1&limit=2", "/api/history?scenario=../../STOP", "/api/alarms?limit=NaN"):
            with self.subTest(path=path):
                status, _, _ = self.request("GET", path)
                self.assertEqual(400, status)

    def test_static_paths_cannot_escape_allowlisted_web_assets(self):
        for path in ("/../scada_server.py", "/%2e%2e/scada_server.py",
                     "/%2e%2e%5cscada_server.py", "/web/../../CODEX_TASK.md",
                     "/runtime/history.sqlite", "/STOP", "/.env"):
            with self.subTest(path=path):
                status, _, _ = self.request("GET", path)
                self.assertIn(status, {400, 403, 404})


if __name__ == "__main__":
    unittest.main()
