const { assert, integer } = require('./mutations.cjs')

// Match Client::GetEXPForLevel, including each float32 rounding and uint32 cast.
// XP multipliers affect awards, not these cumulative thresholds.
function experienceForLevel(level, profile = {}) {
  integer(level, 1, 126, 'Level threshold')
  const bands = [
    [31, 1],
    [36, 1.1],
    [41, 1.2],
    [46, 1.3],
    [52, 1.4],
    [53, 1.5],
    [54, 1.6],
    [55, 1.7],
    [56, 1.9],
    [57, 2.1],
    [58, 2.3],
    [59, 2.5],
    [60, 2.7],
    [61, 3],
    [127, 3.1],
  ]
  const uint32 = (value) => {
    assert(
      Number.isFinite(value) && value >= 0 && value < 0xffffffff,
      'This level exceeds the native XP range for this character.',
      409
    )
    return Math.trunc(value)
  }
  let exp = uint32(
    Math.fround(
      Math.fround((level - 1) ** 3) *
        Math.fround(
          Math.fround(bands.find(([limit]) => level < limit)[1]) * 1000
        )
    )
  )
  if (profile.useOldRaceExpPenalties) {
    const factor =
      { 9: 1.2, 128: 1.2, 10: 1.15, 2: 1.05, 11: 0.95 }[profile.race] ?? 1
    exp = uint32(Math.fround(Math.fround(exp) * Math.fround(factor)))
  }
  if (profile.useOldClassExpPenalties) {
    const factor =
      {
        3: 1.4,
        5: 1.4,
        4: 1.4,
        8: 1.4,
        7: 1.2,
        12: 1.1,
        14: 1.1,
        13: 1.1,
        11: 1.1,
        9: 0.91,
        1: 0.9,
      }[profile.class] ?? 1
    exp = uint32(Math.fround(Math.fround(exp) * Math.fround(factor)))
  }
  return exp
}

async function levelRules(db, activeSet) {
  const names = [
    'MaxLevel',
    'MaxExpLevel',
    'UseOldRaceExpPenalties',
    'UseOldClassExpPenalties',
    'PerCharacterQglobalMaxLevel',
    'PerCharacterBucketMaxLevel',
  ].map((name) => 'Character:' + name)
  const [rows] = await db.query(
    `SELECT v.ruleset_id,v.rule_name,v.rule_value FROM rule_values v
     JOIN rule_sets s ON s.ruleset_id=v.ruleset_id
     WHERE (s.name='default' OR v.ruleset_id=?) AND v.rule_name IN (?)
     ORDER BY (v.ruleset_id=?)`,
    [activeSet, names, activeSet]
  )
  const values = { 'Character:MaxLevel': '65', 'Character:MaxExpLevel': '0' }
  for (const row of rows) values[row.rule_name] = row.rule_value
  const flag = (name) => {
    const value = String(values['Character:' + name] ?? 'false').toLowerCase()
    assert(
      ['true', 'false', '1', '0'].includes(value),
      'Invalid XP rule: ' + name,
      409
    )
    return value === 'true' || value === '1'
  }
  assert(
    !flag('PerCharacterQglobalMaxLevel') && !flag('PerCharacterBucketMaxLevel'),
    'Per-character level limits require a native in-game level change.',
    409
  )
  const maxLevel = integer(
    Number(values['Character:MaxLevel']),
    1,
    125,
    'Active level cap'
  )
  const maxExpLevel = integer(
    Number(values['Character:MaxExpLevel']),
    0,
    125,
    'Active XP level cap'
  )
  return {
    maxLevel: Math.min(maxLevel, maxExpLevel || maxLevel),
    nativeMaxLevel: maxExpLevel || maxLevel,
    useOldRaceExpPenalties: flag('UseOldRaceExpPenalties'),
    useOldClassExpPenalties: flag('UseOldClassExpPenalties'),
  }
}

function boostedState(row, requested, rules) {
  const level = Math.min(requested, rules.maxLevel)
  const profile = { ...rules, race: Number(row.race), class: Number(row.class) }
  integer(profile.race, 1, 65535, 'Character race')
  integer(profile.class, 1, 16, 'Character class')
  const floor = experienceForLevel(level, profile)
  const ceiling = experienceForLevel(level + 1, profile)
  assert(
    ceiling > floor,
    'The native XP interval is invalid for this level.',
    409
  )
  const savedXP = Number(row.exp)
  // At the cap, native SetEXP permits a completely full XP bar (ceiling inclusive).
  const preserve =
    Number(row.level) === level &&
    savedXP >= floor &&
    (savedXP < ceiling ||
      (level === rules.nativeMaxLevel && savedXP === ceiling))
  const oldHigh = integer(Number(row.level2), 0, 255, 'Highest attained level')
  const points =
    integer(Number(row.points), 0, 0xffffffff, 'Training points') +
    (level > oldHigh ? (oldHigh === 0 ? 5 : 5 * (level - oldHigh)) : 0)
  assert(points <= 0xffffffff, 'Training points would overflow', 409)
  return {
    level,
    level2: Math.max(oldHigh, level),
    exp: preserve ? savedXP : floor,
    points,
  }
}

// Zone boot may replace the world ruleset. Refuse a boost that would be undone
// when this character enters any configured zone; do not silently rewrite rules.
async function validateLevelAcrossZones(db, row, next, rules, activeSet) {
  const [sets] = await db.query(
    'SELECT DISTINCT s.ruleset_id FROM zone z JOIN rule_sets s ON s.ruleset_id=z.ruleset'
  )
  const profile = { ...rules, race: Number(row.race), class: Number(row.class) }
  const floor = experienceForLevel(next.level, profile)
  const ceiling = experienceForLevel(next.level + 1, profile)
  for (const set of sets) {
    if (Number(set.ruleset_id) === activeSet) continue
    const zoneRules = await levelRules(db, Number(set.ruleset_id))
    const zoneProfile = { ...profile, ...zoneRules }
    assert(
      next.level <= zoneRules.nativeMaxLevel &&
        experienceForLevel(next.level, zoneProfile) === floor &&
        experienceForLevel(next.level + 1, zoneProfile) === ceiling &&
        (next.exp < ceiling || next.level === zoneRules.nativeMaxLevel),
      `Zone ruleset ${set.ruleset_id} has incompatible level/XP rules; reconcile them before boosting.`,
      409
    )
  }
}

module.exports = {
  experienceForLevel,
  levelRules,
  boostedState,
  validateLevelAcrossZones,
}
