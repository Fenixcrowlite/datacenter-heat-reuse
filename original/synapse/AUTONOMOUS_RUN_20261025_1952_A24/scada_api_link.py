"""Read-only current SCADA scenario SHA crosscheck against verified v08 lineage."""
import json, urllib.request
from pathlib import Path
from dchr_lineage_audit import CASES

def check(meta: dict, lineage: dict) -> dict:
    if meta.get("metadata",{}).get("source_class")!="D_SYNTHETIC" or meta["metadata"].get("hardware_enabled") is not False:
        raise ValueError("SCADA provenance mismatch")
    by_name={s["scenario"]:s["v08_csv_sha256"] for s in lineage["cases"]}
    by_api={s["id"]:s for s in meta["scenarios"]}
    if set(by_name)!=set(CASES) or set(by_api)!=set(CASES):
        raise ValueError("SCADA case set mismatch")
    for name in CASES:
        if by_api[name]["sha256"].lower()!=by_name[name].lower():
            raise ValueError("SCADA source SHA mismatch "+name)
        if by_api[name]["rows"]!=672 or by_api[name]["quality"]!="D":
            raise ValueError("SCADA sample count or quality mismatch "+name)
    return {"status":"PASS_LIVE_SCADA_SHA_LINK","scenario_count":8,"source_class":"D_SYNTHETIC",
            "source_sha256":by_name,"limits":"Only verifies current API-reported source SHA; not a Simulink execution receipt."}

def fetch(url="http://127.0.0.1:8091/api/scenarios"):
    with urllib.request.urlopen(url,timeout=8) as r:
        if r.status!=200:raise ValueError("HTTP "+str(r.status))
        return json.load(r)

if __name__=="__main__":
    d=Path(__file__).resolve().parent
    result=check(fetch(),json.loads((d/"DCHR_LINEAGE_EVIDENCE.json").read_text(encoding="utf-8")))
    (d/"SCADA_LINEAGE_LINK.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(result["status"],result["scenario_count"])
