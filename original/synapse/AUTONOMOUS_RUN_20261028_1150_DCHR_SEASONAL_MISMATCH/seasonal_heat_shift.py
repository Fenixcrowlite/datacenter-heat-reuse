"""Isolated counterfactual audit. Simulated heat is NOT measured or dispatch-feasible."""
from __future__ import annotations
import csv
import datetime as dt
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

SOURCE = Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\results\best_scenario_v2_timeseries.csv")
EXPECTED_SHA = "8125719923bae97901f37cf0f5354df77b46544df0477f863172255748873f25"
CAPACITIES_MWH = (0, 100, 500, 1000, 2500, 5000, 10000, 20000)
FIELDS = ("Curtailed_HP_Heat_MW", "Gas_Heat_MW", "Heat_Demand_MW",
          "HP_Heat_Used_MW", "Storage_Charge_MW", "Storage_Discharge_MW")

def load(path: Path = SOURCE, expected_sha: str | None = EXPECTED_SHA):
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if expected_sha is not None and digest != expected_sha:
        raise ValueError("source SHA256 changed: refuse to use stale baseline")
    rows = []
    prev = None
    for index, row in enumerate(csv.DictReader(data.decode("utf-8-sig").splitlines()), 2):
        try:
            stamp = dt.datetime.strptime(row["Time"], "%d-%b-%Y %H:%M:%S")
            values = {f: float(row[f]) for f in FIELDS}
        except (ValueError, KeyError, TypeError) as exc:
            raise ValueError(f"invalid CSV row {index}") from exc
        if prev is not None and stamp - prev != dt.timedelta(hours=1):
            raise ValueError(f"non-hourly or duplicate timestamp at row {index}")
        if not all(math.isfinite(v) and v >= 0 for v in values.values()):
            raise ValueError(f"negative/nonfinite row {index}")
        if abs(values["Heat_Demand_MW"] - values["HP_Heat_Used_MW"] -
               values["Gas_Heat_MW"] - values["Storage_Discharge_MW"] +
               values["Storage_Charge_MW"]) > 1e-6:
            raise ValueError(f"heat demand balance mismatch row {index}")
        if values["Curtailed_HP_Heat_MW"] > 1e-9 and values["Gas_Heat_MW"] > 1e-9:
            raise ValueError(f"simultaneous curtailment and gas: investigate row {index}")
        rows.append((stamp, values))
        prev = stamp
    if not rows:
        raise ValueError("empty input")
    return rows, digest

def ideal_store(year: list[tuple[float,float]], capacity: float, cycles: int = 3):
    """Ideal hypothetical buffer, initially empty, 100% efficient, unlimited MW.
    Curtailment is *potential* heat: availability/cost NOT demonstrated.
    Years 2/3 repeat the same synthetic weather/demand, not forecasts.
    """
    if capacity < 0 or not math.isfinite(capacity) or cycles < 1:
        raise ValueError("invalid storage configuration")
    if any(q < 0 or g < 0 or not math.isfinite(q+g) or min(q,g)>1e-9 for q,g in year):
        raise ValueError("invalid or overlapping heat streams")
    soc = 0.0
    out = []
    for _ in range(cycles):
        start = soc
        charge = discharge = overflow = 0.0
        for q, gas in year:
            accepted = min(q, capacity-soc)
            soc += accepted
            delivered = min(gas, soc)
            soc -= delivered
            charge += accepted
            discharge += delivered
            overflow += q-accepted
            if soc < -1e-8 or soc > capacity+1e-8:
                raise AssertionError("storage SOC outside capacity")
        if not math.isclose(start+charge-discharge, soc, abs_tol=1e-6):
            raise AssertionError("storage energy conservation failure")
        if not math.isclose(charge+overflow, math.fsum(q for q,_ in year), abs_tol=1e-6):
            raise AssertionError("curtailment double counted")
        out.append({"initial_soc_mwh":start,"saved_gas_heat_mwh":discharge,
                    "charged_mwh":charge,"unused_potential_mwh":overflow,
                    "final_soc_mwh":soc})
    return out

def analyze(rows, source_sha):
    monthly = defaultdict(lambda: {"curtailed_potential_mwh":0.0,
                                    "gas_heat_mwh":0.0, "hours":0})
    pairs=[]
    for stamp, v in rows:
        q=v["Curtailed_HP_Heat_MW"]
        g=v["Gas_Heat_MW"]
        monthly[stamp.month]["curtailed_potential_mwh"] += q
        monthly[stamp.month]["gas_heat_mwh"] += g
        monthly[stamp.month]["hours"] += 1
        pairs.append((q,g))
    q_total=math.fsum(q for q,_ in pairs)
    g_total=math.fsum(g for _,g in pairs)
    overlap_hours=sum(q>1e-9 and g>1e-9 for q,g in pairs)
    overlap_energy=math.fsum(min(q,g) for q,g in pairs)
    scenarios={str(c):ideal_store(pairs,float(c),3) for c in CAPACITIES_MWH}
    for cycles in scenarios.values():
        for y in cycles:
            if y["saved_gas_heat_mwh"] > g_total+1e-6:
                raise AssertionError("savings exceed simulated gas demand")
    return {"classification":"SIMULATED_COUNTERFACTUAL_NOT_DISPATCH_FEASIBLE",
            "source_sha256":source_sha, "rows":len(rows),
            "assumed_interval_hours":1,
            "timezone":"UNSPECIFIED_IN_SOURCE",
            "baseline_existing_storage_capacity_mwh_observed":100,
            "curtailed_potential_mwh":q_total,
            "gas_heat_mwh":g_total,
            "simultaneous_curtailment_gas_hours":overlap_hours,
            "direct_same_hour_overlap_upper_bound_mwh":overlap_energy,
            "monthly":{str(k):v for k,v in sorted(monthly.items())},
            "ideal_counterfactual_capacities_mwh":scenarios,
            "assumptions":[
                "All curtailed HP_Heat is hypothetical potential, not proven recoverable thermal output.",
                "No additional heat-pump electricity, COP/capacity limit, heat-exchanger constraints, network losses, storage losses, investment or cost modeled.",
                "Unrestricted charge/discharge power; 100% efficiency; one-hour constant power; 0 MWh initial storage in first synthetic year.",
                "Years 2 and 3 replay identical synthetic annual conditions; not measured future years or a certified steady state.",
                "Additional idealized storage is NOT an incremental retrofit of the existing 100 MWh baseline storage; do not add savings to baseline without coupled re-simulation.",
                "No claim of actual gas reduction, ERF, REF, WUE, legal compliance or primary-source signoff."
            ],"production_modified":False,"primary_source_signoffs":0}

