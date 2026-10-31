# Source audit №4: Hiltunen & Syri (2020), preliminary v0.6
Status: PARTIAL TECHNICAL ANALYSIS. Original 22-page PDF locally saved in ../sources/papers/04_Hiltunen_Espoo_2020.pdf (first page is repository cover); DOI 10.3390/en13143551.
Reference: Energies 13(14), 3551, Figures 1–3, Tables 1–5, equations (1),(2).
No claim of exact reproduction of proprietary EnergyPRO model.

## Model boundary, location and scenario assumptions (printed pages 5–9)
- Espoo DH, not Frankfurt; 2016 hourly Helsinki DH demand scaled to Espoo: 2601.7 GWh/y, peak 942.5 MW. Hourly 2016 weather; demand/temperature curves are input data, NOT derived by paper from first principles. DH return at constant 50°C, DH supply outdoor-temperature-controlled.
- EnergyPRO version 4.6.797, one-hour timestep over year, planned system year 2030. Dispatch priority from marginal costs. Two operating strategies: OS1 marginal cost; OS2 prioritizing waste heat. Three electricity price cases A 29.36, B 54, C 77 EUR/MWh. Prices are scenario assumptions, not Bratislava 2026 measurements.
- DCHP evaporator source from chilled-water DC loop: 15°C in, 10°C out (Table 1). Design HP: COP 3.7 at 14→7°C source and 50→65°C DH (Table 1); COP generated dynamically by EnergyPRO, detailed internal map NOT given as public analytic formula.
- Fig. 3 energy flow example: useful heat to DH 10 MW = 7.2 MW DC waste source + 2.8 MW electrical compressor input. That means COP=10/2.8 ~3.57, NOT exactly 3.7 design COP; source/design operating points are different.
- Buy-in priced on cold heat at evaporator, NOT on 10 MW heat output: mkt electricity 2.8 MW and payment on 7.2 MW recovered heat separately. Costing all condenser heat at DC buy-in price would double-count electricity.
- Network/thermal storage losses are **neglected** for Espoo in this article; model includes 20,000 m3 water storage, **857.5 MWh**, not Frankfurt 82 MWh.
- CHP CCGT min on/off 24 h, OCGT 4 h, both min output 40% (Table 5). Do NOT substitute 168 h previously reported for another Espoo paper.
- WWHP 70.5 MW and grouped gas/oil/bio-oil/wood boilers, net revenues of CHP electricity modeled. Counterfactual CHP removed when exploring larger DC HP capacities.

## Author equations (printed page 9/10)
Eq. (1): NPV = C [1 − (1+r)^(−t)] / r − C0, where C is constant annual NET cash flow after fixed expenses, r annual discount rate, t lifespan, C0 CAPEX.
Eq. (2): DPP = −ln(1 − C0 r/C)/ln(1+r), only real for 0 < C0*r/C < 1 and positive economic flow.
These are published formulas and must not be silently substituted by simple-payback C0/C.
Assumptions near eqs: 0.6 million EUR/MWth HP CAPEX, 2000 EUR/(MWth year) fixed O&M, 6% r, €234k/year network fixed connection. All historical/scenario, not local market quotations.

## Validation hooks before independent model
T-ESP-04-1: each hour Q_HP_out = Q_DC_evap + P_comp.
T-ESP-04-2: heat buy-in quantity Q_DC_evap, not Q_HP_out.
T-ESP-04-3: test 15→10°C DC loop and 50°C return; T_DH_supply from weather control curve.
T-ESP-04-4: CHP hourly min up/down 24h/4h, 40% min load and heat/power coupling.
T-ESP-04-5: annual sum hourly demand=2601.7 GWh and peak=942.5 MW for paper case; only if original series obtained.
T-ESP-04-6: 857.5 MWh storage with zero storage/network losses only in paper scenario; not generalized to real network.
T-ESP-04-7: NPV formula test r→0 limit: t*C − C0; negative NPV case should not give a misleading finite payback.
T-ESP-04-8: compare OS1 vs OS2 at same price input; no reuse of Frankfurt calibration factors.
T-ESP-04-9: distinguished 2016 observational input and 2030 scenario changes.
T-ESP-04-10: verify paper Eq (2) against Fig. payback; use only if source numerical cash flows can be recovered.

## Open questions
- Obtain raw hourly load, weather, supply curve, hourly spot price profiles, and manufacturer/EnergyPRO COP map before declaring independent replication.
- Inspect complete original result tables and supplementary data for paper level reproduction; until then PARTIAL.
