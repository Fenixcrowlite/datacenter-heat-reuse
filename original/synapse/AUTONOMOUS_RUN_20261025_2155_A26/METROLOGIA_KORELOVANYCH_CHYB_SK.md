# DataCenter → bazén: korelované neistoty tepelného výkonu (nezávislý audit)

**Dátum:** 25. 10. 2026. **Stav:** analytický model a Monte Carlo overené, nie fyzická validácia. **Trieda údajov:** D, syntetické predpoklady. **Scope:** izolovaný audit; existujúce modely MATLAB, CSV a SCADA bez zmien.

## Východisko a fyzikálne veličiny

Prietokový odhad tepelného výkonu: **P = ρ cₚ (V̇/3600) (T₁−T₂)** [W], kde V̇ je v m³/h, ρ=997 kg/m³, cₚ=4182 J/(kg·K). Ilustračný príklad: V̇=30 m³/h, T₁=30 °C, T₂=27 °C, teda ΔT=3 K a **P=104,236 kW**. Predpokladané štandardné neistoty: u(V̇)=1,5 m³/h, u(T₁)=u(T₂)=0,2 K. Sú to predpoklady, nie kalibračné certifikáty.

Pre vektor x=[V̇,T₁,T₂] je kovariančná matica Σ a citlivostný vektor J=[ρcₚΔT/3600, ρcₚV̇/3600, −ρcₚV̇/3600]. Kombinovaná neistota prvého rádu je **u²(P)=J Σ Jᵀ**. Kovariancia meraní sa nesmie automaticky nastaviť na nulu. Neplatná (nie pozitívne semidefinitná) matica sa odmietne.

| Korelácia chýb T₁ a T₂ | u(ΔT) [K] | u(P) [kW] | Interpretácia |
|---:|---:|---:|---|
| 0,0 | 0,2828 | 11,124 | pôvodný nezávislý prípad |
| +0,9 | 0,0894 | 6,068 | spoločná teplotná odchýlka sa čiastočne vyruší |
| −0,9 | 0,3899 | 14,514 | protichodné chyby zväčšujú neistotu |

**Dôležité:** menšia vypočítaná neistota pri kladnej korelácii neznamená vyššiu presnosť skutočných snímačov. Rozhoduje meraná kovariancia a systematické chyby, nie zvolený príklad.

## Nelineárny súčin a priemerovanie

Pri spoločnom normálnom rozdelení prietoku F a teplotného rozdielu D platí E[FD]=μFμD+Cov(F,D) a Var(FD)=μF²Var(D)+μD²Var(F)+2μFμD Cov(F,D)+Var(F)Var(D)+Cov(F,D)². Model poskytuje aj tento presný *podmienený* gaussovský výpočet, nielen lineárnu aproximáciu. Monte Carlo: **3 × 80 000** nezávisle generovaných trojíc, pevné semeno 20261025; všetky tri analytické hodnoty overené s toleranciou 2,5 % štandardnej odchýlky.

Pri opakovaných vzorkách sa **systematická chyba prietoku neskracuje s √N**: pre 4 % systematickú a 1 % náhodnú štandardnú neistotu pri N=96 zostáva kombinovaná relatívna neistota približne **4,0013 %**, nie 0,41 %.

## Zmena teploty celého bazéna za 15 minút

Pre 500 m³ vody a Δt=900 s platí P_storage=ρcₚV(T₂−T₁)/Δt. Ak majú dve časové merania štandardnú neistotu 0,2 K, výsledná neistota odhadu výkonu je:

| Korelácia chýb v čase | u(P_storage) [kW] |
|---:|---:|
| 0,00 | 655,166 |
| 0,95 | 146,500 |

Ak je spoločný stabilný offset oddelený a nezávislá náhodná zložka je len 0,05 K na meranie, neistota z rozdielu je **163,792 kW**. Ani táto priaznivejšia ilustrácia nepostačuje na spoľahlivé určovanie približne 100 kW zdroja zo samotnej 15-minútovej zmeny teploty bazéna.

## QA a obmedzenia

**20/20** automatických testov, Python kompilácia, **3/3** nezávislé Monte Carlo prípady. Testy zahŕňajú nulový spoločný mód, opačné korelácie, nelineárnu korekciu, chybnú kovariančnú maticu, neplatné vstupy a priemerovanie. Audit číta pôvodný skript `neistoty_merania_v08_sk.py` a zaznamenáva jeho SHA256, ale nič do zdrojového projektu nezapisuje.

NIE JE potvrdené: kalibrácia prietokomera a dvojice teplomerov, korelácie z reálnych dát, presné ρ/cₚ pri prevádzkovej teplote, stratové teplo, tepelné vrstvenie bazéna, reálne COP tepelného čerpadla ani bezpečnosť IT chladenia. Pôvodné scenáre sú **D_SYNTHETIC**, nie merania triedy A.

**Ďalší vykonateľný krok:** získať synchronizované merania prietoku a oboch teplôt s identitou prístrojov a kalibračnými listami; odhadnúť kovariančnú maticu a časovú autokoreláciu; validovať výkon na nezávislom kalorimetrickom meraní. Následne aktualizovať interval spoľahlivosti bez spätnej úpravy historických syntetických CSV.
