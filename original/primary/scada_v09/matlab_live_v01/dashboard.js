"use strict";
const $=id=>document.getElementById(id);
const btn=$("go"), form=$("params");
let token="", lastId="", rows=[], meta=null;
const f=(v,n=2)=>Number.isFinite(v)?v.toFixed(n):"—";
function draw(canvasId, series, idx){
  const canvas=$(canvasId),c=canvas.getContext("2d"),w=canvas.width,h=canvas.height;
  c.clearRect(0,0,w,h);c.fillStyle="#101c2a";c.fillRect(0,0,w,h);
  const vals=series.flatMap(a=>a.data.filter(Number.isFinite));
  if(!vals.length)return;
  let lo=Math.min(...vals),hi=Math.max(...vals);if(lo===hi){lo-=1;hi+=1}
  const pad=40, toX=i=>pad+(w-2*pad)*i/Math.max(1,rows.length-1);
  const toY=v=>h-pad-(h-2*pad)*(v-lo)/(hi-lo);
  c.strokeStyle="#243b4b";c.fillStyle="#9ab5c5";c.font="13px system-ui";
  for(let k=0;k<=4;k++){let y=pad+k*(h-2*pad)/4;c.beginPath();c.moveTo(pad,y);c.lineTo(w-pad,y);c.stroke();c.fillText(f(hi-(hi-lo)*k/4,1),3,y+4)}
  for(const s of series){c.strokeStyle=s.color;c.lineWidth=2;c.beginPath();let started=false;
    s.data.forEach((v,i)=>{if(!Number.isFinite(v)){started=false;return}
      if(!started){c.moveTo(toX(i),toY(v));started=true}else c.lineTo(toX(i),toY(v))});c.stroke()}
  c.strokeStyle="#bfcfe2";c.setLineDash([4,5]);c.beginPath();
  c.moveTo(toX(idx),pad);c.lineTo(toX(idx),h-pad);c.stroke();c.setLineDash([]);
  c.fillText("0 ч",pad,h-9);c.fillText("168 ч",w-pad-40,h-9);
}
function show(idx){
  if(!rows.length)return;
  idx=Math.max(0,Math.min(idx,rows.length-1));const r=rows[idx];
  $("temp").textContent=f(r.T_pool_C)+" °C";
  $("pool").textContent=f(r.Q_pool_W/1000)+" кВт";
  $("dh").textContent=f(r.Q_DH_W/1000)+" кВт";
  $("cop").textContent=f(r.COP,2)+" / "+f(r.P_HP_W/1000,1)+" кВт";
  $("time").textContent="t = "+f(r.cas_h,2)+" ч / Stateflow "+f(r.stateflow_mode,0);
  $("timeline").value=idx;
  draw("tempChart",[
    {color:"#3ad3f5",data:rows.map(v=>v.T_pool_C)},
    {color:"#ecb870",data:rows.map(v=>v.T_DH_supply_derived_C)}],idx);
  draw("powerChart",[
    {color:"#3ad3f5",data:rows.map(v=>v.Q_pool_W/1000)},
    {color:"#b69cfa",data:rows.map(v=>v.Q_DH_W/1000)},
    {color:"#f0a367",data:rows.map(v=>v.Q_reject_W/1000)},
    {color:"#88d2a1",data:rows.map(v=>v.P_HP_W/1000)}],idx);
}
$("timeline").addEventListener("input",e=>show(+e.target.value));
async function fetchJSON(path,opt){
  const r=await fetch(path,{cache:"no-store",...opt}),x=await r.json();
  if(!r.ok)throw Error(x.error||("HTTP "+r.status));return x
}
function renderDone(data){
  rows=data.rows;meta=data.metadata;show(rows.length-1);
  $("summary").textContent=[
    "Источник: "+meta.source_class+" / "+meta.derived_quality,
    "Контроллер: "+meta.model_scope,
    "В бассейн: "+f(meta.total_pool_MWh,4)+" МВт·ч",
    "В теплосеть: "+f(meta.total_DH_MWh,4)+" МВт·ч",
    "Отведено REJECT: "+f(meta.total_reject_MWh,4)+" МВт·ч",
    "Электричество компрессора: "+f(meta.total_HP_electrical_MWh,4)+" МВт·ч",
    "Максимум бассейна: "+f(meta.max_T_pool_C,3)+" °C",
    "Контроль баланса воды: "+f(meta.closure_pool_W,7)+" Вт",
    "Контроль TES: "+f(meta.closure_TES_W,7)+" Вт",
    "Контроль потоков: "+f(meta.closure_flow_W,7)+" Вт",
    "Исходная модель SHA-256: "+data.source_sha256,
    "Результат: 672 рассчитанных отсчёта. Без физических измерений и управления."
  ].join("\n");
}
async function refresh(){
  try {
    const s=await fetchJSON("/api/status");token=s.csrf_token;
    const j=s.job;
    $("status").textContent=s.stop?"STOP АКТИВЕН":({"idle":"Готов","queued":"В очереди","running":"MATLAB вычисляет","done":"Расчёт завершён","error":"Ошибка"}[j.state]||j.state);
    const free=Number.isFinite(s.free_ram_mb)?s.free_ram_mb:null;
    const threshold=Number.isFinite(s.matlab_run_min_free_ram_mb)?s.matlab_run_min_free_ram_mb:6144;
    const lowMemory=free===null||free<threshold;
    $("details").textContent="MATLAB "+(s.matlab_present?"доступен":"НЕ НАЙДЕН")+"; v04 "+(s.model_present?"найден":"НЕ НАЙДЕН")+"; Job "+(j.id||"—")+
      "; RAM "+(free===null?"неизвестна":free+" МБ")+" / минимум "+threshold+" МБ для нового расчёта";
    $("error").textContent=j.error||(lowMemory?"Новый MATLAB заблокирован по памяти; готовые результаты остаются доступны.":"");
    btn.disabled=!!s.stop||!s.matlab_present||!s.model_present||j.state==="running"||j.state==="queued"||lowMemory;
    if(j.state==="done" && j.id!==lastId){
      const data=await fetchJSON("/api/result");lastId=j.id;renderDone(data);
    }
  }catch(e){$("status").textContent="Сервер недоступен";$("error").textContent=e.message;btn.disabled=true}
}
form.addEventListener("submit",async e=>{
  e.preventDefault();btn.disabled=true;$("error").textContent="";
  const data={};
  for(const el of form.querySelectorAll("input[name]")){
    data[el.name]=el.type==="checkbox"?el.checked:Number(el.value)
  }
  try{
    const s=await fetchJSON("/api/run",{method:"POST",headers:{"Content-Type":"application/json","X-Live-Token":token},body:JSON.stringify(data)});
    $("details").textContent="Запущен Simulink job "+s.id;
  }catch(err){$("error").textContent=err.message}
  await refresh()
});
setInterval(refresh,2500);refresh();
