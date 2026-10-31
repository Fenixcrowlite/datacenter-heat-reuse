"""Independent Decimal replay of A45 CSV physical balances and HP lag."""
import csv
import json
from decimal import Decimal, getcontext
from pathlib import Path

HERE=Path(__file__).resolve().parent
getcontext().prec=34
D=lambda x:Decimal(str(x))
DT=D(900)
TOL_W=D("0.00001")
TOL_J=D("0.02")
FIELDS=("qit_W","hx_W","leak_W","hp_source_W","reject_W","unhandled_W",
        "hp_condenser_W","hp_electric_W","pool_dh_demand_W","pool_dh_served_W",
        "pool_dh_unmet_W","E_next_J","E_start_J","tes_charge_W",
        "tes_discharge_W","tes_loss_W","hp_available_W","hp_source_target_W")

def audit():
    names=["both","main_only","backup_only","neither",
           "CF_both","CF_backup_only","CF_neither"]
    count=0
    max_residual=D(0)
    cases={}
    for name in names:
        path=HERE/("TRACE_A45_"+name+".csv")
        with path.open(encoding="utf8",newline="") as f:
            rows=list(csv.DictReader(f))
        if len(rows)!=672: raise AssertionError(("COUNT",name,len(rows)))
        maxT=max(float(r["T_next_C"]) for r in rows)
        for r in rows:
            x={k:D(r[k]) for k in FIELDS}
            residuals=[
                x["qit_W"]-x["hx_W"]-x["leak_W"]-x["hp_source_W"]-x["reject_W"]-x["unhandled_W"],
                x["hp_condenser_W"]-x["hp_source_W"]-x["hp_electric_W"],
                x["pool_dh_demand_W"]-x["pool_dh_served_W"]-x["pool_dh_unmet_W"],
                x["E_next_J"]-x["E_start_J"]-DT*(D(".93")*x["tes_charge_W"]-x["tes_discharge_W"]/D(".91")-x["tes_loss_W"])
            ]
            for i,res in enumerate(residuals):
                tol=TOL_J if i==3 else TOL_W
                if abs(res)>tol: raise AssertionError(("BALANCE",name,r["k"],i,str(res)))
                max_residual=max(max_residual,abs(res))
                count+=1
            if x["hp_source_W"]>x["hp_available_W"]+TOL_W:
                raise AssertionError(("HP_CAP",name,r["k"]))
            if x["hp_source_W"]>x["hp_source_target_W"]+TOL_W:
                raise AssertionError(("HP_TARGET",name,r["k"]))
        cases[name]={"rows":len(rows),"max_T_C":maxT}
    return {"status":"A45_DECIMAL_AUDIT_PASS","samples":672*7,
            "balance_checks":count,"max_abs_balance_residual_mixed_units":str(max_residual),
            "cases":cases,"physical_release":False,"matlab_simulink_integrated":False}

if __name__=="__main__":
    result=audit()
    (HERE/"DECIMAL_AUDIT_A45.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf8")
    print(json.dumps(result))
