"""C92 output-only QA with C91 baseline reconciliation and dimension check."""
import hashlib,json,math
from pathlib import Path
D=Path(__file__).resolve().parent
C91=D.parent/"AUTONOMOUS_RUN_20261030_1553_DCHR_C91_POOL_DYNAMIC_THERMOSTAT"
a=json.loads((D/"C92_REFERENCE_COMPARISON.json").read_text(encoding="utf-8"))
b=json.loads((C91/"C91_DYNAMIC_SUMMARY.json").read_text(encoding="utf-8"))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks={}
def check(k,x):
    if not x:raise AssertionError(k)
    checks[k]="PASS"
check("schema",a["schema"]=="C92_ASHRAE_REFERENCE_SENSITIVITY_V1")
check("task_id",a["task_id"]=="scc-2aab24704c2bd0")
check("official_source",a["reference_url"].startswith("https://handbook.ashrae.org/"))
check("source_pin",a["source_input_sha256"]==b["source_C90_sha256"])
check("script_pin",a["source_C91_script_sha256"]==sha(C91/"c91_pool_dynamic.py"))
check("no_signoff",a["source_signoffs_added"]==0)
check("synthetic",a["synthetic"] is True and a["physical_field_validation"] is False)
check("air_speed_within_ASHRAE_range",0.05<=a["reference_velocity_m_s"]<=0.15)
K=3600*(0.089+0.0782*a["reference_velocity_m_s"])/(2501-2.361*28)
check("SI_dimension_conversion",abs(K-a["reference_coefficient_at_28C"])<1e-12)
check("unoccupied_activity",a["reference_activity_unoccupied"]==0.5)
check("public_activity",a["reference_activity_public_occupied"]==1.0)
check("reference_occupied_lower_than_C91",K<0.12*1.5)
check("reference_unoccupied_lower_than_C91",0.5*K<0.12)
check("cover_still_assumed",a["cover_multiplier_still_assumed"]==0.15)
s=a["simulations"]
check("four_scenarios",len(s)==4)
for pct in (10,25):
    c=s[f"C91_assumed_{pct}pct"]
    r=s[f"ASHRAE2023_reference_{pct}pct"]
    base=b["scenarios"][f"fraction_{pct}pct"]
    check(f"baseline_{pct}_HP_MWh",abs(c["HP_heat_MWh"]-base["HP_heat_MWh"])<1e-7)
    check(f"baseline_{pct}_min_C",abs(c["min_temp_C"]-base["min_temp_C"])<1e-9)
    check(f"reference_{pct}_lower_HP_heat",r["HP_heat_MWh"]<c["HP_heat_MWh"])
    check(f"reference_{pct}_no_worse_comfort",r["hours_below_27p5"]<=c["hours_below_27p5"])
    check(f"energy_balance_{pct}",max(c["max_abs_energy_residual_MWh"],r["max_abs_energy_residual_MWh"])<1e-11)
    check(f"source_split_{pct}",all(abs(v["HX_source_used_MWh"]-0.75*v["HP_heat_MWh"])<1e-7 for v in (c,r)))
check("reference_10pct_comfort",s["ASHRAE2023_reference_10pct"]["hours_below_27p5"]==0)
check("reference_25pct_comfort",s["ASHRAE2023_reference_25pct"]["hours_below_27p5"]==0)
out={"schema":"C92_INDEPENDENT_QA_V1","passed":len(checks),"checks":checks,
     "input_c91_summary_sha256":sha(C91/"C91_DYNAMIC_SUMMARY.json"),
     "reference_comparison_sha256":sha(D/"C92_REFERENCE_COMPARISON.json")}
with (D/"C92_INDEPENDENT_QA.json").open("x",encoding="utf-8") as f:
    json.dump(out,f,indent=2,sort_keys=True);f.write("\n")
print("C92 INDEPENDENT QA",len(checks),"/",len(checks),"PASS")
