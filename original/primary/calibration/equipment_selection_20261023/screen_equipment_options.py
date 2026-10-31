# -*- coding: utf-8 -*-
"""Preliminary equipment-selection calculations. Equipment price ranges are budgets, NOT vendor offers.
Source scenarios: verified Simulink 2025 closed-loop; product envelopes from manufacturer
brochures, representative reference installed cost ranges from research.
"""
from __future__ import annotations
import argparse,csv,json,math,statistics
from pathlib import Path
from typing import Optional
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
SLX=ROOT/"calibration"/"closed_loop_simulink_20261023"
P200=ROOT/"calibration"/"coupled_dispatch_20261023"
CP=4182.0;RHO=997.0
def raw(path):return json.loads(Path(path).read_text(encoding="utf-8"))
def num(v):return round(float(v),3)
def flow_m3h(q_kW,dK):
    if q_kW<=0 or dK<=0:raise ValueError("heat and deltaT must be positive")
    return q_kW*1000*3600/(RHO*CP*dK)
def lmtd(hi,ho,ci,co):
    # Counterflow: hot-in vs cold-out, hot-out vs cold-in.
    a=hi-co;b=ho-ci
    if min(a,b)<=0:return None
    if abs(a-b)<1e-10:return a
    return (a-b)/math.log(a/b)
def hx(qkW,sourceIn,sourceDrop,poolReturn,poolRise,u_w_m2k=1500,fouling=1.25):
    ho=sourceIn-sourceDrop;co=poolReturn+poolRise
    L=lmtd(sourceIn,ho,poolReturn,co)
    result={"source_in_C":sourceIn,"source_out_C":ho,
            "pool_return_C":poolReturn,"pool_supply_C":co,
            "Q_design_kW":qkW,
            "hot_flow_m3h":flow_m3h(qkW,sourceDrop),
            "pool_flow_m3h":flow_m3h(qkW,poolRise),
            "lmtd_K":None if L is None else num(L),
            "U_assumed_W_m2K":u_w_m2k,
            "fouling_area_factor":fouling,
            "thermal_feasible":L is not None}
    if L is None:
        result.update({"UA_clean_kW_K":None,"UA_design_kW_K":None,
                        "transfer_area_m2":None})
    else:
        result.update({"UA_clean_kW_K":num(qkW/L),
                       "UA_design_kW_K":num(qkW/L*fouling),
                       "transfer_area_m2":num(1000*qkW/L*fouling/u_w_m2k)})
    return result
def motor_kw(flow_m3h,head_kpa,eta):
    return flow_m3h/3600*head_kpa/eta # since 1kPa*m3/s =1kW.
def npv(capex,net_annual,discount=0.06,life=20):
    af=(1-(1+discount)**(-life))/discount
    return -capex+net_annual*af
def annualized(capex,r=0.06,n=20):
    return capex*r/(1-(1+r)**(-n))
def choose_price_budget(sav,flow_primary,flow_pool,p_primary_kpa,p_pool_kpa,eta,
                        elec,mwh_pool,capex_list,fixed_fraction,
                        auxiliary_kw=0.25):
    full_load_h=mwh_pool*1000/150
    p1=motor_kw(flow_primary,p_primary_kpa,eta)
    p2=motor_kw(flow_pool,p_pool_kpa,eta)
    el_aux_mwh=(p1+p2)*full_load_h/1000 + auxiliary_kw*8760/1000
    el_aux_cost=el_aux_mwh*elec
    rows=[]
    for budget in capex_list:
        maintenance=budget*fixed_fraction
        annual_net=sav-el_aux_cost-maintenance
        rows.append({"CAPEX_budget_EUR":budget,
         "fixed_OandM_EUR_year":num(maintenance),"pump_and_control_kW":num(p1+p2+auxiliary_kw),
         "pump_energy_MWh_year":num(el_aux_mwh),"pump_electricity_EUR_year":num(el_aux_cost),
         "gross_simulink_energy_opex_benefit_EUR_year":num(sav),
         "net_after_pumps_and_maintenance_EUR_year":num(annual_net),
         "simple_payback_years":num(budget/annual_net) if annual_net>0 else None,
         "annualized_CAPEX_EUR_year":num(annualized(budget)),
         "NPV20y_6percent_EUR":num(npv(budget,annual_net)),
         "cash_positive":annual_net>0,
         "economic_screen":"screening BUDGET, not an actual equipment quote"})
    return rows
