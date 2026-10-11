import { test, expect, type Page } from '@playwright/test'

async function fixture(page: Page) {
  const state = { maintenance: true, gateway: false }
  const writes: { path: string; body: any; target?: string }[] = []
  await page.addInitScript(() => {
    window.confirm = () => false
  })
  await page.route('**/api/**', async (route) => {
    const request = route.request()
    const path = new URL(request.url()).pathname
    if (path === '/api/session')
      return route.fulfill({ json: { token: 'a'.repeat(64) } })
    if (request.method() !== 'GET') {
      writes.push({
        path,
        body: request.postDataJSON(),
        target: request.headers()['x-nightcap-target'],
      })
      if (path.endsWith('/maintenance/end')) state.maintenance = false
      return route.fulfill({
        json: { success: true, platinum: 50000, aa_points: 700 },
      })
    }
    let data: any = []
    if (path.endsWith('/status'))
      data = {
        game_running: !state.maintenance,
        maintenance: state.maintenance,
        maintenance_active: state.maintenance,
        setup_ready: true,
        writes_enabled: true,
        credential_gateway_active: state.gateway,
      }
    if (path.endsWith('/characters'))
      data = [
        {
          id: 100,
          name: 'Darthy fixture',
          level: 30,
          class: 1,
          race: 1,
          platinum: 0,
          platinum_bank: 0,
          aa_points: 0,
          aa_points_spent: 0,
        },
      ]
    if (path.endsWith('/progression')) data = { kills: [] }
    return route.fulfill({ json: data })
  })
  await page.goto('/?target=production')
  await expect(
    page.getByRole('button', { name: 'Resume game', exact: true })
  ).toBeVisible()
  return { state, writes }
}

test('resume uses an in-page confirmation when browser prompts are suppressed', async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 })
  const { writes } = await fixture(page)
  await page.getByRole('button', { name: 'Resume game', exact: true }).click()
  const dialog = page.getByRole('dialog')
  await expect(dialog).toBeVisible()
  await expect(dialog).toContainText('Resume the game')
  await expect(dialog).toContainText('OVH production')
  expect(
    await dialog.evaluate((el) => {
      const r = el.getBoundingClientRect()
      return r.left >= 0 && r.right <= innerWidth
    })
  ).toBe(true)
  await expect(
    dialog.getByRole('button', { name: 'Cancel', exact: true })
  ).toBeFocused()
  expect(writes).toHaveLength(0)
  await page.keyboard.press('Escape')
  await expect(dialog).not.toBeVisible()
  await expect(
    page.getByRole('button', { name: 'Resume game', exact: true })
  ).toBeEnabled()
  await expect(page.getByText('Action cancelled', { exact: true })).toHaveCount(
    0
  )
  expect(writes).toHaveLength(0)
  await page.getByRole('button', { name: 'Resume game', exact: true }).click()
  await dialog
    .getByRole('button', { name: 'Confirm action', exact: true })
    .click()
  await expect(page.getByText('Game running', { exact: true })).toBeVisible()
  expect(writes).toEqual([
    { path: '/api/production/maintenance/end', body: {}, target: 'production' },
  ])
})

test('platinum and AA confirmations show the character and amount and display committed totals', async ({
  page,
}) => {
  const { writes } = await fixture(page)
  await page.getByRole('button', { name: /Darthy fixture/ }).click()
  await page.getByRole('button', { name: '+10k Plat', exact: true }).click()
  const dialog = page.getByRole('dialog')
  await expect(dialog).toContainText('Darthy fixture')
  await expect(dialog).toContainText('10,000 platinum')
  await expect(page.getByLabel('Environment', { exact: true })).toBeDisabled()
  await page.screenshot({
    path: 'test-results/gm-confirmation.png',
    fullPage: true,
  })
  await dialog.getByRole('button', { name: 'Cancel', exact: true }).click()
  expect(writes).toHaveLength(0)
  await page.getByRole('button', { name: '+10k Plat', exact: true }).click()
  await dialog
    .getByRole('button', { name: 'Confirm action', exact: true })
    .click()
  await expect(page.getByText('50,000', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: '+100 AA', exact: true }).click()
  await expect(dialog).toContainText('100 AA points')
  await dialog
    .getByRole('button', { name: 'Confirm action', exact: true })
    .click()
  await expect(page.getByText('700', { exact: true })).toBeVisible()
  expect(writes).toEqual([
    {
      path: '/api/production/character/100/currency',
      body: { platinum: 10000 },
      target: 'production',
    },
    {
      path: '/api/production/character/100/aa',
      body: { points: 100 },
      target: 'production',
    },
  ])
})

test('returning to a GM window refreshes maintenance and gateway status', async ({
  page,
}) => {
  const { state, writes } = await fixture(page)
  await expect(
    page.getByText(
      'The IP-independent player gateway has not been activated yet.'
    )
  ).toBeVisible()
  state.maintenance = false
  state.gateway = true
  await page.evaluate(() => window.dispatchEvent(new Event('focus')))
  await expect(page.getByText('Game running', { exact: true })).toBeVisible()
  await expect(
    page.getByRole('button', { name: 'Start maintenance', exact: true })
  ).toBeVisible()
  await expect(
    page.getByText(
      'The IP-independent player gateway has not been activated yet.'
    )
  ).toHaveCount(0)
  expect(writes).toHaveLength(0)
})

test('an unconfirmed dialog holds the cross-tab lock and cancellation releases it', async ({
  page,
  context,
}) => {
  const { writes } = await fixture(page)
  const other = await context.newPage()
  const second = await fixture(other)
  await page.getByRole('button', { name: 'Resume game', exact: true }).click()
  await expect(page.getByRole('dialog')).toBeVisible()
  await other.getByRole('button', { name: 'Resume game', exact: true }).click()
  await expect(other.getByRole('alert')).toContainText('another GM window')
  expect(second.writes).toHaveLength(0)
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Cancel', exact: true })
    .click()
  await other.getByRole('button', { name: 'Resume game', exact: true }).click()
  await expect(other.getByRole('dialog')).toBeVisible()
  await other
    .getByRole('dialog')
    .getByRole('button', { name: 'Cancel', exact: true })
    .click()
  expect(writes).toHaveLength(0)
  expect(second.writes).toHaveLength(0)
  await other.close()
})

test('Resume refreshes again when an older status read is still in flight', async ({
  page,
}) => {
  await fixture(page)
  let held: any
  let started!: () => void
  const waiting = new Promise<void>((resolve) => {
    started = resolve
  })
  let reads = 0
  await page.route('**/api/production/status', async (route) => {
    reads++
    if (reads === 1) {
      held = route
      started()
      return
    }
    await route.fallback()
  })
  await page
    .getByRole('button', { name: 'Refresh status', exact: true })
    .click()
  await waiting
  await page.getByRole('button', { name: 'Resume game', exact: true }).click()
  const resumed = page.waitForResponse('**/api/production/maintenance/end')
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Confirm action', exact: true })
    .click()
  await resumed
  await expect(page.getByLabel('Environment', { exact: true })).toBeEnabled()
  await held.fulfill({
    json: {
      game_running: false,
      maintenance: true,
      maintenance_active: true,
      setup_ready: true,
      writes_enabled: true,
      credential_gateway_active: false,
    },
  })
  await expect(page.getByText('Game running', { exact: true })).toBeVisible()
  expect(reads).toBe(2)
})
