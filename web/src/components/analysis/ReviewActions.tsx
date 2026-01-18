import { CheckCircle2, XCircle, AlertCircle } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { ApproveButton } from './ApproveButton'
import { RejectDialog } from './RejectDialog'
import type { Verdict } from '@/types'

interface ReviewActionsProps {
  analysisId: string
  currentVerdict?: Verdict
}

export function ReviewActions({ analysisId, currentVerdict }: ReviewActionsProps) {
  // Show status if already approved or rejected
  if (currentVerdict === 'APPROVED') {
    return (
      <Card className="border-green-200 bg-green-50">
        <CardContent className="flex items-center gap-3 p-4">
          <CheckCircle2 className="h-5 w-5 text-green-600" />
          <span className="text-green-800 font-medium">
            This analysis has been approved
          </span>
        </CardContent>
      </Card>
    )
  }

  if (currentVerdict === 'REJECTED') {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardContent className="flex items-center gap-3 p-4">
          <XCircle className="h-5 w-5 text-red-600" />
          <span className="text-red-800 font-medium">
            This analysis has been rejected
          </span>
        </CardContent>
      </Card>
    )
  }

  // Show review actions for NEEDS_REVIEW or undefined verdict
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-amber-600" />
            <span className="font-medium">Review Required</span>
          </div>
          <div className="flex items-center gap-2">
            <ApproveButton analysisId={analysisId} />
            <RejectDialog analysisId={analysisId} />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
