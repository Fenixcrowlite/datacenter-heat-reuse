# Equipment options for DataCenter Heat Reuse
**23 October 2026 | Engineering screening, not procurement approval.**

## Selection recommendation
At a 35°C available source, shortlist a **custom-engineered low-temperature titanium gasketed plate heat exchanger** for direct 150 kW pool heating. Request certified four-port thermal duty and pressure losses before purchasing. A 25°C source cannot directly produce 29.5°C pool supply water in the specified 3K hot-side drop case; the alternatives are a dedicated heat pump, hotter district heating water, or a re-engineered circuit.

**Critical catalogue warning:** Pahlén Maxi-Flo titanium MFT680 lists **200 kW at a 60K temperature difference** with 2.11m² of transfer surface. That rating does not prove 150kW at 35°C source and 27.5°C pool return. [Pahlén](https://www.pahlen.com/products/pool-heating/heat-exchangers/maxi-flo-titanium/).

## Counterflow thermal sizing: 150kW
- Source hot-side **35→32°C**, calculated flow **43.17 m³/h**.
- Pool branch **27.5→29.5°C**, calculated flow **64.76 m³/h**.
- LMTD **4.983 K**, clean UA **30.10 kW/K**, area-factor 1.25 design **37.63 kW/K**.
- Assuming overall U=1500 W/(m²·K), **25.1 m²** transfer area; manufacturer U, fouling, corrosion and hydraulic Δp are still unverified.
- With source 32°C, area about **63.9 m²**; at 40°C about **12.5 m²**, with all other assumptions held fixed.

Clean source-side pump candidate **Grundfos TPE** for ~43 m³/h at assumed 70kPa. Pool water side **SPECK BADU 21-80** resistant pump for ~65 m³/h at 80kPa, subject to actual curves and pool-water chemistry. At assumed 60% overall pump efficiency, the combined pump draw is ~3.8 kW while heating, or ~8.52 MWh/year including a 0.25kW continuously energised control cabinet. At selected electricity pricing this is ~€1,296 per year. Use Siemens SITRANS TS500 Pt100 and an independent heat meter/temperature trip. Separate pool and IT circuits physically.

## District heat-pump bank
Measured from the prior **synthetic IT / NASA weather 2025 Simulink input and output**: DC heat source 6.970 MW mean, 7.699 MW P95, 8.291 MW max; district HP useful output 5.477 MW mean, 9.396 MW P95, **10.372 MW max**. Therefore the earlier 9-MW investment sensitivity does **not cover the model peak**.

A detailed scan of 105,120 five-minute source/model records favors **10 MW operating nameplate + 2 MW N+1 spare**: five approximately 2-MW duty modules and one redundant module. The source-driven model exceeds 10 MW for 22 hours and only **2.74 MWh/year** of thermal output. Existing gas back-up could cover this modeled shortfall. Each real module still requires a certified output rating at the exact duty. See `Module_capacity_tradeoff_SK.md`. Suitable manufacturer families to investigate include **Carrier AquaForce 61XWH-ZE** (water output up to 85°C) and **Oilon ChillHeat P** (up to 120°C). No certified 25/35°C-source to 70°C-supply capacity or COP is presently available. Require validated selection outputs at 25/20, 35/30, 45/40°C source and 50/70, 60/70, 70/80°C sink across PLR 25/50/75/100%.

## Investment sensitivity: pool branch
Original executed 2025 Simulink yields gross annual energy OPEX advantage **€12,306.50** for direct 35°C reuse and **€4,279.76** for the 25°C dedicated HP at assumed COP4. Selected Eurostat Slovakia 2025 rates: electricity €152.07/MWh, natural gas €55.63/MWh fuel. Adding assumed pumps, maintenance, 6% discount and 20 years gives direct-exchanger NPV **+€70,967** at €45k CAPEX, **+€34,085** at €75k, **−€8,944** at €110k. The approximate NPV=0 installed budget threshold is **€102,725** direct and **€27,387** for dedicated HP COP4. These numbers are **engineering budgets, not vendor quotations**.

## Procurement evidence required
- Certified capacity and COP(T_source, T_sink, PLR), part load minimum, annual auxiliaries and source/sink pressure drops.
- Formal HX rating at the exact 150kW, 35/32↔27.5/29.5°C condition with material and fouling assumptions.
- Material compatibility with chlorinated/salt pool water, monitored isolation between loops.
- Redundant pool limit sensor/valve and **independent N+1 IT cooling** for full critical server load.
- Complete electrical connection, installation, commissioning, statutory compliance, warranties and written price.

**Unverified:** actual data-centre coolant and IT time-series, manufacturer operating-point COP, pump curves and selected fouling conditions, regulatory complete standards, supplier price and capital cost. The study is for engineering RFQs and sensitivity analysis only.