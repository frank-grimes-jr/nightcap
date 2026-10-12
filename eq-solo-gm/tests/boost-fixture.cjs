const assert = require('node:assert/strict')
const { randomUUID } = require('node:crypto')

// Fixed threshold snapshots from the native float32 curve in zone/exp.cpp.
// The independent native parity test must validate the complete formula; this
// fixture verifies persisted outcomes through the real HTTP route and MariaDB.
const thresholds = new Map([
  [1, 0],
  [2, 1000],
  [10, 729000],
  [30, 24389000],
  [31, 29700000],
  [35, 43234400],
  [36, 51450000],
  [40, 71182800],
  [41, 83200000],
  [45, 110739200],
  [46, 127575000],
  [50, 164708608],
  [51, 175000000],
  [52, 198976496],
  [53, 224972800],
  [54, 253090896],
  [55, 299181600],
  [56, 349387488],
  [57, 403916800],
  [58, 462982496],
  [59, 526802400],
  [60, 616137024],
  [61, 669600000],
  [75, 1256194432],
  [100, 3007926784],
])

module.exports = async function boostRegression({ t, call, query, db, state }) {
  const row = async () =>
    (await query('SELECT level,level2,exp FROM character_data WHERE id=100'))[0]
  const rule = async (name, value, set = 1) =>
    db.query(
      'INSERT INTO rule_values(ruleset_id,rule_name,rule_value,notes) VALUES (?,?,?,?) ON DUPLICATE KEY UPDATE rule_value=VALUES(rule_value)',
      [set, name, String(value), 'boost regression fixture']
    )
  const reset = async (level = 1, exp = 0, highest = level) => {
    await db.query('DELETE FROM variables')
    await db.query('UPDATE zone SET ruleset=0')
    await db.query(
      "DELETE FROM rule_values WHERE ruleset_id=2 AND rule_name='Character:MaxLevel'"
    )
    await db.query(
      "DELETE FROM rule_values WHERE rule_name IN ('Character:MaxExpLevel','Character:UseOldRaceExpPenalties','Character:UseOldClassExpPenalties')"
    )
    await rule('Character:MaxLevel', 50)
    await db.query(
      'UPDATE character_data SET level=?,level2=?,exp=?,race=1,class=1,points=25 WHERE id=100',
      [level, highest, exp]
    )
    state.offline = true
    state.backupFails = false
  }

  await t.test(
    'boost persists native XP at curve boundaries, including unsigned XP above level 90',
    async (t) => {
      for (const [level, exp] of thresholds) {
        await t.test(
          `level ${level} persists the native XP floor`,
          async () => {
            await reset()
            await rule('Character:MaxLevel', 100)
            const result = await call('POST', '/character/100/boost', { level })
            assert.equal(result.status, 200, JSON.stringify(result.body))
            assert.deepEqual(await row(), { level, level2: level, exp })
          }
        )
      }
    }
  )

  await t.test(
    'repeat boost preserves earned XP and a historically higher level',
    async () => {
      await reset(50, 164708608 + 12345, 60)
      const before = await row()
      assert.equal(
        (await call('POST', '/character/100/boost', { level: 50 })).status,
        200
      )
      assert.deepEqual(await row(), before)
    }
  )

  await t.test(
    'same-level correction repairs an inconsistent XP floor',
    async () => {
      await reset(50, 0, 50)
      assert.equal(
        (await call('POST', '/character/100/boost', { level: 50 })).status,
        200
      )
      assert.deepEqual(await row(), { level: 50, level2: 50, exp: 164708608 })
    }
  )

  await t.test(
    'XP at the next level floor is repaired when MaxExpLevel exceeds MaxLevel',
    async () => {
      await reset(50, 175000000, 50)
      await rule('Character:MaxExpLevel', 60)
      const result = await call('POST', '/character/100/boost', { level: 50 })
      assert.equal(result.status, 200, JSON.stringify(result.body))
      assert.deepEqual(await row(), { level: 50, level2: 50, exp: 164708608 })
    }
  )

  await t.test(
    'zone rules with a different XP curve reject a globally valid boost without a receipt',
    async () => {
      await reset(10, 729123, 10)
      await db.query('UPDATE character_data SET race=9 WHERE id=100')
      await rule('Character:UseOldRaceExpPenalties', false)
      await rule('Character:UseOldRaceExpPenalties', true, 2)
      await db.query('UPDATE zone SET ruleset=2 WHERE zoneidnumber=202')
      const before = await row()
      const requestId = randomUUID()
      const result = await call(
        'POST',
        '/character/100/boost',
        { level: 50 },
        requestId
      )
      assert.equal(result.status, 409, JSON.stringify(result.body))
      assert.deepEqual(await row(), before)
      assert.equal(
        (
          await db.query(
            'SELECT COUNT(*) n FROM gm_operations WHERE request_id=?',
            [requestId]
          )
        )[0][0].n,
        0
      )
    }
  )

  await t.test(
    'zone rules with a lower XP cap reject a boost that cannot remain stable after zoning',
    async () => {
      await reset(10, 729123, 10)
      await rule('Character:MaxLevel', 40, 2)
      await db.query('UPDATE zone SET ruleset=2 WHERE zoneidnumber=202')
      const before = await row()
      const requestId = randomUUID()
      const result = await call(
        'POST',
        '/character/100/boost',
        { level: 50 },
        requestId
      )
      assert.equal(result.status, 409, JSON.stringify(result.body))
      assert.deepEqual(await row(), before)
      assert.equal(
        (
          await db.query(
            'SELECT COUNT(*) n FROM gm_operations WHERE request_id=?',
            [requestId]
          )
        )[0][0].n,
        0
      )
    }
  )

  await t.test(
    'zone rules with a compatible higher cap allow the exact global boost target',
    async () => {
      await reset(10, 729123, 10)
      await rule('Character:MaxLevel', 68, 2)
      await db.query('UPDATE zone SET ruleset=2 WHERE zoneidnumber=202')
      const result = await call('POST', '/character/100/boost', { level: 50 })
      assert.equal(result.status, 200, JSON.stringify(result.body))
      assert.deepEqual(await row(), { level: 50, level2: 50, exp: 164708608 })
    }
  )

  await t.test(
    'training points are granted only for new lifetime levels and cannot be farmed by repeated boosts',
    async () => {
      await reset(10, 729000, 20)
      const points = async () =>
        (await query('SELECT points FROM character_data WHERE id=100'))[0]
          .points
      assert.equal(
        (await call('POST', '/character/100/boost', { level: 30 })).status,
        200
      )
      assert.equal(await points(), 75)
      assert.equal(
        (await call('POST', '/character/100/boost', { level: 30 })).status,
        200
      )
      assert.equal(await points(), 75)
      assert.equal(
        (await call('POST', '/character/100/boost', { level: 10 })).status,
        200
      )
      assert.equal(
        (await call('POST', '/character/100/boost', { level: 30 })).status,
        200
      )
      assert.equal(await points(), 75)
    }
  )

  await t.test(
    'level reduction preserves highest attained level and creates a coherent XP pair',
    async () => {
      await reset(50, 164708608, 60)
      assert.equal(
        (await call('POST', '/character/100/boost', { level: 10 })).status,
        200
      )
      assert.deepEqual(await row(), { level: 10, level2: 60, exp: 729000 })
    }
  )

  await t.test(
    'active rules override default values and MaxExpLevel limits the stable boost',
    async () => {
      await reset()
      await db.query("INSERT INTO variables VALUES ('RuleSet','unused')")
      await rule('Character:MaxLevel', 50, 2)
      await rule('Character:MaxExpLevel', 40, 2)
      const result = await call('POST', '/character/100/boost', { level: 50 })
      assert.equal(result.status, 200, JSON.stringify(result.body))
      assert.equal(result.body.level, 40)
      assert.deepEqual(await row(), { level: 40, level2: 40, exp: 71182800 })
    }
  )

  await t.test(
    'a sparse active ruleset inherits the default level cap',
    async () => {
      await reset()
      await db.query(
        "DELETE FROM rule_values WHERE ruleset_id=2 AND rule_name IN ('Character:MaxLevel','Character:MaxExpLevel')"
      )
      await db.query("INSERT INTO variables VALUES ('RuleSet','unused')")
      const result = await call('POST', '/character/100/boost', { level: 60 })
      assert.equal(result.status, 200, JSON.stringify(result.body))
      assert.deepEqual(await row(), { level: 50, level2: 50, exp: 164708608 })
    }
  )

  await t.test(
    'old race and class penalties change persisted XP independently of kill XP rates',
    async () => {
      const cases = [
        {
          race: 9,
          classId: 3,
          raceEnabled: true,
          classEnabled: true,
          exp: 276710464,
        },
        {
          race: 9,
          classId: 3,
          raceEnabled: true,
          classEnabled: false,
          exp: 197650336,
        },
        {
          race: 9,
          classId: 3,
          raceEnabled: false,
          classEnabled: true,
          exp: 230592048,
        },
        {
          race: 11,
          classId: 9,
          raceEnabled: true,
          classEnabled: true,
          exp: 142390592,
        },
      ]
      for (const scenario of cases) {
        await reset()
        await rule('Character:UseOldRaceExpPenalties', scenario.raceEnabled)
        await rule('Character:UseOldClassExpPenalties', scenario.classEnabled)
        await rule('Character:ExpMultiplier', 9)
        await db.query(
          'UPDATE character_data SET race=?,class=? WHERE id=100',
          [scenario.race, scenario.classId]
        )
        const result = await call('POST', '/character/100/boost', { level: 50 })
        assert.equal(result.status, 200, JSON.stringify(result.body))
        assert.deepEqual(await row(), {
          level: 50,
          level2: 50,
          exp: scenario.exp,
        })
      }
      await rule('Character:ExpMultiplier', 1)
    }
  )

  await t.test(
    'unsafe native XP overflow is rejected without changing character state',
    async () => {
      await reset(10, 729123, 10)
      await rule('Character:MaxLevel', 125)
      const before = await row()
      const result = await call('POST', '/character/100/boost', { level: 125 })
      assert.equal(result.status, 409, JSON.stringify(result.body))
      assert.deepEqual(await row(), before)
    }
  )

  await t.test(
    'an active false penalty overrides a true default without affecting earned XP multipliers',
    async () => {
      await reset()
      await rule('Character:UseOldRaceExpPenalties', true)
      await rule('Character:UseOldClassExpPenalties', true)
      await rule('Character:UseOldRaceExpPenalties', false, 2)
      await rule('Character:UseOldClassExpPenalties', false, 2)
      await db.query("INSERT INTO variables VALUES ('RuleSet','unused')")
      await db.query('UPDATE character_data SET race=9,class=3 WHERE id=100')
      const result = await call('POST', '/character/100/boost', { level: 50 })
      assert.equal(result.status, 200, JSON.stringify(result.body))
      assert.deepEqual(await row(), { level: 50, level2: 50, exp: 164708608 })
    }
  )

  await t.test(
    'invalid target levels fail without changing the existing XP pair',
    async () => {
      await reset(10, 729123, 10)
      const before = await row()
      for (const level of [0, -1, 126, 10.5, '50', null]) {
        assert.equal(
          (await call('POST', '/character/100/boost', { level })).status,
          400
        )
        assert.deepEqual(await row(), before)
      }
    }
  )

  await t.test(
    'boost requires maintenance and a successful backup',
    async () => {
      await reset(10, 729123, 10)
      const before = await row()
      state.offline = false
      assert.equal(
        (await call('POST', '/character/100/boost', { level: 50 })).status,
        409
      )
      assert.deepEqual(await row(), before)
      state.offline = true
      state.backupFails = true
      assert.equal(
        (await call('POST', '/character/100/boost', { level: 50 })).status,
        503
      )
      assert.deepEqual(await row(), before)
      state.backupFails = false
    }
  )

  await t.test(
    'boost rolls back level, highest level and XP if the receipt cannot commit',
    async () => {
      await reset(10, 729123, 10)
      const before = await row()
      await db.query(
        "CREATE TRIGGER qa_reject_boost_receipt BEFORE INSERT ON gm_operations FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='boost rollback fixture'"
      )
      try {
        assert.equal(
          (await call('POST', '/character/100/boost', { level: 50 })).status,
          503
        )
        assert.deepEqual(await row(), before)
      } finally {
        await db.query('DROP TRIGGER qa_reject_boost_receipt')
      }
    }
  )

  await t.test(
    'a retried boost returns its receipt without erasing subsequently earned XP',
    async () => {
      await reset()
      const requestId = randomUUID()
      assert.equal(
        (await call('POST', '/character/100/boost', { level: 50 }, requestId))
          .status,
        200
      )
      await db.query('UPDATE character_data SET exp=164708731 WHERE id=100')
      assert.equal(
        (await call('POST', '/character/100/boost', { level: 50 }, requestId))
          .status,
        200
      )
      assert.deepEqual(await row(), { level: 50, level2: 50, exp: 164708731 })
    }
  )
  // Leave the shared account/skills fixture in its original post-boost state.
  await reset(50, 164708608, 50)
  await rule('Character:ExpMultiplier', 1)
}
