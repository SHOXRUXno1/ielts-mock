import { Outlet } from '@tanstack/react-router'

export function TestLayout() {
  return (
    <div className='flex h-svh flex-col bg-white text-slate-900'>
      <Outlet />
    </div>
  )
}
