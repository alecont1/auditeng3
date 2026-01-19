import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

type Severity = 'critical' | 'major' | 'minor' | 'info'

interface SeverityBadgeProps {
  severity?: Severity | null
  className?: string
}

const severityConfig: Record<Severity, { label: string; className: string }> = {
  critical: {
    label: 'Critical',
    className: 'bg-red-100 text-red-800 border-red-200',
  },
  major: {
    label: 'Major',
    className: 'bg-orange-100 text-orange-800 border-orange-200',
  },
  minor: {
    label: 'Minor',
    className: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  },
  info: {
    label: 'Info',
    className: 'bg-slate-100 text-slate-800 border-slate-200',
  },
}

export function SeverityBadge({ severity, className }: SeverityBadgeProps) {
  const config = severity ? severityConfig[severity] : null

  if (!config) {
    return (
      <Badge variant="outline" className={cn('bg-gray-100 text-gray-800 border-gray-200', className)}>
        Unknown
      </Badge>
    )
  }

  return (
    <Badge variant="outline" className={cn(config.className, className)}>
      {config.label}
    </Badge>
  )
}
