"""Independent C124 CSV conservation, continuity and physical state QA."""
import csv,gzip,hashlib,json,math,sys,datetime
from pathlib import Path
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D))
import c124_air_enthalpy as m
p=D/"C124_QUARTER_AIR.csv.gz";meta=json.loads((D/"C124_METADATA.json").read_text())
assert m.sha(p)==meta["data_sha256"]
state={};counts={};total=0;max_mass=0.;max_energy=0.;saturated=0
with gzip.open(p,"rt",encoding="utf-8",newline="") as f:
    for r in csv.DictReader(f):
        key=r["scenario"];n=int(r["quarter"]);counts[key]=counts.get(key,0)+1;total+=1
        vals={k:float(v) for k,v in r.items() if k not in ("scenario","time","quarter")}
        if key in state:
            prev=state[key]
            assert abs(prev[0]-vals["T0_C"])<1e-9
            assert abs(prev[1]-vals["w0"])<1e-9
            assert n==(prev[2]+1)%4
            if n==0:assert datetime.datetime.fromisoformat(r["time"])==datetime.datetime.fromisoformat(prev[3])+datetime.timedelta(hours=1)
            else:assert r["time"]==prev[3]
        state[key]=(vals["T1_C"],vals["w1"],n,r["time"])
        mass=vals["storage_kg"]-(vals["evap_kg"]+vals["vent_vapor_kg"]-vals["dehum_kg"]+vals["humid_kg"]-vals["condensate_kg"])
        energy=vals["H1_kJ"]-(vals["H0_kJ"]+vals["evap_kJ"]+vals["vent_kJ"]+vals["HVAC_kJ"]-vals["dehum_out_kJ"]+vals["humid_in_kJ"]-vals["condensate_out_kJ"])
        assert abs(mass)<1e-7 and abs(energy)<2e-5
        assert abs(m.H(vals["T0_C"],m.M*vals["w0"])-vals["H0_kJ"])<2e-5
        assert abs(m.H(vals["T1_C"],m.M*vals["w1"])-vals["H1_kJ"])<2e-5
        assert abs(m.rh_from(vals["T1_C"],vals["w1"])-vals["RH1"])<1e-9
        assert 0<=vals["RH1"]<=1+1e-8 and -20<vals["T1_C"]<70
        assert 0<=vals["dehum_kg"]<=45.66*.25+1e-9
        assert 0<=vals["humid_kg"]<=45.66*.25+1e-9
        if vals["condensate_kg"]>0:saturated+=1
        max_mass=max(max_mass,abs(mass));max_energy=max(max_energy,abs(energy))
assert total==140160 and len(counts)==4 and all(n==35040 for n in counts.values())
negative=0
for kw in ({"evap":-1},{"evap":float("nan")},{"cap":-1},{"heat":-1}):
    args={"t":29,"w":m.w_from(29,.55),"tw":28,"evap":1,"cap_kg_h":5,"heat_cap_kw":5}
    if "evap" in kw:args["evap"]=kw["evap"]
    if "cap" in kw:args["cap_kg_h"]=kw["cap"]
    if "heat" in kw:args["heat_cap_kw"]=kw["heat"]
    try:m.step(**args)
    except ValueError:negative+=1
    else:raise AssertionError("NEGATIVE_NOT_REJECTED")
assert negative==4
out={"status":"PASS","rows":total,"scenarios":len(counts),"negative_controls":negative,
     "max_mass_residual_kg":max_mass,"max_energy_residual_kJ":max_energy,
     "saturated_quarters":saturated,"data_sha256":m.sha(p)}
(D/"C124_INDEPENDENT_QA.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out))
