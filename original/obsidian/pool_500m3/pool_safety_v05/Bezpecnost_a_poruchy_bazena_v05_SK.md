---
tags: [datacentrum, bazen, Stateflow, Simulink, bezpecnost, snimace, FMEA]
status: VERIFIED_SIMULINK_SYNTHETIC
date: 2026-10-23
language: sk
---
# V05 - bezpečnostná vrstva bazéna, poruchy snímačov a hydrauliky

> [!warning] Hranice dokazovania
> Sedem scenárov v05 bolo skutočne simulovaných na **syntetických** vstupoch. Skutočné senzory NIE SÚ merané. Dva testované snímače sú založené na T_model plus pridaný bias, takže model "pozná pravú teplotu". Detekcia rovnakej chyby oboch senzorov v reálnom objekte **nie je zaručená**. Ide o skúšku algoritmu, nie certifikáciu funkčnej bezpečnosti.

## 1. Spätnoväzbová architektúra

V05 je samostatná nová verzia vytvorená kopírovaním v04. Pôvodné modely v85 a v04 ostali nezmenené.

Vstup je rozšírený z 11 na 16 polí. Prvých 11 polí sú rovnaké signály ako pri v04 (odpadové teplo DC, teplota zdroja, dopyt DH, vzduch, vlhkosť, aktivita, plachta, IT_ok, BAZEN_ok, TES_ok, HX_ok). Dodatočné kanály:
12. Chyba snímača 1 (K),
13. Chyba snímača 2 (K),
14. Potvrdenie prietoku 0/1,
15. Núdzové tlačidlo 0/1,
16. Výslovný ručný RESET 0/1.

