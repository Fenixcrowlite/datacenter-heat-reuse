import {spawn} from "node:child_process";
import {readFile,writeFile,mkdir} from "node:fs/promises";
import path from "node:path";
import assert from "node:assert/strict";
import {setTimeout as sleep} from "node:timers/promises";
const root=path.resolve(import.meta.dirname,"..");
const profile=path.join(root,"runtime","qa_localized_cdp_"+process.pid);
const out=path.join(root,"runtime","i18n_qa");
await mkdir(out,{recursive:true});
const expected={
 ru:["Мнемосхема","Тепловой контур","Температура бассейна","Сравнение сценариев"],
 sk:["Synoptická schéma","Tepelný okruh","Teplota bazéna","Porovnanie scenárov"],
 en:["Synoptic view","Thermal circuit","Pool temperature","Scenario comparison"]};
const ready=await fetch("http://127.0.0.1:8091/api/health");
if(ready.status!==200)throw Error("SCADA offline");
const child=spawn("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",[
 "--headless=new","--no-first-run","--disable-gpu","--disable-extensions",
 "--no-default-browser-check","--disable-background-networking",
 "--remote-debugging-address=127.0.0.1","--remote-debugging-port=0",
 "--user-data-dir="+profile,"--window-size=1510,980","http://127.0.0.1:8091/?lang=ru"
],{stdio:"ignore",windowsHide:true});
let ws,seq=0;
const pending=new Map();
const onMessage=event=>{
 const data=JSON.parse(String(event.data));
 if(data.id && pending.has(data.id)){
  const rec=pending.get(data.id);pending.delete(data.id);
  if(data.error)rec.reject(Error(data.error.message));else rec.resolve(data.result);
 }
};
function send(method,params={}){
 const id=++seq;
 return new Promise((resolve,reject)=>{
  const timer=setTimeout(()=>{pending.delete(id);reject(Error("CDP timeout "+method));},10000);
  pending.set(id,{resolve:r=>{clearTimeout(timer);resolve(r);},reject:e=>{clearTimeout(timer);reject(e);}});
  ws.send(JSON.stringify({id,method,params}));
 });
}
async function evaluate(expression){
 const r=await send("Runtime.evaluate",{expression,returnByValue:true,awaitPromise:true});
 if(r.exceptionDetails)throw Error("Browser JS error "+JSON.stringify(r.exceptionDetails).slice(0,250));
 return r.result.value;
}
async function waitFor(fn,timeout=13000){
 const start=Date.now();
 while(Date.now()-start<timeout){
  try{const result=await fn();if(result)return result;}catch(e){}
  await sleep(250);
 }
 throw Error("Wait timeout");
}
try{
 const port=await waitFor(async()=>{
  const v=(await readFile(path.join(profile,"DevToolsActivePort"),"utf8")).split(/\r?\n/)[0];
  return /^\d+$/.test(v)?Number(v):null;
 });
 const target=await waitFor(async()=>{
  const r=await fetch("http://127.0.0.1:"+port+"/json/list");
  const entries=await r.json();
  return entries.find(e=>e.type==="page")?.webSocketDebuggerUrl;
 });
 ws=new WebSocket(target);ws.addEventListener("message",onMessage);
 await new Promise((res,rej)=>{ws.onopen=res;ws.onerror=()=>rej(Error("CDP socket failure"));});
 await send("Runtime.enable");await send("Page.enable");
 await waitFor(()=>evaluate("window.SCADA_I18N?.current()==='ru' && document.querySelector('#scenario-select')?.options?.length >= 8"));
 for(const lang of ["ru","sk","en"]){
  if(lang!=="ru"){
   const expr="(()=>{const e=document.querySelector('#language-select');e.value='"+lang+"';e.dispatchEvent(new Event('change',{bubbles:true}));return true})()";
   await evaluate(expr);
   await waitFor(()=>evaluate("document.documentElement.lang==='"+lang+"'"));
  }
  const state=await evaluate("(()=>({lang:document.documentElement.lang,body:document.body.innerText,source:document.querySelector('.safety-banner').innerText,scenario:document.querySelector('#scenario-select')?.value,selector:document.querySelector('#language-select')?.value,loaded:!!document.querySelector('.kpi-card')}))()");
  assert.equal(state.lang,lang);assert.equal(state.selector,lang);
  assert(state.loaded,"KPI failed "+lang);
  for(const label of expected[lang])assert(state.body.includes(label),lang+" untranslated: "+label);
  assert(state.source.includes("D_SYNTHETIC")&&state.source.includes("PLC"),"Missing hard-stop banner");
  assert(state.scenario&&state.scenario!=="Загрузка…","No scenarios");
  const picture=await send("Page.captureScreenshot",{format:"png",captureBeyondViewport:false});
  const file=path.join(out,"QA_"+lang+".png");
  await writeFile(file,Buffer.from(picture.data,"base64"));
  console.log("BROWSER_"+lang.toUpperCase()+"_PASS scenario="+state.scenario+" file="+file);
 }
 await send("Page.reload",{ignoreCache:true});
 await waitFor(()=>evaluate("window.SCADA_I18N?.current()==='en' && document.querySelector('.process-panel .panel-heading')?.innerText.includes('Thermal circuit')"));
 console.log("LANGUAGE_PERSISTENCE_RELOAD_PASS");
 await evaluate("(()=>{const e=document.querySelector('#scenario-select');e.value='oba_REJECT_off_bez_shedding';e.dispatchEvent(new Event('change',{bubbles:true}));return true})()");
 await waitFor(()=>evaluate("document.querySelector('#scenario-select')?.value==='oba_REJECT_off_bez_shedding'"));
 await evaluate("(()=>{const e=document.querySelector('#seek-input');e.value='219';e.dispatchEvent(new Event('change',{bubbles:true}));return true})()");
 await waitFor(()=>evaluate("document.querySelector('#sample-position')?.innerText?.includes('220')"));
 const alarms=await evaluate("document.querySelector('#alarm-feed').innerText.slice(0,800)");
 if(!alarms.includes("IT")&&!alarms.includes("REJECT"))throw Error("Fault alarm missing from GUI");
 console.log("OPERATOR_SCENARIO_ALARM_E2E_PASS");
 await evaluate("(()=>{const e=document.querySelector('#scenario-select');e.value='zdravy';e.dispatchEvent(new Event('change',{bubbles:true}));return true})()");
 await waitFor(()=>evaluate("document.querySelector('#scenario-select')?.value==='zdravy'"));
 console.log("I18N_BROWSER_3_LANGUAGES_PASS");
}finally{
 try{ws?.close();}catch(e){}
 try{child.kill();}catch(e){}
}
