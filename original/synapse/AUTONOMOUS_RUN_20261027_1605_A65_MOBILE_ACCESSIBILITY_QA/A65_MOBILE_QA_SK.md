# A65: Mobilná použiteľnosť offline reportu A64

**Zistený reprodukovateľný defekt:** pôvodný A64 HTML report pri mobilnej šírke 390 px mal horizontálny obsah 599 px. Tabuľka so šiestimi stĺpcami presahovala displej o 209 px.

**Oprava bez zásahu do A64:** vytvorený samostatný súbor `mobile_comparison.html`, ktorý mení tabuľkové riadky na mobilné karty s názvami veličín cez `data-label`. Pri desktopovej šírke zostáva pôvodná tabuľková štruktúra.

**Overenie v izolovanom headless Chrome:** šírky 320 px, 390 px, 1440 px; vo všetkých prípadoch `scrollWidth <= viewport`. Počet tabuliek 2, riadkov 10, buniek 60. Všetky pôvodné numerické hodnoty a upozornenie DERIVED SIMULATION zachované.

**Regresia:** 8 unit testov, vrátane odmietnutia nečakaného počtu buniek a dôkazu pôvodného overflow. Prvý pokus o výpis výsledku na Windows zlyhal kvôli CP1251 kódovaniu; zmenené na ASCII-safe JSON a opakovanie prešlo.

**Obmedzenie:** ide o prezentáciu syntetických údajov, nie validáciu fyzikálnej sústavy. Originálne A60/A62/A63/A64 sa nemenili. Žiadny zdieľaný browser profil, GPU render ani externá sieť.
