import { StatusFilter } from './StatusFilter'
import { DateRangeFilter } from './DateRangeFilter'
import { SortSelect } from './SortSelect'

interface AnalysisFiltersProps {
  status: string | undefined
  onStatusChange: (status: string | undefined) => void
  dateFrom: string | undefined
  dateTo: string | undefined
  onDateRangeChange: (from: string | undefined, to: string | undefined) => void
  sortBy: string
  sortOrder: 'asc' | 'desc'
  onSortChange: (sortBy: string, sortOrder: 'asc' | 'desc') => void
}

export function AnalysisFilters({
  status,
  onStatusChange,
  dateFrom,
  dateTo,
  onDateRangeChange,
  sortBy,
  sortOrder,
  onSortChange,
}: AnalysisFiltersProps) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-4">
      <StatusFilter value={status} onChange={onStatusChange} />
      <DateRangeFilter
        dateFrom={dateFrom}
        dateTo={dateTo}
        onChange={onDateRangeChange}
      />
      <SortSelect
        sortBy={sortBy}
        sortOrder={sortOrder}
        onChange={onSortChange}
      />
    </div>
  )
}
