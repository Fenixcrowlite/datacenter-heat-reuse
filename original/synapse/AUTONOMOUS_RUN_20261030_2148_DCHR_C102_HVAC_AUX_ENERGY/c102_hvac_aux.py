"""C102 synthetic HVAC auxiliary electricity ledger; C100 remains immutable.
Fan, steam humidifier and sensible-only cooling; no latent cooling/field claims.
"""
import csv,gzip,hashlib,json,math,os
from pathlib import Path
from collections import defaultdict
D=Path(__file__).resolve().parent
R=D.parent
SCC=R.parent
SRC=R/"AUTONOMOUS_RUN_20261030_2052_DCHR_C100_POOL_AIR_HVAC"
DATA=SRC/"C100_AIR_HOURLY.csv.gz"
SOURCE_SHA="8ce8e04be652540eb635afb75958077c716220a26f3471526264985e0862fff4"
TASK="scc-2aab24704c2bd0"
FLOW_M3_H=3000.0
SFP_KW_PER_M3S=1.5
STEAM_KWH_PER_KG=0.75
COOLING_COP=3.0
AIR_C=29.0
DENSITY=1.18
CP=1.005
FLAGS=("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE")
FIELDS=("scenario","time","Tout_C","HRV_sensible_eff","dehum_electric_MWh",
        "humidification_kg","fan_electric_MWh","humidifier_electric_MWh",
        "sensible_cooling_MWh_th","cooling_electric_MWh",
        "total_HVAC_electric_MWh","external_air_heat_MWh_th")
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):h.update(chunk)
    return h.hexdigest()
