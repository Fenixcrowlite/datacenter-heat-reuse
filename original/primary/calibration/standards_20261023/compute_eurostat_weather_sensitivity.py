# -*- coding: utf-8 -*-
"""Reproducible economics sensitivity from OFFICIAL Eurostat rows + unchanged MATLAB core."""
from pathlib import Path
import csv, json, math, statistics
HERE=Path(__file__).resolve().parent
DATA=HERE/"official_datasets"
OUT=HERE/"experiments"/"real_vs_synthetic_v01"
def rows(path):
    with path.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def select_price(dataset,band,period,tax="X_VAT"):
    matched=[r for r in rows(DATA/(dataset+"_SK_2025_2026_series.csv"))
             if r["geo"]=="SK" and r["nrg_cons"]==band and r["tax"]==tax and r["time"]==period]
    if len(matched)!=1:raise ValueError(f"Ambiguous/missing Eurostat {dataset} {band} {period} {tax}: {len(matched)}")
    if matched[0]["flag"]:raise ValueError("Eurostat price flagged; verify before consumption: "+str(matched[0]))
    return float(matched[0]["value"])*1000 # EUR/kWh -> EUR/MWh
def tariffs(period,tax="X_VAT"):
    e=select_price("nrg_pc_205","MWH70000-149999",period,tax)
    g=select_price("nrg_pc_203","GJ100000-999999",period,tax)
    return {"electric_EUR_MWh":e,"gas_EUR_MWh":g,"period":period,"tax":tax}
h1,h2=181*24,184*24
t1,t2=tariffs("2025-S1"),tariffs("2025-S2")
t26=tariffs("2026-S1")
t2025={k:(t1[k]*h1+t2[k]*h2)/(h1+h2) for k in ["electric_EUR_MWh","gas_EUR_MWh"]}
t2025.update({"period":"2025 weighted 181/184 days","tax":"X_VAT"})
t_synth={"electric_EUR_MWh":100.0,"gas_EUR_MWh":50.0,
         "period":"original synthetic 2026","tax":"engineering placeholders"}
scenarios=[("SYNTHETIC_PRICE",t_synth),("EUROSTAT_2025",t2025),("EUROSTAT_2026H1",t26)]
m=rows(OUT/"matlab_weather_compare.csv")
if len(m)!=2:raise ValueError("Expected two independently MATLAB-executed weather cases")
all_out=[]
for base in m:
    eDC=float(base["DCEnergy_MWh"]);originalPue=1.36
    demand=float(base["HeatDemand_MWh"]);gasHeat=float(base["GasHeat_MWh"])
    hpElectric=float(base["HPElectric_MWh"]);erfbase=float(base["ERF_source_proxy"])
    assert demand>0 and gasHeat>0 and hpElectric>0 and eDC>0
    for pue in [1.20,1.36,1.52]:
        annualDC=eDC*pue/originalPue
        sourceHeat=erfbase*eDC
        for name,p in scenarios:
            baselineCost=demand/0.9*p["gas_EUR_MWh"]
            scenarioCost=gasHeat/0.9*p["gas_EUR_MWh"]+hpElectric*p["electric_EUR_MWh"]
            savings=baselineCost-scenarioCost
            all_out.append({
                "weather":base["Weather"],"PUE":pue,"cost_source":name,
                "heat_demand_MWh":round(demand,3),
                "gas_backup_heat_MWh":round(gasHeat,3),
                "HP_electric_MWh":round(hpElectric,3),
                "electric_EUR_MWh":round(p["electric_EUR_MWh"],4),
                "gas_EUR_MWh":round(p["gas_EUR_MWh"],4),
                "baseline_gas_opex_EUR":round(baselineCost,2),
                "HP_plus_backup_opex_EUR":round(scenarioCost,2),
                "operating_savings_EUR":round(savings,2),
                "data_centre_electricity_MWh":round(annualDC,3),
                "DC_source_heat_proxy_MWh":round(sourceHeat,3),
                "source_heat_proxy_to_DC_energy":round(sourceHeat/annualDC,6),
                "confidence":"weather NASA = reanalysis B; rates Eurostat B; IT/utilization/recovery/HP/GAS efficiency D",
                "caveat":"Model plant dispatch excludes pool; not EU-compliant ERF measurement"
            })
