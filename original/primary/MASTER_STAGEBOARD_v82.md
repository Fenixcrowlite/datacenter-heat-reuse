# Saved-Stateflow refrigerant approach experiment v82

UTC 2026-10-13T10:29:50.956978+00:00.

Preserved saved v80 actually executes 42 schedules / 78 held intervals / 78 positive segments / 0 interior events. MATLAB 128 PASS / 0 FAIL; independent equation/artifact QA 14765 PASS / 0 FAIL; 48 monotonic comparisons and four separate reviewer self-checks PASS. All six required final modes are observed. The clean saved model is reopened and replayed bitwise.

At source-water 30 C, changing both approaches from 1 K to 10 K increases fixed-output compressor electricity by 62.303507% while delivered service stays 0.25 MWh. At fixed evaporator budget 0.1 MW, source-limited service increases 11.190391% through added compressor work. COP decreases in both cases. Extra condenser output is not extra recovered waste heat.

| Boundary and approaches | Delivered (MWh) | Recovered source (MWh) | Compressor (MWh) | Heating COP |
|---|---:|---:|---:|---:|
| fixed_output_T30_e1_h1 | 0.250 | 0.2152325076 | 0.03476749239 | 7.190625000 |
| fixed_output_T30_e10_h10 | 0.250 | 0.1935711407 | 0.05642885933 | 4.430357143 |
| source_limited_T30_e1_h1 | 0.05807672892 | 0.05000000000 | 0.008076728925 | 7.190625000 |
| source_limited_T30_e10_h10 | 0.06457574180 | 0.05000000000 | 0.01457574180 | 4.430357143 |


Source20 printed pages 8 and 27 were visually verified against preserved publisher bytes. Its compressor balance and refrigerant-temperature convention support the limited derivation. The [university record](https://flore.unifi.it/handle/2158/1432822) lists no attached files; the new [research-group route](https://www.dief.unifi.it/vp-278-research.html) links the DOI, not a supplement. Direct publisher open returned 403 and the PDF-route tool cache missed. Metadata and abstract do not supply calibration coefficients. These observations do not establish global unavailability.


Model `matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v80.slx`, SHA256 `f7032682f4d6c338a99f1425311a807254c3022ba8527dba5f616f53b0ac66be`. Evidence `results/hp_approach_v82_20261013T101754_139297Z` includes timestamped MATLAB/Simulink logs, successful receipt, 42 original MAT files, reopened combined MAT, binary exports, independent numeric CSV, specification, primary observations, source snapshots, reviewer revision and preservation hashes. Failed attempts remain in the directory identified by prior_attempts.json.


Limitations:
- Synthetic reduced constant-cooling-factor HP and ambient-reference TES; no equipment calibration, article replication, measured physical validation, annual or generated-code acceptance. Full primary signoffs remain 0/31.
- Checkpoint 0.82 is an executed sensitivity experiment; saved model remains 0.80, thermal kernel/trace schema 75 and reporting API 0.76. No new SLX or production equation change.
- Approach values, eta=0.5, source coefficient, temperature/glide and auxiliary settings are engineering assumptions. The 2025 commercial-device correlation supplement is not acquired.
- No independent compressor-electricity capacity is enforced. Increased source-limited condenser service at larger approaches comes from added compressor work, not extra waste heat. This is a model-boundary limitation, not a numerical dispatch defect.
- Independent QA is same-agent algorithmic independence: exact Fraction algebra and 120/160-digit exp/log trajectories call no production MATLAB solver. MATLAB reopens MAT for binary export; no independent personnel or independent MAT-parser claim.
- The 36 comparison schedules remain below the hot-water floor and contain no interior events. Six standard fixtures cover final modes. No general nonlinear/variable-source-map sensitivity is proved.
- Restricted startup, first batch JSON cell/struct failure, and first QA single-row-shape failures are retained. The reviewer shape repair is separately hash-sealed; production outputs, equations and tolerances were unchanged.


Next actionable task: Acquire the reference62 primary supplement or inspect the author-group-linked 2022 predecessor DOI 10.1016/j.applthermaleng.2022.118194 as separately labelled primary evidence. Do not substitute predecessor coefficients for the 2025 fit. Trace compressor electrical rating, refrigerant axes, admissible map domain and auxiliary thermal destinations before adding a separate explicit electrical-power capacity backend. Preserve accepted v80 and v81-v82 evidence; no repeated monitor tests without a new hypothesis.
