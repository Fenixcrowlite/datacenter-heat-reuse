# C95 | Аудит трассируемости C94

Каталог действительно содержит **31 пронумерованный источник**, но это **не 31 проверка первоисточников**. Формальных новых подтверждений: **0**.
Все значения C94 классифицированы как **D (scenario)**, а не измерения или паспорт оборудования.

| Параметр | C94 | Каноническая запись | Вывод |
|---|---|---|---|
| source_inlet_C | [18.0, 25.0, 35.0] | baseline 35 C; uncertainty [38,50] C | OUTSIDE_UNCERTAINTY_RANGE |
| carnot_efficiency | 0.35 | baseline 0.45; uncertainty [0.4,0.5] | OUTSIDE_UNCERTAINTY_RANGE |
| COP_clamp | [2.0, 6.0] | [2.2,7] | SCENARIO_OVERRIDE |
| HP_thermal_cap_MW | 0.3 | 12 MW (district network) | DIFFERENT_SUBSYSTEM |
| source_evaporator_approach_K | 8.0 | 3 K (HX approach) | DIFFERENT_DEFINITION |
| source_flow_kg_s | [0.5, 2.0, 8.0] | not present in reference_case_v0_3 | UNTRACED_ASSUMPTION |
| source_min_outlet_C_and_pinch_K | 12.0 C; 2.0 K | not present as a pool-loop contract | UNTRACED_ASSUMPTION |
| pool_RH_and_cover | 0.55; 0.15 | not in district-heating parameter registry | UNTRACED_ASSUMPTION |

**Критическое:** температурный диапазон C94 18/25/35 °C лежит вне текущего канонического интервала 38–50 °C, хотя 35 °C указан как отдельный baseline. COP eta=0,35 также вне 0,40–0,50. Это сценарные стресс-тесты, не ошибка вычисления и не новая калибровка.

**Не смешивать масштабы:** насос 0,3 MW для бассейна и насос 12 MW для районной сети относятся к разным подсистемам.

**Следующий шаг:** паспортная COP-карта и данные источника (T_in/T_out, расход, сезонность), UA/NTU и параметры бассейна. Не изменять canonical YAML до независимой проверки.
