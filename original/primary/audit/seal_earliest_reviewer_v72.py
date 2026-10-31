"""Seal later diagnostic/reviewer sources before the authoritative QA run."""
from pathlib import Path
import hashlib, json, shutil, sys
ROOT=Path(__file__).resolve().parents[1]
def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    target=folder/'reviewer_sources.json';assert not target.exists()
    paths=[Path(__file__),ROOT/'audit/verify_earliest_admissibility_v72.py',ROOT/'matlab/run_earliest_rejection_probes_v72.m',ROOT/'audit/run_earliest_rejection_probes_v72.ps1']
    paths+=list(folder.glob('diagnostic_earliest_kernel_v72*.m'))
    records=[]
    for p in paths:
        rel=p.relative_to(ROOT).as_posix();dst=folder/'reviewer_source_snapshot'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
        records.append(dict(path=rel,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    target.write_text(json.dumps(records,indent=2)+'\n');print(f'REVIEWER_SOURCES_V72 SEALED={len(records)}')
if __name__=='__main__':main()
