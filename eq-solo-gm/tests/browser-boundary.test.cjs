const test = require('node:test')
const assert = require('node:assert/strict')
const express = require('express')
const http = require('node:http')
const { ownerBoundary } = require('../api/lib/browser-boundary.cjs')
const { createApp } = require('../api/app.cjs')

test('real HTTP owner boundary rejects cross-site, rebinding and invalid sessions', async (t) => {
  const app = express()
  let guard
  app.use((req, res, next) => guard(req, res, next))
  app.get('/production/api/accounts', (_req, res) =>
    res.json({ environment: 'production' })
  )
  const server = app.listen(0, '127.0.0.1')
  await new Promise((resolve) => server.once('listening', resolve))
  t.after(() => server.close())
  const port = server.address().port
  const url = `http://127.0.0.1:${port}`
  guard = ownerBoundary({ apiPort: port })
  for (const headers of [
    {},
    { 'x-nightcap-owner': '1', origin: 'https://untrusted.example' },
    { 'x-nightcap-owner': '1', 'sec-fetch-site': 'cross-site' },
  ]) {
    const response = await fetch(url + '/api/session', { headers })
    assert.ok(
      [401, 403].includes(response.status),
      JSON.stringify({ headers, status: response.status })
    )
    assert.equal(response.headers.get('access-control-allow-origin'), null)
  }
  // Fetch normalizes Host; use actual raw HTTP headers to exercise DNS rebinding.
  const rebound = await new Promise((resolve, reject) => {
    const request = http.get(
      url + '/api/session',
      { headers: { host: 'rebind.example', 'x-nightcap-owner': '1' } },
      (response) => {
        response.resume()
        resolve(response.statusCode)
      }
    )
    request.on('error', reject)
  })
  assert.equal(rebound, 403)
  const session = await fetch(url + '/api/session', {
    headers: { 'x-nightcap-owner': '1' },
  })
  assert.equal(session.status, 200)
  assert.equal(session.headers.get('cache-control'), 'no-store')
  const { token } = await session.json()
  for (const value of ['', 'é'.repeat(64), 'f'.repeat(64)]) {
    const response = await fetch(url + '/production/api/accounts', {
      headers: { 'x-nightcap-session': value },
    })
    assert.equal(response.status, 401)
  }
  const response = await fetch(url + '/production/api/accounts', {
    headers: { 'x-nightcap-session': token },
  })
  assert.equal(response.status, 200)
  const foreign = await fetch(url + '/production/api/accounts', {
    headers: { 'x-nightcap-session': token, origin: 'http://evil.example' },
  })
  assert.equal(foreign.status, 403)
})

test('production preview refuses every write before touching its database or runtime', async (t) => {
  let app
  let reads = 0
  const database = {
    query: async () => {
      reads++
      return [[]]
    },
  }
  const server = http
    .createServer((req, res) => app(req, res))
    .listen(0, '127.0.0.1')
  await new Promise((resolve) => server.once('listening', resolve))
  t.after(() => server.close())
  const port = server.address().port
  app = createApp({
    databases: { local: database, production: database },
    operations: { local: {}, production: {} },
    port,
  })
  const url = `http://127.0.0.1:${port}`
  const { token } = await (
    await fetch(url + '/api/session', {
      headers: { 'x-nightcap-owner': '1' },
    })
  ).json()
  const headers = {
    'x-nightcap-session': token,
    'x-nightcap-target': 'production',
  }
  for (const [method, endpoint] of [
    ['POST', '/setup'],
    ['POST', '/maintenance/start'],
    ['POST', '/access'],
    ['PATCH', '/accounts/1/password'],
    ['DELETE', '/accounts/1'],
  ]) {
    const response = await fetch(url + '/api/production' + endpoint, {
      method,
      headers,
    })
    assert.equal(response.status, 409)
    assert.match(
      (await response.json()).error,
      /Production changes are disabled/
    )
  }
  assert.equal(reads, 0)
  assert.equal(
    (await fetch(url + '/api/production/accounts', { headers })).status,
    200
  )
  assert.equal(reads, 1)
})
