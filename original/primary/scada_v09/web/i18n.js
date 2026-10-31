"use strict";
/* Operator UI localisation only: raw tag names, CSV, QA, STOP and PLC isolation never change. */
(() => {
  const supported = ["ru", "sk", "en"];
  const translations = [
    ["Обзор SCADA","Prehľad SCADA","SCADA overview"],
    ["Разделы","Sekcie","Sections"],
    ["Мнемосхема","Synoptická schéma","Synoptic view"],
    ["Тренды","Trendy","Trends"],
    ["История","História","History"],
    ["Сценарии","Scenáre","Scenarios"],
    ["Локальный сервер","Lokálny server","Local server"],
    ["Подключение…","Pripájanie…","Connecting…"],
    ["Нет связи","Bez spojenia","Disconnected"],
    ["СИМУЛЯЦИЯ · D_SYNTHETIC","SIMULÁCIA · D_SYNTHETIC","SIMULATION · D_SYNTHETIC"],
    ["Нативный CSV Simulink v08 · качество D · бассейн 500 м³ · физические устройства не подключены","Pôvodné CSV Simulink v08 · kvalita D · bazén 500 m³ · fyzické zariadenia nie sú pripojené","Native Simulink v08 CSV · quality D · 500 m³ pool · no physical devices connected"],
    ["Аппаратные действия отсутствуют в этой системе","Hardvérové ovládanie v tomto systéme nie je dostupné","Hardware control is not available in this system"],
    ["REAL CONTROL / PLC ОТКЛЮЧЕНО","REÁLNE RIADENIE / PLC VYPNUTÉ","REAL CONTROL / PLC DISABLED"],
    ["Нет свежих данных:","Žiadne nové údaje:","No fresh data:"],
    ["Показаны последние полученные значения D_SYNTHETIC; управление временно недоступно.","Zobrazené sú posledné prijaté hodnoty D_SYNTHETIC; ovládanie je dočasne nedostupné.","Showing last received D_SYNTHETIC values; controls are temporarily unavailable."],
    ["STOP АКТИВЕН","STOP AKTÍVNY","STOP ACTIVE"],
    ["Воспроизведение заблокировано сохранённым флагом STOP. Снятие флага — только вручную оператором.","Prehrávanie je blokované uloženým príznakom STOP. Zrušiť ho smie iba operátor ručne.","Playback is blocked by the persistent STOP flag. Only the operator can clear it manually."],
    ["ОПЕРАТОРСКАЯ ПАНЕЛЬ","OPERÁTORSKÝ PANEL","OPERATOR DASHBOARD"],
    ["Тепло, которое работает.","Teplo, ktoré má zmysel.","Making waste heat useful."],
    ["Дата-центр → теплообмен → бассейн","Dátové centrum → výmenník → bazén","Data centre → heat exchanger → pool"],
    ["ОЖИДАНИЕ","ČAKANIE","WAITING"],
    ["ВОСПРОИЗВЕДЕНИЕ","PREHRÁVANIE","PLAYING"],
    ["ПРОГОН ЗАВЕРШЁН","SIMULÁCIA DOKONČENÁ","RUN COMPLETE"],
    ["ПАУЗА","PAUZA","PAUSED"],
    ["ч модели","h modelu","model h"],
    ["отсчётов","vzoriek","samples"],
    ["отсчёта","vzorky","samples"],
    ["отсчёт","vzorka","sample"],
    ["СЦЕНАРИЙ / SCENÁR","SCENÁR","SCENARIO"],
    ["Сценарий / Scenár","Scenár","Scenario"],
    ["Сценарий A","Scenár A","Scenario A"],
    ["Сценарий B","Scenár B","Scenario B"],
    ["Сценарий","Scenár","Scenario"],
    ["Загрузка…","Načítavanie…","Loading…"],
    ["Воспроизвести","Prehrať","Play"],
    ["В начало сценария","Na začiatok scenára","Reset scenario"],
    ["СКОРОСТЬ","RÝCHLOSŤ","SPEED"],
    ["Отсчётов в секунду","Vzoriek za sekundu","Samples per second"],
    ["отсч./с","vzor./s","samples/s"],
    ["ПОЗИЦИЯ","POZÍCIA","POSITION"],
    ["Перейти к отсчёту CSV","Prejsť na vzorku CSV","Seek to CSV sample"],
    ["Управление локальным воспроизведением","Ovládanie lokálneho prehrávania","Local replay controls"],
    ["Текущие показатели","Aktuálne ukazovatele","Current indicators"],
    ["Доступное тепло DC","Dostupné teplo DC","Available DC heat"],
    ["Тепло в бассейн","Teplo do bazéna","Heat to pool"],
    ["Температура бассейна","Teplota bazéna","Pool temperature"],
    ["Модельный риск IT","Modelové riziko IT","Modelled IT risk"],
    ["Электричество ТН","Elektrický príkon TČ","Heat-pump electricity"],
    ["Энергия в TES","Energia v TES","TES stored energy"],
    ["Отдача в теплосеть","Dodávka do CZT","District heating delivery"],
    ["Отвод REJECT A + B","Odvod REJECT A + B","Heat rejection A + B"],
    ["Источник Q_DC_source_raw:","Zdroj Q_DC_source_raw:","Source Q_DC_source_raw:"],
    ["Запрос модели:","Požiadavka modelu:","Model demand:"],
    ["Запрос Q_DH_req:","Požiadavka Q_DH_req:","Demand Q_DH_req:"],
    ["Не обработано:","Neodvedené:","Unhandled:"],
    ["исходный отсчёт","pôvodná vzorka","original sample"],
    ["Индикатор модели, не температура CPU","Indikátor modelu, nie teplota CPU","Model indicator, not CPU temperature"],
    ["значение из CSV","hodnota z CSV","value from CSV"],
    ["ёмкость не документирована","kapacita nie je zdokumentovaná","capacity not documented"],
    ["Тепловой контур","Tepelný okruh","Thermal circuit"],
    ["События","Udalosti","Events"],
    ["Активных состояний:","Aktívnych stavov:","Active conditions:"],
    ["Активных тревог нет","Žiadne aktívne alarmy","No active alarms"],
    ["Ожидание данных","Čakanie na údaje","Waiting for data"],
    ["Только симуляция · качество D","Iba simulácia · kvalita D","Simulation only · quality D"],
    ["События появятся после загрузки CSV.","Udalosti sa zobrazia po načítaní CSV.","Events will appear after CSV loads."],
    ["Событий пока нет.","Zatiaľ žiadne udalosti.","No events yet."],
    ["Состояния определяются по флагам исходного CSV.","Stavy sa určujú z príznakov pôvodného CSV.","Conditions are derived from original CSV flags."],
    ["Квитирование сохраняется только локально. Исходная модель и оборудование не изменяются.","Potvrdenie sa ukladá len lokálne. Pôvodný model ani zariadenia sa nemenia.","Acknowledgements remain local. The source model and equipment are unchanged."],
    ["Квитировать","Potvrdiť","Acknowledge"],
    ["Квитировано","Potvrdené","Acknowledged"],
    ["КВИТИРОВАНО","POTVRDENÉ","ACKNOWLEDGED"],
    ["КРИТИЧЕСКОЕ","KRITICKÉ","CRITICAL"],
    ["ПРЕДУПРЕЖДЕНИЕ","VAROVANIE","WARNING"],
    ["ИНФОРМАЦИЯ","INFORMÁCIA","INFORMATION"],
    ["СНЯТО","UKONČENÉ","CLEARED"],
    ["Событие","Udalosť","Event"],
    ["Критическое","Kritické","Critical"],
    ["Модельный риск IT; не фактическая температура CPU","Modelové riziko IT; nie skutočná teplota CPU","Modelled IT risk; not an actual CPU temperature"],
    ["Неотведённое тепло > 1 W (порог отображения)","Neodvedené teplo > 1 W (prah zobrazenia)","Unhandled heat > 1 W (display threshold)"],
    ["Тепловая утечка > 1 W (порог отображения)","Únik tepla > 1 W (prah zobrazenia)","Heat leakage > 1 W (display threshold)"],
    ["Защёлка безопасности · Bezpečnostná západka","Bezpečnostná západka","Safety interlock latch"],
    ["Расхождение датчиков · Nesúlad snímačov","Nesúlad snímačov","Sensor disagreement"],
    ["Отказ расхода · Porucha prietoku","Porucha prietoku","Flow failure"],
    ["E_STOP в исходной симуляции","E_STOP v pôvodnej simulácii","E_STOP in source simulation"],
    ["Аварийный флаг исходной модели","Havarijný príznak pôvodného modelu","Emergency flag in source model"],
    ["Недопустимое значение датчика в модели","Neplatná hodnota snímača v modeli","Invalid model sensor value"],
    ["Перегрев по флагу модельного датчика","Prehriatie podľa príznaku modelového snímača","Overtemperature flag from model sensor"],
    ["Отказ основного клапана","Porucha hlavného ventilu","Primary valve failure"],
    ["Отказ резервного клапана","Porucha záložného ventilu","Backup valve failure"],
    ["Утечка при нулевой команде модели","Únik pri nulovom povele modelu","Leakage at zero model command"],
    ["STOP сохранён: воспроизведение заблокировано","STOP uložený: prehrávanie je blokované","STOP persisted: replay blocked"],
    ["Каждый отсчёт — из модели.","Každá vzorka pochádza z modelu.","Every sample comes from the model."],
    ["ИСТОЧНИК D_SYNTHETIC","ZDROJ D_SYNTHETIC","SOURCE D_SYNTHETIC"],
    ["Окно","Okno","Window"],
    ["24 часа","24 hodín","24 hours"],
    ["48 часов","48 hodín","48 hours"],
    ["Все доступные","Všetky dostupné","All available"],
    ["Распределение тепла","Rozdelenie tepla","Heat distribution"],
    ["Температуры и риск IT","Teploty a riziko IT","Temperatures and IT risk"],
    ["Тренд тепловых мощностей по реальным отсчётам CSV","Trend tepelných výkonov z pôvodných vzoriek CSV","Heat-flow trends from original CSV samples"],
    ["Тренд температуры бассейна, датчиков и модельного индикатора IT","Trend teploty bazéna, snímačov a modelového indikátora IT","Pool, sensor and modelled IT temperature trends"],
    ["Наведите для значений · нажмите для перехода · легенда скрывает ряды","Kurzorom zobrazíte hodnoty · kliknutím prejdete na vzorku · legenda skryje krivky","Hover for values · click to seek · use legend to hide series"],
    ["T_IT_model_C — модельный индикатор риска, не температура CPU.","T_IT_model_C je modelový indikátor rizika, nie teplota CPU.","T_IT_model_C is a modelled risk indicator, not CPU temperature."],
    ["Не обработано","Neodvedené","Unhandled"],
    ["Бассейн","Bazén","Pool"],
    ["Теплосеть","CZT","District heat"],
    ["IT риск*","IT riziko*","IT risk*"],
    ["Датчик 1","Snímač 1","Sensor 1"],
    ["Датчик 2","Snímač 2","Sensor 2"],
    ["Нет исходных отсчётов для отображения","Žiadne pôvodné vzorky na zobrazenie","No source samples to display"],
    ["Историк / Historian","Historian","Historian"],
    ["Экспорт CSV","Export CSV","Export CSV"],
    ["Посещённые отсчёты текущего сценария из SQLite. Повторное воспроизведение не дублирует записи. Экспорт сохраняет исходные поля.","Navštívené vzorky aktuálneho scenára zo SQLite. Opakované prehrávanie neduplikuje záznamy. Export zachová pôvodné polia.","Visited samples of the current scenario from SQLite. Replay does not duplicate records. Export preserves source fields."],
    ["Строк на странице","Riadkov na stránku","Rows per page"],
    ["Отсчёт","Vzorka","Sample"],
    ["Последняя запись¹","Posledný zápis¹","Last recorded¹"],
    ["Качество","Kvalita","Quality"],
    ["Загрузка истории…","Načítava sa história…","Loading history…"],
    ["Назад","Späť","Previous"],
    ["Далее","Ďalej","Next"],
    ["В SQLite пока нет посещённых отсчётов.","V SQLite zatiaľ nie sú navštívené vzorky.","No visited samples in SQLite yet."],
    ["уникальных записей SQLite · текущий сценарий","jedinečných záznamov SQLite · aktuálny scenár","unique SQLite records · current scenario"],
    ["Время локальной записи в часовом поясе браузера; cas_h — время модели.","Čas miestneho zápisu v časovom pásme prehliadača; cas_h je čas modelu.","Local record time in the browser time zone; cas_h is model time."],
    ["Сравнение сценариев","Porovnanie scenárov","Scenario comparison"],
    ["ПОЛНЫЕ ИСХОДНЫЕ ПРОГОНЫ","ÚPLNÉ PÔVODNÉ BEHY","COMPLETE SOURCE RUNS"],
    ["Сводные показатели по всем исходным отсчётам каждого сценария. Энергия = ΣQ · 900 с; сравнение не меняет воспроизведение.","Súhrny všetkých pôvodných vzoriek jednotlivých scenárov. Energia = ΣQ · 900 s; porovnanie nemení prehrávanie.","Summary metrics over every original sample in each scenario. Energy = ΣQ · 900 s; comparison does not change playback."],
    ["исходные данные","pôvodné údaje","source data"],
    ["Сравнение температуры бассейна двух полных сценариев","Porovnanie teploty bazéna pre dva úplné scenáre","Pool temperature comparison of two full scenarios"],
    ["Отсчёты","Vzorky","Samples"],
    ["В бассейн","Do bazéna","To pool"],
    ["Отвод","Odvod","Rejected"],
    ["Не обработано,","Neodvedené,","Unhandled,"],
    ["Источник","Zdroj","Source"],
    ["Показать сценарий на графике A","Zobraziť scenár v grafe A","Show scenario on chart A"],
    ["Модельный индикатор IT. TES: процент заряда не вычисляется без подтверждённой ёмкости. Пропуски данных отображаются как «—».","Modelový indikátor IT. Percentuálny SOC zásobníka TES sa bez overenej kapacity neurčuje. Chýbajúce údaje sa zobrazia ako „—“.","Modelled IT indicator. TES charge percentage cannot be calculated without confirmed capacity. Missing data appear as “—”."],
    ["Происхождение и технические ограничения","Pôvod údajov a technické obmedzenia","Provenance and technical limitations"],
    ["Это локальное воспроизведение нативных CSV Simulink v08. Новые значения телеметрии не генерируются. Изменение скорости меняет только частоту чтения отсчётов; исходный шаг — 900 секунд. Номинальная продолжительность прогона — 168 часов.","Toto je lokálne prehrávanie pôvodných CSV Simulink v08. Nové telemetrické údaje sa nevytvárajú. Rýchlosť mení len frekvenciu prehrávania; pôvodný krok je 900 sekúnd. Nominálna dĺžka behu je 168 hodín.","This locally replays native Simulink v08 CSV files. No new telemetry is generated. Speed changes only how often samples are read; the source step is 900 seconds. Nominal run length is 168 hours."],
    ["stateflow_mode отображается числом из CSV. T_IT_model_C не является фактической температурой CPU. Энергия TES: E_TES_J / 3 600 000. Аппаратные действия и PLC API отсутствуют.","stateflow_mode sa zobrazuje ako číslo z CSV. T_IT_model_C nie je skutočná teplota CPU. Energia TES: E_TES_J / 3 600 000. Hardvérové akcie a PLC API nie sú dostupné.","stateflow_mode is shown as its CSV numeric value. T_IT_model_C is not an actual CPU temperature. TES energy: E_TES_J / 3,600,000. No hardware actions or PLC API exist."],
    ["Исходные параметры","Pôvodné parametre","Source parameters"],
    ["Оборудование","Zariadenie","Equipment"],
    ["Закрыть","Zavrieť","Close"],
    ["Чтение CSV · качество D · управление устройствами отключено","Čítanie CSV · kvalita D · riadenie zariadení vypnuté","CSV readout · quality D · equipment controls disabled"],
    ["Обновление:","Aktualizácia:","Updated:"],
    ["Получено:","Prijaté:","Received:"],
    ["качеcтво D","kvalita D","quality D"],
    ["качество D","kvalita D","quality D"],
    ["Исходные параметры · D_SYNTHETIC","Pôvodné parametre · D_SYNTHETIC","Source parameters · D_SYNTHETIC"],
    ["Источник текущего сценария:","Zdroj aktuálneho scenára:","Current scenario source:"],
    ["строк","riadkov","rows"],
    ["Независимый QA v08:","Nezávislá kontrola QA v08:","Independent v08 QA:"],
    ["классификация QA:","klasifikácia QA:","QA classification:"],
    ["Классификация всех отображаемых данных:","Klasifikácia všetkých zobrazených údajov:","Classification of all displayed data:"],
    ["статус не предоставлен","stav nie je dostupný","status unavailable"],
    ["Нет токена локальной сессии. Дождитесь подключения.","Chýba token lokálnej relácie. Počkajte na pripojenie.","No local session token. Wait for connection."],
    ["Событие квитировано локально","Udalosť bola potvrdená lokálne","Event acknowledged locally"],
    ["Сравнение недоступно:","Porovnanie nie je dostupné:","Comparison unavailable:"],
    ["Некорректная классификация источника: ожидается","Neplatná klasifikácia zdroja: očakáva sa","Invalid source classification: expected"],
    ["Подключение к локальному серверу","Pripájanie k lokálnemu serveru","Connecting to local server"],
    ["Дата-центр / Datacentrum","Dátové centrum / Datacentrum","Data centre / Datacentrum"],
    ["Теплообменник / Výmenník","Výmenník tepla","Heat exchanger"],
    ["Тепловой насос / Tepelné čerpadlo","Tepelné čerpadlo","Heat pump"],
    ["Бассейн / Bazén · 500 м³","Bazén · 500 m³","Pool · 500 m³"],
    ["Накопитель / Akumulácia TES","Akumulátor tepla / TES","Thermal energy storage / TES"],
    ["Теплосеть / Centrálne zásobovanie teplom","Centrálne zásobovanie teplom","District heating network"],
    ["Отвод тепла / Odvod tepla A + B","Odvod tepla A + B","Heat rejection A + B"],
    ["T_IT_model_C — модельный индикатор риска. Это не измерение температуры CPU.","T_IT_model_C je modelový indikátor rizika. Nie je to meranie teploty CPU.","T_IT_model_C is a modelled risk indicator, not a CPU temperature measurement."],
    ["Отображаются исходные физические потоки и флаги модели. Значения флагов показаны без интерпретации команд.","Zobrazené sú pôvodné tepelné toky a príznaky modelu. Príznaky sa neinterpretujú ako povely.","Original model heat flows and flags are shown. Flags are not interpreted as commands."],
    ["COP и stateflow_mode — исходные значения CSV; названия числовых состояний не назначаются.","COP a stateflow_mode sú pôvodné hodnoty CSV; číselné stavy nemajú priradené mená.","COP and stateflow_mode are original CSV values; numeric states are not assigned names."],
    ["Временная координата cas_h берётся без изменения из CSV. Температура относится к модели бассейна.","Časová súradnica cas_h je priamo z CSV. Teplota patrí modelu bazéna.","Time coordinate cas_h comes unchanged from CSV. Temperature refers to the pool model."],
    ["Энергия в кВт·ч = E_TES_J / 3 600 000. SOC (%) не вычисляется: подтверждённая ёмкость накопителя не документирована. Общая линия TES функционально объединяет заряд и разряд.","Energia v kWh = E_TES_J / 3 600 000. SOC (%) sa neurčuje: overená kapacita akumulátora nie je zdokumentovaná. Linka TES spája nabíjanie a vybíjanie.","Energy in kWh = E_TES_J / 3,600,000. SOC (%) is not calculated because storage capacity is unverified. The TES connection represents charge and discharge."],
    ["Мощности в ваттах — нативные значения Simulink. Отображение не отправляет команд в теплосеть.","Výkony vo wattoch sú pôvodné hodnoty Simulink. Zobrazenie neposiela povely do CZT.","Power values in watts are native Simulink data. The display sends no district heating commands."],
    ["Основной и резервный отвод показываются раздельно. Q_unhandled_W — неотведённая мощность в исходной модели.","Hlavný a záložný odvod sa zobrazujú samostatne. Q_unhandled_W je neodvedený výkon pôvodného modelu.","Main and backup rejection are shown separately. Q_unhandled_W is unhandled power in the source model."],
    ["Штатный режим · Zdravý","Bežná prevádzka · Zdravý","Normal operation · Healthy"],
    ["Заклинивание основного клапана","Zaseknutý hlavný ventil","Primary valve stuck"],
    ["Оба клапана заклинены","Oba ventily zaseknuté","Both valves stuck"],
    ["REJECT A отключён, резерв доступен","REJECT A vypnutý, záloha dostupná","REJECT A offline, backup available"],
    ["Оба REJECT отключены, без shedding","Oba REJECT vypnuté, bez odľahčenia","Both REJECT offline, no shedding"],
    ["Оба REJECT отключены, со shedding","Oba REJECT vypnuté, s odľahčením","Both REJECT offline, with shedding"],
    ["Общее смещение датчиков · Bias","Spoločný posun snímačov · Bias","Common sensor bias"],
    ["Комбинированная авария со shedding","Kombinovaná porucha s odľahčením","Combined failure with shedding"],
    ["ДАТА-ЦЕНТР","DÁTOVÉ CENTRUM","DATA CENTRE"],
    ["ТЕПЛООБМЕН","VÝMENNÍK","HEAT EXCHANGER"],
    ["ТЕПЛОВОЙ НАСОС","TEPELNÉ ČERPADLO","HEAT PUMP"],
    ["БАССЕЙН","BAZÉN","POOL"],
    ["НАКОПИТЕЛЬ TES","AKUMULÁTOR TES","TES STORAGE"],
    ["ТЕПЛОСЕТЬ","CZT","DISTRICT HEAT"],
    ["ОТВОД A / HLAVNÝ","ODVOD A / HLAVNÝ","REJECT A / MAIN"],
    ["ОТВОД B / ZÁLOŽNÝ","ODVOD B / ZÁLOŽNÝ","REJECT B / BACKUP"],
    ["ПРЯМОЙ ТЕПЛООБМЕН / Q_HX_phys","PRIAMY PRENOS TEPLA / Q_HX_phys","DIRECT HEAT TRANSFER / Q_HX_phys"],
    ["ОБЪЁМ 500 м³ · T_pool_C","OBJEM 500 m³ · T_pool_C","VOLUME 500 m³ · T_pool_C"],
    ["СХЕМА ФУНКЦИОНАЛЬНАЯ · ЛИНИИ АКТИВНЫ ПРИ ПОТОКЕ ИЗ CSV · НАЖМИТЕ НА ОБОРУДОВАНИЕ","FUNKČNÁ SCHÉMA · TOKY Z CSV · KLIKNITE NA ZARIADENIE","FUNCTIONAL DIAGRAM · FLOW FROM CSV · SELECT EQUIPMENT"],
    ["Тепло DC","Teplo DC","DC heat"],
    ["ОТВОД","ODVOD","REJECTION"],
    ["ЗНАЧЕНИЯ","HODNOTY","VALUES"],
    ["Отсчёт ","Vzorka ","Sample "]
  ];
  const dictionaries = { sk: new Map(translations.map(([r, sk]) => [r, sk])), en: new Map(translations.map(([r, , en]) => [r, en])) };
  const sorted = translations.map(row => row[0]).filter(s => s.length >= 4).sort((a,b) => b.length-a.length);
  let lang = "ru";
  try { const fromQuery = new URLSearchParams(location.search).get("lang");
    const remembered = localStorage.getItem("dchr_scada_lang");
    lang = supported.includes(fromQuery) ? fromQuery : supported.includes(remembered) ? remembered : "ru";
  } catch (_) { lang = "ru"; }
  const locale = () => ({ru:"ru-RU",sk:"sk-SK",en:"en-GB"})[lang];
  function t(source) {
    if (lang === "ru" || typeof source !== "string") return source;
    let result = source;
    const map = dictionaries[lang];
    for (const original of sorted) {
      if (result.includes(original)) result = result.split(original).join(map.get(original));
    }
    result = result.replace(/кВт·ч/g, "kWh").replace(/кВт/g, "kW")
      .replace(/(\d[\d\s,.]*) м³/g, "$1 m³")
      .replace(/(\d[\d\s,.]*) ч(?=\s|$|·)/g, "$1 h")
      .replace(/(\d[\d\s,.]*) с(?=\s|$|·)/g, "$1 s");
    return result;
  }
  const nodes = new WeakMap(), attributes = new WeakMap();
  function processText(node) {
    const current = node.nodeValue, existing = nodes.get(node);
    if (!existing || existing.rendered !== current) nodes.set(node, {source:current,rendered:current});
    const item = nodes.get(node), desired = t(item.source);
    if (desired !== current) { item.rendered = desired; node.nodeValue = desired; }
    else item.rendered = current;
  }
  function processAttrs(node) {
    if (!(node instanceof Element)) return;
    let cache = attributes.get(node);
    if (!cache) { cache = new Map(); attributes.set(node, cache); }
    for (const name of ["title","aria-label","placeholder"]) {
      if (!node.hasAttribute(name)) continue;
      const current = node.getAttribute(name), previous = cache.get(name);
      if (!previous || current !== previous.rendered) cache.set(name, {source:current,rendered:current});
      const item = cache.get(name), desired = t(item.source);
      if (desired !== current) { item.rendered = desired; node.setAttribute(name, desired); }
      else item.rendered = current;
    }
  }
  function scan(node) {
    if (node.nodeType === Node.TEXT_NODE) return processText(node);
    if (node.nodeType !== Node.ELEMENT_NODE && node.nodeType !== Node.DOCUMENT_NODE) return;
    if (node.nodeType === Node.ELEMENT_NODE) processAttrs(node);
    for (const child of node.childNodes) scan(child);
  }
  function apply() {
    document.documentElement.lang = lang;
    const select = document.getElementById("language-select");
    if (select) select.value = lang;
    scan(document.body);
  }
  function setLanguage(value) {
    if (!supported.includes(value)) return;
    lang = value;
    try { localStorage.setItem("dchr_scada_lang", value); } catch (_) {}
    try { const url = new URL(location.href); url.searchParams.set("lang", value); history.replaceState(history.state, "", url.pathname + url.search + url.hash); } catch (_) {}
    apply();
    window.dispatchEvent(new CustomEvent("scada-languagechange", {detail:{lang}}));
  }
  window.SCADA_I18N = {t, locale, current: () => lang, setLanguage, supported};
  document.addEventListener("DOMContentLoaded", () => {
    const select = document.getElementById("language-select");
    if (select) {
      select.value = lang;
      select.addEventListener("change", e => setLanguage(e.target.value));
    }
    apply();
    const observer = new MutationObserver(mutations => {
      for (const change of mutations) {
        if (change.type === "characterData") processText(change.target);
        if (change.type === "attributes") processAttrs(change.target);
        for (const node of change.addedNodes || []) scan(node);
      }
    });
    observer.observe(document.body,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:["title","aria-label","placeholder"]});
  });
})();
