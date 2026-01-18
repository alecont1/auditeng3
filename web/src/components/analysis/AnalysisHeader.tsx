import { ArrowLeft } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

interface AnalysisHeaderProps {
  equipmentTag?: string
  testType: string
  equipmentType: string
  createdAt: string
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatTestType(testType: string): string {
  return testType
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (l) => l.toUpperCase())
}

function formatEquipmentType(equipmentType: string): string {
  return equipmentType
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (l) => l.toUpperCase())
}

export function AnalysisHeader({
  equipmentTag,
  testType,
  equipmentType,
  createdAt,
}: AnalysisHeaderProps) {
  return (
    <div className="space-y-4">
      <Button variant="ghost" size="sm" asChild className="-ml-2">
        <Link to="/dashboard">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Dashboard
        </Link>
      </Button>

      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">
          {equipmentTag || 'Unknown Equipment'}
        </h1>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="secondary">{formatTestType(testType)}</Badge>
          <Badge variant="outline">{formatEquipmentType(equipmentType)}</Badge>
          <span className="text-sm text-muted-foreground">
            {formatDate(createdAt)}
          </span>
        </div>
      </div>
    </div>
  )
}
