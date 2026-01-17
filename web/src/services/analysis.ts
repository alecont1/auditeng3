import api from '@/lib/api'
import type {
  SubmitAnalysisResponse,
  TaskStatusResponse,
  ListAnalysesParams,
  ListAnalysesResponse,
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
