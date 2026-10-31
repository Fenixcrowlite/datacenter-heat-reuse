# Служебная передача: синтетика, стандарты, бассейн | 2026-10-23
**Кому:** параллельному потоку MATLAB/Simulink по бассейну. **Владение:** не менять существующие файлы чужого потока; весь аудит лежит в `calibration/standards_20261023`.

## Сделано / VERIFIED
- Исходные JSON Python и Simulink прочитаны, вычислительный аудит выполнен `audit_pool_existing.py`.
- 11/11 тестов калькулятора прошли.
- Обнаружено нормативное несоответствие по опубликованному тексту 308/2012 Z.z.: `T_off = 28.2°C`, максимум плавательного бассейна `28°C`. В некоторых сохранённых результатах конечная вода >28°C: Python 2/7, Simulink 2/4. Пик за весь период не проверен.
- Годовой PUE 1.20 является проектным сценарием, среднее Uptime Institute 2026 = 1.52, n=644. НЕ подменять один показатель другим без отдельного эксперимента.
- 500m3 геометрия не подтверждена как сертифицированная соревновательная конфигурация. STN EN 15288-1+A1:2024 действующий стандарт на безопасность проектирования общественных бассейнов. World Aquatics: применять только при соответствующей категории соревнований.
- По EU 2024/1364 ERF = E_REUSE/E_DC; считать только отпущенную за границу ЦОД энергию, не электричество компрессора.

## Протокол для соседнего чата
1. НЕ перезаписывать версии `Bazen_DC_Ohrev_500m3_SK.slx` и v85/v86. Делать новый файл модели.
2. Ввести безопасное ограничение температуры (с гистерезисом, погрешностью датчика, инерцией и проверкой актуальной правовой редакции); KPI не только конечная, но и **максимальная T(t)**.
3. Экспортировать годовую нагрузку бассейна и HP с отдельным учётом источника ЦОД и компрессора. Протокол полей описан в `calibration/standards_20261023/README_RU.md`.
4. Сверить результаты с `pool_existing_QA_20261023.json` и `comparison_result.json`. Это скрининг, не реальная валидация.
5. Для выбранной геометрии получить проверенные данные по STN EN 15288-1+A1 и водоподготовке; для World Aquatics использовать официальную категорию объекта.

## Где открыть калькуляторы
`calibration/standards_20261023/interactive_calculator.html` (параметры меняются в браузере).
`calibration/standards_20261023/benchmark_calculator.py` (CLI JSON).
Источники и статус данных: `sources_and_benchmarks.json`, `parameter_evidence_matrix.csv`.

**Научная честность:** ни полных лицензированных нормативов, ни откалиброванных измерений реального дата-центра/плавательного бассейна пока нет. Юридическое соответствие не заявляем.

## Nové výsledky kalibračnej vetvy (23.10.2026, po pôvodnom handoff)
- NASA POWER 2025 pre Bratislavu stiahnuté: 8 760 / 8 760 platných teplotných riadkov, RH a vietor; historická reanalýza, nie meranie na mieste.
- Eurostat 2025 SK: 152.0726 EUR/MWh elektrina (70k-150k MWh band, X_VAT) a 55.6348 EUR/MWh plyn (100k-1M GJ band, X_VAT); vážené kalendárnymi hodinami 2025.
- Pôvodné fyzikálne jadro MATLAB R2026a vykonané s oboma počasiami, bez zásahu do dátového centra či modelu bazéna: potreba tepla 59 429.977 -> 56 793.695 MWh (-4.436 %).
- Modelové ERF v `matlab/+dchr/compute_metrics.m` nemožno považovať za merané EU ERF. Pre NASA a PUE=1.36 bolo staré číslo 0.488346. Jednoduchý proxy Q_HP-W_HP / E_DC vychádza 0.390076, stále však nejde o meranie na hranici DC. Implementovať korektné E_REUSE meranie podľa EN 50600-4-6.
- Správa v SK/RU/EN, 18 prípadov PUE/počasie/cena, oba oficiálne surové súbory, interaktívny kalkulátor a 20 položiek normatívnej matice sú v `calibration/standards_20261023`.
- Primárne modely `matlab/pool_500m3/*` a `DCHR_*v85/v86` neboli zmenené. Oddelenie ownership ostáva.
- Súbor `normative_kpis_SK.m` je samostatný návrh funkcie na odmietnutie neodmeraného ERF a kontrolu bezpečnej teploty; samostatny matlab -batch smoke-test presiel (PUE/ERF bez meraca a teplotna rezerva); nevyhlasovat za certifikovany ani produkcny.

