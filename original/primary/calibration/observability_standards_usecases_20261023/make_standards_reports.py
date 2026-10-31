# -*- coding: utf-8 -*-
"""Trilingual evidence-review PDF: graphs, KPIs, traceability, use cases.
Full standards text is neither reproduced nor claimed to be reviewed.
"""
import json,csv
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image,KeepTogether
from xml.sax.saxutils import escape
P=Path(__file__).resolve().parent
stats=json.loads((P/"kpi_catalog_2025.json").read_text(encoding="utf-8"))
norms=json.loads((P/"standards_traceability_2026.json").read_text(encoding="utf-8"))
ucs=json.loads((P/"use_case_catalog_2026.json").read_text(encoding="utf-8"))
figs=json.loads((P/"graph_manifest.json").read_text(encoding="utf-8"))
K={m["id"]:m for m in stats}
pfont=Path("C:/Windows/Fonts")
pdfmetrics.registerFont(TTFont("Arial",str(pfont/"arial.ttf")))
pdfmetrics.registerFont(TTFont("ArialB",str(pfont/"arialbd.ttf")))
pdfmetrics.registerFontFamily("Arial",normal="Arial",bold="ArialB")
BRAND=colors.HexColor("#1D3550")
ACCENT=colors.HexColor("#266E9D")
STYLE={
"title":ParagraphStyle("title",fontName="ArialB",fontSize=17,leading=21,textColor=BRAND,spaceAfter=9),
"heading":ParagraphStyle("heading",fontName="ArialB",fontSize=12,leading=16,textColor=ACCENT,spaceBefore=11,spaceAfter=6),
"body":ParagraphStyle("body",fontName="Arial",fontSize=8.9,leading=12,spaceAfter=6),
"small":ParagraphStyle("small",fontName="Arial",fontSize=7,leading=9,spaceAfter=2),
"tiny":ParagraphStyle("tiny",fontName="Arial",fontSize=6.2,leading=7.8,spaceAfter=1),
"warn":ParagraphStyle("warn",fontName="ArialB",fontSize=9,leading=13,textColor=colors.HexColor("#A85C10"),spaceAfter=8)
}
L={
"RU":{
"title":"Дата-центр, бассейн, теплосеть: графики, показатели, стандартизация и юзкейсы",
"intro":"Инженерный аудиторский отчёт. 2025 год симуляции; проверка нормативных источников по состоянию на 23 октября 2026.",
"warning":"НЕ СЕРТИФИЦИРОВАНО. PUE=1,36 и ERF_proxy вычислены из синтетической нагрузки IT; оборудование, приборы, заводской COP и безопасная автоматика реального объекта не подтверждены.",
"summary":"1. Проверенные ключевые показатели",
"graphs":"2. Графики реальных результатов симуляций",
"norms":"3. Матрица нормативного соответствия (только проверочный реестр)",
"usecases":"4. Каталог юзкейсов и испытаний",
"closing":"5. Следующие доказательства для прохождения аудита",
"closure":"Необходимо получить годовые E_IT и E_DC со счётчиков, отдельный E_REUSE на границе DC, подписанные заводские температурные карты HP и низкотемпературного HX, действующие STN с полной проверкой текста, гидравлическую P&ID, SLD/UPS, протоколы аппаратного испытания аварийных функций и подпись инженера. Симуляционный PASS не равен соответствию стандарту.",
"metric_labels":["Показатель","Значение","Единица","Статус / формула"],
"norm_labels":["Норма / подсистема","Проверка / подтверждение","Состояние"],
"uc_labels":["Юзкейс","Результат","Исходные условия и ожидание"],
"plotnote":"Полная галерея: Engineering_Dashboard_2026.html; каждый SVG приложен отдельно.",
"passnote":"PASS означает проверку существующих численных выходных данных, BLOCKED означает отсутствие обязательных измерений или аппаратных испытаний."},
"SK":{
"title":"Dátové centrum a bazén: grafy, ukazovatele, normy a príklady použitia",
"intro":"Výskumný audit. Modelový rok 2025; stav referenčných noriem k 23.10.2026.",
"warning":"NIE JE CERTIFIKOVANÉ. PUE=1.36 a ERF proxy sú vypočítané zo syntetického IT zaťaženia, nie z kalibrovaných meraní. Reálna bezpečnosť a COP zariadení nie sú overené.",
"summary":"1. Výsledné overené modelové ukazovatele",
"graphs":"2. Grafy overených numerických výstupov",
"norms":"3. Matica normových požiadaviek (register, nie osvedčenie)",
"usecases":"4. Prípady použitia a testy",
"closing":"5. Chýbajúce dôkazy pre technické schválenie",
"closure":"Zabezpečiť 12-mesačné kalibrované E_IT a E_DC, samostatný merač E_REUSE na hranici DC, výrobcom certifikované mapy tepelného výkonu/COP/PLR, plné aktuálne STN, projekty hydrauliky P&ID a elektro SLD/UPS, testy hardvérovej bezpečnosti a podpis autorizovaného projektanta. Numerický PASS nepreukazuje legálnu zhodu.",
"metric_labels":["Ukazovateľ","Hodnota","Jednotka","Stav / pôvod"],
"norm_labels":["Norma / oblasť","Overenie / dôkaz","Stav"],
"uc_labels":["Testovací prípad","Výsledok","Vstup a očakávanie"],
"plotnote":"Všetky grafy: Engineering_Dashboard_2026.html a samostatné SVG.",
"passnote":"PASS je numerický test v scenári; BLOCKED predstavuje nepreukázané merania, výrobný výber alebo fyzický test."},
"EN":{
"title":"Data centre and swimming pool: graphs, KPIs, standards and test use cases",
"intro":"Engineering research audit. Simulated operating year 2025; references reviewed on 23 October 2026.",
"warning":"NOT CERTIFIED. PUE=1.36 and ERF source proxy use synthetic IT loads, not real metered facility data. Vendor equipment performance, site conformity and physical safety interlocks are unverified.",
"summary":"1. Verified research metrics",
"graphs":"2. Plots from executed simulation outputs",
"norms":"3. Standards traceability (requirements register, NOT a certificate)",
"usecases":"4. Use cases and software test results",
"closing":"5. Evidence missing for genuine technical acceptance",
"closure":"Obtain 12-month calibrated E_IT and E_DC, independently metered E_REUSE at the DC perimeter, OEM heat/COP/PLR maps, complete effective STN text, signed hydraulic P&ID and electrical SLD/UPS, physical safety interlock FAT/SAT and qualified engineering review. Simulation PASS does not prove regulatory compliance.",
"metric_labels":["Metric","Value","Unit","Evidence / definition"],
"norm_labels":["Reference / domain","Required verification/evidence","Status"],
"uc_labels":["Use case","Result","Condition and expectation"],
"plotnote":"All 20 figures also appear in Engineering_Dashboard_2026.html and standalone SVG.",
"passnote":"PASS confirms an available software simulation assertion only. BLOCKED denotes missing physical or statutory evidence."}}
chart_selected=[x for x in figs if x["name"].startswith(("01_","02_","04_","05_","07_","08_","09_","10_","11_","12_","13_","14_","150_","151_","17_","19_"))]
def paras(s,sty="body"):return Paragraph(escape(str(s)).replace("\n","<br/>"),STYLE[sty])
def tbl(rows,widths,repeat=1,font=7):
 t=Table(rows,colWidths=widths,repeatRows=repeat,hAlign="LEFT")
 t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#D9EBF5")),
 ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F6F9FC")]),
 ("LINEBELOW",(0,0),(-1,-1),.25,colors.HexColor("#D3E0E8")),
 ("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),4),
 ("RIGHTPADDING",(0,0),(-1,-1),4),("TOPPADDING",(0,0),(-1,-1),5),
 ("BOTTOMPADDING",(0,0),(-1,-1),5)]))
 return t
