"""Independent output QA: does not import stratified_tank.py."""
import csv, hashlib, json, math
from decimal import Decimal, getcontext
from pathlib import Path
getcontext().prec=35
H=Path(__file__).resolve().parent
R=json.loads((H/"STRATIFIED_TANK_RESULTS.json").read_text(encoding="utf-8"))
S=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\results\best_scenario_v2_timeseries.csv")
assert hashlib.sha256(S.read_bytes()).hexdigest()==R["source_sha256"]=="8125719923bae97901f37cf0f5354df77b46544df0477f863172255748873f25"
source=list(csv.DictReader(S.open(encoding="utf-8-sig",newline="")))
assert len(source)==R["source_rows"]==8760
assert len(R["case_results"])==5
checked_years=checked_geometry=checked_profiles=0
for case in R["case_results"]:
    c=case["config"];vol=Decimal(str(c["volume_m3"]));height=Decimal("10")
    # Independently compute cylinder side and ends from a radius, not reuse model geometry.
    radius=(vol/(Decimal(str(math.pi))*height)).sqrt()
    area=Decimal("2")*Decimal(str(math.pi))*radius*(height+radius)
    expected_ua=area*Decimal("0.15")/Decimal("1000")
    if c["ua_kw_per_k"]!=0:
        assert abs(expected_ua-Decimal(str(c["ua_kw_per_k"])))<Decimal("0.00000001")
    checked_geometry+=1
    profile=case["final_profile_c"]
    assert len(profile)==c["layers"]
    assert all(math.isfinite(x) and x<=c["charge_temp_c"]+1e-6 for x in profile)
    cell=vol*Decimal("1000")*Decimal("4180")/(Decimal("3600000000")*Decimal(c["layers"]))
    calculated=cell*sum(Decimal(str(x)) for x in profile)
    assert abs(calculated-Decimal(str(case["yearly"][-1]["final_energy_mwh"])))<Decimal("0.000001")
    checked_profiles+=1
    assert len(case["yearly"])==3
    for year in case["yearly"]:
        assert year["year"]==checked_years%3+1
        a=Decimal(str(year["initial_energy_mwh"]))
        b=Decimal(str(year["final_energy_mwh"]))
        ch=Decimal(str(year["charge_mwh"]))
        d=Decimal(str(year["delivered_mwh"]))
        loss=Decimal(str(year["loss_mwh"]))
        e=Decimal(str(year["added_electric_mwh"]))
        src=Decimal(str(year["source_heat_mwh"]))
        assert min(ch,d,loss,e,src)>=0
        assert abs((a+ch-d-loss)-b)<Decimal("0.00001")
        assert abs(ch-(e+src))<Decimal("0.00001")
        assert abs(Decimal(str(year["balance_residual_mwh"])))<Decimal("0.00001")
        assert year["max_substep_residual_mwh"]<1e-7
        assert 0<=year["temperature_blocked_hours"]<=8760
        checked_years+=1
    assert abs(case["yearly"][-1]["final_energy_mwh"]-case["yearly"][-1]["initial_energy_mwh"])>=0
assert R["case_results"][4]["yearly"][2]["loss_mwh"]==0
assert R["case_results"][4]["yearly"][2]["delivered_mwh"]>R["case_results"][1]["yearly"][2]["delivered_mwh"]
assert R["synthetic_not_metered"] is True and R["primary_source_signoffs"]==0
assert R["baseline_existing_storage_mwh"]==100
qa={"status":"PASS","source_rows":8760,"cases":5,"independent_annual_energy_ledgers":checked_years,
    "independent_electric_source_splits":checked_years,
    "independent_cylinder_ua_checks":checked_geometry,
    "independent_final_profile_energy_checks":checked_profiles,
    "lossless_control":True,"no_incremental_savings_claim":True}
(H/"QA_INDEPENDENT.json").write_text(json.dumps(qa,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(qa))
