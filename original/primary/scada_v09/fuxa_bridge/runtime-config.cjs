"use strict";
const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto");
const LOCAL_DIR=path.join(__dirname,"runtime");
const FILE=path.join(LOCAL_DIR,"secrets.json");
function loadSecrets(){
 const x=JSON.parse(fs.readFileSync(FILE,"utf8"));
 if(!x.exporter||!x.viewer||x.exporter.password===x.viewer.password)throw Error("Invalid secrets");
 return x;
}
function ensureSecrets(){
 fs.mkdirSync(LOCAL_DIR,{recursive:true});
 if(fs.existsSync(FILE))return loadSecrets();
 const creds={exporter:{username:"dchr_v09_exporter",password:crypto.randomBytes(32).toString("hex")},
 viewer:{username:"dchr_v09_viewer",password:crypto.randomBytes(32).toString("hex")}};
 try{fs.writeFileSync(FILE,JSON.stringify(creds),{flag:"wx",mode:0o600});}
 catch(e){if(e.code!=="EEXIST")throw e}
 return loadSecrets();
}
module.exports={LOCAL_DIR,FILE,loadSecrets,ensureSecrets};
