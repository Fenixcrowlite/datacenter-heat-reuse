# DCHR C33: čo fyzikálne znamená zásobník „100 MWh“?

**Stav:** izolovaný výpočtový kandidát, syntetické údaje. Nie je to validácia existujúceho zásobníka v Simulinku ani preukázaná úspora plynu.

## Problém definície kapacity

Kapacita zásobníka vody závisí od referenčnej teploty:

\[
E = \frac{\rho V c_p (T_{hot}-T_{ref})}{3{,}6\cdot10^9}\quad[\mathrm{MWh}]
\]

kde \(\rho=1000\,\mathrm{kg/m^3}\), \(c_p=4180\,\mathrm{J/(kg\,K)}\). Ak je „100 MWh“ definovaných voči vratnej vode 35 °C, **neznamená to**, že 100 MWh možno dodať do siete s vyššou požadovanou teplotou.

Z 8760 hodinových syntetických záznamov vychádza najvyššia teplota prívodu siete **61,95185 °C**. Pri predpokladanom priblížení výmenníka 3 K je konzervatívna referenčná teplota **64,95185 °C**.

## Objem pre teoretických 100 MWh

| Teplota nabíjania | Referencia 35 °C | Referencia 64,95185 °C | Násobok objemu |
|---|---:|---:|---:|
| 72 °C | 2 327,69 m³ | **12 219,43 m³** | 5,25× |
| 80 °C | 1 913,88 m³ | **5 723,25 m³** | 2,99× |

Tieto hodnoty sú energetické ekvivalenty pre úplne nabitý zásobník. Nezaručujú dodávku 100 MWh pri reálnej stratifikácii, tepelných stratách a obmedzenom výkone.

## Dynamický test

Použitý bol nezmenený izolovaný model C31 s 8 vrstvami, 8 podkrokmi za hodinu, obmedzením výkonu nabíjania/vybíjania, COP a tepelnými stratami. Každý variant prešiel tri opakované syntetické roky (8760 hodín/rok).

| Teplota | Definícia 100 MWh | Dodané teplo v 3. roku | Dodatočná elektrina v 3. roku |
|---|---|---:|---:|
| 72 °C | Voči 35 °C | 79,63 MWh | 57,68 MWh |
| 72 °C | Voči 64,95185 °C | 416,99 MWh | 275,20 MWh |
| 80 °C | Voči 35 °C | 83,97 MWh | 69,25 MWh |
| 80 °C | Voči 64,95185 °C | 251,18 MWh | 193,35 MWh |

Ročné dodané teplo nie je kapacita zásobníka. Je to súčet opakovaných nabití a vybití. Vyšší ročný výsledok veľkého zásobníka neznamená automaticky vyššiu hospodárnosť.

## Nevyhnutné obmedzenia

Existujúci Simulink už obsahuje zásobník označený 100 MWh. Jeho teplotná referencia, regulačná logika a fyzikálna ekvivalencia neboli overené. Preto **nie je prípustné pripočítať** výsledky C33 k úsporám pôvodnej simulácie. COP, izolácia, hydraulika, teplota vratnej vody a ceny energie sú stále predpoklady; merané údaje a 31 primárnych zdrojov nie sú overené.

**QA:** 28/28 nezávislých kontrol vrátane Decimal výpočtu kapacity, plochy/UA, energetických rezíduí a SHA vstupov. Výstup: `C33_100MWH_GATE_RESULTS.json`.

**Ďalší krok:** nájsť v existujúcom Simulink modeli presnú definíciu stavu 100 MWh, teploty a logiky nabíjania/vybíjania. Až potom zostaviť porovnávací test so zhodnými okrajovými podmienkami.