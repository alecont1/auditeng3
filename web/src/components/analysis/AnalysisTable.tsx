import { Link } from 'react-router-dom'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/ui/empty-state'
import { StatusBadge } from './StatusBadge'
import { VerdictBadge } from './VerdictBadge'
import { AnalysisTableSkeleton } from './AnalysisTableSkeleton'
import type { AnalysisSummary } from '@/types'
import { cn } from '@/lib/utils'

interface AnalysisTableProps {
  analyses: AnalysisSummary[]
  isLoading: boolean
  page: number
  totalPages: number
  onPageChange: (page: number) => void
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

function formatPercentage(value: number): string {
  return `${Math.round(value * 100)}%`
}

function getComplianceColor(score: number): string {
  if (score >= 0.9) return 'text-green-600'
  if (score >= 0.7) return 'text-amber-600'
  return 'text-red-600'
}

export function AnalysisTable({
  analyses,
  isLoading,
  page,
  totalPages,
  onPageChange,
}: AnalysisTableProps) {
  if (isLoading) {
    return <AnalysisTableSkeleton />
  }

  if (analyses.length === 0) {
    return (
      <EmptyState
        title="No analyses yet"
        description="Upload your first document to get started"
        action={
          <Button asChild>
            <Link to="/upload">Upload Document</Link>
          </Button>
        }
      />
    )
  }

  return (
    <div className="space-y-4">
      <div className="rounded-md border overflow-x-auto">
        <Table className="min-w-[800px]">
          <TableHeader>
            <TableRow>
              <TableHead>Equipment Tag</TableHead>
              <TableHead>Test Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Verdict</TableHead>
              <TableHead className="text-right">Compliance</TableHead>
              <TableHead className="text-right">Confidence</TableHead>
              <TableHead>Created</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {analyses.map((analysis) => (
              <TableRow key={analysis.id}>
                <TableCell>
                  <Link
                    to={`/analyses/${analysis.id}`}
                    className="font-medium text-primary hover:underline"
                  >
                    {analysis.equipment_tag}
                  </Link>
                </TableCell>
                <TableCell className="capitalize">
                  {analysis.test_type.replace(/_/g, ' ')}
                </TableCell>
                <TableCell>
                  <StatusBadge status={analysis.status} />
                </TableCell>
                <TableCell>
                  <VerdictBadge verdict={analysis.verdict} />
                </TableCell>
                <TableCell className="text-right">
                  <span className={cn('font-medium', getComplianceColor(analysis.compliance_score))}>
                    {formatPercentage(analysis.compliance_score)}
                  </span>
                </TableCell>
                <TableCell className="text-right text-muted-foreground">
                  {formatPercentage(analysis.confidence_score)}
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {formatDate(analysis.created_at)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Page {page} of {totalPages}
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
