/**
 * Standard API error response from backend
 */
export interface ApiError {
  detail: string
  error_code?: string
}

/**
 * Paginated response wrapper
 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  pages: number
}
