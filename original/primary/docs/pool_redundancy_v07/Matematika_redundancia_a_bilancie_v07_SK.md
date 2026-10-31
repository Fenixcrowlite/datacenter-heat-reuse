---
tags: [datacentrum, bazen, Simulink, Stateflow, redundancia, FMEA]
date: 2026-10-23
status: VERIFIED_SIMULINK_SYNTHETIC_V07
language: sk
---
# V07: dvojité uzatváranie, rezervné chladenie a núdzové odľahčenie IT

> [!warning] Hranice
> Model je nová nezávislá verzia v06 so Stateflow logikou vzniknutou vo v04. Originálna v85 nie je vložená ako vykonávací dispečer. Všetky časové rady sú syntetické predpoklady triedy D. Simulácia nie je certifikáciou fyzickej bezpečnosti.

## 1. Architektúra a modelové parametre

Bazén: 500 m³, plocha hladiny 312,5 m², počiatočná voda 16 °C, termostatická požiadavka 27,58 °C. Časový krok 900 s, 672 krokov na scenár, 168 h. Dva sériové uzatváracie ventily sa modelovo vzájomne zálohujú: jeden zaklinený nedovolí unikajúci tok, ak druhý funguje. Dve odvodné vetvy REJECT majú zvolené maximá 180 kW a 150 kW, nie parametre skutočne overeného zariadenia. Núdzové odľahčenie 70 % tepla sa aplikuje až keď zlyhajú oba odvodné okruhy a modelový tepelný buffer IT prekročí 38 °C.

## 2. Hmotnosť a akumulácia energie vody

$$m=\rho V=997\cdot500=498\,500\ \mathrm{kg}.$$

$$C_w=\rho Vc_p=997\cdot500\cdot4182=2\,084\,727\,000\ \mathrm{J/K}.$$

$$E_{16\rightarrow28}=\frac{12C_w}{3{,}6\cdot10^9}=6{,}94909\ \mathrm{MWh}.$$

Toto je iba energia ohrevu vody bez tepelných strát.

$$T_{w,k+1}=T_{w,k}+\frac{900}{C_w}(Q_{\mathrm{pool,phys},k}-Q_{\mathrm{loss},k}).$$

Straty odparom, konvekciou, radiáciou, konštrukciou, doplnením vody a paušál 2 kW sú predpoklady prevzaté z v04; nie kalibrácia skutočnej bazénovej haly.

## 3. Oneskorenie merania a safety latch

$$T_{1,k}=T_{\mathrm{true},k-1}+b_{1,k};\quad
T_{2,k}=T_{\mathrm{true},k-2}+b_{2,k}.$$

$$D_{\rm diff}=[|T_1-T_2|>0{,}35\ \mathrm K];\quad
D_{\rm high}=[\max(T_1,T_2)\ge27{,}70^\circ C].$$

$$D_{\rm fault}=D_{\rm diff}\lor D_{\rm high}\lor\neg flowOK\lor EStop\lor invalidSensor.$$

Po poruche musí byť softvérové vykurovanie vypnuté. Západka sa uvoľní len po zániku poruchy, explicitnom ručnom resete a nameranej teplote do 27,65 °C. Spoločný bias -0,40 K na oboch snímačoch nespustil alarm. Diagnostika spoločnej chyby bez nezávislého merania teda nie je dokázaná.

## 4. Dva ventily a fyzikálny tok odlišný od povelu

Nech f1,f2 označujú mechanické zlyhanie oboch uzáverov. Pri nulovom softvérovom povele:

$$Q_{\rm leak}=\begin{cases}
\min[25\,000,Q_{\rm REJECT,cmd},4500\max(0,T_{\rm DC}-T_w-3)],&f_1=f_2=1,\\
0,&\text{inak}.
\end{cases}$$

$$Q_{\rm pool,phys}=Q_{\rm pool,cmd}+Q_{\rm leak}.$$

$$Q_{\rm REJECT,afterValve}=Q_{\rm REJECT,cmd}-Q_{\rm leak}.$$

Únik sa ODPOČÍTA z existujúceho toku REJECT, takže model nevytvára neexistujúcu energiu. Parametre 4500 W/K, rozdiel 3 K a maximálne 25 kW sú neoverené scenárové predpoklady. Jeden poškodený uzáver v simulácii prepúšťanie nevyvolal. Obe mechanické poruchy vyvolali 0,48996 MWh úniku. To nie je dôkaz skutočnej nezávislosti komponentov.

## 5. Dve chladiace vetvy a energetické zákony

