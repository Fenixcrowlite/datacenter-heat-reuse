"""Explicitly synthetic counterfactual: pool and district loads remain ON during REJECT faults."""
from __future__ import annotations
import json
from pathlib import Path
import coupled_a42 as a42

HERE=Path(__file__).resolve().parent

def counterfactual(rows):
    result=[dict(r) for r in rows]
    for k in range(96,384):
        r=result[k]
        # Hypothetical 60 kW pool + 100 kW district heat, 20 kW TES discharge.
        # These are stress-test inputs, not original measured/standard loads.
        r.update(qpool=60000.0,qdh=100000.0,qdis=20000.0,
                 qcharge=0.0,hx=0.0,leak=0.0)
    return result

def main():
    base=a42.load_inputs()
    rows=counterfactual(base)
    results={}
    for scenario in ("both","backup_only","neither"):
        trace=a42.replay(rows,scenario)
        name="TRACE_A42_COUNTERFACTUAL_"+scenario+".csv"
        a42.write_csv(HERE/name,trace)
        results[scenario]=dict(**a42.summarize(trace),sha256=a42.sha(HERE/name),
           fault_period_unmet_kWh=sum(x["pool_dh_unmet_W"] for x in trace[96:384])/4000,
           fault_period_it_kWh=sum(x["qit_W"] for x in trace[96:384])/4000)
    report=dict(status="SYNTHETIC_COUNTERFACTUAL_NOT_MEASURED",
        inputs="pool=60kW, district=100kW, TES discharge request=20kW, hours 24..96",
        physical_release_allowed=False, cases=results)
    (HERE/"COUNTERFACTUAL_A42.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf8")
    print(json.dumps(report,indent=2))
if __name__=="__main__":main()
