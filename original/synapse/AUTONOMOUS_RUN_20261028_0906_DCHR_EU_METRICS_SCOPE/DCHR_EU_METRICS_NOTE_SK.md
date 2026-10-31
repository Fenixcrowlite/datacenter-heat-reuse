# DCHR | EU ukazovatele dátového centra: samostatný výpočtový prototyp

**Stav:** overený syntetický výpočet, **nie** certifikácia súladu s právnymi predpismi, **nie** validácia fyzikálneho modelu a **nie** úplný primárny sign-off zdroja č. 25.

## 1. Normatívne definície a hranice merania

Nariadenie Komisie (EÚ) 2024/1364, príloha III, definuje ukazovatele:

| Ukazovateľ | Vzorec | Vstupy | Jednotka |
|---|---|---|---|
| PUE | E_DC / E_IT | celková energia DC / energia IT | 1 |
| ERF | E_REUSE / E_DC | opätovne využitá energia / celková energia DC | 1 |
| REF | E_RES-TOT / E_DC | obnoviteľná energia / celková energia DC | 1 |
| WUE | W_IN / E_IT | spotreba vody / energia IT | m³/MWh |

V implementácii sú energetické vstupy v **kWh** a voda v **m³**. Pri WUE sa E_IT explicitne konvertuje z kWh na MWh delením 1000. Všetky čitatele a menovatele musia zodpovedať rovnakému časovému obdobiu a hranici merania.

**Dôležité:** tepelný výkon dodaný do bazéna po tepelnom čerpadle sa nesmie automaticky dosadiť ako E_REUSE. Výstup tepelného čerpadla môže zahŕňať dodatočnú elektrickú prácu. Bez overeného meracieho rozhrania nie je možné stanoviť regulatórny ERF.

## 2. Odlišné prahové hodnoty

Smernica (EÚ) 2023/1791 rozlišuje:

- **Článok 12 ods. 1:** nahlasovanie údajov pri inštalovanom IT príkone **najmenej 500 kW** (s uvedenými výnimkami).
- **Článok 26 ods. 6–7:** využívanie odpadového tepla alebo posúdenie technickej a ekonomickej realizovateľnosti pri **celkovom menovitom energetickom príkone nad 1 MW**, s podmienkami a výnimkami.

Ide o **dve odlišné veličiny**. Program ich nepriraďuje k jednej univerzálnej hodnote „výkon dátového centra“. Výsledné príznaky sú orientačné; právne uplatnenie závisí od transpozície, výnimiek a aktuálneho konsolidovaného znenia.

## 3. Reprodukovateľný syntetický príklad

Vstupy: E_DC = 1 200 000 kWh, E_IT = 1 000 000 kWh, E_REUSE = 300 000 kWh, E_RES-TOT = 600 000 kWh, W_IN = 2 000 m³.

Výstup: **PUE = 1,2; ERF = 0,25; REF = 0,5; WUE = 2 m³/MWh.** Nejde o merané údaje skutočného dátového centra.

Modul `eu_dc_metrics.py` navyše integruje výkon v kW počas intervalov v hodinách na energiu v kWh. Používa desatinnú aritmetiku a odmieta neplatné hranice merania, záporné a nekonečné vstupy.

## 4. Primárne zdroje a otvorené otázky

1. Smernica (EÚ) 2023/1791, články 12 a 26: https://eur-lex.europa.eu/eli/dir/2023/1791/oj/eng
2. Delegované nariadenie (EÚ) 2024/1364, prílohy II–III: https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj/eng

Vzorce a prahy boli porovnané s publikovanými výňatkami oficiálneho EUR-Lex dňa 28. 10. 2026. **Úplná právna analýza vrátane zmien v roku 2026, národnej transpozície a pôvodného PDF sa nevykonala.** Preto zdroj č. 25 v pôvodnej matici ostáva `fully_signed_off=NO` a celkový stav 0/31 sa nemení.

**Nasledujúci technický krok:** naviazať merané E_DC, E_IT, E_REUSE a vodu na časové rady modelu; explicitne oddeliť energetickú hranicu DC od tepla dodaného bazénu. Až potom počítať indikátory z reálnych dát a posudzovať právny súlad.