def report(result):
    m=result["monthly"]
    s=["# DCHR | Sezónny nesúlad tepla a plynu (simulovaný scenár)",
       "",
       "**Klasifikácia:** hypotetický výpočet z existujúcej simulácie, nie meranie, projekt zásobníka ani potvrdená úspora plynu.",
       f"Zdroj SHA256: `{result['source_sha256']}`. Hodinových intervalov: {result['rows']}.",
       "",
       f"Potenciálne obmedzené teplo: **{result['curtailed_potential_mwh']:,.1f} MWh**; simulované plynové teplo: **{result['gas_heat_mwh']:,.1f} MWh**.",
       f"Priamy súbeh obmedzenia HP a plynu: **{result['simultaneous_curtailment_gas_hours']} hodín**, priama hodinová náhrada najviac **{result['direct_same_hour_overlap_upper_bound_mwh']:.3f} MWh**.",
       "",
       "## Mesačné súčty (MWh, syntetické)","",
       "| Mesiac | Obmedzený potenciál HP | Plynové teplo |","|---:|---:|---:|"]
    for k,v in m.items():
        s.append(f"| {int(k)} | {v['curtailed_potential_mwh']:,.1f} | {v['gas_heat_mwh']:,.1f} |")
    s += ["","## Kontrafaktuálny ideálny zásobník (nie realizovateľný návrh)","",
          "Bez tepelných strát, bez obmedzenia nabíjacieho/vybíjacieho výkonu, bez dodatočnej elektriny HP. Rok 1 začína prázdny; roky 2/3 opakujú presne ten istý syntetický profil.",
          "Uvedené kapacity sú samostatné ideálne scenáre, nie prírastky k existujúcemu 100 MWh zásobníku.",
          "","| Kapacita (MWh) | Rok 1: ideálne vytlačený plyn (MWh) | Rok 2 (MWh) | Rok 3 (MWh) |","|---:|---:|---:|---:|"]
    for k,cycles in result["ideal_counterfactual_capacities_mwh"].items():
        s.append("| "+k+" | "+" | ".join(f"{x['saved_gas_heat_mwh']:,.1f}" for x in cycles)+" |")
    s += ["","## Inžiniersky záver","",
          "Letný prebytok tepla a zimná spotreba plynu sa v tomto modeli **časovo míňajú**. Zvýšenie okamžitej kapacity HP samo osebe nedokazuje úsporu plynu. Potrebné je analyzovať sezónne ukladanie tepla, distribučné teploty, tepelné straty, reálny COP, dodatočnú elektrinu a skutočnú kapacitu výmenníka.",
          "Tepelný výkon `HP_Heat_MW` je **potenciál pred obmedzením**, nie automaticky dostupné teplo. Preto všetky čísla z ideálneho zásobníka predstavujú iba matematické horné hranice za neoverených predpokladov.",
          "Existujúci zásobník v CSV dosahuje 100 MWh; samostatný kontrafaktuálny výpočet nie je kalibrovaná úprava existujúceho dispečingu.",
          "Regulačné metriky ERF/REF/WUE zostávajú nevyhodnotené; primárne zdroje **0/31**.",
          "","**Ďalší krok:** pripraviť spojenú simuláciu s reálnymi obmedzeniami nabíjania/vybíjania, stratami a elektrinou HP, porovnať ročné náklady a zachovať pôvodný model nemenný.",
          ""]
    return "\n".join(s)

def main():
    rows,sha=load()
    if len(rows)!=8760:
        raise ValueError("expected 8760 hourly records")
    result=analyze(rows,sha)
    here=Path(__file__).resolve().parent
    (here/"SEASONAL_MISMATCH.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    (here/"ENGINEERING_NOTE_SK.md").write_text(report(result),encoding="utf-8")
    print(json.dumps({"rows":result["rows"],"overlap_hours":result["simultaneous_curtailment_gas_hours"],
                      "curtailed_mwh":result["curtailed_potential_mwh"],
                      "gas_mwh":result["gas_heat_mwh"],
                      "ideal_100mwh_year2":result["ideal_counterfactual_capacities_mwh"]["100"][1]["saved_gas_heat_mwh"]}))

if __name__=="__main__":
    main()
