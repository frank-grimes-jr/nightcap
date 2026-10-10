const crypto = require('node:crypto')

function ownerBoundary({
  apiPort = 3001,
  uiPort = 5173,
  productionWrites = false,
} = {}) {
  const token = crypto.randomBytes(32).toString('hex')
  const hosts = new Set([`127.0.0.1:${apiPort}`, `localhost:${apiPort}`])
  const origins = new Set(
    [...hosts, `127.0.0.1:${uiPort}`, `localhost:${uiPort}`].map(
      (host) => `http://${host}`
    )
  )
  function guard(req, res, next) {
    res.set('Cache-Control', 'no-store')
    res.set('X-Content-Type-Options', 'nosniff')
    res.set('Referrer-Policy', 'no-referrer')
    res.set('X-Frame-Options', 'DENY')
    const origin = req.get('origin')
    if (
      !hosts.has(req.get('host')) ||
      (origin && !origins.has(origin)) ||
      req.get('sec-fetch-site') === 'cross-site'
    ) {
      return res
        .status(403)
        .json({ error: 'Open the GM tool from its local shortcut.' })
    }
    if (
      req.path === '/api/session' &&
      req.method === 'GET' &&
      req.get('x-nightcap-owner') === '1'
    ) {
      return res.json({
        token,
        production_writes_enabled: productionWrites,
        environments: [
          { id: 'local', label: 'Local development' },
          { id: 'production', label: 'OVH production' },
        ],
      })
    }
    const supplied = req.get('x-nightcap-session') || ''
    if (
      !/^[a-f0-9]{64}$/.test(supplied) ||
      !crypto.timingSafeEqual(Buffer.from(supplied), Buffer.from(token))
    ) {
      return res
        .status(401)
        .json({ error: 'Your GM session expired. Reload this page.' })
    }
    next()
  }
  return guard
}

module.exports = { ownerBoundary }
