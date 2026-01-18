import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

type Severity = 'critical' | 'major' | 'minor' | 'info'

interface SeverityBadgeProps {
  severity: Severity
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
  const config = severityConfig[severity]

  return (
    <Badge variant="outline" className={cn(config.className, className)}>
      {config.label}
    </Badge>
  )
}
