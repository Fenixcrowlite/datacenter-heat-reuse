import argparse
import json
from pathlib import Path
import unittest
from .runner import ROOT,list_models,run_model


def main():
    parser=argparse.ArgumentParser(description='DataCenter Heat Reuse · Python laboratory')
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('list')
    run=sub.add_parser('run');run.add_argument('model_id');run.add_argument('--scenario');run.add_argument('--steps',type=int)
    run.add_argument('--config',type=Path);run.add_argument('--output',type=Path,required=True)
    serve=sub.add_parser('serve');serve.add_argument('--host',default='127.0.0.1');serve.add_argument('--port',type=int,default=8080);serve.add_argument('--runtime',type=Path)
    sub.add_parser('verify')
    args=parser.parse_args()
    if args.command=='list':print(json.dumps(list_models(),indent=2))
    elif args.command=='run':
        config=json.loads(args.config.read_text(encoding='utf-8')) if args.config else None
        result=run_model(args.model_id,config,scenario=args.scenario,steps=args.steps)
        if args.output.exists():parser.error('Output already exists; choose a new filename')
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,ensure_ascii=False,allow_nan=False),encoding='utf-8')
        print(json.dumps(result['metrics'],indent=2))
    elif args.command=='serve':
        from .server import make_server
        server=make_server(args.host,args.port,args.runtime)
        print('Heat Reuse laboratory: http://'+args.host+':'+str(server.server_port),flush=True)
        try:server.serve_forever()
        except KeyboardInterrupt:pass
        finally:server.server_close()
    else:
        suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
        result=unittest.TextTestRunner(verbosity=2).run(suite)
        raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__=='__main__':main()
