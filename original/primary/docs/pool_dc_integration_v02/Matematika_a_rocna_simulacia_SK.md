---
tags: [datacentrum, bazen, matematika, simulink, stateflow, rocna-simulacia]
status: VERIFIED_SIMULINK_SYNTHETIC
jazyk: sk
created: 2026-10-23
---
# Ročná simulácia: odpadové teplo DC → bazén 500 m³

> [!warning] Hranice
> Toto je **syntetický experiment**. Nejde o meranie ani certifikovaný projekt. Nový model DC_Bazen_Alokacia_Rok_v02_SK.slx je nezávislý od existujúcich modelov v85/v86 a od Bazen_DC_Ohrev_500m3_SK.slx. Ich súbory sa nemenili.

## 1. Architektúra

Dátové centrum dodá dostupné odpadové teplo $Q_{\mathrm{DC,av}}$. Dispečing ho rozdeľuje podľa priority: bazén (priamy výmenník HX alebo tepelné čerpadlo TČ), tepelná sieť DH, zásobník TES a nezávislý odvod REJECT. Samotné IT chladenie musí byť bezpečné aj bez odberu tepla bazénom.

Referenčná pridelená vetva má **syntetický príkon IT približne 216 kW v priemere**. **Nie je totožná s existujúcim modelom celého 10 MW dátového centra!** Priemer disponibilného odpadového tepla vetvy je asi 186 kW. Výsledky preto nesmú byť vydávané za ročný výkon celej pôvodnej v85 sústavy.

## 2. Geometria a kapacita vody

Rozmery *ilustratívneho* bazéna $25\times12{,}5\times1{,}6\ \mathrm m$:

$$
V=500\ \mathrm{m^3},\quad A=312{,}5\ \mathrm{m^2},\quad
m=\rho V=997\cdot500=498\,500\ \mathrm{kg}.
$$

$$C=\rho V c_p=997\cdot500\cdot4182=2\,084\,727\,000\ \mathrm{J/K}.$$

$$E_{16\to28}=C(28-16)/(3{,}6\cdot10^9)=6{,}94909\ \mathrm{MWh}.$$

Ide o energiu zvýšenia teploty vody **bez** prevádzkových strát.

## 3. Prvý termodynamický zákon

Pri hodinovom kroku $\Delta t=3600\ \mathrm s$:

$$
C\frac{\Delta T}{\Delta t}=Q_{\mathrm{bazen}}-Q_{\mathrm{straty}},
\quad
T_{k+1}=T_k+\frac{\Delta t}{C}(Q_{\mathrm{bazen},k}-Q_{\mathrm{straty},k}).
$$

Jednotky v celom jadre: energia [J], výkon [W], čas [s], teplota [°C] a rozdiel teplôt [K].

$$Q_{\rm straty}=Q_{\rm vypar}+Q_{\rm konv}+Q_{\rm rad}+Q_{\rm konstr}+Q_{\rm dop}+2000\ \mathrm W.$$

Nelineárna teplota nasýtenej vodnej pary:

$$p_s(T)=0{,}61094\,\exp(17{,}625T/(T+243{,}04))\quad[\mathrm{kPa}].$$

Zjednodušený výpar podľa plochy hladiny, aktivity a vlhkosti:

$$
\dot m_{\rm vypar}=\max\left(0,4\cdot10^{-5}A(p_s(T_w)-RH\,p_s(T_a))
F_a(1-0{,}90K)\right),\quad Q_{\rm vypar}=\dot m_{\rm vypar}2{,}44\cdot10^6.
$$

$K=1$ pri zakrytej hladine, $K=0$ inak; $F_a=1$ počas používania, $0{,}5$ mimo prevádzky. Efekt plachty je **scenárový predpoklad**.

$$Q_{\rm konv}=3A(T_w-T_a)(1-0{,}75K).$$
$$Q_{\rm rad}=0{,}95\sigma A[(T_w+273{,}15)^4-(T_a-2+273{,}15)^4](1-0{,}75K).$$
$$Q_{\rm konstr}=800(T_w-20),\quad Q_{\rm dop}=\dot m_{\rm vypar}4182(T_w-15).$$

Konvekcia môže byť záporná; pri chladnejšej vode odovzdáva teplo do vody vzduch.

## 4. Tepelný výmenník a tepelné čerpadlo

Priama vetva rešpektuje teplotný napor, výkon a disponibilné odpadové teplo:

$$
Q_{\rm HX,max}=\min\{Q_{\rm DC,av},150000,\max[0,8500(T_s-T_w-3)]\}.
$$

Pri TČ je použitý **modelový**, nie katalógovo overený COP:

$$T_{\rm evap}=T_s-5,\quad T_{\rm cond}=\max(34,T_w+8),$$

$$COP=\operatorname{clip}(0{,}43T_{\rm cond,K}/\max[5,T_{\rm cond}-T_{\rm evap}],2{,}5,6).$$

$$
Q_{\rm HP}\le\min(Q_{\rm demand},150000,Q_{\rm DC,av}/(1-1/COP),35000COP).
$$

$$P_{\rm HP}=Q_{\rm HP}/COP,\quad Q_{\rm source}=Q_{\rm HP}-P_{\rm HP}.$$

Priame HX má $P_{\rm compressor}=0$, avšak **čerpadlá, pohony a hydraulické straty v02 ešte nie sú zahrnuté**.

