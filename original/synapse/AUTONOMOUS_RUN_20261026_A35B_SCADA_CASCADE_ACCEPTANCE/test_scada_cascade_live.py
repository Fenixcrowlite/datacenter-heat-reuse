"""Read-only headless SCADA cascade acceptance; all non-GET network blocked.
Only synthetic local what-if DOM controls are changed in isolated browser contexts.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import time
from urllib.request import urlopen
from playwright.sync_api import sync_playwright

HERE=Path(__file__).resolve().parent
ROOT=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\scada_v09")
BASE="http://127.0.0.1:8091"
FILES=(ROOT/"scada_server.py",ROOT/"web"/"app.js",ROOT/"web"/"index.html")
CHROME=Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
EDGE=Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
STOP_ROOTS=(Path(r"C:\Users\Lysda\Desktop\SynapseControlCenter"),
            Path(r"C:\Users\Lysda\Desktop\SynapseControlCenter\recovery"),ROOT,HERE)
FLAGS=("STOP","STOP.flag","STOP.txt",".STOP","PAUSE","PAUSE.flag",".PAUSE","STOP_MANAGED_WORKERS.txt")

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):
            h.update(block)
    return h.hexdigest()

def get(endpoint):
    with urlopen(BASE+endpoint,timeout=5) as r:
        if r.status!=200:raise RuntimeError("HTTP_NOT_200")
        return json.load(r)

def status_safe():
    s=get("/api/status")
    return {k:s[k] for k in ("instance_id","pid","playing","stopped","index","scenario_id","sample_count")}

def check_stop():
    for root in STOP_ROOTS:
        for name in FLAGS:
            if (root/name).exists():
                raise RuntimeError("STOP_ACTIVE "+str(root/name))

def dom(page):
    return page.evaluate("""() => {
        const e=id=>document.getElementById(id);
        const num=id=>Number((e(id)?.textContent||'').replace(',','.').match(/-?\\d+(?:\\.\\d+)?/)?.[0]||NaN);
        return {pool:e('c2-pool').value,dh:e('c2-dh').value,off:Number(e('c2-off').value),
                time:Number(e('c2-time').value),pool_power_kw:num('svg-pool-power'),
                dh_flow_kw:num('svg-dh-flow'),dc_kw:num('svg-dc'),
                pool_pipe_active:e('pipe-pool').classList.contains('active'),
                pool_pipe_off:e('pipe-pool').classList.contains('c2-flow-off'),
                hx_pipe_off:e('pipe-hx').classList.contains('c2-flow-off'),
                dh_pipe_off:e('pipe-dh').classList.contains('c2-flow-off'),
                banner_hidden:e('c2-main-banner').hidden,
                banner:e('c2-main-banner').textContent.slice(0,160),
                pool_mark:e('c2-svg-pool-state').textContent,
                pool_mark_visible:e('c2-svg-pool-state').style.display!=='none'}
    }""")

def range_set(page,id,value):
    page.locator("#"+id).evaluate("""(e,v)=>{e.value=String(v);
        e.dispatchEvent(new Event('input',{bubbles:true}));
        e.dispatchEvent(new Event('change',{bubbles:true}));}""",value)

def browser_check(pw,name,exe):
    tests=[];errors=[];blocked=[]
    def check(label,good,details=None):
        tests.append({"name":name+":"+label,"pass":bool(good),"observed":details})
    browser=pw.chromium.launch(executable_path=str(exe),headless=True,
        args=["--no-first-run","--disable-extensions"])
    try:
        context=browser.new_context(viewport={"width":1360,"height":900})
        page=context.new_page()
        page.on("pageerror",lambda e:errors.append(str(e)))
        def route(r):
            if r.request.method=="GET":r.continue_()
            else:
                blocked.append(r.request.method)
                r.abort()
        page.route("**/*",route)
        page.goto(BASE+"/",wait_until="domcontentloaded",timeout=15000)
        page.wait_for_timeout(1500)
        baseline=dom(page)
        check("baseline_power_positive",baseline["pool_power_kw"]>0 and baseline["dh_flow_kw"]>0,baseline)
        check("baseline_banner_hidden",baseline["banner_hidden"])
        # All controls below are in this isolated browser only. No /api/control requests.
        range_set(page,"c2-off",0);range_set(page,"c2-time",100)
        page.locator("#c2-pool").select_option("0")
        page.wait_for_timeout(250)
        pool=dom(page)
        check("pool_off_zero_and_pipes_off",
            pool["pool_power_kw"]==0 and pool["pool_pipe_off"] and pool["hx_pipe_off"] and not pool["pool_pipe_active"],pool)
        check("pool_off_explicit_label",pool["pool_mark_visible"] and "OFF" in pool["pool_mark"] and not pool["banner_hidden"])
        check("dc_remains_source",pool["dc_kw"]>0)
        if name=="chrome":page.screenshot(path=str(HERE/"SCADA_POOL_OFF_HEADLESS.png"),full_page=False)
        # Polling should not silently restore the base replay visual layer.
        page.wait_for_timeout(2600)
        stable=dom(page)
        check("pool_off_stable_after_poll",stable["pool_power_kw"]==0 and stable["pool_pipe_off"],stable)
        page.locator("#c2-pool").select_option("1")
        page.locator("#c2-dh").select_option("0")
        page.wait_for_timeout(200)
        dh=dom(page)
        check("dh_off_zero_and_pipe_off",dh["dh_flow_kw"]==0 and dh["dh_pipe_off"] and dh["pool_power_kw"]>0,dh)
        page.locator("#c2-pool").select_option("0")
        page.wait_for_timeout(200)
        both=dom(page)
        check("both_off_zero_but_dc_live",both["pool_power_kw"]==0 and both["dh_flow_kw"]==0 and both["dc_kw"]>0,both)
        # Before the what-if onset, the original replay should remain visible.
        range_set(page,"c2-off",120);range_set(page,"c2-time",100)
        page.wait_for_timeout(200)
        before=dom(page)
        check("before_onset_original_baseline",before["pool_power_kw"]>0 and before["dh_flow_kw"]>0 and not before["pool_pipe_off"],before)
        # Reset isolated UI.
        page.locator("#c2-pool").select_option("1")
        page.locator("#c2-dh").select_option("1")
        range_set(page,"c2-off",0);range_set(page,"c2-time",0)
        page.wait_for_timeout(250)
        reset=dom(page)
        check("reset_restores_base",reset["banner_hidden"] and reset["pool_power_kw"]>0 and reset["dh_flow_kw"]>0,reset)
        check("no_non_get_network",not blocked,blocked)
        check("no_js_page_errors",not errors,errors)
        context.close()
    finally:
        browser.close()
    return tests

def main():
    check_stop()
    initial=status_safe()
    health=get("/api/health")
    snap=get("/api/snapshot")
    if not health.get("ok") or initial["stopped"] or initial["playing"]:
        raise RuntimeError("LIVE_SCADA_NOT_IDLE")
    if snap["metadata"]["source_class"]!="D_SYNTHETIC" or snap["metadata"]["hardware_enabled"]:
        raise RuntimeError("NOT_SYNTHETIC")
    before={str(p):sha(p) for p in FILES}
    tests=[]
    with sync_playwright() as pw:
        for name,exe in (("chrome",CHROME),("edge",EDGE)):
            if not exe.is_file():raise RuntimeError("BROWSER_MISSING "+name)
            tests+=browser_check(pw,name,exe)
    after=status_safe()
    afterhash={str(p):sha(p) for p in FILES}
    tests.extend([
        {"name":"live_server_state_unchanged","pass":initial==after,"observed":{"before":initial,"after":after}},
        {"name":"production_sources_unchanged","pass":before==afterhash,"observed":None},
        {"name":"source_label_synthetic","pass":snap["metadata"]["source_class"]=="D_SYNTHETIC" and not snap["metadata"]["hardware_enabled"],"observed":None},
        {"name":"no_tes_soc_invented","pass":snap["derived"]["tes_soc_percent"] is None,"observed":None}
    ])
    out={"time_local":time.strftime("%Y-%m-%d %H:%M:%S"),
         "method":"Headless isolated Chrome+Edge, HTTP GET only, no production writes",
         "tests":tests,"passed":sum(bool(t["pass"]) for t in tests),"total":len(tests),
         "production_source_sha256":before,"server_status_before":initial,"server_status_after":after,
         "release_allowed":False,"simulation_class":"D_SYNTHETIC"}
    (HERE/"SCADA_ACCEPTANCE.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps({"passed":out["passed"],"total":out["total"],
                      "failed":[t["name"] for t in tests if not t["pass"]]},ensure_ascii=False))
    if out["passed"]!=out["total"]:
        raise SystemExit(2)
if __name__=="__main__":
    main()
