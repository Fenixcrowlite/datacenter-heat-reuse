---
tags: [datacentrum, bazen, stateflow, simulink, termodynamika, tes]
date: 2026-10-23
status: VERIFIED_SYNTHETIC_CLOSED_LOOP
language: sk
---
# Uzavretá regulácia Stateflow v04: DC, bazén 500 m³, DH a TES

> [!warning] Hranice modelu
> Model v04 je novo postavený uzavretý dispečer s reálnou spätnou väzbou v Simulinku, ale **vstupy DC sú syntetické**. Pôvodný Stateflow v85 zostal bez zmeny a **nie je vnútri nového v04 vykonávací blok**. Simulácia nie je certifikáciou bezpečnosti ani predikciou reálneho ročného výkonu.

## 1. Bloková architektúra a režimy

Tok: dostupné teplo DC, teplota zdroja, dopyt DH a počasie -> Stateflow + termodynamický distribútor -> priamy HX / tepelné čerpadlo / DH / TES / REJECT -> aktualizácia teploty bazéna a energie TES -> **spätná väzba v ďalšom kroku**.

Skutočné stavy Stateflow: BEZ_ZDROJA (0), PRIAMY_VYMENNIK (1), TEPELNE_CERPADLO (2), CERPAJ_Z_TES (3), IT_BEZPECNE_ODSTAVENIE (4). Stav ovplyvňuje zdrojové teplo, jeho teplota, požiadavka bazéna, IT_ok a energia TES.

## 2. Výpočet objemu, hmotnosti a prvého zákona

Príklad geometrie: $25\times12{,}5\times1{,}6$ m, nie certifikovaný rozmer plaveckého bazéna.

$$V=25\cdot12{,}5\cdot1{,}6=500\,\mathrm{m^3},\quad A=25\cdot12{,}5=312{,}5\,\mathrm{m^2}.$$

$$m=\rho V=997\cdot500=498\,500\,\mathrm{kg}.$$

$$C=\rho V c_p=997\cdot500\cdot4182=2\,084\,727\,000\,\mathrm{J/K}.$$

$$E_{16\rightarrow28}=\frac{12C}{3{,}6\cdot10^9}=6{,}94909\ \mathrm{MWh}.$$

Toto je iba uložená energia bez dynamických strát. Diskrétny termodynamický zákon s $\Delta t=900$ s:

$$T_{k+1}=T_k+\frac{900}{C}(Q_{{\rm pool},k}-Q_{{\rm loss},k}).$$

Pri každom kroku sa zvlášť testuje, že $(T_{k+1}-T_k)C/900=Q_{\rm pool}-Q_{\rm loss}$ [W].

## 3. Zloženie tepelných strát

$$Q_{\rm loss}=Q_{\rm evap}+Q_{\rm conv}+Q_{\rm rad}+Q_{\rm construction}+Q_{\rm makeup}+2000\,\mathrm W.$$

$$p_{\rm sat}(T)=0{,}61094\exp(17{,}625T/(T+243{,}04))\quad[\mathrm{kPa}].$$

$$\dot m_{\rm evap}=\max\left(0,4\cdot10^{-5}A[p_{\rm sat}(T_w)-RH\,p_{\rm sat}(T_a)]F_a(1-0{,}90K)\right).$$

$$Q_{\rm evap}=2{,}44\cdot10^6\dot m_{\rm evap}.$$

$$Q_{\rm conv}=3A(T_w-T_a)(1-0{,}75K).$$

$$Q_{\rm rad}=0{,}95\sigma A[(T_w+273{,}15)^4-(T_a-2+273{,}15)^4](1-0{,}75K).$$

$$\sigma=5{,}670374419\cdot10^{-8}\,\mathrm{W\,m^{-2}K^{-4}}.$$

$$Q_{\rm construction}=800(T_w-20),\quad Q_{\rm makeup}=\dot m_{\rm evap}4182(T_w-15).$$

$K$ je stav plachty, $F_a$ aktivitný koeficient. Predpokladané zníženia plachtou aj kondenzačné teploty sú výlučne scenárové. Záporná konvekcia znamená zisk tepla vody, keď je okolie teplejšie.