## Integrovaná ročná simulácia DC -> teplovodná sieť + bazén (23.10.2026, 13:xx Europe/Bratislava)
**OWNERSHIP:** nová oddelená vetva `calibration/coupled_dispatch_20261023/`; existujúci `matlab/pool_500m3/` a `DCHR_*v85/v86` zostávajú bez zmien.
- **VERIFIED:** MATLAB R2026a: 4 úplné ročné výpočty s NASA POWER 2025 hourly (8760) a 5-min bazénovou fyzikou; konzervatívna rezervácia DC zdroja pred hodinovým dispečingom siete, bez dvojitého využitia.
- **VERIFIED:** bez bazéna rovnaké `dchr.simulate_system` veličiny TČ/elektrina/plyn/TES s toleranciou 1e-8. Zdrojové a tepelné bilančné kontroly `COUPLED_DISPATCH_ANNUAL_VERIFIED`.
- **VERIFIED:** 500 m³, cover: 250.125 MWh/rok; 1000 m³, cover: 388.800 MWh; 500 m³, no cover: 323.950 MWh, všetko modelové tepelné potreby.
- **VERIFIED:** direct 35°C, pool 250.125 MWh, celkový odber DC zdrojového tepla 38238.673 MWh; zisk proti gas-only pool ~10 920 €/rok model OPEX. HP25°C, pool 250.125 MWh, zdroj DC do bazéna 187.594 MWh a kompresor 62.531 MWh; zisk ~3542 €/rok model OPEX.
- **VERIFIED:** max simulovana teplota 27.620 °C, hard model ceiling 27.80°C, staré original SLX 28.2°C thermostat NEPOUZIT BEZ NOVEJ BEZPECNEJ VERZIE. Právne znenie vyhlášky 308/2012 §8(7) z vyhlásenej verzie uvádza 28°C; úplné aktuálne konsolidované znenie zákona a plné texty STN neoverené.
- **VERIFIED:** samostatný `qa_coupled_model_SK.m` s porovnaním kroku 300/60 s, nulovým zdrojom a odmietnutím T_max >28; ročná mat. bilancia. Dodatočný nezávislý Python QA kontroloval všetkých 4 × 8760 CSV bez dvojitého účtovania.
- **DODANE:** `Annual_Coupled_Study_SK/RU/EN.pdf` a `.md`, `Integracia_matematika_rocna_SK.md`, `coupled_annual_SK.png`, `coupled_results_2025.json`, `coupled_scenarios_2025.csv`, `pool_volume_cover_sensitivity_2025.csv`, `coupled_interface_contract_2025.json`.
- **OBSIDIAN COPIED (11/11 SHA256):** `C:\Users\Lysda\Documents\Bimba\02_PROJECTS\02_Automation\DataCenter_Heat_Reuse\calibration\coupled_dispatch_20261023\00_Kalibracia_DC_2025.md`.
- **SIMULINK BRIDGE:** čítať `coupled_interface_contract_2025.json`; exportované CSV sú referenčné výstupy. Neprivádzať už regulovaný `Pool_Q_MW` do starého `teplo_dostupne` s ďalším relé (duplicita regulácie). Pravý closed-loop vyžaduje návrat skutočného bazénového výkonu k DC dispatch.
- **BLOCKED REAL VALIDATION:** IT spotreba, teploty/prietoky, priamo meraný ERF, skutočné COP mapy, výkon výmenníka, čerpadlá/VZT/plachta, úplné normové texty. Výsledok NIE je certifikovaná stavba ani normatívny ERF.

## CLOSED-LOOP SIMULINK R2026a VERIFIED - 23.10.2026

Independent owner lane: `calibration/closed_loop_simulink_20261023`, new model `DC_Pool_Coupled_ClosedLoop_20261023_SK.slx`. ORIGINALS `matlab/pool_500m3/*.slx`, `DCHR_*v85/v86` UNCHANGED. Cross-chat coordination by shared file only, no direct live communication.

