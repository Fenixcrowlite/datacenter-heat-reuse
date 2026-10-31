"""Independent row-by-row C102 accounting QA, no model import."""
import csv,gzip,hashlib,json,math
from collections import defaultdict
from pathlib import Path
D=Path(__file__).resolve().parent
S=D.parent/"AUTONOMOUS_RUN_20261030_2052_DCHR_C100_POOL_AIR_HVAC"/"C100_AIR_HOURLY.csv.gz"
O=D/"C102_AUX_HOURLY.csv.gz"
SUMMARY=D/"C102_AUX_SUMMARY.csv"
META=D/"C102_METADATA.json"
N=0
def check(ok,label):
    global N
    if not ok:raise AssertionError(label)
    N+=1
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()
def near(a,b,tol=3e-9):return math.isclose(a,b,rel_tol=1e-8,abs_tol=tol)
def predicted(a):
    t=float(a["Tout_C"]);e=float(a["HRV_sensible_eff"])
    d=float(a["dehum_electric_MWh"]);m=float(a["humidification_kg"])
    fan=(3000/3600)*1.5/1000
    steam=m*.75/1000
    cool=max(0,t-29)*3000*1.18*1.005/3600000*(1-e)
    return dict(fan_electric_MWh=fan,humidifier_electric_MWh=steam,
      sensible_cooling_MWh_th=cool,cooling_electric_MWh=cool/3,
      total_HVAC_electric_MWh=d+fan+steam+cool/3)
def run():
    m=json.loads(META.read_text(encoding="utf-8"))
    check(m["synthetic"] and not m["field_validated"] and m["source_signoffs_added"]==0,"truth")
    check(m["rows"]==78840 and m["scenarios"]==9,"shape")
    check(sha(S)==m["source_C100_sha256"],"source sha")
    check(sha(O)==m["hourly_sha256"],"output sha")
    check(sha(SUMMARY)==m["summary_sha256"],"summary sha")
    count=defaultdict(int);tot=defaultdict(lambda:defaultdict(float));max_t=-1e6;hot=0;first=None
    with gzip.open(S,"rt",encoding="utf-8",newline="") as sf, gzip.open(O,"rt",encoding="utf-8",newline="") as of:
        for a,b in zip(csv.DictReader(sf),csv.DictReader(of),strict=True):
            if first is None:first=dict(b)
            check(a["scenario"]==b["scenario"] and a["time"]==b["time"],"row key")
            check(a["Tout_C"]==b["Tout_C"] and a["HRV_sensible_eff"]==b["HRV_sensible_eff"],"input preserved")
            check(near(float(a["external_air_heat_MWh"]),float(b["external_air_heat_MWh_th"])),"thermal preserved")
            check(near(float(a["dehum_electric_MWh"]),float(b["dehum_electric_MWh"])),"dehum preserved")
            check(near(float(a["humidification_kg"]),float(b["humidification_kg"])),"humid mass preserved")
            expected=predicted(a)
            for k,v in expected.items():check(near(float(b[k]),v),"independent "+k)
            check(all(float(b[k])>=-1e-12 for k in expected),"nonnegative")
            check(near(float(b["total_HVAC_electric_MWh"]),sum(float(b[k]) for k in ("dehum_electric_MWh","fan_electric_MWh","humidifier_electric_MWh","cooling_electric_MWh"))),"electric sum")
            check(not(float(b["sensible_cooling_MWh_th"])>1e-10 and float(a["vent_sensible_raw_MWh"])>1e-10),"no heat+cool overlap")
            name=b["scenario"];count[name]+=1
            for k in ("dehum_electric_MWh","humidification_kg","fan_electric_MWh","humidifier_electric_MWh","sensible_cooling_MWh_th","cooling_electric_MWh","total_HVAC_electric_MWh","external_air_heat_MWh_th"):
                tot[name][k]+=float(b[k])
            max_t=max(max_t,float(a["Tout_C"]));hot+=int(float(a["Tout_C"])>29)
    check(len(count)==9 and all(v==8760 for v in count.values()),"scenario hours")
    with SUMMARY.open("r",encoding="utf-8",newline="") as f:
        rows=list(csv.DictReader(f))
    check(len(rows)==9,"summary count")
    for r in rows:
        check(int(r["hours"])==8760,"hours")
        for k,v in tot[r["scenario"]].items():check(near(float(r[k]),v,tol=2e-6),"annual total")
    check(hot==0 and max_t<29,"cooling annual not exercised")
    # Inject a hot day as an independent positive cooling control.
    hot_row={"Tout_C":"35","HRV_sensible_eff":"0.5","dehum_electric_MWh":"0","humidification_kg":"0"}
    q=predicted(hot_row)
    check(q["sensible_cooling_MWh_th"]>0 and near(q["cooling_electric_MWh"],q["sensible_cooling_MWh_th"]/3),"hot-hour positive")
    q0=predicted(dict(hot_row,HRV_sensible_eff="0"))
    check(q0["sensible_cooling_MWh_th"]>q["sensible_cooling_MWh_th"],"HRV cooling sensitivity")
    bad=dict(first);bad["fan_electric_MWh"]=str(float(first["fan_electric_MWh"])+0.01)
    check(not near(float(bad["fan_electric_MWh"]),predicted(bad)["fan_electric_MWh"]),"injected fan corruption")
    bad2=dict(first);bad2["total_HVAC_electric_MWh"]=str(float(first["total_HVAC_electric_MWh"])+1)
    check(not near(float(bad2["total_HVAC_electric_MWh"]),predicted(bad2)["total_HVAC_electric_MWh"]),"injected total corruption")
    result={"schema":"C102_INDEPENDENT_QA_V1","status":"PASS","assertions":N,
      "rows_checked":sum(count.values()),"scenarios":len(count),"max_outdoor_C":max_t,
      "annual_hours_above_29C":hot,"cooling_branch_annual_exercised":False,
      "hot_hour_control":True,"corruption_controls":2,
      "hourly_sha256":sha(O),"summary_sha256":sha(SUMMARY),
      "caveat":"Validates synthetic arithmetic and no-double-counting conventions, not HVAC physical performance."}
    with (D/"C102_INDEPENDENT_QA.json").open("x",encoding="utf-8") as f:json.dump(result,f,indent=2,sort_keys=True);f.write("\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":run()
