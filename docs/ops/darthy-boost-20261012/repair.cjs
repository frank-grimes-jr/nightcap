// One-time incident recovery. Default is read-only; --apply needs maintenance.
const path = require('node:path')
const root = path.resolve(__dirname, '../../..')
const lib = (name) => require(path.join(root, 'eq-solo-gm/api/lib', name))
const { assert, mutationService } = lib('mutations.cjs')
const { levelRules, boostedState, validateLevelAcrossZones } = lib(
  'character-level.cjs'
)
const expected = {
  id: 24,
  name: 'Darthy',
  level: 10,
  level2: 50,
  exp: 883418,
  points: 25,
  race: 12,
  class: 11,
}
const requestId = 'e7d73a80-1c6f-4f97-8b8b-f34a7675f41f'

async function repair(conn) {
  const [[before]] = await conn.query(
    'SELECT * FROM character_data WHERE id=24 AND deleted_at IS NULL FOR UPDATE'
  )
  assert(
    before && Object.entries(expected).every(([k, v]) => before[k] === v),
    'Darthy changed since capture; inspect and re-plan instead of overwriting progress.',
    409
  )
  const [[active]] = await conn.query(
    "SELECT ruleset_id FROM rule_sets WHERE name=COALESCE((SELECT value FROM variables WHERE varname='RuleSet' LIMIT 1),'default')"
  )
  assert(active, 'Active ruleset missing', 409)
  const rules = await levelRules(conn, Number(active.ruleset_id))
  const next = boostedState(before, 50, rules)
  assert(
    next.level === 50 && next.exp === 164708608 && next.points === 25,
    'Live boost policy differs from the verified repair',
    409
  )
  // Original boost receipt/backup proves level2=5, points=25 and exp was reset.
  // Preserve the 883418 XP earned afterward; credit omitted 45 * 5 training points.
  next.exp += before.exp
  next.points += 225
  await validateLevelAcrossZones(
    conn,
    before,
    next,
    rules,
    Number(active.ruleset_id)
  )
  await conn.query(
    'UPDATE character_data SET level=?,level2=?,exp=?,points=? WHERE id=?',
    [next.level, next.level2, next.exp, next.points, before.id]
  )
  const [[after]] = await conn.query('SELECT * FROM character_data WHERE id=24')
  assert(
    Object.keys(before).every(
      (key) =>
        JSON.stringify(after[key]) ===
        JSON.stringify(key in next ? next[key] : before[key])
    ),
    'Unexpected character change; rolling back',
    409
  )
  return {
    success: true,
    character: 'Darthy',
    before: expected,
    after: next,
    preserved_earned_xp: before.exp,
    restored_training_points: 225,
  }
}

async function main() {
  const mode = process.argv[2] || '--inspect'
  assert(['--inspect', '--apply'].includes(mode), 'Use --inspect or --apply')
  if (mode === '--apply') {
    require('node:child_process').execFileSync(
      'git',
      ['merge-base', '--is-ancestor', 'HEAD', 'origin/main'],
      { cwd: root, windowsHide: true, stdio: 'pipe' }
    )
  }
  if (mode === '--apply') {
    const runGit = (args) =>
      require('node:child_process').execFileSync('git', args, {
        cwd: root,
        windowsHide: true,
        encoding: 'utf8',
        stdio: ['ignore', 'pipe', 'pipe'],
      })
    const sources = [
      'docs/ops/darthy-boost-20261012/repair.cjs',
      ...require('node:fs')
        .readdirSync(path.join(root, 'eq-solo-gm/api/lib'))
        .filter((name) => /\.(cjs|py)$/.test(name))
        .map((name) => 'eq-solo-gm/api/lib/' + name),
    ]
    runGit(['ls-files', '--error-unmatch', '--', ...sources])
    assert(
      runGit([
        'status',
        '--porcelain',
        '--untracked-files=all',
        '--',
        ...sources,
      ]).trim() === '',
      'Repair and executed API sources must be tracked and clean on the approved main release.',
      409
    )
  }
  const { createDatabases } = lib('database.cjs')
  const { createOperations } = lib('operations.cjs')
  const databases = createDatabases()
  try {
    const ops = createOperations(databases.ssh, databases).production
    if (mode === '--inspect') {
      const [rows] = await databases.production.query(
        'SELECT id,name,level,level2,exp,points,race,class FROM character_data WHERE id=24'
      )
      console.log(
        JSON.stringify(
          { state: await ops.status(), character: rows, expected },
          null,
          2
        )
      )
      return
    }
    const key = await lib('owner-state.cjs').fingerprintKey()
    const req = {
      method: 'POST',
      path: '/repair/character/24/boost-20261012',
      body: {
        expected,
        target: 50,
        earned_xp: 883418,
        missing_training_points: 225,
      },
      get: (name) => (name === 'x-request-id' ? requestId : undefined),
    }
    const result = await mutationService(
      databases.production,
      ops,
      'production',
      key
    ).mutate(
      req,
      { offline: true, backup: true, tables: ['character_data'] },
      repair
    )
    console.log(JSON.stringify(result, null, 2))
  } finally {
    await databases.close()
  }
}
if (require.main === module)
  main().catch((error) => {
    console.error(error.message)
    process.exitCode = 1
  })
module.exports = { repair, expected }