- VERIFIED in MATLAB R2026a: saved real Simulink feedback with Unit Delay for pool T, TES E, relay H, one physical source allocation every 300 seconds, not just external trace replay.
- VERIFIED 4 × 105120 five-minute 2025 simulations (NASA POWER gridded air temperature, synthetic IT loads): no pool35, direct pool35, HP pool25, 24h DC outage 35. All four PASS `SIMULINK_CLOSED_LOOP_QA_PASS HOURS=8760`.
- VERIFIED independent CSV QA (420480 records): DC extraction never exceeds available source at any step, heat pump electricity partition, no pool heat on 48-72h source outage. Max simulated pool water 27.619764°C < model safety ceiling 27.8°C. This does NOT imply legal certification or actual sensor fail-safe.
- Model output 35 direct pool: 250.125 MWh pool useful heat, 250.125 MWh DC source, 9189.267 MWh district gas; baseline 35 no pool gas 9085.895 MWh.
- Model output 25 source with pool HP: 250.125 MWh pool useful, 187.59375 MWh server source, 62.53125 MWh compressor, 7296.988 MWh gas; 25 no-pool same-step baseline checked separately gas 7218.855 MWh.
- EUR 2025 statistical comparison (Eurostat SK selected nonhousehold category, exclude recoverable VAT), model additional energy OPEX benefit versus separate gas-heated pool: 12,306.50 EUR/year direct35, 4,279.76 EUR/year poolHP25, excludes CAPEX/pumps/air handling. Source: `closed_loop_incremental_opex_2025.json`.
- Manufacturer COP: Eurovent Carrier 61XWH-ZE07 **W10-7 source** certified COP at sink outlet 35/45/55/65°C: 5.48/4.71/3.92/3.17. Model Carnot surrogate bias -12.8% to +0.4% over these exact certified points. No extrapolation allowed to 25/35°C server source and 70°C district: `manufacturer_cop_reference_SK.m` returns NaN out of certified range. `run_manufacturer_cop_comparison_SK.m` MATLAB PASS.
- Deliverables `ClosedLoop_Report_SK/RU/EN.pdf` all 2 pages rendered+verified (no clipping), `ClosedLoop_Simulink_Matematika_SK.md` detailed physics, diagram PNG, `STATUS_CLOSED_LOOP_20261023.json` and .slx.
- OBSIDIAN: folder `C:\Users\Lysda\Documents\Bimba\02_PROJECTS\02_Automation\DataCenter_Heat_Reuse\calibration\closed_loop_simulink_20261023` receives 17 SHA256-matched initial files + 8 QA-matched PDFs/MD/status. Dashboard `00_ClosedLoop_DataCenter_Bazen_SK.md`. All files source mirrored, full enormous CSV 4 × 105120 remain on OneDrive only.
- BLOCKED next: actual manufacturer COP map for 25/35→70 and partial load; pump/HX/fan hydraulic parasitics; site IT temp/flow/load telemetry; certified legal/standards full texts; real boundary-metered ERF; six-mode v85/v86 Stateflow integration as a new version; independent IT cooling modeled and physically fail-safe; not an actual commissioning validation.

Next agent: inspect `STATUS_CLOSED_LOOP_20261023.json` and QA, do NOT treat generic COP=4 or comfort temperature guard as manufacturer/legal confirmation. Preserve existing .slx versioned, STOP/OAuth untouched.

## Technical equipment selection and N+1 capacity optimization | 23.10.2026

**Owner:** `calibration/equipment_selection_20261023`. Do not change `matlab/pool_500m3`, `DCHR_*v85/v86`, or parallel Obsidian notes. Synapse chat access was intermittent; final calculations performed via Desktop Commander on actual PC.

