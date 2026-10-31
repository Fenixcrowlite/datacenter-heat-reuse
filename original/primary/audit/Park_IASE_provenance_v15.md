# Park [38] IASE provenance, v15

UTC: 2026-10-08T22:01:37Z. Bounded source investigation; production models and earlier evidence are unchanged.

## Evidence and source identity

Sintong's local original PDF, printed/PDF p70 (index 69), identifies [38] as Seonghyun Park and Janghoo Seo, *Analysis of Air-Side Economizers in Terms of Cooling-Energy Performance in a Data Center Considering Exhaust Air Recirculation*, Energies 11(2), 444 (2018), DOI [10.3390/en11020444](https://doi.org/10.3390/en11020444). Publisher full text confirms the identity. This is primary article body evidence, not abstract-only evidence.

The [publisher PDF](https://mdpi-res.com/d_attachment/energies/energies-11-00444/article_deploy/energies-11-00444.pdf), p9 (index 8), supplies parsed Eq22-23:

```text
T_RA* = T_RA + epsilon_HX (m_dot_OA / m_dot_RA) x (T_OA - T_RA)  [22]
HX_flow_ratio = (m_dot_OA + m_dot_RA) / (2 m_dot_RA)             [23]
```

Park states effectiveness 70% immediately afterward. Park attributes these component equations to Ham, Kim, Choi and Jeong, Applied Energy 138 (2015), 258-275, reference [21], verified in publisher PDF p14. That upstream full text was not verified in this run. See also the [publisher HTML](https://www.mdpi.com/1996-1073/11/2/444), Section 3.3 and references.

## What the evidence does and does not resolve

Park's parsed Eq22 shows `epsilon_HX` followed by the parenthesized mass-flow ratio; it does **not** show a separately written `HX_flow_ratio` factor. Sintong p30, Eq15, visually shows `epsilon HX_flow_ratio(r)` with `r=m_dot_OA/m_dot_RA`. Eq16 defines the arithmetic mean expression. The local page render was inspected: `audit/Sintong_p30_IASE_v15_20261008T220047_157053Z.png`. Its source SHA256 is `8149370d2df0c5899c844095f3890fea112c3d81eaff6671cb3cf0f3da9185f5`.

**Therefore the two available transcriptions differ.** This run cannot certify a faithful substitution or determine whether the parentheses indicate a function argument or multiplication. A fixed scalar effectiveness in Park makes multiplication by `r` a plausible reading, but plausibility is not author intent or a verified normalization. Preserve the printed notation and label candidate interpretations explicitly.

Independent physics should begin by defining the coefficient `alpha` in `T_RA*=T_RA+alpha(T_OA-T_RA)`. For a passive two-stream sensible exchanger with no additional heat/work input, positive flows and equal specific heats, both outlet bounds require `0 <= alpha <= min(1,r)`. The root's independent domain audit derives and tests this. Substituting any ambiguous author coefficient is a separate provenance step; passing physical tests alone will not prove source fidelity.

## Acquisition and visual-review limitations

- Publisher article-body text and PDF page-labelled parsed equations: accessed through web tools.
- Publisher PDF screenshot attempts (p9 and p14): failed with cache miss. A same-paper Semantic Scholar mirror also opened as text but failed screenshot retrieval. No visual Park equation confirmation is claimed.
- Local Python PDF download: blocked by socket restriction `WinError 10013`; no local Park PDF was created. Exact evidence: `audit/Park_acquisition_v15_20261008T215837_580374Z.json`.
- Browser fallback: in-app browser unavailable; Chrome tab creation approval review timed out. This was a timeout, not an approval rejection. No settings were changed and no user intervention is required for the delivered text-only provenance finding.

Status: `PARK_PRIMARY_BODY_TEXT_VERIFIED / PARK_EQUATION_VISUAL_PENDING / UPSTREAM_HAM_NOT_VERIFIED`. This is a partial equation-provenance checkpoint; no complete article replication, calibration or source signoff.

Next actionable task: obtain and visually inspect Park p9, then Ham's cited component equation and definition of effectiveness; reconcile their flow normalization with Sintong p30 before adopting an IASE correlation for unequal or vanishing outdoor flow.
