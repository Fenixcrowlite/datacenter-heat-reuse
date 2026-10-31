# DC SCADA v09 — architektúra lokálneho prehrávania

**LOCAL_SIMULATION_ONLY · D_SYNTHETIC · kvalita D · hardware_enabled=false.** Ide o lokálny prehliadač a prehrávač výsledkov Simulinku pre spätné využitie tepla dátového centra do bazéna 500 m³. Fyzická prevádzka, PLC, priemyselné protokoly a zápis do zariadení nie sú súčasťou jadra.

## Tok dát a hranice

```text
../results/pool_measurement_v08/ (iba čítanie)
  sim_v08_*_SK.csv + QA_NEZAVISLA_V08_SK.json
             |
             v
       Dataset / validácia
       8 × 672 presných riadkov, SHA-256, 900 s
             |
             v
       ReplayEngine + alarmy (RLock)
         |              |
         v              v
  runtime/history.sqlite  lokálne HTTP API 127.0.0.1
  syntetický historik      |
                           v
                   web/ SVG + canvas HMI
                           |
                    voliteľné čítanie
                           v
                   mqtt_bridge.py
                  dchr/v09/sim/#
                           |
                           v
               lokálny Mosquitto → FUXA
```

Jadro používa štandardnú knižnicu Pythonu: `csv`, `json`, `pathlib`, `sqlite3`, `http.server`, `threading`, `logging`. Web používa lokálne HTML/CSS/JavaScript bez CDN a ďalších sieťových zdrojov. Python server nie je všeobecný súborový server: statické súbory sú v pevnom zozname. API neprijíma vlastné cesty k CSV ani k modelom.

## Proveniencia a vedecký význam

Dataset má osem pomenovaných scenárov, každý 672 vzoriek s časmi 0…167,75 h, krok 0,25 h. Hodnoty sa čítajú ako konečné čísla a prehrávajú bez interpolácie. Metadata API obsahujú `source_class=D_SYNTHETIC`, `quality=D`, `mode=LOCAL_SIMULATION_ONLY`, `hardware_enabled=false` a `interpolation=false`. Snapshot pridáva názov zdrojového súboru, SHA-256 a pôvodný čas vzorky; čas pozorovania aplikáciou je samostatný.

Nezávislý report QA uvádza `PASS`, 91 565 kontrol, triedu `D_SYNTHETIC_REPLAY` a scenáre `D_SYNTHETIC`. Overuje zapojenie a numerické vzťahy modelu, **nie kalibráciu meraním ani nezávislosť fyzických snímačov**. Modely MATLAB/Stateflow v85/v04/v05/v06/v07/v08 sa neupravujú a server ich nespúšťa.

`T_IT_model_C` je modelový ukazovateľ tepelného rizika IT, nie meraná teplota CPU. COP je pôvodný stĺpec `COP`. Z energie `E_TES_J` sa dá presne odvodiť kWh delením 3 600 000; menovitá kapacita zásobníka nie je zdokumentovaná, preto SOC zostáva `null`. Nepoužíva sa maximum datasetu ako náhradná kapacita.

## Stav a prehrávanie

Po štarte je prehrávanie pozastavené. Worker posúva index po celých riadkoch rýchlosťou 0,5…16 vzoriek/s podľa monotónnych hodín. Seek je celočíselný a ohraničený na 0…671; seek/reset/zmena scenára pozastavia prehrávanie. Koniec scenára sa nezacyklí automaticky. Čas modelu a čas počítača sa nesmú zamieňať.

Autoritatívny súbor `scada_v09/STOP` sa nikdy automaticky neodstraňuje. Worker kontroluje jeho existenciu približne každých 50 ms a API ju overuje pri práci so stavom. Existujúci STOP pozastaví replay, vyvolá CRITICAL alarm a zablokuje play/reset/seek/scenario. Kvitovanie, čítanie, pause a bezpečné shutdown zostávajú miestne operácie. UI ani MQTT nemajú oprávnenie spustiť fyzické zariadenia.

## HTTP rozhranie

Server počúva iba na IPv4 `127.0.0.1`. Predvolený port je 8091; len pri obsadenom predvolenom porte skúsi 8092 a výslovne to zaloguje. Parameter `--port` vypína automatický fallback. Exkluzívne viazanie socketu a OS zámok `runtime/server.lock` obmedzujú duplicitné inštancie; `runtime/server.json` obsahuje PID, port a náhodné `instance_id`, nikdy token.

| Rozhranie | Význam |
|---|---|
| `GET /api/health` | zdravie procesu, PID, instance_id, metadata D |
| `GET /api/status` | riadenie replay a lokálny CSRF token |
| `GET /api/scenarios` | pevný katalóg a proveniencia scenárov |
| `GET /api/snapshot` | presný riadok, odvodené hodnoty, alarmy; bez tokenu |
| `GET /api/history` | presné zdrojové rady pre trend/scope=full pre porovnanie |
| `GET /api/historian` | skutočne navštívené vzorky v SQLite |
| `GET /api/alarms` | lokálne udalosti a aktívne indikácie |
| `POST /api/control` | play/pause/reset/seek/scenario/speed/ack/shutdown |

