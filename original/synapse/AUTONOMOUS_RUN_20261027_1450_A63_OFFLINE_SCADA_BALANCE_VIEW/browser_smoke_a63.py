"""Isolated headless browser functional smoke; no shared GUI/profile."""
import json
from pathlib import Path
import re
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parent
CHROME=Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
assert CHROME.is_file()
target=(ROOT/"OUTPUT"/"dashboard.html").resolve().as_uri()
with tempfile.TemporaryDirectory(prefix="a63-chrome-",dir=ROOT) as profile:
    args=[str(CHROME),"--headless=new","--disable-gpu","--disable-extensions",
          "--disable-background-networking","--disable-sync","--no-first-run",
          "--no-default-browser-check","--no-proxy-server",
          "--disable-features=MediaRouter","--virtual-time-budget=2500",
          "--user-data-dir="+profile,"--dump-dom",target]
    run=subprocess.run(args,capture_output=True,text=True,encoding="utf-8",
                       errors="replace",timeout=25)
    if run.returncode:
        raise RuntimeError("HEADLESS_CHROME_FAILED:"+str(run.returncode)+run.stderr[-1200:])
    dom=run.stdout
    cards=len(re.findall(r'class="card"',dom))
    paths=len(re.findall(r'<polyline\b',dom))
    if cards!=6 or paths!=7 or "source_kind=derived_simulation" not in dom:
        raise AssertionError("DOM_RENDER_FAILED:"+str((cards,paths)))
    result={"status":"PASS","browser":"isolated headless Chrome","cards_rendered":cards,
            "svg_polylines":paths,"source_kind":"derived_simulation",
            "physical_release":False,"shared_browser_untouched":True}
    (ROOT/"BROWSER_QA_A63.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result))
