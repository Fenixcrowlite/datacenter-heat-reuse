# Private offline recipient kit (post-C130 review candidate)

**Distribution hold, verified 2026-10-31:** the immutable C130 source
archives contain browser QA profile/state files and a historical
\`runtime/secrets.json\` path; this does **not** prove valid credentials
exist, but these artifacts must not be sent to external recipients.
No explicit project \`LICENSE\` or clearances for supplied PDF/PPTX content
were found in the archive manifest audit. The build command now requires
\`--internal-only\` and marks the output \`PRIVATE_LOCAL_ONLY\`. Do not
promote an internal evidence ZIP to an externally shareable package.
Read \`docs/migration/2026-10-31-distribution-hold.md\` first.

This optional **review kit** combines an exact Git tree snapshot of PR #1 with
the **three immutable C130 research source ZIPs**. It is intended for
collaboration and handoff without requiring Git, internet access, MATLAB,
cloud APIs or a GPU on the recipient machine. Python 3.11+ is required for
the native application. Docker is optional.

The kit is **not** a published final release, not a MATLAB replacement for
unported historical projects, and not approval to operate the live SCADA.

## Build at the source workstation

First independently verify the three original archive assets. Build from a
committed review branch, not the local working tree. The builder uses
`git archive <commit>`, so local untracked caches, working copies, logs and
credentials are not packed into the code snapshot. The code snapshot is built from an explicit allowlist of runnable project paths; archived browser QA profiles under the older research trees are not included. The archive builder also rejects browser/credential filenames inside the allowed code directories and scans their contents for high-confidence GitHub token/private-key signatures.

```powershell
python -m tools.portable_kit build --checkout . --archives C:\path\to\downloads --out C:\path\to\DCHR-internal-forensics-only.zip --internal-only
```

The output is a single ZIP with `kit-manifest.json`,
`code/repository.zip`, and the three original source ZIPs under
`sources/`. The kit records SHA-256 + file size for all four assets.
The builder refuses a pre-existing output or an archive with an unexpected
digest. It does not touch the old assets.

## Recipient verification and offline run

The reviewer can use the included standalone `verify_portable_kit.py`
script distributed alongside the kit ZIP (also present in the repository):

```sh
python verify_portable_kit.py verify DCHR-offline-review-kit.zip
python verify_portable_kit.py unpack DCHR-offline-review-kit.zip ./review-recipient
python -m zipfile -e review-recipient/code/repository.zip review-recipient/app
cd review-recipient/app
python -m heat_reuse verify
python -m heat_reuse serve
```

Open `http://localhost:8080` for the English/Slovak interactive
laboratory, its visual heat-flow model, charts and saved experiments. Docker
can be built locally if the pinned base image is already cached; **this kit
does not contain a Docker image**, so an offline recipient without that
base image should use native Python.

To restore all old research roots (several gigabytes / ~98,591 files), from
the application source run:

```sh
python -m tools.snapshot restore ../sources/heat-reuse-source-2026-10-30.zip ../historical
python -m tools.snapshot restore ../sources/heat-reuse-supplement-2026-10-31.zip ../historical
python -m tools.snapshot restore ../sources/heat-reuse-scientific-qa-correction-2026-10-31.zip ../historical
```

The three source archives remain unchanged and are restored only into new
empty paths. The kit's code snapshot comes from the new PR and must **not**
be confused with the older C130 source cutoff.

## Integrity and limitations

Check the full-kit SHA-256 against an independently transmitted SHA in the
handoff note; the internal manifest alone cannot establish authenticity
against someone able to modify the entire ZIP. The verifier rejects
missing, extra or duplicate ZIP members and checks every member's exact
SHA-256 before creating a recipient directory. Re-extraction refuses
overwriting the destination.

Verified native tests are evidence of synthetic MATLAB case reproducibility,
**not equipment validation**, financial profitability or legal redistribution
permission. Keep the private kit under the project's access controls and
obtain independent review before a public release.
