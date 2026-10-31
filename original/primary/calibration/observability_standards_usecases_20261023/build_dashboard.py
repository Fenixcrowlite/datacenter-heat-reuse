# -*- coding: utf-8 -*-
"""Self-contained offline research dashboard; no remote access or JS data fetch."""
from pathlib import Path
import json,csv,html
P=Path(__file__).resolve().parent
k=json.loads((P/"kpi_catalog_2025.json").read_text(encoding="utf-8"))
std=json.loads((P/"standards_traceability_2026.json").read_text(encoding="utf-8"))
use=json.loads((P/"use_case_catalog_2026.json").read_text(encoding="utf-8"))
plots=json.loads((P/"graph_manifest.json").read_text(encoding="utf-8"))
assert len(k)>=30 and len(std)>=50 and len(use)>=30 and len(plots)>=18
counts={t:sum(row["status"]==t for row in use) for t in ("PASS","BLOCKED","FAIL")}
head="""<!doctype html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DCHR / Engineering observability & standards 2026</title><style>
:root{color-scheme:dark;--surface:#17273b;--base:#091321;--line:#2b4761;--accent:#81b8fc;--text:#e7eff8;--mute:#9caec3}
*{box-sizing:border-box}body{background:var(--base);color:var(--text);font:14px/1.5 system-ui,Segoe UI,Arial,sans-serif;max-width:1440px;margin:auto;padding:20px}
h1{font-size:27px;font-weight:700}h2{font-size:19px;margin:22px 0 9px}h3{font-size:15px;margin:0 0 6px}
p{color:var(--mute)}a{color:var(--accent)}
header{border-bottom:1px solid var(--line);padding-bottom:14px}
.nav{display:flex;flex-wrap:wrap;gap:8px}.nav a,.chip{padding:7px 11px;background:#18314d;border-radius:8px;text-decoration:none}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:10px;margin-top:12px}.tile{border:1px solid var(--line);border-radius:11px;background:var(--surface);padding:13px}
.big{font-size:27px;font-weight:700;color:#acd5ff}.hint{font-size:11px;color:var(--mute)}
.controls{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}
input,select,button{background:#122840;color:var(--text);border:1px solid #456884;padding:10px;border-radius:8px;font:inherit}
input{flex:1;min-width:165px}button{cursor:pointer}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px}
.item{border-radius:9px;border:1px solid var(--line);background:var(--surface);padding:12px;overflow-wrap:anywhere}
.item img{width:100%;height:165px;object-fit:contain;background:#fff;border-radius:6px}
.preview{display:block;width:100%;max-height:520px;object-fit:contain;background:#fff;border-radius:10px;padding:5px}
table{border-collapse:collapse;width:100%;table-layout:fixed}th,td{padding:9px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top;overflow-wrap:anywhere}
th{position:sticky;top:0;background:#17283c}.tablewrap{max-height:580px;overflow:auto;border:1px solid var(--line);border-radius:10px}
.green{color:#7bdbb2}.orange{color:#ffc07d}.red{color:#ff8e99}.grey{color:#9fb6cd}
small{color:var(--mute)}#details{max-height:330px;overflow:auto}
pre{white-space:pre-wrap;background:#17273a;padding:10px;border:1px solid #355271;border-radius:8px}
summary{cursor:pointer;font-weight:600}
</style></head><body>
<header><h1>DataCenter Heat Reuse · Инженерные метрики и стандарты</h1>
<p>Моделирование 2025 / редакции нормативов проверены 23.10.2026 · Инженерное исследование, не акт соответствия и не данные работающего объекта</p>
<div class="nav"><a href="#key">KPI</a><a href="#plots">Графики</a><a href="#norms">Нормативы</a><a href="#tests">Юзкейсы</a><a href="#sources">Область применимости</a></div></header>
<section id="key"><h2>Сводка воспроизводимых результатов</h2><div class="tiles" id="summary"></div>
<p>Факт измерения / модельный сценарий / отсутствие измерителя различаются отдельно. Никакой присвоенной сертификации нет.</p>
<h3>Каталог KPI</h3><div class="controls"><input id="ksearch" placeholder="Поиск метрики, единицы или формулы"><select id="kclass"><option value="">Все категории доказательств</option></select></div><div class="tablewrap"><table><thead><tr><th>Метрика</th><th>Значение</th><th>Единица</th><th>Происхождение / статус</th></tr></thead><tbody id="kbody"></tbody></table></div></section>
<section id="plots"><h2>Графики из 105 120 пятиминутных отсчётов на сценарий</h2>
<p>Каждый SVG можно открыть отдельно и увеличивать без потери качества. Выберите график или откройте всю галерею.</p>
<div class="controls"><select id="plotSelect"></select><a id="plotSVG" href="#">Открыть масштабируемый SVG</a></div>
<img id="plotBig" class="preview" alt="Engineering plot">
<details><summary>Все графики в галерее</summary><div class="grid" id="plotsGrid"></div></details></section>
<section id="norms"><h2>Реестр нормативных требований (не декларация соответствия)</h2>
<div class="controls"><input id="ssearch" placeholder="Стандарт, подсистема, требование, подтверждение"><select id="sprio"><option value="">Все приоритеты</option><option>P0</option><option>P1</option><option>P2</option></select><select id="sdomain"><option value="">Все подсистемы</option></select></div>
<div class="tablewrap"><table><thead><tr><th>ID / норма</th><th>Подсистема</th><th>Что проверить</th><th>Доказательство</th><th>Состояние</th></tr></thead><tbody id="sbody"></tbody></table></div></section>
<section id="tests"><h2>36 юзкейсов: результат проверки и блокирующие условия</h2>
<div class="controls"><input id="usearch" placeholder="Ищите отказ, сценарий или сигнал"><select id="ustatus"><option value="">Все</option><option>PASS</option><option>BLOCKED</option><option>FAIL</option></select></div>
<div class="tablewrap"><table><thead><tr><th>ID / сценарий</th><th>Входные условия</th><th>Ожидаемое поведение</th><th>Статус</th><th>Источник результата</th></tr></thead><tbody id="ubody"></tbody></table></div></section>
<section id="sources"><h2>Что необходимо для реальной аттестации</h2>
<p>Действительные измерения 8760h серверов, E_DC и E_IT, расход и температуру теплоносителя, счётчик E_REUSE на границе DC, аттестацию датчиков, заводские COP(Tsource,Tsink,PLR), реальные тепловые характеристики теплообменника, UPS/насосы/гидравлические схемы, испытания защиты, полный текст действующих STN и экспертизу ответственного проектировщика.</p>
<p>Базовые источники: <a href="https://www.iso.org/standard/30134-2">ISO 30134-2:2026</a>, <a href="https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj">EU 2024/1364</a>, <a href="https://normy.normoff.gov.sk/norma/139372/?lang=en">STN EN15288-1+A1</a>, <a href="https://normy.normoff.gov.sk/norma/128828/?lang=en">STN EN15288-2</a>.</p>
</section>
<script>
const DATA=__DATA__;
const $=q=>document.getElementById(q);
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=(v,n=2)=>v==null?'нет измерений':Number(v).toLocaleString('ru-RU',{maximumFractionDigits:n});
const KPI=Object.fromEntries(DATA.kpis.map(k=>[k.id,k]));
const tiles=[['Графиков',DATA.plots.length,'20 самостоятельных SVG/PNG'],['KPI',DATA.kpis.length,'Единицы, определение, качество'],['Нормативных пунктов',DATA.std.length,'Проверять по полным текстам'],['Юзкейсов PASS',DATA.use.filter(u=>u.status==='PASS').length,'Только в пределах симуляции'],['Юзкейсов BLOCKED',DATA.use.filter(u=>u.status==='BLOCKED').length,'Недостаточно физической проверки'],['Использовано серверного тепла',fmt(KPI.E_recovered_source.value,0)+' МВт·ч','Моделирование, не измерено'],['Макс. температура воды',fmt(KPI.Pool_peak_temperature.value)+' °C','Численное значение'],['PUE',fmt(KPI.PUE_assumed.value),'Это допущение, не KPI объекта']];
$('summary').innerHTML=tiles.map(x=>'<div class="tile"><small>'+esc(x[0])+'</small><div class="big">'+esc(x[1])+'</div><div class="hint">'+esc(x[2])+'</div></div>').join('');
const classes=[...new Set(DATA.kpis.map(k=>k.evidence))].sort();classes.forEach(v=>$('kclass').innerHTML+='<option>'+esc(v)+'</option>');
const domains=[...new Set(DATA.std.map(x=>x.domain))].sort();domains.forEach(v=>$('sdomain').innerHTML+='<option>'+esc(v)+'</option>');
function match(...x){return x.some(z=>String(z??'').toLowerCase().includes(this));}
function renderK(){let term=$('ksearch').value.toLowerCase(),status=$('kclass').value;
let rows=DATA.kpis.filter(k=>(!status||k.evidence===status)&&match.call(term,k.id,k.unit,k.definition,k.standard));
$('kbody').innerHTML=rows.map(k=>'<tr><td><b>'+esc(k.id)+'</b></td><td>'+esc(fmt(k.value,4))+'</td><td>'+esc(k.unit)+'</td><td><small>'+esc(k.definition)+'</small><div class="'+(k.value==null?'orange':'grey')+'">'+esc(k.evidence)+'</div></td></tr>').join('')}
function renderS(){let term=$('ssearch').value.toLowerCase(),p=$('sprio').value,dom=$('sdomain').value;
let rows=DATA.std.filter(k=>(!p||k.priority===p)&&(!dom||k.domain===dom)&&match.call(term,k.standard_reference,k.domain,k.subject,k.normative_check_to_confirm,k.required_evidence));
$('sbody').innerHTML=rows.map(k=>'<tr><td><b>'+esc(k.id)+'</b> · <a href="'+esc(k.source_url)+'" target="_blank" rel="noopener">'+esc(k.standard_reference)+'</a></td><td>'+esc(k.domain)+'<div class="orange">'+esc(k.priority)+'</div></td><td>'+esc(k.normative_check_to_confirm)+'</td><td>'+esc(k.required_evidence)+'</td><td class="orange">'+esc(k.evidence_status)+'</td></tr>').join('')}
function renderU(){let term=$('usearch').value.toLowerCase(),status=$('ustatus').value;
let rows=DATA.use.filter(k=>(!status||k.status===status)&&match.call(term,k.title,k.domain,k.preconditions,k.expected_response,k.metric_ids,k.id));
$('ubody').innerHTML=rows.map(k=>'<tr><td><b>'+esc(k.id)+'</b> · '+esc(k.title)+'</td><td>'+esc(k.preconditions)+'</td><td>'+esc(k.expected_response)+'</td><td class="'+(k.status==='PASS'?'green':k.status==='FAIL'?'red':'orange')+'">'+esc(k.status)+'</td><td>'+esc(k.evidence_file)+'</td></tr>').join('')}
function choosePlot(){let i=Number($('plotSelect').value),p=DATA.plots[i];$('plotBig').src='charts/'+p.png;$('plotSVG').href='charts/'+p.svg}
DATA.plots.forEach((p,i)=>{$('plotSelect').innerHTML+='<option value="'+i+'">'+esc(p.name)+'</option>'});
$('plotsGrid').innerHTML=DATA.plots.map(p=>'<div class="item"><a href="charts/'+esc(p.svg)+'"><img src="charts/'+esc(p.png)+'" alt="'+esc(p.name)+'"></a><small>'+esc(p.name)+'</small></div>').join('');
['ksearch','kclass'].forEach(x=>$(x).addEventListener('input',renderK));
['ssearch','sprio','sdomain'].forEach(x=>$(x).addEventListener('input',renderS));
['usearch','ustatus'].forEach(x=>$(x).addEventListener('input',renderU));
$('plotSelect').addEventListener('change',choosePlot);
renderK();renderS();renderU();choosePlot();
</script></body></html>"""
payload=json.dumps({"kpis":k,"std":std,"use":use,"plots":plots},ensure_ascii=False)
page=head.replace("__DATA__",payload)
(P/"Engineering_Dashboard_2026.html").write_text(page,encoding="utf-8")
print("OFFLINE_DASHBOARD_READY",len(page),"bytes",len(plots),"plots",len(std),"standards",len(use),"usecases")
