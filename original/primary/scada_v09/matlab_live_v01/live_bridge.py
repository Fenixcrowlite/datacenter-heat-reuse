"""Local-only SCADA -> MATLAB/Simulink v04 bridge. All outputs synthetic; no PLC."""
from __future__ import annotations
import csv, hashlib, json, math, os, secrets, subprocess, sys, threading, time, uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from historian_v04 import record_visit, read_visited

HERE=Path(__file__).resolve().parent
SCADA=HERE.parent
PROJECT=SCADA.parent
RUNTIME=HERE/"runtime"
JOBS=RUNTIME/"jobs"
HISTORIAN_DB=RUNTIME/"historian_v04_visited.sqlite"
MATLAB=Path(r"C:\Program Files\MATLAB\R2026a\bin\matlab.exe")
ORIGIN_PORT=8094
TOKEN=secrets.token_urlsafe(32)
LOCK=threading.RLock()
JOB={"id":None,"state":"idle"}
PROC=None
SOURCE_MODEL=PROJECT/"matlab"/"pool_feedback_v04"/"DC_Bazen_Uzavreta_Regulacia_v04_SK.slx"
LIMITS={
 "pool_limit_kw":(0,150,150),
 "hp_thermal_limit_kw":(0,200,200),
 "dc_available_limit_kw":(0,500,300),
 "dh_request_limit_kw":(0,500,160),
 "source_temperature_offset_C":(-15,20,0),
 "pool_off_from_h":(0,168,168),
 "dh_off_from_h":(0,168,168),
 "dh_return_C":(5,90,45),
 "dh_mass_flow_kg_s":(.1,100,5),
}
BOOLS=("pool_enabled","dh_enabled","hp_pool_enabled","it_enabled","tes_enabled","hx_enabled")
def stopped():
    return (SCADA/"STOP").is_file() or (HERE/"STOP").is_file()
def iso():
    return datetime.now(timezone.utc).isoformat()
def parse_config(payload):
    if not isinstance(payload,dict) or set(payload)-set(LIMITS)-set(BOOLS):
        raise ValueError("Unknown or invalid fields")
    data={}
    for name,(lo,hi,default) in LIMITS.items():
        value=payload.get(name,default)
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not lo<=value<=hi:
            raise ValueError(name+" must be finite in range")
        data[name]=float(value)
    for name in BOOLS:
        value=payload.get(name,True)
        if not isinstance(value,bool):raise ValueError(name+" must be boolean")
        data[name]=value
    return data
def safe_result(jid):
    if not isinstance(jid,str) or len(jid)!=32 or any(c not in "0123456789abcdef" for c in jid):
        raise ValueError("Invalid ID")
    folder=JOBS/jid
    meta=folder/"result.json"; rows=folder/"result.csv"
    if not meta.is_file() or not rows.is_file():raise FileNotFoundError("Result not complete")
    data=json.loads(meta.read_text(encoding="utf-8-sig"))
    with rows.open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        samples=list(reader)
    if len(samples)!=672 or data.get("status")!="VERIFIED_SIMULINK_NEW_RUN":raise ValueError("Corrupt result")
    vals=[{k:float(v) for k,v in row.items()} for row in samples]
    if not all(math.isfinite(v) for row in vals for v in row.values()):raise ValueError("Nonfinite result")
    return {"metadata":data,"rows":vals,"id":jid,"source_sha256":hashlib.sha256(SOURCE_MODEL.read_bytes()).hexdigest()}
