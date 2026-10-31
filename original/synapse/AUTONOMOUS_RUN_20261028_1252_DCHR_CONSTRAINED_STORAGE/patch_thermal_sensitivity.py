from pathlib import Path
h=Path(__file__).parent
p=h/'constrained_storage.py'
s=p.read_text(encoding='utf-8')
changes=[
('    results=[simulate(rows,c) for c in configs]\n',
 '    results=[simulate(rows,c) for c in configs]\n    thermal_cases=[Config(capacity_mwh=2500,extra_hp_electric_mw=1.5,\n                          storage_temperature_c=t,hourly_loss_fraction=loss)\n                   for t,loss in ((55,0.00025),(65,0.00025),(72,0.00025),\n                                  (80,0.00025),(72,0.0))]\n    thermal_results=[simulate(rows,c) for c in thermal_cases]\n'),
('            "models":results,','            "models":results,"thermal_sensitivity":thermal_results,'),
('    print(json.dumps({"rows":o["rows"],"models":len(o["models"]),',
 '    print(json.dumps({"rows":o["rows"],"models":len(o["models"]),\n                      "thermal_sensitivity":len(o["thermal_sensitivity"]),')
]
for a,b in changes:
    if s.count(a)!=1:raise RuntimeError('ANCHOR_FAIL '+repr(a))
    s=s.replace(a,b)
p.write_text(s,encoding='utf-8')
p=h/'independent_qa.py'
s=p.read_text(encoding='utf-8')
a='    for model in out["models"]:\n'
b='    for model in out["models"]+out["thermal_sensitivity"]:\n'
assert s.count(a)==1
s=s.replace(a,b)
a='    return {"status":"PASS","rows":len(rows),"models_checked":len(out["models"]),'
b='    return {"status":"PASS","rows":len(rows),"models_checked":len(out["models"])+len(out["thermal_sensitivity"]),'
assert s.count(a)==1
s=s.replace(a,b)
p.write_text(s,encoding='utf-8')
print('THERMAL_SENSITIVITY_ADDED')
