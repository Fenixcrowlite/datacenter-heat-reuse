"""Replace previously truncated local Jurgens PDF using a complete streaming download."""
from pathlib import Path
from urllib.request import urlopen,Request
import os
p=Path(__file__).resolve().parents[1]/"sources"/"papers"/"17_Jurgens_Frankfurt_2024.pdf"
url="https://journals.aau.dk/index.php/sepm/article/download/8149/6839/29256"
temp=p.with_suffix(".part")
count=0
with urlopen(Request(url,headers={"User-Agent":"Mozilla/5.0"}),timeout=30) as response:
    with temp.open("wb") as dst:
        while True:
            chunk=response.read(1048576)
            if not chunk:break
            dst.write(chunk)
            count+=len(chunk)
            if count>150000000:raise RuntimeError("File unexpectedly large; refusing >150 MB")
head=temp.open("rb").read(5)
if head!=b"%PDF-":raise RuntimeError("Not a PDF; leave original untouched")
# PyMuPDF will detect most truncations and rendering errors.
import fitz
doc=fitz.open(str(temp))
n=len(doc)
if n<2:raise RuntimeError("Suspicious PDF page count")
text="\n".join(f"\n### PAGE {i+1}\n"+page.get_text() for i,page in enumerate(doc))
doc.close()
os.replace(temp,p)
p.with_suffix(".extracted.txt").write_text(text,encoding="utf-8")
print("VERIFIED_PDF",str(p),"bytes",count,"pages",n,"extracted_chars",len(text))
