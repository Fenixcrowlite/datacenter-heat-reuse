"""Acquire public TES primary sources into this project only; preserve all prior files."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import requests

ROOT = Path(__file__).resolve().parents[1]
URLS = [
    "https://mdpi-res.com/d_attachment/energies/energies-12-04275/article_deploy/energies-12-04275.pdf",
    "https://air.unipr.it/retrieve/e177fbc6-a722-50b0-e053-d805fe0adaee/energies-12-04275.pdf",
    "https://air.unipr.it/retrieve/handle/11381/2868671/188025/energies-12-04275.pdf",
]

def main():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    records = []
    artifact = ROOT / "sources" / "papers" / f"Cadau_2019_TES_v28_{stamp}.pdf"
    for url in URLS:
        record = {"url": url}
        try:
            response = requests.get(url, timeout=25)
            record.update(http_status=response.status_code,
                          content_type=response.headers.get("Content-Type"),
                          bytes=len(response.content), final_url=response.url)
            if response.status_code == 200 and response.content.startswith(b"%PDF-"):
                with artifact.open("xb") as stream:
                    stream.write(response.content)
                record.update(saved=str(artifact.relative_to(ROOT)).replace("\\", "/"),
                              sha256=hashlib.sha256(response.content).hexdigest())
                records.append(record)
                break
            record["saved"] = None
        except requests.RequestException as exc:
            record.update(saved=None, error=type(exc).__name__, detail=str(exc))
        records.append(record)
    payload = {"utc": datetime.now(timezone.utc).isoformat(), "purpose": "public primary TES source acquisition; no publication or credentials", "attempts": records}
    report = ROOT / "audit" / f"TES_source_acquisition_v28_{stamp}.json"
    log = ROOT / "automation" / "logs" / f"TES_source_acquisition_v28_{stamp}.log"
    report.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    log.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return int(not artifact.exists())

if __name__ == "__main__":
    raise SystemExit(main())
