import { test, expect, type Page } from '@playwright/test'

async function fixture(
  page: Page,
  options: { ambiguous?: boolean; partialMaintenance?: boolean } = {}
) {
  const calls: { url: string; method: string; body: any; target?: string }[] =
    []
  await page.route('**/api/**', async (route) => {
    const req = route.request()
    const url = new URL(req.url()).pathname
    const method = req.method()
    const body = req.postDataJSON()
    if (url === '/api/session')
      return route.fulfill({ json: { token: 'a'.repeat(64) } })
    const environment = url.split('/')[2]
    const endpoint = '/' + url.split('/').slice(3).join('/')
    calls.push({
      url,
      method,
      body,
      target: req.headers()['x-nightcap-target'],
    })
    if (method !== 'GET') {
      if (options.ambiguous && endpoint.endsWith('/password'))
        return route.abort('failed')
      if (endpoint === '/access')
        return route.fulfill({
          json: { player: 'joe', code: 'nc1.fixture.code-for-ui-only' },
        })
      return route.fulfill({ json: { success: true, updated: 1 } })
    }
    let data: any = {}
    if (endpoint === '/status')
      data = {
        environment,
        game_running: true,
        maintenance: false,
        maintenance_active: !!options.partialMaintenance,
        setup_ready: true,
        writes_enabled: true,
        credential_gateway_active: true,
      }
    else if (endpoint === '/accounts')
      data = [
        {
          id: environment === 'production' ? 42 : 1,
          account_name: environment === 'production' ? 'joe' : 'localtester',
          source_loginserver: 'local',
          last_login_date: null,
        },
      ]
    else if (endpoint === '/access')
      data = {
        ready: true,
        credentials: [
          {
            id: 'a'.repeat(32),
            player: 'joe',
            created: '2026-10-10T12:00:00Z',
          },
        ],
      }
    else if (endpoint.startsWith('/receipts/'))
      data = { found: true, result: { success: true } }
    else if (endpoint === '/receipts') data = []
    else if (endpoint === '/characters')
      data = [
        {
          id: 100,
          name: 'Fixture',
          class: 1,
          race: 1,
          level: 30,
          aa_points: 0,
          aa_points_spent: 0,
          platinum: 0,
        },
      ]
    else if (endpoint === '/zones')
      data = [
        {
          id: 202,
          long_name: 'Plane of Knowledge',
          short_name: 'poknowledge',
          safe_x: 0,
          safe_y: 0,
          safe_z: 0,
        },
      ]
    else if (endpoint === '/progression/bosses')
      data = [
        {
          expansion_id: 0,
          short: 'Classic',
          bosses: [
            { key: 'fixture_boss', name: 'Fixture Boss', zone: 'Fixture Zone' },
          ],
        },
      ]
    else if (endpoint.endsWith('/progression')) data = { kills: [] }
    else if (endpoint === '/rules')
      data = [
        {
          ruleset_id: 1,
          rule_name: 'Character:ExpMultiplier',
          rule_value: '1',
          notes: 'Experience multiplier',
        },
      ]
    else if (endpoint === '/motd') data = { motd: 'Welcome to Nightcap' }
    else if (endpoint === '/client/settings')
      data = {
        AllLuclinPcModelsOff: 'TRUE',
        path: 'C:\\Nightcap\\eqclient.ini',
      }
    return route.fulfill({ json: data })
  })
  page.on('dialog', (dialog) => dialog.accept())
  return calls
}

test('production reset captures exact account identity and target', async ({
  page,
}) => {
  const calls = await fixture(page)
  await page.goto('/accounts')
  await page
    .getByLabel('Environment', { exact: true })
    .selectOption('production')
  await expect(
    page.getByRole('heading', { name: 'joe', exact: true })
  ).toBeVisible()
  await page
    .getByRole('button', { name: 'Reset password', exact: true })
    .click()
  await page
    .getByLabel('New game password', { exact: true })
    .fill('fixture-password')
  await page
    .locator('form')
    .getByRole('button', { name: 'Reset password', exact: true })
    .click()
  await expect(page.getByRole('status')).toContainText(
    'Password reset and verified for joe'
  )
  const changed = calls.find((c) => c.method === 'PATCH')!
  expect(changed.url).toBe('/api/production/accounts/42/password')
  expect(changed.target).toBe('production')
  expect(changed.body).toEqual({
    account_name: 'joe',
    source_loginserver: 'local',
    new_password: 'fixture-password',
  })
  expect(await page.evaluate(() => JSON.stringify(localStorage))).not.toContain(
    'fixture-password'
  )
  await page.screenshot({
    path: 'test-results/accounts-desktop.png',
    fullPage: true,
  })
})

