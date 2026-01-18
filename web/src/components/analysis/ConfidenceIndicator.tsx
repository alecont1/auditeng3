import { Info } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'

interface ConfidenceIndicatorProps {
  confidenceScore?: number
}

function getConfidenceLevel(score: number): { label: string; className: string } {
  if (score >= 0.85) return { label: 'High', className: 'text-green-600' }
  if (score >= 0.7) return { label: 'Medium', className: 'text-amber-600' }
  return { label: 'Low', className: 'text-red-600' }
}

function getProgressColor(score: number): string {
  if (score >= 0.85) return 'bg-green-600'
  if (score >= 0.7) return 'bg-amber-500'
  return 'bg-red-600'
}

export function ConfidenceIndicator({ confidenceScore }: ConfidenceIndicatorProps) {
  const score = confidenceScore ?? 0
  const percent = score * 100
  const { label, className } = getConfidenceLevel(score)

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Extraction Confidence
          </CardTitle>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Info className="h-4 w-4 text-muted-foreground cursor-help" />
              </TooltipTrigger>
              <TooltipContent className="max-w-xs">
                <p>
                  Confidence score indicates how reliably data was extracted from
                  the document. Higher scores mean more accurate extraction.
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center justify-between">
          <span className={cn('text-2xl font-bold', className)}>
            {percent.toFixed(0)}%
          </span>
          <span className={cn('text-sm font-medium', className)}>{label}</span>
        </div>
        <Progress
          value={percent}
          className="h-2"
          indicatorClassName={getProgressColor(score)}
        />
      </CardContent>
    </Card>
  )
}
