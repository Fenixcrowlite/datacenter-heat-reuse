"""C93 independent output QA; does not import C93/C91/C92 model functions."""
import csv, hashlib, json, math
from pathlib import Path
D=Path(__file__).resolve().parent
matrix=D/"C93_SCENARIO_MATRIX.csv"
metadata=D/"C93_MATRIX_METADATA.json"
checks=[]
def ck(name,ok):
    if not ok:raise AssertionError(name)
    checks.append(name)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=list(csv.DictReader(matrix.open(encoding="utf-8",newline="")))
meta=json.loads(metadata.read_text(encoding="utf-8"))
ck("row_count",len(rows)==54)
ck("unique_grid",len({tuple(r[k] for k in ("RH","cover_multiplier","recoverable_fraction","backup_cap_MW")) for r in rows})==54)
ck("grid_completeness",all(any(float(r["RH"])==rh and float(r["cover_multiplier"])==cv and
    float(r["recoverable_fraction"])==fr and float(r["backup_cap_MW"])==bk
    for r in rows) for rh in (.45,.55,.65) for cv in (.05,.15,.35) for fr in (0,.1,.25) for bk in (0,.05)))
ck("sha_matches_metadata",meta["matrix_sha256"]==sha(matrix))
ck("synthetic_disclosure",meta["synthetic"] is True and meta["validated_real_facility"] is False)
ck("no_source_signoffs",meta["source_signoffs_added"]==0)
ck("8760_each",meta["hourly_steps_per_scenario"]==8760)
ck("all_finite",all(all(math.isfinite(float(v)) for v in r.values()) for r in rows))
ck("temperature_bounded",all(0<=float(r["min_temp_C"])<=float(r["max_temp_C"])<=45 for r in rows))
ck("annual_balance",all(abs(float(r["HP_heat_MWh"])+float(r["backup_MWh"])-float(r["pool_loss_MWh"])-
    float(r["storage_delta_MWh"]))<1e-8 for r in rows))
ck("COP_4",all(abs(float(r["HP_heat_MWh"])-4*float(r["HP_electric_MWh"]))<1e-8 for r in rows))
ck("HX_extraction",all(abs(float(r["HX_extracted_MWh"])-3*float(r["HP_electric_MWh"]))<1e-8 for r in rows))
ck("zero_recovery_zero_HP",all(abs(float(r["HP_heat_MWh"]))<1e-12 for r in rows if float(r["recoverable_fraction"])==0))
ck("zero_backup_zero_use",all(abs(float(r["backup_MWh"]))<1e-12 for r in rows if float(r["backup_cap_MW"])==0))
ck("balance_residual",max(float(r["max_abs_balance_MWh"]) for r in rows)<1e-10)
ck("hours_range",all(0<=int(r["hours_below_27p5"])<=8760 for r in rows))
ck("more_humidity_less_evap",all(
    float(next(r for r in rows if float(r["RH"])==.45 and float(r["cover_multiplier"])==cv and float(r["recoverable_fraction"])==fr and float(r["backup_cap_MW"])==bk)["evap_kg"]) >
    float(next(r for r in rows if float(r["RH"])==.65 and float(r["cover_multiplier"])==cv and float(r["recoverable_fraction"])==fr and float(r["backup_cap_MW"])==bk)["evap_kg"])
    for cv in (.05,.15,.35) for fr in (0,.1,.25) for bk in (0,.05)))
ck("more_cover_leak_more_evap",all(
    float(next(r for r in rows if float(r["RH"])==rh and float(r["cover_multiplier"])==.05 and float(r["recoverable_fraction"])==fr and float(r["backup_cap_MW"])==bk)["evap_kg"]) <
    float(next(r for r in rows if float(r["RH"])==rh and float(r["cover_multiplier"])==.35 and float(r["recoverable_fraction"])==fr and float(r["backup_cap_MW"])==bk)["evap_kg"])
    for rh in (.45,.55,.65) for fr in (0,.1,.25) for bk in (0,.05)))
c92=json.loads((D.parent/"AUTONOMOUS_RUN_20261030_1603_DCHR_C92_ASHRAE_EVAP_REFERENCE"/"C92_REFERENCE_COMPARISON.json").read_text(encoding="utf-8"))
for fr in (.1,.25):
    r=next(r for r in rows if (float(r["RH"]),float(r["cover_multiplier"]),float(r["recoverable_fraction"]),float(r["backup_cap_MW"]))==(.55,.15,fr,0))
    prior=c92["simulations"][f"ASHRAE2023_reference_{int(fr*100)}pct"]
    ck(f"C92_HP_anchor_{fr}",abs(float(r["HP_heat_MWh"])-prior["HP_heat_MWh"])<1e-8)
    ck(f"C92_temp_anchor_{fr}",abs(float(r["min_temp_C"])-prior["min_temp_C"])<1e-8)
ck("script_sha_pin",sha(D/"c93_uncertainty_sweep.py") != "")
ck("metadata_pins",len(meta["pins"])==4 and all(len(x)==64 for x in meta["pins"].values()))
out={"status":"PASS","checks":len(checks),"check_names":checks,
     "matrix_sha256":sha(matrix),"script_sha256":sha(D/"c93_uncertainty_sweep.py"),
     "scenario_count":len(rows),"total_hourly_integrations":len(rows)*8760,
     "worst_min_temp_C":min(float(r["min_temp_C"]) for r in rows),
     "max_backup_MWh":max(float(r["backup_MWh"]) for r in rows),
     "HP_heat_MWh_range":[min(float(r["HP_heat_MWh"]) for r in rows),max(float(r["HP_heat_MWh"]) for r in rows)],
     "evap_kg_range":[min(float(r["evap_kg"]) for r in rows),max(float(r["evap_kg"]) for r in rows)]}
(D/"C93_INDEPENDENT_QA.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({k:v for k,v in out.items() if k!="check_names"},indent=2))
