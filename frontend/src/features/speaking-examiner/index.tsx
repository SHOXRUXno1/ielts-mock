import { getRouteApi } from '@tanstack/react-router'
import { SpeakingExaminerSession } from './speaking-examiner-session'

const route = getRouteApi('/_authenticated/speaking-examiner')

export function SpeakingExaminer() {
  const { attemptId } = route.useSearch()
  return <SpeakingExaminerSession attemptId={attemptId} mode='standalone' />
}
