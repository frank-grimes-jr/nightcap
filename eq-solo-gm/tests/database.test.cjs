const test = require('node:test')
const assert = require('node:assert/strict')
const { randomUUID } = require('node:crypto')
const mysql = require('mysql2/promise')
const { createProductionSSH } = require('../api/lib/production-ssh.cjs')
const { createApp } = require('../api/app.cjs')
const { setup, UserError } = require('../api/lib/mutations.cjs')
const { hashPassword } = require('../api/lib/password.cjs')
const sodium = require('libsodium-wrappers-sumo')

test(
  'isolated MariaDB: target boundaries, transactions, receipts, accounts and character corrections',
  { skip: !process.env.GM_FIXTURE_HOST, timeout: 180000 },
  async (t) => {
    const ssh = createProductionSSH()
    const host = process.env.GM_FIXTURE_HOST
    const config = {
      user: 'root',
      password: 'gm-fixture-only',
      stream: () => ssh.stream(host, 3306),
      connectionLimit: 2,
      multipleStatements: false,
    }
    const admin = mysql.createPool(config)
    const pools = {}
    const state = {
      local: { offline: false, backupFails: false },
      production: { offline: false, backupFails: false },
    }
    const operations = {}
    let server
    try {
      for (const environment of ['local', 'production']) {
        const database = 'gm_qa_' + environment
        await admin.query(`CREATE DATABASE ${database}`)
        const db = (pools[environment] = mysql.createPool({
          ...config,
          database,
        }))
        for (const ddl of [
          'CREATE TABLE login_accounts(id INT,account_name VARCHAR(50),source_loginserver VARCHAR(64),account_password VARCHAR(128),last_login_date DATETIME,created_at DATETIME,PRIMARY KEY(id,source_loginserver)) ENGINE=InnoDB',
          'CREATE TABLE account(id INT PRIMARY KEY,lsaccount_id INT,ls_id VARCHAR(64)) ENGINE=InnoDB',
          'CREATE TABLE character_data(id INT PRIMARY KEY,account_id INT,name VARCHAR(64),level INT,level2 INT,class INT,aa_points INT DEFAULT 0,aa_points_spent INT DEFAULT 0,exp INT DEFAULT 0,zone_id INT DEFAULT 1,zone_instance INT DEFAULT 0,x FLOAT,y FLOAT,z FLOAT,heading FLOAT,deleted_at DATETIME) ENGINE=InnoDB',
          'CREATE TABLE character_currency(id INT PRIMARY KEY,platinum INT DEFAULT 0) ENGINE=InnoDB',
          'CREATE TABLE character_skills(id INT,skill_id INT,value INT,PRIMARY KEY(id,skill_id)) ENGINE=InnoDB',
          'CREATE TABLE character_multiclass(character_id INT PRIMARY KEY,class2 INT,class3 INT) ENGINE=InnoDB',
          'CREATE TABLE skill_caps(class_id INT,level INT,skill_id INT,cap INT) ENGINE=InnoDB',
          'CREATE TABLE variables(varname VARCHAR(64) PRIMARY KEY,value VARCHAR(512)) ENGINE=InnoDB',
          'CREATE TABLE rule_sets(ruleset_id INT PRIMARY KEY,name VARCHAR(64)) ENGINE=InnoDB',
          'CREATE TABLE rule_values(ruleset_id INT,rule_name VARCHAR(100),rule_value VARCHAR(100),notes VARCHAR(255),PRIMARY KEY(ruleset_id,rule_name)) ENGINE=InnoDB',
          'CREATE TABLE zone(id INT,zoneidnumber INT,version INT) ENGINE=InnoDB',
        ])
          await db.query(ddl)
        await setup(db)
        await db.query(
          "INSERT INTO rule_sets VALUES (1,'default'),(2,'unused')"
        )
        await db.query(
          "INSERT INTO rule_values VALUES (1,'Character:MaxLevel','50',''),(1,'Character:ExpMultiplier','1',''),(2,'Character:ExpMultiplier','9','')"
        )
        await db.query(
          "INSERT INTO login_accounts VALUES (1,'joe','local','before',NULL,NULL),(1,'remotejoe','external','untouched',NULL,NULL),(2,'empty','local','before',NULL,NULL)"
        )
        await db.query(
          "INSERT INTO account VALUES (10,1,'local'),(11,1,'external'),(20,2,'local')"
        )
        await db.query(
          "INSERT INTO character_data(id,account_id,name,level,level2,class,zone_instance) VALUES (100,10,'Fixture',30,30,1,77)"
        )
        await db.query('INSERT INTO character_multiclass VALUES (100,2,12)')
        await db.query(
          'INSERT INTO skill_caps VALUES (1,30,0,120),(2,30,18,150),(12,30,18,175),(12,30,43,200)'
        )
        await db.query('INSERT INTO character_skills VALUES (100,0,180)')
        await db.query('INSERT INTO zone VALUES (999,202,0)')
        operations[environment] = {
          status: async () => ({
            environment,
            game_running: !state[environment].offline,
            maintenance: state[environment].offline,
          }),
          hashPassword,
          maintenance: async (start) => {
            state[environment].offline = start
            return {}
          },
          withLease: async (options, action) => {
            if (options.offline && !state[environment].offline)
              throw new UserError('Maintenance required', 409)
            if (state[environment].backupFails)
              throw new Error('backup fixture failure')
            return action({ backup: 'fixture.sql.gz' }, () => {})
          },
          access: async (op, values) => ({
            op,
            ...values,
            ready: true,
            credentials: [],
          }),
        }
      }
      const port = 31991
      const app = createApp({
        databases: pools,
        operations,
        port,
        productionWrites: true,
      })
      server = await new Promise((resolve) => {
        const s = app.listen(port, '127.0.0.1', () => resolve(s))
      })
      const origin = `http://127.0.0.1:${port}`
      const session = await fetch(origin + '/api/session', {
        headers: { 'X-Nightcap-Owner': '1' },
      }).then((r) => r.json())
      async function call(
        method,
        endpoint,
        body = {},
        requestId = randomUUID(),
        target = 'production'
      ) {
        const response = await fetch(origin + '/api/production' + endpoint, {
          method,
          headers: {
            'Content-Type': 'application/json',
            'X-Nightcap-Session': session.token,
            'X-Nightcap-Target': target,
            'X-Request-Id': requestId,
          },
          ...(method === 'GET' ? {} : { body: JSON.stringify(body) }),
        })
        return { status: response.status, body: await response.json() }
      }
      const query = async (sql) => (await pools.production.query(sql))[0]
      await t.test('target and offline guards reject writes', async () => {
        assert.equal(
          (
            await call(
              'POST',
              '/character/100/currency',
              { platinum: 25 },
              randomUUID(),
              'local'
            )
          ).status,
          409
        )
        assert.equal(
          (await call('POST', '/character/100/currency', { platinum: 25 }))
            .status,
          409
        )
        assert.equal(
          (await query('SELECT COUNT(*) n FROM character_currency'))[0].n,
          0
        )
        state.production.offline = true
      })
      await t.test(
        'grant commits once, replay returns receipt, mismatched replay rejects',
        async () => {
          const key = randomUUID()
          assert.equal(
            (
              await call(
                'POST',
                '/character/100/currency',
                { platinum: 25 },
                key
              )
            ).status,
            200
          )
          assert.equal(
            (
              await call(
                'POST',
                '/character/100/currency',
                { platinum: 25 },
                key
              )
            ).status,
            200
          )
          assert.equal(
            (
              await call(
                'POST',
                '/character/100/currency',
                { platinum: 26 },
                key
              )
            ).status,
            409
          )
          assert.equal(
            (
              await query(
                'SELECT platinum FROM character_currency WHERE id=100'
              )
            )[0].platinum,
            25
          )
          assert.equal(
            (
              await pools.local.query(
                'SELECT COUNT(*) n FROM character_currency'
              )
            )[0][0].n,
            0
          )
        }
      )
      await t.test(
        'backup failure and invalid input leave data unchanged',
        async () => {
          state.production.backupFails = true
          assert.equal(
            (await call('POST', '/character/100/aa', { points: 20 })).status,
            503
          )
          state.production.backupFails = false
          assert.equal(
            (await call('POST', '/character/100/aa', { points: 0.5 })).status,
            400
          )
          assert.equal(
            (
              await query('SELECT aa_points FROM character_data WHERE id=100')
            )[0].aa_points,
            0
          )
        }
      )
      await t.test(
        'boost and teleport use cap, canonical zone ID and clear instance',
        async () => {
          assert.equal(
            (await call('POST', '/character/100/boost', { level: 100 })).body
              .level,
            50
          )
          assert.equal(
            (
              await call('POST', '/character/100/teleport', {
                zone_id: 999,
                x: 0,
                y: 0,
                z: 0,
              })
            ).status,
            400
          )
          assert.equal(
            (
              await call('POST', '/character/100/teleport', {
                zone_id: 202,
                x: 1,
                y: 2,
                z: 3,
              })
            ).status,
            200
          )
          const [row] = await query(
            'SELECT level,zone_id,zone_instance FROM character_data WHERE id=100'
          )
          assert.deepEqual(row, { level: 50, zone_id: 202, zone_instance: 0 })
        }
      )
      await t.test(
        'max skills respects held classes and preserves specialized/existing skills',
        async () => {
          assert.equal(
            (await call('POST', '/character/100/maxskills')).status,
            200
          )
          assert.deepEqual(
            await query(
              'SELECT skill_id,value FROM character_skills WHERE id=100 ORDER BY skill_id'
            ),
            [
              { skill_id: 0, value: 180 },
              { skill_id: 18, value: 175 },
            ]
          )
        }
      )
      await t.test(
        'password reset is source-qualified scrypt and receipts contain no secret',
        async () => {
          state.production.offline = false
          const input = {
            account_name: 'joe',
            source_loginserver: 'local',
            new_password: 'fixture-password',
          }
          const reply = await call('PATCH', '/accounts/1/password', input)
          assert.equal(reply.status, 200)
          const rows = await query(
            'SELECT source_loginserver,account_password FROM login_accounts WHERE id=1'
          )
          await sodium.ready
          assert.equal(
            sodium.crypto_pwhash_scryptsalsa208sha256_str_verify(
              rows.find((r) => r.source_loginserver === 'local')
                .account_password,
              input.new_password
            ),
            true
          )
          assert.equal(
            rows.find((r) => r.source_loginserver === 'external')
              .account_password,
            'untouched'
          )
          assert.equal(
            JSON.stringify(await query('SELECT * FROM gm_operations')).includes(
              input.new_password
            ),
            false
          )
          assert.equal(
            (
              await call('PATCH', '/accounts/1/password', {
                ...input,
                account_name: 'other',
              })
            ).status,
            409
          )
          assert.equal(
            (
              await call('PATCH', '/accounts/1/password', {
                ...input,
                source_loginserver: 'external',
                account_name: 'remotejoe',
              })
            ).status,
            409
          )
        }
      )
      await t.test(
        'deletion rejects character ownership and rolls back multi-table failures',
        async () => {
          state.production.offline = true
          assert.equal(
            (
              await call('DELETE', '/accounts/1', {
                account_name: 'joe',
                source_loginserver: 'local',
              })
            ).status,
            409
          )
          await pools.production.query(
            "CREATE TRIGGER qa_reject_delete BEFORE DELETE ON login_accounts FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='fixture rollback'"
          )
          assert.equal(
            (
              await call('DELETE', '/accounts/2', {
                account_name: 'empty',
                source_loginserver: 'local',
              })
            ).status,
            503
          )
          assert.equal(
            (await query('SELECT COUNT(*) n FROM account WHERE id=20'))[0].n,
            1
          )
          await pools.production.query('DROP TRIGGER qa_reject_delete')
          assert.equal(
            (
              await call('DELETE', '/accounts/2', {
                account_name: 'empty',
                source_loginserver: 'local',
              })
            ).status,
            200
          )
        }
      )
      await t.test(
        'rule preset rolls back fully when a rule is absent and scopes active ruleset',
        async () => {
          const bad = await call('PATCH', '/rules', {
            rules: {
              'Character:ExpMultiplier': '3',
              'Zone:GlobalLootMultiplier': '2',
            },
          })
          assert.equal(bad.status, 409)
          assert.equal(
            (
              await query(
                "SELECT rule_value FROM rule_values WHERE ruleset_id=1 AND rule_name='Character:ExpMultiplier'"
              )
            )[0].rule_value,
            '1'
          )
          assert.equal(
            (
              await call('PATCH', '/rules', {
                rules: { 'Character:ExpMultiplier': '3' },
              })
            ).status,
            200
          )
          assert.equal(
            (
              await query(
                "SELECT rule_value FROM rule_values WHERE ruleset_id=2 AND rule_name='Character:ExpMultiplier'"
              )
            )[0].rule_value,
            '9'
          )
          assert.equal(
            (
              await call('PATCH', '/rules', {
                rules: { 'Character:MaxLevel': '99' },
              })
            ).status,
            400
          )
        }
      )
      await t.test(
        'progression batches validate all keys and persist atomically',
        async () => {
          const { PROGRESSION_BOSSES } = require('../api/lib/catalogs.cjs')
          const keys = PROGRESSION_BOSSES[0].bosses
            .slice(0, 2)
            .map((b) => b.key)
          assert.equal(
            (
              await call('PATCH', '/character/100/progression', {
                keys: [...keys, 'invalid'],
                killed: true,
              })
            ).status,
            400
          )
          assert.equal(
            (await query('SELECT COUNT(*) n FROM gm_progression_kills'))[0].n,
            0
          )
          assert.equal(
            (
              await call('PATCH', '/character/100/progression', {
                keys,
                killed: true,
              })
            ).status,
            200
          )
          assert.equal(
            (await query('SELECT COUNT(*) n FROM gm_progression_kills'))[0].n,
            2
          )
        }
      )
      await t.test(
        'player labels match canonical registry format and era cannot bypass policy',
        async () => {
          assert.equal(
            (await call('POST', '/access', { player: 'Joe Smith' })).body
              .player,
            'joe-smith'
          )
          assert.equal(
            (await call('POST', '/expansion/apply', { expansion_id: 5 }))
              .status,
            409
          )
        }
      )
      await t.test(
        'receipt identity survives backend restart with the private stable key',
        async () => {
          const { mutationService } = require('../api/lib/mutations.cjs')
          const key = Buffer.alloc(32, 7)
          const requestId = randomUUID()
          const request = {
            method: 'POST',
            path: '/fixture/restart-grant',
            body: { platinum: 17 },
            get: () => requestId,
          }
          const options = {
            offline: true,
            backup: true,
            tables: ['character_currency'],
          }
          const grant = async (conn) => {
            await conn.query(
              'UPDATE character_currency SET platinum=platinum+17 WHERE id=100'
            )
            return { success: true }
          }
          await mutationService(
            pools.production,
            operations.production,
            'production',
            key
          ).mutate(request, options, grant)
          await mutationService(
            pools.production,
            operations.production,
            'production',
            key
          ).mutate(request, options, grant)
          assert.equal(
            (
              await query(
                'SELECT platinum FROM character_currency WHERE id=100'
              )
            )[0].platinum,
            42
          )
        }
      )
      await t.test(
        'lost lease destroys its SQL connection and releases fence only after rollback',
        async () => {
          const { mutationService } = require('../api/lib/mutations.cjs')
          const controller = new AbortController()
          const leaseOps = {
            withLease: async (_options, action) =>
              action(
                { backup: 'fixture.sql.gz' },
                () => {
                  if (controller.signal.aborted) throw new Error('lost lease')
                },
                controller.signal
              ),
          }
          const request = {
            method: 'POST',
            path: '/fixture/lease-loss',
            body: {},
            get: () => randomUUID(),
          }
          const service = mutationService(
            pools.production,
            leaseOps,
            'production'
          )
          await assert.rejects(
            service.mutate(
              request,
              { tables: ['character_currency'] },
              async (conn) => {
                await conn.query(
                  'UPDATE character_currency SET platinum=platinum+100 WHERE id=100'
                )
                controller.abort()
                await conn.query('SELECT 1')
                return { success: true }
              }
            )
          )
          assert.equal(
            (
              await query(
                'SELECT platinum FROM character_currency WHERE id=100'
              )
            )[0].platinum,
            42
          )
          assert.equal(
            Number(
              (
                await query("SELECT IS_FREE_LOCK('nightcap_gm_writes') AS free")
              )[0].free
            ),
            1
          )
        }
      )
    } finally {
      if (server) await new Promise((resolve) => server.close(resolve))
      for (const db of Object.values(pools)) await db.end()
      for (const environment of ['local', 'production'])
        await admin
          .query(`DROP DATABASE IF EXISTS gm_qa_${environment}`)
          .catch(() => {})
      await admin.end()
      ssh.close()
    }
  }
)
