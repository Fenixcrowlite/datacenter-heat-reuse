# A66: Zjednotený offline prehľad bilancie bazéna

## Účel
A66 spája pôvodné interaktívne grafy A63 s číselným porovnaním integračných metód A64 do jedného samostatného HTML súboru. Nevyžaduje sieťové pripojenie ani externé JavaScriptové knižnice. Pôvodné súbory A60–A65 zostávajú nedotknuté.

## Význam veličín
A60 integruje 672 časových vzoriek lichobežníkovou metódou cez 671 intervalov po 900 s, teda 167,75 h. A62 vykonáva 672 diskrétnych krokov po 900 s, teda 168 h. Rozdiel je preto očakávaný, nie automaticky chyba bilancie.

Pre každý kanál platí presná kontrola:
`E_discrete - E_trapezoid = E_last_rectangle + E_slope_correction`.
Pre bazén Q_pool je rozdiel približne 20,000398 kWh pre oba scenáre.

## Overenie
- Dve simulácie: V08 a V09; päť energetických kanálov.
- Pri načítaní sa kontrolujú SHA256 vstupných CSV a metadát A62 v porovnaní s A63/A64.
- Nezávislý audit opätovne vypočíta SHA256 všetkých ôsmich súborov A60/A62.
- Testy zámerne pozmenených SHA256, integračnej identity a príznaku fyzickej validácie musia zlyhať.
- Izolovaný Chrome testuje 320, 390 a 1440 px a prepínanie V08/V09; bez horizontálneho presahu, bez externých požiadaviek.

## Obmedzenia
Všetky vstupy sú DERIVED SIMULATION, nie merania zariadenia. Tento prehľad nepredstavuje kalibráciu, overenie bezpečnosti, certifikáciu ani priamu komunikáciu s SCADA. Skutočné mobilné zariadenie a fyzická telemetria zostávajú neoverené.
