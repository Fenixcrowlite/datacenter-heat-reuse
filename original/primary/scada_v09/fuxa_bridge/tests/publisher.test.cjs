'use strict';

// Isolated synthetic fixtures below are test inputs, never live telemetry evidence.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const os = require('node:os');

let implementation = {};
try { implementation = require('../publisher.cjs'); }
catch (error) { if (error.code !== 'MODULE_NOT_FOUND') throw error; }
const { validateSnapshot, validateSourceUrl, createPublisher } = implementation;

const credentials = {
  exporter: { username: 'isolated-test-exporter', password: 'isolated-test-exporter-password' },
  viewer: { username: 'isolated-test-viewer', password: 'isolated-test-viewer-password' }
};
const tagNames = ['T_pool_C', 'Q_DC_eff_W', 'Q_pool_phys_W', 'P_HP_W', 'COP',
  'Q_reject_main_W', 'Q_reject_backup_W', 'T_IT_model_C', 'safety_latch', 'Q_unhandled_W'];
function fixture() {
  const now = new Date().toISOString();
  return {
    metadata: { source_class: 'D_SYNTHETIC', quality: 'D', mode: 'LOCAL_SIMULATION_ONLY',
      hardware_enabled: false, sample_period_s: 900, interpolation: false },
    status: { scenario_id: 'isolated-test', scenario_name: 'Isolated test fixture', index: 3,
      playing: false, stopped: false, speed: 1, simulation_time_h: 0.75,
      updated_at: '2000-01-01T00:00:00.000Z', server_time: now, sample_count: 8, at_end: false,
      csrf_token: 'THIS_MUST_NEVER_BE_EXPORTED', pid: 12345 },
    values: { T_pool_C: 21.25, Q_DC_eff_W: 200000, Q_pool_phys_W: 125000,
      P_HP_W: 32000, COP: 4.5, Q_reject_main_W: 1200, Q_reject_backup_W: 50,
      T_IT_model_C: 32, safety_latch: 0, Q_unhandled_W: 25, forbidden_command: 123 },
    sample_timestamp_s: 2700, observed_at: now,
    source_file: 'isolated_test_fixture.csv', source_sha256: 'a'.repeat(64),
    active_alarms: [], derived: { tes_soc_percent: null }
  };
}

test('accepts a paused D replay and exports only whitelisted safe source fields', () => {
  assert.equal(typeof validateSnapshot, 'function', 'publisher validator is required');
  const actual = validateSnapshot(fixture());
  assert.equal(actual.metadata.quality, 'D');
  assert.equal(actual.status.playing, false);
  assert.equal(actual.values.T_pool_C, 21.25);
  assert.equal(actual.values.Q_unhandled_W, 25);
  assert.deepEqual(Object.keys(actual.values).sort(), [...tagNames].sort());
  assert.equal(actual.source_file, 'isolated_test_fixture.csv');
  assert.equal(actual.source_sha256, 'a'.repeat(64));
  assert.equal(actual.sample_timestamp_s, 2700);
  assert.equal(JSON.stringify(actual).includes('THIS_MUST_NEVER_BE_EXPORTED'), false);
  assert.equal('pid' in actual.status, false);
});

test('rejects non-D data, enabled hardware, missing required telemetry and nonfinite scalars', () => {
  for (const mutate of [
    s => { s.metadata.quality = 'A'; },
    s => { s.metadata.source_class = 'LIVE'; },
    s => { s.metadata.mode = 'REMOTE'; },
    s => { s.metadata.hardware_enabled = true; },
    s => { delete s.values.COP; },
    s => { s.values.COP = NaN; },
    s => { s.values.safety_latch = true; },
    s => { s.source_sha256 = 'not-a-hash'; }
  ]) {
    const snapshot = fixture(); mutate(snapshot);
    assert.throws(() => validateSnapshot(snapshot));
  }
});

test('uses observation time for freshness and rejects expired or future observations', () => {
  const snapshot = fixture();
  const now = Date.now();
  snapshot.observed_at = new Date(now - 6000).toISOString();
  snapshot.status.server_time = snapshot.observed_at;
  assert.throws(() => validateSnapshot(snapshot, { now, staleMs: 5000 }));
  snapshot.observed_at = new Date(now + 6000).toISOString();
  snapshot.status.server_time = snapshot.observed_at;
  assert.throws(() => validateSnapshot(snapshot, { now, staleMs: 5000 }));
});

