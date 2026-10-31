---
tags: [datacentrum, bazen, Simulink, Stateflow, FMEA, riziko]
status: VERIFIED_SYNTHETIC_V06
date: 2026-10-23
language: sk
---
# V06: oneskorené meranie, netesný ventil, porucha chladiča REJECT

> [!warning] Rozsah dôkazu
> Všetkých sedem 168-h prípadov bolo skutočne spustených v MATLAB R2026a/Simulink. Vstupy aj modelové senzory sú syntetické. Ide o nový klon v05; pôvodná v85 nie je vnútri vykonávacieho dispečera v06. Nie je to certifikát fyzického zariadenia.

## Architektúra

V05 dokázala nulový príkaz pre ohrev počas chyby. V06 oddeľuje **povel Q_pool_cmd** od **fyzického toku Q_pool_phys**. Stavy Stateflow regulujú jadro prevzaté z v04, na výstup alokácie je pripojený fyzický model poruchového ventilu a chladenia IT. Opravená teplota vody sa vracia do spätnoväzbovej slučky. Nezávislé senzory sa stále **iba simulujú**.

## Tepelná kapacita a fyzikálny zákon

Ilustračná geometria 25 × 12,5 × 1,6 m, hladina 312,5 m², objem 500 m³.

$$C_w=\rho Vc_p=997\cdot500\cdot4182=2\,084\,727\,000\ \mathrm{J/K}.$$

$$E_{16\rightarrow28}=\frac{12C_w}{3{,}6\cdot10^9}=6{,}94909\ \mathrm{MWh}.$$

Toto je iba energia prvého ohrevu bez strát. Časový krok 900 s:

$$T_{k+1}=T_k+\frac{900}{C_w}(Q_{\rm pool,phys}-Q_{\rm loss}).$$

Straty vyparovaním, konvekciou, sálaním, prestupom do konštrukcie, dopĺňaním vody a stálou stratou 2 kW zostali scenárové.

## Oneskorenie snímačov a safety latch

Simulačné vetvy majú nezávislé časové oneskorenie 15/30 min.

$$T_{1,k}=T_{\rm true,k-1}+b_{1,k};\quad
T_{2,k}=T_{\rm true,k-2}+b_{2,k}.$$

$$D_{\rm diff}=[|T_1-T_2|>0{,}35\,\mathrm K];\quad
D_{\rm hot}=[\max(T_1,T_2)\ge27{,}70^\circ C].$$

$$D_{\rm fault}=D_{\rm diff}\lor D_{\rm hot}\lor\neg flowOK\lor EStop\lor invalidSensor.$$

Pri akejkoľvek chybe sa západka nastaví na 1. Uvoľnenie je možné až pri odstránení chyby, explicitnom ručnom RESET a nameranej teplote najviac 27,65 °C. Ak je latch=1, regulátor musí nastaviť Q_pool_cmd=0.

Rovnako posunuté virtuálne senzory o -0,40 K nespustili alarm. Na rozdiel od v05 tu softvér nepozná **skutočný bias** snímača a nevydáva ho za reálne meranie. Tento test odhaľuje problematiku spoločnej chyby dvoch snímačov.

## Zaklinený ventil

V prípade poruchy ventilu a nulového príkazu:

$$Q_{\rm leak}=\min\left(25\,000,\ Q_{\rm reject,cmd},\
4500\max(0,T_{\rm DC}-T_w-3)\right).$$

$$Q_{\rm pool,phys}=Q_{\rm pool,cmd}+Q_{\rm leak}.$$

$$Q_{\rm reject,before}=Q_{\rm reject,cmd}-Q_{\rm leak}.$$

Koeficient 4500 W/K, maximálny únik 25 kW a teplotný rozdiel sú predpoklady, nie hydraulická špecifikácia. Tepelná energia nevzniká: únik sa odpočíta z pôvodnej vetvy REJECT. Pri zaklinenom ventile sa prenieslo 0,489959 MWh aj pri nulovom povele.

