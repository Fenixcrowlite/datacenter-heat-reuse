"""Preserve pre-formatting records and seal corrected GFM table presentation."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil, sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(folder):
    manifest=json.loads((folder/'release_manifest_v82.json').read_text())
    changed=['audit/close_hp_approach_v82.py','audit/HP_approach_results_v82.md',
             'MASTER_STAGEBOARD_v82.md','MASTER_STAGEBOARD_stateflow_v82.md']
    older=folder/'pre_table_formatting';older.mkdir()
    for rel in changed:
        p=ROOT/rel;old=next(e for e in manifest if e['path']==rel)
        if rel.endswith('.md'):
            assert sha(p)==old['sha256'];dst=older/Path(rel).name;shutil.copy2(p,dst)
            original=p.read_text();new=original.replace('|\n\n|','|\n|')
            assert new!=original;p.write_text(new,encoding='utf-8')
        else:
            current=p.read_text();previous=current.replace(".replace('|\\n\\n|','|\\n|')",'')
            dst=older/Path(rel).name;dst.write_bytes(previous.replace('\n','\r\n').encode())
            # apply_patch-created files use LF; preserve exact pre-formatting script.
            if sha(dst)!=old['sha256']:dst.write_bytes(previous.encode())
            assert sha(dst)==old['sha256']
    for e in manifest:
        if e['path'] not in changed:assert sha(ROOT/e['path'])==e['sha256'],e['path']
    for e in json.loads((folder/'preservation.json').read_text()):assert sha(ROOT/e['path'])==e['sha256']
    for e in json.loads((folder/'ledger_prefixes.json').read_text()):
        assert hashlib.sha256((ROOT/e['path']).read_bytes()[:e['size']]).hexdigest()==e['sha256']
    note='Post-close formatting check: corrected blank lines inside the v82 Markdown tables. Numeric results, status, MATLAB artifacts and independent QA are unchanged; pre-formatting report/script bytes and original seals remain in the evidence directory.'
    with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as out:out.write('\n\n'+note+'\n')
    files=[ROOT/e['path'] for e in manifest]+[p for p in older.iterdir()]+[ROOT/'audit/finalize_hp_approach_v82.py',folder/'release_manifest_v82.json',folder/'release_QA_v82.json']
    with (folder/'final_release_v82.json').open('x',encoding='utf-8') as out:
        json.dump(dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),passed=True,
            formatting_only=True,checks='All original seals preserved; only declared Markdown/script formatting change; production and ledger prefixes unchanged',
            files=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in files]),out,indent=2)
    print('V82_FINAL_RELEASE_PASS; numeric/production artifacts unchanged; GFM table verified')
if __name__=='__main__':main((ROOT/sys.argv[1]).resolve())
