import { isRetryableUploadError } from '@/lib/api/error'
import { api, MEDIA_UPLOAD_TIMEOUT_MS } from '@/lib/axios'
import type { Test, TestDetail } from '@/features/tests/data/schema'

export type TestCreatePayload = {
  title: string
  description?: string | null
  is_published?: boolean
  type?: string
  book_name?: string | null
  book_slug?: string | null
  test_number?: number | null
}

export type TestUpdatePayload = Partial<TestCreatePayload>

export type SlugRedirectResult = {
  book_slug: string
  test_number: number
}

// ---------------------------------------------------------------------------
// Import types
// ---------------------------------------------------------------------------

export type ImportSectionSummary = {
  sheet_name: string
  kind: string
  passage_word_count: number | null
  questions_count: number
  tasks_count: number | null
  audio_filename: string | null
}

export type ImportPreview = {
  title: string
  description: string | null
  type: string
  sections: ImportSectionSummary[]
  total_questions: number
  warnings: string[]
  errors: string[]
}

export type ListeningSectionInfo = {
  id: string
  name: string
  audio_filename: string | null
}

export type ImportConfirmResult = {
  test_id: string
  sections_created: number
  questions_created: number
  listening_sections: ListeningSectionInfo[]
}

export async function fetchTests(): Promise<Test[]> {
  const { data } = await api.get<Test[]>('/admin/tests/')
  return data
}

export async function fetchTest(id: string): Promise<TestDetail> {
  const { data } = await api.get<TestDetail>(`/tests/${id}`)
  return data
}

/** Admin-only detail fetch — never goes through take-mode stripping. */
export async function fetchAdminTest(id: string): Promise<TestDetail> {
  const { data } = await api.get<TestDetail>(`/admin/tests/${id}`)
  return data
}

export async function fetchTestBySlug(bookSlug: string, testNumber: number): Promise<TestDetail> {
  const { data } = await api.get<TestDetail>(`/tests/by-slug/${bookSlug}/${testNumber}`)
  return data
}

export async function fetchSlugRedirect(testId: string): Promise<SlugRedirectResult> {
  const { data } = await api.get<SlugRedirectResult>(`/tests/${testId}/slug-redirect`)
  return data
}

export async function createTest(payload: TestCreatePayload): Promise<Test> {
  const { data } = await api.post<Test>('/admin/tests/', payload)
  return data
}

export async function updateTest(
  id: string,
  payload: TestUpdatePayload
): Promise<Test> {
  const { data } = await api.patch<Test>(`/admin/tests/${id}`, payload)
  return data
}

export async function deleteTest(id: string): Promise<void> {
  await api.delete(`/admin/tests/${id}`)
}

// ---------------------------------------------------------------------------
// Import functions
// ---------------------------------------------------------------------------

export async function downloadTemplate(): Promise<void> {
  const response = await api.get('/admin/tests/template', {
    responseType: 'blob',
  })
  const url = URL.createObjectURL(response.data as Blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'ielts_test_template.xlsx'
  a.click()
  URL.revokeObjectURL(url)
}

export async function previewImport(file: File): Promise<ImportPreview> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post<ImportPreview>(
    '/admin/tests/import/preview',
    form,
    { timeout: MEDIA_UPLOAD_TIMEOUT_MS },
  )
  return data
}

export async function confirmImport(file: File): Promise<ImportConfirmResult> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post<ImportConfirmResult>(
    '/admin/tests/import/confirm',
    form,
    { timeout: MEDIA_UPLOAD_TIMEOUT_MS },
  )
  return data
}

export async function publishTest(id: string, force = false): Promise<import('@/features/tests/data/schema').TestDetail> {
  const { data } = await api.post(`/admin/tests/${id}/publish`, null, {
    params: force ? { force: true } : undefined,
  })
  return data
}

export async function normalizeSections(id: string): Promise<import('@/features/tests/data/schema').TestDetail> {
  const { data } = await api.post(`/admin/tests/${id}/normalize-sections`)
  return data
}

export const MAX_AUDIO_UPLOAD_BYTES = 50 * 1024 * 1024

const AUDIO_FILENAME = /\.(mp3|mpeg|ogg|mp4|m4a|wav|webm|aac)$/i

export function assertAudioUpload(file: File): void {
  if (file.size === 0) {
    throw new Error('Empty audio file.')
  }
  if (file.size > MAX_AUDIO_UPLOAD_BYTES) {
    throw new Error('Audio is too large (max 50 MB).')
  }
  if (!file.type.startsWith('audio/') && !AUDIO_FILENAME.test(file.name)) {
    throw new Error(
      'Unsupported audio format. Use MP3, OGG, MP4, WAV, WebM or AAC.',
    )
  }
}

async function postAudioForm(
  testId: string,
  form: FormData,
): Promise<{ url: string }> {
  const { data } = await api.post<{ url: string }>(
    `/admin/tests/${testId}/audio`,
    form,
    { timeout: MEDIA_UPLOAD_TIMEOUT_MS },
  )
  return data
}

export async function uploadSectionAudio(
  testId: string,
  sectionId: string,
  file: File
): Promise<{ url: string }> {
  assertAudioUpload(file)
  const form = new FormData()
  form.append('section_id', sectionId)
  form.append('file', file)
  try {
    return await postAudioForm(testId, form)
  } catch (err) {
    if (!isRetryableUploadError(err)) throw err
    return await postAudioForm(testId, form)
  }
}
