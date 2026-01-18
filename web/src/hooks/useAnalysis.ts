import { useQuery } from '@tanstack/react-query'
import { getAnalysis } from '@/services/analysis'

export function useAnalysis(analysisId: string) {
  return useQuery({
    queryKey: ['analysis', analysisId],
    queryFn: () => getAnalysis(analysisId),
    enabled: !!analysisId,
    // Refetch every 5 seconds if analysis is still processing (null response)
    refetchInterval: (query) => {
      // If data is null, analysis is still processing - poll
      if (query.state.data === null) {
        return 5000
      }
      return false
    },
    // Consider null as "pending" data, not an error
    retry: 3,
  })
}
