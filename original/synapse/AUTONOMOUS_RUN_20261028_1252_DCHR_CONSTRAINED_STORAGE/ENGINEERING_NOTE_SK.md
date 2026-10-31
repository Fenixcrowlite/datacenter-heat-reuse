# DCHR | Obmedzený sezónny zásobník tepla: technická citlivosť

**Dátum:** 28.10.2026. **Stav:** overený izolovaný výpočtový prototyp, nie prevádzková simulácia, realizovateľný projekt ani potvrdená úspora plynu.

## Vstupy a model

Vstup: 8760 syntetických hodinových záznamov z existujúcej simulácie (SHA256 `8125719923bae97901f37cf0f5354df77b46544df0477f863172255748873f25`). Zdrojové CSV, MATLAB/Simulink a SCADA zostali bez zmeny. V pôvodnom modeli **už existuje zásobník 100 MWh**: nové varianty sú samostatné paralelné kontrafaktuálne výpočty, nie automaticky pripočítateľné úspory.

Každú hodinu sa zohľadní strata zásobníka, dostupný potenciál obmedzeného tepla HP, maximálny nabíjací/vybíjací výkon, účinnosti 95 %/95 %, dodatočná elektrina HP, zdrojové teplo, strop celkového príkonu dátového centra a HP a teplotná podmienka výdaja. Pre ilustráciu: limit príkonu lokality **12 MW**, limit celkového elektrického príkonu HP **2,5 MW**, tepelný výkon nabíjania/vybíjania **3 MW**, hodinová strata **0,025 %**, teplota zásobníka **72 °C**, teplotný rozdiel výmenníka **3 K**. Všetky tieto limity sú **predpoklady na citlivostnú analýzu, nie overené technické parametre zariadení**.

Upravený COP pri vyššej výstupnej teplote sa odhaduje heuristicky: `COP_new = COP_original × Lift_original / (Lift_original + max(0, T_store + ΔT_HX − T_DH_supply))`. Nejde o kalibrovanú mapu výrobcu. Elektrina navyše `E_el = Q_charge / COP_new`, zdrojové teplo `Q_source = Q_charge − E_el`. Stav zásobníka: `SOC_next = SOC_previous × (1 − loss) + η_charge × Q_charge − Q_discharge / η_discharge` pri hodinovom kroku. Odber tepla z úložiska je prípustný iba ak `T_store ≥ T_DH_supply + ΔT_HX`.

## Výsledky opakovaného syntetického roku (rok 3)

| Kapacita | Dodatočný limit HP elektriny | Teoreticky pokryté plynové teplo | Dodatočná elektrina HP |
|---:|---:|---:|---:|
| 100 MWh | 0,5 MW | 89,63 MWh | 101,31 MWh |
| 500 MWh | 1,5 MW | 433,11 MWh | 511,64 MWh |
| 2500 MWh | 0,5 MW | 1888,65 MWh | 2134,90 MWh |
| 2500 MWh | 1,5 MW | **1910,04 MWh** | **2399,18 MWh** |
| 10000 MWh | 1,5 MW | 2815,07 MWh | 3413,14 MWh |

V základnom variante 2500 MWh / 1,5 MW vzniká **4959,52 MWh nabíjacieho tepla**, ale približne **2700,98 MWh** sa stratí v úložisku (a ďalšia časť v účinnostiach). Preto teoretické pokrytie plynového tepla **1910,04 MWh** vyžaduje **2399,18 MWh dodatočnej elektriny**. Čísla nemožno priamo odčítať ako peniaze ani porovnávať MWh elektriny a MWh plynového tepla bez cien, účinnosti kotla, emisií a okrajových podmienok.

### Citlivosť teploty a strát (2500 MWh, limit elektriny 1,5 MW)

| Teplota zásobníka | Strata za hodinu | Pokryté plynové teplo | Dodatočná elektrina | Hodiny zablokovaného výdaja |
|---:|---:|---:|---:|---:|
| 55 °C | 0,025 % | 65,99 MWh | 1310,87 MWh | 3222 |
| 65 °C | 0,025 % | 1920,94 MWh | 2051,43 MWh | 0 |
| 72 °C | 0,025 % | 1910,04 MWh | 2399,18 MWh | 0 |
| 80 °C | 0,025 % | 1897,92 MWh | 2767,57 MWh | 0 |
| 72 °C | 0 % (idealizované) | 2375,07 MWh | 1270,01 MWh | 0 |

**Záver:** sezónne straty a teplotná použiteľnosť sú rozhodujúce. Zvýšenie teploty zásobníka bez dôkazu o COP a cene energie nemusí pomôcť. Pri 55 °C výdaj často nevyhovuje teplote siete. Všetky výsledky sú scenáre, nie reálne úspory.

## Overenie a hranice dôvery

20/20 jednotkových testov PASS. Nezávislá implementácia s `Decimal` overila 26 280 hodinových krokov jedného scenára (3 roky), energetickú bilanciu všetkých 39 modelových rokov a teplotné brány; PASS. Zdrojové SHA256 zodpovedá pôvodnému CSV. Nepoužila sa žiadna nová Codex/GPU úloha.

**Neoverené:** reálne menovité limity HP a lokality, zásobník/stratifikácia, teplotná dynamika, reálne počasie, hodinové tarify, náklady na sezónny zásobník, skutočná dodatočná disponibilita zdrojového tepla, COP mapa, elektrické prípojky, priame znovusimulovanie pôvodného 100 MWh zásobníka a 31/31 signoffov primárnych zdrojov (aktuálne 0/31).

**Nasledujúci krok:** prepojiť variant s pôvodným Simulink dispečingom a 100 MWh zásobníkom; potvrdiť výrobné COP mapy a elektrické stropy; potom vyhodnotiť čisté náklady a sezónnu uskutočniteľnosť.
