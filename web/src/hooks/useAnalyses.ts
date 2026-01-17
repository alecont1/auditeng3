import { useQuery } from '@tanstack/react-query'
import { getAnalyses } from '@/services'
import type { ListAnalysesParams } from '@/types'

/**
 * Hook for fetching paginated list of analyses
 */
export function useAnalyses(params: ListAnalysesParams = {}) {
  return useQuery({
    queryKey: ['analyses', params],
    queryFn: () => getAnalyses(params),
  })
}
