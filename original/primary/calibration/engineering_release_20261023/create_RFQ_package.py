# -*- coding: utf-8 -*-
"""Versioned preliminary RFQ package; never sends messages or purchases equipment."""
from pathlib import Path
import csv,json
P=Path(__file__).resolve().parent
vendors=[
 ("Carrier / CLIMAPORT","Ing. Juraj Kupcik","kupcik@climaport.sk",
  "https://carrier-eshop.sk/2020/06/09/kto-je-kto-climaport-obchodne-oddelenie/",
  "District high-temperature water heat pumps","Slovakia contact published in 2020; current assignment unverified"),
 ("Oilon ChillHeat","Industrial sales","Chillheat.Sales@oilon.com",
  "https://oilon.com/en-gb/products/oilon-chillheat-p-30-p-450/",
  "District high-temperature water heat pumps","P-series <=450kW B0/W35; ask about S-series and larger plant"),
 ("Alfa Laval Slovakia","Sales contact via website","",
  "https://www.alfalaval.sk/produkty-a-riesenia/prenos-tepla/doskove-vymenniky-tepla/plate-heat-exchangers/",
  "Low-grade pool heat exchanger","Contact page, no verified recipient"),
 ("Guntner","Data Center Solutions","",
  "https://guntner.com/applications/data-centers",
  "Independent IT heat rejection / recoolers","Manufacturer sizing and local ambient design required"),
 ("Kelvion","Data center recooling solutions","",
  "https://www.kelvion.com/industry-solutions/data-center",
  "Independent IT heat rejection / recoolers","Manufacturer site offers custom recoolers")
]
with (P/"vendor_directory_grounded.csv").open("x",newline="",encoding="utf-8-sig") as f:
 w=csv.writer(f);w.writerow(["company","contact","public_email","official_source","scope","source_caveat"]);w.writerows(vendors)
