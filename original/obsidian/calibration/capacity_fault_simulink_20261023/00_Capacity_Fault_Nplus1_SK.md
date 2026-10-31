---
date: 2026-10-23
tags: [data-center, pool, heat-pump, Simulink, N-plus-1, failures]
status: VERIFIED_SIMULINK_MODEL_NOT_CERTIFIED
---

# Výber zariadení a N+1: simulácia 2025

- [[Nplus1_Carrier_Selection_SK]] / [[Nplus1_Carrier_Selection_SK.pdf]]
- [[Nplus1_Carrier_Selection_RU]] / [[Nplus1_Carrier_Selection_RU.pdf]]
- [[Nplus1_Carrier_Selection_EN]] / [[Nplus1_Carrier_Selection_EN.pdf]]
- [[DC_Pool_Capacity_Fault_20261023_SK.slx]] - nová verzia, bez zmeny pôvodných modelov
- [[capacity_fault_simulink_2025.csv]] - sedem skutočne vykonaných 8760h scenárov
- [[Carrier_2025_nominal_vs_Nplus1_options.csv]] - porovnanie katalógových menovitých výkonov
- [[Carrier_2025_rated_vs_simulated_economics.json]] - porovnanie 6+1 vs 7+1
- [[nplus1_pdf_qa.json]] - vizuálna QA správ

**Výsledok:** zníženie tepelnej kapacity siete z 12 na 10 MW pri absencii bazéna pridalo len 2.684 MWh plynu ročne. Simulácia 30-minútového obnovenia rezervného modulu pridala 0.130 MWh plynu oproti stabilnej 10-MW vetve bazéna.

Carrier 2025 model 17 má menovitý výkon 1570 kW pri W20/15 a W70/75. Neznamená to skutočný výkon pri 35/30 a 50/70, preto sú zostavy 6+1 a 7+1 len orientačné pred výberom výrobcu.

Krok po kroku: `run_capacity_fault_annual_SK.m` a `dc_pool_coupled_step_capacity_SK.m`, externá reanalýza NASA POWER 2025, predpokladaný profil IT. Pôvodná Simulink verzia a práca paralelného chatu neboli menené.