## Odvod tepla dátového centra

Dostupnosť chladiča je simulovaný bezrozmerný parameter a (0 znamená výpadok).

$$Q_{\rm reject,phys}=\min(Q_{\rm reject,before},180\,000a).$$

$$Q_{\rm unhandled}=Q_{\rm reject,before}-Q_{\rm reject,phys}.$$

$$Q_{\rm DC,av}=Q_{\rm HX,phys}+Q_{\rm HP,source}
+Q_{\rm reject,phys}+Q_{\rm unhandled}.$$

Fiktívny IT tepelný buffer je indikátor rizika, nie teplota serverov:

$$C_{\rm IT}=8\cdot10^6\ \mathrm{J/K};\quad
Q_{\rm passive}=\max(0,2000(T_{\rm IT}-30)).$$

$$T_{\rm IT,k+1}=\max\left(30,T_{\rm IT,k}+
\frac{900}{C_{\rm IT}}(Q_{\rm unhandled}-Q_{\rm passive})\right).$$

Modelový alarm aktivuje hranica 42 °C. **Nie je to skutočný limit CPU ani chladiacej vody.**

## Vykonané scenáre

| Scenár | Netesnosť [MWh] | Neodvedené teplo [MWh] | Max. model T_IT [°C] | Interlock [vzorky] |
|---|---:|---:|---:|---:|
| Zdravý | 0 | 0 | 30,00 | 0 |
| Nesúhlas snímača | 0 | 0 | 30,00 | 48 |
| Spoločný bias | 0 | 0 | 30,00 | 0 |
| Zaklinený ventil | 0,489959 | 0 | 30,00 | 108 |
| REJECT vypnutý | 0 | 0,079660 | 47,06 | 0 |
| Bez prietoku | 0 | 0 | 30,00 | 52 |
| Kombinovaná porucha | 0,152588 | 0,057152 | 42,72 | 64 |

![[povel_vs_prietok_v06_SK.png]]

![[teplota_IT_riziko_v06_SK.png]]

## QA a interpretácia

**84 801 nezávislých kontrol Python: PASS**, čítaných z pôvodných Simulink CSV. Overený je prvý zákon bazéna aj TČ, energetické prerozdelenie zdroja DC vrátane neodvedeného tepla, skutočné oneskorenie oboch snímačov, bezpečnostná západka a jej reset, nulový softvérový povel pri blokovaní, fyzické presakovanie pri zaseknutom ventile a vývoj rizikového IT buffera. Originál v85 zostal so SHA-256 2a9de22c0c55e8c4a87f7b0e0cfe9cd97db08c991f09d98361b009de310adde7.

**Čo ešte chýba:** reálne dva snímače s kalibráciou, redundantné fyzické uzatváranie ventilu, výkon reálneho IT chladiča, prietoky a hydraulika, výrobné COP(Tsource,Tsink,PLR), merané časové profily a aktuálne právne posúdenie. Simulačná správnosť NIE JE osvedčenie bezpečnosti.

## Reprodukcia

MATLAB R2026a v adresári OneDrive/Projects/DataCenter_Heat_Reuse/matlab/pool_failure_v06 spustiť spusti_poruchove_scenare_v06_sk.m.

Python QA: python qa_v06_sk.py

Hlavná Simulink schéma: DC_Bazen_Fyzikalne_Poruchy_v06_SK.slx. CSV a JSON: results/pool_failure_v06.

Odkazy na metodiku a pravidlá (aktuálna právna platnosť zvlášť overovaná):
- EU Delegated Regulation 2024/1364: https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj
- STN EN 15288-1+A1:2024, popis: https://normy.normoff.gov.sk/norma/139372/nahlad/
- Historická vyhláška 308/2012: https://static.slov-lex.sk/static/SK/ZZ/2012/308/vyhlasene_znenie.print.html
