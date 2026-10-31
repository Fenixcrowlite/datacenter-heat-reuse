'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
test('runtime secrets use separate strong random role passwords and are stable on reload', () => {
  const { ensureSecrets, loadSecrets, LOCAL_DIR } = require('../runtime-config.cjs');
  const first = ensureSecrets();
  assert.equal(first.exporter.username, 'dchr_v09_exporter');
  assert.equal(first.viewer.username, 'dchr_v09_viewer');
  assert.match(first.exporter.password, /^[a-f0-9]{64}$/);
  assert.match(first.viewer.password, /^[a-f0-9]{64}$/);
  assert.notEqual(first.exporter.password, first.viewer.password);
  assert.deepEqual(loadSecrets(), first);
  assert.ok(fs.existsSync(path.join(LOCAL_DIR, 'secrets.json')));
});
