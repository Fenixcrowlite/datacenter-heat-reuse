from pathlib import Path
import zipfile,json,hashlib
root=Path(__file__).resolve().parent
archive=root.parent.parent/'ENGINEERING_RELEASE_20261023.zip'
if archive.exists():raise FileExistsError(str(archive))
files=[p for p in sorted(root.rglob('*')) if p.is_file() and
 '__pycache__' not in p.parts and p.suffix not in ('.pyc',)]
assert len(files)>=30
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=7) as z:
 for f in files:z.write(f,arcname='engineering_release_20261023/'+str(f.relative_to(root)).replace('\\','/'))
with zipfile.ZipFile(archive,'r') as z:
 assert z.testzip() is None
 names=z.namelist()
 assert any(x.endswith('.slx') for x in names)
 assert sum(x.lower().endswith('.pdf') for x in names)>=3
report={'zip_path':str(archive),'bytes':archive.stat().st_size,'members':len(names),
 'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'integrity_test':'PASSED'}
(root/'ARCHIVE_VERIFICATION_20261023.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('RELEASE_ARCHIVE_CREATED_VERIFIED',json.dumps(report,ensure_ascii=False))
