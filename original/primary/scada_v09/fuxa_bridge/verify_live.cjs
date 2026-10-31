"use strict";
const mqtt=require("mqtt"),{ensureSecrets}=require("./runtime-config.cjs"),{TAGS}=require("./publisher.cjs");
async function check(){
 const creds=ensureSecrets();
 const source=await (await fetch("http://127.0.0.1:8091/api/snapshot")).json();
 if(source.metadata.source_class!=="D_SYNTHETIC")throw Error("Upstream is not D");
 const reader=mqtt.connect("mqtt://127.0.0.1:18883",
  {username:creds.viewer.username,password:creds.viewer.password,reconnectPeriod:0,protocolVersion:4});
 const values=new Map();let metadata=null;
 reader.on("message",(topic,buffer)=>{
  if(topic==="dchr/v09/sim/meta"){try{metadata=JSON.parse(buffer.toString())}catch{}}
  if(topic.startsWith("dchr/v09/sim/value/"))values.set(topic.split("/").at(-1),buffer.toString());
 });
 await new Promise((resolve,reject)=>{reader.once("connect",resolve);reader.once("error",reject)});
 await new Promise((resolve,reject)=>reader.subscribe("dchr/v09/sim/#",{qos:1},e=>e?reject(e):resolve()));
 const timeout=Date.now()+5000;
 while(Date.now()<timeout && !(metadata?.state==="online" && TAGS.every(t=>values.has(t)))){
   await new Promise(r=>setTimeout(r,100));
 }
 if(metadata?.state!=="online" || metadata.source_class!=="D_SYNTHETIC" || metadata.hardware_enabled!==false)throw Error("Invalid metadata");
 if(TAGS.some(t=>!values.has(t)||!Number.isFinite(Number(values.get(t)))))throw Error("Missing MQTT tag");
 const now=await (await fetch("http://127.0.0.1:8091/api/snapshot")).json();
 const diff=Math.abs(+values.get("T_pool_C")-now.values.T_pool_C);
 if(diff>0.001)throw Error("MQTT does not match source T_pool_C");
 console.log(JSON.stringify({status:"MQTT_LIVE_E2E_PASS",tags:TAGS.length,source:"D_SYNTHETIC",
  sample_index:now.status.index,T_pool_C:+values.get("T_pool_C"),difference_C:diff,
  plc_control:false}));
 await new Promise(resolve=>reader.end(false,resolve));
}
check().catch(e=>{console.error("MQTT_LIVE_E2E_FAIL",e.message);process.exitCode=1});
