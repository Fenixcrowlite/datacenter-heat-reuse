---
tags: [datacentrum, bazen, integracia, stateflow, architektura]
status: IMPLEMENTED_POOL_MODEL__INTEGRATION_PLANNED
---
# Integračné rozhranie: dátové centrum -> bazén 500 m³

## Aktuálne vykonaná realizácia

- Samostatný funkčný Simulink model: Bazen_DC_Ohrev_500m3_SK.slx.
- Fyzikálny modul: nelineárne tepelné straty závislé od T, aktivity, plachty.
- Dynamika: jedna tepelná kapacita vody, kontinuálny integrátor.
- Regulácia: dvojpolohový termostat s hysterezou 27,8/28,2 °C.
- Zdroj: časová veličina dostupného tepelného výkonu na vstupe bazéna [W].
- Nameraná telemetria reálneho dátového centra nebola pripojená.
- Tepelné čerpadlo a priama vetva sú zatiaľ alternatívnymi účtovnými scenármi, nie plnohodnotným fyzikálnym okruhom zdroja v Simulinku.

## Zmluva budúcej integrácie

| Veličina | Smer | Jednotka | Význam |
|---|---|---|---|
| P_DC_IT | vstup | W | okamžitý IT príkon, nie PUE krát IT |
| Q_DC_obnovitelne | vstup | W | teplo prípustné z nezávislého chladenia |
| T_DC_vystup | vstup | °C | zdrojová teplota pre HX / TČ |
| m_DC | vstup | kg/s | hmotnostný prietok |
| T_bazen | stav/výstup | °C | teplota 500 m³ vody |
| Q_potreba_bazen | požiadavka | W | výkon od termostatu a regulátora |
| Q_do_bazena | vstup | W | skutočne dodané užitočné teplo |
| P_el_TC | výstup | W | elektrina kompresora pri voľbe TČ |
| Q_DC_spotreba | výstup | W | teplo odobraté DC, bez dvojitého započítania |
| IT_cooling_ok | interlock | boolean | pri 0 musí byť využitie tepla bezpečne odstavené |
| STOP | interlock | boolean | prechod do bezpečného stavu |

## Fyzikálne podmienky a ochrany

1. Zachovať vlastný rezervný odvod všetkého odpadového tepla IT; bazén nesmie byť jediný chladiaci odber.
2. Primárny okruh DC a bazénová voda nikdy nie sú priamo hydraulicky prepojené; použiť samostatný výmenník.
3. $0\le Q_{\rm pool}\le Q_{\rm HX,max}$; dostupnosť sa hodnotí v danom čase, nie podľa 10 MW IT nominálu.
4. Priamou vetvou vyhrievať len pri dostatočnom teplotnom rozdiele a súčasne vyhovujúcom prietoku výmenníka.
5. Pri TČ dodržať $Q_{\rm out}=Q_{\rm source}+P_{\rm el}$, skutočný COP závisí od teplôt.
6. Súčet tepla pre vykurovaciu sieť, bazén, zásobník a vyradené teplo nesmie prekročiť dostupné teplo zdroja.
7. Uvažovať minimálne prietoky, ramp rate, anti-short-cycle a spoľahlivé snímače.
8. Pred spojením s v85/v86 Stateflow overiť elektrické stropy, dĺžku horizontu, záznam stavov a bezpečnostné interlocky.

## Architektúra budúcej rozšírenej schémy

DC_IT -> Heat_recovery_constraint -> allocation(DH / POOL / TES / REJECT)
POOL -> (HX_direct or HP) -> Termostat -> Heat_balance -> T_pool
     -> demand feedback to allocation
DC_IT -> independent dry cooler for IT safety

**Pravidlo:** nové prepojenie je až po samostatnom porovnaní výpočtov Python, MATLAB a pôvodného v85/v86 reportingu. Túto integráciu zatiaľ neoznačovať ako implementovanú.

## Spustenie a reprodukovateľnosť

Z MATLAB Command Window:

    run('C:/Users/Lysda/OneDrive/Projects/DataCenter_Heat_Reuse/matlab/pool_500m3/spusti_simulaciu_bazena_sk.m')
    run('C:/Users/Lysda/OneDrive/Projects/DataCenter_Heat_Reuse/matlab/pool_500m3/spusti_scenare_bazena_sk.m')

Python:

    python C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\matlab\pool_500m3\pool_calc_report_sk.py
    python C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\matlab\pool_500m3\rozsir_technicke_pdf_sk.py

Pred opätovným rozšírením PDF vždy znovu spustiť generátor základnej 3-stranovej správy, potom doplniť 4-stranovú matematickú prílohu.

## Limitácie verzie

Matematický výpočet je deterministický a reprodukovateľný. Odpadové teplo DC nie je doložené meraniami konkrétnej budovy. Súčasná simulácia bazéna testuje **tepelné zaťaženie a riadenie**, nie reálnu kvalifikáciu technického návrhu a bezpečnosti.
