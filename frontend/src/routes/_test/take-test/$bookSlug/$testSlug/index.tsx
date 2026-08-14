import { createFileRoute } from '@tanstack/react-router'

/**
 * Intro / resume entry. The shell short-circuits this route: it renders the
 * intro screen when there is no attempt and redirects into the first section
 * once one exists, so nothing is rendered here.
 */
export const Route = createFileRoute('/_test/take-test/$bookSlug/$testSlug/')({
  component: () => null,
})
