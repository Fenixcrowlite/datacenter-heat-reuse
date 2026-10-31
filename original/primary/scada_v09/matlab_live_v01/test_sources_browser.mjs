import {spawn} from "node:child_process";
import {readFile,writeFile,mkdir} from "node:fs/promises";
import path from "node:path";
import assert from "node:assert/strict";
import {setTimeout as sleep} from "node:timers/promises";

const root=path.resolve(import.meta.dirname);
const profile=path.join(root,"runtime","qa_source_browser_"+process.pid);
await mkdir(profile,{recursive:true});
const chrome=spawn("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",[
  "--headless=new","--no-first-run","--disable-gpu","--disable-extensions",
  "--no-default-browser-check","--disable-background-networking",
  "--remote-debugging-address=127.0.0.1","--remote-debugging-port=0",
  "--user-data-dir="+profile,"--window-size=1440,940",
  "http://127.0.0.1:8094/#source-selector"
],{stdio:"ignore",windowsHide:true});
let ws,seq=0;const pending=new Map(),exceptions=[];
function send(method,params={}){
  const id=++seq;return new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>{pending.delete(id);reject(Error("CDP timeout "+method));},15000);
    pending.set(id,{resolve:v=>{clearTimeout(timer);resolve(v);},reject:e=>{clearTimeout(timer);reject(e);}});
    ws.send(JSON.stringify({id,method,params}));
  });
}
async function evaluate(expression){
  const r=await send("Runtime.evaluate",{expression,returnByValue:true,awaitPromise:true});
  if(r.exceptionDetails)throw Error("JS: "+JSON.stringify(r.exceptionDetails).slice(0,500));
  return r.result.value;
}
async function until(fn,timeout=24000) {
  const deadline=Date.now()+timeout;
  while(Date.now()<deadline){try{const r=await fn();if(r)return r;}catch{}
    await sleep(250);}
  throw Error("Browser load timeout");
}
try{
  const port=await until(async()=>{
    const raw=await readFile(path.join(profile,"DevToolsActivePort"),"utf8");
    return Number(raw.split(/\r?\n/)[0]) || null;
  });
  const target=await until(async()=>{
    const response=await fetch("http://127.0.0.1:"+port+"/json/list");
    return (await response.json()).find(t=>t.type==="page")?.webSocketDebuggerUrl;
  });
  ws=new WebSocket(target);
  ws.addEventListener("message",e=>{
    const msg=JSON.parse(String(e.data));
    if(msg.method==="Runtime.exceptionThrown")exceptions.push(msg.params?.exceptionDetails?.text||"JS error");
    const entry=pending.get(msg.id);if(!entry)return;
    pending.delete(msg.id);
    if(msg.error)entry.reject(Error(msg.error.message));else entry.resolve(msg.result);
  });
  await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject});
  await send("Runtime.enable");await send("Page.enable");
  await until(()=>evaluate("document.querySelector('#sc-provenance')?.textContent.startsWith('SOURCE=v04')"));
  const before=await evaluate("({source:document.querySelector('#sc-provenance').textContent,temp:document.querySelector('#sc-pool-temp').textContent,rows:document.querySelectorAll('#sc-table-body tr').length,chart:document.querySelector('#sc-temp-chart').width})");
  assert.match(before.source,/SOURCE=v04/);assert(before.rows>0);assert(before.chart>=900);
  await evaluate("(()=>{const s=document.querySelector('#sc-source');s.value='v08';s.dispatchEvent(new Event('change',{bubbles:true}));return true})()");
  await until(()=>evaluate("document.querySelector('#sc-provenance')?.textContent.startsWith('SOURCE=v08')"));
  const after=await evaluate("({source:document.querySelector('#sc-provenance').textContent,temp:document.querySelector('#sc-pool-temp').textContent,rows:document.querySelectorAll('#sc-table-body tr').length,note:document.querySelector('#sc-temp-note').textContent,error:document.querySelector('#sc-error').textContent})");
  assert.match(after.source,/SOURCE=v08/);
  assert(after.rows>0);assert.equal(after.error,"");
  assert.notEqual(after.temp,before.temp,"Source value did not switch");
  assert(after.note.includes("нет проверенной температуры подачи"));
  await evaluate("(()=>{const s=document.querySelector('#sc-index');s.value='80';s.dispatchEvent(new Event('input',{bubbles:true}));return true})()");
  const scrub=await evaluate("({temp:document.querySelector('#sc-pool-temp').textContent,clock:document.querySelector('#sc-clock').textContent,diagnostics:document.querySelector('#sc-diagnostics').textContent})");
  assert(scrub.clock.includes("20.00 ч"));assert(scrub.diagnostics.startsWith("v08:"));
  await evaluate("document.querySelector('#source-selector').scrollIntoView()");
  const pic=await send("Page.captureScreenshot",{format:"png",captureBeyondViewport:false});
  const img=path.join(root,"runtime","QA_SOURCE_SELECTOR_BROWSER_20261025.png");
  await writeFile(img,Buffer.from(pic.data,"base64"));
  assert.equal(exceptions.length,0,"Uncaught browser JS errors");
  console.log(JSON.stringify({verdict:"PASS",v04:before,v08:after,at_20h:scrub,screenshot:img,uncaught_errors:exceptions.length},null,2));
}catch(e){console.error("BROWSER_FAIL",e.stack||e.message);process.exitCode=1;}
finally{if(ws)ws.close();chrome.kill();}