test('source URL policy refuses remote hosts, credentials, query strings and other endpoints', () => {
  assert.equal(typeof validateSourceUrl, 'function', 'loopback source policy is required');
  assert.equal(validateSourceUrl('http://127.0.0.1:8091/api/snapshot').hostname, '127.0.0.1');
  for (const url of ['https://127.0.0.1/api/snapshot', 'http://example.com/api/snapshot',
    'http://127.0.0.1/api/status', 'http://user:pass@127.0.0.1/api/snapshot',
    'http://127.0.0.1/api/snapshot?token=x', 'http://127.0.0.1/api/snapshot#x']) {
    assert.throws(() => validateSourceUrl(url));
  }
});

async function waitFor(predicate, timeoutMs = 7000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (await predicate()) return;
    await new Promise(resolve => setTimeout(resolve, 20));
  }
  assert.fail('Timed out waiting for the observable publisher result');
}

async function isolatedHarness(t, response = () => ({ status: 200, body: fixture() })) {
  const mqtt = require('mqtt');
  const { createBroker } = require('../broker.cjs');
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'fuxa-publisher-test-'));
  const stopFile = path.join(directory, 'STOP');
  const broker = await createBroker({ credentials, host: '127.0.0.1', port: 0, stopFile });
  const brokerUrl = `mqtt://127.0.0.1:${broker.address().port}`;
  let getResponse = response;
  const requests = [];
  const source = http.createServer((request, reply) => {
    requests.push({ method: request.method, url: request.url });
    const result = getResponse(request);
    reply.writeHead(result.status || 200, { 'content-type': 'application/json', ...(result.headers || {}) });
    reply.end(typeof result.body === 'string' ? result.body : JSON.stringify(result.body));
  });
  await new Promise(resolve => source.listen(0, '127.0.0.1', resolve));
  const sourceUrl = `http://127.0.0.1:${source.address().port}/api/snapshot`;
  const consumer = mqtt.connect(brokerUrl, { ...credentials.viewer, reconnectPeriod: 0 });
  await new Promise((resolve, reject) => { consumer.once('connect', resolve); consumer.once('error', reject); });
  const messages = [];
  consumer.on('message', (topic, body, packet) => messages.push({ topic, body: body.toString(), retain: packet.retain }));
  await new Promise((resolve, reject) => consumer.subscribe('dchr/v09/sim/#', { qos: 1 }, error => error ? reject(error) : resolve()));
  let publisher;
  t.after(async () => {
    if (publisher) await publisher.stop('test cleanup');
    await new Promise(resolve => consumer.end(false, resolve));
    await new Promise(resolve => source.close(resolve));
    await broker.close();
    fs.rmSync(directory, { recursive: true, force: true });
  });
  return { mqtt, brokerUrl, sourceUrl, stopFile, messages, requests,
    setResponse(fn) { getResponse = fn; },
    async start(options = {}) {
      publisher = createPublisher({ credentials, brokerUrl, sourceUrl, stopFile,
        intervalMs: 50, staleMs: 250, requestTimeoutMs: 100, ...options });
      await publisher.start();
      return publisher;
    },
    async retained() {
      const observer = mqtt.connect(brokerUrl, { ...credentials.viewer, reconnectPeriod: 0 });
      const packets = [];
      observer.on('message', (topic, body) => packets.push({ topic, body: body.toString() }));
      await new Promise((resolve, reject) => { observer.once('connect', resolve); observer.once('error', reject); });
      await new Promise((resolve, reject) => observer.subscribe('dchr/v09/sim/#', error => error ? reject(error) : resolve()));
      await new Promise(resolve => setTimeout(resolve, 100));
      await new Promise(resolve => observer.end(false, resolve));
      return packets;
    }
  };
}