Príkazy prijímajú iba obmedzené JSON objekty, žiadne alternatívne kľúče alebo súborové cesty. Číselné rýchlosti a indexy sa po kontrole typu ohraničujú. Každý POST vyžaduje náhodný `X-SCADA-Token`; ak sa pošle `Origin`, musí zodpovedať aktuálnemu lokálnemu origin. Host a klient sa overujú; CORS a cross-origin OPTIONS nie sú povolené. CSP obmedzuje webové zdroje na lokálny server. Toto sú ochrany lokálnej simulácie, nie certifikovaná priemyselná bezpečnostná vrstva.

## Historik a alarmy

SQLite používa WAL a synchronizovaný prístup z replay/HTTP vlákien. Primárny kľúč vzorky je `(source_hash, scenario_id, sample_index)`: opakovaný replay mení `last_seen`, nepridáva duplicitné vzorky. `sample_timestamp_s` je pôvodný čas simulácie; `first_seen` a `last_seen` sú UTC pozorovania. Pri inom SHA-256 sa staršie zdrojové verzie odstraňujú, takže aktívny korpus je najviac 5 376 vzoriek.

Alarmy vychádzajú z príznakov CSV (`E_STOP`, `IT_model_alarm`, `safety_latch`, `emergency_flag`, `invalid_sensor`, `flow_fault`, `sensor_mismatch`, `sensor_hot`, chyby ventilov, `leak_at_zero_cmd`). Jedinými toleranciami zobrazenia sú `Q_unhandled_W > 1 W` a `abs(Q_leak_W) > 1 W`; nepredstierajú priemyselný ochranný limit. STOP má samostatný alarm aplikácie.

Udalosti ACTIVE/CLEARED/ACK nesú severity, scenár, index, čas a kvalitu D. Unikátny kľúč zdroja/scenára/indexu/kódu/stavu zabraňuje opakovanej identickej udalosti; uchováva sa najviac 5 000 alarmových udalostí. Kvitovanie nemení pôvodné príznaky ani `safety_latch`. Log `runtime/scada.log` sa rotuje po 512 KiB s tromi zálohami.

## Voliteľný MQTT a kontajnery

`mqtt_bridge.py` je samostatný explicitne spustený proces s jedinou voliteľnou závislosťou `paho-mqtt`. Číta iba loopback snapshot cez HTTP bez proxy a presmerovaní; odmietne payload bez explicitnej kvality D a zakázaného hardvéru. Publikuje snapshot a jednotlivé číselné tagy do `dchr/v09/sim/#`, nikdy nevolá subscribe. Whitelist stavu odstráni CSRF token aj pri budúcej zmene API. Heslá sú výlučne v premenných prostredia; pomocný skript ich môže načítať z ignorovaného `.env` bez vypísania. STOP ukončuje most. Retained správy vyžadujú kontrolu času čerstvosti a stavu mosta.

Docker Compose je odložená voliteľná konfigurácia s profilom `fuxa`; natívny HMI funguje bez nej. Broker sa z hosta sprístupňuje len cez `127.0.0.1:18883` a FUXA cez `127.0.0.1:1881`. Mosquitto zakazuje anonymous a používa password_file plus oddelené ACL: `scada_exporter` môže len publikovať simuláciu, `fuxa_viewer` ju môže len čítať. Bootstrap sa spúšťa ručne, neštartuje Docker Desktop ani trvalé služby; jednorazový kontajner vytvorí hashované heslá zo vstupu stdin. Perzistentné dáta sú v pomenovaných volumes. Grafana je samostatný profil s vlastným lokálnym secret súborom; nemá nakonfigurovaný dátový zdroj.

Compose nevyužíva privileged, host networking ani automatický reštart. Limity RAM: broker 128 MiB, FUXA 512 MiB, Grafana 256 MiB. V čase implementácie sa Docker a FUXA nespúšťali. Pred vlastným použitím je potrebné manuálne nastavenie FUXA, autorizácie a JSON tagov; táto konfigurácia nie je výsledkom UI commissioning.

## Prevádzková hranica skriptov

`start_scada.ps1` odmietne STOP, rozpozná existujúci vlastný PID, spustí iba lokálny Python na explicitný pokyn používateľa a do 8 sekúnd overí HTTP identitu. `stop_scada.ps1` najprv vytvorí STOP, potom porovná PID/CommandLine/instance_id a žiada iba graceful shutdown svojho servera. Žiadny skript nepoužíva plošné zabíjanie procesov, nemení firewall, power plan ani autostart. Pri pochybnosti sa proces nezabíja a STOP zostáva platný.
