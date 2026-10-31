"""Metadata discovery only. Suggestions below threshold are NOT verified DOIs.
Use for source triage, then inspect publisher/author original for acceptance.
"""
from pathlib import Path
import json, re, csv, urllib.request, urllib.parse, time, difflib, unicodedata
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1]
catalog=(ROOT/"sources/source_catalog.md").read_text(encoding="utf-8")
regex=re.compile(r"^(\d+)\.\s+(.+?)\s+—\s+\*(.+?)\*",re.M)
records=[]
for nr,author,title in regex.findall(catalog):
    if int(nr)>24: continue
    records.append({"nr":int(nr),"author_year":author,"title":title.rstrip(" .")})
def canonical(x):
    x=unicodedata.normalize("NFKD",x).casefold()
    x="".join(c for c in x if c.isalnum() or c.isspace())
    return " ".join(x.split())
def similarity(a,b):
    return difflib.SequenceMatcher(None,canonical(a),canonical(b)).ratio()
out=[]
for record in records:
    q=urllib.parse.urlencode({"query.title":record["title"],"rows":"3"})
    url="https://api.crossref.org/works?"+q
    r=dict(record,status="NETWORK_ERROR",candidates=[])
    try:
        request=urllib.request.Request(url,headers={"User-Agent":"DataCenter-Heat-Academic-Review/0.6 (noncommercial scholarly metadata audit)","Accept":"application/json"})
        with urllib.request.urlopen(request,timeout=18) as response:
            data=json.load(response)
        for item in data.get("message",{}).get("items",[]):
            title=(item.get("title") or [""])[0]
            score=round(similarity(record["title"],title),4)
            year=None
            dateparts=(item.get("published") or {}).get("date-parts") or (item.get("issued") or {}).get("date-parts")
            if dateparts: year=dateparts[0][0]
            r["candidates"].append({"title":title,"doi":item.get("DOI"),"year":year,"similarity":score,"publisher":item.get("publisher")})
        r["candidates"].sort(key=lambda v:v["similarity"],reverse=True)
        best=r["candidates"][0] if r["candidates"] else None
        r["status"]=("HIGH_TITLE_MATCH_REVIEW_AUTHOR_YEAR" if best and best["similarity"]>=.91 else "AMBIGUOUS_REVIEW_REQUIRED")
    except Exception as exc:
        r["error"]=repr(exc)[:230]
    out.append(r)
    print(f'{r["nr"]:02d} {r["status"]} {r["candidates"][0]["similarity"] if r["candidates"] else "n/a"}',flush=True)
    time.sleep(.35)
json_path=ROOT/"audit/metadata_crossref_v06.json"
json_path.write_text(json.dumps({"generated":datetime.now(timezone.utc).isoformat(),"qualification":"Crossref candidates must still be manually verified; reports/policy sources 25–31 not included.","papers":out},ensure_ascii=False,indent=2),encoding="utf-8")
csv_path=ROOT/"audit/metadata_crossref_v06.csv"
with csv_path.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f);w.writerow(["nr","title","status","candidate_doi","candidate_title","match_score","candidate_year"])
    for r in out:
        b=r["candidates"][0] if r["candidates"] else {}
        w.writerow([r["nr"],r["title"],r["status"],b.get("doi"),b.get("title"),b.get("similarity"),b.get("year")])
print("SUMMARY",json.dumps({"total":len(out),"high_title_match":sum(r["status"]=="HIGH_TITLE_MATCH_REVIEW_AUTHOR_YEAR" for r in out),"ambiguous":sum(r["status"]=="AMBIGUOUS_REVIEW_REQUIRED" for r in out),"network_error":sum(r["status"]=="NETWORK_ERROR" for r in out)}),flush=True)
