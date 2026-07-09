import { createFileRoute, Outlet } from '@tanstack/react-router'

export const Route = createFileRoute('/_test/take-test/$bookSlug/$testSlug')({
  component: () => <Outlet />,
})
