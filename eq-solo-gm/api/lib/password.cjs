const sodium = require('libsodium-wrappers-sumo')
const { assert } = require('./mutations.cjs')
async function hashPassword(password) {
  assert(
    typeof password === 'string' && /^[\x21-\x7e]{1,28}$/.test(password),
    'Use 1–28 printable ASCII characters without spaces'
  )
  await sodium.ready
  const hash = sodium.crypto_pwhash_scryptsalsa208sha256_str(
    password,
    524288,
    16777216
  )
  assert(
    hash.startsWith('$7$') &&
      sodium.crypto_pwhash_scryptsalsa208sha256_str_verify(hash, password),
    'Password hashing failed',
    503
  )
  return hash
}
module.exports = { hashPassword }
