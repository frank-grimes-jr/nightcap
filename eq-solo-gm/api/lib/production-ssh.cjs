const { spawn } = require('node:child_process')
const { Duplex } = require('node:stream')
const { readFileSync } = require('node:fs')
const { homedir } = require('node:os')
const path = require('node:path')
const net = require('node:net')
const { UserError } = require('./mutations.cjs')

const DESTINATION = 'ubuntu@135.148.47.202'
const SSH_OPTIONS = [
  '-T',
  '-i',
  path.join(homedir(), '.ssh', 'nightcap_ovh'),
  '-o',
  'BatchMode=yes',
  '-o',
  'StrictHostKeyChecking=yes',
  '-o',
  'ConnectTimeout=8',
  '-o',
  'ServerAliveInterval=15',
  '-o',
  'ServerAliveCountMax=2',
]
const HELPER = readFileSync(
  path.join(__dirname, 'production_helper.py'),
  'utf8'
)
const unavailable = () =>
  new UserError(
    'Production connection unavailable. Check the saved OVH SSH key and SSH agent, then reconnect.',
    503
  )

function createProductionSSH(start = spawn) {
  const children = new Set()
  function launch(args) {
    const child = start('ssh', [...SSH_OPTIONS, ...args], {
      windowsHide: true,
      shell: false,
      stdio: ['pipe', 'pipe', 'pipe'],
    })
    children.add(child)
    child.once('close', () => children.delete(child))
    return child
  }
  function run(operation, values = {}, timeout = 20000) {
    if (
      ![
        'connection',
        'status',
        'password_mode',
        'access_list',
        'access_issue',
        'access_revoke',
        'access_initialize',
        'maintenance_start',
        'maintenance_end',
      ].includes(operation)
    ) {
      return Promise.reject(new Error('Unsupported production operation'))
    }
    const input = Buffer.from(JSON.stringify({ ...values, operation }))
    if (input.length > 16384)
      return Promise.reject(new Error('Production request is too large'))
    return new Promise((resolve, reject) => {
      const child = launch([DESTINATION, 'sudo -n python3 -'])
      let output = Buffer.alloc(0)
      let failed = false
      const timer = setTimeout(
        () =>
          fail(
            new Error(
              'Production request timed out. Refresh before retrying a change.'
            )
          ),
        timeout
      )
      function fail(error) {
        if (failed) return
        failed = true
        clearTimeout(timer)
        child.kill()
        reject(error)
      }
      child.on('error', () => fail(unavailable()))
      child.stdin.on('error', () => fail(unavailable()))
      child.stderr.on('data', () => {}) // SSH/helper diagnostics can contain sensitive material.
      child.stdout.on('data', (chunk) => {
        output = Buffer.concat([output, chunk])
        if (output.length > 2 * 1024 * 1024)
          fail(new Error('Production response exceeded its limit'))
      })
      child.once('close', (code) => {
        clearTimeout(timer)
        if (failed) return
        if (code !== 0) return reject(unavailable())
        try {
          const reply = JSON.parse(output.toString('utf8'))
          if (!reply.ok)
            return reject(
              new UserError(reply.error || 'Production operation failed', 409)
            )
          resolve(reply.result)
        } catch {
          reject(new Error('Invalid production response'))
        }
      })
      const data = input.toString('base64')
      child.stdin.end(
        `import base64,json\nREQUEST=json.loads(base64.b64decode('${data}'))\n${HELPER}`
      )
    })
  }
  async function withLease(options, action) {
    const child = launch([
      DESTINATION,
      `sudo -n python3 -u -c "exec(__import__('base64').b64decode('${Buffer.from(HELPER).toString('base64')}'))"`,
    ])
    let pending = ''
    let ready = false
    let lost = false
    const controller = new AbortController()
    child.once('close', () => {
      lost = true
      controller.abort()
    })
    const timeout = setTimeout(() => child.kill(), 300000)
    child.stderr.on('data', () => {})
    const acquired = new Promise((resolve, reject) => {
      child.on('error', () => reject(unavailable()))
      child.stdin.on('error', () => reject(unavailable()))
      child.on('close', () => {
        if (!ready) reject(unavailable())
      })
      child.stdout.on('data', (chunk) => {
        pending += chunk.toString()
        if (pending.length > 65536) {
          child.kill()
          reject(new Error('Invalid maintenance lease response'))
          return
        }
        if (!ready && pending.includes('\n')) {
          try {
            const reply = JSON.parse(pending.split('\n')[0])
            if (!reply.ok) {
              reject(new UserError(reply.error, 409))
              child.kill()
              return
            }
            ready = true
            resolve(reply.result)
          } catch {
            reject(new Error('Invalid maintenance lease response'))
            child.kill()
          }
        }
      })
    })
    child.stdin.write(
      JSON.stringify({
        operation: 'lease',
        offline: !!options.offline,
        backup: !!options.backup,
        tables: options.tables ?? null,
      }) + '\n'
    )
    try {
      const state = await acquired
      return await action(
        state,
        () => {
          if (lost || child.killed)
            throw new Error(
              'Maintenance lease lost; the change was not confirmed'
            )
        },
        controller.signal
      )
    } finally {
      clearTimeout(timeout)
      child.stdin.end()
      child.kill()
    }
  }
  function stream(host, port) {
    // Only an inspected RFC1918 Docker address is accepted, never a browser target.
    const octets = String(host).split('.').map(Number)
    const privateAddress =
      octets[0] === 10 ||
      (octets[0] === 172 && octets[1] >= 16 && octets[1] <= 31) ||
      (octets[0] === 192 && octets[1] === 168)
    if (net.isIP(host) !== 4 || !privateAddress || port !== 3306)
      throw new Error('Unexpected production database address')
    const child = launch(['-W', `${host}:${port}`, DESTINATION])
    const socket = Duplex.from({
      readable: child.stdout,
      writable: child.stdin,
    })
    child.stderr.on('data', () => {})
    child.once('error', () => socket.destroy(unavailable()))
    child.once('close', (code) => {
      if (code !== 0) socket.destroy(unavailable())
    })
    socket.once('close', () => child.kill())
    return socket
  }
  return {
    run,
    stream,
    withLease,
    close: () => {
      for (const child of children) child.kill()
    },
  }
}

module.exports = { createProductionSSH }
