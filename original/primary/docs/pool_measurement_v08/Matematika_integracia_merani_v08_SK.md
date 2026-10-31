---
tags: [datacentrum, bazen, Simulink, Stateflow, merania, QA]
status: VERIFIED_SYNTHETIC_REPLAY_NOT_FIELD_CALIBRATION
language: sk
date: 2026-10-23
---
# V08 - externé merania, matematika a nezávislá kontrola

> [!warning] Hranica evidencie
> V08 je reálne spustený model MATLAB/Simulink R2026a. Jeho dva vstupné teplotné kanály sú vedené z CSV, nie z vnútorných delay blokov. **Všetky doteraz dostupné hodnoty sú však syntetické D, odvodené zo záznamov v07, nie z fyzických snímačov.** V08 je overená integrácia a regresný test, nie reálna kalibrácia.

## 1. Architektúra

V08 vznikol ako nový nezávislý model odvodzovaný z v07, ktorý má vlastný päťstavový Stateflow, dve uzatváracie vetvy, dva REJECT chladiče a scenárové núdzové odľahčenie IT. Originálna v85 nie je súčasťou vykonávacieho dispečera v08 a zostala nezmenená.

CSV import → validátor proveniencie a kvality → 21 prevádzkových signálov + 2 externé T1/T2 → ochranný Stateflow gate → regulácia DC/TČ/DH/TES/bazén → Simulink fyzikálne stavy → nezávislý QA.

Zmena v08: bezpečnostný gate dostáva skutočne pripojené EXTERNÉ vstupy T1/T2 z časových súborov namiesto vnútorných virtuálnych delay blokov. Povelové a poruchové signály v D-replay stále pochádzajú z pôvodného v07.

## 2. Importné schéma a proveniencia

Validačný kontrakt je trinásť stĺpcov, ISO 8601 UTC a presne 900 s medzi časovými bodmi:

timestamp_utc, Q_DC_available_W, T_DC_C, Q_DH_request_W, T_air_C, RH, T_pool_sensor1_C, T_pool_sensor2_C, pool_flow_m3h, P_IT_W, Q_REJECT_measured_W, main_reject_ok, backup_reject_ok.

Kategórie zdrojov: A = skutočné merania s prístrojmi a kalibráciou, B = publikované údaje s identifikáciou zdroja, C = výrobné podklady, D = syntetika a predpoklady. Test validátora odmieta falošné A, nepravidelný krok a neplatnú provenienciu.

**Pozor:** P_IT a Q_REJECT z validovaného záznamu sa zatiaľ len archivujú, nie používajú na kalibráciu COP alebo ERF. Priemer prietoku 30 m³/h v príklade je konštruovaná hodnota, nie pozorovanie.

## 3. Bazén a prvý termodynamický zákon

Ilustračný 500 m³ bazén, hladina 312,5 m². Modelová hmotnosť:

$$m=\rho V=997\cdot500=498\,500\;\mathrm{kg}.$$

$$C_w=mc_p=997\cdot500\cdot4182=2\,084\,727\,000\;\mathrm{J/K}.$$

$$E_{16\to28}=\frac{12C_w}{3{,}6\cdot10^9}=6{,}94909\;\mathrm{MWh}.$$

Ideálne akumulované teplo bez strát. Diskrétna rovnica pre 900 s:

$$T_{k+1}=T_k+\frac{900}{C_w}(Q_{\rm pool,phys}-Q_{\rm loss}).$$

Straty zostali syntetické z v04: výpar, konvekcia, radiácia, prestup do konštrukcie, dopĺňaná voda, pomocná strata.

## 4. Rozdelenie odpadového tepla

V08 nezmenil fyzické bloky redundantnej v07, preto musia zostať uzavreté bilančné rovnice:

$$Q_{\rm DC,eff}=Q_{\rm HX,phys}+Q_{\rm HP,source}+Q_{\rm REJECT,A}+Q_{\rm REJECT,B}+Q_{\rm unhandled}.$$

$$Q_{\rm HP,out}=Q_{\rm HP,source}+P_{\rm compressor}.$$

$$Q_{\rm pool,phys}=Q_{\rm HX,phys}+Q_{\rm HP,pool}.$$

Pri chybe ventilu sa pretečené teplo odoberá z REJECT, nie vytvára zo vzduchu. Pri poruche odvodu DC sa neodvedená energia explicitne zaznamenáva. Fyzikálne uzatvorenie ventilu sa nesmie odvodiť iba zo softvérového STOP.

## 5. Vstupy senzorov a nájdená regresná chyba

$$T_{1,k}=T_{\rm external1,k};\qquad T_{2,k}=T_{\rm external2,k}.$$

$$D_{\rm diff}=[|T_1-T_2|>0{,}35\;\mathrm K],\quad D_{\rm hot}=[\max(T_1,T_2)\ge27{,}70^\circ C].$$

Doplnené sú výpadok prietoku, E-STOP a neplatné meranie. Po poruche ostáva ohrev vypnutý do explicitného resetu pri odstránení chyby a pod modelovým prahom 27,65 °C.

