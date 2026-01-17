import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

interface StatusFilterProps {
  value: string | undefined
  onChange: (value: string | undefined) => void
}

export function StatusFilter({ value, onChange }: StatusFilterProps) {
  const handleChange = (newValue: string) => {
    // "all" represents no filter
    onChange(newValue === 'all' ? undefined : newValue)
  }

  return (
    <Select value={value ?? 'all'} onValueChange={handleChange}>
      <SelectTrigger className="w-[160px]">
        <SelectValue placeholder="All Statuses" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="all">All Statuses</SelectItem>
        <SelectItem value="pending">Pending</SelectItem>
        <SelectItem value="completed">Completed</SelectItem>
        <SelectItem value="failed">Failed</SelectItem>
      </SelectContent>
    </Select>
  )
}