Pri disponiblite aA,aB v intervale 0 až 1:

$$Q_A=\min(Q_{\rm REJECT,afterValve},180\,000a_A).$$

$$Q_B=\min[\max(0,Q_{\rm REJECT,afterValve}-Q_A),150\,000a_B].$$

$$Q_{\rm unhandled}=\max(0,Q_{\rm REJECT,afterValve}-Q_A-Q_B).$$

$$\boxed{Q_{\rm DC,available}=Q_{\rm HX,phys}+Q_{\rm HP,source}+Q_A+Q_B+Q_{\rm unhandled}.}$$

$$Q_{\rm HP,out}=Q_{\rm HP,source}+P_{\rm compressor}.$$

Neodvedené teplo nie je možné zanedbať: zostáva samostatne účtované ako akumulácia alebo budúca požiadavka na núdzový odvod.

## 6. Núdzové odľahčenie IT a model tepelného rizika

Pri obojstrannom výpadku REJECT, povolení ochrany a modelovej T_IT >=38 °C:

$$Q_{\rm avoided}=0{,}70Q_{\rm DC,raw};\quad
Q_{\rm DC,effective}=Q_{\rm DC,raw}-Q_{\rm avoided}.$$

Odľahčenie je okamžité bez modelu reakčného času IT záťaže a SLA. Pre hypotetický buffer:

$$C_{\rm IT}=8\cdot10^6\,\mathrm{J/K};\quad
Q_{\rm passive}=\max(0,2000(T_{\rm IT}-30)).$$

$$T_{\rm IT,k+1}=\max[30,T_{\rm IT,k}+900(Q_{\rm unhandled}-Q_{\rm passive})/C_{\rm IT}].$$

Alarm pri 42 °C je výlučne scenárový indikátor. NEPREDSTAVUJE teplotu CPU ani schválený bezpečnostný limit.

## 7. Výsledky ôsmich skutočných Simulink behov

| Scenár | Únik [MWh] | Neodvedené [MWh] | Rezerva odvedená [MWh] | Znížené IT teplo [MWh] | Max. T_IT_model [°C] |
|---|---:|---:|---:|---:|---:|
| Bez poruchy | 0 | 0 | 0 | 0 | 30,00 |
| Jeden ventil zaseknutý | 0 | 0 | 0 | 0 | 30,00 |
| Oba ventily zaseknuté | 0,48996 | 0 | 0 | 0 | 30,00 |
| Hlavný REJECT off | 0 | 0 | 0,07966 | 0 | 30,00 |
| Obe vetvy off, bez odľahčenia | 0 | 0,07966 | 0 | 0 | 47,06 |
| Obe vetvy off, odľahčenie on | 0 | 0,04989 | 0 | 0,15212 | 40,33 |
| Spoločný bias snímačov | 0 | 0 | 0 | 0 | 30,00 |
| Kombinovaná havária, odľahčenie | 0,14602 | 0,03903 | 0 | 0,06969 | 39,26 |

V modelovej poruche REJECT odľahčenie znížilo neodvedenú energiu o približne 37,4 %. Bez údajov konkrétnej inštalácie nemožno tento pokles použiť ako garantovaný návrhový parameter.

## 8. QA, reprodukcia a ďalší postup

Nezávislá Python kontrola CSV: 129 251 PASS. Kontrolovaný je prvý zákon zdroja a HP, bilancia vody, dva ventily, oba chladiče, snímače 15/30 min, latch, RESET, redukcia zdrojového tepla a tepelný buffer IT. Originálna v85 zostala nezmenená podľa hash SHA-256.

MATLAB R2026a: v OneDrive/Projects/DataCenter_Heat_Reuse/matlab/pool_redundancy_v07 spustiť spusti_scenare_v07_sk.m. QA: python qa_nezavisla_v07_sk.py.

![[ventily_a_redundancia_v07_SK.png]]

![[IT_riziko_v07_SK.png]]

**Nie je overené:** hydraulické parametre a výrobné mapy COP, skutočné teploty serverov, aktuálne právne požiadavky, reálne merané časové profily a spoľahlivosť spoločného napájania. Na kalibráciu v nasledujúcej verzii treba reálne timestampované merania s uvedením zdroja, jednotiek, neistoty a kategórie dôkazu A/B/C/D.

Odkazy: EU 2024/1364 https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj ; STN EN 15288-1+A1:2024 https://normy.normoff.gov.sk/norma/139372/nahlad/ ; historické znenie 308/2012 https://static.slov-lex.sk/static/SK/ZZ/2012/308/vyhlasene_znenie.print.html
