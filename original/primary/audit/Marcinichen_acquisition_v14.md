# Marcinichen 2012: v14 acquisition defect and evidence boundary

Run date: 2026-10-08 UTC. DOI: `10.1016/j.applthermaleng.2011.12.008`.
Scope: obtain the original needed to resolve the pumped/compressed temperature distinction in the Ebrahimi review. **Full original not acquired; no Marcinichen equation, table, page, temperature or experiment validated in this run.**

## Observed access results

| Channel / official location | Observed result | Evidence class |
|---|---|---|
| Web open of [EPFL PDF](https://infoscience.epfl.ch/bitstreams/30ae8dd8-5fc0-481b-8ccd-284d7f125195/download) | HTTP 429 Too Many Requests | Failed primary acquisition; no binary PDF or content hash |
| Web open of [EPFL repository record](https://infoscience.epfl.ch/entities/publication/492583b0-1f58-4eea-9a7f-c130235a95c7) | Tool returned Internal Error; no HTTP status exposed | Failed record access; do not assign an assumed 429 |
| Web open of [publisher article](https://www.sciencedirect.com/science/article/pii/S1359431111007058) and its `/abs/` preview | HTTP 403 Forbidden | Failed direct access |
| Web search of official EPFL PDF / publisher title | Indexed first-page material and publisher section previews were returned | Cached/indexed excerpts only; not a complete primary-text inspection |
| Web open of [EPFL Graph Search record](https://graphsearch.epfl.ch/en/publication/492583b0-1f58-4eea-9a7f-c130235a95c7) | Metadata and abstract accessible; official-source link points to the same repository record | Metadata/abstract only; the page itself warns that it is generated and may be incomplete |
| Local Python `urllib`, official EPFL PDF | `TRANSPORT_BLOCKED`: PermissionError, WinError 10013, errno 13; acquisition process exit 2 | Local network permission failure; **not** a server HTTP response |

The timed local attempt is recorded in `Marcinichen_acquisition_v14_20261008T214932788906Z.json`: 21:49:32.788906–21:49:32.888251 UTC. The preceding web observations occurred during this run; their tools did not expose exact request timestamps. No date from a search index is treated as the paper publication date.

## Scientific implication

Publisher search previews describe an in-house steady-state cycle simulation and a power-plant heat-recovery case, rather than establishing a universal source temperature. This is a preview-level scope observation, **not validation of any case value**. The pump/compressor distinction remains an unresolved source gap.

Existing primary-review evidence is `audit/Marcinichen_reference_crosscheck_v11_RU.md` and `audit/Ebrahimi_Table_Crosscheck_v10_RU.md`. The preserved Ebrahimi PDF SHA-256 still matches `4aaffa92f30b0d5aa9c7a7e58e5ff8cad3eb05c9f8969b079d6127aab1600a40`. Its review-level pumped outlet near 48 °C and compressed outlet near 90 °C must not be promoted to independently checked Marcinichen results. In particular, do not adopt the liquid-pump Table 10 upper limit as a guaranteed pump-only design temperature or identify refrigerant condensing temperature with secondary-water outlet temperature.

Blocking defects: **B14-MARCINICHEN-PRIMARY** (official PDF rate-limited) and **B14-LOCAL-NETWORK** (local socket access prohibited). A successful metadata query or acquisition-gate unit test closes neither defect.

## Recovery deliverable and verification

`audit/Marcinichen_acquisition_v14.py` makes at most one official-URL attempt per invocation, preserves prior files, uses exclusive creation, caps response size, and rejects non-PDF, malformed, wrong-title and wrong-DOI candidates. A downloaded candidate is labelled identity-only until an actual page-level audit is performed. No download retry, access-control bypass, publication, user-setting or runner change was performed.

`python audit/Marcinichen_acquisition_v14_test.py`: **7 passed, 0 failed/errors**, with in-memory synthetic fixtures only. Tests check HTML/access-page rejection, spoofed PDF magic, size bounds, wrong DOI/title, and retention of false equation/table verification flags after identity matching. They are acquisition-safety tests, **not scientific validation**. Timestamped evidence is `Marcinichen_acquisition_v14_tests_20261008T214932831440Z.json`; console logs are `automation/logs/Marcinichen_acquisition_v14_tests_20261008T2149Z.log` and `automation/logs/Marcinichen_acquisition_v14_fetch_20261008T2149Z.log`. Log-name time labels are UTC minute buckets; exact start/finish times are inside JSON. The installed PyMuPDF emits a deprecation warning for its `fitz` alias; all gates passed with that alias in this run.

## Concrete handoff

1. On a later run after access conditions change, run the single-attempt acquisition command once. If it still returns 429/transport-blocked, retain the failure evidence and switch to local primary material; repeated immediate retries add no source evidence.
2. The bounded offline alternative is `sources/papers/09_Sintong_Stockholm_2023.pdf`, already present, SHA-256 `8149370d2df0c5899c844095f3890fea112c3d81eaff6671cb3cf0f3da9185f5`. Independently audit its HX heat-capacity/temperature bounds and sign/loss boundary using the corrected `audit/Sintong_primary_source_correction_v07_RU.md`; its source model is air-cooled and cannot settle the two-phase Marcinichen claim.
3. For the original Marcinichen temperature audit, an authorized library/author-supplied copy identified by this DOI is a specific alternate acquisition route. No request was sent. Once a valid PDF is local, map pump/compressor cases to secondary inlet/outlet, condensing temperature, page/table/equation and operating assumptions before calibrating any source-temperature scenario.

No source register, stageboard, status, dispatch result, MATLAB/Simulink/Stateflow availability or paper sign-off was changed by this lane.
