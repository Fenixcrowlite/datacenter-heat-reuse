# v21: Source 01 Table 1 original-price audit

18/18 article checks passed; 12/12 monthly prices verified against Wahlroos et al. (2017), PDF p7 / journal p1233. Printed unit EUR/MWh and month/value alignment checked visually. DOI 10.1016/j.energy.2017.08.078.

The article cites Stenberg (2015) Aalto thesis [20] as the source of proposed procurement prices. Thesis original NOT verified. Prices are scenario assumptions, not Nord Pool electricity spot prices. Calendar 2015 day-weighted mean = 26.908493150684933 EUR/MWh (derived arithmetic, not an article result).

Reproducible tests: audit/audit_source01_table1_v21.py -> PASS 18/18. Read-only verifier audit/verify_source01_table1_v21.py -> PASS 18/18, 12 CSV rows, 31 bibliography records, 0 full signoffs and SHA integrity. Full source signoffs 0/31. No independent physical validation. Next: verify Stenberg thesis [20]. Old versions untouched.
