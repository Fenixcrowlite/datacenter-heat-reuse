from pathlib import Path
import pymupdf
O=Path(__file__).resolve().parents[2]/"results"/"pool_safety_v05"
figs=[O/"interlock_timeline_v05_SK.png",O/"teplota_poruchy_v05_SK.png"]
labels={
 "SK":["Čas blokovania v siedmich scenároch","Vývoj teploty vody"],
 "EN":["Fault latch timeline","Pool-water temperature traces"],
 "RU":["Временные интервалы блокировки","Температура воды в модели"]}
for lang in ("SK","EN","RU"):
 old=O/f"Bezpecnost_bazena_v05_{lang}.pdf"
 doc=pymupdf.open(str(old))
 # Cover the failed image placeholders on their original pages.
 for pg in doc:
  for key in labels[lang]:
   for r in pg.search_for(key):
    box=pymupdf.Rect(max(0,r.x0-18),max(0,r.y0-4),min(pg.rect.width,r.x1+6),min(pg.rect.height,r.y1+5))
    pg.add_redact_annot(box,fill=(1,1,1))
  if list(pg.annots() or []):
   pg.apply_redactions(images=2,graphics=0,text=0)
 page=doc.new_page(width=595,height=842)
 titles={"SK":"Simulovane havarijne stavy bazena",
         "EN":"Executed synthetic pool fault scenarios",
         "RU":"Результаты моделирования аварий бассейна"}
 page.insert_text((43,43),titles[lang],fontsize=17,fontname="helv",color=(.13,.2,.3))
 page.insert_text((43,65),"Stateflow / Simulink v05 | 7 x 168 h | dt = 900 s | SYNTHETIC",fontsize=10)
 for f,y in zip(figs,(92,402)):
  page.insert_image(pymupdf.Rect(43,y,552,y+255),filename=str(f),keep_proportion=True)
 page.insert_text((43,716),"Two graphics originate from the actual exported v05 Simulink CSV.",fontsize=9)
 page.insert_text((43,737),"The safety gate is NOT a certified physical sensor or plant protection system.",fontsize=9)
 temp=O/f"_revised_{lang}.pdf"
 doc.save(str(temp),garbage=4,deflate=True)
 doc.close()
 check=pymupdf.open(str(temp))
 assert len(check)>=3
 assert len(check[-1].get_images(full=True))>=2,(lang,'not embedded')
 body="\n".join(p.get_text() for p in check)
 assert "10.393" in body or "10,393" in body
 check.close()
 originalArchive=O/f"_replaced_draft_{lang}.pdf"
 if originalArchive.exists():raise RuntimeError("Existing backup: "+str(originalArchive))
 old.rename(originalArchive)
 temp.rename(old)
 print("PDF_REPAIRED_GRAPHICS",lang,"pages",len(pymupdf.open(str(old))),"size",old.stat().st_size)
