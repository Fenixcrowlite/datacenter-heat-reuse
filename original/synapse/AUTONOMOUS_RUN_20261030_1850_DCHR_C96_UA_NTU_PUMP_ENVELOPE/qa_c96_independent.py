"""Independent C96 validation: recompute HX counterflow, pump, pool and annual balances.
Does NOT import C96 model; intentionally corrupt synthetic samples must fail.
"""
import csv, gzip, hashlib, json, math
from collections import defaultdict
from pathlib import Path
D=Path(__file__).resolve().parent
CAP=500*997*4.186/3600000
CP=4.18

def check_row(r):
    hot=float(r["hot_in_C"]); flow=float(r["hot_flow_kg_s"])
    ua=float(r["UA_kW_K"]); cop=float(r["COP_assumed"])
    ch=flow*CP;cc=2*CP;cm=min(ch,cc);cr=cm/max(ch,cc)
    ntu=ua/cm
    if abs(cr-1)<1e-9: eps=ntu/(1+ntu)
    else:
        z=math.exp(-ntu*(1-cr))
        eps=(1-z)/(1-cr*z)
    qntu=eps*cm*(hot-15)/1000
    qcap=min(float(r["rejected_MW"]),qntu,ch*(hot-12)/1000)
    hp=float(r["hp_heat_MW"]);el=float(r["hp_electric_MW"])
    extracted=float(r["hx_extracted_MW"]); pump=float(r["pump_electric_MW"])
    backup=float(r["backup_MW"]); loss=float(r["pool_loss_MW"])
    t=float(r["pool_start_C"]);t2=float(r["pool_end_C"])
    q=hp-el
    assert 0<=eps<=1 and 0<=qcap+1e-10
    assert abs(eps-float(r["epsilon"]))<2e-11
    assert abs(ntu-float(r["NTU"]))<2e-11
    assert abs(qntu-float(r["hx_ntu_capacity_MW"]))<2e-11
    assert abs(qcap-float(r["hx_capacity_MW"]))<2e-11
    assert abs(extracted-q)<3e-11 and extracted<=qcap+2e-11
    assert abs(hp-el*cop)<2e-11 and hp<=0.3+1e-11 and el<=0.075+1e-11
    assert abs(float(r["hot_out_C"])-(hot-1000*extracted/ch))<3e-10
    assert abs(float(r["cold_out_C"])-(15+1000*extracted/cc))<3e-10
    assert float(r["hot_out_C"])>=12-1e-10
    assert float(r["cold_out_C"])<=hot+1e-10
    expected_pump=((30*flow+40*2)/0.6/1e6) if hp>0 else 0
    assert abs(pump-expected_pump)<2e-11
    assert 0<=backup<=float(r["backup_cap_MW"])+1e-11
    assert abs(CAP*(t2-t)-(hp+backup-loss))<2e-10
    return {"loss_MWh":loss,"hp_heat_MWh":hp,"hp_electric_MWh":el,
      "hx_extracted_MWh":extracted,"pump_electric_MWh":pump,
      "backup_MWh":backup,"storage_MWh":CAP*(t2-t)}

def reject_corruption(row):
    mutated=dict(row);mutated["hp_electric_MW"]=str(float(row["hp_electric_MW"])+0.001)
    try:check_row(mutated)
    except AssertionError:return True
    return False

def main():
    metadata=json.loads((D/"C96_METADATA.json").read_text(encoding="utf-8"))
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    assert sha(D/"C96_HOURLY.csv.gz")==metadata["hourly_sha256"]
    assert sha(D/"C96_SUMMARY.csv")==metadata["summary_sha256"]
    assert metadata["synthetic"] and not metadata["field_validated"] and not metadata["vendor_COP"]
    assert metadata["primary_source_signoffs_added"]==0
    with (D/"C96_SUMMARY.csv").open(encoding="utf-8",newline="") as f:
        summaries={r["scenario"]:r for r in csv.DictReader(f)}
    assert len(summaries)==26
    acc=defaultdict(lambda:defaultdict(float))
    count=defaultdict(int);low=defaultdict(int);mins=defaultdict(lambda:100.0)
    first={};last={}
    bad_sample=None
    with gzip.open(D/"C96_HOURLY.csv.gz","rt",encoding="utf-8",newline="") as f:
        for r in csv.DictReader(f):
            scenario=r["scenario"]
            assert scenario in summaries
            if bad_sample is None and float(r["hp_heat_MW"])>0:bad_sample=r
            values=check_row(r)
            for k,v in values.items():acc[scenario][k]+=v
            count[scenario]+=1
            mins[scenario]=min(mins[scenario],float(r["pool_end_C"]))
            low[scenario]+=int(float(r["pool_end_C"])<27.5)
            if scenario not in first:first[scenario]=r
            if scenario in last:
                assert abs(float(r["pool_start_C"])-float(last[scenario]["pool_end_C"]))<2e-11
            last[scenario]=r
    assert sum(count.values())==227760 and all(n==8760 for n in count.values())
    assert bad_sample is not None and reject_corruption(bad_sample)
    groups=0
    for sid,s in summaries.items():
        assert sid in acc
        for key in ("loss_MWh","hp_heat_MWh","hp_electric_MWh","hx_extracted_MWh",
                    "pump_electric_MWh","backup_MWh","storage_MWh"):
            assert abs(acc[sid][key]-float(s[key]))<2e-7,(sid,key)
        assert abs(float(s["total_electric_MWh"])-float(s["hp_electric_MWh"])-float(s["pump_electric_MWh"]))<1e-8
        assert abs(mins[sid]-float(s["min_pool_C"]))<2e-11
        assert low[sid]==int(s["hours_below_27p5"])
        assert abs(float(first[sid]["pool_start_C"])-28.0)<2e-11
        assert abs(CAP*(float(last[sid]["pool_end_C"])-28.0)-float(s["storage_MWh"]))<1e-7
        groups+=1
    # independent counterflow LMTD identity, evaluated at full UA/NTU capacity
    lmtd_checks=0
    for hot in (35.0,38.0,50.0):
        for flow in (0.5,2.0):
            for ua in (2.0,10.0):
                ch=flow*CP;cc=2*CP;cm=min(ch,cc);cr=cm/max(ch,cc);ntu=ua/cm
                if abs(cr-1)<1e-9:eps=ntu/(1+ntu)
                else:
                    z=math.exp(-ntu*(1-cr));eps=(1-z)/(1-cr*z)
                q=eps*cm*(hot-15)
                d1=hot-(15+q/cc);d2=(hot-q/ch)-15
                assert d1>0 and d2>0
                lmtd=d1 if abs(d1-d2)<1e-9 else (d1-d2)/math.log(d1/d2)
                assert abs(q-ua*lmtd)<1e-8,(hot,flow,ua,q,ua*lmtd)
                lmtd_checks+=1
    report={"status":"PASS","hourly_rows_verified":sum(count.values()),
      "scenario_groups_verified":groups,"LMTD_independent_checks":lmtd_checks,
      "negative_corruption_detected":True,"source_signoffs_added":0,
      "field_validation":False,"hourly_sha256":metadata["hourly_sha256"],
      "summary_sha256":metadata["summary_sha256"]}
    with (D/"C96_INDEPENDENT_QA.json").open("x",encoding="utf-8") as f:
        json.dump(report,f,indent=2,sort_keys=True);f.write("\n")
    print(json.dumps(report,indent=2))
if __name__=="__main__":main()