\`\`\`text
Poruchy -> senzory modelu -> SAFETY GATE -> efektívny BAZEN_ok -> v04 fyzika
                   ^             |
                   |             +--> blokovanie a latch -> pamäť predchádzajúceho kroku
                   |
              T_bazena (diskrétne uložený stav)
\`\`\`

Neobmedzuje sa IT_ok, takže chyba bazéna nespôsobuje automaticky stratu chladiacej funkcie serverov. Pri bazénovom stop-e musí nevyužité teplo zostať v iných vetvách a samostatnom odovzdaní do REJECT.

## 2. Detekčné podmienky a návrhové prahy

$T_1=T_{\mathrm{model}}+b_1$ a $T_2=T_{\mathrm{model}}+b_2$, kde $b_i$ je syntetická injekcia odchýlky snímača.

$$D_{\rm disagree}=[|T_1-T_2|>0{,}35\ \mathrm K].$$

$$D_{\rm plausibility}=[|b_1|>0{,}45\ \mathrm K]\lor[|b_2|>0{,}45\ \mathrm K].$$

$$D_{\rm hot}=[T_1\ge27{,}70^\circ C]\lor[T_2\ge27{,}70^\circ C].$$

$$D_{\rm flow}=[\mathrm{flow\_ok}=0],\quad
D_{\rm eStop}=[\mathrm{EStop}=1].$$

$$D_k=D_{\rm disagree}\lor D_{\rm plausibility}\lor D_{\rm hot}
\lor D_{\rm flow}\lor D_{\rm eStop}\lor D_{\rm nonfinite}.$$

**Prahy sú modelové parametre**, nie výrobné bezpečnostné nastavenia alebo hodnota garantovaná normou. Matematická "plausibility" overuje bias proti známemu T_model a nemôže sa automaticky preniesť do systému bez referenčného snímača.

## 3. Bezpečnostné blokovanie so západkou

Nech $L_{k-1}$ je predchádzajúci stav blokovania a $R_k$ povel ručného RESET.

$$L_k=\begin{cases}
1,&D_k=1,\\
0,&D_k=0\ \land\ L_{k-1}=1\ \land\ R_k=1\ \land\ T_{\rm model}\le27{,}65^\circ C,\\
L_{k-1},&\text{inak}.
\end{cases}$$

Pri $L_k=1$ sa vždy nastaví efektívny signál $\mathrm{BAZEN\_ok}=0$. Vzápätí existujúce fyzikálne jadro v04 dá $Q_{\mathrm{pool},k}=0$, bez predpokladu okamžitého zastavenia IT chladenia. Ručný reset v okamihu trvajúcej poruchy neodomkne výmenník.

V reálnom systéme budú potrebné nezávislé relé, hardvérové blokovanie čerpadla, dohľad nad ventilmi a pri nesúlade meraní test bezpečného stavu. Model aktuálne **nedokazuje úroveň SIL ani PL**.

## 4. Energetické invarianty pri poruche

Aj počas odstavenia bazéna sa musia dodržiavať:

$$Q_{\rm DC,av}=Q_{\rm direct}+Q_{\rm HP,source}+Q_{\rm reject}.$$

$$Q_{\rm HP,out}=Q_{\rm HP,pool}+Q_{\rm HP,DH}+Q_{\rm HP,TES}
=Q_{\rm HP,source}+P_{\rm compressor}.$$

$$Q_{\rm pool}=Q_{\rm direct}+Q_{\rm HP,pool}.$$

$$C(T_{k+1}-T_k)=900(Q_{\rm pool,k}-Q_{\rm loss,k}),$$

$$C=997\cdot 500\cdot 4182=2\,084\,727\,000\quad\mathrm{J/K}.$$

V každej skúške $Q_{\rm pool}\ge0$, $Q_{\rm pool}\le150$ kW, teplota vody neprekročila modelový strop 27,75 °C. Výpočtové zachovanie energie bolo nezávisle overené aj čítaním CSV v Pythone.

## 5. Skutočne vykonané scenáre MATLAB R2026a

Každý prípad: 168 hodín, 672 krokov s dĺžkou 900 s. Počas poruchy sa nezastavuje celá energetika DC.

| Scenár | Zablokované hodiny | Bazén MWh | Reset prijatý |
|---|---:|---:|---:|
| Zdravá prevádzka | 0 | 10,39308 | 0 |
| Rozdiel snímačov | 8 | 10,19676 | 1 |
| Pomalý drift senzora | 13,75 | 10,34316 | 1 |
| Výpadok prietoku | 14 | 10,35232 | 1 |
| E-STOP | 18 | 10,31058 | 1 |
| Reset počas poruchy | 18 | 10,25458 | 1 (po odstránení chyby) |
| Súhlasne posunuté senzory | 15 | 10,35938 | 1 |

V simulátore oba rovnako posunuté senzory vyhodnotila kontrola voči T_model, ale v praxi spoločný posun senzorov môže byť nerozpoznateľný bez ďalšieho nezávislého merania.

**Nezávislý QA:** 32 928 PASS v siedmich scenároch nad uloženými CSV. Model bez porúch súhlasil s v04 pre teplotu, bazénový výkon a REJECT v tolerancii $10^{-7}$. Pôvodný v85 zachoval SHA-256.

## 6. FMEA / kontrolná matica

| Porucha | Simulovaný detektor | Bezpečná reakcia | Chýbajúca fyzická evidencia |
|---|---|---|---|
| Rozpojenie snímačov | $|T_1-T_2|>0,35$ | STOP prívodu tepla bazénu, latch | Reálne nezávislé snímače |
| Drift jedného senzora | Kontrola voči T_model | STOP, latch | Referenčné meranie a kalibrácia |
| Nulový prietok | flow_ok=0 | STOP, latch | Prietokomer, ventil a čas odozvy |
| E-STOP bazéna | manuálny vstup | STOP, latch | Hardvérovo nezávislý reťazec |
| Predčasný reset | Aktívne D=1 | Blokovanie ostáva | Reset politiky a oprávnenia |
| Spoločná chyba T1/T2 | Modelová kontrola bias | STOP v simulátore | Možná spoločná chyba v realite |
| Porucha chladiča IT | **Nesimulované ako fyzická porucha** | Nezávislý REJECT požadovaný | Redundantné čerpadlá/chladiče |

## 7. Reprodukcia

MATLAB R2026a: z adresára OneDrive/Projects/DataCenter_Heat_Reuse/matlab/pool_safety_v05 spustiť spusti_poruchy_v05_sk.m.

Python po exporte CSV: QA_v05_sk.py.

Model: DC_Bazen_Bezpecnost_v05_SK.slx. Výsledky: results/pool_safety_v05/resultaty_v05_SK.json, QA_V05_SK.json, scenar_*.csv.

## 8. Zdroje a ďalší technický krok

- EU Delegated Regulation 2024/1364, Energy Reuse Factor: https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj
- Published historical Slovak pool text, §8(7): https://static.slov-lex.sk/static/SK/ZZ/2012/308/vyhlasene_znenie.print.html
- STN EN 15288-1+A1:2024 (public description): https://normy.normoff.gov.sk/norma/139372/nahlad/

Primárny ďalší krok: nahradiť $T_{\rm model}+b$ dvomi **nezávislými fyzickými meraniami** s oneskorením, nastaviť fail-safe limit pomocou teplotných neurčitostí, prietoky m_dot a výrobné COP, simulovať poruchu ventilu zostávajúceho otvoreného a zlyhanie redundantného odvodu tepla. V05 nie je priemyselný bezpečnostný certifikát.
