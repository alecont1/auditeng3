import { useQuery } from '@tanstack/react-query'
import { getTaskStatus } from '@/services/analysis'
import type { TaskStatusResponse } from '@/types'

interface UseTaskStatusOptions {
  taskId: string | null
  enabled?: boolean
  onCompleted?: (result: TaskStatusResponse) => void
  onFailed?: (error: string) => void
}

export function useTaskStatus({
  taskId,
  enabled = true,
  onCompleted,
  onFailed,
}: UseTaskStatusOptions) {
  return useQuery({
    queryKey: ['taskStatus', taskId],
    queryFn: () => getTaskStatus(taskId!),
    enabled: enabled && !!taskId,
    refetchInterval: (query) => {
      const data = query.state.data
      // Stop polling when completed or failed
      if (data?.status === 'completed' || data?.status === 'failed') {
        if (data.status === 'completed' && onCompleted) {
          onCompleted(data)
        }
        if (data.status === 'failed' && onFailed) {
          onFailed(data.error || 'Analysis failed')
        }
        return false
      }
      // Poll every 2 seconds while processing
      return 2000
    },
  })
}
