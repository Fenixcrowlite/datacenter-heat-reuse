---
tags: [datacentrum, bazen, MATLAB, Simulink, stateflow, kontrola, v85, most]
status: VERIFIED_ONE_WAY_REPLAY
language: sk
created: 2026-10-23
---
# Prepojenie Stateflow v85 a bazéna 500 m³: fyzikálna bilancia v03

> [!important] Overený výkon, nie ročná predikcia
> Skutočný pôvodný model v85 bol v MATLAB R2026a znova spustený. Výsledné stopy sú bitovo identické s archivovanými súbormi MAT v86 a prešli dchr.report_held_schedule_v76. Nový samostatný Simulink model prijíma výkon už dodanej priamej tepelnej služby v85 a rozdeľuje ho medzi bazén a pôvodný odber DH. Deväť simulácií a 99 nezávislých kontrol prešlo. Originál v85 zostal nezmenený.

## 1. Hranice a účel

Zdrojové odpadové teplo DC → pôvodný Stateflow v85 (HP, TES, DH) → skutočne dodaná priama HP služba → nový most v03 → bazén + zostávajúca dodávka DH.

Nový most **nepridáva žiadnu ďalšiu energiu**, nemení elektrický príkon kompresora v85 ani jeho pôvodnú rozhodovaciu logiku. Bazén získava iba časť už vyrobenej a pôvodne do DH smerovanej služby.

$$Q_{\mathrm{HP,service,v85}}=Q_{\mathrm{pool}}+Q_{\mathrm{DH,remaining}}.$$

Heat pump charging do TES nie je voľne dostupné teplo pre bazén. Backup heat a elektrický príkon nie sú priamo presmerované.

## 2. Pôvod meraných modelových signálov

Pôvodný v85 model má report interval_trace_v66, 1380 položiek na interval a 80 na makrosegment. Podľa auditovaného report_held_schedule_v75:

- z(25) = priamo dodaná HP služba [MW];
- z(7:8) = dolná a horná medza trvania segmentu [h];
- trace(k,13) = počet segmentov k-teho intervalu;
- direct_HP_service_MWh_hull = bilančná obálka pôvodného reportu.

$$E_{k,\mathrm{HP,service}}=\sum_{s=1}^{n_k} z_{25,s}\frac{\tau_{\mathrm{min},s}+\tau_{\mathrm{max},s}}{2}\quad[\mathrm{MWh}].$$

$$Q_{k,\mathrm{HP,service}}=10^6 E_{k,\mathrm{HP,service}}/\Delta t_k\quad[\mathrm W].$$

Výpočty sa kontrolujú proti pôvodnej intervalovej obálke. Stred trvania je reprezentant pre diskrétny model, nie zvýšenie fyzikálnej presnosti. Pre regulačné garancie je potrebné doplniť výslovnú obálkovú optimalizáciu.

## 3. Rovnice bazéna

$$C=\rho Vc_p=997\cdot500\cdot4182=2\,084\,727\,000\quad\mathrm{J/K}.$$

$$E_{16\rightarrow28}=C\cdot12/(3{,}6\cdot10^9)=6{,}94909\quad\mathrm{MWh}.$$

Druhý výraz je energia akumulácie bez strát. Skutočný model má konvekciu, žiarenie, vyparovanie, podložie, dopĺňanie vody a ďalších 2 kW scenárového odvodu.

$$T_{k+1}=T_k+\frac{900}{C}(Q_{\mathrm{pool},k}-Q_{\mathrm{loss},k}).$$

$$Q_{\mathrm{loss}}=Q_{\mathrm{evap}}+Q_{\mathrm{conv}}+Q_{\mathrm{rad}}+Q_{\mathrm{construction}}+Q_{\mathrm{makeup}}+2000\,\mathrm W.$$

$$p_{\mathrm{sat}}(T)=0{,}61094\exp(17{,}625T/(T+243{,}04))\quad[\mathrm{kPa}].$$

$$\dot m_{\mathrm{evap}}=\max(0,4\cdot10^{-5}A[p_{\mathrm{sat}}(T_w)-RH p_{\mathrm{sat}}(T_a)]F_a(1-0{,}90K)).$$

$$Q_{\mathrm{evap}}=2{,}44\cdot10^6\dot m_{\mathrm{evap}}.$$

$$Q_{\mathrm{conv}}=3A(T_w-T_a)(1-0{,}75K).$$

$$Q_{\mathrm{rad}}=0{,}95\sigma A[(T_w+273{,}15)^4-(T_a-2+273{,}15)^4](1-0{,}75K).$$

$$Q_{\mathrm{construction}}=800(T_w-20),\quad Q_{\mathrm{makeup}}=\dot m_{\mathrm{evap}}4182(T_w-15).$$

