"""Independent CSV-level C130 energy, COP, storage and continuity audit."""
from pathlib import Path
import csv,gzip,hashlib,json,math,copy
D=Path(__file__).resolve().parent
DATA=D/"C130_DYNAMIC_COP_BUFFER.csv.gz"
META=D/"C130_METADATA.json"
SUMMARY=D/"C130_SUMMARY.json"
def sha(p):return hashlib.file_digest(p.open("rb"),"sha256").hexdigest()
def close(a,b,tol=2e-7):return abs(a-b)<=tol
def verify(r,previous=None):
    f=lambda k:float(r[k])
    for k in ("COP","source_in_kJ","buffer_before_kJ","buffer_after_kJ",
              "source_spill_kJ","source_desired_kJ","source_ramped_kJ",
              "thermal_output_kJ","electric_kJ","recovered_kJ",
              "source_temp_C","sink_temp_C","pool_heat_kJ","air_heat_kJ",
              "source_cap_kJ","pool_residual_kJ","air_residual_kJ",
              "combined_residual_kJ","air_mass_residual_kg"):
        if not math.isfinite(f(k)):raise AssertionError("NONFINITE "+k)
    cop=max(1.5,min(6.5,.32*(f("sink_temp_C")+273.15)/
        (f("sink_temp_C")-f("source_temp_C"))))
    if not close(f("COP"),cop,1e-9):raise AssertionError("COP_CURVE")
    if f("COP")<=1 or f("source_temp_C")>=f("sink_temp_C"):raise AssertionError("TEMPERATURE")
    if not close(f("thermal_output_kJ"),f("electric_kJ")+f("recovered_kJ")):
        raise AssertionError("HEAT_PUMP_ENERGY")
    if not close(f("electric_kJ"),f("thermal_output_kJ")/f("COP")):
        raise AssertionError("ELECTRIC")
    if not close(f("thermal_output_kJ"),f("pool_heat_kJ")+f("air_heat_kJ")):
        raise AssertionError("DELIVERY")
    if not close(f("buffer_before_kJ")+f("source_in_kJ"),
                 f("recovered_kJ")+f("buffer_after_kJ")+f("source_spill_kJ")):
        raise AssertionError("SOURCE_ENERGY")
    if any(f(k)<-1e-7 for k in ("electric_kJ","recovered_kJ","source_in_kJ",
            "buffer_before_kJ","buffer_after_kJ","source_spill_kJ")):
        raise AssertionError("NEGATIVE")
    if f("thermal_output_kJ")>min(f("source_desired_kJ"),f("source_ramped_kJ"))+1e-7:
        raise AssertionError("OUTPUT_EXCEEDS_DEMAND")
    if f("source_desired_kJ")>f("source_cap_kJ")+1e-7:
        raise AssertionError("CAP_EXCEEDED")
    if f("buffer_after_kJ")>f("buffer_capacity_kWh")*3600000+1e-7:
        raise AssertionError("BUFFER_CAPACITY")
    if previous is not None:
        if not close(f("buffer_before_kJ"),float(previous["buffer_after_kJ"])):
            raise AssertionError("BUFFER_CONTINUITY")
        if not close(f("pool_T0"),float(previous["pool_T1"])):
            raise AssertionError("POOL_CONTINUITY")
        if not close(f("air_T0"),float(previous["air_T1"])):
            raise AssertionError("AIR_CONTINUITY")
    if max(abs(f(k)) for k in ("pool_residual_kJ","air_residual_kJ",
            "combined_residual_kJ","air_mass_residual_kg"))>1e-5:
        raise AssertionError("STATE_BALANCE")
    return True
def negative_controls(row):
    changes=[
        ("COP","0.5"),("electric_kJ","0"),("recovered_kJ","0"),
        ("source_in_kJ","-5"),("buffer_after_kJ","-1"),
        ("source_desired_kJ","0"),("source_cap_kJ","0"),
        ("buffer_capacity_kWh","-1"),("pool_heat_kJ","-100"),
    ]
    passed=0
    for key,val in changes:
        altered=dict(row)
        # Avoid a no-op mutation on a genuine zero-valued field.
        if altered[key]==val:val="999999999"
        altered[key]=val
        try:verify(altered)
        except (AssertionError,ZeroDivisionError,ValueError):passed+=1
        else:raise AssertionError("NEGATIVE_CONTROL_NOT_CAUGHT "+key)
    return passed
def main():
    meta=json.loads(META.read_text(encoding="utf-8"))
    summary=json.loads(SUMMARY.read_text(encoding="utf-8"))
    if meta["data_sha256"]!=sha(DATA):raise AssertionError("DATA_SHA")
    if meta["summary_sha256"]!=sha(SUMMARY):raise AssertionError("SUMMARY_SHA")
    seen={};counts={};sums={};first=None;last={}
    with gzip.open(DATA,"rt",encoding="utf-8",newline="") as f:
        for r in csv.DictReader(f):
            name=r["scenario"]
            if name not in summary:raise AssertionError("UNEXPECTED_SCENARIO")
            if first is None and float(r["electric_kJ"])>1 and float(r["source_desired_kJ"])>1:first=dict(r)
            verify(r,last.get(name))
            last[name]=r
            counts[name]=counts.get(name,0)+1
            a=sums.setdefault(name,{"source_in_MWh":0.,"buffer_spill_MWh":0.,
               "electric_MWh":0.,"recovered_MWh":0.,"thermal_MWh":0.,
               "pool_MWh":0.,"air_MWh":0.,"RH_above65_quarters":0.,
               "source_limited_quarters":0.})
            for k,field in (("source_in_MWh","source_in_kJ"),
                            ("buffer_spill_MWh","source_spill_kJ"),
                            ("electric_MWh","electric_kJ"),
                            ("recovered_MWh","recovered_kJ"),
                            ("thermal_MWh","thermal_output_kJ"),
                            ("pool_MWh","pool_heat_kJ"),("air_MWh","air_heat_kJ")):
                a[k]+=float(r[field])/3600000.
            a["RH_above65_quarters"]+=int(float(r["RH1"])>.65)
            a["source_limited_quarters"]+=int(float(r["thermal_output_kJ"])+1e-7<float(r["source_ramped_kJ"]))
    if len(counts)!=6 or sum(counts.values())!=4032:raise AssertionError("ROW_COUNT")
    for name,n in counts.items():
        if n!=672:raise AssertionError("SCENARIO_LENGTH")
        for k,v in sums[name].items():
            if not close(v,summary[name][k],2e-7):
                raise AssertionError("SUMMARY_MISMATCH "+name+" "+k)
        if not close(float(last[name]["buffer_after_kJ"])/3600000,
                     summary[name]["final_buffer_kWh"]):raise AssertionError("FINAL_BUFFER")
    negatives=negative_controls(first)
    result={"status":"PASS","independent":True,"rows":sum(counts.values()),
            "scenarios":len(counts),"negative_controls":negatives,
            "data_sha256":sha(DATA),"summary_sha256":sha(SUMMARY),
            "checks":"COP(T), thermal=electric+recovered, buffer conservation, source cap, "
                     "state balance, per-scenario continuity, recomputed summaries"}
    out=D/"C130_INDEPENDENT_QA.json"
    if out.exists():raise RuntimeError("OUTPUT_EXISTS")
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