test('environment switch clears account form and selection', async ({
  page,
}) => {
  await fixture(page)
  await page.goto('/accounts')
  await page
    .getByRole('button', { name: 'Reset password', exact: true })
    .click()
  await page.getByLabel('New game password').fill('do-not-carry-over')
  await page
    .getByLabel('Environment', { exact: true })
    .selectOption('production')
  await expect(page.getByLabel('New game password')).toHaveCount(0)
  await expect(
    page.getByRole('heading', { name: 'localtester', exact: true })
  ).toHaveCount(0)
})

test('ambiguous mutation survives reload and blocks new grants until inspected', async ({
  page,
}) => {
  await fixture(page, { ambiguous: true })
  await page.goto('/accounts')
  await page
    .getByLabel('Environment', { exact: true })
    .selectOption('production')
  await page
    .getByRole('button', { name: 'Reset password', exact: true })
    .click()
  await page.getByLabel('New game password').fill('fixture-password')
  await page
    .locator('form')
    .getByRole('button', { name: 'Reset password', exact: true })
    .click()
  await expect(
    page.getByText('The last action could not be confirmed.', { exact: false })
  ).toBeVisible()
  await page.reload()
  await expect(page.getByLabel('Environment', { exact: true })).toHaveValue(
    'production'
  )
  await expect(page.getByLabel('Environment', { exact: true })).toBeDisabled()
  await expect(
    page.getByRole('button', { name: 'Reset password', exact: true })
  ).toBeDisabled()
  await page.getByRole('button', { name: 'Check action receipt' }).click()
  await expect(
    page.getByText('This database action committed successfully.')
  ).toBeVisible()
  await page
    .getByRole('button', { name: 'I checked the result', exact: false })
    .click()
  await expect(page.getByLabel('Environment', { exact: true })).toBeEnabled()
})

test('partial maintenance failure retains Resume recovery action', async ({
  page,
}) => {
  await fixture(page, { partialMaintenance: true })
  await page.goto('/accounts')
  await expect(page.getByRole('button', { name: 'Resume game' })).toBeVisible()
  await expect(
    page.getByRole('button', { name: 'Complete shutdown' })
  ).toBeVisible()
})

test('access code is delivered once and cleared on environment change', async ({
  page,
}) => {
  await fixture(page)
  await page.goto('/access')
  await page
    .getByLabel('Environment', { exact: true })
    .selectOption('production')
  await page.getByLabel('Player name').fill('Joe')
  await page.getByRole('button', { name: 'Generate code', exact: true }).click()
  await expect(page.getByLabel('Generated access code')).toHaveValue(
    'nc1.fixture.code-for-ui-only'
  )
  expect(await page.evaluate(() => JSON.stringify(localStorage))).not.toContain(
    'nc1.'
  )
  await page.screenshot({
    path: 'test-results/access-desktop.png',
    fullPage: true,
  })
  await page.getByLabel('Environment', { exact: true }).selectOption('local')
  await expect(page.getByLabel('Generated access code')).toHaveCount(0)
})

test('mobile account controls fit the viewport', async ({ page }) => {
  await fixture(page)
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/accounts')
  await expect(
    page.getByRole('heading', { name: 'localtester', exact: true })
  ).toBeVisible()
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth
    )
  ).toBe(true)
  await page.screenshot({
    path: 'test-results/accounts-mobile.png',
    fullPage: true,
  })
})

test('a second tab cannot overwrite the first tab pending action', async ({
  page,
  context,
}) => {
  const other = await context.newPage()
  await fixture(page)
  const otherCalls = await fixture(other)
  await page.goto('/accounts')
  await other.goto('/accounts')
  for (const tab of [page, other]) {
    await tab
      .getByRole('button', { name: 'Reset password', exact: true })
      .click()
    await tab.getByLabel('New game password').fill('fixture-password')
  }
  let held: any
  let started!: () => void
  const entered = new Promise<void>((resolve) => {
    started = resolve
  })
  await page.route('**/api/local/accounts/1/password', async (route) => {
    held = route
    started()
  })
  await page
    .locator('form')
    .getByRole('button', { name: 'Reset password', exact: true })
    .click()
  await entered
  const firstPending = await page.evaluate(() =>
    localStorage.getItem('nightcap-gm-pending-action')
  )
  await other
    .locator('form')
    .getByRole('button', { name: 'Reset password', exact: true })
    .click()
  await expect(other.getByRole('status')).toContainText('another GM window')
  expect(otherCalls.filter((call) => call.method !== 'GET')).toHaveLength(0)
  expect(
    await other.evaluate(() =>
      localStorage.getItem('nightcap-gm-pending-action')
    )
  ).toBe(firstPending)
  await held.abort('failed')
  await expect(
    page.getByText('The last action could not be confirmed.', { exact: false })
  ).toBeVisible()
  await page.reload()
  await expect(page.getByLabel('Environment', { exact: true })).toBeDisabled()
  expect(
    await page.evaluate(() =>
      localStorage.getItem('nightcap-gm-pending-action')
    )
  ).toBe(firstPending)
  await other.close()
})
