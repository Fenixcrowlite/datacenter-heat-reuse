"""Conservative OA discovery and acquisition. No repository paywall bypass.
Only PDF URLs marked as OA in OpenAlex; validate binary PDF and cap size.
"""
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request,urlopen
import json,time,subprocess,sys
from datetime import datetime,timezone
root=Path(__file__).resolve().parents[1]
data=json.loads((root/"audit/metadata_crossref_v06.json").read_text(encoding="utf-8"))
paperdir=root/"sources/papers";paperdir.mkdir(exist_ok=True)
audit=[]
def request_json(url,timeout=12):
    req=Request(url,headers={"User-Agent":"Scholarly-Heat-Reuse-Verification/0.6 (noncommercial; OpenAlex sources)","Accept":"application/json"})
    with urlopen(req,timeout=timeout) as f:return json.load(f)
for paper in data["papers"]:
    n=paper["nr"]
    row={"nr":n,"status":"NOT_ATTEMPTED","doi":"","url":""}
    cand=(paper.get("candidates") or [{}])[0]
    if paper.get("status")!="HIGH_TITLE_MATCH_REVIEW_AUTHOR_YEAR" or cand.get("similarity",0)<0.91:
        row["status"]="UNVERIFIED_DOI_SKIPPED";audit.append(row);continue
    doi=cand.get("doi");row["doi"]=doi
    present=[p for p in paperdir.glob(f"{n:02d}_*.pdf") if p.stat().st_size>4096]
    if present:
        row["status"]="ALREADY_PRESENT";row["filename"]=present[0].name;audit.append(row);continue
    try:
        work=request_json("https://api.openalex.org/works/https://doi.org/"+quote(doi,safe=""),timeout=12)
        candidate_urls=[]
        for loc in (work.get("best_oa_location"),work.get("primary_location"))+tuple(work.get("locations") or []):
            if isinstance(loc,dict) and loc.get("is_oa") and loc.get("pdf_url"):
                u=loc["pdf_url"]
                if u not in candidate_urls: candidate_urls.append(u)
        row["status"]="NO_OA_PDF_URL"
        for url in candidate_urls[:3]:
            row["url"]=url
            try:
                req=Request(url,headers={"User-Agent":"Mozilla/5.0", "Accept":"application/pdf,*/*"})
                with urlopen(req,timeout=14) as resp: buf=resp.read(18_000_001)
                if len(buf)>18_000_000 or len(buf)<4096 or not buf.startswith(b"%PDF"):
                    row["status"]="REJECTED_NON_PDF_OR_TOO_LARGE";continue
                fname=f"{n:02d}_OpenAlex_OA.pdf"
                dest=paperdir/fname;dest.write_bytes(buf)
                row.update(status="DOWNLOADED",filename=fname,size=len(buf));break
            except Exception as exc:
                row["status"]="FETCH_ERROR";row["error"]=str(exc)[:170]
    except Exception as exc:
        row["status"]="OPENALEX_ERROR";row["error"]=str(exc)[:170]
    audit.append(row)
    print(f'{n:02d}: {row["status"]}',flush=True)
    time.sleep(.4)
out=root/"audit/openalex_acquisition_v06.json"
out.write_text(json.dumps({"updated":datetime.now(timezone.utc).isoformat(),"evidence_not_validation":True,"results":audit},indent=2,ensure_ascii=False),encoding="utf-8")
print("REPORT",out,flush=True)
script=root/"audit/build_review_matrix_v06.py"
if script.exists():
    print("REBUILD REGISTER",flush=True)
    subprocess.run([sys.executable,str(script)],check=True)
