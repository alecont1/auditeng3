import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { AuditEvent } from '@/types'

interface AuditEventCardProps {
  event: AuditEvent
}

/**
 * Get color class based on event type prefix
 */
function getEventColor(eventType: string): string {
  if (eventType.startsWith('extraction')) return 'bg-blue-500'
  if (eventType.startsWith('validation')) return 'bg-green-500'
  if (eventType.startsWith('finding')) return 'bg-amber-500'
  if (eventType.startsWith('verdict')) return 'bg-purple-500'
  if (eventType.includes('review') || eventType.includes('human')) return 'bg-indigo-500'
  return 'bg-gray-500'
}

/**
 * Get badge variant based on event type prefix
 */
function getBadgeVariant(eventType: string): 'default' | 'secondary' | 'destructive' | 'outline' {
  if (eventType.startsWith('extraction')) return 'default'
  if (eventType.startsWith('validation')) return 'secondary'
  return 'outline'
}

/**
 * Format event type to human readable label
 * e.g., "extraction_started" -> "Extraction Started"
 */
function formatEventType(eventType: string): string {
  return eventType
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

/**
 * Format ISO timestamp to readable format
 * e.g., "Jan 17, 2026 14:32:15"
 */
function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp)
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).format(date)
}

/**
 * Get confidence score color based on value
 */
function getConfidenceColor(score: number): string {
  if (score >= 0.9) return 'text-green-600'
  if (score >= 0.7) return 'text-amber-600'
  return 'text-red-600'
}

export function AuditEventCard({ event }: AuditEventCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const hasDetails =
    event.details ||
    event.model_version ||
    event.prompt_version ||
    event.confidence_score !== undefined ||
    event.rule_id

  return (
    <Card
      className={`cursor-pointer transition-shadow hover:shadow-md ${hasDetails ? '' : 'cursor-default'}`}
      onClick={() => hasDetails && setIsExpanded(!isExpanded)}
    >
      <CardContent className="p-4">
        {/* Collapsed view - always visible */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Event type dot */}
            <div className={`w-2.5 h-2.5 rounded-full ${getEventColor(event.event_type)}`} />

            {/* Event type badge */}
            <Badge variant={getBadgeVariant(event.event_type)}>
              {formatEventType(event.event_type)}
            </Badge>

            {/* Timestamp */}
            <span className="text-sm text-muted-foreground">
              {formatTimestamp(event.event_timestamp)}
            </span>
          </div>

          {/* Expand indicator */}
          {hasDetails && (
            <button
              type="button"
              className="text-muted-foreground hover:text-foreground transition-colors"
              aria-label={isExpanded ? 'Collapse details' : 'Expand details'}
            >
              {isExpanded ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </button>
          )}
        </div>

        {/* Expanded view - details section */}
        {isExpanded && hasDetails && (
          <div className="mt-4 pt-4 border-t space-y-3">
            {/* Model and Prompt versions */}
            {(event.model_version || event.prompt_version) && (
              <div className="flex flex-wrap gap-4 text-sm">
                {event.model_version && (
                  <div>
                    <span className="text-muted-foreground">Model: </span>
                    <span className="font-mono">{event.model_version}</span>
                  </div>
                )}
                {event.prompt_version && (
                  <div>
                    <span className="text-muted-foreground">Prompt: </span>
                    <span className="font-mono">{event.prompt_version}</span>
                  </div>
                )}
              </div>
            )}

            {/* Confidence score */}
            {event.confidence_score !== undefined && (
              <div className="text-sm">
                <span className="text-muted-foreground">Confidence: </span>
                <span className={`font-medium ${getConfidenceColor(event.confidence_score)}`}>
                  {(event.confidence_score * 100).toFixed(1)}%
                </span>
              </div>
            )}

            {/* Rule ID */}
            {event.rule_id && (
              <div className="text-sm">
                <span className="text-muted-foreground">Rule: </span>
                <span className="font-mono">{event.rule_id}</span>
              </div>
            )}

            {/* Details JSON */}
            {event.details && Object.keys(event.details).length > 0 && (
              <div className="text-sm">
                <span className="text-muted-foreground block mb-1">Details:</span>
                <div className="bg-muted rounded-md p-3 overflow-x-auto">
                  <pre className="text-xs font-mono whitespace-pre-wrap break-words">
                    {JSON.stringify(event.details, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
