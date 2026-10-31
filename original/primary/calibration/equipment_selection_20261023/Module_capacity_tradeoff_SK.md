---
date: 2026-10-23
tags: [data-center, district-heating, heat-pumps, sizing, optimization, N-plus-1]
status: SOFTWARE_VERIFIED_FINANCIAL_SCREENING_NOT_PROCUREMENT
owner: equipment_selection
---
# Doplnenie: presnejší výber počtu modulov TČ pre sieť

Predchádzajúci výber 12 MW užitočného **prevádzkového** výkonu pre pokrytie špičky je technicky možný, ale z finančnej citlivosti nemusí byť optimálny. Nová kontrola čítala skutočný 300s výstup **105 120 krokov** simulácie `no_pool_35_8760h.csv` a orezala modelový výkon TČ pri rôznych limitoch. Každý variant má jeden záložný 2-MW modul navyše (N+1); nezohľadňuje priebežnú zmenu stavu TES a novú optimalizáciu plynu po obmedzení, ide o predbežné rozhodovanie.

Skutočný modelový maximálny výkon TČ siete: **10,372 MW**.

| Prevádzkové moduly po 2 MW | Záložný modul | Inštalovaný menovitý výkon | Nepokryté TČ teplo → doplnkový plyn za rok | Počet hodín s obmedzením |
|---:|---:|---:|---:|---:|
| 3 = 6 MW | 1 = 2 MW | 8 MW | **10 303,08 MWh** | 4 220,33 h |
| 4 = 8 MW | 1 = 2 MW | 10 MW | **2 563,93 MWh** | 3 230,08 h |
| **5 = 10 MW** | **1 = 2 MW** | **12 MW** | **2,74 MWh** | **22,00 h** |
| 6 = 12 MW | 1 = 2 MW | 14 MW | 0 MWh | 0 h |

### Preferovaná voľba: 5 prevádzkových modulov po 2 MW + 1 záložný (6 celkovo)

Modelové špičky nad 10 MW spôsobujú iba **2,74 MWh/rok** nedodania TČ (asi 0,006 % ročnej užitočnej dodávky TČ). Existujúca záložná kotolňa ich môže teoreticky pokryť. Nakupovať ďalší modul iba kvôli týmto hodinám nemusí byť ekonomicky obhájiteľné.

Pri predpokladanej investícii **1000 EUR/kW inštalovaného menovitého výkonu** a 2 % servis/rok, 50 kW parazitných čerpadiel škálovaných podľa veľkosti, 20 rokov a 6 % diskont:
- 6 MW prevádzkové +2 MW záloha: orientačné NPV **+3,00 mil. EUR**, ale vysoká dodatočná spotreba plynu.
- 8 MW +2 MW záloha: NPV **+3,16 mil. EUR**, ale ďalších 2,56 GWh plynu za rok.
- **10 MW +2 MW záloha:** NPV **+1,50 mil. EUR**, veľmi malé nepokryté teplo.
- 12 MW +2 MW záloha: NPV **−1,07 mil. EUR**, bez materiálneho zisku v užitočnom teple.

**Upozornenie:** rozpočet je čisto scenárový, nie výrobná ponuka. PUE a COP boli odvodené zo syntetického tepelného modelu; nový model so samostatnou optimalizáciou TES a 5-min časom treba ešte spustiť pri zvolenom limite výkonu. COP a 2 MW výkon konkrétneho modulu musia byť doložené **pri zdroji 35→30 °C a sieťovej vode 50→70 °C**, vrátane čiastočného výkonu.

Návrh RFQ: Carrier AquaForce 61XWH-ZE alebo Oilon ChillHeat P, výrobcom dimenzovaná zostava 6 modulov s 1 záložným; nie slepé tvrdenie o 2 MW výkonu každej katalógovej varianty.

Doplnkové dôkazy: `network_module_2MW_Nplus1_screen.csv`, `network_module_2MW_Nplus1_screen.json`, `optimize_module_capacity.py` (reprodukovateľný výpočet na pôvodných 105 120 časových intervaloch). Pozri [[Equipment_Selection_SK]], [[Equipment_Selection_RU]], [[Equipment_Selection_EN]].

**Vykonané nezávislé testy algoritmu:** časový súčet, nákup redundancie 2 MW nad prevádzkovou kapacitou, súčet orezania a vyčíslenie plynovej substitúcie. Správa necertifikuje správnosť dodávateľa, plnú normovú zhodu ani skutočnú cenu.
