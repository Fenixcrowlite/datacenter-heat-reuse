---
date: 2026-10-23
tags: [datacentrum, bazen, teplovodna-siet, vyber-zariadeni, financie]
status: VERIFIED_SCREENING_NOT_PRODUCT_APPROVED
---
# DataCenter → bazén: výber zariadení

Aktualizované správy 23.10.2026 (v02 po kapacitnej optimalizácii):

- [[Equipment_Selection_SK_20261023_v02]] a [[Equipment_Selection_SK_v02.pdf]]
- [[Equipment_Selection_RU]] a [[Equipment_Selection_RU_v02.pdf]]
- [[Equipment_Selection_EN]] a [[Equipment_Selection_EN_v02.pdf]]
- [[Module_capacity_tradeoff_SK]] a [[Module_capacity_tradeoff_SK.pdf]]
- [[equipment_configurator.html]] - interaktívny kalkulátor tepla, plochy, COP a NPV
- [[equipment_selection_default.json]] - výpočty materiálov a plôch
- [[HX_low_grade_heat_default.csv]] - plochy HX pri 25-45 C
- [[CAPEX_pool_cases_default.csv]] - scenáre investície
- [[network_module_2MW_Nplus1_screen.csv]] - kapacitná optimalizácia
- `screen_equipment_options.py` a `optimize_module_capacity.py` - reprodukovateľné skripty

**Rozhodnutie:** 35 C priamy bazénový výmenník, pokiaľ výrobca certifikuje 150 kW pri 35/32 a 27.5/29.5 C. TČ pre sieť pri simulovanom profile predbežne 5x2 MW pracovné + 1x2 MW záložné, vyžaduje konkrétny výber COP a výkonov výrobcom.

**UPOZORNENIE:** 200 kW Pahlén sa uvádza pri cca 60 K rozdiele, nie pri 35 C. Tu potrebujeme individualny nizkoteplotný návrh UA 37.63 kW/K. CAPEX je rozpočtový scenár, nie cenová ponuka. Pôvodný Simulink a modely iného chatu neboli zmenené.

Poznamka: sucasny `Equipment_Selection_SK.md` bol upraveny paralelnym pracovnym tokom a **NEBOL PREPISANY**. Aktualna kopia je `Equipment_Selection_SK_20261023_v02.md`.
