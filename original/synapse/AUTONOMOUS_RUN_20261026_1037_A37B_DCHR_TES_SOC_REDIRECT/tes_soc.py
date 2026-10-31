"""A37B: v04 TES SOC saturation correction of isolated A36 both-off dispatch.

Source-backed v04: Emax=900 kWh, initial=450 kWh, eta_charge=.93,
eta_discharge=.91, loss=0.002*E/86400 W, dt=900 s.
HP uses A36 fixed-interval COP proxy. No actual hardware/Stateflow control.
"""
import csv,hashlib,json,math
from pathlib import Path
HERE=Path(__file__).resolve().parent
A36=HERE.parent/"AUTONOMOUS_RUN_20261026_0744_A36_DCHR_REDISPATCH_REFERENCE"
V08=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\results\pool_measurement_v08\sim_v08_zdravy_SK.csv")
V04=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\matlab\pool_feedback_v04\alokuj_teplo_v04_sk.txt")
DT=900.;EMAX=900*3.6e6;E0=450*3.6e6;ETA_C=.93;ETA_D=.91;TOL=1e-4
FIELDS=["cas_h","E_TES_start_J","E_TES_next_J","TES_SOC_next",
        "Q_charge_requested_W","Q_charge_actual_W","Q_charge_curtailed_W",
        "Q_TES_discharge_W","Q_TES_loss_W","Q_HP_source_corrected_W",
        "P_HP_corrected_W","Q_reject_corrected_W","Q_reject_increment_W",
        "TES_balance_residual_J","HP_balance_residual_W","DC_balance_residual_W"]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def val(x,name):
    x=float(x)
    if not math.isfinite(x) or x < -1e-8:raise ValueError("invalid "+name)
    return max(0.,x)
def tes_step(E,requested,discharge):
    E=val(E,"E");request=val(requested,"charge");dis=val(discharge,"discharge")
    if E>EMAX+TOL:raise ValueError("TES over capacity")
    if request>1e-7 and dis>1e-7:raise ValueError("simultaneous charge/discharge")
    loss=.002*E/86400.
    available=max(0.,(E-loss*DT)*ETA_D/DT)
    if dis>available+1e-5:raise ValueError("TES insufficient discharge")
    room=max(0.,(EMAX-E+DT*(dis/ETA_D+loss))/(ETA_C*DT))
    actual=min(request,room)
    Enext=E+DT*(ETA_C*actual-dis/ETA_D-loss)
    if Enext>EMAX+TOL or Enext < -TOL:raise AssertionError("TES bound")
    Enext=max(0.,min(EMAX,Enext))
    residual=Enext-E-DT*(ETA_C*actual-dis/ETA_D-loss)
    if abs(residual)>TOL:raise AssertionError("TES balance")
    return {"E_next_J":Enext,"charge_actual_W":actual,
            "charge_curtailed_W":request-actual,"loss_W":loss,
            "TES_balance_residual_J":residual}
def load():
    a=json.loads((A36/"RESULTS.json").read_text(encoding="utf8"))
    if sha(V08)!=a["source_sha256"]:raise RuntimeError("V08_SHA_CHANGED")
    src=A36/a["scenarios"]["both_off"]["output"]
    if sha(src)!=a["scenarios"]["both_off"]["output_sha256"]:raise RuntimeError("A36_SHA_CHANGED")
    model=V04.read_text(encoding="utf-8-sig")
    for signature in ["Emax=900*3.6e6","eta_c=0.93; eta_d=0.91",
                      "Qtesloss=0.002*max(0,E)/86400",
                      "Enext=max(0,min(Emax,E+dt*(eta_c*Qcharge-Qdis/eta_d-Qtesloss)))"]:
        if signature not in model:raise RuntimeError("V04_EQUATION_CHANGED")
    with V08.open(encoding="utf-8-sig",newline="") as f:raw=list(csv.DictReader(f))
    with src.open(encoding="utf8",newline="") as f:dispatch=list(csv.DictReader(f))
    if len(raw)!=672 or len(dispatch)!=672:raise RuntimeError("EXPECTED_672")
    return raw,dispatch,src
def baseline_replay(raw):
    E=E0;maxerr=0.
    for row in raw:
        x=tes_step(E,row["Q_HP_charge_W"],row["Q_TES_discharge_W"])
        maxerr=max(maxerr,abs(x["E_next_J"]-float(row["E_TES_J"])))
        E=x["E_next_J"]
    return maxerr
