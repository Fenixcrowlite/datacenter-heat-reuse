"use strict";
// Private low-footprint MQTT runtime for D_SYNTHETIC SCADA v09. No PLC commands.
const fs=require("node:fs"),path=require("node:path");
const {createBroker}=require("./broker.cjs");
const {createPublisher}=require("./publisher.cjs");
const {ensureSecrets}=require("./runtime-config.cjs");
const ROOT=path.resolve(__dirname,"..");
const STOP=[path.join(ROOT,"STOP"),path.join(__dirname,"STOP")];
const port=18883;
let runtime,timer,closing=false;
function hasStop(){return STOP.some(p=>fs.existsSync(p))}
async function shutdown(reason){
 if(closing)return;closing=true;clearInterval(timer);
 console.log("MQTT_SHUTDOWN "+reason);
 try{if(runtime?.publisher)await runtime.publisher.stop(reason)}catch(e){console.error("PUBLISHER_STOP_ERROR "+e.name)}
 try{if(runtime?.broker)await runtime.broker.close()}catch(e){console.error("BROKER_STOP_ERROR "+e.name)}
 process.exitCode=0;
}
async function main(){
 if(hasStop())throw Error("STOP active");
 const credentials=ensureSecrets();
 const broker=await createBroker({credentials,host:"127.0.0.1",port,stopFile:STOP[0]});
 runtime={broker};
 const publisher=createPublisher({credentials,brokerUrl:"mqtt://127.0.0.1:"+port,
   sourceUrl:"http://127.0.0.1:8091/api/snapshot",stopFile:STOP[0],
   intervalMs:1000,staleMs:7000,requestTimeoutMs:3000});
 runtime.publisher=publisher;
 await publisher.start();
 if(hasStop()){await shutdown("STOP");return}
 console.log("MQTT_READY 127.0.0.1:"+port+" mode="+publisher.state+" quality=D_SYNTHETIC no hardware");
 timer=setInterval(()=>{if(hasStop()){void shutdown("STOP")}},600);
 for(const sig of ["SIGINT","SIGTERM"])process.on(sig,()=>{void shutdown(sig)});
}
main().catch(async e=>{console.error("MQTT_START_FAILED "+e.message);await shutdown("startup failure");process.exitCode=1});
