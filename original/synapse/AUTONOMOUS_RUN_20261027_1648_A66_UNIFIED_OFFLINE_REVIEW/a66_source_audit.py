"""A66 independent re-hash of all eight upstream CSV/summary files."""
import json,hashlib
from pathlib import Path
import a66_unified as m
def audit():
    cmp=m.load()[1]
    checks={}
    for scenario in ("V08","V09"):
        a=cmp["scenarios"][scenario]
        n=scenario[-2:]
        p60=m.RECOVERY/"AUTONOMOUS_RUN_20261027_1250_A60_SCADA_DERIVED_EXPORT"/f"OUTPUT_V{n}_DERIVED"
        p62=m.RECOVERY/"AUTONOMOUS_RUN_20261027_1405_A62_SIGNED_LOSS_EXPORT"/f"OUTPUT_V{n}_SIGNED"
        for name,path in (
            ("a60_csv",p60/"analysis_timeseries.csv"),
            ("a60_summary",p60/"summary.json"),
            ("a62_csv",p62/"analysis_with_signed_losses.csv"),
            ("a62_summary",p62/"summary.json")):
            expected=a[name+"_sha256"]
            actual=hashlib.sha256(path.read_bytes()).hexdigest()
            if actual!=expected:
                raise ValueError("SOURCE_FILE_CHANGED:"+scenario+":"+name)
            checks[scenario+":"+name]=actual
    return {"verified_hashes":len(checks),"status":"PASS","checks":checks,"physical_release":False}
if __name__=="__main__":
    print(json.dumps(audit(),sort_keys=True))
