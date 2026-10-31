"""Independent high-precision TES/HP/DC cross-check without importing tes_soc.py."""
import csv,hashlib,json
from decimal import Decimal,getcontext
from pathlib import Path
getcontext().prec=36
HERE=Path(__file__).resolve().parent
V08=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\results\pool_measurement_v08\sim_v08_zdravy_SK.csv")
A36=HERE.parent/"AUTONOMOUS_RUN_20261026_0744_A36_DCHR_REDISPATCH_REFERENCE"/"scenario_both_off.csv"
D=lambda x:Decimal(str(x))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def close(a,b,tol="0.0002"):
    if abs(D(a)-D(b))>D(tol):raise AssertionError(f"DECIMAL {a} != {b}")
def main():
    result=json.loads((HERE/"RESULTS_A37B.json").read_text(encoding="utf8"))
    assert result["physical_release_allowed"] is False
    assert sha(V08)==result["source_v08_sha256"] and sha(A36)==result["source_a36_sha256"]
    trace=HERE/result["trace"];assert sha(trace)==result["trace_sha256"]
    with V08.open(encoding="utf-8-sig",newline="") as f:raw=list(csv.DictReader(f))
    with A36.open(encoding="utf8",newline="") as f:dispatch=list(csv.DictReader(f))
    with trace.open(encoding="utf8",newline="") as f:rows=list(csv.DictReader(f))
    assert len(rows)==len(raw)==len(dispatch)==672
    E=D(450)*D(3600000);Emax=D(900)*D(3600000);dt=D(900)
    clips=0;charge_kwh=D(0);reject_kwh=D(0);checks=0
    for i,(r,b,o) in enumerate(zip(raw,dispatch,rows)):
        close(r["cas_h"],b["cas_h"],"0.000000001")
        close(o["cas_h"],r["cas_h"],"0.000000001")
        charge=D(b["Q_HP_charge_W"]);dis=D(b["Q_TES_discharge_W"])
        loss=D("0.002")*E/D(86400)
        room=max(D(0),(Emax-E+dt*(dis/D(".91")+loss))/(D(".93")*dt))
        actual=min(charge,room)
        nextE=max(D(0),min(Emax,E+dt*(D(".93")*actual-dis/D(".91")-loss)))
        old_cond=sum(D(b[k]) for k in ("Q_HP_pool_W","Q_HP_DH_W","Q_HP_charge_W"))
        new_cond=old_cond-(charge-actual)
        new_p=D(b["P_HP_proxy_W"])*new_cond/old_cond if old_cond else D(0)
        new_source=new_cond-new_p
        new_reject=D(b["Q_reject_required_W"])+D(b["Q_HP_source_W"])-new_source
        close(o["E_TES_start_J"],E)
        close(o["E_TES_next_J"],nextE)
        close(o["Q_charge_actual_W"],actual,"0.000001")
        close(o["Q_charge_curtailed_W"],charge-actual,"0.000001")
        close(o["Q_TES_loss_W"],loss,"0.000001")
        close(o["P_HP_corrected_W"],new_p,"0.000001")
        close(o["Q_HP_source_corrected_W"],new_source,"0.000001")
        close(o["Q_reject_corrected_W"],new_reject,"0.000001")
        close(o["TES_SOC_next"],nextE/Emax,"0.000000001")
        assert Emax>=nextE>=0
        if charge-actual>D("0.000001"):clips+=1
        charge_kwh+=(charge-actual)*D(".25")/1000
        reject_kwh+=(new_reject-D(b["Q_reject_required_W"]))*D(".25")/1000
        E=nextE;checks+=12
    assert clips==result["clip_intervals"]
    close(result["charge_curtailed_kWh"],charge_kwh,"0.000001")
    close(result["additional_reject_kWh"],reject_kwh,"0.000001")
    close(result["final_TES_SOC"],E/Emax,"0.000000001")
    out={"status":"PASS","rows":len(rows),"independent_decimal_checks":checks,
         "source_sha_verified":True,"physical_release_allowed":False}
    (HERE/"INDEPENDENT_QA.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf8")
    print(json.dumps(out))
if __name__=="__main__":main()
