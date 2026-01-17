import { useState } from 'react'
import { format } from 'date-fns'
import { CalendarIcon } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Calendar } from '@/components/ui/calendar'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { cn } from '@/lib/utils'

interface DateRangeFilterProps {
  dateFrom: string | undefined
  dateTo: string | undefined
  onChange: (from: string | undefined, to: string | undefined) => void
}

export function DateRangeFilter({ dateFrom, dateTo, onChange }: DateRangeFilterProps) {
  const [open, setOpen] = useState(false)

  // Convert string dates to Date objects for the calendar
  const fromDate = dateFrom ? new Date(dateFrom) : undefined
  const toDate = dateTo ? new Date(dateTo) : undefined

  const handleSelect = (range: { from?: Date; to?: Date } | undefined) => {
    const from = range?.from ? format(range.from, 'yyyy-MM-dd') : undefined
    const to = range?.to ? format(range.to, 'yyyy-MM-dd') : undefined
    onChange(from, to)
  }

  const handleClear = () => {
    onChange(undefined, undefined)
    setOpen(false)
  }

  const displayText = () => {
    if (fromDate && toDate) {
      return `${format(fromDate, 'MMM d')} - ${format(toDate, 'MMM d, yyyy')}`
    }
    if (fromDate) {
      return `From ${format(fromDate, 'MMM d, yyyy')}`
    }
    return 'Select dates'
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className={cn(
            'w-[200px] justify-start text-left font-normal',
            !dateFrom && !dateTo && 'text-muted-foreground'
          )}
        >
          <CalendarIcon className="mr-2 h-4 w-4" />
          {displayText()}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="start">
        <Calendar
          mode="range"
          selected={fromDate && toDate ? { from: fromDate, to: toDate } : fromDate ? { from: fromDate, to: undefined } : undefined}
          onSelect={handleSelect}
          numberOfMonths={2}
        />
        <div className="border-t p-3 flex justify-end gap-2">
          <Button variant="ghost" size="sm" onClick={handleClear}>
            Clear
          </Button>
          <Button size="sm" onClick={() => setOpen(false)}>
            Apply
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  )
}
