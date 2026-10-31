from pathlib import Path
import csv
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / 'results' / 'figures'
OUT = ROOT / 'presentation' / 'DataCenter_Heat_Reuse_v0_1_RU.pptx'
CSV = ROOT / 'results' / 'scenario_summary.csv'

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

NAVY = RGBColor(18, 37, 58)
BLUE = RGBColor(34, 105, 160)
LIGHT = RGBColor(241, 245, 249)
DARK = RGBColor(30, 41, 59)
MUTED = RGBColor(71, 85, 105)
WHITE = RGBColor(255, 255, 255)
GREEN = RGBColor(38, 128, 95)

with CSV.open(encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))
best = rows[-1]

def add_title(slide, title, subtitle=None):
    box = slide.shapes.add_textbox(Inches(0.65), Inches(0.35), Inches(12), Inches(0.7))
    p = box.text_frame.paragraphs[0]
    p.text = title; p.font.size = Pt(27); p.font.bold = True; p.font.color.rgb = NAVY
    if subtitle:
        sb = slide.shapes.add_textbox(Inches(0.67), Inches(1.03), Inches(11.8), Inches(0.45))
        sp = sb.text_frame.paragraphs[0]; sp.text = subtitle; sp.font.size = Pt(12); sp.font.color.rgb = MUTED

def add_footer(slide, n):
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.65), Inches(7.18), Inches(12.0), Inches(0.015))
    line.fill.solid(); line.fill.fore_color.rgb = RGBColor(203,213,225); line.line.fill.background()
    tb = slide.shapes.add_textbox(Inches(11.9), Inches(7.2), Inches(0.6), Inches(0.2))
    p=tb.text_frame.paragraphs[0]; p.text=str(n); p.font.size=Pt(8); p.font.color.rgb=MUTED; p.alignment=PP_ALIGN.RIGHT

def bullets(slide, items, x=0.8, y=1.55, w=5.8, h=4.8, size=18):
    tb=slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf=tb.text_frame; tf.word_wrap=True
    for i,item in enumerate(items):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph(); p.text=item; p.font.size=Pt(size); p.font.color.rgb=DARK; p.space_after=Pt(11); p.level=0
    return tb

def add_image(slide, filename, x, y, w=None, h=None):
    path = FIG / filename
    if w and h: slide.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(w), Inches(h))
    elif w: slide.shapes.add_picture(str(path), Inches(x), Inches(y), width=Inches(w))
    else: slide.shapes.add_picture(str(path), Inches(x), Inches(y), height=Inches(h))

def metric_card(slide, x, y, w, label, value, note=''):
    sh=slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(1.25))
    sh.fill.solid(); sh.fill.fore_color.rgb=LIGHT; sh.line.color.rgb=RGBColor(203,213,225)
    t=slide.shapes.add_textbox(Inches(x+0.2), Inches(y+0.15), Inches(w-0.4), Inches(0.95)); tf=t.text_frame
    p=tf.paragraphs[0]; p.text=value; p.font.size=Pt(25); p.font.bold=True; p.font.color.rgb=BLUE
    p2=tf.add_paragraph(); p2.text=label; p2.font.size=Pt(11); p2.font.color.rgb=DARK
    if note:
        p3=tf.add_paragraph(); p3.text=note; p3.font.size=Pt(8); p3.font.color.rgb=MUTED

# 1 cover
s=prs.slides.add_slide(prs.slide_layouts[6])
bg=s.background.fill; bg.solid(); bg.fore_color.rgb=NAVY
box=s.shapes.add_textbox(Inches(0.9), Inches(1.35), Inches(11.5), Inches(1.7)); tf=box.text_frame
p=tf.paragraphs[0]; p.text='РЈС‚РёР»РёР·Р°С†РёСЏ С‚РµРїР»Р° РґР°С‚Р°-С†РµРЅС‚СЂР°'; p.font.size=Pt(38); p.font.bold=True; p.font.color.rgb=WHITE
p2=tf.add_paragraph(); p2.text='РњРѕРґСѓР»СЊРЅР°СЏ РјР°С‚РµРјР°С‚РёС‡РµСЃРєР°СЏ РјРѕРґРµР»СЊ, MATLAB/Simulink Рё СЃС†РµРЅР°СЂРЅС‹Р№ СЌРєСЃРїРµСЂРёРјРµРЅС‚'; p2.font.size=Pt(21); p2.font.color.rgb=RGBColor(191,219,254)
p3=tf.add_paragraph(); p3.text='Engineering reference model v0.1 В· 8760 h'; p3.font.size=Pt(14); p3.font.color.rgb=RGBColor(203,213,225); p3.space_before=Pt(18)

