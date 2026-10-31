/* DCHR CASCADE V02, browser-only D_DERIVED sensitivity study, never controls PLC. */
(() => {
  "use strict";
  const host = document.querySelector(".playback-panel");
  if (!host || document.getElementById("cascade-v02")) return;
  const root = document.createElement("section");
  root.className="panel nr-panel";root.id="cascade-v02";
  root.innerHTML=[
    '<div class="nr-heading"><div><p class="eyebrow">DCHR · CASCADE v02 · D_DERIVED</p><h2>Бассейн и центральная система отопления</h2>',
    '<p>Независимый расчёт чувствительности поверх Simulink v08. Тепловые мощности можно уменьшить, но не увеличить сверх исходной симуляции.</p></div>',
    '<span class="nr-pill">READ ONLY · NO PLC</span></div>',
    '<div class="nr-presets" id="c2-presets"><button type="button" data-preset="base">Исходный режим</button>',
    '<button type="button" data-preset="pool">Выключить бассейн</button>',
    '<button type="button" data-preset="dh">Выключить теплосеть</button>',
    '<button type="button" data-preset="both">Отключить обе ветви</button>',
    '<button type="button" data-preset="hp">Без догрева ТН</button></div>',
    '<div class="nr-controls c2-controls">',
    '<label>Исходный сценарий<select id="c2-case"></select></label>',
    '<label>Бассейн<select id="c2-pool"><option value="1">ВКЛ</option><option value="0">ВЫКЛ</option></select></label>',
    '<label>Центральная теплосеть<select id="c2-dh"><option value="1">ВКЛ</option><option value="0">ВЫКЛ</option></select></label>',
    '<label>Догрев бассейна ТН<select id="c2-hp"><option value="1">ВКЛ</option><option value="0">ВЫКЛ</option></select></label>',
    '<label>Лимит мощности бассейна, кВт<input type="number" id="c2-poolkw" min="0" max="150" step="5" value="150"></label>',
    '<label>Лимит мощности теплосети, кВт<input type="number" id="c2-dhkw" min="0" max="500" step="5" value="500"></label>',
    '<label>Температура обратки, °C (допущение)<input type="number" id="c2-return" min="5" max="90" step="1" value="40"></label>',
    '<label>Расход теплоносителя, кг/с (допущение)<input type="number" id="c2-flow" min="0.1" max="100" step="0.1" value="3"></label>',
    '<label>Применить изменения с <output id="c2-off-label">0,00 ч</output><input type="range" id="c2-off" min="0" max="672" step="1" value="0"></label>',
    '<label>Просмотреть момент <output id="c2-time-label">0,00 ч</output><input type="range" id="c2-time" min="0" max="671" step="1" value="0"></label>',
    '</div>',
    '<div class="nr-actions"><button id="c2-sync" class="secondary-button" type="button">↔ Момент SCADA</button>',
    '<button id="c2-export" class="secondary-button" type="button">↓ Экспорт CSV</button><span id="c2-status" role="status">Загрузка…</span></div>',
    '<div id="c2-kpis" class="nr-kpis"></div>',
    '<div class="c2-graph-grid"><div class="nr-chart-wrap"><h3>Температура бассейна · °C</h3><canvas id="c2-poolplot"></canvas><p>Базовая (янтарная) / сценарная (голубая)</p></div>',
    '<div class="nr-chart-wrap"><h3>Температура подачи ЦО · °C</h3><canvas id="c2-dhplot"></canvas><p>Расчёт по тепловой мощности, температуре обратки и расходу. Без тепловой инерции.</p></div></div>',
    '<details class="nr-tech" open><summary>Полный технический паспорт текущего отсчёта</summary><div id="c2-tech" class="nr-tech-grid"></div></details>',
    '<p class="nr-caveat"><b>Метод и границы:</b> D_SYNTHETIC → D_DERIVED. Исходные мощности считаются верхней границей, свободная энергия в другие ветви НЕ перераспределяется.',
    ' Бассейн: C = 997 × 500 × 4182 Дж/К, шаг 900 с, лимит 27,75 °C, теплопотери по формулам v04.',
    ' Теплосеть: T подачи = T обратки + Q теплосети / (расход × 4182). Обратка и расход задаются вручную, поэтому это не реальные измерения.',
    ' При выключенной теплосети предполагается сохраняющаяся циркуляция без нагрева: T подачи = T обратки.',
    ' Насосы, трубные потери и инерция теплосети не моделируются. COP, электроэнергия, TES, режим Stateflow и показатели IT не пересчитываются.',
    ' Изменения управляют ТОЛЬКО этой расчётной панелью, никогда оборудованием или нативным replay.</p>'
  ].join("");
  host.insertAdjacentElement("afterend",root);
  const nav = document.querySelector(".site-header nav");
  if (nav && !nav.querySelector('a[href="#cascade-v02"]')) {
    const link = document.createElement("a");link.href="#cascade-v02";link.textContent="Каскад";nav.appendChild(link);
  }
  if(location.hash==="#cascade-v02" || location.hash==="#nr-cascade") requestAnimationFrame(()=>root.scrollIntoView({block:"start"}));
  const $=id=>document.getElementById(id);
  const f=(n,d=2)=>typeof n==="number"&&Number.isFinite(n)?n.toLocaleString("ru-RU",{minimumFractionDigits:d,maximumFractionDigits:d}):"—";
  const cp=4182,cap=997*500*4182,dt=900,a=312.5;
  let raw=[],model=[],cases=[],selectedPreset="base";
  const numeric=(id,min,max)=>{const n=Number($(id).value);return Number.isFinite(n)&&n>=min&&n<=max?n:null;};
  function heatLoss(t,b){
    const air=b.T_air_C,rh=Math.max(0,Math.min(1,b.RH)),activity=Math.max(0,b.activity),cover=Math.max(0,Math.min(1,b.cover));
    const pv=.61094*Math.exp(17.625*t/(t+243.04)),pa=rh*.61094*Math.exp(17.625*air/(air+243.04));
    const evapMass=Math.max(0,4e-5*a*(pv-pa)*activity*(1-.9*cover));
    return evapMass*2440000+3*a*(t-air)*(1-.75*cover)+.95*5.670374419e-8*a*((t+273.15)**4-(air-2+273.15)**4)*(1-.75*cover)+800*(t-20)+evapMass*cp*(t-15)+2000;
  }
  function build(){
    if(!raw.length)return;
    const poolKW=numeric("c2-poolkw",0,150),dhKW=numeric("c2-dhkw",0,500);
    const ret=numeric("c2-return",5,90),flow=numeric("c2-flow",.1,100);
    if([poolKW,dhKW,ret,flow].some(v=>v===null)){$("c2-status").textContent="Недопустимые настройки: проверьте диапазон и число";return;}
    const onset=+ $("c2-off").value, poolOn=$("c2-pool").value==="1",dhOn=$("c2-dh").value==="1",hpOn=$("c2-hp").value==="1";
    let temp=16, poolEnergy=0, dhEnergy=0, removedPool=0, removedDH=0;
    model=raw.map((v,i)=>{
      const b=v.values,modified=i>=onset,loss=heatLoss(temp,b);
      const baselinePool=Math.max(0,b.Q_pool_phys_W),baselineDH=Math.max(0,b.Q_DH_W);
      const baseDirect=Math.min(baselinePool,Math.max(0,b.Q_HX_phys_W));
      const modelApproach=Math.max(0,8500*(b.T_DC_C-temp-5));
      const direct=Math.min(baseDirect,modelApproach,150000);
      const baseAvailable=hpOn?baselinePool:direct;
      const allowed=poolOn?Math.min(baseAvailable,poolKW*1000):0;
      const safe=Math.max(0,(27.75-temp)*cap/dt+loss);
      const poolChanged=modified && (!poolOn || !hpOn || poolKW<150);
      const newPool=poolChanged?Math.min(allowed,safe):baselinePool;
      const newDH=modified?(dhOn?Math.min(baselineDH,dhKW*1000):0):baselineDH;
      const newTemp=poolChanged?temp+dt*(newPool-loss)/cap:b.T_pool_C;
      const baseSupply=ret+baselineDH/(flow*cp),newSupply=ret+newDH/(flow*cp);
      poolEnergy+=newPool*dt/3600000;dhEnergy+=newDH*dt/3600000;
      removedPool+=(baselinePool-newPool)*dt/3600000;
      removedDH+=(baselineDH-newDH)*dt/3600000;
      temp=newTemp;
      return {i,time:b.cas_h,b,modified,pool:newPool,dh:newDH,t:newTemp,baseT:b.T_pool_C,loss,
        supply:newSupply,baseSupply,ret,flow,poolEnergy,dhEnergy,removedPool,removedDH,
        direct,available:baseAvailable};
    });
    $("c2-off-label").textContent=f(onset*.25)+" ч";
    render();
  }
  function tile(label,value,unit,sub){
    return '<div class="nr-kpi"><small>'+label+'</small><strong>'+value+' <span>'+unit+'</span></strong><small>'+sub+'</small></div>';
  }
  // CASCADE_SYNOPTIC_SYNC_V03

  // The native SCADA synoptic represents v08 replay. In a modified what-if
  // scenario, make its visual layer explicitly scenario-aware without
  // touching server replay, alarms, historical samples or hardware.
  function visualActive() {
    return $("c2-pool").value!=="1" || $("c2-dh").value!=="1" ||
      $("c2-hp").value!=="1" || Number($("c2-poolkw").value)!==150 ||
      Number($("c2-dhkw").value)!==500 ||
      Number($("c2-return").value)!==40 || Number($("c2-flow").value)!==3;
  }
  const synopticPanel=document.querySelector(".process-panel");
  const synopticBanner=document.createElement("div");
  synopticBanner.id="c2-main-banner";synopticBanner.hidden=true;
  if(synopticPanel) synopticPanel.querySelector(".panel-heading").insertAdjacentElement("afterend",synopticBanner);
  const svg=document.getElementById("synoptic");
  function svgMark(id,x,y,color) {
    const t=document.createElementNS("http://www.w3.org/2000/svg","text");
    t.id=id;t.setAttribute("x",String(x));t.setAttribute("y",String(y));
    t.setAttribute("fill",color);t.setAttribute("font-size","13");
    t.setAttribute("font-weight","700");t.style.display="none";
    svg?.appendChild(t);return t;
  }
  const poolMark=svgMark("c2-svg-pool-state",903,174,"#ffb187");
  const dhMark=svgMark("c2-svg-dh-state",1089,415,"#ffb187");
  const idsToPaint=["svg-dc","svg-dc-flow","svg-hx","svg-hp-source","svg-hp-pool",
    "svg-pool","svg-pool-power","svg-dh","svg-dh-flow","svg-cop","svg-hp-power",
    "svg-tes","svg-tes-flow","svg-reject-a","svg-reject-b","unhandled-label"];
  function syncMain(){
    if(!svg || !model.length)return;
    const active=visualActive();
    if(!active){
      synopticBanner.hidden=true;
      svg.classList.remove("c2-cascade-overlay");
      for(const key of ["pipe-pool","pipe-hx","pipe-dh"])
        document.getElementById(key)?.classList.remove("c2-flow-off");
      svg.querySelectorAll(".c2-source-reference").forEach(line => line.classList.remove("c2-source-reference"));
      document.querySelector('[data-equipment="pool"]')?.classList.remove("c2-equipment-off");
      document.querySelector('[data-equipment="dh"]')?.classList.remove("c2-equipment-off");
      poolMark.style.display="none";dhMark.style.display="none";
      return;
    }
    const ix=Math.min(model.length-1,Number($("c2-time").value)),row=model[ix],b=row.b;
    // Never mix source signals from different scenarios or simulation times:
    // every base reference in the synoptic comes from the same v08 CSV row.
    const usedDirect=row.modified
      ? Math.min(row.pool,row.direct) : Math.max(0,b.Q_HX_phys_W);
    const usedHP=Math.max(0,row.pool-usedDirect);
    const isPoolOff=row.modified&&$("c2-pool").value==="0";
    const isDHOff=row.modified&&$("c2-dh").value==="0";
    const labels={
      "svg-dc":f(b.Q_DC_eff_W/1000,1)+" кВт",
      "svg-dc-flow":f(b.Q_DC_eff_W/1000,1),
      "svg-hx":f(usedDirect/1000,1)+" кВт",
      "svg-hp-source":f(b.Q_HP_source_W/1000,1),
      "svg-hp-pool":f(usedHP/1000,1)+" кВт",
      "svg-pool":f(row.t,1)+" °C",
      "svg-pool-power":f(row.pool/1000,1)+" кВт",
      "svg-dh":f(row.dh/1000,1)+" кВт",
      "svg-dh-flow":f(row.dh/1000,1)+" кВт",
      "svg-cop":"COP "+f(b.COP,2),
      "svg-hp-power":"P_HP "+f(b.P_HP_W/1000,1)+" кВт*",
      "svg-tes":f(b.E_TES_J/3600000,1)+" кВт·ч*",
      "svg-tes-flow":"заряд "+f(b.Q_HP_charge_W/1000,1)+" / разряд "+f(b.Q_TES_discharge_W/1000,1)+" кВт · v08*",
      "svg-reject-a":f(b.Q_reject_main_W/1000,1)+" кВт*",
      "svg-reject-b":f(b.Q_reject_backup_W/1000,1)+" кВт*",
      "unhandled-label":"Q_unhandled "+f(b.Q_unhandled_W/1000,1)+" кВт*"
    };
    for(const id of idsToPaint){
      const node=document.getElementById(id);
      if(node && Object.hasOwn(labels,id))node.textContent=labels[id];
    }
    const kpis=[
      [0,b.Q_DC_eff_W/1000,"D_SYNTHETIC / v08*"],
      [1,row.pool/1000,"D_DERIVED · выбранный каскад"],
      [2,row.t,"D_DERIVED · модель воды"],
      [3,b.T_IT_model_C,"D_SYNTHETIC / модельный IT риск*"],
      [4,b.P_HP_W/1000,"D_SYNTHETIC / электричество не пересчитано*"],
      [5,b.E_TES_J/3600000,"D_SYNTHETIC / TES не пересчитан*"],
      [6,row.dh/1000,"D_DERIVED · выбранный каскад"],
      [7,(b.Q_reject_main_W+b.Q_reject_backup_W)/1000,"D_SYNTHETIC / REJECT не перераспределён*"]
    ];
    for(const [i,val,detail] of kpis){
      const node=document.getElementById("kpi-"+i);
      if(node)node.textContent=f(val,1);
      const d=document.getElementById("kpi-detail-"+i);
      if(d)d.textContent=detail;
    }
    const flowStates={
      "pipe-dc":b.Q_DC_eff_W,
      "pipe-hx":usedDirect,
      "pipe-hp-source":b.Q_HP_source_W,
      "pipe-pool":usedHP,
      "pipe-dh":row.dh,
      "pipe-tes":b.Q_HP_charge_W-b.Q_TES_discharge_W,
      "pipe-reject-a":b.Q_reject_main_W,
      "pipe-reject-b":b.Q_reject_backup_W
    };
    const unchangedReferencePipes = new Set(["pipe-dc","pipe-hp-source","pipe-tes","pipe-reject-a","pipe-reject-b"]);
    for(const [id,value] of Object.entries(flowStates)){
      const line=document.getElementById(id);
      if(!line)continue;
      line.classList.toggle("active",Math.abs(value)>1e-6);
      line.classList.toggle("c2-flow-off",(id==="pipe-hx"||id==="pipe-pool")?isPoolOff:(id==="pipe-dh"?isDHOff:false));
      // Reference-only v08 values are not recomputed by the what-if dispatcher.
      // Keep their magnitude visible but NEVER animate them as scenario flows.
      line.classList.toggle("c2-source-reference",unchangedReferencePipes.has(id));
    }
    document.querySelector('[data-equipment="pool"]')?.classList.toggle("c2-equipment-off",isPoolOff);
    document.querySelector('[data-equipment="dh"]')?.classList.toggle("c2-equipment-off",isDHOff);
    poolMark.style.display=isPoolOff?"":"none";
    poolMark.textContent="БАССЕЙН OFF";
    dhMark.style.display=isDHOff?"":"none";
    dhMark.textContent="OFF";
    svg.classList.add("c2-cascade-overlay");
    synopticBanner.hidden=false;
    const mPool=row.modified?($("c2-pool").value==="0"?"OFF":"ON"):"ПОКА БАЗА";
    const mDh=row.modified?($("c2-dh").value==="0"?"OFF":"ON"):"ПОКА БАЗА";
    synopticBanner.textContent="КАСКАД v02 · WHAT-IF / D_DERIVED · "+
      "Бассейн "+mPool+" · ЦО "+mDh+
      " · t="+f(row.time,2)+" ч · источник "+$("c2-case").value+
      ". * DC, HP, TES, REJECT и IT: исходные v08, без пересчёта, их линии статичны. Тренды, события и историк ниже относятся к replay сервера, НЕ к этому сценарию.";
    const stateflow=document.getElementById("stateflow");
    if(stateflow)stateflow.textContent="WHAT-IF / STATEFLOW v08* "+b.stateflow_mode;
  }
  window.DCHR_CASCADE_SYNC=syncMain;
  window.DCHR_CASCADE_EQUIPMENT=(key)=>{
    if(!model.length || !visualActive() || !["pool","dh","hx","tes"].includes(key))return false;
    const row=model[Math.min(671,Number($("c2-time").value))],b=row.b;
    const labels=key==="pool"?[
      ["Режим бассейна",row.modified?$("c2-pool").value==="0"?"OFF":"ON":"BASE"],
      ["T воды D_DERIVED",f(row.t,3)+" °C"],
      ["T воды v08",f(row.baseT,3)+" °C"],
      ["Мощность нагрева D_DERIVED",f(row.pool/1000,2)+" кВт"],
      ["Потери D_DERIVED",f(row.loss/1000,3)+" кВт"],
      ["Объём модели","500 м³"]
    ]:key==="dh"?[
      ["Режим ЦО",row.modified?$("c2-dh").value==="0"?"OFF":"ON":"BASE"],
      ["T подачи D_DERIVED",f(row.supply,3)+" °C"],
      ["T обратки, допущение",f(row.ret,2)+" °C"],
      ["Массовый расход, допущение",f(row.flow,2)+" кг/с"],
      ["Мощность D_DERIVED",f(row.dh/1000,2)+" кВт"],
      ["Мощность v08",f(b.Q_DH_W/1000,2)+" кВт"]
    ]:[
      ["Прямой HX в сценарии",f((row.modified?Math.min(row.pool,row.direct):b.Q_HX_phys_W)/1000,2)+" кВт"],
      ["Исходный HX v08",f(b.Q_HX_phys_W/1000,2)+" кВт"],
      ["Температура DC v08",f(b.T_DC_C,3)+" °C"]
    ];
    document.getElementById("equipment-title").textContent=key==="pool"?"БАССЕЙН · КАСКАД v02":key==="dh"?"ЦЕНТРАЛЬНАЯ СИСТЕМА · КАСКАД v02":"HX · КАСКАД v02";
    const dl=document.getElementById("equipment-values");dl.replaceChildren();
    for(const [name,value] of labels){
      const div=document.createElement("div"),dt=document.createElement("dt"),dd=document.createElement("dd");
      dt.textContent=name;dd.textContent=value;div.append(dt,dd);dl.append(div);
    }
    document.getElementById("equipment-note").textContent=
      "D_DERIVED, сценарная визуализация. Оригинальные значения Simulink v08 не изменены; приборная телеметрия и управление оборудованием отсутствуют.";
    return true;
  };

  function render(){
    if(!model.length)return;
    const ix=+ $("c2-time").value,v=model[Math.min(model.length-1,ix)],b=v.b;
    $("c2-time-label").textContent=f(v.time)+" ч · "+(v.i+1)+"/672";
    $("c2-kpis").innerHTML=[
      tile("Бассейн · температура",f(v.t,3),"°C","базовая "+f(v.baseT,3)+" °C"),
      tile("ЦО · температура подачи",f(v.supply,2),"°C","базовая "+f(v.baseSupply,2)+" °C"),
      tile("ЦО · температура обратки",f(v.ret,2),"°C","заданная, не датчик"),
      tile("Мощность в бассейн",f(v.pool/1000),"кВт","базовая "+f(b.Q_pool_phys_W/1000)+" кВт"),
      tile("Мощность теплосети",f(v.dh/1000),"кВт","базовая "+f(b.Q_DH_W/1000)+" кВт"),
      tile("Разница T бассейна",f(v.t-v.baseT,3),"К","расчёт относительно Simulink v08"),
      tile("Без распределения: бассейн",f(v.removedPool),"кВт·ч","интеграл недопоставки"),
      tile("Без распределения: ЦО",f(v.removedDH),"кВт·ч","интеграл недопоставки"),
      tile("Тепловая потеря бассейна",f(v.loss/1000),"кВт","знак учитывает притоки")
    ].join("");
    const tech=[
      ["Время и шаг",f(v.time)+" ч / 900 с"],
      ["Бассейн: включён",v.modified?$("c2-pool").value==="1"?"ДА":"НЕТ":"БАЗА"],
      ["Теплосеть: включена",v.modified?$("c2-dh").value==="1"?"ДА":"НЕТ":"БАЗА"],
      ["Догрев HP: включён",v.modified?$("c2-hp").value==="1"?"ДА":"НЕТ":"БАЗА"],
      ["T бассейна, новая",f(v.t,3)+" °C"],["T бассейна, исходная",f(v.baseT,3)+" °C"],
      ["T подачи ЦО, расчёт",f(v.supply,3)+" °C"],
      ["T подачи ЦО, базовый расчёт",f(v.baseSupply,3)+" °C"],
      ["T обратки ЦО, допущение",f(v.ret,2)+" °C"],["Расход ЦО, допущение",f(v.flow,2)+" кг/с"],
      ["ΔT ЦО, расчёт",f(v.supply-v.ret,3)+" K"],
      ["T воздуха (v08)",f(b.T_air_C,2)+" °C"],["T источника DC (v08)",f(b.T_DC_C,2)+" °C"],
      ["Датчик 1 (v08)",f(b.sensor1_C,2)+" °C"],["Датчик 2 (v08)",f(b.sensor2_C,2)+" °C"],
      ["Т риск IT, модель (v08)*",f(b.T_IT_model_C,2)+" °C"],
      ["Q бассейн, расчёт",f(v.pool/1000,2)+" кВт"],
      ["Q теплосеть, расчёт",f(v.dh/1000,2)+" кВт"],
      ["Ограничитель бассейна",$("c2-poolkw").value+" кВт"],
      ["Ограничитель ЦО",$("c2-dhkw").value+" кВт"],
      ["Q прямого HX, доступно",f(v.direct/1000,2)+" кВт"],
      ["Q HP бассейн (v08)*",f(b.Q_HP_pool_W/1000,2)+" кВт"],
      ["Q запрос бассейна (v08)*",f(b.Q_pool_req_W/1000,2)+" кВт"],
      ["Q запрос теплосети (v08)*",f(b.Q_DH_req_W/1000,2)+" кВт"],
      ["Q DC доступно (v08)*",f(b.Q_DC_eff_W/1000,2)+" кВт"],
      ["Мощность компрессора (v08)*",f(b.P_HP_W/1000,2)+" кВт"],
      ["COP (v08)*",f(b.COP,3)],["TES энергия (v08)*",f(b.E_TES_J/3600000,2)+" кВт·ч"],
      ["T теплоносителя в бассейне",f(v.t,3)+" °C"],
      ["C бассейна",f(cap/1000000,2)+" МДж/K"],
      ["Накопленная теплота бассейна",f(v.poolEnergy,2)+" кВт·ч"],
      ["Накопленная теплота ЦО",f(v.dhEnergy,2)+" кВт·ч"],
      ["Влажность (v08)*",f(b.RH*100,1)+" %"],
      ["Потери бассейна",f(v.loss/1000,3)+" кВт"],
      ["Stateflow режим (v08)*",String(b.stateflow_mode)]
    ];
    $("c2-tech").innerHTML=tech.map(([l,val])=>'<div><span>'+l+'</span><b>'+val+'</b></div>').join("");
    $("c2-status").textContent="D_DERIVED | сценарий "+$("c2-case").value+" | 672 × 900 c | пределы: P бассейн "+$("c2-poolkw").value+" кВт, ЦО "+$("c2-dhkw").value+" кВт | базовые поля (*) не пересчитаны";
    plot("c2-poolplot",v.i,"baseT","t",false);
    plot("c2-dhplot",v.i,"baseSupply","supply",true);
    syncMain();
    if(!visualActive())window.DCHR_NATIVE_RESTORE?.();
  }
  function plot(id,marker,keyBase,keyNew,dh){
    const canvas=$(id),width=Math.max(320,Math.floor(canvas.getBoundingClientRect().width)),height=255,dpr=window.devicePixelRatio||1;
    canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);
    const g=canvas.getContext("2d");g.setTransform(dpr,0,0,dpr,0,0);
    const left=48,right=12,top=12,bottom=31,w=width-left-right,h=height-top-bottom;
    const vals=model.flatMap(row=>[row[keyBase],row[keyNew]]);
    const lo=Math.floor(Math.min(...vals)-.5),hi=Math.ceil(Math.max(...vals)+.5),span=Math.max(1,hi-lo);
    const x=i=>left+w*i/671,y=v=>top+(hi-v)/span*h;
    g.font="11px Segoe UI, sans-serif";g.lineWidth=1;
    for(let i=0;i<=4;i++){const yy=top+h*i/4;g.beginPath();g.moveTo(left,yy);g.lineTo(width-right,yy);g.strokeStyle="#324357";g.stroke();g.fillStyle="#a5b9c8";g.fillText(f(hi-span*i/4,1)+"°",3,yy+4);}
    for(let d=0;d<=7;d++){g.fillStyle="#a5b9c8";g.fillText(d+"д",x(Math.floor(d*671/7))-8,height-7);}
    [[keyBase,"#f5b76c"],[keyNew,"#5ae1ed"]].forEach(([key,color])=>{
      g.beginPath();model.forEach((row,i)=>{if(i===0)g.moveTo(x(i),y(row[key]));else g.lineTo(x(i),y(row[key]));});
      g.strokeStyle=color;g.lineWidth=2.2;g.stroke();g.beginPath();g.arc(x(marker),y(model[marker][key]),3,0,Math.PI*2);g.fillStyle=color;g.fill();
    });
    g.beginPath();g.moveTo(x(marker),top);g.lineTo(x(marker),top+h);g.setLineDash([4,4]);g.strokeStyle="#e9f3fd";g.lineWidth=1;g.stroke();g.setLineDash([]);
  }
  function preset(name){
    const values={
      base:["1","1","1",150,500],
      pool:["0","1","1",150,500],
      dh:["1","0","1",150,500],
      both:["0","0","1",150,500],
      hp:["1","1","0",150,500]
    }[name];
    if(!values)return;
    selectedPreset=name;
    ["c2-pool","c2-dh","c2-hp"].forEach((id,i)=>{$(id).value=values[i];});
    $("c2-poolkw").value=values[3];$("c2-dhkw").value=values[4];
    document.querySelectorAll("#c2-presets button").forEach(b=>b.classList.toggle("active",b.dataset.preset===name));
    build();
  }
  async function load(){
    try{
      if(!cases.length){
        const [source,status]=await Promise.all([
          fetch("/api/scenarios",{cache:"no-store"}).then(r=>r.json()),
          fetch("/api/status",{cache:"no-store"}).then(r=>r.json())]);
        if(source.metadata?.source_class!=="D_SYNTHETIC" || !Array.isArray(source.scenarios) || status.stopped)throw Error("Нет достоверных данных или активен STOP");
        cases=source.scenarios;$("c2-case").replaceChildren(...cases.map(s=>new Option(s.name,s.id)));
        $("c2-case").value="zdravy";
      }
      const id=$("c2-case").value;
      if(!cases.find(s=>s.id===id))throw Error("Неизвестный сценарий");
      const response=await fetch("/api/history?scenario="+encodeURIComponent(id)+"&scope=full&limit=672",{cache:"no-store"});
      if(!response.ok)throw Error("HTTP "+response.status);
      const payload=await response.json();
      if(payload.metadata?.source_class!=="D_SYNTHETIC" || payload.rows?.length!==672 || payload.rows.some(r=>r.quality!=="D"))throw Error("Непроверенный источник");
      raw=payload.rows;$("c2-export").disabled=false;build();
    }catch(e){$("c2-status").textContent="Ошибка: "+e.message;$("c2-export").disabled=true;}
  }
  document.querySelectorAll("#c2-presets button").forEach(btn=>btn.addEventListener("click",()=>preset(btn.dataset.preset)));
  $("c2-case").addEventListener("change",load);
  ["c2-pool","c2-dh","c2-hp","c2-poolkw","c2-dhkw","c2-return","c2-flow","c2-off"].forEach(id=>
    $(id).addEventListener("input",()=>{selectedPreset="custom";document.querySelectorAll("#c2-presets button").forEach(b=>b.classList.remove("active"));build();}));
  $("c2-time").addEventListener("input",render);
  ["c2-poolplot","c2-dhplot"].forEach(id=>$(id).addEventListener("click",event=>{
    const rect=event.currentTarget.getBoundingClientRect(),alpha=Math.min(1,Math.max(0,(event.clientX-rect.left-48)/(rect.width-60)));
    $("c2-time").value=String(Math.round(alpha*671));render();
  }));
  $("c2-sync").addEventListener("click",async()=>{
    try{const s=await fetch("/api/status",{cache:"no-store"}).then(r=>r.json());$("c2-time").value=String(s.index);render();}
    catch(e){$("c2-status").textContent="Ошибка связи: "+e.message;}
  });
  $("c2-export").addEventListener("click",()=>{
    if(!model.length)return;
    const csv=["cas_h,T_pool_native_C,T_pool_scenario_C,T_DH_supply_baseline_assumed_C,T_DH_supply_scenario_assumed_C,T_DH_return_assumed_C,massflow_assumed_kg_s,Q_pool_native_W,Q_pool_derived_W,Q_DH_native_W,Q_DH_derived_W,Q_pool_loss_derived_W,modified,D_DERIVED"];
    model.forEach(r=>csv.push([r.time,r.baseT,r.t,r.baseSupply,r.supply,r.ret,r.flow,r.b.Q_pool_phys_W,r.pool,r.b.Q_DH_W,r.dh,r.loss,Number(r.modified),1].join(",")));
    const url=URL.createObjectURL(new Blob([csv.join("\r\n")],{type:"text/csv;charset=utf-8"}));
    const a=document.createElement("a");a.href=url;a.download="DCHR_CASCADE_v02_"+$("c2-case").value+"_D_DERIVED.csv";a.click();
    setTimeout(()=>URL.revokeObjectURL(url),4000);
  });
  window.addEventListener("resize",()=>{if(model.length)render();});
  preset("base");load();
})();