def replay(raw,dispatch):
    E=E0;out=[]
    for i,(r,d) in enumerate(zip(raw,dispatch)):
        h=float(r["cas_h"])
        if abs(h-float(d["cas_h"]))>1e-9 or abs(h-i*.25)>1e-8:
            raise RuntimeError("TIMESTAMPS")
        req=val(d["Q_HP_charge_W"],"charge request")
        dis=val(d["Q_TES_discharge_W"],"discharge")
        x=tes_step(E,req,dis)
        old_cond=sum(val(d[k],k) for k in ["Q_HP_pool_W","Q_HP_DH_W","Q_HP_charge_W"])
        old_p=val(d["P_HP_proxy_W"],"P_HP_proxy_W")
        new_cond=old_cond-x["charge_curtailed_W"]
        new_p=old_p*new_cond/old_cond if old_cond>1e-8 else 0.
        new_src=new_cond-new_p
        old_src=val(d["Q_HP_source_W"],"Q_HP_source_W")
        old_reject=val(d["Q_reject_required_W"],"Q_reject_required_W")
        new_reject=old_reject+old_src-new_src
        if new_reject < -1e-6:raise AssertionError("negative reject")
        hp_res=new_cond-new_src-new_p
        dc_res=val(r["Q_DC_eff_W"],"Qdc")-val(d["Q_HX_W"],"HX")-new_src-new_reject-val(r["Q_leak_W"],"leak")-val(d["Q_unhandled_W"],"unhandled")
        if abs(hp_res)>1e-5 or abs(dc_res)>1e-5:raise AssertionError("HP/DC energy closure")
        out.append(dict(cas_h=h,E_TES_start_J=E,E_TES_next_J=x["E_next_J"],
            TES_SOC_next=x["E_next_J"]/EMAX,Q_charge_requested_W=req,
            Q_charge_actual_W=x["charge_actual_W"],Q_charge_curtailed_W=x["charge_curtailed_W"],
            Q_TES_discharge_W=dis,Q_TES_loss_W=x["loss_W"],
            Q_HP_source_corrected_W=new_src,P_HP_corrected_W=new_p,
            Q_reject_corrected_W=new_reject,Q_reject_increment_W=new_reject-old_reject,
            TES_balance_residual_J=x["TES_balance_residual_J"],
            HP_balance_residual_W=hp_res,DC_balance_residual_W=dc_res))
        E=x["E_next_J"]
    return out
def main():
    raw,dispatch,src=load()
    err=baseline_replay(raw)
    if err>1e-4:raise RuntimeError("BASELINE_TES_NOT_REPRODUCED")
    out=replay(raw,dispatch)
    path=HERE/"TES_SOC_TRACE.csv"
    with path.open("w",encoding="utf8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(out)
    clips=[x for x in out if x["Q_charge_curtailed_W"]>1e-6]
    report={"status":"SYNTHETIC_TES_SOC_CORRECTION_ONLY","physical_release_allowed":False,
        "source_v04_sha256":sha(V04),"source_v08_sha256":sha(V08),
        "source_a36_sha256":sha(src),"samples":len(out),
        "baseline_replay_max_E_error_J":err,
        "TES_capacity_kWh":900,"TES_initial_kWh":450,
        "clip_intervals":len(clips),"first_clip_h":clips[0]["cas_h"] if clips else None,
        "charge_curtailed_kWh":sum(x["Q_charge_curtailed_W"] for x in out)*.25/1000,
        "additional_reject_kWh":sum(x["Q_reject_increment_W"] for x in out)*.25/1000,
        "compressor_proxy_savings_kWh":sum((float(d["P_HP_proxy_W"])-x["P_HP_corrected_W"]) for x,d in zip(out,dispatch))*.25/1000,
        "final_TES_SOC":out[-1]["TES_SOC_next"],
        "max_TES_SOC":max(x["TES_SOC_next"] for x in out),
        "trace_sha256":sha(path),
        "limitations":"TES only: frozen A36 HP COP, unchanged DC demand, no dynamic pool/DH or control reoptimization; no certified equipment",
        "trace":path.name}
    (HERE/"RESULTS_A37B.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
