# Integrovaná ročná simulácia: dátové centrum, teplovodná sieť a plavecký bazén

*Výsledky nezávislej integrácie MATLAB R2026a, rok počasia 2025, 23.10.2026*

> **Výlučne výskumný scenár. Nie je to certifikovaný projekt stavby ani meraná prevádzka.**

Úloha: porovnať využitie odpadového tepla dátového centra v teplovodnej sieti pri pridaní bazéna. Reálna vstupná teplota pochádza z hodinovej reanalýzy NASA POWER, ale výkon serverov, vlastnosti výmenníka a prostredie plavárne zostávajú predpokladmi.

## Metodika a matematická bilancia

Bazén: L = 25 m, W = 12,5 m, priemerná hĺbka 1,6 m, V = 500 m³, A = 312,5 m². Začiatočná teplota vody 16 °C, hysterézia vykurovania 27,25 °C / 27,60 °C, modelový strop 27,80 °C. Tepelný výmenník 150 kW, denná prevádzka 08:00-20:00 v čase Europe/Bratislava. V noci sa modeluje zakrytie hladiny.

Použitá dynamika: C·dT/dt = Q_bazén - Q_výpar - Q_konvekcia - Q_žiarenie - Q_konštrukcia - Q_doplnková voda - Q_ostatné; C = ρ·V·cp. Päťminútový explicitný numerický krok je vložený do hodinového dispečingu siete.

Energetická hranica DC: Q_HP,out = Q_DC,odoberané + W_kompresor. Príkon kompresora nie je recyklovaným serverovým teplom. Na účely predbežného ERF sa počíta iba extrahované teplo, skutočný ERF však vyžaduje meranie na systémovej hranici podľa nariadenia (EÚ) 2024/1364.

Zabezpečenie proti dvojitému použitiu: najvyšší päťminútový odber tepla bazénom počas každej hodiny sa najprv rezervuje. Až zvyšný hodinový zdroj možno prideliť tepelnému čerpadlu pre sieť. Táto konzervatívna aproximácia môže podhodnotiť využitie zdroja v krátkych intervaloch.

## Ročné výsledky

| Prípad | Bazén MWh | Zdroj DC MWh | Plyn MWh | Zdroj do bazéna MWh |
|---|---|---|---|---|
| Zdroj 35°C bez bazéna | 0.0 | 38,107.5 | 9,085.9 | 0.0 |
| 35°C priamy výmenník | 250.1 | 38,238.7 | 9,234.4 | 250.1 |
| Zdroj 25°C bez bazéna | 0.0 | 36,689.7 | 7,218.9 | 0.0 |
| 25°C bazén cez TČ | 250.1 | 36,793.7 | 7,331.1 | 187.6 |

## Ekonomické porovnanie

Modelová dodatočná úspora voči alternatíve, keď sa rovnaké teplo bazéna získa plynovým kotlom (účinnosť 90 %): priamy výmenník 10,920 EUR/rok; nízkoteplotný zdroj s TČ pri COP = 4: 3,542 EUR/rok. Zahrnutá je strata tepla dostupného pre sieť a dodatočný plyn. Nie sú zahrnuté CAPEX, čerpadlá, výmenníkový návrh, servis ani VZT bazénovej haly.

## Citlivosť bazénových parametrov

Rok a rovnaké zdroje; bazén 500 m³ s nočným zakrytím: 250.1 MWh; 1000 m³ so zakrytím: 388.8 MWh; 500 m³ bez zakrytia: 324.0 MWh. Zväčšenie plochy a koeficient prestupu UA sú stále modelové škálovania, nie údaje z konkrétnej stavby.

## Validácia a obmedzenia

Rovnaký dispečer bez bazéna reprodukoval referenčnú implementáciu dchr.simulate_system (elektrina TČ, plyn, akumulátor, výkon TČ). Bilancia bazéna uzatvorená, zdroj sa nepoužíva dvakrát. Najvyššia vypočítaná teplota vody 27,62 °C. Neoveruje to poruchu snímača, prestupný čas ventilu, kvalitu vody ani normovú zhodu.

## Oficiálne zdroje a pôvod údajov
- [NASA POWER 2025, 8760h Bratislava, gridded reanalysis](https://power.larc.nasa.gov/docs/services/api/temporal/hourly/)
- [Eurostat non-household electricity nrg_pc_205, Slovakia 2025](https://ec.europa.eu/eurostat/databrowser/view/nrg_pc_205/default/table)
- [Eurostat non-household gas nrg_pc_203, Slovakia 2025](https://ec.europa.eu/eurostat/databrowser/view/nrg_pc_203/default/table)
- [EU Commission Delegated Regulation 2024/1364 PUE & ERF](https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj)
- [Slovak Decree 308/2012 §8 swimming pools published text](https://static.slov-lex.sk/static/SK/ZZ/2012/308/vyhlasene_znenie.print.html)
- [STN EN 15288-1+A1 pool safety design](https://normy.normoff.gov.sk/norma/139372/?lang=en)

Nevyriešené: hodinové merania IT záťaže; skutočný COP pri čiastočnej záťaži a teplotách; teplonosné prietoky; BMS plavárne, vzduchotechnika a spotreba vody; skutočná cena energií; tepelné straty výmenníka a čerpadiel; aktuálne úplné znenie požiadaviek STN a zákona. Model Simulink iného pracovného toku zostal nezmenený.

Podklady a reprodukcia: run_coupled_annual_SK.m; simulate_coupled_pool_SK.m; coupled_scenarios_2025.csv; 4 × 8760h CSV; pool_volume_cover_sensitivity_2025.csv.

![[coupled_annual_SK.png]]
