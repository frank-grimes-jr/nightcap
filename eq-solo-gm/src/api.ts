import axios, { type AxiosRequestConfig } from 'axios'
import { reactive, onUnmounted } from 'vue'

export type Environment = 'local' | 'production'
export const owner = reactive({
  environment: (new URLSearchParams(location.search).get('target') ===
  'production'
    ? 'production'
    : 'local') as Environment,
  epoch: 0,
  busy: false,
  subject: '',
  uncertain: '',
  uncertainEnvironment: 'local' as Environment,
})
const PENDING_KEY = 'nightcap-gm-pending-action'
function readPending() {
  try {
    const pending = JSON.parse(localStorage.getItem(PENDING_KEY) || 'null')
    return pending &&
      /^[a-f0-9-]{36}$/.test(pending.id) &&
      ['local', 'production'].includes(pending.environment)
      ? pending
      : null
  } catch {
    return null
  }
}
function restorePending() {
  const pending = readPending()
  if (
    pending &&
    /^[a-f0-9-]{36}$/.test(pending.id) &&
    ['local', 'production'].includes(pending.environment)
  ) {
    owner.uncertain = pending.id
    owner.uncertainEnvironment = pending.environment
    if (owner.environment !== pending.environment) {
      owner.environment = pending.environment
      owner.epoch++
    }
  }
}
restorePending()
function clearPending(requestId: string) {
  if (readPending()?.id === requestId) localStorage.removeItem(PENDING_KEY)
  if (owner.uncertain === requestId) owner.uncertain = ''
}
export async function resolvePendingAction() {
  await navigator.locks.request(
    'nightcap-gm-mutation',
    { ifAvailable: true },
    async (lock) => {
      if (!lock)
        throw new Error(
          'An action is still running in another GM window. Wait for it to finish.'
        )
      clearPending(owner.uncertain)
    }
  )
}
export const labels = {
  local: 'Local development',
  production: 'OVH production',
}
let session: Promise<string> | undefined
async function token() {
  session ??= axios
    .get('/api/session', {
      headers: { 'X-Nightcap-Owner': '1' },
      timeout: 10000,
    })
    .then((r) => r.data.token)
    .catch((e) => {
      session = undefined
      throw e
    })
  return session
}
export function selectEnvironment(environment: Environment) {
  if (
    owner.busy ||
    owner.uncertain ||
    !['local', 'production'].includes(environment)
  )
    return
  owner.environment = environment
  owner.epoch++
  owner.subject = ''
}
function actionName(url: string, method: string) {
  if (url.includes('/maintenance/start'))
    return 'Start maintenance and disconnect all players'
  if (url.includes('/maintenance/end')) return 'Resume the game'
  if (url.includes('/password')) return 'Reset game password'
  if (url.includes('/accounts/') && method === 'DELETE') return 'Delete account'
  if (url.includes('/access/initialize'))
    return 'Initialize the player access registry'
  if (url.includes('/access'))
    return method === 'DELETE'
      ? 'Revoke this launcher access code'
      : 'Generate a launcher access code'
  if (url.includes('/setup')) return 'Set up GM history and progression tables'
  if (url.includes('/currency')) return 'Grant platinum'
  if (url.includes('/aa')) return 'Grant AA points'
  if (url.includes('/boost'))
    return 'Change character level and reset level experience'
  if (url.includes('/maxskills')) return 'Raise eligible combat skills'
  if (url.includes('/teleport')) return 'Move character'
  if (url.includes('/progression')) return 'Update progression tracking'
  if (url.includes('/vendors'))
    return 'Restore the reviewed spell vendor catalog'
  if (url.includes('/rules')) return 'Save server rules'
  if (url.includes('/motd')) return 'Change message of the day'
  return 'Save settings'
}

export function useApi() {
  const environment = owner.environment
  const epoch = owner.epoch
  let disposed = false
  const controller = new AbortController()
  onUnmounted(() => {
    disposed = true
    controller.abort()
  })
  async function perform(
    method: string,
    url: string,
    data?: unknown,
    config: AxiosRequestConfig = {}
  ) {
    if (disposed || owner.epoch !== epoch)
      throw new Error('View changed; reload this page')
    const mutation = method !== 'GET'
    const requestId = crypto.randomUUID()
    if (mutation) {
      if (owner.busy || owner.uncertain)
        throw new Error('Finish the pending action first')
      const subject =
        (data as any)?.account_name || (data as any)?.player || owner.subject
      if (
        !confirm(
          `${actionName(url, method)}${subject ? ` for ${subject}` : ''}?\n\nTarget: ${labels[environment]}`
        )
      )
        throw new Error('Action cancelled')
      owner.busy = true
    }
    try {
      const sessionToken = await token()
      if (mutation)
        localStorage.setItem(
          PENDING_KEY,
          JSON.stringify({
            id: requestId,
            environment,
            started: new Date().toISOString(),
          })
        )
      const response = await axios.request({
        ...config,
        method,
        url: url.replace(/^\/api/, `/api/${environment}`),
        data,
        signal: mutation ? undefined : controller.signal,
        timeout: mutation ? 300000 : 20000,
        headers: {
          ...config.headers,
          'X-Nightcap-Session': sessionToken,
          'X-Nightcap-Target': environment,
          'X-Request-Id': requestId,
        },
      })
      if (mutation) clearPending(requestId)
      if (disposed || owner.epoch !== epoch)
        throw new Error('View changed; reload this page')
      return response
    } catch (error: any) {
      if (mutation && (!error.response || error.response.status >= 500)) {
        owner.uncertain = requestId
        owner.uncertainEnvironment = environment
      } else if (mutation) clearPending(requestId)
      if (error.response?.data?.error) error.message = error.response.data.error
      throw error
    } finally {
      if (mutation) owner.busy = false
    }
  }
  async function request(
    method: string,
    url: string,
    data?: unknown,
    config: AxiosRequestConfig = {}
  ) {
    if (method === 'GET') return perform(method, url, data, config)
    if (!navigator.locks)
      throw new Error(
        'Open the GM tool in current Chrome or Edge to make changes.'
      )
    return navigator.locks.request(
      'nightcap-gm-mutation',
      { ifAvailable: true },
      async (lock) => {
        if (!lock)
          throw new Error(
            'An action is still running in another GM window. Wait for it to finish.'
          )
        if (readPending()) {
          restorePending()
          throw new Error(
            'Inspect the pending action before making another change.'
          )
        }
        return perform(method, url, data, config)
      }
    )
  }
  return {
    get: (url: string, config?: AxiosRequestConfig) =>
      request('GET', url, undefined, config),
    post: (url: string, data: unknown = {}, config?: AxiosRequestConfig) =>
      request('POST', url, data, config),
    patch: (url: string, data: unknown = {}, config?: AxiosRequestConfig) =>
      request('PATCH', url, data, config),
    delete: (url: string, config?: AxiosRequestConfig) =>
      request('DELETE', url, config?.data ?? {}, config),
  }
}