**VERIFIED WITH EXECUTED INPUTS**
- `screen_equipment_options.py` read saved 2025 Simulink 105120-step output, derived DC heat source 6.970 MW mean, 7.699 MW p95, 8.291 MW peak; district HP output 5.477 MW mean, 9.396 MW p95, **10.372 MW peak**.
- Direct 150 kW HX: DC 35→32 °C / pool 27.5→29.5 °C; counterflow LMTD 4.983 K, clean UA 30.10 kW/K, engineering design UA **37.63 kW/K**, nominal estimated **25.1 m²** if U=1500 W/m²K. Source32 demands 63.9 m², source25/30 infeasible at those terminal temperatures. Hot flow43.17m³/h, pool flow64.76m³/h. 70/80kPa pump pressure losses and η=60% are **assumptions**.
- **DO NOT** use Pahlén MFT680 catalogue 200 kW as proof of 150kW under low-temperature approach: catalogue capacity relates to approximately 60K ΔT and only 2.11m² surface. Need custom manufacturer quote with signed rating 35/32↔27.5/29.5 and correct water chemistry.
- Original true closed-loop Simulink benefit before pump power/maintenance: direct HX €12,306.50/y, dedicated pool HP COP4 €4,279.76/y. Engineering budget cashflow NPV20y@6%: direct HX CAPEX €45/75/110k => +€70.97k/+€34.08k/-€8.94k, CAPEX break even €102.72k. Pool HP COP4 NPV0 CAPEX only about €27.39k, not a quote. Envelopes and uncertainties in `equipment_selection_default.json`.
- `optimize_module_capacity.py` clipped each actual executed Simulink thermal output step at duty limits 6/8/10/12 MW, one 2MW spare N+1. Additional boiler heat: **10,303.08 / 2,563.93 / 2.74 / 0 MWh/y** respectively, duty cap10 only 22 restricted hours. Earlier 9MW standalone plant OPEX case undersized; latest **screening preferred 5×2MW duty + 1×2MW spare** with only 2.74MWh/a extra gas, subject vendor actual point capacity and TES redispatch.
- Vendors real envelopes: Carrier AquaForce 61XWH ZE, Oilon ChillHeat P (district); Alfa Laval custom titanium plate HX (pool), Pahlén MFT680 **reference rejected for this low-grade duty**, Grundfos TPE *only for clean primary loop*, SPECK BADU pool-water duty candidate, Siemens SITRANS TS500 and independent certified heat meter. **No negotiated vendor prices** or 25/35→70 COP curves.
- `equipment_configurator.html`: live editable exchanger temperatures and UA, flow rates, gas/electricity, budget CAPEX, COP, 20y NPV, JSON export. JavaScript syntax tested.
- Reports `Equipment_Selection_SK_v02.pdf`, `Equipment_Selection_RU_v02.pdf`, `Equipment_Selection_EN_v02.pdf`, `Module_capacity_tradeoff_SK.pdf` created; first three PDF visuals/text coordinates QA passed, 2pp each.
- Obsidian `C:\Users\Lysda\Documents\Bimba\02_PROJECTS\02_Automation\DataCenter_Heat_Reuse\calibration\equipment_selection_20261023\00_Vyber_zariadeni_20261023.md`. A parallel existing `Equipment_Selection_SK.md` conflicted. **NOT overwritten**; own SK version copied as `Equipment_Selection_SK_20261023_v02.md`, SHA256 verified, hub relinked. See `obsidian_conflict_resolution_20261023.json`.

**P0 ENGINEERING GAPS**: real DC cooling time series and cooling capacity/backup, actual supplier heat exchanger UA/flow/DP/chemistry, actual heat pump maps at 25/35°C→70°C full/partial load, pressure losses/pumps, electrical safety, real capital quotes, current Slovak law and standards full text. At 10MW duty clipping TES/gas dispatch was a screening approximation; rerun full 300s model with updated nameplate to verify impact. Do not present NPV or PUE as measured or legally certified.

**STOP / ownership:** No live state of original SLX altered and no other chat's Obsidian file overwritten. Next technical step could be versioned full manufacturer COP/PLR in independent linked model and explicit N+1 failure modes.

## Capacity fault v2 + Carrier 2025 update (2026-10-23 afternoon)

**VERIFIED and isolated owner**: `calibration/capacity_fault_simulink_20261023/`. New `DC_Pool_Capacity_Fault_20261023_SK.slx` with fifth independent From Workspace input **HPmaxAvailable_MW** for 300-second variable district HP delivered thermal capacity. Original `calibration/closed_loop_simulink_20261023/*`, `matlab/pool_500m3/*` and v85/v86 SLX unchanged. Seven FULL MATLAB Simulink 2025 annual models ×105120 steps; each step independently verifies no double source allocation, pool temperature <=27.8C, HP energy and DH thermal balance, TES bounds. 12-MW no-pool reference reproduces prior closed-loop model exactly.

Model annual DH backup gas heat MWh: 12MW no-pool 9085.895, 10MW no-pool 9088.579, 10MW pool 9191.507, 10MW pool with one 2MW failure 24h 9207.071, N+1 restores 10MW after 30min 9191.637, pool Carrier6*duty nominal9.42MW 9256.806, pool Carrier7*duty nominal10.99MW 9189.267. Worst-day failure starts UTC hour 487, computed from NASA 2025 district demand, model cooling independent remains unverified.

