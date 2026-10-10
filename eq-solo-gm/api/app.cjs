const express = require('express')
const path = require('node:path')
const { ownerBoundary } = require('./lib/browser-boundary.cjs')
const { createRouter } = require('./lib/router.cjs')
const { extraRoutes } = require('./lib/settings.cjs')
const { UserError } = require('./lib/mutations.cjs')

function createApp({
  databases,
  operations,
  port = 3001,
  productionWrites = false,
  fingerprintKey,
}) {
  const app = express()
  app.disable('x-powered-by')
  const guard = ownerBoundary({ apiPort: port, productionWrites })
  app.use((req, res, next) => {
    res.set('X-Frame-Options', 'DENY')
    res.set('X-Content-Type-Options', 'nosniff')
    res.set('Referrer-Policy', 'no-referrer')
    res.set(
      'Content-Security-Policy',
      "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    )
    if (![`127.0.0.1:${port}`, `localhost:${port}`].includes(req.get('host')))
      return res.sendStatus(403)
    if (req.path.startsWith('/api/')) return guard(req, res, next)
    next()
  })
  app.use(express.json({ limit: '16kb', strict: true }))
  for (const environment of ['local', 'production']) {
    app.use(
      `/api/${environment}`,
      (req, res, next) => {
        if (
          environment === 'production' &&
          req.method !== 'GET' &&
          !productionWrites
        )
          return res.status(409).json({
            error:
              'Production changes are disabled until the reviewed GM release is approved and enabled.',
          })
        next()
      },
      createRouter({
        db: databases[environment],
        ops: operations[environment],
        environment,
        extraRoutes,
        fingerprintKey,
        writesEnabled: environment === 'local' || productionWrites,
      })
    )
  }
  app.use('/api', (_req, res) =>
    res.status(404).json({ error: 'Unknown GM operation' })
  )
  app.use(express.static(path.resolve(__dirname, '../dist'), { maxAge: 0 }))
  app.get('*', (_req, res) =>
    res.sendFile(path.resolve(__dirname, '../dist/index.html'))
  )
  app.use((error, _req, res, _next) => {
    // Never forward SQL/SSH diagnostics, query values, hashes or stack traces.
    const missingSetup = error.code === 'ER_NO_SUCH_TABLE'
    const message =
      error instanceof UserError
        ? error.message
        : missingSetup
          ? 'A required table is missing. Check GM setup and the selected database.'
          : 'The operation could not be confirmed. Check the server connection and action history before retrying.'
    res
      .status(
        error instanceof UserError
          ? error.status
          : error.type === 'entity.parse.failed'
            ? 400
            : 503
      )
      .json({ error: message })
  })
  return app
}
module.exports = { createApp }
