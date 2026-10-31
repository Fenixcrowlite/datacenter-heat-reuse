"use strict";
(() => {
  const $ = id => document.getElementById(id);
  const state = {mode: "v04", samples: [], provenance: "", idx: 0, serial: 0};
  const number = (v, n = 2) => Number.isFinite(v) ? Number(v).toFixed(n) : "—";
  const finite = v => typeof v === "number" && Number.isFinite(v);
  const kw = w => finite(w) ? w / 1000 : null;

  function verify(raw, mode) {
    if (!raw || !raw.metadata || raw.metadata.source_class !== "D_SYNTHETIC" ||
        raw.metadata.hardware_enabled !== false || !Array.isArray(raw.rows) ||
        raw.rows.length !== 672) throw Error("Нет подтверждённых 672 отсчётов D_SYNTHETIC");
    if (mode === "v04" && (raw.metadata.derived_quality !== "D_DERIVED" ||
        raw.metadata.status !== "VERIFIED_SIMULINK_NEW_RUN" ||
        !/v04/.test(raw.metadata.model_scope || "") ||
        typeof raw.id !== "string")) throw Error("Неверная принадлежность данных MATLAB v04");
    if (mode === "v08" && (raw.metadata.quality !== "D" ||
        raw.rows_kind !== "source_samples_not_visited_historian" ||
        typeof raw.scenario_id !== "string")) throw Error("Неверная принадлежность архива v08");
  }
  function normalize(raw, mode) {
    verify(raw, mode);
    const samples = raw.rows.map((entry, i) => {
      const v = mode === "v08" ? entry.values : entry;
      if (!v || !finite(v.cas_h) || Math.abs(v.cas_h - i * .25) > 1e-8)
        throw Error("Неверный временной индекс");
      const pool = mode === "v08" ? v.Q_pool_phys_W : v.Q_pool_W;
      const reject = mode === "v08" ? v.Q_reject_main_W + v.Q_reject_backup_W : v.Q_reject_W;
      if (![v.T_pool_C, pool, v.Q_DH_W, reject].every(finite))
        throw Error("Повреждённый отсчёт " + i);
      return {time: v.cas_h, poolTemp: v.T_pool_C, poolKw: kw(pool),
        dhKw: kw(v.Q_DH_W), rejectKw: kw(reject),
        dhSupply: mode === "v04" && finite(v.T_DH_supply_derived_C) ? v.T_DH_supply_derived_C : null,
        raw: v};
    });
    const provenance = mode === "v08"
      ? "SOURCE=v08 / D_SYNTHETIC / архивный CSV, сценарий=" + raw.scenario_id +
        " / исходные отсчёты (не журнал посещений); текущий индекс сервера=" + raw.scenario_index
      : "SOURCE=v04 / D_SYNTHETIC → D_DERIVED / новый расчёт sim(), job=" + raw.id +
        " / 672 отсчёта; не Stateflow v85";
    return {samples, provenance};
  }

  function draw(canvas, series, markerIndex) {
    const ctx = canvas.getContext("2d");
    const w = canvas.width, h = canvas.height, left = 54, right = w - 20, top = 28, bottom = h - 29;
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = "#101c2a";ctx.fillRect(0, 0, w, h);
    const all = series.flatMap(s => s.values.filter(finite));
    if (!all.length) return;
    let min = Math.min(...all), max = Math.max(...all), span = max - min;
    if (span < 0.0001) {min -= 1; max += 1;span = max - min;}
    else {min -= span * .08;max += span * .08;span = max - min;}
    const x = i => left + (right - left) * i / 671;
    const y = v => bottom - (bottom - top) * (v - min) / span;
    ctx.lineWidth = 1;ctx.font = "12px system-ui";ctx.textBaseline = "middle";
    for (let k = 0; k <= 4; k++) {
      const value = min + span * k / 4, yy = y(value);
      ctx.strokeStyle = "#354455";ctx.beginPath();ctx.moveTo(left, yy);ctx.lineTo(right, yy);ctx.stroke();
      ctx.fillStyle = "#a9bed0";ctx.fillText(number(value, 1), 5, yy);
    }
    ctx.textBaseline = "alphabetic";ctx.fillStyle = "#a9bed0";
    ctx.fillText("0 ч", left, h - 8);ctx.fillText("84 ч", x(336)-10, h-8);
    ctx.fillText("168 ч", right-35, h-8);
    for (const s of series) {
      ctx.strokeStyle = s.color;ctx.lineWidth = 2;ctx.beginPath();
      let started = false;
      s.values.forEach((v,i) => {
        if (!finite(v)) {started=false;return;}
        if (!started) {ctx.moveTo(x(i),y(v));started=true;}
        else ctx.lineTo(x(i),y(v));
      });
      ctx.stroke();
    }
    ctx.strokeStyle="#eef8ff";ctx.lineWidth=1;ctx.beginPath();
    ctx.moveTo(x(markerIndex),top);ctx.lineTo(x(markerIndex),bottom);ctx.stroke();
    let captionX=left;
    for (const s of series) {
      ctx.fillStyle=s.color;ctx.fillRect(captionX,7,9,9);
      ctx.fillStyle="#dceafa";ctx.fillText(s.name,captionX+14,16);
      captionX += 16 + ctx.measureText(s.name).width + 20;
    }
  }

  function diagnosis(s) {
    if (state.mode === "v08") {
      const v = s.raw, flags = ["E_STOP","IT_model_alarm","safety_latch","emergency_flag",
        "invalid_sensor","flow_fault","sensor_mismatch","sensor_hot",
        "primary_valve_fault","secondary_valve_fault"]
        .filter(k => finite(v[k]) && v[k] > 0);
      if (finite(v.Q_unhandled_W) && v.Q_unhandled_W > 1) flags.push("Q_unhandled_W > 1 W");
      if (finite(v.Q_leak_W) && Math.abs(v.Q_leak_W) > 1) flags.push("|Q_leak_W| > 1 W");
      return "v08: флаги модели в выбранном отсчёте (НЕ подтверждённые аварии оборудования): " +
             (flags.length ? flags.join(", ") : "активных флагов не обнаружено") +
             ". Официальный журнал replay остаётся в SCADA v09.";
    }
    const v = s.raw, ks = ["residual_DC_W","residual_DH_W","residual_HP_W","residual_pool_W"];
    const invalid = ks.filter(k => !finite(v[k]) || Math.abs(v[k]) > 1e-5);
    return "v04: диагностика численного баланса (НЕ система защиты и НЕ журнал SCADA). " +
      (invalid.length ? "Не пройдены: " + invalid.join(", ") :
        "Невязки DC/DH/HP/бассейна в пределах 1e-5 W.") +
      " T подачи ЦО здесь только алгебраическая оценка, без гидравлической динамики.";
  }
  function render() {
    if (!state.samples.length) return;
    const s = state.samples[state.idx];
    $("sc-clock").textContent = number(s.time,2) + " ч / индекс " + state.idx;
    $("sc-total").textContent = "672 × 900 с";
    $("sc-pool-temp").textContent = number(s.poolTemp,2);
    $("sc-pool-power").textContent = number(s.poolKw,2);
    $("sc-dh-power").textContent = number(s.dhKw,2);
    $("sc-reject-power").textContent = number(s.rejectKw,2);
    $("sc-diagnostics").textContent = diagnosis(s);
    $("sc-provenance").textContent = state.provenance;
    $("sc-temp-note").textContent = state.mode === "v04" ?
      "Голубой: бассейн. Оранжевый: расчётная подача ЦО без инерции труб." :
      "Голубой: бассейн. В v08 нет проверенной температуры подачи ЦО; линия не выдумывается.";
    draw($("sc-temp-chart"), [
      {name:"Бассейн °C",color:"#3ad3f5",values:state.samples.map(r=>r.poolTemp)},
      ...(state.mode === "v04" ?
        [{name:"ЦО °C*",color:"#ecb870",values:state.samples.map(r=>r.dhSupply)}] : [])
    ],state.idx);
    draw($("sc-power-chart"),[
      {name:"Бассейн кВт",color:"#3ad3f5",values:state.samples.map(r=>r.poolKw)},
      {name:"ЦО кВт",color:"#b69cfa",values:state.samples.map(r=>r.dhKw)},
      {name:"REJECT кВт",color:"#f0a367",values:state.samples.map(r=>r.rejectKw)}
    ],state.idx);
    const body = $("sc-table-body");body.replaceChildren();
    for (let i = Math.max(0,state.idx - 6); i <= Math.min(671,state.idx + 6); i++) {
      const r = state.samples[i],tr=document.createElement("tr");
      if (i === state.idx) tr.style.background="#26465c";
      for (const value of [r.time,r.poolTemp,r.poolKw,r.dhKw,r.rejectKw]) {
        const td=document.createElement("td");td.textContent=number(value,2);
        td.style.padding="5px";td.style.borderBottom="1px solid #304256";
        tr.appendChild(td);
      }
      body.appendChild(tr);
    }
  }
  async function load() {
    const serial=++state.serial, mode=$("sc-source").value;
    state.mode=mode;state.samples=[];
    for (const key of ["sc-pool-temp","sc-pool-power","sc-dh-power","sc-reject-power","sc-clock","sc-total"]) {
      $(key).textContent="—";
    }
    $("sc-diagnostics").textContent="Нет подтверждённых данных выбранного источника.";
    $("sc-temp-note").textContent="—";
    $("sc-table-body").replaceChildren();
    for (const key of ["sc-temp-chart","sc-power-chart"]) {
      const canvas=$(key);canvas.getContext("2d").clearRect(0,0,canvas.width,canvas.height);
    }
    $("sc-error").textContent="";
    $("sc-provenance").textContent="Загрузка " + mode + "…";
    $("sc-refresh").disabled=true;
    try {
      const response=await fetch(mode === "v08" ? "/api/archive" : "/api/result",
                                  {cache:"no-store",credentials:"same-origin"});
      if (!response.ok) throw Error("Источник недоступен: HTTP " + response.status);
      const raw=await response.json();
      if (serial!==state.serial) return;
      const result=normalize(raw,mode);
      state.samples=result.samples;state.provenance=result.provenance;
      state.idx=mode === "v08" && Number.isInteger(raw.scenario_index) ?
        Math.min(671,Math.max(0,raw.scenario_index)) : 0;
      $("sc-index").value=String(state.idx);
      render();
    } catch(e) {
      if (serial===state.serial) {
        $("sc-error").textContent=String(e.message||e);
        $("sc-provenance").textContent="Не удалось загрузить подтверждённый источник " + mode;
      }
    } finally {
      if (serial===state.serial) $("sc-refresh").disabled=false;
    }
  }
  $("sc-source").addEventListener("change",load);
  $("sc-refresh").addEventListener("click",load);
  $("sc-index").addEventListener("input",()=>{
    if (!state.samples.length) return;
    state.idx=Math.max(0,Math.min(671,Number($("sc-index").value)||0));render();
  });
  load();
})();
