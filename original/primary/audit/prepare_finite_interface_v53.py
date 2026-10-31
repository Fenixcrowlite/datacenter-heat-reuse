"""Create immutable inputs and preservation baseline before local execution."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    folder=ROOT/'results'/f'finite_interface_v53_{stamp}';folder.mkdir()
    spec={'version':'0.53','model_version':'0.52','new_model':False,
        'boundary':dict(source_in_C=35.,source_glide_K=5.,evaporator_approach_K=5.,
            condenser_approach_K=5.,tank_max_C=70.,delivery_C=45.,charge_approach_K=2.,
            discharge_approach_K=3.,direct_approach_K=2.,hot_in_C=40.,
            source_capacity_MW_per_K=.8,hot_capacity_MW_per_K=.6,hp_capacity_MW=8.,
            cooling_factor=.5,aux_per_compressor=.1,aux_hot_fraction=0.),
        'policy':dict(dt_h=.25,ambient_C=20.,heat_capacity_MWh_per_K=.2,
            charge_limit_MW=3.,discharge_limit_MW=4.,eta_charge=.9,eta_discharge=.8,
            loss_rate_per_h=.05,boiler_limit_MW=2.,restart_C=60.,
            initial_energy_MWh=1.,min_on_h=.25,min_off_h=.25),
        'evidence_class':'SYNTHETIC_ENGINEERING_NOT_EQUIPMENT_CALIBRATION'}
    (folder/'spec.json').write_text(json.dumps(spec,indent=2)+'\n')
    old=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))
    old += list(ROOT.glob('STATUS*.json'))+list(ROOT.glob('MASTER_STAGEBOARD*.md'))
    old += [ROOT/'sources/papers/20_Verzino_Varna_2026.pdf']
    old=[p for p in old if 'v53' not in p.name]
    preserve=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),size=p.stat().st_size) for p in old]
    (folder/'preservation.json').write_text(json.dumps(preserve,indent=2)+'\n')
    evidence=folder/'primary_evidence';evidence.mkdir()
    source=ROOT/'results/hp_traceability_v43_20261010T131612_418934Z/primary_evidence'
    for name in ['page_08.txt','page_08.png','page_10.txt','page_10.png','page_27.txt','page_27.png']:
        (evidence/name).write_bytes((source/name).read_bytes())
    observations={
        'timestamp_utc':datetime.now(timezone.utc).isoformat(),
        'local_primary_pdf_sha256':sha(ROOT/'sources/papers/20_Verzino_Varna_2026.pdf'),
        'source20_primary_text_verified':'Preserved local p8 Eqs4-7 and saturation-temperature definition visually inspected; p10 and p27 locators retained.',
        'source20_model_relation':'Cooling-factor convention and explicit pinch/glide support boundary definitions, not this single-HP sensible-TES architecture or fixture values.',
        'web_observations':[
            {'url':'https://www.mdpi.com/1996-1073/19/3/800','class':'CURRENT_PRIMARY_ACCESS_FAILURE','observed':'Direct open returned HTTP429. Search-indexed text identifies article and source20 supplement link; current bytes/equations not verified.'},
            {'url':'https://www.mdpi.com/article/10.3390/en19030800/s1','class':'SUPPLEMENT_LINK_ACCESS_FAILURE','observed':'Not accessible via web tool; no supplement content acquired. This is source20 supplement, not verified upstream62 supplement.'},
            {'url':'https://www.sciencedirect.com/science/article/pii/S2451904925003038','class':'UPSTREAM_PRIMARY_ACCESS_FAILURE','observed':'Direct open returned HTTP403; no primary text/coefficients acquired.'},
            {'url':'https://flore.unifi.it/handle/2158/1432822','class':'REPOSITORY_METADATA_NOT_PRIMARY_TEXT','observed':'Matching Rocchetti/Socci 2025 TSEP61,103513 DOI; lines75-77 report no associated files. No equation or calibration inferred from abstract.'}],
        'upstream62_equations_verified':False,'equipment_calibration':'OPEN','full_primary_signoffs':0}
    (folder/'source_observations.json').write_text(json.dumps(observations,indent=2)+'\n')
    print(folder.relative_to(ROOT).as_posix())
if __name__=='__main__':main()
