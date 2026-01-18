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

/**
 * Pagination metadata from backend
 */
export interface PaginationMeta {
  page: number
  per_page: number
  total: number
  total_pages: number
}

/**
 * Query params for list analyses endpoint
 */
export interface ListAnalysesParams {
  page?: number
  per_page?: number
  status?: 'pending' | 'completed' | 'failed'
  date_from?: string
  date_to?: string
  sort_by?: 'created_at' | 'compliance_score'
  sort_order?: 'asc' | 'desc'
}

/**
 * Response from GET /api/analyses
 */
export interface ListAnalysesResponse {
  items: AnalysisSummary[]
  meta: PaginationMeta
}

/**
 * Evidence supporting a finding
 */
export interface FindingEvidence {
  extracted_value: unknown
  threshold: unknown
  standard_reference: string
}

/**
 * Detailed finding in analysis response
 */
export interface FindingDetail {
  rule_id: string
  severity: 'critical' | 'major' | 'minor' | 'info'
  message: string
  field_path?: string
  evidence?: FindingEvidence
  remediation?: string
}

/**
 * Complete analysis detail (from GET /api/analyses/:id)
 */
export interface AnalysisDetail {
  id: string
  equipment_type: string
  test_type: string
  equipment_tag?: string
  verdict?: Verdict
  compliance_score?: number
  confidence_score?: number
  findings: FindingDetail[]
  extraction_result?: Record<string, unknown>
  created_at: string
}

/**
 * Audit event from audit trail
 */
export interface AuditEvent {
  id: string
  event_type: string
  event_timestamp: string
  details?: Record<string, unknown>
  model_version?: string
  prompt_version?: string
  confidence_score?: number
  rule_id?: string
}

/**
 * Response from GET /api/analyses/{id}/audit
 */
export interface AuditTrailResponse {
  analysis_id: string
  event_count: number
  events: AuditEvent[]
}
