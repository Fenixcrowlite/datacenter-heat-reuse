"use strict";
const DATA=JSON.parse(document.getElementById("payload").textContent);
const NS="http://www.w3.org/2000/svg";
const colors=["#60a5fa","#f59e0b","#34d399"];
function elem(tag,attrs){const e=document.createElementNS(NS,tag);for(const [k,v] of Object.entries(attrs||{}))e.setAttribute(k,String(v));return e;}
function fmt(x,d=3){return Number(x).toLocaleString("sk-SK",{maximumFractionDigits:d,minimumFractionDigits:d});}
function card(label,val,unit){const e=document.createElement("div");e.className="card";const s=document.createElement("small");s.textContent=label;const b=document.createElement("strong");b.textContent=fmt(val)+" "+unit;e.append(s,b);return e;}
function chart(id,rows,indices,scale,labels){
 const svg=document.getElementById(id);svg.replaceChildren();const W=1100,H=225,L=66,R=16,T=16,B=34;
 const values=rows.flatMap(r=>indices.map(i=>r[i]*scale));let lo=Math.min(...values),hi=Math.max(...values);
 if(lo===hi){lo-=1;hi+=1;}const pad=(hi-lo)*.07;lo-=pad;hi+=pad;
 const x=i=>L+(W-L-R)*i/(rows.length-1),y=v=>H-B-(v-lo)/(hi-lo)*(H-T-B);
 svg.setAttribute("viewBox","0 0 "+W+" "+H);
 for(let i=0;i<5;i++){const v=lo+(hi-lo)*i/4;const yy=y(v);
 svg.append(elem("line",{x1:L,y1:yy,x2:W-R,y2:yy,stroke:"#34435a","stroke-width":1}));
 const t=elem("text",{x:5,y:yy+4,fill:"#b6c5d8","font-size":14});t.textContent=fmt(v,1);svg.append(t);}
 for(let i=0;i<=4;i++){const t=elem("text",{x:x((rows.length-1)*i/4),y:H-8,fill:"#b6c5d8","font-size":14,"text-anchor":"middle"});t.textContent=fmt(rows[rows.length-1][0]/3600*i/4,1)+"h";svg.append(t);}
 indices.forEach((idx,j)=>{const pts=rows.map((r,i)=>x(i).toFixed(2)+","+y(r[idx]*scale).toFixed(2)).join(" ");svg.append(elem("polyline",{points:pts,fill:"none",stroke:colors[j],"stroke-width":2.3,"vector-effect":"non-scaling-stroke"}));});
 if(lo<0&&hi>0)svg.append(elem("line",{x1:L,y1:y(0),x2:W-R,y2:y(0),stroke:"#e5e7eb","stroke-dasharray":"6 5",opacity:.7}));
 const cursor=elem("line",{x1:L,y1:T,x2:L,y2:H-B,stroke:"#fff","stroke-dasharray":"3 4",opacity:0});svg.append(cursor);
 svg.addEventListener("pointermove",ev=>{const rect=svg.getBoundingClientRect();const pos=(ev.clientX-rect.left)/rect.width*W;const i=Math.max(0,Math.min(rows.length-1,Math.round((pos-L)/(W-L-R)*(rows.length-1))));cursor.setAttribute("x1",x(i));cursor.setAttribute("x2",x(i));cursor.setAttribute("opacity",1);document.getElementById("hover").textContent="t="+fmt(rows[i][0]/3600,2)+" h | "+labels.map((name,j)=>name+": "+fmt(rows[i][indices[j]]*scale,3)).join(" | ");});
 svg.addEventListener("pointerleave",()=>cursor.setAttribute("opacity",0));
}
function render(){const key=document.getElementById("scenario").value,m=DATA.metrics[key],r=DATA.series[key].rows;
 const cards=document.getElementById("cards");cards.replaceChildren(
 card("Teplo do bazéna",m.input_MWh,"MWh"),card("Podpísané straty",m.signed_loss_MWh,"MWh"),
 card("Akumulovaná energia",m.stored_MWh,"MWh"),card("Zisk z okolia",m.ambient_gain_MWh,"MWh"),
 card("Konečná teplota",m.final_temperature_C,"°C"),card("Max. rezíduum",m.max_residual_W,"W"));
 document.getElementById("status").textContent=m.negative_loss_rows+" intervalov so ziskom z okolia";
 chart("temp",r,[1],1,["T_pool °C"]);chart("flows",r,[2,3,4],.001,["Q_pool kW","Q_loss kW","Q_net kW"]);
 chart("energy",r,[5,6,7],1/3600000000,["Vstup MWh","Straty MWh","Akumulácia MWh"]);
 document.getElementById("provenance").textContent="CSV SHA256: "+m.source_csv_sha256+" | uzáver bilancie: "+fmt(m.closure_J,7)+" J | source_kind=derived_simulation | physical_release=false";
}
document.getElementById("scenario").addEventListener("change",render);render();
