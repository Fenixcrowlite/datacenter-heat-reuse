import pymupdf
from pathlib import Path
o=Path(__file__).resolve().parents[2]/"results"/"pool_safety_v05"
q=pymupdf.open(str(o/"_ru_font_fixed.pdf"))
q[-1].get_pixmap(matrix=pymupdf.Matrix(1.1,1.1),alpha=False).save(str(o/"RU_HEADER_NEW_PREVIEW.png"))
print("preview_ready")