Pri prvom v08 teste sa pridával pôvodný simulačný bias opakovane k hodnotám CSV, ktoré už bias obsahovali. Nezávislý QA to správne identifikoval. Po odstránení dvojitého bias z novej v08 bol vykonaný opakovaný beh všetkých 8 scenárov; záverečná nezávislá kontrola je PASS.

Spoločný -0,4 K bias dvoch snímačov zostáva bez nezávislej referencie nedetekovateľný. Toto je stále skutočné riziko.

## 6. Metrológia a porovnanie metód

Predpoklady triedy D: objemový prietok $\dot V=30\ \mathrm{m^3/h}$, rozdiel prívodu a návratu $\Delta T=3\ K$, nezávislá štandardná neistota teplomerov $u(T_1)=u(T_2)=0{,}2\ K$, relatívna štandardná neistota prietoku 5 %.

$$\dot m=\rho\dot V/3600=8{,}3083\;\mathrm{kg/s}.$$

$$Q_{\rm flow}=\dot m c_p\Delta T=104\,236{,}35\;\mathrm W.$$

$$u(\Delta T)=\sqrt{u(T_1)^2+u(T_2)^2}=0{,}28284\ K.$$

$$\frac{u(Q)}{Q}=\sqrt{\left(\frac{u(\dot V)}{\dot V}\right)^2+
\left(\frac{u(\Delta T)}{\Delta T}\right)^2}=0{,}10671.$$

$$\boxed{Q_{\rm flow}=104{,}24\pm11{,}12\ \mathrm{kW}\ (1\ standardna\ neistota).}$$

Nie je to meraná ani certifikovaná chyba konkrétneho prístroja.

Ak by sme namiesto prietokomeru odvodzovali výkon len z dvoch teplotných meraní celých 500 m³ vzdialených 900 s, pri rovnakej predpokladanej nezávislej chybe 0,2 K by vyšlo:

$$u(Q_{\rm pool\,dT})=\frac{C_w}{900}\sqrt{2}\cdot0{,}2
=655{,}17\ \mathrm{kW}.$$

Neistota je väčšia než špičkový výpočtový výkon bazénovej vetvy 150 kW. Na prevádzkové monitorovanie tepelného výkonu je preto potrebný kvalitný prietokomer a oddelená meraná dvojica teplôt prívodu/návratu, vrátane posúdenia korelovaných chýb.

## 7. Skutočne vykonaný replay v08

8 scenárov × 672 krokov (168 h na scenár). Maximálne odchýlky v08 od v07 po CSV normalizácii:

| Scenár | Max. dT [°C] | Max. dQ [W] | Rozdiel latch |
|---|---:|---:|---:|
| Zdravý | 1,95e-8 | 0,0340 | 0 |
| Jeden ventil zaseknutý | 2,55e-8 | 0,0292 | 0 |
| Oba ventily zaseknuté | 3,01e-8 | 0,0435 | 0 |
| Hlavný REJECT off, záloha | 1,95e-8 | 0,0340 | 0 |
| Oba REJECT off bez redukcie | 1,95e-8 | 0,0340 | 0 |
| Oba REJECT off s redukciou | 1,95e-8 | 0,0340 | 0 |
| Spoločný bias | 1,95e-8 | 0,0340 | 0 |
| Kombinovaná porucha | 2,90e-8 | 0,0418 | 0 |

Nezávislá kontrola v08 z pôvodných CSV: **91 565 PASS**. Validujú sa externé merané signály oproti záznamom, blokovanie, energetické zákony, dva ventily, oba REJECT, porovnanie stavu vody a výstupov s v07.

![[externe_snimace_v08_SK.png]]
![[regresia_tepla_v08_SK.png]]

## 8. Obmedzenia a ďalšie kroky

Reálna kalibrácia je zatiaľ BLOCKED_REAL_DATA: chýbajú fyzické nezávislé merania, časové pečiatky z prístrojov, dokumenty ich kalibrácie, hydraulická topológia a údaje o prietokoch, výrobné mapy COP, meraný stav REJECT a 8760 h zdrojových profilov. Vstupná zložka source_D je iba syntetický replay vytvorený z v07 a nesmie byť zamieňaná s A meraním.

Technické súbory: matlab/pool_measurement_v08/DC_Bazen_Externe_Merania_v08_SK.slx, spusti_merania_replay_v08_sk.m, qa_nezavisla_v08_sk.py, priprav_D_replay_v08.py, neistoty_merania_v08_sk.py. Výsledky: results/pool_measurement_v08/vysledky_v08_SK.json, QA_NEZAVISLA_V08_SK.json, NEISTOTY_MERANIA_V08_SK.json, sim_v08_*.csv a 3 správy SK/EN/RU.

Reprodukcia: MATLAB R2026a z priečinka matlab/pool_measurement_v08 vyvolať spusti_merania_replay_v08_sk. Potom Python qa_nezavisla_v08_sk.py. Generátor syntetických D zdrojov je jednorazový a odmieta prepísanie.

Normatívny rámec: EU 2024/1364 https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj. Na presný typ bazéna sa musí ešte zvoliť aktuálny príslušný normový rámec a konsolidovaná legislatíva, vrátane príslušnej STN EN 15288-1+A1:2024. Žiadna certifikovaná zhoda sa týmto netvrdí.
