import { Progress } from '@/components/ui/progress'
import { Spinner } from '@/components/ui/spinner'
import type { TaskStatus } from '@/types'

interface UploadProgressProps {
  uploadProgress: number
  taskStatus?: TaskStatus
  taskProgress?: number
}

export function UploadProgress({
  uploadProgress,
  taskStatus,
  taskProgress,
}: UploadProgressProps) {
  // During upload: show upload progress
  // After upload: show task status with spinner

  const isUploading = uploadProgress < 100
  const statusMessage = getStatusMessage(taskStatus)

  return (
    <div className="space-y-4 p-6 border rounded-lg">
      <div className="flex items-center gap-3">
        <Spinner size="sm" />
        <span className="font-medium">
          {isUploading ? 'Uploading...' : statusMessage}
        </span>
      </div>
      <Progress value={isUploading ? uploadProgress : (taskProgress || 0)} />
      <p className="text-sm text-muted-foreground">
        {isUploading
          ? `${uploadProgress}% uploaded`
          : taskStatus === 'processing'
            ? 'AI is analyzing your document...'
            : 'Please wait...'}
      </p>
    </div>
  )
}

function getStatusMessage(status?: TaskStatus): string {
  switch (status) {
    case 'pending': return 'Queued for processing'
    case 'processing': return 'Analyzing document'
    case 'completed': return 'Analysis complete'
    case 'failed': return 'Analysis failed'
    default: return 'Processing'
  }
}
