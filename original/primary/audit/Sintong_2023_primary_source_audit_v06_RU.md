# Source №9 — Sintong (2023), первичный аудит математики v0.6
СТАТУС: PARTIAL PRIMARY. Полный PDF сохранён в sources/papers/09_Sintong_Stockholm_2023.pdf, 71 стр.
Автор: Jeremy Ericsson Sintong, Uppsala University, Master Thesis, Stockholm techno-economic study (2023).
Университетский источник: https://www.diva-portal.org/smash/get/diva2%3A1780867/FULLTEXT01.pdf
Граница: air-cooled DC with server model, indirect airside economizer (IASE), hot-aisle HX, vapor-compression HP, DH supply (market model). Четыре конфигурации A1...A4. Не путать с Frankfurt или Espoo.

## Первичная карта уравнений (номера и страницы оригинального PDF)
### Сервер / ИТ / охлаждение (PDF стр. 27–30)
Eq3: P_server=P_IT+P_server_fan.
Eq4: эмпирическая аппроксимация P_IT(U_cpu,T_die), текстовое извлечение формулы повреждено; перепроверить визуально до использования.
Eq5: T_die=-34.42 U^2+58.60 U+48.61 [°C]. U в ДОЛЯХ от 0 до 1; иначе физически абсурд.
Eq6: T_amb=19.74 U+20.53 [°C].
Eq7: R_total=(T_die-T_amb)/P_IT=0.14+17440/RPM^1.56 [K/W]. Сверить все коэффициенты, знак и диапазон RPM с Ham et al [27], original.
Eq8: P_sfan(RPM)=7.07e-12 RPM^3 - 2.72e-8 RPM^2 +2.61e-4 RPM [W]; эмпирический диапазон, за пределами измерений не экстраполировать.
Eq9: DeltaT_server=-0.341 T_amb+17.058 [K]; эмпирическая зависимость.
Eq10: P_total=N_servers*P_server; 150 racks×42 slots×2 servers=12600 servers как сценарное допущение.
Eq11–14: empirical chiller/CRAH electrical model; alpha=.32 beta=.11 gamma=.63, idle CRAH=7–10% peak. Размерности P_sfmax и f требуют независимой проверки.

### Free cooling и HX (PDF стр. 30–32)
Eq15: T_RA_star=T_RA+epsilon*HX_flow_ratio*(T_OA-T_RA).
Eq16: HX_flow_ratio=(m_dot_OA+m_dot_RA)/(2*m_dot_RA).
Проверка: при пассивном HX T_RA_star обязан быть между T_OA и T_RA. Если epsilon*HX_flow_ratio>1, Eq15 может давать overshoot; необходимо указать область допустимого расхода/корректную формулу.
Eq17: cross-flow epsilon-NTU для обоих несмешивающихся потоков, PDF text extraction повреждает скобки и степени: НЕЛЬЗЯ копировать, пока не проверена страница визуально.
Eq18: при C_min/C_max<=0.01 автор использует epsilon=1-exp(-UA/C_min); проверить асимптотику.
Eq19: T_RA_out=T_RA-epsilon*(C_min/C_RA)*(T_RA-T_HPevap_in).
Eq20: Q_HX=epsilon*C_min*(T_RA-T_HPevap_in).
UA=500 [W/m2K]×38 [m2] =19000 W/K: историческое авторское параметрическое предположение, проверить применимость к выбранному DC.
Проверки: Q_HX>=0 при положительном перепаде, Q_HX<=C_min*DeltaT, баланс обеих сторон, pinch.

