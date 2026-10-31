"use strict";
const fs=require("node:fs"),mqtt=require("mqtt");
const QUALITY=Object.freeze({source_class:"D_SYNTHETIC",quality:"D",mode:"LOCAL_SIMULATION_ONLY",hardware_enabled:false});
const TAGS=["T_pool_C","Q_DC_eff_W","Q_pool_phys_W","P_HP_W","COP",
 "Q_reject_main_W","Q_reject_backup_W","T_IT_model_C","safety_latch","Q_unhandled_W"];
const PREFIX="dchr/v09/sim";
function validateSourceUrl(raw){
 const u=new URL(raw);
 if(u.protocol!=="http:"|| !["127.0.0.1","localhost","[::1]"].includes(u.hostname)
    ||u.username||u.password||u.search||u.hash||u.pathname!=="/api/snapshot" || !u.port)throw Error("Only local exact snapshot URI accepted");
 return u;
}
function validateSnapshot(value,{now=Date.now(),staleMs=5000}={}){
 if(!value||typeof value!=="object")throw Error("Bad response");
 const m=value.metadata||{},s=value.status||{},v=value.values||{};
 if(m.source_class!==QUALITY.source_class||m.quality!=="D"||m.mode!==QUALITY.mode||m.hardware_enabled!==false)throw Error("Wrong provenance");
 if(typeof s.scenario_id!=="string"||!Number.isInteger(s.index)||typeof s.playing!=="boolean"||s.stopped!==false)throw Error("Unsafe or incomplete status");
 if(typeof value.source_file!=="string"||value.source_file.length>180||! /^[a-zA-Z0-9_.-]+\.csv$/.test(value.source_file))throw Error("Bad source filename");
 if(typeof value.source_sha256!=="string"|| !/^[0-9a-f]{64}$/i.test(value.source_sha256))throw Error("No source SHA");
 const observed=Date.parse(value.observed_at||s.server_time||"");
 if(!Number.isFinite(observed)||observed>now+staleMs||now-observed>staleMs)throw Error("Stale source observation");
 const vals={};
 for(const tag of TAGS){
  if(typeof v[tag]!=="number"||!Number.isFinite(v[tag]))throw Error("Missing or nonfinite "+tag);
  vals[tag]=v[tag];
 }
 if(!Number.isFinite(value.sample_timestamp_s))throw Error("Bad model timestamp");
 return {metadata:{...QUALITY},status:{
  scenario_id:s.scenario_id,index:s.index,playing:s.playing,stopped:false,
  simulation_time_h:Number(s.simulation_time_h)||0
 },values:vals,sample_timestamp_s:value.sample_timestamp_s,
 source_file:value.source_file,source_sha256:value.source_sha256,
 observed_at:new Date(observed).toISOString()};
}
function createPublisher({credentials,brokerUrl="mqtt://127.0.0.1:18883",
 sourceUrl="http://127.0.0.1:8091/api/snapshot",stopFile,
 intervalMs=1000,staleMs=5000,requestTimeoutMs=3500}={}){
 validateSourceUrl(sourceUrl);
 const mqttUrl=new URL(brokerUrl);
 if(mqttUrl.protocol!=="mqtt:"||!["127.0.0.1","localhost"].includes(mqttUrl.hostname)||!mqttUrl.port||mqttUrl.username||mqttUrl.password||mqttUrl.search||mqttUrl.hash)throw Error("Only local MQTT");
 if(!credentials?.exporter?.username||!credentials.exporter.password)throw Error("Missing exporter credentials");
 let client,timer,working=false,seq=0,lastState="idle",lastFingerprint="";
 const state={get state(){return lastState}};
 const stopped=()=>!!stopFile&&fs.existsSync(stopFile);
 function publish(topic,payload,retain=true){
  return new Promise((resolve,reject)=>{
   if(!client||!client.connected)return reject(Error("No MQTT connection"));
   client.publish(PREFIX+"/"+topic,payload,{qos:1,retain},e=>e?reject(e):resolve());
  });
 }
 async function clearValues(){
  for(const tag of TAGS)await publish("value/"+tag,"",true);
 }
 async function metadata(status,snapshot=null){
  const packet_seq=++seq;
  const body={...QUALITY,source:"D",state:status,packet_seq,packet_id:"dchr:"+packet_seq,
   checked_at_unix:Date.now()/1000};
  if(snapshot)body.snapshot=snapshot;
  await publish("meta",JSON.stringify(body),true);
 }
 async function fail(stateName){
  if(!client?.connected)return;
  try{await clearValues();await metadata(stateName)}catch{}
 }
 async function poll(){
  if(working||lastState==="stopped")return;
  if(stopped()){await api.stop("STOP");return}
  working=true;
  try{
   const ac=new AbortController(),timeout=setTimeout(()=>ac.abort(),requestTimeoutMs);
   let reply;
   try{reply=await fetch(sourceUrl,{method:"GET",redirect:"manual",signal:ac.signal,cache:"no-store"})}
   finally{clearTimeout(timeout)}
   if(reply.status!==200)throw Error("Source HTTP not 200");
   const text=await reply.text();
   if(Buffer.byteLength(text)>524288)throw Error("Oversized data");
   const validated=validateSnapshot(JSON.parse(text),{staleMs});
   if(stopped()){working=false;await api.stop("STOP");return}
   const fingerprint=JSON.stringify([validated.status.scenario_id,validated.status.index,
                                     validated.source_sha256,validated.values]);
   if(lastState!=="online" || fingerprint!==lastFingerprint){
     for(const [key,value] of Object.entries(validated.values)){
       await publish("value/"+key,String(value));
     }
   }
   lastFingerprint=fingerprint;
   await metadata("online",validated);
   lastState="online";
  }catch(e){
   if(lastState!=="stopped" && lastState!=="stale"){
     await fail("stale");lastState="stale";lastFingerprint="";
   }
  }finally{working=false}
 }
 const api={state:"idle",async start(){
   if(stopped()){lastState="stopped";return api}
   if(client)throw Error("Already started");
   client=mqtt.connect(brokerUrl,{username:credentials.exporter.username,
     password:credentials.exporter.password,reconnectPeriod:0,clean:true,
     clientId:"dchr-publisher-"+require("node:crypto").randomBytes(6).toString("hex")});
   await new Promise((resolve,reject)=>{
     client.once("connect",resolve);client.once("error",reject);
   });
   lastState="starting";timer=setInterval(()=>{void poll()},intervalMs);
   await poll();return api;
  },async stop(reason="manual"){
   if(lastState==="stopped")return;
   clearInterval(timer);
   if(client?.connected)await fail("offline");
   lastState="stopped";
   if(client)await new Promise(resolve=>client.end(false,resolve));
  }};
 Object.defineProperty(api,"state",{get:()=>lastState});
 return api;
}
module.exports={TAGS,QUALITY,validateSourceUrl,validateSnapshot,createPublisher};
