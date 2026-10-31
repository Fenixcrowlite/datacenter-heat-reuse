# A50 graphical Stateflow sensor-lag integration | 2026-10-27 03:51-04:00 CET
Existing Synapse task scc-3d9d172beb6e1b; no new task/worker. Primary SynapseMCP Web initially ONLINE, then timed out; Ngrok authorized fallback used after verifying live ping. Desktop Commander unavailable due usage limit.
MATLAB R2026a executed six synthetic fault-injection scenarios: neither and backup_only x sensor lag 0/1/4 samples, 240 steps each, 11 channels, 15840 numeric parity comparisons PASS vs independent Python A45.
First TRIPPED zero-based indices: neither 98/98/98; backup_only 98/98/103. Extra 60-minute sensor delay postpones backup_only trip by five 15-minute samples, a modeled safety-relevant behavior. Zero REJECT interlock remains independent of sensor lag.
7/7 independent Python acceptance tests PASS; MATLAB script initially had argument quoting and chained-indexing errors, corrected and rerun to completion.
A50 saved SLX is a baseline isolated A48 copy; sensor lag is injected in memory during each run. Graphical Stateflow is the supervisor; no physical equipment or external control.
A48 SHA256 unchanged: 063f9afb5816cd4f6bed415256293eee67b328718b141c29d84853ddafab25cb
A50 SLX SHA256: 8edb7f64b9fe27c54be4c5d1223e242feb6f733cde97dce4c044b25729dc5cbe
Evidence SHA256: 8eac779de927eb8ae102b350d4faacde58fb60ac3bc5a88fbb1fac01b65116c8
Manifest SHA256: 3de3b038132b60535055d90ad3ad8af2562941f3aee012e94ac0f74989db7dd2
No Codex, new worker, GPU render, GUI/OAuth/STOP change or VRS. Physical release BLOCKED.
NEXT: A51: vary trip-delay guard in an isolated graphical Stateflow copy (0/2/4 steps), independently compare 240-step trajectories and prove thermal/energy balances; keep physical validation and 31 source signoffs BLOCKED.
