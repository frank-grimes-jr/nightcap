const { execFile, spawn } = require('node:child_process')
const { promisify } = require('node:util')
const fs = require('node:fs/promises')
const path = require('node:path')
const { createWriteStream } = require('node:fs')
const { pipeline } = require('node:stream/promises')
const { createGzip } = require('node:zlib')
const runFile = promisify(execFile)
const ROOT = path.resolve(__dirname, '../../..')
const { directory } = require('./owner-state.cjs')
const { UserError } = require('./mutations.cjs')

async function docker(args, timeout = 15000) {
  try {
    return (
      await runFile('docker', args, {
        windowsHide: true,
        timeout,
        maxBuffer: 1024 * 1024,
      })
    ).stdout
  } catch {
    throw new Error(
      'Local Docker operation failed. Check that the local stack is available.'
    )
  }
}

function createOperations(ssh, databases) {
  const marker = path.join(directory, 'local-maintenance.json')
  async function hasMarker() {
    try {
      await fs.access(marker)
      return true
    } catch {
      return false
    }
  }
  async function offline() {
    if (!(await local.status()).maintenance)
      throw new UserError(
        'Start local maintenance before editing game data.',
        409
      )
  }
  const local = {
    async status() {
      const rows = JSON.parse(
        await docker(['inspect', 'akk-stack-eqemu-server-1'])
      )
      const active = await hasMarker()
      return {
        environment: 'local',
        label: 'Local development',
        game_running: rows[0].State.Running,
        maintenance_active: active,
        maintenance: active && !rows[0].State.Running,
        access_registry_ready: false,
        credential_gateway_active: false,
      }
    },
    async maintenance(start) {
      if (start) {
        if (!(await hasMarker())) {
          if (!(await local.status()).game_running)
            throw new UserError(
              'The local game is already stopped outside GM maintenance.',
              409
            )
          await fs.mkdir(directory, { recursive: true, mode: 0o700 })
          await fs.writeFile(
            marker,
            JSON.stringify({ started: new Date().toISOString() }),
            { flag: 'wx', mode: 0o600 }
          )
        }
      } else {
        if (!(await hasMarker()))
          throw new UserError('No local GM maintenance session to resume', 409)
        const [[free]] = await databases.local.query(
          "SELECT IS_FREE_LOCK('nightcap_gm_writes') AS available"
        )
        if (Number(free.available) !== 1)
          throw new UserError('A GM database action is still in progress', 409)
      }
      await docker(
        [
          start ? 'stop' : 'start',
          ...(start ? ['-t', '100'] : []),
          'akk-stack-eqemu-server-1',
        ],
        120000
      )
      if (!start) await fs.unlink(marker)
      return local.status()
    },
    async withLease(options, action) {
      if (options.offline) await offline()
      let backup = null
      if (options.backup) {
        const backupDirectory = path.join(directory, 'backups')
        await fs.mkdir(backupDirectory, { recursive: true, mode: 0o700 })
        backup = new Date().toISOString().replace(/[:.]/g, '-') + '.sql.gz'
        const child = spawn(
          'docker',
          [
            'exec',
            'akk-stack-mariadb-1',
            'mariadb-dump',
            '-ueqemu',
            '-peqemu',
            '--single-transaction',
            '--quick',
            'peq',
            ...(options.tables || []),
          ],
          { windowsHide: true, stdio: ['ignore', 'pipe', 'ignore'] }
        )
        const timer = setTimeout(() => child.kill(), 180000)
        const finished = new Promise((resolve, reject) => {
          child.on('error', reject)
          child.on('close', (code) =>
            code === 0
              ? resolve()
              : reject(new Error('Backup failed; no GM change was made'))
          )
        })
        try {
          await Promise.all([
            finished,
            pipeline(
              child.stdout,
              createGzip(),
              createWriteStream(
                path.join(backupDirectory, backup + '.partial'),
                {
                  flags: 'wx',
                  mode: 0o600,
                }
              )
            ),
          ])
        } finally {
          clearTimeout(timer)
        }
        await fs.rename(
          path.join(backupDirectory, backup + '.partial'),
          path.join(backupDirectory, backup)
        )
      }
      if (options.offline) await offline()
      return action({ backup }, () => (options.offline ? offline() : undefined))
    },
    async hashPassword(password) {
      const config = JSON.parse(
        await fs.readFile(
          path.join(
            process.env.NIGHTCAP_LOCAL_STACK || 'E:\\EQ_Local_Dev\\akk-stack',
            'server/login.json'
          ),
          'utf8'
        )
      )
      if ((config.security?.mode ?? 14) !== 14)
        throw new UserError(
          'Local login hash mode changed; review it before resetting passwords',
          409
        )
      return require('./password.cjs').hashPassword(password)
    },
    async access(operation) {
      if (operation === 'access_list')
        return {
          ready: false,
          credentials: [],
          message: 'Player access codes belong to the production gateway.',
        }
      throw new Error('Select OVH production to manage launcher access codes.')
    },
  }
  const production = {
    status: () => ssh.run('status'),
    maintenance: (start) =>
      ssh.run(start ? 'maintenance_start' : 'maintenance_end', {}, 150000),
    withLease: (options, action) => ssh.withLease(options, action),
    async hashPassword(password) {
      await ssh.run('password_mode')
      return require('./password.cjs').hashPassword(password)
    },
    access: (operation, values) => ssh.run(operation, values),
  }
  return { local, production }
}
module.exports = { createOperations, ROOT }
