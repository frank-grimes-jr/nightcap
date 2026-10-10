const { createDatabases } = require('./lib/database.cjs')
const { createOperations } = require('./lib/operations.cjs')
const { createApp } = require('./app.cjs')
const { fingerprintKey } = require('./lib/owner-state.cjs')
async function start() {
  const databases = createDatabases()
  const operations = createOperations(databases.ssh, databases)
  const app = createApp({
    databases,
    operations,
    fingerprintKey: await fingerprintKey(),
    productionWrites: process.env.NIGHTCAP_GM_PRODUCTION_WRITES === '1',
  })
  const server = app.listen(3001, '127.0.0.1', () =>
    console.log('Nightcap GM: http://127.0.0.1:3001')
  )
  server.on('error', () => {
    console.error('GM port 3001 is unavailable. Close the other GM instance.')
    process.exitCode = 1
  })
  for (const signal of ['SIGINT', 'SIGTERM'])
    process.on(signal, () =>
      server.close(() => databases.close().finally(() => process.exit()))
    )
}
start().catch(() => {
  console.error(
    'GM startup failed. Check local owner-state permissions and dependencies.'
  )
  process.exitCode = 1
})
