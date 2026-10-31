# v21: Source01 Table 1 prices

Original: sources/papers/01_Wahlroos_Espoo_2017.pdf, SHA256 f70dc2d65045dc6e23ebc069ebdfcdca566b4134b01f84a08e916b46bc92f651. Table 1 is on PDF p7, journal p1233. Unit printed EUR/MWh (PDF text extraction represents euro as V). January to December: 40.2, 40.4, 38.6, 27, 19.2, 16, 13.8, 14.6, 19.2, 24, 32.8, 38.

Section 4.1.2 states proposed marginal procurement prices adopted from reference [20], Stenberg 2015 Aalto thesis, based on Finnish marginal heat-production costs and interviews. The thesis original has not been verified. These are not Nord Pool electricity prices and should not be treated as measured tariffs.

Checks: python audit/audit_source01_table1_v21.py -> PASS 18/18; python audit/verify_source01_table1_v21.py -> PASS 18/18 and integrity checks. Evidence audit/evidence_source01_v21/table1_checks_v21.json, table1_prices_v21.csv, source01_original_page07_v21.png. Scope: partial agreement with original article only. No independent physical validation or full-paper signoff. Full signoffs 0/31. Next: obtain and inspect Stenberg 2015 original thesis.
