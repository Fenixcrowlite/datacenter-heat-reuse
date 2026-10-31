"""Independent C100 numerical and scientific QA, no writes to shared projects."""
from __future__ import annotations
import csv,gzip,hashlib,json,math
from collections import defaultdict
from pathlib import Path
D=Path(__file__).resolve().parent
META=D/"C100_METADATA.json"
DATA=D/"C100_AIR_HOURLY.csv.gz"
SUMMARY=D/"C100_AIR_SUMMARY.csv"
CHECKS=0

def check(ok,label):
    global CHECKS
    if not ok:raise AssertionError(label)
    CHECKS+=1

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()

def near(a,b,abs_tol=1e-8,rel_tol=1e-8):
    return math.isclose(a,b,rel_tol=rel_tol,abs_tol=abs_tol)

def independently_validate(row):
    t=float(row["Tout_C"]);rh=float(row["RH_out_assumed"]);eff=float(row["HRV_sensible_eff"])
    evap=float(row["evap_kg"])
    # Independent expression: saturation pressure in Pa, convert to kPa after Magnus.
    pv_out=(610.94*math.exp(17.625*t/(t+243.04)))*rh/1000
    pv_in=(610.94*math.exp(17.625*29/(29+243.04)))*.55/1000
    w_out=0.62198*pv_out/(101.325-pv_out)
    w_in=0.62198*pv_in/(101.325-pv_in)
    net=evap+3540*(w_out-w_in)
    dehum=max(net,0)
    humid=max(-net,0)
    sensible=max(0,3540*1.005*(29-t)/3600000)*(1-eff)
    elec=dehum*.5/1000
    latent=dehum*(2501-2.361*29)/3600000
    credit=min(sensible,.5*(latent+elec))
    external=sensible-credit
    return dict(w_indoor=w_in,w_outdoor=w_out,dehum_kg=dehum,
        humidification_kg=humid,vent_sensible_after_HRV_MWh=sensible,
        dehum_electric_MWh=elec,condensate_latent_MWh=latent,
        condenser_air_credit_MWh=credit,external_air_heat_MWh=external)

def detect_corruption(row):
    predicted=independently_validate(row)
    return (not near(float(row["dehum_kg"]),predicted["dehum_kg"],abs_tol=1e-6) or not near(float(row["humidification_kg"]),predicted["humidification_kg"],abs_tol=1e-6) or not near(float(row["w_outdoor"]),predicted["w_outdoor"],abs_tol=1e-8))

def run():
    m=json.loads(META.read_text(encoding="utf-8"))
    check(m["synthetic"] and not m["field_validated"] and not m["measured_weather"],"truth")
    check(not m["manufacturer_dehumidifier"] and m["source_signoffs_added"]==0,"signoffs")
    check(m["hourly_rows"]==78840 and m["scenarios"]==9,"shape")
    check(sha(DATA)==m["hourly_sha256"],"hourly SHA")
    check(sha(SUMMARY)==m["summary_sha256"],"summary SHA")
    agg=defaultdict(lambda:defaultdict(float))
    count=defaultdict(int)
    previous={}
    first=None
    with gzip.open(DATA,"rt",encoding="utf-8",newline="") as f:
        for row in csv.DictReader(f):
            if first is None:first=dict(row)
            name=row["scenario"]
            count[name]+=1
            vals={k:float(v) for k,v in row.items() if k not in ("scenario","time")}
            check(all(math.isfinite(v) for v in vals.values()),"finite")
            check(vals["evap_kg"]>=0 and vals["dehum_kg"]>=0 and vals["humidification_kg"]>=0,"nonnegative mass")
            check(vals["dehum_kg"]*vals["humidification_kg"]<1e-12,"exclusive moisture")
            check(abs(vals["moisture_residual_kg"])<1e-8,"moisture balance")
            check(near(vals["vent_sensible_after_HRV_MWh"],
                vals["condenser_air_credit_MWh"]+vals["external_air_heat_MWh"],abs_tol=3e-10),"air energy")
            check(vals["condenser_air_credit_MWh"]<=vals["vent_sensible_after_HRV_MWh"]+1e-10,"no overcredit")
            check(near(vals["dehum_electric_MWh"],vals["dehum_kg"]*.0005,abs_tol=2e-10),"electric units")
            check(near(vals["vent_sensible_raw_MWh"]*(1-vals["HRV_sensible_eff"]),
                vals["vent_sensible_after_HRV_MWh"],abs_tol=3e-10),"HRV units")
            expected=independently_validate(row)
            for key,val in expected.items():
                check(near(vals[key],val,abs_tol=1e-6,rel_tol=1e-8),"independent "+key)
            if name in previous:
                from datetime import datetime,timedelta
                check(datetime.fromisoformat(row["time"])-datetime.fromisoformat(previous[name])==timedelta(hours=1),"hourly sequence")
            previous[name]=row["time"]
            for key in ("evap_kg","dehum_kg","humidification_kg",
                "vent_sensible_raw_MWh","vent_sensible_after_HRV_MWh",
                "dehum_electric_MWh","condensate_latent_MWh",
                "condenser_air_credit_MWh","external_air_heat_MWh"):
                agg[name][key]+=vals[key]
    check(len(count)==9 and all(n==8760 for n in count.values()),"9 x 8760")
    with SUMMARY.open("r",encoding="utf-8",newline="") as f:summ=list(csv.DictReader(f))
    check(len(summ)==9,"summary rows")
    for s in summ:
        name=s["scenario"]
        check(name in count and int(s["hours"])==8760,"summary group")
        for key,val in agg[name].items():
            check(near(float(s[key]),val,abs_tol=1e-6,rel_tol=1e-9),"summary "+key)
    # Monotonic tests are scoped: sensible HRV lowers heat for fixed outdoor RH.
    for rh in (40,70,90):
        a=next(s for s in summ if s["scenario"]==f"RHout{rh}_HRV0")
        b=next(s for s in summ if s["scenario"]==f"RHout{rh}_HRV50")
        c=next(s for s in summ if s["scenario"]==f"RHout{rh}_HRV80")
        check(float(a["external_air_heat_MWh"])>=float(b["external_air_heat_MWh"])>=float(c["external_air_heat_MWh"]),"HRV monotonic")
        check(near(float(a["dehum_electric_MWh"]),float(c["dehum_electric_MWh"]),abs_tol=1e-7),"HRV moisture independence")
    check(not detect_corruption(first),"clean row passes")
    broken=dict(first);broken["dehum_kg"]=str(float(first["dehum_kg"])+10)
    check(detect_corruption(broken),"injected dehum corruption detected")
    broken2=dict(first);broken2["RH_out_assumed"]=str(float(first["RH_out_assumed"])+.3)
    check(detect_corruption(broken2),"injected RH corruption detected")
    result={"schema":"C100_INDEPENDENT_QA_V1","status":"PASS",
        "assertions":CHECKS,"rows_checked":sum(count.values()),"scenarios":len(count),
        "hourly_sha256":sha(DATA),"summary_sha256":sha(SUMMARY),
        "negative_dehum_detected":True,"negative_rh_detected":True,
        "caveat":"Synthetic assumptions; this QA validates arithmetic and accounting, not measured performance."}
    with (D/"C100_INDEPENDENT_QA.json").open("x",encoding="utf-8") as f:
        json.dump(result,f,indent=2,sort_keys=True);f.write("\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":run()
