# v44 upstream map and electrical/thermal boundary audit

Production remains accepted saved Stateflow v42 and HP component v40.
This additive audit changes no plant equation or saved model.

The local source20 PDF p8 Eqs(4)-(7) and p27 references61/62 were visually
inspected again using the preserved v43 page PNGs. Its SHA256 is
713d1ea564efacbb8813eafc474482292b167140e1b2f47d1e234d3db7302a6e.
p8 explicitly cites reference62's supplementary file for validation of a
polynomial EER formulation; this confirms the citation, not the upstream
coefficients. The [university record](https://flore.unifi.it/handle/2158/1432822)
matches the citation but lists no attached files. Publisher indexed metadata
and abstract establish identity only; direct publisher/DOI access failed.
No numbered equation from reference62 is transcribed or inferred.

The [manufacturer selector page](https://www.danfoss.com/en/service-and-support/downloads/dcs/coolselector-2/)
describes online access and report export. Its launch link led to the public
agreement entry page; no application was installed or agreement accepted.
The [manufacturer MLZ/LLZ announcement](https://www.danfoss.com/en/service-and-support/tech-insider/commercial-refrigeration-and-sensing-solutions/)
points to Coolselector for maps and polynomial coefficients. That statement
does not identify the equipment used by source20 or disclose its fitted EER.
Local urllib attempts were blocked by WinError10013, not observed server HTTP
denials. Web observations and local acquisition failures are separately retained.
No assertion that the paper or coefficients are globally unavailable is made.

## Two-temperature information cannot be reduced to lift without evidence

From the verified source20 cooling definitions only:

    EER = etaC * TL / (TH - TL), 0 < TL < TH, 0 < etaC <= 1

At fixed lift d and constant etaC, shifting both absolute temperatures by s
changes EER by etaC*s/d. The derivative along constant lift is etaC/d, nonzero.
Thus a function of lift alone cannot reproduce even this simple two-axis
relationship over an operating region containing such shifts. Synthetic example:
TL=278.15K or308.15K, d=30K, etaC=0.5 gives EER4.6358333333 or5.1358333333.
This is an information-loss proof for this assumed constant-factor law, not
a proof of the form/order/coefficient count of the unacquired reference62 fit.

Temperatures in ratios must be Kelvin; temperature differences have K units.
For an eventual empirically fitted polynomial, the exact temperature convention,
cross terms, degree/order, output definition, normalization and coefficient units
must be transcribed. A generic term a_ij*T_e^i*T_c^j has coefficient units
output/(temperature-unit)^(i+j). Temperature offsets change coefficients;
changing input Celsius to Kelvin without transforming coefficients is invalid.
This dimensional statement supplies no article coefficients or polynomial form.

## Auxiliary heat placement is needed as well as electrical denominator

The paper's compressor boundary is QH=QL+Wc; fans are accounted separately.
Let Wa>=0 be auxiliary electricity and alpha in[0,1] the fraction of that
auxiliary power delivered as heat to the specific counted heating output.
This alpha is a synthetic boundary parameter; the article does not calibrate it.
For the expanded boundary with no other losses:

    QH_counted = QL + Wc + alpha*Wa
    Wtotal = Wc + Wa
    EERsystem = QL/Wtotal
    COPHsystem = QH_counted/Wtotal
    COPHsystem - EERsystem = (Wc + alpha*Wa)/(Wc + Wa)
                           = 1 - (1-alpha)*Wa/Wtotal

All Q/W are powers in kW; ratios, alpha and Wa/Wtotal are dimensionless.
These equations assume steady operation, counted QL unchanged, no other thermal
loss and identical electrical denominator. Additional losses require explicit
terms; they cannot be absorbed by silently changing the efficiency convention.

Correction to the v43 derivation's auxiliary sentence: an identical enlarged
electrical boundary alone is insufficient for COPH=EER+1. All included auxiliary
electricity must also be credited as heat at the counted hot outlet (or Wa=0).
The v43 compressor-only conversion, matrices and saved-model results remain
unchanged. This is a reporting-boundary correction, not a detected v42 code defect.

Synthetic example QL=1000kW, EERcomp=4, Wc=250kW, Wa=25kW, alpha=0:
EERsystem=3.6363636364, COPHsystem=4.5454545455, difference10/11.
If alpha=1 and no other loss, QH=1275kW and the difference is1.
These are engineering examples, not manufacturer performance points.

486 MATLAB vectors span TL_C5/20/35, lift10/30/60K, etaC0.35/0.5/0.65,
QL1/1000kW, Wa/Wc0/0.1/0.5, alpha0/0.5/1. Exact Fraction QA uses
inverse work Wc=QL*d/(etaC*TL), separate output-port checks, same-lift groups
and saved-MAT re-export; it does not import the MATLAB or production functions.
Reviewer mutations are separately labelled synthetic selfchecks.

## Required acquisition handoff

Keep the source20-specific calibration blocker OPEN. Acquire the reference62
primary PDF and identified supplementary file through an accessible official
route; verify publication identity, supplement association/version and bytes.
Extract fit equations/coefficients, axes and units, compressor model/refrigerant,
superheat/subcooling and speed/rating convention, two-dimensional admissible
envelope, fit error and validation points. A current arbitrary Coolselector
product export cannot by itself reproduce the paper's fit or original database.
For each auxiliary, specify electrical consumption, thermal destination and
whether its heat enters counted QH; carry losses and pump/fan power explicitly.
Only then design a separate refrigerant-map backend and compare to v42.

No physical validation, article replication or full source signoff is claimed.
No new Stateflow regression was needed because no plant/model helper changed.
