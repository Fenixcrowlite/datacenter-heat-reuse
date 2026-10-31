# A56: Nezávislý adversariálny audit identifikácie A55

**Stav:** implementovaný a otestovaný syntetický kontrolný modul. **Nie je to fyzikálna kalibrácia ani certifikácia bezpečnosti.** Pôvodné A55 a modely Stateflow ostali nezmenené.

## Identifikované chyby prijímacej logiky A55

A55 používa pre kompresor iba intervaly, kde platí `0 < r < 1`, pričom ostatné intervaly potichu ignoruje. Ak je dosť ostatných dobrých intervalov, chybný priebeh môže byť prijatý. Pri energetickej bilancii A55 ignoruje malé zmeny teploty `|ΔT| < 0.01 K`, dokonca aj keď majú nesprávne znamienko. Globálny fit kapacity môže zároveň zakryť zmenu parametra medzi prvou a druhou časťou merania.

V troch **umelo poškodených** časových radoch A55 stále vrátilo kandidátsky odhad; nový A56 ich zamietol. Ide o reprodukovateľný adversariálny test, nie o nález na skutočnom zariadení.

## Nové pravidlá A56

1. Pri stabilnom príkaze kompresora a dostatočnej odchýlke od žiadaného výkonu musí každý skúmaný interval spĺňať `0 < r_i = (P_i - P_cmd)/(P_(i-1) - P_cmd) < 1`. Inak `A56_COMPRESSOR_NONCONTRACTIVE_STEP`. **Toto platí len pre predpokladaný model prvého rádu**; zložitejší fyzikálny kompresor môže potrebovať iný model.
2. Pri významnej energii `E_i = Q_net,i · Δt_i` sa nesmie objaviť opačné znamienko `ΔT_i E_i < 0`, ani pri `|ΔT_i| < 0.01 K`. Pri `E_i ≈ 0` a merateľnom `ΔT_i` sa vyžaduje kontrola chýbajúceho toku.
3. Aspoň 80 % intervalov s `|E_i| ≥ 1000 J` musí mať použiteľné `|ΔT_i| ≥ 0.01 K`; ide o konzervatívny analytický prah, nie normu.
4. Identifikácia `C_eff = Σ(ΔT_i E_i)/Σ(ΔT_i²)` sa vykoná osobitne na prvej a druhej polovici použiteľných intervalov. Ak `|C_1-C_2|/max(|C_1|,|C_2|) > 0.10`, kandidát sa zamietne ako nestacionárny.
5. Kontrola SHA256 zdrojového A55; pôvodné validačné pravidlá A55 sa zachovávajú. Výstup nikdy nenastaví `physical_release=True`.

## Predpoklady a obmedzenia

Prah 0.01 K je odvodený z predchádzajúceho A55, nie z presnosti konkrétneho snímača. Prahy 80 % a 10 % sú predbežné konzervatívne kritériá pre syntetický QA. Pri reálnom zariadení treba určiť neistoty teploty, prietoku a výkonu, časovú synchronizáciu, hranice kontrolného objemu a prípustnú triedu dynamického modelu. Ak je časová konštanta nelineárna alebo kompresor prekmitáva, A56 správne odmietne **model prvého rádu**, nie automaticky zariadenie.

**Ďalší krok:** získať identifikované a kalibrované dáta konkrétneho zariadenia; definovať meracie neistoty a nezávislý plán overenia; až potom znovu spustiť izolovanú Stateflow regresiu. Bez fyzikálnych dát zostáva schválenie prevádzky BLOKOVANÉ.
