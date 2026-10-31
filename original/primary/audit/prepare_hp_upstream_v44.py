"""Workspace-only public-source acquisition and synthetic boundary fixtures."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, itertools, json, urllib.request, urllib.error

ROOT = Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    out = ROOT/'results'/('hp_upstream_v44_'+stamp); out.mkdir()
    prior = json.loads((ROOT/'audit/HP_traceability_manifest_v43_20261010T131912_453081Z.json').read_text())['files']
    names = ['STATUS_v43.json','MASTER_STAGEBOARD_v43.md','STATUS_stateflow_v42.json',
             'matlab/simulink/DCHR_Dispatch_Stateflow_v42.slx',
             'matlab/+dchr/+components/heat_pump_step_v40.m','sources/papers/20_Verzino_Varna_2026.pdf']
    sealed={x['path']:x for x in prior}
    for n in names:
        p=ROOT/n; sealed[n]=dict(path=n,bytes=p.stat().st_size,sha256=sha(p))
    (out/'preservation.json').write_text(json.dumps(list(sealed.values()),indent=2)+'\n')
    urls = [
        ('crossref','https://api.crossref.org/works/10.1016/j.tsep.2025.103513'),
        ('publisher','https://www.sciencedirect.com/science/article/pii/S2451904925003038'),
        ('repository','https://flore.unifi.it/handle/2158/1432822'),
        ('selector','https://www.danfoss.com/en/service-and-support/downloads/dcs/coolselector-2/'),
        ('manufacturer','https://www.danfoss.com/en/service-and-support/tech-insider/commercial-refrigeration-and-sensing-solutions/')]
    receipts=[]
    for key,url in urls:
        item=dict(id=key,url=url,timestamp_utc=datetime.now(timezone.utc).isoformat())
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'DCHR-research-audit/0.44'})
            with urllib.request.urlopen(req,timeout=18) as response:
                body=response.read(8000000)
                path=out/(key+('.json' if key=='crossref' else '.html'))
                path.write_bytes(body)
                item.update(status=response.status,final_url=response.url,bytes=len(body),
                            content_type=response.headers.get('Content-Type'),path=str(path.relative_to(ROOT)),sha256=sha(path))
        except urllib.error.HTTPError as exc:
            item.update(status=exc.code,error_type='HTTPError')
        except Exception as exc:
            item.update(status=None,error_type=type(exc).__name__,message=str(exc))
        receipts.append(item)
        print(json.dumps(item),flush=True)
    (out/'acquisition.json').write_text(json.dumps(receipts,indent=2)+'\n')
    vectors=list(itertools.product([5,20,35],[10,30,60],[.35,.5,.65],[1,1000],[0,.1,.5],[0,.5,1]))
    spec=dict(version='0.44',model_version='0.42',new_model=False,
              fixture_class='ENGINEERING_SYNTHETIC_NOT_EQUIPMENT_DATA',
              input_columns=['TL_C','lift_K','eta_cooling','QL_kW','aux_over_comp','aux_heat_recovered_fraction'],vectors=vectors)
    (out/'spec.json').write_text(json.dumps(spec,indent=2)+'\n')
    (ROOT/'audit/hp_upstream_current_v44.txt').write_text(str(out.relative_to(ROOT))+'\n')
    print('PREPARED='+str(out.relative_to(ROOT)),flush=True)
if __name__=='__main__': main()