**Vendor correction:** official Carrier 2025 high temp 61XWH-ZE brochure max model17 nominal 1570kW at evaporator entering/leaving W20/15 and condenser entering/leaving W70/75, not 2MW. Do NOT buy hypothetical 5x2MW Carrier set. 6 duty model17 = 9.42 MW +1 spare (7 total); 7 duty model17 =10.99 MW+1 spare (8 total). Actual capacity and COP @DC 35/30C with district heating 50/70C must be selected by Carrier Packaged Chillers Builder (PCB). Brochure: https://brandportal.carrier.com/m/7e93b9e9f7e9d2a2/original/10191_PSD_02_2025_61XW_ZE_Short_version.pdf (page8 ratings, page9 COP plots, not exact site cert). Eurovent certified smaller model 07 W10-7 points do not certify this design.

**Economics:** 7 duty model17 versus 6 duty nominal increases recovered useful heat in model and avoids 67.538 MWh/year natural gas, but consumes 14.145 MWh/year additional compressor electricity. At selected Eurostat SK 2025 average rates net modeled benefit ONLY EUR 2023.92/year. With assumed 2% annual maintenance of additional CAPEX, 6% discount/20 years max NPV=0 incremental CAPEX approx EUR 18,882.58. Hence do not assume additional eighth unit economical for 2025 load. Capital costs remain UNSOURCED vendor budgets.

**Artifacts** (SK RU EN): `Nplus1_Carrier_Selection_{SK,RU,EN}.pdf` + .md, `capacity_fault_simulink_2025.csv/json`, `Carrier_2025_nominal_vs_Nplus1_options.csv`, `Carrier_2025_rated_vs_simulated_economics.json`, MATLAB function/builder/runner. 3 PDFs rendered & QA: 2 pages each, no clipped words. Obsidian folder `C:\Users\Lysda\Documents\Bimba\02_PROJECTS\02_Automation\DataCenter_Heat_Reuse\calibration\capacity_fault_simulink_20261023`, 15 files copied verified SHA256, no conflicts. Hub `00_Capacity_Fault_Nplus1_SK.md`.

**Next P0**: vendor actual point selection for heating 50/70 or 60/70C source 25/20 and 35/30C, plant COP/PLR and flow/pressure drops; source heat flow sizing and independent 10MW-rated IT waste-heat rejection N+1 safety design. Not a certified installation, no physical fail-safe proved. Avoid overriding STOP/OAuth or other chat's files.

## ENGINEERING RELEASE v2026-10-23: Independent IT safety + vendor RFQs

**STATUS VERIFIED NUMERICALLY, NOT COMMISSIONED**.
New isolated owner branch: `calibration/engineering_release_20261023/`. No original `matlab/pool_500m3`, `DCHR`, or baseline v1/v2 models were overwritten. Deliverable archive `ENGINEERING_RELEASE_20261023.zip` at project root, **41 files ZIP integrity PASSED**.

