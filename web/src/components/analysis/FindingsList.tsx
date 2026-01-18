import { CheckCircle2 } from 'lucide-react'
import { FindingCard } from './FindingCard'
import type { FindingDetail } from '@/types'

interface FindingsListProps {
  findings: FindingDetail[]
}

type SeverityOrder = 'critical' | 'major' | 'minor' | 'info'
const severityOrder: SeverityOrder[] = ['critical', 'major', 'minor', 'info']

function groupBySeverity(findings: FindingDetail[]): Record<SeverityOrder, FindingDetail[]> {
  const groups: Record<SeverityOrder, FindingDetail[]> = {
    critical: [],
    major: [],
    minor: [],
    info: [],
  }

  findings.forEach((finding) => {
    const severity = finding.severity as SeverityOrder
    if (groups[severity]) {
      groups[severity].push(finding)
    }
  })

  return groups
}

function getSeverityLabel(severity: SeverityOrder): string {
  return severity.charAt(0).toUpperCase() + severity.slice(1)
}

function getSeverityColor(severity: SeverityOrder): string {
  switch (severity) {
    case 'critical':
      return 'text-red-600'
    case 'major':
      return 'text-orange-600'
    case 'minor':
      return 'text-yellow-600'
    case 'info':
      return 'text-slate-600'
  }
}

export function FindingsList({ findings }: FindingsListProps) {
  if (findings.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <CheckCircle2 className="h-12 w-12 text-green-600 mb-3" />
        <h3 className="font-semibold text-lg">No Issues Found</h3>
        <p className="text-muted-foreground text-sm">
          All validation checks passed successfully.
        </p>
      </div>
    )
  }

  const groupedFindings = groupBySeverity(findings)

  // Count findings by severity for summary
  const criticalCount = groupedFindings.critical.length
  const majorCount = groupedFindings.major.length

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="text-sm text-muted-foreground">
        <span className="font-medium text-foreground">{findings.length}</span> finding
        {findings.length !== 1 ? 's' : ''}
        {(criticalCount > 0 || majorCount > 0) && (
          <span>
            {' ('}
            {criticalCount > 0 && (
              <span className="text-red-600">{criticalCount} critical</span>
            )}
            {criticalCount > 0 && majorCount > 0 && ', '}
            {majorCount > 0 && (
              <span className="text-orange-600">{majorCount} major</span>
            )}
            {')'}
          </span>
        )}
      </div>

      {/* Grouped findings */}
      {severityOrder.map((severity) => {
        const severityFindings = groupedFindings[severity]
        if (severityFindings.length === 0) return null

        return (
          <div key={severity} className="space-y-3">
            <h4 className={`text-sm font-medium ${getSeverityColor(severity)}`}>
              {getSeverityLabel(severity)} ({severityFindings.length})
            </h4>
            <div className="space-y-2">
              {severityFindings.map((finding, index) => (
                <FindingCard
                  key={`${finding.rule_id}-${index}`}
                  finding={finding}
                />
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
