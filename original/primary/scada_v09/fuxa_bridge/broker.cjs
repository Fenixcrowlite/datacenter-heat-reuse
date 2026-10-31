"use strict";
const fs=require("node:fs"), path=require("node:path"),crypto=require("node:crypto"),http=require("node:http");
const net=require("node:net"),aedesFactory=opts=>require("aedes").Aedes.createBroker(opts),mqtt=require("mqtt");
const ROOT=path.resolve(__dirname,".."),DIR=__dirname,LOCAL=path.join(DIR,"runtime");
const SECRETS=path.join(LOCAL,"broker_secrets.json"),STOP=path.join(DIR,"STOP"),ROOT_STOP=path.join(ROOT,"STOP");
const HOST="127.0.0.1",PORT=18883;
const QUAL=Object.freeze({source_class:"D_SYNTHETIC",quality:"D",mode:"LOCAL_SIMULATION_ONLY",hardware_enabled:false});
const ALLOW=/^dchr\/v09\/sim\/(?:value\/[a-zA-Z0-9_]+|meta|status|snapshot)$/;
const EDITOR_ONLY_WRITE= /^dchr\/v09\/sim\//;
function refuseStop(){if(fs.existsSync(STOP)||fs.existsSync(ROOT_STOP))throw Error("STOP active, broker and replay disabled");}
function secrets(){
 fs.mkdirSync(LOCAL,{recursive:true});
 if(fs.existsSync(SECRETS))return JSON.parse(fs.readFileSync(SECRETS,"utf8"));
 const credentials={exporter:crypto.randomBytes(32).toString("hex"),viewer:crypto.randomBytes(32).toString("hex")};
 fs.writeFileSync(SECRETS,JSON.stringify(credentials),{encoding:"utf8",mode:0o600,flag:"wx"});
 return credentials;
}
function secureEqual(a,b){const x=Buffer.from(String(a||"")),y=Buffer.from(String(b||""));return x.length===y.length&&crypto.timingSafeEqual(x,y);}
function authorize(role,kind,topic){
 if(typeof topic!=="string" || !(ALLOW.test(topic) || (kind==="subscribe" && topic==="dchr/v09/sim/#")))return false;
 if(kind==="publish")return role==="exporter"&&EDITOR_ONLY_WRITE.test(topic);
 if(kind==="subscribe")return role==="viewer";
 return false;
}
async function protect(){
 const expected=require("./runtime-config.cjs").ensureSecrets(),broker=await aedesFactory({id:"dchr-v09-local-broker"});
 const tcp=net.createServer(broker.handle);
 broker.authenticate=(client,username,password,done)=>{
  const pw=Buffer.isBuffer(password)?password.toString("utf8"):String(password||"");
  const user=Buffer.isBuffer(username)?username.toString("utf8"):String(username||"");
  const role=user===expected.exporter.username?"exporter":user===expected.viewer.username?"viewer":null;
  if(!role || !secureEqual(pw,expected[role].password))return done(Error("Auth denied"),false);
  client.scadaRole=role;done(null,true);
 };
 broker.authorizePublish=(client,pkt,done)=>{
  if(!client || !authorize(client.scadaRole,"publish",pkt.topic))return done(Error("Publish denied"));
  done(null);
 };
 broker.authorizeSubscribe=(client,sub,done)=>{
  if(!client || !authorize(client.scadaRole,"subscribe",sub.topic))return done(Error("Subscribe denied"));
  done(null,sub);
 };
 return {broker,tcp,expected};
}
function fetchSnapshot(){
 return new Promise(async(resolve,reject)=>{
  try{
   const ac=new AbortController();const timeout=setTimeout(()=>ac.abort(),3500);
   try{
    const resp=await fetch("http://127.0.0.1:8091/api/snapshot",{signal:ac.signal,redirect:"error"});
    if(!resp.ok)throw Error("API "+resp.status);
    const data=await resp.json();
    const m=data.metadata||{};
    if(m.source_class!=="D_SYNTHETIC"||m.quality!=="D"||m.hardware_enabled!==false||m.mode!=="LOCAL_SIMULATION_ONLY")throw Error("Source quality invalid");
    resolve(data);
   }finally{clearTimeout(timeout);}
  }catch(e){reject(e);}
 });
}
async function start(){
 refuseStop();
 const {broker,tcp,expected}=await protect();
 let publisher,alive=true,busy=false,previousIndex="",timer;
 tcp.listen(PORT,HOST,()=>{
  console.log("MQTT_SIM_BROKER_ONLINE host=127.0.0.1 port="+PORT+" quality=D_SYNTHETIC");
  publisher=mqtt.connect("mqtt://127.0.0.1:"+PORT,{clientId:"dchr-v09-exporter-"+process.pid,
   username:expected.exporter.username,password:expected.exporter.password,clean:true,reconnectPeriod:1000,
   will:{topic:"dchr/v09/sim/status",payload:JSON.stringify({...QUAL,state:"offline",reason:"unexpected publisher disconnect"}),qos:1,retain:true}});
  publisher.on("connect",()=>{publisher.publish("dchr/v09/sim/meta",JSON.stringify({...QUAL,interval_ms:1000}),{qos:1,retain:true});
   publisher.publish("dchr/v09/sim/status",JSON.stringify({...QUAL,state:"online"}),{qos:1,retain:true});});
  publisher.on("error",()=>{}); // Do not leak credential-bearing network errors.
  timer=setInterval(async()=>{
   if(busy||!alive)return;
   if(fs.existsSync(STOP)||fs.existsSync(ROOT_STOP)){shutdown();return;}
   if(!publisher?.connected)return;
   busy=true;
   try{
    const s=await fetchSnapshot(),v=s.values||{},status=s.status||{};
    const index=status.scenario_id+":"+status.index;
    if(index!==previousIndex){
     previousIndex=index;
     for(const [k,val] of Object.entries(v)){
      if(/^[a-zA-Z0-9_]+$/.test(k)&&typeof val==="number"&&Number.isFinite(val)){
       publisher.publish("dchr/v09/sim/value/"+k,String(val),{qos:1,retain:true});
      }
     }
    }
    // Always refresh liveness; even when simulation is paused.
    publisher.publish("dchr/v09/sim/status",JSON.stringify({...QUAL,state:"online",scenario_id:status.scenario_id,
      index:status.index,playing:status.playing,stopped:status.stopped,checked_at_unix:Date.now()/1000}),{qos:1,retain:true});
    publisher.publish("dchr/v09/sim/snapshot",JSON.stringify({metadata:QUAL,status:{
       scenario_id:status.scenario_id,index:status.index,playing:status.playing,stopped:status.stopped},
      values:v,checked_at_unix:Date.now()/1000}),{qos:1,retain:false});
   }catch(e){
    publisher.publish("dchr/v09/sim/status",JSON.stringify({...QUAL,state:"stale",reason:"API unavailable",
      checked_at_unix:Date.now()/1000}),{qos:1,retain:true});
   }finally{busy=false;}
  },1000);
 });
 const shutdown=()=>{
  if(!alive)return;alive=false;clearInterval(timer);
  if(publisher?.connected){publisher.publish("dchr/v09/sim/status",JSON.stringify({...QUAL,state:"offline",reason:"publisher stopped"}),{retain:true,qos:1},()=>publisher.end(true));}
  else publisher?.end(true);
  tcp.close();broker.close();setTimeout(()=>process.exit(0),350).unref();
 };
 for(const sig of ["SIGINT","SIGTERM"])process.on(sig,shutdown);
 process.on("uncaughtException",e=>{console.error("MQTT broker fatal:",e.name);shutdown();});
 return {tcp,broker};
}
async function createBroker({credentials,host="127.0.0.1",port=0,stopFile}={}){
 if(host!=="127.0.0.1"||!Number.isInteger(port)||port<0||port>65535)throw Error("Loopback only");
 if(stopFile&&fs.existsSync(stopFile))throw Error("STOP active");
 if(!credentials?.exporter||!credentials?.viewer)throw Error("Credentials required");
 const aedes=await aedesFactory({id:"dchr-isolated-"+crypto.randomBytes(5).toString("hex")});
 const tcp=net.createServer(aedes.handle);
 aedes.authenticate=(client,user,pass,cb)=>{
  const value=Buffer.isBuffer(pass)?pass.toString():String(pass||"");
  const login=Buffer.isBuffer(user)?user.toString():String(user||"");
  const role=login===credentials.exporter.username?"exporter":login===credentials.viewer.username?"viewer":null;
  if(!role||!secureEqual(value,credentials[role].password))return cb(Error("Auth denied"),false);
  client.scadaRole=role;cb(null,true);
 };
 aedes.authorizePublish=(client,pkt,cb)=>{
  if(!authorize(client?.scadaRole,"publish",pkt.topic))return cb(Error("Publish denied"));
  cb(null);
 };
 aedes.authorizeSubscribe=(client,sub,cb)=>{
  if(!authorize(client?.scadaRole,"subscribe",sub.topic))return cb(Error("Subscribe denied"));
  cb(null,sub);
 };
 try{await new Promise((resolve,reject)=>{
  tcp.once("error",reject);tcp.listen(port,host,()=>{tcp.removeListener("error",reject);resolve()});
 });}catch(e){aedes.close();throw e}
 return {address:()=>tcp.address(),close:async()=>{await new Promise(resolve=>tcp.close(resolve));await new Promise(resolve=>aedes.close(resolve));},server:tcp,aedes};
}
if(require.main===module)start().catch(e=>{console.error("MQTT_START_FAILED",e.name);process.exitCode=1});
module.exports={QUAL,ALLOW,authorize,secrets,protect,fetchSnapshot,start,createBroker};
