"""Optional, explicitly launched, read-only D_SYNTHETIC MQTT exporter.

The native SCADA has no MQTT dependency. Install paho-mqtt separately to use this
adapter. No subscriptions, command topics, PLC writes, or external hosts exist.
"""
from __future__ import annotations

import argparse
import json
import logging
from logging.handlers import RotatingFileHandler
import math
import os
from pathlib import Path
import signal
import threading
import time
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, build_opener

ROOT = Path(__file__).resolve().parent
LOOPBACK = {"127.0.0.1", "localhost", "::1"}
QUALITY = {"source_class": "D_SYNTHETIC", "quality": "D",
           "mode": "LOCAL_SIMULATION_ONLY", "hardware_enabled": False}
STOP_EVENT = threading.Event()


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("API redirects are forbidden")


def local_url(value: str) -> str:
    parts = urlsplit(value)
    if (parts.scheme != "http" or parts.hostname not in LOOPBACK
            or parts.username or parts.password or parts.query or parts.fragment
            or parts.path not in ("", "/")):
        raise ValueError("SCADA_URL must be a loopback HTTP root URL")
    if not 1 <= (parts.port or 80) <= 65535:
        raise ValueError("Invalid local API port")
    return value.rstrip("/")


def mqtt_config() -> tuple[str, int, str, str]:
    host = os.getenv("SCADA_MQTT_HOST", "127.0.0.1")
    if host not in LOOPBACK:
        raise ValueError("MQTT host must be loopback")
    port = int(os.getenv("SCADA_MQTT_PORT", "18883"))
    if not 1 <= port <= 65535:
        raise ValueError("Invalid MQTT port")
    username = os.getenv("SCADA_MQTT_USERNAME", "")
    password = os.getenv("SCADA_MQTT_PASSWORD", "")
    if not username or not password:
        raise ValueError("Set SCADA_MQTT_USERNAME and SCADA_MQTT_PASSWORD")
    return host, port, username, password


def stopped() -> bool:
    return STOP_EVENT.is_set() or (ROOT / "STOP").exists()


def wait(seconds: float) -> None:
    deadline = time.monotonic() + seconds
    while not stopped() and time.monotonic() < deadline:
        STOP_EVENT.wait(min(0.1, max(0, deadline - time.monotonic())))


def fetch_snapshot(opener, url: str) -> dict:
    with opener.open(url + "/api/snapshot", timeout=3) as response:
        body = response.read(524289)
    if len(body) > 524288:
        raise ValueError("Snapshot too large")
    snapshot = json.loads(body)
    metadata = snapshot.get("metadata", {})
    if (metadata.get("source_class") != "D_SYNTHETIC"
            or metadata.get("quality") != "D"
            or metadata.get("mode") != "LOCAL_SIMULATION_ONLY"
            or metadata.get("hardware_enabled") is not False):
        raise ValueError("Exporter accepts only explicit synthetic D data")
    # Whitelist sections: /api/status carries a local CSRF token and is never read.
    source_status = snapshot.get("status", {})
    safe_status = {key: source_status[key] for key in
                   ("scenario_id", "scenario_name", "index", "playing", "stopped", "speed",
                    "simulation_time_h", "updated_at", "server_time", "sample_count", "at_end")
                   if key in source_status}
    return {"metadata": dict(QUALITY), "status": safe_status,
            "values": snapshot.get("values", {}),
            "derived": snapshot.get("derived", {}),
            "sample_timestamp_s": snapshot.get("sample_timestamp_s"),
            "source_file": snapshot.get("source_file"),
            "source_sha256": snapshot.get("source_sha256"),
            "exported_at_unix": time.time()}


def payload(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, allow_nan=False,
                      separators=(",", ":"))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval", type=float, default=1.0,
                        help="Export interval, 0.25..60 seconds (default 1)")
    args = parser.parse_args(argv)
    if not math.isfinite(args.interval) or not 0.25 <= args.interval <= 60:
        parser.error("--interval must be within 0.25..60")
    if stopped():
        print("STOP is present: MQTT replay export is disabled.")
        return 0
    try:
        url = local_url(os.getenv("SCADA_URL", "http://127.0.0.1:8091"))
        host, port, username, password = mqtt_config()
    except (ValueError, TypeError):
        parser.error("Use loopback addresses, valid ports, and MQTT credential environment variables")
    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        print("Optional dependency missing: install paho-mqtt to use this exporter.")
        return 2
    runtime = ROOT / "runtime"
    runtime.mkdir(exist_ok=True)
    logger = logging.getLogger("scada_mqtt")
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(runtime / "mqtt_bridge.log", maxBytes=524288,
                                  backupCount=2, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.addHandler(logging.StreamHandler())
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: STOP_EVENT.set())
    opener = build_opener(ProxyHandler({}), NoRedirect())
    kwargs = {"client_id": "dchr-v09-local-synthetic-export"}
    if hasattr(mqtt, "CallbackAPIVersion"):
        kwargs["callback_api_version"] = mqtt.CallbackAPIVersion.VERSION2
    client = mqtt.Client(**kwargs)
    client.username_pw_set(username, password)
    client.max_queued_messages_set(512)
    client.max_inflight_messages_set(20)
    base = "dchr/v09/sim"
    client.will_set(base + "/bridge_state", payload({**QUALITY, "state": "offline",
                    "reason": "bridge connection lost; retained telemetry can be stale"}),
                    qos=1, retain=True)
    connected = threading.Event()

    def on_connect(_client, _userdata, _flags, reason_code, *_properties):
        if reason_code == 0:
            connected.set()

    def on_disconnect(*_args):
        connected.clear()

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.reconnect_delay_set(min_delay=1, max_delay=10)
    loop_started = False
    try:
        logger.info("Read-only MQTT exporter: D_SYNTHETIC / hardware disabled")
        while not stopped():
            try:
                if not loop_started:
                    client.connect(host, port, keepalive=15)
                    client.loop_start()
                    loop_started = True
                if not connected.is_set():
                    wait(1)
                    continue
                snapshot = fetch_snapshot(opener, url)
                status = snapshot["status"]
                context = {**QUALITY, "scenario_id": status.get("scenario_id"),
                           "index": status.get("index"),
                           "cas_h": snapshot["values"].get("cas_h"),
                           "exported_at_unix": snapshot["exported_at_unix"]}
                client.publish(base + "/snapshot", payload(snapshot), qos=1, retain=True)
                for name, value in snapshot["values"].items():
                    if isinstance(value, (int, float)) and math.isfinite(value):
                        # Tag names originate from fixed CSV headers, never paths.
                        if name.replace("_", "").isalnum():
                            client.publish(base + "/tag/" + name,
                                           payload({**context, "value": value}),
                                           qos=1, retain=True)
                client.publish(base + "/bridge_state", payload({**QUALITY,
                               "state": "online", "playing": status.get("playing", False),
                               "exported_at_unix": time.time()}), qos=1, retain=True)
                wait(args.interval)
            except (URLError, OSError, ValueError, TypeError, KeyError) as exc:
                # Exception text might include connection details; log only its type.
                logger.warning("Local export unavailable (%s); retry in 3 s", type(exc).__name__)
                wait(3)
    finally:
        if loop_started:
            try:
                info = client.publish(base + "/bridge_state", payload({**QUALITY,
                                      "state": "offline", "reason": "STOP or local exit",
                                      "exported_at_unix": time.time()}), qos=1, retain=True)
                info.wait_for_publish(timeout=2)
            except (RuntimeError, ValueError):
                pass
            client.disconnect()
            client.loop_stop()
        logger.info("MQTT exporter stopped; no command subscriptions were created")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