def footer(canvas,doc):
 canvas.setFont("Arial",7);canvas.setFillColor(colors.grey)
 canvas.drawString(14*mm,10*mm,"DataCenter Heat Reuse | 2026-10-23 | "+doc._lang+" | SIMULATION ONLY")
 canvas.drawRightString(A4[0]-14*mm,10*mm,str(doc.page))
def make(lang):
 l=L[lang]
 dst=P/("Standards_Graphs_Usecases_"+lang+".pdf")
 if dst.exists():raise FileExistsError(str(dst))
 doc=SimpleDocTemplate(str(dst),pagesize=A4,leftMargin=14*mm,rightMargin=14*mm,
   topMargin=17*mm,bottomMargin=17*mm)
 doc._lang=lang
 flow=[paras(l["title"],"title"),paras(l["intro"]),paras(l["warning"],"warn"),
 paras(l["summary"],"heading")]
 main=["E_IT","E_recovered_source","E_rejected_IT","Heat_pool_direct","Heat_district_HP35",
 "Electric_district_HP35","Backup_gas_thermal","Pool_peak_temperature",
 "Pool_hours_above_28","Source_overallocation_peak","ERF_source_proxy",
 "ERF_reportable","WUE_reportable"]
 rows=[[paras(t,"small") for t in l["metric_labels"]]]
 for key in main:
  x=next(m for m in stats if m["id"]==key)
  v=x["value"]
  val="MISSING" if v is None else f"{v:,.3f}"
  rows.append([paras(key,"small"),paras(val,"small"),paras(x["unit"],"tiny"),
   paras(x["evidence"]+"; "+x["definition"],"tiny")])
 flow.extend([tbl(rows,[51*mm,25*mm,27*mm,80*mm]),Spacer(1,5*mm),paras(l["graphs"],"heading"),paras(l["plotnote"])])
 for plot in chart_selected:
  path=P/"charts"/plot["png"]
  if not path.exists():raise FileNotFoundError(path)
  flow.extend([paras(plot["name"].replace("_"," "),"small"),
    Image(str(path),width=177*mm,height=94*mm,kind="proportional"),Spacer(1,3*mm)])
 flow.extend([PageBreak(),paras(l["norms"],"heading"),
   paras("56 entries across 22 disciplines. Full licensed standards NOT reviewed; status cannot be marked compliant.")])
 rows=[[paras(v,"tiny") for v in l["norm_labels"]]]
 for s in norms:
  rows.append([paras(s["id"]+" | "+s["standard_reference"]+" | "+s["domain"],"tiny"),
   paras(s["normative_check_to_confirm"]+"; Evidence: "+s["required_evidence"],"tiny"),
   paras(s["priority"]+" | "+s["evidence_status"],"tiny")])
 flow.append(tbl(rows,[59*mm,89*mm,35*mm]))
 flow.extend([PageBreak(),paras(l["usecases"],"heading"),paras(l["passnote"])])
 rows=[[paras(v,"tiny") for v in l["uc_labels"]]]
 for u in ucs:
  rows.append([paras(u["id"]+" | "+u["title"],"tiny"),
   paras(u["status"],"tiny"),
   paras(u["preconditions"]+" / "+u["expected_response"],"tiny")])
 flow.append(tbl(rows,[56*mm,22*mm,105*mm]))
 flow.extend([PageBreak(),paras(l["closing"],"heading"),paras(l["closure"])])
 flow.extend([paras("Source pages: https://www.iso.org/standard/30134-2 ; https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj ; https://normy.normoff.gov.sk/norma/139372/?lang=en ; https://www.ashrae.org/technical-resources/topics-and-initiatives/ai-data-center/introduction-and-purpose","small")])
 doc.build(flow,onFirstPage=footer,onLaterPages=footer)
 print("REPORT_PDF_CREATED",lang,dst.stat().st_size)
for lang in ("SK","RU","EN"):make(lang)
