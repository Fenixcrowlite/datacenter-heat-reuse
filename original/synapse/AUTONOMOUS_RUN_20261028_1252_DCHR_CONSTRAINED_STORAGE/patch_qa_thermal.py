from pathlib import Path
p=Path(__file__).parent/'independent_qa.py'
s=p.read_text(encoding='utf-8')
a='    target=next(m for m in out["models"] if m["config"]["capacity_mwh"]==2500'
b='    assert len(out["thermal_sensitivity"])==5\n    thermal=out["thermal_sensitivity"]\n    assert thermal[0]["year_results"][2]["temperature_blocked_hours"]>0\n    assert thermal[2]["year_results"][2]["temperature_blocked_hours"]==0\n    assert thermal[4]["year_results"][2]["delivered_mwh"]>thermal[2]["year_results"][2]["delivered_mwh"]\n    target=next(m for m in out["models"] if m["config"]["capacity_mwh"]==2500'
assert s.count(a)==1
s=s.replace(a,b)
a='"aggregate_years_checked":24,'
b='"aggregate_years_checked":39,'
assert s.count(a)==1
s=s.replace(a,b)
p.write_text(s,encoding='utf-8')
print('QA_THERMAL_GATES_ADDED')
