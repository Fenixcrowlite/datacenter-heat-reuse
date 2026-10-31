"""C95 independent source/parameter traceability audit; reads OneDrive, writes task-local only."""
import csv,hashlib,json,re
from pathlib import Path
D=Path(__file__).resolve().parent
PROJECT=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")
SOURCE=PROJECT/"sources"
C94=D.parent/"AUTONOMOUS_RUN_20261030_1755_DCHR_C94_HX_TEMPERATURE_ENVELOPE"/"C94_METADATA.json"
PINS={
    "source_catalog.md":"02e6eb9704486cae8aa0ed79745d2e1ac92621a4505134618468d6b7ccecc889",
    "parameter_registry.yaml":"e571b056d3616a3bf11d4bc2d2139f84cb3426c3039f61d881a89bb45beb40f2",
    "traceability_matrix_v0_2.csv":"a7b57a88b2042cb90a9c48bb94491a4748d0677ac5fdac2d4c31c0ab2e79ad19",
    "C94_METADATA.json":"6ea733cf7af0c5c406d42d0c8636175fa958bf417e886f91c31fbaacc99a4eaf"}
FLAGS=("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def guard():
    for root in (D,D.parent,D.parent.parent,PROJECT):
        for name in FLAGS:
            if (root/name).exists():raise RuntimeError("STOP_ACTIVE "+str(root/name))
def scalar(yaml,key):
    m=re.search(r"^\s*"+re.escape(key)+r":\s*\{value:\s*([0-9.]+),\s*class:\s*([A-D])\}",yaml,re.M)
    if not m:raise RuntimeError("YAML_SCALAR_NOT_FOUND "+key)
    return float(m.group(1)),m.group(2)
def bounds(yaml,key):
    sec=yaml.split("uncertainty_v0_3:",1)
    if len(sec)!=2:raise RuntimeError("UNCERTAINTY_SECTION_MISSING")
    m=re.search(r"^\s*"+re.escape(key)+r":\s*\{[^\n]*?bounds:\s*\[([0-9.]+),\s*([0-9.]+)\],\s*class:\s*([A-D])",sec[1],re.M)
    if not m:raise RuntimeError("YAML_BOUNDS_NOT_FOUND "+key)
    return float(m.group(1)),float(m.group(2)),m.group(3)
def run():
    guard()
    paths={"source_catalog.md":SOURCE/"source_catalog.md",
           "parameter_registry.yaml":SOURCE/"parameter_registry.yaml",
           "traceability_matrix_v0_2.csv":SOURCE/"traceability_matrix_v0_2.csv",
           "C94_METADATA.json":C94}
    for name,p in paths.items():
        if sha(p)!=PINS[name]:raise RuntimeError("SOURCE_DRIFT "+name)
    catalog=paths["source_catalog.md"].read_text(encoding="utf-8-sig")
    nums=[int(x) for x in re.findall(r"(?m)^(\d+)\.\s",catalog)]
    if nums!=list(range(1,32)):raise RuntimeError("NOT_31_ORDERED_SOURCES")
    yaml=paths["parameter_registry.yaml"].read_text(encoding="utf-8-sig")
    meta=json.loads(C94.read_text(encoding="utf-8"))
    assert meta["synthetic"] is True and meta["measured"] is False
    assert meta["primary_source_signoffs_added"]==0
    t_base,t_class=scalar(yaml,"source_temperature_C_baseline")
    t_low,t_high,t_range_class=bounds(yaml,"source_temperature_C")
    eta_base,eta_class=scalar(yaml,"carnot_efficiency")
    eta_low,eta_high,_=bounds(yaml,"carnot_efficiency")
    cop_min,_=scalar(yaml,"cop_min");cop_max,_=scalar(yaml,"cop_max")
    hp_cap,_=scalar(yaml,"max_heat_output_MW")
    hx_approach,_=scalar(yaml,"approach_K")
    a=meta["assumptions"]
    with paths["traceability_matrix_v0_2.csv"].open(encoding="utf-8-sig",newline="") as f:
        trace=list(csv.DictReader(f))
    if len(trace)<8 or not any("HP COP" in r["Parameter_or_claim"] for r in trace):
        raise RuntimeError("TRACEABILITY_MATRIX_DRIFT")
    rows=[
        dict(parameter="source_inlet_C",C94=str(a["source_inlet_C"]),
             canonical=f"baseline {t_base:g} C; uncertainty [{t_low:g},{t_high:g}] C",
             class_C94="D",class_canonical=t_class,
             verdict="OUTSIDE_UNCERTAINTY_RANGE",
             action="Treat 18/25/35 C as a separate low-grade-source stress test; do not calibrate or merge as canonical."),
        dict(parameter="carnot_efficiency",C94=str(a["carnot_efficiency_assumed"]),
             canonical=f"baseline {eta_base:g}; uncertainty [{eta_low:g},{eta_high:g}]",
             class_C94="D",class_canonical=eta_class,verdict="OUTSIDE_UNCERTAINTY_RANGE",
             action="Compare eta 0.35 against registry 0.40-0.50 and vendor COP(T) before plant conclusions."),
        dict(parameter="COP_clamp",C94=str(a["COP_clamp"]),
             canonical=f"[{cop_min:g},{cop_max:g}]",class_C94="D",class_canonical="D",
             verdict="SCENARIO_OVERRIDE",
             action="Report 2-6 as C94-specific proxy; do not silently replace reference 2.2-7."),
        dict(parameter="HP_thermal_cap_MW",C94=str(a["HP_thermal_cap_MW"]),
             canonical=f"{hp_cap:g} MW (district network)",class_C94="D",class_canonical="D",
             verdict="DIFFERENT_SUBSYSTEM",
             action="0.3 MW pool-only HP is not the canonical 12 MW district HP; keep separate namespaces."),
        dict(parameter="source_evaporator_approach_K",C94=str(a["source_evaporator_approach_K"]),
             canonical=f"{hx_approach:g} K (HX approach)",class_C94="D",class_canonical="D",
             verdict="DIFFERENT_DEFINITION",
             action="8 K evaporator inlet assumption and 3 K HX approach are not interchangeable."),
        dict(parameter="source_flow_kg_s",C94=str(a["source_flow_kg_s"]),
             canonical="not present in reference_case_v0_3",class_C94="D",class_canonical="MISSING",
             verdict="UNTRACED_ASSUMPTION",
             action="Add pool-specific flow measurement or manufacturer interval to a reviewed parameter registry."),
        dict(parameter="source_min_outlet_C_and_pinch_K",
             C94=f"{a['source_min_outlet_C']} C; {a['pinch_at_source_outlet_K']} K",
             canonical="not present as a pool-loop contract",class_C94="D",class_canonical="MISSING",
             verdict="UNTRACED_ASSUMPTION",
             action="Obtain return-temperature constraints and HX/evaporator pinch datasheets."),
        dict(parameter="pool_RH_and_cover",C94=f"{a['relative_humidity']}; {a['cover_multiplier']}",
             canonical="not in district-heating parameter registry",class_C94="D",class_canonical="MISSING",
             verdict="UNTRACED_ASSUMPTION",
             action="Separate indoor pool HVAC/cover assumptions and calibrate with facility schedule.")
    ]
    assert len(rows)==8
    assert all(x["class_C94"]=="D" for x in rows)
    assert all(not(t_low<=t<=t_high) for t in a["source_inlet_C"])
    assert not eta_low<=a["carnot_efficiency_assumed"]<=eta_high
    assert a["HP_thermal_cap_MW"]!=hp_cap
    assert a["source_evaporator_approach_K"]!=hx_approach
    assert meta["primary_source_signoffs_added"]==0
    for p in (D/"C95_DRIFT_MATRIX.csv",D/"C95_AUDIT.json",D/"C95_FINDINGS.md"):
        if p.exists():raise RuntimeError("OUTPUT_EXISTS "+str(p))
    with (D/"C95_DRIFT_MATRIX.csv").open("x",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    report={"schema":"C95_SOURCE_TRACEABILITY_AUDIT_V1","task_id":"scc-2aab24704c2bd0",
            "catalog_entries_verified":len(nums),"catalog_not_formal_signoff":True,
            "primary_source_signoffs_added":0,"C94_synthetic":True,
            "drift_rows":len(rows),"verdict_counts":{v:sum(x["verdict"]==v for x in rows)
                for v in sorted(set(x["verdict"] for x in rows))},
            "input_sha256":PINS,"matrix_sha256":sha(D/"C95_DRIFT_MATRIX.csv"),
            "qa_internal":"9 explicit assertions PASS; 4 pinned SHA checks; 31 catalog IDs",
            "next":"Resolve C94 vs canonical scenario definitions; request measured source/flow and vendor COP, no source signoffs."}
    (D/"C95_AUDIT.json").write_text(json.dumps(report,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    lines=["# C95 | Аудит трассируемости C94","",
      "Каталог действительно содержит **31 пронумерованный источник**, но это **не 31 проверка первоисточников**. Формальных новых подтверждений: **0**.",
      "Все значения C94 классифицированы как **D (scenario)**, а не измерения или паспорт оборудования.","",
      "| Параметр | C94 | Каноническая запись | Вывод |","|---|---|---|---|"]
    for r in rows:lines.append(f"| {r['parameter']} | {r['C94']} | {r['canonical']} | {r['verdict']} |")
    lines+=["","**Критическое:** температурный диапазон C94 18/25/35 °C лежит вне текущего канонического интервала 38–50 °C, хотя 35 °C указан как отдельный baseline. COP eta=0,35 также вне 0,40–0,50. Это сценарные стресс-тесты, не ошибка вычисления и не новая калибровка.",
            "","**Не смешивать масштабы:** насос 0,3 MW для бассейна и насос 12 MW для районной сети относятся к разным подсистемам.",
            "","**Следующий шаг:** паспортная COP-карта и данные источника (T_in/T_out, расход, сезонность), UA/NTU и параметры бассейна. Не изменять canonical YAML до независимой проверки.",""]
    (D/"C95_FINDINGS.md").write_text("\n".join(lines),encoding="utf-8")
    print(json.dumps(report,indent=2,ensure_ascii=False))
if __name__=="__main__":run()
