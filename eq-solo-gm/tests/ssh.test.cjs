const test = require('node:test')
const assert = require('node:assert/strict')
const { EventEmitter } = require('node:events')
const { PassThrough } = require('node:stream')
const { createProductionSSH } = require('../api/lib/production-ssh.cjs')

function fakeChild() {
  const child = new EventEmitter()
  child.stdin = new PassThrough()
  child.stdout = new PassThrough()
  child.stderr = new PassThrough()
  child.exitCode = null
  child.killed = false
  child.kill = () => {
    child.killed = true
    child.exitCode = 1
    child.emit('close', 1)
  }
  return child
}
test('SSH lease loss aborts the protected operation and invalidates its commit check', async () => {
  const child = fakeChild()
  const ssh = createProductionSSH(() => child)
  const result = ssh.withLease(
    { offline: true, backup: true, tables: ['character_data'] },
    async (_state, check, signal) => {
      assert.equal(signal.aborted, false)
      queueMicrotask(() => child.kill())
      await new Promise((resolve) =>
        signal.addEventListener('abort', resolve, { once: true })
      )
      assert.throws(check, /lease lost/)
      return 'aborted'
    }
  )
  child.stdout.write(
    JSON.stringify({ ok: true, result: { backup: 'fixture.sql.gz' } }) + '\n'
  )
  assert.equal(await result, 'aborted')
  ssh.close()
})
test('SSH helper rejects unsupported operations and non-private database destinations', async () => {
  let launched = false
  const ssh = createProductionSSH(() => {
    launched = true
    return fakeChild()
  })
  await assert.rejects(ssh.run('arbitrary_command'), /Unsupported/)
  for (const host of [
    '127.0.0.1',
    '8.8.8.8',
    '::1',
    '172.32.0.1',
    '10.0.0.1;bad',
  ])
    assert.throws(() => ssh.stream(host, 3306), /Unexpected/)
  assert.throws(() => ssh.stream('10.1.0.1', 22), /Unexpected/)
  assert.equal(launched, false)
})
