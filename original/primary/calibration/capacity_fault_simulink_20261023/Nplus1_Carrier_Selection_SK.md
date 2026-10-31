# Výber Carrier a N+1, 23.10.2026

Stav: numericky overená Simulink simulácia, nie osvedčenie o normovej zhode ani cenová ponuka.

Nový model: `DC_Pool_Capacity_Fault_20261023_SK.slx`, 7 celoročných scenárov po 105120 krokoch.
## Nová simulácia výpadkov a limity výkonu

| Scenár | Ročný plyn siete MWh |
|---|---:|
| Bez bazéna, TČ 12 MW | 9085.895 |
| Bez bazéna, TČ 10 MW | 9088.579 |
| Bazén, TČ 10 MW | 9191.507 |
| Bazén, 24h strata 2 MW | 9207.071 |
| Bazén, N+1 obnova za 30 min | 9191.637 |
| Bazén, zdroj TČ max. 9.42 MW | 9256.806 |
| Bazén, zdroj TČ max. 10.99 MW | 9189.267 |

Model v každom kroku 300s prepočítal teplotu bazéna, termostat, akumulátor TES, tepelné čerpadlo a plynový zdroj. Kontroly: odber DC nesmie byť pridelený dvakrát, T bazéna zostáva do 27.80 °C, tepelné a elektrické bilancie platia. Maximum T bolo 27.62 °C.

## Aktualizovaný výrobca: Carrier 61XWH-ZE

Technický katalóg Carrier 2025 uvádza pri skúške vody zdroja **20/15 °C** a teplej strany **70/75 °C** najväčší model 17 s **1570 kW menovitého tepla** (podľa EN14511). Predošlá hypotéza 2 MW na kus nie je pre túto sériu zdokumentovaná.

- 6 aktívnych × 1.57 MW = 9.42 MW; + 1 rezervný: **7 agregátov**.
- 7 aktívnych × 1.57 MW = 10.99 MW; + 1 rezervný: **8 agregátov**.
- Ročný rozdiel simulovaného plynu 67.538 MWh; väčšia zostava spotrebuje aj o 14.145 MWh viac elektriny kompresorov.
- Rozdiel prevádzkového energetického prínosu len **2023.92 EUR/rok** pri tarife Eurostat SK 2025.

### Ekonomický záver s neistotou

Pri údržbe 2% z obstarávacej ceny ročne, diskonte 6% a životnosti 20 rokov je dodatočná investícia do ôsmeho modelu 17 ekonomicky ospravedlniteľná len približne do **18 883 EUR**. Ide o matematický prah, nie o trhovú cenu.

**Pozor:** tento záver platí iba pre porovnanie modelovej prevádzky. Skutočná kapacita a COP pri zdroji DC 35/30 °C a teplovodnej sieti 50/70 °C sú NEOVERENÉ. Rozmerovanie podľa katalógovej bodovej kapacity sa nesmie používať pre stavebný projekt. Pre zdroj 25 °C treba samostatný výber.

### Nezávislé núdzové chladenie IT

Pri IT príkonovom návrhu 10 MW treba mať samostatný bezpečne použiteľný odvod tepla minimálne na príslušné plné návrhové zaťaženie, aj pri vypnutí bazéna, siete a všetkých TČ. Skutočná rezerva chladenia vrátane PUE režijných strat a záložných vetiev vyžaduje odborný tepelný a spoľahlivostný návrh.

### Podklady a dodávateľské dopyty

- [Carrier 2025 katalóg](https://brandportal.carrier.com/m/7e93b9e9f7e9d2a2/original/10191_PSD_02_2025_61XW_ZE_Short_version.pdf), strana 8 pre menovité podmienky a strana 9 pre ilustračné COP krivky (nie záväzný výber).
- [Eurovent Carrier model 61XWH-ZE07](https://www.eurovent-certification.com/en/catalog/program/certificate/participant/model/show/199588446), iné skúšobné podmienky W10-7.
- RFQ: potvrdiť počet strojov, Qheat, COP, teplotu zdroja, tlakové straty, minimálny PLR, spúšťací prúd, servis a pravidlá N+1.

**Stav:** fyzikálna softvérová simulácia úspešná; výrobcom podpísané výkony, COP, CAPEX a právne predpisy ešte nie sú potvrdené.
