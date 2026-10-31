"""Independent CSV-only first-law and provenance QA. Does NOT import redispatch."""
from pathlib import Path
from decimal import Decimal as D
import csv, hashlib, json, math

HERE=Path(__file__).resolve().parent
summary=json.loads((HERE/"RESULTS.json").read_text(encoding="utf8"))
source=Path(summary["source_path"])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(source)==summary["source_sha256"]
with source.open(encoding="utf-8-sig",newline="") as f:
    native=list(csv.DictReader(f))
assert len(native)==672
checks=0
for name, entry in summary["scenarios"].items():
    file=HERE/entry["output"]
    assert sha(file)==entry["output_sha256"]
    with file.open(encoding="utf8",newline="") as f:
        output=list(csv.DictReader(f))
    assert len(output)==672
    for i,(n,o) in enumerate(zip(native,output)):
        v=lambda key:float(o[key])
        original=lambda key:float(n[key])
        # Independent first-law identities using exported values, not model residuals.
        assert abs(v("Q_pool_W")-v("Q_HX_W")-v("Q_HP_pool_W"))<1e-5
        assert abs(v("Q_DH_W")-v("Q_HP_DH_W")-v("Q_TES_discharge_W"))<1e-5
        assert abs(v("Q_HP_pool_W")+v("Q_HP_DH_W")+v("Q_HP_charge_W")
                   -v("Q_HP_source_W")-v("P_HP_proxy_W"))<1e-5
        assert abs(original("Q_DC_eff_W")-v("Q_HX_W")-v("Q_HP_source_W")
                   -v("Q_reject_actual_W")-v("Q_unhandled_W")
                   -original("Q_leak_W"))<1e-5
        assert all(v(k)>=-1e-7 for k in (
            "Q_pool_W","Q_DH_W","Q_reject_actual_W","Q_unhandled_W","P_HP_proxy_W"))
        if i<96:
            assert abs(v("Q_pool_W")-original("Q_pool_phys_W"))<1e-5
            assert abs(v("Q_DH_W")-original("Q_DH_W"))<1e-5
        if i>=96 and name in ("pool_off","both_off","both_off_assumed_reject150"):
            assert v("Q_pool_W")==0
        if i>=96 and name in ("dh_off","both_off","both_off_assumed_reject150"):
            assert v("Q_DH_W")==0
        if name=="both_off_assumed_reject150":
            assert v("Q_reject_actual_W")<=150000.00001
            assert (v("Q_unhandled_W")>0)==(v("Q_reject_required_W")>150000.00001)
        checks+=5
    if name=="baseline":
        for n,o in zip(native,output):
            assert abs(float(n["Q_reject_physical_W"])-float(o["Q_reject_required_W"]))<1e-5
        checks+=672
# Decimal-based independent COP-proxy spot check after scenario activation.
r=native[96]
hp_pool=D(r["Q_HP_pool_W"])
hp_dh=D(r["Q_HP_DH_W"])
charge=D(r["Q_HP_charge_W"])
p=D(r["P_HP_W"])
baseline_cond=hp_pool+hp_dh+charge
expected_p=(p*charge/baseline_cond) if baseline_cond else D(0)
with (HERE/"scenario_both_off.csv").open(encoding="utf8",newline="") as f:
    o=list(csv.DictReader(f))[96]
assert abs(D(o["P_HP_proxy_W"])-expected_p)<D("0.00001")
checks+=1
assert not summary["physical_release_allowed"]
assert summary["TES_state"]=="NOT RECOMPUTED"
assert summary["net_electric_savings"].startswith("NOT VALIDATED")
report={"independent_checks_passed":checks,"rows_checked":len(native)*len(summary["scenarios"]),
        "source_sha256":sha(source),"status":"PASS",
        "notes":"Independent CSV first-law checks + Decimal COP spot check. Synthetic input only; no physical release."}
(HERE/"INDEPENDENT_QA.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf8")
print(json.dumps(report,indent=2))
