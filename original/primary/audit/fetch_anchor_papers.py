"""Fetch full-text originals for private scientific audit; do not republish."""
from pathlib import Path
import urllib.request, urllib.error
root=Path(__file__).resolve().parents[1]/"sources"/"papers"
root.mkdir(parents=True,exist_ok=True)
sources={
"17_Jurgens_Frankfurt_2024.pdf":"https://journals.aau.dk/index.php/sepm/article/download/8149/6839/29256",
"01_Wahlroos_Espoo_2017.pdf":"https://aaltodoc.aalto.fi/server/api/core/bitstreams/bc9e99fc-64e6-4978-bf32-1de99acbfae1/content",
"20_Verzino_Varna_2026.pdf":"https://www.mdpi.com/1996-1073/19/3/800/pdf"
}
for name,url in sources.items():
    file=root/name
    if file.exists() and file.stat().st_size>10240:
        print("EXISTS",name,file.stat().st_size,flush=True);continue
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (academic personal research)","Accept":"application/pdf,*/*"})
        with urllib.request.urlopen(req,timeout=20) as r:
            data=r.read(30000000)
        if not data.startswith(b"%PDF"):raise ValueError("Not a PDF; first bytes: "+repr(data[:40]))
        file.write_bytes(data)
        print("FETCHED",name,len(data),flush=True)
    except Exception as ex:
        print("FAILED",name,type(ex).__name__,str(ex)[:300],flush=True)
try:
    import fitz
    for name in sources:
        p=root/name
        if not p.exists():continue
        doc=fitz.open(str(p))
        out=p.with_suffix(".extracted.txt")
        out.write_text("\n".join(f"\n### PAGE {i+1}\n"+pg.get_text() for i,pg in enumerate(doc)),encoding="utf-8")
        print("EXTRACTED",name,len(doc),out,flush=True)
except Exception as ex:print("EXTRACTION_ERROR",type(ex).__name__,str(ex)[:300],flush=True)