## 4. Termostat a tvrdý modelový limit teploty

Termostat: zapnutie 27,35 °C, vypnutie 27,65 °C; cieľ aktuálnej regulácie 27,58 °C. Oddelený limit v matematickom modeli 27,75 °C.

$$Q_{\rm safe}=\max(0,C(27{,}75-T)/900+Q_{\rm loss}).$$

$$Q_{\rm target}=\max(0,C(27{,}58-T)/900+Q_{\rm loss}).$$

$$Q_{\rm request}=\min(150\,000,Q_{\rm safe},Q_{\rm target})$$

pri zapnutom termostate, inak nula. Pri BAZEN_ok=0 je nulová požiadavka nezávisle od teploty. Reálny chybný/oneskorený snímač sa v04 **neoveruje**.

## 5. Priamy HX a tepelné čerpadlo

Príkon do priamej vetvy bazéna:

$$Q_{\rm direct,max}=\min(Q_{\rm pool,req},Q_{\rm DC,av},150\,000,\max(0,8500(T_{\rm DC}-T_w-5))).$$

Konštanta 8500 W/K a minimálny rozdiel teplôt 5 K nie sú overeným projektom reálneho výmenníka.

$$COP_{\rm scenar}=\operatorname{clip}\left(0{,}43\frac{52+273{,}15}{\max[5,52-(T_{\rm DC}-5)]},2{,}5,6\right).$$

$$Q_{\rm HP,out,max}=\min(200\,000,55\,000 COP,Q_{\rm DC,rem}/(1-1/COP)).$$

$$P_{\rm compressor}=Q_{\rm HP,out}/COP,\qquad Q_{\rm HP,source}=Q_{\rm HP,out}-P_{\rm compressor}.$$

Pohon kompresora má strop 55 kW; tepelné čerpadlo výstup max. 200 kW. Výstupná voda je scenárovo modelovaná pri 52 °C, nevychádza z katalógového COP(T,PLR).

## 6. Dispečer, sieť a prvý zákon

Pri priorite bazéna sa pre DH rezervuje do 50 kW zo zdroja TČ, ďalší výkon naplní bazén, sieť a pri prebytku TES. Pre DH môže TES vybiť maximálne 80 kW, TČ nabíja TES max. 70 kW.

$$\boxed{Q_{\rm DC,av}=Q_{\rm direct}+Q_{\rm HP,source}+Q_{\rm reject}.}$$

$$\boxed{Q_{\rm HP,out}=Q_{\rm HP,pool}+Q_{\rm HP,DH}+Q_{\rm HP,TES}=Q_{\rm HP,source}+P_{\rm compressor}.}$$

$$Q_{\rm pool}=Q_{\rm direct}+Q_{\rm HP,pool},\qquad Q_{\rm DH}=Q_{\rm HP,DH}+Q_{\rm TES,discharge}.$$

$$Q_{\rm DH,unmet}=\max(0,Q_{\rm DH,demand}-Q_{\rm DH}).$$

Paux je oddelená elektrina pre obehové čerpadlá a pohony. Kompresorová elektrina **nie je teplo obnoviteľné z DC**.

Pri IT_ok=0 je tok z DC presmerovaný do nezávislého odvodu; nabíjanie TES a vykurovanie bazéna z DC sa zruší. Vysokotemperatúrne TES môže naďalej kryť požiadavku DH. Táto funkcia v modeli nenahrádza certifikovanú fyzickú poistku chladenia IT.

## 7. Energetická bilancia TES

$E_{\max}=0{,}90$ MWh; $E_0=0{,}45$ MWh; nabíjacia účinnosť 0,93; vybíjacia účinnosť 0,91; modelovaná strata $0{,}2\%$ za deň.

$$Q_{\rm TES,standing}=0{,}002 E_{\rm TES}/86400.$$

$$E_{\rm TES,k+1}=E_{\rm TES,k}+900\left(0{,}93Q_{\rm charge}-Q_{\rm discharge}/0{,}91-Q_{\rm TES,standing}\right).$$