test('real broker receives finite scalar topics with an associated D metadata packet', async t => {
  const h = await isolatedHarness(t);
  await h.start();
  await waitFor(() => h.messages.some(m => m.topic.endsWith('/meta') && JSON.parse(m.body).state === 'online'));
  const meta = h.messages.filter(m => m.topic.endsWith('/meta')).map(m => JSON.parse(m.body)).find(m => m.state === 'online');
  assert.equal(meta.source, 'D');
  assert.equal(meta.source_class, 'D_SYNTHETIC');
  assert.equal(meta.hardware_enabled, false);
  assert.equal(meta.mode, 'LOCAL_SIMULATION_ONLY');
  assert.equal(meta.quality, 'D');
  assert.equal(meta.snapshot.values.T_pool_C, 21.25);
  assert.equal(meta.snapshot.source_file, 'isolated_test_fixture.csv');
  assert.equal(meta.snapshot.status.scenario_id, 'isolated-test');
  assert.ok(Number.isInteger(meta.packet_seq));
  assert.ok(meta.packet_id.endsWith(`:${meta.packet_seq}`));
  await waitFor(() => h.messages.some(m => m.topic === 'dchr/v09/sim/value/Q_unhandled_W'));
  const retained = await h.retained();
  const scalars = retained.filter(m => m.topic.includes('/value/'));
  assert.equal(scalars.length, 10);
  assert.equal(scalars.find(m => m.topic.endsWith('/T_pool_C')).body, '21.25');
  assert.equal(scalars.every(m => Number.isFinite(JSON.parse(m.body))), true);
  assert.equal(JSON.stringify(retained).includes('THIS_MUST_NEVER_BE_EXPORTED'), false);
  assert.equal(h.requests.every(r => r.method === 'GET' && r.url === '/api/snapshot'), true);
});

test('HTTP outage clears retained numbers, marks stale, and recovers on a fresh D response', async t => {
  const h = await isolatedHarness(t);
  await h.start();
  await waitFor(() => h.messages.some(m => m.topic.endsWith('/value/COP')));
  h.setResponse(() => ({ status: 503, body: { unavailable: true } }));
  await waitFor(() => h.messages.some(m => m.topic.endsWith('/meta') && JSON.parse(m.body).state === 'stale'));
  assert.equal((await h.retained()).filter(m => m.topic.includes('/value/')).length, 0);
  h.setResponse(() => ({ status: 200, body: fixture() }));
  const recoverAfter = h.messages.length;
  await waitFor(() => h.messages.slice(recoverAfter).some(m => m.topic.endsWith('/meta') && JSON.parse(m.body).state === 'online'));
  assert.equal((await h.retained()).filter(m => m.topic.includes('/value/')).length, 10);
});

test('redirects are never followed and oversized bodies never become telemetry', async t => {
  const h = await isolatedHarness(t, () => ({ status: 302, headers: { location: '/api/status' }, body: '' }));
  await h.start();
  await waitFor(() => h.messages.some(m => m.topic.endsWith('/meta') && JSON.parse(m.body).state === 'stale'));
  assert.equal(h.requests.some(r => r.url === '/api/status'), false);
  h.setResponse(() => ({ status: 200, body: 'x'.repeat(524289) }));
  await new Promise(resolve => setTimeout(resolve, 200));
  assert.equal((await h.retained()).filter(m => m.topic.includes('/value/')).length, 0);
});

test('STOP at runtime clears retained scalars and publishes offline D metadata', async t => {
  const h = await isolatedHarness(t);
  await h.start();
  await waitFor(() => h.messages.some(m => m.topic.endsWith('/value/COP')));
  fs.writeFileSync(h.stopFile, 'isolated test stop');
  await waitFor(() => h.messages.some(m => m.topic.endsWith('/meta') && JSON.parse(m.body).state === 'offline'));
  const packets = await h.retained();
  assert.equal(packets.filter(m => m.topic.includes('/value/')).length, 0);
  assert.equal(JSON.parse(packets.find(m => m.topic.endsWith('/meta')).body).quality, 'D');
});

test('STOP at startup prevents source requests and MQTT publication', async t => {
  const h = await isolatedHarness(t);
  fs.writeFileSync(h.stopFile, 'isolated test startup stop');
  const publisher = await h.start();
  await new Promise(resolve => setTimeout(resolve, 120));
  assert.equal(h.requests.length, 0);
  assert.equal(h.messages.length, 0);
  assert.equal(publisher.state, 'stopped');
});
