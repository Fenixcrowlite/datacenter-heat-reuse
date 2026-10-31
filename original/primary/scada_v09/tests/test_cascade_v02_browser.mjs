import {spawn} from "node:child_process";
import {readFile,writeFile,mkdir} from "node:fs/promises";
import path from "node:path";
import {setTimeout as sleep} from "node:timers/promises";
import assert from "node:assert/strict";
const root=path.resolve(import.meta.dirname,".."),profile=path.join(root,"runtime","qa_c2_"+process.pid);
await mkdir(profile,{recursive:true});
const chrome=spawn("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",[
  "--headless=new","--no-first-run","--disable-gpu","--disable-extensions",
  "--no-default-browser-check","--disable-background-networking",
  "--remote-debugging-address=127.0.0.1","--remote-debugging-port=0",
  "--user-data-dir="+profile,"--window-size=1500,1000","http://127.0.0.1:8091/#cascade-v02"
],{stdio:"ignore",windowsHide:true});
let ws,seq=0;const pending=new Map();
function send(method,params={}){
  const id=++seq;return new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>{pending.delete(id);reject(Error("CDP timeout: "+method));},10000);
    pending.set(id,{resolve:v=>{clearTimeout(timer);resolve(v);},reject:e=>{clearTimeout(timer);reject(e);}});
    ws.send(JSON.stringify({id,method,params}));
  });
}
async function evalJS(expression){
  const ret=await send("Runtime.evaluate",{expression,returnByValue:true,awaitPromise:true});
  if(ret.exceptionDetails)throw Error("JS: "+JSON.stringify(ret.exceptionDetails).slice(0,450));
  return ret.result.value;
}
async function until(fn,timeout=16000){
  const start=Date.now();
  while(Date.now()-start<timeout){try{const v=await fn();if(v)return v;}catch(e){}await sleep(250);}
  throw Error("Timeout waiting for scenario browser");
}
const get=()=>evalJS("(()=>{const value=(i)=>document.querySelector('#c2-kpis .nr-kpi:nth-child('+i+') strong')?.innerText;return {pool:value(1),supply:value(2),returnT:value(3),Qpool:value(4),Qdh:value(5),poolOn:document.querySelector('#c2-pool').value,dhOn:document.querySelector('#c2-dh').value,techCount:document.querySelectorAll('#c2-tech div').length,technical:document.querySelector('#c2-tech').innerText,notice:document.querySelector('#c2-status').innerText};})()");
const click=name=>evalJS("(()=>{document.querySelector('[data-preset=\""+name+"\"]').click();return true})()");
const number=s=>Number(s.replace(/[^0-9,.-]/g,"").replaceAll(" ","").replace(",","."));
try{
  const port=await until(async()=>{
    const data=await readFile(path.join(profile,"DevToolsActivePort"),"utf8");
    const p=Number(data.split(/\r?\n/)[0]);return p>0?p:null;
  });
  const target=await until(async()=>{
    const r=await fetch("http://127.0.0.1:"+port+"/json/list");
    return (await r.json()).find(t=>t.type==="page")?.webSocketDebuggerUrl;
  });
  ws=new WebSocket(target);ws.addEventListener("message",event=>{
    const msg=JSON.parse(String(event.data)),entry=pending.get(msg.id);
    if(!entry)return;pending.delete(msg.id);
    if(msg.error)entry.reject(Error(msg.error.message));else entry.resolve(msg.result);
  });
  await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
  await send("Runtime.enable");await send("Page.enable");
  await until(()=>evalJS("document.querySelectorAll('#c2-tech div').length >= 30 && document.querySelectorAll('#c2-case option').length===8"));
  await evalJS("(()=>{const e=document.querySelector('#c2-time');e.value='320';e.dispatchEvent(new Event('input',{bubbles:true}));return true})()");
  const baseline=await get();
  assert(baseline.techCount>=30&&baseline.notice.includes("D_DERIVED"));
  console.log("BASE_PASS",baseline.pool,baseline.supply);
  await click("pool");const pool=await get();
  assert.equal(pool.poolOn,"0");assert.equal(pool.dhOn,"1");assert(number(pool.Qpool)===0);
  assert.equal(pool.Qdh,baseline.Qdh);assert.notEqual(pool.pool,baseline.pool);
  const schemePool=await evalJS("(()=>({pool:document.querySelector('#svg-pool-power')?.textContent,temp:document.querySelector('#svg-pool')?.textContent,mode:document.querySelector('#c2-svg-pool-state')?.textContent,marker:document.querySelector('#c2-svg-pool-state')?.style.display,pipePool:document.querySelector('#pipe-pool')?.classList.contains('c2-flow-off'),pipeHX:document.querySelector('#pipe-hx')?.classList.contains('c2-flow-off'),dh:document.querySelector('#svg-dh')?.textContent,banner:document.querySelector('#c2-main-banner')?.textContent,derived:document.querySelector('#kpi-detail-1')?.textContent}))()");
  assert.equal(number(schemePool.pool),0,"Main synoptic MUST show zero pool heat");
  assert(schemePool.mode==="БАССЕЙН OFF" && schemePool.marker!=="none");
  assert(schemePool.pipePool && schemePool.pipeHX,"Pool pipes must be disabled on schematic");
  assert(schemePool.banner.includes("D_DERIVED") && schemePool.derived.includes("D_DERIVED"),"Data provenance absent");
  assert(number(schemePool.dh)>0,"DH remains active in pool OFF scenario");
  assert(Math.abs(number(schemePool.temp)-number(pool.pool))<0.06,"Main synoptic pool temperature is stale");
  await sleep(1200);
  assert.equal(number(await evalJS("document.querySelector('#svg-pool-power').textContent")),0,"Native refresh overwrote what-if overlay");
  const poolImage=await send("Page.captureScreenshot",{format:"png",captureBeyondViewport:true});
  await writeFile(path.join(root,"runtime","QA_CASCADE_SYNOPTIC_POOL_OFF_20261023.png"),Buffer.from(poolImage.data,"base64"));
  console.log("SYNOPTIC_POOL_OFF_PASS",schemePool.pool,schemePool.temp,schemePool.mode);
  console.log("POOL_OFF_PASS",pool.pool);
  await click("dh");const dh=await get();
  assert.equal(dh.dhOn,"0");assert(number(dh.Qdh)===0);
  assert.equal(dh.supply,dh.returnT);assert.equal(dh.pool,baseline.pool);
  const schemeDH=await evalJS("(()=>({power:document.querySelector('#svg-dh').textContent,pipe:document.querySelector('#pipe-dh').classList.contains('c2-flow-off'),marker:document.querySelector('#c2-svg-dh-state').textContent,visible:document.querySelector('#c2-svg-dh-state').style.display,pool:document.querySelector('#svg-pool-power').textContent}))()");
  assert.equal(number(schemeDH.power),0,"Main synoptic DH power must be zero");
  assert(schemeDH.pipe && schemeDH.marker==="OFF" && schemeDH.visible!=="none","DH flow still shown as ON");
  assert(number(schemeDH.pool)>0,"Pool must remain supplied when DH is OFF");
  console.log("SYNOPTIC_DH_OFF_PASS",schemeDH.power);
  console.log("DH_OFF_PASS",dh.supply);
  await click("both");const both=await get();
  assert(number(both.Qdh)===0&&number(both.Qpool)===0);
  console.log("BOTH_OFF_PASS");
  await click("hp");const hp=await get();
  assert(number(hp.Qpool)<number(baseline.Qpool));
  console.log("HP_REHEAT_OFF_PASS",hp.Qpool);
  await click("base");
  const reset=await evalJS("(()=>({hidden:document.querySelector('#c2-main-banner').hidden,overlay:document.querySelector('#synoptic').classList.contains('c2-cascade-overlay'),poolClass:document.querySelector('#pipe-pool').classList.contains('c2-flow-off'),dhClass:document.querySelector('#pipe-dh').classList.contains('c2-flow-off'),poolMarker:document.querySelector('#c2-svg-pool-state').style.display}))()");
  assert(reset.hidden && !reset.overlay && !reset.poolClass && !reset.dhClass && reset.poolMarker==="none","Baseline diagram did not restore");
  console.log("SYNOPTIC_BASE_RESTORE_PASS");
  await evalJS("(()=>{for(const [id,val] of [['c2-poolkw','40'],['c2-dhkw','25'],['c2-return','45'],['c2-flow','2']]){const el=document.querySelector('#'+id);el.value=val;el.dispatchEvent(new Event('input',{bubbles:true}));}return true})()");
  const caps=await get();
  assert(caps.technical.includes("40 кВт")&&caps.technical.includes("25 кВт"));
  assert(number(caps.Qpool)<=40.001&&number(caps.Qdh)<=25.001);
  assert(Math.abs(number(caps.supply)-(45+number(caps.Qdh)*1000/(2*4182)))<.011);
  console.log("CAP_AND_TEMPERATURE_PASS",caps.Qpool,caps.Qdh,caps.supply);
  await click("pool");
  await evalJS("(()=>{document.querySelector('#c2-off').value='400';document.querySelector('#c2-off').dispatchEvent(new Event('input',{bubbles:true}));document.querySelector('#c2-time').value='300';document.querySelector('#c2-time').dispatchEvent(new Event('input',{bubbles:true}));return true})()");
  const before=await get(); 
  await click("base");
  await evalJS("(()=>{document.querySelector('#c2-time').value='300';document.querySelector('#c2-time').dispatchEvent(new Event('input',{bubbles:true}));return true})()");
  const baseBefore=await get();
  assert.equal(before.pool,baseBefore.pool);assert.equal(before.Qpool,baseBefore.Qpool);
  await click("pool");
  await evalJS("(()=>{document.querySelector('#c2-time').value='440';document.querySelector('#c2-time').dispatchEvent(new Event('input',{bubbles:true}));return true})()");
  assert(number((await get()).Qpool)===0);
  console.log("DELAYED_CUT_PASS");
  await evalJS("(()=>{document.querySelector('#c2-case').value='oba_REJECT_off_bez_shedding';document.querySelector('#c2-case').dispatchEvent(new Event('change',{bubbles:true}));return true})()");
  await until(()=>evalJS("document.querySelector('#c2-status')?.innerText.includes('D_DERIVED') && document.querySelector('#c2-case').value==='oba_REJECT_off_bez_shedding'"));
  console.log("ALTERNATE_SOURCE_PASS");
  await click("base");
  const pic=await send("Page.captureScreenshot",{format:"png",captureBeyondViewport:true});
  const targetFile=path.join(root,"runtime","QA_CASCADE_V02_20261023.png");
  await writeFile(targetFile,Buffer.from(pic.data,"base64"));
  console.log("CASCADE_V02_BROWSER_PASS screenshot="+targetFile);
}catch(e){console.error("CASCADE_V02_BROWSER_FAIL",e.stack||e.message);process.exitCode=1;}
finally{if(ws)ws.close();chrome.kill();}
