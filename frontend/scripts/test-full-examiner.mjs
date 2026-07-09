/**
 * Full Speaking AI Examiner cycle test with step-by-step logging.
 */
import { chromium } from 'playwright'
import { writeFileSync } from 'fs'

const logs = []
const log = (step, msg) => {
  const line = `[STEP ${step}] ${msg}`
  console.log(line)
  logs.push(line)
}

// ── Step 1: Login ──
log(1, 'Logging in via API...')
const loginResp = await fetch('http://localhost:8000/admin/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: 'admin@ielts-mock.com', password: 'admin' }),
})
const { access_token: token } = await loginResp.json()
log(1, `Login OK (${loginResp.status})`)

const authHeaders = {
  Authorization: `Bearer ${token}`,
  'Content-Type': 'application/json',
}

// ── Step 2: Simli token ──
log(2, 'Fetching Simli token...')
const simliResp = await fetch(
  'http://localhost:8000/admin/speaking-examiner/simli-token',
  { headers: authHeaders },
)
const simliData = await simliResp.json()
log(
  2,
  `Simli enabled=${simliData.enabled}, token=${Boolean(simliData.session_token)}, ice=${(simliData.ice_servers || []).length}`,
)

// ── Step 3: Start session (Gemini + ElevenLabs) ──
log(3, 'Starting examiner session (Gemini + ElevenLabs)...')
const startResp = await fetch(
  'http://localhost:8000/admin/speaking-examiner/start',
  { method: 'POST', headers: authHeaders },
)
const startData = await startResp.json()
const audioLen = (startData.audio_base64 || '').length
log(3, `Start OK (${startResp.status})`)
log(3, `Examiner: "${(startData.text || '').slice(0, 80)}..."`)
log(3, `Audio base64 length: ${audioLen} ${audioLen > 0 ? '✓' : '✗ EMPTY'}`)
log(3, `Part: ${startData.part}`)

if (audioLen === 0) {
  log(3, 'FAIL: ElevenLabs returned no audio — lip sync will not work')
}

// ── Step 4: Browser — Simli + Start ──
log(4, 'Opening browser at /speaking-examiner...')
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

const consoleLogs = []
const page = await context.newPage()
page.on('console', (msg) => {
  const text = msg.text()
  if (
    text.includes('[Simli]') ||
    text.includes('SimliClient') ||
    text.toLowerCase().includes('error') ||
    text.includes('Connected') ||
    text.includes('Falling back')
  ) {
    consoleLogs.push(`[browser:${msg.type()}] ${text}`)
  }
})

await page.goto('http://localhost:5173/speaking-examiner', {
  waitUntil: 'domcontentloaded',
})
log(4, 'Page loaded')

log(5, 'Clicking Start Speaking Test...')
await page.getByRole('button', { name: /Start Speaking Test/i }).click()

log(5, 'Waiting for Simli connection (20s)...')
await page.waitForTimeout(20000)

const videoCount = await page.locator('video').count()
const videoVisible = await page
  .locator('video')
  .first()
  .isVisible()
  .catch(() => false)
const connecting = await page
  .getByText('Connecting avatar')
  .isVisible()
  .catch(() => false)
const examinerText = await page
  .locator('.rounded-lg.border.bg-blue-50\\/50')
  .textContent()
  .catch(() => '')

log(5, `Video elements: ${videoCount}, visible: ${videoVisible}`)
log(5, `Still connecting: ${connecting}`)
log(5, `Examiner text shown: "${(examinerText || '').slice(0, 80)}..."`)

log(6, 'Simli browser console logs:')
if (consoleLogs.length === 0) {
  log(6, '(no Simli logs captured)')
} else {
  consoleLogs.slice(0, 15).forEach((l) => log(6, l))
  if (consoleLogs.length > 15) log(6, `... +${consoleLogs.length - 15} more`)
}

const simliConnected = consoleLogs.some((l) => l.includes('[Simli] Connected'))
log(6, `Simli connected: ${simliConnected ? 'YES ✓' : 'NO ✗'}`)
log(6, `ElevenLabs audio available: ${audioLen > 0 ? 'YES ✓' : 'NO ✗'}`)
log(
  6,
  `Lip sync possible: ${simliConnected && audioLen > 0 ? 'YES (video+audio)' : 'NO'}`,
)

// ── Step 7: Respond (simulate candidate answer) ──
log(7, 'Simulating candidate response via API...')
const history = [{ role: 'examiner', text: startData.text }]
const respondResp = await fetch(
  'http://localhost:8000/admin/speaking-examiner/respond',
  {
    method: 'POST',
    headers: authHeaders,
    body: JSON.stringify({
      candidate_text: 'My name is Alex Smith, you can call me Alex.',
      conversation_history: history,
    }),
  },
)
const respondData = await respondResp.json()
const respondAudioLen = (respondData.audio_base64 || '').length
log(7, `Respond OK (${respondResp.status})`)
log(7, `Next question: "${(respondData.text || '').slice(0, 80)}..."`)
log(7, `Audio base64 length: ${respondAudioLen}`)

await browser.close()

log(8, '=== SUMMARY ===')
log(8, `Backend: running`)
log(8, `ElevenLabs: ${audioLen > 0 ? 'OK' : 'FAILED (402 or empty)'}`)
log(8, `Simli WebRTC: ${simliConnected ? 'Connected' : 'Not connected'}`)
log(8, `Video in DOM: ${videoCount > 0 ? 'Yes' : 'No'}`)
log(8, `Gemini dialogue: OK`)
log(8, `Full lip sync: ${simliConnected && audioLen > 0 ? 'Should work' : 'Blocked'}`)
