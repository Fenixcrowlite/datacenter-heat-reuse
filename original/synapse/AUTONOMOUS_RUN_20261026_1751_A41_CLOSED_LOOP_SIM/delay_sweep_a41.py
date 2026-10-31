"""Sensitivity to cold-standby REJECT B switch delay, synthetic only."""
import json
from pathlib import Path
import closed_loop_a41 as a41
def main():
    rows,_=a41.inputs()
    result={}
    for steps in range(5):
        a41.DELAY_STEPS=steps
        trace=a41.replay(rows,"backup_only")
        alarms=[r for r in trace if r["T_next_C"]>=42]
        result[str(steps)]=dict(max_temperature_C=max(r["T_next_C"] for r in trace),
            first_temperature_alarm_hour=alarms[0]["cas_h"] if alarms else None,
            alarm_intervals=len(alarms),critical_steps=sum(r["mode"]==2 for r in trace),
            unhandled_kWh=sum(r["unhandled_W"] for r in trace)/4000)
    temps=[result[str(k)]["max_temperature_C"] for k in range(5)]
    assert temps==sorted(temps),("NONMONOTONE_DELAY_RESPONSE",temps)
    assert result["2"]["max_temperature_C"]>42
    assert result["0"]["max_temperature_C"]<42
    out=dict(status="SYNTHETIC_DELAY_SENSITIVITY_NOT_CERTIFIED",delay_steps=result)
    (Path(__file__).parent/"DELAY_SWEEP.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf8")
    print(json.dumps(out,indent=2))
if __name__=="__main__":main()
