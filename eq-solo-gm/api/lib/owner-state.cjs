const fs = require('node:fs/promises')
const path = require('node:path')
const os = require('node:os')
const crypto = require('node:crypto')
const { promisify } = require('node:util')
const { execFile } = require('node:child_process')
const run = promisify(execFile)
const directory = path.join(os.homedir(), '.nightcap-gm')

async function fingerprintKey() {
  await fs.mkdir(directory, { recursive: true, mode: 0o700 })
  if (process.platform === 'win32') {
    const { stdout } = await run('whoami', ['/user', '/fo', 'csv', '/nh'], {
      windowsHide: true,
    })
    const sid = stdout.match(/S-1-5-\d+(?:-\d+)+/)?.[0]
    if (!sid) throw new Error('Cannot identify the local GM owner')
    await run(
      'icacls',
      [directory, '/inheritance:r', '/grant:r', `*${sid}:(OI)(CI)F`],
      { windowsHide: true }
    )
  } else await fs.chmod(directory, 0o700)
  const file = path.join(directory, 'receipt-key')
  try {
    await fs.writeFile(file, crypto.randomBytes(32), {
      flag: 'wx',
      mode: 0o600,
    })
  } catch (error) {
    if (error.code !== 'EEXIST') throw error
  }
  const key = await fs.readFile(file)
  if (key.length !== 32) throw new Error('Invalid private GM receipt key')
  return key
}
module.exports = { fingerprintKey, directory }
