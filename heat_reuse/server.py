"""Local source browser and simulation HTTP interface (stdlib only)."""
from contextlib import closing
from datetime import datetime,timezone
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import csv
import io
import json
import mimetypes
import os
from pathlib import Path
import re
import sqlite3
import threading
from urllib.parse import unquote,urlsplit
import uuid

from .runner import ROOT,list_models,run_model


class Store:
    def __init__(self,path):
        self.path=Path(path);self.path.mkdir(parents=True,exist_ok=True)
        self.lock=threading.RLock()
        with closing(sqlite3.connect(self.path/'history.sqlite')) as db:
            db.execute('CREATE TABLE IF NOT EXISTS results(id TEXT PRIMARY KEY, created TEXT, model TEXT, scenario TEXT, metrics TEXT)');db.commit()

    def save(self,result):
        result=dict(result,id=uuid.uuid4().hex,created_utc=datetime.now(timezone.utc).isoformat())
        raw=json.dumps(result,ensure_ascii=False,allow_nan=False,separators=(',',':'))
        with self.lock:
            path=self.path/(result['id']+'.json');temporary=path.with_suffix('.partial')
            temporary.write_text(raw,encoding='utf-8');temporary.replace(path)
            with closing(sqlite3.connect(self.path/'history.sqlite')) as db:
                db.execute('INSERT INTO results VALUES(?,?,?,?,?)',(result['id'],result['created_utc'],result['model_id'],result['scenario'],json.dumps(result['metrics'],allow_nan=False)))
                db.commit()
        return result

    def load(self,identifier):
        if not re.fullmatch(r'[0-9a-f]{32}',identifier):raise ValueError('Invalid result ID')
        return json.loads((self.path/(identifier+'.json')).read_text(encoding='utf-8'))

    def list(self):
        with self.lock,closing(sqlite3.connect(self.path/'history.sqlite')) as db:
            rows=db.execute('SELECT id,created,model,scenario,metrics FROM results ORDER BY created DESC LIMIT 100').fetchall()
        return [dict(id=r[0],created_utc=r[1],model_id=r[2],scenario=r[3],metrics=json.loads(r[4])) for r in rows]


def document_index():
    roots=[ROOT/'docs',ROOT/'original/primary/docs',ROOT/'original/primary/calibration',
           ROOT/'original/primary/presentations',ROOT/'original/download_presentations']
    entries=[]
    for root in roots:
        if not root.exists():continue
        for path in root.rglob('*'):
            if path.is_file() and path.suffix.lower() in {'.md','.pdf','.pptx'}:
                relative=path.relative_to(ROOT).as_posix()
                entries.append({'path':relative,'name':path.name,'bytes':path.stat().st_size,
                                'language':'SK' if re.search(r'(^|[/_.-])SK([/_.-]|$)',relative,re.I) else 'EN' if re.search(r'(^|[/_.-])EN([/_.-]|$)',relative,re.I) else 'other'})
    return sorted(entries,key=lambda x:(x['language'],x['path']))


