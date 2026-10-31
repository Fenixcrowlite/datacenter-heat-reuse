---
tags: [datacentrum, odpadove-teplo, bazen, matlab, simulink, termodynamika]
status: SCENARIO_VALIDATED_PYTHON
jazyk: sk
objem_m3: 500
created: 2026-10-23
---
# Ohrev bazéna 500 m³ odpadovým teplom dátového centra

> [!important] Rozsah a dôveryhodnosť
> Tento dodatok nemení existujúce validované modely **DataCenter Heat Reuse v85/v86**. Ide o nový odberný tepelný uzol. Číselné parametre sú **projektové scenáre (trieda D)**, nie namerané hodnoty. Skutočná implementácia potrebuje výmenníkový návrh, hydrauliku, meranie teplôt a prietokov a nezávislé IT chladenie.

## 1. Úloha a geometria

- Objem: $V=500\,\mathrm{m^3}=500\,000\,\mathrm{L}$.
- Geometria príkladu: dĺžka $L=25$ m, šírka $W=12{,}5$ m, hĺbka $d=1{,}6$ m.
- Plocha vody: $A=L W=312{,}5\,\mathrm{m^2}$, objem $V=LWd=500\,\mathrm{m^3}$.
- Počiatočná teplota: $T_0=16^\circ\mathrm C$, cieľová $T_{\mathrm{zad}}=28^\circ\mathrm C$.
- Hustota vody $\rho=997\,\mathrm{kg/m^3}$, merná tepelná kapacita $c_p=4182\,\mathrm{J/(kg\,K)}$.

Energia uložená pri ohreve o $\Delta T$:

$$E=m c_p \Delta T=\rho Vc_p\Delta T.$$

Rozmerová kontrola: $(\mathrm{kg/m^3})(\mathrm{m^3})(\mathrm{J/kg/K})(\mathrm K)=\mathrm J$.

$$C=\rho Vc_p=997\cdot500\cdot4182=2\,084\,727\,000\ \mathrm{J/K}.$$

$$C=0{,}57909\ \mathrm{MWh/K},\qquad E_{16\to28}=6{,}94909\ \mathrm{MWh}.$$

**Dôležité:** $6{,}95$ MWh neobsahuje nijaké dynamické tepelné straty. $E/P$ poskytuje iba *ideálny* minimálny čas pri konštantnom výkone.

## 2. Prvý termodynamický zákon pre bazén

Ak uvažujeme vodu ako jedno dokonale zmiešané teplotné teleso:

$$\boxed{C\frac{dT}{dt}=\dot Q_{\mathrm{dod}}-\dot Q_{\mathrm{vypar}}-\dot Q_{\mathrm{konv}}-\dot Q_{\mathrm{rad}}-\dot Q_{\mathrm{pod}}-\dot Q_{\mathrm{dop}}-\dot Q_{\mathrm{ostatne}}}$$

Dynamická modelová veličina je $T(t)$ [°C], čas je v sekundách, každý $\dot Q$ v [W]. Straty **môžu byť algebraicky záporné** pri prestupe tepla z okolia do studenej vody.

### 2.1 Vyparovanie podľa zjednodušenej korelácie ASHRAE

Použitá redukovaná empirická rovnica pre vnútorné bazény (tlak je v kPa):

$$\dot m_{\rm vypar}=4\cdot10^{-5} A\max(p_{\rm sat}(T)-p_a,0)\,F_a(1-r_{\rm kryt}K),$$

kde $K\in\{0,1\}$ značí zakrytie, $r_{\rm kryt}=0{,}90$ je predpokladaná redukcia, $F_a=1$ počas prevádzky, $F_a=0{,}5$ po zatvorení.

$$p_a=\varphi p_{\rm sat}(T_a),\quad \varphi=0{,}6,\quad T_a=29^\circ\mathrm C.$$

Aproximácia tlaku nasýtenej vodnej pary:

$$p_{\rm sat}(T)=0{,}61094\exp\!\left(\frac{17{,}625T}{T+243{,}04}\right)\quad[\mathrm{kPa}].$$

$$\dot Q_{\rm vypar}=\dot m_{\rm vypar}\,h_{fg},\quad h_{fg}=2{,}44\cdot10^6\ \mathrm{J/kg}.$$

**Obmedzenie:** výpar silne závisí od počtu plavcov, turbulencie, vzduchotechniky a vlhkosti; korelácia nenahrádza kalibrovanú psychrometrickú bilanciu.

### 2.2 Konvekcia vody so vzduchom

