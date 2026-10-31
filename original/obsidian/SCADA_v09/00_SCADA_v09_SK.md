---
tags: [datacentrum, bazen, scada, simulink, meranie, tepelna-energia, hmi]
created: 2026-10-23
language: sk
status: VERIFIED_LOCAL_SIMULATION_D
---
# Datacentrum → bazén 500 m³ | SCADA v09

> [!warning] Kvalita dát a hranice bezpečnosti
> Vizuálna SCADA v09 používa iba uložené D_SYNTHETIC dáta z reálne vykonaných Simulink v08 simulácií. **Nie sú to merania z fyzických zariadení**. HMI **NEOVLÁDA** skutočný PLC, servery, ventily ani bezpečnostné obvody; táto funkcionalita je zakázaná. REJECT/IT teplota sú modelové indikátory.

## Spustená lokálna služba

Na PC je k dispozícii iba počas behu:

http://127.0.0.1:8091/

V projekte OneDrive/Projects/DataCenter_Heat_Reuse/scada_v09:

    .\start_scada.ps1

Bezpečný STOP s perzistentným lokálnym stop flag:

    .\stop_scada.ps1

STOP sa automaticky nemaže a nevypína žiadne cudzie služby.

## Obsah navigácie

- [[README_RU]] — praktický manuál a riadenie simulácie
- [[ARCHITECTURE_SK]] — architektúra SCADA a bezpečnostné hranice
- [[TEST_PLAN]] — nezávislé testy
- [[CODEX_RESULT]] — výsledok kódovania a reprodukcia
- [[SCADA_V09_HANDOFF_20261023]] — technické odovzdanie, limity, ďalší postup

## Skutočne overené

- 8 × 672 vzoriek, 900 s krok, 168 hodín na scenár.
- 27 Python testov PASS; JavaScript syntakticky PASS.
- HTTP endpointy, alarmový scenár s obojstranným zlyhaním REJECT, play/pause/seek, bezpečný návrat do zdravého scenára fungujú.
- SQLite historian, STOP, CSRF, izolácia názvov zdroja.
- Browser screenshoty boli vygenerované z naozaj spustenej webovej SCADA.

![[QA_HMI_1600x940.png]]

![[QA_HMI_TABLET_920x1200.png]]

## Nie je ešte spustené

MQTT, Mosquitto, FUXA ani Grafana **neboli fyzicky spustené**. Sú pripravené v samostatnom voliteľnom Docker profile, ale Docker Desktop spotreboval viac než 8 GB RAM a bol zastavený. Nespúšťať automaticky, kým nebude potvrdený bezpečný rozpočet pamäte.

## Realizácia

Aktuálny projekt je použiteľná simulovaná HMI bez externej infraštruktúry. Ďalej treba získať A-merania, kalibračné protokoly a projekt hydrauliky pred akýmkoľvek reálnym riadením.