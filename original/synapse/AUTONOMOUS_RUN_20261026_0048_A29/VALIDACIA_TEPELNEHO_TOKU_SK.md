# A29 | Nezávislá validácia tepelného výkonu pomocou kalorimetra

**Projekt:** DataCenter Heat Reuse / bazénový okruh. **Stav:** nástroj pripravený, fyzická validácia NEVYKONANÁ. Demonštračné dáta sú syntetické.

## Meracia otázka
Dokáže model predpovedať tepelný výkon mimo intervalu, v ktorom boli určené korekcie a kovariancia snímačov, a zhoduje sa s **nezávislým** certifikovaným meračom tepla?

Predikcia: **P = ρ · cₚ · V̇ · (T_prívod − T_spiatočka) / 3600** [kW], ak ρ [kg/m³], cₚ [kJ/(kg·K)] a V̇ [m³/h]. Korekcia snímačov: x_korigované = x_merané − priemerná chyba z A28. Hodnoty ρ a cₚ sa musia zdokumentovať pre konkrétnu teplotu a médium.

Lokálna lineárna propagácia: **u²(P) = J C Jᵀ + u²_m**, kde C je kovariančná matica reziduálnych chýb troch snímačov z A28, J = (ρcₚΔT/3600, ρcₚV̇/3600, −ρcₚV̇/3600) a u_m je deklarovaná štandardná neistota nezávislého merača tepla. Táto hodnota **nezahŕňa** neistotu odhadu C, korekcií, ρ, cₚ, kalibračný drift ani časovú koreláciu.

## Minimálny zber dát
1. Získať originálne synchronizované kalibračné CSV, metadáta a report A28. Nástroj A29 overuje SHA256 a nezávisle prepočíta priemerné chyby aj 3×3 kovarianciu. Originály nesmú byť spätne upravené.
2. Na **neskoršom, neprekrývajúcom sa** časovom úseku zbierať `time_utc,flow_read_m3h,hot_read_C,cold_read_C,meter_kw` s časovou zónou a pevne deklarovanou periódou. Minimum 12 bodov; pre serióznu validáciu treba podstatne dlhší záznam a viac prevádzkových režimov.
3. Nezávislý merač tepla musí mať samostatný identifikátor, dokumentáciu zapojenia, kalibračný certifikát, výrobcu, rozsah, neistotu a nezávislé dátové rozhranie. Nezávislosť uvedená v JSON nie je automaticky dokázaná.
4. V metadátach deklarovať `source_class`, jednotky, `meter_independent=true`, `sample_period_s`, `density_kg_m3`, `specific_heat_kj_kg_K`, `meter_std_uncertainty_kw` a pri reálnych dátach `meter_certificate` s SHA256, identifikátorom, vydavateľom a platnosťou. Overiť aj skutočnú dôveryhodnosť vydavateľa mimo programu.
5. Pred porovnaním zohľadniť dynamické oneskorenie prúdenia, miesto merania, tepelné straty potrubia a odlišnú integráciu merača. A29 zatiaľ **nekompenzuje** časový posun ani neistotu parametrov.

## Výstup a kritériá
A29 vypíše priemernú odchýlku [kW], MAE/RMSE [kW], relatívnu chybu [%], bodovú kombinovanú štandardnú neistotu [kW], normalizované rezíduá a orientačný integrál energie [kWh] ľavými obdĺžnikmi. Tieto metriky sú **diagnostické**, nie automatická skúška zhody s normou.

**Fail-closed:** `release_allowed=false` pre syntetické aj predbežne reálne dáta. Na uvoľnenie sú potrebné nezávislé potvrdenie certifikátov, analýza systematických neistôt, časovej korelácie, pokrytie prevádzkových režimov a schválený validačný protokol. Nástroj nevydáva metrologický certifikát.

## Príklad spustenia
```powershell
python holdout_heatmeter_gate.py --calibration example_synthetic/cal_report.json --calibration-csv example_synthetic/cal.csv --calibration-metadata example_synthetic/cal_meta.json --holdout example_synthetic/holdout.csv --metadata example_synthetic/holdout_meta.json --output example_synthetic/HOLDOUT_EVIDENCE.json
```
Príklad obsahuje **výlučne syntetické** dáta, nesmie sa uvádzať ako experimentálne overenie bazéna.
