import { useState, useEffect, useMemo } from 'react'
import { useAnalyses } from '@/hooks'
import { AnalysisTable, AnalysisFilters, QuickStats } from '@/components/analysis'

const PER_PAGE = 10

export function DashboardPage() {
  const [page, setPage] = useState(1)

  // Filter state
  const [status, setStatus] = useState<string | undefined>()
  const [dateFrom, setDateFrom] = useState<string | undefined>()
  const [dateTo, setDateTo] = useState<string | undefined>()
  const [sortBy, setSortBy] = useState('created_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')

  // Reset page to 1 when filters change
  useEffect(() => {
    setPage(1)
  }, [status, dateFrom, dateTo, sortBy, sortOrder])

  const { data, isLoading } = useAnalyses({
    page,
    per_page: PER_PAGE,
    status: status as 'pending' | 'completed' | 'failed' | undefined,
    date_from: dateFrom,
    date_to: dateTo,
    sort_by: sortBy as 'created_at' | 'compliance_score',
    sort_order: sortOrder,
  })

  const analyses = data?.items ?? []
  const totalPages = data?.meta.total_pages ?? 1
  const totalCount = data?.meta.total ?? 0

  // Compute stats from current data (approximation until backend provides stats endpoint)
  const stats = useMemo(() => {
    const today = new Date().toISOString().split('T')[0]

    const pendingCount = analyses.filter((a) => a.status === 'pending').length
    const completedTodayCount = analyses.filter((a) => {
      const createdDate = a.created_at.split('T')[0]
      return a.status === 'completed' && createdDate === today
    }).length

    return {
      totalCount,
      pendingCount,
      completedTodayCount,
    }
  }, [analyses, totalCount])

  const handleDateRangeChange = (from: string | undefined, to: string | undefined) => {
    setDateFrom(from)
    setDateTo(to)
  }

  const handleSortChange = (newSortBy: string, newSortOrder: 'asc' | 'desc') => {
    setSortBy(newSortBy)
    setSortOrder(newSortOrder)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          View and manage your equipment analyses.
        </p>
      </div>

      <QuickStats
        totalCount={stats.totalCount}
        pendingCount={stats.pendingCount}
        completedTodayCount={stats.completedTodayCount}
        isLoading={isLoading}
      />

      <AnalysisFilters
        status={status}
        onStatusChange={setStatus}
        dateFrom={dateFrom}
        dateTo={dateTo}
        onDateRangeChange={handleDateRangeChange}
        sortBy={sortBy}
        sortOrder={sortOrder}
        onSortChange={handleSortChange}
      />

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
