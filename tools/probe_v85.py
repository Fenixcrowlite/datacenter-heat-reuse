"""Development probe; source path is provided explicitly, no author path."""
import argparse
import json
from pathlib import Path
import time
import traceback
from heat_reuse.matlab_subset import compile_functions,M


def module(model):
    modules=[];public={}
    for source in model['functions']:
        functions=compile_functions(source['source']);modules.append(functions)
        if source['names']:public[source['names'][0]]=functions[source['names'][0]]
    for functions in modules:
        for name,function in public.items():functions.setdefault(name,function)
    return public


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('report',type=Path);args=parser.parse_args()
    model=json.loads(next(Path('models/extracted').glob('dchr-electrical-dispatch-stateflow-v85-*.json')).read_text(encoding='utf-8'))
    functions=module(model);report=json.loads(args.report.read_text(encoding='utf-8-sig'))
    case=report['runs'][0];start=time.monotonic()
    try:
        y,certificate=functions['electrical_dispatch_v85'](M(case['input'],12,1),M(case['raw_policy'],27,1),M([0.]*1380,1380,1),M([0.]*27,27,1))
        print('v85 zero_demand output',y.flat()[:14]);print('maxdifference',max(abs(a-b) for a,b in zip(y.flat(),case['trace'])))
    except Exception:traceback.print_exc(limit=12)
    print('seconds',time.monotonic()-start,flush=True)
