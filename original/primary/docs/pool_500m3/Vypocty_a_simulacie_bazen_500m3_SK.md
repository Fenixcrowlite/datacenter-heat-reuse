# Výpočty bazéna 500 m³: zdroj dátové centrum
> Referenčná fyzikálna simulácia, nie kalibrovaný návrh.

## Energetická bilancia
$$\rho Vc_p\frac{dT}{dt}=\dot Q_{dod}-\dot Q_{vypar}-\dot Q_{konv}-\dot Q_{rad}-\dot Q_{pod}-\dot Q_{dop}-\dot Q_{ostatne}$$
$$E=\rho Vc_p(28-16)=6.9491\;\mathrm{MWh}$$

## Simulované varianty
| Prípad | Dosiahnutie 28 °C [h] | Dodané teplo [MWh] | Elektrina TČ [MWh] |
|---|---:|---:|---:|
| TC_75kW | 98.18 | 9.67 | 2.42 |
| TC_150kW | 47.43 | 10.86 | 2.72 |
| TC_300kW | 23.41 | 11.53 | 2.88 |
| VYMENNIK_150kW | 47.43 | 10.86 | 0.00 |
| TC_150kW_bez_krytu | 46.86 | 12.01 | 3.00 |
| TC_150kW_RH40 | 50.84 | 12.90 | 3.22 |
| TC_150kW_RH80 | 45.40 | 9.14 | 2.28 |

## Podmienky
- T0 = 16 °C, regulácia [27,8; 28,2] °C.
- Objem 500 m³, plocha 312,5 m², Tair = 29 °C, RH = 60 %.
- 08:00 až 20:00 otvorené; v noci kryt (redukcia výparu 90 %).
- COP TČ = 4, tepelná dodávka 75, 150 alebo 300 kW. Zdroj DC vetva max. 500 kW.
- Bilancia zdroja TČ: Qout=Qsource+Welectric.
- Model nekryje vykurovanie, ventiláciu ani odvlhčovanie budovy.

## Reprodukovateľné súbory
- Projektový model: matlab/pool_500m3/Bazen_DC_Ohrev_500m3_SK.slx
- MATLAB test: matlab/pool_500m3/spusti_simulaciu_bazena_sk.m
- Číselné údaje: results/pool_500m3_v01/vysledky_bazen_500m3.json
- PDF: Bazen_500m3_SK.pdf, Bazen_500m3_EN.pdf, Bazen_500m3_RU.pdf

## Zdroj metodiky
https://handbook.ashrae.org/Handbooks/A23/SI/A23_Ch06/a23_ch06_si.aspx