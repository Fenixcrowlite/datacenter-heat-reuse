"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const source = fs.readFileSync(path.join(__dirname,"source_compare.js"),"utf8");
const html = fs.readFileSync(path.join(__dirname,"dashboard.html"),"utf8");
const endpoint = "http://127.0.0.1:8094";
const ids = ["sc-source","sc-refresh","sc-provenance","sc-error","sc-pool-temp",
  "sc-pool-power","sc-dh-power","sc-reject-power","sc-temp-chart","sc-temp-note",
  "sc-power-chart","sc-index","sc-clock","sc-total","sc-diagnostics","sc-table-body"];
const context2d = {
  clearRect(){},fillRect(){},beginPath(){},moveTo(){},lineTo(){},stroke(){},
  fillText(){},measureText(s){return {width:String(s).length * 7}}
};
const nodes = new Map();
function element(id){
  if(!nodes.has(id)) nodes.set(id,{
    id,style:{},textContent:"",value:id==="sc-source"?"v04":"0",
    width:950,height:225,children:[],listeners:{},
    getContext(){return context2d},
    addEventListener(type,listener){this.listeners[type]=listener},
    replaceChildren(){this.children=[]},
    appendChild(child){this.children.push(child)}
  });
  return nodes.get(id);
}
const calls = [];
async function api(url,opts) {
  assert(url.startsWith("/api/"));
  calls.push(url);
  return fetch(endpoint+url,opts);
}
async function waitFor(fn,seconds=10){
  const until=Date.now()+seconds*1000;
  while(Date.now()<until) {
    if(fn()) return;
    await new Promise(resolve=>setTimeout(resolve,120));
  }
  throw Error("UI did not initialize in time");
}
(async()=>{
  ids.forEach(element);
  for(const id of ids) assert(html.includes('id="'+id+'"'),"missing HTML id "+id);
  assert(html.includes('src="/source_compare.js"'));
  const base=await fetch(endpoint+"/api/archive").then(r=>r.json());
  assert.equal(base.rows.length,672);
  assert.equal(base.metadata.source_class,"D_SYNTHETIC");
  assert.equal(Object.prototype.hasOwnProperty.call(base,"csrf_token"),false);
  const live=await fetch(endpoint+"/api/result").then(r=>r.json());
  assert.equal(live.rows.length,672);
  assert.equal(live.metadata.derived_quality,"D_DERIVED");

  const document={
    getElementById:element,
    createElement(name){
      return {name,style:{},textContent:"",children:[],
        appendChild(child){this.children.push(child)}};
    }
  };
  vm.runInNewContext(source,{document,fetch:api,console},{timeout:4000});
  await waitFor(()=>element("sc-provenance").textContent.startsWith("SOURCE=v04"));
  assert.equal(Number(element("sc-pool-temp").textContent),Number(live.rows[0].T_pool_C.toFixed(2)));
  assert.equal(Number(element("sc-pool-power").textContent),
    Number((live.rows[0].Q_pool_W/1000).toFixed(2)));
  assert.match(element("sc-diagnostics").textContent,/v04:/);
  const job=live.id;
  assert(element("sc-provenance").textContent.includes(job));

  element("sc-source").value="v08";
  await element("sc-source").listeners.change();
  assert.match(element("sc-provenance").textContent,/SOURCE=v08/);
  assert.equal(Number(element("sc-pool-temp").textContent),
    Number(base.rows[base.scenario_index].values.T_pool_C.toFixed(2)));
  assert.match(element("sc-diagnostics").textContent,/v08:/);
  assert(!element("sc-provenance").textContent.includes(job),"v04 job leaked into v08");
  assert.match(element("sc-temp-note").textContent,/нет проверенной температуры подачи/);
  assert(element("sc-table-body").children.length>0);
  element("sc-index").value="80";
  element("sc-index").listeners.input();
  assert.equal(Number(element("sc-pool-temp").textContent),
    Number(base.rows[80].values.T_pool_C.toFixed(2)));
  const result = {
    status:"PASS",mode_switches:["v04","v08"],archive_rows:base.rows.length,
    matlab_rows:live.rows.length,distinct_provenance:true,csrf_exposed:false,
    v08_sample_80_C:base.rows[80].values.T_pool_C,v04_sample_0_C:live.rows[0].T_pool_C,
    qa:"Real HTTP + browser-script DOM/canvas harness. No real browser screenshot.",
    calls
  };
  const dest=path.join(__dirname,"runtime","QA_SOURCE_SELECTOR_20261025.json");
  fs.writeFileSync(dest,JSON.stringify(result,null,2));
  console.log(JSON.stringify(result,null,2));
})().catch(e=>{console.error(e.stack);process.exitCode=1});
