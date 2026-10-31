# Uzavretá simulačná slučka DC - bazén - teplovodná sieť
**MATLAB/Simulink R2026a | Výpočtový rok 2025 | 23.10.2026**

**Stav: VERIFIKOVANÁ NUMERICKÁ SIMULÁCIA, nie normovo certifikovaný projekt.**

## Architektúra
Uložený model **DC_Pool_Coupled_ClosedLoop_20261023_SK.slx** obsahuje spätné väzby cez tri bloky Unit Delay: teplota vody, energia zásobníka TES a termostat. Výpočet každých 300 sekúnd dodá teplo bazénu a zostávajúci skutočne dostupný zdroj spracuje dispečer teplovodnej siete.

- Ochrana modelu: zapnúť ohrev pri 27,25 °C, vypnúť pri 27,60 °C, nepovoliť krok nad 27,80 °C.
- 500 m³ bazén: 25 × 12,5 × 1,6 m, plocha vody 312,5 m², vykurovací výkon max. 150 kW.
- Tepelná bilancia: **C × ΔT / Δt = Q_bazén − Q_straty**, kde C = ρ × V × cp.
- Rozdelenie zdroja: **Q_DC,bazén + Q_DC,sieť ≤ Q_DC,dostupné**.
- TČ: **Q_HP,výstup = Q_DC,zdroj + W_kompresor**. Kompresorový príkon nie je odpadovým teplom.

## Ročná verifikácia
Vykonané 4 scenáre po 105 120 krokoch so skutočnou meteorologickou reanalýzou NASA POWER 2025 a syntetickým IT zaťažením.

| Scenár | Teplo bazénu MWh | Zdroj DC do bazéna MWh | Plyn teplovodnej siete MWh |
|---|---:|---:|---:|
| 35 °C, bez bazéna | 0,00 | 0,00 | 9 085,89 |
| 35 °C, priamy výmenník | 250,125 | 250,125 | 9 189,27 |
| 25 °C, bazénové TČ (COP 4) | 250,125 | 187,594 | 7 296,99 |
| 35 °C, odstávka DC na 24 h | 250,00 | 250,00 | 9 404,84 |

Nezávislý Python test prečítal 4 × 105 120 Simulink záznamov, overil bilančné identity, nulový odber počas 24-hodinovej odstávky a absenciu dvojitého využitia tepla. Maximálna vypočítaná teplota bola **27,62 °C**.

## Ekonomická citlivosť
Použité štatistické ceny Eurostat SK 2025: elektrina **152,07 EUR/MWh**, plyn **55,63 EUR/MWh**. Pri porovnaní s plynovým ohrevom rovnakého bazéna: modelová dodatočná úspora **12 306,50 EUR/rok** pri priamom výmenníku a **4 279,76 EUR/rok** pri bazénovom TČ. CAPEX, čerpadlá, servis a klimatizácia bazénovej haly nie sú zahrnuté.

## Overenie COP výrobcu
Certifikácia Eurovent pre **Carrier 61XWH-ZE07**, zdroj vody W10-7: COP 5,48 pri teplej vode 35 °C; 4,71 pri 45 °C; 3,92 pri 55 °C; 3,17 pri 65 °C. Modelová Carnotova aproximácia sa na týchto bodoch odchyľuje o **−12,8 až +0,4 %**. Bez potvrdenej výkonovej mapy sa údaje **nesmú extrapolovať** na zdroj 25/35 °C a sieť 70 °C.

## Normy a ďalšie hranice
Slovenský publikovaný text vyhlášky 308/2012 Z. z. §8 ods.7 udáva pre plavecký bazén maximálne 28 °C; pred reálnym projektom treba potvrdiť aktuálne účinné znenie, prechodové prehriatie a neistotu snímačov. STN EN 15288-1+A1 a EN 50600-4-6 vyžadujú osobitné odborné overenie. Právne použiteľný ERF potrebuje skutočný merač na hranici dátového centra. Náhradné chladenie serverov nie je v tejto simulácii implementované.

**Primárne zdroje:** [EU 2024/1364](https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj), [Slov-Lex](https://static.slov-lex.sk/static/SK/ZZ/2012/308/vyhlasene_znenie.print.html), [Eurovent Carrier](https://www.eurovent-certification.com/en/catalog/program/certificate/participant/model/show/199588446), [NASA POWER](https://power.larc.nasa.gov/docs/services/api/temporal/hourly/).

**Prílohy:** Simulink .slx, ClosedLoop_Simulink_Matematika_SK.md, originálne MATLAB skripty, JSON audit, 4 × CSV.