Všetky súčty majú jednotku W. Záporná konvekcia je oprávnená, keď vzduch odovzdáva teplo chladnejšej vode.

## 4. Termostat a modelový bezpečnostný strop

Zopnutie pri 27,35 °C, vypnutie pri 27,65 °C, výpočtový strop 27,75 °C.

$$Q_{\mathrm{safe}}=\max(0,C(27{,}75-T_k)/900+Q_{\mathrm{loss},k}).$$

Pri zapnutom termostate a bez STOP:

$$Q_{\mathrm{pool}}=\min(Q_{\mathrm{v85}},150\,000,Q_{\mathrm{safe}}),$$

ináč je $Q_{\mathrm{pool}}=0$. Zvyšok ostáva $Q_{\mathrm{DH,remaining}}=Q_{\mathrm{v85}}-Q_{\mathrm{pool}}$.

STOP bazéna znamená odpojenie bazéna, nie vypnutie IT chladenia. Pre skutočný projekt musí existovať nezávislý bezpečný odvod tepla DC. Chyby snímačov nie sú certifikované touto simuláciou.

## 5. Reálne vykonané testy

| Prípad v85 | Stav bazéna | Do bazéna [MWh] | Do DH [MWh] |
|---|---|---:|---:|
| service_E3.0_a1.0_H2_dt0.25 | 16 °C | 0,150000 | 0,297566 |
| service_E3.0_a1.0_H2_dt0.25 | 27,70 °C | 0 | 0,447566 |
| service_E3.0_a1.0_H2_dt0.25 | STOP | 0 | 0,447566 |
| charge_E4.95_a1.0_H2_dt0.25 | 16 °C / 27,70 °C / STOP | 0 | 0 |
| binding_stop | 16 °C / 27,70 °C / STOP | 0 | 0 |

Tri pôvodné prípady x tri stavy bazéna = deväť úplných v03 simulácií. Každý zdrojový prípad bol znova v85 simulovaný, identita jeho stopy overená s archivovaným MAT.

$$0{,}447565789 = 0{,}150000000+0{,}297565789\quad\mathrm{MWh}.$$

Pre studenú vodu v hlavnom scenári je najvyššia vypočítaná teplota 16,31419 °C. V prípade vstupných 27,70 °C termostat blokuje ohrev.

## 6. QA, nezmeniteľnosť a hranice platnosti

- 9 simulácií Simulink: PASS.
- 99 nezávislých kontrol Python: PASS.
- Energetická bilancia DH + bazén = pôvodne vydaná HP služba: PASS.
- Tepelná kapacita a súčet tokov bazéna: PASS.
- STOP a nulová služba pri čisto nabíjacom prípade: PASS.
- Teplota <=27,75 °C v kontrolovaných prípadoch: PASS.
- SHA-256 pôvodnej v85: 2a9de22c0c55e8c4a87f7b0e0cfe9cd97db08c991f09d98361b009de310adde7.

**Obmedzenie:** iba krátke certifikované časové intervaly (hodinové prípady), nie 8760 h. Model v03 je jednosmerná integrácia už dodanej služby, nie samostatné nové odoberanie odpadového tepla, a nie obojsmerné rozhodovanie Stateflow. Výkaz ERF pôvodnej v85 sa nesmie nafukovať presmerovaním tej istej energie.

## 7. Reprodukovateľnosť

MATLAB: v adresári OneDrive/Projects/DataCenter_Heat_Reuse/matlab/pool_v85_bridge_v03 spustiť spusti_skutocne_v85_a_bazen_sk.m.

Python QA: z rovnakého adresára spustiť qa_most_v85_sk.py.

- Model: Bazen_Prepripojenie_Sluzby_v85_v03_SK.slx.
- Zoznam: results/pool_v85_bridge_v03/most_v85_bazen_v03_SK.json.
- Nezávislé QA: results/pool_v85_bridge_v03/QA_NEZAVISLA_V85_BRIDGE_SK.json.
- Časové priebehy: 9 samostatných sim_*.csv.
- [[Matematika_a_rocna_simulacia_SK]]: predchádzajúci *syntetický* 8760 h experiment v02.

## 8. Literatúra a predpisy

- EU Delegated Regulation 2024/1364: https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj
- Slov-Lex 308/2012, pôvodné znenie §8(7), 28 °C pre plavecký bazén: https://static.slov-lex.sk/static/SK/ZZ/2012/308/vyhlasene_znenie.print.html
- STN EN 15288-1+A1:2024: https://normy.normoff.gov.sk/norma/139372/nahlad/

Pre fyzický návrh overiť aktuálne účinné predpisy, hydrauliku, snímače, katalógové parametre a dostupnosť kompletných výrobných máp COP.


## Grafy vykonanych scenarov

![[priebeh_bazen_v85_SK.png]]

![[rozdelena_sluzba_v85_SK.png]]

