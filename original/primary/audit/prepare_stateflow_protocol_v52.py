"""Additive canonical endpoint protocol. v51 remains an unaccepted defect artifact."""
from pathlib import Path
from datetime import datetime, timezone
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'matlab/simulink'
def put(p,s):
    assert not p.exists(),p
    p.write_text(s)
def main():
    for p in list(HERE.glob('*v51.m'))+list((ROOT/'matlab').glob('*v51.m')):
        if p.name.startswith(('inspect_','review_')):continue
        s=p.read_text().replace('v51','v52').replace('V51','V52').replace('0.51','0.52')
        if p.name=='build_dispatch_stateflow_v51.m':
            s=s.replace('zeros(22,64)','zeros(23,64)').replace("'[22 1]'","'[23 1]'")
        if p.name=='dchr_segment_plan_v51.m':
            s=s.replace('plan=zeros(22,64)','plan=zeros(23,64)')
            s=s.replace('plan(:,count)=[span;', 'plan(1:22,count)=[span;')
            s=s.replace('for k=count+1:64', '    plan(23,count)=E;\nend_marker_unused\nfor k=count+1:64')
            # Stamp after remainder handling, inside the while loop.
            s=s.replace('end\n    plan(23,count)=E;\nend_marker_unused','    plan(23,count)=E;\nend')
            s=s.replace('bound;bound];','bound;bound;E];')
        if p.name=='stateflow_allocate_v51.m':
            needle='[endpoint,standing]=stateflow_tes_endpoint_v52(A,qc,qd,cfg,span,seg(13));'
            s=s.replace(needle,needle+"\nroundoff=64*eps(max(1,cfg(2)));\nassert(isfinite(seg(23)) && seg(23)>=0 && seg(23)<=cfg(2) && abs(endpoint-seg(23))<=roundoff,'Canonical endpoint disagrees with physical integration.');\nendpoint=seg(23); % explicit state protocol across host/compiled arithmetic\n")
        if p.name=='stateflow_contract_gate_v51.m':
            s=s.replace("assert(span>=0 && span==s(1)","assert(z(5)==s(23),'Canonical endpoint protocol mismatch.');\n    assert(span>=0 && span==s(1)")
        if p.name in ('run_stateflow_padding_v51.m','export_padding_identity_v51.m'):
            s=s.replace('1408','1472').replace('22,64','23,64')
            s=s.replace('[42 51]','[42 52]')
            s=s.replace('versionNumber==42','versionNumber==42')
            # Numeric version literals used by focused tests.
            s=s.replace('configure(mdl,c,51)','configure(mdl,c,52)').replace('inspect(result,c,51)','inspect(result,c,52)')
        if p.name=='run_annual_sensitivity_v51.m':
            s=s.replace("writetable(struct2table(matrix),fullfile(folder,'sensitivity_matrix.csv'));",
                        "if ~isempty(matrix),writetable(struct2table(matrix),fullfile(folder,'sensitivity_matrix.csv'));end")
        put(p.with_name(p.name.replace('v51','v52')),s)
    put(ROOT/'audit/run_stateflow_protocol_v52.ps1',(ROOT/'audit/run_stateflow_padding_v51.ps1').read_text().replace('v51','v52').replace('V51','V52'))
    old=ROOT/'results/stateflow_padding_v51_20261010T230758_239448Z'
    spec=json.loads((old/'spec.json').read_text());spec.update(version='0.52',model_version='0.52',new_model=True,v51_failed_evidence=old.relative_to(ROOT).as_posix())
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');folder=ROOT/'results'/('stateflow_protocol_v52_'+stamp);folder.mkdir()
    (folder/'spec.json').write_text(json.dumps(spec,indent=2)+'\n')
    paths={ROOT/x['path'] for x in json.loads((old/'preservation.json').read_text())}
    paths.update(p for p in old.rglob('*') if p.is_file() and 'local_build' not in p.parts)
    paths.update(HERE.glob('*v51*'));paths.update((ROOT/'matlab').glob('*v51*'));paths.update((ROOT/'audit').glob('*v51*'))
    entries=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(paths) if p.is_file()]
    (folder/'preservation.json').write_text(json.dumps(entries,indent=2)+'\n')
    print(folder.relative_to(ROOT).as_posix())
if __name__=='__main__':main()
