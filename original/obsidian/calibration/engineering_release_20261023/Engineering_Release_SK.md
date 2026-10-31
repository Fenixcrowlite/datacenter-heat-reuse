# Záverečná výskumná etapa: dátové centrum, bazén, teplovod a nezávislé chladenie

**23 October 2026 | Model status: VERIFIED NUMERICAL STUDY**
> Numericky overené v Pythone a MATLAB/Simulinku. NIE je to certifikovaný projekt ani osvedčenie o zhode.

### 1. Hranica energetického modelu
Scenár menovitého IT výkonu 10 MW, profil zaťaženia IT syntetický; NASA POWER Bratislava 2025 je meteorologická reanalýza. PUE je predpoklad, nie meranie prevádzky.

### 2. Ročná bilancia chladenia IT
Zo 105 120 päťminútových údajov Simulinku: teplo IT 71 833 MWh, reálne použité serverové zdrojové teplo v modeli 38 275 MWh, zvyšné teplo na odvedenie 33 558 MWh. Priemer zvyšku 3,831 MW. Pri súbežnom výpadku bazéna a teplovodu treba nezávisle odviesť návrhových 10 MW.

### 3. Hydraulika a akumulácia
Pre vodu 997 kg/m³, cp 4182 J/(kgK): 10 MW a 5 K znamená cca 1 727 m³/h, vnútorný priemer jedného rozvodu pri 2 m/s približne 553 mm. Definitívne DN určuje glykol, skutočný rozvod, tlaková strata a čerpadlá.

### 4. Skutočné bezpečnostné testy Simulinku
Samostatný uložený model IT_Independent_HeatRejection_20261023_SK.slx, šesť 1-hodinových prípadov, krok 5 sekúnd, bazén a sieť nevykupujú žiadne teplo, zásobník vody 10 m³, T0=35°C a trip=40°C.

| Scenár | Maximum T modelu °C | Bez prekročenia? |
|---|---:|:---:|
| 6 modulov, 0% derating, 30 s | 36.44 | PASS |
| 7 modulov, -10%, 30 s | 35.72 | PASS |
| 7 modulov, -10%, 300 s | 42.20 | TRIP |
| 6 modulov, -10%, trvalý deficit | 122.76 | TRIP |
| 7 modulov, -20%, trvalý deficit | 70.74 | TRIP |
| 7 modulov, porucha čerpadla 10 s | 37.88 | TRIP |

**Note / Poznámka / Примечание:** Results ABOVE the configured trip threshold are invalid for physical equipment; no IT load shedding or boiling model is included.

### 5. Bezpečnostná architektúra
Chladenie IT musí pracovať nezávisle od tepelného odberu bazéna či teplovodu. Čistý výkon 2 MW/blok musí výrobca doložiť pri návrhovej letnej vonkajšej teplote. Pri 10-MW IT sa 6 modulov N+1 udrží len bez deratingu; pri -10% je potrebných približne 7×2 MW, ak po jednej poruche zostane 10,8 MW. Pre 30-s deficit 2 MW pri ΔT=5K je ideálne tepelné minimum zásobníka 2,88m³. To však NEZARUČUJE prietok IT: UPS čerpadlá, ventily, napájanie a bezpečnostné relé sú P0.

### 6. Výrobcovia a overené hranice
Carrier 61XWH-ZE17 1570kW pri W20/15 a W70/75, nie v našej prevádzke. Oilon ChillHeat P30-P450 do 450kW B0/W35; séria S až 2000kW v iných podmienkach. Alfa Laval ponúka zákazkové doskové výmenníky pre bazény. Güntner a Kelvion sú kandidáti nezávislého chladenia. Výrobné mapy COP/PLR pre 25/20 alebo 35/30 → 50/70°C zatiaľ nie sú k dispozícii.

### 7. Bazén a legislatíva
500m³ bazén 25×12,5×1,6m, nízkoteplotný výmenník 150kW predbežne UA=37,63 kW/K so scenárovým faktorom zanesenia. Vyhlásený §8 ods.7 308/2012 uvádza 28°C pre plavecký bazén, účinné znenie a plnú STN EN15288-1+A1 pred stavbou overiť. ERF meraný podľa EU 2024/1364 na hranici dátového centra.

### 8. RFQ a otvorené požiadavky
Vyhotovené štyri nezáväzné návrhy dopytov pre Carrier, Oilon, Alfa Laval a dodávateľov recoolerov. NEODOSLANÉ. Potrebujeme výrobcom overené tepelné parametre, COP/PLR, prietoky, tlakové straty, N+1 záložný čas, ceny a realizovateľnosť; ďalej reálne IT/BMS údaje, hydrauliku, SLD napájania, plné normy a funkčné skúšky.

### Source material

- [Carrier 61XWH-ZE 2025, published 1570 kW W20/15 / W70/75](https://brandportal.carrier.com/m/7e93b9e9f7e9d2a2/original/10191_PSD_02_2025_61XW_ZE_Short_version.pdf)
- [Oilon ChillHeat product data](https://oilon.com/wp-content/uploads/2024/04/Oilon_ChillHeat-EN.pdf)
- [Alfa Laval Slovakia plate heat exchangers](https://www.alfalaval.sk/produkty-a-riesenia/prenos-tepla/doskove-vymenniky-tepla/plate-heat-exchangers/)
- [Güntner data center cooling](https://guntner.com/applications/data-centers)
- [Kelvion data center cooling](https://www.kelvion.com/industry-solutions/data-center)
- [ASHRAE Data Centers engineering](https://handbook.ashrae.org/Handbooks/A23/SI/A23_Ch20/a23_ch20_si.aspx)
- [EU delegated regulation 2024/1364 ERF](https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj)
- [Slov-Lex swimming pool requirements, decree 308/2012 original edition](https://static.slov-lex.sk/static/SK/ZZ/2012/308/vyhlasene_znenie.print.html)

### Reproducible outputs
- `independent_cooling_design_scenarios.json` and `cooling_nplus1_derating.csv`
- `IT_Independent_HeatRejection_20261023_SK.slx`
- `test_IT_cooling_failure_SK.m` and `IT_cooling_failsafe_simulink_results.json`
- `cooling_fault_second_scale.csv`, `cooling_failover_sensitivity.csv`
- `RFQ_Carrier_EN.md`, `RFQ_Oilon_EN.md`, `RFQ_AlfaLaval_EN.md`, `RFQ_DryCooler_EN.md`
- `cooling_resilience_calculator.html`
- `FMEA_engineering_gaps.csv`

**No procurement, email delivery, commissioning or operating safety certification has occurred.**
