# Stav doplnku: ohrev bazéna 500 m³, 2026-10-23

## VERIFIED

- Originálny projekt DCHR Stateflow v85 zachovaný: SHA256 = 2A9DE22C0C55E8C4A87F7B0E0CFE9CD97DB08C991F09D98361B009DE310ADDE7.
- Python: 7 scenárov, sedem dní; kľúčový čas na 28 °C pri 150 kW = 47,434 h.
- Python prvý zákon: rezíduum energetickej bilancie 7,15e-14 MWh; TČ druhá bilancia -1,91e-13 MWh.
- Python časové kroky 300 / 60 s: rozdiel prvého dosiahnutia 28 °C = 0,607 min; posledné vzorky sa môžu líšiť pre hysterezis cyklov.
- MATLAB R2026a/Simulink: vytvorený a uložený skutočný .slx s integrátorom, MATLAB Function tepelných strát a hysterezis termostatom.
- Simulink: TC_75kW 97,883 h, TC_150kW 47,317 h, TC_300kW 23,350 h, TC_150kW_bez_plachty 46,833 h.
- Relatívna bilancia Simulink: 0,0066 % / 0,0117 % / 0,0217 % / pod 0,000001 % podľa scenára.
- Výstupy CSV, JSON, grafy PNG uložené. Tri PDF s rozšírenou matematikou: SK, EN, RU, všetky 7 strán, kontrola hraníc textových blokov bez odrezania.
- Tri PDF a Obsidian poznámky vrátane diagramov priamo skopírované do trezoru Bimba; kontrola SHA256 súhlasí.

## BOUNDARY / SCENARIO ONLY

- Objem 500 m³ a plocha 312,5 m² sú príklad, nie univerzálna norma.
- T vzduchu, RH, UA, účinnosť plachty, tepelný výkon, COP a zdrojová teplota sú prevádzkové hypotézy.
- Model vody bazéna neobsahuje HVAC haly, odvlhčovanie, hygienickú výmenu vody nad rámec vyparovania, bazénovú hydrauliku a kalibrovaný COP(T).
- V SLX je užitočný tepelný prívod pre bazén, nie plný fyzikálny model tepelného čerpadla alebo výmenníka.
- Návrh nie je validovaný údajmi skutočnej prevádzky. Pôvodná interná vrstva dispatch v85/v86 nebola modifikovaná.

## PLANNED (pri budúcom rozšírení)

- Vstupy zo skutočného dátového centra a oddelený HX s realistickým prietokom.
- Teplotne a výkonovo závislá COP mapa; zdrojové hydraulické obmedzenia a pomocný príkon.
- Vzduchotechnika bazéna, odvlhčenie a vyššie vrstvy riadenia Stateflow.
- Spoločný dispatch DC -> DH / TES / pool / reject bez dvojitého započítania zdroja.
- Ročný profil reálneho dátového centra a ceny elektriny/taríf, dimenzovanie a bezpečnostná certifikácia.

## Opakovanie

    powershell -File "C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\matlab\pool_500m3\spusti_vsetko_bazen_sk.ps1"

Súvisiace súbory: Matematicky_rozbor_a_simulacia_SK.md; Rozhranie_integracie_DC_Bazen_SK.md; pool_calc_report_sk.py; rozsir_technicke_pdf_sk.py; spusti_simulaciu_bazena_sk.m; spusti_scenare_bazena_sk.m.