# 2 motivation
s=prs.slides.add_slide(prs.slide_layouts[6]); add_title(s,'1. Р—Р°РґР°С‡Р° Рё РёСЃСЃР»РµРґРѕРІР°С‚РµР»СЊСЃРєРёР№ РІРѕРїСЂРѕСЃ')
bullets(s,[
'Р”Р°С‚Р°-С†РµРЅС‚СЂ СЃРѕР·РґР°С‘С‚ РїРѕС‡С‚Рё РїРѕСЃС‚РѕСЏРЅРЅС‹Р№ РїРѕС‚РѕРє РЅРёР·РєРѕРїРѕС‚РµРЅС†РёР°Р»СЊРЅРѕРіРѕ С‚РµРїР»Р°, Р° РіРѕСЂРѕРґСЃРєРѕР№ СЃРїСЂРѕСЃ СЃРёР»СЊРЅРѕ РјРµРЅСЏРµС‚СЃСЏ РїРѕ СЃРµР·РѕРЅСѓ.',
'РљР»СЋС‡РµРІРѕР№ РІРѕРїСЂРѕСЃ: РєРѕРіРґР° С‚РµРїР»Рѕ С‚РµС…РЅРёС‡РµСЃРєРё Рё СЌРєРѕРЅРѕРјРёС‡РµСЃРєРё РІС‹РіРѕРґРЅРѕ РїРѕРґРЅСЏС‚СЊ С‚РµРїР»РѕРІС‹Рј РЅР°СЃРѕСЃРѕРј Рё РѕС‚РґР°С‚СЊ РІ Р¦Рў?',
'РњРѕРґРµР»СЊ РґРѕР»Р¶РЅР° РїРѕР·РІРѕР»СЏС‚СЊ РјРµРЅСЏС‚СЊ cooling technology, heat pump, storage, С‚РµРїР»РѕСЃРµС‚СЊ Рё СЃС‚СЂР°С‚РµРіРёСЋ СѓРїСЂР°РІР»РµРЅРёСЏ РЅРµР·Р°РІРёСЃРёРјРѕ РґСЂСѓРі РѕС‚ РґСЂСѓРіР°.',
'v0.1 РЅРµ РєРѕРїРёСЂСѓРµС‚ РѕРґРёРЅ РєРµР№СЃ, Р° СЃРѕР·РґР°С‘С‚ РІРѕСЃРїСЂРѕРёР·РІРѕРґРёРјСѓСЋ РїР»Р°С‚С„РѕСЂРјСѓ РґР»СЏ РїРѕСЃР»РµРґСѓСЋС‰РµР№ РєР°Р»РёР±СЂРѕРІРєРё.' ],0.8,1.55,11.6,4.8,19); add_footer(s,2)

# 3 literature anchors
s=prs.slides.add_slide(prs.slide_layouts[6]); add_title(s,'2. РќР° С‡С‘Рј РѕСЃРЅРѕРІР°РЅР° Р°СЂС…РёС‚РµРєС‚СѓСЂР° РјРѕРґРµР»Рё','РљР»СЋС‡РµРІС‹Рµ РєРµР№СЃС‹ РёР· РёСЃС…РѕРґРЅРѕРіРѕ СЃРїРёСЃРєР° РёР· 31 СЂР°Р±РѕС‚С‹')
bullets(s,[
'Espoo (Wahlroos et al., 2017): СЃРёСЃС‚РµРјРЅР°СЏ РіРѕРґРѕРІР°СЏ СЃРёРјСѓР»СЏС†РёСЏ 20вЂ“60 MW waste heat; >95% С‡Р°СЃРѕРІ РёСЃРїРѕР»СЊР·РѕРІР°РЅРёСЏ РІ СЂР°СЃСЃРјРѕС‚СЂРµРЅРЅС‹С… СЃС†РµРЅР°СЂРёСЏС….',
'Frankfurt (JГјrgens et al., 2024): 144 GWh/a, 37 MWth HP + 20 MWth gas + peak storage; 97.5% РїРѕРєСЂС‹С‚РёСЏ РІ РёСЃСЃР»РµРґСѓРµРјРѕРј РєРµР№СЃРµ.',
'Varna / THUNDER (Verzino et al., 2026): heat pump + thermal/thermochemical storage + existing district-heating context.',
'OrГі et al. (2019): air-cooled DC РїРѕРєР°Р·С‹РІР°РµС‚, РїРѕС‡РµРјСѓ РЅР°Р»РёС‡РёРµ С‚РµРїР»Р° РµС‰С‘ РЅРµ РіР°СЂР°РЅС‚РёСЂСѓРµС‚ С…РѕСЂРѕС€СѓСЋ СЌРєРѕРЅРѕРјРёРєСѓ.' ],0.8,1.55,11.6,4.8,17); add_footer(s,3)

