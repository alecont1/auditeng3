import { useState } from 'react'
import { Loader2, XCircle } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { useRejectAnalysis } from '@/hooks/useRejectAnalysis'

interface RejectDialogProps {
  analysisId: string
  disabled?: boolean
  onSuccess?: () => void
}

const MIN_REASON_LENGTH = 10

export function RejectDialog({ analysisId, disabled, onSuccess }: RejectDialogProps) {
  const [open, setOpen] = useState(false)
  const [reason, setReason] = useState('')
  const { mutate: reject, isPending } = useRejectAnalysis(analysisId)

  const isValidReason = reason.trim().length >= MIN_REASON_LENGTH

  const handleReject = () => {
    if (!isValidReason) return

    reject(reason.trim(), {
      onSuccess: () => {
        setOpen(false)
        setReason('')
        onSuccess?.()
      },
    })
  }

  const handleOpenChange = (newOpen: boolean) => {
    if (!isPending) {
      setOpen(newOpen)
      if (!newOpen) {
        setReason('')
      }
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button variant="outline" disabled={disabled}>
          <XCircle className="mr-2 h-4 w-4" />
          Reject
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Reject Analysis</DialogTitle>
          <DialogDescription>
            Please provide a reason for rejecting this analysis. This helps
            track why equipment failed compliance checks.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="reason">Rejection Reason</Label>
            <Textarea
              id="reason"
              placeholder="Enter the reason for rejection (minimum 10 characters)..."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={4}
              disabled={isPending}
            />
            <p className="text-xs text-muted-foreground">
              {reason.trim().length}/{MIN_REASON_LENGTH} characters minimum
            </p>
          </div>
        </div>
        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            variant="ghost"
            onClick={() => handleOpenChange(false)}
            disabled={isPending}
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={handleReject}
            disabled={!isValidReason || isPending}
          >
            {isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <XCircle className="mr-2 h-4 w-4" />
            )}
            Reject Analysis
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
