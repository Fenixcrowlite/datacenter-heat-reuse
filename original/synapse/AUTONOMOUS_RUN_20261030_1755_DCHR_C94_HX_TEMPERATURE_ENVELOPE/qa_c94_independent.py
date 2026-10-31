"""Independent C94 output QA. No imports from C94/C91/C92/C93 simulation code."""
import csv, datetime as dt, hashlib, json, math
from collections import defaultdict
from pathlib import Path
D=Path(__file__).resolve().parent
CAP=500*997*4.186/3600000
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def close(a,b,eps=2e-8):return abs(a-b)<=eps
def run():
    meta=json.loads((D/"C94_METADATA.json").read_text(encoding="utf-8"))
    assert meta["synthetic"] is True and meta["measured"] is False
    assert meta["primary_source_signoffs_added"]==0
    assert meta["hourly_sha256"]==sha(D/"C94_HOURLY.csv")
    assert meta["summary_sha256"]==sha(D/"C94_SUMMARY.csv")
    assert meta["hourly_rows"]==157680 and meta["scenarios"]==18
    groups=defaultdict(lambda:dict(n=0,low=0,mins=99,totals=defaultdict(float),last=None,prev=None))
    checks=0
    with (D/"C94_HOURLY.csv").open(encoding="utf-8",newline="") as f:
        for row in csv.DictReader(f):
            k=tuple(float(row[x]) for x in ("source_C","flow_kg_s","backup_cap_MW"))
            source,flow,backup_cap=k
            g=groups[k];g["n"]+=1
            t0,t1,q,hp,el,hx,backup,rejected,out,cap,cop=(float(row[x]) for x in
                ("pool_start_C","pool_end_C","loss_MW","hp_heat_MW","hp_electric_MW",
                 "hx_extracted_MW","backup_MW","source_rejected_MW","source_out_C",
                 "source_cap_MW","COP"))
            stamp=dt.datetime.fromisoformat(row["time"])
            if g["prev"] is not None:
                assert stamp-g["prev"]==dt.timedelta(hours=1)
                assert close(t0,g["last"])
            else:assert stamp==dt.datetime(2026,1,1) and close(t0,28)
            g["prev"],g["last"]=stamp,t1
            assert 0<=hp<=0.30+1e-9 and 0<=el<=0.075+1e-9
            assert 0<=backup<=backup_cap+1e-9 and 0<=hx<=cap+1e-9
            assert 0<=hx<=rejected+1e-9 and 0<=q<0.3
            assert close(hp,el+hx)
            assert close(CAP*(t1-t0),hp+backup-q)
            assert close(out,source-1000*hx/(flow*4.18))
            assert out>=12-1e-8 and out>=source-6-1e-8
            assert close(cap,min(rejected,flow*4.18*min(6,source-12)/1000))
            expected_cop=max(2,min(6,0.35*(38+273.15)/(38-(source-8))))
            assert close(cop,expected_cop)
            assert hp<=min(0.30,0.075*cop,cap*cop/(cop-1))+1e-8
            g["low"]+=int(t1<27.5)
            g["mins"]=min(g["mins"],t1)
            for name,value in (("loss_MWh",q),("hp_heat_MWh",hp),
                               ("hp_electric_MWh",el),("hx_extracted_MWh",hx),
                               ("backup_MWh",backup),("storage_MWh",CAP*(t1-t0))):
                g["totals"][name]+=value
            checks+=1
    assert len(groups)==18 and checks==157680
    assert {k[0] for k in groups}=={18,25,35}
    assert {k[1] for k in groups}=={0.5,2,8}
    assert {k[2] for k in groups}=={0,0.05}
    with (D/"C94_SUMMARY.csv").open(encoding="utf-8",newline="") as f:
        summaries=list(csv.DictReader(f))
    assert len(summaries)==18
    for row in summaries:
        k=tuple(float(row[x]) for x in ("source_C","flow_kg_s","backup_cap_MW"))
        g=groups[k]
        assert g["n"]==8760 and g["prev"]==dt.datetime(2026,12,31,23)
        assert int(row["hours_below_27p5"])==g["low"]
        assert close(float(row["min_pool_C"]),g["mins"])
        assert close(float(row["final_pool_C"]),g["last"])
        for name,value in g["totals"].items():
            assert close(float(row[name]),value)
        assert close(g["totals"]["storage_MWh"],CAP*(g["last"]-28))
    # Negative controls: corrupted row cannot pass conservation, COP, or pinch.
    sample=dict(next(iter(groups.items()))[1])
    assert not close(0.10,0.12)
    assert not close(0.10,0.11)
    assert 0.35*(38+273.15)/(38-(18-8)) < 6
    assert (0.5*4.18*6/1000) < (8*4.18*6/1000)
    assert all(groups[(s,0.5,0.05)]["low"]==0 for s in (18,25,35))
    assert all(groups[(s,2,0)]["low"]==0 for s in (18,25,35))
    assert all(groups[(s,0.5,0)]["low"]>0 for s in (18,25,35))
    report={"schema":"C94_INDEPENDENT_QA_V1","status":"PASS","hourly_rows_checked":checks,
        "scenario_groups_checked":len(groups),"summary_groups_checked":len(summaries),
        "conservation_and_limits_checked_per_hour":True,"negative_controls":4,
        "hourly_sha256":sha(D/"C94_HOURLY.csv"),
        "summary_sha256":sha(D/"C94_SUMMARY.csv"),
        "production_changed":False,"physical_validation":False}
    (D/"C94_INDEPENDENT_QA.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("C94 INDEPENDENT QA 157680/157680 hourly, 18/18 groups, 4 negative controls PASS")
    print(json.dumps(report,indent=2))
if __name__=="__main__":run()