# 4 architecture
s=prs.slides.add_slide(prs.slide_layouts[6]); add_title(s,'3. РњРѕРґСѓР»СЊРЅР°СЏ Р°СЂС…РёС‚РµРєС‚СѓСЂР°')
# boxes
labels=[('IT load',0.7),('DC heat\nrecovery',2.55),('Heat pump',4.6),('Dispatch',6.55),('District\nheating',8.45),('Gas\nbackup',10.45)]
for lab,x in labels:
    sh=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(2.55), Inches(1.45), Inches(1.0)); sh.fill.solid(); sh.fill.fore_color.rgb=LIGHT; sh.line.color.rgb=BLUE
    tb=s.shapes.add_textbox(Inches(x+0.08), Inches(2.78), Inches(1.3), Inches(0.55)); p=tb.text_frame.paragraphs[0]; p.text=lab; p.font.size=Pt(14); p.font.bold=True; p.font.color.rgb=DARK; p.alignment=PP_ALIGN.CENTER
for x1,x2 in [(2.15,2.55),(4.0,4.6),(6.05,6.55),(8.0,8.45)]:
    a=s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x1), Inches(2.82), Inches(x2-x1), Inches(0.42)); a.fill.solid(); a.fill.fore_color.rgb=BLUE; a.line.fill.background()
a=s.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(7.05), Inches(3.75), Inches(0.45), Inches(0.7)); a.fill.solid(); a.fill.fore_color.rgb=GREEN; a.line.fill.background()
sh=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.25), Inches(4.6), Inches(2.0), Inches(0.85)); sh.fill.solid(); sh.fill.fore_color.rgb=RGBColor(236,253,245); sh.line.color.rgb=GREEN
p=s.shapes.add_textbox(Inches(6.4), Inches(4.86), Inches(1.7), Inches(0.35)).text_frame.paragraphs[0]; p.text='Thermal storage'; p.font.size=Pt(14); p.font.bold=True; p.font.color.rgb=GREEN; p.alignment=PP_ALIGN.CENTER
bullets(s,['РљР°Р¶РґС‹Р№ Р±Р»РѕРє РёРјРµРµС‚ Р·Р°РјРµРЅСЏРµРјС‹Р№ РёРЅС‚РµСЂС„РµР№СЃ: real telemetry, manufacturer COP map, PCM/TCM storage, MPC, hydraulic network.'],0.9,5.8,11.2,0.8,16); add_footer(s,4)

# 5 math
s=prs.slides.add_slide(prs.slide_layouts[6]); add_title(s,'4. РЇРґСЂРѕ РјР°С‚РµРјР°С‚РёС‡РµСЃРєРѕР№ РјРѕРґРµР»Рё')
bullets(s,[
'Р”РѕСЃС‚СѓРїРЅРѕРµ С‚РµРїР»Рѕ:  Qsrc(t) = О·rec В· PIT(t)',
'COP:  COP в‰€ О·C В· Th /(Th в€’ Tc)',
'РўРµРїР»Рѕ HP:  QHP = Qsrc В· COP/(COP в€’ 1)',
'РЎРїСЂРѕСЃ:  QDH = [QDHW + Qspace В· f(Tout)] / О·network',
'Storage:  Ek+1 = Ek(1в€’О»О”t) + О·cQcО”t в€’ QdО”t/О·d',
'Р‘Р°Р»Р°РЅСЃ:  QDH = QHP,direct + Qstorage,dis + Qgas' ],0.9,1.6,11.3,4.9,20); add_footer(s,5)

# 6 scenario parameters
s=prs.slides.add_slide(prs.slide_layouts[6]); add_title(s,'5. Р­РєСЃРїРµСЂРёРјРµРЅС‚: 4 РѕСЃРЅРѕРІРЅС‹С… СЃС†РµРЅР°СЂРёСЏ','РћРґРёРЅР°РєРѕРІС‹Рµ РїРѕРіРѕРґР°, IT-load, С‚РµРїР»РѕСЃРµС‚СЊ Рё С†РµРЅС‹; РјРµРЅСЏСЋС‚СЃСЏ cooling/source Рё storage')
headers=['РЎС†РµРЅР°СЂРёР№','T source','Recovery','Storage']
data=[['Air25','25 В°C','0.70','0 MWh'],['Liquid35','35 В°C','0.85','0 MWh'],['Warm45','45 В°C','0.90','0 MWh'],['Warm45 + storage','45 В°C','0.90','100 MWh']]
rows_n=len(data)+1; cols_n=4
table=s.shapes.add_table(rows_n,cols_n,Inches(1.25),Inches(2.0),Inches(10.8),Inches(3.0)).table
for c,h in enumerate(headers): table.cell(0,c).text=h
for r,row in enumerate(data,1):
    for c,v in enumerate(row): table.cell(r,c).text=v
