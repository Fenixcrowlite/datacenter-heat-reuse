from pathlib import Path
import urllib.request,json
from datetime import datetime,timezone
base=Path(__file__).resolve().parents[1]/"sources/papers"
base.mkdir(parents=True,exist_ok=True)
works={
"08_Tofani_Stockholm_2022.pdf":"https://kth.diva-portal.org/smash/get/diva2%3A1723944/FULLTEXT01.pdf",
"09_Sintong_Stockholm_2023.pdf":"https://www.diva-portal.org/smash/get/diva2%3A1780867/FULLTEXT01.pdf",
}
report=[]
for fname,url in works.items():
    entry={"filename":fname,"url":url}
    target=base/fname
    try:
        if target.exists() and target.open("rb").read(4)==b"%PDF":entry["status"]="ALREADY_PRESENT"
        else:
            request=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0","Accept":"application/pdf,*/*"})
            with urllib.request.urlopen(request,timeout=25) as r:data=r.read(25_000_001)
            if len(data)>25_000_000 or len(data)<4000 or not data.startswith(b"%PDF"): raise ValueError("Not a PDF or exceeds 25MB")
            target.write_bytes(data);entry.update(status="DOWNLOADED",size=len(data))
    except Exception as e:entry.update(status="FAILED",error=str(e)[:240])
    print(fname,entry["status"],flush=True)
    report.append(entry)
(base.parent.parent/"audit/stockholm_theses_fetch_v06.json").write_text(json.dumps({"time":datetime.now(timezone.utc).isoformat(),"results":report},ensure_ascii=False,indent=2),encoding="utf-8")
