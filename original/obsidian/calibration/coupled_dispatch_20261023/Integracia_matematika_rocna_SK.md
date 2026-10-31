---
tags: [datacentrum, bazen, odpadove-teplo, matlab, kalibracia, energeticka-bilancia]
date: 2026-10-23
status: VERIFIED_NUMERICAL_SCENARIO_NOT_CERTIFIED
owner: calibration_coupled_dispatch
---
# Integrácia DC - teplovodná sieť - bazén: matematika a metodika

> [!important] Základ validácie
> Ako **externý meraním nezávislý zdroj** je použitá reanalýza NASA POWER (2025, 8760 hodinových dát pre Bratislavu), **nie** skutočný profil spotreby konkrétneho dátového centra. Všetky výkony, charakteristika COP a parametre interiéru plavárne sú modelové scenáre. Tieto výsledky nemožno vyhlásiť za prevádzkovú certifikáciu.

## 1. Sieť a dostupné odpadové teplo

Hodinový model pôvodného DC (bez zásahu do jeho kódu):

$$
P_{IT}(t)=P_{IT,rated}\cdot u(t),\qquad
\dot Q_{DC,available}(t)=P_{IT}(t) f_{rec}
$$

Predpoklad: $P_{IT,rated}=10$ MW, priemerné $u=0.82$ (syntetický časový rad), $f_{rec}=0.85$. PUE scenár = 1.36 podľa kapacitne váženého orientačného benchmarku 2026 (nie meranie prevádzky).

Energetická hranica:

$$
E_{DC}=\sum_t P_{IT}(t)\cdot PUE\cdot\Delta t;
\quad ERF_{legal}=\frac{E_{REUSE,measured}}{E_{DC}}
$$

V štúdii preto uvádzame len **ERF_source_proxy**. Model dostupnosť zdroja nekalibruje podľa meraní teplôt/prietokov a nenahrádza meranie $E_{REUSE}$ na hranici DC.

## 2. Dynamická bilancia bazéna

Typ plaveckého bazéna (ilustračný): $25\times12.5\times1.6$ m, $V=500\,\mathrm{m^3}$, $A=312.5\,\mathrm{m^2}$. Používame $\rho=997\,\mathrm{kg/m^3}$, $c_p=4182\,\mathrm{J/(kg K)}$.

$$
C=\rho Vc_p=2\,084\,727\,000\,\mathrm{J/K}
$$

$$
C\frac{dT}{dt}=\dot Q_{pool}-\dot Q_{evap}-\dot Q_{conv}-\dot Q_{rad}-\dot Q_{ground}-\dot Q_{makeup}-\dot Q_{other}
$$

### Evaporácia, konvekcia, radiácia

V rámci pôvodnej *redukovanej korelácie* (neodráža skutočný projekt VZT):

$$
p_{sat}(T)=0.61094\exp\!\left(\frac{17.625T}{T+243.04}\right)\quad [\mathrm{kPa}]
$$

$$
\dot m_{evap}=4\cdot10^{-5}A\max(p_{sat}(T)-RH\,p_{sat}(T_{air}),0)\,F_a(1-0.90\,K)
$$

$$
\dot Q_{evap}=\dot m_{evap}h_{fg};\qquad
\dot Q_{conv}=hA(T-T_{air})(1-0.75K)
$$

$$
\dot Q_{rad}=\epsilon\sigma A[(T+273.15)^4-(T_{wall}+273.15)^4](1-0.75K)
$$

$$
\dot Q_{ground}=UA(T-T_{ground});\quad
\dot Q_{makeup}=\dot m_{evap}c_p(T-T_{fill})
$$

Referenčne: $T_{air}=29$ °C, $RH=0.60$, $T_{wall}=27$ °C, $T_{ground}=20$ °C, $T_{fill}=15$ °C, $UA=800$ W/K pre **500 m³**. Pre iné rozmery sa UA škáluje pomerom plochy dna a stien **len ako predpoklad**:

$$
UA'=800\cdot\frac{LW+2(L+W)d}{312.5+2(25+12.5)1.6}
$$

Prevádzka 08:00-20:00 miestneho času Europe/Bratislava, nočné zakrytie $K=1$ (nie zaručená skutočná redukcia odparu), explicitný Euler $\Delta t=300$ s.

## 3. Regulácia a prevencia prehriatia

Regulátor má hysterezis: zapni pri $T\leq27.25$ °C, vypni pri $T\geq27.60$ °C. Modelový tvrdý strop $T_{max}=27.80$ °C, limit publikovaného §8 vyhlášky 308/2012 Z. z. pre plavecký bazén je 28 °C. Overiť účinné konsolidované znenie predpisu; fyzikálna prevádzka potrebuje samostatnú ochranu aj snímače, prebehy a neistotu merania.

Prúd dodaného tepla je zhora ohraničený:

$$
\dot Q_{pool}\leq\min\!\left(150\,\mathrm{kW},\frac{C(T_{max}-T)}{\Delta t}+\dot Q_{loss}\right)
$$

Pre priamy výmenník sa kontroluje nutná teplotná podmienka $T_{DC,source}\geq T_{pool}+3$ K, **nie však výkonový datasheet výmenníka**.

Pre tepelné čerpadlo pri zdroji 25 °C je $COP=4$ scenárová konštanta:

