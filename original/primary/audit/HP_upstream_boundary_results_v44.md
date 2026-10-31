# v44 upstream equipment and auxiliary-boundary results

UTC 2026-10-10T17:42:00.742886+00:00. PASS scoped boundary audit; upstream calibration blocker OPEN.
Production model remains0.42, SHA256 `db9777f73cbe9c6e56f0e9900d2c7b6c915588768b68b2464809802109b69a9c`.
No new SLX, plant/helper change or Stateflow execution is claimed this run.
Existing v42 actual six-mode acceptance and independent QA remain preserved.

MATLAB 26.1.0.3346908 (R2026a) Update 5: 486 synthetic vectors,
2648 PASS / 0 FAIL. Saved MAT was reopened and every numeric matrix,
specification and report matched the JSON export. Independent exact Fraction
port/ratio, two-axis, receipt, source-locator, artifact and preservation QA:
7228 PASS / 0 FAIL. Reviewer mutation checks4 PASS / 0 FAIL,
counted separately. Check breakdown: {"MAT": 3, "artifact": 2, "energy": 972, "equation": 5346, "execution": 4, "numeric": 486, "preservation": 88, "scope": 1, "source": 2, "two_axes": 324}.
The successful batch exit0 log contains no Warning or Error text; initial
sandbox startup failure is retained with exit1 in its own log/receipt.

New derived finding: COPHsystem-EERsystem equals
1-(1-alpha)*Wa/(Wc+Wa), for the stated expanded boundary and no other loss.
Using the same electrical denominator is insufficient to assert a difference1
unless Wa=0 or all auxiliary power becomes counted hot output.
This corrects the v43 report's auxiliary sentence; its compressor-only equations
and executed results are preserved and unchanged. No v42 code defect is claimed.
Same-lift MATLAB groups also show different EER at different absolute temperatures.
This rejects an unsupported information reduction; no reference62 polynomial
equation/order/coefficient is claimed.

Local source20 p8 and p27 were visually inspected again. Its explicit upstream
supplement citation is verified; upstream primary content is not. Retrieved
[university repository record](https://flore.unifi.it/handle/2158/1432822)
has no attached file. Publisher indexed metadata/abstract identify the citation;
direct publisher/DOI opens failed. Exact DOI/title/PII and supplement-oriented
searches found no verified supplementary download link. Manufacturer public
pages identify selector availability and coefficient access routes, but no
equipment-specific map was acquired. Local urllib attempts all failed with
WinError10013; those are local access failures, not observed publisher HTTP
responses. These observations do not prove global/public unavailability.

Required calibration evidence remains: primary supplement identity/version,
both refrigerant-temperature axes, fit equations/coefficients and units, product/
refrigerant, superheat/subcooling, speed/rating convention, admissible envelope,
fit errors and validation data, plus auxiliary electrical/thermal destinations.
Full signoffs0/31; no physical validation or article replication.
Derivation and boundary contract: audit/HP_upstream_boundary_derivation_v44.md.
Access records: result-directory acquisition.json and source_observations_v44.json.
Evidence: results/hp_upstream_v44_20261010T173843_592523Z; results/hp_upstream_v44_20261010T173843_592523Z/independent_QA_v44_20261010T174040_285460Z.json.

Next actionable task: Audit annual reporting boundaries in matlab/+dchr/compute_metrics_v2.m and compute_metrics.m, using fresh two-interval MATLAB fixtures and independent integrated energy arithmetic. Check whether mean_cop is a heat-weighted diagnostic or an annual heat/electricity ratio, and whether finite-backup Unmet_Heat_MW is excluded from delivered reuse. Map pump/fan electricity and thermal destinations explicitly before an additive reporting repair; do not invent auxiliary loads or change v42 dispatch. Keep upstream62 calibration blocked until its primary supplement and equipment-specific coefficient/domain evidence are acquired. Do not repeat identical failed acquisition attempts without a new accessible route.
Stop after this coherent task and handoff.
