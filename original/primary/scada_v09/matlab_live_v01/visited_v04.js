"use strict";
(() => {
  const el=id=>document.getElementById(id);
  const status=el("visit-status"), body=el("visit-body"), timeline=el("timeline");
  let currentId="", pending=null, serial=0, previousSignature="", enabled=false;

  const fmt=(n,d=2)=>typeof n==="number"&&Number.isFinite(n)?n.toFixed(d):"—";
  async function json(path,options) {
    const response=await fetch(path,{cache:"no-store",credentials:"same-origin",...options});
    const data=await response.json();
    if(!response.ok)throw new Error(data.error||("HTTP "+response.status));
    return data;
  }
  async function loadHistory(jid) {
    const received=await json("/api/visited");
    if(received.job_id!==jid||received.metadata?.source_class!=="D_SYNTHETIC"||
       received.metadata?.derived_quality!=="D_DERIVED"||
       received.metadata?.hardware_enabled!==false||
       received.metadata?.not_v08_native_historian!==true||
       !Array.isArray(received.rows))throw Error("История не соответствует v04 job");
    if(jid!==currentId)return;
    body.replaceChildren();
    const visits=received.rows;
    for(const v of visits.slice(-30)) {
      const tr=document.createElement("tr");
      for(const cell of [v.first_seen_utc,fmt(v.time_h),fmt(v.T_pool_C),
                         fmt(v.Q_DH_W/1000),fmt(v.P_HP_W/1000)]) {
        const td=document.createElement("td");
        td.textContent=String(cell);td.style.padding="5px 8px";
        td.style.borderBottom="1px solid #304256";
        tr.appendChild(td);
      }
      body.appendChild(tr);
    }
    status.textContent="Посещено "+visits.length+" / 672 отсчётов · job "+jid+
      " · отдельный локальный historian v04 (синтетические данные)";
  }
  async function observe() {
    const own=++serial;
    try {
      const s=await json("/api/status");
      if(own!==serial)return;
      if(s.stop||s.job?.state!=="done"||!s.job.id) {
        enabled=false;currentId="";previousSignature="";
        body.replaceChildren();status.textContent=s.stop?
            "STOP активен: запись остановлена":"Нет завершённого MATLAB v04 job.";
        return;
      }
      enabled=true;
      if(currentId!==s.job.id) {
        currentId=s.job.id;previousSignature="";
        await loadHistory(currentId);
        // On initial launch, dashboard.js restores a saved job and selects its last sample.
        // Recording is triggered only after a user seeks through the v04 timeline.
      }
    } catch(e) {
      enabled=false;status.textContent="Историк недоступен: "+e.message;
    }
  }
  async function visit() {
    if(!enabled||!currentId)return;
    const desired=Number(timeline.value), jid=currentId;
    if(!Number.isInteger(desired)||desired<0||desired>=672)return;
    const signature=jid+":"+desired;
    if(signature===previousSignature)return;
    try {
      const s=await json("/api/status");
      if(s.stop||s.job?.state!=="done"||s.job.id!==jid) return;
      const result=await json("/api/visit",{
        method:"POST",
        headers:{"Content-Type":"application/json","X-Live-Token":s.csrf_token},
        body:JSON.stringify({id:jid,sample_index:desired})
      });
      if(result.job_id!==jid||result.derived_quality!=="D_DERIVED"||!result.ok)
        throw Error("Unexpected historian confirmation");
      previousSignature=signature;
      if(currentId===jid) await loadHistory(jid);
    } catch(e) {
      status.textContent="История не записана: "+e.message;
    }
  }
  timeline.addEventListener("input",()=>{
    if(pending!==null)clearTimeout(pending);
    pending=setTimeout(()=>{pending=null;visit()},420);
  });
  setInterval(observe,2600);
  observe();
})();
