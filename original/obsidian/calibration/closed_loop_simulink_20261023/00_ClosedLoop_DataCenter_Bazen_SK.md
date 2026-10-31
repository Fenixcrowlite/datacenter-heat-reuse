---
tags: [datacentrum, bazen, simulink, closed-loop, kalibracia]
status: VERIFIED_SIMULATION_NOT_CERTIFIED
date: 2026-10-23
---
# DataCenter ↔ bazén ↔ teplovodná sieť

Nový oddelený model MATLAB/Simulink so skutočnou 5-minútovou tepelnou spätnou väzbou.

- [[ClosedLoop_Simulink_Matematika_SK]] - kompletné rovnice, výsledky a metodika
- [[DC_Pool_Coupled_ClosedLoop_20261023_SK.slx]] - nový Simulink model, bez zásahu do pôvodného bazénového projektu
- ![[DC_Pool_Coupled_Simulink_diagram.png]]
- ![[carrier_cop_certified_comparison_SK.png]]
- [[manufacturer_certified_points_carrier.csv]] - overené skúšobné body Eurovent pri W10-7
- [[simulink_closed_loop_summary_8760h.json]] - 8760h výsledky
- [[closed_loop_independent_QA_2025.json]] - nezávislé kontroly
- [[closed_loop_incremental_opex_2025.json]] - OPEX citlivosť

Veľké vstupné/výstupné CSV (4 × 105120 riadkov) zostávajú v:
`C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\calibration\closed_loop_simulink_20261023\`

UPOZORNENIE: reálna prevádzka, normová zhoda a COP pre 25–35°C / 70°C ešte nie sú overené.

## Aktualizované technické správy PDF (SK / RU / EN)

- [[ClosedLoop_Report_SK.pdf]]
- [[ClosedLoop_Report_RU.pdf]]
- [[ClosedLoop_Report_EN.pdf]]
- [[STATUS_CLOSED_LOOP_20261023.json]]
