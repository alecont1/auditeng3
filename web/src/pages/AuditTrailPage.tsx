import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, AlertTriangle, RefreshCw, FileText } from 'lucide-react'
import { useAuditTrail } from '@/hooks'
import { AuditTimeline } from '@/components/analysis'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header skeleton */}
      <div className="space-y-4">
        <Skeleton className="h-9 w-40" />
        <div className="flex items-center gap-4">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-6 w-24" />
        </div>
      </div>

      {/* Timeline skeleton */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <Skeleton className="h-10 w-40" />
          <Skeleton className="h-6 w-24" />
        </div>
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex gap-4">
            <Skeleton className="w-3 h-3 rounded-full" />
            <Skeleton className="flex-1 h-20 rounded-lg" />
          </div>
        ))}
      </div>
    </div>
  )
}

export function AuditTrailPage() {
  const { analysisId } = useParams<{ analysisId: string }>()
  const { data: auditData, isLoading, isError, error, refetch } = useAuditTrail(analysisId)

  if (isLoading) {
    return <LoadingSkeleton />
  }

  if (isError) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Error loading audit trail</AlertTitle>
        <AlertDescription className="flex items-center justify-between">
          <span>{(error as Error)?.message || 'Something went wrong'}</span>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Retry
          </Button>
        </AlertDescription>
      </Alert>
    )
  }

  // Truncate ID for display
  const truncatedId = analysisId
    ? analysisId.length > 12
      ? `${analysisId.slice(0, 8)}...${analysisId.slice(-4)}`
      : analysisId
    : 'Unknown'

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="space-y-4">
        {/* Back link */}
        <Link
          to={`/analyses/${analysisId}`}
          className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Analysis
        </Link>

        {/* Page title and metadata */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-3">
            <FileText className="h-6 w-6 text-muted-foreground" />
            <h1 className="text-2xl font-bold tracking-tight">Audit Trail</h1>
          </div>
          <span className="text-muted-foreground">|</span>
          <code className="text-sm text-muted-foreground">{truncatedId}</code>
          {auditData && (
            <>
              <span className="text-muted-foreground">|</span>
              <span className="text-sm text-muted-foreground">
                {auditData.event_count} events
              </span>
            </>
          )}
        </div>
      </div>

      {/* Timeline */}
      <AuditTimeline
        events={auditData?.events ?? []}
        isLoading={isLoading}
      />
    </div>
  )
}
