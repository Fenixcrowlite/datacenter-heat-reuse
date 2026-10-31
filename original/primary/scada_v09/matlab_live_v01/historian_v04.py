"""Isolated visited-sample historian for synthetic MATLAB v04 jobs (NOT v08 native).

This is an opt-in storage component. The running SCADA server does not automatically
install the endpoints. No measured / PLC / hardware fields are accepted.
"""
from __future__ import annotations
import hashlib, json, math, sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

# Inject the owning bridge's safe_result to avoid recursive module imports.
safe_result = None  # optional test override

FIELDS=("cas_h","T_pool_C","Q_pool_W","Q_DH_W","Q_reject_W","P_HP_W")

def validate_record(job_id, index, loader=None):
    if not isinstance(job_id,str) or len(job_id)!=32 or any(c not in "0123456789abcdef" for c in job_id):
        raise ValueError("Invalid v04 job ID")
    if isinstance(index,bool) or not isinstance(index,int) or not 0<=index<672:
        raise ValueError("Sample index must be 0..671")
    if loader is None:
        if callable(safe_result):
            loader=safe_result
        else:
            from live_bridge import safe_result as loader
    result=loader(job_id)
    metadata=result.get("metadata",{})
    if metadata.get("source_class")!="D_SYNTHETIC" or metadata.get("derived_quality")!="D_DERIVED" or metadata.get("hardware_enabled") is not False or metadata.get("status")!="VERIFIED_SIMULINK_NEW_RUN":
        raise ValueError("Refuse non-synthetic or unverified source")
    values=result["rows"][index]
    if abs(values["cas_h"]-.25*index)>1e-8 or not all(
            key in values and type(values[key]) in (int,float) and math.isfinite(values[key])
            for key in FIELDS):
        raise ValueError("Corrupt v04 sample")
    filehash=result["source_sha256"]
    if len(filehash)!=64 or any(c not in "0123456789abcdef" for c in filehash):
        raise ValueError("Invalid source SHA256")
    # Source hash must match the checksum captured when this job was submitted.
    # A renamed/replaced original SLX must not silently relabel archived results.
    cfg=(Path(__file__).resolve().parent/"runtime"/"jobs"/job_id/"config.json")
    saved=json.loads(cfg.read_text(encoding="utf-8-sig"))
    # Original 2026-10-24 legacy jobs predate the job-config checksum field.
    # Accept those only against the independently preserved v04 source SHA256.
    legacy_v04_sha="0d9a59466a0284ca6bb61d6756222dcca fc2ac7aa683ae41de35ce6d72f94ee0".replace(" ","")
    expected=saved.get("expected_source_sha256")
    if (expected is not None and expected!=filehash) or (expected is None and filehash!=legacy_v04_sha):
        raise ValueError("Source model changed since verified job")
    return filehash,{key:values[key] for key in FIELDS}

def open_db(path: Path):
    path=Path(path)
    if path.suffix!=".sqlite":
        raise ValueError("Historian requires SQLite file")
    path.parent.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(path,timeout=4)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=4000")
    con.execute("""CREATE TABLE IF NOT EXISTS v04_visited (
       job_id TEXT NOT NULL,
       source_sha256 TEXT NOT NULL,
       sample_index INTEGER NOT NULL,
       time_h REAL NOT NULL,
       first_seen_utc TEXT NOT NULL,
       T_pool_C REAL NOT NULL,
       Q_pool_W REAL NOT NULL,
       Q_DH_W REAL NOT NULL,
       Q_reject_W REAL NOT NULL,
       P_HP_W REAL NOT NULL,
       PRIMARY KEY(job_id,source_sha256,sample_index)
    )""")
    return con

def record_visit(job_id,index,db_path,loader=None):
    source,values=validate_record(job_id,index,loader=loader)
    now=datetime.now(timezone.utc).isoformat(timespec="seconds")
    with closing(open_db(db_path)) as con:
        count=con.execute("SELECT COUNT(*) FROM v04_visited WHERE job_id=? AND source_sha256=?",
                          (job_id,source)).fetchone()[0]
        if count>=672: return {"added":False,"count":count}
        row=(job_id,source,index,values["cas_h"],now,
             values["T_pool_C"],values["Q_pool_W"],values["Q_DH_W"],
             values["Q_reject_W"],values["P_HP_W"])
        cur=con.execute("""INSERT OR IGNORE INTO v04_visited
            (job_id,source_sha256,sample_index,time_h,first_seen_utc,
            T_pool_C,Q_pool_W,Q_DH_W,Q_reject_W,P_HP_W) VALUES(?,?,?,?,?,?,?,?,?,?)""",row)
        con.commit()
        return {"added":cur.rowcount==1,"count":count+(cur.rowcount==1)}

def read_visited(job_id,db_path,limit=672):
    if not isinstance(job_id,str) or len(job_id)!=32 or any(c not in "0123456789abcdef" for c in job_id):
        raise ValueError("Invalid v04 job ID")
    if isinstance(limit,bool) or not isinstance(limit,int) or not 1<=limit<=672:
        raise ValueError("Invalid historian limit")
    with closing(open_db(db_path)) as con:
        columns=["sample_index","time_h","first_seen_utc","T_pool_C",
                 "Q_pool_W","Q_DH_W","Q_reject_W","P_HP_W","source_sha256"]
        cur=con.execute("""SELECT sample_index,time_h,first_seen_utc,T_pool_C,
                       Q_pool_W,Q_DH_W,Q_reject_W,P_HP_W,source_sha256
                       FROM v04_visited WHERE job_id=? ORDER BY sample_index LIMIT ?""",(job_id,limit))
        rows=[dict(zip(columns,row)) for row in cur.fetchall()]
    return {"metadata":{"source_class":"D_SYNTHETIC","derived_quality":"D_DERIVED",
                        "model":"v04 new Simulink; visited historian ONLY",
                        "hardware_enabled":False,"not_v08_native_historian":True},
            "job_id":job_id,"rows":rows}
