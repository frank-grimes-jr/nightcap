const fs = require('node:fs/promises')
const path = require('node:path')
const { promisify } = require('node:util')
const { execFile } = require('node:child_process')
const { assert, fields, UserError } = require('./mutations.cjs')
const { activeRuleset, wrap } = require('./router.cjs')
const { EXPANSION_DEFS } = require('./catalogs.cjs')
const { ROOT } = require('./operations.cjs')
const runFile = promisify(execFile)

async function clientFile() {
  const candidate =
    process.env.NIGHTCAP_CLIENT_INI || 'C:\\Nightcap\\eqclient.ini'
  let resolved
  try {
    resolved = await fs.realpath(candidate)
  } catch {
    throw new UserError(
      'The owner client copy was not found. Configure NIGHTCAP_CLIENT_INI in the local GM shortcut settings.',
      409
    )
  }
  assert(
    path.basename(resolved).toLowerCase() === 'eqclient.ini' &&
      !resolved.toLowerCase().split(/[\\/]/).includes('client_rof2_dev'),
    'The protected development client cannot be edited',
    403
  )
  const info = await fs.stat(resolved)
  assert(
    info.isFile() && info.size < 1024 * 1024,
    'Unexpected client settings file'
  )
  return resolved
}
async function committedEra() {
  // Read committed source rather than an arbitrary browser-provided config.
  const { stdout } = await runFile('git', ['show', 'HEAD:era.json'], {
    cwd: ROOT,
    windowsHide: true,
    timeout: 10000,
  })
  return JSON.parse(stdout)
}

