# Карта зависимостей v0.3

Главная цепочка причинности:

`IT load -> available waste heat -> HX -> temperature lift -> COP -> HP electricity -> direct heat/storage/gas -> OPEX + CO2 + exergy`

| Параметр | На что влияет напрямую | Что меняется дальше | Главные KPI |
|---|---|---|---|
| `P_IT,max`, `u(t)` | количество тепла DC | загрузка HX/HP | coverage, ERF, curtailment |
| `PUE` | полная энергия DC | denominator ERF/ERE | ERF, ERE |
| `recovery_fraction` | доступное source heat | HP heat potential | coverage, gas, curtailment |
| `T_source` | temperature lift | COP, HP electricity | COP, OPEX, CO2 |
| `HX effectiveness` | heat to evaporator | HP utilization | coverage |
| `HX approach_K` | effective source temperature | temperature lift | COP |
| `T_supply` | hot-side temperature | lift | COP, exergy |
| `T_return` | возможность низкотемпературной интеграции | будущая гидравлика | pump power, usable heat |
| `HP max MW` | peak thermal output | unmet peak | gas backup |
| `storage MWh` | перенос энергии во времени | curtailment -> useful heat | coverage, gas |
| charge/discharge MW | скорость storage | доступность на пиках | gas, SOC |
| outdoor temperature | heat demand + DH temperature | temporal mismatch | coverage, storage need |
| electricity price | cost HP | dispatch/economics | OPEX, LCOH, payback |
| gas price | backup cost | ценность heat reuse | savings, payback |
| grid CO2 factor | HP emissions | net decarbonization | CO2 saving |

## Ключевая зависимость: temperature lift

$$\Delta T=T_{sink}-T_{source}$$

При модели Карно:

$$COP\propto\frac{T_h}{T_h-T_c}$$

Поэтому одновременно полезны две стратегии: поднять температуру тепла на стороне DC и снизить требуемую температуру теплосети.

## Почему высокий COP не равен высокому coverage

При ограниченном source heat:

$$Q_{out}=Q_{source}\frac{COP}{COP-1}$$

При росте COP уменьшается электрическая доля в выходном тепле. Coverage дополнительно ограничивается мощностью HP, формой спроса, recovery fraction и совпадением спроса с доступным теплом во времени. Поэтому COP нельзя использовать как единственный показатель проекта.

## Почему storage не решает сезонность автоматически

100 MWh при тепловой нагрузке порядка 10 MW - это примерно 10 часов идеального переноса энергии. Это полезно для суточного mismatch, но недостаточно для переноса летнего избытка в зимний сезон.

Для seasonal storage нужен отдельный компонент с другой физикой, потерями, ограничениями мощности и CAPEX.

## Узкие места, которые специально сделаны заменяемыми

1. `make_inputs` - synthetic -> real weather/telemetry.
2. `dc_source` - constant recovery -> cooling-system model.
3. `heat_exchanger` - effectiveness -> epsilon-NTU / manufacturer data.
4. `heat_pump` - Carnot surrogate -> manufacturer map / compressor model.
5. `heat_demand` - degree-day -> measured load / building model.
6. `storage_step` - one-node -> stratified/PCM/thermochemical.
7. dispatch loop - rule based -> LP/MILP/MPC.
8. economics - constant tariffs -> hourly prices, NPV, ownership model.

Так проект можно усложнять вертикально по одному блоку, не превращая всю систему в монолит.
