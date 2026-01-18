import { CheckCircle2, Loader2 } from 'lucide-react'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import { useApproveAnalysis } from '@/hooks/useApproveAnalysis'

interface ApproveButtonProps {
  analysisId: string
  disabled?: boolean
  onSuccess?: () => void
}

export function ApproveButton({ analysisId, disabled, onSuccess }: ApproveButtonProps) {
  const { mutate: approve, isPending } = useApproveAnalysis(analysisId)

  const handleApprove = () => {
    approve(undefined, {
      onSuccess: () => {
        onSuccess?.()
      },
    })
  }

  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <Button
          variant="default"
          className="bg-green-600 hover:bg-green-700"
          disabled={disabled || isPending}
        >
          {isPending ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <CheckCircle2 className="mr-2 h-4 w-4" />
          )}
          Approve
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Approve this analysis?</AlertDialogTitle>
          <AlertDialogDescription>
            This will mark the analysis as approved. This action confirms that
            the equipment meets compliance requirements.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleApprove}
            className="bg-green-600 hover:bg-green-700"
          >
            Confirm Approval
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
