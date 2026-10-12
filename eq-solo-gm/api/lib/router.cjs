const express = require('express')
const {
  levelRules,
  boostedState,
  validateLevelAcrossZones,
} = require('./character-level.cjs')
const {
  assert,
  id,
  integer,
  fields,
  setup,
  mutationService,
} = require('./mutations.cjs')
const { EXPANSION_DEFS, PROGRESSION_BOSSES } = require('./catalogs.cjs')
const RULES = {
  'Character:ExpMultiplier': [0, 100],
  'Character:AAExpMultiplier': [0, 100],
  'AA:ExpPerPoint': [1, 2147483647, true],
  'Zone:GlobalLootMultiplier': [0, 100, true],
  'Character:DeathExpLossMultiplier': [0, 10, true],
}
const BOSSES = new Set(
  PROGRESSION_BOSSES.flatMap((e) => e.bosses.map((b) => b.key))
)
const wrap = (fn) => (req, res, next) =>
  Promise.resolve()
    .then(() => fn(req, res))
    .catch(next)

async function activeRuleset(db) {
  const [[row]] = await db.query(
    "SELECT ruleset_id FROM rule_sets WHERE name=COALESCE((SELECT value FROM variables WHERE varname='RuleSet' LIMIT 1),'default')"
  )
  assert(row, 'The active ruleset could not be identified', 409)
  return Number(row.ruleset_id)
}
async function character(db, value) {
  const [[row]] = await db.query(
    'SELECT * FROM character_data WHERE id=? AND deleted_at IS NULL FOR UPDATE',
    [id(value)]
  )
  assert(row, 'Character not found', 404)
  return row
}
async function account(db, value, body) {
  assert(
    typeof body.source_loginserver === 'string' &&
      body.source_loginserver.length <= 64,
    'Login source is required'
  )
  assert(typeof body.account_name === 'string', 'Account name is required')
  const [rows] = await db.query(
    'SELECT id,account_name,source_loginserver FROM login_accounts WHERE id=? AND source_loginserver=? FOR UPDATE',
    [id(value), body.source_loginserver]
  )
  assert(
    rows.length === 1 && rows[0].account_name === body.account_name,
    'Account identity changed; refresh before editing',
    409
  )
  assert(
    rows[0].source_loginserver === 'local',
    'Reset or delete externally managed accounts at their login provider',
    409
  )
  return rows[0]
}