function extraRoutes(router, { db, ops, mutations, change, offline }) {
  router.get(
    '/client/settings',
    wrap(async (_req, res) => {
      const file = await clientFile()
      const text = await fs.readFile(file, 'utf8')
      const setting = text.match(/^AllLuclinPcModelsOff=(TRUE|FALSE)\s*$/m)?.[1]
      assert(setting, 'Client model setting is absent or ambiguous', 409)
      res.json({
        AllLuclinPcModelsOff: setting,
        usingLuclinModels: setting === 'FALSE',
        path: file,
        scope: 'This computer only',
      })
    })
  )
  router.patch(
    '/client/settings',
    wrap(async (req, res) => {
      fields(req.body, ['AllLuclinPcModelsOff'])
      assert(
        ['TRUE', 'FALSE'].includes(req.body.AllLuclinPcModelsOff),
        'Select classic or Luclin models'
      )
      res.json(
        await mutations.exclusive(async () => {
          const file = await clientFile()
          const source = await fs.readFile(file, 'utf8')
          assert(
            (source.match(/^AllLuclinPcModelsOff=.*$/gm) || []).length === 1,
            'Expected exactly one client model setting',
            409
          )
          const backup = file + '.gm-' + Date.now() + '.bak'
          await fs.copyFile(file, backup, 1)
          const temp = file + '.gm-pending'
          try {
            await fs.writeFile(
              temp,
              source.replace(
                /^AllLuclinPcModelsOff=.*$/m,
                'AllLuclinPcModelsOff=' + req.body.AllLuclinPcModelsOff
              ),
              { flag: 'wx' }
            )
            await fs.rename(temp, file)
          } catch (error) {
            await fs.unlink(temp).catch(() => {})
            throw error
          }
          return { success: true, scope: 'This computer only', backup }
        })
      )
    })
  )
  router.get('/expansions', (_req, res) => res.json(EXPANSION_DEFS))
  async function expansionStatus() {
    const set = await activeRuleset(db)
    const [rules] = await db.query(
      "SELECT rule_name,rule_value FROM rule_values WHERE ruleset_id=? AND rule_name IN ('Expansion:CurrentExpansion','Character:MaxLevel','Expansion:UseCurrentExpansionAAOnly')",
      [set]
    )
    const values = Object.fromEntries(
      rules.map((r) => [r.rule_name, r.rule_value])
    )
    const current = EXPANSION_DEFS.find(
      (e) => e.id === Number(values['Expansion:CurrentExpansion'])
    )
    assert(current, 'Expansion rule is missing', 409)
    return {
      expansion_id: current.id,
      expansion_name: current.name,
      expansion_short: current.short,
      max_level: Number(values['Character:MaxLevel']),
      year: current.year,
      aa_open: values['Expansion:UseCurrentExpansionAAOnly'] === 'false',
      declared: await committedEra(),
    }
  }
  router.get(
    '/expansion/status',
    wrap(async (_req, res) => res.json(await expansionStatus()))
  )
  router.get(
    '/expansion/:id/preview',
    wrap(async (req, res) => {
      const target = EXPANSION_DEFS.find((e) => String(e.id) === req.params.id)
      assert(target, 'Invalid expansion')
      const current = await expansionStatus()
      const [[locked]] = await db.query(
        'SELECT COUNT(*) AS cnt FROM zone WHERE expansion>? AND bypass_expansion_check=0',
        [target.id]
      )
      const [zones] = await db.query(
        'SELECT long_name,short_name,expansion FROM zone WHERE expansion>? AND bypass_expansion_check=0 ORDER BY expansion,long_name LIMIT 300',
        [target.id]
      )
      const [added] = await db.query(
        'SELECT long_name,short_name FROM zone WHERE expansion=? ORDER BY long_name',
        [target.id]
      )
      const [[over]] = await db.query(
        'SELECT COUNT(*) AS cnt FROM character_data WHERE level>? AND deleted_at IS NULL',
        [target.max_level]
      )
      const [byExp] = await db.query(
        'SELECT expansion,COUNT(*) AS count FROM zone WHERE expansion>? AND bypass_expansion_check=0 GROUP BY expansion ORDER BY expansion',
        [target.id]
      )
      const [[aa]] = await db.query(
        'SELECT SUM(expansion>?) AS higher,SUM(expansion<=?) AS earlier FROM aa_ranks',
        [target.id, target.id]
      )
      res.json({
        target,
        current_expansion_id: current.expansion_id,
        current_max_level: current.max_level,
        locked_zone_count: locked.cnt,
        added_zone_count: added.length,
        locked_zones: zones,
        added_zones: added,
        zones_by_exp: byExp,
        chars_over_cap: over.cnt,
        hidden_aa_count: current.aa_open ? 0 : aa.higher,
        accessible_aa_count: current.aa_open
          ? Number(aa.higher) + Number(aa.earlier)
          : aa.earlier,
        declared: current.declared,
        requires_release: true,
        client: {
          current_all_luclin_off: null,
          target_all_luclin_off: target.id >= 3 ? 'FALSE' : 'TRUE',
          models_label: target.id >= 3 ? 'Luclin models' : 'Classic models',
          will_change: false,
          ini_found: false,
        },
      })
    })
  )
  router.post(
    '/expansion/apply',
    wrap(async () => {
      throw new UserError(
        'Era changes require a committed era.json, reviewed merchant catalog and the apply-era release workflow. The GM tool cannot bypass this repository policy.',
        409
      )
    })
  )
  router.post(
    '/vendors/refresh',
    wrap(async (req, res) => {
      fields(req.body, [])
      res.json(
        await mutations.exclusive(async () => {
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
            return await ops.withLease(
              { offline: true, backup: true, tables: ['merchantlist'] },
              async (_lease, checkLease, signal) => {
                const onLost = () => conn.destroy()
                signal?.addEventListener('abort', onLost, { once: true })
                try {
                  // This reviewed SQL owns its transaction, drift guards and advisory lock.
                  // It is idempotent; never run the retired DELETE/rebuild handler.
                  const source = await fs.readFile(
                    path.join(ROOT, 'eq-solo-gm/scripts/vendor_restock.sql'),
                    'utf8'
                  )
                  const match = source.match(
                    /DELIMITER \/\/\s*(BEGIN NOT ATOMIC[\s\S]*?END) \/\/\s*DELIMITER ;/
                  )
                  assert(
                    match,
                    'Canonical restock format changed; review it before running',
                    409
                  )
                  await checkLease()
                  await conn.query(match[1])
                  await checkLease()
                  const [rows] = await conn.query(
                    'SELECT merchantid,COUNT(*) AS count FROM merchantlist WHERE merchantid IN (99221,99222,99223,99224,99251,99252,99253) OR merchantid BETWEEN 99300 AND 99315 GROUP BY merchantid'
                  )
                  return {
                    success: true,
                    archetypes: rows.map((r) => ({
                      label: `Merchant ${r.merchantid}`,
                      count: r.count,
                    })),
                    message:
                      'Canonical stock restored. Resume the game to load it.',
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
      )
    })
  )
}
module.exports = { extraRoutes, clientFile }
