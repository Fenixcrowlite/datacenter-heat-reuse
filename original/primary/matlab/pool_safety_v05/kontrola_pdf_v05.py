from pathlib import Path
import pymupdf
O=Path(__file__).resolve().parents[2]/"results"/"pool_safety_v05"
for lang in ("SK","EN","RU"):
 path=O/f"Bezpecnost_bazena_v05_{lang}.pdf"
 pdf=pymupdf.open(str(path))
 assert 2<=len(pdf)<=10,(lang,len(pdf))
 body="\n".join(x.get_text() for x in pdf)
 assert "32928" in body.replace(" ","").replace(",",""),(lang,"QA number missing")
 assert "10,393" in body or "10.393" in body,(lang,"table missing")
 if lang=="RU":
  assert sum(1 for c in body if "\u0400"<=c<="\u04ff")>=250,"Russian text not embedded"
 if lang=="SK":
  assert "bezpeč" in body.lower(),"Slovak diacritics missing"
 for i,page in enumerate(pdf):
  for b in page.get_text("blocks"):
   if len(b)>4:
    assert b[0]>=-2 and b[1]>=-2 and b[2]<=page.rect.width+2 and b[3]<=page.rect.height+2,(lang,i,"clipped block",b[:4])
 images=sum(len(page.get_images(full=True)) for page in pdf)
 assert images>=1,(lang,"graphs not embedded")
 pdf[-1].get_pixmap(matrix=pymupdf.Matrix(1.1,1.1),alpha=False).save(str(O/f"PDF_QA_PREVIEW_{lang}.png"))
 print("PDF_VALIDATED",lang,"pages",len(pdf),"chars",len(body),"images",images,"size",path.stat().st_size)
