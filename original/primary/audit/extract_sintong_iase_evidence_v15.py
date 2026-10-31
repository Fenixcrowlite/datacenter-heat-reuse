"""Preserve page-level primary evidence without modifying the original PDF."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "sources/papers/09_Sintong_Stockholm_2023.pdf"
EXPECTED = "8149370d2df0c5899c844095f3890fea112c3d81eaff6671cb3cf0f3da9185f5"


def main():
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%S_%fZ")
    digest = hashlib.sha256(PDF.read_bytes()).hexdigest()
    assert digest == EXPECTED, "PDF differs from the prior acquisition checkpoint"
    records = []
    with pymupdf.open(PDF) as document:
        for index, role in [(22, "A2 IASE context"), (29, "Eq15-16 and operating criterion"),
                            (30, "Fig14 two-stream schematic"), (69, "Reference38")]:
            page = document[index]
            prefix = f"audit/Sintong_p{index+1}_IASE_v15_{stamp}"
            txt, png = ROOT / (prefix + ".txt"), ROOT / (prefix + ".png")
            with txt.open("x", encoding="utf-8") as stream:
                stream.write(page.get_text())
            assert not png.exists()
            page.get_pixmap(matrix=pymupdf.Matrix(2, 2)).save(png)
            records.append({"pdf_page_1based": index + 1, "pdf_index_0based": index,
                            "role": role, "text": txt.relative_to(ROOT).as_posix(),
                            "render": png.relative_to(ROOT).as_posix(),
                            "text_sha256": hashlib.sha256(txt.read_bytes()).hexdigest(),
                            "render_sha256": hashlib.sha256(png.read_bytes()).hexdigest()})
    data = {"timestamp_utc": now.isoformat(), "source": PDF.relative_to(ROOT).as_posix(),
            "source_sha256": digest, "pages": records,
            "category": "local_primary_page_extraction_and_render",
            "visual_review_required": True, "paper_replication": False}
    target = ROOT / f"audit/Sintong_IASE_primary_evidence_v15_{stamp}.json"
    with target.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2)
        stream.write("\n")
    log = ROOT / f"automation/logs/Sintong_IASE_extraction_v15_{stamp}.log"
    with log.open("x", encoding="utf-8") as stream:
        stream.write(f"UTC {now.isoformat()}\nOriginal PDF hash: PASS\n")
        stream.write("Pages23,30,31,70 text/render extraction: PASS\n")
        stream.write("Exploratory console extraction initially failed cp1251 encoding; rerun with -X utf8 succeeded. No original PDF changed.\n")
        stream.write(f"Evidence {target.relative_to(ROOT).as_posix()}\nVisual equation reading is a separate review step.\n")
    print(json.dumps({"evidence": target.relative_to(ROOT).as_posix(),
                      "log": log.relative_to(ROOT).as_posix(), "pages": records}))


if __name__ == "__main__":
    main()
