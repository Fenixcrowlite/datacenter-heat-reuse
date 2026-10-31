"""Prepare an additive, primary-text HP boundary audit; preserve accepted v42."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, itertools, sys
import pymupdf

ROOT = Path(__file__).resolve().parents[1]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    out = ROOT / 'results' / ('hp_traceability_v43_' + stamp)
    out.mkdir()
    evidence = out / 'primary_evidence'
    evidence.mkdir()
    pdf = ROOT / 'sources/papers/20_Verzino_Varna_2026.pdf'
    doc = pymupdf.open(pdf)
    pages = [1, 6, 8, 9, 10, 23, 27]
    for page in pages:
        (evidence / f'page_{page:02d}.txt').write_text(doc[page-1].get_text(), encoding='utf-8')
    for page in [8, 10, 23, 27]:
        doc[page-1].get_pixmap(matrix=pymupdf.Matrix(1.7, 1.7)).save(evidence / f'page_{page:02d}.png')
    source = dict(source_id=20, doi='10.3390/en19030800', pdf_path=str(pdf.relative_to(ROOT)),
                  sha256=digest(pdf), pages=len(doc), relevant_equations=[4,5,6,7],
                  equation_page=8, vcc23_assumption_page=10, nomenclature_page=23,
                  upstream_references_page=27,
                  primary_text_class='LOCAL_PUBLISHER_PDF_RELEVANT_TEXT_VERIFIED_PENDING_VISUAL_REVIEW',
                  online_access={'url':'https://www.mdpi.com/1996-1073/19/3/800',
                                 'direct_open':'429', 'indexed_publisher_text':'AVAILABLE',
                                 'latest_pdf_identity':'NOT_REDOWNLOADED_OR_VERIFIED'},
                  upstream_61_62_64='NOT_VERIFIED', full_signoff=False)
    (out/'source_evidence.json').write_text(json.dumps(source,indent=2)+'\n',encoding='utf-8')
    vectors=[]
    # All sweep points are engineering fixtures, not article equipment points.
    for sc,tc,eta,pinch,qs,request in itertools.product([20,35,45],[65,80,95],[.45,.5,.55],[0,5,10],[.5,5],[1,100]):
        vectors.append([sc,tc,eta,pinch,qs,request])
    spec=dict(version='0.43', model_version='0.42', new_model=False,
              fixture_class='ENGINEERING_SYNTHETIC_NOT_MEASURED', vectors=vectors,
              source_power_unit='MW', temperature_input_unit='degC',
              pinch_policy='TL=sourceC-pinch+273.15; TH=sinkC+pinch+273.15; symmetric scenario only',
              capacity_MW=100, cop_max=1000, cop_min=1.000001,
              stateflow_case=dict(source_C=35,sink_C=75,pinch_K=5,eta_cooling=.5,
                                 source_MW=.5,demand_MW=.68,initial_energy_MWh=5))
    (out/'spec.json').write_text(json.dumps(spec,indent=2)+'\n',encoding='utf-8')
    files={}
    for manifest in ['audit/Stateflow_clock_manifest_v42_20261010T131054_029975Z.json',
                     'audit/Stateflow_clock_postclose_manifest_v42_20261010T131122_477101Z.json']:
        p=ROOT/manifest
        files[manifest]=dict(path=manifest,sha256=digest(p),bytes=p.stat().st_size)
        for item in json.loads(p.read_text(encoding='utf-8-sig'))['files']:
            files[item['path']]=item
    for name in ['sources/papers/20_Verzino_Varna_2026.pdf','audit/literature_traceability_v25.csv',
                 'STATUS_stateflow_v42.json','MASTER_STAGEBOARD_stateflow_v42.md',
                 'matlab/+dchr/+components/heat_pump_step_v40.m',
                 'matlab/simulink/DCHR_Dispatch_Stateflow_v42.slx']:
        p=ROOT/name
        files[name]=dict(path=name,sha256=digest(p),bytes=p.stat().st_size)
    (out/'preservation.json').write_text(json.dumps(list(files.values()),indent=2)+'\n',encoding='utf-8')
    (ROOT/'audit/hp_traceability_current_v43.txt').write_text(str(out.relative_to(ROOT))+'\n',encoding='utf-8')
    print('PREPARED='+str(out.relative_to(ROOT)))
    print('ENGINEERING_VECTORS='+str(len(vectors)))

if __name__=='__main__': main()
