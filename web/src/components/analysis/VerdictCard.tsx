import { CheckCircle2, XCircle, AlertCircle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'
import type { Verdict } from '@/types'

interface VerdictCardProps {
  verdict?: Verdict
  complianceScore?: number
}

const verdictConfig: Record<Verdict, { icon: typeof CheckCircle2; label: string; className: string }> = {
  APPROVED: {
    icon: CheckCircle2,
    label: 'Approved',
    className: 'text-green-600',
  },
  REJECTED: {
    icon: XCircle,
    label: 'Rejected',
    className: 'text-red-600',
  },
  NEEDS_REVIEW: {
    icon: AlertCircle,
    label: 'Needs Review',
    className: 'text-amber-600',
  },
}

function getScoreColor(score: number): string {
  if (score >= 90) return 'text-green-600'
  if (score >= 70) return 'text-amber-600'
  return 'text-red-600'
}

function getProgressColor(score: number): string {
  if (score >= 90) return 'bg-green-600'
  if (score >= 70) return 'bg-amber-500'
  return 'bg-red-600'
}

export function VerdictCard({ verdict, complianceScore }: VerdictCardProps) {
  const config = verdict ? verdictConfig[verdict] : null
  const Icon = config?.icon
  const scorePercent = complianceScore ?? 0

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          Verdict
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Verdict display */}
        {config && Icon ? (
          <div className="flex items-center gap-3">
            <Icon className={cn('h-10 w-10', config.className)} />
            <span className={cn('text-2xl font-bold', config.className)}>
              {config.label}
            </span>
          </div>
        ) : (
          <div className="flex items-center gap-3 text-muted-foreground">
            <AlertCircle className="h-10 w-10" />
            <span className="text-2xl font-bold">Pending</span>
          </div>
        )}

        {/* Compliance score */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Compliance Score</span>
            <span className={cn('font-bold text-lg', getScoreColor(scorePercent))}>
              {scorePercent.toFixed(0)}%
            </span>
          </div>
          <Progress
            value={scorePercent}
            className="h-2"
            indicatorClassName={getProgressColor(scorePercent)}
          />
        </div>
      </CardContent>
    </Card>
  )
}
