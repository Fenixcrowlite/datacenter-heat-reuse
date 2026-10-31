# A64: Zosúladenie lichobežníkovej a diskrétnej integrácie
**Dátum:** 27.10.2026. **Typ údajov:** DERIVED_SIMULATION. **Fyzická validácia:** NIE.

## Problém
A60 počíta energiu zo 672 vzoriek na **671 časových intervaloch**, t. j. 167,75 h.
A62 interpretuje každú zo 672 vzoriek ako výkon počas nasledujúceho 900-sekundového kroku, t. j. 168 h.
Preto hodnoty nie sú priamo zameniteľné, hoci obe implementácie môžu byť správne pre svoju definíciu času.

## Matematický dôkaz
Pre konštantný krok Δt = 900 s a vzorky P₀ … Pₙ₋₁:
- Lichobežníková energia: E₆₀ = Δt·[P₀/2 + Σᵢ₌₁ⁿ⁻² Pᵢ + Pₙ₋₁/2].
- Diskrétna energia: E₆₂ = Δt·Σᵢ₌₀ⁿ⁻¹ Pᵢ.
- Rozdiel: E₆₂−E₆₀ = Δt·(P₀+Pₙ₋₁)/2.
- Rozklad: rozdiel = Pₙ₋₁·Δt + Δt/2·Σᵢ₌₀ⁿ⁻²(Pᵢ−Pᵢ₊₁).

Prvý člen je pridaný posledný krok; druhý je korekcia spôsobená zmenou výkonu medzi vzorkami.
Výsledok v kWh získame delením 3 600 000 J/kWh. Pri nepravidelnom časovom kroku sa táto koncová identita nesmie automaticky použiť.

## Overenie
Súbory A60/A62 sa načítajú **iba na čítanie**, ich SHA256 sa porovnajú s uloženými súhrnmi a s krížovým odkazom A62→A60.
A64 kontroluje zhodu spoločných stĺpcov, 900 s monotónnu časovú os, oba energetické výpočty a kumulatívnu energiu A62.
Nezávislý modul opakuje integráciu iným vzorcom s `Decimal` a overuje výsledky pre oba varianty.
Samostatný HTML report je offline, nevyužíva sieť, nemení spoločnú SCADA ani GUI.

## Limity
CSV obsahujú výsledky simulácie, nie kalibrované fyzikálne merania.
A60/A62 nie sú dôkazom účinnosti tepelného čerpadla ani bezpečnosti zariadenia.
Reálne dáta musia obsahovať UTC čas, identitu snímačov, kalibračné doklady a fyzikálne parametre podľa A55–A58.
