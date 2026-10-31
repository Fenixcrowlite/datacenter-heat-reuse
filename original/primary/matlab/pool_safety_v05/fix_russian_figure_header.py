from pathlib import Path
import pymupdf
out=Path(__file__).resolve().parents[2]/"results"/"pool_safety_v05"
path=out/"Bezpecnost_bazena_v05_RU.pdf"
d=pymupdf.open(str(path))
pg=d[-1]
rect=pymupdf.Rect(39,22,565,52)
pg.add_redact_annot(rect,fill=(1,1,1))
pg.apply_redactions(images=0,graphics=0,text=0)
pg.insert_font(fontname="RussianArial",fontfile=r"C:\Windows\Fonts\arial.ttf")
pg.insert_text((43,43),"Результаты моделирования отказов бассейна",fontsize=17,fontname="RussianArial",color=(.13,.2,.3))
temp=out/"_ru_font_fixed.pdf"
d.save(str(temp),garbage=4,deflate=True);d.close()
q=pymupdf.open(str(temp))
assert "Результаты моделирования отказов бассейна" in q[-1].get_text()
assert len(q[-1].get_images(full=True))>=2
q.close()
old=out/"_ru_header_previous.pdf"
if old.exists():raise RuntimeError("Not replacing existing backup")
path.rename(old)
temp.rename(path)
print("RU_FONT_HEADER_FIXED",path.stat().st_size)
