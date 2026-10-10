const crypto = require('node:crypto')

class UserError extends Error {
  constructor(message, status = 400) {
    super(message)
    this.status = status
  }
}
const assert = (condition, message, status) => {
  if (!condition) throw new UserError(message, status)
}
const integer = (value, min, max, label) => {
  assert(
    Number.isSafeInteger(value) && value >= min && value <= max,
    `${label} must be a whole number from ${min} to ${max}`
  )
  return value
}
const id = (value) => {
  assert(/^[1-9]\d{0,9}$/.test(String(value)), 'Invalid ID')
  return integer(Number(value), 1, 2147483647, 'ID')
}
const fields = (body, allowed) =>
  assert(
    body &&
      !Array.isArray(body) &&
      Object.keys(body).every((k) => allowed.includes(k)),
    'Unexpected request fields'
  )

async function setup(db) {
  // Explicit owner action, never app startup. IF NOT EXISTS makes interrupted setup resumable.
  await db.query(`CREATE TABLE IF NOT EXISTS gm_operations (
    request_id CHAR(36) PRIMARY KEY, operation VARCHAR(160) NOT NULL,
    fingerprint CHAR(64) NOT NULL, result LONGTEXT NOT NULL, backup_name VARCHAR(160),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4`)
  await db.query(`CREATE TABLE IF NOT EXISTS gm_progression_kills (
    character_id INT NOT NULL, boss_key VARCHAR(100) NOT NULL,
    killed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(character_id,boss_key)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4`)
  return { success: true }
}

function mutationService(
  db,
  ops,
  environment,
  fingerprintKey = crypto.randomBytes(32)
) {
  let busy = false
  async function exclusive(action) {
    assert(
      !busy,
      'Another GM action is in progress. Wait for it to finish.',
      409
    )
    busy = true
    try {
      return await action()
    } finally {
      busy = false
    }
  }
  async function mutate(req, options, action) {
    const requestId = req.get('x-request-id') || ''
    assert(
      /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(
        requestId
      ),
      'A unique action ID is required'
    )
    const operation = req.method + ' ' + req.path
    const fingerprint = crypto
      .createHmac('sha256', fingerprintKey)
      .update(JSON.stringify([environment, operation, req.body ?? {}]))
      .digest('hex')
    return exclusive(async () => {
      // Establish the SSH DB stream before taking the remote maintenance lock.
      const conn = await db.getConnection()
      let fenced = false
      try {
        const [[lock]] = await conn.query(
          "SELECT GET_LOCK('nightcap_gm_writes',0) AS held"
        )
        assert(
          Number(lock.held) === 1,
          'Another GM database action is in progress',
          409
        )
        fenced = true
        const [[prior]] = await conn.query(
          'SELECT operation,fingerprint,result FROM gm_operations WHERE request_id=?',
          [requestId]
        )
        if (prior) {
          assert(
            prior.operation === operation && prior.fingerprint === fingerprint,
            'This action ID was already used. Inspect its receipt before attempting another change.',
            409
          )
          return JSON.parse(prior.result)
        }
        return await ops.withLease(
          options,
          async (lease, checkLease, signal) => {
            const onLost = () => conn.destroy()
            signal?.addEventListener('abort', onLost, { once: true })
            try {
              await checkLease()
              const [engines] = await conn.query(
                'SELECT TABLE_NAME,ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME IN (?)',
                [['gm_operations', ...options.tables]]
              )
              assert(
                engines.length ===
                  new Set(['gm_operations', ...options.tables]).size &&
                  engines.every((r) => r.ENGINE === 'InnoDB'),
                'All affected tables must exist and use InnoDB before this action.',
                409
              )
              await conn.beginTransaction()
              try {
                const result = await action(conn)
                result.request_id = requestId
                result.environment = environment
                await checkLease()
                await conn.query(
                  'INSERT INTO gm_operations(request_id,operation,fingerprint,result,backup_name) VALUES (?,?,?,?,?)',
                  [
                    requestId,
                    operation,
                    fingerprint,
                    JSON.stringify(result),
                    lease.backup,
                  ]
                )
                await checkLease()
                await conn.commit()
                return result
              } catch (error) {
                await conn.rollback().catch(() => {})
                throw error
              }
            } finally {
              signal?.removeEventListener('abort', onLost)
            }
          }
        )
      } finally {
        if (fenced)
          await conn
            .query("SELECT RELEASE_LOCK('nightcap_gm_writes')")
            .catch(() => conn.destroy())
        conn.release()
      }
    })
  }
  return { mutate, exclusive }
}
module.exports = {
  UserError,
  assert,
  integer,
  id,
  fields,
  setup,
  mutationService,
}
