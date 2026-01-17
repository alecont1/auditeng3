import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

type Status = 'pending' | 'completed' | 'failed'

interface StatusBadgeProps {
  status: Status
  className?: string
}

const statusConfig: Record<Status, { label: string; className: string }> = {
  pending: {
    label: 'Pending',
    className: 'bg-amber-100 text-amber-800 border-amber-200 hover:bg-amber-100',
  },
  completed: {
    label: 'Completed',
    className: 'bg-green-100 text-green-800 border-green-200 hover:bg-green-100',
  },
  failed: {
    label: 'Failed',
    className: 'bg-red-100 text-red-800 border-red-200 hover:bg-red-100',
  },
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = statusConfig[status]

  return (
    <Badge variant="outline" className={cn(config.className, className)}>
      {config.label}
    </Badge>
  )
}
