# -*- coding: utf-8 -*-
"""First-order metrology uncertainty; demonstration class D only, not calibration."""
from pathlib import Path
import json,math
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results'/'pool_measurement_v08'
rho=997;cp=4182;volume=500;dt=900
C=rho*cp*volume
Vdot=30;dT=3;uflow_frac=.05;uT1=uT2=.2
m_dot=rho*Vdot/3600
Q=m_dot*cp*dT
u_dT=math.hypot(uT1,uT2)
urel=math.hypot(uflow_frac,u_dT/dT)
uq=Q*urel
uQ_storage=math.sqrt(2)*.2*C/dt
worstUQ_storage=2*.2*C/dt
p={
 'status':'CALCULATED_ASSUMED_UNCERTAINTY_NOT_CALIBRATION',
 'source_class':'D','assumptions':{'pool_volume_m3':volume,'rho_kg_m3':rho,
  'cp_J_kgK':cp,'sample_seconds':dt,'flow_m3h':Vdot,
  'heat_exchanger_deltaT_K':dT,'flow_relative_std_uncertainty':uflow_frac,
  'each_temperature_std_uncertainty_K':.2,
  'temperature_sensor_independent_errors':True},
 'thermal_storage_J_K':C,'nominal_flow_based_heat_W':Q,
 'standard_uncertainty_flow_heat_W':uq,'relative_standard_uncertainty_flow_heat':urel,
 'standard_uncertainty_15min_pool_dT_power_W':uQ_storage,
 'worst_case_bounded_15min_pool_dT_power_W':worstUQ_storage,
 'warning':'Do not estimate 100-150kW pool heating solely by 15min temperature finite difference with 0.2K temperature errors; use traceable volume flow and supply/return thermometers. Independent uncertainties assumed, no correlated sensor drift.'}
(OUT/'NEISTOTY_MERANIA_V08_SK.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8')
print('METROLOGY_D_UNCERTAINTY_PASS',Q/1000,uq/1000,uQ_storage/1000,'kW')
