import { useState } from 'react'
import { useAnalyses } from '@/hooks'
import { AnalysisTable } from '@/components/analysis'

const PER_PAGE = 10

export function DashboardPage() {
  const [page, setPage] = useState(1)
  const { data, isLoading } = useAnalyses({ page, per_page: PER_PAGE })

  const analyses = data?.items ?? []
  const totalPages = data?.meta.total_pages ?? 1

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          View and manage your equipment analyses.
        </p>
      </div>

      <AnalysisTable
        analyses={analyses}
        isLoading={isLoading}
        page={page}
        totalPages={totalPages}
        onPageChange={setPage}
      />
    </div>
  )
}
