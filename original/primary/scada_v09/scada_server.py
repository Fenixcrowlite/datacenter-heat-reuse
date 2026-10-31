"""Local D_SYNTHETIC CSV replay. No device drivers or hardware command paths."""
from __future__ import annotations

import argparse
import csv
import errno
import hashlib
import ipaddress
import json
import logging
from logging.handlers import RotatingFileHandler
import math
import os
from pathlib import Path
import secrets
import signal
import socket
import sqlite3
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlsplit

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = BASE_DIR.parent / "results" / "pool_measurement_v08"
METADATA = {
    "source_class": "D_SYNTHETIC", "quality": "D",
    "mode": "LOCAL_SIMULATION_ONLY", "hardware_enabled": False,
    "sample_period_s": 900, "interpolation": False,
    "it_temperature_note": "T_IT_model_C: модельный индикатор риска, не температура CPU",
    "tes_soc_note": "Ёмкость TES не документирована; SOC не вычисляется",
    "alarm_rules": "Флаги CSV > 0; Q_unhandled_W > 1 W; |Q_leak_W| > 1 W (порог отображения)",
}
SCENARIO_NAMES = {
    "zdravy": "Штатный режим · Zdravý",
    "primarny_ventil_zaseknuty": "Заклинивание основного клапана",
    "oba_ventily_zaseknute": "Оба клапана заклинены",
    "hlavny_REJECT_off_zalozny_ok": "REJECT A отключён, резерв доступен",
    "oba_REJECT_off_bez_shedding": "Оба REJECT отключены, без shedding",
    "oba_REJECT_off_so_shedding": "Оба REJECT отключены, со shedding",
    "spolocny_bias_senzorov": "Общее смещение датчиков · Bias",
    "kombinovana_havaria_so_shedding": "Комбинированная авария со shedding",
}
REQUIRED_COLUMNS = {
    "cas_h", "T_pool_C", "Q_DC_eff_W", "Q_pool_phys_W", "Q_HP_source_W",
    "P_HP_W", "COP", "Q_reject_main_W", "Q_reject_backup_W", "Q_unhandled_W",
    "Q_leak_W", "T_IT_model_C", "safety_latch", "E_TES_J", "Q_DH_W",
    "stateflow_mode", "sensor1_C", "sensor2_C", "IT_model_alarm",
}


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def envelope(**values):
    return {"metadata": dict(METADATA), **values}


@dataclass
class Scenario:
    id: str
    name: str
    source_file: str
    sha256: str
    rows: list[dict[str, float]]
    summary: dict

    def describe(self):
        return {
            "id": self.id, "name": self.name, "source_file": self.source_file,
            "sha256": self.sha256, "source_class": "D_SYNTHETIC", "quality": "D",
            "rows": len(self.rows), "first_time_h": self.rows[0]["cas_h"],
            "last_time_h": self.rows[-1]["cas_h"], "coverage_hours": len(self.rows) * .25,
            "sample_period_s": 900, "summary": self.summary,
        }


