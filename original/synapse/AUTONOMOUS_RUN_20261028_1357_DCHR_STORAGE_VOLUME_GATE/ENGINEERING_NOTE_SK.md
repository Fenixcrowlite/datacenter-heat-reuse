# DCHR | Fyzikálna brána objemu sezónneho zásobníka vody

**Dátum:** 28.10.2026. **Stav:** izolovaný a numericky overený orientačný výpočet; **nie** projekt nádrže, overená úspora plynu ani validácia Simulinku.

## Prečo je táto kontrola potrebná

Predchádzajúci citlivostný model používa kapacitu 2500 MWh a konštantnú teplotu zásobníka 72 °C bez explicitnej zmeny teploty vody pri vybíjaní. Kapacita v MWh nie je fyzický objem. Nový výpočet odhaľuje minimálny rozsah potrebného vodného zásobníka pri idealizovanom citeľnom teple, ešte pred návrhom izolácie, stratifikácie, hydrauliky a stavebnej realizácie.

Použité syntetické hodinové dáta: 8760 záznamov, SHA256 `8125719923bae97901f37cf0f5354df77b46544df0477f863172255748873f25`. Teplota dodávky tepla do siete: minimum **45 °C**, 95. percentil **57,5493 °C**, maximum **61,95185 °C**. Pre výmenník sa predpokladá priblíženie **3 K**.

## Fyzika, jednotky a hranice

Citeľná energia vody: **E = ρ · V · cₚ · ΔT**. Preto **V = E / (ρ · cₚ · ΔT)**, pričom E v jouloch, ρ = 1000 kg/m³ (optimistické zaokrúhlenie), cₚ = 4180 J/(kg·K), ΔT = T_horúca − (T_dodávka + 3 K). Pre 1 MWh platí 3,6 × 10⁹ J. Tento model predpokladá ideálne využitie celej teplotnej zmeny. Neobsahuje stratifikáciu, zmiešavanie, dynamickú teplotu vratnej vody ani straty výmenníka okrem 3 K. Ide o **optimistickú dolnú hranicu objemu**, nie o rozmerovú dokumentáciu.

### Výsledky pre 2500 MWh

| Horúca voda | Podmienka dodávky | Využiteľné ΔT | Ideálny objem vody |
|---:|---|---:|---:|
| 55 °C | maximum 61,95185 °C + 3 K | nemožné | **nevhodné pre všetky hodiny** |
| 65 °C | maximum + 3 K | 0,04815 K | **44 714 805 m³** |
| 72 °C | minimum 45 °C + 3 K | 24 K | **89 713 m³** |
| 72 °C | 95. percentil + 3 K | 11,4507 K | **188 034 m³** |
| 72 °C | maximum + 3 K | 7,04815 K | **305 486 m³** |
| 80 °C | maximum + 3 K | 15,04815 K | **143 081 m³** |

Pre referenčný variant **2500 MWh / 72 °C / maximálna požadovaná teplota** zodpovedá 305 486 m³ vody pri idealizovanej výške 10 m pôdorysu asi **30 549 m²**, ekvivalentný priemer jedinej valcovej nádrže približne **197,2 m**. To nie je odporúčaný tvar nádrže, iba názorná mierka. Aj pri 100 MWh by pri rovnakej teplotnej podmienke išlo približne o 12 219 m³.

**Citlivosť pri 65 °C:** iba 0,04815 K rezervy nad maximálnou teplotou siete s výmenníkom spôsobuje extrémnu nestabilitu objemového odhadu. Malá chyba merania alebo predpokladu by túto koncepciu zneplatnila. Pre dimenzovanie je potrebná skutočná teplotná krivka a definícia použiteľného teplotného intervalu.

## Dlhodobé straty

Predchádzajúci model predpokladá pomernú hodinovú stratu SOC **0,025 %**. Bez ďalšieho nabíjania a vybíjania zostáva z pôvodnej energie podľa `(1−0,00025)^h` po 30 dňoch **83,53 %**, po 90 dňoch **58,27 %** a po 180 dňoch iba **33,95 %**. Polčas je približne **2772 hodín / 115,5 dňa**. Tento parameter nie je odvodený z plochy, izolácie, teploty okolia a koeficientu prestupu tepla, preto nejde o validovanú tepelnú stratu konkrétneho zásobníka.

## Overenie a závery

**16/16 jednotkových testov PASS**, nezávislý prepočet **64/64 scenárov** pomocou `Decimal`, z toho 8 teplotne neuskutočniteľných, 56 geometrických rekonštrukcií a 3 nezávislé kontroly retencie. Pri variante 65 °C vznikol najskôr príliš prísny absolútny tolerančný limit pre veľké objemy; opravený na absolútnu alebo relatívnu toleranciu a pôvodný neúspešný log zachovaný.

**Dôležité:** pôvodný systém už má zásobník 100 MWh. Tento výpočet nemení dispečing, nedokazuje dodatočnú úsporu, neoveruje investičné náklady a nepreukazuje, že sa dá takáto nádrž postaviť. Plný text primárnych zdrojov je stále neoverený **0/31**.

**Nasledujúci krok:** zaviesť do samostatného dynamického modelu stav teploty a teplotne závislé vyčerpávanie energie, modelovať teplotu vratnej vody, účinný teplotný rozsah a stratifikáciu; následne porovnať s pôvodným Simulink dispečingom vrátane existujúceho 100 MWh zásobníka a overiť technické parametre výrobcu.