def quantile(xs,p):
    v=sorted(xs);i=(len(v)-1)*p;lo=math.floor(i);hi=math.ceil(i)
    return v[lo]+(v[hi]-v[lo])*(i-lo)
def profile_stats():
    p=SLX/"no_pool_35_8760h.csv"
    # downsample every 12th 300s record to 1h. We need values per step: exact maxima.
    x={"source":[],"dh_req":[],"dh_q":[],"dh_el":[],"gas":[],"src_pool":[]}
    with p.open(encoding="utf-8-sig",newline="") as f:
        for i,row in enumerate(csv.DictReader(f)):
            if i%12==0:
                x["source"].append(float(row["DCAvailable_MW"]))
                x["dh_q"].append(float(row["DistrictHPHeat_MW"]))
                x["dh_el"].append(float(row["DistrictHPel_MW"]))
                x["gas"].append(float(row["GasHeat_MW"]))
    return {
     "annual_hours":len(x["source"]),
     "DC_source_MW_mean":num(statistics.mean(x["source"])),
     "DC_source_MW_p95":num(quantile(x["source"],.95)),
     "DC_source_MW_max":num(max(x["source"])),
     "DH_HP_output_MW_mean":num(statistics.mean(x["dh_q"])),
     "DH_HP_output_MW_p95":num(quantile(x["dh_q"],.95)),
     "DH_HP_output_MW_max":num(max(x["dh_q"])),
     "DH_HP_electric_MW_max":num(max(x["dh_el"])),
     "gas_MW_peak":num(max(x["gas"])),
     "source_capacity_at_COP_4_8_MW":num(max(x["source"])*4.8/(4.8-1)),
     "thermal_nominal_module_count_2MW_to_cover_model_peak":math.ceil(max(x["dh_q"])/2),
     "N_plus_1_2MW_modules":math.ceil(max(x["dh_q"])/2)+1,
     "note":"Nominal ranges are NOT outputs at 35°C source and 70°C sink. Vendor selection must certify operating point."}
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--heat-kw",type=float,default=150)
    parser.add_argument("--pool-return-c",type=float,default=27.5)
    parser.add_argument("--pool-rise-k",type=float,default=2)
    parser.add_argument("--primary-drop-k",type=float,default=3)
    parser.add_argument("--fouling-factor",type=float,default=1.25)
    parser.add_argument("--U-w-m2k",type=float,default=1500)
    parser.add_argument("--primary-head-kpa",type=float,default=70)
    parser.add_argument("--pool-head-kpa",type=float,default=80)
    parser.add_argument("--pump-efficiency",type=float,default=.60)
    parser.add_argument("--output-tag",default="default")
    args=parser.parse_args()
    assert args.heat_kw>0 and 0<args.pump_efficiency<=1 and args.U_w_m2k>0
    savings=raw(SLX/"closed_loop_incremental_opex_2025.json")
    result=raw(SLX/"simulink_closed_loop_summary_8760h.json")
    case={x["name"]:x for x in result}
    direct=float(savings["direct35"]["net_energy_opex_benefit_EUR"])
    hp=float(savings["hp25"]["net_energy_opex_benefit_EUR"])
    price_e=float(savings["electricity_EUR_MWh_2025_X_VAT"])
    # direct from DC at 35 is only potential; HX must meet UA with approach and fouling.
    trials=[]
    for source in (25,30,32,35,40,45):
        for U in (800,1500,2500):
            trial=hx(args.heat_kw,source,args.primary_drop_k,args.pool_return_c,
                     args.pool_rise_k,U,args.fouling_factor)
            trial["U_label"]="ASSUMED overall U, not manufacturer datasheet"
            trials.append(trial)
    nominal=hx(args.heat_kw,35,args.primary_drop_k,args.pool_return_c,
               args.pool_rise_k,args.U_w_m2k,args.fouling_factor)
    flow1=nominal["hot_flow_m3h"];flow2=nominal["pool_flow_m3h"]
    # CAPEX budgets inclusive of HX or HP, hydraulics, controls + commissioning.
    # No quoted manufacturer's price; pool branch scope only. N+1 options depend on site.
    alternatives={
     "A_DIRECT_35C_TITANIUM_HX":{
         "equipment":"Gasketed titanium plate HX custom engineered, clean primary VFD TPE, treated pool side SPECK BADU, 2 x isolation valves and calibrated temperature/flow meters",
         "source_C":35,"sink_C":27.5,"rated_useful_kW":args.heat_kw,
         "model_verified_pool_MWh":case["direct_35"]["pool_heat_MWh"],
         "gross_economic_benefit_EUR_year":direct,
         "capex_scenarios_EUR":[45000,75000,110000],
         "uncertainty":"Titanium HX must be custom-selected from real four-port conditions; Pahlen MFT680 200 kW @ 60K is NOT suitable evidence.",
         "budgets":choose_price_budget(direct,flow1,flow2,args.primary_head_kpa,
                            args.pool_head_kpa,args.pump_efficiency,price_e,
                            case["direct_35"]["pool_heat_MWh"],[45000,75000,110000],.02)},
     "B_POOL_HP_25C":{
        "equipment":"Oilon ChillHeat P series or Carrier AquaSnap 61WH; nominal range only, candidate not point-selected; with corrosion-resistant pool isolation HX and variable-speed pumps",
        "source_C":25,"sink_C":30,"rated_useful_kW":args.heat_kw,
        "model_verified_pool_MWh":case["heatpump_25"]["pool_heat_MWh"],
        "pool_compressor_energy_MWh_at_COP4":case["heatpump_25"]["pool_HP_electric_MWh"],
        "gross_economic_benefit_EUR_year":hp,
        "budget_scenarios_EUR":[100000,170000,250000],
        "uncertainty":"COP4 is original unverified surrogate; manufacturer performance at 25/30 and seasonal part-load must be obtained.",
        "budgets":choose_price_budget(hp,flow_m3h(112.5,3),flow2,
                           args.primary_head_kpa,args.pool_head_kpa,
                           args.pump_efficiency,price_e,
                           case["heatpump_25"]["pool_heat_MWh"],
                           [100000,170000,250000],.025)},
     "C_USE_DH_70C_POOL_HX":{
        "equipment":"Isolated pool titanium/316L plate HX supplied from district network at 70C. Pool disinfection/filtration independent.",
        "source_C":70,"sink_C":27.5,"rated_useful_kW":args.heat_kw,
        "gross_energy_benefit_EUR_year":None,
        "uncertainty":"No independent closed-loop marginal dispatch with pool on DH supply: OPEX/NPV UNSOLVED. HX surface low vs 35C but DH marginal generation/distribution cost required.",
        "budget_scenarios_EUR":[25000,45000,75000]}
    }
    # Electrothermal cost break-even (against gas delivered heat) without installed costs.
    gas=float(savings["gas_EUR_MWh_2025_X_VAT"])
    break_even_cop=price_e/(gas/.9)
    max_direct_capex=(direct-alternatives["A_DIRECT_35C_TITANIUM_HX"]["budgets"][0]["pump_electricity_EUR_year"])/(
      1/((1-(1+.06)**(-20))/.06)+.02)
    max_hp_capex=(hp-alternatives["B_POOL_HP_25C"]["budgets"][0]["pump_electricity_EUR_year"])/(
      1/((1-(1+.06)**(-20))/.06)+.025)
    profile=profile_stats()
    out={
      "date":"2026-10-23","version":"equipment_screen_v01",
      "not_vendor_quotation":True,"input_vars":vars(args),
      "source_confidence":{"Eurostat_2025_SK":"published statistics B",
         "NASA_POWER_2025":"external gridded reanalysis B",
         "Carrier_or_Oilon":"product series exists, operating point not vendor verified C",
         "HX_U_and_pressure_loss":"engineer D assumed",
         "CAPEX":"engineer scenario D, not price offer"},
      "profile":profile,
      "pool_HX_nominal_calculation":nominal,
      "electricity_price_EUR_MWh":price_e,"gas_price_EUR_MWh":gas,
      "gas_heating_cost_per_MWh_EUR":num(gas/.9),
      "HP_COP_break_even_energy_only":num(break_even_cop),
      "annual_source_pool_useful_heat_MWh":num(case["direct_35"]["pool_heat_MWh"]),
      "alternatives":alternatives,
      "CAPEX_NPV0_limit_EUR":{"A_DIRECT_35":num(max_direct_capex),
                             "B_HP_25":num(max_hp_capex)},
      "sources":[
       {"name":"Pahlen Maxi Flo titanium","url":"https://www.pahlen.com/products/pool-heating/heat-exchangers/maxi-flo-titanium/","limitation":"200kW at 60K difference NOT at 35C"},
       {"name":"Carrier 61XWH ZE","url":"https://www.carrier.com/commercial/en/eu/products/heating/water-to-water-heat-pumps/61xwhze/","limitation":"up to 85C & nominal range, no selected 35→70 COP"},
       {"name":"Oilon ChillHeat P","url":"https://oilon.com/en-us/products/oilon-chillheat-p-30-p-450/","limitation":"up to 120C, rating at conditions TBD"},
       {"name":"Carrier 61WH R290 SK reseller","url":"https://www.climaport.sk/produkty/aquasnap-61wh/","limitation":"50-824kW range & 78C limit, safety R290"},
       {"name":"Speck BADU pool pumps","url":"https://speck-bombas.com/catalogo/badu-21-80/","limitation":"rated maxima NOT duty point curve"},
       {"name":"Grundfos TPE clean-water loops","url":"https://api.grundfos.com/literature/Grundfosliterature-5840195.pdf","limitation":"not for direct chlorinated pool water without material review"},
       {"name":"Siemens SITRANS TS500","url":"https://www.siemens.com/global/en/products/automation/process-instrumentation/temperature-measurement/sensor-sitrans-ts500.html","limitation":"SIL options do NOT certify the complete safety chain"},
       {"name":"Danish Energy Agency technology catalogue 2026","url":"https://ens.dk/node/3449","limitation":"general representative investments not binding quotes"},
       {"name":"10MW Kalundborg real project","url":"https://smart-cities-marketplace.ec.europa.eu/insights/solutions/waste-water-heat-source-kalundborg-denmark","limitation":"2017 project €7.25m; very different location/design"}],
      "explicit_missing":["HX full manufacturer thermal rating & pressure drop at W35/32 and pool27.5/29.5","Pool water quality and wetted materials","Equipment CAPEX signed quotes",
        "DC and pool VFD pump heads/hydraulic curves","Actual district HP product COP 25/35 to 70C","Pool HP COP 25C to 30C and N+1 approach",
        "Independent IT chilling N+1 at full IT design load","Electrical grid connection and siting","Life-cycle commissioning, owner labor, taxes","Official engineering sign-off"]}
    tag=args.output_tag
    if not tag.replace("_","").isalnum():raise ValueError("Tag must be alphanumeric or underscore")
    of=HERE/f"equipment_selection_{tag}.json"
    if of.exists():raise FileExistsError(str(of))
    of.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding="utf-8")
    fh=HERE/f"HX_low_grade_heat_{tag}.csv"
    with fh.open("x",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(trials[0]));w.writeheader();w.writerows(trials)
    rf=HERE/f"CAPEX_pool_cases_{tag}.csv"
    budget=[]
    for key,v in alternatives.items():
        for r in v.get("budgets",[]):budget.append({"alternative":key,**r})
    with rf.open("x",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(budget[0]));w.writeheader();w.writerows(budget)
    print("EQUIPMENT_SELECTION_VERIFIED",json.dumps({
       "source_profile":profile,
       "HX_nominal":nominal,
       "npv0_capex_limit":out["CAPEX_NPV0_limit_EUR"],
       "gross_benefits":[round(direct,2),round(hp,2)],"file":str(of)},ensure_ascii=False))
if __name__=="__main__":main()
