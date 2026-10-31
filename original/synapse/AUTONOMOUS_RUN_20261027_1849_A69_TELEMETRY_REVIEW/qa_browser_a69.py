"""True 320/390/1440 CSS viewport checks via isolated local Chrome DevTools."""
import json
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

import websocket

HERE = Path(__file__).resolve().parent
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
PAGE = HERE / "OUTPUT_SYNTHETIC" / "review.html"
WIDTHS = (320, 390, 1440)


def command(ws, serial, method, params=None):
    ws.send(json.dumps({"id": serial, "method": method, "params": params or {}}))
    while True:
        reply = json.loads(ws.recv())
        if reply.get("id") == serial:
            if "error" in reply:
                raise RuntimeError(f"CDP_{method}:{reply['error']}")
            return reply.get("result", {})


def run():
    if not CHROME.is_file() or not PAGE.is_file():
        raise RuntimeError("BROWSER_OR_REPORT_MISSING")
    with tempfile.TemporaryDirectory(prefix="a69-cdp-", dir=HERE) as td:
        profile = Path(td) / "profile"
        args = [str(CHROME), "--headless=new", "--disable-gpu", "--no-first-run",
                "--no-default-browser-check", "--no-sandbox",
                "--remote-debugging-port=0", "--user-data-dir=" + str(profile),
                "about:blank"]
        process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            active = profile / "DevToolsActivePort"
            for _ in range(100):
                if active.is_file():
                    break
                if process.poll() is not None:
                    raise RuntimeError("CHROME_EXITED_BEFORE_CDP")
                time.sleep(0.1)
            if not active.is_file():
                raise RuntimeError("CDP_PORT_NOT_READY")
            port = int(active.read_text(encoding="utf-8").splitlines()[0])
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=5) as response:
                tabs = json.load(response)
            pages = [tab for tab in tabs if tab.get("type") == "page"]
            if not pages:
                raise RuntimeError("CDP_NO_PAGE")
            ws = websocket.create_connection(pages[0]["webSocketDebuggerUrl"],
                                             timeout=8, suppress_origin=True)
            try:
                command(ws, 1, "Page.enable")
                results = {}
                serial = 2
                for width in WIDTHS:
                    command(ws, serial, "Emulation.setDeviceMetricsOverride", {
                        "width": width, "height": 844, "deviceScaleFactor": 1,
                        "mobile": width < 500})
                    serial += 1
                    command(ws, serial, "Page.navigate", {"url": PAGE.as_uri()})
                    serial += 1
                    expression = """(() => ({
                        ready:document.readyState, innerWidth:window.innerWidth,
                        scrollWidth:document.documentElement.scrollWidth,
                        bodyWidth:document.body.scrollWidth,
                        svg:document.querySelectorAll('svg').length,
                        series:document.querySelectorAll('polyline').length,
                        banner:document.querySelector('.banner')?.textContent.trim()
                    }))()"""
                    data = None
                    for _ in range(30):
                        reply = command(ws, serial, "Runtime.evaluate",
                                        {"expression": expression, "returnByValue": True})
                        serial += 1
                        data = reply.get("result", {}).get("value", {})
                        if data.get("ready") == "complete" and data.get("banner"):
                            break
                        time.sleep(0.1)
                    if not data or data.get("ready") != "complete":
                        raise RuntimeError(f"CDP_DOCUMENT_NOT_READY_{width}")
                    if data["innerWidth"] != width:
                        raise AssertionError(f"VIEWPORT_NOT_APPLIED_{width}:{data}")
                    if data["scrollWidth"] > width or data["bodyWidth"] > width:
                        raise AssertionError(f"OVERFLOW_{width}:{data}")
                    if data["svg"] != 2 or data["series"] != 4 or "SYNTETICKÉ" not in data["banner"]:
                        raise AssertionError(f"INVALID_DOM_{width}:{data}")
                    results[str(width)] = data
            finally:
                ws.close()
        finally:
            process.terminate()
            try:
                process.wait(timeout=6)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
    return {"status": "PASS", "browser": "Chrome CDP isolated, actual CSS viewport",
            "viewport_results": results, "physical_release": False}


if __name__ == "__main__":
    result = run()
    (HERE / "BROWSER_QA_A69.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=True))