## 5. Tepelný dispečing a ochrany

$$Q_{\rm DC,av}=Q_{\rm source}+Q_{\rm DH}+Q_{\rm TES}+Q_{\rm reject}.$$

Priorita je bazén → sieť → zásobník → odpad. **STOP=1** nastaví odbery bazéna, siete a zásobníka na nulu a zvyšok odvedie nezávislou chladiacou vetvou. Tým nie je deklarovaná fyzická bezpečnostná certifikácia skutočného DC.

Termostat zapína pri $T\le27{,}35^\circ C$ a vypína pri $T\ge27{,}65^\circ C$. Matematická hranica:

$$
Q_{\rm safe}=\max(0,C(27{,}75-T_k)/3600+Q_{\rm straty,k}),\quad
Q_{\rm pool}\le\min(150000,Q_{\rm safe}).
$$

Model nedokazuje bezpečnosť pri chybe, oneskorení alebo nesprávnom umiestnení teplotného snímača. Pri posúdení reálneho plaveckého bazéna preveriť aktuálne znenie právnych požiadaviek.

## 6. Skutočne vykonaná simulácia MATLAB/Simulink R2026a

Štyri scenáre, 8760 hodinových krokov, viacstupňová kontrola bilancie:

| Scenár | Tmax °C | Bazén MWh | Z DC do bazéna MWh | Elektrina TČ MWh | Sieť MWh | TES MWh | Reject MWh |
|---|---:|---:|---:|---:|---:|---:|---:|
| Základ | 27,750 | 254,39 | 211,99 | 42,40 | 567,69 | 53,48 | 795,85 |
| Teplejší zdroj (+12 K) | 27,750 | 254,32 | 226,03 | 28,29 | 566,96 | 52,31 | 783,72 |
| STOP 168 h | 27,750 | 251,74 | 209,78 | 41,96 | 561,68 | 52,44 | 805,11 |
| Bez plachty | 27,750 | 331,06 | 275,89 | 55,18 | 561,61 | 51,91 | 739,60 |

Energia bazéna v základnom scenári:

$$254{,}3893=211{,}9911+42{,}3982\ \mathrm{MWh}.$$

Energia vyčleneného DC:

$$1629{,}0146=211{,}9911+567{,}6910+53{,}4794+795{,}8531\ \mathrm{MWh}.$$

Zvyšok akumulovaný vo vode za 8760 h:

$$254{,}3893-247{,}7121=6{,}6772\ \mathrm{MWh}.$$

Najvyššia energetická reziduálna chyba vody v štyroch scenároch je približne $4{,}1\cdot 10^{-14}\ \mathrm{MWh}$ (čisto numerická konzervácia).

Teplejší zdroj umožnil 696 hodín priameho HX a 1170 hodín TČ. Základ vyžadoval 1760 hodín TČ. Odstránenie plachty zvýšilo modelovú dodávku tepla približne o **76,68 MWh/rok** a kompresorovú elektrinu o **12,78 MWh/rok**.

![[rocna_teplota_SK.png]]

## 7. KPI a správna hranica ERF

Nariadenie EÚ 2024/1364 stanovuje:

$$PUE=E_{\rm DC}/E_{\rm IT},\qquad ERF=E_{\rm REUSE}/E_{\rm DC}.$$

Ilustratívne podľa zvoleného obvodu *prideleného IT bloku*: ERF = **0,343** pri PUE 1,20 alebo **0,271** pri PUE 1,52. Do $E_{\rm REUSE}$ je započítané teplo vyvezené zo zdroja DC do bazéna a siete, **nie** dodatočná elektrina kompresora ani nevyvezené teplo uložené do TES. Tieto čísla **nie sú reportovateľným ERF celého 10 MW dátového centra**.

## 8. Artefakty a ďalší postup

- [[Rocna_integracia_bazen_500m3_SK.pdf]]: technický PDF (SK).
- [[Rocna_integracia_bazen_500m3_EN.pdf]]: technical PDF (EN).
- [[Rocna_integracia_bazen_500m3_RU.pdf]]: технический PDF (RU).
- Model v OneDrive: Projects/DataCenter_Heat_Reuse/matlab/pool_dc_integration_v02/DC_Bazen_Alokacia_Rok_v02_SK.slx
- Spustenie v MATLAB: z uvedeného adresára vykonať spusti_rocne_scenare_sk.m.
- Zdroj fyziky: blok_tok_dc_bazen_sk.txt; časové exporty CSV a JSON v results/pool_dc_integration_v02.
- [[Matematicky_rozbor_a_simulacia_SK]]: pôvodný 7-dňový fyzikálny modul.

**BLOKOVANÉ pre realitu:** napojenie na signály pôvodného v85/v86 (v02 má syntetický vstup), výrobné COP mapy, prietoky a tlakové straty, pomocné príkonové položky, HVAC/odvlhčovanie, nezávislé senzory a tolerancie.

## 9. Referencie

- ASHRAE, Natatoriums: https://handbook.ashrae.org/handbooks/F17/SI/F17_Ch36/f17_ch36_si.aspx
- EU Delegated Regulation 2024/1364: https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj
- Slov-Lex 308/2012 §8(7), znenie 2012: https://www.slov-lex.sk/ezbierky/pravne-predpisy/SK/ZZ/2012/308/20121015.html
