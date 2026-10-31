from pathlib import Path
import pymupdf
out=Path(__file__).resolve().parents[2]/"results"/"pool_v85_bridge_v03"
for lang,pg in (("SK",0),("RU",1)):
 pdf=pymupdf.open(str(out/("Most_v85_bazen_v03_"+lang+".pdf")))
 pdf[pg].get_pixmap(matrix=pymupdf.Matrix(1.4,1.4),alpha=False).save(str(out/("QA_preview_"+lang+"_p"+str(pg+1)+".png")))
 print("RENDERED",lang,pg+1)
