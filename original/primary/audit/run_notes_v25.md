# v25: Hiltunen & Syri (2020), original numerical audit (PARTIAL)
Original: sources/papers/04_Hiltunen_Espoo_2020.pdf, DOI 10.3390/en13143551.
Figure 3, PDF p7 (printed p6): 10 MW DH = 7.2 MW recovered + 2.8 MW electric, COP=3.57142857; not the Table1 WWHP design COP 3.7.
Table 2, PDF p8 (printed p7): 17 temperatures, 17 supply and 17 return prices in EUR/MWh checked against transcription.
Table 3, PDF p9 (printed p8): electricity scenarios A=29.36, B=54, C=77 EUR/MWh.
TES, PDF p9: 20,000 m3 and 857.5 MWh; paper explicitly neglects storage and network losses. Our v16 nonzero loss is a separate assumption, NOT validated by this paper.
No upstream Fortum tariff [6], HP source [15],[29], electricity scenarios [30]-[34], hourly data or EnergyPRO dispatch independently replicated. Full signoffs 0/31, no independent physical validation.
Reproduction: run audit/audit_hiltunen_primary_v25.py on a fresh project copy without v25 outputs; script refuses overwrite.
