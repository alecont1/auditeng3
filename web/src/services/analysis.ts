import api from '@/lib/api'
import type {
  SubmitAnalysisResponse,
  TaskStatusResponse,
  ListAnalysesParams,
  ListAnalysesResponse,
  AnalysisDetail,
} from '@/types'

/**
 * Submit document for analysis
 * Uses multipart/form-data for file upload
 */
export async function submitAnalysis(
  file: File,
  onUploadProgress?: (progress: number) => void
): Promise<SubmitAnalysisResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await api.post<SubmitAnalysisResponse>(
    '/analyses/submit',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (event) => {
        if (event.total && onUploadProgress) {
          const progress = Math.round((event.loaded / event.total) * 100)
          onUploadProgress(progress)
        }
      },
    }
  )

  return response.data
}

/**
 * Get task status for polling
 */
export async function getTaskStatus(taskId: string): Promise<TaskStatusResponse> {
  const response = await api.get<TaskStatusResponse>(`/tasks/${taskId}`)
  return response.data
}

/**
 * Get paginated list of analyses
 */
export async function getAnalyses(
  params: ListAnalysesParams = {}
): Promise<ListAnalysesResponse> {
  const response = await api.get<ListAnalysesResponse>('/analyses', { params })
  return response.data
}

/**
 * Get single analysis by ID
 * Returns null if analysis is still processing (202 status)
 */
export async function getAnalysis(analysisId: string): Promise<AnalysisDetail | null> {
  const response = await api.get<AnalysisDetail>(`/analyses/${analysisId}`, {
    validateStatus: (status) => status === 200 || status === 202,
  })

  // 202 means analysis is still processing
  if (response.status === 202) {
    return null
  }

  return response.data
}

/**
 * Approve an analysis
 * PUT /api/analyses/{id}/approve
 */
export async function approveAnalysis(analysisId: string): Promise<void> {
  await api.put(`/analyses/${analysisId}/approve`)
}

/**
 * Reject an analysis with reason
 * PUT /api/analyses/{id}/reject
 */
export async function rejectAnalysis(analysisId: string, reason: string): Promise<void> {
  await api.put(`/analyses/${analysisId}/reject`, { reason })
}

/**
 * Download PDF report for a completed analysis
 * GET /api/analyses/{id}/report
 *
 * Handles blob response and triggers browser download
 */
export async function downloadReport(analysisId: string): Promise<void> {
  const response = await api.get(`/analyses/${analysisId}/report`, {
    responseType: 'blob',
  })

  // Create blob from response data
  const blob = new Blob([response.data], { type: 'application/pdf' })

  // Create object URL for download
  const url = URL.createObjectURL(blob)

  // Create temporary anchor element to trigger download
  const link = document.createElement('a')
  link.href = url
  link.download = `report_${analysisId}.pdf`

  // Append to body, click to download, then remove
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  // Cleanup: revoke object URL
  URL.revokeObjectURL(url)
}
