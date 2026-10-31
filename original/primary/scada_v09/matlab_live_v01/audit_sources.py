"""Read-only SCADA v08 / MATLAB v04 provenance and consistency audit."""
from __future__ import annotations
import json, math, socket, sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import build_opener, ProxyHandler, HTTPRedirectHandler

ROOT = Path(__file__).resolve().parent
class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError("Redirect forbidden")

def get(port, path):
    opener = build_opener(ProxyHandler({}), NoRedirect())
    with opener.open(f"http://127.0.0.1:{port}{path}", timeout=5) as response:
        if response.status != 200:
            raise ValueError("Bad HTTP status")
        data = response.read(4_000_001)
        if len(data) > 4_000_000:
            raise ValueError("Oversized API response")
        return json.loads(data)

def tcp_open(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return True
    except OSError:
        return False

def audit():
    native = get(8091, "/api/snapshot")
    live = get(8094, "/api/result")
    status = get(8094, "/api/status")
    nm = native["metadata"]
    lm = live["metadata"]
    rows = live["rows"]
    assert nm["source_class"] == "D_SYNTHETIC"
    assert nm["hardware_enabled"] is False
    assert lm["source_class"] == "D_SYNTHETIC"
    assert lm["derived_quality"] == "D_DERIVED"
    assert lm["hardware_enabled"] is False
    assert "v04" in lm["model_scope"] and "v85" in lm["model_scope"]
    assert lm["rows"] == 672 == len(rows)
    assert all(abs(r["cas_h"] - i*.25) < 1e-8 for i,r in enumerate(rows))
    assert all(all(isinstance(x,(int,float)) and math.isfinite(x) for x in r.values()) for r in rows)
    assert status["job"]["state"] == "done"
    assert status["job"]["result_summary"]["rows"] == 672
    # This is an integrity check for computed balances, not field-data calibration.
    residuals = {k:max(abs(float(r[k])) for r in rows) for k in
       ("residual_DC_W","residual_DH_W","residual_HP_W","residual_pool_W")}
    assert all(v < 1e-5 for v in residuals.values()), residuals
    cfg = status["job"]["config"]
    if not cfg["hp_pool_enabled"]:
        assert all(abs(r["Q_HP_pool_W"]) < 1e-5 for r in rows)
    for key, off, power in (("pool_enabled","pool_off_from_h","Q_pool_W"),
                             ("dh_enabled","dh_off_from_h","Q_DH_W")):
        if not cfg[key]:
            assert all(abs(r[power]) < 1e-5 for r in rows)
        if isinstance(cfg.get(off), (float,int)):
            assert all(abs(r[power]) < 1e-5 for r in rows if r["cas_h"] >= cfg[off])
    result = {
      "checked_at":datetime.now(timezone.utc).isoformat(),
      "verdict":"PASS",
      "not_a_live_v85_controller":True,
      "not_field_measurements":True,
      "v08":{"source":"SCADA_ARCHIVED_REPLAY", "scenario":native["status"]["scenario_id"],
             "index":native["status"]["index"],"pool_C":native["values"]["T_pool_C"]},
      "v04":{"source":"MATLAB_REAL_SIMULINK_BATCH", "job_id":status["job"]["id"],
             "state":status["job"]["state"],"rows":len(rows),
             "pool_first_C":rows[0]["T_pool_C"],"pool_final_C":rows[-1]["T_pool_C"],
             "energy_residual_max_W":residuals},
      "service":{"native_scada_8091":True,"matlab_bridge_8094":True,
                 "mqtt_18883":tcp_open(18883),"fuxa_1881":tcp_open(1881)},
      "warning":"v08 replay and v04 fresh simulation are separate datasets; do not merge their KPIs, historian or alarm classes"
    }
    dst = ROOT/"runtime"/"SOURCE_AUDIT_LATEST.json"
    dst.parent.mkdir(exist_ok=True)
    dst.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    return result
if __name__ == "__main__":
    try:
        print(json.dumps(audit(),ensure_ascii=False,indent=2))
    except Exception as e:
        print(json.dumps({"verdict":"FAIL","reason":str(e)},ensure_ascii=False),file=sys.stderr)
        sys.exit(1)
