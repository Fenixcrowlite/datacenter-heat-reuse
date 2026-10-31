"""Create an immutable local evidence folder before the coupled-boundary audit."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    folder=ROOT/'results'/('coupled_interface_v54_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'))
    folder.mkdir()
    spec=json.loads((ROOT/'results/finite_interface_v53_20261011T062818_250661Z/spec.json').read_text())
    spec.update(version='0.54',new_model=False,scope='COUPLED_BOUNDARY_AND_UNSUPPORTED_SAVED_V52_AUDIT')
    spec['boundary'].pop('hot_in_C');spec['boundary'].pop('aux_hot_fraction')
    spec['boundary']['hot_capacity_MW_per_K']=4.
    spec['policy'].update(dt_h=.05,charge_limit_MW=8.,initial_energy_MWh=9.6)
    (folder/'spec.json').write_text(json.dumps(spec,indent=2)+'\n')
    files=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))
    files+=list(ROOT.glob('STATUS*.json'))+list(ROOT.glob('MASTER_STAGEBOARD*.md'))
    files+=[ROOT/'sources/papers/20_Verzino_Varna_2026.pdf']
    (folder/'preservation.json').write_text(json.dumps([dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),size=p.stat().st_size) for p in files if 'v54' not in p.name],indent=2)+'\n')
    src=ROOT/'results/finite_interface_v53_20261011T062818_250661Z/primary_evidence';dst=folder/'primary_evidence';dst.mkdir()
    for n in ['page_08.txt','page_08.png']:shutil.copy2(src/n,dst/n)
    observations=dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),source20_pdf_sha256=sha(ROOT/'sources/papers/20_Verzino_Varna_2026.pdf'),
        primary_verified='Local preserved page8 visually reinspected: Eqs4-7 compressor balance and saturation Kelvin EER convention. No fixture values adopted.',
        source20_current_access='https://www.mdpi.com/1996-1073/19/3/800 returned HTTP429 via web tool this run.',
        upstream_metadata='https://flore.unifi.it/handle/2158/1432822 opened; matching DOI103513 metadata and no associated files. No primary equations verified.',
        coupled_topology_evidence='ENGINEERING_ASSUMPTION: well-mixed tank-return condenser circuit, variable flow; not source20 topology/calibration.',
        equipment_calibration='OPEN',full_primary_signoffs=0)
    (folder/'source_observations.json').write_text(json.dumps(observations,indent=2)+'\n')
    snapshot=[]
    for rel in ['matlab/+dchr/+components/coupled_temperature_boundary_v54.m','matlab/+dchr/+components/source_affine_charge_step_v54.m',
                'matlab/run_coupled_interface_v54.m','audit/verify_coupled_interface_v54.py','audit/Coupled_temperature_derivation_v54.md',
                'matlab/simulink/DCHR_Dispatch_Stateflow_v52.slx','matlab/simulink/dchr_segment_plan_v52.m','matlab/simulink/dchr_stateflow_hp_v52.m',
                'matlab/simulink/stateflow_contract_gate_v52.m','matlab/simulink/build_dispatch_stateflow_v52.m']:
        p=ROOT/rel;out=folder/'source_snapshot'/rel;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,out)
        snapshot.append(dict(path=rel,sha256=sha(p)))
    (folder/'source_hashes.json').write_text(json.dumps(snapshot,indent=2)+'\n')
    print(folder.relative_to(ROOT).as_posix())
if __name__=='__main__':main()
