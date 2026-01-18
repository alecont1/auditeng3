import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { rejectAnalysis } from '@/services/analysis'

export function useRejectAnalysis(analysisId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (reason: string) => rejectAnalysis(analysisId, reason),
    onSuccess: () => {
      toast.success('Analysis rejected')
      // Invalidate both single analysis and list
      queryClient.invalidateQueries({ queryKey: ['analysis', analysisId] })
      queryClient.invalidateQueries({ queryKey: ['analyses'] })
    },
    onError: (error) => {
      // Provide specific error messages
      const errorMessage = error instanceof Error ? error.message : ''
      if (errorMessage.includes('409') || errorMessage.toLowerCase().includes('already')) {
        toast.error('Analysis has already been reviewed.')
      } else if (errorMessage.includes('404') || errorMessage.toLowerCase().includes('not found')) {
        toast.error('Analysis not found. It may have been deleted.')
      } else if (errorMessage.toLowerCase().includes('network') || error instanceof TypeError) {
        toast.error('Unable to complete action. Please check your connection and try again.')
      } else {
        toast.error(errorMessage || 'Failed to reject analysis. Please try again.')
      }
    },
  })
}
