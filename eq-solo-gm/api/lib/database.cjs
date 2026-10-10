const mysql = require('mysql2/promise')
const { createProductionSSH } = require('./production-ssh.cjs')

function createDatabases() {
  const ssh = createProductionSSH()
  const local = mysql.createPool({
    host: '127.0.0.1',
    port: 3307,
    user: 'eqemu',
    password: 'eqemu',
    database: 'peq',
    connectionLimit: 3,
    connectTimeout: 8000,
  })
  let productionPromise
  async function production() {
    if (!productionPromise) {
      productionPromise = ssh
        .run('connection')
        .then((config) => {
          if (
            config.database !== 'peq' ||
            typeof config.user !== 'string' ||
            typeof config.password !== 'string'
          )
            throw new Error('Unexpected production database identity')
          return mysql.createPool({
            user: config.user,
            password: config.password,
            database: config.database,
            stream: () => ssh.stream(config.host, config.port),
            connectionLimit: 3,
            queueLimit: 12,
            waitForConnections: true,
            connectTimeout: 10000,
            multipleStatements: false,
            supportBigNumbers: true,
          })
        })
        .catch((error) => {
          productionPromise = null
          throw error
        })
    }
    return productionPromise
  }
  return {
    local,
    production: {
      query: async (...args) => (await production()).query(...args),
      getConnection: async () => (await production()).getConnection(),
    },
    ssh,
    async close() {
      await local.end()
      if (productionPromise) {
        try {
          await (await productionPromise).end()
        } catch {}
      }
      ssh.close()
    },
  }
}
module.exports = { createDatabases }