def make_server(host='127.0.0.1',port=8080,runtime=None):
    store=Store(runtime or os.environ.get('HEAT_REUSE_RUNTIME',ROOT/'runtime'))
    calculation_lock=threading.Lock()
    # Host-header validation prevents DNS rebinding to a loopback laboratory.
    # Binding to 0.0.0.0 for Docker does NOT implicitly authorize LAN names.
    allowed_hosts={'localhost','127.0.0.1','::1'}
    if host not in {'0.0.0.0','::',''}:
        allowed_hosts.add(host.lower())
    allowed_hosts.update(part.strip().lower() for part in
        os.environ.get('HEAT_REUSE_ALLOWED_HOSTS','').split(',') if part.strip())

    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass

        def trusted_host(self):
            values=self.headers.get_all('Host',[])
            if len(values)!=1:
                return False
            raw=values[0].strip()
            if not raw or any(c in raw for c in ('/','?','#','@','\\')):
                return False
            try:
                parsed=urlsplit('http://'+raw)
                name=parsed.hostname
                port_number=parsed.port
            except ValueError:
                return False
            return (name in allowed_hosts
                and (port_number is None or port_number==self.server.server_port))

        def send(self,body,status=200,content_type='application/json; charset=utf-8',filename=None):
            if isinstance(body,(dict,list)):body=json.dumps(body,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()
            elif isinstance(body,str):body=body.encode()
            self.send_response(status);self.send_header('Content-Type',content_type);self.send_header('Content-Length',str(len(body)))
            self.send_header('X-Content-Type-Options','nosniff');self.send_header('Cache-Control','no-store')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'")
            if filename:self.send_header('Content-Disposition','attachment; filename="'+filename+'"')
            self.end_headers();self.wfile.write(body)

        def do_GET(self):
            if not self.trusted_host():
                return self.send({'error':'Untrusted Host'},403)
            path=unquote(urlsplit(self.path).path)
            try:
                if path=='/api/health':return self.send({'status':'ok','mode':'SIMULATION','matlab_required':False})
                if path=='/api/models':return self.send({'models':list_models()})
                if path=='/api/results':return self.send(store.list())
                if path.startswith('/api/results/'):
                    identifier=path.split('/')[-1];csv_mode=identifier.endswith('.csv')
                    result=store.load(identifier[:-4] if csv_mode else identifier)
                    if not csv_mode:return self.send(result)
                    output=io.StringIO(newline='');writer=csv.DictWriter(output,fieldnames=list(result['rows'][0]));writer.writeheader();writer.writerows(result['rows'])
                    return self.send(output.getvalue(),content_type='text/csv; charset=utf-8',filename=result['id']+'.csv')
                if path=='/api/catalog':
                    file=ROOT/'models/catalog.json'
                    return self.send(json.loads(file.read_text(encoding='utf-8')) if file.exists() else {'models':[]})
                if path.startswith('/api/model/'):
                    identifier=path.rsplit('/',1)[-1]
                    catalog=json.loads((ROOT/'models/catalog.json').read_text(encoding='utf-8'))
                    entry=next((m for m in catalog['models'] if m['id']==identifier),None)
                    if entry is None:raise FileNotFoundError()
                    return self.send(json.loads((ROOT/'models'/entry['file']).read_text(encoding='utf-8')))
                if path=='/api/documents':return self.send(document_index())
                if path.startswith('/files/'):
                    relative=path[len('/files/'):]
                    if relative not in {d['path'] for d in document_index()}:raise FileNotFoundError()
                    file=(ROOT/relative).resolve()
                    if not file.is_relative_to(ROOT.resolve()):raise ValueError('Invalid document path')
                    return self.send(file.read_bytes(),content_type=mimetypes.guess_type(file.name)[0] or 'application/octet-stream')
                static={'/':'index.html','/app.js':'app.js','/styles.css':'styles.css'}
                if path not in static:raise FileNotFoundError()
                file=ROOT/'web'/static[path]
                return self.send(file.read_bytes(),content_type=mimetypes.guess_type(file.name)[0] or 'application/octet-stream')
            except FileNotFoundError:self.send({'error':'Not found'},404)
            except (ValueError,KeyError):self.send({'error':'Invalid request'},400)

        def do_POST(self):
            if not self.trusted_host():
                return self.send({'error':'Untrusted Host'},403)
            if self.path!='/api/run':return self.send({'error':'Not found'},404)
            if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.send({'error':'JSON required'},415)
            origin=self.headers.get('Origin')
            if origin and urlsplit(origin).netloc!=self.headers.get('Host'):return self.send({'error':'Origin mismatch'},403)
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=1024*1024:raise ValueError('Invalid body length')
                def invalid_constant(value):raise ValueError('Nonfinite JSON number')
                body=json.loads(self.rfile.read(size),parse_constant=invalid_constant)
                if not isinstance(body,dict) or set(body)-{'model_id','config','scenario','steps'}:raise ValueError('Unknown request fields')
                if not calculation_lock.acquire(blocking=False):return self.send({'error':'Calculation already running'},409)
                try:result=run_model(body.get('model_id'),body.get('config'),scenario=body.get('scenario'),steps=body.get('steps'))
                finally:calculation_lock.release()
                return self.send(store.save(result))
            except (ValueError,TypeError,KeyError,OverflowError) as error:
                return self.send({'error':str(error)},400)

    server=ThreadingHTTPServer((host,port),Handler)
    server.daemon_threads=True
    return server