function createRouter({
  db,
  ops,
  environment,
  extraRoutes,
  fingerprintKey,
  writesEnabled = true,
}) {
  const router = express.Router()
  const mutations = mutationService(db, ops, environment, fingerprintKey)
  const change = (options, fn) =>
    wrap(async (req, res) =>
      res.json(await mutations.mutate(req, options, (conn) => fn(conn, req)))
    )
  const offline = (tables) => ({ offline: true, backup: true, tables })
  router.use((req, res, next) => {
    if (req.method !== 'GET' && req.get('x-nightcap-target') !== environment)
      return res.status(409).json({
        error: 'The environment confirmation does not match this action.',
      })
    next()
  })
  router.get(
    '/ping',
    wrap(async (_req, res) => {
      await db.query('SELECT 1')
      res.json({ ok: true, db: 'connected', environment })
    })
  )
  router.get(
    '/status',
    wrap(async (_req, res) => {
      const state = await ops.status()
      const [tables] = await db.query(
        "SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME IN ('gm_operations','gm_progression_kills')"
      )
      res.json({
        ...state,
        setup_ready: tables.length === 2,
        writes_enabled: writesEnabled,
      })
    })
  )
  router.post(
    '/setup',
    wrap(async (_req, res) =>
      res.json(
        await mutations.exclusive(async () => {
          // Open the lazy production pool before acquiring its SSH lease.
          await db.query('SELECT 1')
          return ops.withLease({ backup: true }, () => setup(db))
        })
      )
    )
  )
  router.post(
    '/maintenance/:action',
    wrap(async (req, res) => {
      assert(
        ['start', 'end'].includes(req.params.action),
        'Invalid maintenance action'
      )
      fields(req.body, [])
      res.json(
        await mutations.exclusive(() =>
          ops.maintenance(req.params.action === 'start')
        )
      )
    })
  )
  router.get(
    '/receipts/:id',
    wrap(async (req, res) => {
      assert(/^[a-f0-9-]{36}$/.test(req.params.id), 'Invalid receipt ID')
      const [[row]] = await db.query(
        'SELECT operation,result,created_at FROM gm_operations WHERE request_id=?',
        [req.params.id]
      )
      res.json(
        row
          ? { found: true, ...row, result: JSON.parse(row.result) }
          : { found: false }
      )
    })
  )
  router.get(
    '/receipts',
    wrap(async (_req, res) => {
      const [rows] = await db.query(
        'SELECT request_id,operation,created_at,backup_name FROM gm_operations ORDER BY created_at DESC LIMIT 50'
      )
      res.json(rows)
    })
  )

  router.get(
    '/accounts',
    wrap(async (_req, res) => {
      const [rows] = await db.query(
        'SELECT id,account_name,source_loginserver,last_login_date,created_at FROM login_accounts ORDER BY account_name LIMIT 1000'
      )
      res.json(rows)
    })
  )
  router.patch(
    '/accounts/:id/password',
    wrap(async (req, res) => {
      fields(req.body, ['new_password', 'account_name', 'source_loginserver'])
      const password = req.body.new_password
      assert(
        typeof password === 'string' && /^[\x21-\x7e]{1,28}$/.test(password),
        'Use 1â€“28 printable ASCII characters without spaces'
      )
      const hash = await ops.hashPassword(password)
      const result = await mutations.mutate(
        req,
        { offline: false, backup: true, tables: ['login_accounts'] },
        async (conn) => {
          const row = await account(conn, req.params.id, req.body)
          const [updated] = await conn.query(
            'UPDATE login_accounts SET account_password=? WHERE id=? AND source_loginserver=?',
            [hash, row.id, row.source_loginserver]
          )
          assert(
            updated.affectedRows === 1,
            'Expected exactly one account',
            409
          )
          const [[saved]] = await conn.query(
            'SELECT account_password FROM login_accounts WHERE id=? AND source_loginserver=?',
            [row.id, row.source_loginserver]
          )
          assert(
            saved.account_password === hash,
            'Password verification failed',
            409
          )
          return {
            success: true,
            account: row.account_name,
            message: 'Password reset and verified.',
          }
        }
      )
      res.json(result)
    })
  )
  router.delete(
    '/accounts/:id',
    change(
      offline(['login_accounts', 'account', 'character_data']),
      async (conn, req) => {
        fields(req.body, ['account_name', 'source_loginserver'])
        const row = await account(conn, req.params.id, req.body)
        const [owned] = await conn.query(
          'SELECT cd.id FROM character_data cd JOIN account a ON a.id=cd.account_id WHERE a.lsaccount_id=? AND a.ls_id=? LIMIT 1 FOR UPDATE',
          [row.id, row.source_loginserver]
        )
        assert(
          !owned.length,
          'This account owns characters, including archived characters. Reassign or remove them through a reviewed recovery procedure first.',
          409
        )
        await conn.query(
          'DELETE FROM account WHERE lsaccount_id=? AND ls_id=?',
          [row.id, row.source_loginserver]
        )
        const [removed] = await conn.query(
          'DELETE FROM login_accounts WHERE id=? AND source_loginserver=?',
          [row.id, row.source_loginserver]
        )
        assert(removed.affectedRows === 1, 'Expected exactly one account', 409)
        return { success: true, deleted: row.account_name }
      }
    )
  )
  router.get(
    '/access',
    wrap(async (_req, res) => res.json(await ops.access('access_list')))
  )
  router.post(
    '/access/initialize',
    wrap(async (req, res) => {
      fields(req.body, [])
      res.json(await mutations.exclusive(() => ops.access('access_initialize')))
    })
  )
  router.post(
    '/access',
    wrap(async (req, res) => {
      fields(req.body, ['player'])
      assert(typeof req.body.player === 'string', 'Player name is required')
      const player = req.body.player.trim().toLowerCase().replace(/\s+/g, '-')
      assert(
        /^[a-z0-9][a-z0-9_-]{0,63}$/.test(player),
        'Use letters, numbers, spaces, underscores or hyphens, up to 64 characters'
      )
      res.json(
        await mutations.exclusive(() => ops.access('access_issue', { player }))
      )
    })
  )
  router.delete(
    '/access/:id',
    wrap(async (req, res) => {
      assert(
        /^[a-f0-9]{16,64}$/.test(req.params.id),
        'Invalid access credential ID'
      )
      res.json(
        await mutations.exclusive(() =>
          ops.access('access_revoke', { credential_id: req.params.id })
        )
      )
    })
  )

  router.get(
    '/characters',
    wrap(async (_req, res) => {
      const [rows] =
        await db.query(`SELECT cd.id,cd.name,cd.level,cd.class,cd.race,cd.zone_id,cd.aa_points,cd.aa_points_spent,cd.exp,
      cd.str,cd.sta,cd.agi,cd.dex,cd.wis,cd.int,cd.cha,cd.cur_hp,cd.mana,
      cc.platinum,cc.gold,cc.silver,cc.copper,cc.platinum_bank,cc.gold_bank
      FROM character_data cd LEFT JOIN character_currency cc ON cc.id=cd.id WHERE cd.deleted_at IS NULL ORDER BY cd.name LIMIT 1000`)
      res.json(rows)
    })
  )
  router.get(
    '/zones',
    wrap(async (_req, res) => {
      const [rows] = await db.query(
        "SELECT zoneidnumber AS id,short_name,long_name,safe_x,safe_y,safe_z FROM zone WHERE version=0 AND long_name<>'' ORDER BY long_name LIMIT 2000"
      )
      res.json(rows)
    })
  )
  router.post(
    '/character/:id/boost',
    change(offline(['character_data']), async (conn, req) => {
      fields(req.body, ['level'])
      const requested = integer(req.body.level, 1, 125, 'Level')
      const row = await character(conn, req.params.id)
      const set = await activeRuleset(conn)
      const rules = await levelRules(conn, set)
      const next = boostedState(row, requested, rules)
      await validateLevelAcrossZones(conn, row, next, rules, set)
      await conn.query(
        'UPDATE character_data SET level=?,level2=?,exp=?,points=? WHERE id=?',
        [next.level, next.level2, next.exp, next.points, row.id]
      )
      return {
        success: true,
        character: row.name,
        ...next,
        maxLevel: rules.maxLevel,
        capped: next.level < requested,
      }
    })
  )
  router.post(
    '/character/:id/currency',
    change(
      offline(['character_data', 'character_currency']),
      async (conn, req) => {
        fields(req.body, ['platinum'])
        const amount = integer(req.body.platinum, 1, 1000000, 'Platinum')
        const row = await character(conn, req.params.id)
        const [[currency]] = await conn.query(
          'SELECT platinum FROM character_currency WHERE id=? FOR UPDATE',
          [row.id]
        )
        assert(
          Number(currency?.platinum ?? 0) + amount <= 2147483647,
          'Platinum would overflow the client limit'
        )
        await conn.query(
          'INSERT INTO character_currency(id,platinum) VALUES (?,?) ON DUPLICATE KEY UPDATE platinum=platinum+VALUES(platinum)',
          [row.id, amount]
        )
        return {
          success: true,
          character: row.name,
          platinum: Number(currency?.platinum ?? 0) + amount,
        }
      }
    )
  )
  router.post(
    '/character/:id/aa',
    change(offline(['character_data']), async (conn, req) => {
      fields(req.body, ['points'])
      const points = integer(req.body.points, 1, 100000, 'AA points')
      const row = await character(conn, req.params.id)
      assert(
        Number(row.aa_points) + points <= 2147483647,
        'AA points would overflow'
      )
      await conn.query(
        'UPDATE character_data SET aa_points=aa_points+? WHERE id=?',
        [points, row.id]
      )
      return {
        success: true,
        character: row.name,
        aa_points: Number(row.aa_points) + points,
      }
    })
  )
  router.post(
    '/character/:id/teleport',
    change(offline(['character_data']), async (conn, req) => {
      fields(req.body, ['zone_id', 'x', 'y', 'z'])
      const zone = id(req.body.zone_id)
      const [[valid]] = await conn.query(
        'SELECT zoneidnumber FROM zone WHERE zoneidnumber=? AND version=0',
        [zone]
      )
      assert(valid, 'Unknown base zone')
      for (const axis of ['x', 'y', 'z'])
        assert(
          typeof req.body[axis] === 'number' &&
            Number.isFinite(req.body[axis]) &&
            Math.abs(req.body[axis]) <= 1000000,
          'Invalid teleport coordinates'
        )
      const row = await character(conn, req.params.id)
      await conn.query(
        'UPDATE character_data SET zone_id=?,zone_instance=0,x=?,y=?,z=?,heading=0 WHERE id=?',
        [zone, req.body.x, req.body.y, req.body.z, row.id]
      )
      return { success: true, character: row.name, zone_id: zone }
    })
  )
  router.post(
    '/character/:id/maxskills',
    change(
      offline(['character_data', 'character_skills', 'character_multiclass']),
      async (conn, req) => {
        fields(req.body ?? {}, [])
        const row = await character(conn, req.params.id)
        const [[multi]] = await conn.query(
          'SELECT class2,class3 FROM character_multiclass WHERE character_id=?',
          [row.id]
        )
        const classes = [
          ...new Set(
            [row.class, multi?.class2, multi?.class3]
              .map(Number)
              .filter((c) => c >= 1 && c <= 16)
          ),
        ]
        const [caps] = await conn.query(
          'SELECT skill_id,MAX(cap) AS cap FROM skill_caps WHERE class_id IN (?) AND level<=? GROUP BY skill_id',
          [classes, row.level]
        )
        // Specialization, tradeskills and research have additional AA/choice gates.
        // Keep them untouched rather than grant illegal secondary specializations.
        const choiceSkills = new Set([
          43, 44, 45, 46, 47, 56, 57, 58, 59, 60, 61, 63, 64, 65, 68, 69,
        ])
        let updated = 0
        for (const skill of caps) {
          if (choiceSkills.has(Number(skill.skill_id))) continue
          await conn.query(
            'INSERT INTO character_skills(id,skill_id,value) VALUES (?,?,?) ON DUPLICATE KEY UPDATE value=GREATEST(value,VALUES(value))',
            [row.id, skill.skill_id, skill.cap]
          )
          updated++
        }
        return {
          success: true,
          character: row.name,
          updated,
          note: 'Held-class combat skills raised. Specializations and tradeskills preserved.',
        }
      }
    )
  )

  router.get('/progression/bosses', (_req, res) => res.json(PROGRESSION_BOSSES))
  router.get(
    '/character/:id/progression',
    wrap(async (req, res) => {
      const [rows] = await db.query(
        'SELECT boss_key FROM gm_progression_kills WHERE character_id=?',
        [id(req.params.id)]
      )
      res.json({ kills: rows.map((r) => r.boss_key) })
    })
  )
  const progression = change(
    {
      offline: false,
      backup: true,
      tables: ['character_data', 'gm_progression_kills'],
    },
    async (conn, req) => {
      const single = req.params.bossKey
      fields(req.body ?? {}, single ? [] : ['keys', 'killed'])
      const keys = single ? [single] : req.body.keys
      const killed = single ? req.method === 'POST' : req.body.killed
      assert(
        Array.isArray(keys) &&
          keys.length >= 1 &&
          keys.length <= 100 &&
          keys.every((k) => BOSSES.has(k)) &&
          typeof killed === 'boolean',
        'Invalid progression selection'
      )
      const row = await character(conn, req.params.id)
      for (const key of new Set(keys)) {
        if (killed)
          await conn.query(
            'INSERT IGNORE INTO gm_progression_kills(character_id,boss_key) VALUES (?,?)',
            [row.id, key]
          )
        else
          await conn.query(
            'DELETE FROM gm_progression_kills WHERE character_id=? AND boss_key=?',
            [row.id, key]
          )
      }
      return { success: true, character: row.name, updated: keys.length }
    }
  )
  router.patch('/character/:id/progression', progression)
  router.post('/character/:id/progression/:bossKey', progression)
  router.delete('/character/:id/progression/:bossKey', progression)

  router.get(
    '/rules',
    wrap(async (_req, res) => {
      const set = await activeRuleset(db)
      const [rows] = await db.query(
        'SELECT ruleset_id,rule_name,rule_value,notes FROM rule_values WHERE ruleset_id=? AND rule_name IN (?) ORDER BY rule_name',
        [set, Object.keys(RULES)]
      )
      res.json(rows)
    })
  )
  const updateRules = change(offline(['rule_values']), async (conn, req) => {
    fields(req.body, req.params.name ? ['value'] : ['rules'])
    const values = req.params.name
      ? { [req.params.name]: req.body.value }
      : req.body.rules
    assert(
      values &&
        typeof values === 'object' &&
        !Array.isArray(values) &&
        Object.keys(values).length > 0,
      'Select at least one rule'
    )
    const set = await activeRuleset(conn)
    for (const [name, raw] of Object.entries(values)) {
      assert(Object.hasOwn(RULES, name), 'This rule is not editable here')
      const [min, max, whole] = RULES[name]
      assert(
        (typeof raw === 'string' || typeof raw === 'number') &&
          String(raw).trim() !== '',
        'Invalid rule value'
      )
      const value = Number(raw)
      assert(
        Number.isFinite(value) &&
          value >= min &&
          value <= max &&
          (!whole || Number.isInteger(value)),
        `Invalid value for ${name}`
      )
      const [result] = await conn.query(
        'UPDATE rule_values SET rule_value=? WHERE ruleset_id=? AND rule_name=?',
        [String(value), set, name]
      )
      assert(
        result.affectedRows === 1,
        `Rule ${name} is not present in the active ruleset`,
        409
      )
    }
    return {
      success: true,
      message: 'Rules saved. Resume the game to load them.',
      ruleset_id: set,
    }
  })
  router.patch('/rules', updateRules)
  router.patch('/rules/:name', updateRules)
  router.get(
    '/motd',
    wrap(async (_req, res) => {
      const [[row]] = await db.query(
        "SELECT value FROM variables WHERE varname='MOTD'"
      )
      res.json({ motd: row?.value ?? '' })
    })
  )
  router.patch(
    '/motd',
    change(offline(['variables']), async (conn, req) => {
      fields(req.body, ['motd'])
      assert(
        typeof req.body.motd === 'string' &&
          req.body.motd.length <= 500 &&
          !/[\x00-\x1f]/.test(req.body.motd),
        'MOTD must be a single line up to 500 characters'
      )
      const [result] = await conn.query(
        "UPDATE variables SET value=? WHERE varname='MOTD'",
        [req.body.motd]
      )
      assert(result.affectedRows === 1, 'MOTD variable is missing', 409)
      return { success: true, motd: req.body.motd }
    })
  )
  router.get(
    '/npc-scale/:zone',
    wrap(async (_req, res) => {
      const [rows] = await db.query(
        "SELECT type,level,hp,ac,accuracy,slow_mitigation,attack FROM npc_scale_global_base WHERE type IN ('all','named') ORDER BY type,level LIMIT 200"
      )
      res.json({ scope: 'global', rows })
    })
  )
  if (extraRoutes)
    extraRoutes(router, { db, ops, environment, mutations, change, offline })
  return router
}
module.exports = { createRouter, activeRuleset, RULES, wrap }
