# -*- coding: utf-8 -*-
"""One-second emergency failover model for IT cooling with optional thermal reservoir.
Assumptions: cooling modules are proven NET duty at site ambient, not catalogue ratings.
"""
from __future__ import annotations
import csv,json
from pathlib import Path
P=Path(__file__).resolve().parent
CP=4182;RHO=997
cases=[
 ("6units_nominal_30s",6,0,30,30),
 ("6units_derated10pct_30s",6,.10,30,30),
 ("7units_derated10pct_30s",7,.10,30,30),
 ("7units_derated10pct_5min",7,.10,300,300),
 ("7units_derated20pct_30s",7,.20,30,30),
 ("7units_nominal_total_cooling_lost_60s",7,0,60,60),
]
records=[]
for name,units,derate,delay,horizon in cases:
    net=2*(1-derate)
    # N+1: one designated spare normally disconnected, all other units operating.
    duty=units-1
    initial_capacity=duty*net
    fail_capacity=(duty-1)*net
    after_capacity=duty*net
    normal_short=max(0,10-initial_capacity)
    fault_short=max(0,10-fail_capacity)
    fail_energy_kWh=fault_short*delay/3600*1000
    # End-of-event deficit may persist even after N+1, so no finite reservoir
    # can make permanently undersized cooling system safe.
    permanently_undersized=after_capacity<10-1e-9
    usable_deltaT=5
    minimum_buffer=fail_energy_kWh*3600000/(RHO*CP*usable_deltaT)
    # full-loss scenario not a one-unit fault
    if "total_cooling" in name:
        fail_capacity=0;fault_short=10;fail_energy_kWh=10*delay/3600*1000
        minimum_buffer=fail_energy_kWh*3600000/(RHO*CP*usable_deltaT)
        after_capacity=initial_capacity
        permanently_undersized=after_capacity<10-1e-9
    records.append({"scenario":name,"cooler_count_total":units,
     "net_capacity_per_unit_MW":round(net,3),
     "net_capacity_normal_MW":round(initial_capacity,3),
     "net_capacity_during_fault_MW":round(fail_capacity,3),
     "net_capacity_after_spare_MW":round(after_capacity,3),
     "fault_seconds":delay,"deficit_during_fault_MW":round(fault_short,3),
     "buffer_min_5K_m3":round(minimum_buffer,3),
     "normal_10MW_design_load_unserved_MW":round(normal_short,3),
     "capacity_adequate_after_failover":not permanently_undersized,
     "requires_independent_UPS_pump":True,
     "classification":"model hypothesis only: rated and derated duties not manufacturer confirmed"})
assert records[0]["capacity_adequate_after_failover"]
assert not records[1]["capacity_adequate_after_failover"]
assert records[2]["capacity_adequate_after_failover"]
assert records[3]["buffer_min_5K_m3"]>records[2]["buffer_min_5K_m3"]
assert records[5]["buffer_min_5K_m3"]>records[2]["buffer_min_5K_m3"]
with (P/"cooling_fault_second_scale.csv").open("x",encoding="utf-8-sig",newline="") as f:
 w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
(P/"cooling_fault_second_scale.json").write_text(json.dumps(records,indent=2,ensure_ascii=False),encoding="utf-8")
print("FAILSAFE_COOLING_SCENARIOS_VERIFIED",json.dumps([{"case":x["scenario"],"buffer_m3":x["buffer_min_5K_m3"],"adequate":x["capacity_adequate_after_failover"]} for x in records],ensure_ascii=False))