$$\dot Q_{\rm konv}=h A (T-T_a)(1-r_{\rm konv}K),\quad h=3\,\mathrm{W/(m^2K)},\ r_{\rm konv}=0{,}75.$$

Pre $T=28^\circ\mathrm C<T_a=29^\circ\mathrm C$ je člen záporný: vzduch *ohrieva* vodu.

### 2.3 Tepelné žiarenie

$$\dot Q_{\rm rad}=\varepsilon\sigma A [(T+273{,}15)^4-(T_{\rm stena}+273{,}15)^4]\,(1-0{,}75K),$$

$\varepsilon=0{,}95$, $\sigma=5{,}670374419\cdot10^{-8}\,\mathrm{W\,m^{-2}K^{-4}}$, $T_{\rm stena}=27^\circ\mathrm C$.

### 2.4 Prestup cez dno a steny

$$\dot Q_{\rm pod}=UA(T-T_{\rm zem}),\quad UA=800\ \mathrm{W/K},\quad T_{\rm zem}=20^\circ\mathrm C.$$

Zlúčená vodivosť $UA$ je scenárový parameter; skutočná hodnota závisí od geometrie, hydroizolácie, izolácie a zeminy.

### 2.5 Doplňovaná voda a ostatné straty

$$\dot Q_{\rm dop}=\dot m_{\rm vypar}c_p(T-T_{\rm privod}),\quad T_{\rm privod}=15^\circ\mathrm C.$$

Konštantný doplnkový odvod $\dot Q_{\rm ostatne}=2\,\mathrm{kW}$ reprezentuje technologické odbery; **nie je to nameraná spotreba filtrácie**.

## 3. Zdroj z dátového centra

Referenčný projekt uvádza $P_{\rm IT,rated}=10$ MW, priemerné využitie $f_u=0{,}82$, scenárový podiel záchytu $f_r=0{,}85$:

$$\dot Q_{\rm DC,pot}=P_{\rm IT,rated} f_u f_r=6{,}97\,\mathrm{MW}.$$

Potenciál zdroja **nie je** dodané teplo do bazéna. Zvažujeme oddelenú vetvu $\dot Q_{\rm DC,v}=0{,}5$ MW s nezávislou ochranou IT chladenia.

**Priamy výmenník:** zdrojová teplota predpoklad 35 °C, minimálny teplotný rozdiel 3 K, voda najviac ~28,2 °C. Skutočný výkon musí potvrdiť tepelno-hydraulický návrh výmenníka.

**Tepelné čerpadlo:** pre nízkoteplotný zdroj 25 °C je použitá efektívna scenárová hodnota $COP=4$:

$$COP=\frac{\dot Q_{\rm TC,out}}{P_{\rm el}},\quad P_{\rm el}=\frac{\dot Q_{\rm TC,out}}{COP},$$

$$\dot Q_{\rm zdroj}=\dot Q_{\rm TC,out}-P_{\rm el}=\dot Q_{\rm TC,out}(1-1/COP).$$

Pre výkon do bazéna 150 kW: $P_{\rm el}=37{,}5$ kW, odobraté teplo dátového centra $\dot Q_{\rm zdroj}=112{,}5$ kW. Elektrina **nie je odpadové teplo** a nesmie sa dvakrát započítať.

## 4. Regulácia a numerická integrácia

- Žiadaná voda 28 °C, hysterezia: zapnutie pod 27,8 °C, vypnutie nad 28,2 °C.
- Otváracie hodiny 08:00–20:00: aktivita 1, plachta 0.
- Mimo prevádzky 20:00–08:00: aktivita 0,5, plachta 1.
- Scenáre dodaného výkonu 75 / 150 / 300 kW, režim TČ aj priamy výmenník.
- Varianty relatívnej vlhkosti 40 / 60 / 80 % a bez plachty.
- Výpočtový krok $\Delta t=300$ s, 7 dní. Kontrola na 60 s.

Explicitný Euler:

$$T_{k+1}=T_k+\frac{\Delta t}{C}\left(\dot Q_{\rm dod,k}-\dot Q_{\rm strata,k}\right).$$

Kontrola diskrétnej energie:

$$C(T_N-T_0)-\sum_{k=0}^{N-1}(\dot Q_{\rm dod,k}-\dot Q_{\rm strata,k})\Delta t\approx0.$$

Porovnanie konečnej teploty pri rozdielnych časových krokoch s hysterezisovým relé môže vykazovať fázový posun cyklov. Treba porovnať tiež prvé dosiahnutie cieľa, integrovanú energiu a celý priebeh.

## 5. Výsledky

