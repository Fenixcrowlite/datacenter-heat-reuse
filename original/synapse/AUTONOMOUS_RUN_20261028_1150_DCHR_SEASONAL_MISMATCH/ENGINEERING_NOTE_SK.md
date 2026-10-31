# DCHR | Sezónny nesúlad tepla a plynu (simulovaný scenár)

**Klasifikácia:** hypotetický výpočet z existujúcej simulácie, nie meranie, projekt zásobníka ani potvrdená úspora plynu.
Zdroj SHA256: `8125719923bae97901f37cf0f5354df77b46544df0477f863172255748873f25`. Hodinových intervalov: 8760.

Potenciálne obmedzené teplo: **22,545.4 MWh**; simulované plynové teplo: **12,549.1 MWh**.
Priamy súbeh obmedzenia HP a plynu: **0 hodín**, priama hodinová náhrada najviac **0.000 MWh**.

## Mesačné súčty (MWh, syntetické)

| Mesiac | Obmedzený potenciál HP | Plynové teplo |
|---:|---:|---:|
| 1 | 0.0 | 3,860.6 |
| 2 | 0.0 | 2,982.6 |
| 3 | 0.2 | 1,509.8 |
| 4 | 1,016.4 | 18.2 |
| 5 | 3,580.6 | 0.0 |
| 6 | 4,081.8 | 0.0 |
| 7 | 4,278.6 | 0.0 |
| 8 | 4,258.4 | 0.0 |
| 9 | 3,670.3 | 0.0 |
| 10 | 1,653.8 | 0.0 |
| 11 | 5.3 | 1,041.7 |
| 12 | 0.0 | 3,136.2 |

## Kontrafaktuálny ideálny zásobník (nie realizovateľný návrh)

Bez tepelných strát, bez obmedzenia nabíjacieho/vybíjacieho výkonu, bez dodatočnej elektriny HP. Rok 1 začína prázdny; roky 2/3 opakujú presne ten istý syntetický profil.
Uvedené kapacity sú samostatné ideálne scenáre, nie prírastky k existujúcemu 100 MWh zásobníku.

| Kapacita (MWh) | Rok 1: ideálne vytlačený plyn (MWh) | Rok 2 (MWh) | Rok 3 (MWh) |
|---:|---:|---:|---:|
| 0 | 0.0 | 0.0 | 0.0 |
| 100 | 100.2 | 100.2 | 100.2 |
| 500 | 500.2 | 500.2 | 500.2 |
| 1000 | 1,000.2 | 1,000.2 | 1,000.2 |
| 2500 | 2,500.2 | 2,500.2 | 2,500.2 |
| 5000 | 4,178.1 | 5,000.2 | 5,000.2 |
| 10000 | 4,178.1 | 10,000.2 | 10,000.2 |
| 20000 | 4,178.1 | 12,549.1 | 12,549.1 |

## Inžiniersky záver

Letný prebytok tepla a zimná spotreba plynu sa v tomto modeli **časovo míňajú**. Zvýšenie okamžitej kapacity HP samo osebe nedokazuje úsporu plynu. Potrebné je analyzovať sezónne ukladanie tepla, distribučné teploty, tepelné straty, reálny COP, dodatočnú elektrinu a skutočnú kapacitu výmenníka.
Tepelný výkon `HP_Heat_MW` je **potenciál pred obmedzením**, nie automaticky dostupné teplo. Preto všetky čísla z ideálneho zásobníka predstavujú iba matematické horné hranice za neoverených predpokladov.
Existujúci zásobník v CSV dosahuje 100 MWh; samostatný kontrafaktuálny výpočet nie je kalibrovaná úprava existujúceho dispečingu.
Regulačné metriky ERF/REF/WUE zostávajú nevyhodnotené; primárne zdroje **0/31**.

**Ďalší krok:** pripraviť spojenú simuláciu s reálnymi obmedzeniami nabíjania/vybíjania, stratami a elektrinou HP, porovnať ročné náklady a zachovať pôvodný model nemenný.
