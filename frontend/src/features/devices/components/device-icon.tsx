import { Monitor, Smartphone, Tablet, HelpCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

const ICON_MAP = {
  desktop: Monitor,
  mobile: Smartphone,
  tablet: Tablet,
  unknown: HelpCircle,
} as const

type DeviceIconProps = {
  deviceType: string
  className?: string
  size?: number
}

export function DeviceIcon({
  deviceType,
  className,
  size = 20,
}: DeviceIconProps) {
  const key = (deviceType in ICON_MAP
    ? deviceType
    : 'unknown') as keyof typeof ICON_MAP
  const Icon = ICON_MAP[key]
  return <Icon size={size} className={cn('shrink-0', className)} />
}
