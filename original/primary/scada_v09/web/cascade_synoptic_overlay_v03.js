
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
      "svg-tes-flow":"+"+f(b.Q_HP_charge_W/1000,1)+" / −"+f(b.Q_TES_discharge_W/1000,1)+" кВт*",
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
    for(const [id,value] of Object.entries(flowStates)){
      const line=document.getElementById(id);
      if(!line)continue;
      line.classList.toggle("active",Math.abs(value)>1e-6);
      line.classList.toggle("c2-flow-off",(id==="pipe-hx"||id==="pipe-pool")?isPoolOff:(id==="pipe-dh"?isDHOff:false));
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
      ". * DC, HP, TES, REJECT и IT: исходные v08, без пересчёта. Тренды, события и историк ниже относятся к replay сервера, НЕ к этому сценарию.";
    const stateflow=document.getElementById("stateflow");
    if(stateflow)stateflow.textContent="WHAT-IF / STATEFLOW v08* "+b.stateflow_mode;
  }
  window.DCHR_CASCADE_SYNC=syncMain;
  window.DCHR_CASCADE_EQUIPMENT=(key)=>{
    if(!model.length || !visualActive() || !["pool","dh","hx"].includes(key))return false;
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
