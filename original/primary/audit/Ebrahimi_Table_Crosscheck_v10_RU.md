# №21 Ebrahimi et al. (2014): сверка первичных таблиц, v0.10

Оригинал: `sources/papers/21_Ebrahimi_2014.pdf`, 17 страниц, DOI `10.1016/j.rser.2013.12.007`.
SHA-256 оригинала: `4aaffa92f30b0d5aa9c7a7e58e5ff8cad3eb05c9f8969b079d6127aab1600a40`.

PDF стр. 6 / печатная 627, Table 6: cold aisle 10–32 °C, hot aisle 50–60 °C, rise over server 10–20 K, airflow 200–2500 CFM/rack, chiller water return 35 °C.
PDF стр. 6 / печатная 627, Table 8: water supply 20–60 °C (standard), 70–75 °C (maximum), server water rise 2–5 K, 5–10 GPM/rack.
PDF стр. 8 / печатная 629, Table 10 (liquid pump): secondary condenser cooling fluid outlet 45–90 °C. Table 11 (vapor compression): secondary condenser outlet about 90 °C.

Проверка математической совместимости Table 6: T_hot = T_cold + delta_T. Совместимые холодные температуры в пределах трёх напечатанных интервалов только 30–32 °C; например 32→50 °C с приростом 18 K. Крайняя комбинация 10→60 °C дала бы 50 K, что вне диапазона 10–20 K. Это НЕ доказательство ошибки авторов: табличные диапазоны агрегируют разные исследования, их экстремумы нельзя соединять в единый design point.

Возможное несоответствие: Table 10 с меткой liquid pump допускает 90 °C на вторичном выходе, тогда как исходный Marcinichen et al. [12] для pumped case в Table 9 даёт около 48 °C, а ~90 °C соответствует vapor compression. До сверки оригинала [12] этот диапазон нельзя применять как гарантированную температуру pump-only.

Тип доказательства: значения сверены с первичным PDF; интервальная арифметика проверяет математическое тождество; независимая экспериментальная валидация НЕ выполнена. Статус №21: PARTIAL_PRIMARY, fully_signed_off=NO.
