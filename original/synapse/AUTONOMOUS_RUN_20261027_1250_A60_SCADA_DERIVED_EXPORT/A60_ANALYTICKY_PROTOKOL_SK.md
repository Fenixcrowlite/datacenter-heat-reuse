# A60: export a porovnanie odvodených dát SCADA v08/v09

**Rozsah:** výlučne existujúce výstupy matematickej simulácie, nie merania fyzického zariadenia.

## Transformácia
Pre dve explicitne známe schémy CSV prevádza modul `cas_h` na `time_s = 3600 cas_h` a premenúva sedem veličín: teplota bazéna, výkon dátového centra, odvod tepla REJECT, teplo do bazéna, dodávka tepla do centrálneho systému, elektrický príkon tepelného čerpadla a energia TES. Vstupné súbory sa nemenia. Každý výstup obsahuje SHA256 pôvodného CSV, kanonické časové rady a sumár.

## Energetický výpočet
Pre okamžitý výkon `P_i [W]` a čas `t_i [s]` sa energia vypočíta lichobežníkovou integráciou:
`E_MWh = sum((P_i + P_(i+1))/2 * (t_(i+1)-t_i)) / 3.6e9`.
Rozdiel energie TES: `(E_TES_last - E_TES_first)/3.6e9`. Čas je relatívny, bez časového pásma UTC.

## Nezávislá kontrola
Modul `independent_qa_a60.py` nezávisle číta pôvodné CSV, overuje SHA256, každý premenovaný údaj a znovu integruje päť výkonových kanálov pomocou Decimal. Pre v08 a v09 vykoná 5 376 porovnaní normalizovaných veličín a 10 integrálnych kontrol.

Hraničné tolerancie porovnania sú **prieskumné softvérové kritériá**, nie certifikované tolerancie senzorov ani vopred registrovaná fyzikálna validácia.

## Hranica použitia
`source_kind = derived_simulation`, `physical_release = false`, `measurement_calibration_ready = false`. Súbory neposkytujú skutočné časové značky UTC, identifikátory kalibrovaného meracieho okruhu ani odozvu kompresora po skokovej zmene povelu. Nesmú byť odovzdané do A55 ako reálne merania.

## Ďalší krok
Získať autentický export meraní s desiatimi kanálmi A59, s certifikátmi kalibrácie a časovou synchronizáciou. Až potom spustiť A55 až A58 a porovnanie so Stateflow. Zatiaľ je fyzikálna validácia **BLOCKED**.