for r in range(rows_n):
    for c in range(cols_n):
        cell=table.cell(r,c); cell.margin_left=Inches(.08); cell.margin_right=Inches(.08)
        for p in cell.text_frame.paragraphs: p.font.size=Pt(15); p.font.color.rgb=DARK; p.alignment=PP_ALIGN.CENTER
        if r==0: cell.fill.solid(); cell.fill.fore_color.rgb=NAVY; cell.text_frame.paragraphs[0].font.color.rgb=WHITE; cell.text_frame.paragraphs[0].font.bold=True
bullets(s,['Р¦РµРЅС‹ Рё emission factors Р·РґРµСЃСЊ вЂ” СЃС†РµРЅР°СЂРЅС‹Рµ РїР°СЂР°РјРµС‚СЂС‹, РЅРµ С‚РµРєСѓС‰Р°СЏ РєРѕС‚РёСЂРѕРІРєР° РЎР»РѕРІР°РєРёРё.'],1.25,5.45,10.7,0.7,14); add_footer(s,6)

# 7 headline results
s=prs.slides.add_slide(prs.slide_layouts[6]); add_title(s,'6. Р РµР·СѓР»СЊС‚Р°С‚ reference experiment','Warm 45 В°C + 100 MWh storage')
metric_card(s,0.8,1.65,2.65,'РџРѕРєСЂС‹С‚РёРµ СЃРїСЂРѕСЃР°',f"{float(best['Coverage'])*100:.1f}%")
metric_card(s,3.55,1.65,2.65,'РЎСЂРµРґРЅРёР№ COP',f"{float(best['MeanCOP']):.2f}")
metric_card(s,6.3,1.65,2.65,'Residual gas',f"{float(best['GasHeat_MWh'])/1000:.1f} GWh")
metric_card(s,9.05,1.65,2.65,'COв‚‚ saving*',f"{float(best['CO2SavingFraction'])*100:.1f}%",'*РїРѕ scenario EF')
metric_card(s,2.15,3.45,3.3,'Reused heat',f"{float(best['ReusedHeat_MWh'])/1000:.1f} GWh/a")
metric_card(s,5.65,3.45,3.3,'HP electricity',f"{float(best['HPElectric_MWh'])/1000:.1f} GWh/a")
metric_card(s,9.15,3.45,3.3,'OPEX saving*',f"в‚¬{float(best['OpexSaving_EUR'])/1e6:.2f} M/a",'*scenario prices')
bullets(s,['Р“Р»Р°РІРЅС‹Р№ СЃРјС‹СЃР» СЂРµР·СѓР»СЊС‚Р°С‚Р° РЅРµ РІ РєРѕРЅРєСЂРµС‚РЅРѕРј РµРІСЂРѕ-С‡РёСЃР»Рµ, Р° РІ РІРѕСЃРїСЂРѕРёР·РІРѕРґРёРјРѕРј СЌРЅРµСЂРіРµС‚РёС‡РµСЃРєРѕРј Р±Р°Р»Р°РЅСЃРµ Рё С‡СѓРІСЃС‚РІРёС‚РµР»СЊРЅРѕСЃС‚Рё Рє РїР°СЂР°РјРµС‚СЂР°Рј.'],1.0,5.45,11.3,0.8,15); add_footer(s,7)

# 8 scenario comparison
s=prs.slides.add_slide(prs.slide_layouts[6]); add_title(s,'7. РЎС†РµРЅР°СЂРёРё: С‚РµС…РЅРёС‡РµСЃРєРёР№ РєРѕРјРїСЂРѕРјРёСЃСЃ')
add_image(s,'01_scenario_comparison.png',2.15,1.35,w=9.0)
add_footer(s,8)