shared="""We are preparing an early-stage academic engineering feasibility model for heat reuse from a hypothetical 10 MW IT data centre in Bratislava, Slovakia. No existing installation, verified operating telemetry or purchasing commitment is claimed.

PLEASE quote budgetary, non-binding performance with conditions explicitly listed, or state that a condition lies outside your envelope.

Project boundary: 10 MW rated IT heat (synthetic 2025 average IT 8.2 MW), average recoverable low-grade heat 6.97 MW in the scenario; separate district heating plant and 500 m³ public swimming pool. District heating heat-pump output target approximately 10 MW duty (thermal) with N+1 architecture; backup boiler exists only in modeled economics. No final pipe flow, fluid composition, piping pressure drop, power supply or procurement timetable has been validated.

Test matrix to quote, EACH with full and 25/50/75% part load:
A: evaporation/source water IN/OUT 25/20 C; district condenser IN/OUT 50/70 C.
B: evaporation/source water IN/OUT 35/30 C; district condenser IN/OUT 50/70 C.
C: evaporation/source water IN/OUT 45/40 C; district condenser IN/OUT 50/70 C.
D: evaporation/source water IN/OUT 35/30 C; district condenser IN/OUT 60/70 C.
E: evaporation/source water IN/OUT 35/30 C; district condenser IN/OUT 70/80 C.
Please reject unsupported combinations. Specify whether performance includes internal pumps/fans.

Required deliverables: exact equipment model/variant and module count; output heat kW and electrical kW; source extracted heat kW, COP and seasonal performance assumptions; operating envelope; nominal/min/max source/sink flow; pressure drop kPa each side; recommended glycol concentration; part-load and minimum modulation; refrigerant/GWP and safety installation conditions; 1-module failure and standby restart controls; auxiliary kW; required voltage/start/inrush; sound and footprint; water quality; availability and budgetary CAPEX including commissioning, installation exclusions, delivery time, maintenance and warranty. Supply OEM selection report and applicable EN14511 test evidence where possible.

A prior Carrier 61XWH-ZE 2025 brochure quotes max 1,570 kW for model 17 at W20/15 source and W70/75 sink. THIS IS NOT the required project operating point; no extrapolation accepted."""
special={
"Carrier":"""Subject: Technical selection request | 10 MW heat-reuse study | Carrier 61XWH-ZE

Dear Engineering / HVAC team,

Please pass this non-binding technical selection request to the Carrier 61XWH-ZE industrial heat pump engineering team. We would appreciate results from the official equipment selection program at the specified water conditions, including R1234ze L/medium/high source variants and possible series or parallel module arrangements.

"""+shared+"""

We are particularly interested in comparing a configuration near 6 operating +1 standby versus 7 operating +1 standby units, but actual useful kW per unit must be confirmed first. Please indicate whether heat pump source water at 35 C has any upper/lower restrictions by variant.

Best regards,
Academic engineering feasibility study
(Identity and institutional affiliation to be completed before sending.)
""",
"Oilon":"""Subject: Performance-map request | data-centre waste-heat reuse to 70 C district heating

Dear Oilon ChillHeat Sales / Engineering,

Please recommend a technically credible ChillHeat P- or S-series configuration for the conditions below, using your Oilon Selection Tool. The P30–P450 brochure rating is at B0/W35 and does not establish heat delivered at our project temperatures. For the 10 MW duty target, please propose the most appropriate multi-unit layout and failover.

"""+shared+"""

Please distinguish P30–P450 and S-series allowable maximum water temperatures and cooling/heating duty per selected configuration; availability of manufacturer-certified part-load data is important.

Best regards,
Academic engineering feasibility study
(Identity and institutional affiliation to be completed before sending.)
""",
"AlfaLaval":"""Subject: Gasketed titanium plate exchanger RFQ | 150 kW at small approach temperature

Dear Alfa Laval applications engineering,

Please size a physically isolated pool heating plate exchanger and provide a non-binding performance-based budget. Design duty is 150 kW THERMAL at counterflow hot side 35 C in / 32 C out, cold pool-water branch 27.5 C in / 29.5 C out. The preliminary flows for water are 43.17 m³/h primary and 64.76 m³/h secondary. Counterflow LMTD approx. 4.98 K and CLEAN UA approx. 30.1 kW/K; the study requires a 25% engineering fouling-area allowance corresponding to design UA 37.6 kW/K before OEM review.

Please quote real useful kW and pressure drops at this exact point, plates/gaskets suited to chlorinated or salt-treated pool water, maintainability/cleaning, channel velocities, minimum terminal approach and fouling basis, double-wall separation if recommended, drawing with isolation valves and chemical dosing injection downstream of exchanger, maximum allowable pressure, accessories and budget price with exclusions. We are not treating Pahlén 200 kW at 60 K as evidence for this duty.

This is an academic feasibility study in Slovakia with no purchasing authorization or installed site yet. Please treat the enquiry as non-binding.

Best regards,
Academic engineering feasibility study
(Identity and institutional affiliation to be completed before sending.)
""",
"DryCooler":"""Subject: Independent 10 MW critical IT cooling / N+1 recoolers | equipment sizing enquiry

Dear Data Centre Cooling Engineering,

We request a non-binding technical concept for independent rejection of the entire 10 MW RATED IT thermal load, even if all district heating and pool heat-reuse paths are simultaneously unavailable. The location is the Bratislava area. Please compare dry and adiabatic/hybrid coolers, with water/glycol supply/return candidates 30/35, 35/40 and 40/45 C; we need you to verify actual allowable IT coolant set points. Ambient dry-bulb/ wet-bulb extremes, noise, water constraints, electrical demand and site conditions are not measured and must be resolved during selection.

Compare physically adequate N+1 banks of effective modules around 2 MW NET heat rejection at site design conditions, not rated sales brochure output. Calculate full 10 MW after loss of the largest module including ambient derating, with UPS-supported circulation pumping, standby changeover options 10/30/60/300 seconds, separate power paths, independent controls and bypass valve. Supply fan kW, pump kW and dp at target flow, annual estimated fan consumption on 8760h local NASA reanalysis (not site measurements), water use, glycol concentration, frost safety, maintenance, acoustic output, structural loads, CAD/GA and indicative CAPEX.

A nominal single-unit catalogue number without peak-ambient selection and N+1 fault case cannot qualify as safe emergency IT cooling. No real purchase order is authorized.

Best regards,
Academic engineering feasibility study
(Identity and institutional affiliation to be completed before sending.)
"""}
for k,content in special.items():
 (P/("RFQ_"+k+"_EN.md")).write_text(content,encoding="utf-8")
o={"status":"DRAFTS_CREATED_NOT_SENT","source_date":"2026-10-23",
"vendors":[{"name":v[0],"email":v[2],"url":v[3],"caveat":v[5]} for v in vendors],
"documents":["RFQ_"+k+"_EN.md" for k in special],
"caveats":["Do not claim to represent STU or a specific operator without authorization.",
"Non-binding technical feasibility, no pricing confirmed or offers received.",
"Do not expose user contact identity unless authorized."]}
(P/"RFQ_package_status.json").write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding="utf-8")
print("ENGINEERING_RFQ_DRAFTS_READY",list(special),len(vendors),"manufacturers; not sent")
