import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { Verdict } from '@/types'

interface VerdictBadgeProps {
  verdict: Verdict
  className?: string
}

const verdictConfig: Record<Verdict, { label: string; className: string }> = {
  APPROVED: {
    label: 'Approved',
    className: 'border-green-500 text-green-700 bg-transparent',
  },
  REJECTED: {
    label: 'Rejected',
    className: 'border-red-500 text-red-700 bg-transparent',
  },
  NEEDS_REVIEW: {
    label: 'Needs Review',
    className: 'border-amber-500 text-amber-700 bg-transparent',
  },
}

export function VerdictBadge({ verdict, className }: VerdictBadgeProps) {
  const config = verdictConfig[verdict]

  return (
    <Badge variant="outline" className={cn(config.className, className)}>
      {config.label}
    </Badge>
  )
}