| Experiment | Dosiahnutie 28 °C | Dodané teplo za 7 dní | Elektrina TČ |
|---|---:|---:|---:|
| TČ 75 kW, plachta | 98,18 h | 9,675 MWh | 2,419 MWh |
| TČ 150 kW, plachta | 47,43 h | 10,863 MWh | 2,716 MWh |
| TČ 300 kW, plachta | 23,41 h | 11,525 MWh | 2,881 MWh |
| Priamy výmenník 150 kW | 47,43 h | 10,863 MWh | 0 MWh kompresor |
| TČ 150 kW, bez plachty | 46,86 h | 12,013 MWh | 3,003 MWh |
| TČ 150 kW, RH 40 % | 50,84 h | 12,900 MWh | 3,225 MWh |
| TČ 150 kW, RH 80 % | 45,40 h | 9,138 MWh | 2,284 MWh |

> [!note] Interpretácia 7-dňovej energie
> Sedemdňový súčet zahŕňa ohrev zo 16 °C aj následné udržiavanie. Scenáre s väčším výkonom zohrievajú vodu rýchlejšie a potom ju dlhšie udržiavajú, preto sa celkové dodávky za 7 dní nemusia znižovať so zvyšujúcim sa inštalovaným výkonom.

Teplonosná strata pri 28 °C: počas prevádzky **52,13 kW**, pod plachtou **10,77 kW**. Jednoduchý 12+12 hodinový vážený priemer vychádza **31,45 kW**, iba pri konštantnej 28 °C.

## 6. Validácia a rozdiel medzi softvérmi

- Python: bilancia energie pri kroku 300 s má rezíduum $7{,}15\cdot10^{-14}$ MWh, keďže je počítaná na rovnakom časovom kroku.
- Python: $\sum Q_{\mathrm{TC,out}}-\sum Q_{\mathrm{DC}}-\sum W_{\mathrm{TC}}$ je numericky ~0.
- Kontrola $\Delta t=60$ s vs 300 s môže na úplnom konci 7 dní vykazovať rozdiel pre hystereziu. Samotná posledná vzorka nie je vhodná na určenie chyby integrátora; overiť čas dosiahnutia cieľa a energetickú bilanciu.
- MATLAB/Simulink: samostatný model s integrátorom, relačným termostatom, blokom strát a časovým harmonogramom. Súbor simulink_akceptacia_SK.json uvádza skutočný výsledok po jeho vykonaní.

## 7. Čo ešte potrebuje skutočný projekt

1. Meranie prietokov a teplôt zdrojového okruhu DC.
2. Katalógový výkon výmenníka pri danej aproximačnej teplote a čerpaní.
3. COP(Tzdroj, T výstup, PLR) alebo výrobcom overená mapa tepelného čerpadla.
4. Vzduchotechniku, prevádzkovú vlhkosť, plochu hladiny a reálny režim plavcov.
5. Hydraulickú schému s oddelením okruhov, dávkovaním chemikálií a bezpečnostnými poistkami.
6. Primárnu bezpečnosť a úplne nezávislé chladenie dátového centra.
7. Ročný scenár počasia, údržby, času plachty a optimalizáciu prevádzkových nákladov.

## 8. Súvisiace artefakty

- [[Vypocty_a_simulacie_bazen_500m3_SK]] - prehľad a výsledky
- [[Bazen_500m3_SK.pdf]] - kompletná technická správa SK
- [[Bazen_500m3_EN.pdf]] - English version
- [[Bazen_500m3_RU.pdf]] - русская версия
- [[priebeh_teploty_simulink_SK.png]] - skutočný graf zo Simulinku (ak existuje)
- Projekt: OneDrive/Projects/DataCenter_Heat_Reuse/matlab/pool_500m3/
- CSV a kontrolné JSON: OneDrive/Projects/DataCenter_Heat_Reuse/results/pool_500m3_v01/

## 9. Zdroje a zodpovedajúce rovnice

- **ASHRAE HVAC Applications, Indoor Swimming Pools**: aproximácia vyparovania a activity factors. https://handbook.ashrae.org/Handbooks/A23/SI/A23_Ch06/a23_ch06_si.aspx
- **EnergyPlus Engineering Reference, Indoor Swimming Pool**: výpar, konvekcia a hranice modelu. https://energyplus.net/assets/nrel_custom/pdfs/pdfs_v22.1.0/EngineeringReference.pdf
- **Interný projekt**: docs/Assumptions_and_Parameters.md, MASTER_STAGEBOARD_v86.md; parametre pre scenár, nie validáciu reálnej prevádzky.
