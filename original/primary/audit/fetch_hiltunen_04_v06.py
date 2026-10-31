from pathlib import Path
from urllib.request import Request, urlopen
import json
root=Path(__file__).resolve().parents[1]
target=root/"sources/papers/04_Hiltunen_Espoo_2020.pdf"
url="https://aaltodoc.aalto.fi/server/api/core/bitstreams/8c0f6f75-a753-47f7-9036-8feafe318eec/content"
try:
    data=urlopen(Request(url,headers={"User-Agent":"Mozilla/5.0"}),timeout=20).read(12000000)
    if data[:4]!=b"%PDF" or len(data)<5000:
        raise ValueError("Not a PDF")
    if target.exists() and target.stat().st_size>5000:
        print("ALREADY_PRESENT",target,flush=True)
    else:
        target.write_bytes(data)
        print("DOWNLOADED",target,"bytes",len(data),flush=True)
except Exception as e:
    print("FAILED:",type(e).__name__,str(e)[:250],flush=True)
