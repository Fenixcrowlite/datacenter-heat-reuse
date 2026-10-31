"""Independent Decimal reimplementation: does NOT import model step/simulate."""
import csv, hashlib, json
from decimal import Decimal as D, getcontext
from pathlib import Path
getcontext().prec=32
HERE=Path(__file__).parent
SRC=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\results\best_scenario_v2_timeseries.csv")
SHA="8125719923bae97901f37cf0f5354df77b46544df0477f863172255748873f25"
def check():
    raw=SRC.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==SHA
    rows=list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
    out=json.loads((HERE/"CONSTRAINED_SENSITIVITY.json").read_text(encoding="utf-8"))
    assert len(rows)==8760 and out["rows"]==8760 and out["source_sha256"]==SHA
    gas=sum((D(r["Gas_Heat_MW"]) for r in rows),D(0))
    potential=sum((D(r["Curtailed_HP_Heat_MW"]) for r in rows),D(0))
    for model in out["models"]+out["thermal_sensitivity"]:
        assert model["classification"]=="SYNTHETIC_CONSTRAINED_SENSITIVITY_NOT_INCREMENTAL_SAVINGS"
        c=model["config"]
        for y in model["year_results"]:
            assert 0<=y["delivered_mwh"]<=float(gas)+1e-5
            assert 0<=y["charge_mwh"]<=float(potential)+1e-5
            assert y["additional_electric_mwh"]<=8760*c["extra_hp_electric_mw"]+1e-5
            assert 0<=y["final_soc_mwh"]<=c["capacity_mwh"]+1e-5
            lhs=y["initial_soc_mwh"]+y["charge_mwh"]*c["charge_efficiency"]
            rhs=y["final_soc_mwh"]+y["loss_mwh"]+y["delivered_mwh"]/c["discharge_efficiency"]
            assert abs(lhs-rhs)<0.0001,(c,y["year"],lhs,rhs)
    assert len(out["thermal_sensitivity"])==5
    thermal=out["thermal_sensitivity"]
    assert thermal[0]["year_results"][2]["temperature_blocked_hours"]>0
    assert thermal[2]["year_results"][2]["temperature_blocked_hours"]==0
    assert thermal[4]["year_results"][2]["delivered_mwh"]>thermal[2]["year_results"][2]["delivered_mwh"]
    target=next(m for m in out["models"] if m["config"]["capacity_mwh"]==2500
                and m["config"]["extra_hp_electric_mw"]==1.5)
    c={k:D(str(v)) for k,v in target["config"].items()}
    soc=D(0); observed=[]; row_checks=0
    for year in range(3):
        begin=soc; totals={k:D(0) for k in ("charge_mwh","delivered_mwh","loss_mwh",
                                         "additional_electric_mwh","source_heat_mwh",
                                         "remaining_gas_heat_mwh")}
        blocked=0
        for r in rows:
            cop=D(r["COP"]);lift=D(r["Temperature_Lift_K"])
            supply=D(r["DH_Supply_C"])
            extra=max(D(0),c["storage_temperature_c"]+c["hx_approach_k"]-supply)
            cop_eff=cop*lift/(lift+extra)
            loss=soc*c["hourly_loss_fraction"];soc-=loss
            headroom=min(c["extra_hp_electric_mw"],
                         max(D(0),c["site_electric_cap_mw"]-D(r["DC_Total_MW"])),
                         max(D(0),c["hp_total_electric_cap_mw"]-D(r["HP_Electric_MW"])))
            source_head=max(D(0),D(r["Source_Heat_Available_MW"])-D(r["HP_Source_Used_MW"]))
            charge=D(0);electric=D(0);source=D(0)
            if cop_eff>D("1.01") and c["capacity_mwh"]>0:
                q=D(r["Curtailed_HP_Heat_MW"])*min(D(1),cop_eff/cop)
                charge=max(D(0),min(q,c["charge_mw"],headroom*cop_eff,
                                    source_head/(D(1)-D(1)/cop_eff),
                                    max(D(0),c["capacity_mwh"]-soc)/c["charge_efficiency"]))
                electric=charge/cop_eff;source=charge-electric
                soc+=charge*c["charge_efficiency"]
            gas_d=D(r["Gas_Heat_MW"])
            can_discharge=c["storage_temperature_c"]>=supply+c["hx_approach_k"]
            delivered=min(gas_d,c["discharge_mw"],soc*c["discharge_efficiency"]) if can_discharge else D(0)
            soc-=delivered/c["discharge_efficiency"]
            assert -D("1e-15")<=soc<=c["capacity_mwh"]+D("1e-15")
            assert electric<=headroom+D("1e-15")
            assert source<=source_head+D("1e-15")
            for key,val in (("charge_mwh",charge),("delivered_mwh",delivered),
                            ("loss_mwh",loss),("additional_electric_mwh",electric),
                            ("source_heat_mwh",source),
                            ("remaining_gas_heat_mwh",gas_d-delivered)):
                totals[key]+=val
            blocked+=int(not can_discharge);row_checks+=1
        y=target["year_results"][year]
        for key,val in totals.items():
            assert abs(val-D(str(y[key])))<D("0.000002"),(year,key,str(val),y[key])
        assert abs(soc-D(str(y["final_soc_mwh"])))<D("0.000002")
        assert abs(begin-D(str(y["initial_soc_mwh"])))<D("0.000002")
        assert blocked==y["temperature_blocked_hours"]
        observed.append({"year":year+1,"delivered_mwh":float(totals["delivered_mwh"]),
                         "electric_mwh":float(totals["additional_electric_mwh"])})
    return {"status":"PASS","rows":len(rows),"models_checked":len(out["models"])+len(out["thermal_sensitivity"]),
            "aggregate_years_checked":39,"independent_decimal_hour_steps":row_checks,
            "independent_decimal_years":observed,
            "source_sha256":SHA}
if __name__=="__main__":
    result=check()
    (HERE/"QA_INDEPENDENT.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result))