def guard():
    for root in (D,R,SCC,Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")):
        for name in FLAGS:
            if (root/name).exists():raise RuntimeError("STOP_ACTIVE "+str(root/name))
def calc(row,sfp=SFP_KW_PER_M3S,steam=STEAM_KWH_PER_KG,cop=COOLING_COP):
    if not all(math.isfinite(v) and v>0 for v in (sfp,steam,cop)):
        raise ValueError("INVALID_ASSUMPTION")
    t=float(row["Tout_C"]);hrv=float(row["HRV_sensible_eff"])
    if not -50<t<80 or not 0<=hrv<=1:raise ValueError("INVALID_WEATHER_OR_HRV")
    dehum=float(row["dehum_electric_MWh"])
    humid=float(row["humidification_kg"])
    heat=float(row["external_air_heat_MWh"])
    if min(dehum,humid,heat)<0:raise ValueError("NEGATIVE_SOURCE")
    fan=(FLOW_M3_H/3600.0)*sfp/1000.0
    humid_e=humid*steam/1000.0
    cool_th=max(0.0,(t-AIR_C))*FLOW_M3_H*DENSITY*CP/3600000.0*(1-hrv)
    cool_e=cool_th/cop
    total=dehum+fan+humid_e+cool_e
    return (fan,humid_e,cool_th,cool_e,total)
def selftest():
    row={"Tout_C":"35","HRV_sensible_eff":"0.5","dehum_electric_MWh":"0.01",
         "humidification_kg":"10","external_air_heat_MWh":"0"}
    a=calc(row)
    assert math.isclose(a[0],0.00125,abs_tol=1e-12)
    assert math.isclose(a[1],0.0075,abs_tol=1e-12)
    assert a[2]>0 and math.isclose(a[3],a[2]/3,rel_tol=1e-12)
    assert math.isclose(a[4],0.01+a[0]+a[1]+a[3],rel_tol=1e-12)
    assert calc(dict(row,Tout_C="10"))[2]==0
    assert calc(dict(row,HRV_sensible_eff="0"))[2]>a[2]
    for bad in (0,-1,float("nan")):
        try:calc(row,sfp=bad)
        except ValueError:pass
        else:raise AssertionError("BAD_SFP_ACCEPTED")
    print("C102 SELFTEST 9/9 PASS")
def run():
    guard();selftest()
    if sha(DATA)!=SOURCE_SHA:raise RuntimeError("C100_SOURCE_SHA_DRIFT")
    hourly=D/"C102_AUX_HOURLY.csv.gz";tmp=D/"C102_AUX_HOURLY.partial.csv.gz"
    summary=D/"C102_AUX_SUMMARY.csv";meta=D/"C102_METADATA.json"
    if any(p.exists() for p in (hourly,tmp,summary,meta)):raise RuntimeError("OUTPUT_EXISTS")
    sums=defaultdict(lambda:defaultdict(float));count=defaultdict(int)
    with gzip.open(DATA,"rt",encoding="utf-8",newline="") as inp, gzip.open(tmp,"wt",encoding="utf-8",newline="",compresslevel=4) as outf:
        reader=csv.DictReader(inp);writer=csv.writer(outf);writer.writerow(FIELDS)
        for row in reader:
            n=sum(count.values())
            if n%720==0:guard()
            name=row["scenario"];count[name]+=1
            fan,humid_e,cool_th,cool_e,total=calc(row)
            vals=(float(row["dehum_electric_MWh"]),float(row["humidification_kg"]),fan,humid_e,cool_th,cool_e,total,float(row["external_air_heat_MWh"]))
            for key,val in zip(FIELDS[4:],vals):sums[name][key]+=val
            writer.writerow([name,row["time"],row["Tout_C"],row["HRV_sensible_eff"]]+[f"{v:.12f}" for v in vals])
    if len(count)!=9 or any(v!=8760 for v in count.values()):raise RuntimeError("ROW_COUNT_MISMATCH")
    guard();os.replace(tmp,hourly)
    with summary.open("x",encoding="utf-8",newline="") as f:
        w=csv.writer(f);w.writerow(["scenario","hours"]+list(FIELDS[4:]))
        for name in sorted(count):
            w.writerow([name,count[name]]+[f"{sums[name][key]:.9f}" for key in FIELDS[4:]])
    m={"schema":"C102_HVAC_AUX_V1","task_id":TASK,"synthetic":True,
       "field_validated":False,"source_signoffs_added":0,
       "source_C100_sha256":SOURCE_SHA,"rows":sum(count.values()),"scenarios":len(count),
       "hourly_sha256":sha(hourly),"summary_sha256":sha(summary),
       "assumptions":{"flow_m3_h":FLOW_M3_H,"SFP_kW_per_m3s":SFP_KW_PER_M3S,
       "steam_humidifier_kWh_per_kg":STEAM_KWH_PER_KG,"cooling_COP":COOLING_COP,
       "indoor_air_C":AIR_C,"dry_air_density_kg_m3":DENSITY,"cp_kJ_kgK":CP},
       "accounting":"Purchased HVAC electricity is dehumidifier + fan + steam humidifier + sensible-only cooling. External air heat is thermal, separate. Pool water evaporation latent heat is NOT added again. No dehumidifier condenser heat counted in cooling.",
       "exclusions":["latent cooling and reheat","HRV bypass/frost","supply/exhaust pressure and filters","pump power","humidifier heat interaction","actual measured humidity and airflow","manufacturer equipment curves"],
       "limitations":["Outdoor RH is scenario-constant, Tout synthetic from C88.","SFP/steam/COP are assumptions, not manufacturer specifications.","No full psychrometric energy balance or equipment sizing acceptance."]}
    with meta.open("x",encoding="utf-8") as f:json.dump(m,f,indent=2,sort_keys=True);f.write("\n")
    print(json.dumps({"rows":m["rows"],"hourly_sha256":m["hourly_sha256"],"summary_sha256":m["summary_sha256"],
      "anchor":{k:round(v,4) for k,v in sums["RHout70_HRV50"].items()}},indent=2))
if __name__=="__main__":
    import sys
    selftest() if "--selftest" in sys.argv else run()