$$
W_{pool}=\frac{Q_{pool}}{COP};\quad
Q_{DC,pool}=Q_{pool}-W_{pool}
$$

## 4. Alokácia výkonu medzi bazén a tepelnú sieť

Každú hodinu sa najprv v 12 krokoch po 300 s vyhodnotí maximálne potrebný tepelný výkon DC pre bazén:

$$
P_{pool,reserved,h}=\max_{j=1..12}P_{DC,pool,j}
$$

$$
P_{DC,DH,available,h}=\max(0,P_{DC,available,h}-P_{pool,reserved,h})
$$

Tým sa zamedzuje súbežnému dvojitému využitiu zdroja v 1-hodinovom dispečingu a 5-minútovej regulácii. Konzervatívne rezervované, ale nespotrebované teplo môže zostať nevyužité. **Nie je to optimalizačný dispečer ani skutočný riadiaci systém.**

V tepelnom čerpadle siete platí:

$$
Q_{HP,out}=Q_{DC,DH,extracted}+W_{HP}
$$

Podmienka:

$$
Q_{DC,pool}+Q_{DC,DH,extracted}\leq Q_{DC,available}
$$

Pre sieť pri každej hodine:

$$
Q_{DH,demand}=Q_{HP,out}-Q_{TES,charge}+Q_{TES,discharge}+Q_{gas}
$$

## 5. Výstupy a nezávislé kontroly

| Konfigurácia | Teplo bazénu MWh/rok | Odobraté DC teplo celkom MWh/rok | Záložný plyn MWh/rok |
|---|---:|---:|---:|
| 35 °C bez bazéna | 0.0 | 38107.5 | 9085.9 |
| 35 °C priamy výmenník | 250.1 | 38238.7 | 9234.4 |
| 25 °C bez bazéna | 0.0 | 36689.7 | 7218.9 |
| 25 °C TČ bazéna | 250.1 | 36793.7 | 7331.1 |

Testy:
- Celoročná bilancia bazéna: $C(T_{end}-T_0)=\sum(Q_{pool}-Q_{loss})\Delta t$ s rezíduom menším než $10^{-4}$ MWh.
- Bilancia využitého zdroja bez dvojitého účtovania, testovaný každý hodinový interval.
- $DT=60$ s vs $DT=300$ s na 7-dňovom horizonte: vykurovanie 10.0925 vs 10.0375 MWh; zmena o 0.055 MWh.
- Bez bazéna sú výstupy tepelného čerpadla, plynu a TES číselne zhodné s pôvodným `dchr.simulate_system`.
- Pri nulovom zdroji DC sa vykurovanie bazéna nepovolí.
- Parametrická citlivosť: 500 m³ s krytom 250.125 MWh; 1000 m³ s krytom 388.8 MWh; 500 m³ bez krytu 323.95 MWh.
- Maximálna simulovaná teplota pri bazéne 500 m³ 27.62 °C.

## 6. OPEX iba v hraniciach modelu

Pre režim 35°C porovnávame: samostatný plynový ohrev rovnakého bazénového profilu vs dodatočná vetva DC s vplyvom odberu tepla na zvyšok siete.

$$
\Delta OPEX=\frac{Q_{pool}}{\eta_{gas}}c_{gas}-\frac{\Delta Q_{gas,DH}}{\eta_{gas}}c_{gas}
- (\Delta W_{HP,DH}+W_{pool})c_{elec}
$$

Ceny Eurostat SK 2025 pre zvolené priemyselné kategórie: 55.6348 EUR/MWh plynu a 152.0726 EUR/MWh elektriny, $\eta_{gas}=0.90$ je modelový parameter. Priamy výmenník približne **10 920 EUR/rok**, TČ pre bazén približne **3 542 EUR/rok** modelovej *dodatočnej* úspory. Bez investičných nákladov, čerpadiel, revízií, prevádzky vzduchotechniky, skutočnej ceny energií.

## 7. Artefakty

- `run_coupled_annual_SK.m` a `simulate_coupled_pool_SK.m`: plný výpočtový kód.
- `qa_coupled_model_SK.m`: regresné, numerické a bezpečnostné testy.
- `coupled_scenarios_2025.csv`: ročné ukazovatele.
- `*_8760h.csv`: časové rady pre prepojenie s paralelnou vetvou Simulink.
- `coupled_annual_SK.png`: graf teploty a využitia tepla.
- `Annual_Coupled_Study_SK/RU/EN.pdf`: trojjazyčná dokumentácia.

## 8. Referenčné odkazy

- [EU 2024/1364 ERF](https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj)
- [Slov-Lex 308/2012 §8](https://static.slov-lex.sk/static/SK/ZZ/2012/308/vyhlasene_znenie.print.html)
- [STN EN 15288-1+A1](https://normy.normoff.gov.sk/norma/139372/?lang=en)
- [NASA POWER Hourly](https://power.larc.nasa.gov/docs/services/api/temporal/hourly/)
- [Eurostat electricity](https://ec.europa.eu/eurostat/databrowser/view/nrg_pc_205/default/table)
- [Eurostat gas](https://ec.europa.eu/eurostat/databrowser/view/nrg_pc_203/default/table)

![[coupled_annual_SK.png]]

Pozri tiež: [[Annual_Coupled_Study_SK]], [[Annual_Coupled_Study_RU]], [[Annual_Coupled_Study_EN]], [[Matematicky_rozbor_a_simulacia_SK]].