class Dataset:
    """Read only the eight native CSVs; reject incomplete/nonfinite data."""

    def __init__(self, data_dir=DEFAULT_DATA_DIR):
        self.scenarios = {}
        data_dir = Path(data_dir)
        self.qa = json.loads((data_dir / "QA_NEZAVISLA_V08_SK.json").read_text(encoding="utf-8-sig"))
        if self.qa.get("status") != "PASS" or self.qa.get("source_class") != "D_SYNTHETIC_REPLAY":
            raise ValueError("Unexpected upstream QA classification/status")
        for scenario_id in SCENARIO_NAMES:
            path = data_dir / f"sim_v08_{scenario_id}_SK.csv"
            raw = path.read_bytes()
            with path.open(encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                if not REQUIRED_COLUMNS.issubset(reader.fieldnames or ()):
                    raise ValueError(f"Missing native columns in {path.name}")
                rows = []
                for index, row in enumerate(reader):
                    if None in row or any(v is None for v in row.values()):
                        raise ValueError(f"Malformed CSV row in {path.name}")
                    numeric = {k: float(v) for k, v in row.items()}
                    if not all(math.isfinite(v) for v in numeric.values()):
                        raise ValueError(f"Nonfinite CSV value in {path.name}")
                    if abs(numeric["cas_h"] - index * .25) > 1e-9:
                        raise ValueError(f"Unexpected sample interval in {path.name}")
                    rows.append(numeric)
            if len(rows) != 672:
                raise ValueError(f"Expected 672 native rows in {path.name}, got {len(rows)}")
            summary = {
                "pool_min_C": min(r["T_pool_C"] for r in rows),
                "pool_max_C": max(r["T_pool_C"] for r in rows),
                "it_risk_max_C": max(r["T_IT_model_C"] for r in rows),
                # Native step powers integrated as 900 s rectangles, not interpolation.
                "pool_energy_kwh": sum(r["Q_pool_phys_W"] for r in rows) * .25 / 1000,
                "unhandled_energy_kwh": sum(r["Q_unhandled_W"] for r in rows) * .25 / 1000,
                "reject_energy_kwh": sum(r["Q_reject_main_W"] + r["Q_reject_backup_W"] for r in rows) * .25 / 1000,
                "integration": "sum(native W × 900 s) / 3600000; 168 h",
            }
            self.scenarios[scenario_id] = Scenario(scenario_id, SCENARIO_NAMES[scenario_id], path.name,
                                                   hashlib.sha256(raw).hexdigest(), rows, summary)
        qa_cases = {case["name"]: case for case in self.qa.get("cases", [])}
        if set(qa_cases) != set(self.scenarios) or any(
            qa_cases[s].get("rows") != 672 or qa_cases[s].get("source_class") != "D_SYNTHETIC"
            for s in self.scenarios
        ):
            raise ValueError("Upstream QA cases do not match native CSVs")


def evaluate_alarms(row):
    """Indications from source flags, with only documented display tolerances."""
    result = []
    flags = {
        "E_STOP": ("CRITICAL", "E_STOP в исходной симуляции"),
        "IT_model_alarm": ("CRITICAL", "Модельный риск IT; не фактическая температура CPU"),
        "safety_latch": ("CRITICAL", "Защёлка безопасности · Bezpečnostná západka"),
        "emergency_flag": ("CRITICAL", "Аварийный флаг исходной модели"),
        "invalid_sensor": ("CRITICAL", "Недопустимое значение датчика в модели"),
        "flow_fault": ("WARNING", "Отказ расхода · Porucha prietoku"),
        "sensor_mismatch": ("WARNING", "Расхождение датчиков · Nesúlad snímačov"),
        "sensor_hot": ("WARNING", "Перегрев по флагу модельного датчика"),
        "primary_valve_fault": ("WARNING", "Отказ основного клапана"),
        "secondary_valve_fault": ("WARNING", "Отказ резервного клапана"),
        "leak_at_zero_cmd": ("WARNING", "Утечка при нулевой команде модели"),
    }
    for code, (severity, message) in flags.items():
        if row.get(code, 0) > 0:
            result.append({"code": code, "severity": severity, "message": message})
    if row.get("Q_unhandled_W", 0) > 1:
        result.append({"code": "Q_unhandled_W", "severity": "CRITICAL", "message": "Неотведённое тепло > 1 W (порог отображения)"})
    if abs(row.get("Q_leak_W", 0)) > 1:
        result.append({"code": "Q_leak_W", "severity": "WARNING", "message": "Тепловая утечка > 1 W (порог отображения)"})
    return result


class ReplayEngine:
    def __init__(self, dataset, runtime_dir=BASE_DIR / "runtime", stop_path=None, start_worker=False):
        self.dataset = dataset
        self.runtime_dir = Path(runtime_dir).resolve()
        if not self.runtime_dir.is_relative_to(BASE_DIR):
            raise ValueError("Runtime must remain within scada_v09")
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.stop_path = Path(stop_path) if stop_path is not None else BASE_DIR / "STOP"
        self.lock = threading.RLock()
        self.token = secrets.token_urlsafe(32)
        self.instance_id = secrets.token_hex(16)
        self.scenario_id = "zdravy"
        self.index = 0
        self.speed = 1.0
        self.playing = False
        self.stopped = False
        self.updated_at = utc_now()
        self._active = {}
        self._closed = threading.Event()
        self._wake = threading.Event()
        self.worker = None
        self.db = sqlite3.connect(self.runtime_dir / "history.sqlite", check_same_thread=False)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS samples (
                source_hash TEXT NOT NULL, scenario_id TEXT NOT NULL, sample_index INTEGER NOT NULL,
                sample_timestamp_s REAL NOT NULL, first_seen TEXT NOT NULL, last_seen TEXT NOT NULL,
                source_class TEXT NOT NULL DEFAULT 'D_SYNTHETIC', quality TEXT NOT NULL DEFAULT 'D',
                values_json TEXT NOT NULL, PRIMARY KEY(source_hash,scenario_id,sample_index));
            CREATE TABLE IF NOT EXISTS alarm_events (
                id INTEGER PRIMARY KEY, source_hash TEXT NOT NULL, scenario_id TEXT NOT NULL,
                sample_index INTEGER NOT NULL, time_h REAL NOT NULL, created_at TEXT NOT NULL,
                code TEXT NOT NULL, severity TEXT NOT NULL, message TEXT NOT NULL, state TEXT NOT NULL,
                acknowledged INTEGER NOT NULL DEFAULT 0, source_class TEXT NOT NULL DEFAULT 'D_SYNTHETIC',
                quality TEXT NOT NULL DEFAULT 'D', UNIQUE(source_hash,scenario_id,sample_index,code,state));
        """)
        hashes = tuple(s.sha256 for s in dataset.scenarios.values())
        placeholders = ",".join("?" for _ in hashes)
        for table in ("samples", "alarm_events"):
            self.db.execute(f"DELETE FROM {table} WHERE source_hash NOT IN ({placeholders})", hashes)
        self.db.commit()
        with self.lock:
            self._check_stop()
            self._record()
        if start_worker:
            self.start_worker()

    @property
    def scenario(self):
        return self.dataset.scenarios[self.scenario_id]

    def _check_stop(self):
        stopped = self.stop_path.exists()
        changed = stopped != self.stopped
        self.stopped = stopped
        if stopped:
            self.playing = False
        if changed:
            self.updated_at = utc_now()
            self._record()

    def _record(self):
        row = self.scenario.rows[self.index]
        now = utc_now()
        self.db.execute("""INSERT INTO samples
            (source_hash,scenario_id,sample_index,sample_timestamp_s,first_seen,last_seen,values_json)
            VALUES(?,?,?,?,?,?,?) ON CONFLICT(source_hash,scenario_id,sample_index)
            DO UPDATE SET last_seen=excluded.last_seen""",
            (self.scenario.sha256, self.scenario_id, self.index, row["cas_h"] * 3600, now, now,
             json.dumps(row, separators=(",", ":"), allow_nan=False)))
        active = {a["code"]: a for a in evaluate_alarms(row)}
        if self.stopped:
            active["STOP"] = {"code": "STOP", "severity": "CRITICAL", "message": "STOP сохранён: воспроизведение заблокировано"}
        for code in active.keys() - self._active.keys():
            active[code]["id"] = self._event(active[code], "ACTIVE")
        for code in active.keys() & self._active.keys():
            active[code]["id"] = self._active[code].get("id")
        for code in self._active.keys() - active.keys():
            self._event(self._active[code], "CLEARED")
        self._active = active
        self.db.execute("DELETE FROM alarm_events WHERE id NOT IN (SELECT id FROM alarm_events ORDER BY id DESC LIMIT 5000)")
        self.db.commit()

    def _event(self, alarm, state):
        self.db.execute("""INSERT OR IGNORE INTO alarm_events
            (source_hash,scenario_id,sample_index,time_h,created_at,code,severity,message,state)
            VALUES(?,?,?,?,?,?,?,?,?)""", (self.scenario.sha256, self.scenario_id, self.index,
                self.scenario.rows[self.index]["cas_h"], utc_now(), alarm["code"], alarm["severity"], alarm["message"], state))
        return self.db.execute("""SELECT id FROM alarm_events WHERE source_hash=? AND scenario_id=?
            AND sample_index=? AND code=? AND state=?""", (self.scenario.sha256, self.scenario_id,
                self.index, alarm["code"], state)).fetchone()[0]

    def _status(self):
        return {
            "instance_id": self.instance_id, "pid": os.getpid(),
            "playing": self.playing, "stopped": self.stopped, "speed": self.speed,
            "index": self.index, "sample_count": len(self.scenario.rows),
            "scenario_id": self.scenario_id, "scenario_name": self.scenario.name,
            "simulation_time_h": self.scenario.rows[self.index]["cas_h"],
            "updated_at": self.updated_at, "server_time": utc_now(),
            "at_end": self.index == len(self.scenario.rows) - 1,
        }

    def status(self):
        with self.lock:
            self._check_stop()
            return envelope(**self._status(), csrf_token=self.token)

    def snapshot(self):
        with self.lock:
            self._check_stop()
            row = dict(self.scenario.rows[self.index])
            return envelope(status=self._status(), values=row,
                sample_timestamp_s=row["cas_h"] * 3600, observed_at=utc_now(),
                source_file=self.scenario.source_file, source_sha256=self.scenario.sha256,
                derived={"tes_energy_kwh": row["E_TES_J"] / 3600000,
                         "tes_soc_percent": None, "tes_soc_note": METADATA["tes_soc_note"]},
                active_alarms=self._active_alarms())

    def _active_alarms(self):
        result = []
        for alarm in self._active.values():
            event = self.db.execute("SELECT id,acknowledged FROM alarm_events WHERE id=?",
                                    (alarm.get("id"),)).fetchone()
            result.append({**alarm, "id": event[0] if event else None,
                           "acknowledged": bool(event and event[1]), "quality": "D", "source_class": "D_SYNTHETIC"})
        return result

    def scenarios_payload(self):
        return envelope(scenarios=[s.describe() for s in self.dataset.scenarios.values()], qa=self.dataset.qa)

    @staticmethod
    def _limit(value, maximum):
        if isinstance(value, bool):
            raise ValueError("Invalid limit")
        try:
            return max(1, min(maximum, int(value)))
        except (ValueError, TypeError, OverflowError):
            raise ValueError("Invalid limit") from None

    def history(self, limit=672, scenario_id=None, scope="played"):
        with self.lock:
            self._check_stop()
            scenario_id = scenario_id or self.scenario_id
            if scenario_id not in self.dataset.scenarios or scope not in ("played", "full"):
                raise ValueError("Unknown scenario or history scope")
            scenario = self.dataset.scenarios[scenario_id]
            end = len(scenario.rows) if scope == "full" else (self.index + 1 if scenario_id == self.scenario_id else 0)
            start = max(0, end - self._limit(limit, 672))
            return envelope(scenario_id=scenario_id, data_kind="native_source_samples", scope=scope,
                rows=[{"sample_index": i, "sample_timestamp_s": scenario.rows[i]["cas_h"] * 3600,
                       "values": dict(scenario.rows[i]), "quality": "D", "source_class": "D_SYNTHETIC"}
                      for i in range(start, end)])

    def historian(self, limit=100, scenario_id=None):
        with self.lock:
            if scenario_id is not None and scenario_id not in self.dataset.scenarios:
                raise ValueError("Unknown scenario")
            condition = " WHERE scenario_id=?" if scenario_id is not None else ""
            args = ([scenario_id] if scenario_id is not None else []) + [self._limit(limit, 5376)]
            cursor = self.db.execute("SELECT scenario_id,sample_index,sample_timestamp_s,first_seen,last_seen,values_json "
                                     "FROM samples" + condition + " ORDER BY last_seen DESC LIMIT ?", args)
            rows = [{"scenario_id": s, "sample_index": i, "sample_timestamp_s": t,
                     "first_seen": first, "last_seen": last, "values": json.loads(v),
                     "quality": "D", "source_class": "D_SYNTHETIC"} for s, i, t, first, last, v in cursor]
            return envelope(data_kind="persisted_visited_samples", rows=rows)

    def alarms(self, limit=60):
        with self.lock:
            self._check_stop()
            cursor = self.db.execute("SELECT * FROM alarm_events ORDER BY id DESC LIMIT ?", (self._limit(limit, 5000),))
            names = [c[0] for c in cursor.description]
            events = [dict(zip(names, row)) for row in cursor]
            for event in events:
                event["acknowledged"] = bool(event["acknowledged"])
            return envelope(events=events, active_alarms=self._active_alarms())

    def control(self, payload):
        if not isinstance(payload, dict) or not isinstance(payload.get("action"), str):
            raise ValueError("Expected a command object")
        allowed = {"play": set(), "pause": set(), "reset": set(), "seek": {"index"},
                   "scenario": {"scenario_id"}, "speed": {"speed"}, "ack": {"alarm_id"}}
        action = payload["action"]
        if action not in allowed or set(payload) != allowed[action] | {"action"}:
            raise ValueError("Unknown command or arguments")
        with self.lock:
            self._check_stop()
            if self.stopped and action in {"play", "reset", "seek", "scenario"}:
                raise RuntimeError("STOP persists; replay remains blocked")
            if action == "play":
                self.playing = self.index < len(self.scenario.rows) - 1
            elif action == "pause":
                self.playing = False
            elif action == "reset":
                self.playing = False
                self.index = 0
            elif action == "scenario":
                scenario_id = payload["scenario_id"]
                if not isinstance(scenario_id, str) or scenario_id not in self.dataset.scenarios:
                    raise ValueError("Unknown scenario")
                # Clear previous scenario indications before entering a new scenario.
                for alarm in self._active.values():
                    self._event(alarm, "CLEARED")
                self._active = {}
                self.scenario_id = scenario_id
                self.index = 0
                self.playing = False
            elif action == "seek":
                value = payload["index"]
                if type(value) is not int:
                    raise ValueError("index must be an integer")
                self.index = max(0, min(len(self.scenario.rows) - 1, value))
                self.playing = False
            elif action == "speed":
                value = payload["speed"]
                if type(value) not in (int, float) or (isinstance(value, float) and not math.isfinite(value)):
                    raise ValueError("speed must be finite")
                self.speed = float(max(.5, min(16., value)))
            elif action == "ack":
                alarm_id = payload["alarm_id"]
                if type(alarm_id) is not int or not 1 <= alarm_id <= 9223372036854775807:
                    raise ValueError("Invalid alarm_id")
                event = self.db.execute("SELECT id FROM alarm_events WHERE id=? AND state='ACTIVE'", (alarm_id,)).fetchone()
                if event is None:
                    raise ValueError("Unknown active alarm event")
                self.db.execute("UPDATE alarm_events SET acknowledged=1 WHERE id=?", (alarm_id,))
                self.db.execute("""INSERT OR IGNORE INTO alarm_events
                    (source_hash,scenario_id,sample_index,time_h,created_at,code,severity,message,state,acknowledged)
                    SELECT source_hash,scenario_id,sample_index,time_h,?,code,severity,message,'ACK',1
                    FROM alarm_events WHERE id=?""", (utc_now(), alarm_id))
            self.updated_at = utc_now()
            self._record()
            self._wake.set()
            return envelope(status=self._status())

    def tick(self):
        with self.lock:
            self._check_stop()
            if self.playing and self.index < len(self.scenario.rows) - 1:
                self.index += 1
                self.updated_at = utc_now()
                if self.index == len(self.scenario.rows) - 1:
                    self.playing = False
                self._record()

    def start_worker(self):
        if self.worker is not None:
            return
        self.worker = threading.Thread(target=self._run, name="CSV-replay", daemon=True)
        self.worker.start()

    def _run(self):
        due = time.monotonic()
        try:
            while not self._closed.is_set():
                with self.lock:
                    self._check_stop()
                    now = time.monotonic()
                    if self.playing and now >= due:
                        self.tick()
                        due = now + 1 / self.speed
                    elif not self.playing:
                        due = now + 1 / self.speed
                    delay = min(.05, max(0., due - time.monotonic())) if self.playing else .05
                # STOP is inspected at least every 50 ms even at 0.5 step/s.
                if self._wake.wait(delay):
                    self._wake.clear()
                    due = time.monotonic() + 1 / self.speed
        except Exception:
            logging.exception("Replay worker failed; playback paused")
            with self.lock:
                self.playing = False
                self._active["WORKER"] = {"code": "WORKER", "severity": "CRITICAL", "message": "Ошибка replay worker: требуется перезапуск"}

    def close(self):
        self._closed.set()
        self._wake.set()
        if self.worker is not None:
            self.worker.join(timeout=3)
        with self.lock:
            self.db.close()


class LocalServer(ThreadingHTTPServer):
    daemon_threads = False
    allow_reuse_address = False
    block_on_close = True

    def server_bind(self):
        # On Windows SO_REUSEADDR can steal an existing listener; explicitly exclude it.
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()

    def handle_error(self, request, client_address):
        logging.exception("Local HTTP request failed")


def make_server(engine, port=0):
    class Handler(BaseHTTPRequestHandler):
        server_version = "DCHR-Local-Simulation/09"
        protocol_version = "HTTP/1.0"

        def setup(self):
            super().setup()
            self.connection.settimeout(5)

        def log_message(self, format, *args):
            # Never log headers, tokens, query values or payloads.
            logging.info("HTTP %s %s", self.command, urlsplit(self.path).path[:120])

        def _send(self, status, body, content_type="application/json; charset=utf-8"):
            data = json.dumps(body, ensure_ascii=False, allow_nan=False).encode("utf-8") if isinstance(body, dict) else body
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
            self.end_headers()
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def _error(self, status, message):
            self._send(status, envelope(error=message))

        def send_error(self, code, message=None, explain=None):
            self._error(code, "Unsupported or invalid HTTP request")

        def _validated_path(self):
            if not ipaddress.ip_address(self.client_address[0]).is_loopback:
                raise PermissionError("Loopback only")
            port = self.server.server_port
            host = self.headers.get("Host", "")
            if host not in (f"127.0.0.1:{port}", f"localhost:{port}"):
                raise PermissionError("Invalid Host")
            origin = self.headers.get("Origin")
            if origin is not None and origin != f"http://{host}":
                raise PermissionError("Cross-origin requests denied")
            parsed = urlsplit(self.path)
            path = unquote(parsed.path, errors="strict")
            if parsed.scheme or parsed.netloc or any(c in path for c in ("\\", "\x00", "%")) or ".." in path or "//" in path:
                raise ValueError("Unsafe path")
            return path, parse_qs(parsed.query, keep_blank_values=True, max_num_fields=8)

        @staticmethod
        def _query(query, allowed):
            if set(query) - set(allowed) or any(len(v) != 1 for v in query.values()):
                raise ValueError("Invalid query parameters")
            return {k: v[0] for k, v in query.items()}

        def do_GET(self):
            try:
                path, query = self._validated_path()
                if path in ("/api/health", "/healthz", "/health"):
                    self._query(query, ())
                    status = engine.status()
                    result = envelope(ok=True, instance_id=engine.instance_id, pid=os.getpid(),
                                      stopped=status["stopped"], playing=status["playing"], server_time=utc_now())
                elif path == "/api/status":
                    self._query(query, ())
                    result = engine.status()
                elif path == "/api/snapshot":
                    self._query(query, ())
                    result = engine.snapshot()
                elif path == "/api/scenarios":
                    self._query(query, ())
                    result = engine.scenarios_payload()
                elif path in ("/api/history", "/api/historian"):
                    args = self._query(query, ("limit", "scenario", "scope") if path == "/api/history" else ("limit", "scenario"))
                    kwargs = {"limit": args.get("limit", 672 if path == "/api/history" else 100), "scenario_id": args.get("scenario")}
                    if path == "/api/history":
                        result = engine.history(**kwargs, scope=args.get("scope", "played"))
                    else:
                        result = engine.historian(**kwargs)
                elif path == "/api/alarms":
                    args = self._query(query, ("limit",))
                    result = engine.alarms(args.get("limit", 60))
                elif path in ("/", "/index.html", "/styles.css", "/app.js", "/i18n.js"):
                    params = self._query(query, ("lang",) if path in ("/", "/index.html") else ())
                    if params.get("lang", "ru") not in ("ru", "sk", "en"):
                        raise ValueError("Unsupported UI language")
                    name = {"/": "index.html", "/index.html": "index.html", "/styles.css": "styles.css", "/app.js": "app.js", "/i18n.js": "i18n.js"}[path]
                    mime = {"index.html": "text/html; charset=utf-8", "styles.css": "text/css; charset=utf-8", "app.js": "text/javascript; charset=utf-8", "i18n.js": "text/javascript; charset=utf-8"}[name]
                    self._send(200, (BASE_DIR / "web" / name).read_bytes(), mime)
                    return
                else:
                    self._error(404, "Unknown local endpoint")
                    return
                self._send(200, result)
            except PermissionError as exc:
                self._error(403, str(exc))
            except (ValueError, UnicodeError) as exc:
                self._error(400, str(exc))
            except Exception:
                logging.exception("GET failed")
                self._error(500, "Local server error")

        def do_POST(self):
            try:
                path, query = self._validated_path()
                if path != "/api/control":
                    self._error(404, "Unknown local endpoint")
                    return
                self._query(query, ())
                if not secrets.compare_digest(self.headers.get("X-SCADA-Token", ""), engine.token):
                    raise PermissionError("Invalid CSRF token")
                if self.headers.get_content_type() != "application/json" or self.headers.get("Transfer-Encoding"):
                    raise ValueError("Only bounded JSON bodies accepted")
                length = int(self.headers.get("Content-Length", "0"))
                if length < 1 or length > 4096:
                    raise ValueError("Body length must be 1..4096 bytes")
                payload = json.loads(self.rfile.read(length), parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite JSON")))
                if payload == {"action": "shutdown"}:
                    engine.control({"action": "pause"})
                    self._send(200, envelope(status=engine._status(), shutting_down=True))
                    threading.Thread(target=self.server.shutdown, name="SCADA-shutdown", daemon=True).start()
                    return
                self._send(200, engine.control(payload))
            except PermissionError as exc:
                self._error(403, str(exc))
            except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
                self._error(400, str(exc))
            except RuntimeError as exc:
                self._error(409, str(exc))
            except Exception:
                logging.exception("POST failed")
                self._error(500, "Local server error")

        def do_OPTIONS(self):
            self._error(405, "Method disabled; no cross-origin access")

        do_PUT = do_DELETE = do_PATCH = do_TRACE = do_OPTIONS

    return LocalServer(("127.0.0.1", port), Handler)


class InstanceLock:
    """OS-owned lock survives crashes safely; the lock file itself is not a PID authority."""
    def __init__(self, path):
        self.stream = open(path, "a+b")
        self.stream.seek(0)
        if not self.stream.read(1):
            self.stream.write(b"0")
            self.stream.flush()
        self.stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.stream.close()
            raise RuntimeError("Another SCADA v09 process owns runtime/server.lock") from None

    def close(self):
        self.stream.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description="DCHR v09 LOCAL D_SYNTHETIC simulation, no hardware control")
    parser.add_argument("--port", type=int, help="Explicit local port; disables automatic fallback")
    args = parser.parse_args(argv)
    if args.port is not None and not 1024 <= args.port <= 65535:
        parser.error("port must be 1024..65535")
    runtime = BASE_DIR / "runtime"
    runtime.mkdir(exist_ok=True)
    handlers = [RotatingFileHandler(runtime / "scada.log", maxBytes=512 * 1024, backupCount=3, encoding="utf-8")]
    # Hidden PowerShell starts redirect stderr: do not duplicate the polled request
    # log into an unbounded redirect file. The rotating log remains authoritative.
    if sys.stderr.isatty():
        handlers.append(logging.StreamHandler())
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=handlers)
    lock = engine = server = None
    identity = runtime / "server.json"
    try:
        lock = InstanceLock(runtime / "server.lock")
        engine = ReplayEngine(Dataset(), runtime)
        try:
            server = make_server(engine, args.port if args.port is not None else 8091)
        except OSError as exc:
            occupied = exc.errno == errno.EADDRINUSE or getattr(exc, "winerror", None) == 10048
            if args.port is not None or not occupied:
                raise
            logging.warning("Port 8091 occupied; binding local fallback 127.0.0.1:8092")
            server = make_server(engine, 8092)
        identity.write_text(json.dumps({"pid": os.getpid(), "port": server.server_port,
            "instance_id": engine.instance_id, "script": str(Path(__file__).resolve()),
            "source_class": "D_SYNTHETIC"}), encoding="utf-8")
        engine.start_worker()
        logging.info("LOCAL SIMULATION ONLY / D_SYNTHETIC at http://127.0.0.1:%s; STOP=%s; hardware disabled", server.server_port, engine.stopped)

        def shutdown_signal(signum, frame):
            threading.Thread(target=server.shutdown, daemon=True).start()

        signal.signal(signal.SIGINT, shutdown_signal)
        signal.signal(signal.SIGTERM, shutdown_signal)
        server.serve_forever(poll_interval=.1)
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        logging.error("SCADA startup refused: %s", exc)
        return 1
    finally:
        if server is not None:
            server.server_close()
        if engine is not None:
            engine.close()
            if identity.exists():
                try:
                    if json.loads(identity.read_text(encoding="utf-8")).get("instance_id") == engine.instance_id:
                        identity.unlink()
                except (OSError, ValueError):
                    logging.warning("Could not clean server identity")
        if lock is not None:
            lock.close()
        logging.info("SCADA stopped; STOP file preserved")


if __name__ == "__main__":
    raise SystemExit(main())
