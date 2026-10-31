from pathlib import Path
p=Path(__file__).parent/'constrained_storage.py'
s=p.read_text(encoding='utf-8')
changes=[
('("COP","Temperature_Lift_K","DH_Supply_C","Source_Heat_Available_MW",','("COP","Temperature_Lift_K","DH_Supply_C","DC_Total_MW","Source_Heat_Available_MW",'),
('    extra_hp_electric_mw: float = 1.5\n','    extra_hp_electric_mw: float = 1.5\n    site_electric_cap_mw: float = 12.0\n    hp_total_electric_cap_mw: float = 2.5\n'),
('min(c.charge_mw,c.discharge_mw,c.extra_hp_electric_mw)<0','min(c.charge_mw,c.discharge_mw,c.extra_hp_electric_mw,c.site_electric_cap_mw,c.hp_total_electric_cap_mw)<0'),
('    source_headroom=max(0.0,v["Source_Heat_Available_MW"]-v["HP_Source_Used_MW"])','    source_headroom=max(0.0,v["Source_Heat_Available_MW"]-v["HP_Source_Used_MW"])\n    electric_headroom=min(c.extra_hp_electric_mw,\n                          max(0.0,c.site_electric_cap_mw-v["DC_Total_MW"]),\n                          max(0.0,c.hp_total_electric_cap_mw-v["HP_Electric_MW"]))'),
('c.extra_hp_electric_mw*effective_cop,','electric_headroom*effective_cop,'),
('if added_electric>c.extra_hp_electric_mw+EPS or source_draw>source_headroom+EPS:','if added_electric>electric_headroom+EPS or source_draw>source_headroom+EPS:'),
('              "COP extra-lift derating is heuristic','              "Extra HP electricity bounded by configured site MW cap and total HP electric MW cap; both assumed, not measured nameplate limits.",\n              "COP extra-lift derating is heuristic')
]
for old,new in changes:
    if s.count(old)!=1: raise RuntimeError('PATCH_ANCHOR_MISMATCH '+repr(old))
    s=s.replace(old,new)
p.write_text(s,encoding='utf-8')
t=Path(__file__).parent/'test_constrained_storage.py'
s=t.read_text(encoding='utf-8')
old='"Source_Heat_Available_MW":10.0,"HP_Source_Used_MW":2.0,'
new='"DC_Total_MW":10.0,"Source_Heat_Available_MW":10.0,"HP_Source_Used_MW":2.0,'
assert s.count(old)==1
s=s.replace(old,new)
old='    def test_source_cap(self):'
new='    def test_site_electric_cap(self):\n        _,z=step(row(DC_Total_MW=11.99),0,Config())\n        self.assertLessEqual(z["additional_electric_mwh"],0.01+1e-9)\n    def test_hp_total_electric_cap(self):\n        _,z=step(row(HP_Electric_MW=2.49),0,Config())\n        self.assertLessEqual(z["additional_electric_mwh"],0.01+1e-9)\n    def test_source_cap(self):'
assert s.count(old)==1
s=s.replace(old,new)
t.write_text(s,encoding='utf-8')
print('PATCHED_SITE_AND_HP_ELECTRIC_CAPS')
