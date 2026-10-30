"""Read-only extraction of packaged Simulink/Stateflow model structure.

Structural extraction is deliberately not reported as numerical migration.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile


def props(element):
    return {p.attrib.get('Name',''):p.text or '' for p in element.findall('P')}


def extract_model(path):
    path=Path(path)
    raw=path.read_bytes()
    model={'name':path.stem,'id':re.sub(r'[^a-z0-9]+','-',path.stem.lower()).strip('-'),
           'sha256':hashlib.sha256(raw).hexdigest(),'blocks':[],'lines':[],'states':[],
           'transitions':[],'functions':[],'data':[],'execution_status':'not_ported'}
    with zipfile.ZipFile(path) as archive:
        for name in sorted(archive.namelist()):
            if not name.startswith('simulink/') or not name.endswith('.xml'):
                continue
            info=archive.getinfo(name)
            if info.file_size>25*1024*1024:raise ValueError('Oversized model XML')
            root=ET.fromstring(archive.read(name))
            if 'stateflow/' in name:
                for node in root.iter():
                    data=props(node)
                    if node.tag=='state':
                        model['states'].append({'id':node.attrib.get('id'),
                                                'label':data.get('labelString',data.get('name','')),
                                                'position':data.get('position'),'xml':name})
                    elif node.tag=='transition':
                        model['transitions'].append({'id':node.attrib.get('id'),'label':data.get('labelString',''),
                                                     'properties':data,'source':props(node.find('src')) if node.find('src') is not None else {},
                                                     'destination':props(node.find('dst')) if node.find('dst') is not None else {},'xml':name})
                    elif node.tag=='data':
                        model['data'].append({'id':node.attrib.get('id'),'name':node.attrib.get('name',data.get('name')),'properties':data,'xml':name})
                    if node.tag=='P' and node.attrib.get('Name')=='script' and (node.text or '').strip():
                        source=node.text
                        names=re.findall(r'(?m)^function\s+(?:(?:\[[^\]]*\]|\w+)\s*=\s*)?(\w+)\s*\(',source)
                        model['functions'].append({'names':names,'source':source,'xml':name,
                                                   'sha256':hashlib.sha256(source.encode()).hexdigest()})
            else:
                for node in root.iter('Block'):
                    model['blocks'].append({'sid':node.attrib.get('SID'),'name':node.attrib.get('Name'),
                                             'type':node.attrib.get('BlockType'),'properties':props(node),'xml':name})
                for line in root.iter('Line'):
                    data=props(line)
                    destinations=[p.text for p in line.iter('P') if p.attrib.get('Name')=='Dst']
                    if data.get('Src'):
                        model['lines'].append({'source':data['Src'],'destinations':destinations,'xml':name})
    return model


def build_catalog(root,output):
    root,output=Path(root),Path(output)
    output.mkdir(parents=True,exist_ok=True)
    models={};copies={}
    for path in sorted(root.rglob('*.slx')):
        model=extract_model(path)
        sha=model['sha256']
        copies.setdefault(sha,[]).append(path.relative_to(root).as_posix())
        if sha not in models:
            model['file']='extracted/'+model['id']+'-'+sha[:12]+'.json'
            models[sha]=model
    (output/'extracted').mkdir(exist_ok=True)
    entries=[]
    for sha,model in models.items():
        model['copies']=copies[sha]
        if model['name']=='DC_Bazen_Uzavreta_Regulacia_v04_SK':
            model['execution_status']='verified_python_port';model['python_model_id']='pool-v04'
        (output/model['file']).write_text(json.dumps(model,ensure_ascii=False,indent=2),encoding='utf-8')
        entries.append({key:value for key,value in model.items() if key not in {'blocks','lines','states','transitions','functions','data'}}|
                       {'block_count':len(model['blocks']),'state_count':len(model['states']),'function_count':len(model['functions'])})
    report={'format':'dchr-model-catalog-v1','source':'read-only SLX structural extraction','models':entries,
            'distinct_binaries':len(entries),'files':sum(len(v) for v in copies.values())}
    (output/'catalog.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('root',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();result=build_catalog(args.root,args.output)
    print(json.dumps({'distinct_binaries':result['distinct_binaries'],'files':result['files']}))
