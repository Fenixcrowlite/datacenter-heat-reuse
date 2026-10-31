"""Independent read-only QA of C90 output, without importing its model module."""
import csv, hashlib, json, math
from collections import defaultdict
from pathlib import Path

R=Path(__file__).resolve().parent
S=R.parent/"AUTONOMOUS_RUN_20261030_1254_DCHR_C88_NATIVE_MATLAB_REPLAY"/"Warm45_Storage100_v2_MATLAB_NATIVE.csv"
EXPECTED="07d1d7f19d92ce34d5b3e5a44a2131234a4a2e7991e21f018b197137ed0eb370"
checks={}
def check(label,condition):
    checks[label]=bool(condition)
    if not condition:
        raise AssertionError(label)

def digest(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

j=json.loads((R/"C90_POOL_SUMMARY.json").read_text(encoding="utf-8"))
hourly=list(csv.DictReader((R/"C90_POOL_HOURLY.csv").open(encoding="utf-8",newline="")))
monthly=list(csv.DictReader((R/"C90_POOL_MONTHLY.csv").open(encoding="utf-8",newline="")))
source=list(csv.DictReader(S.open(encoding="utf-8",newline="")))
sc=j["scenarios"]
check("pinned_native_source",digest(S)==EXPECTED==j["input_C88_sha256"])
check("8760_native_hours",len(source)==8760==j["input_hours"])
check("six_scenarios_52560_rows",len(sc)==6 and len(hourly)==6*8760)
check("72_monthly_rows",len(monthly)==72)
check("500m3_heat_capacity",abs(j["pool"]["heat_capacity_MWh_per_C"]-500*997*4.186/3_600_000)<1e-12)
check("all_scenarios_have_nonzero_pool_demand",all(v["pool_load_MWh"]>0 for v in sc.values()))
check("no_source_means_no_delivery",all(sc[n]["pool_delivered_MWh"]==0 for n in ("covered_no_extra",)))
check("source_fraction_coverage_monotone",sc["covered_no_extra"]["pool_energy_coverage_fraction"]<=sc["covered_25pct"]["pool_energy_coverage_fraction"]<=sc["covered_50pct"]["pool_energy_coverage_fraction"]<=sc["covered_100pct"]["pool_energy_coverage_fraction"]+1e-12)
check("night_cover_reduces_water_demand",sc["covered_50pct"]["pool_load_MWh"]<sc["uncovered_50pct"]["pool_load_MWh"])
check("dry_air_increases_evaporation_load",sc["covered_dry_air_50pct"]["pool_load_MWh"]>sc["covered_50pct"]["pool_load_MWh"])
check("all_hourly_heat_balances",all(abs(float(r["pool_load_MW"])-float(r["delivered_to_pool_MW"])-float(r["unmet_pool_MW"]))<2e-10 for r in hourly))
check("no_source_overdraw",all(float(r["potential_aux_HP_heat_MW"])*0.75<=float(r["HX_rejected_MW"])*float(r["recoverable_fraction"])+2e-10 for r in hourly))
check("delivery_bounded_by_potential",all(float(r["delivered_to_pool_MW"])<=float(r["potential_aux_HP_heat_MW"])+1e-10 for r in hourly))
check("no_negative_heating",all(min(float(r["pool_load_MW"]),float(r["unmet_pool_MW"]),float(r["delivered_to_pool_MW"]))>=-1e-10 for r in hourly))
hour_sum=defaultdict(float)
for row in hourly:
    hour_sum[row["scenario"]]+=float(row["pool_load_MW"])
check("hourly_annual_reconciliation",all(abs(hour_sum[k]-v["pool_load_MWh"])<0.000005 for k,v in sc.items()))
month_sum=defaultdict(float)
for row in monthly:
    month_sum[row["scenario"]]+=float(row["pool_load_MWh"])
check("monthly_annual_reconciliation",all(abs(month_sum[k]-v["pool_load_MWh"])<1e-7 for k,v in sc.items()))
check("ventilation_separate_from_pool",j["assumptions"]["air_ventilation_is_separate"] is True and all(v["air_ventilation_separate_MWh"]>0 for v in sc.values()))
check("no_field_validation_claim",j["validated_physical_coefficients"] is False and j["synthetic"] is True)
check("source_recoverability_disclaimer",j["assumptions"]["HX_Rejected_MW_is_counterfactual_not_proven_recoverable"] is True)
check("source_potential_electric_cap",all(float(r["potential_aux_HP_heat_MW"])<=0.30+1e-10 for r in hourly))
print(json.dumps({"qa":"PASS","checks":len(checks),"all_pass":all(checks.values()),"checks_detail":checks},indent=2))