Inputs verified from prior saved `direct_35_8760h.csv` Simulink data (105120 steps):
- Annual modeled IT heat 71,832.833 MWh, source heat extracted by heat pump plus pool 38,274.674 MWh, residual rejected 33,558.160 MWh, mean residual rejection 3.8308 MW. Design worst case without any reused heat **10 MW full rated IT heat**.
- At liquid water 997 kg/m3, 4182 J/kgK, 10 MW with 5K deltaT needs **~1727 m3/h**, hydraulics provisional and NO actual pump head curves. Minimum theoretical buffer for 2MW cooling loss 30s at 5K usable deltaT is **2.878m3**; for 300s 28.781m3. Does NOT preserve IT coolant flow without UPS pumps and independent valves.
- **SIMULINK NEW** `IT_Independent_HeatRejection_20261023_SK.slx` with 5sec thermal buffer feedback; 6 one-hour fault scenarios physically executed, expected hazard detection assertions PASS. With 10m3 buffer and Tmax40C: 6 total×2MW no derating, 30s standby PASS; 7 total×2MW at -10% derating, 30s PASS; 7×2 at -10%, 300s delay TRIP; 6×2 at -10% continuous deficit TRIP; 7×2 at -20% continuous deficit TRIP; pump flow loss 10s TRIP irrespective water temperature. Over-trip hypothetical temperatures are **not physically valid predictions** beyond shutdown threshold, as server load shedding is not modeled. Real safety relay/plant not commissioned.
- **Vendor correction confirmed via manufacturer catalogs:** Carrier 61XWH-ZE model17 1570kW nominal at evaporator 20/15C, condenser 70/75C, not verified site 35/30→50/70; Oilon P30-P450 30–450kW B0/W35, Oilon S up to2000kW at other conditions. No actual 35→70 rated COP or heating duty available.
- Independent recooler shortlists Güntner V-shape VARIO and Kelvion data-center recooling, effective cooling capacity at Bratislava peak ambient **not vendor confirmed**.
- **RFQ drafts created NOT SENT**: Carrier / Climaport (public contact verified historical), Oilon, Alfa Laval, recooler vendors. See `RFQ_package_status.json`, `RFQ_*_EN.md`, `vendor_directory_grounded.csv`. No employer, actual operating DC or purchase authority was claimed.
- QA: `QA_ENGINEERING_RELEASE_20261023.json` confirms 3 PDF reports SK/RU/EN 2 pages each un-clipped, HTML cooling calculator JS syntax verified, 18 FMEA issues, 4 RFQ drafts, 6 Simulink model tests. Obsidian folder `C:\Users\Lysda\Documents\Bimba\02_PROJECTS\02_Automation\DataCenter_Heat_Reuse\calibration\engineering_release_20261023`: **28 files SHA256 identical, 0 conflicts**. Hub `00_Engineering_Release_20261023.md`.
- Compiled ZIP at `C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\ENGINEERING_RELEASE_20261023.zip`, 662604 bytes, SHA256 cbaae384cc3c512994baef8acdc874abb91a79aa46349f77e3fc628c2480de2e.

**P0 HARD BLOCKERS TO PHYSICAL BUILD**: Real 8760h IT/BMS/coolant telemetry; manufacturer selection tool output at all source/sink/PLR points incl ambient peak; installed price signed offers; fluid quality, complete hydraulic Δp and redundant UPS-powered flow, electrical single-line; actual legal effective decree and licensed STN; independent fail-safe relay proof; qualified designer signoff and commissioning. DO NOT state that N+1 is safety-certified based on model-only validation. ERF requires energy meter at DC boundary per EU 2024/1364.

**STOP and ownership respected**; work does not continue asynchronously after this chat turn.


## Research observability, standards and use cases | 23.10.2026

**OWNED BRANCH:** calibration/observability_standards_usecases_20261023 (isolated; prior models and parallel pool branch NOT changed).
- 20 independent charts as PNG+SVG based on executed 2025 300-second Simulink outputs, with source chart manifest.
- 34 KPIs with units, equations, model vs measured provenance; official PUE, ERF, WUE, REF NOT available without actual physical metering; synthetic PUE assumed 1.36.
- 14 normalized signal definitions, 300-second samples in UTC, 420480 data points across four annual cases pass allocation and thermal partition test.
- 56 standard traceability requirements across 22 disciplines; catalog references rechecked including latest ISO/IEC 30134-2:2026 and ISO 9001:2026; effective Slovak pool public standards STN EN 15288-1+A1:2024 / 15288-2:2019. Full licensed STN text NOT available or reviewed; all entries UNVERIFIED, not certified.
- 36 use cases with explicit input expected response, result, source and priority: 22 SOFTWARE PASS, 14 BLOCKED real measurements/hardware/legal verification; no false compliance claims.
- 56-entry cross-links standard -> relevant use case -> KPI -> missing evidence (requirements_tests_metrics_traceability.csv).
- Standalone offline dashboard HTML with plot selection and interactive filters, 20 PNG+SVG, all supporting JSON/CSV.
- Trilingual reports Standards_Graphs_Usecases_SK/RU/EN.pdf, 14/15/14 pages; PDF coordinate QA zero clipped words; all charts SVG parse and HTML script node syntax PASS.
- Obsidian calibration/observability_standards_usecases_20261023 has 61 SHA256-matched files; no collision.
- Immutable project ZIP OBSERVABILITY_STANDARDS_USECASES_20261023.zip, verified integrity.
- NEXT P0: obtain real IT electrical/thermal and WUE/ERF meters, OEM heat-pump and exchanger COP curves, hydronic/electrical UPS P&ID/SLD, hardware-in-the-loop & FAT/SAT, applicable current consolidated law/full license norms, signed independent safety case.

No autonomous background executor was started. STOP, ownership and OAuth boundaries respected.
