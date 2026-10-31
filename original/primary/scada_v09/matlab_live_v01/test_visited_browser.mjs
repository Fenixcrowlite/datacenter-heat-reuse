import {spawn} from "node:child_process";
import {readFile,writeFile,mkdir} from "node:fs/promises";
import path from "node:path";
import assert from "node:assert/strict";
import {setTimeout as sleep} from "node:timers/promises";

const dir=path.resolve(import.meta.dirname), profile=path.join(dir,"runtime","qa_visited_browser_"+process.pid);
await mkdir(profile,{recursive:true});
const browser=spawn("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",[
  "--headless=new","--no-first-run","--disable-gpu","--disable-extensions",
  "--no-default-browser-check","--disable-background-networking",
  "--remote-debugging-address=127.0.0.1","--remote-debugging-port=0",
  "--user-data-dir="+profile,"--window-size=1450,1000","http://127.0.0.1:8094/#visited-history"
],{stdio:"ignore",windowsHide:true});
let ws,seq=0;const pending=new Map(),exceptionTexts=[];
function cmd(method,params={}){
  const id=++seq;return new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>{pending.delete(id);reject(Error("CDP timed out: "+method))},12000);
    pending.set(id,{resolve:r=>{clearTimeout(timer);resolve(r)},reject:e=>{clearTimeout(timer);reject(e)}});
    ws.send(JSON.stringify({id,method,params}));
  });
}
async function js(expression){
  const r=await cmd("Runtime.evaluate",{expression,awaitPromise:true,returnByValue:true});
  if(r.exceptionDetails)throw Error("Runtime.evaluate: "+JSON.stringify(r.exceptionDetails).slice(0,500));
  return r.result.value;
}
async function until(fn,limit=20000) {
  const deadline=Date.now()+limit;
  while(Date.now()<deadline){try{const val=await fn();if(val)return val}catch{}
    await sleep(220);}
  throw Error("Timed out in browser test");
}
try {
  const port=await until(async()=>{
    const raw=await readFile(path.join(profile,"DevToolsActivePort"),"utf8");
    return Number(raw.split(/\r?\n/)[0])||null;
  });
  const target=await until(async()=>{
    const response=await fetch("http://127.0.0.1:"+port+"/json/list");
    return (await response.json()).find(x=>x.type==="page")?.webSocketDebuggerUrl;
  });
  ws=new WebSocket(target);
  ws.addEventListener("message",event=>{
    const msg=JSON.parse(String(event.data));
    if(msg.method==="Runtime.exceptionThrown")
      exceptionTexts.push(msg.params?.exceptionDetails?.text||"Uncaught browser error");
    const entry=pending.get(msg.id);if(!entry)return;
    pending.delete(msg.id);
    if(msg.error)entry.reject(Error(msg.error.message));else entry.resolve(msg.result);
  });
  await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject});
  await cmd("Runtime.enable");await cmd("Page.enable");
  await until(()=>js("document.querySelector('#visit-status')?.textContent.includes('Посещено')"));
  const init=await js("({status:document.querySelector('#visit-status').textContent,job:document.querySelector('#details').textContent,rows:document.querySelectorAll('#visit-body tr').length})");
  assert(init.rows>=1);assert(init.status.includes("v04"));
  const memory=await fetch("http://127.0.0.1:8094/api/status").then(r=>r.json());
  const gate=await js("({disabled:document.querySelector('#go').disabled,details:document.querySelector('#details').textContent})");
  assert(gate.details.includes("RAM"),"RAM readiness absent in HMI");
  if(memory.free_ram_mb<memory.matlab_run_min_free_ram_mb) {
    assert.equal(gate.disabled,true,"Unsafe MATLAB button was enabled under memory threshold");
  }
  await js("(()=>{const r=document.querySelector('#timeline');r.value='120';r.dispatchEvent(new Event('input',{bubbles:true}));return true})()");
  await until(()=>js("document.querySelector('#visit-status')?.textContent.includes('Посещено 2 / 672')"));
  const before=await fetch("http://127.0.0.1:8094/api/visited").then(r=>r.json());
  assert(before.rows.some(r=>r.sample_index===80));
  assert(before.rows.some(r=>r.sample_index===120));
  const visitsBefore=before.rows.length;
  await js("(()=>{const s=document.querySelector('#sc-source');s.value='v08';s.dispatchEvent(new Event('change',{bubbles:true}));return true})()");
  await until(()=>js("document.querySelector('#sc-provenance')?.textContent.startsWith('SOURCE=v08')"));
  await js("(()=>{const s=document.querySelector('#sc-index');s.value='95';s.dispatchEvent(new Event('input',{bubbles:true}));return true})()");
  await sleep(900);
  const after=await fetch("http://127.0.0.1:8094/api/visited").then(r=>r.json());
  assert.equal(after.rows.length,visitsBefore,"v08 switch incorrectly logged into v04 historian");
  assert.equal(exceptionTexts.length,0,JSON.stringify(exceptionTexts));
  await js("document.querySelector('#visited-history').scrollIntoView()");
  const capture=await cmd("Page.captureScreenshot",{format:"png",captureBeyondViewport:false});
  const file=path.join(dir,"runtime","QA_VISITED_BROWSER_20261026.png");
  await writeFile(file,Buffer.from(capture.data,"base64"));
  console.log(JSON.stringify({status:"BROWSER_PASS",initial:init,visit_120_saved:true,
    visited_total:after.rows.length,v08_not_written:true,
    browser_uncaught:exceptionTexts.length,screenshot:file},null,2));
}catch(e){console.error("BROWSER_FAIL",e.stack||e);process.exitCode=1}
finally{if(ws)ws.close();browser.kill()}