### Компрессор HP + доставка (PDF стр. 33)
Eq21: m_dot_refrig=Q_DC_cooling/(h_evap_out-h_s) [kg/s], знак величин требует проверки.
Eq22: **как НАПЕЧАТАНО:** Q_DC_cooling=m_dot_air*cp_air*(T_SA-T_server_out).
Риск SIGN: типичный T_server_out>T_SA, следовательно, RHS <0. Если Q_DC_cooling должен обозначать положительную отводимую мощность, нужно (+): m_dot*cp*(T_server_out-T_SA). Возможно автор использует «поток из воздушного контрольного объёма» со знаком минус, но тогда Eq21 и Eq24 должны придерживаться той же конвенции. НЕЛЬЗЯ исправлять без проверки и доказательства.
Eq23: P_comp=m_dot_refrig*(h_discharge_is-h_suction)/eta_comp.
Eq24 **как извлечено из PDF**: Q_DH=Q_DC_cooling+P_comp/eta_supp,DH, eta_supp=0.97 и описано как ~3% тепловых потерь. Для пассивной доставки физическая функция должна быть Q_DH_delivered=eta_supp*(Q_evap+P_comp), а не увеличение P_comp на 1/eta. Подозрение: inconsistency/loss accounting. Нужна ВИЗУАЛЬНАЯ проверка Eq24 и авторского кода.
Eq25 COP=Q_DH/P_comp, но если Q_DH ПОСЛЕ теплопотерь, это системный net COP, не compressor-only heat pump COP. Отдельные метрики COP_HP и COP_DH_net.

### KPI + экономика (PDF стр. 34–39)
Eq26 PUE=E_DC_total/E_IT; Eq27/28 build per A1...A4 including HP electric consumption only if WHR.
Eq29 ERF=Q_DH/E_DC_total and Eq30 ERE=(E_DC_total-Q_DH)/E_IT=(1-ERF)*PUE.
Eq31/32 SPFthermal=Q_DH/(E_DC_total-E_IT), SPF_IT=Q_DH/E_IT; Eq33 HSPF=Q_DH/P_comp.
RISKS: Eq33 numerically duplicates Eq25 at ONE timestep; true 'seasonal' requires sum_t(Q*dt)/sum_t(P*dt), NOT arithmetic average of hourly ratios.
Eq34 OPEX(t)=ElectricPower(t)*price_elec(t)-Q_DH(t)*price_DH(t). When power MW and tariff EUR/MWh, daily/year cashflow needs multiplication by dt [h]; do not silently assume dt=1 for all solvers.
Eq35 LCO=sum_i OPEX_i/(1+r)^i; if claiming maximum viable CAPEX, compare saved LCO of a BASELINE vs candidate, not a signed total raw LCO.

## Verification test vectors to implement (independent source audit, NOT adopted formula)
SIGN-22: T_SA=20C,T_out=35C,m=1 kg/s,cp=1005J/kg K. Eq22 produces -15.075 kW but positive recovered/removed heat convention yields +15.075 kW.
LOSS-24: Q_evap=7.2MW,P_comp=2.8MW,eta=0.97. Physical generated Q_hot=10MW, delivered net=9.7MW. Eq24-as-extracted gives 7.2+2.8/.97>10MW (a loss apparently increases output). NEED corroboration with original source.
FREE-15: epsilon*HX_flow_ratio must not exceed 1 without additional constraints; enforce outlet temp bounds.
KPI-33: annual SPF=sum_t Q_hot(t)*dt / sum_t P_comp(t)*dt; cannot assume mean_t COP(t) unless P weights constant.
PRICE-34: P[MW]*price[EUR/MWh]*dt[h]=EUR; no missing dt.

## Источники допущений и дальнейшие действия
Ham et al. [27] referenced for Eq3–7/9; Rahmani [22] Eq11–14; Park [38] free-cooling Eq15–16; HX theory [28], [53]; CoolProp [29] Eq21–25; Stockholm Exergi [5] + NordPool and Meteonorm for prices/weather.
Не маркировать «подтверждённой» без чтения оригиналов [27]/[22]/[38] и проверки страницы Eq17/Eq24 визуально.
Ожидаемый факт из abstract: +FC & WHR reduces cooling energy by 55.6% vs FC alone, PUE 1.95→1.52; итоговый KPI не принимать за независимую проверку при использовании той же модели/данных.
