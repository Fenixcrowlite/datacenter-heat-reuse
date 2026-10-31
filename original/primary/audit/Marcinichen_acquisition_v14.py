"""Single-attempt official OA acquisition with immutable, timestamped evidence.

This command does not verify article equations. It rejects HTML, malformed PDFs,
and PDFs whose opening pages do not identify the requested title and DOI.
It never retries a rate limit or replaces existing source/evidence files.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.request

import fitz

ROOT = Path(__file__).resolve().parents[1]
URL = "https://infoscience.epfl.ch/bitstreams/30ae8dd8-5fc0-481b-8ccd-284d7f125195/download"
DOI = "10.1016/j.applthermaleng.2011.12.008"
TITLE = "on-chip two-phase cooling of datacenters"
MAX_BYTES = 18_000_000
SOURCE = ROOT / "sources" / "papers" / "Marcinichen_2012_v14.pdf"


def inspect_candidate(data):
    """Return binary/identity provenance; do not infer scientific validation."""
    if not 4096 <= len(data) <= MAX_BYTES:
        raise ValueError("candidate outside 4096..18000000 byte acquisition bounds")
    if not data.startswith(b"%PDF"):
        raise ValueError("candidate is not a PDF; HTML/access pages rejected")
    try:
        with fitz.open(stream=data, filetype="pdf") as doc:
            if doc.page_count < 2:
                raise ValueError("candidate has fewer than two pages")
            opening = " ".join(" ".join(doc[i].get_text() for i in range(min(2, doc.page_count))).lower().split())
            if DOI not in opening or TITLE not in opening:
                raise ValueError("opening pages do not match both requested title and DOI")
            return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                    "page_count": doc.page_count, "identity_gate": "TITLE_AND_DOI_MATCH",
                    "equations_verified": False, "temperature_tables_verified": False}
    except (fitz.FileDataError, fitz.EmptyFileError) as exc:
        raise ValueError("candidate has PDF magic but cannot be parsed") from exc


def acquire_once():
    started = datetime.now(timezone.utc)
    stamp = started.strftime("%Y%m%dT%H%M%S%fZ")
    result = {"started_utc": started.isoformat(), "doi": DOI, "url": URL,
              "channel": "local_python_urllib", "attempts": 0,
              "primary_text_verified": False, "primary_table_or_equation_match": False,
              "independent_validation": "NOT_PERFORMED"}
    try:
        if SOURCE.exists():
            result.update(status="EXISTING_SOURCE_INSPECTED_NO_WRITE", **inspect_candidate(SOURCE.read_bytes()))
        else:
            result["attempts"] = 1
            req = urllib.request.Request(URL, headers={"User-Agent": "AcademicHeatReuseAudit/0.14", "Accept": "application/pdf"})
            with urllib.request.urlopen(req, timeout=18) as response:
                result.update(http_status=response.status, content_type=response.headers.get("Content-Type"))
                data = response.read(MAX_BYTES + 1)
            provenance = inspect_candidate(data)
            # Exclusive creation prevents overwrite if another run acquires it.
            with SOURCE.open("xb") as target:
                target.write(data)
            result.update(status="ACQUIRED_IDENTITY_ONLY", source_path=str(SOURCE.relative_to(ROOT)), **provenance)
    except urllib.error.HTTPError as exc:
        result.update(status="HTTP_ACCESS_BLOCKED", http_status=exc.code, reason=exc.reason,
                      retry_after=exc.headers.get("Retry-After"))
    except urllib.error.URLError as exc:
        error = exc.reason
        result.update(status="TRANSPORT_BLOCKED", error_type=type(error).__name__,
                      errno=getattr(error, "errno", None), winerror=getattr(error, "winerror", None),
                      error=str(error))
    except (ValueError, OSError) as exc:
        result.update(status="CANDIDATE_REJECTED_OR_FILESYSTEM_BLOCKED", error_type=type(exc).__name__, error=str(exc))
    result["finished_utc"] = datetime.now(timezone.utc).isoformat()
    out = ROOT / "audit" / f"Marcinichen_acquisition_v14_{stamp}.json"
    with out.open("x", encoding="utf-8") as target:
        json.dump(result, target, ensure_ascii=False, indent=2)
    print(json.dumps({"status": result["status"], "evidence": str(out.relative_to(ROOT))}, ensure_ascii=True))
    # Successful logging is separate from successful acquisition.
    return 0 if result["status"] in {"ACQUIRED_IDENTITY_ONLY", "EXISTING_SOURCE_INSPECTED_NO_WRITE"} else 2


if __name__ == "__main__":
    raise SystemExit(acquire_once())
