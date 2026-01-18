import { useQuery } from '@tanstack/react-query'
import { getAuditTrail } from '@/services/analysis'

export function useAuditTrail(analysisId: string | undefined) {
  return useQuery({
    queryKey: ['audit-trail', analysisId],
    queryFn: () => getAuditTrail(analysisId!),
    enabled: !!analysisId,
    staleTime: 30000, // 30 seconds - audit trails don't change often
  })
}
