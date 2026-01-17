/**
 * Analysis submission response
 */
export interface SubmitAnalysisResponse {
  analysis_id: string
  task_id: string
  message: string
}

/**
 * Task status from polling endpoint
 */
export type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed'

export interface TaskStatusResponse {
  task_id: string
  status: TaskStatus
  progress?: number // 0-100
  result?: {
    analysis_id: string
  }
  error?: string
}

/**
 * Analysis verdict
 */
export type Verdict = 'APPROVED' | 'REJECTED' | 'NEEDS_REVIEW'

/**
 * Analysis summary (for list views)
 */
export interface AnalysisSummary {
  id: string
  equipment_tag: string
  test_type: string
  equipment_type: string
  verdict: Verdict
  compliance_score: number
  confidence_score: number
  status: 'pending' | 'completed' | 'failed'
  created_at: string
  updated_at: string
}
