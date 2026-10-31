# -*- coding: utf-8 -*-
"""Independent IT cooling heat rejection, N+1 and pump/thermal buffer study.
This is a numerical SCREENING using existing verified Simulink output; no hardware certification.
"""
from pathlib import Path
import csv,json,math,statistics
ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parent.parent
SOURCE=PROJECT/"calibration"/"closed_loop_simulink_20261023"/"direct_35_8760h.csv"
RHO=997.0;CP=4182.0
def flow_m3h(qmw,dK):
    return qmw*1e6*3600/(RHO*CP*dK)
def buffer_volume_m3(deficit_MW,delay_s,usable_dT_K):
    return deficit_MW*1e6*delay_s/(RHO*CP*usable_dT_K)
def headers(q_m3h,v_ms=2.0):
    return 1000*math.sqrt(4*(q_m3h/3600)/(math.pi*v_ms))
def hydro(q,delta,velocity=2.0):
    f=flow_m3h(q,delta)
    return {"heat_MW":q,"water_dT_K":delta,"volume_flow_m3h":round(f,2),
            "inside_diameter_mm_at_velocity":round(headers(f,velocity),1),
            "velocity_assumed_ms":velocity,
            "status":"preliminary fluid sizing, no glycol viscosity or pressure losses"}
def collect():
    n=0; recovered=0; rejected=0; eIT=0; maxIT=0
    full_loss_delta=0; qdump_p95=[]
    with SOURCE.open(encoding="utf-8-sig",newline="") as f:
        for row in csv.DictReader(f):
            n+=1
            avail=float(row["DCAvailable_MW"])
            used=float(row["DCtoPool_MW"])+float(row["DCtoDistrict_MW"])
            it=avail/.85
            qdump=it-used
            assert qdump>=-1e-8 and used<=avail+1e-8
            maxIT=max(it,maxIT)
            eIT+=it/12;recovered+=used/12
            rejected+=qdump/12
            if n%12==0:qdump_p95.append(qdump)
    assert n==105120 and abs(eIT-recovered-rejected)<1e-5
    qdump_p95.sort()
    return {"rows":n,"E_IT_heat_MWh":round(eIT,3),
            "E_reused_source_MWh":round(recovered,3),
            "E_rejected_MWh":round(rejected,3),
            "mean_rejection_MW":round(rejected/8760,4),
            "max_IT_heat_MW":round(maxIT,4),
            "rejection_annual_p95_MW":round(qdump_p95[int(.95*(len(qdump_p95)-1))],4),
            "all_heat_reuse_stopped_required_cooler_MW_design":10,
            "source":"direct_35_8760h.csv actual 105120 Simulink output, IT inferred from availability /0.85"}
def coolers():
    # No manufacturer or ambient correction yet. All capacity values are effective net MW.
    cases=[]
    for unit_count in (5,6,7,8):
        for derate in (0,0.10,0.20):
            useful=2*(1-derate)
            after1=(unit_count-1)*useful
            max_supported=min(10,after1)
            shortfall=max(0,10-after1)
            cases.append({"installed_units":unit_count,
             "thermal_nominal_per_unit_MW":2,"design_ambient_derating_fraction":derate,
             "capacity_after_any_one_outage_MW":round(after1,3),
             "full_IT_10MW_survives_single_failure_after_failover":after1>=10-1e-9,
             "remaining_deficit_MW":round(shortfall,3),
             "efficiency_and_vendor_data":"not known; hypothetical net capacity after ambient derate"})
    return cases
def transients():
    events=[]
    # fixed critical IT rejection demand is 10 MW: maximum conservative full-load design.
    for missing in (2,10):
        for delay in (10,30,60,300,900):
            q=missing*delay/3600
            events.append({"cooling_shortage_MW":missing,"full_failover_delay_s":delay,
             "shortage_energy_kWh":round(q*1000,3),
             "buffer_5K_m3":round(buffer_volume_m3(missing,delay,5),3),
             "buffer_2K_m3":round(buffer_volume_m3(missing,delay,2),3),
             "contingency":"THERMAL only; storage does not preserve flow without separate UPS pumps"})
    return events
def write(name,data):
    path=ROOT/name
    if path.exists():raise FileExistsError(str(path))
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
def main():
    profile=collect()
    c=coolers();e=transients()
    hydraulics=[{"circuit":"IT_FULL_LOAD_10MW_5K",**hydro(10,5)},
      {"circuit":"RECOVERY_FULL_IT_85PCT_5K",**hydro(8.5,5)},
      {"circuit":"POOL_PRIMARY_150KW_3K",**hydro(.15,3)},
      {"circuit":"POOL_SECONDARY_150KW_2K",**hydro(.15,2)},
      {"circuit":"DH_10MW_20K",**hydro(10,20)},
      {"circuit":"DH_10MW_10K",**hydro(10,10)}]
    full={"study":"N+1 independent rejection of full rated IT heat, separate from heat recovery",
          "evidence_class":"engineering simulation D + model original baseline",
          "profile":profile,"cooling_modules_n_plus_1":c,"thermal_bridge_transients":e,
          "hydraulic":hydraulics,
          "selection":"At zero derating, 6x2 MW units withstand one unit outage. At 10% derating, 7x2 MW units required to retain >=10MW after one outage.",
          "failure_isolation":["heat reuse network stops -> fallback rejects all IT heat",
                               "pool heating disabled -> IT cooling independent",
                               "loss of main electrical supply -> UPS-supported pumps + alternative power generator need site design",
                               "one cooler fails -> second path N+1 with independent valves/headers",
                               "loss of 50% coolant flow -> thermal volume DOES NOT ensure chip flow",
                               "instrument failure -> hardware thermal limit and independent alarms"],
          "unverified":["real IT 10 MW peak meter data and mix of air/liquid loads",
                        "cooler manufacturer capacity at design maximum ambient air temperature",
                        "UPS runtime and power draw, piping layout, valves, coolant chemistry",
                        "hardware transient response and functional safety classification",
                        "cooling PUE overhead, fan and pump CAPEX, exact utility connection"]}
    write("independent_cooling_design_scenarios.json",full)
    with (ROOT/"cooling_failover_sensitivity.csv").open("x",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=list(e[0]));w.writeheader();w.writerows(e)
    with (ROOT/"cooling_nplus1_derating.csv").open("x",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=list(c[0]));w.writeheader();w.writerows(c)
    with (ROOT/"hydraulic_capacity_table.csv").open("x",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=list(hydraulics[0]));w.writeheader();w.writerows(hydraulics)
    assert next(x for x in c if x["installed_units"]==6 and x["design_ambient_derating_fraction"]==0)["full_IT_10MW_survives_single_failure_after_failover"]
    assert not next(x for x in c if x["installed_units"]==6 and x["design_ambient_derating_fraction"]==.10)["full_IT_10MW_survives_single_failure_after_failover"]
    assert next(x for x in c if x["installed_units"]==7 and x["design_ambient_derating_fraction"]==.10)["full_IT_10MW_survives_single_failure_after_failover"]
    print("INDEPENDENT_COOLING_VERIFIED",json.dumps({"profile":profile,
         "30sec_2MW_5K_buffer_m3":round(buffer_volume_m3(2,30,5),3),
         "300sec_2MW_5K_buffer_m3":round(buffer_volume_m3(2,300,5),3)},ensure_ascii=False))
if __name__=="__main__":main()
