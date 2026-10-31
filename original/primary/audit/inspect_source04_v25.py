from pathlib import Path
import fitz
p=Path(__file__).resolve().parents[1]/"sources"/"papers"/"04_Hiltunen_Espoo_2020.pdf"
d=fitz.open(p)
print("PAGES",len(d))
for i,page in enumerate(d):
    t=page.get_text()
    words=("COP","coefficient of performance","heat pump","Table 1","thermal storage","electricity price")
    print("PDF_PAGE",i+1,"CHARS",len(t),"HITS",[(w,t.lower().count(w.lower())) for w in words if w.lower() in t.lower()])
    if 4<=i<=10:
        print("PAGE_TEXT_START",i+1)
        print(t[:14000])
        print("PAGE_TEXT_END",i+1)
