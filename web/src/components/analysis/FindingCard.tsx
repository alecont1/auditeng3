import { useState } from 'react'
import { ChevronDown, ChevronRight, Lightbulb } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { SeverityBadge } from './SeverityBadge'
import { cn } from '@/lib/utils'
import type { FindingDetail } from '@/types'

interface FindingCardProps {
  finding: FindingDetail
  defaultExpanded?: boolean
}

export function FindingCard({ finding, defaultExpanded = false }: FindingCardProps) {
  const [expanded, setExpanded] = useState(defaultExpanded)
  const hasDetails = finding.evidence || finding.remediation

  return (
    <Card className="overflow-hidden">
      <button
        onClick={() => hasDetails && setExpanded(!expanded)}
        className={cn(
          'w-full text-left p-4 flex items-start gap-3',
          hasDetails && 'cursor-pointer hover:bg-muted/50 transition-colors'
        )}
        disabled={!hasDetails}
      >
        {/* Expand indicator */}
        <div className="mt-0.5 text-muted-foreground">
          {hasDetails ? (
            expanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )
          ) : (
            <div className="h-4 w-4" />
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0 space-y-2">
          <div className="flex items-center gap-2 flex-wrap">
            <SeverityBadge severity={finding.severity} />
            <code className="text-xs bg-muted px-1.5 py-0.5 rounded font-mono">
              {finding.rule_id}
            </code>
          </div>
          <p className="text-sm">{finding.message}</p>
        </div>
      </button>

      {/* Expanded content */}
      {expanded && hasDetails && (
        <CardContent className="pt-0 pb-4 pl-11 pr-4 space-y-4 border-t bg-muted/30">
          {/* Evidence section */}
          {finding.evidence && (
            <div className="space-y-2">
              <h4 className="text-xs font-medium uppercase text-muted-foreground">
                Evidence
              </h4>
              <div className="text-sm space-y-1">
                <div className="flex gap-2">
                  <span className="text-muted-foreground">Extracted:</span>
                  <span className="font-medium">
                    {String(finding.evidence.extracted_value)}
                  </span>
                </div>
                {finding.evidence.threshold !== undefined && (
                  <div className="flex gap-2">
                    <span className="text-muted-foreground">Threshold:</span>
                    <span className="font-medium">
                      {String(finding.evidence.threshold)}
                    </span>
                  </div>
                )}
                {finding.evidence.standard_reference !== 'N/A' && (
                  <div className="flex gap-2">
                    <span className="text-muted-foreground">Standard:</span>
                    <span className="font-medium">
                      {finding.evidence.standard_reference}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Remediation section */}
          {finding.remediation && (
            <div className="space-y-2">
              <h4 className="text-xs font-medium uppercase text-muted-foreground">
                Remediation
              </h4>
              <div className="flex items-start gap-2 text-sm bg-blue-50 dark:bg-blue-950/30 p-3 rounded-md">
                <Lightbulb className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                <p>{finding.remediation}</p>
              </div>
            </div>
          )}
        </CardContent>
      )}
    </Card>
  )
}
