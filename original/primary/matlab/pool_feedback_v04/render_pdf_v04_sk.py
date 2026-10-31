from pathlib import Path
import pymupdf
out=Path(__file__).resolve().parents[2]/"results"/"pool_feedback_v04"
for lang,pg in (("SK",1),("RU",2),("EN",0)):
 pdf=pymupdf.open(str(out/("Dispecer_Bazen_v04_"+lang+".pdf")))
 pdf[pg].get_pixmap(matrix=pymupdf.Matrix(1.3,1.3),alpha=False).save(str(out/("QA_preview_v04_"+lang+"_p"+str(pg+1)+".png")))
 print("RENDERED",lang,pg+1)