# 9 temp lift
s=prs.slides.add_slide(prs.slide_layouts[6]); add_title(s,'8. РўРµРјРїРµСЂР°С‚СѓСЂРЅС‹Р№ РїРѕРґСЉС‘Рј РѕРїСЂРµРґРµР»СЏРµС‚ COP')
add_image(s,'06_cop_temperature_lift_map.png',0.8,1.45,w=7.5)
bullets(s,['Source T в†‘ в†’ temperature lift в†“ в†’ COP в†‘.','DH supply T в†“ в†’ COP в†‘.','Р­С‚Рѕ СЃРІСЏР·С‹РІР°РµС‚ РІС‹Р±РѕСЂ liquid cooling СЃ РїРѕРєРѕР»РµРЅРёРµРј/СЂРµР¶РёРјРѕРј district heating.'],8.55,1.8,4.0,3.5,17); add_footer(s,9)

# 10 winter operation
s=prs.slides.add_slide(prs.slide_layouts[6]); add_title(s,'9. Р”РёРЅР°РјРёРєР°: РґРІРµ Р·РёРјРЅРёРµ РЅРµРґРµР»Рё')
add_image(s,'02_winter_operation.png',1.8,1.4,w=9.7)
add_footer(s,10)

# 11 storage
s=prs.slides.add_slide(prs.slide_layouts[6]); add_title(s,'10. Storage: РїРѕР»РµР·РµРЅ, РЅРѕ РёРјРµРµС‚ diminishing returns')
add_image(s,'07_storage_sensitivity.png',0.85,1.4,w=7.6)
bullets(s,['РќР°РєРѕРїРёС‚РµР»СЊ РїРµСЂРµРЅРѕСЃРёС‚ СЌРЅРµСЂРіРёСЋ РІРѕ РІСЂРµРјРµРЅРё, РЅРѕ РЅРµ РјРµРЅСЏРµС‚ СЃРµР·РѕРЅРЅСѓСЋ С„РёР·РёРєСѓ СЃРїСЂРѕСЃР°.','РџРѕСЃР»Рµ РѕРїСЂРµРґРµР»С‘РЅРЅРѕР№ С‘РјРєРѕСЃС‚Рё РґРѕРїРѕР»РЅРёС‚РµР»СЊРЅС‹Р№ MWh storage РґР°С‘С‚ РІСЃС‘ РјРµРЅСЊС€РёР№ СЌС„С„РµРєС‚.','РЎР»РµРґСѓСЋС‰РёР№ СЌС‚Р°Рї: daily vs seasonal storage Рё РѕРїС‚РёРјРёР·Р°С†РёСЏ СЂР°Р·РјРµСЂР°.'],8.65,1.75,3.8,4.0,16); add_footer(s,11)

# 12 limits roadmap
s=prs.slides.add_slide(prs.slide_layouts[6]); add_title(s,'11. РћРіСЂР°РЅРёС‡РµРЅРёСЏ v0.1 Рё РїСѓС‚СЊ Рє РїРѕР»РЅРѕС†РµРЅРЅРѕР№ РјРѕРґРµР»Рё')
bullets(s,[
'v0.1: lumped energy balance, synthetic weather/load, simplified COP, generic storage.',
'v0.2: СЂРµР°Р»СЊРЅС‹Рµ hourly weather/load + heat-exchanger UA/LMTD + manufacturer HP map.',
'v0.3: supply/return curve, hydraulic losses, stratified/PCM/thermochemical storage, exergy.',
'v0.4: CAPEX, NPV, LCOH, uncertainty and Monte-Carlo / Sobol sensitivity.',
'v1.0: calibrated Bratislava/selected city case + Simscape/MPC + telemetry/digital-twin interface.' ],0.85,1.55,11.5,4.8,18); add_footer(s,12)

# 13 sources
s=prs.slides.add_slide(prs.slide_layouts[6]); add_title(s,'12. РљР»СЋС‡РµРІС‹Рµ РёСЃС‚РѕС‡РЅРёРєРё')
bullets(s,[
'Wahlroos, M. et al. (2017). Energy 140, 1228вЂ“1238. DOI: 10.1016/j.energy.2017.08.078.',
'JГјrgens, B. et al. (2024). Int. J. Sustainable Energy Planning and Management. DOI: 10.54337/ijsepm.8149.',
'OrГі, E. et al. (2019). Sustainable Cities and Society 45, 522вЂ“542. DOI: 10.1016/j.scs.2018.12.012.',
'Verzino, A. et al. (2026). Energies 19(3), 800. DOI: 10.3390/en19030800.',
'Yuan, X. et al. (2023). Renewable and Sustainable Energy Reviews 188, 113777.',
'EU Directive 2023/1791 on energy efficiency.' ],0.85,1.55,11.6,4.9,15); add_footer(s,13)

prs.save(OUT)
print(OUT)


