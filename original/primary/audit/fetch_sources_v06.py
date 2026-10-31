"""Fetch original literature without silently accepting HTML/access-denied pages."""
from pathlib import Path
import json, time, shutil, urllib.request, urllib.error
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "sources" / "papers"
PAPERS.mkdir(parents=True, exist_ok=True)
CATALOG = {
    "04_Hiltunen_Espoo_2020.pdf": [
        "https://www.mdpi.com/1996-1073/13/14/3551/pdf",
    ],
    "20_Verzino_Varna_2026.pdf": [
        "https://www.mdpi.com/1996-1073/19/3/800/pdf",
        "https://www.mdpi.com/1996-1073/19/3/800/pdf-vor",
    ],
    "21_Ebrahimi_2014.pdf": [
        "https://files.ifi.uzh.ch/hilty/t/Literature_by_RQs/RQ%20104/2014_Ebrahimi_Jones_Fleischer_A_Review_of_data_center_cooling_technology.pdf",
    ],
}
log = {"date": datetime.now(timezone.utc).isoformat(), "files": []}
src = Path(r"C:\Users\Lysda\Downloads\Telegram Desktop\Datacentra_teplo_vedecke_prace.pdf")
original_dir = ROOT / "sources" / "original"
original_dir.mkdir(exist_ok=True)
if src.exists() and src.read_bytes()[:4] == b"%PDF":
    out = original_dir / src.name
    if not out.exists():
        shutil.copy2(src, out)
    log["original_catalog"] = str(out)

for filename, urls in CATALOG.items():
    target = PAPERS / filename
    entry = {"filename": filename, "status": "MISSING", "tried": []}
    if target.exists() and target.stat().st_size > 4096 and target.open("rb").read(4) == b"%PDF":
        entry.update(status="ALREADY_PRESENT", size=target.stat().st_size)
    else:
        for url in urls:
            try:
                req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 (compatible; AcademicReferenceAudit/1.0)", "Accept":"application/pdf,*/*"})
                with urllib.request.urlopen(req, timeout=18) as resp:
                    data = resp.read(15_000_001)
                if not data.startswith(b"%PDF") or len(data) < 4096:
                    entry["tried"].append({"url":url, "error":"non-PDF response; rejected"})
                    continue
                if len(data) > 15_000_000:
                    entry["tried"].append({"url":url, "error":"file exceeded 15MB audit download cap"})
                    continue
                target.write_bytes(data)
                entry.update(status="DOWNLOADED", source_url=url, size=len(data))
                break
            except Exception as exc:
                entry["tried"].append({"url":url, "error":str(exc)[:250]})
    log["files"].append(entry)
    print(f'{entry["filename"]}: {entry["status"]}', flush=True)
with (ROOT/"audit"/"source_acquisition_v06.json").open("w", encoding="utf-8") as f:
    json.dump(log, f, ensure_ascii=False, indent=2)
print("REPORT:", ROOT/"audit"/"source_acquisition_v06.json", flush=True)
