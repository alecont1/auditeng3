import { useState, useMemo } from 'react'
import { Filter } from 'lucide-react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { AuditEventCard } from './AuditEventCard'
import type { AuditEvent } from '@/types'

interface AuditTimelineProps {
  events: AuditEvent[]
  isLoading?: boolean
}

type FilterType = 'all' | 'extraction' | 'validation' | 'findings' | 'review'

/**
 * Filter event based on selected filter type
 */
function matchesFilter(event: AuditEvent, filter: FilterType): boolean {
  if (filter === 'all') return true
  if (filter === 'extraction') return event.event_type.startsWith('extraction')
  if (filter === 'validation') return event.event_type.startsWith('validation')
  if (filter === 'findings') return event.event_type.startsWith('finding')
  if (filter === 'review') {
    return event.event_type.includes('review') || event.event_type.startsWith('verdict')
  }
  return true
}

/**
 * Get timeline dot color based on event type
 */
function getTimelineDotColor(eventType: string): string {
  if (eventType.startsWith('extraction')) return 'bg-blue-500'
  if (eventType.startsWith('validation')) return 'bg-green-500'
  if (eventType.startsWith('finding')) return 'bg-amber-500'
  if (eventType.startsWith('verdict')) return 'bg-purple-500'
  if (eventType.includes('review') || eventType.includes('human')) return 'bg-indigo-500'
  return 'bg-gray-500'
}

function TimelineSkeleton() {
  return (
    <div className="space-y-4">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="flex gap-4">
          <div className="flex flex-col items-center">
            <Skeleton className="w-3 h-3 rounded-full" />
            <Skeleton className="w-0.5 h-16" />
          </div>
          <div className="flex-1">
            <Skeleton className="h-20 w-full rounded-lg" />
          </div>
        </div>
      ))}
    </div>
  )
}

function EmptyState() {
  return (
    <div className="text-center py-12">
      <div className="text-muted-foreground">
        <Filter className="h-12 w-12 mx-auto mb-4 opacity-50" />
        <p className="text-lg font-medium">No audit events found</p>
        <p className="text-sm mt-1">
          No events match the current filter. Try selecting "All Events" or check back later.
        </p>
      </div>
    </div>
  )
}

export function AuditTimeline({ events, isLoading }: AuditTimelineProps) {
  const [filter, setFilter] = useState<FilterType>('all')

  // Filter events based on selected filter
  const filteredEvents = useMemo(() => {
    return events.filter((event) => matchesFilter(event, filter))
  }, [events, filter])

  if (isLoading) {
    return (
      <div className="space-y-4">
        {/* Filter dropdown skeleton */}
        <div className="flex items-center justify-between">
          <Skeleton className="h-10 w-40" />
          <Skeleton className="h-6 w-24" />
        </div>
        <TimelineSkeleton />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Filter controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <Select value={filter} onValueChange={(value) => setFilter(value as FilterType)}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Filter events" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Events</SelectItem>
              <SelectItem value="extraction">Extraction</SelectItem>
              <SelectItem value="validation">Validation</SelectItem>
              <SelectItem value="findings">Findings</SelectItem>
              <SelectItem value="review">Review</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Event count badge */}
        <Badge variant="secondary">
          {filteredEvents.length}/{events.length} events
        </Badge>
      </div>

      {/* Timeline display */}
      {filteredEvents.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="relative">
          {/* Vertical timeline line */}
          <div className="absolute left-[5px] top-3 bottom-3 w-0.5 bg-gray-200" />

          {/* Timeline events */}
          <div className="space-y-4">
            {filteredEvents.map((event, index) => (
              <div key={event.id} className="flex gap-4 relative">
                {/* Timeline dot */}
                <div className="flex flex-col items-center z-10">
                  <div
                    className={`w-3 h-3 rounded-full ${getTimelineDotColor(event.event_type)} ring-2 ring-background`}
                  />
                  {/* Connector line (hidden for last item) */}
                  {index < filteredEvents.length - 1 && (
                    <div className="w-0.5 flex-1 bg-transparent" />
                  )}
                </div>

                {/* Event card */}
                <div className="flex-1 pb-2">
                  <AuditEventCard event={event} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
