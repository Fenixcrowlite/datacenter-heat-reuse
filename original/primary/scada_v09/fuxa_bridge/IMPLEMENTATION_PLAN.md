# Native FUXA acceptance implementation plan

User specification: ../CODEX_MQTT_FUXA_TASK.md. User explicitly requests autonomous implementation without clarification.

Architecture: Aedes loopback MQTT broker with independent publish-only exporter and subscribe-only viewer. Node exporter polls the existing snapshot GET endpoint; retained scalar topics serve FUXA and metadata preserves D provenance and freshness. Native npm FUXA is isolated in fuxa/ and must be verified loopback before remaining active.

Constraints: writes only in fuxa_bridge, except append-only ../CODEX_FUXA_RESULT.md. Honor ../STOP. No edits to HMI, PLC, older versions, system configuration or unrelated processes. No fabricated live data or leaked secrets.

- [ ] Broker: test failed authentication, real role connections, read/write ACLs, wildcard escape, command/PLC/will rejection; implement broker.cjs and run tests.
- [ ] Publisher: validate actual D snapshots, GET-only loopback polling, required scalar tags, metadata, outage cleanup/recovery; implement publisher.cjs after failing tests.
- [ ] Runtime: restrictive inherited Windows ACL on .local, random separate credentials, owned child supervision, IPC graceful shutdown, STOP and exclusive ownership lock. Verify actual start/status/stop/restart.
- [ ] FUXA: bounded local npm installation; inspect installed native server and project schema; configure read-only MQTT device and real dashboard. Verify binding and runtime tags, or report exact blocker.
- [ ] Acceptance: full Node suite; actual source to MQTT to consumer comparison and FUXA if available; browser screenshot only for actual ready app. Record factual component status, PIDs and resource use.

Review focus: paused source freshness differs from frozen API; retained values must not masquerade as fresh; credentials and generated FUXA files remain ignored; stale PID must never cause another process to be killed; FUXA defaults must not expose wildcard listeners.

Ruling: use existing explicitly authorized workspace rather than worktrees, because there is no Git repository and the user restricts all implementation writes to this directory. No commits or branch operations apply.