output=OUT/"weather_pue_price_sensitivity_18_cases.csv"
if output.exists():raise FileExistsError(str(output))
with output.open("w",newline="",encoding="utf-8-sig") as f:
    wr=csv.DictWriter(f,fieldnames=list(all_out[0]));wr.writeheader();wr.writerows(all_out)
syn=next(r for r in m if r["Weather"]=="SYNTHETIC")
real=next(r for r in m if r["Weather"]=="NASA_POWER_2025")
demandDiff=float(real["HeatDemand_MWh"])-float(syn["HeatDemand_MWh"])
summary={
 "dates":{"weather":"2025 hourly NASA POWER","prices":"2025-S1/S2, 2026-S1 official Eurostat",
          "PUE":"2026 Uptime benchmark",
          "study":"2026-10-23"},
 "n_cases":len(all_out),
 "provider_provenance":{
 "NASA":"NASA POWER / MERRA-2 gridded reanalysis; not site thermometer",
 "Eurostat_electric":"nrg_pc_205 SK MWH70000-149999 X_VAT KWH EUR",
 "Eurostat_gas":"nrg_pc_203 SK GJ100000-999999 X_VAT KWH EUR",
 "benchmarks":"Uptime average PUE 1.52, capacity weighted 1.36 in 2026",
 "DC_IT_telemetry":"not available; remains synthetic",
 "HP_COP_map":"not available; existing theoretical COP surrogate retained"},
 "pricing":{"2025_S1":t1,"2025_S2":t2,"2025_hour_weighted":t2025,"2026_S1":t26,
            "synthetic_baseline":t_synth},
 "monthly_pricing_limitation":"Using period-average prices, not actual hourly time-of-use tariffs",
 "weather_vs_model":{
   "synthetic_mean_C":float(syn["MeanOutdoor_C"]),
   "real_reanalysis_2025_mean_C":float(real["MeanOutdoor_C"]),
   "mean_temperature_bias_synthetic_minus_reanalysis_C":round(float(syn["MeanOutdoor_C"])-float(real["MeanOutdoor_C"]),4),
   "synthetic_model_demand_MWh":float(syn["HeatDemand_MWh"]),
   "reanalysis_model_demand_MWh":float(real["HeatDemand_MWh"]),
   "demand_difference_MWh":round(demandDiff,3),
   "demand_change_percent":round(100*demandDiff/float(syn["HeatDemand_MWh"]),3)},
 "ERF_caution":{"original_model_ERF_synthetic":float(syn["ERF_original_energy_included"]),
                "source_heat_proxy_synthetic":float(syn["ERF_source_proxy"]),
                "original_model_ERF_NASA":float(real["ERF_original_energy_included"]),
                "source_heat_proxy_NASA":float(real["ERF_source_proxy"]),
                "warning":"Original metric includes HP-generated heat; proxy subtracts compressor but is NOT a boundary-metered EN 50600-4-6 ERF"},
 "output":str(output),
 "limitations":["2025 NASA reanalysis instead of site metering","same uncalibrated synthetic IT load across comparisons",
                "Eurostat average price != negotiated datacentre contract","no CAPEX, tax recovery, pumping nor district tariff",
                "no pool dispatch integration yet","no legal standard full-text validation"]}
(OUT/"real_data_calibration_report.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"cases":len(all_out),"prices_EUR_MWh_2025":t2025,
    "heat_demand_change_pct":summary["weather_vs_model"]["demand_change_percent"],
    "old_ERF_NASA":summary["ERF_caution"]["original_model_ERF_NASA"],
    "source_proxy_NASA":summary["ERF_caution"]["source_heat_proxy_NASA"],
    "result":str(output)},ensure_ascii=False,indent=2))
