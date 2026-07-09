/**
 * UI-only test: Start button → Simli + ElevenLabs via browser flow.
 */
import { chromium } from 'playwright'

const log = (step, msg) => console.log(`[STEP ${step}] ${msg}`)

const loginResp = await fetch('http://localhost:8000/admin/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: 'admin@ielts-mock.com', password: 'admin' }),
})
const { access_token: token } = await loginResp.json()

log(1, 'Backend login OK')

const browser = await chromium.launch({ headless: true })
const context = await browser.newContext()
await context.addCookies([
  {
    name: 'thisisjustarandomstring',
    value: JSON.stringify(token),
    domain: 'localhost',
    path: '/',
  },
])

const simliLogs = []
const page = await context.newPage()
page.on('console', (msg) => {
  const t = msg.text()
  if (t.includes('[Simli]') || t.includes('SimliClient')) simliLogs.push(t)
})

log(2, 'Open /speaking-examiner')
await page.goto('http://localhost:5173/speaking-examiner')

log(3, 'Click Start Speaking Test (triggers /start + Simli mount)')
await page.getByRole('button', { name: /Start Speaking Test/i }).click()

log(4, 'Wait 25s for Gemini + ElevenLabs + Simli connect + audio')
await page.waitForTimeout(25000)

const examinerText = await page
  .locator('.rounded-lg.border.bg-blue-50\\/50')
  .textContent()
  .catch(() => '')

log(5, `Examiner text: "${(examinerText || '').trim().slice(0, 100)}"`)
log(5, `Video visible: ${await page.locator('video').first().isVisible().catch(() => false)}`)
log(5, `Connecting spinner: ${await page.getByText('Connecting avatar').isVisible().catch(() => false)}`)
log(5, `Phase button: ${await page.getByRole('button', { name: /Examiner speaking|Tap to speak/i }).textContent().catch(() => 'n/a')}`)

log(6, 'Simli logs:')
simliLogs
  .filter((l) =>
    l.includes('[Simli]') ||
    l.includes('Connected') ||
    l.includes('START') ||
    l.includes('video_metadata'),
  )
  .slice(0, 12)
  .forEach((l) => log(6, l.slice(0, 120)))

const connected = simliLogs.some((l) => l.includes('[Simli] Connected'))
log(7, `Simli connected: ${connected}`)
log(7, `Has examiner speech text: ${Boolean(examinerText?.trim())}`)

await browser.close()