def read_native_v08():
    """Fixed loopback read-only archive adapter. No control token, no URL input."""
    from urllib.request import build_opener, ProxyHandler, HTTPRedirectHandler
    from urllib.parse import quote

    class RefuseRedirect(HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            raise ValueError("Archive redirect denied")

    opener = build_opener(ProxyHandler({}), RefuseRedirect())

    def read_fixed(path):
        # Host and base port cannot be overridden by clients.
        with opener.open("http://127.0.0.1:8091" + path, timeout=5) as resp:
            if resp.status != 200:
                raise ValueError("Native archive unavailable")
            raw = resp.read(4_000_001)
        if len(raw) > 4_000_000:
            raise ValueError("Oversized native archive")
        return json.loads(raw)

    status = read_fixed("/api/status")
    scenario = status.get("scenario_id", "")
    if not isinstance(scenario, str) or not (1 <= len(scenario) <= 80) or not all(
        c.isascii() and (c.isalnum() or c == "_") for c in scenario
    ):
        raise ValueError("Invalid native scenario")
    history = read_fixed("/api/history?scenario=" + quote(scenario, safe="") +
                         "&scope=full&limit=672")
    meta = history.get("metadata", {})
    if (meta.get("source_class") != "D_SYNTHETIC" or meta.get("quality") != "D" or
            meta.get("hardware_enabled") is not False or
            history.get("scenario_id") != scenario or
            history.get("scope") != "full"):
        raise ValueError("Unexpected native provenance")
    rows = history.get("rows", [])
    if len(rows) != 672 or any(
        not isinstance(rec, dict) or rec.get("sample_index") != i or
        not isinstance(rec.get("values"), dict) or
        abs(rec["values"].get("cas_h", -1) - i * .25) > 1e-8 or
        not all(isinstance(v, (int, float)) and math.isfinite(v)
                for v in rec["values"].values())
        for i, rec in enumerate(rows)
    ):
        raise ValueError("Invalid native full-history time grid")
    # Never forward csrf_token, replay control or host-internal state.
    return {"metadata": dict(meta), "source": "v08 archival Simulink CSV replay",
            "scenario_id": scenario, "scenario_index": status.get("index"),
            "rows": rows, "rows_kind": "source_samples_not_visited_historian",
            "hardware_enabled": False}

def stop_owned_matlab(process):
    if process.poll() is not None:return
    if os.name=="nt":
        # Terminate only the subprocess tree created by this bridge.
        try:subprocess.run(["taskkill","/PID",str(process.pid),"/T","/F"],
                           capture_output=True,timeout=10,check=False)
        except (OSError,subprocess.TimeoutExpired):process.terminate()
    else:process.terminate()

def work(jid,config):
    global PROC,JOB
    folder=JOBS/jid
    cmd=[str(MATLAB),"-batch", "run('"+str((HERE/"live_v04_runner.m").resolve()).replace("\\","/")+"')"]
    try:
        if stopped():raise RuntimeError("STOP active")
        env=os.environ.copy();env["DCHR_JOB_JSON"]=str(folder/"config.json")
        with (folder/"matlab.log").open("w",encoding="utf-8") as log:
            process=subprocess.Popen(cmd,cwd=str(HERE),env=env,stdout=log,stderr=subprocess.STDOUT,
                                     stdin=subprocess.DEVNULL,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
            with LOCK: PROC=process;JOB.update(state="running",pid=process.pid,started_at=iso())
            started=time.monotonic()
            while process.poll() is None:
                if stopped():
                    stop_owned_matlab(process)
                    raise RuntimeError("STOP detected; owned MATLAB job terminated")
                if time.monotonic()-started>360:
                    stop_owned_matlab(process)
                    raise RuntimeError("MATLAB timeout 360s")
                free=available_ram_mb()
                if free is not None and free<384:
                    stop_owned_matlab(process)
                    raise RuntimeError("MATLAB owned job stopped: critically low RAM")
                time.sleep(.75)
        if process.returncode!=0:raise RuntimeError("MATLAB exited with code "+str(process.returncode))
        if stopped():raise RuntimeError("STOP active on completion")
        result=safe_result(jid)
        if result["source_sha256"]!=json.loads((folder/"config.json").read_text(encoding="utf-8"))["expected_source_sha256"]:
            raise RuntimeError("Original model checksum changed; refuse result")
        with LOCK:
            JOB.update(state="done",finished_at=iso(),result_summary=result["metadata"],pid=None)
    except Exception as exc:
        with LOCK: JOB.update(state="error",error=str(exc)[:280],finished_at=iso(),pid=None)
    finally:
        with LOCK: PROC=None
MIN_FREE_RAM_MATLAB_MB=6144

def available_ram_mb():
    """Windows physical available RAM; fail closed if OS telemetry unavailable."""
    if os.name!="nt":
        return None
    try:
        import ctypes
        class MEMSTAT(ctypes.Structure):
            _fields_=[("dwLength",ctypes.c_ulong),
                      ("dwMemoryLoad",ctypes.c_ulong),
                      ("ullTotalPhys",ctypes.c_ulonglong),
                      ("ullAvailPhys",ctypes.c_ulonglong),
                      ("ullTotalPageFile",ctypes.c_ulonglong),
                      ("ullAvailPageFile",ctypes.c_ulonglong),
                      ("ullTotalVirtual",ctypes.c_ulonglong),
                      ("ullAvailVirtual",ctypes.c_ulonglong),
                      ("ullAvailExtendedVirtual",ctypes.c_ulonglong)]
        v=MEMSTAT()
        v.dwLength=ctypes.sizeof(MEMSTAT)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(v)):
            return None
        return int(v.ullAvailPhys//(1024*1024))
    except (AttributeError,OSError,ValueError):
        return None

def launch(payload):
    global JOB
    config=parse_config(payload)
    if stopped():raise RuntimeError("STOP active")
    free=available_ram_mb()
    if free is None or free<MIN_FREE_RAM_MATLAB_MB:
        raise RuntimeError("MATLAB run blocked: free RAM "+str(free)+" MB; requires "+
                           str(MIN_FREE_RAM_MATLAB_MB)+" MB")
    if not MATLAB.is_file() or not SOURCE_MODEL.is_file():raise RuntimeError("MATLAB or model not found")
    with LOCK:
        if JOB.get("state") in ("queued","running"):raise RuntimeError("Another MATLAB job owns the runner")
        jid=uuid.uuid4().hex
        folder=JOBS/jid;folder.mkdir(parents=True,exist_ok=False)
        spec={**config,"project_root":str(PROJECT),
              "expected_source_sha256":hashlib.sha256(SOURCE_MODEL.read_bytes()).hexdigest()}
        (folder/"config.json").write_text(json.dumps(spec,indent=2),encoding="utf-8")
        JOB={"id":jid,"state":"queued","created_at":iso(),"source_class":"D_SYNTHETIC",
             "model":"v04 real Simulink run, not v08/v85","config":config}
        threading.Thread(target=work,args=(jid,config),daemon=True,name="matlab-job").start()
        return dict(JOB)
def restore_latest():
    global JOB
    if not JOBS.is_dir():return
    folders=sorted((p for p in JOBS.iterdir() if p.is_dir()),key=lambda p:p.stat().st_mtime,reverse=True)
    for folder in folders:
        try:
            result=safe_result(folder.name)
            config=json.loads((folder/"config.json").read_text(encoding="utf-8"))
            JOB={"id":folder.name,"state":"done","restored_at":iso(),
                 "source_class":"D_SYNTHETIC","model":"v04 real Simulink run, not v08/v85",
                 "config":{k:v for k,v in config.items() if k in LIMITS or k in BOOLS},
                 "result_summary":result["metadata"]}
            return
        except (ValueError,FileNotFoundError,KeyError,TypeError):pass
class Server(ThreadingHTTPServer):
    daemon_threads=True
    allow_reuse_address=False
    def server_bind(self):
        import socket
        if hasattr(socket,"SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
        super().server_bind()
class Handler(BaseHTTPRequestHandler):
    protocol_version="HTTP/1.0"
    def log_message(self,*args):pass
    def validate(self):
        import ipaddress
        if not ipaddress.ip_address(self.client_address[0]).is_loopback:raise PermissionError("loopback only")
        host=self.headers.get("Host","")
        if host not in (f"127.0.0.1:{ORIGIN_PORT}",f"localhost:{ORIGIN_PORT}"):
            raise PermissionError("invalid host")
        origin=self.headers.get("Origin")
        if origin is not None and origin!="http://"+host:raise PermissionError("invalid origin")
        p=urlsplit(self.path)
        if p.query or p.fragment or p.scheme or p.netloc or ".." in p.path or "\\" in p.path:
            raise ValueError("Invalid URL")
        return p.path
    def send(self,code,value,kind="application/json; charset=utf-8"):
        raw=json.dumps(value,ensure_ascii=False,allow_nan=False).encode() if isinstance(value,dict) else value
        self.send_response(code);self.send_header("Content-Type",kind)
        self.send_header("Content-Length",str(len(raw)))
        self.send_header("Cache-Control","no-store")
        self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("X-Frame-Options","DENY")
        self.send_header("Referrer-Policy","no-referrer")
        self.send_header("Content-Security-Policy","default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'")
        self.end_headers()
        try:self.wfile.write(raw)
        except (BrokenPipeError,ConnectionResetError):pass
    def do_GET(self):
        try:
            p=self.validate()
            if p in ("/","/index.html"):
                self.send(200,(HERE/"dashboard.html").read_bytes(),"text/html; charset=utf-8")
            elif p=="/dashboard.js":
                self.send(200,(HERE/"dashboard.js").read_bytes(),"text/javascript; charset=utf-8")
            elif p=="/source_compare.js":
                self.send(200,(HERE/"source_compare.js").read_bytes(),"text/javascript; charset=utf-8")
            elif p=="/visited_v04.js":
                self.send(200,(HERE/"visited_v04.js").read_bytes(),"text/javascript; charset=utf-8")
            elif p=="/api/archive":
                self.send(200,read_native_v08())
            elif p=="/api/status":
                with LOCK: s=dict(JOB)
                self.send(200,{"ok":True,"stop":stopped(),"model_present":SOURCE_MODEL.is_file(),
                               "matlab_present":MATLAB.is_file(),"job":s,"csrf_token":TOKEN,
                               "free_ram_mb":available_ram_mb(),
                               "matlab_run_min_free_ram_mb":MIN_FREE_RAM_MATLAB_MB,
                               "model":"v04 Stateflow/Simulink new execution",
                               "source_class":"D_SYNTHETIC","hardware_enabled":False})
            elif p=="/api/result":
                with LOCK: s=dict(JOB)
                if s.get("state")!="done":self.send(409,{"error":"No completed model execution"})
                else:self.send(200,safe_result(s["id"]))
            elif p=="/api/visited":
                with LOCK: s=dict(JOB)
                if s.get("state")!="done":self.send(409,{"error":"No completed v04 job"})
                else:self.send(200,read_visited(s["id"],HISTORIAN_DB))
            elif p=="/api/health":
                with LOCK: s=dict(JOB)
                self.send(200,{"ok":True,"stop":stopped(),"state":s["state"],"model":"v04"})
            else:self.send(404,{"error":"Not found"})
        except (ValueError,PermissionError) as e:self.send(403,{"error":str(e)})
        except FileNotFoundError:self.send(404,{"error":"Result unavailable"})
        except Exception:self.send(500,{"error":"Server error"})
    def do_POST(self):
        try:
            route=self.validate()
            if route not in ("/api/run","/api/visit"):
                return self.send(404,{"error":"Not found"})
            if not secrets.compare_digest(self.headers.get("X-Live-Token",""),TOKEN):
                raise PermissionError("bad token")
            if self.headers.get("Content-Type","")!="application/json" or self.headers.get("Transfer-Encoding"):
                raise ValueError("JSON only")
            size=int(self.headers.get("Content-Length","0"))
            if not 1<=size<=4096:raise ValueError("Invalid body size")
            payload=json.loads(self.rfile.read(size),parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite")))
            if route=="/api/run":
                self.send(202,launch(payload))
            else:
                if stopped():raise RuntimeError("STOP active")
                if not isinstance(payload,dict) or set(payload)!=set(("id","sample_index")):
                    raise ValueError("Strict visit schema: id, sample_index")
                with LOCK: s=dict(JOB)
                if s.get("state")!="done" or payload["id"]!=s.get("id"):
                    raise RuntimeError("Visit only the current completed v04 job")
                if type(payload["sample_index"]) is not int or not 0<=payload["sample_index"]<672:
                    raise ValueError("Visit sample index 0..671")
                report=record_visit(payload["id"],payload["sample_index"],HISTORIAN_DB,
                                    loader=safe_result)
                self.send(200,{"ok":True,"source_class":"D_SYNTHETIC",
                               "derived_quality":"D_DERIVED","job_id":s["id"],**report})
        except RuntimeError as e:self.send(409,{"error":str(e)})
        except (ValueError,TypeError,PermissionError) as e:self.send(400,{"error":str(e)})
        except Exception:self.send(500,{"error":"Server error"})
    def do_OPTIONS(self):self.send(405,{"error":"Disabled"})
if __name__=="__main__":
    RUNTIME.mkdir(exist_ok=True);JOBS.mkdir(exist_ok=True)
    restore_latest()
    server=Server(("127.0.0.1",ORIGIN_PORT),Handler)
    (RUNTIME/"server.json").write_text(json.dumps({"pid":os.getpid(),"port":ORIGIN_PORT,"started_at":iso()}),encoding="utf-8")
    try:server.serve_forever(poll_interval=.5)
    finally:server.server_close()
