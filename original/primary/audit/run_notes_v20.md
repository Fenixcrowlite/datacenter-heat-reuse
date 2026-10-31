# v20: Source 01 primary audit (partial)

Source: Wahlroos et al. (2017), DOI 10.1016/j.energy.2017.08.078.
Original: sources/papers/01_Wahlroos_Espoo_2017.pdf. SHA256 f70dc2d65045dc6e23ebc069ebdfcdca566b4134b01f84a08e916b46bc92f651. PDF p1 is repository cover.

Visual check PDF p4 / journal 1230, Eq(1): ERE=(P_DataCenter+P_Cooling-P_Reuse)/P_IT. Reuse is subtracted. ERE is dimensionless; prevent cooling double count.
PDF p6 / journal 1232: EnergyPRO, hourly dispatch for 2013/2015; direct DH supply without temperature upgrading was assumed. PDF p7 / journal 1233: thermal storage excluded, CHP minimum commitment 168 h, constant DH return/supply 49/87 C.

PDF p7 prints a 20,000 m2 hot-water tank with 800 MWh. Unit is suspicious; unresolved source-unit discrepancy, not silently corrected.
PDF p8 / journal 1234, Table2: marginal-cost constant waste heat MW 2013 moderate/high 23.4/58.5, 2015 moderate/high 18.7/46.8. These differ from monthly-shifting 100%-utilization scenarios.

PDF p9 / journal 1235, Table4: overall savings 0.6/6.3/3.2/7.3 percent. Production-cost reductions 5.5/12.2/4.0/9.9 percent. 2013 high 12.2% is NOT overall savings (6.3%).
Reproduce: python audit/audit_wahlroos_primary_v20.py. Results: audit/evidence_source01_v20/primary_checks_v20.json and five rendered original pages. 11/11 hash/text/locator checks passed; PDF pages 4,7,8,9 inspected visually.

CLASSIFICATION: partial primary-original evidence, NOT full paper signoff, NOT independent physical validation, NOT reproduction of EnergyPRO or HP/TES behavior. Full signoffs 0/31. Next: audit seasonal prices in Table1 and input provenance.
Read-only verification: python audit/verify_source01_v20.py -> PASS 11/11 recorded checks, 5 renders, 31 CSV rows, 0 signed off. This verifies evidence integrity, not physical validation.
