import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

interface SortSelectProps {
  sortBy: string
  sortOrder: 'asc' | 'desc'
  onChange: (sortBy: string, sortOrder: 'asc' | 'desc') => void
}

type SortOption = {
  value: string
  label: string
  sortBy: string
  sortOrder: 'asc' | 'desc'
}

const SORT_OPTIONS: SortOption[] = [
  { value: 'created_at_desc', label: 'Newest first', sortBy: 'created_at', sortOrder: 'desc' },
  { value: 'created_at_asc', label: 'Oldest first', sortBy: 'created_at', sortOrder: 'asc' },
  { value: 'compliance_score_desc', label: 'Highest score', sortBy: 'compliance_score', sortOrder: 'desc' },
  { value: 'compliance_score_asc', label: 'Lowest score', sortBy: 'compliance_score', sortOrder: 'asc' },
]

export function SortSelect({ sortBy, sortOrder, onChange }: SortSelectProps) {
  const currentValue = `${sortBy}_${sortOrder}`

  const handleChange = (value: string) => {
    const option = SORT_OPTIONS.find((opt) => opt.value === value)
    if (option) {
      onChange(option.sortBy, option.sortOrder)
    }
  }

  return (
    <Select value={currentValue} onValueChange={handleChange}>
      <SelectTrigger className="w-[160px]">
        <SelectValue placeholder="Sort by" />
      </SelectTrigger>
      <SelectContent>
        {SORT_OPTIONS.map((option) => (
          <SelectItem key={option.value} value={option.value}>
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
