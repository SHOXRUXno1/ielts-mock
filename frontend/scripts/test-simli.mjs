import { chromium } from 'playwright'

const logs = []

const loginResp = await fetch('http://localhost:8000/admin/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'admin@ielts-mock.com',
    password: 'admin',
  }),
})
const { access_token: token } = await loginResp.json()

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

const page = await context.newPage()

page.on('console', (msg) => {
  const text = msg.text()
  if (
    text.includes('[Simli]') ||
    text.includes('SimliClient') ||
    text.includes('livekit') ||
    text.includes('WebRTC') ||
    text.toLowerCase().includes('error') ||
    text.includes('Falling back')
  ) {
    logs.push(`[${msg.type()}] ${text}`)
  }
})

page.on('pageerror', (err) => logs.push(`[pageerror] ${err.message}`))

try {
  await page.goto('http://localhost:5173/speaking-examiner', {
    waitUntil: 'domcontentloaded',
  })

  await page.waitForTimeout(18000)

  const videoVisible = await page.locator('video').first().isVisible().catch(() => false)
  const videoCount = await page.locator('video').count()
  const lottieVisible = await page
    .locator('.lottie, canvas')
    .first()
    .isVisible()
    .catch(() => false)
  const connecting = await page.getByText('Connecting avatar').isVisible().catch(() => false)
  const failedText = await page
    .getByText(/Failed to connect|Avatar connection lost|Startup failed/i)
    .count()
  const startVisible = await page
    .getByRole('button', { name: /Start Speaking Test/i })
    .isVisible()
    .catch(() => false)

  console.log('--- PAGE STATE ---')
  console.log('video count:', videoCount, 'visible:', videoVisible)
  console.log('lottie visible:', lottieVisible)
  console.log('connecting spinner:', connecting)
  console.log('error text blocks:', failedText)
  console.log('start button visible:', startVisible)

  if (startVisible) {
    await page.getByRole('button', { name: /Start Speaking Test/i }).click()
    await page.waitForTimeout(8000)
    const examinerText = await page
      .locator('.rounded-lg.border.bg-blue-50\\/50')
      .textContent()
      .catch(() => null)
    console.log('examiner text after start:', examinerText?.slice(0, 120))
  }

  console.log('--- CONSOLE LOGS ---')
  if (logs.length === 0) console.log('(no Simli-related console logs captured)')
  else logs.forEach((l) => console.log(l))
} catch (e) {
  console.log('SCRIPT ERROR:', e.message)
} finally {
  await browser.close()
}