Obmedzenia: $0\le E_{\rm TES}\le E_{\max}$, súčasné nabíjanie a vybíjanie nie je povolené. Nezahrnuté sú stratifikácia ani reálne minimálne teploty výmenníkov.

## 8. Vykonané simulácie (osem krát 672 intervalov)

| Scenár | Bazén MWh | Sieť MWh | Kompresor MWh | Deficit DH MWh |
|---|---:|---:|---:|---:|
| Základ | 10,393 | 16,101 | 4,764 | 1,539 |
| Bazén vypnutý | 10,021 | 16,101 | 4,821 | 1,539 |
| IT STOP 24 h | 10,309 | 14,570 | 4,558 | 3,070 |
| Zdroj 0 počas 24 h | 10,309 | 14,570 | 4,558 | 3,070 |
| Zdroj +12 °C | 10,401 | 15,084 | 2,744 | 2,556 |
| Bez plachty | 11,410 | 16,172 | 4,996 | 1,468 |
| TES vypnuté | 10,393 | 15,605 | 4,581 | 2,035 |
| Vysoký dopyt DH | 10,393 | 22,884 | 6,003 | 10,716 |

V základnom prípade príjem zo zdroja DC $28{,}56$ MWh = zdroj TČ $19{,}263$ MWh + HX priamo $3{,}051$ MWh + nezávislý REJECT $6{,}246$ MWh. Bazén získal $10{,}393$ MWh, voda stratila $3{,}687$ MWh a uložila približne $6{,}706$ MWh. Pomocné elektrické pohony spotrebovali scenárovo $0{,}297$ MWh nad rámec kompresora.

![[priebeh_teploty_v04_SK.png]]

## 9. QA a presné limity

- MATLAB/Stateflow R2026a: 8 scenárov PASS, teplotné maximum 27,58 °C.
- Nezávislá kontrola Python z originálnych CSV: **65 493 PASS**.
- Model v04 bol po odstránení warningov lokálnych symbolov Stateflow znovu skompilovaný a všetky scenáre zopakované bez warningov.
- Pôvodná v85 sa nezmenila, jej SHA-256: 2a9de22c0c55e8c4a87f7b0e0cfe9cd97db08c991f09d98361b009de310adde7.

**Neoverené:** presné fyzické údaje DC, aktualizované predpisy a úplné licencované STN, hydraulický výmenník, skutočné COP výrobcu, bazénová HVAC a odvlhčenie, teplotná homogenita vody, senzorické poruchy, ročné časové rady a formálne previazanie s v85 chartom.

## 10. Reprodukcia

MATLAB: z priečinka OneDrive/Projects/DataCenter_Heat_Reuse/matlab/pool_feedback_v04 spustiť spusti_scenare_v04_sk.m.

Python: z toho istého priečinka spustiť qa_nezavisla_v04_sk.py a vytvor_pdf_v04_3jazyky.py.

Súvisiace dokumenty a súbory:
- [[Dispecer_Bazen_v04_SK.pdf]]
- [[Dispecer_Bazen_v04_EN.pdf]]
- [[Dispecer_Bazen_v04_RU.pdf]]
- DC_Bazen_Uzavreta_Regulacia_v04_SK.slx (nový samostatný model)
- spusti_scenare_v04_sk.m, alokuj_teplo_v04_sk.txt, vypocitaj_dopyt_bazena_sk.txt, volba_rezimu_v04_sk.m
- Results/pool_feedback_v04/scenar_*.csv, vysledky_dispecer_v04_SK.json, QA_NEZAVISLA_V04_SK.json.

## 11. Literatura a predpisy

- EU Delegated Regulation 2024/1364: https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj
- Slov-Lex 308/2012, historické znenie: https://static.slov-lex.sk/static/SK/ZZ/2012/308/vyhlasene_znenie.print.html
- STN EN 15288-1+A1:2024: https://normy.normoff.gov.sk/norma/139372/nahlad/
- ASHRAE natatorium: https://handbook.ashrae.org/handbooks/F17/SI/F17_Ch36/f17_ch36_si.aspx

Uvedená archívna vyhláška a nevykonaná úplná kontrola STN sa nesmú vydávať za schválenie projektu podľa aktuálnej legislatívy.
