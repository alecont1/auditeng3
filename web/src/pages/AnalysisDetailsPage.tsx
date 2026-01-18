import { useParams } from 'react-router-dom'
import { Loader2, AlertTriangle, RefreshCw } from 'lucide-react'
import { useAnalysis } from '@/hooks'
import {
  AnalysisHeader,
  VerdictCard,
  ConfidenceIndicator,
  FindingsList,
  ReviewActions,
  DownloadReportButton,
} from '@/components/analysis'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header skeleton */}
      <div className="space-y-4">
        <Skeleton className="h-9 w-40" />
        <div className="space-y-2">
          <Skeleton className="h-10 w-64" />
          <div className="flex gap-2">
            <Skeleton className="h-6 w-24" />
            <Skeleton className="h-6 w-32" />
            <Skeleton className="h-6 w-40" />
          </div>
        </div>
      </div>

      {/* Cards skeleton */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardContent className="p-6 space-y-4">
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-12 w-32" />
            <Skeleton className="h-2 w-full" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 space-y-4">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-10 w-24" />
            <Skeleton className="h-2 w-full" />
          </CardContent>
        </Card>
      </div>

      {/* Findings placeholder skeleton */}
      <Card>
        <CardContent className="p-6">
          <Skeleton className="h-4 w-24 mb-4" />
          <div className="space-y-3">
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function ProcessingState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 space-y-4">
      <Loader2 className="h-12 w-12 animate-spin text-primary" />
      <div className="text-center space-y-2">
        <h2 className="text-xl font-semibold">Processing Analysis</h2>
        <p className="text-muted-foreground">
          Your document is being analyzed. This page will update automatically.
        </p>
      </div>
    </div>
  )
}

export function AnalysisDetailsPage() {
  const { id } = useParams<{ id: string }>()
  const { data: analysis, isLoading, isError, error, refetch } = useAnalysis(id!)

  if (isLoading) {
    return <LoadingSkeleton />
  }

  if (isError) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Error loading analysis</AlertTitle>
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

  // Analysis is still processing (null response from API) or undefined
  if (!analysis) {
    return <ProcessingState />
  }

  // Enable download only when analysis has a verdict (completed)
  const isCompleted = !!analysis.verdict

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <AnalysisHeader
          equipmentTag={analysis.equipment_tag}
          testType={analysis.test_type}
          equipmentType={analysis.equipment_type}
          createdAt={analysis.created_at}
        />
        <DownloadReportButton
          analysisId={analysis.id}
          disabled={!isCompleted}
        />
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <VerdictCard
          verdict={analysis.verdict}
          complianceScore={analysis.compliance_score}
        />
        <ConfidenceIndicator confidenceScore={analysis.confidence_score} />
      </div>

      {/* Review Actions */}
      <ReviewActions analysisId={analysis.id} currentVerdict={analysis.verdict} />

      {/* Findings Section */}
      <Card>
        <CardContent className="p-6">
          <h3 className="font-semibold mb-4">Validation Findings</h3>
          <FindingsList findings={analysis.findings} />
        </CardContent>
      </Card>
    </div>
  )
}
