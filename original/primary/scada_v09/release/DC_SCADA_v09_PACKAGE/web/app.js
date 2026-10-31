"use strict";

(() => {
  const $ = (id) => document.getElementById(id);
  const numberFormat = new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 1 });
  const format = (value, digits = 1) => typeof value === "number" && Number.isFinite(value)
    ? new Intl.NumberFormat("ru-RU", { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(value) : "—";
  const numeric = (value) => typeof value === "number" && Number.isFinite(value);
  const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const text = (id, value) => { $(id).textContent = value; };
  const kw = (value) => numeric(value) ? value / 1000 : null;
  const state = { token: "", status: null, snapshot: null, scenarios: [], history: [], persisted: [], page: 0, historyKey: "", busy: false, dragging: false, comparisonVersion: 0, instanceId: null };
  const fullRuns = new Map();
  let toastTimer;

  async function api(path, options = {}) {
    const response = await fetch(path, { cache: "no-store", credentials: "same-origin", signal: AbortSignal.timeout(5000), ...options });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
    if (data.metadata?.source_class !== "D_SYNTHETIC" || data.metadata?.quality !== "D" || data.metadata?.hardware_enabled !== false) {
      throw new Error("Некорректная классификация источника: ожидается D_SYNTHETIC / hardware_enabled=false");
    }
    return data;
  }

  function toast(message, error = false) {
    const node = $("toast");
    node.textContent = message;
    node.classList.toggle("error", error);
    node.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { node.hidden = true; }, 4800);
  }

  function connected(ok, error = "") {
    $("connection-dot").className = `status-dot ${ok ? "online" : "offline"}`;
    text("connection-status", ok ? "Локальный сервер" : "Нет связи");
    $("connection-error").hidden = ok;
    if (!ok) text("connection-error", `Нет свежих данных: ${error}. Показаны последние полученные значения D_SYNTHETIC; управление временно недоступно.`);
    document.querySelectorAll(".playback-panel button,.playback-panel select,.playback-panel input").forEach((el) => { el.disabled = !ok; });
    if (ok && state.status) {
      setStopControls(state.status.stopped);
      $("play-button").disabled = state.status.stopped || state.status.playing || state.status.at_end;
      $("pause-button").disabled = !state.status.playing;
    }
  }

  function setStopControls(stopped) {
    ["play-button", "reset-button", "scenario-select", "seek-input"].forEach((id) => { $(id).disabled = stopped; });
  }

  function renderStatus(status) {
    state.status = status;
    if (status.csrf_token) state.token = status.csrf_token;
    text("sample-time", `${format(status.simulation_time_h, 2)} ч модели`);
    text("sample-position", `${numberFormat.format(status.index + 1)} / ${numberFormat.format(status.sample_count)} отсчётов · Δt = 900 с`);
    text("seek-output", `${format(status.simulation_time_h, 2)} ч`);
    if (!state.dragging) {
      $("seek-input").max = String(Math.max(0, status.sample_count - 1));
      $("seek-input").value = String(status.index);
    }
    $("scenario-select").value = status.scenario_id;
    $("speed-select").value = String(status.speed);
    const pill = $("playback-state");
    pill.textContent = status.stopped ? "■ STOP" : status.playing ? "● ВОСПРОИЗВЕДЕНИЕ" : status.at_end ? "ПРОГОН ЗАВЕРШЁН" : "Ⅱ ПАУЗА";
    pill.className = `state-pill ${status.stopped ? "stopped" : status.playing ? "playing" : ""}`;
    $("stop-banner").hidden = !status.stopped;
    setStopControls(status.stopped);
    $("play-button").disabled = status.stopped || status.playing || status.at_end;
    $("pause-button").disabled = !status.playing;
    text("stateflow", `STATEFLOW ${numeric(state.snapshot?.values?.stateflow_mode) ? state.snapshot.values.stateflow_mode : "—"} · RAW`);
    const scenario = state.scenarios.find((s) => s.id === status.scenario_id);
    if (scenario) {
      text("source-file", `Источник текущего сценария: ${scenario.source_file} · ${scenario.rows} строк · D_SYNTHETIC / D`);
      text("source-sha", `SHA-256: ${scenario.sha256}`);
    }
  }

  const kpis = [
    { label: "Доступное тепло DC", tag: "Q_DC_eff_W", color: "var(--orange)", value: (v) => kw(v.Q_DC_eff_W), unit: "кВт", detail: (v) => `Источник Q_DC_source_raw: ${format(kw(v.Q_DC_source_raw_W))} кВт` },
    { label: "Тепло в бассейн", tag: "Q_pool_phys_W", color: "var(--cyan)", value: (v) => kw(v.Q_pool_phys_W), unit: "кВт", detail: (v) => `Запрос модели: ${format(kw(v.Q_pool_req_W))} кВт` },
    { label: "Температура бассейна", tag: "T_pool_C", color: "var(--cyan)", value: (v) => v.T_pool_C, unit: "°C", detail: () => "BAZÉN · 500 м³ · исходный отсчёт" },
    { label: "Модельный риск IT", tag: "T_IT_model_C", color: "var(--red)", value: (v) => v.T_IT_model_C, unit: "°C*", detail: () => "* Индикатор модели, не температура CPU" },
    { label: "Электричество ТН", tag: "P_HP_W / COP", color: "var(--orange)", value: (v) => kw(v.P_HP_W), unit: "кВт", detail: (v) => `COP = ${format(v.COP, 2)} · значение из CSV` },
    { label: "Энергия в TES", tag: "E_TES_J", color: "var(--green)", value: (v, d) => d.tes_energy_kwh ?? (numeric(v.E_TES_J) ? v.E_TES_J / 3600000 : null), unit: "кВт·ч", detail: () => "SOC — · ёмкость не документирована" },
    { label: "Отдача в теплосеть", tag: "Q_DH_W", color: "var(--purple)", value: (v) => kw(v.Q_DH_W), unit: "кВт", detail: (v) => `Запрос Q_DH_req: ${format(kw(v.Q_DH_req_W))} кВт` },
    { label: "Отвод REJECT A + B", tag: "Q_reject_main / backup", color: "var(--red)", value: (v) => numeric(v.Q_reject_main_W) && numeric(v.Q_reject_backup_W) ? kw(v.Q_reject_main_W + v.Q_reject_backup_W) : null, unit: "кВт", detail: (v) => `Не обработано: ${format(kw(v.Q_unhandled_W))} кВт` },
  ];

  function createKpis() {
    $("kpi-grid").innerHTML = kpis.map((k, i) => `<article class="kpi-card" title="D_SYNTHETIC · качество D"><div class="kpi-label"><span>${k.label}</span><span class="kpi-tag">${k.tag}</span></div><div class="kpi-number"><span id="kpi-${i}">—</span><small>${k.unit}</small></div><div class="kpi-detail" id="kpi-detail-${i}">D_SYNTHETIC · D</div></article>`).join("");
    $("kpi-grid").querySelectorAll(".kpi-card").forEach((node, i) => node.style.setProperty("--accent", kpis[i].color));
  }

  function renderSnapshot(snapshot) {
    state.snapshot = snapshot;
    const v = snapshot.values;
    const d = snapshot.derived || {};
    kpis.forEach((k, i) => { text(`kpi-${i}`, format(k.value(v, d))); text(`kpi-detail-${i}`, k.detail(v, d)); });
    const labels = { "svg-dc": [v.Q_DC_eff_W, "кВт"], "svg-dc-flow": [v.Q_DC_eff_W, ""], "svg-hx": [v.Q_HX_phys_W, "кВт"], "svg-hp-source": [v.Q_HP_source_W, ""], "svg-hp-pool": [v.Q_HP_pool_W, "кВт"], "svg-pool-power": [v.Q_pool_phys_W, "кВт"], "svg-dh": [v.Q_DH_W, "кВт"], "svg-dh-flow": [v.Q_DH_W, "кВт"], "svg-reject-a": [v.Q_reject_main_W, "кВт"], "svg-reject-b": [v.Q_reject_backup_W, "кВт"] };
    Object.entries(labels).forEach(([id, [value, unit]]) => { text(id, `${format(kw(value))} ${unit}`.trim()); });
    text("svg-cop", `COP ${format(v.COP, 2)}`);
    text("svg-hp-power", `P_HP ${format(kw(v.P_HP_W))} кВт`);
    text("svg-pool", `${format(v.T_pool_C)} °C`);
    text("svg-tes", `${format(d.tes_energy_kwh)} кВт·ч`);
    text("svg-tes-flow", `+${format(kw(v.Q_HP_charge_W))} / −${format(kw(v.Q_TES_discharge_W))} кВт`);
    text("unhandled-label", `Q_unhandled ${format(kw(v.Q_unhandled_W))} кВт · D`);
    const flows = { "pipe-dc": v.Q_DC_eff_W, "pipe-hx": v.Q_HX_phys_W, "pipe-hp-source": v.Q_HP_source_W, "pipe-pool": v.Q_HP_pool_W, "pipe-dh": v.Q_DH_W, "pipe-tes": (v.Q_HP_charge_W || 0) - (v.Q_TES_discharge_W || 0), "pipe-reject-a": v.Q_reject_main_W, "pipe-reject-b": v.Q_reject_backup_W };
    Object.entries(flows).forEach(([id, value]) => {
      const node = $(id);
      node.classList.toggle("active", numeric(value) && Math.abs(value) > 0);
      node.classList.toggle("reverse", value < 0);
      node.style.animationPlayState = snapshot.status.playing ? "" : "paused";
    });
    renderStatus(snapshot.status);
    text("last-update", `Получено: ${new Date(snapshot.observed_at || Date.now()).toLocaleTimeString("ru-RU")} · качество D`);
    if ($("equipment-dialog").open && $("equipment-dialog").dataset.key) renderEquipment($("equipment-dialog").dataset.key);
  }

  const severityColors = { CRITICAL: "#ff7b8a", WARNING: "#ffb162", INFO: "#7eacd5" };
  const severityNames = { CRITICAL: "КРИТИЧЕСКОЕ", WARNING: "ПРЕДУПРЕЖДЕНИЕ", INFO: "ИНФОРМАЦИЯ" };
  function renderAlarms(data) {
    const active = data.active_alarms || [];
    text("alarm-count", active.length);
    text("alarm-status", active.length ? `Активных состояний: ${active.length}` : "Активных тревог нет");
    $("alarm-status").className = active.some((a) => a.severity === "CRITICAL") ? "red-text" : active.length ? "orange-text" : "green-text";
    if (!data.events?.length) { $("alarm-feed").innerHTML = '<p class="empty-state">Событий пока нет.<br>Состояния определяются по флагам исходного CSV.</p>'; return; }
    $("alarm-feed").innerHTML = data.events.map((event) => {
      const scenario = state.scenarios.find((s) => s.id === event.scenario_id);
      const label = event.state === "CLEARED" ? "СНЯТО" : event.state === "ACK" ? "КВИТИРОВАНО" : severityNames[event.severity] || event.severity;
      const color = event.state === "CLEARED" ? "#61d6a2" : severityColors[event.severity] || "#7eacd5";
      return `<article class="alarm-item" data-severity-color="${color}" title="${esc(scenario?.name || event.scenario_id)} · D_SYNTHETIC"><div class="alarm-meta"><span class="alarm-severity">${esc(label)}</span><span>${format(event.time_h, 2)} ч модели</span></div><p class="alarm-message">${esc(event.message)}</p><div class="alarm-bottom"><span>${esc(event.code)} · D</span>${event.state === "ACTIVE" && !event.acknowledged ? `<button class="ack-button" data-ack="${Number(event.id)}" type="button">Квитировать</button>` : `<span>${event.acknowledged ? "✓ Квитировано" : "Событие"}</span>`}</div></article>`;
    }).join("");
    $("alarm-feed").querySelectorAll("[data-severity-color]").forEach((node) => node.style.setProperty("--severity", node.dataset.severityColor));
  }

  class LineChart {
    constructor(canvasId, tooltipId, series, legendId = null, seekable = true) {
      this.canvas = $(canvasId); this.ctx = this.canvas.getContext("2d"); this.tooltip = $(tooltipId); this.series = series; this.rows = []; this.hover = null; this.seekable = seekable;
      if (legendId) {
        this.legend = $(legendId);
        this.legend.innerHTML = series.map((s, i) => `<button class="legend-button" type="button" data-series="${i}" aria-pressed="true"><i class="legend-dot"></i>${esc(s.label)}</button>`).join("");
        this.legend.querySelectorAll(".legend-dot").forEach((node, i) => { node.style.background = series[i].color; });
        this.legend.addEventListener("click", (event) => { const button = event.target.closest("[data-series]"); if (!button) return; const s = this.series[Number(button.dataset.series)]; s.hidden = !s.hidden; button.classList.toggle("inactive", s.hidden); button.setAttribute("aria-pressed", String(!s.hidden)); this.draw(); });
      }
      new ResizeObserver(() => this.draw()).observe(this.canvas.parentElement);
      this.canvas.addEventListener("pointermove", (event) => this.move(event));
      this.canvas.addEventListener("pointerleave", () => { this.hover = null; this.tooltip.hidden = true; this.draw(); });
      this.canvas.addEventListener("click", (event) => { this.move(event); if (this.seekable && this.hover !== null && !state.status?.stopped) command("seek", { index: this.rows[this.hover].sample_index }); });
    }
    setRows(rows) { this.rows = rows; this.hover = null; this.tooltip.hidden = true; this.draw(); }
    value(row, series) { const value = row.values[series.key]; return numeric(value) ? value * (series.factor ?? 1) : null; }
    draw() {
      const rect = this.canvas.getBoundingClientRect();
      if (!rect.width || !rect.height) return;
      const ratio = Math.min(devicePixelRatio || 1, 3);
      this.canvas.width = Math.round(rect.width * ratio); this.canvas.height = Math.round(rect.height * ratio);
      const ctx = this.ctx; ctx.setTransform(ratio, 0, 0, ratio, 0, 0); ctx.clearRect(0, 0, rect.width, rect.height);
      this.box = { left: 48, right: rect.width - 15, top: 20, bottom: rect.height - 36 };
      const b = this.box; const visible = this.series.filter((s) => !s.hidden);
      const values = this.rows.flatMap((row) => visible.map((s) => this.value(row, s)).filter(numeric));
      let min = values.length ? Math.min(...values) : 0, max = values.length ? Math.max(...values) : 1;
      const padding = Math.max((max - min) * .12, Math.abs(max) * .015, .1);
      min -= padding; max += padding;
      if (this.series.some((s) => s.unit === "кВт") && min > 0) min = 0;
      this.xMin = this.rows.length ? this.rows[0].values.cas_h : 0; this.xMax = this.rows.length > 1 ? this.rows[this.rows.length - 1].values.cas_h : this.xMin + .25;
      this.toX = (v) => b.left + (v - this.xMin) / (this.xMax - this.xMin || 1) * (b.right - b.left);
      this.toY = (v) => b.bottom - (v - min) / (max - min) * (b.bottom - b.top);
      ctx.font = '9px "Segoe UI", sans-serif'; ctx.lineWidth = 1;
      for (let i = 0; i <= 4; i++) {
        const y = b.top + (b.bottom - b.top) * i / 4;
        ctx.strokeStyle = "#223246"; ctx.beginPath(); ctx.moveTo(b.left, y); ctx.lineTo(b.right, y); ctx.stroke();
        ctx.fillStyle = "#72869f"; ctx.textAlign = "right"; ctx.fillText(format(max - (max - min) * i / 4, max - min < 5 ? 1 : 0), b.left - 8, y + 3);
      }
      for (let i = 0; i <= 4; i++) {
        const x = b.left + (b.right - b.left) * i / 4;
        ctx.fillStyle = "#72869f"; ctx.textAlign = i === 0 ? "left" : i === 4 ? "right" : "center";
        ctx.fillText(`${format(this.xMin + (this.xMax - this.xMin) * i / 4, 1)} ч`, x, b.bottom + 20);
      }
      if (!values.length) { ctx.fillStyle = "#8094aa"; ctx.textAlign = "center"; ctx.fillText("Нет исходных отсчётов для отображения", (b.left + b.right) / 2, (b.top + b.bottom) / 2); return; }
      ctx.save(); ctx.beginPath(); ctx.rect(b.left - 3, b.top - 3, b.right - b.left + 6, b.bottom - b.top + 6); ctx.clip();
      visible.forEach((series) => {
        ctx.strokeStyle = series.color; ctx.lineWidth = 1.7; ctx.beginPath(); let previous = null;
        // A step joins native samples without inventing intermediate telemetry.
        this.rows.forEach((row) => { const value = this.value(row, series); if (!numeric(value)) { previous = null; return; } const x = this.toX(row.values.cas_h), y = this.toY(value); if (previous !== null) { ctx.lineTo(x, previous); ctx.lineTo(x, y); } else ctx.moveTo(x, y); previous = y; }); ctx.stroke();
        if (this.rows.length === 1) { const value = this.value(this.rows[0], series); if (numeric(value)) { ctx.beginPath(); ctx.arc(this.toX(this.rows[0].values.cas_h), this.toY(value), 3, 0, Math.PI * 2); ctx.fillStyle = series.color; ctx.fill(); } }
      });
      if (this.hover !== null && this.rows[this.hover]) {
        const row = this.rows[this.hover], x = this.toX(row.values.cas_h);
        ctx.setLineDash([3, 4]); ctx.strokeStyle = "#a0b4cb"; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(x, b.top); ctx.lineTo(x, b.bottom); ctx.stroke(); ctx.setLineDash([]);
        visible.forEach((series) => { const value = this.value(row, series); if (numeric(value)) { ctx.fillStyle = series.color; ctx.beginPath(); ctx.arc(x, this.toY(value), 3, 0, Math.PI * 2); ctx.fill(); } });
      }
      ctx.restore();
    }
    move(event) {
      if (!this.rows.length || !this.box) return;
      const rect = this.canvas.getBoundingClientRect(), x = event.clientX - rect.left;
      const time = this.xMin + Math.max(0, Math.min(1, (x - this.box.left) / (this.box.right - this.box.left))) * (this.xMax - this.xMin);
      let index = 0, distance = Infinity;
      this.rows.forEach((row, i) => { const delta = Math.abs(row.values.cas_h - time); if (delta < distance) { distance = delta; index = i; } });
      this.hover = index; const row = this.rows[index];
      const visible = this.series.filter((s) => !s.hidden);
      this.tooltip.innerHTML = `<div class="tooltip-heading">${format(row.values.cas_h, 2)} ч · отсчёт ${row.sample_index + 1} · D</div>${visible.map((s) => `<div class="tooltip-row"><span><i class="legend-dot"></i>${esc(s.label)}</span><b>${format(this.value(row, s), s.unit === "°C" ? 2 : 1)} ${s.unit}</b></div>`).join("")}`;
      this.tooltip.querySelectorAll(".legend-dot").forEach((node, i) => { node.style.background = visible[i].color; });
      this.tooltip.hidden = false;
      this.tooltip.style.left = `${Math.max(2, Math.min(x + 12, rect.width - this.tooltip.offsetWidth - 4))}px`;
      this.tooltip.style.top = "8px";
      this.draw();
    }
  }

  const thermal = new LineChart("thermal-chart", "thermal-tooltip", [
    { key: "Q_DC_eff_W", label: "DC", color: "#ffb162", unit: "кВт", factor: .001 },
    { key: "Q_pool_phys_W", label: "Бассейн", color: "#49d5e8", unit: "кВт", factor: .001 },
    { key: "Q_DH_W", label: "Теплосеть", color: "#b5a0ff", unit: "кВт", factor: .001 },
    { key: "Q_reject_total_W", label: "REJECT", color: "#ff7b8a", unit: "кВт", factor: .001 },
    { key: "Q_unhandled_W", label: "Не обработано", color: "#e5db8a", unit: "кВт", factor: .001 },
  ], "thermal-legend");
  const temperature = new LineChart("temperature-chart", "temperature-tooltip", [
    { key: "T_pool_C", label: "Бассейн", color: "#49d5e8", unit: "°C" },
    { key: "T_IT_model_C", label: "IT риск*", color: "#ff7b8a", unit: "°C" },
    { key: "sensor1_C", label: "Датчик 1", color: "#61d6a2", unit: "°C" },
    { key: "sensor2_C", label: "Датчик 2", color: "#b5a0ff", unit: "°C" },
  ], "temperature-legend");
  const comparison = new LineChart("comparison-chart", "comparison-tooltip", [
    { key: "a", label: "A · T_pool_C", color: "#49d5e8", unit: "°C" },
    { key: "b", label: "B · T_pool_C", color: "#ffb162", unit: "°C" },
  ], null, false);

  function renderTrends() {
    const count = Number($("trend-window").value), rows = state.history.slice(-count);
    thermal.setRows(rows); temperature.setRows(rows);
  }

  function renderHistory() {
    const rows = state.persisted, size = Number($("history-page-size").value), pages = Math.max(1, Math.ceil(rows.length / size));
    state.page = Math.min(Math.max(state.page, 0), pages - 1);
    $("history-body").innerHTML = rows.slice(state.page * size, (state.page + 1) * size).map((row) => {
      const v = row.values;
      return `<tr class="${row.sample_index === state.status?.index ? "current-row" : ""}"><td>${row.sample_index + 1}</td><td>${format(v.cas_h, 2)}</td><td>${format(v.T_pool_C, 2)}</td><td>${format(kw(v.Q_DC_eff_W))}</td><td>${format(kw(v.Q_pool_phys_W))}</td><td>${format(kw(v.P_HP_W))}</td><td>${format(v.T_IT_model_C, 2)}</td><td>${format(kw(v.Q_unhandled_W))}</td><td>${row.last_seen ? esc(new Date(row.last_seen).toLocaleString("ru-RU")) : "—"}</td><td><span class="table-quality">D_SYNTHETIC / D</span></td></tr>`;
    }).join("") || '<tr><td colspan="10" class="empty-state">В SQLite пока нет посещённых отсчётов.</td></tr>';
    text("history-count", `${rows.length} уникальных записей SQLite · текущий сценарий`);
    text("history-page", `${state.page + 1} / ${pages}`);
    $("history-prev").disabled = state.page === 0; $("history-next").disabled = state.page >= pages - 1; $("export-button").disabled = !rows.length;
  }

  function exportHistory() {
    if (!state.persisted.length) return;
    const fields = Object.keys(state.persisted[0].values);
    const cell = (value) => `"${String(value ?? "").replace(/"/g, '""')}"`;
    const headers = ["scenario_id", "sample_index", "first_seen", "last_seen", "source_class", "quality", ...fields];
    const lines = [headers.map(cell).join(","), ...state.persisted.map((row) => [row.scenario_id, row.sample_index, row.first_seen, row.last_seen, "D_SYNTHETIC", "D", ...fields.map((key) => row.values[key])].map(cell).join(","))];
    const url = URL.createObjectURL(new Blob(["\uFEFF", lines.join("\r\n")], { type: "text/csv;charset=utf-8" }));
    const a = document.createElement("a"); a.href = url; a.download = `scada_v09_D_SYNTHETIC_${state.status.scenario_id}.csv`; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function renderScenarios(data) {
    state.scenarios = data.scenarios;
    const options = data.scenarios.map((s) => `<option value="${esc(s.id)}">${esc(s.name)}</option>`).join("");
    ["scenario-select", "compare-a", "compare-b"].forEach((id) => { $(id).innerHTML = options; });
    $("compare-b").selectedIndex = Math.min(1, data.scenarios.length - 1);
    $("comparison-body").innerHTML = data.scenarios.map((s) => `<tr><td title="${esc(s.source_file)}"><button class="compare-open" data-scenario="${esc(s.id)}" type="button" title="Показать сценарий на графике A">${esc(s.name)}</button></td><td>${s.rows}</td><td>${format(s.summary.pool_min_C, 2)}…${format(s.summary.pool_max_C, 2)}</td><td>${format(s.summary.it_risk_max_C, 2)}</td><td>${format(s.summary.pool_energy_kwh)}</td><td>${format(s.summary.reject_energy_kwh)}</td><td>${format(s.summary.unhandled_energy_kwh)}</td><td>D_SYNTHETIC</td></tr>`).join("");
    text("qa-status", `Независимый QA v08: ${data.qa?.status || "статус не предоставлен"} · классификация QA: ${data.qa?.source_class || "—"}. Классификация всех отображаемых данных: D_SYNTHETIC / D.`);
  }

  async function fullRun(id) {
    if (!fullRuns.has(id)) fullRuns.set(id, api(`/api/history?scope=full&limit=672&scenario=${encodeURIComponent(id)}`).catch((e) => { fullRuns.delete(id); throw e; }));
    return fullRuns.get(id);
  }
  async function renderComparison() {
    const version = ++state.comparisonVersion;
    try {
      const a = $("compare-a").value, b = $("compare-b").value;
      const [runA, runB] = await Promise.all([fullRun(a), fullRun(b)]);
      if (version !== state.comparisonVersion) return;
      const byTime = new Map();
      runA.rows.forEach((row) => byTime.set(row.values.cas_h, { sample_index: row.sample_index, values: { cas_h: row.values.cas_h, a: row.values.T_pool_C } }));
      runB.rows.forEach((row) => { const target = byTime.get(row.values.cas_h) || { sample_index: row.sample_index, values: { cas_h: row.values.cas_h } }; target.values.b = row.values.T_pool_C; byTime.set(row.values.cas_h, target); });
      comparison.setRows([...byTime.values()].sort((x, y) => x.values.cas_h - y.values.cas_h));
    } catch (e) { toast(`Сравнение недоступно: ${e.message}`, true); }
  }

  const equipment = {
    dc: { title: "Дата-центр / Datacentrum", keys: ["Q_DC_source_raw_W", "Q_DC_eff_W", "Q_IT_shed_W", "T_DC_C", "T_IT_model_C", "IT_model_alarm", "IT_ok"], note: "T_IT_model_C — модельный индикатор риска. Это не измерение температуры CPU." },
    hx: { title: "Теплообменник / Výmenník", keys: ["Q_HX_phys_W", "HX_ok", "Q_leak_W", "primary_valve_fault", "secondary_valve_fault", "primary_valve_stuck", "secondary_valve_stuck"], note: "Отображаются исходные физические потоки и флаги модели. Значения флагов показаны без интерпретации команд." },
    hp: { title: "Тепловой насос / Tepelné čerpadlo", keys: ["COP", "P_HP_W", "P_aux_W", "Q_HP_source_W", "Q_HP_pool_W", "Q_HP_DH_W", "Q_HP_charge_W", "stateflow_mode"], note: "COP и stateflow_mode — исходные значения CSV; названия числовых состояний не назначаются." },
    pool: { title: "Бассейн / Bazén · 500 м³", keys: ["T_pool_C", "Q_pool_req_W", "Q_pool_phys_W", "Q_pool_loss_W", "sensor1_C", "sensor2_C", "pool_enabled", "sensor_mismatch", "safety_latch"], note: "Временная координата cas_h берётся без изменения из CSV. Температура относится к модели бассейна." },
    tes: { title: "Накопитель / Akumulácia TES", keys: ["E_TES_J", "Q_HP_charge_W", "Q_TES_discharge_W", "Q_TES_loss_W", "TES_ok"], note: "Энергия в кВт·ч = E_TES_J / 3 600 000. SOC (%) не вычисляется: подтверждённая ёмкость накопителя не документирована. Общая линия TES функционально объединяет заряд и разряд." },
    dh: { title: "Теплосеть / Centrálne zásobovanie teplom", keys: ["Q_DH_req_W", "Q_DH_W", "Q_DH_unmet_W", "Q_HP_DH_W"], note: "Мощности в ваттах — нативные значения Simulink. Отображение не отправляет команд в теплосеть." },
    reject: { title: "Отвод тепла / Odvod tepla A + B", keys: ["Q_reject_main_W", "Q_reject_backup_W", "Q_reject_total_W", "Q_reject_physical_W", "Q_unhandled_W", "reject_main_availability", "reject_backup_availability", "flow_fault", "emergency_flag"], note: "Основной и резервный отвод показываются раздельно. Q_unhandled_W — неотведённая мощность в исходной модели." },
  };
  function renderEquipment(key) {
    const config = equipment[key], values = state.snapshot?.values || {};
    if (!config) return;
    text("equipment-title", config.title);
    $("equipment-values").innerHTML = config.keys.map((field) => {
      const unit = field.endsWith("_W") ? " W" : field.endsWith("_C") ? " °C" : field.endsWith("_J") ? " J" : "";
      return `<div><dt>${esc(field)}</dt><dd>${format(values[field], unit === " J" ? 0 : 3)}${unit}</dd></div>`;
    }).join("");
    text("equipment-note", config.note);
  }

  async function refresh(force = false) {
    if (state.busy) return;
    state.busy = true;
    try {
      const snapshot = await api("/api/snapshot");
      if (state.instanceId && state.instanceId !== snapshot.status.instance_id) {
        const status = await api("/api/status"); state.token = status.csrf_token; fullRuns.clear(); state.historyKey = "";
      }
      state.instanceId = snapshot.status.instance_id;
      renderSnapshot(snapshot); connected(true);
      const key = `${snapshot.status.scenario_id}:${snapshot.status.index}`;
      if (force || key !== state.historyKey) {
        const id = encodeURIComponent(snapshot.status.scenario_id);
        const [history, persisted] = await Promise.all([api(`/api/history?limit=672&scenario=${id}`), api(`/api/historian?limit=672&scenario=${id}`)]);
        if (history.scenario_id === state.status.scenario_id) {
          state.history = history.rows.filter((row) => row.sample_index <= snapshot.status.index); state.persisted = persisted.rows;
          state.historyKey = key; renderTrends(); renderHistory();
        }
      }
      renderAlarms(await api("/api/alarms?limit=60"));
    } catch (error) { connected(false, error.message); } finally { state.busy = false; }
  }

  async function command(action, params = {}) {
    if (!state.token) return toast("Нет токена локальной сессии. Дождитесь подключения.", true);
    try {
      const result = await api("/api/control", { method: "POST", headers: { "Content-Type": "application/json", "X-SCADA-Token": state.token }, body: JSON.stringify({ action, ...params }) });
      if (result.status) renderStatus(result.status);
      if (action === "scenario" || action === "reset") state.page = 0;
      state.historyKey = "";
      await refresh(true);
      if (action === "ack") toast("Событие квитировано локально · D_SYNTHETIC");
    } catch (error) { toast(error.message, true); await refresh(); }
  }

  $("play-button").addEventListener("click", () => command("play"));
  $("pause-button").addEventListener("click", () => command("pause"));
  $("reset-button").addEventListener("click", () => command("reset"));
  $("scenario-select").addEventListener("change", (e) => command("scenario", { scenario_id: e.target.value }));
  $("speed-select").addEventListener("change", (e) => command("speed", { speed: Number(e.target.value) }));
  $("seek-input").addEventListener("input", (e) => { state.dragging = true; text("seek-output", `Отсчёт ${Number(e.target.value) + 1}`); });
  $("seek-input").addEventListener("change", (e) => { state.dragging = false; command("seek", { index: Number(e.target.value) }); });
  $("trend-window").addEventListener("change", renderTrends);
  $("history-page-size").addEventListener("change", () => { state.page = 0; renderHistory(); });
  $("history-prev").addEventListener("click", () => { state.page--; renderHistory(); });
  $("history-next").addEventListener("click", () => { state.page++; renderHistory(); });
  $("export-button").addEventListener("click", exportHistory);
  $("alarm-feed").addEventListener("click", (e) => { const button = e.target.closest("[data-ack]"); if (button) command("ack", { alarm_id: Number(button.dataset.ack) }); });
  ["compare-a", "compare-b"].forEach((id) => $(id).addEventListener("change", renderComparison));
  $("comparison-body").addEventListener("click", (e) => { const button = e.target.closest("[data-scenario]"); if (button) { $("compare-a").value = button.dataset.scenario; renderComparison(); } });
  $("synoptic").addEventListener("click", (e) => { const item = e.target.closest("[data-equipment]"); if (item) { $("equipment-dialog").dataset.key = item.dataset.equipment; renderEquipment(item.dataset.equipment); $("equipment-dialog").showModal(); } });
  $("synoptic").addEventListener("keydown", (e) => { if ((e.key === "Enter" || e.key === " ") && e.target.dataset.equipment) { e.preventDefault(); e.target.dispatchEvent(new MouseEvent("click", { bubbles: true })); } });
  $("close-dialog").addEventListener("click", () => $("equipment-dialog").close());
  $("equipment-dialog").addEventListener("click", (e) => { if (e.target === $("equipment-dialog")) { const r = e.target.getBoundingClientRect(); if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) e.target.close(); } });
  document.querySelectorAll(".site-header nav a").forEach((a) => a.addEventListener("click", () => { document.querySelectorAll(".site-header nav a").forEach((item) => item.classList.toggle("active", item === a)); }));
  setInterval(() => { text("wall-clock", new Date().toLocaleTimeString("ru-RU")); }, 1000);
  createKpis();
  connected(false, "Подключение к локальному серверу");
  async function initialize() {
    try {
      const [status, scenarios] = await Promise.all([api("/api/status"), api("/api/scenarios")]);
      state.token = status.csrf_token; renderScenarios(scenarios); renderStatus(status);
      await refresh(true); await renderComparison();
    } catch (error) { connected(false, error.message); }
  }
  initialize();
  setInterval(() => { if (!state.token || !state.scenarios.length) initialize(); else refresh(); }, 1000);
})();
